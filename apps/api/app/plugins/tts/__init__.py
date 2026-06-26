from __future__ import annotations

import base64
import os
import re
import wave
from pathlib import Path
from urllib.parse import urljoin
from uuid import uuid4

import requests

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


class CosyVoiceHttpTtsProvider(StaticPlugin):
    provider_id = "cosyvoice_tts"
    category = "tts"
    display_name = "CosyVoice HTTP TTS"
    source_type = "local_service"
    repo_url = "https://github.com/FunAudioLLM/CosyVoice"
    license = "check_before_commercial_use"
    capabilities = ("tts", "voice_clone", "external_http")
    config_schema = {
        "type": "object",
        "properties": {
            "base_url_env": {"type": "string", "default": "TAVERN_COSYVOICE_BASE_URL"},
            "health_path": {"type": "string", "default": ""},
            "speech_path": {"type": "string", "default": "/v1/audio/speech"},
            "mode": {"type": "string", "enum": ["sft", "zero_shot", "cross_lingual", "instruct", "instruct2"]},
            "model": {"type": "string", "default": "CosyVoice2-0.5B"},
            "voice": {"type": "string"},
            "response_format": {"type": "string", "default": "wav"},
            "timeout_seconds": {"type": "number", "default": 120},
            "output_dir": {"type": "string", "default": ".working_dir/artifacts/tts"},
        },
    }
    metadata = {
        "implementation": "external_http_adapter",
        "upstream": "FunAudioLLM/CosyVoice",
        "supported_paths": ["/v1/audio/speech", "/inference_sft", "/inference_zero_shot", "/inference_cross_lingual", "/inference_instruct", "/inference_instruct2"],
    }

    def __init__(self, workspace_root: str | Path = ".", repo_url: str = "", commit: str = "", license: str = "", adapter: str = "apps/api/app/plugins/tts") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.repo_url = repo_url or self.repo_url
        self.commit = commit
        self.license = license or self.license
        self.adapter = adapter

    def health_check(self) -> dict[str, object]:
        base_url = _env("TAVERN_COSYVOICE_BASE_URL")
        if not base_url:
            return {"status": "not_configured", "provider_id": self.provider_id, "category": self.category, "required_env": "TAVERN_COSYVOICE_BASE_URL"}
        health_path = os.environ.get("TAVERN_COSYVOICE_HEALTH_PATH", "").strip()
        if not health_path:
            return {"status": "ready", "provider_id": self.provider_id, "category": self.category, "base_url": _redact_url(base_url), "health_check": "disabled"}
        try:
            response = requests.get(_join_url(base_url, health_path), timeout=min(self._timeout(), 10.0))
        except requests.RequestException as exc:
            return {"status": "unhealthy", "provider_id": self.provider_id, "category": self.category, "error": _short_error(exc)}
        if 200 <= response.status_code < 400:
            return {"status": "ready", "provider_id": self.provider_id, "category": self.category, "base_url": _redact_url(base_url), "status_code": response.status_code}
        return {"status": "unhealthy", "provider_id": self.provider_id, "category": self.category, "status_code": response.status_code, "error": response.text[:200]}

    def estimate_cost(self, payload: dict[str, object]) -> PluginCostEstimate:
        text = str(payload.get("text") or payload.get("input") or "")
        return PluginCostEstimate(estimated_cost=0, detail={"characters": len(text), "external_service": True, "provider_id": self.provider_id})

    def submit_job(self, payload: dict[str, object]) -> PluginJob:
        job_id = f"tts-job-{uuid4().hex[:10]}"
        base_url = _env("TAVERN_COSYVOICE_BASE_URL")
        if not base_url:
            return PluginJob(job_id=job_id, status="failed", error="TAVERN_COSYVOICE_BASE_URL is not configured", metadata={"provider_id": self.provider_id})
        text = str(payload.get("text") or payload.get("input") or "").strip()
        if not text:
            return PluginJob(job_id=job_id, status="failed", error="text is required for CosyVoice TTS", metadata={"provider_id": self.provider_id})

        speech_path = os.environ.get("TAVERN_COSYVOICE_SPEECH_PATH", "/v1/audio/speech").strip() or "/v1/audio/speech"
        try:
            response = self._post_speech(base_url, speech_path, text, payload)
            return self._job_from_response(job_id, speech_path, response, payload)
        except requests.RequestException as exc:
            return PluginJob(job_id=job_id, status="failed", error=_short_error(exc), metadata={"provider_id": self.provider_id, "speech_path": speech_path})
        except Exception as exc:  # defensive boundary: plugin failure must not crash MVP orchestration
            return PluginJob(job_id=job_id, status="failed", error=_short_error(exc), metadata={"provider_id": self.provider_id, "speech_path": speech_path})

    def _post_speech(self, base_url: str, speech_path: str, text: str, payload: dict[str, object]) -> requests.Response:
        url = _join_url(base_url, speech_path)
        headers = _auth_headers()
        timeout = self._timeout()
        if _is_official_cosyvoice_path(speech_path):
            data = _official_cosyvoice_form(text, payload)
            return requests.post(url, data=data, headers=headers, timeout=timeout)
        headers = {"Accept": "application/json, audio/*, application/octet-stream", **headers}
        body = {
            "model": os.environ.get("TAVERN_COSYVOICE_MODEL", "CosyVoice2-0.5B"),
            "input": text,
            "voice": str(payload.get("voice") or os.environ.get("TAVERN_COSYVOICE_VOICE", "中文女声")),
            "response_format": _audio_format(),
            "speed": _float_env("TAVERN_COSYVOICE_SPEED", 1.0),
            "sample_rate": _int_env("TAVERN_COSYVOICE_SAMPLE_RATE", 24000),
            "metadata": {"product_id": payload.get("product_id"), "plan_id": payload.get("plan_id")},
        }
        return requests.post(url, json=body, headers=headers, timeout=timeout)

    def _job_from_response(self, job_id: str, speech_path: str, response: requests.Response, payload: dict[str, object]) -> PluginJob:
        if response.status_code >= 400:
            return PluginJob(job_id=job_id, status="failed", error=f"CosyVoice HTTP {response.status_code}: {response.text[:240]}", metadata={"provider_id": self.provider_id, "speech_path": speech_path})
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type == "application/json" or _looks_like_json(response.content):
            return self._job_from_json(job_id, response, payload)
        if not response.content:
            return PluginJob(job_id=job_id, status="failed", error="CosyVoice returned an empty response", metadata={"provider_id": self.provider_id, "speech_path": speech_path})
        mime_type = content_type if content_type.startswith("audio/") else _mime_for_format(_audio_format())
        wrap_raw_pcm = _should_wrap_raw_pcm(speech_path, content_type)
        output_uri, output_path = self._write_audio(job_id, payload, response.content, mime_type, wrap_raw_pcm=wrap_raw_pcm)
        return PluginJob(
            job_id=job_id,
            status="succeeded",
            output_uri=output_uri,
            metadata={
                "provider_id": self.provider_id,
                "speech_path": speech_path,
                "mime_type": "audio/wav" if wrap_raw_pcm else mime_type,
                "bytes": output_path.stat().st_size,
                "sample_rate": _int_env("TAVERN_COSYVOICE_SAMPLE_RATE", 24000),
            },
        )

    def _job_from_json(self, job_id: str, response: requests.Response, payload: dict[str, object]) -> PluginJob:
        data = response.json()
        output_uri = str(data.get("output_uri") or data.get("audio_url") or data.get("url") or "")
        if output_uri:
            return PluginJob(job_id=job_id, status="succeeded", output_uri=output_uri, metadata={"provider_id": self.provider_id, "response": _safe_json_metadata(data)})
        audio_base64 = str(data.get("audio_base64") or data.get("audio") or "")
        if audio_base64:
            raw_audio = base64.b64decode(audio_base64)
            mime_type = str(data.get("mime_type") or _mime_for_format(_audio_format()))
            output_uri, output_path = self._write_audio(job_id, payload, raw_audio, mime_type, wrap_raw_pcm=False)
            return PluginJob(job_id=job_id, status="succeeded", output_uri=output_uri, metadata={"provider_id": self.provider_id, "mime_type": mime_type, "bytes": output_path.stat().st_size})
        return PluginJob(job_id=job_id, status="failed", error="CosyVoice JSON response did not include output_uri, audio_url, or audio_base64", metadata={"provider_id": self.provider_id, "response_keys": sorted(data)})

    def _write_audio(self, job_id: str, payload: dict[str, object], audio: bytes, mime_type: str, *, wrap_raw_pcm: bool) -> tuple[str, Path]:
        plan_id = _safe_segment(str(payload.get("plan_id") or "manual"))
        output_dir = self._output_dir() / plan_id
        output_dir.mkdir(parents=True, exist_ok=True)
        extension = "wav" if wrap_raw_pcm else _extension_for_mime(mime_type)
        output_path = output_dir / f"{job_id}.{extension}"
        if wrap_raw_pcm:
            with wave.open(str(output_path), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(_int_env("TAVERN_COSYVOICE_SAMPLE_RATE", 24000))
                wav_file.writeframes(audio)
        else:
            output_path.write_bytes(audio)
        return output_path.as_uri(), output_path

    def _output_dir(self) -> Path:
        configured = os.environ.get("TAVERN_TTS_OUTPUT_DIR", ".working_dir/artifacts/tts")
        path = Path(configured)
        return path if path.is_absolute() else self.workspace_root / path

    def _timeout(self) -> float:
        return _float_env("TAVERN_COSYVOICE_TIMEOUT_SECONDS", 120.0)


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


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _join_url(base_url: str, path: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def _auth_headers() -> dict[str, str]:
    api_key = os.environ.get("TAVERN_COSYVOICE_API_KEY", "").strip()
    if not api_key:
        return {}
    return {"Authorization": f"Bearer {api_key}"}


def _audio_format() -> str:
    return os.environ.get("TAVERN_COSYVOICE_FORMAT", "wav").strip().lower() or "wav"


def _mime_for_format(audio_format: str) -> str:
    return {"mp3": "audio/mpeg", "mpeg": "audio/mpeg", "wav": "audio/wav", "pcm": "application/octet-stream"}.get(audio_format, "audio/wav")


def _extension_for_mime(mime_type: str) -> str:
    if mime_type in {"audio/mpeg", "audio/mp3"}:
        return "mp3"
    if mime_type in {"audio/wav", "audio/x-wav"}:
        return "wav"
    if mime_type in {"application/octet-stream", "binary/octet-stream"}:
        return _audio_format() if _audio_format() != "pcm" else "s16le"
    return "wav"


def _is_official_cosyvoice_path(path: str) -> bool:
    normalized = "/" + path.strip().lstrip("/")
    return normalized.startswith("/inference_")


def _official_cosyvoice_form(text: str, payload: dict[str, object]) -> dict[str, str]:
    voice = str(payload.get("voice") or os.environ.get("TAVERN_COSYVOICE_VOICE", "中文女声"))
    form = {"tts_text": text, "spk_id": voice}
    prompt_text = str(payload.get("prompt_text") or os.environ.get("TAVERN_COSYVOICE_PROMPT_TEXT", ""))
    instruct_text = str(payload.get("instruct_text") or os.environ.get("TAVERN_COSYVOICE_INSTRUCT_TEXT", ""))
    if prompt_text:
        form["prompt_text"] = prompt_text
    if instruct_text:
        form["instruct_text"] = instruct_text
    return form


def _should_wrap_raw_pcm(path: str, content_type: str) -> bool:
    return _audio_format() == "wav" and _is_official_cosyvoice_path(path) and content_type in {"", "application/octet-stream", "binary/octet-stream"}


def _looks_like_json(content: bytes) -> bool:
    stripped = content.strip()
    return stripped.startswith(b"{") and stripped.endswith(b"}")


def _safe_json_metadata(data: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in data.items() if key not in {"audio", "audio_base64"}}


def _safe_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-._") or "manual"


def _redact_url(value: str) -> str:
    return re.sub(r"//([^:@/]+):([^@/]+)@", r"//\1:***@", value)


def _short_error(exc: BaseException) -> str:
    return str(exc).replace("\n", " ")[:300]


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
