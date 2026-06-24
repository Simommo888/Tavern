from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from interfaces.production import utc_now_iso

TaskStatus = Literal["queued", "running", "succeeded", "failed"]
TaskType = Literal[
    "live.audience_event.received",
    "live.anchor_reply.generate",
    "live.speech.generate",
    "live.compliance.review",
    "avatar.job.generate",
    "platform.event.ingest",
    "production.run.started",
]


class AsyncTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task-{uuid4().hex[:10]}")
    task_type: TaskType
    routing_key: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = "queued"
    result: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    idempotency_key: str = ""
    attempts: int = 0
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


def build_task(task_type: TaskType, payload: dict[str, Any], idempotency_key: str = "") -> AsyncTask:
    return AsyncTask(task_type=task_type, routing_key=task_type, payload=payload, idempotency_key=idempotency_key or f"{task_type}:{uuid4().hex}")
