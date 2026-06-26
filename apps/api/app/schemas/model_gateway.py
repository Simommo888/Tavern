from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ModelGatewayRequest(BaseModel):
    provider: Literal["openai", "claude", "gemini"] | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    wire_api: str | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)
    tools: list[dict[str, Any]] = Field(default_factory=list)
    prompt_template: str | None = None
    prompt_payload: dict[str, Any] = Field(default_factory=dict)
    max_tokens: int | None = None
    effort: Literal["low", "medium", "high", "xhigh", "max"] | None = None


class PromptRenderRequest(BaseModel):
    prompt_template: str
    prompt_payload: dict[str, Any] = Field(default_factory=dict)


class PromptTemplateUpsertRequest(BaseModel):
    name: str
    system: str
    user_instruction: str
    max_output_seconds: int | None = None
