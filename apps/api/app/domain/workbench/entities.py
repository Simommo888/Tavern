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
ProjectStatus = Literal["draft", "active", "archived"]
AgentStatus = Literal["idle", "working", "blocked", "offline"]
RunStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
AssetStatus = Literal["uploaded", "processing", "ready", "failed", "archived"]
ComponentStatus = Literal["draft", "ready", "archived"]
PluginCategory = Literal["model", "tts", "avatar", "video", "streaming", "workflow", "rag", "storage"]
PluginSourceType = Literal["builtin", "github", "api", "local_service"]


class ProductFaq(BaseModel):
    question: str
    answer: str


class ProductRecord(BaseModel):
    product_id: str = Field(default_factory=lambda: f"prod-{uuid4().hex[:10]}")
    product_name: str
    sku: str = ""
    price: float = 0
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
    status: RunStatus = "queued"
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


class Project(BaseModel):
    project_id: str = Field(default_factory=lambda: f"proj-{uuid4().hex[:10]}")
    name: str
    brand_name: str = ""
    industry: str = "酒类直播电商"
    objective: str = "生成可复用的 AI 数字人直播方案"
    status: ProjectStatus = "active"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class AgentProfile(BaseModel):
    agent_id: str = Field(default_factory=lambda: f"agent-{uuid4().hex[:10]}")
    name: str
    role: str
    department: str = "LiveOS"
    status: AgentStatus = "idle"
    current_task: str = ""
    progress: float = 0
    token_count: int = 0
    cost_estimate: float = 0
    elapsed_seconds: int = 0
    logs: list[str] = Field(default_factory=list)
    output_summary: str = ""
    tool_names: list[str] = Field(default_factory=list)
    model_provider: str = "openai_compatible"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class AgentRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"agent-run-{uuid4().hex[:10]}")
    project_id: str = ""
    agent_id: str = ""
    workflow_run_id: str = ""
    node_run_id: str = ""
    task: str
    status: RunStatus = "queued"
    progress: float = 0
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    token_count: int = 0
    cost_estimate: float = 0
    duration_seconds: float = 0
    error: str = ""
    started_at: str = Field(default_factory=utc_now_iso)
    completed_at: str = ""


class Asset(BaseModel):
    asset_id: str = Field(default_factory=lambda: f"asset-{uuid4().hex[:10]}")
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    version: str = "v1"
    project_id: str = ""
    name: str
    asset_type: str = "document"
    source_uri: str = ""
    object_key: str = ""
    preview_url: str = ""
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    converted_component_ids: list[str] = Field(default_factory=list)
    status: AssetStatus = "ready"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class LiveComponent(BaseModel):
    component_id: str = Field(default_factory=lambda: f"component-{uuid4().hex[:10]}")
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    component_code: str = ""
    name: str
    component_type: str
    current_version: str = "v1"
    project_id: str = ""
    source_asset_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    product_types: list[str] = Field(default_factory=list)
    usage_count: int = 0
    rating: float = 0
    gmv: float = 0
    ctr: float = 0
    cvr: float = 0
    best_session_count: int = 0
    resource_url: str = ""
    preview_url: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: ComponentStatus = "ready"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class ComponentVersion(BaseModel):
    version_id: str = Field(default_factory=lambda: f"component-version-{uuid4().hex[:10]}")
    component_id: str
    version: str = "v1"
    resource_url: str = ""
    preview_url: str = ""
    changelog: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)


class LiveRoomTemplate(BaseModel):
    template_id: str = Field(default_factory=lambda: f"room-template-{uuid4().hex[:10]}")
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    version: str = "v1"
    project_id: str = ""
    name: str
    component_ids: list[str] = Field(default_factory=list)
    layout: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class LiveScene(BaseModel):
    scene_id: str = Field(default_factory=lambda: f"scene-{uuid4().hex[:10]}")
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    version: str = "v1"
    project_id: str = ""
    name: str
    scene_type: str = "live_room"
    component_ids: list[str] = Field(default_factory=list)
    component_slots: list[dict[str, Any]] = Field(default_factory=list)
    component_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    layout: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: ComponentStatus = "ready"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class LiveRoomComposition(BaseModel):
    composition_id: str = Field(default_factory=lambda: f"room-composition-{uuid4().hex[:10]}")
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    version: str = "v1"
    project_id: str = ""
    name: str
    template_id: str = ""
    scene_ids: list[str] = Field(default_factory=list)
    scene_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    components: list[dict[str, Any]] = Field(default_factory=list)
    component_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: ComponentStatus = "ready"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class LiveSessionSnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: f"session-snapshot-{uuid4().hex[:10]}")
    project_id: str = ""
    session_id: str = ""
    composition_id: str = ""
    component_ids: list[str] = Field(default_factory=list)
    script_ids: list[str] = Field(default_factory=list)
    prompt_versions: list[str] = Field(default_factory=list)
    avatar_id: str = ""
    voice_id: str = ""
    workflow_version: str = "v1"
    performance_metric_id: str = ""
    snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)


class PerformanceMetric(BaseModel):
    metric_id: str = Field(default_factory=lambda: f"performance-{uuid4().hex[:10]}")
    project_id: str = ""
    session_id: str = ""
    component_ids: list[str] = Field(default_factory=list)
    gmv: float = 0
    ctr: float = 0
    cvr: float = 0
    watch_seconds: int = 0
    retention_rate: float = 0
    interaction_rate: float = 0
    like_count: int = 0
    comment_count: int = 0
    order_count: int = 0
    refund_rate: float = 0
    product_clicks: int = 0
    add_to_cart_rate: float = 0
    conversion_rate: float = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)


class BestPractice(BaseModel):
    best_practice_id: str = Field(default_factory=lambda: f"best-{uuid4().hex[:10]}")
    project_id: str = ""
    title: str
    query_label: str = ""
    source_session_id: str = ""
    component_ids: list[str] = Field(default_factory=list)
    script_ids: list[str] = Field(default_factory=list)
    prompt_versions: list[str] = Field(default_factory=list)
    score: float = 0
    reason: str = ""
    reusable_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)


class PromptVersion(BaseModel):
    prompt_version_id: str = Field(default_factory=lambda: f"prompt-version-{uuid4().hex[:10]}")
    prompt_id: str = ""
    name: str
    purpose: str
    version: str = "v1"
    content: str
    variables: list[str] = Field(default_factory=list)
    score: float = 0
    use_count: int = 0
    cost_estimate: float = 0
    gmv: float = 0
    ctr: float = 0
    cvr: float = 0
    status: str = "active"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class MvpLivePlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"mvp-plan-{uuid4().hex[:10]}")
    project_id: str = ""
    product_id: str = ""
    workflow_run_id: str = ""
    script_template_id: str = ""
    avatar_id: str = ""
    avatar_job_id: str = ""
    live_room_composition_id: str = ""
    status: RunStatus = "succeeded"
    steps: list[dict[str, Any]] = Field(default_factory=list)
    product_snapshot: dict[str, Any] = Field(default_factory=dict)
    brand_analysis: dict[str, Any] = Field(default_factory=dict)
    script_snapshot: dict[str, Any] = Field(default_factory=dict)
    speech_artifact_uri: str = ""
    avatar_video_uri: str = ""
    live_video_uri: str = ""
    saved_outputs: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class WorkflowDefinition(BaseModel):
    workflow_definition_id: str = Field(default_factory=lambda: f"workflow-def-{uuid4().hex[:10]}")
    name: str
    version: str = "v1"
    description: str = ""
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "active"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class WorkflowRun(BaseModel):
    workflow_run_id: str = Field(default_factory=lambda: f"workflow-run-{uuid4().hex[:10]}")
    project_id: str = ""
    workflow_definition_id: str = ""
    status: RunStatus = "running"
    progress: float = 0
    current_node_id: str = ""
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    token_count: int = 0
    cost_estimate: float = 0
    duration_seconds: float = 0
    error: str = ""
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class WorkflowNodeRun(BaseModel):
    node_run_id: str = Field(default_factory=lambda: f"workflow-node-{uuid4().hex[:10]}")
    workflow_run_id: str
    node_id: str
    name: str
    agent_id: str = ""
    status: RunStatus = "queued"
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    prompt_version_id: str = ""
    logs: list[str] = Field(default_factory=list)
    token_count: int = 0
    cost_estimate: float = 0
    duration_seconds: float = 0
    error: str = ""
    started_at: str = Field(default_factory=utc_now_iso)
    completed_at: str = ""


class PluginProvider(BaseModel):
    plugin_id: str = Field(default_factory=lambda: f"plugin-{uuid4().hex[:10]}")
    category: PluginCategory
    provider_id: str
    display_name: str
    source_type: PluginSourceType = "builtin"
    repo_url: str = ""
    commit: str = ""
    license: str = ""
    capabilities: list[str] = Field(default_factory=list)
    enabled: bool = True
    health_status: str = "unknown"
    config_schema: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
