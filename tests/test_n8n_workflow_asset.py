import json
import tempfile
import unittest
from pathlib import Path

from apps.api.app.application.workbench_service import WorkbenchService


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "workflows" / "n8n" / "tavern-product-to-streaming.workflow.json"
EXPECTED_STAGES = [
    "商品/品牌资料",
    "Planner Agent（任务规划）",
    "Story Agent（故事生成）",
    "Script Agent（直播话术）",
    "Director Agent（镜头拆解）",
    "Visual Director Agent（画面设计 + Prompt）",
    "Asset Agent（素材匹配/生成）",
    "Image Agent（背景/贴图生成）",
    "Video Agent（镜头视频生成）",
    "Editor Agent（剪辑/BGM/合成）",
]
EXPECTED_API_PATHS = [
    "/api/v1/workflow/definitions",
    "/api/v1/workflow/product-videos/runs",
    "/api/v1/workflow/product-videos/runs/{{$json.workflow.run.workflow_run_id}}/nodes/planner/run",
    "/api/v1/workflow/runs",
]


class N8nWorkflowAssetTests(unittest.TestCase):
    def test_n8n_workflow_asset_matches_tavern_workflow_contract(self):
        self.assertTrue(WORKFLOW_PATH.exists())
        workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))

        self.assertIn("Tavern", workflow["name"])
        self.assertIn("Complete-Video", workflow["name"])

        node_names = [node["name"] for node in workflow["nodes"]]
        self.assertEqual([name.split(" ", 1)[1] for name in node_names if name[:2].isdigit()], EXPECTED_STAGES)

        with tempfile.TemporaryDirectory() as tmp:
            service = WorkbenchService(Path(tmp))
            definitions = service.workflow_definitions.list()
            product_video = next(item for item in definitions if item.version == "product-video-v1")
        self.assertEqual([node["label"] for node in product_video.nodes], EXPECTED_STAGES)
        self.assertEqual(product_video.nodes[-1]["artifact"], "complete_video")

        serialized = json.dumps(workflow, ensure_ascii=False)
        self.assertNotIn("/api/v1/workflow/product-videos/run\"", serialized)
        self.assertIn("one_http_node_per_agent", serialized)
        for api_path in EXPECTED_API_PATHS:
            self.assertIn(api_path, serialized)

        forbidden_fragments = [
            "credentialId",
            "access_token",
            "api_key",
            "secret_key",
            "bearer ",
        ]
        lowered = serialized.lower()
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, lowered)


if __name__ == "__main__":
    unittest.main()
