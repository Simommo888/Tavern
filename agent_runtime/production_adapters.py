from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from interfaces.production import AlcoholSalesBrief, CompositionManifest, FfmpegCommandSummary, MaterialRecord
from tools.video_generator_veo_google_api import VideoGeneratorVeoGoogleAPI
from utils.ffmpeg_cli import compose_timeline

from .heygen_skills import HeyGenLiveRoomSkills
from .config import video_api_key, video_base_url, video_model
from .models import ToolResult
from .production_store import ProductionStore, manifest_from_materials
from .tools import ToolArgumentSchema, ToolRuntimeContext, ToolSpec


DRY_RUN_ENV = "VIMAX_PRODUCTION_DRY_RUN"


def build_production_adapter_specs(workspace_root: str | Path, session_index: Any) -> list[ToolSpec]:
    adapter = AlcoholProductionAdapters(Path(workspace_root), session_index)
    return [
        ToolSpec(
            name="alcohol_story_generation",
            description="Worker agent: expand a user's alcohol live-commerce idea into a modular sales story and create a ProductionRun/material record.",
            handler=adapter.alcohol_story_generation,
            schema={
                "session_id": ToolArgumentSchema(str, required=False, default=""),
                "idea": ToolArgumentSchema(str, required=True),
                "product_brief": ToolArgumentSchema(str, required=False, default=""),
                "brand": ToolArgumentSchema(str, required=False, default=""),
                "product_name": ToolArgumentSchema(str, required=False, default=""),
                "target_audience": ToolArgumentSchema(str, required=False, default=""),
                "sales_goal": ToolArgumentSchema(str, required=False, default=""),
                "style": ToolArgumentSchema(str, required=False, default=""),
            },
        ),
        ToolSpec(
            name="alcohol_script_generation",
            description="Worker agent: turn a sales story material into a live-commerce host script with CTA and compliance notes.",
            handler=adapter.alcohol_script_generation,
            schema={
                "session_id": ToolArgumentSchema(str, required=False, default=""),
                "run_id": ToolArgumentSchema(str, required=False, default=""),
                "story_material_id": ToolArgumentSchema(str, required=False, default=""),
                "duration_target_seconds": ToolArgumentSchema(int, required=False, default=60),
                "cta_requirements": ToolArgumentSchema(str, required=False, default=""),
                "compliance_requirements": ToolArgumentSchema(str, required=False, default=""),
            },
        ),
        ToolSpec(
            name="alcohol_storyboard_generation",
            description="Worker agent: convert a live-commerce sales script into storyboard and shot-plan materials for HeyGen and Veo workers.",
            handler=adapter.alcohol_storyboard_generation,
            schema={
                "session_id": ToolArgumentSchema(str, required=False, default=""),
                "run_id": ToolArgumentSchema(str, required=False, default=""),
                "script_material_id": ToolArgumentSchema(str, required=False, default=""),
                "aspect_ratio": ToolArgumentSchema(str, required=False, default="9:16"),
                "max_shots": ToolArgumentSchema(int, required=False, default=6),
                "visual_style": ToolArgumentSchema(str, required=False, default="高质感酒类直播间"),
            },
        ),
        ToolSpec(
            name="heygen_live_room_generation",
            description="Compatibility alias: delegate HeyGen digital-human live-room generation to the digital-human live-room skill package.",
            handler=adapter.heygen_live_room_generation,
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
        ToolSpec(
            name="veo_transition_closeup_generation",
            description="Worker agent: call Veo 3.1 (or dry-run) to create alcohol product close-up and transition clips, then register materials.",
            handler=adapter.veo_transition_closeup_generation,
            schema={
                "session_id": ToolArgumentSchema(str, required=False, default=""),
                "run_id": ToolArgumentSchema(str, required=False, default=""),
                "storyboard_material_id": ToolArgumentSchema(str, required=False, default=""),
                "shot_plan_material_id": ToolArgumentSchema(str, required=False, default=""),
                "prompts": ToolArgumentSchema(list, required=False, default=[]),
                "clip_count": ToolArgumentSchema(int, required=False, default=2),
                "aspect_ratio": ToolArgumentSchema(str, required=False, default="9:16"),
                "resolution": ToolArgumentSchema(str, required=False, default="1080p"),
                "duration": ToolArgumentSchema(int, required=False, default=6),
                "dry_run": ToolArgumentSchema(bool, required=False, default=False),
            },
        ),
        ToolSpec(
            name="ffmpeg_video_composition",
            description="Worker agent: compose registered digital-human and transition clips with ffmpeg CLI, create final video material and manifest.",
            handler=adapter.ffmpeg_video_composition,
            schema={
                "session_id": ToolArgumentSchema(str, required=False, default=""),
                "run_id": ToolArgumentSchema(str, required=False, default=""),
                "material_ids": ToolArgumentSchema(list, required=False, default=[]),
                "target_resolution": ToolArgumentSchema(str, required=False, default="1080x1920"),
                "target_fps": ToolArgumentSchema(int, required=False, default=30),
                "dry_run": ToolArgumentSchema(bool, required=False, default=False),
            },
        ),
        ToolSpec(
            name="production_run_status",
            description="Review tool: inspect the active alcohol production run, registered materials, and traceability status.",
            handler=adapter.production_run_status,
            schema={"session_id": ToolArgumentSchema(str, required=False, default="")},
            concurrency_safe=True,
        ),
        ToolSpec(
            name="production_performance_ingest",
            description="Worker agent: ingest manual commerce performance metrics and promote high-performing runs to reusable patterns.",
            handler=adapter.production_performance_ingest,
            schema={
                "session_id": ToolArgumentSchema(str, required=False, default=""),
                "platform": ToolArgumentSchema(str, required=False, default=""),
                "platform_video_id": ToolArgumentSchema(str, required=False, default=""),
                "published_url": ToolArgumentSchema(str, required=False, default=""),
                "views": ToolArgumentSchema(int, required=False, default=0),
                "clicks": ToolArgumentSchema(int, required=False, default=0),
                "orders": ToolArgumentSchema(int, required=False, default=0),
                "gmv": ToolArgumentSchema(str, required=False, default="0"),
                "roi": ToolArgumentSchema(str, required=False, default="0"),
                "conversion_rate": ToolArgumentSchema(str, required=False, default="0"),
                "completion_rate": ToolArgumentSchema(str, required=False, default="0"),
            },
        ),
        ToolSpec(
            name="production_reusable_patterns_search",
            description="Review tool: search reusable high-performance alcohol live-commerce patterns for future runs.",
            handler=adapter.production_reusable_patterns_search,
            schema={
                "query": ToolArgumentSchema(str, required=False, default=""),
                "limit": ToolArgumentSchema(int, required=False, default=5),
            },
            concurrency_safe=True,
        ),
    ]


class AlcoholProductionAdapters:
    def __init__(self, workspace_root: Path, session_index: Any) -> None:
        self.workspace_root = workspace_root.resolve()
        self.session_index = session_index
        self.store = ProductionStore(self.workspace_root, session_index)

    async def alcohol_story_generation(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        idea = str(args.get("idea") or "").strip()
        if not idea:
            return _error("alcohol_story_generation", "Provide `idea` for story generation.", "missing_input")
        brief = AlcoholSalesBrief(
            brand=str(args.get("brand") or ""),
            product_name=str(args.get("product_name") or ""),
            product_brief=str(args.get("product_brief") or ""),
            target_audience=str(args.get("target_audience") or ""),
            sales_goal=str(args.get("sales_goal") or ""),
            style=str(args.get("style") or "高质感酒类直播间销售视频"),
        )
        run = self.store.create_or_load_run(session_id=str(args.get("session_id") or ""), user_idea=idea, brief=brief)
        task = self.store.start_task(run, agent_name="story_generation_agent", tool_name="alcohol_story_generation", metadata={"idea": idea})
        self._stage(run.session_id, "production_story", "Generating alcohol sales story")
        _progress(runtime, "story_generation", "Expanding idea into sales story", {"run_id": run.run_id})
        story = _sales_story_template(idea, brief)
        material = self.store.add_text_material(run, material_type="story", role="sales_story", content=story, source_agent="story_generation_agent", task_id=task.task_id, prompt=idea, metadata={"brief": brief.model_dump()})
        run.story_material_id = material.material_id
        run.status = "planning"
        run.stage = "story_generated"
        self.store.save_run(run)
        self.store.finish_task(task, output_material_ids=[material.material_id])
        return _ok("alcohol_story_generation", {"run_id": run.run_id, "session_id": run.session_id, "story_material_id": material.material_id, "story_path": material.file_path, "next_tool": "alcohol_script_generation"})

    async def alcohol_script_generation(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        try:
            run = self._load_run(str(args.get("session_id") or ""))
            story_id = str(args.get("story_material_id") or run.story_material_id or "")
            story_material = self._require_material(run.session_id, story_id, "story")
            story = self._read_material_text(run.session_id, story_material)
            task = self.store.start_task(run, agent_name="script_generation_agent", tool_name="alcohol_script_generation", input_material_ids=[story_id])
            self._stage(run.session_id, "production_script", "Generating alcohol live-commerce script")
            _progress(runtime, "script_generation", "Converting story to host script", {"run_id": run.run_id, "story_material_id": story_id})
            duration = int(args.get("duration_target_seconds") or 60)
            script = _sales_script_template(story, run.brief, duration, str(args.get("cta_requirements") or ""), str(args.get("compliance_requirements") or ""))
            material = self.store.add_text_material(run, material_type="sales_script", role="host_script", content=script, source_agent="script_generation_agent", task_id=task.task_id, prompt=story[:500], input_material_ids=[story_id], metadata={"duration_target_seconds": duration})
            run.script_material_id = material.material_id
            run.stage = "script_generated"
            self.store.save_run(run)
            self.store.finish_task(task, output_material_ids=[material.material_id])
            return _ok("alcohol_script_generation", {"run_id": run.run_id, "script_material_id": material.material_id, "script_path": material.file_path, "next_tool": "alcohol_storyboard_generation"})
        except Exception as exc:
            return _error("alcohol_script_generation", str(exc))

    async def alcohol_storyboard_generation(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        try:
            run = self._load_run(str(args.get("session_id") or ""))
            script_id = str(args.get("script_material_id") or run.script_material_id or "")
            script_material = self._require_material(run.session_id, script_id, "sales_script")
            script = self._read_material_text(run.session_id, script_material)
            task = self.store.start_task(run, agent_name="storyboard_generation_agent", tool_name="alcohol_storyboard_generation", input_material_ids=[script_id])
            self._stage(run.session_id, "production_storyboard", "Generating storyboard and shot plan")
            _progress(runtime, "storyboard_generation", "Creating sales storyboard and shot plan", {"run_id": run.run_id, "script_material_id": script_id})
            max_shots = int(args.get("max_shots") or 6)
            aspect_ratio = str(args.get("aspect_ratio") or "9:16")
            storyboard, shot_plan = _storyboard_and_shot_plan(script, run.brief, max_shots, aspect_ratio, str(args.get("visual_style") or ""))
            storyboard_material = self.store.add_text_material(run, material_type="storyboard", role="sales_storyboard", content=json.dumps(storyboard, ensure_ascii=True, indent=2), source_agent="storyboard_generation_agent", task_id=task.task_id, input_material_ids=[script_id], metadata={"aspect_ratio": aspect_ratio}, ext="json")
            shot_material = self.store.add_text_material(run, material_type="shot_plan", role="live_commerce_shot_plan", content=json.dumps(shot_plan, ensure_ascii=True, indent=2), source_agent="storyboard_generation_agent", task_id=task.task_id, input_material_ids=[script_id, storyboard_material.material_id], metadata={"max_shots": max_shots}, ext="json")
            run.storyboard_material_id = storyboard_material.material_id
            run.shot_plan_material_id = shot_material.material_id
            run.stage = "storyboard_generated"
            self.store.save_run(run)
            self.store.finish_task(task, output_material_ids=[storyboard_material.material_id, shot_material.material_id])
            return _ok("alcohol_storyboard_generation", {"run_id": run.run_id, "storyboard_material_id": storyboard_material.material_id, "shot_plan_material_id": shot_material.material_id, "next_tools": ["heygen_live_room_generation", "veo_transition_closeup_generation"]})
        except Exception as exc:
            return _error("alcohol_storyboard_generation", str(exc))

    async def heygen_live_room_generation(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        """Backward-compatible entrypoint for callers that still use the production adapter directly."""
        skill = HeyGenLiveRoomSkills(self.workspace_root, self.session_index)
        return await skill.heygen_live_room_generate_clip(args, runtime)

    async def veo_transition_closeup_generation(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        try:
            run = self._load_run(str(args.get("session_id") or ""))
            input_ids = [item for item in [str(args.get("storyboard_material_id") or run.storyboard_material_id or ""), str(args.get("shot_plan_material_id") or run.shot_plan_material_id or "")] if item]
            task = self.store.start_task(run, agent_name="transition_closeup_video_agent", tool_name="veo_transition_closeup_generation", input_material_ids=input_ids, provider="veo3.1")
            self._stage(run.session_id, "production_veo", "Generating Veo 3.1 transition and close-up clips")
            dry_run = _dry_run(args)
            prompts = [str(item) for item in (args.get("prompts") or []) if str(item).strip()]
            if not prompts:
                prompts = _default_veo_prompts(run.brief, int(args.get("clip_count") or 2))
            materials: list[MaterialRecord] = []
            generator = None if dry_run else self._build_veo_generator()
            for index, prompt in enumerate(prompts[: max(1, int(args.get("clip_count") or len(prompts)))]):
                _progress(runtime, "veo_generate", "Generating product transition/close-up clip", {"run_id": run.run_id, "index": index, "dry_run": dry_run})
                output_path = self.store.production_dir(run.session_id) / "assets" / "clips" / f"veo-{task.task_id}-{index}.mp4"
                if dry_run:
                    output_path.write_bytes(f"VEO_DRY_RUN_CLIP_{index}:{prompt}".encode("utf-8"))
                    provider_job_id = f"veo-dry-run-{index}"
                else:
                    video = await generator.generate_single_video(prompt=prompt, reference_image_paths=[], resolution=str(args.get("resolution") or "1080p"), aspect_ratio=str(args.get("aspect_ratio") or "9:16"), duration=int(args.get("duration") or 6), progress=lambda stage, message, metadata=None: _progress(runtime, stage, message, metadata))
                    video.save(str(output_path))
                    provider_job_id = f"veo-{uuid4().hex[:8]}"
                material = self.store.add_file_material(run, material_type="product_closeup_video" if index % 2 == 0 else "transition_video", role="bottle_closeup" if index % 2 == 0 else "sales_transition", file_path=output_path, source_agent="transition_closeup_video_agent", source_provider="google_veo", provider_model="veo-3.1-generate-preview", provider_job_id=provider_job_id, task_id=task.task_id, prompt=prompt, input_material_ids=input_ids, metadata={"dry_run": dry_run, "aspect_ratio": args.get("aspect_ratio"), "duration": args.get("duration")})
                materials.append(material)
            run.transition_clip_ids.extend([item.material_id for item in materials])
            run.stage = "transition_closeups_generated"
            self.store.save_run(run)
            self.store.finish_task(task, output_material_ids=[item.material_id for item in materials])
            return _ok("veo_transition_closeup_generation", {"run_id": run.run_id, "transition_clip_material_ids": [item.material_id for item in materials], "next_tool": "ffmpeg_video_composition"})
        except Exception as exc:
            return _error("veo_transition_closeup_generation", str(exc))

    async def ffmpeg_video_composition(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        try:
            run = self._load_run(str(args.get("session_id") or ""))
            material_ids = [str(item) for item in (args.get("material_ids") or []) if str(item)] or [*run.digital_human_clip_ids, *run.transition_clip_ids]
            if not material_ids:
                raise RuntimeError("No clip material ids provided for composition")
            materials_by_id = self.store.latest_materials_by_id(run.session_id)
            materials = [materials_by_id[item] for item in material_ids if item in materials_by_id]
            missing = [item for item in material_ids if item not in materials_by_id]
            if missing:
                raise RuntimeError(f"Missing material records for composition: {missing}")
            task = self.store.start_task(run, agent_name="video_composition_agent", tool_name="ffmpeg_video_composition", input_material_ids=material_ids, provider="ffmpeg")
            self._stage(run.session_id, "production_composition", "Composing final sales video")
            dry_run = _dry_run(args)
            output_path = self.store.production_dir(run.session_id) / "assets" / "final" / f"final-{run.run_id}.mp4"
            input_paths = [self.store.resolve_material_path(run.session_id, material) for material in materials]
            manifest = manifest_from_materials(run=run, materials=materials, output_path=str(output_path.relative_to(self.session_index.working_dir(run.session_id))).replace("\\", "/"))
            ok, errors = self.store.validate_manifest_traceability(manifest)
            if not ok:
                raise RuntimeError("Traceability gate failed before composition: " + "; ".join(errors))
            if dry_run:
                output_path.write_bytes(b"FFMPEG_DRY_RUN_FINAL_VIDEO_PLACEHOLDER")
                manifest.ffmpeg_commands.append(FfmpegCommandSummary(argv=["ffmpeg", "dry-run", *[str(path) for path in input_paths], str(output_path)], returncode=0, stderr_preview="dry-run"))
            else:
                _progress(runtime, "ffmpeg_compose", "Running ffmpeg composition", {"input_count": len(input_paths)})
                result = compose_timeline(input_paths, output_path)
                manifest.ffmpeg_commands.append(result.summary())
            final_material = self.store.add_file_material(run, material_type="final_video", role="final_sales_video", file_path=output_path, source_agent="video_composition_agent", source_provider="ffmpeg", provider_model="ffmpeg-cli", task_id=task.task_id, input_material_ids=material_ids, metadata={"dry_run": dry_run}, used_in_final=True)
            for material in materials:
                material.used_in_final = True
                self.store.append_material(material)
            manifest.output_material_id = final_material.material_id
            manifest.output_path = final_material.file_path
            manifest_path = self.store.write_manifest(manifest)
            manifest_material = self.store.add_text_material(run, material_type="composition_manifest", role="traceability_manifest", content=json.dumps(manifest.model_dump(), ensure_ascii=True, indent=2), source_agent="video_composition_agent", task_id=task.task_id, input_material_ids=[*material_ids, final_material.material_id], ext="json")
            run.status = "completed"
            run.stage = "final_video_composed"
            run.final_video_material_id = final_material.material_id
            run.composition_manifest_path = str(manifest_path.relative_to(self.session_index.working_dir(run.session_id))).replace("\\", "/")
            self.store.save_run(run)
            self.store.finish_task(task, output_material_ids=[final_material.material_id, manifest_material.material_id])
            return _ok("ffmpeg_video_composition", {"run_id": run.run_id, "final_video_material_id": final_material.material_id, "composition_manifest_material_id": manifest_material.material_id, "final_video_path": final_material.file_path, "traceability_passed": True})
        except Exception as exc:
            return _error("ffmpeg_video_composition", str(exc))

    async def production_run_status(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        try:
            run = self._load_run(str(args.get("session_id") or ""))
            materials = self.store.load_materials(run.session_id)
            manifest_status: dict[str, Any] = {"exists": False}
            try:
                manifest = self.store.load_manifest(run.session_id)
                ok, errors = self.store.validate_manifest_traceability(manifest)
                manifest_status = {"exists": True, "traceability_passed": ok, "errors": errors}
            except FileNotFoundError:
                pass
            return _ok("production_run_status", {"run": run.model_dump(), "material_count": len(materials), "materials": [item.model_dump() for item in materials[-20:]], "manifest": manifest_status})
        except Exception as exc:
            return _error("production_run_status", str(exc))

    async def production_performance_ingest(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        try:
            run = self._load_run(str(args.get("session_id") or ""))
            payload = {
                "platform": str(args.get("platform") or ""),
                "platform_video_id": str(args.get("platform_video_id") or ""),
                "published_url": str(args.get("published_url") or ""),
                "views": int(args.get("views") or 0),
                "clicks": int(args.get("clicks") or 0),
                "orders": int(args.get("orders") or 0),
                "gmv": _float(args.get("gmv")),
                "roi": _float(args.get("roi")),
                "conversion_rate": _float(args.get("conversion_rate")),
                "completion_rate": _float(args.get("completion_rate")),
            }
            metric = self.store.add_performance_metric(run, payload)
            pattern = self.store.maybe_create_reusable_pattern(run, metric)
            run.performance_summary = {"latest_metric_id": metric.metric_id, "score": metric.score, "platform": metric.platform}
            if pattern:
                run.reusable_pattern_ids.append(pattern.pattern_id)
            self.store.save_run(run)
            return _ok("production_performance_ingest", {"metric": metric.model_dump(), "reusable_pattern": pattern.model_dump() if pattern else None})
        except Exception as exc:
            return _error("production_performance_ingest", str(exc))

    async def production_reusable_patterns_search(self, args: dict[str, Any], runtime: ToolRuntimeContext | None = None) -> ToolResult:
        patterns = self.store.search_reusable_patterns(str(args.get("query") or ""), int(args.get("limit") or 5))
        return _ok("production_reusable_patterns_search", {"patterns": [item.model_dump() for item in patterns]})

    def _load_run(self, session_id: str = ""):
        return self.store.load_run(session_id or None)

    def _require_material(self, session_id: str, material_id: str, expected_type: str = "") -> MaterialRecord:
        if not material_id:
            raise RuntimeError(f"Missing material id for expected type: {expected_type}")
        material = self.store.latest_materials_by_id(session_id).get(material_id)
        if material is None:
            raise RuntimeError(f"Unknown material id: {material_id}")
        if expected_type and material.material_type != expected_type:
            raise RuntimeError(f"Material {material_id} is {material.material_type}, expected {expected_type}")
        return material

    def _read_material_text(self, session_id: str, material: MaterialRecord) -> str:
        path = self.store.resolve_material_path(session_id, material)
        return path.read_text(encoding="utf-8")

    def _stage(self, session_id: str, stage: str, summary: str) -> None:
        try:
            self.session_index.update_stage(session_id, stage, summary)
        except Exception:
            pass

    def _build_veo_generator(self):
        api_key = video_api_key(self.workspace_root)
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY, GOOGLE_API_KEY, or VIMAX_VIDEO_API_KEY is required for real Veo 3.1 generation. Set dry_run=true for a local dry run.")
        model = video_model(self.workspace_root)
        return VideoGeneratorVeoGoogleAPI(api_key=api_key, t2v_model=model, ff2v_model=model, flf2v_model=model, base_url=video_base_url(self.workspace_root))


def _sales_story_template(idea: str, brief: AlcoholSalesBrief) -> str:
    product = brief.product_name or brief.product_brief or "这款酒"
    audience = brief.target_audience or "成熟理性的酒类消费者"
    goal = brief.sales_goal or "建立信任并推动下单"
    return (
        f"酒类直播销售故事：围绕「{idea}」展开。\n"
        f"产品主角：{product}。品牌：{brief.brand or '待补充'}。\n"
        f"目标人群：{audience}。销售目标：{goal}。\n"
        "故事结构：1）三秒开场用真实消费场景提出购买理由；2）主播用克制可信的方式讲产地、口感、包装和送礼/宴请场景；"
        "3）穿插酒瓶、酒标、倒酒、礼盒和直播间福利特写；4）以限时权益和理性饮酒提示收束。\n"
        "合规底线：不面向未成年人，不暗示过量饮酒，不宣传医疗保健功效，不鼓励危险行为。"
    )


def _sales_script_template(story: str, brief: AlcoholSalesBrief, duration: int, cta: str, compliance: str) -> str:
    product = brief.product_name or brief.product_brief or "这款酒"
    return (
        f"# 酒类直播销售脚本（目标 {duration}s）\n\n"
        "## Segment 1 / 开场钩子\n"
        f"主播：如果你正在找一款适合宴请、送礼或自饮的酒，先看这款 {product} 的三个细节。\n\n"
        "## Segment 2 / 信任背书\n"
        f"主播：它的核心卖点来自：{brief.product_brief or '产地、工艺、口感和包装质感'}。我们不夸张承诺，只讲你能看见、能比较的地方。\n\n"
        "## Segment 3 / 视觉特写\n"
        "镜头：酒瓶标签 macro、瓶身反光、倒酒入杯、礼盒陈列、直播间价格权益卡。\n\n"
        "## Segment 4 / 转化 CTA\n"
        f"主播：{cta or '需要的朋友可以先领券看规格，按需购买，理性饮酒。'}\n\n"
        "## Compliance Notes\n"
        f"{compliance or '不得面向未成年人；不得宣传医疗功效；不得鼓励过量饮酒；需提示理性饮酒。'}\n\n"
        "## Source Story\n"
        f"{story}\n"
    )


def _storyboard_and_shot_plan(script: str, brief: AlcoholSalesBrief, max_shots: int, aspect_ratio: str, visual_style: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    product = brief.product_name or brief.product_brief or "酒类产品"
    base = [
        ("hook", "数字人主播正面进入直播间，三秒内讲清购买场景", "heygen"),
        ("bottle_closeup", f"{product} 瓶身和酒标高质感 macro 特写", "veo"),
        ("pouring", "倒酒入杯，展示酒液颜色和杯壁质感", "veo"),
        ("trust", "主播解释产地、工艺、包装和适用场景", "heygen"),
        ("offer", "礼盒、权益卡、限时福利和库存提示转场", "veo"),
        ("cta", "主播收束 CTA，并提示理性饮酒", "heygen"),
    ][: max(1, max_shots)]
    storyboard = []
    shot_plan = []
    for idx, (purpose, visual, worker) in enumerate(base):
        storyboard.append({"idx": idx, "purpose": purpose, "visual": visual, "aspect_ratio": aspect_ratio, "style": visual_style or "高质感酒类直播间", "worker": worker})
        shot_plan.append({"shot_id": f"shot-{idx}", "purpose": purpose, "required_worker": worker, "key_selling_point": product, "overlay_text": "理性饮酒" if purpose == "cta" else "", "estimated_duration": 6 if worker == "veo" else 10})
    return storyboard, shot_plan


def _extract_host_lines(script_text: str) -> str:
    lines = []
    for line in script_text.splitlines():
        if "主播" in line or line.startswith("## Segment"):
            lines.append(line)
    return "\n".join(lines).strip() or script_text[:1500]


def _default_veo_prompts(brief: AlcoholSalesBrief, count: int) -> list[str]:
    product = brief.product_name or brief.product_brief or "premium Chinese liquor bottle"
    prompts = [
        f"Vertical 9:16 luxury live-commerce macro close-up of {product}, clean studio lighting, bottle label sharp, premium reflections, no minors, responsible drinking tone.",
        f"Vertical 9:16 cinematic pouring shot for {product}, amber liquid into glass, elegant gift-box background, smooth transition for live sales video.",
        f"Vertical 9:16 product shelf transition: {product} gift box, coupon card, livestream room lights, premium but restrained commercial style.",
    ]
    return prompts[: max(1, count)]


def _dry_run(args: dict[str, Any]) -> bool:
    return bool(args.get("dry_run")) or os.environ.get(DRY_RUN_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _progress(runtime: ToolRuntimeContext | None, stage: str, message: str, metadata: dict[str, Any] | None = None) -> None:
    if runtime:
        runtime.emit_progress(message, stage=stage, metadata=metadata or {})


def _float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _ok(name: str, payload: dict[str, Any]) -> ToolResult:
    return ToolResult(name, True, json.dumps(payload, ensure_ascii=True, indent=2), payload)


def _error(name: str, message: str, error_type: str = "exception") -> ToolResult:
    return ToolResult(name, False, message, {"error_type": error_type})
