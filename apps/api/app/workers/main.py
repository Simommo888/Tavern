from __future__ import annotations

import os
from pathlib import Path

from apps.api.app.application.tasks.dispatcher import TaskDispatcher
from apps.api.app.application.tasks.queue import FileTaskQueue


def main() -> None:
    workspace_root = Path(os.environ.get("TAVERN_WORKSPACE_ROOT", ".")).resolve()
    queue = FileTaskQueue(workspace_root)
    if not queue.tasks.list():
        queue.publish("platform.event.ingest", {"platform": "manual", "event_type": "comment", "text": "这个适合送礼吗？"}, idempotency_key="worker-seed-platform-event")
    processed = TaskDispatcher(workspace_root).drain_once()
    print(f"Tavern worker processed {len(processed)} task(s).")


if __name__ == "__main__":
    main()
