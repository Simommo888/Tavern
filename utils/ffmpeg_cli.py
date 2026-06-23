from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from interfaces.production import FfmpegCommandSummary


@dataclass(slots=True)
class FfmpegResult:
    argv: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> FfmpegCommandSummary:
        return FfmpegCommandSummary(argv=self.argv, returncode=self.returncode, stdout_preview=self.stdout[:1000], stderr_preview=self.stderr[:1000], metadata=self.metadata)


def resolve_ffmpeg(explicit_path: str = "") -> str:
    return _resolve_binary("ffmpeg", explicit_path or os.environ.get("FFMPEG_BINARY", ""))


def resolve_ffprobe(explicit_path: str = "") -> str:
    return _resolve_binary("ffprobe", explicit_path or os.environ.get("FFPROBE_BINARY", ""))


def ffmpeg_version(ffmpeg_path: str = "") -> FfmpegResult:
    ffmpeg = resolve_ffmpeg(ffmpeg_path)
    return run_ffmpeg([ffmpeg, "-version"], check=False)


def ffprobe_media(path: str | Path, ffprobe_path: str = "") -> dict[str, Any]:
    ffprobe = resolve_ffprobe(ffprobe_path)
    result = run_ffmpeg([
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,width,height,r_frame_rate,avg_frame_rate",
        "-of",
        "json",
        str(Path(path)),
    ])
    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe returned invalid JSON: {exc}; stdout={result.stdout[:500]!r}") from exc


def normalize_clip(input_path: str | Path, output_path: str | Path, *, width: int = 1920, height: int = 1080, fps: int = 30, ffmpeg_path: str = "") -> FfmpegResult:
    ffmpeg = resolve_ffmpeg(ffmpeg_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return run_ffmpeg([
        ffmpeg,
        "-y",
        "-i",
        str(Path(input_path)),
        "-vf",
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(output),
    ])


def concat_clips(input_paths: list[str | Path], output_path: str | Path, *, ffmpeg_path: str = "", list_file: str | Path | None = None) -> FfmpegResult:
    if not input_paths:
        raise ValueError("concat_clips requires at least one input path")
    ffmpeg = resolve_ffmpeg(ffmpeg_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    list_path = Path(list_file) if list_file is not None else output.with_suffix(".concat.txt")
    list_path.parent.mkdir(parents=True, exist_ok=True)
    list_path.write_text("".join(f"file '{_escape_concat_path(Path(path))}'\n" for path in input_paths), encoding="utf-8")
    return run_ffmpeg([
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-c",
        "copy",
        str(output),
    ])


def compose_timeline(input_paths: list[str | Path], output_path: str | Path, *, ffmpeg_path: str = "") -> FfmpegResult:
    # MVP composition is concat-based. The separate name keeps room for a richer
    # filter_complex timeline without changing the production adapter contract.
    return concat_clips(input_paths, output_path, ffmpeg_path=ffmpeg_path)


def run_ffmpeg(argv: list[str], *, check: bool = True, timeout: float | None = None) -> FfmpegResult:
    if not argv:
        raise ValueError("argv cannot be empty")
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, shell=False)
    result = FfmpegResult(argv=list(argv), returncode=completed.returncode, stdout=completed.stdout or "", stderr=completed.stderr or "")
    if check and completed.returncode != 0:
        raise RuntimeError(f"ffmpeg command failed with exit code {completed.returncode}: {completed.stderr[:1000]}")
    return result


def _resolve_binary(name: str, explicit_path: str = "") -> str:
    candidates = []
    if explicit_path:
        candidates.append(explicit_path)
    found = shutil.which(name)
    if found:
        candidates.append(found)
    exe_found = shutil.which(f"{name}.exe")
    if exe_found:
        candidates.append(exe_found)
    for candidate in candidates:
        path = Path(candidate)
        if path.exists() or shutil.which(candidate):
            return str(path if path.exists() else candidate)
    raise FileNotFoundError(f"{name} binary not found. Set {name.upper()}_BINARY or add {name} to PATH.")


def _escape_concat_path(path: Path) -> str:
    return str(path.resolve()).replace("'", "'\\''")
