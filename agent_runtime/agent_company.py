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
        scored: list[tuple[int, int, AgentRoleSpec, tuple[str, ...]]] = []
        for index, role in enumerate(self._roles):
            matches = tuple(signal for signal in role.routing_signals if signal and signal.lower() in normalized)
            if matches:
                scored.append((len(matches), -index, role, matches))
        if scored:
            _, _, role, matches = max(scored, key=lambda item: (item[0], item[1]))
            confidence = min(0.98, 0.55 + 0.12 * len(matches))
            return AgentRoute(
                role_id=role.role_id,
                role_name=role.name,
                confidence=confidence,
                matched_signals=matches,
                reason=f"matched signals: {', '.join(matches)}",
                handoff_to=role.handoff_to,
                fallback_role_id=self._fallback_role_id(),
            )
        fallback = self._fallback_role()
        return AgentRoute(
            role_id=fallback.role_id,
            role_name=fallback.name,
            confidence=0.35,
            matched_signals=(),
            reason="no strong signal matched; defaulting to CEO",
            handoff_to=fallback.handoff_to,
            fallback_role_id=fallback.role_id,
        )

    def structure_context(self) -> str:
        if not self._roles:
            return "No Agent Company registry configured."
        lines = [
            "Agent Company",
            "- Principle: 能删就删，能复用就复用。",
            "- Contract: Prompt -> Memory -> Tool -> Workflow -> MCP.",
            f"- Chain: {' -> '.join(role.title for role in self._roles)}",
            "",
            "Role Registry:",
        ]
        for index, role in enumerate(self._roles):
            next_role = self._role_name(role.handoff_to[0]) if role.handoff_to else (self._role_name(self._roles[index + 1].role_id) if index + 1 < len(self._roles) else "")
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
        handoff_to=("brand",),
        legacy_modules=(),
        routing_signals=("规划", "拆解", "计划", "路线图", "排期", "优先级", "workflow"),
    ),
    AgentRoleSpec(
        role_id="brand",
        title="Brand",
        name="Brand Analyst Agent",
        department="Brand",
        mission="提炼品牌定位、信任背书和内容语气",
        responsibilities=("识别品牌资产", "提炼品牌故事", "定义内容调性", "输出信任背书"),
        input_keys=("brand_assets", "audience", "tone_constraints"),
        output_keys=("brand_strategy", "brand_story", "tone_of_voice"),
        tool_names=("read_file", "search_text", "memory_read"),
        prompt_focus=("品牌", "定位", "背书", "调性"),
        handoff_to=("product",),
        legacy_modules=(),
        routing_signals=("品牌", "定位", "背书", "调性", "故事", "信任"),
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
        handoff_to=("story",),
        legacy_modules=(),
        routing_signals=("商品", "卖点", "sku", "faq", "价格", "规格", "场景"),
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
        output_keys=("shooting_notes", "director_cues", "sequence_adjustments"),
        tool_names=("search_text", "memory_read"),
        prompt_focus=("导演", "调度", "节奏", "拍摄"),
        handoff_to=("voice",),
        legacy_modules=("agents.scene_extractor", "agents.event_extractor"),
        routing_signals=("导演", "调度", "节奏", "拍摄", "导演组", "镜头调度"),
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
        routing_signals=("直播间", "场景", "舞台", "组件", "layout", "布景"),
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
