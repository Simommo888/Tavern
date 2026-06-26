from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from agent_runtime.llm import ModelGateway, PromptRegistry, PromptTemplate
from apps.api.app.schemas.model_gateway import ModelGatewayRequest, PromptRenderRequest, PromptTemplateUpsertRequest

router = APIRouter(prefix="/model-gateway", tags=["model-gateway"])
_workspace_root = Path(__file__).resolve().parents[5]
_prompt_registry = PromptRegistry(workspace_root=_workspace_root)


@router.get("/providers")
def list_model_providers() -> dict[str, Any]:
    return {
        "providers": [
            {
                "provider_id": "model-claude",
                "name": "claude",
                "provider": "claude",
                "display_name": "Claude 高质量策划模型",
                "default_model": "claude-opus-4-8",
                "chat_model": "claude-opus-4-8",
                "embedding_model": "",
                "streaming_supported": True,
                "prompt_management_supported": True,
                "configured": False,
                "capabilities": ["streaming", "prompt_management", "tool_use", "adaptive_thinking"],
                "sdk": "anthropic.AsyncAnthropic",
            },
            {
                "provider_id": "model-gpt",
                "name": "gpt",
                "provider": "openai",
                "display_name": "GPT 主力回复模型",
                "default_model": "gpt-5.5",
                "chat_model": "gpt-5.5",
                "embedding_model": "text-embedding-3-large",
                "streaming_supported": True,
                "prompt_management_supported": True,
                "configured": False,
                "capabilities": ["streaming", "prompt_management", "tool_use", "openai_compatible_relays"],
                "sdk": "openai.AsyncOpenAI",
            },
            {
                "provider_id": "model-gemini",
                "name": "gemini",
                "provider": "gemini",
                "display_name": "Gemini 多模态模型",
                "default_model": "gemini-2.5-pro",
                "chat_model": "gemini-2.5-pro",
                "embedding_model": "",
                "streaming_supported": True,
                "prompt_management_supported": True,
                "configured": False,
                "capabilities": ["streaming", "prompt_management"],
                "sdk": "google.genai.Client",
            },
        ]
    }


@router.get("/prompts")
def list_prompt_templates() -> dict[str, Any]:
    prompts = []
    for index, template in enumerate(_prompt_registry.templates.values(), start=1):
        purpose = "live_reply" if template.name == "live_anchor_reply" else template.name
        prompts.append({
            "prompt_id": f"prompt-{index:03d}",
            "name": template.name,
            "purpose": purpose,
            "version": "v1",
            "content": template.user_instruction,
            "variables": sorted(_prompt_variables(template.user_instruction)),
            "system": template.system,
            "user_instruction": template.user_instruction,
            "max_output_seconds": template.max_output_seconds,
        })
    return {"prompts": prompts}


@router.post("/prompts")
def upsert_prompt_template(request: PromptTemplateUpsertRequest) -> dict[str, Any]:
    template = _prompt_registry.upsert(
        PromptTemplate(
            name=request.name,
            system=request.system,
            user_instruction=request.user_instruction,
            max_output_seconds=request.max_output_seconds,
        )
    )
    return {
        "prompt": {
            "prompt_id": f"prompt-custom-{request.name}",
            "name": template.name,
            "purpose": template.name,
            "version": "custom",
            "content": template.user_instruction,
            "variables": sorted(_prompt_variables(template.user_instruction)),
            "system": template.system,
            "user_instruction": template.user_instruction,
            "max_output_seconds": template.max_output_seconds,
        }
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
        message = await gateway.complete(messages, request.tools, max_tokens=request.max_tokens, effort=request.effort)
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
            async for chunk in gateway.stream_complete(messages, request.tools, max_tokens=request.max_tokens, effort=request.effort):
                yield f"event: token\ndata: {chunk}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {str(exc)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _prompt_variables(template: str) -> set[str]:
    import re

    return set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", template))


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
