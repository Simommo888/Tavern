from __future__ import annotations

import os
from pathlib import Path

import aiohttp

from .config import tts_api_key, tts_base_url, tts_model, tts_voice

DEFAULT_EDGE_TTS_VOICE = "zh-CN-XiaoxiaoNeural"


async def synthesize_speech(text: str, output_dir: str | Path, artifact_id: str) -> tuple[Path, str, str]:
    """Generate a speech audio artifact.

    Provider selection:
    - ``TAVERN_TTS_PROVIDER=sapi``: local Windows SAPI WAV.
    - ``TAVERN_TTS_PROVIDER=openai``: OpenAI-compatible ``/audio/speech``.
    - ``TAVERN_TTS_PROVIDER=edge`` or unset: edge-tts.
    - ``TAVERN_TTS_PROVIDER=placeholder``: local silent WAV.

    Every provider falls back to a silent WAV placeholder so live-room replies
    always have an audio URL, even in offline demos/tests.
    """
    provider = os.environ.get("TAVERN_TTS_PROVIDER", "edge").strip().lower()
    if provider in {"off", "placeholder", "silent"}:
        return _silent_placeholder(output_dir, artifact_id)
    try:
        if provider in {"sapi", "windows", "windows-sapi"}:
            return _windows_sapi_tts(text, output_dir, artifact_id)
        if provider in {"openai", "openai-compatible", "api"}:
            return await _openai_compatible_tts(text, output_dir, artifact_id)
        return await _edge_tts(text, output_dir, artifact_id)
    except Exception:
        return _silent_placeholder(output_dir, artifact_id)


async def _openai_compatible_tts(text: str, output_dir: str | Path, artifact_id: str) -> tuple[Path, str, str]:
    api_key = tts_api_key()
    base_url = tts_base_url().rstrip("/")
    if not api_key or not base_url:
        raise RuntimeError("TTS api_key/base_url is not configured")
    output_path = Path(output_dir) / f"{artifact_id}.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": tts_model(),
        "voice": tts_voice(),
        "input": text,
        "response_format": "mp3",
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
        async with session.post(f"{base_url}/audio/speech", headers=headers, json=payload) as response:
            data = await response.read()
            if response.status >= 400:
                raise RuntimeError(f"OpenAI-compatible TTS failed with HTTP {response.status}: {data[:300]!r}")
    output_path.write_bytes(data)
    return output_path, "audio/mpeg", "openai-compatible-tts"


def _windows_sapi_tts(text: str, output_dir: str | Path, artifact_id: str) -> tuple[Path, str, str]:
    import pythoncom
    import win32com.client

    output_path = Path(output_dir) / f"{artifact_id}.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pythoncom.CoInitialize()
    try:
        voice = win32com.client.Dispatch("SAPI.SpVoice")
        stream = win32com.client.Dispatch("SAPI.SpFileStream")
        audio_format = win32com.client.Dispatch("SAPI.SpAudioFormat")
        audio_format.Type = 22  # SAFT22kHz16BitMono
        stream.Format = audio_format
        stream.Open(str(output_path), 3, False)  # SSFMCreateForWrite
        voice.AudioOutputStream = stream
        voice.Rate = int(os.environ.get("TAVERN_SAPI_RATE", "0"))
        voice.Volume = int(os.environ.get("TAVERN_SAPI_VOLUME", "100"))
        voice.Speak(text)
        stream.Close()
    finally:
        pythoncom.CoUninitialize()
    return output_path, "audio/wav", "windows-sapi"


async def _edge_tts(text: str, output_dir: str | Path, artifact_id: str) -> tuple[Path, str, str]:
    import edge_tts

    output_path = Path(output_dir) / f"{artifact_id}.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    voice = os.environ.get("TAVERN_EDGE_TTS_VOICE", DEFAULT_EDGE_TTS_VOICE)
    rate = os.environ.get("TAVERN_EDGE_TTS_RATE", "+0%")
    volume = os.environ.get("TAVERN_EDGE_TTS_VOLUME", "+0%")
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    await communicate.save(str(output_path))
    return output_path, "audio/mpeg", "edge-tts"


def _silent_placeholder(output_dir: str | Path, artifact_id: str) -> tuple[Path, str, str]:
    from .live_room_runtime import _write_silence_wav

    output_path = Path(output_dir) / f"{artifact_id}.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_silence_wav(output_path, duration_seconds=0.35)
    return output_path, "audio/wav", "silent-placeholder"
