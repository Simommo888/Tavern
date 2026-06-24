from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Literal
from uuid import uuid4

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI

from .config import llm_api_key, llm_base_url, llm_model, llm_model_provider, llm_wire_api
from .models import ToolCall

LLM_MAX_ATTEMPTS = 3
LLM_RETRY_BACKOFF_SECONDS = (1.0, 4.0)
LLM_REQUEST_TIMEOUT_SECONDS = 300.0
CLAUDE_DEFAULT_MODEL = "claude-opus-4-8"
GEMINI_DEFAULT_MODEL = "gemini-2.5-pro"

ModelProvider = Literal["openai", "claude", "gemini"]


def _is_retryable_llm_error(exc: BaseException) -> bool:
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


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    name: str
    system: str
    user_instruction: str
    max_output_seconds: int | None = None


class PromptRegistry:
    def __init__(self, templates: dict[str, PromptTemplate] | None = None) -> None:
        self.templates = templates or _default_prompt_templates()

    def get(self, name: str) -> PromptTemplate:
        try:
            return self.templates[name]
        except KeyError as exc:
            raise KeyError(f"Unknown prompt template: {name}") from exc

    def render_messages(self, name: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        template = self.get(name)
        instruction = template.user_instruction
        if template.max_output_seconds:
            instruction = f"{instruction}\n主播口播时长控制在 {template.max_output_seconds} 秒以内。"
        return [
            {"role": "system", "content": template.system},
            {"role": "user", "content": json.dumps({"instruction": instruction, "payload": payload}, ensure_ascii=False)},
        ]


class ModelGateway:
    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        wire_api: str | None = None,
        workspace_root: str = ".",
    ) -> None:
        self.provider = _normalize_provider(provider or llm_model_provider(workspace_root))
        self.model = model or _default_model_for_provider(self.provider, workspace_root)
        self.base_url = base_url or llm_base_url(workspace_root)
        self.api_key = api_key or llm_api_key(workspace_root)
        self.wire_api = (wire_api or llm_wire_api(workspace_root)).strip().lower()
        if not self.api_key:
            raise RuntimeError("VIMAX_LLM_API_KEY is required for the model gateway")
        self.prompt_registry = PromptRegistry()
        self.client = self._build_client()

    async def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AssistantMessage:
        for attempt in range(LLM_MAX_ATTEMPTS):
            try:
                return await self._complete_once(messages, tools)
            except Exception as exc:
                if attempt == LLM_MAX_ATTEMPTS - 1 or not _is_retryable_llm_error(exc):
                    raise
                delay = LLM_RETRY_BACKOFF_SECONDS[min(attempt, len(LLM_RETRY_BACKOFF_SECONDS) - 1)]
                logging.warning("LLM call failed (%s); retrying in %.1fs (attempt %d/%d)", exc, delay, attempt + 1, LLM_MAX_ATTEMPTS)
                await asyncio.sleep(delay)
        raise RuntimeError("LLM call failed after retries")

    async def stream_complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AsyncIterator[str]:
        if self.provider == "claude":
            async for chunk in self._stream_claude(messages, tools):
                yield chunk
            return
        if self.provider == "gemini":
            async for chunk in self._stream_gemini(messages):
                yield chunk
            return
        async for chunk in self._stream_openai(messages, tools):
            yield chunk

    async def complete_prompt(self, template_name: str, payload: dict[str, Any]) -> AssistantMessage:
        return await self.complete(self.prompt_registry.render_messages(template_name, payload), tools=[])

    async def _complete_once(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AssistantMessage:
        if self.provider == "claude":
            return await self._complete_claude(messages, tools)
        if self.provider == "gemini":
            return await self._complete_gemini(messages)
        return await self._complete_openai(messages, tools)

    def _build_client(self) -> Any:
        if self.provider == "claude":
            try:
                import anthropic
            except ImportError as exc:
                raise RuntimeError("Install the official Anthropic SDK: pip install anthropic") from exc
            return anthropic.AsyncAnthropic(api_key=self.api_key, timeout=LLM_REQUEST_TIMEOUT_SECONDS)
        if self.provider == "gemini":
            try:
                from google import genai
            except ImportError as exc:
                raise RuntimeError("Install the official Gemini SDK: pip install google-genai") from exc
            return genai.Client(api_key=self.api_key)
        return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=LLM_REQUEST_TIMEOUT_SECONDS)

    async def _complete_openai(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AssistantMessage:
        response = await self._create_openai_response(messages, tools)
        if self.wire_api == "responses":
            return _assistant_message_from_responses(response)
        return _assistant_message_from_chat_completion(response)

    async def _create_openai_response(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        if self.wire_api == "responses":
            return await self.client.responses.create(
                model=self.model,
                input=_responses_input(messages),
                tools=_responses_tools(tools),
            )
        return await self.client.chat.completions.create(model=self.model, messages=messages, tools=tools or None, tool_choice="auto" if tools else None)

    async def _stream_openai(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(model=self.model, messages=messages, tools=tools or None, tool_choice="auto" if tools else None, stream=True)
        async for event in stream:
            if not event.choices:
                continue
            delta = event.choices[0].delta.content or ""
            if delta:
                yield delta

    async def _complete_claude(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AssistantMessage:
        system, claude_messages = _claude_messages(messages)
        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 16000,
            "system": system,
            "messages": claude_messages,
            "tools": _claude_tools(tools) or None,
        }
        if self.model.startswith("claude-opus-4") or self.model.startswith("claude-sonnet-4-6"):
            request["thinking"] = {"type": "adaptive"}
            request["output_config"] = {"effort": "high"}
        response = await self.client.messages.create(**{key: value for key, value in request.items() if value is not None})
        if response.stop_reason == "refusal":
            raise RuntimeError("Claude refused the request")
        return _assistant_message_from_claude(response)

    async def _stream_claude(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AsyncIterator[str]:
        system, claude_messages = _claude_messages(messages)
        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 64000,
            "system": system,
            "messages": claude_messages,
            "tools": _claude_tools(tools) or None,
        }
        if self.model.startswith("claude-opus-4") or self.model.startswith("claude-sonnet-4-6"):
            request["thinking"] = {"type": "adaptive"}
            request["output_config"] = {"effort": "high"}
        async with self.client.messages.stream(**{key: value for key, value in request.items() if value is not None}) as stream:
            async for text in stream.text_stream:
                if text:
                    yield text

    async def _complete_gemini(self, messages: list[dict[str, Any]]) -> AssistantMessage:
        prompt = _gemini_prompt(messages)
        response = await asyncio.to_thread(self.client.models.generate_content, model=self.model, contents=prompt)
        text = str(getattr(response, "text", "") or "")
        raw = response.model_dump() if hasattr(response, "model_dump") else {}
        return AssistantMessage(text=text, raw_message=raw)

    async def _stream_gemini(self, messages: list[dict[str, Any]]) -> AsyncIterator[str]:
        prompt = _gemini_prompt(messages)
        stream = await asyncio.to_thread(self.client.models.generate_content_stream, model=self.model, contents=prompt)
        for chunk in stream:
            text = str(getattr(chunk, "text", "") or "")
            if text:
                yield text


class OpenAICompatibleLLM(ModelGateway):
    def __init__(self, model: str | None = None, base_url: str | None = None, api_key: str | None = None, wire_api: str | None = None) -> None:
        super().__init__(provider="openai", model=model, base_url=base_url, api_key=api_key, wire_api=wire_api)


class UnifiedModelGateway(ModelGateway):
    pass


def _normalize_provider(provider: str) -> ModelProvider:
    normalized = provider.strip().lower().replace("anthropic", "claude").replace("google", "gemini")
    if normalized in {"openai", "claude", "gemini"}:
        return normalized  # type: ignore[return-value]
    raise ValueError(f"Unsupported LLM provider: {provider}")


def _default_model_for_provider(provider: ModelProvider, workspace_root: str) -> str:
    configured = llm_model(workspace_root)
    if configured and configured != "gpt-5.5":
        return configured
    if provider == "claude":
        return CLAUDE_DEFAULT_MODEL
    if provider == "gemini":
        return GEMINI_DEFAULT_MODEL
    return configured


def _default_prompt_templates() -> dict[str, PromptTemplate]:
    return {
        "live_anchor_reply": PromptTemplate(
            name="live_anchor_reply",
            system="你是酒类电商直播间数字人主播，回答要自然口语化、可信、克制，并严格遵守酒类合规：不面向未成年人，不宣传医疗保健功效，不鼓励过量饮酒或酒驾。",
            user_instruction="生成一句适合主播直接口播的中文回复，优先回答观众问题，同时结合当前商品卖点和直播节奏。",
            max_output_seconds=15,
        ),
        "prompt_generate": PromptTemplate(
            name="prompt_generate",
            system="你是企业级直播运营话术专家，负责为数字人直播生成可审查、可复用、可配置的话术。",
            user_instruction="基于输入的商品、场景和话术类型生成中文直播话术，保持真实、自然、合规。",
            max_output_seconds=15,
        ),
    }


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


def _claude_messages(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, str]]]:
    system_parts: list[str] = []
    converted: list[dict[str, str]] = []
    for message in messages:
        role = str(message.get("role") or "user")
        content = str(message.get("content") or "")
        if role == "system":
            system_parts.append(content)
        elif role == "assistant":
            converted.append({"role": "assistant", "content": content})
        else:
            converted.append({"role": "user", "content": content})
    if not converted:
        converted.append({"role": "user", "content": ""})
    return "\n\n".join(part for part in system_parts if part), converted


def _claude_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted = []
    for tool in tools or []:
        function = tool.get("function", {})
        name = function.get("name")
        if not name:
            continue
        schema = function.get("parameters") or {"type": "object", "properties": {}}
        if isinstance(schema, dict):
            schema = {**schema, "additionalProperties": schema.get("additionalProperties", False)}
        converted.append({"name": name, "description": function.get("description", ""), "input_schema": schema})
    return converted


def _assistant_message_from_claude(response: Any) -> AssistantMessage:
    chunks: list[str] = []
    calls: list[ToolCall] = []
    for block in response.content:
        block_type = getattr(block, "type", "")
        if block_type == "text":
            chunks.append(str(getattr(block, "text", "") or ""))
        elif block_type == "tool_use":
            calls.append(ToolCall(id=getattr(block, "id", "") or f"tool-{uuid4().hex[:12]}", name=getattr(block, "name", ""), arguments=dict(getattr(block, "input", {}) or {})))
    raw = response.to_dict() if hasattr(response, "to_dict") else {}
    return AssistantMessage(text="".join(chunks), tool_calls=calls, raw_message=raw)


def _gemini_prompt(messages: list[dict[str, Any]]) -> str:
    rows = []
    for message in messages:
        role = str(message.get("role") or "user")
        content = str(message.get("content") or "")
        if content:
            rows.append(f"[{role}]\n{content}")
    return "\n\n".join(rows)
