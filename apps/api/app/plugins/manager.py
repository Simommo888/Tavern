from __future__ import annotations

from collections import defaultdict
from typing import Any

from apps.api.app.plugins.base import LiveOSPlugin, PluginCostEstimate, PluginJob, PluginManifest


class PluginManager:
    """Runtime boundary for Plugin Interface -> Manager -> Loader -> Implementation."""

    def __init__(self, plugins: list[LiveOSPlugin] | None = None) -> None:
        self._providers: dict[str, LiveOSPlugin] = {}
        self._by_category: dict[str, list[str]] = defaultdict(list)
        for plugin in plugins or []:
            self.register(plugin)

    def register(self, plugin: LiveOSPlugin) -> None:
        if plugin.provider_id in self._providers:
            old_category = self._providers[plugin.provider_id].category
            self._by_category[old_category] = [provider_id for provider_id in self._by_category[old_category] if provider_id != plugin.provider_id]
        self._providers[plugin.provider_id] = plugin
        self._by_category[plugin.category].append(plugin.provider_id)

    def get(self, provider_id: str) -> LiveOSPlugin:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise KeyError(f"Unknown plugin provider: {provider_id}") from exc

    def list(self, category: str | None = None) -> list[LiveOSPlugin]:
        if category is None:
            return list(self._providers.values())
        return [self._providers[provider_id] for provider_id in self._by_category.get(category, [])]

    def manifests(self, category: str | None = None) -> list[PluginManifest]:
        return [plugin.manifest() for plugin in self.list(category)]

    def health(self, provider_id: str | None = None) -> dict[str, Any]:
        if provider_id:
            plugin = self.get(provider_id)
            return plugin.health_check()
        return {plugin.provider_id: plugin.health_check() for plugin in self.list()}

    def estimate_cost(self, provider_id: str, payload: dict[str, Any]) -> PluginCostEstimate:
        return self.get(provider_id).estimate_cost(payload)

    def submit_job(self, provider_id: str, payload: dict[str, Any]) -> PluginJob:
        return self.get(provider_id).submit_job(payload)

    def get_job(self, provider_id: str, job_id: str) -> PluginJob:
        return self.get(provider_id).get_job(job_id)

    def cancel_job(self, provider_id: str, job_id: str) -> PluginJob:
        return self.get(provider_id).cancel_job(job_id)
