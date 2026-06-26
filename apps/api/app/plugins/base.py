from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

PluginCategory = Literal["model", "tts", "avatar", "video", "streaming", "workflow", "rag", "storage"]
PluginSourceType = Literal["builtin", "github", "api", "local_service"]


@dataclass(frozen=True)
class PluginManifest:
    provider_id: str
    category: str
    display_name: str
    source_type: str = "builtin"
    repo_url: str = ""
    commit: str = ""
    license: str = ""
    capabilities: tuple[str, ...] = ()
    health_status: str = "unknown"
    adapter: str = ""
    config_schema: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PluginJob:
    job_id: str
    status: str
    output_uri: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PluginCostEstimate:
    estimated_cost: float = 0
    currency: str = "USD"
    detail: dict[str, Any] = field(default_factory=dict)


class LiveOSPlugin(Protocol):
    provider_id: str
    category: str
    display_name: str
    source_type: str
    repo_url: str
    commit: str
    license: str
    capabilities: tuple[str, ...]
    config_schema: dict[str, Any]
    metadata: dict[str, Any]

    def manifest(self) -> PluginManifest: ...

    def health_check(self) -> dict[str, Any]: ...

    def estimate_cost(self, payload: dict[str, Any]) -> PluginCostEstimate: ...

    def submit_job(self, payload: dict[str, Any]) -> PluginJob: ...

    def get_job(self, job_id: str) -> PluginJob: ...

    def cancel_job(self, job_id: str) -> PluginJob: ...


class StaticPlugin:
    provider_id = "static"
    category = "workflow"
    display_name = "Static Plugin"
    source_type = "builtin"
    repo_url = ""
    commit = ""
    license = ""
    capabilities: tuple[str, ...] = ()
    config_schema: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    health_status = "ready"

    def manifest(self) -> PluginManifest:
        return plugin_manifest(self)

    def health_check(self) -> dict[str, Any]:
        return {"status": self.health_status, "provider_id": self.provider_id, "category": self.category}

    def estimate_cost(self, payload: dict[str, Any]) -> PluginCostEstimate:
        return PluginCostEstimate(detail={"payload_keys": sorted(payload)})

    def submit_job(self, payload: dict[str, Any]) -> PluginJob:
        return PluginJob(job_id=f"{self.provider_id}-job", status="queued", metadata={"provider_id": self.provider_id, "payload": payload})

    def get_job(self, job_id: str) -> PluginJob:
        return PluginJob(job_id=job_id, status="queued", metadata={"provider_id": self.provider_id})

    def cancel_job(self, job_id: str) -> PluginJob:
        return PluginJob(job_id=job_id, status="cancelled", metadata={"provider_id": self.provider_id})


class NotInstalledPlugin(StaticPlugin):
    source_type = "github"
    health_status = "not_installed"

    def __init__(
        self,
        provider_id: str,
        category: str,
        repo_url: str = "",
        capabilities: tuple[str, ...] = (),
        *,
        display_name: str = "",
        commit: str = "",
        license: str = "",
        adapter: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.provider_id = provider_id
        self.category = category
        self.display_name = display_name or provider_id.replace("_", " ").title()
        self.repo_url = repo_url
        self.commit = commit
        self.license = license
        self.capabilities = capabilities
        self.config_schema = {}
        self.metadata = {"adapter": adapter, **(metadata or {})}

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "not_installed",
            "provider_id": self.provider_id,
            "category": self.category,
            "repo_url": self.repo_url,
            "adapter": self.metadata.get("adapter", ""),
        }

    def estimate_cost(self, payload: dict[str, Any]) -> PluginCostEstimate:
        return PluginCostEstimate(detail={"reason": "provider_not_installed", "payload_keys": sorted(payload)})

    def submit_job(self, payload: dict[str, Any]) -> PluginJob:
        return PluginJob(
            job_id=f"{self.provider_id}-not-installed",
            status="failed",
            error=f"{self.provider_id} is not installed. See third_party/manifest.json.",
            metadata={"provider_id": self.provider_id, "repo_url": self.repo_url},
        )

    def get_job(self, job_id: str) -> PluginJob:
        return PluginJob(job_id=job_id, status="failed", error=f"{self.provider_id} is not installed.")

    def cancel_job(self, job_id: str) -> PluginJob:
        return PluginJob(job_id=job_id, status="cancelled", metadata={"provider_id": self.provider_id})


def plugin_manifest(plugin: LiveOSPlugin) -> PluginManifest:
    return PluginManifest(
        provider_id=plugin.provider_id,
        category=plugin.category,
        display_name=getattr(plugin, "display_name", plugin.provider_id),
        source_type=getattr(plugin, "source_type", "builtin"),
        repo_url=getattr(plugin, "repo_url", ""),
        commit=getattr(plugin, "commit", ""),
        license=getattr(plugin, "license", ""),
        capabilities=tuple(getattr(plugin, "capabilities", ())),
        health_status=str(plugin.health_check().get("status", "unknown")),
        config_schema=dict(getattr(plugin, "config_schema", {}) or {}),
        metadata=dict(getattr(plugin, "metadata", {}) or {}),
    )
