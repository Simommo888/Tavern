from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from agent_runtime.llm import ModelGateway, PromptRegistry
from apps.api.app.schemas.model_gateway import ModelGatewayRequest, PromptRenderRequest

router = APIRouter(prefix="/model-gateway", tags=["model-gateway"])
_prompt_registry = PromptRegistry()
_workspace_root = Path(__file__).resolve().parents[5]


@router.get("/providers")
def list_model_providers() -> dict[str, Any]:
    return {
        "providers": [
            {
                "provider": "claude",
                "default_model": "claude-opus-4-8",
                "capabilities": ["streaming", "prompt_management", "tool_use", "adaptive_thinking"],
                "sdk": "anthropic.AsyncAnthropic",
            },
            {
                "provider": "openai",
                "default_model": "gpt-5.5",
                "capabilities": ["streaming", "prompt_management", "tool_use", "openai_compatible_relays"],
                "sdk": "openai.AsyncOpenAI",
            },
            {
                "provider": "gemini",
                "default_model": "gemini-2.5-pro",
                "capabilities": ["streaming", "prompt_management"],
                "sdk": "google.genai.Client",
            },
        ]
    }


@router.get("/prompts")
def list_prompt_templates() -> dict[str, Any]:
    return {
        "prompts": [
            {
                "name": template.name,
                "system": template.system,
                "user_instruction": template.user_instruction,
                "max_output_seconds": template.max_output_seconds,
            }
            for template in _prompt_registry.templates.values()
        ]
    }


@router.post("/prompts/render")
def render_prompt(request: PromptRenderRequest) -> dict[str, Any]:
    try:
        return {"messages": _prompt_registry.render_messages(request.prompt_template, request.prompt_payload)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/complete")
async def complete(request: ModelGatewayRequest) -> dict[str, Any]:
    try:
        gateway = _gateway_from_request(request)
        messages = _messages_from_request(request, gateway.prompt_registry)
        message = await gateway.complete(messages, request.tools)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": {"text": message.text, "tool_calls": [call.as_dict() for call in message.tool_calls], "raw_message": message.raw_message}}


@router.post("/stream")
async def stream_complete(request: ModelGatewayRequest) -> StreamingResponse:
    try:
        gateway = _gateway_from_request(request)
        messages = _messages_from_request(request, gateway.prompt_registry)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def event_stream():
        try:
            async for chunk in gateway.stream_complete(messages, request.tools):
                yield f"event: token\ndata: {chunk}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {str(exc)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _gateway_from_request(request: ModelGatewayRequest) -> ModelGateway:
    return ModelGateway(
        provider=request.provider,
        model=request.model,
        base_url=request.base_url,
        api_key=request.api_key,
        wire_api=request.wire_api,
        workspace_root=str(_workspace_root),
    )


def _messages_from_request(request: ModelGatewayRequest, registry: PromptRegistry) -> list[dict[str, Any]]:
    if request.prompt_template:
        return registry.render_messages(request.prompt_template, request.prompt_payload)
    if not request.messages:
        raise ValueError("messages or prompt_template is required")
    return request.messages
