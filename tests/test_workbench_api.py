import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.app.api.v1 import live as live_module
from apps.api.app.api.v1 import workbench as workbench_module
from apps.api.app.agents.live_anchor_graph import LiveAnchorGraph
from apps.api.app.application.live_room_service import LiveRoomService
from apps.api.app.application.workbench_service import WorkbenchService
from apps.api.app.main import create_app


class WorkbenchApiTests(unittest.TestCase):
    def test_live_api_v1_creates_session_and_reply(self):
        with tempfile.TemporaryDirectory() as tmp:
            live_module._service = LiveRoomService(Path(tmp))
            client = TestClient(create_app())

            created = client.post("/api/v1/live/sessions", json={"product_name": "测试礼盒"})
            self.assertEqual(created.status_code, 200)
            session_id = created.json()["session"]["session_id"]

            reply = client.post(f"/api/v1/live/sessions/{session_id}/events", json={"text": "多少钱？", "user_name": "测试观众"})
            self.assertEqual(reply.status_code, 200)
            self.assertEqual(reply.json()["reply"]["intent"], "price_question")
            self.assertTrue(reply.json()["reply"]["speech_audio_url"].startswith("/api/v1/live/sessions/"))

            snapshot = client.get(f"/api/v1/live/sessions/{session_id}")
            self.assertEqual(snapshot.status_code, 200)
            self.assertEqual([event["type"] for event in snapshot.json()["events"]], ["session_created", "audience_event", "speech_artifact", "anchor_reply"])

    def test_workbench_business_apis_expose_seeded_operational_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench_module._service = WorkbenchService(Path(tmp))
            client = TestClient(create_app())

            summary = client.get("/api/v1/dashboard/summary")
            self.assertEqual(summary.status_code, 200)
            self.assertEqual(summary.json()["live_status"], "running")
            self.assertGreater(summary.json()["online_users"], 0)

            products = client.get("/api/v1/products")
            self.assertEqual(products.status_code, 200)
            self.assertEqual(products.json()["products"][0]["status"], "published")

            generated = client.post("/api/v1/scripts/templates/generate", json={"category": "sales"})
            self.assertEqual(generated.status_code, 200)
            self.assertTrue(generated.json()["template"]["ai_generated"])

            rules = client.get("/api/v1/workflow/rules")
            self.assertEqual(rules.status_code, 200)
            self.assertGreaterEqual(len(rules.json()["rules"]), 3)

            metrics = client.get("/api/v1/platform/metrics")
            self.assertEqual(metrics.status_code, 200)
            self.assertGreater(metrics.json()["metrics"][0]["gmv"], 0)

    def test_rag_model_avatar_and_platform_apis(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench_module._service = WorkbenchService(Path(tmp))
            client = TestClient(create_app())

            documents = client.get("/api/v1/knowledge/documents")
            self.assertEqual(documents.status_code, 200)
            self.assertEqual(documents.json()["documents"][0]["status"], "indexed")

            search = client.post("/api/v1/knowledge/search", json={"query": "送礼 商务宴请"})
            self.assertEqual(search.status_code, 200)
            self.assertTrue(search.json()["chunks"])

            providers = client.get("/api/v1/model-gateway/providers")
            self.assertEqual(providers.status_code, 200)
            self.assertEqual({item["name"] for item in providers.json()["providers"]}, {"gpt", "claude", "gemini"})

            prompts = client.get("/api/v1/model-gateway/prompts")
            self.assertEqual(prompts.status_code, 200)
            self.assertEqual(prompts.json()["prompts"][0]["purpose"], "live_reply")

            avatar_id = client.get("/api/v1/avatars").json()["avatars"][0]["avatar_id"]
            job = client.post(f"/api/v1/avatars/{avatar_id}/jobs", json={"input_text": "欢迎来到直播间"})
            self.assertEqual(job.status_code, 200)
            self.assertEqual(job.json()["job"]["provider_job_id"], "heygen-dry-run")

            platform_event = client.post("/api/v1/platform/events", json={"platform": "manual", "event_type": "comment", "text": "真假怎么保证？"})
            self.assertEqual(platform_event.status_code, 200)
            self.assertEqual(platform_event.json()["event"]["text"], "真假怎么保证？")

    def test_live_anchor_graph_produces_compliant_reply(self):
        result = LiveAnchorGraph().run({"event_text": "喝了是不是养生？", "product_context": {"product_name": "测试酒"}})
        self.assertEqual(result["intent"], "compliance_risk")
        self.assertIn("不能宣传养生", result["final_reply"])


if __name__ == "__main__":
    unittest.main()
