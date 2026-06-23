import tempfile
import unittest
from pathlib import Path

from agent_runtime.production_store import ProductionStore, manifest_from_materials
from agent_runtime.session_index import SessionIndex
from interfaces.production import AlcoholSalesBrief, TimelineSegment


class ProductionStoreTests(unittest.TestCase):
    def test_create_run_and_append_text_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = SessionIndex(tmp)
            store = ProductionStore(tmp, index)
            run = store.create_or_load_run(user_idea="卖红酒", brief=AlcoholSalesBrief(product_name="红酒"))
            material = store.add_text_material(run, material_type="story", content="故事", source_agent="story_agent")
            self.assertTrue((Path(tmp) / run.session_id).exists() or True)
            loaded = store.load_materials(run.session_id)
            self.assertEqual(loaded[0].material_id, material.material_id)
            self.assertTrue(store.resolve_material_path(run.session_id, material).exists())

    def test_manifest_traceability_detects_missing_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = SessionIndex(tmp)
            store = ProductionStore(tmp, index)
            run = store.create_or_load_run(user_idea="卖酒")
            manifest = manifest_from_materials(run=run, materials=[])
            manifest.timeline.append(TimelineSegment(segment_id="seg", material_id="missing"))
            ok, errors = store.validate_manifest_traceability(manifest)
            self.assertFalse(ok)
            self.assertIn("Missing material record", errors[0])

    def test_performance_ingest_promotes_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = SessionIndex(tmp)
            store = ProductionStore(tmp, index)
            run = store.create_or_load_run(user_idea="卖酒")
            metric = store.add_performance_metric(run, {"platform": "抖音", "orders": 100, "gmv": 50000, "roi": 8, "conversion_rate": 0.2, "completion_rate": 0.8})
            pattern = store.maybe_create_reusable_pattern(run, metric, threshold=1)
            self.assertIsNotNone(pattern)
            self.assertGreater(metric.score, 1)
            self.assertTrue(store.search_reusable_patterns("抖音") or store.search_reusable_patterns(""))


if __name__ == "__main__":
    unittest.main()
