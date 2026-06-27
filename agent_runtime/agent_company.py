from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Sequence


DEFAULT_AGENT_CAPABILITIES = ("prompt", "memory", "tool", "workflow", "mcp")


@dataclass(frozen=True, slots=True)
class AgentRoute:
    role_id: str
    role_name: str
    confidence: float
    matched_signals: tuple[str, ...] = ()
    reason: str = ""
    handoff_to: tuple[str, ...] = ()
    fallback_role_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "role_name": self.role_name,
            "confidence": self.confidence,
            "matched_signals": list(self.matched_signals),
            "reason": self.reason,
            "handoff_to": list(self.handoff_to),
            "fallback_role_id": self.fallback_role_id,
        }


@dataclass(frozen=True, slots=True)
class AgentRoleSpec:
    role_id: str
    title: str
    name: str
    department: str
    mission: str
    responsibilities: tuple[str, ...] = ()
    input_keys: tuple[str, ...] = ()
    output_keys: tuple[str, ...] = ()
    tool_names: tuple[str, ...] = ()
    prompt_focus: tuple[str, ...] = ()
    memory_scope: str = "session"
    handoff_to: tuple[str, ...] = ()
    mcp_capabilities: tuple[str, ...] = DEFAULT_AGENT_CAPABILITIES
    legacy_modules: tuple[str, ...] = ()
    routing_signals: tuple[str, ...] = ()
    routing_weights: dict[str, float] = field(default_factory=dict)
    required_routing_signals: tuple[str, ...] = ()
    negative_routing_signals: tuple[str, ...] = ()
    routing_threshold: float = 0.55
    metadata: dict[str, Any] = field(default_factory=dict)

    def describe(self, *, next_role: str = "") -> str:
        lines = [f"- {self.title} / {self.department}", f"  name: {self.name}", f"  mission: {self.mission}"]
        if self.responsibilities:
            lines.append("  responsibilities:")
            lines.extend(f"    - {item}" for item in self.responsibilities)
        if self.input_keys:
            lines.append(f"  inputs: {', '.join(self.input_keys)}")
        if self.output_keys:
            lines.append(f"  outputs: {', '.join(self.output_keys)}")
        if self.tool_names:
            lines.append(f"  tools: {', '.join(self.tool_names)}")
        if self.prompt_focus:
            lines.append(f"  prompt_focus: {', '.join(self.prompt_focus)}")
        lines.append(f"  memory_scope: {self.memory_scope}")
        lines.append(f"  mcp_layers: {', '.join(self.mcp_capabilities)}")
        if self.legacy_modules:
            lines.append(f"  legacy_modules: {', '.join(self.legacy_modules)}")
        if next_role:
            lines.append(f"  handoff_to: {next_role}")
        return "\n".join(lines)

    def profile_payload(
        self,
        *,
        status: str = "idle",
        current_task: str = "",
        progress: float = 0.0,
        token_count: int = 0,
        cost_estimate: float = 0.0,
        elapsed_seconds: int = 0,
        logs: Sequence[str] | None = None,
        output_summary: str = "",
        model_provider: str = "openai_compatible",
    ) -> dict[str, Any]:
        metadata = {
            **self.metadata,
            "role_id": self.role_id,
            "title": self.title,
            "mission": self.mission,
            "responsibilities": list(self.responsibilities),
            "input_keys": list(self.input_keys),
            "output_keys": list(self.output_keys),
            "tool_names": list(self.tool_names),
            "prompt_focus": list(self.prompt_focus),
            "memory_scope": self.memory_scope,
            "handoff_to": list(self.handoff_to),
            "mcp_capabilities": list(self.mcp_capabilities),
            "legacy_modules": list(self.legacy_modules),
            "routing_signals": list(self.routing_signals),
            "routing_weights": dict(self.routing_weights),
            "required_routing_signals": list(self.required_routing_signals),
            "negative_routing_signals": list(self.negative_routing_signals),
            "routing_threshold": self.routing_threshold,
        }
        return {
            "name": self.name,
            "role": self.mission,
            "department": self.department,
            "status": status,
            "current_task": current_task or self.mission,
            "progress": progress,
            "token_count": token_count,
            "cost_estimate": cost_estimate,
            "elapsed_seconds": elapsed_seconds,
            "logs": list(logs or ()),
            "output_summary": output_summary or self.mission,
            "tool_names": list(self.tool_names),
            "model_provider": model_provider,
            "metadata": metadata,
        }


class AgentCompanyRegistry:
    def __init__(self, roles: Sequence[AgentRoleSpec] | None = None) -> None:
        self._roles = tuple(roles or ())
        self._by_role_id = {role.role_id: role for role in self._roles}
        if len(self._by_role_id) != len(self._roles):
            raise ValueError("AgentCompanyRegistry requires unique role_id values")
        self._ordered_role_ids = [role.role_id for role in self._roles]

    def list_roles(self) -> list[AgentRoleSpec]:
        return list(self._roles)

    def role_ids(self) -> list[str]:
        return list(self._ordered_role_ids)

    def get(self, role_id: str) -> AgentRoleSpec:
        try:
            return self._by_role_id[role_id]
        except KeyError as exc:
            raise KeyError(f"Unknown agent role: {role_id}") from exc

    def route_for_request(self, text: str) -> AgentRoute:
        if not self._roles:
            return AgentRoute(role_id="", role_name="", confidence=0.0, reason="Agent company registry is empty")
        normalized = _normalize_text(text)
        scored: list[tuple[float, int, int, AgentRoleSpec, tuple[str, ...], tuple[str, ...]]] = []
        for index, role in enumerate(self._roles):
            score, matches, required_matches = _score_role_route(role, normalized)
            if score >= role.routing_threshold:
                scored.append((score, len(required_matches), -index, role, matches, required_matches))
        if scored:
            score, _, _, role, matches, required_matches = max(scored, key=lambda item: (item[0], item[1], item[2]))
            confidence = min(0.98, max(0.55, score / (score + 2.5)))
            reason = f"weighted signals: {', '.join(matches)}; score={score:.2f}"
            if required_matches:
                reason += f"; required matched: {', '.join(required_matches)}"
            return AgentRoute(
                role_id=role.role_id,
                role_name=role.name,
                confidence=confidence,
                matched_signals=matches,
                reason=reason,
                handoff_to=role.handoff_to,
                fallback_role_id=self._fallback_role_id(),
            )
        fallback = self._fallback_role()
        weak_matches = _weak_route_matches(self._roles, normalized)
        reason = "low confidence; matched weak signals only" if weak_matches else "no strong signal matched; defaulting to CEO"
        return AgentRoute(
            role_id=fallback.role_id,
            role_name=fallback.name,
            confidence=0.35,
            matched_signals=weak_matches,
            reason=reason,
            handoff_to=fallback.handoff_to,
            fallback_role_id=fallback.role_id,
        )

    def structure_context(self) -> str:
        if not self._roles:
            return "No Agent Company registry configured."
        primary_roles = tuple(role for role in self._roles if not role.metadata.get("not_primary_workflow_node"))
        auxiliary_roles = tuple(role for role in self._roles if role.metadata.get("not_primary_workflow_node"))
        lines = [
            "Agent Company",
            "- Principle: 能删就删，能复用就复用。",
            "- Contract: Prompt -> Memory -> Tool -> Workflow -> MCP.",
            f"- Chain: {' -> '.join(role.title for role in primary_roles)}",
        ]
        if auxiliary_roles:
            lines.append(f"- Auxiliary gates: {', '.join(role.title for role in auxiliary_roles)}")
        lines.extend(["", "Role Registry:"])
        for index, role in enumerate(self._roles):
            if role.handoff_to:
                next_role = self._role_name(role.handoff_to[0])
            elif role.metadata.get("not_primary_workflow_node"):
                next_role = ""
            else:
                next_primary = _next_primary_role(self._roles, index)
                next_role = self._role_name(next_primary.role_id) if next_primary is not None else ""
            lines.append(role.describe(next_role=next_role))
        return "\n".join(lines)

    def route_context(self, text: str, tool_registry: Any | None = None) -> str:
        if not self._roles:
            return "No Agent Company registry configured."
        route = self.route_for_request(text)
        role = self._by_role_id.get(route.role_id) or self._fallback_role()
        coverage = self._role_tool_coverage(role.role_id, tool_registry)
        lines = [
            "Current request routing:",
            f"- request: {text.strip() or '<empty>'}",
            f"- suggested_role: {role.title} ({role.name})",
            f"- department: {role.department}",
            f"- confidence: {route.confidence:.2f}",
            f"- reason: {route.reason}",
        ]
        if route.matched_signals:
            lines.append(f"- matched_signals: {', '.join(route.matched_signals)}")
        if route.handoff_to:
            lines.append(f"- handoff_chain: {role.title} -> {' -> '.join(self._role_name(role_id) for role_id in route.handoff_to)}")
        if coverage["available_tools"] or coverage["missing_tools"]:
            lines.append("- tool_coverage:")
            if coverage["available_tools"]:
                lines.append(f"  - available: {', '.join(coverage['available_tools'])}")
            if coverage["missing_tools"]:
                lines.append(f"  - missing: {', '.join(coverage['missing_tools'])}")
        return "\n".join(lines)

    def tool_coverage(self, tool_registry: Any | None) -> list[dict[str, Any]]:
        return [self._role_tool_coverage(role.role_id, tool_registry) for role in self._roles]

    def _role_tool_coverage(self, role_id: str, tool_registry: Any | None) -> dict[str, Any]:
        role = self.get(role_id)
        available_tool_names = _available_tool_names(tool_registry)
        available = [name for name in role.tool_names if name in available_tool_names]
        missing = [name for name in role.tool_names if name not in available_tool_names]
        return {
            "role_id": role.role_id,
            "name": role.name,
            "department": role.department,
            "available_tools": available,
            "missing_tools": missing,
        }

    def _fallback_role(self) -> AgentRoleSpec:
        return self._by_role_id.get("ceo") or (self._roles[0] if self._roles else AgentRoleSpec("", "", "", "", ""))

    def _fallback_role_id(self) -> str:
        return self._fallback_role().role_id

    def _role_name(self, role_id: str) -> str:
        role = self._by_role_id.get(role_id)
        return role.title if role is not None else role_id


def build_default_agent_company() -> AgentCompanyRegistry:
    return AgentCompanyRegistry(DEFAULT_AGENT_ROLES)


DEFAULT_AGENT_ROLES: tuple[AgentRoleSpec, ...] = (
    AgentRoleSpec(
        role_id="ceo",
        title="CEO",
        name="CEO Agent",
        department="Executive",
        mission="统筹全局目标、验收标准与跨角色冲突裁决",
        responsibilities=("定义项目成功标准", "确认角色边界", "裁决优先级冲突", "把控最终交付质量"),
        input_keys=("project_goal", "business_constraints", "current_state"),
        output_keys=("company_policy", "acceptance_criteria", "priority_order"),
        tool_names=("memory_read", "search_text", "todo_read"),
        prompt_focus=("目标", "验收", "边界", "优先级"),
        handoff_to=("planner",),
        legacy_modules=(),
        routing_signals=("目标", "验收", "策略", "统筹", "公司", "okr", "决策"),
    ),
    AgentRoleSpec(
        role_id="planner",
        title="Planner",
        name="Planner Agent",
        department="Strategy",
        mission="拆解任务、安排角色与产出顺序",
        responsibilities=("将目标拆成阶段", "定义角色协作顺序", "识别依赖关系", "形成执行路线图"),
        input_keys=("project_brief", "company_policy", "constraints"),
        output_keys=("execution_plan", "handoff_map", "phase_order"),
        tool_names=("search_text", "glob_files", "list_files", "memory_read"),
        prompt_focus=("规划", "拆解", "排期", "阶段"),
        handoff_to=("product",),
        legacy_modules=(),
        routing_signals=("规划", "拆解", "计划", "路线图", "排期", "优先级", "workflow"),
    ),
    AgentRoleSpec(
        role_id="product",
        title="Product",
        name="Product Analyst Agent",
        department="Product",
        mission="解析商品卖点、价格、FAQ、场景与合规表达",
        responsibilities=("梳理商品信息", "总结卖点与场景", "抽取FAQ", "标记价格与合规要点"),
        input_keys=("product_data", "faq", "pricing", "scenario_notes"),
        output_keys=("product_insights", "value_propositions", "faq_summary"),
        tool_names=("read_json", "search_text", "memory_read"),
        prompt_focus=("商品", "卖点", "FAQ", "价格", "场景"),
        handoff_to=("brand",),
        legacy_modules=(),
        routing_signals=("商品", "卖点", "sku", "faq", "价格", "规格", "场景"),
        routing_weights={"商品": 1.4, "卖点": 1.3, "sku": 1.5, "faq": 1.5, "价格": 1.2, "规格": 1.2, "场景": 0.35},
    ),
    AgentRoleSpec(
        role_id="brand",
        title="Brand",
        name="Brand Analyst Agent",
        department="Brand",
        mission="提炼品牌定位、信任背书和内容语气",
        responsibilities=("识别品牌资产", "提炼品牌故事", "定义内容调性", "输出信任背书"),
        input_keys=("product_insights", "brand_assets", "audience", "tone_constraints"),
        output_keys=("brand_strategy", "brand_story", "tone_of_voice"),
        tool_names=("read_file", "search_text", "memory_read"),
        prompt_focus=("品牌", "定位", "背书", "调性"),
        handoff_to=("story",),
        legacy_modules=(),
        routing_signals=("品牌", "定位", "背书", "调性", "品牌故事", "信任"),
        routing_weights={"品牌": 1.2, "定位": 1.1, "背书": 1.4, "调性": 1.4, "品牌故事": 1.6, "信任": 1.1},
    ),
    AgentRoleSpec(
        role_id="story",
        title="Story",
        name="Story Agent",
        department="Creative",
        mission="把品牌与商品信息转成可讲述的故事线",
        responsibilities=("组织故事主线", "构建情绪钩子", "生成角色关系", "维持叙事连贯性"),
        input_keys=("brand_strategy", "product_insights", "audience"),
        output_keys=("story_outline", "characters", "emotional_hooks"),
        tool_names=("read_file", "memory_read", "search_text"),
        prompt_focus=("故事", "叙事", "人设", "情绪"),
        handoff_to=("script",),
        legacy_modules=("agents.screenwriter", "agents.global_information_planner", "agents.novel_compressor"),
        routing_signals=("故事", "叙事", "世界观", "人设", "story"),
        routing_weights={"故事": 0.8, "叙事": 1.3, "世界观": 1.3, "人设": 1.2, "story": 1.0},
    ),
    AgentRoleSpec(
        role_id="script",
        title="Script",
        name="Script Agent",
        department="Creative",
        mission="生成直播口播、节奏和 CTA 脚本",
        responsibilities=("编写直播口播", "设计 CTA 节点", "控制节奏", "兼顾合规表达"),
        input_keys=("story_outline", "cta_requirements", "compliance_notes"),
        output_keys=("sales_script", "call_to_action", "compliance_notes"),
        tool_names=("read_file", "write_json", "memory_read"),
        prompt_focus=("剧本", "话术", "口播", "CTA"),
        handoff_to=("storyboard",),
        legacy_modules=("agents.script_planner", "agents.script_enhancer", "agents.screenwriter"),
        routing_signals=("剧本", "话术", "口播", "脚本", "文案", "cta"),
    ),
    AgentRoleSpec(
        role_id="storyboard",
        title="Storyboard",
        name="Storyboard Agent",
        department="Creative",
        mission="把剧本拆成镜头和分镜",
        responsibilities=("拆解镜头", "控制景别与视角", "维持镜头连续性", "输出 shot plan"),
        input_keys=("script", "characters", "visual_constraints"),
        output_keys=("storyboard", "shot_plan", "camera_notes"),
        tool_names=("read_json", "write_json", "glob_files"),
        prompt_focus=("分镜", "镜头", "画面", "shot"),
        handoff_to=("director",),
        legacy_modules=("agents.storyboard_artist",),
        routing_signals=("分镜", "镜头", "shot", "画面", "storyboard"),
    ),
    AgentRoleSpec(
        role_id="director",
        title="Director",
        name="Director Agent",
        department="Creative",
        mission="协调镜头、节奏、表演和生产顺序",
        responsibilities=("协调镜头语言", "把控表演节奏", "整理拍摄顺序", "维护导演意图"),
        input_keys=("storyboard", "shot_plan", "production_schedule"),
        output_keys=("director_script", "shooting_notes", "director_cues", "sequence_adjustments"),
        tool_names=("search_text", "memory_read"),
        prompt_focus=("导演", "调度", "节奏", "拍摄", "Director Script"),
        handoff_to=("visual_director",),
        legacy_modules=("agents.scene_extractor", "agents.event_extractor"),
        routing_signals=("导演", "调度", "节奏", "拍摄", "导演组", "镜头调度", "director script", "导演执行稿", "拍摄顺序"),
        routing_weights={"导演": 0.45, "调度": 1.0, "节奏": 0.8, "拍摄": 0.9, "导演组": 1.4, "镜头调度": 1.8, "director script": 1.8, "导演执行稿": 1.8, "拍摄顺序": 1.5},
    ),
    AgentRoleSpec(
        role_id="visual_director",
        title="Visual Director",
        name="Visual Director Agent",
        department="Creative",
        mission="把 Story、Script 和 Director Script 转换成统一、可执行的视觉生产蓝图",
        responsibilities=(
            "定义品牌视觉语言、主辅色、材质、字体、字幕和 UI 风格",
            "设计场景、摄影、灯光、构图、数字人、商品、字幕、贴图和转场方案",
            "为 Image/Video/Avatar Agent 输出跨模型稳定的 image_prompt 与 video_prompt",
            "优先映射 Asset Library 中的可复用素材，并输出 OBS 图层方案",
            "执行视觉自审，确保 Brand Consistency、Luxury、Lighting、Composition、Commercial Quality、Prompt Quality、Runtime Readiness 均达到 90 分以上",
        ),
        input_keys=(
            "story",
            "script",
            "director_script",
            "brand",
            "product",
            "audience",
            "emotion",
            "live_goal",
            "platform",
            "scene",
            "current_assets",
            "runtime_context",
        ),
        output_keys=(
            "visual_blueprint",
            "brand_visual_blueprint",
            "scene_blueprint",
            "camera_blueprint",
            "lighting_blueprint",
            "composition_blueprint",
            "image_prompt",
            "video_prompt",
            "asset_mapping",
            "obs_layers",
        ),
        tool_names=("read_file", "read_json", "search_text", "glob_files", "memory_read"),
        prompt_focus=("视觉导演", "Visual Blueprint", "摄影", "灯光", "构图", "Image Prompt", "Video Prompt", "OBS 图层"),
        handoff_to=("voice",),
        legacy_modules=("agents.camera_image_generator", "agents.reference_image_selector", "agents.best_image_selector"),
        routing_signals=(
            "visual director",
            "visual blueprint",
            "视觉导演",
            "视觉蓝图",
            "视觉",
            "品牌视觉",
            "image prompt",
            "video prompt",
            "摄影",
            "灯光",
            "构图",
            "asset mapping",
            "obs layer",
            "obs 图层",
            "veo",
            "flux",
            "可灵",
            "即梦",
        ),
        routing_weights={
            "visual director": 2.4,
            "visual blueprint": 2.4,
            "视觉导演": 2.4,
            "视觉蓝图": 2.4,
            "视觉": 0.2,
            "品牌视觉": 1.8,
            "image prompt": 2.0,
            "video prompt": 2.0,
            "摄影": 0.8,
            "灯光": 0.8,
            "构图": 0.8,
            "asset mapping": 2.0,
            "obs layer": 2.0,
            "obs 图层": 2.0,
            "veo": 0.6,
            "flux": 0.6,
            "可灵": 0.6,
            "即梦": 0.6,
        },
        required_routing_signals=("visual director", "visual blueprint", "视觉导演", "视觉蓝图", "品牌视觉", "image prompt", "video prompt", "asset mapping", "obs layer", "obs 图层"),
        metadata={
            "output_contract": "Return only YAML/JSON under visual_blueprint and pass runtime schema validation: required fields include image_prompt, video_prompt, asset_mapping, obs_layers, and director_note; no explanations or analysis.",
            "system_prompt_version": "visual-director-v1.0",
            "system_prompt": """
# Visual Director Agent System Prompt v1.0

## Role
你是 Visual Director Agent（视觉导演 Agent）。你不是 UI 设计师、平面设计师、美术或 Prompt Engineer。你的身份是电影导演 + 摄影指导（Director of Photography）+ 品牌视觉总监 + 直播视觉导演 + AI 视频生产架构师。

## Mission
把 Story、Script 和 Director Script 转换成统一、高质量、可执行的 Visual Blueprint，保证品牌所有直播视频拥有统一、专业、高级、电影级的视觉语言。

## Required Output
Only output final YAML:
visual_blueprint:
  brand:
  scene:
  camera:
  lighting:
  composition:
  avatar:
  product:
  subtitle:
  overlay:
  music:
  transition:
  image_prompt:
  video_prompt:
  asset_mapping:
  obs_layers:
  director_note:

## Principles
Premium, Luxury, Minimal, Elegant, Realistic, Commercial, Cinematic, Natural, Chinese Luxury, High-end Live Commerce. No cheap livestream style, noisy effects, rainbow colors, heavy outlines, exaggerated motion, or Taobao-burst visual language.

## Brand Rules
For 张裕: warm wood, deep wine red, champagne gold, winery, wood, leather, copper, glass, European cellar, warm light. Brand mood: Heritage, Premium, Luxury, Winery, Timeless.

## Camera Rules
Story pacing is slow and stable: Slow Push, Slow Dolly, Static. No frequent cuts, fast pans, or exaggerated motion.

## Lighting Rules
Story: 3200K warm light. Business: 4200K high-end hotel. Winery: warm yellow, wood grain. Highlight bottle and digital human.

## Composition Rules
Default Rule of Thirds: avatar left, product right, logo top-left, price bottom-right. Keep visual balance and negative space.

## Subtitle Rules
Modern sans-serif, white text, champagne-gold keywords. No rainbow colors, heavy outlines, or exaggerated animation.

## Prompt Rules
Image Prompt must include photography, lighting, lens/camera, depth of field, material, brand, and style. Video Prompt must include camera movement, lighting, scene, mood, style, duration, and motion.

## Asset Rules
Prefer Asset Library before generation. Output explicit Asset Mapping for background, product, logo, subtitle, overlay, music, and transition.

## OBS Rules
Output OBS Layer Mapping: Layer01 Background, Layer02 Avatar, Layer03 Product, Layer04 Subtitle, Layer05 Overlay, Layer06 Logo, Layer07 Comment.

## Self Review
Before output, internally score Brand Consistency, Luxury, Lighting, Composition, Commercial Quality, Prompt Quality, Runtime Readiness from 0 to 100. If any score is below 90, redesign before output.
""".strip(),
        },
    ),
    AgentRoleSpec(
        role_id="voice",
        title="Voice",
        name="Voice Agent",
        department="Production",
        mission="控制口播语气、TTS 方案和播报时长",
        responsibilities=("选择播报语气", "约束口播时长", "适配 TTS 配置", "输出语音驱动脚本"),
        input_keys=("script", "voice_profile", "duration_target"),
        output_keys=("tts_plan", "audio_script", "voice_constraints"),
        tool_names=("memory_read", "read_json"),
        prompt_focus=("语音", "TTS", "播报", "音色"),
        handoff_to=("avatar",),
        legacy_modules=("agent_runtime.speech_tts",),
        routing_signals=("语音", "tts", "播报", "音色", "声音"),
    ),
    AgentRoleSpec(
        role_id="avatar",
        title="Avatar",
        name="Avatar Agent",
        department="Production",
        mission="驱动数字人配置、脚本准备与出镜形象",
        responsibilities=("检查数字人配置", "准备 HeyGen 脚本", "生成数字人口播片段", "维护出镜形象"),
        input_keys=("script", "avatar_profile", "background_asset_path"),
        output_keys=("avatar_job", "clip", "generation_status"),
        tool_names=("heygen_live_room_check_config", "heygen_live_room_prepare_script", "heygen_live_room_generate_clip"),
        prompt_focus=("数字人", "avatar", "主播形象", "出镜"),
        handoff_to=("scene",),
        legacy_modules=("agent_runtime.heygen_skills", "agent_runtime.production_adapters"),
        routing_signals=("数字人", "avatar", "形象", "主播", "heygen"),
    ),
    AgentRoleSpec(
        role_id="scene",
        title="Scene",
        name="Scene Agent",
        department="Studio",
        mission="组合直播间组件、画面层和场景模板",
        responsibilities=("编排场景层级", "组织组件组合", "输出直播间结构", "整理画面布局"),
        input_keys=("asset_list", "layout_rules", "scene_template"),
        output_keys=("scene_layout", "composition", "layer_order"),
        tool_names=("list_files", "write_json", "search_text"),
        prompt_focus=("直播间", "场景", "组件", "布局"),
        handoff_to=("composer",),
        legacy_modules=("agents.camera_image_generator", "agents.reference_image_selector"),
        routing_signals=("直播间", "场景", "舞台", "组件", "layout", "布景", "场景模板", "组件布局"),
        routing_weights={"直播间": 1.4, "场景": 0.35, "舞台": 1.0, "组件": 1.2, "layout": 1.2, "布景": 1.3, "场景模板": 1.6, "组件布局": 1.8},
    ),
    AgentRoleSpec(
        role_id="composer",
        title="Composer",
        name="Video Composer Agent",
        department="Production",
        mission="合成口播、镜头与视频成片",
        responsibilities=("调用 ffmpeg 合成", "管理最终成片", "记录合成清单", "维护导出规范"),
        input_keys=("clips", "shot_plan", "render_constraints"),
        output_keys=("final_video", "manifest", "composition_status"),
        tool_names=("ffmpeg_video_composition", "production_run_status"),
        prompt_focus=("合成", "剪辑", "视频", "成片"),
        handoff_to=("streaming",),
        legacy_modules=("agent_runtime.production_adapters", "utils.ffmpeg_cli"),
        routing_signals=("合成", "剪辑", "视频", "ffmpeg", "成片", "render"),
        routing_weights={"合成": 1.4, "剪辑": 1.2, "视频": 0.4, "ffmpeg": 1.8, "成片": 1.5, "render": 1.4},
    ),
    AgentRoleSpec(
        role_id="streaming",
        title="Streaming",
        name="Streaming Agent",
        department="Broadcast",
        mission="管理推流、开播和发布状态",
        responsibilities=("检查开播条件", "维护推流状态", "追踪发布进度", "处理播出反馈"),
        input_keys=("final_video", "platform", "stream_target"),
        output_keys=("publish_status", "stream_plan", "live_state"),
        tool_names=("production_run_status", "production_performance_ingest"),
        prompt_focus=("推流", "开播", "直播", "发布"),
        handoff_to=("analytics",),
        legacy_modules=("agent_runtime.live_room_runtime", "agent_runtime.production_adapters"),
        routing_signals=("推流", "开播", "直播", "stream", "broadcast", "发布"),
    ),
    AgentRoleSpec(
        role_id="compliance",
        title="Compliance",
        name="Compliance Agent",
        department="Governance",
        mission="作为酒类直播合规 gate 审查文案、视觉和发布方案",
        responsibilities=(
            "检查酒类合规、理性饮酒和成年人购买提示",
            "拦截未成年人、酒驾、过量饮酒和危险饮酒场景",
            "识别健康、养生、保健、治疗或医疗功效暗示",
            "检查价格、库存、奖项、年份等绝对化或不可证实表达",
            "审查视觉素材中的未成年人饮酒、驾驶饮酒和不合规饮酒场景",
        ),
        input_keys=("product_profile", "brand_brief", "script", "director_script", "visual_blueprint", "asset_mapping", "obs_layers", "platform_policy"),
        output_keys=("compliance_report", "risk_flags", "safe_rewrites", "gate_decision"),
        tool_names=("search_text", "memory_read"),
        prompt_focus=("合规", "酒类", "未成年人", "理性饮酒", "治疗暗示", "价格库存奖项年份", "视觉风险"),
        handoff_to=(),
        legacy_modules=("agent_runtime.live_compliance", "apps.api.app.domain.compliance.policies", "apps.api.app.application.compliance_service"),
        routing_signals=("合规", "酒类合规", "未成年", "小孩", "学生", "养生", "保健", "治疗", "医疗", "功效", "开车", "酒驾", "过量饮酒", "多喝", "最低价", "全网最低", "库存", "年份", "奖项", "饮酒场景"),
        routing_weights={"合规": 1.8, "酒类合规": 2.2, "未成年": 2.0, "小孩": 1.6, "学生": 1.3, "养生": 1.8, "保健": 1.8, "治疗": 1.8, "医疗": 1.8, "功效": 1.4, "开车": 1.8, "酒驾": 2.0, "过量饮酒": 1.8, "多喝": 1.4, "最低价": 1.6, "全网最低": 1.8, "库存": 1.0, "年份": 1.0, "奖项": 1.0, "饮酒场景": 1.5},
        metadata={
            "not_primary_workflow_node": True,
            "gate_after": ["script", "visual_director"],
            "gate_before": ["streaming"],
            "policy_scope": ["alcohol", "minor_safety", "health_claims", "price_inventory_awards_vintage", "visual_drinking_scene"],
        },
    ),
    AgentRoleSpec(
        role_id="analytics",
        title="Analytics",
        name="Analytics Agent",
        department="Data",
        mission="观察 GMV、CTR、CVR 并提炼复盘",
        responsibilities=("读取结果指标", "总结高绩效模式", "提炼复盘结论", "识别数据异常"),
        input_keys=("metrics", "events", "performance_summary"),
        output_keys=("analysis", "best_practices", "performance_notes"),
        tool_names=("production_run_status", "production_reusable_patterns_search", "search_text"),
        prompt_focus=("数据", "GMV", "CTR", "CVR", "复盘"),
        handoff_to=("optimization",),
        legacy_modules=("agent_runtime.production_store", "apps.api.app.application.workbench_service"),
        routing_signals=("数据", "gmv", "ctr", "cvr", "复盘", "分析", "统计"),
    ),
    AgentRoleSpec(
        role_id="optimization",
        title="Optimization",
        name="Optimization Agent",
        department="Optimization",
        mission="把分析结果转为下一轮迭代动作",
        responsibilities=("输出优化建议", "整理下一轮实验", "把经验沉淀成复用规则", "推动闭环迭代"),
        input_keys=("analysis", "best_practices", "experiment_results"),
        output_keys=("optimized_plan", "tuning_actions", "iteration_backlog"),
        tool_names=("memory_read", "search_text", "todo_read"),
        prompt_focus=("优化", "迭代", "提升", "调优"),
        handoff_to=(),
        legacy_modules=("agent_runtime.context_compactor",),
        routing_signals=("优化", "迭代", "提升", "best practice", "改进", "a/b", "调优"),
    ),
)


def _next_primary_role(roles: Sequence[AgentRoleSpec], index: int) -> AgentRoleSpec | None:
    for role in roles[index + 1:]:
        if not role.metadata.get("not_primary_workflow_node"):
            return role
    return None


def _score_role_route(role: AgentRoleSpec, normalized: str) -> tuple[float, tuple[str, ...], tuple[str, ...]]:
    matches = tuple(signal for signal in role.routing_signals if signal and signal.lower() in normalized)
    if not matches:
        return 0.0, (), ()
    required_matches = tuple(signal for signal in role.required_routing_signals if signal and signal.lower() in normalized)
    if role.required_routing_signals and not required_matches:
        return 0.0, matches, ()
    score = 0.0
    for signal in matches:
        score += role.routing_weights.get(signal, _default_signal_weight(signal))
    for signal in role.negative_routing_signals:
        if signal and signal.lower() in normalized:
            score -= role.routing_weights.get(signal, 1.0)
    return max(0.0, score), matches, required_matches


def _default_signal_weight(signal: str) -> float:
    normalized = signal.lower().strip()
    if len(normalized) <= 2 or normalized in {"视觉", "场景", "导演", "视频", "故事", "直播", "分析"}:
        return 0.4
    if " " in normalized or len(normalized) >= 5:
        return 1.4
    return 1.0


def _weak_route_matches(roles: Sequence[AgentRoleSpec], normalized: str) -> tuple[str, ...]:
    weak: list[str] = []
    for role in roles:
        for signal in role.routing_signals:
            if signal and signal.lower() in normalized and role.routing_weights.get(signal, _default_signal_weight(signal)) < role.routing_threshold:
                weak.append(signal)
    return tuple(dict.fromkeys(weak))


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _available_tool_names(tool_registry: Any | None) -> set[str]:
    if tool_registry is None or not hasattr(tool_registry, "list_tools"):
        return set()
    try:
        tools = tool_registry.list_tools()
    except Exception:
        return set()
    names: set[str] = set()
    for item in tools:
        if isinstance(item, dict) and item.get("name"):
            names.add(str(item["name"]))
    return names
