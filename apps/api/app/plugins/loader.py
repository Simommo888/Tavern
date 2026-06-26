from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apps.api.app.plugins.avatar import LiveTalkingAvatarProvider, MuseTalkAvatarProvider, SadTalkerAvatarProvider
from apps.api.app.plugins.base import LiveOSPlugin, NotInstalledPlugin
from apps.api.app.plugins.model.openai_compatible import OpenAICompatibleModelProvider
from apps.api.app.plugins.rag import LocalKeywordRagProvider
from apps.api.app.plugins.tts import CosyVoiceHttpTtsProvider, EdgeTtsProvider, FishSpeechProvider, OpenAICompatibleTtsProvider
from apps.api.app.plugins.video.ffmpeg_moviepy import FfmpegMoviePyProvider


class PluginLoader:
    """Loads built-in adapters and third-party manifest candidates."""

    def __init__(self, workspace_root: str | Path = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()

    def load(self) -> list[LiveOSPlugin]:
        plugins: list[LiveOSPlugin] = [
            OpenAICompatibleModelProvider(),
            CosyVoiceHttpTtsProvider(self.workspace_root),
            OpenAICompatibleTtsProvider(),
            EdgeTtsProvider(),
            FfmpegMoviePyProvider(),
            LocalKeywordRagProvider(),
        ]
        plugins.extend(self._third_party_candidates())
        return _dedupe_by_provider_id(plugins)

    def _third_party_candidates(self) -> list[LiveOSPlugin]:
        manifest_path = self.workspace_root / "third_party" / "manifest.json"
        if not manifest_path.exists():
            return [
                FishSpeechProvider(),
                LiveTalkingAvatarProvider(),
                MuseTalkAvatarProvider(),
                SadTalkerAvatarProvider(),
            ]
        payload = json.loads(manifest_path.read_text(encoding="utf-8") or "[]")
        return [self._candidate_from_manifest(item) for item in payload]

    def _candidate_from_manifest(self, item: dict[str, Any]) -> LiveOSPlugin:
        provider_id = _provider_id(str(item.get("name") or ""))
        category = _category_from_adapter(str(item.get("adapter") or ""))
        capabilities = _capabilities_for(provider_id, category)
        display_name = _display_name_for(provider_id, str(item.get("name") or provider_id))
        if provider_id == "cosyvoice_tts":
            return CosyVoiceHttpTtsProvider(self.workspace_root, repo_url=str(item.get("repo_url") or ""), commit=str(item.get("commit") or ""), license=str(item.get("license") or ""), adapter=str(item.get("adapter") or ""))
        if provider_id == "fish_speech":
            return FishSpeechProvider(repo_url=str(item.get("repo_url") or ""), commit=str(item.get("commit") or ""), license=str(item.get("license") or ""), adapter=str(item.get("adapter") or ""))
        if provider_id == "livetalking":
            return LiveTalkingAvatarProvider(repo_url=str(item.get("repo_url") or ""), commit=str(item.get("commit") or ""), license=str(item.get("license") or ""), adapter=str(item.get("adapter") or ""))
        if provider_id == "musetalk":
            return MuseTalkAvatarProvider(repo_url=str(item.get("repo_url") or ""), commit=str(item.get("commit") or ""), license=str(item.get("license") or ""), adapter=str(item.get("adapter") or ""))
        if provider_id == "sadtalker":
            return SadTalkerAvatarProvider(repo_url=str(item.get("repo_url") or ""), commit=str(item.get("commit") or ""), license=str(item.get("license") or ""), adapter=str(item.get("adapter") or ""))
        return NotInstalledPlugin(
            provider_id,
            category,
            str(item.get("repo_url") or ""),
            capabilities,
            display_name=display_name,
            commit=str(item.get("commit") or ""),
            license=str(item.get("license") or ""),
            adapter=str(item.get("adapter") or ""),
            metadata={"purpose": str(item.get("purpose") or ""), "status": str(item.get("status") or "")},
        )


def _dedupe_by_provider_id(plugins: list[LiveOSPlugin]) -> list[LiveOSPlugin]:
    deduped: dict[str, LiveOSPlugin] = {}
    for plugin in plugins:
        deduped[plugin.provider_id] = plugin
    return list(deduped.values())


def _provider_id(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "cosyvoice": "cosyvoice_tts",
        "cosyvoice_tts": "cosyvoice_tts",
        "fish_speech": "fish_speech",
        "livetalking": "livetalking",
        "live_talking": "livetalking",
        "musetalk": "musetalk",
        "muse_talk": "musetalk",
        "sadtalker": "sadtalker",
        "sad_talker": "sadtalker",
    }
    return aliases.get(normalized, normalized or "unknown")


def _category_from_adapter(adapter: str) -> str:
    if "/tts" in adapter or adapter.endswith("tts"):
        return "tts"
    if "/avatar" in adapter or adapter.endswith("avatar"):
        return "avatar"
    if "/video" in adapter or adapter.endswith("video"):
        return "video"
    if "/rag" in adapter or adapter.endswith("rag"):
        return "rag"
    return "workflow"


def _capabilities_for(provider_id: str, category: str) -> tuple[str, ...]:
    mapping = {
        "cosyvoice_tts": ("tts", "voice_clone", "external_http"),
        "fish_speech": ("tts", "voice_clone"),
        "livetalking": ("realtime_avatar", "audio_drive"),
        "musetalk": ("audio_drive", "lip_sync"),
        "sadtalker": ("talking_head",),
    }
    return mapping.get(provider_id, (category,))


def _display_name_for(provider_id: str, fallback: str) -> str:
    mapping = {
        "cosyvoice_tts": "CosyVoice HTTP TTS",
        "fish_speech": "Fish Speech Adapter",
        "livetalking": "LiveTalking Adapter",
        "musetalk": "MuseTalk Adapter",
        "sadtalker": "SadTalker Adapter",
    }
    return mapping.get(provider_id, fallback)
