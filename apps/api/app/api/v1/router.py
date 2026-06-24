from __future__ import annotations

from fastapi import APIRouter

from apps.api.app.api.v1.live import router as live_router
from apps.api.app.api.v1.model_gateway import router as model_gateway_router
from apps.api.app.api.v1.workbench import router as workbench_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(live_router)
api_router.include_router(model_gateway_router)
api_router.include_router(workbench_router)
