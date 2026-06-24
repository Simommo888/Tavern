from __future__ import annotations

from typing import Any, TypedDict


class LiveAnchorState(TypedDict, total=False):
    tenant_id: str
    session_id: str
    audience_event_id: str
    event_text: str
    product_context: dict[str, Any]
    intent: str
    retrieved_chunks: list[dict[str, Any]]
    compliance_notes: list[str]
    draft_reply: str
    final_reply: str
    speech_artifact_id: str
    model_invocation_ids: list[str]
    errors: list[str]
