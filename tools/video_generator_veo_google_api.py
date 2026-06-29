import logging
import os
from typing import List, Optional
import asyncio
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from interfaces.video_output import VideoOutput
from utils.rate_limiter import RateLimiter

# https://ai.google.dev/gemini-api/docs/video-generation?hl=zh-cn


class VideoGeneratorVeoGoogleAPI:
    def __init__(
        self,
        api_key: str,
        t2v_model: str = "veo-3.1-generate-preview",
        ff2v_model: str = "veo-3.1-generate-preview",
        flf2v_model: str = "veo-3.1-generate-preview",
        base_url: str = "",
        rate_limiter: Optional[RateLimiter] = None,
    ):
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or os.environ.get("VIMAX_VIDEO_API_KEY")
        resolved_base_url = base_url or os.environ.get("GOOGLE_GEMINI_BASE_URL", "")
        resolved_model = os.environ.get("GEMINI_MODEL", "")
        if not resolved_key or not resolved_base_url or not resolved_model:
            try:
                from agent_runtime.config import video_api_key, video_base_url, video_model

                resolved_key = resolved_key or video_api_key()
                resolved_base_url = resolved_base_url or video_base_url()
                resolved_model = resolved_model or video_model()
            except Exception:
                pass
        self.api_key = resolved_key or ""
        self.t2v_model = resolved_model or t2v_model
        self.ff2v_model = resolved_model or ff2v_model
        self.flf2v_model = resolved_model or flf2v_model
        self.base_url = (resolved_base_url or "").rstrip("/")
        self.rate_limiter = rate_limiter

        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["http_options"] = types.HttpOptions(base_url=self.base_url, api_version="v1beta")
        self.client = genai.Client(**client_kwargs)
    
    async def generate_single_video(
        self,
        prompt: str,
        reference_image_paths: List[str],
        resolution: str = "1080p",
        aspect_ratio: str = "16:9",
        duration: int = 8,
        **kwargs,
    ) -> VideoOutput:

        params = {
            "prompt": prompt,
        }
        config_params = {
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "duration_seconds": duration,
        }
        if len(reference_image_paths) == 0:
            params["model"] = self.t2v_model
        elif len(reference_image_paths) == 1:
            params["model"] = self.ff2v_model
            params["image"] = types.Image.from_file(location=reference_image_paths[0])
        elif len(reference_image_paths) == 2:
            params["model"] = self.flf2v_model
            params["image"] = types.Image.from_file(location=reference_image_paths[0])
            config_params["last_frame"] = types.Image.from_file(location=reference_image_paths[1])
        else:
            raise ValueError("The number of reference images must be no more than 2")

        logging.info(f"Calling {params['model']} to generate video...")

        # Apply rate limiting if configured
        if self.rate_limiter:
            await self.rate_limiter.acquire()

        # Retry logic for rate limit errors
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                operation = self.client.models.generate_videos(
                    **params,
                    config=types.GenerateVideosConfig(**config_params),
                )
                break
            except ClientError as e:
                status_code = _client_error_status_code(e)
                if status_code == 429 and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logging.warning(f"Rate limit hit (429), retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logging.error("Veo video generation request failed: %s", _client_error_summary(e))
                    raise RuntimeError(f"Veo video generation request failed: {_client_error_summary(e)}") from e

        while not operation.done:
            await asyncio.sleep(2)
            operation = self.client.operations.get(operation)
            logging.info(f"Video generation not completed, waiting 2 seconds...")

        # Check if operation completed successfully
        if operation.error:
            error_msg = f"Video generation failed: {operation.error}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        if not operation.response:
            error_msg = "Video generation completed but no response received"
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        if not hasattr(operation.response, 'generated_videos') or not operation.response.generated_videos:
            error_msg = "Video generation completed but no videos were generated"
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        generated_video = operation.response.generated_videos[0]
        self.client.files.download(file=generated_video.video)

        video_output = VideoOutput(
            fmt="bytes",
            ext="mp4",
            data=generated_video.video.video_bytes,
        )
        return video_output


def _client_error_status_code(error: ClientError) -> int | None:
    for attr in ("status_code", "code"):
        value = getattr(error, attr, None)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    response = getattr(error, "response", None)
    value = getattr(response, "status_code", None)
    if isinstance(value, int):
        return value
    return None


def _client_error_summary(error: ClientError) -> str:
    status_code = _client_error_status_code(error)
    parts = []
    if status_code is not None:
        parts.append(f"status={status_code}")
    for attr in ("message", "details"):
        value = getattr(error, attr, None)
        if value:
            parts.append(f"{attr}={value}")
    response = getattr(error, "response", None)
    response_text = getattr(response, "text", None)
    if response_text:
        parts.append(f"response={str(response_text)[:500]}")
    if not parts:
        parts.append(str(error))
    return "; ".join(parts)
