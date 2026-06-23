import unittest
from unittest.mock import patch

from tools.digital_human_generator_heygen_api import DigitalHumanGeneratorHeyGenAPI


class HeyGenGeneratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_dry_run_returns_placeholder_bytes_without_api_key(self):
        generator = DigitalHumanGeneratorHeyGenAPI(api_key="", avatar_id="avatar", voice_id="voice")
        result = await generator.generate_live_room_segment(script_text="主播：理性饮酒", dry_run=True)
        self.assertEqual(result.provider_job_id, "heygen-dry-run")
        self.assertIsNotNone(result.video_bytes)

    async def test_real_run_requires_api_key(self):
        generator = DigitalHumanGeneratorHeyGenAPI(api_key="", avatar_id="avatar", voice_id="voice")
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                await generator.generate_live_room_segment(script_text="主播：理性饮酒")


if __name__ == "__main__":
    unittest.main()
