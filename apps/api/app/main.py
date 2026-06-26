from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.api.v1.router import api_router
from apps.api.app.core.logging import configure_logging, get_logger
from apps.api.app.core.settings import get_settings

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    app = FastAPI(title=f"{settings.app_name} API", version=settings.version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    logger.info("Tavern API initialized", extra={"environment": settings.environment, "storage_backend": settings.storage_backend})

    @app.get("/health")
    def health() -> dict[str, str]:
        return settings.public_health()

    @app.get("/ready")
    def ready() -> dict[str, str]:
        return settings.readiness()

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("apps.api.app.main:app", host="127.0.0.1", port=8770, reload=False)


if __name__ == "__main__":
    main()
