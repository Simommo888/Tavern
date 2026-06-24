from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from interfaces.production import utc_now_iso

LiveRoomStatus = Literal["created", "running", "stopped"]
AudienceIntent = Literal["price_question", "gift_question", "promotion_question", "compliance_risk", "product_question", "smalltalk"]


class ProductProfile(BaseModel):
    product_name: str = "酱香酒端午礼盒"
    brand: str = ""
    price: str = "以直播间实时权益为准"
    specification: str = ""
    selling_points: list[str] = Field(default_factory=lambda: ["节日送礼", "礼盒包装", "成熟消费者宴请场景"])
    promotions: list[str] = Field(default_factory=list)
    compliance_notes: list[str] = Field(default_factory=lambda: ["不面向未成年人", "理性饮酒", "不宣传医疗或保健功效", "不鼓励酒后驾驶"])
    metadata: dict[str, Any] = Field(default_factory=dict)


class AudienceEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt-{uuid4().hex[:10]}")
    user_id: str = "anonymous"
    user_name: str = "观众"
    text: str
    source: str = "manual"
    created_at: str = Field(default_factory=utc_now_iso)


class AnchorReply(BaseModel):
    reply_id: str = Field(default_factory=lambda: f"reply-{uuid4().hex[:10]}")
    session_id: str
    event_id: str = ""
    intent: AudienceIntent = "smalltalk"
    text: str
    compliance_passed: bool = True
    compliance_notes: list[str] = Field(default_factory=list)
    speech_artifact_id: str = ""
    speech_audio_url: str = ""
    created_at: str = Field(default_factory=utc_now_iso)


class SpeechArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: f"speech-{uuid4().hex[:10]}")
    session_id: str
    reply_id: str
    text: str
    provider: str = "browser-fallback-placeholder"
    audio_path: str = ""
    mime_type: str = "audio/wav"
    duration_seconds: float = 0.0
    created_at: str = Field(default_factory=utc_now_iso)


class LiveRoomSession(BaseModel):
    session_id: str = Field(default_factory=lambda: f"live-{uuid4().hex[:10]}")
    status: LiveRoomStatus = "created"
    product: ProductProfile = Field(default_factory=ProductProfile)
    current_topic: str = "开场介绍"
    event_count: int = 0
    reply_count: int = 0
    recent_events: list[AudienceEvent] = Field(default_factory=list)
    recent_replies: list[AnchorReply] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class LiveRoomEventRecord(BaseModel):
    type: str
    session_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
