from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ProductionStatus = Literal["created", "planning", "rendering", "composing", "completed", "failed"]
TaskStatus = Literal["pending", "in_progress", "completed", "failed", "skipped"]


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class AlcoholSalesBrief(BaseModel):
    brand: str = ""
    product_name: str = ""
    product_brief: str = ""
    target_audience: str = ""
    sales_goal: str = ""
    channel: str = "直播间"
    tone: str = "可信、克制、有转化力"
    style: str = "高质感酒类直播间销售视频"
    mandatory_points: list[str] = Field(default_factory=list)
    prohibited_points: list[str] = Field(default_factory=lambda: [
        "不得面向未成年人",
        "不得暗示过量饮酒",
        "不得宣传医疗或保健功效",
        "不得鼓励酒后驾驶或危险行为",
    ])
    compliance_constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProductionRun(BaseModel):
    run_id: str
    session_id: str
    user_idea: str = ""
    brief: AlcoholSalesBrief = Field(default_factory=AlcoholSalesBrief)
    workflow_version: str = "alcohol-live-commerce-v1"
    status: ProductionStatus = "created"
    stage: str = "created"
    story_material_id: str = ""
    script_material_id: str = ""
    storyboard_material_id: str = ""
    shot_plan_material_id: str = ""
    digital_human_clip_ids: list[str] = Field(default_factory=list)
    transition_clip_ids: list[str] = Field(default_factory=list)
    composition_manifest_path: str = ""
    final_video_material_id: str = ""
    performance_summary: dict[str, Any] = Field(default_factory=dict)
    reusable_pattern_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProductionTaskRecord(BaseModel):
    task_id: str
    run_id: str
    session_id: str
    agent_name: str
    agent_role: str = "worker"
    status: TaskStatus = "pending"
    input_material_ids: list[str] = Field(default_factory=list)
    output_material_ids: list[str] = Field(default_factory=list)
    tool_name: str = ""
    provider: str = ""
    provider_job_ids: list[str] = Field(default_factory=list)
    started_at: str = Field(default_factory=utc_now_iso)
    finished_at: str = ""
    attempt_count: int = 1
    cost_estimate: float = 0.0
    error: str = ""
    progress_events: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MaterialRecord(BaseModel):
    material_id: str
    material_type: str
    role: str = ""
    session_id: str
    run_id: str
    task_id: str = ""
    source_agent: str = ""
    source_provider: str = ""
    provider_model: str = ""
    provider_job_id: str = ""
    prompt: str = ""
    negative_prompt: str = ""
    input_material_ids: list[str] = Field(default_factory=list)
    file_path: str = ""
    content_hash: str = ""
    mime_type: str = ""
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    text_content_preview: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    used_in_final: bool = False
    usage_notes: str = ""


class TimelineSegment(BaseModel):
    segment_id: str
    material_id: str
    file_path: str = ""
    start_time: float = 0.0
    duration: float = 0.0
    in_point: float = 0.0
    out_point: float | None = None
    layer: int = 0
    transform: dict[str, Any] = Field(default_factory=dict)
    audio_policy: str = "keep"
    transition_in: str = ""
    transition_out: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class FfmpegCommandSummary(BaseModel):
    argv: list[str] = Field(default_factory=list)
    returncode: int = 0
    stdout_preview: str = ""
    stderr_preview: str = ""
    created_at: str = Field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompositionManifest(BaseModel):
    composition_id: str
    run_id: str
    session_id: str
    timeline: list[TimelineSegment] = Field(default_factory=list)
    subtitles: list[dict[str, Any]] = Field(default_factory=list)
    audio_tracks: list[dict[str, Any]] = Field(default_factory=list)
    ffmpeg_commands: list[FfmpegCommandSummary] = Field(default_factory=list)
    output_material_id: str = ""
    output_path: str = ""
    created_at: str = Field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PerformanceMetric(BaseModel):
    metric_id: str
    run_id: str
    final_video_material_id: str = ""
    platform: str = ""
    platform_video_id: str = ""
    published_url: str = ""
    time_window_start: str = ""
    time_window_end: str = ""
    impressions: int = 0
    views: int = 0
    clicks: int = 0
    ctr: float = 0.0
    orders: int = 0
    units_sold: int = 0
    gmv: float = 0.0
    refunds: float = 0.0
    ad_spend: float = 0.0
    roi: float = 0.0
    conversion_rate: float = 0.0
    average_watch_seconds: float = 0.0
    completion_rate: float = 0.0
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    source: str = "manual"
    ingested_at: str = Field(default_factory=utc_now_iso)
    score: float = 0.0


class ReusablePattern(BaseModel):
    pattern_id: str
    source_run_id: str
    source_metric_id: str = ""
    score: float = 0.0
    product_category: str = "酒类"
    sales_angle: str = ""
    story_structure: str = ""
    script_hook: str = ""
    cta_style: str = ""
    digital_human_avatar: str = ""
    live_room_layout: str = ""
    transition_style: str = ""
    winning_material_ids: list[str] = Field(default_factory=list)
    recommended_reuse: str = ""
    avoid_notes: str = ""
    created_at: str = Field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = Field(default_factory=dict)
