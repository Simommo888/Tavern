from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class TavernSettings:
    app_name: str = "Tavern LiveOS"
    environment: str = "local"
    log_level: str = "INFO"
    workspace_root: Path = Path(".")
    storage_backend: str = "file"
    database_url: str = ""
    redis_url: str = ""
    rabbitmq_url: str = ""
    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    tts_provider: str = "edge"
    cors_origins: tuple[str, ...] = ("*",)

    @property
    def version(self) -> str:
        return "0.2.0"

    def public_health(self) -> dict[str, str]:
        return {
            "status": "ok",
            "app": self.app_name,
            "environment": self.environment,
            "storage_backend": self.storage_backend,
        }

    def readiness(self) -> dict[str, str]:
        ready = "ready"
        if self.storage_backend == "postgres" and not self.database_url:
            ready = "not_ready"
        return {
            "status": ready,
            "app": self.app_name,
            "storage_backend": self.storage_backend,
            "workspace_root": str(self.workspace_root),
        }


@lru_cache(maxsize=1)
def get_settings() -> TavernSettings:
    return TavernSettings(
        app_name=os.environ.get("TAVERN_APP_NAME", "Tavern LiveOS"),
        environment=os.environ.get("TAVERN_ENV", "local"),
        log_level=os.environ.get("TAVERN_LOG_LEVEL", "INFO"),
        workspace_root=Path(os.environ.get("TAVERN_WORKSPACE_ROOT", ".")).resolve(),
        storage_backend=os.environ.get("TAVERN_STORAGE_BACKEND", "file").strip().lower() or "file",
        database_url=os.environ.get("DATABASE_URL", ""),
        redis_url=os.environ.get("REDIS_URL", ""),
        rabbitmq_url=os.environ.get("RABBITMQ_URL", ""),
        minio_endpoint=os.environ.get("MINIO_ENDPOINT", ""),
        minio_access_key=os.environ.get("MINIO_ACCESS_KEY", ""),
        minio_secret_key=os.environ.get("MINIO_SECRET_KEY", ""),
        tts_provider=os.environ.get("TAVERN_TTS_PROVIDER", "edge"),
        cors_origins=_csv_env("TAVERN_CORS_ORIGINS", ("*",)),
    )


def _csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    return values or default
