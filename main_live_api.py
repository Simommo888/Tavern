from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from agent_runtime.live_room_models import AudienceEvent, ProductProfile
from agent_runtime.live_room_runtime import LiveRoomRuntime

app = FastAPI(title="Tavern Live Room API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_runtime = LiveRoomRuntime(Path(__file__).resolve().parent)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/live/sessions")
async def create_live_session(product: ProductProfile | None = None) -> dict[str, Any]:
    session = await _runtime.create_session(product or ProductProfile())
    return {"session": session.model_dump()}


@app.get("/api/live/sessions/{session_id}")
def get_live_session(session_id: str) -> dict[str, Any]:
    try:
        session = _runtime.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"session": session.model_dump(), "events": [event.model_dump() for event in _runtime.events(session_id)]}


@app.post("/api/live/sessions/{session_id}/events")
async def post_audience_event(session_id: str, event: AudienceEvent) -> dict[str, Any]:
    try:
        reply = await _runtime.handle_audience_event(session_id, event)
        session = _runtime.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"reply": reply.model_dump(), "session": session.model_dump()}


@app.get("/api/live/sessions/{session_id}/events")
def list_live_events(session_id: str) -> dict[str, Any]:
    try:
        _runtime.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"events": [event.model_dump() for event in _runtime.events(session_id)]}


@app.get("/api/live/sessions/{session_id}/speech/latest")
def latest_speech(session_id: str) -> dict[str, Any]:
    try:
        session = _runtime.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    reply = session.recent_replies[-1] if session.recent_replies else None
    return {"speech": reply.model_dump() if reply else None}


@app.get("/api/live/sessions/{session_id}/speech/{artifact_id}/audio")
def speech_audio(session_id: str, artifact_id: str) -> FileResponse:
    try:
        path = _runtime.speech_audio_path(session_id, artifact_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="speech audio not found")
    speech = _runtime.get_speech_artifact(session_id, artifact_id)
    return FileResponse(path, media_type=speech.mime_type, filename=path.name)


@app.get("/api/live/sessions/{session_id}/events/stream")
async def stream_live_events(session_id: str) -> StreamingResponse:
    try:
        _runtime.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def event_stream():
        offset = 0
        while True:
            events = _runtime.events(session_id)
            for event in events[offset:]:
                yield f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"
            offset = len(events)
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/live/sessions/{session_id}/stop")
def stop_live_session(session_id: str) -> dict[str, Any]:
    try:
        session = _runtime.stop_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"session": session.model_dump()}


def main() -> None:
    import uvicorn

    uvicorn.run("main_live_api:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
