import json
import tempfile
import unittest
from pathlib import Path

from agent_runtime.production_adapters import AlcoholProductionAdapters
from agent_runtime.session_index import SessionIndex
from agent_runtime.tools import ToolRuntimeContext


class ProductionAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_dry_run_full_pipeline_creates_traceable_final_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = SessionIndex(tmp)
            adapter = AlcoholProductionAdapters(Path(tmp), index)
            story = await adapter.alcohol_story_generation({"idea": "做一条酱香酒直播间销售视频", "product_name": "样品酱香酒", "sales_goal": "提升成交"})
            self.assertTrue(story.ok)
            story_payload = json.loads(story.content)

            script = await adapter.alcohol_script_generation({"session_id": story_payload["session_id"]})
            self.assertTrue(script.ok)
            storyboard = await adapter.alcohol_storyboard_generation({"session_id": story_payload["session_id"]})
            self.assertTrue(storyboard.ok)
            heygen = await adapter.heygen_live_room_generation({"session_id": story_payload["session_id"], "dry_run": True})
            self.assertTrue(heygen.ok)
            veo = await adapter.veo_transition_closeup_generation({"session_id": story_payload["session_id"], "dry_run": True, "clip_count": 1})
            self.assertTrue(veo.ok)
            final = await adapter.ffmpeg_video_composition({"session_id": story_payload["session_id"], "dry_run": True})
            self.assertTrue(final.ok)
            final_payload = json.loads(final.content)
            self.assertTrue(final_payload["traceability_passed"])

            status = await adapter.production_run_status({"session_id": story_payload["session_id"]})
            self.assertTrue(status.ok)
            status_payload = json.loads(status.content)
            self.assertTrue(status_payload["manifest"]["exists"])
            self.assertEqual(status_payload["run"]["status"], "completed")

    async def test_progress_events_are_forwarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = SessionIndex(tmp)
            adapter = AlcoholProductionAdapters(Path(tmp), index)
            events = []
            runtime = ToolRuntimeContext("alcohol_story_generation", "alcohol_story_generation", progress_callback=events.append)
            result = await adapter.alcohol_story_generation({"idea": "卖一款红酒"}, runtime)
            self.assertTrue(result.ok)
            self.assertTrue(any(event.get("type") == "tool_progress" for event in events))

    async def test_performance_ingest_promotes_reusable_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = SessionIndex(tmp)
            adapter = AlcoholProductionAdapters(Path(tmp), index)
            story = await adapter.alcohol_story_generation({"idea": "卖酒"})
            session_id = json.loads(story.content)["session_id"]
            result = await adapter.production_performance_ingest({"session_id": session_id, "platform": "抖音", "orders": 100, "gmv": "50000", "roi": "8", "conversion_rate": "0.2", "completion_rate": "0.8"})
            self.assertTrue(result.ok)
            payload = json.loads(result.content)
            self.assertIsNotNone(payload["reusable_pattern"])


if __name__ == "__main__":
    unittest.main()
