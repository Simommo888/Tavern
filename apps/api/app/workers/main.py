from __future__ import annotations

from apps.api.app.application.tasks.dispatcher import TaskDispatcher
from apps.api.app.application.tasks.queue import FileTaskQueue
from apps.api.app.core.logging import configure_logging, get_logger
from apps.api.app.core.settings import get_settings

logger = get_logger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings)
    queue = FileTaskQueue(settings.workspace_root)
    if not queue.tasks.list():
        queue.publish("platform.event.ingest", {"platform": "manual", "event_type": "comment", "text": "这个适合送礼吗？"}, idempotency_key="worker-seed-platform-event")
    processed = TaskDispatcher(settings.workspace_root).drain_once()
    logger.info("Tavern worker processed tasks", extra={"processed_count": len(processed), "storage_backend": settings.storage_backend})


if __name__ == "__main__":
    main()
