"""Real installed SDK contract smoke; no network or real AWS credentials.

Skipped when SDKs are not installed. Run with requirements-runtime.txt installed
to exercise the real AgentCore ASGI streaming endpoint and Strands constructor.
"""
import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from test_adversarial import fixture

SDK_AVAILABLE = all(importlib.util.find_spec(name) is not None for name in ("strands", "bedrock_agentcore", "httpx"))
OFFLINE_ENV = {
    "AWS_ACCESS_KEY_ID": "offline-test", "AWS_SECRET_ACCESS_KEY": "offline-test",
    "AWS_SESSION_TOKEN": "offline-test", "AWS_EC2_METADATA_DISABLED": "true",
    "AWS_CONFIG_FILE": os.devnull, "AWS_SHARED_CREDENTIALS_FILE": os.devnull,
    "BAKU_USE_LLM": "false",
}


@unittest.skipUnless(SDK_AVAILABLE, "optional real SDK dependencies are not installed")
class LocalSDKSmoke(unittest.IsolatedAsyncioTestCase):
    async def test_actual_agentcore_streaming_endpoint_five_slots(self):
        import httpx
        from baku_fc.runtime import create_app
        with patch.dict(os.environ, OFFLINE_ENV, clear=True):
            for pid in range(5):
                app = create_app(pid)
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://offline") as client:
                    response = await client.post("/invocations", json={"prompt": json.dumps(fixture(pid))})
                    self.assertEqual(response.status_code, 200)
                    data_lines = [line[6:] for line in response.text.splitlines() if line.startswith("data: ")]
                    self.assertEqual(len(data_lines), 1)
                    envelope = json.loads(data_lines[0])
                    # AgentCore SSE serializes the yielded string. The workshop
                    # handler itself yields JSON text, so unwrap both layers.
                    self.assertIsInstance(envelope, str)
                    commands = json.loads(envelope)
                    self.assertEqual(len(commands), 1)
                    self.assertEqual(commands[0]["playerId"], pid)

    async def test_real_bedrock_model_constructor_accepts_settings_without_request(self):
        from baku_fc.runtime import StrandsInference
        from baku_fc.config import load_settings
        workshop_settings = Path(__file__).resolve().parents[1] / "workshop" / "ai-team-baku-v6" / "settings.workshop.json"
        with patch.dict(os.environ, OFFLINE_ENV, clear=True):
            provider = StrandsInference(load_settings(workshop_settings))
            self.assertEqual(provider.model.config.get("model_id"), "us.openai.gpt-5.6-luna")
            self.assertEqual(provider.model.client.meta.region_name, "us-east-1")
            self.assertEqual(provider.model.client.meta.config.retries["total_max_attempts"], 1)

    async def test_real_strands_pipeline_parses_a_stubbed_bedrock_stream(self):
        from baku_fc.runtime import StrandsInference
        from baku_fc.config import Settings
        from baku_fc.commands import decode
        events = [
            {"messageStart": {"role": "assistant"}},
            {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": '{"choice":0}'}}},
            {"contentBlockStop": {"contentBlockIndex": 0}},
            {"messageStop": {"stopReason": "end_turn"}},
            {"metadata": {"usage": {"inputTokens": 20, "outputTokens": 5, "totalTokens": 25},
                          "metrics": {"latencyMs": 1}}},
        ]
        with patch.dict(os.environ, OFFLINE_ENV, clear=True):
            provider = StrandsInference(Settings())
            with patch.object(provider.model.client, "converse_stream", return_value={"stream": iter(events)}) as method:
                result = provider('Choose one option. Return only {"choice":0}.', '{"CANDIDATES":[{}]}')
                self.assertEqual(decode(result), {"choice": 0})
                self.assertEqual(method.call_count, 1)


if __name__ == "__main__":
    unittest.main()
