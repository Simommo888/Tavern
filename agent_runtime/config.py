from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

DEFAULT_LLM_MODEL = "gpt-5.5"
DEFAULT_LLM_MODEL_PROVIDER = "openai"
DEFAULT_LLM_BASE_URL = "https://yunwu.ai/v1"
DEFAULT_IMAGE_MODEL = "gemini-3.1-flash-image-preview"
DEFAULT_IMAGE_BASE_URL = "https://yunwu.ai"
DEFAULT_VIDEO_MODEL = "veo3.1-fast"
DEFAULT_VIDEO_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_MODEL_PROVIDER = "openai"
DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
DEFAULT_TTS_MODEL = "tts-1"
DEFAULT_TTS_VOICE = "alloy"


@lru_cache(maxsize=4)
def load_agent_config(workspace_root: str | Path = ".") -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    payload: dict[str, Any] = {}
    for name in ("agent.local.yaml", "agent.secrets.local.yaml"):
        path = root / "configs" / name
        if not path.exists():
            continue
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Invalid configs/{name}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise RuntimeError(f"configs/{name} must be a YAML mapping")
        payload = _deep_merge(payload, loaded)
    return payload


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def config_value(section: str, key: str, env_names: list[str], default: str = "", workspace_root: str | Path = ".") -> str:
    for env_name in env_names:
        value = os.environ.get(env_name)
        if value:
            return value
    section_payload = load_agent_config(workspace_root).get(section, {})
    if isinstance(section_payload, dict):
        value = section_payload.get(key)
        if isinstance(value, str) and value:
            return value
    return default


def llm_model(workspace_root: str | Path = ".") -> str:
    return config_value("llm", "model", ["TAVERN_LLM_MODEL", "VIMAX_LLM_MODEL"], DEFAULT_LLM_MODEL, workspace_root)


def llm_model_provider(workspace_root: str | Path = ".") -> str:
    return config_value("llm", "model_provider", ["TAVERN_LLM_MODEL_PROVIDER", "VIMAX_LLM_MODEL_PROVIDER"], DEFAULT_LLM_MODEL_PROVIDER, workspace_root)


def llm_base_url(workspace_root: str | Path = ".") -> str:
    return config_value("llm", "base_url", ["TAVERN_LLM_BASE_URL", "VIMAX_LLM_BASE_URL"], DEFAULT_LLM_BASE_URL, workspace_root)


def llm_wire_api(workspace_root: str | Path = ".") -> str:
    return config_value("llm", "wire_api", ["TAVERN_LLM_WIRE_API", "VIMAX_LLM_WIRE_API"], "chat_completions", workspace_root)


def llm_api_key(workspace_root: str | Path = ".") -> str:
    explicit = os.environ.get("TAVERN_LLM_API_KEY") or os.environ.get("VIMAX_LLM_API_KEY")
    if explicit:
        return explicit
    section_payload = load_agent_config(workspace_root).get("llm", {})
    if isinstance(section_payload, dict):
        value = section_payload.get("api_key")
        if isinstance(value, str) and value:
            return value
    return os.environ.get("OPENAI_API_KEY") or os.environ.get("VIMAX_API_KEY") or ""


def image_model(workspace_root: str | Path = ".") -> str:
    return config_value("image", "model", ["VIMAX_IMAGE_MODEL"], DEFAULT_IMAGE_MODEL, workspace_root)


def image_base_url(workspace_root: str | Path = ".") -> str:
    return config_value("image", "base_url", ["VIMAX_IMAGE_BASE_URL"], DEFAULT_IMAGE_BASE_URL, workspace_root)


def image_api_key(workspace_root: str | Path = ".") -> str:
    return config_value("image", "api_key", ["VIMAX_IMAGE_API_KEY", "VIMAX_LLM_API_KEY", "VIMAX_API_KEY"], llm_api_key(workspace_root), workspace_root)



def embedding_model(workspace_root: str | Path = ".") -> str:
    return config_value("embedding", "model", ["VIMAX_EMBEDDING_MODEL"], DEFAULT_EMBEDDING_MODEL, workspace_root)


def embedding_model_provider(workspace_root: str | Path = ".") -> str:
    return config_value("embedding", "model_provider", ["VIMAX_EMBEDDING_MODEL_PROVIDER"], DEFAULT_EMBEDDING_MODEL_PROVIDER, workspace_root)


def embedding_base_url(workspace_root: str | Path = ".") -> str:
    return config_value("embedding", "base_url", ["VIMAX_EMBEDDING_BASE_URL"], "", workspace_root)


def embedding_api_key(workspace_root: str | Path = ".") -> str:
    return config_value("embedding", "api_key", ["VIMAX_EMBEDDING_API_KEY"], "", workspace_root)


def reranker_model(workspace_root: str | Path = ".") -> str:
    return config_value("reranker", "model", ["VIMAX_RERANKER_MODEL"], DEFAULT_RERANKER_MODEL, workspace_root)


def reranker_base_url(workspace_root: str | Path = ".") -> str:
    return config_value("reranker", "base_url", ["VIMAX_RERANKER_BASE_URL"], "", workspace_root)


def reranker_api_key(workspace_root: str | Path = ".") -> str:
    return config_value("reranker", "api_key", ["VIMAX_RERANKER_API_KEY"], "", workspace_root)


def tts_model(workspace_root: str | Path = ".") -> str:
    return config_value("tts", "model", ["TAVERN_TTS_MODEL", "OPENAI_TTS_MODEL"], DEFAULT_TTS_MODEL, workspace_root)


def tts_voice(workspace_root: str | Path = ".") -> str:
    return config_value("tts", "voice", ["TAVERN_TTS_VOICE", "OPENAI_TTS_VOICE"], DEFAULT_TTS_VOICE, workspace_root)


def tts_base_url(workspace_root: str | Path = ".") -> str:
    return config_value("tts", "base_url", ["TAVERN_TTS_BASE_URL", "OPENAI_TTS_BASE_URL"], llm_base_url(workspace_root), workspace_root)


def tts_api_key(workspace_root: str | Path = ".") -> str:
    return config_value("tts", "api_key", ["TAVERN_TTS_API_KEY", "OPENAI_TTS_API_KEY"], llm_api_key(workspace_root), workspace_root)


def video_model(workspace_root: str | Path = ".") -> str:
    return config_value("video", "model", ["VIMAX_VIDEO_MODEL", "GEMINI_MODEL"], DEFAULT_VIDEO_MODEL, workspace_root)


def video_base_url(workspace_root: str | Path = ".") -> str:
    return config_value("video", "base_url", ["VIMAX_VIDEO_BASE_URL", "GOOGLE_GEMINI_BASE_URL"], DEFAULT_VIDEO_BASE_URL, workspace_root)


def video_api_key(workspace_root: str | Path = ".") -> str:
    return config_value("video", "api_key", ["VIMAX_VIDEO_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "VIMAX_API_KEY"], llm_api_key(workspace_root), workspace_root)


def api_provider_from_base_url(base_url: str) -> str:
    normalized = base_url.strip().lower()
    if "openrouter.ai" in normalized:
        return "openrouter"
    if "yunwu.ai" in normalized:
        return "yunwu"
    if "gpt.xinshu.ai" in normalized:
        return "google"
    return ""


def video_provider(workspace_root: str | Path = ".") -> str:
    """Infer the video API relay/provider from video.base_url.

    This is not a model provider setting. OpenRouter/Yunwu are transport/API
    gateways here, so users should configure base_url and let the adapter pick
    the matching implementation.
    """
    return api_provider_from_base_url(video_base_url(workspace_root))
