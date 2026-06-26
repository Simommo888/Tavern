from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from agent_runtime.llm import ModelGateway, OpenAICompatibleLLM, PromptRegistry, PromptTemplate, _claude_messages, _claude_tools


class ModelGatewayTests(unittest.TestCase):
    def test_prompt_registry_renders_live_anchor_template(self):
        messages = PromptRegistry().render_messages("live_anchor_reply", {"intent": "price_question"})
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("酒类电商直播间数字人主播", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("15 秒以内", messages[1]["content"])
        self.assertIn("price_question", messages[1]["content"])

    def test_openai_compatible_llm_keeps_legacy_provider(self):
        llm = OpenAICompatibleLLM(model="m", base_url="http://localhost:1", api_key="k", wire_api="chat_completions")
        self.assertEqual(llm.provider, "openai")
        self.assertEqual(llm.model, "m")

    def test_claude_provider_uses_current_default_model(self):
        client = MagicMock()
        with patch.dict("sys.modules", {"anthropic": MagicMock(AsyncAnthropic=MagicMock(return_value=client))}):
            gateway = ModelGateway(provider="claude", api_key="k")
        self.assertEqual(gateway.provider, "claude")
        self.assertEqual(gateway.model, "claude-opus-4-8")
        self.assertIs(gateway.client, client)

    def test_claude_messages_separate_system_prompt(self):
        system, messages = _claude_messages([
            {"role": "system", "content": "system rules"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "tool", "content": "tool result"},
        ])
        self.assertEqual(system, "system rules")
        self.assertEqual(messages, [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "user", "content": "tool result"},
        ])

    def test_openai_tools_convert_to_claude_tools(self):
        tools = _claude_tools([
            {
                "type": "function",
                "function": {
                    "name": "lookup_product",
                    "description": "查询商品知识库",
                    "parameters": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]},
                },
            }
        ])
        self.assertEqual(tools[0]["name"], "lookup_product")
        self.assertEqual(tools[0]["input_schema"]["additionalProperties"], False)
        self.assertEqual(tools[0]["input_schema"]["required"], ["sku"])

    def test_prompt_registry_persists_custom_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = PromptRegistry(workspace_root=tmp)
            registry.upsert(PromptTemplate(name="closing", system="sys", user_instruction="say bye", max_output_seconds=8))
            restored = PromptRegistry(workspace_root=tmp)
            messages = restored.render_messages("closing", {"room": "wine"})
            self.assertEqual(messages[0]["content"], "sys")
            self.assertIn("say bye", messages[1]["content"])
            self.assertIn("8 秒以内", messages[1]["content"])
            self.assertTrue((Path(tmp) / ".working_dir" / "model_gateway" / "prompt_templates.json").exists())

    def test_openai_completion_passes_request_max_tokens(self):
        async def run() -> None:
            llm = OpenAICompatibleLLM(model="m", base_url="http://localhost:1", api_key="k", wire_api="chat_completions")
            create = AsyncMock(return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="ok", tool_calls=None, model_dump=MagicMock(return_value={})))]))
            llm.client = MagicMock(chat=MagicMock(completions=MagicMock(create=create)))
            result = await llm.complete([{"role": "user", "content": "x"}], tools=[], max_tokens=123)
            self.assertEqual(result.text, "ok")
            self.assertEqual(create.await_args.kwargs["max_tokens"], 123)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
