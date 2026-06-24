from __future__ import annotations

from pathlib import Path

from interfaces.production import utc_now_iso
from apps.api.app.domain.tasks.entities import AsyncTask, build_task
from apps.api.app.infrastructure.repositories.file_workbench import JsonCollectionRepository


class FileTaskQueue:
    def __init__(self, workspace_root: str | Path = ".") -> None:
        self.tasks = JsonCollectionRepository(Path(workspace_root), "async_tasks", AsyncTask, "task_id")

    def publish(self, task_type: str, payload: dict, idempotency_key: str = "") -> AsyncTask:
        if idempotency_key:
            for task in self.tasks.list():
                if task.idempotency_key == idempotency_key:
                    return task
        task = build_task(task_type, payload, idempotency_key)
        return self.tasks.upsert(task)

    def list_queued(self) -> list[AsyncTask]:
        return [task for task in self.tasks.list() if task.status == "queued"]

    def mark_running(self, task: AsyncTask) -> AsyncTask:
        updated = task.model_copy(update={"status": "running", "attempts": task.attempts + 1, "updated_at": utc_now_iso()})
        return self.tasks.upsert(updated)

    def mark_succeeded(self, task: AsyncTask, result: dict) -> AsyncTask:
        updated = task.model_copy(update={"status": "succeeded", "result": result, "updated_at": utc_now_iso()})
        return self.tasks.upsert(updated)

    def mark_failed(self, task: AsyncTask, error: str) -> AsyncTask:
        updated = task.model_copy(update={"status": "failed", "error": error, "updated_at": utc_now_iso()})
        return self.tasks.upsert(updated)
