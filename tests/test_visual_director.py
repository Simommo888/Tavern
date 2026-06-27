import unittest

from agents.visual_director import VisualBlueprintValidationError, parse_visual_blueprint_output


VALID_BLUEPRINT = """
visual_blueprint:
  brand:
    palette: 深酒红与香槟金
  scene:
    background: 高端酒窖直播间场景
  camera:
    lens: 50mm
  lighting:
    key: 3200K warm lighting
  composition:
    rule: rule of thirds
  avatar:
    position: left
  product:
    position: right
  subtitle:
    style: modern sans-serif
  overlay:
    style: minimal
  music:
    cue: piano
  transition:
    style: slow dissolve
  image_prompt: "premium commercial photography, 50mm camera lens, warm lighting, shallow depth of field, wood material, 张裕 brand, cinematic style"
  video_prompt: "slow camera movement and motion through a warm winery scene, cinematic lighting, premium mood and style, 8 seconds duration"
  asset_mapping:
    background: BG_WINE_CELLAR_001
    product: PRODUCT_KOYA_001
  obs_layers:
    - layer: Layer01
      source: Background
    - layer: Layer02
      source: Avatar
  director_note: 保持高级克制的酒类直播视觉语言
"""


class VisualDirectorSchemaTests(unittest.TestCase):
    def test_parse_valid_yaml_visual_blueprint(self):
        document = parse_visual_blueprint_output(VALID_BLUEPRINT)
        self.assertEqual(document.visual_blueprint.asset_mapping["background"], "BG_WINE_CELLAR_001")
        self.assertEqual(document.visual_blueprint.obs_layers[0]["layer"], "Layer01")

    def test_parse_valid_json_visual_blueprint(self):
        document = parse_visual_blueprint_output('''{
          "visual_blueprint": {
            "brand": "张裕", "scene": "酒窖场景", "camera": "50mm lens", "lighting": "warm lighting",
            "composition": "rule of thirds", "avatar": "left", "product": "right", "subtitle": "white sans-serif",
            "overlay": "minimal", "music": "piano", "transition": "slow dissolve",
            "image_prompt": "premium commercial photography with camera lens, warm lighting, shallow depth of field, wood material, brand style",
            "video_prompt": "slow camera movement and motion in a winery scene, warm lighting, elegant style, 8 seconds duration",
            "asset_mapping": {"background": "BG_001"},
            "obs_layers": [{"layer": "Layer01", "source": "Background"}],
            "director_note": "执行视觉蓝图"
          }
        }''')
        self.assertEqual(document.visual_blueprint.brand, "张裕")

    def test_parse_fenced_yaml_visual_blueprint(self):
        document = parse_visual_blueprint_output(f"```yaml\n{VALID_BLUEPRINT}\n```")
        self.assertIn("cinematic", document.visual_blueprint.image_prompt)

    def test_missing_root_fails(self):
        with self.assertRaisesRegex(VisualBlueprintValidationError, "missing required root key"):
            parse_visual_blueprint_output("brand: 张裕")

    def test_missing_asset_mapping_fails(self):
        with self.assertRaisesRegex(VisualBlueprintValidationError, "asset_mapping"):
            parse_visual_blueprint_output(VALID_BLUEPRINT.replace("  asset_mapping:\n    background: BG_WINE_CELLAR_001\n    product: PRODUCT_KOYA_001\n", ""))

    def test_empty_obs_layers_fails(self):
        with self.assertRaisesRegex(VisualBlueprintValidationError, "obs_layers"):
            parse_visual_blueprint_output(VALID_BLUEPRINT.replace("  obs_layers:\n    - layer: Layer01\n      source: Background\n    - layer: Layer02\n      source: Avatar\n", "  obs_layers: []\n"))

    def test_incomplete_image_prompt_fails(self):
        with self.assertRaisesRegex(VisualBlueprintValidationError, "image_prompt"):
            parse_visual_blueprint_output(VALID_BLUEPRINT.replace(
                "premium commercial photography, 50mm camera lens, warm lighting, shallow depth of field, wood material, 张裕 brand, cinematic style",
                "beautiful wine bottle"
            ))

    def test_incomplete_video_prompt_fails(self):
        with self.assertRaisesRegex(VisualBlueprintValidationError, "video_prompt"):
            parse_visual_blueprint_output(VALID_BLUEPRINT.replace(
                "slow camera movement and motion through a warm winery scene, cinematic lighting, premium mood and style, 8 seconds duration",
                "premium wine video"
            ))


if __name__ == "__main__":
    unittest.main()
