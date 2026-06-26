from __future__ import annotations

from uuid import uuid4

from apps.api.app.plugins.base import PluginCostEstimate, PluginJob, StaticPlugin


class FfmpegMoviePyProvider(StaticPlugin):
    provider_id = "ffmpeg_moviepy"
    category = "video"
    display_name = "FFmpeg / MoviePy Composer"
    source_type = "builtin"
    capabilities = ("compose", "subtitle", "transcode")
    health_status = "ready"
    config_schema = {
        "type": "object",
        "properties": {
            "ffmpeg_path": {"type": "string"},
            "ffprobe_path": {"type": "string"},
        },
    }
    metadata = {"implementation": "utils.ffmpeg_cli"}

    def health_check(self) -> dict[str, str]:
        return {"status": "ready", "provider_id": self.provider_id, "category": self.category}

    def estimate_cost(self, payload: dict[str, object]) -> PluginCostEstimate:
        duration = float(payload.get("duration_seconds") or 0)
        return PluginCostEstimate(estimated_cost=0, detail={"duration_seconds": duration, "local_compute": True})

    def submit_job(self, payload: dict[str, object]) -> PluginJob:
        job_id = f"video-job-{uuid4().hex[:10]}"
        return PluginJob(job_id=job_id, status="queued", metadata={"provider_id": self.provider_id, "payload": payload})

    def get_job(self, job_id: str) -> PluginJob:
        return PluginJob(job_id=job_id, status="queued", metadata={"provider_id": self.provider_id})

    def cancel_job(self, job_id: str) -> PluginJob:
        return PluginJob(job_id=job_id, status="cancelled", metadata={"provider_id": self.provider_id})
