from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from apps.api.app.application.workbench_service import WorkbenchService

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
    from apps.api.app.domain.workbench.entities import WorkflowRule

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
    from apps.api.app.domain.workbench.entities import PlatformMetricSnapshot

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
    chunks = _service.search_knowledge(str(payload.get("query") or ""), str(payload.get("product_id") or ""))
    return {"chunks": [item.model_dump() for item in chunks]}


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
