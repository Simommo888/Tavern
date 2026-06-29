import json
import tempfile
import unittest
from pathlib import Path

from apps.api.app.application.workbench_service import WorkbenchService


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "workflows" / "n8n" / "tavern-product-to-streaming.workflow.json"
EXPECTED_STAGES = ["商品", "品牌", "故事", "剧本", "分镜", "导演", "视觉导演", "语音", "数字人", "直播间", "视频", "推流"]
EXPECTED_API_PATHS = [
    "/api/v1/workflow/definitions",
    "/api/v1/mvp/live-plans/run",
    "/api/v1/workflow/runs",
]


class N8nWorkflowAssetTests(unittest.TestCase):
    def test_n8n_workflow_asset_matches_tavern_workflow_contract(self):
        self.assertTrue(WORKFLOW_PATH.exists())
        workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))

        self.assertIn("Tavern", workflow["name"])
        self.assertIn("Product-to-Streaming", workflow["name"])

        node_names = [node["name"] for node in workflow["nodes"]]
        self.assertEqual([name.split(" ", 1)[1] for name in node_names if name[:2].isdigit()], EXPECTED_STAGES)

        with tempfile.TemporaryDirectory() as tmp:
            service = WorkbenchService(Path(tmp))
            definitions = service.workflow_definitions.list()
            product_to_streaming = next(item for item in definitions if item.version == "phase5-v1")
        self.assertEqual([node["label"] for node in product_to_streaming.nodes], EXPECTED_STAGES)

        serialized = json.dumps(workflow, ensure_ascii=False)
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
