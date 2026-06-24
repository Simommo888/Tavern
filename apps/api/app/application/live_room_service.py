from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_runtime.llm import AssistantMessage, OpenAICompatibleLLM
from apps.api.app.application.compliance_service import ComplianceService
from apps.api.app.application.speech_service import SpeechService
from apps.api.app.application.tasks.queue import FileTaskQueue
from apps.api.app.domain.live.entities import AnchorReply, AudienceEvent, AudienceIntent, LiveRoomEventRecord, LiveRoomSession, ProductProfile, SpeechArtifact
from apps.api.app.domain.tasks.entities import AsyncTask
from apps.api.app.domain.live.services import classify_intent, fallback_reply
from apps.api.app.infrastructure.repositories.file_live import FileLiveRoomRepository


class LiveRoomService:
    def __init__(self, workspace_root: str | Path = ".", llm: Any | None = None, repository: FileLiveRoomRepository | None = None, task_queue: FileTaskQueue | None = None) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.repository = repository or FileLiveRoomRepository(self.workspace_root)
        self.task_queue = task_queue or FileTaskQueue(self.workspace_root)
        self.llm = llm or OpenAICompatibleLLM()
        self.compliance = ComplianceService()
        self.speech = SpeechService(self.repository)

    async def create_session(self, product: ProductProfile | dict[str, Any] | None = None) -> LiveRoomSession:
        profile = product if isinstance(product, ProductProfile) else ProductProfile.model_validate(product or {})
        session = LiveRoomSession(status="running", product=profile)
        self.repository.save_session(session)
        self.repository.append_event(session.session_id, "session_created", {"session": session.model_dump()})
        return session

    def get_session(self, session_id: str) -> LiveRoomSession:
        return self.repository.get_session(session_id)

    def enqueue_audience_event(self, session_id: str, event: AudienceEvent | dict[str, Any]) -> AsyncTask:
        session = self.repository.get_session(session_id)
        payload = event if isinstance(event, AudienceEvent) else AudienceEvent.model_validate(event)
        intent = classify_intent(payload.text)
        session.event_count += 1
        session.recent_events = [*session.recent_events, payload][-20:]
        session.updated_at = payload.created_at
        self.repository.save_session(session)
        self.repository.append_event(session.session_id, "audience_event", {"event": payload.model_dump(), "intent": intent, "mode": "async"})
        task = self.task_queue.publish(
            "live.audience_event.received",
            {"session_id": session.session_id, "event": payload.model_dump()},
            idempotency_key=f"live-event:{session.session_id}:{payload.event_id}",
        )
        self.repository.append_event(session.session_id, "workflow_task_queued", {"task": task.model_dump()})
        return task

    async def process_queued_audience_event(self, session_id: str, event: AudienceEvent | dict[str, Any]) -> AnchorReply:
        session = self.repository.get_session(session_id)
        payload = event if isinstance(event, AudienceEvent) else AudienceEvent.model_validate(event)
        intent = classify_intent(payload.text)
        reply = await self._create_reply(session, payload, intent)
        session.reply_count += 1
        session.recent_replies = [*session.recent_replies, reply][-20:]
        session.updated_at = reply.created_at
        self.repository.save_session(session)
        speech = self.get_speech_artifact(session.session_id, reply.speech_artifact_id)
        self.repository.append_event(session.session_id, "speech_artifact", {"speech": speech.model_dump()})
        self.repository.append_event(session.session_id, "anchor_reply", {"reply": reply.model_dump(), "mode": "async"})
        return reply

    async def handle_audience_event(self, session_id: str, event: AudienceEvent | dict[str, Any]) -> AnchorReply:
        session = self.repository.get_session(session_id)
        payload = event if isinstance(event, AudienceEvent) else AudienceEvent.model_validate(event)
        intent = classify_intent(payload.text)
        reply = await self._create_reply(session, payload, intent)
        session.event_count += 1
        session.reply_count += 1
        session.recent_events = [*session.recent_events, payload][-20:]
        session.recent_replies = [*session.recent_replies, reply][-20:]
        session.updated_at = reply.created_at
        self.repository.save_session(session)
        speech = self.get_speech_artifact(session.session_id, reply.speech_artifact_id)
        self.repository.append_event(session.session_id, "audience_event", {"event": payload.model_dump(), "intent": intent})
        self.repository.append_event(session.session_id, "speech_artifact", {"speech": speech.model_dump()})
        self.repository.append_event(session.session_id, "anchor_reply", {"reply": reply.model_dump()})
        return reply

    def get_speech_artifact(self, session_id: str, artifact_id: str) -> SpeechArtifact:
        return self.repository.get_speech_artifact(session_id, artifact_id)

    def speech_audio_path(self, session_id: str, artifact_id: str) -> Path:
        return self.repository.speech_audio_path(session_id, artifact_id)

    def stop_session(self, session_id: str) -> LiveRoomSession:
        session = self.repository.get_session(session_id)
        session.status = "stopped"
        self.repository.save_session(session)
        self.repository.append_event(session.session_id, "session_stopped", {"session_id": session_id})
        return session

    def events(self, session_id: str) -> list[LiveRoomEventRecord]:
        return self.repository.events(session_id)

    async def _create_reply(self, session: LiveRoomSession, payload: AudienceEvent, intent: AudienceIntent) -> AnchorReply:
        draft = await self._draft_reply(session, payload, intent)
        checked = self.compliance.review_alcohol_reply(f"{payload.text}\n{draft}" if intent == "compliance_risk" else draft)
        reply = AnchorReply(
            session_id=session.session_id,
            event_id=payload.event_id,
            intent=intent,
            text=checked.text,
            compliance_passed=checked.passed,
            compliance_notes=checked.notes,
        )
        speech = await self.speech.create_speech_artifact(reply)
        reply.speech_artifact_id = speech.artifact_id
        reply.speech_audio_url = f"/api/v1/live/sessions/{session.session_id}/speech/{speech.artifact_id}/audio"
        return reply

    async def _draft_reply(self, session: LiveRoomSession, event: AudienceEvent, intent: AudienceIntent) -> str:
        system = "你是一个酒类电商直播间数字人主播。回答要口语化、简短、可信、克制，并严格遵守酒类合规：不面向未成年人，不宣传医疗保健功效，不鼓励过量饮酒或酒驾。"
        prompt = {
            "product": session.product.model_dump(),
            "audience_event": event.model_dump(),
            "intent": intent,
            "instruction": "生成一句适合主播直接口播的中文回复，80字以内。",
        }
        try:
            message: AssistantMessage = await self.llm.complete([
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ], tools=[])
            text = message.text.strip()
            if text:
                return text
        except Exception:
            pass
        return fallback_reply(session.product, event.text, intent)
