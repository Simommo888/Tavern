from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI

from .config import llm_api_key, llm_base_url, llm_model, llm_wire_api
from .models import ToolCall

LLM_MAX_ATTEMPTS = 3
LLM_RETRY_BACKOFF_SECONDS = (1.0, 4.0)
LLM_REQUEST_TIMEOUT_SECONDS = 300.0


def _is_retryable_llm_error(exc: BaseException) -> bool:
    """Rate limits, server errors, and connection problems are transient;
    auth/validation errors will never succeed and must surface immediately."""
    status = getattr(exc, "status_code", None)
    if status is not None:
        try:
            status = int(status)
        except (TypeError, ValueError):
            return False
        return status == 429 or status >= 500
    return isinstance(exc, (APIConnectionError, APITimeoutError))


@dataclass(slots=True)
class AssistantMessage:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_message: dict[str, Any] = field(default_factory=dict)


class OpenAICompatibleLLM:
    def __init__(self, model: str | None = None, base_url: str | None = None, api_key: str | None = None, wire_api: str | None = None) -> None:
        self.model = model or llm_model()
        self.base_url = base_url or llm_base_url()
        self.api_key = api_key or llm_api_key()
        self.wire_api = (wire_api or llm_wire_api()).strip().lower()
        if not self.api_key:
            raise RuntimeError("VIMAX_LLM_API_KEY is required for the agent LLM client")
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=LLM_REQUEST_TIMEOUT_SECONDS)

    async def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AssistantMessage:
        for attempt in range(LLM_MAX_ATTEMPTS):
            try:
                response = await self._create_response(messages, tools)
                break
            except Exception as exc:
                if attempt == LLM_MAX_ATTEMPTS - 1 or not _is_retryable_llm_error(exc):
                    raise
                delay = LLM_RETRY_BACKOFF_SECONDS[min(attempt, len(LLM_RETRY_BACKOFF_SECONDS) - 1)]
                logging.warning("LLM call failed (%s); retrying in %.1fs (attempt %d/%d)", exc, delay, attempt + 1, LLM_MAX_ATTEMPTS)
                await asyncio.sleep(delay)
        if self.wire_api == "responses":
            return _assistant_message_from_responses(response)
        return _assistant_message_from_chat_completion(response)

    async def _create_response(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        if self.wire_api == "responses":
            return await self.client.responses.create(
                model=self.model,
                input=_responses_input(messages),
                tools=_responses_tools(tools),
            )
        return await self.client.chat.completions.create(model=self.model, messages=messages, tools=tools or None, tool_choice="auto" if tools else None)


def _assistant_message_from_chat_completion(response: Any) -> AssistantMessage:
    if not response.choices:
        raise RuntimeError("LLM response contained no choices (content filter or relay error)")
    message = response.choices[0].message
    text = message.content or ""
    calls: list[ToolCall] = []
    for call in message.tool_calls or []:
        try:
            arguments = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            arguments = {}
        calls.append(ToolCall(id=call.id or f"tool-{uuid4().hex[:12]}", name=call.function.name, arguments=arguments))
    return AssistantMessage(text=text, tool_calls=calls, raw_message=message.model_dump())


def _assistant_message_from_responses(response: Any) -> AssistantMessage:
    text = getattr(response, "output_text", "") or ""
    calls: list[ToolCall] = []
    raw = response.model_dump() if hasattr(response, "model_dump") else {}
    for item in getattr(response, "output", []) or []:
        item_type = getattr(item, "type", "")
        if item_type != "function_call":
            continue
        raw_arguments = getattr(item, "arguments", "{}") or "{}"
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError:
            arguments = {}
        calls.append(ToolCall(id=getattr(item, "call_id", "") or getattr(item, "id", "") or f"tool-{uuid4().hex[:12]}", name=getattr(item, "name", ""), arguments=arguments))
    if not text and not calls:
        text = _text_from_response_output(raw)
    return AssistantMessage(text=text, tool_calls=calls, raw_message=raw)


def _responses_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for message in messages:
        role = str(message.get("role") or "user")
        if role == "tool":
            converted.append({"role": "user", "content": f"Tool result for {message.get('name', 'tool')}:\n{message.get('content', '')}"})
            continue
        converted.append({"role": role, "content": str(message.get("content") or "")})
    return converted


def _responses_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    converted = []
    for tool in tools or []:
        function = tool.get("function", {})
        converted.append(
            {
                "type": "function",
                "name": function.get("name"),
                "description": function.get("description", ""),
                "parameters": function.get("parameters", {"type": "object", "properties": {}}),
            }
        )
    return converted or None


def _text_from_response_output(raw: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in raw.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if isinstance(content, dict):
                chunks.append(str(content.get("text") or ""))
    return "".join(chunks)
