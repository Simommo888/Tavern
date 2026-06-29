from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import json
import mimetypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from openai import OpenAI

from utils.image import download_image
from utils.video import download_video


@dataclass(frozen=True, slots=True)
class GeneratedMediaResult:
    provider: str
    uri: str
    model: str
    metadata: dict[str, Any]


def generate_openai_image(
    *,
    prompt: str,
    output_path: Path,
    api_key: str,
    model: str,
    size: str,
    base_url: str,
    timeout_seconds: float,
) -> GeneratedMediaResult:
    client_kwargs: dict[str, Any] = {"api_key": api_key, "timeout": timeout_seconds}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    response = client.images.generate(model=model, prompt=prompt, size=size, n=1)
    data = response.data[0]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    b64_json = getattr(data, "b64_json", None)
    url = getattr(data, "url", None)
    if b64_json:
        output_path.write_bytes(base64.b64decode(b64_json))
        source = "b64_json"
    elif url:
        download_image(url, str(output_path))
        source = "url"
    else:
        raise RuntimeError("OpenAI image generation returned neither b64_json nor url")

    return GeneratedMediaResult(
        provider="openai_image",
        uri=output_path.resolve().as_uri(),
        model=model,
        metadata={"source": source, "size": size},
    )


def generate_jimeng_video(
    *,
    prompt: str,
    output_path: Path,
    api_key: str,
    base_url: str,
    model: str,
    req_key: str,
    submit_action: str,
    result_action: str,
    api_version: str,
    aspect_ratio: str,
    duration_seconds: int,
    fps: int,
    timeout_seconds: float,
    poll_interval_seconds: float,
    max_poll_attempts: int,
    access_key: str = "",
    secret_key: str = "",
    region: str = "cn-north-1",
    service: str = "cv",
) -> GeneratedMediaResult:
    client = JimengVideoClient(
        api_key=api_key,
        base_url=base_url,
        req_key=req_key,
        submit_action=submit_action,
        result_action=result_action,
        api_version=api_version,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
        max_poll_attempts=max_poll_attempts,
        access_key=access_key,
        secret_key=secret_key,
        region=region,
        service=service,
    )
    task_id = client.submit_task(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        duration_seconds=duration_seconds,
        fps=fps,
    )
    video_url, result_payload = client.poll_result(task_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    download_video(video_url, str(output_path))
    return GeneratedMediaResult(
        provider="jimeng_ai",
        uri=output_path.resolve().as_uri(),
        model=model,
        metadata={
            "task_id": task_id,
            "req_key": req_key,
            "aspect_ratio": aspect_ratio,
            "duration_seconds": duration_seconds,
            "fps": fps,
            "result_status": _extract_status(result_payload),
        },
    )


class JimengVideoClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        req_key: str,
        submit_action: str,
        result_action: str,
        api_version: str,
        timeout_seconds: float,
        poll_interval_seconds: float,
        max_poll_attempts: int,
        access_key: str = "",
        secret_key: str = "",
        region: str = "cn-north-1",
        service: str = "cv",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("?")
        self.req_key = req_key
        self.submit_action = submit_action
        self.result_action = result_action
        self.api_version = api_version
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.max_poll_attempts = max_poll_attempts
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.service = service

    def submit_task(self, *, prompt: str, aspect_ratio: str, duration_seconds: int, fps: int) -> str:
        payload = {
            "req_key": self.req_key,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "seed": -1,
            "frames": max(1, int(duration_seconds) * int(fps) + 1),
        }
        response_json = self._post(self.submit_action, payload)
        task_id = _find_first(response_json, ["data.task_id", "Result.task_id", "result.task_id", "task_id", "data.id", "Result.id", "id"])
        if not task_id:
            raise RuntimeError(f"Jimeng submit response returned no task_id: {response_json}")
        return str(task_id)

    def poll_result(self, task_id: str) -> tuple[str, dict[str, Any]]:
        payload = {"req_key": self.req_key, "task_id": task_id}
        last_payload: dict[str, Any] = {}
        pending_statuses = {"", "created", "pending", "queued", "running", "processing", "in_progress"}
        success_statuses = {"done", "succeeded", "success", "completed"}
        failed_statuses = {"failed", "fail", "error", "cancelled", "canceled"}
        for _ in range(max(1, self.max_poll_attempts)):
            response_json = self._post(self.result_action, payload)
            last_payload = response_json
            status = (_extract_status(response_json) or "").lower()
            video_url = _find_first(response_json, ["data.video_url", "Result.video_url", "result.video_url", "video_url", "data.content.video_url", "content.video_url", "data.url", "Result.url", "url"])
            if video_url and (status in success_statuses or status in pending_statuses):
                return str(video_url), response_json
            if status in failed_statuses:
                raise RuntimeError(f"Jimeng video generation failed: {response_json}")
            time.sleep(self.poll_interval_seconds)
        raise TimeoutError(f"Jimeng video generation did not complete after {self.max_poll_attempts} polls: {last_payload}")

    def _post(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = _with_query(self.base_url, {"Action": action, "Version": self.api_version})
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        response = requests.post(
            url,
            headers=self._headers(url, body),
            data=body.encode("utf-8"),
            timeout=self.timeout_seconds,
        )
        try:
            response_json = response.json()
        except ValueError as exc:
            raise RuntimeError(f"Jimeng API returned non-JSON response with HTTP {response.status_code}") from exc
        if response.status_code >= 400:
            raise RuntimeError(f"Jimeng API returned HTTP {response.status_code}: {response_json}")
        code = response_json.get("code") if isinstance(response_json, dict) else None
        ok_codes = {None, 0, 10000, "0", "10000", "Success", "success"}
        if code not in ok_codes and not _find_first(response_json, ["data.task_id", "Result.task_id", "task_id", "data.video_url", "Result.video_url", "video_url"]):
            raise RuntimeError(f"Jimeng API returned error code {code}: {response_json}")
        return response_json

    def _headers(self, url: str, body: str) -> dict[str, str]:
        if self.access_key and self.secret_key:
            return _volcengine_headers(
                url=url,
                body=body,
                access_key=self.access_key,
                secret_key=self.secret_key,
                region=self.region,
                service=self.service,
            )
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}


def _with_query(url: str, query: dict[str, str]) -> str:
    split = urlsplit(url)
    merged = dict(parse_qsl(split.query, keep_blank_values=True))
    merged.update(query)
    return urlunsplit((split.scheme, split.netloc, split.path or "/", urlencode(merged), split.fragment))


def _volcengine_headers(*, url: str, body: str, access_key: str, secret_key: str, region: str, service: str) -> dict[str, str]:
    split = urlsplit(url)
    host = split.netloc
    canonical_uri = split.path or "/"
    canonical_querystring = _canonical_query(split.query)
    now = dt.datetime.now(dt.UTC)
    x_date = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    content_type = "application/json"
    canonical_headers = f"content-type:{content_type}\nhost:{host}\nx-content-sha256:{payload_hash}\nx-date:{x_date}\n"
    signed_headers = "content-type;host;x-content-sha256;x-date"
    canonical_request = "\n".join(["POST", canonical_uri, canonical_querystring, canonical_headers, signed_headers, payload_hash])
    credential_scope = f"{datestamp}/{region}/{service}/request"
    string_to_sign = "\n".join(["HMAC-SHA256", x_date, credential_scope, hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()])
    signing_key = _volcengine_signing_key(secret_key, datestamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization = f"HMAC-SHA256 Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    return {
        "Authorization": authorization,
        "Content-Type": content_type,
        "Host": host,
        "X-Content-Sha256": payload_hash,
        "X-Date": x_date,
    }


def _volcengine_signing_key(secret_key: str, date: str, region: str, service: str) -> bytes:
    key = hmac.new(secret_key.encode("utf-8"), date.encode("utf-8"), hashlib.sha256).digest()
    key = hmac.new(key, region.encode("utf-8"), hashlib.sha256).digest()
    key = hmac.new(key, service.encode("utf-8"), hashlib.sha256).digest()
    return hmac.new(key, b"request", hashlib.sha256).digest()


def _canonical_query(query: str) -> str:
    pairs = parse_qsl(query, keep_blank_values=True)
    return urlencode(sorted(pairs), doseq=True)


def _find_first(payload: dict[str, Any], paths: list[str]) -> Any:
    for path in paths:
        current: Any = payload
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        if current is not None and current != "":
            return current
    return None


def _extract_status(payload: dict[str, Any]) -> str:
    return str(_find_first(payload, ["data.status", "Result.status", "result.status", "status", "data.task_status", "Result.task_status", "task_status", "data.message", "Result.message", "message"]) or "")


def media_extension_from_content_type(content_type: str, default: str) -> str:
    ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else None
    return (ext or default).lstrip(".")
