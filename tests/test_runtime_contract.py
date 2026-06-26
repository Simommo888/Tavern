import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.app.core.settings import get_settings
from apps.api.app.main import create_app


class RuntimeContractTests(unittest.TestCase):
    def tearDown(self):
        get_settings.cache_clear()

    def test_settings_reads_unified_tavern_environment(self):
        get_settings.cache_clear()
        with patch.dict(os.environ, {
            "TAVERN_APP_NAME": "Tavern TestOS",
            "TAVERN_ENV": "ci",
            "TAVERN_LOG_LEVEL": "DEBUG",
            "TAVERN_WORKSPACE_ROOT": "/tmp/tavern",
            "TAVERN_STORAGE_BACKEND": "file",
            "TAVERN_CORS_ORIGINS": "http://localhost:5180,http://127.0.0.1:5180",
            "DATABASE_URL": "postgresql://example",
            "REDIS_URL": "redis://example",
            "RABBITMQ_URL": "amqp://example",
            "MINIO_ENDPOINT": "http://minio:9000",
        }, clear=True):
            settings = get_settings()
            self.assertEqual(settings.app_name, "Tavern TestOS")
            self.assertEqual(settings.environment, "ci")
            self.assertEqual(settings.log_level, "DEBUG")
            self.assertEqual(settings.storage_backend, "file")
            self.assertEqual(settings.database_url, "postgresql://example")
            self.assertEqual(settings.cors_origins, ("http://localhost:5180", "http://127.0.0.1:5180"))

    def test_health_and_readiness_expose_runtime_contract(self):
        get_settings.cache_clear()
        with patch.dict(os.environ, {"TAVERN_ENV": "ci", "TAVERN_STORAGE_BACKEND": "file"}, clear=True):
            client = TestClient(create_app())
            health = client.get("/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json()["app"], "Tavern LiveOS")
            self.assertEqual(health.json()["environment"], "ci")
            self.assertEqual(health.json()["storage_backend"], "file")
            ready = client.get("/ready")
            self.assertEqual(ready.status_code, 200)
            self.assertEqual(ready.json()["status"], "ready")

    def test_postgres_readiness_requires_database_url(self):
        get_settings.cache_clear()
        with patch.dict(os.environ, {"TAVERN_STORAGE_BACKEND": "postgres"}, clear=True):
            client = TestClient(create_app())
            self.assertEqual(client.get("/ready").json()["status"], "not_ready")


if __name__ == "__main__":
    unittest.main()
