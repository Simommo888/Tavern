from __future__ import annotations

from pathlib import Path
from typing import Callable

from apps.api.app.application.tasks.queue import FileTaskQueue
from apps.api.app.domain.tasks.entities import AsyncTask

TaskHandler = Callable[[AsyncTask], dict]


class TaskDispatcher:
    def __init__(self, workspace_root: str | Path = ".") -> None:
        self.queue = FileTaskQueue(workspace_root)
        self.handlers: dict[str, TaskHandler] = {
            "live.audience_event.received": self._ack,
            "live.anchor_reply.generate": self._ack,
            "live.speech.generate": self._ack,
            "live.compliance.review": self._ack,
            "avatar.job.generate": self._ack,
            "platform.event.ingest": self._ack,
            "production.run.started": self._ack,
        }

    def drain_once(self) -> list[AsyncTask]:
        processed: list[AsyncTask] = []
        for task in self.queue.list_queued():
            running = self.queue.mark_running(task)
            try:
                handler = self.handlers.get(running.task_type, self._ack)
                result = handler(running)
                processed.append(self.queue.mark_succeeded(running, result))
            except Exception as exc:
                processed.append(self.queue.mark_failed(running, str(exc)))
        return processed

    def _ack(self, task: AsyncTask) -> dict:
        return {"handled": True, "task_type": task.task_type, "payload": task.payload}
