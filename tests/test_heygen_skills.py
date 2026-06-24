import json
import tempfile
import unittest
from pathlib import Path

from agent_runtime.heygen_skills import HeyGenLiveRoomSkills, build_heygen_skill_specs
from agent_runtime.production_adapters import AlcoholProductionAdapters
from agent_runtime.session_index import SessionIndex
from agent_runtime.tools import ToolRegistry


class HeyGenSkillTests(unittest.IsolatedAsyncioTestCase):
    async def test_skill_package_exposes_config_prepare_and_generate_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = SessionIndex(tmp)
            registry = ToolRegistry(build_heygen_skill_specs(Path(tmp), index))

            names = {tool["function"]["name"] for tool in registry.list_function_tools()}
            self.assertIn("heygen_live_room_check_config", names)
            self.assertIn("heygen_live_room_prepare_script", names)
            self.assertIn("heygen_live_room_generate_clip", names)
            self.assertEqual(registry.resolve_name("heygen_live_room_generation"), "heygen_live_room_generate_clip")
            self.assertEqual(registry.resolve_name("digital_human_live_room_generation"), "heygen_live_room_generate_clip")

    async def test_prepare_then_generate_dry_run_registers_traceable_materials(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = SessionIndex(tmp)
            adapter = AlcoholProductionAdapters(Path(tmp), index)
            skills = HeyGenLiveRoomSkills(Path(tmp), index)

            story = await adapter.alcohol_story_generation({"idea": "做一条酱香酒直播间销售视频"})
            session_id = json.loads(story.content)["session_id"]
            script = await adapter.alcohol_script_generation({"session_id": session_id})
            script_id = json.loads(script.content)["script_material_id"]
            storyboard = await adapter.alcohol_storyboard_generation({"session_id": session_id})
            shot_plan_id = json.loads(storyboard.content)["shot_plan_material_id"]

            prepared = await skills.heygen_live_room_prepare_script({"session_id": session_id, "script_material_id": script_id, "shot_plan_material_id": shot_plan_id})
            self.assertTrue(prepared.ok)
            prepared_payload = json.loads(prepared.content)
            self.assertTrue(prepared_payload["heygen_script_material_id"])

            generated = await skills.heygen_live_room_generate_clip({"session_id": session_id, "heygen_script_material_id": prepared_payload["heygen_script_material_id"], "dry_run": True})
            self.assertTrue(generated.ok)
            payload = json.loads(generated.content)
            self.assertEqual(payload["agent_name"], "digital_human_live_room_agent")
            self.assertEqual(payload["provider_job_ids"], ["heygen-dry-run"])
            self.assertEqual(payload["input_material_ids"], [prepared_payload["heygen_script_material_id"]])
            self.assertTrue((index.working_dir(session_id) / payload["clip_paths"][0]).exists())

    async def test_adapter_legacy_entrypoint_delegates_to_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = SessionIndex(tmp)
            adapter = AlcoholProductionAdapters(Path(tmp), index)

            story = await adapter.alcohol_story_generation({"idea": "做一条清香酒直播间销售视频"})
            session_id = json.loads(story.content)["session_id"]
            await adapter.alcohol_script_generation({"session_id": session_id})

            generated = await adapter.heygen_live_room_generation({"session_id": session_id, "dry_run": True})
            self.assertTrue(generated.ok)
            payload = json.loads(generated.content)
            self.assertEqual(payload["agent_name"], "digital_human_live_room_agent")
            self.assertTrue(payload["digital_human_clip_material_ids"])


if __name__ == "__main__":
    unittest.main()
