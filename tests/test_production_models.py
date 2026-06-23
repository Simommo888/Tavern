import unittest

from interfaces.production import AlcoholSalesBrief, CompositionManifest, MaterialRecord, ProductionRun, TimelineSegment


class ProductionModelTests(unittest.TestCase):
    def test_production_run_round_trips(self):
        run = ProductionRun(run_id="run-1", session_id="session-1", user_idea="卖一款酱香酒", brief=AlcoholSalesBrief(product_name="样品酒", sales_goal="提升转化"))
        payload = run.model_dump()
        restored = ProductionRun.model_validate(payload)
        self.assertEqual(restored.brief.product_name, "样品酒")
        self.assertEqual(restored.status, "created")

    def test_material_record_tracks_source_and_hash(self):
        material = MaterialRecord(material_id="mat-1", material_type="sales_script", session_id="s", run_id="r", source_agent="script_generation_agent", content_hash="abc")
        self.assertEqual(material.source_agent, "script_generation_agent")
        self.assertFalse(material.used_in_final)

    def test_composition_manifest_contains_timeline_segments(self):
        manifest = CompositionManifest(composition_id="comp-1", run_id="r", session_id="s", timeline=[TimelineSegment(segment_id="seg-1", material_id="clip-1", duration=6.0)])
        self.assertEqual(manifest.timeline[0].material_id, "clip-1")


if __name__ == "__main__":
    unittest.main()
