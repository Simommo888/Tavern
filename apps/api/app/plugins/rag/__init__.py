from __future__ import annotations

from uuid import uuid4

from apps.api.app.plugins.base import PluginCostEstimate, PluginJob, StaticPlugin


class LocalKeywordRagProvider(StaticPlugin):
    provider_id = "local_keyword_rag"
    category = "rag"
    display_name = "Local Keyword RAG"
    source_type = "builtin"
    capabilities = ("chunk", "keyword_search", "score")
    health_status = "ready"
    config_schema = {
        "type": "object",
        "properties": {
            "max_chars": {"type": "integer"},
            "overlap_chars": {"type": "integer"},
            "limit": {"type": "integer"},
        },
    }
    metadata = {"implementation": "apps.api.app.application.workbench_service.search_knowledge_with_scores"}

    def submit_job(self, payload: dict[str, object]) -> PluginJob:
        return PluginJob(job_id=f"rag-job-{uuid4().hex[:10]}", status="queued", metadata={"provider_id": self.provider_id, "payload": payload})

    def estimate_cost(self, payload: dict[str, object]) -> PluginCostEstimate:
        query = str(payload.get("query") or "")
        return PluginCostEstimate(estimated_cost=0, detail={"query_characters": len(query), "local_compute": True})
