from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any

import aiohttp
import requests


@dataclass(slots=True)
class HeyGenGenerationResult:
    provider_job_id: str = ""
    video_url: str = ""
    video_bytes: bytes | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    def save(self, path: str) -> None:
        if self.video_bytes is not None:
            with open(path, "wb") as handle:
                handle.write(self.video_bytes)
            return
        if not self.video_url:
            raise RuntimeError("HeyGen result has neither video bytes nor video URL")
        response = requests.get(self.video_url, timeout=(10, 300))
        response.raise_for_status()
        with open(path, "wb") as handle:
            handle.write(response.content)


class DigitalHumanGeneratorHeyGenAPI:
    """Small HeyGen API wrapper for digital-human live commerce clips.

    The wrapper keeps API keys out of prompts and tool arguments by reading them
    from environment variables by default. Tests and dry-runs can pass
    ``dry_run=True`` to avoid real network calls.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        avatar_id: str | None = None,
        voice_id: str | None = None,
        poll_interval_seconds: float = 5.0,
        timeout_seconds: float = 600.0,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("HEYGEN_API_KEY", "")
        self.base_url = (base_url or os.environ.get("HEYGEN_BASE_URL", "https://api.heygen.com")).rstrip("/")
        self.avatar_id = avatar_id or os.environ.get("HEYGEN_AVATAR_ID", "")
        self.voice_id = voice_id or os.environ.get("HEYGEN_VOICE_ID", "")
        self.poll_interval_seconds = poll_interval_seconds
        self.timeout_seconds = timeout_seconds

    async def generate_live_room_segment(
        self,
        *,
        script_text: str,
        avatar_id: str = "",
        voice_id: str = "",
        background_asset_path: str = "",
        product_asset_paths: list[str] | None = None,
        aspect_ratio: str = "16:9",
        resolution: str = "1080p",
        metadata: dict[str, Any] | None = None,
        progress=None,
        dry_run: bool = False,
    ) -> HeyGenGenerationResult:
        avatar = avatar_id or self.avatar_id
        voice = voice_id or self.voice_id
        if dry_run or os.environ.get("HEYGEN_DRY_RUN", "").lower() in {"1", "true", "yes", "on"}:
            payload = {
                "dry_run": True,
                "avatar_id": avatar,
                "voice_id": voice,
                "script_text": script_text,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "metadata": metadata or {},
            }
            if progress:
                progress("heygen_dry_run", "Prepared dry-run HeyGen digital human clip", {"avatar_id": avatar, "voice_id": voice})
            return HeyGenGenerationResult(provider_job_id="heygen-dry-run", video_bytes=b"HEYGEN_DRY_RUN_VIDEO_PLACEHOLDER", raw_response=payload)
        if not self.api_key:
            raise RuntimeError("HEYGEN_API_KEY is required for HeyGen digital human generation")
        if not avatar or not voice:
            raise RuntimeError("HEYGEN_AVATAR_ID and HEYGEN_VOICE_ID are required for HeyGen digital human generation")

        product_asset_paths = product_asset_paths or []
        payload = self._build_payload(
            script_text=script_text,
            avatar_id=avatar,
            voice_id=voice,
            background_asset_path=background_asset_path,
            product_asset_paths=product_asset_paths,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            metadata=metadata or {},
        )
        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json", "Accept": "application/json"}
        timeout = aiohttp.ClientTimeout(total=min(self.timeout_seconds, 120.0))
        if progress:
            progress("heygen_create", "Creating HeyGen digital human video task", {"avatar_id": avatar, "voice_id": voice})
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{self.base_url}/v2/video/generate", headers=headers, json=payload) as response:
                create_payload = await response.json(content_type=None)
                if response.status >= 400:
                    raise RuntimeError(f"HeyGen create failed with HTTP {response.status}: {create_payload}")
        job_id = _dig(create_payload, "data", "video_id") or create_payload.get("video_id") or create_payload.get("id")
        if not job_id:
            raise RuntimeError(f"HeyGen create response missing video id: {create_payload}")
        if progress:
            progress("heygen_task_created", "HeyGen digital human task created", {"provider_job_id": job_id})
        status_payload = await self._poll_status(job_id, headers, progress)
        video_url = _dig(status_payload, "data", "video_url") or status_payload.get("video_url") or status_payload.get("url")
        if not video_url:
            raise RuntimeError(f"HeyGen completed response missing video URL: {status_payload}")
        return HeyGenGenerationResult(provider_job_id=str(job_id), video_url=str(video_url), raw_response={"create": create_payload, "status": status_payload})

    def _build_payload(self, *, script_text: str, avatar_id: str, voice_id: str, background_asset_path: str, product_asset_paths: list[str], aspect_ratio: str, resolution: str, metadata: dict[str, Any]) -> dict[str, Any]:
        width, height = _resolution_for(aspect_ratio, resolution)
        payload: dict[str, Any] = {
            "video_inputs": [
                {
                    "character": {"type": "avatar", "avatar_id": avatar_id},
                    "voice": {"type": "text", "input_text": script_text, "voice_id": voice_id},
                    "background": _background_payload(background_asset_path),
                }
            ],
            "dimension": {"width": width, "height": height},
            "metadata": {"product_asset_paths": product_asset_paths, **metadata},
        }
        return payload

    async def _poll_status(self, job_id: str, headers: dict[str, str], progress) -> dict[str, Any]:
        deadline = asyncio.get_running_loop().time() + self.timeout_seconds
        timeout = aiohttp.ClientTimeout(total=60.0)
        last_payload: dict[str, Any] = {}
        while asyncio.get_running_loop().time() < deadline:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/v1/video_status.get", headers=headers, params={"video_id": job_id}) as response:
                    payload = await response.json(content_type=None)
                    if response.status >= 400:
                        raise RuntimeError(f"HeyGen status failed with HTTP {response.status}: {payload}")
            last_payload = payload
            status = str(_dig(payload, "data", "status") or payload.get("status") or "").lower()
            if progress:
                progress("heygen_status", f"HeyGen status: {status or 'unknown'}", {"provider_job_id": job_id, "status": status})
            if status in {"completed", "complete", "success", "succeeded"}:
                return payload
            if status in {"failed", "error", "cancelled", "canceled"}:
                raise RuntimeError(f"HeyGen task {job_id} failed: {payload}")
            await asyncio.sleep(self.poll_interval_seconds)
        raise RuntimeError(f"HeyGen task {job_id} timed out after {self.timeout_seconds:g}s; last_payload={last_payload}")


def _dig(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _resolution_for(aspect_ratio: str, resolution: str) -> tuple[int, int]:
    if aspect_ratio == "9:16":
        return (720, 1280) if resolution == "720p" else (1080, 1920)
    if aspect_ratio == "1:1":
        return (720, 720) if resolution == "720p" else (1080, 1080)
    return (1280, 720) if resolution == "720p" else (1920, 1080)


def _background_payload(path: str) -> dict[str, Any]:
    if path:
        return {"type": "image", "url": path}
    return {"type": "color", "value": "#111111"}
