import tempfile
import unittest
from pathlib import Path

from apps.api.app.application.tasks.dispatcher import TaskDispatcher
from apps.api.app.application.tasks.queue import FileTaskQueue


class AsyncTaskTests(unittest.TestCase):
    def test_file_task_queue_is_idempotent_and_dispatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue = FileTaskQueue(Path(tmp))
            first = queue.publish("platform.event.ingest", {"text": "测试弹幕"}, idempotency_key="event-1")
            second = queue.publish("platform.event.ingest", {"text": "测试弹幕"}, idempotency_key="event-1")
            self.assertEqual(first.task_id, second.task_id)
            self.assertEqual(len(queue.list_queued()), 1)

            processed = TaskDispatcher(Path(tmp)).drain_once()
            self.assertEqual(len(processed), 1)
            self.assertEqual(processed[0].status, "succeeded")
            self.assertEqual(processed[0].result["task_type"], "platform.event.ingest")


if __name__ == "__main__":
    unittest.main()
