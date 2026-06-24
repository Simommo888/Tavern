from __future__ import annotations

import json
import wave
from pathlib import Path
from typing import Any

from .live_compliance import check_alcohol_compliance
from .live_room_models import AnchorReply, AudienceEvent, AudienceIntent, LiveRoomEventRecord, LiveRoomSession, ProductProfile, SpeechArtifact
from .llm import AssistantMessage, OpenAICompatibleLLM
from .speech_tts import synthesize_speech


class LiveRoomRuntime:
    def __init__(self, workspace_root: str | Path = ".", llm: Any | None = None) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.store_dir = self.workspace_root / ".working_dir" / "live_rooms"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.llm = llm or OpenAICompatibleLLM()

    async def create_session(self, product: ProductProfile | dict[str, Any] | None = None) -> LiveRoomSession:
        profile = product if isinstance(product, ProductProfile) else ProductProfile.model_validate(product or {})
        session = LiveRoomSession(status="running", product=profile)
        self._save_session(session)
        self._append_event(session.session_id, "session_created", {"session": session.model_dump()})
        return session

    def get_session(self, session_id: str) -> LiveRoomSession:
        path = self._session_path(session_id)
        if not path.exists():
            raise KeyError(f"Unknown live room session: {session_id}")
        return LiveRoomSession.model_validate_json(path.read_text(encoding="utf-8"))

    async def handle_audience_event(self, session_id: str, event: AudienceEvent | dict[str, Any]) -> AnchorReply:
        session = self.get_session(session_id)
        payload = event if isinstance(event, AudienceEvent) else AudienceEvent.model_validate(event)
        intent = classify_intent(payload.text)
        draft = await self._draft_reply(session, payload, intent)
        checked = check_alcohol_compliance(f"{payload.text}\n{draft}" if intent == "compliance_risk" else draft)
        reply = AnchorReply(session_id=session.session_id, event_id=payload.event_id, intent=intent, text=checked.text, compliance_passed=checked.passed, compliance_notes=checked.notes)
        speech = await self.create_speech_artifact(reply)
        reply.speech_artifact_id = speech.artifact_id
        reply.speech_audio_url = f"/api/live/sessions/{session.session_id}/speech/{speech.artifact_id}/audio"
        session.event_count += 1
        session.reply_count += 1
        session.recent_events = [*session.recent_events, payload][-20:]
        session.recent_replies = [*session.recent_replies, reply][-20:]
        session.updated_at = reply.created_at
        self._save_session(session)
        self._append_event(session.session_id, "audience_event", {"event": payload.model_dump(), "intent": intent})
        self._append_event(session.session_id, "speech_artifact", {"speech": speech.model_dump()})
        self._append_event(session.session_id, "anchor_reply", {"reply": reply.model_dump()})
        return reply

    async def create_speech_artifact(self, reply: AnchorReply) -> SpeechArtifact:
        speech = SpeechArtifact(session_id=reply.session_id, reply_id=reply.reply_id, text=reply.text)
        output_dir = self.store_dir / reply.session_id / "speech"
        path, mime_type, provider = await synthesize_speech(reply.text, output_dir, speech.artifact_id)
        speech.audio_path = str(path.relative_to(self.store_dir / reply.session_id)).replace("\\", "/")
        speech.mime_type = mime_type
        speech.provider = provider
        self._save_speech_artifact(speech)
        return speech

    def get_speech_artifact(self, session_id: str, artifact_id: str) -> SpeechArtifact:
        path = self._speech_meta_path(session_id, artifact_id)
        if not path.exists():
            raise KeyError(f"Unknown speech artifact: {artifact_id}")
        return SpeechArtifact.model_validate_json(path.read_text(encoding="utf-8"))

    def speech_audio_path(self, session_id: str, artifact_id: str) -> Path:
        speech = self.get_speech_artifact(session_id, artifact_id)
        path = (self.store_dir / session_id / speech.audio_path).resolve()
        if self.store_dir.resolve() not in path.parents:
            raise ValueError("Speech audio path escapes live room store")
        return path

    def stop_session(self, session_id: str) -> LiveRoomSession:
        session = self.get_session(session_id)
        session.status = "stopped"
        self._save_session(session)
        self._append_event(session.session_id, "session_stopped", {"session_id": session_id})
        return session

    def events(self, session_id: str) -> list[LiveRoomEventRecord]:
        path = self._events_path(session_id)
        if not path.exists():
            return []
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(LiveRoomEventRecord.model_validate_json(line))
        return rows

    async def _draft_reply(self, session: LiveRoomSession, event: AudienceEvent, intent: AudienceIntent) -> str:
        product = session.product
        prompt = {"product": product.model_dump(), "audience_event": event.model_dump(), "intent": intent}
        try:
            if hasattr(self.llm, "complete_prompt"):
                message: AssistantMessage = await self.llm.complete_prompt("live_anchor_reply", prompt)
            else:
                message = await self.llm.complete([
                    {"role": "system", "content": "你是酒类电商直播间数字人主播，回答要自然口语化、可信、克制，并严格遵守酒类合规。"},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ], tools=[])
            text = message.text.strip()
            if text:
                return text
        except Exception:
            pass
        return fallback_reply(product, event.text, intent)

    def _session_path(self, session_id: str) -> Path:
        return self.store_dir / session_id / "session.json"

    def _events_path(self, session_id: str) -> Path:
        return self.store_dir / session_id / "events.jsonl"

    def _speech_path(self, session_id: str, artifact_id: str) -> Path:
        return self.store_dir / session_id / "speech" / f"{artifact_id}.wav"

    def _speech_meta_path(self, session_id: str, artifact_id: str) -> Path:
        return self.store_dir / session_id / "speech" / f"{artifact_id}.json"

    def _save_speech_artifact(self, speech: SpeechArtifact) -> None:
        path = self._speech_meta_path(speech.session_id, speech.artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(speech.model_dump_json(indent=2), encoding="utf-8")

    def _save_session(self, session: LiveRoomSession) -> None:
        path = self._session_path(session.session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(session.model_dump_json(indent=2), encoding="utf-8")

    def _append_event(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        record = LiveRoomEventRecord(type=event_type, session_id=session_id, payload=payload)
        path = self._events_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json() + "\n")


def _write_silence_wav(path: Path, duration_seconds: float = 0.35, sample_rate: int = 16000) -> None:
    frame_count = max(1, int(duration_seconds * sample_rate))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frame_count)


def classify_intent(text: str) -> AudienceIntent:
    lowered = text.lower()
    if any(token in text for token in ["多少钱", "价格", "几块", "贵不贵"]):
        return "price_question"
    if any(token in text for token in ["送人", "送礼", "领导", "长辈", "端午"]):
        return "gift_question"
    if any(token in text for token in ["优惠", "福利", "券", "活动"]):
        return "promotion_question"
    if any(token in text for token in ["养生", "保健", "治", "未成年", "小孩", "开车", "多喝"]):
        return "compliance_risk"
    if any(token in text for token in ["度数", "规格", "产地", "香型", "口感"]):
        return "product_question"
    if "price" in lowered:
        return "price_question"
    return "smalltalk"


def fallback_reply(product: ProductProfile, text: str, intent: AudienceIntent) -> str:
    name = product.product_name or "这款产品"
    if intent == "price_question":
        return f"{name}的价格和权益以直播间当前活动为准，我建议大家按自己的送礼或宴请需求理性选择。"
    if intent == "gift_question":
        return f"{name}更适合成年人节日送礼、宴请拜访这类正式场景，礼盒包装会更体面一些。"
    if intent == "promotion_question":
        return f"今天主要看直播间实时权益和组合活动，我会把规格、适用场景和注意事项讲清楚。"
    if intent == "product_question":
        points = "、".join(product.selling_points[:3]) or "礼盒包装、宴请送礼"
        return f"{name}主打{points}，具体规格建议以下单页和客服确认为准。"
    if intent == "compliance_risk":
        return "酒类产品只面向成年人，不能宣传养生或医疗功效，也提醒大家适量理性饮酒。"
    return f"欢迎来到直播间，今天主要给大家介绍{name}，有价格、送礼和规格问题都可以直接问。"
