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
runtime. The only deployment-specific override is the AWS cross-region inference
profile `us.amazon.nova-micro-v1:0`, which is the model ID used by the workshop.

Register the resulting runtime ARNs in this order:

1. `baku_v6_gk_agent` - GK / player 0
2. `baku_v6_def_agent` - DEF / player 1
3. `baku_v6_mid_agent` - MID / player 2
4. `baku_v6_fwd1_agent` - FWD / player 3
5. `baku_v6_fwd2_agent` - FWD / player 4
