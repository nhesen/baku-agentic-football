# Baku FC V6 - AWS Workshop deployment

This directory adapts the stable V6 policy to the direct-code-deploy layout used
by the AWS Agentic Football workshop. It creates one AgentCore runtime for each
portal slot: GK, DEF, MID, FWD1, and FWD2.

From the repository root in AWS CloudShell:

```bash
python3 -m pip install --user bedrock-agentcore-starter-toolkit
cd workshop/ai-team-baku-v6
chmod +x deploy-all.sh
./deploy-all.sh
```

The deploy script copies the canonical `baku_fc/` package into each temporary
runtime. Nothing in the five thin entrypoints duplicates or replaces the GitHub
tactics: they select player IDs 0-4 and call `baku_fc.runtime.create_app()`.

The deployment-specific model is the AWS US cross-region inference profile
`us.openai.gpt-5.6-luna`. Luna is the low-latency GPT-5.6 variant and supports
the Bedrock Converse API used by Strands. The model can only select from the
legal tactical candidates produced by the V6 engine; the validated deterministic
V6 fallback remains active when inference is slow or unavailable.

Register the resulting runtime ARNs in this order:

1. `baku_v6_gk_agent` - GK / player 0
2. `baku_v6_def_agent` - DEF / player 1
3. `baku_v6_mid_agent` - MID / player 2
4. `baku_v6_fwd1_agent` - FWD / player 3
5. `baku_v6_fwd2_agent` - FWD / player 4
