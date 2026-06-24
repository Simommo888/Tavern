from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from interfaces.production import MaterialRecord, ProductionRun
from tools.digital_human_generator_heygen_api import DigitalHumanGeneratorHeyGenAPI

from .models import ToolResult
from .production_store import ProductionStore
from .tools import ToolArgumentSchema, ToolRuntimeContext, ToolSpec


DRY_RUN_ENV = "VIMAX_PRODUCTION_DRY_RUN"
HEYGEN_DRY_RUN_ENV = "HEYGEN_DRY_RUN"
DIGITAL_HUMAN_AGENT = "digital_human_live_room_agent"
HEYGEN_PROVIDER = "heygen"


def build_heygen_skill_specs(workspace_root: str | Path, session_index: Any) -> list[ToolSpec]:
    skills = HeyGenLiveRoomSkills(Path(workspace_root), session_index)
    return [
        ToolSpec(
            name="heygen_live_room_check_config",
            description="Digital-human live-room agent skill: check HeyGen configuration without exposing secrets; reports whether real generation or dry-run is available.",
            handler=skills.heygen_live_room_check_config,
            schema={
                "session_id": ToolArgumentSchema(str, required=False, default=""),
                "avatar_id": ToolArgumentSchema(str, required=False, default=""),
                "voice_id": ToolArgumentSchema(str, required=False, default=""),
                "dry_run": ToolArgumentSchema(bool, required=False, default=False),
            },
            concurrency_safe=True,
        ),
        ToolSpec(
            name="heygen_live_room_prepare_script",
            description="Digital-human live-room agent skill: convert a sales_script material into a HeyGen-ready host script material and register it in the production ledger.",
            handler=skills.heygen_live_room_prepare_script,
            schema={
                "session_id": ToolArgumentSchema(str, required=False, default=""),
                "run_id": ToolArgumentSchema(str, required=False, default=""),
                "script_material_id": ToolArgumentSchema(str, required=False, default=""),
                "shot_plan_material_id": ToolArgumentSchema(str, required=False, default=""),
                "segment_strategy": ToolArgumentSchema(str, required=False, default="host_lines"),
            },
        ),
        ToolSpec(
            name="heygen_live_room_generate_clip",
            description="Digital-human live-room agent skill: call HeyGen or dry-run to generate a digital-human live-room clip, save it, and register a traceable video material.",
            handler=skills.heygen_live_room_generate_clip,
            aliases=("heygen_live_room_generation", "digital_human_live_room_generation"),
            schema={
                "session_id": ToolArgumentSchema(str, required=False, default=""),
                "run_id": ToolArgumentSchema(str, required=False, default=""),
                "script_material_id": ToolArgumentSchema(str, required=False, default=""),
                "heygen_script_material_id": ToolArgumentSchema(str, required=False, default=""),
                "script_text": ToolArgumentSchema(str, required=False, default=""),
                "avatar_id": ToolArgumentSchema(str, required=False, default=""),
                "voice_id": ToolArgumentSchema(str, required=False, default=""),
                "background_asset_path": ToolArgumentSchema(str, required=False, default=""),
                "product_asset_paths": ToolArgumentSchema(list, required=False, default=[]),
                "aspect_ratio": ToolArgumentSchema(str, required=False, default="9:16"),
                "resolution": ToolArgumentSchema(str, required=False, default="1080p"),
                "clip_role": ToolArgumentSchema(str, required=False, default="host_live_room"),
                "dry_run": ToolArgumentSchema(bool, required=False, default=False),
            },
        ),
    ]


class HeyGenLiveRoomSkills:
    def __init__(self, workspace_root: str | Path, session_index: Any) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.session_index = session_index
        self.store = ProductionStore(self.workspace_root, session_index)

    async def heygen_live_room_check_config(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        dry_run = _effective_dry_run(args)
        avatar = str(args.get("avatar_id") or os.environ.get("HEYGEN_AVATAR_ID") or "")
        voice = str(args.get("voice_id") or os.environ.get("HEYGEN_VOICE_ID") or "")
        api_key_configured = bool(os.environ.get("HEYGEN_API_KEY"))
        base_url = os.environ.get("HEYGEN_BASE_URL", "https://api.heygen.com")
        missing = []
        if not api_key_configured:
            missing.append("HEYGEN_API_KEY")
        if not avatar:
            missing.append("HEYGEN_AVATAR_ID")
        if not voice:
            missing.append("HEYGEN_VOICE_ID")
        payload = {
            "provider": HEYGEN_PROVIDER,
            "agent_name": DIGITAL_HUMAN_AGENT,
            "session_id": str(args.get("session_id") or ""),
            "base_url": base_url,
            "api_key_configured": api_key_configured,
            "avatar_configured": bool(avatar),
            "voice_configured": bool(voice),
            "effective_dry_run": dry_run,
            "can_generate_real": not dry_run and not missing,
            "can_generate": dry_run or not missing,
            "missing": [] if dry_run else missing,
            "next_tool": "heygen_live_room_prepare_script",
        }
        _progress(runtime, "heygen_config", "Checked HeyGen live-room configuration", {"effective_dry_run": dry_run, "can_generate_real": payload["can_generate_real"]})
        return _ok("heygen_live_room_check_config", payload)

    async def heygen_live_room_prepare_script(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        task = None
        run: ProductionRun | None = None
        try:
            run = self._load_run(str(args.get("session_id") or ""))
            script_id = str(args.get("script_material_id") or run.script_material_id or "")
            script_material = self._require_material(run.session_id, script_id, {"sales_script"})
            input_ids = [script_id]
            shot_plan_id = str(args.get("shot_plan_material_id") or run.shot_plan_material_id or "")
            if shot_plan_id:
                self._require_material(run.session_id, shot_plan_id, {"shot_plan"})
                input_ids.append(shot_plan_id)
            script_text = self._read_material_text(run.session_id, script_material)
            prepared = _extract_host_lines(script_text)
            task = self.store.start_task(run, agent_name=DIGITAL_HUMAN_AGENT, tool_name="heygen_live_room_prepare_script", input_material_ids=input_ids, provider=HEYGEN_PROVIDER, metadata={"segment_strategy": str(args.get("segment_strategy") or "host_lines")})
            self._stage(run.session_id, "production_heygen_script", "Preparing HeyGen host script")
            _progress(runtime, "heygen_prepare_script", "Preparing host lines for HeyGen", {"run_id": run.run_id, "script_material_id": script_id})
            material = self.store.add_text_material(
                run,
                material_type="heygen_script",
                role="host_script_for_heygen",
                content=prepared,
                source_agent=DIGITAL_HUMAN_AGENT,
                task_id=task.task_id,
                prompt=script_text[:500],
                input_material_ids=input_ids,
                metadata={"segment_strategy": str(args.get("segment_strategy") or "host_lines"), "source_material_type": script_material.material_type},
            )
            self.store.finish_task(task, output_material_ids=[material.material_id])
            return _ok("heygen_live_room_prepare_script", {"run_id": run.run_id, "session_id": run.session_id, "heygen_script_material_id": material.material_id, "heygen_script_path": material.file_path, "segment_count": _segment_count(prepared), "input_material_ids": input_ids, "next_tool": "heygen_live_room_generate_clip"})
        except Exception as exc:
            if task is not None:
                self.store.finish_task(task, error=str(exc), metadata={"error_type": _classify_error(exc)})
            return _error("heygen_live_room_prepare_script", str(exc), _classify_error(exc))

    async def heygen_live_room_generate_clip(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        task = None
        run: ProductionRun | None = None
        try:
            raw_script_text = str(args.get("script_text") or "").strip()
            run = self._load_or_create_run(str(args.get("session_id") or ""), raw_script_text)
            source_material = self._resolve_script_material(run, args)
            input_material_ids: list[str] = []
            if source_material is not None:
                input_material_ids.append(source_material.material_id)
                source_text = self._read_material_text(run.session_id, source_material)
                script_text = source_text if source_material.material_type == "heygen_script" else _extract_host_lines(source_text)
            else:
                if not raw_script_text:
                    raise RuntimeError("Provide `heygen_script_material_id`, `script_material_id`, or `script_text` for HeyGen live-room generation.")
                script_text = _extract_host_lines(raw_script_text)

            dry_run = _effective_dry_run(args)
            task = self.store.start_task(run, agent_name=DIGITAL_HUMAN_AGENT, tool_name="heygen_live_room_generate_clip", input_material_ids=input_material_ids, provider=HEYGEN_PROVIDER, metadata={"dry_run": dry_run})
            self._stage(run.session_id, "production_heygen", "Generating HeyGen digital human live-room clip")
            if source_material is None:
                source_material = self.store.add_text_material(
                    run,
                    material_type="heygen_script",
                    role="host_script_for_heygen",
                    content=script_text,
                    source_agent=DIGITAL_HUMAN_AGENT,
                    task_id=task.task_id,
                    prompt=raw_script_text[:500],
                    metadata={"source": "script_text"},
                )
                input_material_ids = [source_material.material_id]

            aspect_ratio = str(args.get("aspect_ratio") or "9:16")
            resolution = str(args.get("resolution") or "1080p")
            product_asset_paths = [str(item) for item in (args.get("product_asset_paths") or []) if str(item).strip()]
            background_asset_path = str(args.get("background_asset_path") or "")
            clip_role = str(args.get("clip_role") or "host_live_room")
            generator = DigitalHumanGeneratorHeyGenAPI()
            result = await generator.generate_live_room_segment(
                script_text=script_text,
                avatar_id=str(args.get("avatar_id") or ""),
                voice_id=str(args.get("voice_id") or ""),
                background_asset_path=background_asset_path,
                product_asset_paths=product_asset_paths,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                metadata={"run_id": run.run_id, "session_id": run.session_id, "clip_role": clip_role},
                progress=lambda stage, message, metadata=None: _progress(runtime, stage, message, metadata),
                dry_run=dry_run,
            )
            output_path = self.store.production_dir(run.session_id) / "assets" / "clips" / f"heygen-{task.task_id}.mp4"
            result.save(str(output_path))
            material = self.store.add_file_material(
                run,
                material_type="digital_human_video",
                role=clip_role,
                file_path=output_path,
                source_agent=DIGITAL_HUMAN_AGENT,
                source_provider=HEYGEN_PROVIDER,
                provider_model=HEYGEN_PROVIDER,
                provider_job_id=result.provider_job_id,
                task_id=task.task_id,
                prompt=script_text[:1000],
                input_material_ids=input_material_ids,
                metadata={
                    "raw_response": result.raw_response,
                    "dry_run": dry_run,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                    "background_asset_path": background_asset_path,
                    "product_asset_paths": product_asset_paths,
                },
            )
            if material.material_id not in run.digital_human_clip_ids:
                run.digital_human_clip_ids.append(material.material_id)
            run.stage = "digital_human_generated"
            self.store.save_run(run)
            self.store.finish_task(task, output_material_ids=[material.material_id], metadata={"provider_job_id": result.provider_job_id, "input_material_ids": input_material_ids})
            return _ok(
                "heygen_live_room_generate_clip",
                {
                    "run_id": run.run_id,
                    "session_id": run.session_id,
                    "agent_name": DIGITAL_HUMAN_AGENT,
                    "digital_human_clip_material_ids": [material.material_id],
                    "provider_job_ids": [result.provider_job_id],
                    "clip_paths": [material.file_path],
                    "input_material_ids": input_material_ids,
                    "dry_run": dry_run,
                    "next_tool": "ffmpeg_video_composition",
                },
            )
        except Exception as exc:
            if task is not None:
                self.store.finish_task(task, error=str(exc), metadata={"error_type": _classify_error(exc)})
            if run is not None:
                run.status = "failed"
                run.stage = "digital_human_failed"
                self.store.save_run(run)
            return _error("heygen_live_room_generate_clip", str(exc), _classify_error(exc))

    def _load_run(self, session_id: str = "") -> ProductionRun:
        return self.store.load_run(session_id or None)

    def _load_or_create_run(self, session_id: str, script_text: str) -> ProductionRun:
        try:
            return self.store.load_run(session_id or None)
        except FileNotFoundError:
            if not script_text:
                raise
            return self.store.create_or_load_run(session_id=session_id, user_idea=script_text[:160])

    def _resolve_script_material(self, run: ProductionRun, args: dict[str, Any]) -> MaterialRecord | None:
        material_id = str(args.get("heygen_script_material_id") or args.get("script_material_id") or run.script_material_id or "")
        if not material_id:
            return None
        return self._require_material(run.session_id, material_id, {"heygen_script", "sales_script"})

    def _require_material(self, session_id: str, material_id: str, expected_types: set[str]) -> MaterialRecord:
        if not material_id:
            raise RuntimeError(f"Missing material id for expected types: {sorted(expected_types)}")
        material = self.store.latest_materials_by_id(session_id).get(material_id)
        if material is None:
            raise RuntimeError(f"Unknown material id: {material_id}")
        if expected_types and material.material_type not in expected_types:
            raise RuntimeError(f"Material {material_id} is {material.material_type}, expected one of {sorted(expected_types)}")
        return material

    def _read_material_text(self, session_id: str, material: MaterialRecord) -> str:
        path = self.store.resolve_material_path(session_id, material)
        return path.read_text(encoding="utf-8")

    def _stage(self, session_id: str, stage: str, summary: str) -> None:
        try:
            self.session_index.update_stage(session_id, stage, summary)
        except Exception:
            pass


def _extract_host_lines(script_text: str) -> str:
    lines = []
    for line in script_text.splitlines():
        if "主播" in line or line.startswith("## Segment"):
            lines.append(line)
    return "\n".join(lines).strip() or script_text[:1500]


def _segment_count(script_text: str) -> int:
    count = sum(1 for line in script_text.splitlines() if line.startswith("## Segment"))
    return max(1, count)


def _effective_dry_run(args: dict[str, Any]) -> bool:
    return _truthy(args.get("dry_run")) or _env_truthy(DRY_RUN_ENV) or _env_truthy(HEYGEN_DRY_RUN_ENV)


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _progress(runtime: ToolRuntimeContext | None, stage: str, message: str, metadata: dict[str, Any] | None = None) -> None:
    if runtime:
        runtime.emit_progress(message, stage=stage, metadata=metadata or {})


def _classify_error(exc: Exception) -> str:
    message = str(exc)
    if "Provide `" in message or "Missing material id" in message or "Unknown material id" in message:
        return "missing_input"
    if "HEYGEN_API_KEY" in message or "HEYGEN_AVATAR_ID" in message or "HEYGEN_VOICE_ID" in message:
        return "missing_config"
    if "save" in message.lower() or "video url" in message.lower() or "neither video bytes" in message.lower():
        return "save_error"
    if "HeyGen" in message or "HTTP" in message or "timed out" in message:
        return "provider_error"
    return "exception"


def _ok(name: str, payload: dict[str, Any]) -> ToolResult:
    return ToolResult(name, True, json.dumps(payload, ensure_ascii=True, indent=2), payload)


def _error(name: str, message: str, error_type: str = "exception") -> ToolResult:
    return ToolResult(name, False, message, {"error_type": error_type})
