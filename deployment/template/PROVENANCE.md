# Deployment template provenance

The `agentcore/cdk/` files are copied unchanged from the official AWS sample:

- Repository: https://github.com/aws-samples/sample-ai-possibilities
- Commit: `15279eb89b7113b145f3a1394ddaec5d39c04ac4`
- Source directory: `agentic-football-sample-agents/ai-team-strands-balanced/agentcore/cdk`
- Source link: https://github.com/aws-samples/sample-ai-possibilities/tree/15279eb89b7113b145f3a1394ddaec5d39c04ac4/agentic-football-sample-agents/ai-team-strands-balanced/agentcore/cdk
- Retrieved: 16 October 2026.
- Licence: MIT No Attribution (MIT-0), retained in `LICENSE-MIT-0`.

`tools/build_agents.py` is a new local packaging helper. It uses the sample's
CodeZip/Python 3.12 schema, generates the five runtime specifications, and copies
the local `baku_fc` package into each independent code location.

Generated runtimes explicitly set `instrumentation.enableOtel` to `false`.
The tested runtime requirements do not include the optional
`opentelemetry-instrument` launcher; the upstream construct would otherwise
prepend that executable to the startup entrypoint. Application logs remain
available through the AgentCore runtime's normal logging.

The template pins CDK packages in `package-lock.json`. The official sample
requires the npm `@aws/agentcore` CLI version 0.25.0 or later. The legacy Python
starter toolkit also provides an executable named `agentcore`; the two deployment
formats differ. Check which CLI is on PATH before running deployment commands.

The builder does not read AWS credentials, bootstrap CDK, change installed tools,
call AWS, or deploy. Deployment and ARN listing are explicit manual commands.

## Player Portal invocation access

The build generates no cross-account access policy because the Baku match
server's IAM principal has not been supplied. If the portal invokes from another
AWS account, its organizer must provide the exact calling role ARN and intended
runtime endpoint. AWS requires an allow policy on **both the runtime and its
endpoint**, plus the caller's identity policy allowing
`bedrock-agentcore:InvokeAgentRuntime` on both resources. The runtime's own
execution role and its permissions to call Bedrock are a separate concern.

Follow the official [resource-based policy guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/resource-based-policies.html)
using that exact role and both actual resource ARNs. AWS documents
`aws bedrock-agentcore-control put-resource-policy --resource-arn <actual-arn> --policy file://policy.json`.
No policy is applied by this package. Run the event portal's connectivity/fitness
test after the workshop's invocation permissions are configured.

If the portal and runtime are already covered by the workshop's account/role
setup, retain that setup. An empty `aws-targets.json` in a dry build is
intentional: rerun the builder with `--account` and the event region before
deployment. The account value is only an account ID, never credentials.
