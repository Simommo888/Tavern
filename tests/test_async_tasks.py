import tempfile
import unittest
from pathlib import Path

from apps.api.app.application.live_room_service import LiveRoomService
from apps.api.app.application.tasks.dispatcher import TaskDispatcher
from apps.api.app.application.tasks.queue import FileTaskQueue
from apps.api.app.infrastructure.postgres.repositories import PostgresRepositoryNotConfigured, PostgresWorkbenchRepository
from apps.api.app.infrastructure.postgres.settings import PostgresSettings


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

    def test_dispatcher_processes_live_audience_event_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = LiveRoomService(Path(tmp))
            session = self._run(service.create_session({"product_name": "异步测试礼盒"}))
            task = service.enqueue_audience_event(session.session_id, {"text": "多少钱？", "user_name": "异步观众"})
            self.assertEqual(task.status, "queued")

            processed = TaskDispatcher(Path(tmp)).drain_once()
            self.assertEqual(processed[0].status, "succeeded")
            saved = service.get_session(session.session_id)
            self.assertEqual(saved.event_count, 1)
            self.assertEqual(saved.reply_count, 1)
            self.assertEqual(saved.recent_replies[-1].intent, "price_question")
            self.assertEqual([event.type for event in service.events(session.session_id)], ["session_created", "audience_event", "workflow_task_queued", "speech_artifact", "anchor_reply"])

    def test_postgres_repository_requires_database_url(self):
        with self.assertRaises(PostgresRepositoryNotConfigured):
            PostgresWorkbenchRepository(PostgresSettings(database_url=""))
        repo = PostgresWorkbenchRepository(PostgresSettings(database_url="postgresql://user:pass@localhost:5432/tavern"))
        self.assertEqual(repo.health()["status"], "configured")

    def _run(self, coro):
        import asyncio

        return asyncio.run(coro)


if __name__ == "__main__":
    unittest.main()
