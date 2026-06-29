from __future__ import annotations

import json
from pathlib import Path
import os
import re
from typing import Any

from agent_runtime.agent_company import build_default_agent_company
from agent_runtime.config import image_api_key, image_base_url, video_api_key, video_base_url
from interfaces.production import utc_now_iso
from apps.api.app.core.logging import get_logger
from apps.api.app.domain.workbench.entities import (
    AgentProfile,
    AgentRun,
    Asset,
    AvatarJob,
    AvatarProfile,
    BestPractice,
    ComponentVersion,
    KnowledgeChunk,
    KnowledgeDocument,
    LiveComponent,
    LiveRoomComposition,
    LiveRoomTemplate,
    LiveScene,
    LiveSessionSnapshot,
    ModelProviderConfig,
    MvpLivePlan,
    PerformanceMetric,
    PlatformAccount,
    PlatformEvent,
    PlatformMetricSnapshot,
    PluginProvider,
    ProductRecord,
    Project,
    PromptTemplate,
    PromptVersion,
    ScriptTemplate,
    WorkflowDefinition,
    WorkflowNodeRun,
    WorkflowRule,
    WorkflowRun,
)
from apps.api.app.infrastructure.media_generation import generate_jimeng_video, generate_openai_image
from apps.api.app.infrastructure.repositories.file_workbench import JsonCollectionRepository
from apps.api.app.plugins.registry import build_plugin_manager

logger = get_logger(__name__)


class WorkbenchService:
    def __init__(self, workspace_root: str | Path = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.products = JsonCollectionRepository(self.workspace_root, "products", ProductRecord, "product_id")
        self.avatars = JsonCollectionRepository(self.workspace_root, "avatars", AvatarProfile, "avatar_id")
        self.scripts = JsonCollectionRepository(self.workspace_root, "scripts", ScriptTemplate, "template_id")
        self.workflow_rules = JsonCollectionRepository(self.workspace_root, "workflow_rules", WorkflowRule, "rule_id")
        self.platform_accounts = JsonCollectionRepository(self.workspace_root, "platform_accounts", PlatformAccount, "account_id")
        self.metrics = JsonCollectionRepository(self.workspace_root, "platform_metrics", PlatformMetricSnapshot, "snapshot_id")
        self.knowledge_documents = JsonCollectionRepository(self.workspace_root, "knowledge_documents", KnowledgeDocument, "document_id")
        self.knowledge_chunks = JsonCollectionRepository(self.workspace_root, "knowledge_chunks", KnowledgeChunk, "chunk_id")
        self.model_providers = JsonCollectionRepository(self.workspace_root, "model_providers", ModelProviderConfig, "provider_id")
        self.prompt_templates = JsonCollectionRepository(self.workspace_root, "prompt_templates", PromptTemplate, "prompt_id")
        self.avatar_jobs = JsonCollectionRepository(self.workspace_root, "avatar_jobs", AvatarJob, "job_id")
        self.platform_events = JsonCollectionRepository(self.workspace_root, "platform_events", PlatformEvent, "event_id")

        self.projects = JsonCollectionRepository(self.workspace_root, "projects", Project, "project_id")
        self.agent_profiles = JsonCollectionRepository(self.workspace_root, "agent_profiles", AgentProfile, "agent_id")
        self.agent_runs = JsonCollectionRepository(self.workspace_root, "agent_runs", AgentRun, "run_id")
        self.assets = JsonCollectionRepository(self.workspace_root, "assets", Asset, "asset_id")
        self.components = JsonCollectionRepository(self.workspace_root, "components", LiveComponent, "component_id")
        self.component_versions = JsonCollectionRepository(self.workspace_root, "component_versions", ComponentVersion, "version_id")
        self.live_room_templates = JsonCollectionRepository(self.workspace_root, "live_room_templates", LiveRoomTemplate, "template_id")
        self.live_scenes = JsonCollectionRepository(self.workspace_root, "live_scenes", LiveScene, "scene_id")
        self.live_room_compositions = JsonCollectionRepository(self.workspace_root, "live_room_compositions", LiveRoomComposition, "composition_id")
        self.live_session_snapshots = JsonCollectionRepository(self.workspace_root, "live_session_snapshots", LiveSessionSnapshot, "snapshot_id")
        self.performance_metrics = JsonCollectionRepository(self.workspace_root, "performance_metrics", PerformanceMetric, "metric_id")
        self.best_practices = JsonCollectionRepository(self.workspace_root, "best_practices", BestPractice, "best_practice_id")
        self.prompt_versions = JsonCollectionRepository(self.workspace_root, "prompt_versions", PromptVersion, "prompt_version_id")
        self.mvp_live_plans = JsonCollectionRepository(self.workspace_root, "mvp_live_plans", MvpLivePlan, "plan_id")
        self.workflow_definitions = JsonCollectionRepository(self.workspace_root, "workflow_definitions", WorkflowDefinition, "workflow_definition_id")
        self.workflow_runs = JsonCollectionRepository(self.workspace_root, "workflow_runs", WorkflowRun, "workflow_run_id")
        self.workflow_node_runs = JsonCollectionRepository(self.workspace_root, "workflow_node_runs", WorkflowNodeRun, "node_run_id")
        self.plugin_providers = JsonCollectionRepository(self.workspace_root, "plugin_providers", PluginProvider, "plugin_id")
        self.plugin_manager = build_plugin_manager(self.workspace_root)
        self._ensure_seed_data()

    def dashboard_summary(self) -> dict[str, Any]:
        latest_metric = self.metrics.list()[-1] if self.metrics.list() else PlatformMetricSnapshot(
            online_users=1286,
            gmv=68420,
            order_count=329,
            interaction_rate=0.186,
            conversion_rate=0.042,
            current_product_id=self.products.list()[0].product_id if self.products.list() else "",
        )
        current_product = None
        if latest_metric.current_product_id:
            try:
                current_product = self.products.get(latest_metric.current_product_id)
            except KeyError:
                current_product = None
        agents = self.agent_profiles.list()
        active_agents = [agent for agent in agents if agent.status == "working"]
        return {
            "online_users": latest_metric.online_users,
            "current_gmv": latest_metric.gmv,
            "today_revenue": latest_metric.gmv,
            "order_count": latest_metric.order_count,
            "interaction_rate": latest_metric.interaction_rate,
            "conversion_rate": latest_metric.conversion_rate,
            "current_product": current_product.model_dump() if current_product else None,
            "avatar_status": "ready" if self.avatars.list() else "not_configured",
            "live_status": "running",
            "project_count": len(self.projects.list()),
            "active_agent_count": len(active_agents),
            "component_count": len(self.components.list()),
            "workflow_run_count": len(self.workflow_runs.list()),
        }

    def create_product(self, payload: dict[str, Any]) -> ProductRecord:
        return self.products.upsert(ProductRecord.model_validate(payload))

    def update_product(self, product_id: str, payload: dict[str, Any]) -> ProductRecord:
        product = self.products.get(product_id)
        updated = product.model_copy(update={**payload, "updated_at": utc_now_iso()})
        return self.products.upsert(updated)

    def publish_product(self, product_id: str) -> ProductRecord:
        return self.update_product(product_id, {"status": "published"})

    def unpublish_product(self, product_id: str) -> ProductRecord:
        return self.update_product(product_id, {"status": "draft"})

    def create_avatar(self, payload: dict[str, Any]) -> AvatarProfile:
        return self.avatars.upsert(AvatarProfile.model_validate(payload))

    def update_avatar(self, avatar_id: str, payload: dict[str, Any]) -> AvatarProfile:
        avatar = self.avatars.get(avatar_id)
        updated = avatar.model_copy(update={**payload, "updated_at": utc_now_iso()})
        return self.avatars.upsert(updated)

    def create_script(self, payload: dict[str, Any]) -> ScriptTemplate:
        return self.scripts.upsert(ScriptTemplate.model_validate(payload))

    def update_script(self, template_id: str, payload: dict[str, Any]) -> ScriptTemplate:
        template = self.scripts.get(template_id)
        updated = template.model_copy(update={**payload, "updated_at": utc_now_iso()})
        return self.scripts.upsert(updated)

    def generate_script(self, category: str, product_id: str = "") -> ScriptTemplate:
        product_name = "这款酒"
        if product_id:
            try:
                product_name = self.products.get(product_id).product_name
            except KeyError:
                pass
        templates = {
            "opening": f"欢迎来到直播间，今天给大家重点介绍{product_name}，适合成年人节日送礼和商务宴请场景，大家按需理性选择。",
            "product": f"{product_name}主打礼盒包装、宴请送礼和成熟消费者聚会场景，具体规格和权益以直播间页面为准。",
            "sales": f"如果你正在考虑成年人节日拜访或商务宴请，可以关注{product_name}当前组合权益，理性下单、按需选择。",
            "interaction": f"大家有价格、香型、规格、送礼场景的问题都可以打在公屏，我会逐个说明{product_name}的适用场景。",
            "thanks": f"感谢支持{product_name}，也提醒大家酒类产品只面向成年人，请适量饮酒、理性消费。",
        }
        return self.create_script({
            "name": f"AI生成-{category}",
            "category": category,
            "content": templates.get(category, templates["interaction"]),
            "product_id": product_id,
            "ai_generated": True,
            "tags": ["酒类合规", "AI生成"],
        })

    def create_knowledge_document(self, payload: dict[str, Any]) -> KnowledgeDocument:
        return self.knowledge_documents.upsert(KnowledgeDocument.model_validate(payload))

    def index_knowledge_document(self, document_id: str, text: str = "") -> KnowledgeDocument:
        document = self.knowledge_documents.get(document_id)
        source_text = text.strip() or f"{document.name} 商品资料：适合成年人商务宴请、节日送礼和聚会场景。酒类产品不宣传医疗保健功效。"
        chunks = _split_knowledge_text(source_text)
        existing = [chunk for chunk in self.knowledge_chunks.list() if chunk.document_id != document_id]
        for index, chunk_text in enumerate(chunks):
            existing.append(KnowledgeChunk(document_id=document_id, product_id=document.product_id, chunk_index=index, text=chunk_text, embedding_status="embedded", metadata={"source_type": document.source_type, "retrieval": "keyword_v1"}))
        self.knowledge_chunks._write(existing)
        updated = document.model_copy(update={"status": "indexed", "chunk_count": len(chunks), "updated_at": utc_now_iso()})
        return self.knowledge_documents.upsert(updated)

    def search_knowledge(self, query: str, product_id: str = "", limit: int = 5) -> list[KnowledgeChunk]:
        return [item["chunk"] for item in self.search_knowledge_with_scores(query, product_id=product_id, limit=limit)]

    def search_knowledge_with_scores(self, query: str, product_id: str = "", limit: int = 5) -> list[dict[str, Any]]:
        query_terms = _tokenize_knowledge_query(query)
        chunks = self.knowledge_chunks.list()
        if product_id:
            chunks = [chunk for chunk in chunks if chunk.product_id in {"", product_id}]
        scored: list[tuple[float, KnowledgeChunk, list[str]]] = []
        for chunk in chunks:
            score, matched_terms = _score_knowledge_chunk(query_terms, chunk.text)
            if score > 0 or not query_terms:
                scored.append((score, chunk, matched_terms))
        scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
        return [
            {"score": score, "matched_terms": matched_terms, "chunk": chunk}
            for score, chunk, matched_terms in scored[: max(1, min(limit, 20))]
        ]

    def create_avatar_job(self, payload: dict[str, Any]) -> AvatarJob:
        job = AvatarJob.model_validate(payload)
        if not job.provider_job_id:
            job = job.model_copy(update={"provider_job_id": "heygen-dry-run", "status": "succeeded", "output_url": f"minio://avatar-jobs/{job.job_id}.mp4", "updated_at": utc_now_iso()})
        return self.avatar_jobs.upsert(job)

    def ingest_platform_event(self, payload: dict[str, Any]) -> PlatformEvent:
        event = PlatformEvent.model_validate(payload)
        self.platform_events.upsert(event)
        return event

    def create_project(self, payload: dict[str, Any]) -> Project:
        return self.projects.upsert(Project.model_validate(payload))

    def update_project(self, project_id: str, payload: dict[str, Any]) -> Project:
        project = self.projects.get(project_id)
        return self.projects.upsert(project.model_copy(update={**payload, "updated_at": utc_now_iso()}))

    def list_mvp_live_plans(self, project_id: str = "") -> list[MvpLivePlan]:
        plans = _filter_by_project(self.mvp_live_plans.list(), project_id)
        return sorted(plans, key=lambda item: item.updated_at, reverse=True)

    def get_mvp_live_plan(self, plan_id: str) -> MvpLivePlan:
        return self.mvp_live_plans.get(plan_id)

    def run_mvp_live_commerce(self, payload: dict[str, Any]) -> MvpLivePlan:
        product = self._resolve_mvp_product(payload)
        project = self._resolve_mvp_project(payload, product)
        brand_analysis = _mvp_brand_analysis(product, payload)
        script = self.generate_script("sales", product.product_id)
        script = self.update_script(script.template_id, {
            "name": f"MVP数字人口播-{product.product_name}",
            "content": _mvp_script_content(product, brand_analysis, str(payload.get("script_note") or "")),
            "tags": ["Phase9", "MVP", "数字人口播", "酒类合规"],
        })
        avatar = self._resolve_mvp_avatar(payload)
        composition = self._ensure_mvp_live_room(project, product, brand_analysis)
        plan = MvpLivePlan(project_id=project.project_id, product_id=product.product_id)

        tts_job = self._submit_mvp_tts_job({
            "text": script.content,
            "voice": avatar.voice_name or "zh-CN-XiaoxiaoNeural",
            "product_id": product.product_id,
            "plan_id": plan.plan_id,
            "tts_provider": payload.get("tts_provider"),
        })
        speech_uri = tts_job.get("output_uri") or f"minio://mvp-plans/{plan.plan_id}/speech/{tts_job.get('job_id', 'tts')}.wav"
        avatar_job = self.create_avatar_job({
            "avatar_id": avatar.avatar_id,
            "job_type": "text_drive",
            "input_text": script.content,
            "input_audio_url": speech_uri,
        })
        avatar_video_uri = avatar_job.output_url or f"minio://mvp-plans/{plan.plan_id}/avatar/{avatar_job.job_id}.mp4"
        video_job = self.submit_plugin_job("ffmpeg_moviepy", {
            "duration_seconds": max(15, min(180, len(script.content) // 5)),
            "script_template_id": script.template_id,
            "avatar_video_uri": avatar_video_uri,
            "live_room_composition_id": composition.composition_id,
            "product_id": product.product_id,
            "plan_id": plan.plan_id,
        })
        live_video_uri = video_job.get("output_uri") or f"minio://mvp-plans/{plan.plan_id}/video/{video_job.get('job_id', 'live-video')}.mp4"

        workflow_def = self._ensure_phase_nine_mvp_workflow_definition()
        workflow_run = self.workflow_runs.upsert(WorkflowRun(
            project_id=project.project_id,
            workflow_definition_id=workflow_def.workflow_definition_id,
            status="succeeded",
            progress=1,
            current_node_id="saved_plan",
            input_payload={"product_id": product.product_id, "plan_id": plan.plan_id, "source": "phase9_mvp"},
            output_payload={
                "plan_id": plan.plan_id,
                "script_template_id": script.template_id,
                "avatar_job_id": avatar_job.job_id,
                "live_room_composition_id": composition.composition_id,
                "live_video_uri": live_video_uri,
            },
            logs=[
                "上传商品已进入 MVP 流程",
                "品牌分析、剧本、口播、数字人、直播视频已串联",
                "直播方案已保存，可在 MVP 页面复用",
            ],
            token_count=4200,
            cost_estimate=0,
            duration_seconds=96,
            updated_at=utc_now_iso(),
        ))
        steps = _mvp_steps(product, brand_analysis, script, avatar, avatar_job, composition, speech_uri, live_video_uri, plan.plan_id, tts_job)
        self._write_mvp_node_runs(workflow_run, workflow_def, steps, script.template_id)
        saved_outputs = {
            "project_id": project.project_id,
            "product_id": product.product_id,
            "script_template_id": script.template_id,
            "tts_job": tts_job,
            "avatar_job_id": avatar_job.job_id,
            "video_job": video_job,
            "live_room_composition_id": composition.composition_id,
            "plan_uri": f"minio://mvp-plans/{plan.plan_id}/plan.json",
        }
        plan = plan.model_copy(update={
            "workflow_run_id": workflow_run.workflow_run_id,
            "script_template_id": script.template_id,
            "avatar_id": avatar.avatar_id,
            "avatar_job_id": avatar_job.job_id,
            "live_room_composition_id": composition.composition_id,
            "steps": steps,
            "product_snapshot": product.model_dump(),
            "brand_analysis": brand_analysis,
            "script_snapshot": script.model_dump(),
            "speech_artifact_uri": speech_uri,
            "avatar_video_uri": avatar_video_uri,
            "live_video_uri": live_video_uri,
            "saved_outputs": saved_outputs,
            "metadata": {"phase": "phase9_mvp", "workflow": "product_to_saved_live_plan", "principle": "reuse_existing_plugins"},
            "updated_at": utc_now_iso(),
        })
        saved = self.mvp_live_plans.upsert(plan)
        self._attach_mvp_plan_to_project(project, product, saved)
        logger.info("Phase 9 MVP live plan saved", extra={"plan_id": saved.plan_id, "project_id": project.project_id, "product_id": product.product_id})
        return saved

    def run_product_video_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot = self.create_product_video_workflow_run(payload)
        workflow_run_id = str(snapshot["run"]["workflow_run_id"])
        for node in snapshot["definition"]["nodes"]:
            snapshot = self.run_product_video_workflow_node(workflow_run_id, str(node["id"]))
        return snapshot

    def create_product_video_workflow_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        product = self._resolve_video_product(payload)
        project = self._resolve_video_project(payload, product)
        brand_name = _video_brand_name(payload, project, product)
        workflow_def = self._ensure_product_video_workflow_definition()
        workflow_run = self.workflow_runs.upsert(WorkflowRun(
            project_id=project.project_id,
            workflow_definition_id=workflow_def.workflow_definition_id,
            status="running",
            progress=0,
            current_node_id=str(workflow_def.nodes[0]["id"]),
            input_payload={
                "project_id": project.project_id,
                "product_id": product.product_id,
                "brand_name": brand_name,
                "workflow": "product_brand_to_complete_video",
                "request": _sanitize_workflow_payload(payload),
            },
            logs=["商品/品牌资料已进入端到端视频生产工作流", "等待 n8n 或 Tavern 控制台逐节点执行"],
        ))
        self._product_video_artifact_root(workflow_run.workflow_run_id).mkdir(parents=True, exist_ok=True)
        self._ensure_product_video_node_placeholders(workflow_run, workflow_def)
        return self.get_product_video_workflow_snapshot(workflow_run.workflow_run_id)

    def run_product_video_workflow_node(self, workflow_run_id: str, node_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        workflow_run = self.workflow_runs.get(workflow_run_id)
        workflow_def = self._product_video_definition_for_run(workflow_run)
        node_ids = [str(node["id"]) for node in workflow_def.nodes]
        if node_id not in node_ids:
            raise ValueError(f"Unknown product video workflow node: {node_id}")
        self._ensure_product_video_node_placeholders(workflow_run, workflow_def)
        node_index = node_ids.index(node_id)
        product = self.products.get(str(workflow_run.input_payload.get("product_id") or ""))
        project = self.projects.get(str(workflow_run.input_payload.get("project_id") or ""))
        request = dict(workflow_run.input_payload.get("request") or {})
        request.update(_sanitize_workflow_payload(payload))
        brand_name = str(workflow_run.input_payload.get("brand_name") or _video_brand_name(request, project, product))
        artifact_root = self._product_video_artifact_root(workflow_run.workflow_run_id)
        artifact_root.mkdir(parents=True, exist_ok=True)

        data, artifact_uri, final_video = self._execute_product_video_stage(node_id, workflow_run, workflow_def, product, project, brand_name, request, artifact_root)
        node_def = workflow_def.nodes[node_index]
        existing_node_run = self._get_product_video_node_run(workflow_run.workflow_run_id, node_id)
        node_run = WorkflowNodeRun(
            workflow_run_id=workflow_run.workflow_run_id,
            node_id=node_id,
            name=str(node_def.get("label")),
            agent_id=str(node_def.get("agent")),
            status="succeeded",
            input_payload={
                "upstream": workflow_def.nodes[node_index - 1]["id"] if node_index else "operator",
                "workflow": "product_brand_to_complete_video",
                "provider_config": _product_video_provider_config(node_id),
            },
            output_payload={"artifact": node_def.get("artifact", ""), "artifact_uri": artifact_uri, "data": data},
            prompt_version_id=str(data.get("script_template_id") or "") if node_id == "script" else "",
            logs=[f"{node_def.get('label')} 已完成", f"产物：{node_def.get('artifact', '')}", f"Provider：{_product_video_provider_config(node_id)['provider']}"],
            token_count=int(data.get("token_count") or (900 if node_def.get("reusable", True) else 300)),
            duration_seconds=float(data.get("duration_seconds") or (8 + node_index * 2)),
            completed_at=utc_now_iso(),
        )
        if existing_node_run:
            node_run = node_run.model_copy(update={"node_run_id": existing_node_run.node_run_id, "started_at": existing_node_run.started_at})
        node_run = self.workflow_node_runs.upsert(node_run)
        self._write_product_video_agent_run(project, workflow_run, node_def, node_run)

        completed_count = len([node for node in self._product_video_node_runs(workflow_run.workflow_run_id, workflow_def) if node.status == "succeeded"])
        is_done = completed_count >= len(workflow_def.nodes)
        next_node_id = node_ids[min(node_index + 1, len(node_ids) - 1)]
        output_payload = dict(workflow_run.output_payload)
        artifacts = dict(output_payload.get("artifacts") or {})
        artifacts[node_id] = artifact_uri
        output_payload.update({"product_id": product.product_id, "brand_name": brand_name, "artifacts": artifacts})
        if final_video:
            output_payload["final_video"] = final_video
            artifacts["complete_video"] = str(final_video.get("uri") or "")
            artifacts["final_video"] = str(final_video.get("uri") or "")
        workflow_run = self.workflow_runs.upsert(workflow_run.model_copy(update={
            "status": "succeeded" if is_done else "running",
            "progress": round(completed_count / len(workflow_def.nodes), 4),
            "current_node_id": node_id if is_done else next_node_id,
            "output_payload": output_payload,
            "logs": [*workflow_run.logs, f"{node_def.get('label')} 已输出 {node_def.get('artifact', '')}"][-12:],
            "token_count": workflow_run.token_count + node_run.token_count,
            "duration_seconds": workflow_run.duration_seconds + node_run.duration_seconds,
            "updated_at": utc_now_iso(),
        }))
        if final_video:
            metadata = dict(project.metadata)
            metadata["latest_product_video_workflow_run_id"] = workflow_run.workflow_run_id
            metadata["latest_complete_video_uri"] = str(final_video.get("uri") or "")
            metadata["product_ids"] = _unique_strings([*metadata.get("product_ids", []), product.product_id])
            self.projects.upsert(project.model_copy(update={"metadata": metadata, "updated_at": utc_now_iso()}))
        return self.get_product_video_workflow_snapshot(workflow_run.workflow_run_id)

    def get_product_video_workflow_snapshot(self, workflow_run_id: str) -> dict[str, Any]:
        workflow_run = self.workflow_runs.get(workflow_run_id)
        workflow_def = self._product_video_definition_for_run(workflow_run)
        nodes = self._product_video_node_runs(workflow_run.workflow_run_id, workflow_def)
        product = self.products.get(str(workflow_run.input_payload.get("product_id") or ""))
        project = self.projects.get(str(workflow_run.input_payload.get("project_id") or ""))
        return {
            "definition": workflow_def.model_dump(),
            "run": workflow_run.model_dump(),
            "nodes": [node.model_dump() for node in nodes],
            "project": project.model_dump(),
            "product": product.model_dump(),
            "final_video": workflow_run.output_payload.get("final_video", {}),
            "artifacts": workflow_run.output_payload.get("artifacts", {}),
        }

    def _resolve_video_product(self, payload: dict[str, Any]) -> ProductRecord:
        product_id = str(payload.get("product_id") or "")
        if product_id:
            product = self.products.get(product_id)
            return product if product.status == "published" else self.publish_product(product.product_id)
        product_payload = payload.get("product") if isinstance(payload.get("product"), dict) else payload.get("product_profile") if isinstance(payload.get("product_profile"), dict) else None
        if product_payload:
            product = self.create_product({
                "product_name": str(product_payload.get("product_name") or product_payload.get("name") or "完整视频商品"),
                "sku": str(product_payload.get("sku") or f"VIDEO-{len(self.products.list()) + 1:03d}"),
                "price": float(product_payload.get("price") or 0),
                "original_price": float(product_payload.get("original_price") or product_payload.get("price") or 0),
                "aroma_type": str(product_payload.get("aroma_type") or product_payload.get("category") or ""),
                "alcohol_degree": str(product_payload.get("alcohol_degree") or ""),
                "volume": str(product_payload.get("volume") or ""),
                "selling_points": _string_list(product_payload.get("selling_points") or product_payload.get("selling_point") or []),
                "scenes": _string_list(product_payload.get("scenes") or product_payload.get("scene") or []),
                "faqs": product_payload.get("faqs") or [],
                "status": "published",
            })
            return product
        return self._resolve_mvp_product(payload)

    def _resolve_video_project(self, payload: dict[str, Any], product: ProductRecord) -> Project:
        project_id = str(payload.get("project_id") or "")
        if project_id:
            project = self.projects.get(project_id)
        else:
            project_payload = payload.get("project") if isinstance(payload.get("project"), dict) else {}
            brand_name = str(payload.get("brand_name") or project_payload.get("brand_name") or product.product_name)
            project = self.create_project({
                "name": str(project_payload.get("name") or f"{product.product_name} 完整视频生产项目"),
                "brand_name": brand_name,
                "industry": str(project_payload.get("industry") or "直播电商短视频"),
                "objective": str(project_payload.get("objective") or "商品/品牌资料到完整视频的端到端自动生产"),
                "tags": _unique_strings([*(_string_list(project_payload.get("tags") or [])), "完整视频", "n8n", "Agent Workflow"]),
                "metadata": dict(project_payload.get("metadata") or {}),
            })
        metadata = dict(project.metadata)
        metadata["product_ids"] = _unique_strings([*metadata.get("product_ids", []), product.product_id])
        metadata["workflow"] = "product_brand_to_complete_video"
        return self.projects.upsert(project.model_copy(update={"metadata": metadata, "updated_at": utc_now_iso()}))

    def _ensure_product_video_workflow_definition(self) -> WorkflowDefinition:
        nodes = _product_video_workflow_nodes()
        edges = [{"source": nodes[index]["id"], "target": nodes[index + 1]["id"], "type": "handoff"} for index in range(len(nodes) - 1)]
        payload = {
            "name": "Product/Brand-to-Complete-Video Workflow",
            "version": "product-video-v1",
            "description": "商品/品牌资料→Planner Agent→Story Agent→Script Agent→Director Agent→Visual Director Agent→Asset Agent→Image Agent→Video Agent→Editor Agent→完整视频的端到端生产链路。",
            "nodes": nodes,
            "edges": edges,
            "status": "active",
            "updated_at": utc_now_iso(),
        }
        for definition in self.workflow_definitions.list():
            if definition.version == "product-video-v1":
                return self.workflow_definitions.upsert(definition.model_copy(update=payload))
        return self.workflow_definitions.upsert(WorkflowDefinition(**payload))

    def _product_video_definition_for_run(self, workflow_run: WorkflowRun) -> WorkflowDefinition:
        if workflow_run.workflow_definition_id:
            try:
                return self.workflow_definitions.get(workflow_run.workflow_definition_id)
            except KeyError:
                pass
        return self._ensure_product_video_workflow_definition()

    def _product_video_artifact_root(self, workflow_run_id: str) -> Path:
        return self.workspace_root / ".working_dir" / "workbench" / "video_workflows" / workflow_run_id

    def _product_video_node_runs(self, workflow_run_id: str, workflow_def: WorkflowDefinition) -> list[WorkflowNodeRun]:
        node_order = {str(node["id"]): index for index, node in enumerate(workflow_def.nodes)}
        nodes = [node for node in self.workflow_node_runs.list() if node.workflow_run_id == workflow_run_id and node.node_id in node_order]
        return sorted(nodes, key=lambda node: node_order.get(node.node_id, 999))

    def _get_product_video_node_run(self, workflow_run_id: str, node_id: str) -> WorkflowNodeRun | None:
        for node in self.workflow_node_runs.list():
            if node.workflow_run_id == workflow_run_id and node.node_id == node_id:
                return node
        return None

    def _ensure_product_video_node_placeholders(self, workflow_run: WorkflowRun, workflow_def: WorkflowDefinition) -> None:
        existing_node_ids = {node.node_id for node in self._product_video_node_runs(workflow_run.workflow_run_id, workflow_def)}
        for index, node in enumerate(workflow_def.nodes):
            node_id = str(node["id"])
            if node_id in existing_node_ids:
                continue
            self.workflow_node_runs.upsert(WorkflowNodeRun(
                workflow_run_id=workflow_run.workflow_run_id,
                node_id=node_id,
                name=str(node.get("label")),
                agent_id=str(node.get("agent")),
                status="queued" if index else "running",
                input_payload={"upstream": workflow_def.nodes[index - 1]["id"] if index else "operator", "provider_config": _product_video_provider_config(node_id)},
                output_payload={"artifact": node.get("artifact", ""), "artifact_uri": "", "data": {}},
                logs=["等待上游节点完成" if index else "等待商品/品牌资料结构化"],
            ))

    def _execute_product_video_stage(self, node_id: str, workflow_run: WorkflowRun, workflow_def: WorkflowDefinition, product: ProductRecord, project: Project, brand_name: str, request: dict[str, Any], artifact_root: Path) -> tuple[dict[str, Any], str, dict[str, Any] | None]:
        upstream = {node.node_id: node.output_payload.get("data", {}) for node in self._product_video_node_runs(workflow_run.workflow_run_id, workflow_def) if node.status == "succeeded"}
        if node_id == "product_brand_input":
            data = _video_product_brand_brief(product, project, brand_name, request)
            return data, _write_json_artifact(artifact_root, "00-product-brand-input.json", data), None
        if node_id == "planner":
            data = _video_planner_plan(product, brand_name, request)
            return data, _write_json_artifact(artifact_root, "01-planner-plan.json", data), None
        if node_id == "story":
            planner_plan = dict(upstream.get("planner") or _video_planner_plan(product, brand_name, request))
            data = _video_story(product, brand_name, planner_plan)
            return data, _write_json_artifact(artifact_root, "02-story.json", data), None
        if node_id == "script":
            story = dict(upstream.get("story") or _video_story(product, brand_name, _video_planner_plan(product, brand_name, request)))
            script_text = _video_script(product, brand_name, story, request)
            script = self.create_script({
                "name": f"完整视频直播话术-{product.product_name}",
                "category": "sales",
                "content": script_text,
                "product_id": product.product_id,
                "ai_generated": True,
                "tags": ["完整视频", "直播话术", "端到端工作流"],
            })
            data = {"script_template_id": script.template_id, "content": script.content, "category": script.category}
            return data, _write_json_artifact(artifact_root, "03-script.json", data), None
        if node_id == "director":
            story = dict(upstream.get("story") or _video_story(product, brand_name, _video_planner_plan(product, brand_name, request)))
            script_data = dict(upstream.get("script") or {})
            script_text = str(script_data.get("content") or _video_script(product, brand_name, story, request))
            data = _video_director_plan(product, story, script_text, request)
            return data, _write_json_artifact(artifact_root, "04-director-shot-plan.json", data), None
        if node_id == "visual_director":
            director_plan = dict(upstream.get("director") or _video_director_plan(product, dict(upstream.get("story") or {}), str(dict(upstream.get("script") or {}).get("content") or ""), request))
            data = _video_visual_blueprint(product, brand_name, director_plan, request)
            return data, _write_json_artifact(artifact_root, "05-visual-blueprint.json", data), None
        if node_id == "asset":
            visual_blueprint = dict(upstream.get("visual_director") or {})
            source_assets = self._select_video_source_assets(project, product, request)
            data = _video_asset_manifest(product, project, source_assets, visual_blueprint)
            return data, _write_json_artifact(artifact_root, "06-asset-manifest.json", data), None
        if node_id == "image":
            visual_blueprint = dict(upstream.get("visual_director") or _video_visual_blueprint(product, brand_name, dict(upstream.get("director") or {}), request))
            data = self._create_video_image_assets(project, product, visual_blueprint, artifact_root)
            return data, _write_json_artifact(artifact_root, "07-image-assets.json", data), None
        if node_id == "video":
            director_plan = dict(upstream.get("director") or {})
            visual_blueprint = dict(upstream.get("visual_director") or {})
            data = self._create_video_clip_assets(project, product, director_plan, visual_blueprint, artifact_root)
            return data, _write_json_artifact(artifact_root, "08-video-clips.json", data), None
        if node_id == "editor":
            script_data = dict(upstream.get("script") or {})
            script = self.scripts.get(str(script_data.get("script_template_id") or "")) if script_data.get("script_template_id") else self.create_script({"name": f"完整视频直播话术-{product.product_name}", "category": "sales", "content": _video_script(product, brand_name, dict(upstream.get("story") or {}), request), "product_id": product.product_id, "ai_generated": True, "tags": ["完整视频", "直播话术", "端到端工作流"]})
            director_plan = dict(upstream.get("director") or {})
            visual_blueprint = dict(upstream.get("visual_director") or {})
            image_outputs = dict(upstream.get("image") or {"assets": []})
            video_outputs = dict(upstream.get("video") or {"clips": []})
            editor_manifest = _video_editor_manifest(product, brand_name, script, director_plan, visual_blueprint, image_outputs, video_outputs, request)
            final_video_path = artifact_root / "final-video.placeholder.mp4"
            final_video_path.write_text(_video_placeholder_content(product, brand_name, editor_manifest), encoding="utf-8")
            final_video_uri = _artifact_uri(final_video_path)
            final_video_asset = self.create_asset(project.project_id, {
                "name": f"完整视频-{product.product_name}",
                "asset_type": "video",
                "object_key": final_video_uri,
                "preview_url": final_video_uri,
                "tags": ["完整视频", "Editor Agent", "端到端工作流"],
                "metadata": {"workflow_run_id": workflow_run.workflow_run_id, "product_id": product.product_id, "brand_name": brand_name, "provider_config": _product_video_provider_config("editor"), "upstream_clip_providers": [str(clip.get("provider") or "") for clip in video_outputs.get("clips", [])]},
            })
            clip_providers = {str(clip.get("provider") or "") for clip in video_outputs.get("clips", [])}
            final_status = "media_ready" if clip_providers and "placeholder_video" not in clip_providers else "placeholder_ready"
            final_video = {"asset_id": final_video_asset.asset_id, "uri": final_video_uri, "duration_seconds": editor_manifest["timeline"]["duration_seconds"], "format": "mp4", "status": final_status, "note": "真实 Image/Video provider 可用时使用生成媒体；无外部密钥或 provider 失败时回退为可追踪占位产物。"}
            data = {**editor_manifest, "final_video": final_video}
            return data, final_video_uri, final_video
        raise ValueError(f"Unsupported product video workflow node: {node_id}")

    def _write_product_video_agent_run(self, project: Project, workflow_run: WorkflowRun, node: dict[str, Any], node_run: WorkflowNodeRun) -> None:
        self.agent_runs.upsert(AgentRun(
            project_id=project.project_id,
            agent_id=str(node.get("agent")),
            workflow_run_id=workflow_run.workflow_run_id,
            node_run_id=node_run.node_run_id,
            task=str(node.get("description") or node.get("label") or ""),
            status="succeeded",
            progress=1,
            input_payload=node_run.input_payload,
            output_payload=node_run.output_payload,
            logs=node_run.logs,
            token_count=node_run.token_count,
            duration_seconds=node_run.duration_seconds,
            completed_at=utc_now_iso(),
        ))

    def _select_video_source_assets(self, project: Project, product: ProductRecord, payload: dict[str, Any]) -> list[dict[str, Any]]:
        provided_assets = payload.get("assets") if isinstance(payload.get("assets"), list) else []
        selected: list[Asset] = []
        for index, asset_payload in enumerate(provided_assets):
            if not isinstance(asset_payload, dict):
                continue
            selected.append(self.create_asset(project.project_id, {
                "name": str(asset_payload.get("name") or f"外部素材 {index + 1}"),
                "asset_type": str(asset_payload.get("asset_type") or asset_payload.get("type") or "document"),
                "source_uri": str(asset_payload.get("source_uri") or asset_payload.get("url") or ""),
                "object_key": str(asset_payload.get("object_key") or asset_payload.get("source_uri") or ""),
                "preview_url": str(asset_payload.get("preview_url") or asset_payload.get("url") or ""),
                "tags": _string_list(asset_payload.get("tags") or ["输入素材"]),
                "metadata": {"workflow": "product_brand_to_complete_video", "product_id": product.product_id, **dict(asset_payload.get("metadata") or {})},
            }))
        selected.extend(self.list_assets(project.project_id))
        if not selected:
            selected.append(self.create_asset(project.project_id, {
                "name": f"{product.product_name} 商品资料",
                "asset_type": "document",
                "object_key": f"workbench://products/{product.product_id}",
                "tags": ["商品资料", "自动生成"],
                "metadata": {"workflow": "product_brand_to_complete_video", "product_id": product.product_id},
            }))
        deduped: dict[str, Asset] = {asset.asset_id: asset for asset in selected}
        return [asset.model_dump() for asset in deduped.values()]

    def _create_video_image_assets(self, project: Project, product: ProductRecord, visual_blueprint: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
        image_dir = artifact_root / "images"
        image_dir.mkdir(parents=True, exist_ok=True)
        outputs = []
        provider = "openai_image" if _openai_image_enabled(str(self.workspace_root)) else "placeholder_image"
        errors: list[dict[str, str]] = []
        for prompt in visual_blueprint.get("image_prompts", []):
            image_id = str(prompt.get("id") or f"image_{len(outputs) + 1}")
            prompt_text = str(prompt.get("prompt") or f"{product.product_name} live commerce image")
            image_path = image_dir / f"{image_id}.png"
            metadata: dict[str, Any] = {"workflow": "product_brand_to_complete_video", "product_id": product.product_id, "prompt": prompt, "provider": provider}
            try:
                if provider == "openai_image":
                    generated = generate_openai_image(
                        prompt=prompt_text,
                        output_path=image_path,
                        api_key=_openai_image_api_key(str(self.workspace_root)),
                        model=str(os.environ.get("TAVERN_OPENAI_IMAGE_MODEL") or "gpt-image-1"),
                        size=str(os.environ.get("TAVERN_OPENAI_IMAGE_SIZE") or _image_size_for_canvas(visual_blueprint)),
                        base_url=_openai_image_base_url(str(self.workspace_root)),
                        timeout_seconds=float(os.environ.get("TAVERN_MEDIA_TIMEOUT_SECONDS") or 300),
                    )
                    uri = generated.uri
                    metadata.update(generated.metadata)
                    metadata["model"] = generated.model
                    tags = ["Image Agent", "OpenAI", "完整视频"]
                else:
                    raise RuntimeError("OPENAI_API_KEY is not configured")
            except Exception as exc:
                provider = "placeholder_image"
                image_path = image_dir / f"{image_id}.placeholder.png"
                image_path.write_text(f"Placeholder image for {product.product_name}\nPrompt: {prompt_text}\nReason: {exc}\n", encoding="utf-8")
                uri = _artifact_uri(image_path)
                metadata.update({"placeholder": True, "fallback_provider": "placeholder_image", "fallback_reason": str(exc)})
                tags = ["Image Agent", "占位图", "完整视频"]
                errors.append({"image_id": image_id, "error": str(exc)})
            asset = self.create_asset(project.project_id, {
                "name": str(prompt.get("label") or image_id),
                "asset_type": "image",
                "object_key": uri,
                "preview_url": uri,
                "tags": tags,
                "metadata": metadata,
            })
            outputs.append({"image_id": image_id, "asset_id": asset.asset_id, "uri": uri, "prompt": prompt, "provider": metadata.get("fallback_provider") or metadata.get("provider")})
        return {"provider": provider, "assets": outputs, "status": "ready", "errors": errors}

    def _create_video_clip_assets(self, project: Project, product: ProductRecord, director_plan: dict[str, Any], visual_blueprint: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
        video_dir = artifact_root / "clips"
        video_dir.mkdir(parents=True, exist_ok=True)
        clips = []
        provider = "jimeng_ai" if _jimeng_video_enabled(str(self.workspace_root)) else "placeholder_video"
        errors: list[dict[str, str]] = []
        prompts_by_shot = {str(item.get("shot_id")): item for item in visual_blueprint.get("video_prompts", [])}
        for shot in director_plan.get("shots", []):
            shot_id = str(shot.get("shot_id") or f"shot_{len(clips) + 1}")
            prompt = prompts_by_shot.get(shot_id, {})
            prompt_text = str(prompt.get("prompt") or shot.get("visual") or f"{product.product_name} product video")
            shot_duration_seconds = int(shot.get("duration_seconds") or 5)
            duration_seconds = shot_duration_seconds
            jimeng_duration_seconds = _jimeng_duration_seconds(shot_duration_seconds)
            clip_path = video_dir / f"{shot_id}.mp4"
            metadata: dict[str, Any] = {"workflow": "product_brand_to_complete_video", "product_id": product.product_id, "shot": shot, "prompt": prompt, "provider": provider}
            try:
                if provider == "jimeng_ai":
                    generated = generate_jimeng_video(
                        prompt=prompt_text,
                        output_path=clip_path,
                        api_key=_jimeng_video_api_key(str(self.workspace_root)),
                        base_url=_jimeng_video_base_url(str(self.workspace_root)),
                        model=str(os.environ.get("TAVERN_JIMENG_VIDEO_MODEL") or "jimeng-video"),
                        req_key=str(os.environ.get("TAVERN_JIMENG_REQ_KEY") or "jimeng_t2v_v30"),
                        submit_action=str(os.environ.get("TAVERN_JIMENG_SUBMIT_ACTION") or "CVSync2AsyncSubmitTask"),
                        result_action=str(os.environ.get("TAVERN_JIMENG_RESULT_ACTION") or "CVSync2AsyncGetResult"),
                        api_version=str(os.environ.get("TAVERN_JIMENG_API_VERSION") or "2022-08-31"),
                        aspect_ratio=_jimeng_aspect_ratio(visual_blueprint),
                        duration_seconds=jimeng_duration_seconds,
                        fps=int(os.environ.get("TAVERN_JIMENG_FPS") or 24),
                        timeout_seconds=float(os.environ.get("TAVERN_MEDIA_TIMEOUT_SECONDS") or 300),
                        poll_interval_seconds=float(os.environ.get("TAVERN_JIMENG_POLL_INTERVAL_SECONDS") or 2),
                        max_poll_attempts=int(os.environ.get("TAVERN_JIMENG_MAX_POLL_ATTEMPTS") or 300),
                        access_key=str(os.environ.get("TAVERN_JIMENG_ACCESS_KEY") or ""),
                        secret_key=str(os.environ.get("TAVERN_JIMENG_SECRET_KEY") or ""),
                        region=str(os.environ.get("TAVERN_JIMENG_REGION") or "cn-north-1"),
                        service=str(os.environ.get("TAVERN_JIMENG_SERVICE") or "cv"),
                    )
                    uri = generated.uri
                    metadata.update(generated.metadata)
                    metadata["model"] = generated.model
                    metadata["requested_duration_seconds"] = jimeng_duration_seconds
                    tags = ["Video Agent", "即梦", "镜头视频", "完整视频"]
                else:
                    raise RuntimeError("TAVERN_JIMENG_API_KEY or TAVERN_JIMENG_ACCESS_KEY/TAVERN_JIMENG_SECRET_KEY is not configured")
            except Exception as exc:
                provider = "placeholder_video"
                clip_path = video_dir / f"{shot_id}.placeholder.mp4"
                clip_path.write_text(f"Placeholder clip for {product.product_name}\nShot: {shot}\nPrompt: {prompt_text}\nReason: {exc}\n", encoding="utf-8")
                uri = _artifact_uri(clip_path)
                metadata.update({"placeholder": True, "fallback_provider": "placeholder_video", "fallback_reason": str(exc), "requested_duration_seconds": jimeng_duration_seconds})
                tags = ["Video Agent", "镜头视频", "完整视频", "占位视频"]
                errors.append({"shot_id": shot_id, "error": str(exc)})
            asset = self.create_asset(project.project_id, {
                "name": f"{product.product_name} {shot_id} 镜头视频",
                "asset_type": "video",
                "object_key": uri,
                "preview_url": uri,
                "tags": tags,
                "metadata": metadata,
            })
            clips.append({"shot_id": shot_id, "asset_id": asset.asset_id, "uri": uri, "duration_seconds": duration_seconds, "prompt": prompt, "provider": metadata.get("fallback_provider") or metadata.get("provider")})
        return {"provider": provider, "clips": clips, "status": "ready", "errors": errors}

    def _write_product_video_node_runs(self, workflow_run: WorkflowRun, workflow_def: WorkflowDefinition, stage_payloads: dict[str, Any], artifacts: dict[str, str], prompt_version_id: str) -> list[WorkflowNodeRun]:
        saved_nodes: list[WorkflowNodeRun] = []
        for index, node in enumerate(workflow_def.nodes):
            node_id = str(node.get("id"))
            output_payload = stage_payloads.get(node_id, {})
            artifact_uri = artifacts.get("complete_video", "") if node_id == "editor" else artifacts.get(node_id, "")
            node_run = WorkflowNodeRun(
                workflow_run_id=workflow_run.workflow_run_id,
                node_id=node_id,
                name=str(node.get("label")),
                agent_id=str(node.get("agent")),
                status="succeeded",
                input_payload={"upstream": workflow_def.nodes[index - 1]["id"] if index else "operator", "workflow": "product_brand_to_complete_video"},
                output_payload={"artifact": node.get("artifact", ""), "artifact_uri": artifact_uri, "data": output_payload},
                prompt_version_id=prompt_version_id if node_id == "script" else "",
                logs=[f"{node.get('label')} 已完成", f"产物：{node.get('artifact', '')}"],
                token_count=900 if node.get("reusable", True) else 300,
                duration_seconds=float(8 + index * 2),
                completed_at=utc_now_iso(),
            )
            saved_nodes.append(self.workflow_node_runs.upsert(node_run))
        return saved_nodes

    def _write_product_video_agent_runs(self, project: Project, workflow_run: WorkflowRun, workflow_def: WorkflowDefinition, nodes: list[WorkflowNodeRun]) -> None:
        node_by_id = {node.node_id: node for node in nodes}
        for node in workflow_def.nodes:
            node_id = str(node.get("id"))
            if node_id == "product_brand_input":
                continue
            node_run = node_by_id.get(node_id)
            self.agent_runs.upsert(AgentRun(
                project_id=project.project_id,
                agent_id=str(node.get("agent")),
                workflow_run_id=workflow_run.workflow_run_id,
                node_run_id=node_run.node_run_id if node_run else "",
                task=str(node.get("description") or node.get("label") or ""),
                status="succeeded",
                progress=1,
                output_payload=node_run.output_payload if node_run else {},
                logs=node_run.logs if node_run else [],
                token_count=node_run.token_count if node_run else 0,
                duration_seconds=node_run.duration_seconds if node_run else 0,
                completed_at=utc_now_iso(),
            ))

    def list_agent_runs(self, project_id: str = "") -> list[AgentRun]:
        return _filter_by_project(self.agent_runs.list(), project_id)

    def list_assets(self, project_id: str = "") -> list[Asset]:
        return _filter_by_project(self.assets.list(), project_id)

    def list_components(self, project_id: str = "") -> list[LiveComponent]:
        return _filter_by_project(self.components.list(), project_id)

    def list_live_scenes(self, project_id: str = "") -> list[LiveScene]:
        return _filter_by_project(self.live_scenes.list(), project_id)

    def list_live_room_compositions(self, project_id: str = "") -> list[LiveRoomComposition]:
        return _filter_by_project(self.live_room_compositions.list(), project_id)

    def list_workflow_runs(self, project_id: str = "") -> list[WorkflowRun]:
        return _filter_by_project(self.workflow_runs.list(), project_id)

    def list_best_practices(self, project_id: str = "") -> list[BestPractice]:
        items = _filter_by_project(self.best_practices.list(), project_id)
        return sorted(items, key=lambda item: item.score, reverse=True)

    def create_asset(self, project_id: str, payload: dict[str, Any]) -> Asset:
        return self.assets.upsert(Asset.model_validate({**payload, "project_id": project_id}))

    def create_component(self, project_id: str, payload: dict[str, Any]) -> LiveComponent:
        component = LiveComponent.model_validate({**payload, "project_id": project_id})
        if not component.component_code:
            component = component.model_copy(update={"component_code": _component_code(component.component_type, len(self.components.list()) + 1)})
        component = self.components.upsert(component)
        self._sync_asset_component_links(component)
        return component

    def create_live_scene(self, project_id: str, payload: dict[str, Any]) -> LiveScene:
        scene = LiveScene.model_validate({**payload, "project_id": project_id})
        scene = self._hydrate_scene(scene)
        return self.live_scenes.upsert(scene)

    def create_live_room(self, project_id: str, payload: dict[str, Any]) -> LiveRoomComposition:
        composition = LiveRoomComposition.model_validate({**payload, "project_id": project_id})
        composition = self._hydrate_live_room(composition)
        return self.live_room_compositions.upsert(composition)

    def clone_best_practice(self, best_practice_id: str, target_project_id: str = "") -> LiveRoomComposition:
        best = self.best_practices.get(best_practice_id)
        project_id = target_project_id or best.project_id
        scene = self.create_live_scene(project_id, {
            "name": f"复用场景 - {best.title}",
            "component_ids": best.component_ids,
            "component_slots": [{"component_id": component_id, "locked": True} for component_id in best.component_ids],
            "tags": ["Best Practice", "克隆"],
            "metadata": {"source_best_practice_id": best.best_practice_id},
        })
        composition = LiveRoomComposition(
            project_id=project_id,
            name=f"复用方案 - {best.title}",
            scene_ids=[scene.scene_id],
            components=[{"component_id": component_id, "locked": True} for component_id in best.component_ids],
            tags=["Best Practice", "可复用"],
            metadata={"source_best_practice_id": best.best_practice_id},
        )
        return self.create_live_room(project_id, composition.model_dump())

    def _resolve_mvp_product(self, payload: dict[str, Any]) -> ProductRecord:
        product_id = str(payload.get("product_id") or "")
        if product_id:
            product = self.products.get(product_id)
            return product if product.status == "published" else self.publish_product(product.product_id)
        product_payload = payload.get("product") if isinstance(payload.get("product"), dict) else None
        if product_payload:
            product = self.create_product({
                "product_name": str(product_payload.get("product_name") or product_payload.get("name") or "MVP直播商品"),
                "sku": str(product_payload.get("sku") or f"MVP-{len(self.products.list()) + 1:03d}"),
                "price": float(product_payload.get("price") or 0),
                "original_price": float(product_payload.get("original_price") or product_payload.get("price") or 0),
                "aroma_type": str(product_payload.get("aroma_type") or product_payload.get("category") or ""),
                "alcohol_degree": str(product_payload.get("alcohol_degree") or ""),
                "volume": str(product_payload.get("volume") or ""),
                "selling_points": _string_list(product_payload.get("selling_points") or product_payload.get("selling_point") or []),
                "scenes": _string_list(product_payload.get("scenes") or product_payload.get("scene") or []),
                "faqs": product_payload.get("faqs") or [],
                "status": "published",
            })
            return product
        products = self.products.list()
        if products:
            product = next((item for item in products if item.status == "published"), products[0])
            return product if product.status == "published" else self.publish_product(product.product_id)
        return self.create_product({
            "product_name": "MVP酒类礼盒",
            "sku": "MVP-GIFT-001",
            "price": 299,
            "original_price": 399,
            "aroma_type": "礼盒",
            "selling_points": ["品牌背书", "节日送礼", "直播间权益"],
            "scenes": ["商务宴请", "节日拜访"],
            "status": "published",
        })

    def _resolve_mvp_project(self, payload: dict[str, Any], product: ProductRecord) -> Project:
        project_id = str(payload.get("project_id") or "")
        if project_id:
            project = self.projects.get(project_id)
        else:
            project_payload = payload.get("project") if isinstance(payload.get("project"), dict) else {}
            if project_payload:
                project = self.create_project({
                    "name": str(project_payload.get("name") or f"{product.product_name} MVP直播项目"),
                    "brand_name": str(project_payload.get("brand_name") or payload.get("brand_name") or ""),
                    "industry": str(project_payload.get("industry") or "直播电商"),
                    "objective": str(project_payload.get("objective") or "打通商品到直播视频的 MVP 方案"),
                    "tags": _string_list(project_payload.get("tags") or ["Phase9", "MVP"]),
                    "metadata": dict(project_payload.get("metadata") or {}),
                })
            else:
                projects = self.projects.list()
                project = projects[0] if projects else self.create_project({
                    "name": f"{product.product_name} MVP直播项目",
                    "brand_name": str(payload.get("brand_name") or ""),
                    "objective": "打通商品到直播视频的 MVP 方案",
                    "tags": ["Phase9", "MVP"],
                })
        metadata = dict(project.metadata)
        metadata["product_ids"] = _unique_strings([*metadata.get("product_ids", []), product.product_id])
        metadata["phase9_last_product_id"] = product.product_id
        return self.projects.upsert(project.model_copy(update={"metadata": metadata, "updated_at": utc_now_iso()}))

    def _resolve_mvp_avatar(self, payload: dict[str, Any]) -> AvatarProfile:
        avatar_id = str(payload.get("avatar_id") or "")
        if avatar_id:
            return self.avatars.get(avatar_id)
        avatars = self.avatars.list()
        if avatars:
            return next((item for item in avatars if item.status == "ready"), avatars[0])
        return self.create_avatar({
            "name": "MVP数字人主播",
            "provider": "heygen",
            "voice_name": "中文女声",
            "status": "ready",
        })

    def _ensure_mvp_live_room(self, project: Project, product: ProductRecord, brand_analysis: dict[str, Any]) -> LiveRoomComposition:
        components = self.list_components(project.project_id) or self.components.list()
        if not components:
            asset = self.create_asset(project.project_id, {
                "name": f"{product.product_name} 商品图",
                "asset_type": "image",
                "object_key": f"minio://mvp-products/{product.product_id}.png",
                "tags": ["MVP", "商品"],
                "metadata": {"product_id": product.product_id},
            })
            components = [self.create_component(project.project_id, {
                "name": f"{product.product_name} 商品卡",
                "component_type": "Product",
                "source_asset_ids": [asset.asset_id],
                "tags": ["MVP", "商品卡"],
                "metadata": {"slot": "product_card", "product_id": product.product_id},
            })]
        selected = _select_mvp_components(components)
        scene = self.create_live_scene(project.project_id, {
            "name": f"MVP讲品场景 - {product.product_name}",
            "scene_type": "mvp_product_pitch",
            "component_ids": [component.component_id for component in selected],
            "component_slots": [
                {"component_id": component.component_id, "slot": str(component.metadata.get("slot") or component.component_type), "layer": index + 1, "locked": True}
                for index, component in enumerate(selected)
            ],
            "layout": {"canvas": "1080x1920", "safe_area": "center", "composition": "phase9_mvp_live_video"},
            "tags": ["Phase9", "MVP", "直播间"],
            "metadata": {"product_id": product.product_id, "brand_name": brand_analysis.get("brand_name", ""), "mvp_step": "live_room"},
        })
        return self.create_live_room(project.project_id, {
            "name": f"MVP直播方案 - {product.product_name}",
            "scene_ids": [scene.scene_id],
            "components": [{"component_id": component.component_id, "source": "phase9_mvp"} for component in selected],
            "tags": ["Phase9", "MVP", "可保存方案"],
            "metadata": {"product_id": product.product_id, "brand_analysis": brand_analysis, "mvp_step": "saved_plan"},
        })

    def _ensure_phase_nine_mvp_workflow_definition(self) -> WorkflowDefinition:
        nodes = [
            {"id": "upload_product", "label": "上传商品", "agent": "Product Agent", "stage": "Product", "artifact": "product_snapshot", "description": "接收运营上传的商品资料并生成结构化快照", "reusable": True},
            {"id": "brand_analysis", "label": "品牌分析", "agent": "Brand Agent", "stage": "Brand", "artifact": "brand_analysis", "description": "分析品牌背书、人群、调性和合规表达边界", "reusable": True},
            {"id": "script", "label": "剧本", "agent": "Script Agent", "stage": "Script", "artifact": "live_script", "description": "生成可给数字人朗读的直播口播剧本", "reusable": True},
            {"id": "speech", "label": "数字人口播", "agent": "Voice Agent", "stage": "Voice", "artifact": "speech_artifact", "description": "复用 TTS Plugin 生成数字人口播音频", "reusable": False},
            {"id": "avatar", "label": "数字人", "agent": "Avatar Agent", "stage": "Avatar", "artifact": "avatar_video", "description": "复用 Avatar Job 生成数字人讲解片段", "reusable": False},
            {"id": "live_video", "label": "直播视频", "agent": "Composer Agent", "stage": "Video", "artifact": "live_video", "description": "复用 FFmpeg/MoviePy Wrapper 合成直播视频", "reusable": False},
            {"id": "saved_plan", "label": "保存方案", "agent": "CEO Agent", "stage": "Project", "artifact": "mvp_live_plan", "description": "保存商品、脚本、数字人、直播间和视频产物的可复用方案", "reusable": True},
        ]
        edges = [{"source": nodes[index]["id"], "target": nodes[index + 1]["id"], "type": "handoff"} for index in range(len(nodes) - 1)]
        payload = {
            "name": "Phase 9 MVP Product-to-Saved-Live-Plan",
            "version": "phase9-v1",
            "description": "上传商品→品牌分析→剧本→数字人口播→数字人→直播视频→保存方案的 MVP 闭环。",
            "nodes": nodes,
            "edges": edges,
            "status": "active",
            "updated_at": utc_now_iso(),
        }
        for definition in self.workflow_definitions.list():
            node_ids = {str(node.get("id")) for node in definition.nodes}
            if "saved_plan" in node_ids and "live_video" in node_ids:
                return self.workflow_definitions.upsert(definition.model_copy(update=payload))
        return self.workflow_definitions.upsert(WorkflowDefinition(**payload))

    def _write_mvp_node_runs(self, workflow_run: WorkflowRun, workflow_def: WorkflowDefinition, steps: list[dict[str, Any]], prompt_version_id: str) -> None:
        step_by_id = {str(step.get("id")): step for step in steps}
        for node in workflow_def.nodes:
            step = step_by_id.get(str(node.get("id")), {})
            self.workflow_node_runs.upsert(WorkflowNodeRun(
                workflow_run_id=workflow_run.workflow_run_id,
                node_id=str(node.get("id")),
                name=str(node.get("label")),
                agent_id=str(node.get("agent")),
                status="succeeded",
                input_payload={"source": "phase9_mvp", "plan_step": node.get("id")},
                output_payload={"summary": step.get("summary", ""), "artifact_uri": step.get("artifact_uri", ""), "data": step.get("data", {})},
                prompt_version_id=prompt_version_id if node.get("id") in {"brand_analysis", "script"} else "",
                logs=[str(step.get("summary") or f"{node.get('label')} 已完成")],
                token_count=int(step.get("token_count") or 0),
                duration_seconds=float(step.get("duration_seconds") or 0),
                completed_at=utc_now_iso(),
            ))

    def _attach_mvp_plan_to_project(self, project: Project, product: ProductRecord, plan: MvpLivePlan) -> None:
        metadata = dict(project.metadata)
        metadata["product_ids"] = _unique_strings([*metadata.get("product_ids", []), product.product_id])
        metadata["mvp_plan_ids"] = _unique_strings([*metadata.get("mvp_plan_ids", []), plan.plan_id])
        metadata["latest_mvp_plan_id"] = plan.plan_id
        metadata["latest_live_video_uri"] = plan.live_video_uri
        self.projects.upsert(project.model_copy(update={"metadata": metadata, "updated_at": utc_now_iso()}))

    def analytics_overview(self, project_id: str = "") -> dict[str, Any]:
        performances = _filter_by_project(self.performance_metrics.list(), project_id)
        components = _filter_by_project(self.components.list(), project_id)
        snapshots = _filter_by_project(self.live_session_snapshots.list(), project_id)
        prompt_versions = self.prompt_versions.list()
        avatars = self.avatars.list()
        best = self.list_best_practices(project_id)
        top_session = max(performances, key=lambda item: item.gmv, default=None)
        top_components = sorted(components, key=lambda item: (item.gmv, item.cvr, item.ctr), reverse=True)[:10]
        top_ranking = _top_session_ranking(performances, snapshots)
        component_ranking = _component_ranking(components)
        prompt_ranking = _prompt_ranking(prompt_versions, snapshots, performances)
        avatar_ranking = _avatar_ranking(avatars, snapshots, performances)
        return {
            "summary": _analytics_summary(performances, components, prompt_versions, avatars, snapshots),
            "top_session": top_session.model_dump() if top_session else None,
            "top_ranking": top_ranking,
            "top_components": [item.model_dump() for item in top_components],
            "component_ranking": component_ranking,
            "prompt_ranking": prompt_ranking,
            "avatar_ranking": avatar_ranking,
            "best_practices": [item.model_dump() for item in best[:10]],
            "best_practice_ranking": _best_practice_ranking(best),
            "snapshot_count": len(snapshots),
        }

    def list_plugins(self, category: str = "") -> list[PluginProvider]:
        self.sync_plugin_providers()
        providers = self.plugin_providers.list()
        if category:
            providers = [provider for provider in providers if provider.category == category]
        return sorted(providers, key=lambda item: (item.category, item.provider_id))

    def plugin_health(self, provider_id: str = "") -> dict[str, Any]:
        return self.plugin_manager.health(provider_id or None)

    def estimate_plugin_cost(self, provider_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        estimate = self.plugin_manager.estimate_cost(provider_id, payload)
        return {"estimated_cost": estimate.estimated_cost, "currency": estimate.currency, "detail": estimate.detail}

    def submit_plugin_job(self, provider_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.plugin_manager.submit_job(provider_id, payload).__dict__

    def get_plugin_job(self, provider_id: str, job_id: str) -> dict[str, Any]:
        return self.plugin_manager.get_job(provider_id, job_id).__dict__

    def cancel_plugin_job(self, provider_id: str, job_id: str) -> dict[str, Any]:
        return self.plugin_manager.cancel_job(provider_id, job_id).__dict__

    def _submit_mvp_tts_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        providers = _mvp_tts_provider_candidates(str(payload.get("tts_provider") or ""))
        errors: list[dict[str, str]] = []
        for provider_id in providers:
            if provider_id == "placeholder":
                continue
            try:
                health = self.plugin_manager.health(provider_id)
                if health.get("status") in {"not_configured", "unhealthy", "not_installed"}:
                    errors.append({"provider_id": provider_id, "error": str(health.get("error") or health.get("status"))})
                    continue
                job = self.submit_plugin_job(provider_id, payload)
            except Exception as exc:
                errors.append({"provider_id": provider_id, "error": str(exc)[:240]})
                continue
            metadata = {**dict(job.get("metadata") or {}), "provider_id": provider_id}
            if errors:
                metadata["fallback_errors"] = errors
            job = {**job, "metadata": metadata}
            if job.get("status") != "failed":
                return job
            errors.append({"provider_id": provider_id, "error": str(job.get("error") or "failed")[:240]})
        return {
            "job_id": "tts-placeholder",
            "status": "placeholder",
            "output_uri": "",
            "error": "",
            "metadata": {"provider_id": "placeholder", "fallback_errors": errors},
        }

    def _sync_asset_component_links(self, component: LiveComponent) -> None:
        if not component.source_asset_ids:
            return
        for asset_id in component.source_asset_ids:
            if not _exists(self.assets, asset_id):
                continue
            asset = self.assets.get(asset_id)
            converted = list(dict.fromkeys([*asset.converted_component_ids, component.component_id]))
            metadata = {**asset.metadata, "componentized": True, "component_count": len(converted)}
            self.assets.upsert(asset.model_copy(update={"converted_component_ids": converted, "metadata": metadata, "updated_at": utc_now_iso()}))

    def _hydrate_scene(self, scene: LiveScene) -> LiveScene:
        component_ids = list(dict.fromkeys([*scene.component_ids, *[str(slot.get("component_id")) for slot in scene.component_slots if slot.get("component_id")]]))
        component_snapshot = [self.components.get(component_id).model_dump() for component_id in component_ids if _exists(self.components, component_id)]
        slots = scene.component_slots or [{"component_id": component_id, "layer": index + 1, "slot": f"layer_{index + 1}"} for index, component_id in enumerate(component_ids)]
        metadata = {**scene.metadata, "component_count": len(component_ids), "contract": "Asset -> Component -> Scene -> LiveRoom"}
        return scene.model_copy(update={"component_ids": component_ids, "component_slots": slots, "component_snapshot": component_snapshot, "metadata": metadata, "updated_at": utc_now_iso()})

    def _hydrate_live_room(self, composition: LiveRoomComposition) -> LiveRoomComposition:
        scenes = [self.live_scenes.get(scene_id) for scene_id in composition.scene_ids if _exists(self.live_scenes, scene_id)]
        scene_snapshot = [scene.model_dump() for scene in scenes]
        component_ids = list(dict.fromkeys([
            *[str(item.get("component_id")) for item in composition.components if item.get("component_id")],
            *[component_id for scene in scenes for component_id in scene.component_ids],
        ]))
        components = composition.components or [{"component_id": component_id, "source": "scene"} for component_id in component_ids]
        component_snapshot = [self.components.get(component_id).model_dump() for component_id in component_ids if _exists(self.components, component_id)]
        tags = list(dict.fromkeys([*composition.tags, *[tag for scene in scenes for tag in scene.tags]]))
        metadata = {**composition.metadata, "scene_count": len(scenes), "component_count": len(component_ids), "contract": "Asset -> Component -> Scene -> LiveRoom"}
        return composition.model_copy(update={"scene_snapshot": scene_snapshot, "components": components, "component_snapshot": component_snapshot, "tags": tags, "metadata": metadata, "updated_at": utc_now_iso()})

    def _ensure_phase_five_workflow_definition(self) -> WorkflowDefinition:
        nodes = [
            {"id": "product", "label": "商品", "agent": "Product Agent", "stage": "Product", "artifact": "product_profile", "description": "沉淀 SKU、价格、卖点、FAQ 与合规边界", "reusable": True},
            {"id": "brand", "label": "品牌", "agent": "Brand Agent", "stage": "Brand", "artifact": "brand_brief", "description": "生成品牌背书、调性、信任证明与人群定位", "reusable": True},
            {"id": "story", "label": "故事", "agent": "Story Agent", "stage": "Story", "artifact": "brand_story", "description": "把品牌与商品转成直播间可讲述的故事线", "reusable": True},
            {"id": "script", "label": "剧本", "agent": "Script Agent", "stage": "Script", "artifact": "live_script", "description": "输出开场、讲品、促单、互动和收口口播", "reusable": True},
            {"id": "storyboard", "label": "分镜", "agent": "Storyboard Agent", "stage": "Storyboard", "artifact": "shot_plan", "description": "拆解镜头、字幕、视觉层和转场节奏", "reusable": True},
            {"id": "director", "label": "导演", "agent": "Director Agent", "stage": "Director", "artifact": "director_script", "description": "协调镜头、节奏、表演与生产顺序，沉淀 Director Script 和导演执行意图", "reusable": True},
            {"id": "visual_director", "label": "视觉导演", "agent": "Visual Director Agent", "stage": "Visual", "artifact": "visual_blueprint", "description": "将 Story、Script 和 Director Script 转换成品牌统一的 Visual Blueprint、Prompt、Asset Mapping 与 OBS 图层", "reusable": True},
            {"id": "voice", "label": "语音", "agent": "Voice Agent", "stage": "Voice", "artifact": "speech_audio", "description": "将口播剧本交给 TTS provider 生成语音素材", "reusable": False},
            {"id": "avatar", "label": "数字人", "agent": "Avatar Agent", "stage": "Avatar", "artifact": "avatar_clip", "description": "驱动数字人主播生成口播片段", "reusable": False},
            {"id": "live_room", "label": "直播间", "agent": "Scene Agent", "stage": "LiveRoom", "artifact": "live_room_composition", "description": "组合背景、商品卡、权益 POP 与数字人图层", "reusable": True},
            {"id": "video", "label": "视频", "agent": "Composer Agent", "stage": "Video", "artifact": "composed_video", "description": "用视频 provider/FFmpeg wrapper 合成完整直播视频", "reusable": False},
            {"id": "streaming", "label": "推流", "agent": "Streaming Agent", "stage": "Streaming", "artifact": "stream_publish_plan", "description": "生成 OBS/RTMP/平台开播检查与推流方案", "reusable": False},
        ]
        edges = [{"source": nodes[index]["id"], "target": nodes[index + 1]["id"], "type": "handoff"} for index in range(len(nodes) - 1)]
        payload = {
            "name": "AI Live Commerce Product-to-Streaming Workflow",
            "version": "phase5-v1",
            "description": "商品→品牌→故事→剧本→分镜→导演→视觉导演→语音→数字人→直播间→视频→推流的企业级直播生产主链路。",
            "nodes": nodes,
            "edges": edges,
            "status": "active",
            "updated_at": utc_now_iso(),
        }
        definitions = self.workflow_definitions.list()
        for definition in definitions:
            node_ids = {str(node.get("id")) for node in definition.nodes}
            if "streaming" in node_ids and "live_room" in node_ids:
                return self.workflow_definitions.upsert(definition.model_copy(update=payload))
        for definition in definitions:
            node_ids = {str(node.get("id")) for node in definition.nodes}
            if "upload" in node_ids or definition.name == "AI Live Commerce Production Pipeline":
                return self.workflow_definitions.upsert(definition.model_copy(update=payload))
        return self.workflow_definitions.upsert(WorkflowDefinition(**payload))

    def _ensure_seed_data(self) -> None:
        if not self.products.list():
            product = self.create_product({
                "product_name": "可雅白兰地礼盒",
                "sku": "KOYA-500-GB",
                "price": 399,
                "original_price": 599,
                "aroma_type": "白兰地",
                "alcohol_degree": "40%vol",
                "volume": "500ml",
                "selling_points": ["节日送礼", "礼盒包装", "商务宴请"],
                "scenes": ["商务宴请", "送礼", "聚会"],
                "faqs": [{"question": "适合送领导吗？", "answer": "适合成年人正式拜访和商务宴请场景，建议按预算理性选择。"}],
                "status": "published",
            })
        else:
            product = self.products.list()[0]
        if not self.avatars.list():
            self.create_avatar({
                "name": "酒类品牌数字人主播",
                "provider": "heygen",
                "heygen_avatar_id": "",
                "heygen_voice_id": "",
                "voice_name": "中文女声",
                "status": "ready",
            })
        avatar = self.avatars.list()[0]
        if not self.workflow_rules.list():
            for rule in [
                {"name": "用户进入欢迎", "event_type": "user_enter", "action_type": "welcome", "delay_seconds": 0},
                {"name": "下单感谢", "event_type": "order_created", "action_type": "thank_order", "delay_seconds": 0},
                {"name": "冷场 60 秒互动", "event_type": "cold_start", "action_type": "run_script", "delay_seconds": 60},
            ]:
                self.workflow_rules.upsert(WorkflowRule.model_validate(rule))
        if not self.platform_accounts.list():
            self.platform_accounts.upsert(PlatformAccount(display_name="手动模拟直播间", platform="manual", credentials_configured=True))
        if not self.metrics.list():
            self.metrics.upsert(PlatformMetricSnapshot(current_product_id=product.product_id, online_users=1286, gmv=68420, order_count=329, interaction_rate=0.186, conversion_rate=0.042))
        if not self.model_providers.list():
            for provider in [
                {"name": "gpt", "display_name": "GPT 主力回复模型", "chat_model": "gpt-4.1", "embedding_model": "text-embedding-3-large", "configured": False},
                {"name": "claude", "display_name": "Claude 高质量策划模型", "chat_model": "claude-sonnet-4-6", "configured": False},
                {"name": "gemini", "display_name": "Gemini 多模态模型", "chat_model": "gemini-2.5-pro", "configured": False},
            ]:
                self.model_providers.upsert(ModelProviderConfig.model_validate(provider))
        if not self.prompt_templates.list():
            self.prompt_templates.upsert(PromptTemplate(
                name="酒类主播回复 Prompt",
                purpose="live_reply",
                content="你是酒类电商数字人主播，回复必须自然口语化、15秒以内，并遵守酒类合规。",
                variables=["product", "audience_event", "retrieved_knowledge"],
            ))
        if not self.knowledge_documents.list():
            document = self.create_knowledge_document({"name": "可雅白兰地直播 FAQ", "source_type": "text", "product_id": product.product_id, "status": "uploaded"})
            self.index_knowledge_document(document.document_id, "适合送领导吗？适合成年人正式拜访和商务宴请场景。\n有什么卖点？礼盒包装、节日送礼、成熟消费者聚会场景。\n合规提醒：酒类不宣传养生、保健或医疗功效，不面向未成年人。")
        if not self.projects.list():
            project = self.create_project({
                "name": "张裕葡萄酒 AI 直播项目",
                "brand_name": "张裕 / 可雅",
                "industry": "酒类直播电商",
                "objective": "沉淀可复用的高转化数字人直播方案",
                "tags": ["葡萄酒", "白兰地", "礼盒", "AI Company"],
                "metadata": {"product_ids": [product.product_id]},
            })
        else:
            project = self.projects.list()[0]
        status_by_role = {"ceo": "working", "planner": "working", "brand": "working", "script": "working", "visual_director": "working", "avatar": "blocked", "composer": "blocked"}
        task_by_role = {
            "ceo": "统筹本场直播生产流水线并确认验收标准",
            "planner": "拆解 Phase 4 Agent Company 执行顺序",
            "brand": "提炼品牌信任背书与内容调性",
            "script": "优化直播口播与促单话术",
            "visual_director": "将分镜与导演稿转换成可执行 Visual Blueprint",
            "avatar": "等待 Avatar/TTS provider 配置",
            "composer": "等待数字人与转场素材进入合成",
        }
        progress_by_role = {"ceo": 0.82, "planner": 0.68, "brand": 0.76, "product": 1.0, "script": 0.64, "visual_director": 0.52, "scene": 0.35, "avatar": 0.18, "composer": 0.18}
        token_by_role = {"ceo": 2480, "planner": 1840, "brand": 1320, "product": 980, "script": 3560, "visual_director": 1680, "scene": 720, "avatar": 420, "composer": 420}
        elapsed_by_role = {"ceo": 186, "planner": 126, "brand": 94, "product": 61, "script": 212, "visual_director": 88, "scene": 40, "avatar": 37, "composer": 37}
        logs_by_role = {
            "ceo": ["已确认项目目标", "正在审核 Agent 输出"],
            "planner": ["已拆解 Agent Company 角色链", "已建立 handoff 顺序"],
            "brand": ["已读取品牌资料", "输出品牌关键词"],
            "product": ["商品卖点解析完成"],
            "script": ["已生成开场脚本", "正在生成促单脚本"],
            "visual_director": ["已锁定品牌视觉原则", "正在生成 Visual Blueprint"],
            "scene": ["已匹配酒类礼盒场景模板"],
            "avatar": ["HeyGen provider 待配置", "数字人脚本接口已映射"],
            "composer": ["FFmpeg provider 就绪", "Avatar provider 未配置"],
        }
        existing_role_ids = {str(agent.metadata.get("role_id") or "") for agent in self.agent_profiles.list()}
        for role in build_default_agent_company().list_roles():
            if role.role_id in existing_role_ids:
                continue
            payload = role.profile_payload(
                status=status_by_role.get(role.role_id, "idle"),
                current_task=task_by_role.get(role.role_id, f"等待 {role.title} 任务输入"),
                progress=progress_by_role.get(role.role_id, 0.0),
                token_count=token_by_role.get(role.role_id, 0),
                elapsed_seconds=elapsed_by_role.get(role.role_id, 0),
                logs=logs_by_role.get(role.role_id, ["Agent Company 角色已注册"]),
            )
            self.agent_profiles.upsert(AgentProfile.model_validate(payload))
        if not self.assets.list():
            for asset in [
                {"project_id": project.project_id, "name": "品牌介绍文档", "asset_type": "document", "object_key": "minio://assets/brand-story.pdf", "tags": ["Brand KB", "品牌资料"], "metadata": {"phase": "asset", "source": "brand"}},
                {"project_id": project.project_id, "name": "可雅礼盒产品图", "asset_type": "image", "object_key": "minio://assets/koya-gift.png", "preview_url": "/assets/koya-gift.png", "tags": ["产品图", "礼盒"], "metadata": {"phase": "asset", "source": "product"}},
                {"project_id": project.project_id, "name": "直播间背景素材", "asset_type": "image", "object_key": "minio://assets/wine-bg.png", "preview_url": "/assets/wine-bg.png", "tags": ["背景", "酒窖"], "metadata": {"phase": "asset", "source": "scene"}},
            ]:
                self.assets.upsert(Asset.model_validate(asset))
        assets = self.assets.list()
        product_asset = next((item for item in assets if "产品图" in item.tags), assets[0])
        background_asset = next((item for item in assets if "背景" in item.tags), assets[-1])
        if not self.components.list():
            for component in [
                {"project_id": project.project_id, "component_code": "Background_001", "name": "深色酒窖背景", "component_type": "Background", "source_asset_ids": [background_asset.asset_id], "tags": ["高级", "酒类", "礼盒"], "industries": ["酒类"], "product_types": ["白兰地", "葡萄酒"], "usage_count": 12, "rating": 4.8, "gmv": 186400, "ctr": 0.126, "cvr": 0.052, "best_session_count": 3, "resource_url": "minio://components/background-001.png", "metadata": {"slot": "background", "z_index": 1}},
                {"project_id": project.project_id, "component_code": "Avatar_001", "name": "专业女主播数字人", "component_type": "Avatar", "tags": ["可信", "专业"], "industries": ["酒类", "礼品"], "product_types": ["礼盒"], "usage_count": 8, "rating": 4.6, "gmv": 132600, "ctr": 0.109, "cvr": 0.047, "best_session_count": 2, "resource_url": "minio://components/avatar-001.mp4", "metadata": {"slot": "host", "z_index": 3}},
                {"project_id": project.project_id, "component_code": "ProductCard_001", "name": "可雅礼盒商品卡", "component_type": "Product", "source_asset_ids": [product_asset.asset_id], "tags": ["商品", "礼盒", "价格卡"], "industries": ["酒类"], "product_types": ["白兰地", "礼盒"], "usage_count": 10, "rating": 4.5, "gmv": 156800, "ctr": 0.132, "cvr": 0.056, "best_session_count": 4, "resource_url": "minio://components/product-card-001.svg", "metadata": {"slot": "product_card", "z_index": 4}},
                {"project_id": project.project_id, "component_code": "POP_001", "name": "限时权益 POP", "component_type": "POP", "tags": ["促单", "权益"], "industries": ["电商"], "product_types": ["礼盒"], "usage_count": 18, "rating": 4.4, "gmv": 216800, "ctr": 0.148, "cvr": 0.061, "best_session_count": 5, "resource_url": "minio://components/pop-001.svg", "metadata": {"slot": "promo", "z_index": 5}},
            ]:
                saved = self.create_component(project.project_id, component)
                self.component_versions.upsert(ComponentVersion(component_id=saved.component_id, version=saved.current_version, resource_url=saved.resource_url, preview_url=saved.preview_url, changelog="初始可复用组件版本", metadata={"source_asset_ids": saved.source_asset_ids, "tags": saved.tags}))
        components = self.components.list()
        if not self.live_room_templates.list():
            self.live_room_templates.upsert(LiveRoomTemplate(project_id=project.project_id, name="酒类礼盒高转化直播间", component_ids=[item.component_id for item in components], tags=["酒类", "礼盒", "高转化"], layout={"canvas": "1080x1920", "layers": [item.component_code for item in components]}, metadata={"contract": "Asset -> Component -> Scene -> LiveRoom"}))
        if not self.live_scenes.list():
            self.create_live_scene(project.project_id, {
                "name": "讲品主场景",
                "scene_type": "product_pitch",
                "component_ids": [item.component_id for item in components],
                "component_slots": [{"component_id": item.component_id, "slot": str(item.metadata.get("slot") or item.component_type), "layer": index + 1, "locked": item.component_type in {"Background", "Avatar"}} for index, item in enumerate(components)],
                "layout": {"canvas": "1080x1920", "safe_area": "center", "composition": "digital_human_live_commerce"},
                "tags": ["讲品", "酒类", "礼盒", "可复用场景"],
                "metadata": {"objective": "商品讲解和促单", "version_note": "Phase 6 scene seed"},
            })
        scenes = self.live_scenes.list()
        if not self.live_room_compositions.list():
            self.create_live_room(project.project_id, {
                "name": "张裕礼盒直播间组合 A",
                "template_id": self.live_room_templates.list()[0].template_id if self.live_room_templates.list() else "",
                "scene_ids": [scene.scene_id for scene in scenes],
                "tags": ["酒类", "礼盒", "高转化", "LiveRoom"],
                "metadata": {"objective": "AI 数字人酒类礼盒直播", "version_note": "Phase 6 composition seed"},
            })
        else:
            for composition_item in self.live_room_compositions.list():
                self.live_room_compositions.upsert(self._hydrate_live_room(composition_item))
        composition = self.live_room_compositions.list()[0]
        prompt = self.prompt_templates.list()[0]
        default_prompt_versions = [
            {"name": prompt.name, "purpose": prompt.purpose, "version": prompt.version, "content": prompt.content, "variables": prompt.variables, "score": 86, "use_count": 24, "cost_estimate": 18.6, "gmv": 68420, "ctr": 0.12, "cvr": 0.042},
            {"name": "促单权益 Prompt", "purpose": "sales_push", "version": "v2", "content": "生成限时权益促单话术，强调理性下单和成年人饮酒合规。", "variables": ["product", "benefit", "deadline"], "score": 91, "use_count": 31, "cost_estimate": 21.4, "gmv": 93600, "ctr": 0.148, "cvr": 0.061},
            {"name": "分镜导演 Prompt", "purpose": "storyboard", "version": "v1", "content": "把直播剧本拆成数字人、商品卡、POP、字幕和镜头节奏。", "variables": ["script", "components"], "score": 84, "use_count": 16, "cost_estimate": 12.7, "gmv": 54200, "ctr": 0.118, "cvr": 0.039},
            {"name": "视觉导演 Prompt", "purpose": "visual_blueprint", "version": "v1", "content": "把 Story、Script、Director Script、Brand、Product、Audience、Emotion、Live Goal、Platform、Scene、Current Assets 和 Runtime Context 转换成 Visual Blueprint；只输出 visual_blueprint YAML，包含 brand、scene、camera、lighting、composition、avatar、product、subtitle、overlay、music、transition、image_prompt、video_prompt、asset_mapping、obs_layers、director_note。", "variables": ["story", "script", "director_script", "brand", "product", "audience", "emotion", "live_goal", "platform", "scene", "current_assets", "runtime_context"], "score": 92, "use_count": 0, "cost_estimate": 0, "gmv": 0, "ctr": 0, "cvr": 0},
        ]
        existing_prompt_purposes = {item.purpose for item in self.prompt_versions.list()}
        for prompt_payload in default_prompt_versions:
            if prompt_payload["purpose"] not in existing_prompt_purposes:
                self.prompt_versions.upsert(PromptVersion(prompt_id=prompt.prompt_id, **prompt_payload))
        prompt_version = self.prompt_versions.list()[0]
        workflow_def = self._ensure_phase_five_workflow_definition()
        workflow_run = next((run for run in self.workflow_runs.list() if run.workflow_definition_id == workflow_def.workflow_definition_id), None)
        if workflow_run is None:
            workflow_run = self.workflow_runs.upsert(WorkflowRun(
                project_id=project.project_id,
                workflow_definition_id=workflow_def.workflow_definition_id,
                status="running",
                progress=0.45,
                current_node_id="visual_director",
                input_payload={"project_id": project.project_id, "product_id": product.product_id, "workflow": "product_to_streaming"},
                output_payload={"completed_artifacts": ["product_profile", "brand_brief", "brand_story", "live_script", "shot_plan", "director_script"]},
                logs=["商品节点已生成 SKU 与卖点快照", "品牌节点已生成信任背书", "故事节点已输出直播叙事主线", "剧本、分镜与导演节点已完成", "正在生成 Visual Blueprint"],
                token_count=10040,
                cost_estimate=12.8,
                duration_seconds=420,
            ))
        existing_node_ids = {node.node_id for node in self.workflow_node_runs.list() if node.workflow_run_id == workflow_run.workflow_run_id}
        for index, node in enumerate(workflow_def.nodes):
            if node["id"] in existing_node_ids:
                continue
            status = "succeeded" if node["id"] in {"product", "brand", "story", "script", "storyboard", "director"} else "running" if node["id"] == "visual_director" else "queued"
            self.workflow_node_runs.upsert(WorkflowNodeRun(
                workflow_run_id=workflow_run.workflow_run_id,
                node_id=node["id"],
                name=node["label"],
                agent_id=node["agent"],
                status=status,
                prompt_version_id=prompt_version.prompt_version_id if node["id"] in {"brand", "product", "story", "script"} else "",
                input_payload={"upstream": workflow_def.nodes[index - 1]["id"] if index else "operator"},
                output_payload={"artifact": node.get("artifact", "") if status != "queued" else ""},
                logs=[f"{node['label']}节点状态：{status}", f"产物：{node.get('artifact', '待生成')}"] if status != "queued" else ["等待上游节点完成"],
                token_count=1200 if status != "queued" else 0,
                duration_seconds=52 if status == "succeeded" else 0,
            ))
        if not self.agent_runs.list():
            workflow_run = self.workflow_runs.list()[0]
            for agent in self.agent_profiles.list()[:4]:
                self.agent_runs.upsert(AgentRun(project_id=project.project_id, agent_id=agent.agent_id, workflow_run_id=workflow_run.workflow_run_id, task=agent.current_task or agent.role, status="running" if agent.status == "working" else "succeeded", progress=agent.progress, logs=agent.logs, token_count=agent.token_count, duration_seconds=agent.elapsed_seconds))
        if not self.performance_metrics.list():
            metric = self.performance_metrics.upsert(PerformanceMetric(project_id=project.project_id, session_id="demo-live-session", component_ids=[item.component_id for item in components], gmv=68420, ctr=0.126, cvr=0.042, watch_seconds=920, retention_rate=0.38, interaction_rate=0.186, like_count=2380, comment_count=642, order_count=329, refund_rate=0.018, product_clicks=4180, add_to_cart_rate=0.083, conversion_rate=0.042))
            self.performance_metrics.upsert(PerformanceMetric(project_id=project.project_id, session_id="demo-live-session-pop", component_ids=[item.component_id for item in components if item.component_type in {"Product", "POP", "Avatar"}], gmv=93600, ctr=0.148, cvr=0.061, watch_seconds=1160, retention_rate=0.43, interaction_rate=0.214, like_count=3180, comment_count=854, order_count=428, refund_rate=0.014, product_clicks=5360, add_to_cart_rate=0.101, conversion_rate=0.061))
            self.performance_metrics.upsert(PerformanceMetric(project_id=project.project_id, session_id="demo-live-session-story", component_ids=[item.component_id for item in components if item.component_type in {"Background", "Avatar", "Product"}], gmv=54200, ctr=0.118, cvr=0.039, watch_seconds=820, retention_rate=0.36, interaction_rate=0.172, like_count=1980, comment_count=488, order_count=241, refund_rate=0.019, product_clicks=3460, add_to_cart_rate=0.076, conversion_rate=0.039))
        else:
            metric = self.performance_metrics.list()[0]
        if not self.live_session_snapshots.list():
            prompt_versions = self.prompt_versions.list()
            for index, performance_metric in enumerate(self.performance_metrics.list()):
                prompt_for_snapshot = prompt_versions[min(index, len(prompt_versions) - 1)]
                self.live_session_snapshots.upsert(LiveSessionSnapshot(project_id=project.project_id, session_id=performance_metric.session_id, composition_id=composition.composition_id, component_ids=performance_metric.component_ids or [item.component_id for item in components], script_ids=[item.template_id for item in self.scripts.list()], prompt_versions=[prompt_for_snapshot.prompt_version_id], avatar_id=avatar.avatar_id, voice_id=avatar.heygen_voice_id or "voice-default", workflow_version=workflow_def.version, performance_metric_id=performance_metric.metric_id, snapshot={"composition": composition.model_dump(), "performance": performance_metric.model_dump(), "prompt_version": prompt_for_snapshot.model_dump()}))
        if not self.best_practices.list():
            self.best_practices.upsert(BestPractice(project_id=project.project_id, title="葡萄酒礼盒 GMV 最高直播组合", query_label="葡萄酒 GMV 最高", source_session_id=metric.session_id, component_ids=[item.component_id for item in components], script_ids=[item.template_id for item in self.scripts.list()], prompt_versions=[prompt_version.prompt_version_id], score=91.5, reason="深色酒窖背景 + 专业数字人 + 限时权益 POP 在礼盒送礼场景中 CTR/CVR 均高于均值。", reusable_payload={"composition_id": composition.composition_id, "workflow_definition_id": workflow_def.workflow_definition_id}))
        self._ensure_phase_nine_mvp_workflow_definition()
        self._ensure_product_video_workflow_definition()
        self.sync_plugin_providers()

    def sync_plugin_providers(self) -> list[PluginProvider]:
        providers: list[PluginProvider] = []
        self.plugin_manager = build_plugin_manager(self.workspace_root)
        for manifest in self.plugin_manager.manifests():
            provider = PluginProvider.model_validate({
                "plugin_id": f"plugin-{manifest.category}-{manifest.provider_id}",
                "category": manifest.category,
                "provider_id": manifest.provider_id,
                "display_name": manifest.display_name,
                "source_type": manifest.source_type,
                "repo_url": manifest.repo_url,
                "commit": manifest.commit,
                "license": manifest.license,
                "capabilities": list(manifest.capabilities),
                "health_status": manifest.health_status,
                "config_schema": manifest.config_schema,
                "metadata": manifest.metadata,
            })
            providers.append(self.plugin_providers.upsert(provider))
        return providers


def _analytics_summary(performances: list[PerformanceMetric], components: list[LiveComponent], prompt_versions: list[PromptVersion], avatars: list[AvatarProfile], snapshots: list[LiveSessionSnapshot]) -> dict[str, Any]:
    return {
        "gmv": sum(item.gmv for item in performances),
        "ctr": _average([item.ctr for item in performances]),
        "cvr": _average([item.cvr for item in performances]),
        "order_count": sum(item.order_count for item in performances),
        "session_count": len(performances),
        "component_count": len(components),
        "prompt_count": len(prompt_versions),
        "avatar_count": len(avatars),
        "snapshot_count": len(snapshots),
    }


def _top_session_ranking(performances: list[PerformanceMetric], snapshots: list[LiveSessionSnapshot]) -> list[dict[str, Any]]:
    snapshot_by_metric_id = {snapshot.performance_metric_id: snapshot for snapshot in snapshots if snapshot.performance_metric_id}
    snapshot_by_session_id = {snapshot.session_id: snapshot for snapshot in snapshots if snapshot.session_id}
    rows = []
    for metric in sorted(performances, key=lambda item: (item.gmv, item.cvr, item.ctr), reverse=True):
        snapshot = snapshot_by_metric_id.get(metric.metric_id) or snapshot_by_session_id.get(metric.session_id)
        rows.append({
            "rank": len(rows) + 1,
            "session_id": metric.session_id,
            "metric_id": metric.metric_id,
            "gmv": metric.gmv,
            "ctr": metric.ctr,
            "cvr": metric.cvr,
            "order_count": metric.order_count,
            "component_ids": metric.component_ids,
            "prompt_versions": snapshot.prompt_versions if snapshot else [],
            "avatar_id": snapshot.avatar_id if snapshot else "",
            "composition_id": snapshot.composition_id if snapshot else "",
            "score": _ranking_score(metric.gmv, metric.ctr, metric.cvr),
        })
    return rows[:10]


def _component_ranking(components: list[LiveComponent]) -> list[dict[str, Any]]:
    rows = []
    sorted_components = sorted(components, key=lambda item: (item.gmv, item.cvr, item.ctr, item.rating), reverse=True)
    for component in sorted_components:
        rows.append({
            "rank": len(rows) + 1,
            "component_id": component.component_id,
            "component_code": component.component_code,
            "name": component.name,
            "component_type": component.component_type,
            "gmv": component.gmv,
            "ctr": component.ctr,
            "cvr": component.cvr,
            "usage_count": component.usage_count,
            "best_session_count": component.best_session_count,
            "score": round(component.gmv / 10000 + component.ctr * 100 + component.cvr * 100 + component.rating * 5 + component.best_session_count * 2, 2),
        })
    return rows[:20]


def _prompt_ranking(prompt_versions: list[PromptVersion], snapshots: list[LiveSessionSnapshot], performances: list[PerformanceMetric]) -> list[dict[str, Any]]:
    metric_by_id = {metric.metric_id: metric for metric in performances}
    rows = []
    for prompt in prompt_versions:
        prompt_snapshots = [snapshot for snapshot in snapshots if prompt.prompt_version_id in snapshot.prompt_versions]
        attributed_metrics = [metric_by_id[snapshot.performance_metric_id] for snapshot in prompt_snapshots if snapshot.performance_metric_id in metric_by_id]
        attributed_gmv = sum(metric.gmv for metric in attributed_metrics)
        gmv = max(prompt.gmv, attributed_gmv)
        ctr = _average([metric.ctr for metric in attributed_metrics]) if attributed_metrics else prompt.ctr
        cvr = _average([metric.cvr for metric in attributed_metrics]) if attributed_metrics else prompt.cvr
        rows.append({
            "rank": 0,
            "prompt_version_id": prompt.prompt_version_id,
            "prompt_id": prompt.prompt_id,
            "name": prompt.name,
            "purpose": prompt.purpose,
            "version": prompt.version,
            "gmv": gmv,
            "ctr": ctr,
            "cvr": cvr,
            "use_count": prompt.use_count,
            "cost_estimate": prompt.cost_estimate,
            "session_count": len(prompt_snapshots),
            "score": round(prompt.score + gmv / 10000 + cvr * 100, 2),
        })
    rows.sort(key=lambda item: (item["gmv"], item["score"], item["cvr"]), reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows[:20]


def _avatar_ranking(avatars: list[AvatarProfile], snapshots: list[LiveSessionSnapshot], performances: list[PerformanceMetric]) -> list[dict[str, Any]]:
    metric_by_id = {metric.metric_id: metric for metric in performances}
    rows = []
    for avatar in avatars:
        avatar_snapshots = [snapshot for snapshot in snapshots if snapshot.avatar_id == avatar.avatar_id]
        metrics = [metric_by_id[snapshot.performance_metric_id] for snapshot in avatar_snapshots if snapshot.performance_metric_id in metric_by_id]
        gmv = sum(metric.gmv for metric in metrics)
        ctr = _average([metric.ctr for metric in metrics])
        cvr = _average([metric.cvr for metric in metrics])
        rows.append({
            "rank": 0,
            "avatar_id": avatar.avatar_id,
            "name": avatar.name,
            "provider": avatar.provider,
            "voice_name": avatar.voice_name,
            "status": avatar.status,
            "session_count": len(avatar_snapshots),
            "gmv": gmv,
            "ctr": ctr,
            "cvr": cvr,
            "score": _ranking_score(gmv, ctr, cvr) + len(avatar_snapshots) * 5,
        })
    rows.sort(key=lambda item: (item["gmv"], item["score"], item["cvr"]), reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows[:20]


def _best_practice_ranking(best_practices: list[BestPractice]) -> list[dict[str, Any]]:
    return [
        {
            "rank": index,
            "best_practice_id": item.best_practice_id,
            "title": item.title,
            "query_label": item.query_label,
            "score": item.score,
            "reason": item.reason,
            "component_ids": item.component_ids,
            "prompt_versions": item.prompt_versions,
            "source_session_id": item.source_session_id,
        }
        for index, item in enumerate(sorted(best_practices, key=lambda entry: entry.score, reverse=True), start=1)
    ][:20]


def _ranking_score(gmv: float, ctr: float, cvr: float) -> float:
    return round(gmv / 10000 + ctr * 100 + cvr * 100, 2)


def _average(values: list[float]) -> float:
    filtered = [value for value in values if value is not None]
    return round(sum(filtered) / len(filtered), 4) if filtered else 0


def _filter_by_project(items: list[Any], project_id: str) -> list[Any]:
    if not project_id:
        return items
    return [item for item in items if getattr(item, "project_id", "") in {"", project_id}]


def _component_code(component_type: str, number: int) -> str:
    prefix = re.sub(r"[^A-Za-z0-9]+", "", component_type or "Component") or "Component"
    return f"{prefix}_{number:03d}"


def _mvp_tts_provider_candidates(explicit_provider: str = "") -> list[str]:
    if explicit_provider and _normalize_tts_provider(explicit_provider) == "placeholder":
        return ["placeholder"]
    mvp_provider = os.environ.get("TAVERN_MVP_TTS_PROVIDER", "cosyvoice_tts")
    if not explicit_provider and _normalize_tts_provider(mvp_provider) == "placeholder":
        return ["placeholder"]
    configured = [
        explicit_provider,
        mvp_provider,
        os.environ.get("TAVERN_TTS_PROVIDER", ""),
        os.environ.get("TAVERN_TTS_FALLBACK_PROVIDER", "edge_tts"),
        "edge_tts",
        "placeholder",
    ]
    candidates: list[str] = []
    for provider in configured:
        normalized = _normalize_tts_provider(provider)
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    return candidates or ["placeholder"]


def _normalize_tts_provider(provider: str | None) -> str:
    normalized = str(provider or "").strip().lower().replace("-", "_")
    aliases = {
        "cosyvoice": "cosyvoice_tts",
        "cosyvoice_tts": "cosyvoice_tts",
        "edge": "edge_tts",
        "edge_tts": "edge_tts",
        "openai": "openai_compatible_tts",
        "openai_tts": "openai_compatible_tts",
        "openai_compatible": "openai_compatible_tts",
        "openai_compatible_tts": "openai_compatible_tts",
        "placeholder": "placeholder",
        "silent": "placeholder",
        "off": "placeholder",
        "none": "placeholder",
    }
    return aliases.get(normalized, normalized)


def _mvp_brand_analysis(product: ProductRecord, payload: dict[str, Any]) -> dict[str, Any]:
    brand_name = str(payload.get("brand_name") or payload.get("brand") or product.product_name.split("礼盒")[0] or "直播品牌")
    selling_points = product.selling_points or ["直播间权益", "成熟消费者场景", "礼盒包装"]
    scenes = product.scenes or ["节日送礼", "商务宴请"]
    return {
        "brand_name": brand_name,
        "positioning": f"{brand_name}围绕{product.product_name}建立可信、克制、专业的数字人直播表达。",
        "target_audience": ["成年人消费者", "节日送礼人群", "商务宴请采购人群"],
        "trust_points": selling_points[:4],
        "content_tone": "专业、热情、克制，不夸大功效",
        "selling_scenes": scenes,
        "compliance_boundary": ["不面向未成年人", "不宣传养生保健或医疗功效", "提醒理性饮酒", "不鼓励酒后驾驶"],
    }


def _mvp_script_content(product: ProductRecord, brand_analysis: dict[str, Any], note: str = "") -> str:
    selling_points = "、".join(product.selling_points or brand_analysis.get("trust_points", []) or ["礼盒包装", "直播间权益"])
    scenes = "、".join(product.scenes or brand_analysis.get("selling_scenes", []) or ["节日送礼", "商务宴请"])
    price = f"¥{product.price:g}" if product.price else "以直播间实时权益为准"
    note_text = f"\n运营提示：{note}" if note else ""
    return (
        f"大家好，欢迎来到直播间。今天这款是{product.product_name}，品牌定位是{brand_analysis.get('positioning', '')}\n"
        f"它适合{scenes}等成年人消费场景，核心看点是{selling_points}。\n"
        f"当前参考价是{price}，具体组合权益以直播间页面为准，大家按需理性选择。\n"
        f"如果你正在准备拜访、宴请或节日礼物，可以先把这款加入对比；有规格、香型、发货、送礼问题可以直接打在公屏。\n"
        f"也提醒大家，酒类产品不面向未成年人，不宣传保健或医疗功效，请适量饮酒，不要酒后驾驶。{note_text}"
    )


def _mvp_steps(product: ProductRecord, brand_analysis: dict[str, Any], script: ScriptTemplate, avatar: AvatarProfile, avatar_job: AvatarJob, composition: LiveRoomComposition, speech_uri: str, live_video_uri: str, plan_id: str, tts_job: dict[str, Any]) -> list[dict[str, Any]]:
    tts_metadata = dict(tts_job.get("metadata") or {})
    tts_provider = str(tts_metadata.get("provider_id") or "placeholder")
    speech_summary = "CosyVoice TTS 已生成口播音频" if tts_provider == "cosyvoice_tts" and tts_job.get("output_uri") else "TTS 已回退到备用 provider 或占位 URI"
    return [
        {"id": "upload_product", "label": "上传商品", "status": "succeeded", "summary": f"商品 {product.product_name} 已发布并结构化", "artifact_uri": f"workbench://products/{product.product_id}", "data": {"product_id": product.product_id, "sku": product.sku}, "duration_seconds": 8},
        {"id": "brand_analysis", "label": "品牌分析", "status": "succeeded", "summary": f"{brand_analysis.get('brand_name')} 品牌分析已生成", "artifact_uri": f"workbench://mvp-plans/{plan_id}/brand-analysis", "data": brand_analysis, "token_count": 900, "duration_seconds": 18},
        {"id": "script", "label": "剧本", "status": "succeeded", "summary": "数字人口播剧本已生成并保存为 Script Template", "artifact_uri": f"workbench://scripts/{script.template_id}", "data": {"script_template_id": script.template_id, "characters": len(script.content)}, "token_count": 1200, "duration_seconds": 22},
        {"id": "speech", "label": "数字人口播", "status": "succeeded", "summary": speech_summary, "artifact_uri": speech_uri, "data": {"provider_id": tts_provider, "tts_job_id": tts_job.get("job_id", ""), "speech_artifact_uri": speech_uri, "fallback_errors": tts_metadata.get("fallback_errors", [])}, "duration_seconds": 12},
        {"id": "avatar", "label": "数字人", "status": "succeeded", "summary": f"数字人 {avatar.name} 文本驱动任务已完成", "artifact_uri": avatar_job.output_url, "data": {"avatar_id": avatar.avatar_id, "avatar_job_id": avatar_job.job_id}, "duration_seconds": 16},
        {"id": "live_video", "label": "直播视频", "status": "succeeded", "summary": "FFmpeg/MoviePy Wrapper 已生成直播视频占位产物", "artifact_uri": live_video_uri, "data": {"live_video_uri": live_video_uri, "composition_id": composition.composition_id}, "duration_seconds": 16},
        {"id": "saved_plan", "label": "保存方案", "status": "succeeded", "summary": "MVP直播方案已保存，可复用到项目与数据中心", "artifact_uri": f"workbench://mvp-plans/{plan_id}", "data": {"plan_id": plan_id}, "duration_seconds": 4},
    ]


def _sanitize_workflow_payload(payload: dict[str, Any]) -> dict[str, Any]:
    forbidden = {"api_key", "openai_api_key", "jimeng_api_key", "secret", "secret_key", "access_token", "authorization", "bearer"}
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        lowered = key.lower()
        if lowered in forbidden or any(fragment in lowered for fragment in ["api_key", "secret", "token", "authorization"]):
            sanitized[key] = "***"
            continue
        if isinstance(value, dict):
            sanitized[key] = _sanitize_workflow_payload(value)
        elif isinstance(value, list):
            sanitized[key] = [_sanitize_workflow_payload(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    return sanitized


def _product_video_provider_config(node_id: str) -> dict[str, Any]:
    text_image_config = {
        "provider": os.environ.get("TAVERN_TEXT_IMAGE_MODEL_PROVIDER", "OpenAI"),
        "model_provider": os.environ.get("TAVERN_TEXT_IMAGE_MODEL_PROVIDER", "OpenAI"),
        "model": os.environ.get("TAVERN_TEXT_IMAGE_MODEL", "gpt-5.5"),
        "review_model": os.environ.get("TAVERN_TEXT_IMAGE_REVIEW_MODEL", "gpt-5.5"),
        "model_reasoning_effort": os.environ.get("TAVERN_TEXT_IMAGE_REASONING_EFFORT", "xhigh"),
        "base_url": os.environ.get("TAVERN_OPENAI_BASE_URL", "https://mirror.xinshu.ai"),
        "wire_api": os.environ.get("TAVERN_OPENAI_WIRE_API", "responses"),
        "requires_openai_auth": True,
        "api_key_env": "OPENAI_API_KEY",
        "disable_response_storage": _env_bool("TAVERN_DISABLE_RESPONSE_STORAGE", True),
        "network_access": os.environ.get("TAVERN_NETWORK_ACCESS", "enabled"),
        "windows_wsl_setup_acknowledged": _env_bool("TAVERN_WINDOWS_WSL_SETUP_ACKNOWLEDGED", True),
    }
    if node_id == "image":
        return {
            "provider": "openai_image",
            "model_provider": "OpenAI",
            "model": os.environ.get("TAVERN_OPENAI_IMAGE_MODEL", "gpt-image-1"),
            "size": os.environ.get("TAVERN_OPENAI_IMAGE_SIZE", "1024x1536"),
            "base_url": os.environ.get("TAVERN_OPENAI_IMAGE_BASE_URL") or os.environ.get("TAVERN_OPENAI_BASE_URL", "https://mirror.xinshu.ai"),
            "api_key_env": "OPENAI_API_KEY",
            "fallback_provider": "placeholder_image",
            "network_access": os.environ.get("TAVERN_NETWORK_ACCESS", "enabled"),
        }
    if node_id == "video":
        return {
            "provider": "jimeng_ai",
            "model_provider": "JimengAI",
            "model": os.environ.get("TAVERN_JIMENG_VIDEO_MODEL", "jimeng-video"),
            "base_url": os.environ.get("TAVERN_JIMENG_BASE_URL", "https://visual.volcengineapi.com"),
            "req_key": os.environ.get("TAVERN_JIMENG_REQ_KEY", "jimeng_t2v_v30"),
            "submit_action": os.environ.get("TAVERN_JIMENG_SUBMIT_ACTION", "CVSync2AsyncSubmitTask"),
            "result_action": os.environ.get("TAVERN_JIMENG_RESULT_ACTION", "CVSync2AsyncGetResult"),
            "api_version": os.environ.get("TAVERN_JIMENG_API_VERSION", "2022-08-31"),
            "api_key_env": "TAVERN_JIMENG_API_KEY",
            "access_key_env": "TAVERN_JIMENG_ACCESS_KEY",
            "secret_key_env": "TAVERN_JIMENG_SECRET_KEY",
            "network_access": os.environ.get("TAVERN_NETWORK_ACCESS", "enabled"),
            "fallback_provider": "placeholder_video",
        }
    if node_id == "editor":
        return {
            "provider": "ffmpeg_moviepy",
            "model_provider": "local_editor",
            "upstream_video_provider": "jimeng_ai",
            "api_key_env": "TAVERN_JIMENG_API_KEY",
            "fallback_provider": "placeholder_editor",
        }
    return text_image_config


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _openai_image_api_key(workspace_root: str = ".") -> str:
    return os.environ.get("OPENAI_API_KEY") or image_api_key(workspace_root)


def _openai_image_base_url(workspace_root: str = ".") -> str:
    return os.environ.get("TAVERN_OPENAI_IMAGE_BASE_URL") or os.environ.get("TAVERN_OPENAI_BASE_URL") or image_base_url(workspace_root)


def _jimeng_video_api_key(workspace_root: str = ".") -> str:
    return os.environ.get("TAVERN_JIMENG_API_KEY") or video_api_key(workspace_root)


def _jimeng_video_base_url(workspace_root: str = ".") -> str:
    return os.environ.get("TAVERN_JIMENG_BASE_URL") or video_base_url(workspace_root) or "https://visual.volcengineapi.com"


def _openai_image_enabled(workspace_root: str = ".") -> bool:
    return bool(_openai_image_api_key(workspace_root)) and not _env_bool("TAVERN_FORCE_PLACEHOLDER_MEDIA", False)


def _jimeng_video_enabled(workspace_root: str = ".") -> bool:
    has_bearer = bool(_jimeng_video_api_key(workspace_root))
    has_volc_keys = bool(os.environ.get("TAVERN_JIMENG_ACCESS_KEY") and os.environ.get("TAVERN_JIMENG_SECRET_KEY"))
    return (has_bearer or has_volc_keys) and not _env_bool("TAVERN_FORCE_PLACEHOLDER_MEDIA", False)


def _image_size_for_canvas(visual_blueprint: dict[str, Any]) -> str:
    canvas = str(visual_blueprint.get("layout", {}).get("canvas") or "")
    if canvas in {"1024x1024", "1024x1536", "1536x1024"}:
        return canvas
    return "1024x1536"


def _jimeng_aspect_ratio(visual_blueprint: dict[str, Any]) -> str:
    canvas = str(visual_blueprint.get("layout", {}).get("canvas") or "1080x1920")
    if canvas in {"1080x1920", "720x1280", "1024x1536"}:
        return "9:16"
    if canvas in {"1920x1080", "1280x720", "1536x1024"}:
        return "16:9"
    return "9:16" if "9:16" in str(visual_blueprint.get("layout", {}).get("safe_area") or "9:16") else "16:9"


def _jimeng_duration_seconds(duration_seconds: int) -> int:
    allowed = [int(item.strip()) for item in str(os.environ.get("TAVERN_JIMENG_ALLOWED_DURATIONS") or "5,10").split(",") if item.strip().isdigit()]
    allowed = sorted(set(allowed or [5, 10]))
    return min(allowed, key=lambda item: abs(item - max(1, duration_seconds)))


def _product_video_workflow_nodes() -> list[dict[str, Any]]:
    return [
        {"id": "product_brand_input", "label": "商品/品牌资料", "agent": "Product Agent", "stage": "Input", "artifact": "product_brand_brief", "description": "结构化商品、品牌、卖点、素材与合规边界", "reusable": True},
        {"id": "planner", "label": "Planner Agent（任务规划）", "agent": "Planner Agent", "stage": "Plan", "artifact": "run_plan", "description": "拆解端到端视频生产任务、依赖、验收标准与产物目录", "reusable": True},
        {"id": "story", "label": "Story Agent（故事生成）", "agent": "Story Agent", "stage": "Story", "artifact": "brand_story", "description": "把商品和品牌资料生成直播视频故事线", "reusable": True},
        {"id": "script", "label": "Script Agent（直播话术）", "agent": "Script Agent", "stage": "Script", "artifact": "live_script", "description": "生成数字人可朗读的直播话术、CTA 与合规提示", "reusable": True},
        {"id": "director", "label": "Director Agent（镜头拆解）", "agent": "Director Agent", "stage": "Director", "artifact": "shot_plan", "description": "拆解镜头、表演、字幕、转场与生产顺序", "reusable": True},
        {"id": "visual_director", "label": "Visual Director Agent（画面设计 + Prompt）", "agent": "Visual Director Agent", "stage": "Visual", "artifact": "visual_blueprint", "description": "输出画面设计、图片 Prompt、视频 Prompt、OBS 图层和视觉统一规则", "reusable": True},
        {"id": "asset", "label": "Asset Agent（素材匹配/生成）", "agent": "Asset Agent", "stage": "Asset", "artifact": "asset_manifest", "description": "匹配输入素材并生成缺口素材清单", "reusable": True},
        {"id": "image", "label": "Image Agent（背景/贴图生成）", "agent": "Image Agent", "stage": "Image", "artifact": "image_assets", "description": "生成背景、贴图、商品卡和视觉层占位产物", "reusable": False},
        {"id": "video", "label": "Video Agent（镜头视频生成）", "agent": "Video Agent", "stage": "Video", "artifact": "shot_clips", "description": "按镜头计划生成镜头视频占位产物", "reusable": False},
        {"id": "editor", "label": "Editor Agent（剪辑/BGM/合成）", "agent": "Editor Agent", "stage": "Editor", "artifact": "complete_video", "description": "剪辑镜头、字幕、BGM、转场并输出完整视频", "reusable": False},
    ]


def _video_brand_name(payload: dict[str, Any], project: Project, product: ProductRecord) -> str:
    return str(payload.get("brand_name") or payload.get("brand") or project.brand_name or product.product_name.split("礼盒")[0] or product.product_name)


def _video_product_brand_brief(product: ProductRecord, project: Project, brand_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    brand_profile = payload.get("brand_profile") if isinstance(payload.get("brand_profile"), dict) else {}
    return {
        "product": product.model_dump(),
        "brand": {
            "brand_name": brand_name,
            "positioning": str(brand_profile.get("positioning") or project.objective or f"{brand_name}围绕{product.product_name}建立可信的直播视频表达"),
            "tone": str(brand_profile.get("tone") or "专业、热情、克制、可信"),
            "proof_points": _string_list(brand_profile.get("proof_points") or product.selling_points or ["品牌背书", "直播间权益"]),
        },
        "audience": _string_list(payload.get("audience") or ["成年人消费者", "礼品采购人群", "直播间新客"]),
        "goal": str(payload.get("goal") or "生成一条可用于数字人直播/短视频投放的完整商品视频"),
        "compliance": ["不面向未成年人", "不宣传医疗保健功效", "提醒理性消费", "不鼓励酒后驾驶"],
    }


def _video_planner_plan(product: ProductRecord, brand_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    duration_seconds = int(payload.get("duration_seconds") or 45)
    return {
        "objective": f"用 {duration_seconds} 秒完成 {brand_name} {product.product_name} 的直播视频生产。",
        "duration_seconds": duration_seconds,
        "aspect_ratio": str(payload.get("aspect_ratio") or "9:16"),
        "agents": [node["agent"] for node in _product_video_workflow_nodes()[1:]],
        "milestones": [
            {"id": "creative", "depends_on": ["product_brand_input"], "outputs": ["run_plan", "brand_story", "live_script"]},
            {"id": "production_design", "depends_on": ["creative"], "outputs": ["shot_plan", "visual_blueprint", "asset_manifest"]},
            {"id": "media_generation", "depends_on": ["production_design"], "outputs": ["image_assets", "shot_clips"]},
            {"id": "post_production", "depends_on": ["media_generation"], "outputs": ["complete_video"]},
        ],
        "acceptance_criteria": ["每个节点有可审计产物", "无外部密钥时也能生成占位素材", "最终视频 URI 写入资产中心", "n8n 可按同一顺序触发并展示"],
    }


def _video_story(product: ProductRecord, brand_name: str, planner_plan: dict[str, Any]) -> dict[str, Any]:
    scenes = product.scenes or ["节日送礼", "商务宴请"]
    selling_points = product.selling_points or ["礼盒包装", "直播间权益", "品牌背书"]
    return {
        "title": f"{brand_name} {product.product_name} 的一场安心送礼故事",
        "logline": f"围绕{scenes[0]}场景，用{selling_points[0]}建立信任，再用直播权益推动理性下单。",
        "beats": [
            {"beat": "hook", "text": f"一个成年人送礼/宴请前的真实选择问题：{product.product_name}是否体面又合适？"},
            {"beat": "trust", "text": f"{brand_name}用{ '、'.join(selling_points[:3]) }建立可信理由。"},
            {"beat": "demo", "text": f"主播展示包装、规格、适用场景和直播间权益，帮助观众快速判断。"},
            {"beat": "cta", "text": "提醒按需理性选择，并把规格、发货、送礼问题留给公屏互动。"},
        ],
        "duration_seconds": planner_plan.get("duration_seconds", 45),
    }


def _video_script(product: ProductRecord, brand_name: str, story: dict[str, Any], payload: dict[str, Any]) -> str:
    price = f"¥{product.price:g}" if product.price else "以直播间实时权益为准"
    selling_points = "、".join(product.selling_points or ["礼盒包装", "直播权益", "品牌背书"])
    scenes = "、".join(product.scenes or ["节日送礼", "商务宴请"])
    return (
        f"开场：如果你正在为{scenes}挑一份体面礼物，可以先看这款{brand_name}{product.product_name}。\n"
        f"故事：{story.get('logline', '')}\n"
        f"讲品：它的核心看点是{selling_points}，参考价格{price}，具体组合权益以直播间页面为准。\n"
        f"镜头提示：先给包装和商品特写，再切到主播讲解，最后展示权益贴片和购买提醒。\n"
        f"互动：想了解规格、香型、发货和送礼场景，可以直接打在公屏。\n"
        f"合规：酒类产品仅面向成年人，不宣传保健或医疗功效，请适量饮酒，不要酒后驾驶。"
    )


def _video_director_plan(product: ProductRecord, story: dict[str, Any], script_text: str, payload: dict[str, Any]) -> dict[str, Any]:
    target_duration = int(payload.get("duration_seconds") or story.get("duration_seconds") or 45)
    base_duration = max(5, target_duration // 5)
    script_lines = [line for line in script_text.split("\n") if line.strip()] or [f"介绍{product.product_name}的核心卖点。"]
    shots = [
        {"shot_id": "shot_01", "duration_seconds": base_duration, "purpose": "Hook", "camera": "slow push-in", "visual": "高质感背景 + 商品轮廓", "narration": _script_line(script_lines, 0)},
        {"shot_id": "shot_02", "duration_seconds": base_duration, "purpose": "Trust", "camera": "medium host shot", "visual": "数字人主播 + 品牌信任点字幕", "narration": _script_line(script_lines, 1)},
        {"shot_id": "shot_03", "duration_seconds": base_duration, "purpose": "Product", "camera": "macro detail", "visual": "包装、瓶身、权益贴图", "narration": _script_line(script_lines, 2)},
        {"shot_id": "shot_04", "duration_seconds": base_duration, "purpose": "Interaction", "camera": "host to product card", "visual": "公屏问题贴片 + 商品卡", "narration": _script_line(script_lines, 4)},
        {"shot_id": "shot_05", "duration_seconds": max(5, target_duration - base_duration * 4), "purpose": "CTA", "camera": "clean end card", "visual": "权益 POP + 合规提示", "narration": script_lines[-1]},
    ]
    return {"shots": shots, "transitions": ["warm dissolve", "match cut", "subtle zoom"], "subtitle_style": "white sans-serif with champagne-gold keywords", "safe_area": "9:16 center", "product_id": product.product_id}


def _script_line(lines: list[str], index: int) -> str:
    if not lines:
        return ""
    return lines[min(index, len(lines) - 1)]


def _video_visual_blueprint(product: ProductRecord, brand_name: str, director_plan: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    palette = str(payload.get("palette") or "深酒红、香槟金、暖木色")
    image_prompts = [
        {"id": "background_hero", "label": "品牌直播背景", "prompt": f"premium live commerce background for {brand_name} {product.product_name}, {palette}, warm cinematic lighting, 9:16, product-safe empty center"},
        {"id": "product_sticker", "label": "商品卖点贴图", "prompt": f"clean ecommerce sticker card for {product.product_name}, champagne gold typography, selling points, transparent style"},
        {"id": "end_card", "label": "结尾权益卡", "prompt": f"premium end card for adult alcohol live commerce, rational consumption reminder, {palette}, 9:16"},
    ]
    video_prompts = [
        {"shot_id": shot["shot_id"], "prompt": f"{shot['camera']} motion, {shot['visual']}, premium commercial video, warm lighting, 9:16, duration {shot['duration_seconds']} seconds"}
        for shot in director_plan.get("shots", [])
    ]
    return {
        "brand": {"name": brand_name, "palette": palette, "tone": "premium, trustworthy, restrained"},
        "layout": {"canvas": "1080x1920", "safe_area": director_plan.get("safe_area", "9:16 center"), "subtitle_style": director_plan.get("subtitle_style", "white sans-serif")},
        "image_prompts": image_prompts,
        "video_prompts": video_prompts,
        "asset_mapping": {"background": "background_hero", "product": "product_sticker", "cta": "end_card"},
        "obs_layers": [
            {"layer": "Layer01", "source": "background_hero", "z_index": 1},
            {"layer": "Layer02", "source": "avatar_clip", "z_index": 3},
            {"layer": "Layer03", "source": "product_sticker", "z_index": 4},
            {"layer": "Layer04", "source": "subtitle", "z_index": 5},
        ],
        "director_note": "保持酒类直播视觉高级但克制，所有卖点表达必须可由商品资料支撑。",
    }


def _video_asset_manifest(product: ProductRecord, project: Project, source_assets: list[dict[str, Any]], visual_blueprint: dict[str, Any]) -> dict[str, Any]:
    required = ["background", "product", "cta", "avatar_clip", "subtitle", "bgm"]
    matched = {asset.get("asset_id", f"asset_{index}"): {"name": asset.get("name"), "asset_type": asset.get("asset_type"), "object_key": asset.get("object_key") or asset.get("source_uri")} for index, asset in enumerate(source_assets)}
    return {
        "product_id": product.product_id,
        "project_id": project.project_id,
        "required_slots": required,
        "matched_assets": matched,
        "generated_slots": visual_blueprint.get("asset_mapping", {}),
        "missing_slots": [slot for slot in required if slot not in {"background", "product", "cta", "subtitle"}],
        "strategy": "优先复用运营上传素材；缺口由 Image/Video Agent 生成占位产物，真实 provider 配置后替换。",
    }


def _video_editor_manifest(product: ProductRecord, brand_name: str, script: ScriptTemplate, director_plan: dict[str, Any], visual_blueprint: dict[str, Any], image_outputs: dict[str, Any], video_outputs: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    clips = video_outputs.get("clips", [])
    duration = sum(int(clip.get("duration_seconds") or 0) for clip in clips) or int(payload.get("duration_seconds") or 45)
    return {
        "timeline": {
            "duration_seconds": duration,
            "resolution": "1080x1920",
            "fps": int(payload.get("fps") or 25),
            "clips": clips,
            "image_overlays": image_outputs.get("assets", []),
            "transitions": director_plan.get("transitions", []),
            "captions": [{"source": "script", "script_template_id": script.template_id, "style": visual_blueprint.get("layout", {}).get("subtitle_style", "white sans-serif")}],
            "bgm": {"style": str(payload.get("bgm_style") or "premium light corporate"), "volume": -18},
        },
        "render": {"container": "mp4", "codec": "h264", "audio_codec": "aac", "provider": "placeholder_editor"},
        "quality_gate": ["完整视频 URI 可访问", "镜头顺序与 Director Plan 一致", "字幕引用 Script Agent 输出", "合规提示保留"],
        "brand_name": brand_name,
        "product_id": product.product_id,
    }


def _video_placeholder_content(product: ProductRecord, brand_name: str, editor_manifest: dict[str, Any]) -> str:
    return json.dumps({
        "placeholder_video": True,
        "brand_name": brand_name,
        "product_name": product.product_name,
        "timeline": editor_manifest.get("timeline", {}),
        "note": "This text file is registered as a placeholder .mp4 artifact for offline workflow verification.",
    }, ensure_ascii=False, indent=2)


def _artifact_uri(path: Path) -> str:
    return path.resolve().as_uri()


def _write_json_artifact(root: Path, filename: str, payload: dict[str, Any]) -> str:
    path = root / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return _artifact_uri(path)


def _select_mvp_components(components: list[LiveComponent]) -> list[LiveComponent]:
    selected: list[LiveComponent] = []
    for wanted in ["Background", "Avatar", "Product", "POP"]:
        component = next((item for item in components if item.component_type.lower() == wanted.lower()), None)
        if component:
            selected.append(component)
    for component in components:
        if len(selected) >= 4:
            break
        if component.component_id not in {item.component_id for item in selected}:
            selected.append(component)
    return selected or components[:1]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[\n,，、/]+", value) if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _unique_strings(values: list[Any]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))


def _exists(repository: JsonCollectionRepository[Any], item_id: str) -> bool:
    try:
        repository.get(item_id)
        return True
    except KeyError:
        return False


def _split_knowledge_text(text: str, max_chars: int = 420, overlap_chars: int = 80) -> list[str]:
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    line_parts = [part.strip() for part in normalized.split("\n") if part.strip()]
    if len(line_parts) > 1 and all(len(part) <= max_chars for part in line_parts):
        return line_parts
    paragraphs = [part.strip() for part in re.split(r"\n{1,}|(?<=[。！？；])", normalized) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs or [normalized]:
        if not current:
            current = paragraph
            continue
        if len(current) + len(paragraph) <= max_chars:
            current = f"{current}\n{paragraph}"
            continue
        chunks.append(current)
        prefix = current[-overlap_chars:] if overlap_chars and len(current) > overlap_chars else ""
        current = f"{prefix}\n{paragraph}".strip() if prefix else paragraph
    if current:
        chunks.append(current)
    return chunks or [normalized]


def _tokenize_knowledge_query(query: str) -> list[str]:
    compact = re.sub(r"\s+", "", query.strip().lower())
    terms = [term for term in re.split(r"[\s,，。！？?；;、/]+", query.lower()) if term]
    wine_terms = [
        "价格", "多少钱", "优惠", "福利", "发货", "口感", "香型", "度数", "容量", "规格", "真假", "正品",
        "送礼", "领导", "长辈", "商务", "宴请", "收藏", "聚会", "礼盒", "白兰地", "葡萄酒", "可雅", "张裕", "解百纳", "龙八",
        "养生", "保健", "未成年", "开车", "酒驾", "退款",
    ]
    terms.extend(term for term in wine_terms if term in compact)
    if compact and not terms:
        terms.append(compact)
    return sorted(set(terms), key=len, reverse=True)


def _score_knowledge_chunk(query_terms: list[str], text: str) -> tuple[float, list[str]]:
    lowered = text.lower()
    matched: list[str] = []
    score = 0.0
    for term in query_terms:
        count = lowered.count(term.lower())
        if not count:
            continue
        matched.append(term)
        score += count * (2.0 if len(term) >= 2 else 1.0)
    if matched and any(term in {"未成年", "开车", "酒驾", "养生", "保健"} for term in matched):
        score += 1.5
    return score, matched
