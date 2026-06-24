from __future__ import annotations

from apps.api.app.infrastructure.postgres.settings import PostgresSettings


class PostgresRepositoryNotConfigured(RuntimeError):
    pass


class PostgresWorkbenchRepository:
    def __init__(self, settings: PostgresSettings | None = None) -> None:
        self.settings = settings or PostgresSettings()
        if not self.settings.configured:
            raise PostgresRepositoryNotConfigured("DATABASE_URL must point to PostgreSQL before enabling PostgresWorkbenchRepository")

    def health(self) -> dict[str, str]:
        return {"status": "configured", "driver": "postgresql", "database_url": self.settings.database_url.split('@')[-1] if '@' in self.settings.database_url else "configured"}
