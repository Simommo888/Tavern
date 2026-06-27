import tempfile
import unittest
from pathlib import Path

from agent_runtime.agent_company import build_default_agent_company
from agent_runtime.prompts import PromptBuilder
from agent_runtime.session_index import SessionIndex
from agent_runtime.tools import ToolRegistry, ToolSpec, build_builtin_registry
from apps.api.app.application.workbench_service import WorkbenchService


class AgentCompanyTests(unittest.TestCase):
    def test_default_company_has_phase_four_roles_in_order(self):
        company = build_default_agent_company()
        self.assertEqual(company.role_ids(), [
            "ceo",
            "planner",
            "product",
            "brand",
            "story",
            "script",
            "storyboard",
            "director",
            "visual_director",
            "voice",
            "avatar",
            "scene",
            "composer",
            "streaming",
            "compliance",
            "analytics",
            "optimization",
        ])
        for role in company.list_roles():
            self.assertTrue(role.mission)
            self.assertTrue(role.department)
            self.assertTrue(role.responsibilities)
            self.assertTrue(role.input_keys)
            self.assertTrue(role.output_keys)
            self.assertIn("prompt", role.mcp_capabilities)
            self.assertIn("memory", role.mcp_capabilities)
            self.assertIn("tool", role.mcp_capabilities)
            self.assertIn("workflow", role.mcp_capabilities)
            self.assertIn("mcp", role.mcp_capabilities)

    def test_company_routes_common_liveos_requests(self):
        company = build_default_agent_company()
        cases = {
            "帮我分析品牌背书和内容调性": "brand",
            "解析这个商品 SKU 的卖点和 FAQ": "product",
            "生成直播口播脚本和 CTA": "script",
            "把剧本拆成分镜镜头": "storyboard",
            "输出导演执行稿和镜头调度": "director",
            "把分镜转换成 Visual Blueprint 和 OBS 图层": "visual_director",
            "单独看一下视觉感觉": "ceo",
            "设计直播间场景组件布局": "scene",
            "把视频用 FFmpeg 合成成片": "composer",
            "检查酒类合规和未成年人风险": "compliance",
            "检查数字人主播 avatar 配置": "avatar",
            "复盘 GMV CTR CVR 数据": "analytics",
        }
        for text, role_id in cases.items():
            with self.subTest(text=text):
                self.assertEqual(company.route_for_request(text).role_id, role_id)

    def test_tool_coverage_marks_available_and_missing_tools(self):
        company = build_default_agent_company()
        registry = ToolRegistry([
            ToolSpec("heygen_live_room_check_config", "check", lambda args: None, schema={}),
            ToolSpec("production_run_status", "status", lambda args: None, schema={}),
        ])
        coverage = {item["role_id"]: item for item in company.tool_coverage(registry)}
        self.assertIn("heygen_live_room_check_config", coverage["avatar"]["available_tools"])
        self.assertIn("heygen_live_room_prepare_script", coverage["avatar"]["missing_tools"])
        self.assertIn("production_run_status", coverage["analytics"]["available_tools"])

    def test_prompt_builder_injects_agent_company_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "prompts").mkdir()
            (root / "prompts" / "agent.md").write_text("agent rules", encoding="utf-8")
            (root / "prompts" / "workflow.md").write_text("workflow rules", encoding="utf-8")
            index = SessionIndex(root)
            index.create(idea="wine live room")
            registry = build_builtin_registry(root, index)
            builder = PromptBuilder(root / "prompts", index, registry)
            parts = builder.build_parts("请分析品牌背书")
            self.assertIn("agent.company", [part.id for part in parts])
            message = builder.build_messages("请分析品牌背书")[0]["content"]
            self.assertIn("Agent Company registry is active", message)
            self.assertIn("CEO -> Planner -> Product -> Brand -> Story", message)
            self.assertIn("Auxiliary gates: Compliance", message)
            self.assertIn("suggested_role: Brand", message)

    def test_workbench_seeds_agent_profiles_from_company_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = WorkbenchService(Path(tmp))
            agents = service.agent_profiles.list()
            self.assertEqual(len(agents), 17)
            role_ids = [str(agent.metadata.get("role_id")) for agent in agents]
            self.assertEqual(role_ids, build_default_agent_company().role_ids())
            visual_director = next(agent for agent in agents if agent.metadata.get("role_id") == "visual_director")
            self.assertIn("visual_blueprint", visual_director.metadata.get("output_keys", []))
            self.assertEqual(visual_director.metadata.get("system_prompt_version"), "visual-director-v1.0")
            self.assertIn("system_prompt", visual_director.metadata)
            compliance = next(agent for agent in agents if agent.metadata.get("role_id") == "compliance")
            self.assertTrue(compliance.metadata.get("not_primary_workflow_node"))
            self.assertIn("script", compliance.metadata.get("gate_after", []))
            self.assertIn("streaming", compliance.metadata.get("gate_before", []))
            avatar = next(agent for agent in agents if agent.metadata.get("role_id") == "avatar")
            self.assertIn("heygen_live_room_check_config", avatar.tool_names)
            self.assertIn("mcp_capabilities", avatar.metadata)


if __name__ == "__main__":
    unittest.main()
