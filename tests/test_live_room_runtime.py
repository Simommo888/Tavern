import tempfile
import unittest
from pathlib import Path

from agent_runtime.llm import AssistantMessage
from agent_runtime.live_room_models import AudienceEvent, ProductProfile
from agent_runtime.live_room_runtime import LiveRoomRuntime, classify_intent


class FakeLLM:
    async def complete(self, messages, tools):
        return AssistantMessage(text="这款礼盒适合成年人节日送礼，包装比较体面，建议按需理性选择。")


class LiveRoomRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_session_and_reply(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = LiveRoomRuntime(Path(tmp), llm=FakeLLM())
            session = await runtime.create_session(ProductProfile(product_name="测试礼盒"))
            reply = await runtime.handle_audience_event(session.session_id, AudienceEvent(text="适合送领导吗？"))
            self.assertEqual(reply.intent, "gift_question")
            self.assertIn("理性", reply.text)
            saved = runtime.get_session(session.session_id)
            self.assertEqual(saved.event_count, 1)
            self.assertEqual(len(runtime.events(session.session_id)), 4)
            self.assertTrue(reply.speech_artifact_id)
            self.assertTrue(runtime.speech_audio_path(session.session_id, reply.speech_artifact_id).exists())

    async def test_compliance_rewrites_risky_question(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = LiveRoomRuntime(Path(tmp), llm=FakeLLM())
            session = await runtime.create_session()
            reply = await runtime.handle_audience_event(session.session_id, AudienceEvent(text="喝了是不是养生？"))
            self.assertEqual(reply.intent, "compliance_risk")
            self.assertFalse(reply.compliance_passed)
            self.assertIn("不能宣传养生", reply.text)

    def test_classify_intent(self):
        self.assertEqual(classify_intent("多少钱"), "price_question")
        self.assertEqual(classify_intent("今天有没有优惠"), "promotion_question")
        self.assertEqual(classify_intent("小孩能喝吗"), "compliance_risk")


if __name__ == "__main__":
    unittest.main()
