from __future__ import annotations

from pathlib import Path
from typing import Any

from apps.api.app.plugins.base import LiveOSPlugin, PluginCostEstimate, PluginJob, PluginManifest
from apps.api.app.plugins.loader import PluginLoader
from apps.api.app.plugins.manager import PluginManager


class PluginRegistry:
    """Backward-compatible facade over PluginManager."""

    def __init__(self, manager: PluginManager | None = None) -> None:
        self._manager = manager or PluginManager()

    def register(self, plugin: LiveOSPlugin) -> None:
        self._manager.register(plugin)

    def get(self, provider_id: str) -> LiveOSPlugin:
        return self._manager.get(provider_id)

    def list(self, category: str | None = None) -> list[LiveOSPlugin]:
        return self._manager.list(category)

    def manifests(self, category: str | None = None) -> list[PluginManifest]:
        return self._manager.manifests(category)

    def health(self, provider_id: str | None = None) -> dict[str, Any]:
        return self._manager.health(provider_id)

    def estimate_cost(self, provider_id: str, payload: dict[str, Any]) -> PluginCostEstimate:
        return self._manager.estimate_cost(provider_id, payload)

    def submit_job(self, provider_id: str, payload: dict[str, Any]) -> PluginJob:
        return self._manager.submit_job(provider_id, payload)

    def get_job(self, provider_id: str, job_id: str) -> PluginJob:
        return self._manager.get_job(provider_id, job_id)

    def cancel_job(self, provider_id: str, job_id: str) -> PluginJob:
        return self._manager.cancel_job(provider_id, job_id)


def build_plugin_manager(workspace_root: str | Path = ".") -> PluginManager:
    return PluginManager(PluginLoader(workspace_root).load())


def default_registry(workspace_root: str | Path = ".") -> PluginRegistry:
    return PluginRegistry(build_plugin_manager(workspace_root))
