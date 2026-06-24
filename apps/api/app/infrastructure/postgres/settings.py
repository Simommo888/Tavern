from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PostgresSettings:
    database_url: str = os.environ.get("DATABASE_URL", "")

    @property
    def configured(self) -> bool:
        return self.database_url.startswith("postgresql://") or self.database_url.startswith("postgresql+")
