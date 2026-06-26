from __future__ import annotations

from uuid import uuid4

from apps.api.app.plugins.base import PluginCostEstimate, PluginJob, StaticPlugin


class OpenAICompatibleModelProvider(StaticPlugin):
    provider_id = "openai_compatible"
    category = "model"
    display_name = "OpenAI Compatible Model Gateway"
    source_type = "builtin"
    capabilities = ("chat", "embedding", "streaming", "tool_use")
    health_status = "ready"
    config_schema = {
        "type": "object",
        "properties": {
            "base_url": {"type": "string"},
            "api_key_env": {"type": "string"},
            "chat_model": {"type": "string"},
            "embedding_model": {"type": "string"},
        },
    }
    metadata = {"implementation": "agent_runtime.llm.ModelGateway"}

    def health_check(self) -> dict[str, str]:
        return {"status": "configured_by_model_gateway", "provider_id": self.provider_id, "category": self.category}

    def estimate_cost(self, payload: dict[str, object]) -> PluginCostEstimate:
        prompt_tokens = int(payload.get("prompt_tokens") or 0)
        completion_tokens = int(payload.get("completion_tokens") or 0)
        return PluginCostEstimate(detail={"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens})

    def submit_job(self, payload: dict[str, object]) -> PluginJob:
        return PluginJob(job_id=f"model-job-{uuid4().hex[:10]}", status="queued", metadata={"provider_id": self.provider_id, "payload": payload})

    def get_job(self, job_id: str) -> PluginJob:
        return PluginJob(job_id=job_id, status="queued", metadata={"provider_id": self.provider_id})

    def cancel_job(self, job_id: str) -> PluginJob:
        return PluginJob(job_id=job_id, status="cancelled", metadata={"provider_id": self.provider_id})
