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
        model_kwargs = dict(
            model_id=cfg.model_id,
            region_name=cfg.region,
            boto_client_config=Config(connect_timeout=cfg.connect_timeout_s,
                                      read_timeout=cfg.read_timeout_s,
                                      retries={"total_max_attempts": 1, "mode": "standard"}),
            max_tokens=16,
        )
        # Bedrock GPT-5.6 Converse rejects the temperature field entirely.
        # Claude accepts zero temperature, which keeps the menu selection
        # deterministic across the five independent player runtimes.
        if ".openai.gpt-5.6-" not in cfg.model_id:
            model_kwargs["temperature"] = 0.0
        self.model = BedrockModel(**model_kwargs)
        self._direct_converse = ".openai.gpt-5.6-" in cfg.model_id
        self._agent = None
        self._agent_system = None

    def __call__(self, system, user):
        if self._direct_converse:
            # The football response is a tiny {"choice":N} object. Calling
            # Converse directly avoids constructing a full Strands Agent and
            # processing its event stream on every sub-500 ms match tick.
            inference_config = {"maxTokens": 16}
            if ".openai.gpt-5.6-" not in self.model.config["model_id"]:
                inference_config["temperature"] = 0.0
            response = self.model.client.converse(
                modelId=self.model.config["model_id"],
                system=[{"text": system}],
                messages=[{"role": "user", "content": [{"text": user}]}],
                inferenceConfig=inference_config,
            )
            blocks = response.get("output", {}).get("message", {}).get("content", [])
            return "".join(block.get("text", "") for block in blocks if isinstance(block, dict))
        from strands import Agent
        # Keep one instrumented Strands agent so AgentCore observability can
        # verify the allowed Claude model and count tokens. Clear match history
        # before each independent tick; the engine permits only one in-flight
        # request, so a timed-out call cannot race a newer one.
        if self._agent is None or self._agent_system != system:
            self._agent = Agent(model=self.model, system_prompt=system,
                                callback_handler=None, tools=[])
            self._agent_system = system
        else:
            self._agent.messages.clear()
        return str(self._agent(user))


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
