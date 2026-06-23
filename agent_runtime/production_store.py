from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from interfaces.production import (
    AlcoholSalesBrief,
    CompositionManifest,
    MaterialRecord,
    PerformanceMetric,
    ProductionRun,
    ProductionTaskRecord,
    ReusablePattern,
    TimelineSegment,
    utc_now_iso,
)


TEXT_MATERIAL_TYPES = {"idea", "story", "sales_script", "storyboard", "shot_plan", "composition_manifest", "reusable_pattern"}


class ProductionStore:
    """Session-scoped production ledger for modular commerce video assets."""

    def __init__(self, workspace_root: str | Path, session_index: Any) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.session_index = session_index
        self.knowledge_dir = self.workspace_root / ".vimax" / "production_knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

    def active_session(self, idea: str = "", user_requirement: str = "", style: str = "") -> dict[str, Any]:
        session = self.session_index.active()
        if session is not None:
            return session
        return self.session_index.create(idea=idea, user_requirement=user_requirement, style=style)

    def production_dir(self, session_id: str | None = None) -> Path:
        root = self.session_index.working_dir(session_id)
        path = root / "production"
        self._ensure_layout(path)
        return path

    def create_or_load_run(self, *, session_id: str = "", user_idea: str = "", brief: AlcoholSalesBrief | dict[str, Any] | None = None) -> ProductionRun:
        session = self.session_index.get(session_id) if session_id else self.active_session(idea=user_idea)
        if session is None:
            session = self.session_index.create(idea=user_idea, session_id=session_id or None)
        production_dir = self.production_dir(session["session_id"])
        path = production_dir / "run.json"
        if path.exists():
            return ProductionRun.model_validate_json(path.read_text(encoding="utf-8"))
        run = ProductionRun(
            run_id=self._new_id("run", user_idea or session["session_id"]),
            session_id=session["session_id"],
            user_idea=user_idea or str(session.get("idea") or ""),
            brief=AlcoholSalesBrief.model_validate(brief or {}),
        )
        self.save_run(run)
        return run

    def load_run(self, session_id: str | None = None) -> ProductionRun:
        path = self.production_dir(session_id) / "run.json"
        if not path.exists():
            raise FileNotFoundError(f"Production run not found: {path}")
        return ProductionRun.model_validate_json(path.read_text(encoding="utf-8"))

    def save_run(self, run: ProductionRun) -> None:
        run.updated_at = utc_now_iso()
        path = self.production_dir(run.session_id) / "run.json"
        self._write_json(path, run.model_dump())

    def update_run(self, run: ProductionRun, **updates: Any) -> ProductionRun:
        for key, value in updates.items():
            setattr(run, key, value)
        self.save_run(run)
        return run

    def start_task(self, run: ProductionRun, *, agent_name: str, tool_name: str, input_material_ids: list[str] | None = None, metadata: dict[str, Any] | None = None, provider: str = "") -> ProductionTaskRecord:
        task = ProductionTaskRecord(
            task_id=self._new_id("task", agent_name),
            run_id=run.run_id,
            session_id=run.session_id,
            agent_name=agent_name,
            status="in_progress",
            input_material_ids=input_material_ids or [],
            tool_name=tool_name,
            provider=provider,
            metadata=metadata or {},
        )
        self.append_task(task)
        return task

    def finish_task(self, task: ProductionTaskRecord, *, output_material_ids: list[str] | None = None, error: str = "", metadata: dict[str, Any] | None = None) -> ProductionTaskRecord:
        task.status = "failed" if error else "completed"
        task.output_material_ids = output_material_ids or task.output_material_ids
        task.error = error
        task.finished_at = utc_now_iso()
        if metadata:
            task.metadata.update(metadata)
        self.append_task(task)
        return task

    def append_task(self, task: ProductionTaskRecord) -> None:
        self._append_jsonl(self.production_dir(task.session_id) / "tasks.jsonl", task.model_dump())

    def add_text_material(
        self,
        run: ProductionRun,
        *,
        material_type: str,
        content: str,
        role: str = "",
        source_agent: str = "",
        task_id: str = "",
        prompt: str = "",
        input_material_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        ext: str = "txt",
    ) -> MaterialRecord:
        material_id = self._new_id(self._short_type(material_type), role or material_type)
        rel_path = Path("production") / "assets" / "text" / f"{material_id}.{ext}"
        abs_path = self.workspace_root / self.session_index.working_dir(run.session_id).relative_to(self.workspace_root) / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        record = MaterialRecord(
            material_id=material_id,
            material_type=material_type,
            role=role,
            session_id=run.session_id,
            run_id=run.run_id,
            task_id=task_id,
            source_agent=source_agent,
            prompt=prompt,
            input_material_ids=input_material_ids or [],
            file_path=str(rel_path).replace("\\", "/"),
            content_hash=self.file_hash(abs_path),
            mime_type="text/plain" if ext != "json" else "application/json",
            text_content_preview=content[:240],
            metadata=metadata or {},
        )
        self.append_material(record)
        return record

    def add_file_material(
        self,
        run: ProductionRun,
        *,
        material_type: str,
        file_path: str | Path,
        role: str = "",
        source_agent: str = "",
        source_provider: str = "",
        provider_model: str = "",
        provider_job_id: str = "",
        task_id: str = "",
        prompt: str = "",
        input_material_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        used_in_final: bool = False,
    ) -> MaterialRecord:
        abs_path = Path(file_path).resolve()
        if not abs_path.exists():
            raise FileNotFoundError(f"Material file not found: {abs_path}")
        record = MaterialRecord(
            material_id=self._new_id(self._short_type(material_type), role or abs_path.stem),
            material_type=material_type,
            role=role,
            session_id=run.session_id,
            run_id=run.run_id,
            task_id=task_id,
            source_agent=source_agent,
            source_provider=source_provider,
            provider_model=provider_model,
            provider_job_id=provider_job_id,
            prompt=prompt,
            input_material_ids=input_material_ids or [],
            file_path=self._relative_to_session(run.session_id, abs_path),
            content_hash=self.file_hash(abs_path),
            mime_type=self._guess_mime(abs_path),
            metadata=metadata or {},
            used_in_final=used_in_final,
        )
        self.append_material(record)
        return record

    def append_material(self, material: MaterialRecord) -> None:
        self._append_jsonl(self.production_dir(material.session_id) / "materials.jsonl", material.model_dump())

    def load_materials(self, session_id: str | None = None) -> list[MaterialRecord]:
        path = self.production_dir(session_id) / "materials.jsonl"
        return [MaterialRecord.model_validate(row) for row in self._read_jsonl(path)]

    def latest_materials_by_id(self, session_id: str | None = None) -> dict[str, MaterialRecord]:
        items: dict[str, MaterialRecord] = {}
        for material in self.load_materials(session_id):
            items[material.material_id] = material
        return items

    def write_manifest(self, manifest: CompositionManifest) -> Path:
        path = self.production_dir(manifest.session_id) / "composition_manifest.json"
        self._write_json(path, manifest.model_dump())
        return path

    def load_manifest(self, session_id: str | None = None) -> CompositionManifest:
        path = self.production_dir(session_id) / "composition_manifest.json"
        if not path.exists():
            raise FileNotFoundError(f"Composition manifest not found: {path}")
        return CompositionManifest.model_validate_json(path.read_text(encoding="utf-8"))

    def validate_manifest_traceability(self, manifest: CompositionManifest) -> tuple[bool, list[str]]:
        errors: list[str] = []
        materials = self.latest_materials_by_id(manifest.session_id)
        for segment in manifest.timeline:
            material = materials.get(segment.material_id)
            if material is None:
                errors.append(f"Missing material record for segment {segment.segment_id}: {segment.material_id}")
                continue
            path = self.resolve_material_path(manifest.session_id, material)
            if not path.exists():
                errors.append(f"Missing material file for {material.material_id}: {material.file_path}")
                continue
            if material.content_hash and self.file_hash(path) != material.content_hash:
                errors.append(f"Hash mismatch for {material.material_id}: {material.file_path}")
        return not errors, errors

    def add_performance_metric(self, run: ProductionRun, payload: dict[str, Any]) -> PerformanceMetric:
        metric = PerformanceMetric(
            metric_id=self._new_id("metric", run.run_id),
            run_id=run.run_id,
            final_video_material_id=run.final_video_material_id,
            **{key: value for key, value in payload.items() if key in PerformanceMetric.model_fields and key != "metric_id"},
        )
        metric.score = self.performance_score(metric)
        self._append_jsonl(self.production_dir(run.session_id) / "performance_metrics.jsonl", metric.model_dump())
        return metric

    def maybe_create_reusable_pattern(self, run: ProductionRun, metric: PerformanceMetric, *, threshold: float = 60.0) -> ReusablePattern | None:
        if metric.score < threshold:
            return None
        materials = [item for item in self.load_materials(run.session_id) if item.used_in_final or item.material_id in {run.story_material_id, run.script_material_id, run.storyboard_material_id, run.shot_plan_material_id}]
        pattern = ReusablePattern(
            pattern_id=self._new_id("pattern", run.run_id),
            source_run_id=run.run_id,
            source_metric_id=metric.metric_id,
            score=metric.score,
            sales_angle=run.brief.sales_goal or run.user_idea[:120],
            story_structure=" -> ".join([item.material_type for item in materials[:12]]),
            script_hook=(next((item.text_content_preview for item in materials if item.material_type == "sales_script"), "")[:160]),
            transition_style=", ".join(sorted({item.role for item in materials if item.material_type in {"transition_video", "product_closeup_video"} and item.role})[:5]),
            winning_material_ids=[item.material_id for item in materials],
            recommended_reuse="复用该视频的开场钩子、素材组合、数字人节奏和转场特写结构。",
            metadata={"platform": metric.platform, "gmv": metric.gmv, "roi": metric.roi, "conversion_rate": metric.conversion_rate},
        )
        self._append_jsonl(self.production_dir(run.session_id) / "reusable_patterns.jsonl", pattern.model_dump())
        self._append_jsonl(self.knowledge_dir / "reusable_patterns.jsonl", pattern.model_dump())
        return pattern

    def search_reusable_patterns(self, query: str = "", limit: int = 5) -> list[ReusablePattern]:
        rows = [ReusablePattern.model_validate(row) for row in self._read_jsonl(self.knowledge_dir / "reusable_patterns.jsonl")]
        if query:
            needle = query.lower()
            rows = [row for row in rows if needle in json.dumps(row.model_dump(), ensure_ascii=True).lower()]
        return sorted(rows, key=lambda item: item.score, reverse=True)[:limit]

    def resolve_material_path(self, session_id: str, material: MaterialRecord) -> Path:
        path = Path(material.file_path)
        if path.is_absolute():
            return path
        return (self.session_index.working_dir(session_id) / path).resolve()

    def performance_score(self, metric: PerformanceMetric) -> float:
        roi_score = min(max(metric.roi, 0.0), 10.0) * 6.0
        conversion_score = min(max(metric.conversion_rate, 0.0), 1.0) * 25.0
        completion_score = min(max(metric.completion_rate, 0.0), 1.0) * 10.0
        order_score = min(metric.orders, 100) * 0.3
        gmv_score = min(metric.gmv / 1000.0, 20.0)
        return round(roi_score + conversion_score + completion_score + order_score + gmv_score, 2)

    def file_hash(self, path: str | Path) -> str:
        digest = hashlib.sha256()
        with Path(path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _ensure_layout(self, path: Path) -> None:
        for subdir in ["assets/text", "assets/clips", "assets/final", "prompts", "provider_jobs", "ffmpeg"]:
            (path / subdir).mkdir(parents=True, exist_ok=True)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
        os.replace(tmp_path, path)

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True, default=str) + "\n")

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def _relative_to_session(self, session_id: str, path: Path) -> str:
        root = self.session_index.working_dir(session_id)
        try:
            return str(path.resolve().relative_to(root)).replace("\\", "/")
        except ValueError:
            return str(path.resolve())

    def _new_id(self, prefix: str, source: str = "") -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", source.lower()).strip("-")[:32] or prefix
        return f"{prefix}-{slug}-{uuid4().hex[:8]}"

    def _short_type(self, material_type: str) -> str:
        return "".join(part[0] for part in material_type.split("_") if part)[:6] or "mat"

    def _guess_mime(self, path: Path) -> str:
        suffix = path.suffix.lower()
        return {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".json": "application/json",
            ".txt": "text/plain",
        }.get(suffix, "application/octet-stream")


def manifest_from_materials(*, run: ProductionRun, materials: list[MaterialRecord], output_path: str = "") -> CompositionManifest:
    timeline = []
    cursor = 0.0
    for index, material in enumerate(materials):
        duration = float(material.duration_seconds or material.metadata.get("duration_seconds") or 0.0)
        timeline.append(TimelineSegment(segment_id=f"segment-{index}", material_id=material.material_id, file_path=material.file_path, start_time=cursor, duration=duration, out_point=duration or None, layer=0))
        cursor += duration
    return CompositionManifest(composition_id=f"composition-{uuid4().hex[:8]}", run_id=run.run_id, session_id=run.session_id, timeline=timeline, output_path=output_path)
