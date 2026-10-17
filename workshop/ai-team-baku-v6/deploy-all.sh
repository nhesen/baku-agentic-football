#!/usr/bin/env bash
set -uo pipefail

# Deploy the stable Baku FC V6 policy as five independent AgentCore runtimes.
# This follows the AWS Agentic Football workshop's direct-code-deploy contract.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$SCRIPT_DIR/_build"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
export AWS_DEFAULT_REGION

ALL_AGENTS=("ai-gk" "ai-def" "ai-mid" "ai-fwd1" "ai-fwd2")
if [ -n "${1:-}" ]; then
  AGENTS=("$1")
else
  AGENTS=("${ALL_AGENTS[@]}")
fi

echo "=========================================="
echo "  Baku FC V6 - Deploy AgentCore runtimes"
echo "=========================================="

for command in agentcore aws; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "ERROR: '$command' is required."
    exit 1
  fi
done

AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text 2>/dev/null)" || {
  echo "ERROR: AWS credentials are missing or expired."
  exit 1
}
export AWS_ACCOUNT_ID

echo "Account: $AWS_ACCOUNT_ID"
echo "Region:  $AWS_DEFAULT_REGION"

cleanup() {
  rm -rf "$BUILD_DIR"
}
trap cleanup EXIT

DEPLOYED=()
FAILED=()

for agent in "${AGENTS[@]}"; do
  AGENT_SRC="$SCRIPT_DIR/$agent"
  STAGE="$BUILD_DIR/$agent"

  if [ ! -d "$AGENT_SRC" ]; then
    echo "ERROR: Unknown agent '$agent'."
    FAILED+=("$agent")
    continue
  fi

  rm -rf "$STAGE"
  mkdir -p "$STAGE/src"
  cp "$AGENT_SRC/src/main.py" "$STAGE/src/main.py"
  cp -R "$REPO_ROOT/baku_fc" "$STAGE/src/baku_fc"
  cp "$SCRIPT_DIR/settings.workshop.json" "$STAGE/src/baku_fc/settings.json"
  cp "$REPO_ROOT/requirements-runtime.txt" "$STAGE/requirements.txt"

  sed \
    -e "s|\${AWS_ACCOUNT_ID}|$AWS_ACCOUNT_ID|g" \
    -e "s|\${AWS_DEFAULT_REGION}|$AWS_DEFAULT_REGION|g" \
    "$AGENT_SRC/.bedrock_agentcore.yaml.template" > "$STAGE/.bedrock_agentcore.yaml"

  echo
  echo "Deploying $agent..."
  if (cd "$STAGE" && agentcore deploy --auto-update-on-conflict); then
    DEPLOYED+=("$agent")
  else
    FAILED+=("$agent")
  fi
done

echo
echo "Deployed: ${DEPLOYED[*]:-none}"
echo "Failed:   ${FAILED[*]:-none}"

if [ "${#FAILED[@]}" -gt 0 ]; then
  exit 1
fi

echo "All five Baku FC V6 runtimes are deployed."
