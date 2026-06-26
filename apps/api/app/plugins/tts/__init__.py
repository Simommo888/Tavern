from __future__ import annotations

from uuid import uuid4

from apps.api.app.plugins.base import NotInstalledPlugin, PluginCostEstimate, PluginJob, StaticPlugin


class OpenAICompatibleTtsProvider(StaticPlugin):
    provider_id = "openai_compatible_tts"
    category = "tts"
    display_name = "OpenAI Compatible TTS"
    source_type = "builtin"
    capabilities = ("tts", "speech_api")
    health_status = "ready"
    config_schema = {
        "type": "object",
        "properties": {
            "base_url": {"type": "string"},
            "api_key_env": {"type": "string"},
            "model": {"type": "string"},
            "voice": {"type": "string"},
        },
    }
    metadata = {"implementation": "agent_runtime.speech_tts._openai_compatible_tts"}

    def submit_job(self, payload: dict[str, object]) -> PluginJob:
        return PluginJob(job_id=f"tts-job-{uuid4().hex[:10]}", status="queued", metadata={"provider_id": self.provider_id, "payload": payload})

    def estimate_cost(self, payload: dict[str, object]) -> PluginCostEstimate:
        text = str(payload.get("text") or "")
        return PluginCostEstimate(detail={"characters": len(text)})


class EdgeTtsProvider(StaticPlugin):
    provider_id = "edge_tts"
    category = "tts"
    display_name = "Edge TTS Local Adapter"
    source_type = "builtin"
    capabilities = ("tts", "offline_demo_fallback")
    health_status = "ready"
    config_schema = {
        "type": "object",
        "properties": {
            "voice": {"type": "string"},
            "rate": {"type": "string"},
            "volume": {"type": "string"},
        },
    }
    metadata = {"implementation": "agent_runtime.speech_tts._edge_tts"}

    def submit_job(self, payload: dict[str, object]) -> PluginJob:
        return PluginJob(job_id=f"tts-job-{uuid4().hex[:10]}", status="queued", metadata={"provider_id": self.provider_id, "payload": payload})

    def estimate_cost(self, payload: dict[str, object]) -> PluginCostEstimate:
        text = str(payload.get("text") or "")
        return PluginCostEstimate(estimated_cost=0, detail={"characters": len(text), "local_or_free_provider": True})


class FishSpeechProvider(NotInstalledPlugin):
    def __init__(self, repo_url: str = "https://github.com/fishaudio/fish-speech", commit: str = "", license: str = "Apache-2.0", adapter: str = "apps/api/app/plugins/tts") -> None:
        super().__init__(
            "fish_speech",
            "tts",
            repo_url,
            ("tts", "voice_clone"),
            display_name="Fish Speech Adapter",
            commit=commit,
            license=license,
            adapter=adapter,
            metadata={"integration": "wrapper_candidate"},
        )
