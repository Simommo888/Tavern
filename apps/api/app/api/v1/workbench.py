from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from apps.api.app.application.workbench_service import WorkbenchService
from apps.api.app.domain.workbench.entities import (
    AgentRun,
    Asset,
    LiveComponent,
    LiveRoomComposition,
    LiveScene,
    PlatformMetricSnapshot,
    Project,
    WorkflowRule,
    WorkflowRun,
)

router = APIRouter(tags=["workbench"])
_service = WorkbenchService(Path(__file__).resolve().parents[5])


@router.get("/dashboard/summary")
def dashboard_summary() -> dict[str, Any]:
    return _service.dashboard_summary()


@router.get("/products")
def list_products() -> dict[str, Any]:
    return {"products": [item.model_dump() for item in _service.products.list()]}


@router.post("/products")
def create_product(payload: dict[str, Any]) -> dict[str, Any]:
    return {"product": _service.create_product(payload).model_dump()}


@router.get("/products/{product_id}")
def get_product(product_id: str) -> dict[str, Any]:
    try:
        return {"product": _service.products.get(product_id).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/products/{product_id}")
def update_product(product_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return {"product": _service.update_product(product_id, payload).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/products/{product_id}")
def delete_product(product_id: str) -> dict[str, str]:
    _service.products.delete(product_id)
    return {"status": "deleted"}


@router.post("/products/{product_id}/publish")
def publish_product(product_id: str) -> dict[str, Any]:
    try:
        return {"product": _service.publish_product(product_id).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/products/{product_id}/unpublish")
def unpublish_product(product_id: str) -> dict[str, Any]:
    try:
        return {"product": _service.unpublish_product(product_id).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/avatars")
def list_avatars() -> dict[str, Any]:
    return {"avatars": [item.model_dump() for item in _service.avatars.list()]}


@router.post("/avatars")
def create_avatar(payload: dict[str, Any]) -> dict[str, Any]:
    return {"avatar": _service.create_avatar(payload).model_dump()}


@router.patch("/avatars/{avatar_id}")
def update_avatar(avatar_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return {"avatar": _service.update_avatar(avatar_id, payload).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/scripts/templates")
def list_script_templates() -> dict[str, Any]:
    return {"templates": [item.model_dump() for item in _service.scripts.list()]}


@router.post("/scripts/templates")
def create_script_template(payload: dict[str, Any]) -> dict[str, Any]:
    return {"template": _service.create_script(payload).model_dump()}


@router.patch("/scripts/templates/{template_id}")
def update_script_template(template_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return {"template": _service.update_script(template_id, payload).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/scripts/templates/{template_id}")
def delete_script_template(template_id: str) -> dict[str, str]:
    _service.scripts.delete(template_id)
    return {"status": "deleted"}


@router.post("/scripts/templates/generate")
def generate_script_template(payload: dict[str, Any]) -> dict[str, Any]:
    category = str(payload.get("category") or "interaction")
    product_id = str(payload.get("product_id") or "")
    return {"template": _service.generate_script(category, product_id).model_dump()}


@router.get("/workflow/rules")
def list_workflow_rules() -> dict[str, Any]:
    return {"rules": [item.model_dump() for item in _service.workflow_rules.list()]}


@router.post("/workflow/rules")
def create_workflow_rule(payload: dict[str, Any]) -> dict[str, Any]:
    return {"rule": _service.workflow_rules.upsert(WorkflowRule.model_validate(payload)).model_dump()}


@router.patch("/workflow/rules/{rule_id}")
def update_workflow_rule(rule_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        rule = _service.workflow_rules.get(rule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"rule": _service.workflow_rules.upsert(rule.model_copy(update=payload)).model_dump()}


@router.delete("/workflow/rules/{rule_id}")
def delete_workflow_rule(rule_id: str) -> dict[str, str]:
    _service.workflow_rules.delete(rule_id)
    return {"status": "deleted"}


@router.get("/platform/accounts")
def list_platform_accounts() -> dict[str, Any]:
    return {"accounts": [item.model_dump() for item in _service.platform_accounts.list()]}


@router.get("/platform/metrics")
def list_platform_metrics() -> dict[str, Any]:
    return {"metrics": [item.model_dump() for item in _service.metrics.list()]}


@router.post("/platform/metrics")
def create_platform_metric(payload: dict[str, Any]) -> dict[str, Any]:
    return {"metric": _service.metrics.upsert(PlatformMetricSnapshot.model_validate(payload)).model_dump()}


@router.get("/knowledge/documents")
def list_knowledge_documents() -> dict[str, Any]:
    return {"documents": [item.model_dump() for item in _service.knowledge_documents.list()]}


@router.post("/knowledge/documents")
def create_knowledge_document(payload: dict[str, Any]) -> dict[str, Any]:
    return {"document": _service.create_knowledge_document(payload).model_dump()}


@router.delete("/knowledge/documents/{document_id}")
def delete_knowledge_document(document_id: str) -> dict[str, str]:
    _service.knowledge_documents.delete(document_id)
    remaining_chunks = [chunk for chunk in _service.knowledge_chunks.list() if chunk.document_id != document_id]
    _service.knowledge_chunks._write(remaining_chunks)
    return {"status": "deleted"}


@router.post("/knowledge/documents/{document_id}/index")
def index_knowledge_document(document_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        document = _service.index_knowledge_document(document_id, str((payload or {}).get("text") or ""))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"document": document.model_dump(), "chunks": [item.model_dump() for item in _service.knowledge_chunks.list() if item.document_id == document_id]}


@router.post("/knowledge/search")
def search_knowledge(payload: dict[str, Any]) -> dict[str, Any]:
    results = _service.search_knowledge_with_scores(
        str(payload.get("query") or ""),
        product_id=str(payload.get("product_id") or ""),
        limit=int(payload.get("limit") or 5),
    )
    return {
        "chunks": [item["chunk"].model_dump() for item in results],
        "results": [{"score": item["score"], "matched_terms": item["matched_terms"], "chunk": item["chunk"].model_dump()} for item in results],
    }


@router.get("/model-gateway/providers")
def list_model_providers() -> dict[str, Any]:
    return {"providers": [item.model_dump() for item in _service.model_providers.list()]}


@router.get("/model-gateway/prompts")
def list_prompt_templates() -> dict[str, Any]:
    return {"prompts": [item.model_dump() for item in _service.prompt_templates.list()]}


@router.post("/avatars/{avatar_id}/jobs")
def create_avatar_job(avatar_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        _service.avatars.get(avatar_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"job": _service.create_avatar_job({**payload, "avatar_id": avatar_id}).model_dump()}


@router.get("/avatars/jobs/{job_id}")
def get_avatar_job(job_id: str) -> dict[str, Any]:
    try:
        return {"job": _service.avatar_jobs.get(job_id).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/platform/events")
def list_platform_events() -> dict[str, Any]:
    return {"events": [item.model_dump() for item in _service.platform_events.list()]}


@router.post("/platform/events")
def ingest_platform_event(payload: dict[str, Any]) -> dict[str, Any]:
    return {"event": _service.ingest_platform_event(payload).model_dump()}


@router.get("/projects")
def list_projects() -> dict[str, Any]:
    return {"projects": [item.model_dump() for item in _service.projects.list()]}


@router.post("/projects")
def create_project(payload: dict[str, Any]) -> dict[str, Any]:
    return {"project": _service.create_project(payload).model_dump()}


@router.get("/mvp/live-plans")
def list_mvp_live_plans(project_id: str = "") -> dict[str, Any]:
    return {"plans": [item.model_dump() for item in _service.list_mvp_live_plans(project_id)]}


@router.get("/mvp/live-plans/{plan_id}")
def get_mvp_live_plan(plan_id: str) -> dict[str, Any]:
    try:
        return {"plan": _service.get_mvp_live_plan(plan_id).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/mvp/live-plans/run")
def run_mvp_live_commerce(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return {"plan": _service.run_mvp_live_commerce(payload).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}")
def get_project(project_id: str) -> dict[str, Any]:
    try:
        return {"project": _service.projects.get(project_id).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/projects/{project_id}")
def update_project(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return {"project": _service.update_project(project_id, payload).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/agents")
def list_agents() -> dict[str, Any]:
    return {"agents": [item.model_dump() for item in _service.agent_profiles.list()]}


@router.get("/agents/runs")
def list_all_agent_runs() -> dict[str, Any]:
    return {"runs": [item.model_dump() for item in _service.agent_runs.list()]}


@router.get("/assets")
def list_all_assets() -> dict[str, Any]:
    return {"assets": [item.model_dump() for item in _service.assets.list()]}


@router.get("/components")
def list_all_components() -> dict[str, Any]:
    return {"components": [item.model_dump() for item in _service.components.list()]}


@router.get("/scenes")
def list_all_live_scenes() -> dict[str, Any]:
    return {"scenes": [item.model_dump() for item in _service.live_scenes.list()]}


@router.get("/live-room-compositions")
def list_all_live_room_compositions() -> dict[str, Any]:
    return {"compositions": [item.model_dump() for item in _service.live_room_compositions.list()]}


@router.get("/workflow/definitions")
def list_workflow_definitions() -> dict[str, Any]:
    return {"definitions": [item.model_dump() for item in _service.workflow_definitions.list()]}


@router.get("/workflow/runs")
def list_all_workflow_runs() -> dict[str, Any]:
    return {"runs": [item.model_dump() for item in _service.workflow_runs.list()]}


@router.get("/workflow/runs/{workflow_run_id}/nodes")
def list_workflow_node_runs(workflow_run_id: str) -> dict[str, Any]:
    return {"nodes": [item.model_dump() for item in _service.workflow_node_runs.list() if item.workflow_run_id == workflow_run_id]}


@router.get("/prompt-versions")
def list_prompt_versions() -> dict[str, Any]:
    return {"prompt_versions": [item.model_dump() for item in _service.prompt_versions.list()]}


@router.get("/plugins/providers")
def list_plugin_providers(category: str = "") -> dict[str, Any]:
    return {"providers": [item.model_dump() for item in _service.list_plugins(category)]}


@router.get("/plugins/providers/{provider_id}/health")
def get_plugin_health(provider_id: str) -> dict[str, Any]:
    try:
        return {"health": _service.plugin_health(provider_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/plugins/providers/{provider_id}/estimate")
def estimate_plugin_cost(provider_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return {"estimate": _service.estimate_plugin_cost(provider_id, payload)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/plugins/providers/{provider_id}/jobs")
def submit_plugin_job(provider_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return {"job": _service.submit_plugin_job(provider_id, payload)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/plugins/providers/{provider_id}/jobs/{job_id}")
def get_plugin_job(provider_id: str, job_id: str) -> dict[str, Any]:
    try:
        return {"job": _service.get_plugin_job(provider_id, job_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/plugins/providers/{provider_id}/jobs/{job_id}/cancel")
def cancel_plugin_job(provider_id: str, job_id: str) -> dict[str, Any]:
    try:
        return {"job": _service.cancel_plugin_job(provider_id, job_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/analytics/overview")
def analytics_overview() -> dict[str, Any]:
    return _service.analytics_overview()


@router.get("/projects/{project_id}/agent-runs")
def list_project_agent_runs(project_id: str) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"runs": [item.model_dump() for item in _service.list_agent_runs(project_id)]}


@router.post("/projects/{project_id}/agent-runs")
def create_project_agent_run(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"run": _service.agent_runs.upsert(AgentRun.model_validate({**payload, "project_id": project_id})).model_dump()}


@router.get("/projects/{project_id}/assets")
def list_project_assets(project_id: str) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"assets": [item.model_dump() for item in _service.list_assets(project_id)]}


@router.post("/projects/{project_id}/assets")
def create_project_asset(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"asset": _service.create_asset(project_id, payload).model_dump()}


@router.get("/projects/{project_id}/components")
def list_project_components(project_id: str) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"components": [item.model_dump() for item in _service.list_components(project_id)]}


@router.post("/projects/{project_id}/components")
def create_project_component(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"component": _service.create_component(project_id, payload).model_dump()}


@router.get("/projects/{project_id}/scenes")
def list_project_scenes(project_id: str) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"scenes": [item.model_dump() for item in _service.list_live_scenes(project_id)]}


@router.post("/projects/{project_id}/scenes")
def create_project_scene(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"scene": _service.create_live_scene(project_id, payload).model_dump()}


@router.get("/projects/{project_id}/live-rooms")
def list_project_live_rooms(project_id: str) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"compositions": [item.model_dump() for item in _service.list_live_room_compositions(project_id)]}


@router.post("/projects/{project_id}/live-rooms")
def create_project_live_room(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"composition": _service.create_live_room(project_id, payload).model_dump()}


@router.get("/projects/{project_id}/workflow-runs")
def list_project_workflow_runs(project_id: str) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"runs": [item.model_dump() for item in _service.list_workflow_runs(project_id)]}


@router.post("/projects/{project_id}/workflow-runs")
def create_project_workflow_run(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"run": _service.workflow_runs.upsert(WorkflowRun.model_validate({**payload, "project_id": project_id})).model_dump()}


@router.get("/projects/{project_id}/analytics/best-practices")
def list_project_best_practices(project_id: str) -> dict[str, Any]:
    _ensure_project(project_id)
    return {"best_practices": [item.model_dump() for item in _service.list_best_practices(project_id)]}


@router.post("/projects/{project_id}/analytics/best-practices/{best_practice_id}/clone")
def clone_project_best_practice(project_id: str, best_practice_id: str) -> dict[str, Any]:
    _ensure_project(project_id)
    try:
        return {"composition": _service.clone_best_practice(best_practice_id, target_project_id=project_id).model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/analytics/overview")
def project_analytics_overview(project_id: str) -> dict[str, Any]:
    _ensure_project(project_id)
    return _service.analytics_overview(project_id)


def _ensure_project(project_id: str) -> Project:
    try:
        return _service.projects.get(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
