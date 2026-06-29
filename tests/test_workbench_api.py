import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from apps.api.app.api.v1 import live as live_module
from apps.api.app.api.v1 import workbench as workbench_module
from apps.api.app.agents.live_anchor_graph import LiveAnchorGraph
from apps.api.app.application.live_room_service import LiveRoomService
from apps.api.app.application.workbench_service import WorkbenchService
from apps.api.app.main import create_app


class WorkbenchApiTests(unittest.TestCase):
    def test_live_api_v1_creates_session_and_reply(self):
        with tempfile.TemporaryDirectory() as tmp:
            live_module._service = LiveRoomService(Path(tmp))
            client = TestClient(create_app())

            created = client.post("/api/v1/live/sessions", json={"product_name": "测试礼盒"})
            self.assertEqual(created.status_code, 200)
            session_id = created.json()["session"]["session_id"]

            reply = client.post(f"/api/v1/live/sessions/{session_id}/events", json={"text": "多少钱？", "user_name": "测试观众"})
            self.assertEqual(reply.status_code, 200)
            self.assertEqual(reply.json()["reply"]["intent"], "price_question")
            self.assertTrue(reply.json()["reply"]["speech_audio_url"].startswith("/api/v1/live/sessions/"))

            snapshot = client.get(f"/api/v1/live/sessions/{session_id}")
            self.assertEqual(snapshot.status_code, 200)
            self.assertEqual([event["type"] for event in snapshot.json()["events"]], ["session_created", "audience_event", "speech_artifact", "anchor_reply"])

    def test_live_api_v1_accepts_async_audience_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            live_module._service = LiveRoomService(Path(tmp))
            client = TestClient(create_app())

            created = client.post("/api/v1/live/sessions", json={"product_name": "异步礼盒"})
            session_id = created.json()["session"]["session_id"]
            accepted = client.post(f"/api/v1/live/sessions/{session_id}/events?mode=async", json={"text": "适合送礼吗？", "user_name": "异步观众"})
            self.assertEqual(accepted.status_code, 202)
            self.assertTrue(accepted.json()["accepted"])
            self.assertEqual(accepted.json()["task"]["task_type"], "live.audience_event.received")

    def test_workbench_business_apis_expose_seeded_operational_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench_module._service = WorkbenchService(Path(tmp))
            client = TestClient(create_app())

            summary = client.get("/api/v1/dashboard/summary")
            self.assertEqual(summary.status_code, 200)
            self.assertEqual(summary.json()["live_status"], "running")
            self.assertGreater(summary.json()["online_users"], 0)

            products = client.get("/api/v1/products")
            self.assertEqual(products.status_code, 200)
            self.assertEqual(products.json()["products"][0]["status"], "published")

            generated = client.post("/api/v1/scripts/templates/generate", json={"category": "sales"})
            self.assertEqual(generated.status_code, 200)
            self.assertTrue(generated.json()["template"]["ai_generated"])

            rules = client.get("/api/v1/workflow/rules")
            self.assertEqual(rules.status_code, 200)
            self.assertGreaterEqual(len(rules.json()["rules"]), 3)

            definitions = client.get("/api/v1/workflow/definitions")
            self.assertEqual(definitions.status_code, 200)
            workflow = definitions.json()["definitions"][0]
            self.assertEqual([node["label"] for node in workflow["nodes"]], ["商品", "品牌", "故事", "剧本", "分镜", "导演", "视觉导演", "语音", "数字人", "直播间", "视频", "推流"])
            self.assertEqual(workflow["nodes"][-1]["id"], "streaming")
            self.assertIn("分镜→导演→视觉导演→语音", workflow["description"])
            self.assertEqual(workflow["edges"][-1], {"source": "video", "target": "streaming", "type": "handoff"})

            runs = client.get("/api/v1/workflow/runs")
            self.assertEqual(runs.status_code, 200)
            run = runs.json()["runs"][0]
            nodes = client.get(f"/api/v1/workflow/runs/{run['workflow_run_id']}/nodes")
            self.assertEqual(nodes.status_code, 200)
            self.assertEqual([node["node_id"] for node in nodes.json()["nodes"]], ["product", "brand", "story", "script", "storyboard", "director", "visual_director", "voice", "avatar", "live_room", "video", "streaming"])

            assets = client.get("/api/v1/assets")
            self.assertEqual(assets.status_code, 200)
            self.assertIn("uuid", assets.json()["assets"][0])
            self.assertIn("version", assets.json()["assets"][0])

            components = client.get("/api/v1/components")
            self.assertEqual(components.status_code, 200)
            component = components.json()["components"][0]
            self.assertIn("uuid", component)
            self.assertIn("source_asset_ids", component)
            self.assertIn("metadata", component)

            scenes = client.get("/api/v1/scenes")
            self.assertEqual(scenes.status_code, 200)
            scene = scenes.json()["scenes"][0]
            self.assertIn("uuid", scene)
            self.assertIn("component_slots", scene)
            self.assertGreaterEqual(len(scene["component_ids"]), 1)
            self.assertEqual(scene["metadata"]["contract"], "Asset -> Component -> Scene -> LiveRoom")

            live_rooms = client.get("/api/v1/live-room-compositions")
            self.assertEqual(live_rooms.status_code, 200)
            live_room = live_rooms.json()["compositions"][0]
            self.assertIn(scene["scene_id"], live_room["scene_ids"])
            self.assertGreaterEqual(len(live_room["scene_snapshot"]), 1)
            self.assertEqual(live_room["metadata"]["contract"], "Asset -> Component -> Scene -> LiveRoom")

            metrics = client.get("/api/v1/platform/metrics")
            self.assertEqual(metrics.status_code, 200)
            self.assertGreater(metrics.json()["metrics"][0]["gmv"], 0)

            analytics = client.get("/api/v1/analytics/overview")
            self.assertEqual(analytics.status_code, 200)
            overview = analytics.json()
            self.assertGreater(overview["summary"]["gmv"], 0)
            self.assertGreater(overview["summary"]["ctr"], 0)
            self.assertGreater(overview["summary"]["cvr"], 0)
            self.assertEqual(overview["top_ranking"][0]["rank"], 1)
            self.assertIn("score", overview["top_ranking"][0])
            self.assertGreaterEqual(len(overview["component_ranking"]), 1)
            self.assertGreaterEqual(len(overview["prompt_ranking"]), 1)
            self.assertGreaterEqual(len(overview["avatar_ranking"]), 1)
            self.assertGreaterEqual(len(overview["best_practice_ranking"]), 1)

    def test_product_video_workflow_runs_product_brand_to_complete_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench_module._service = WorkbenchService(Path(tmp))
            client = TestClient(create_app())

            response = client.post("/api/v1/workflow/product-videos/run", json={
                "brand_name": "龙八",
                "duration_seconds": 45,
                "product": {
                    "product_name": "龙八礼盒",
                    "sku": "LB-VIDEO-001",
                    "price": 299,
                    "original_price": 399,
                    "aroma_type": "酱香",
                    "selling_points": ["宴请送礼", "礼盒包装", "直播权益"],
                    "scenes": ["商务宴请", "节日拜访"],
                },
                "brand_profile": {
                    "positioning": "面向成年人礼赠和宴请场景的可信酒类品牌",
                    "tone": "高级、可信、克制",
                },
            })
            self.assertEqual(response.status_code, 200)
            workflow = response.json()["workflow"]
            self.assertEqual(workflow["run"]["status"], "succeeded")
            self.assertEqual(workflow["definition"]["version"], "product-video-v1")
            self.assertEqual(
                [node["node_id"] for node in workflow["nodes"]],
                ["product_brand_input", "planner", "story", "script", "director", "visual_director", "asset", "image", "video", "editor"],
            )
            self.assertEqual(workflow["nodes"][-1]["output_payload"]["artifact"], "complete_video")
            self.assertTrue(workflow["final_video"]["uri"].startswith("file://"))
            self.assertEqual(workflow["final_video"]["status"], "placeholder_ready")
            self.assertIn("complete_video", workflow["artifacts"])
            self.assertIn("final_video", workflow["run"]["output_payload"])

            definitions = client.get("/api/v1/workflow/definitions")
            product_video_definition = next(item for item in definitions.json()["definitions"] if item["version"] == "product-video-v1")
            self.assertEqual(product_video_definition["nodes"][-1]["id"], "editor")
            self.assertEqual(product_video_definition["nodes"][-1]["artifact"], "complete_video")

            nodes = client.get(f"/api/v1/workflow/runs/{workflow['run']['workflow_run_id']}/nodes")
            self.assertEqual(nodes.status_code, 200)
            self.assertEqual([node["status"] for node in nodes.json()["nodes"]], ["succeeded"] * 10)

            assets = client.get("/api/v1/assets")
            self.assertEqual(assets.status_code, 200)
            complete_video_assets = [asset for asset in assets.json()["assets"] if asset["asset_type"] == "video" and "Editor Agent" in asset["tags"]]
            self.assertTrue(complete_video_assets)
            self.assertEqual(complete_video_assets[-1]["object_key"], workflow["final_video"]["uri"])

    def test_product_video_workflow_supports_stepwise_agent_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench_module._service = WorkbenchService(Path(tmp))
            client = TestClient(create_app())
            payload = {
                "brand_name": "龙八",
                "duration_seconds": 45,
                "api_key": "must-not-persist",
                "product": {
                    "product_name": "龙八礼盒",
                    "sku": "LB-STEP-001",
                    "price": 299,
                    "selling_points": ["宴请送礼", "礼盒包装", "直播权益"],
                    "scenes": ["商务宴请", "节日拜访"],
                },
            }

            created = client.post("/api/v1/workflow/product-videos/runs", json=payload)
            self.assertEqual(created.status_code, 200)
            workflow = created.json()["workflow"]
            run_id = workflow["run"]["workflow_run_id"]
            self.assertEqual(workflow["run"]["status"], "running")
            self.assertEqual(workflow["run"]["input_payload"]["request"]["api_key"], "***")
            self.assertEqual([node["status"] for node in workflow["nodes"]], ["running"] + ["queued"] * 9)

            for node_id in ["product_brand_input", "planner", "story", "script", "director", "visual_director", "asset", "image", "video", "editor"]:
                result = client.post(f"/api/v1/workflow/product-videos/runs/{run_id}/nodes/{node_id}/run", json={})
                self.assertEqual(result.status_code, 200)
                workflow = result.json()["workflow"]

            self.assertEqual(workflow["run"]["status"], "succeeded")
            self.assertEqual(workflow["run"]["progress"], 1)
            self.assertEqual(workflow["nodes"][-1]["output_payload"]["artifact"], "complete_video")
            self.assertTrue(workflow["final_video"]["uri"].startswith("file://"))
            planner_node = next(node for node in workflow["nodes"] if node["node_id"] == "planner")
            video_node = next(node for node in workflow["nodes"] if node["node_id"] == "video")
            self.assertEqual(planner_node["input_payload"]["provider_config"]["model"], "gpt-5.5")
            self.assertEqual(planner_node["input_payload"]["provider_config"]["api_key_env"], "OPENAI_API_KEY")
            self.assertEqual(video_node["input_payload"]["provider_config"]["provider"], "jimeng_ai")
            self.assertEqual(video_node["input_payload"]["provider_config"]["api_key_env"], "TAVERN_JIMENG_API_KEY")

    def test_phase_nine_mvp_api_runs_product_to_saved_live_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench_module._service = WorkbenchService(Path(tmp))
            client = TestClient(create_app())

            response = client.post("/api/v1/mvp/live-plans/run", json={
                "brand_name": "龙八",
                "product": {
                    "product_name": "龙八礼盒",
                    "sku": "LB-MVP-001",
                    "price": 299,
                    "original_price": 399,
                    "aroma_type": "酱香",
                    "selling_points": ["宴请送礼", "礼盒包装", "直播权益"],
                    "scenes": ["商务宴请", "节日拜访"],
                },
            })
            self.assertEqual(response.status_code, 200)
            plan = response.json()["plan"]
            self.assertEqual(plan["status"], "succeeded")
            self.assertEqual([step["label"] for step in plan["steps"]], ["上传商品", "品牌分析", "剧本", "数字人口播", "数字人", "直播视频", "保存方案"])
            self.assertIn("live_video_uri", plan)
            self.assertEqual(plan["brand_analysis"]["brand_name"], "龙八")
            self.assertTrue(plan["script_snapshot"]["content"].startswith("大家好"))
            self.assertEqual(plan["saved_outputs"]["live_room_composition_id"], plan["live_room_composition_id"])
            self.assertIn(plan["steps"][3]["data"]["provider_id"], {"edge_tts", "placeholder"})
            self.assertIn("tts_job", plan["saved_outputs"])

            listed = client.get("/api/v1/mvp/live-plans")
            self.assertEqual(listed.status_code, 200)
            self.assertEqual(listed.json()["plans"][0]["plan_id"], plan["plan_id"])

            definitions = client.get("/api/v1/workflow/definitions")
            mvp_definition = next(item for item in definitions.json()["definitions"] if item["version"] == "phase9-v1")
            self.assertEqual([node["label"] for node in mvp_definition["nodes"]], ["上传商品", "品牌分析", "剧本", "数字人口播", "数字人", "直播视频", "保存方案"])

            nodes = client.get(f"/api/v1/workflow/runs/{plan['workflow_run_id']}/nodes")
            self.assertEqual(nodes.status_code, 200)
            self.assertEqual([node["status"] for node in nodes.json()["nodes"]], ["succeeded"] * 7)

    def test_phase_nine_mvp_uses_cosyvoice_when_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench_module._service = WorkbenchService(Path(tmp))
            client = TestClient(create_app())
            response = Mock()
            response.status_code = 200
            response.headers = {"content-type": "audio/wav"}
            response.content = b"RIFF....WAVEfmt "
            with patch.dict(os.environ, {"TAVERN_COSYVOICE_BASE_URL": "http://cosyvoice.test", "TAVERN_COSYVOICE_SPEECH_PATH": "/v1/audio/speech"}, clear=False):
                with patch("apps.api.app.plugins.tts.requests.get", return_value=response):
                    with patch("apps.api.app.plugins.tts.requests.post", return_value=response):
                        result = client.post("/api/v1/mvp/live-plans/run", json={"brand_name": "CosyVoice验证"})

            self.assertEqual(result.status_code, 200)
            plan = result.json()["plan"]
            self.assertEqual(plan["steps"][3]["data"]["provider_id"], "cosyvoice_tts")
            self.assertTrue(plan["speech_artifact_uri"].startswith("file://"))
            self.assertEqual(plan["saved_outputs"]["tts_job"]["metadata"]["provider_id"], "cosyvoice_tts")

    def test_rag_model_avatar_and_platform_apis(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench_module._service = WorkbenchService(Path(tmp))
            client = TestClient(create_app())

            documents = client.get("/api/v1/knowledge/documents")
            self.assertEqual(documents.status_code, 200)
            self.assertEqual(documents.json()["documents"][0]["status"], "indexed")

            search = client.post("/api/v1/knowledge/search", json={"query": "送礼 商务宴请", "limit": 3})
            self.assertEqual(search.status_code, 200)
            self.assertTrue(search.json()["chunks"])
            self.assertGreater(search.json()["results"][0]["score"], 0)
            self.assertIn("matched_terms", search.json()["results"][0])

            providers = client.get("/api/v1/model-gateway/providers")
            self.assertEqual(providers.status_code, 200)
            self.assertEqual({item["name"] for item in providers.json()["providers"]}, {"gpt", "claude", "gemini"})

            prompts = client.get("/api/v1/model-gateway/prompts")
            self.assertEqual(prompts.status_code, 200)
            self.assertEqual(prompts.json()["prompts"][0]["purpose"], "live_reply")

            avatar_id = client.get("/api/v1/avatars").json()["avatars"][0]["avatar_id"]
            job = client.post(f"/api/v1/avatars/{avatar_id}/jobs", json={"input_text": "欢迎来到直播间"})
            self.assertEqual(job.status_code, 200)
            self.assertEqual(job.json()["job"]["provider_job_id"], "heygen-dry-run")

            platform_event = client.post("/api/v1/platform/events", json={"platform": "manual", "event_type": "comment", "text": "真假怎么保证？"})
            self.assertEqual(platform_event.status_code, 200)
            self.assertEqual(platform_event.json()["event"]["text"], "真假怎么保证？")

    def test_operator_write_apis_update_workbench_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench_module._service = WorkbenchService(Path(tmp))
            client = TestClient(create_app())

            product = client.post("/api/v1/products", json={"product_name": "龙八礼盒", "sku": "LB-001", "price": 299}).json()["product"]
            published = client.post(f"/api/v1/products/{product['product_id']}/publish")
            self.assertEqual(published.status_code, 200)
            self.assertEqual(published.json()["product"]["status"], "published")
            unpublished = client.post(f"/api/v1/products/{product['product_id']}/unpublish")
            self.assertEqual(unpublished.json()["product"]["status"], "draft")

            rule = client.post("/api/v1/workflow/rules", json={"name": "关注促单", "event_type": "user_follow", "action_type": "sales_push"}).json()["rule"]
            toggled = client.patch(f"/api/v1/workflow/rules/{rule['rule_id']}", json={"enabled": False})
            self.assertEqual(toggled.status_code, 200)
            self.assertFalse(toggled.json()["rule"]["enabled"])

            document = client.post("/api/v1/knowledge/documents", json={"name": "测试资料", "source_type": "text"}).json()["document"]
            indexed = client.post(f"/api/v1/knowledge/documents/{document['document_id']}/index", json={"text": "商务宴请\n节日送礼"})
            self.assertEqual(indexed.status_code, 200)
            self.assertEqual(indexed.json()["document"]["chunk_count"], 2)

            metric = client.post("/api/v1/platform/metrics", json={"online_users": 99, "gmv": 1234, "order_count": 12})
            self.assertEqual(metric.status_code, 200)
            self.assertEqual(metric.json()["metric"]["online_users"], 99)

    def test_live_anchor_graph_produces_compliant_reply(self):
        result = LiveAnchorGraph().run({"event_text": "喝了是不是养生？", "product_context": {"product_name": "测试酒"}})
        self.assertEqual(result["intent"], "compliance_risk")
        self.assertIn("不能宣传养生", result["final_reply"])

    def test_live_anchor_graph_retrieves_product_knowledge(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbench = WorkbenchService(Path(tmp))
            product = workbench.products.list()[0]
            result = LiveAnchorGraph(workbench=workbench).run({"event_text": "适合送领导吗？", "product_context": product.model_dump()})
            self.assertTrue(result["retrieved_chunks"])
            self.assertIn("送领导", result["retrieved_chunks"][0]["text"])


if __name__ == "__main__":
    unittest.main()
