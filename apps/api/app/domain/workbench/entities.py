from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from interfaces.production import utc_now_iso

ProductStatus = Literal["draft", "published", "archived"]
AvatarStatus = Literal["draft", "ready", "disabled"]
ScriptCategory = Literal["opening", "product", "sales", "interaction", "thanks"]
WorkflowEventType = Literal["user_enter", "user_follow", "fan_club_join", "comment", "order_created", "refund", "cold_start"]
WorkflowActionType = Literal["welcome", "reply_comment", "tell_story", "sales_push", "thank_order", "switch_product", "run_script"]
PlatformType = Literal["manual", "mock", "douyin", "taobao", "wechat_channels"]


class ProductFaq(BaseModel):
    question: str
    answer: str


class ProductRecord(BaseModel):
    product_id: str = Field(default_factory=lambda: f"prod-{uuid4().hex[:10]}")
    product_name: str
    sku: str
    price: float
    original_price: float = 0
    aroma_type: str = ""
    alcohol_degree: str = ""
    volume: str = ""
    selling_points: list[str] = Field(default_factory=list)
    scenes: list[str] = Field(default_factory=list)
    faqs: list[ProductFaq] = Field(default_factory=list)
    status: ProductStatus = "draft"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class AvatarProfile(BaseModel):
    avatar_id: str = Field(default_factory=lambda: f"avatar-{uuid4().hex[:10]}")
    name: str
    provider: str = "heygen"
    heygen_avatar_id: str = ""
    heygen_voice_id: str = ""
    voice_name: str = ""
    source_material_urls: list[str] = Field(default_factory=list)
    status: AvatarStatus = "draft"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class ScriptTemplate(BaseModel):
    template_id: str = Field(default_factory=lambda: f"script-{uuid4().hex[:10]}")
    name: str
    category: ScriptCategory
    content: str
    product_id: str = ""
    tags: list[str] = Field(default_factory=list)
    ai_generated: bool = False
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class WorkflowRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: f"rule-{uuid4().hex[:10]}")
    name: str
    event_type: WorkflowEventType
    action_type: WorkflowActionType
    enabled: bool = True
    delay_seconds: int = 0
    conditions: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class PlatformAccount(BaseModel):
    account_id: str = Field(default_factory=lambda: f"platform-{uuid4().hex[:10]}")
    platform: PlatformType = "manual"
    display_name: str
    status: str = "connected"
    credentials_configured: bool = False
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class PlatformMetricSnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: f"metric-{uuid4().hex[:10]}")
    session_id: str = ""
    platform: PlatformType = "manual"
    online_users: int = 0
    gmv: float = 0
    order_count: int = 0
    interaction_rate: float = 0
    conversion_rate: float = 0
    current_product_id: str = ""
    created_at: str = Field(default_factory=utc_now_iso)


class KnowledgeDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: f"doc-{uuid4().hex[:10]}")
    name: str
    source_type: Literal["pdf", "word", "excel", "csv", "text"] = "text"
    product_id: str = ""
    object_key: str = ""
    status: Literal["uploaded", "indexed", "failed"] = "uploaded"
    chunk_count: int = 0
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class KnowledgeChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: f"chunk-{uuid4().hex[:10]}")
    document_id: str
    product_id: str = ""
    chunk_index: int = 0
    text: str
    embedding_status: Literal["pending", "embedded", "failed"] = "pending"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)


class ModelProviderConfig(BaseModel):
    provider_id: str = Field(default_factory=lambda: f"model-{uuid4().hex[:10]}")
    name: Literal["gemini", "claude", "gpt", "openai_compatible"] = "openai_compatible"
    display_name: str
    base_url: str = ""
    chat_model: str = ""
    embedding_model: str = ""
    streaming_supported: bool = True
    prompt_management_supported: bool = True
    configured: bool = False
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class PromptTemplate(BaseModel):
    prompt_id: str = Field(default_factory=lambda: f"prompt-{uuid4().hex[:10]}")
    name: str
    purpose: str
    version: str = "v1"
    content: str
    variables: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class AvatarJob(BaseModel):
    job_id: str = Field(default_factory=lambda: f"avatar-job-{uuid4().hex[:10]}")
    avatar_id: str
    job_type: Literal["create_avatar", "text_drive", "speech_drive", "live_avatar_session"] = "text_drive"
    input_text: str = ""
    input_audio_url: str = ""
    provider_job_id: str = ""
    status: Literal["queued", "running", "succeeded", "failed"] = "queued"
    output_url: str = ""
    error: str = ""
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class PlatformEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"platform-event-{uuid4().hex[:10]}")
    account_id: str = ""
    session_id: str = ""
    platform: PlatformType = "manual"
    event_type: WorkflowEventType = "comment"
    user_name: str = "观众"
    text: str = ""
    order_amount: float = 0
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
