from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from apps.api.app.application.live_room_service import LiveRoomService
from apps.api.app.schemas.live import AudienceEvent, ProductProfile

router = APIRouter(prefix="/live", tags=["live"])
_service = LiveRoomService(Path(__file__).resolve().parents[5])


@router.post("/sessions")
async def create_live_session(product: ProductProfile | None = None) -> dict[str, Any]:
    session = await _service.create_session(product or ProductProfile())
    return {"session": session.model_dump()}


@router.get("/sessions/{session_id}")
def get_live_session(session_id: str) -> dict[str, Any]:
    try:
        session = _service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"session": session.model_dump(), "events": [event.model_dump() for event in _service.events(session_id)]}


@router.post("/sessions/{session_id}/events")
async def post_audience_event(session_id: str, event: AudienceEvent) -> dict[str, Any]:
    try:
        reply = await _service.handle_audience_event(session_id, event)
        session = _service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"reply": reply.model_dump(), "session": session.model_dump()}


@router.get("/sessions/{session_id}/events")
def list_live_events(session_id: str) -> dict[str, Any]:
    try:
        _service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"events": [event.model_dump() for event in _service.events(session_id)]}


@router.get("/sessions/{session_id}/speech/latest")
def latest_speech(session_id: str) -> dict[str, Any]:
    try:
        session = _service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    reply = session.recent_replies[-1] if session.recent_replies else None
    return {"speech": reply.model_dump() if reply else None}


@router.get("/sessions/{session_id}/speech/{artifact_id}/audio")
def speech_audio(session_id: str, artifact_id: str) -> FileResponse:
    try:
        path = _service.speech_audio_path(session_id, artifact_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="speech audio not found")
    speech = _service.get_speech_artifact(session_id, artifact_id)
    return FileResponse(path, media_type=speech.mime_type, filename=path.name)


@router.get("/sessions/{session_id}/events/stream")
async def stream_live_events(session_id: str) -> StreamingResponse:
    try:
        _service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def event_stream():
        offset = 0
        while True:
            events = _service.events(session_id)
            for event in events[offset:]:
                yield f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"
            offset = len(events)
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/sessions/{session_id}/stop")
def stop_live_session(session_id: str) -> dict[str, Any]:
    try:
        session = _service.stop_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"session": session.model_dump()}
