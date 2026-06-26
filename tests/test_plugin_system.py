import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.app.api.v1 import workbench as workbench_module
from apps.api.app.application.workbench_service import WorkbenchService
from apps.api.app.main import create_app
from apps.api.app.plugins.registry import default_registry


class PluginSystemTests(unittest.TestCase):
    def test_default_registry_loads_core_plugin_categories(self):
        registry = default_registry(Path(__file__).resolve().parents[1])
        provider_ids = {plugin.provider_id for plugin in registry.list()}
        self.assertIn("openai_compatible", provider_ids)
        self.assertIn("openai_compatible_tts", provider_ids)
        self.assertIn("edge_tts", provider_ids)
        self.assertIn("ffmpeg_moviepy", provider_ids)
        self.assertIn("local_keyword_rag", provider_ids)
        self.assertIn("fish_speech", provider_ids)
        self.assertIn("livetalking", provider_ids)

        self.assertEqual(registry.get("openai_compatible").category, "model")
        self.assertEqual(registry.get("ffmpeg_moviepy").category, "video")
        self.assertEqual(registry.get("local_keyword_rag").category, "rag")
        self.assertEqual(registry.health("fish_speech")["status"], "not_installed")

    def test_workbench_syncs_plugins_from_manager(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = WorkbenchService(Path(tmp))
            providers = service.list_plugins()
            provider_ids = {provider.provider_id for provider in providers}
            self.assertIn("openai_compatible", provider_ids)
            self.assertIn("ffmpeg_moviepy", provider_ids)
            self.assertIn("local_keyword_rag", provider_ids)
            self.assertIn("fish_speech", provider_ids)
            self.assertEqual(service.plugin_health("ffmpeg_moviepy")["status"], "ready")
            estimate = service.estimate_plugin_cost("local_keyword_rag", {"query": "送礼"})
            self.assertEqual(estimate["estimated_cost"], 0)
            self.assertEqual(estimate["detail"]["query_characters"], 2)

    def test_plugin_api_exposes_manager_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench_module._service = WorkbenchService(Path(tmp))
            client = TestClient(create_app())

            providers = client.get("/api/v1/plugins/providers")
            self.assertEqual(providers.status_code, 200)
            provider_ids = {item["provider_id"] for item in providers.json()["providers"]}
            self.assertIn("openai_compatible", provider_ids)
            self.assertIn("fish_speech", provider_ids)

            rag = client.get("/api/v1/plugins/providers", params={"category": "rag"})
            self.assertEqual(rag.status_code, 200)
            self.assertEqual([item["provider_id"] for item in rag.json()["providers"]], ["local_keyword_rag"])

            health = client.get("/api/v1/plugins/providers/fish_speech/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json()["health"]["status"], "not_installed")

            estimate = client.post("/api/v1/plugins/providers/edge_tts/estimate", json={"text": "欢迎来到直播间"})
            self.assertEqual(estimate.status_code, 200)
            self.assertEqual(estimate.json()["estimate"]["detail"]["characters"], 7)

            submitted = client.post("/api/v1/plugins/providers/ffmpeg_moviepy/jobs", json={"duration_seconds": 3})
            self.assertEqual(submitted.status_code, 200)
            self.assertEqual(submitted.json()["job"]["status"], "queued")


if __name__ == "__main__":
    unittest.main()
