from __future__ import annotations

import logging

from apps.api.app.core.settings import TavernSettings, get_settings


def configure_logging(settings: TavernSettings | None = None) -> None:
    resolved = settings or get_settings()
    logging.basicConfig(
        level=getattr(logging, resolved.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
