"""Actual AgentCore/Strands adapter. Offline modules do not import cloud SDKs."""
from __future__ import annotations

import asyncio
import json
import os

from .config import load_settings
from .engine import Engine


class StrandsInference:
    def __init__(self, cfg):
        from botocore.config import Config
        from strands.models import BedrockModel
        self.model = BedrockModel(
            model_id=cfg.model_id,
            region_name=cfg.region,
            boto_client_config=Config(connect_timeout=cfg.connect_timeout_s,
                                      read_timeout=cfg.read_timeout_s,
                                      retries={"total_max_attempts": 1, "mode": "standard"}),
            temperature=0.1, max_tokens=32,
        )

    def __call__(self, system, user):
        from strands import Agent
        # Fresh agent per call: a timed-out invocation can never mutate the next
        # agent's messages, and prompt history cannot grow across match ticks.
        agent = Agent(model=self.model, system_prompt=system, callback_handler=None, tools=[])
        return str(agent(user))


def create_app(default_pid: int):
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    cfg = load_settings(os.environ.get("BAKU_SETTINGS_PATH"))
    app = BedrockAgentCoreApp()
    inference = StrandsInference(cfg) if cfg.use_llm else None
    engine = Engine(default_pid, cfg, inference)

    @app.entrypoint
    async def invoke(payload, context):
        result = await asyncio.to_thread(engine.decide, payload)
        app.logger.info(json.dumps({"baku_fc": result["meta"]}, separators=(",", ":")))
        # Preserve the workshop's streaming JSON-array response contract. The
        # metadata is logged, never inserted into the engine's command array.
        yield json.dumps(result["commands"], separators=(",", ":"), allow_nan=False)

    return app
