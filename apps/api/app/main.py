from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Tavern AI Live Workbench API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        return {"status": "ready"}

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("apps.api.app.main:app", host="127.0.0.1", port=8770, reload=False)


if __name__ == "__main__":
    main()
