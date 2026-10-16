#!/usr/bin/env python3
"""Build five self-contained AgentCore runtimes locally; never calls AWS.

Uses the CDK deployment contract of the official AWS sample pinned in
deployment/template/PROVENANCE.md. Run from a short workspace path on Windows.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path

PLAYERS = (
    (0, "baku_gk"),
    (1, "baku_anchor"),
    (2, "baku_pivot_left"),
    (3, "baku_pivot_right"),
    (4, "baku_striker"),
)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(source: Path, output: Path, account: str | None, region: str,
          model: str | None = None, project_name: str = "BakuFC") -> Path:
    """Only copies and writes local files. Credentials are neither read nor needed."""
    source, output = source.resolve(), output.resolve()
    package = source / "baku_fc"
    if not (package / "runtime.py").is_file():
        raise ValueError(f"Missing runtime package: {package}")
    if output == source or output == package or package in output.parents:
        raise ValueError("Output must be a separate deployment directory, outside baku_fc.")
    if account is not None and not re.fullmatch(r"\d{12}", account):
        raise ValueError("--account must contain exactly 12 digits.")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,29}", project_name):
        raise ValueError("Project name must be 1..30 letters, digits, underscores and start with a letter.")
    if not re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-\d+", region):
        raise ValueError("Use an AWS region such as us-east-1.")
    template = source / "deployment" / "template"
    if template == output or template in output.parents or output in template.parents:
        raise ValueError("Output must be separate from the deployment template.")
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template / "agentcore", output / "agentcore", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("node_modules", "dist", "cdk.out", "__pycache__"))
    shutil.copy2(template / "LICENSE-MIT-0", output / "LICENSE-MIT-0")
    shutil.copy2(template / "PROVENANCE.md", output / "PROVENANCE.md")

    settings_path = package / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    # Baked configuration travels with every ZIP; no reliance on local shell env.
    settings["region"] = region
    if model is not None:
        settings["model_id"] = model

    dependencies = [line.strip() for line in (source / "requirements-runtime.txt").read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.lstrip().startswith("#")]
    runtimes = []
    for pid, name in PLAYERS:
        runtime_source = output / "runtimes" / name / "src"
        runtime_source.mkdir(parents=True, exist_ok=True)
        shutil.copytree(package, runtime_source / "baku_fc", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".env"))
        write_json(runtime_source / "baku_fc" / "settings.json", settings)
        (runtime_source / "main.py").write_text(
            "from baku_fc.runtime import create_app\n\n"
            f"app = create_app({pid})\n\n"
            "if __name__ == '__main__':\n    app.run()\n", encoding="utf-8")
        dependency_lines = ",\n".join(f'    "{value}"' for value in dependencies)
        (runtime_source / "pyproject.toml").write_text(
            f'[project]\nname = "{name}"\nversion = "0.1.0"\n'
            'requires-python = ">=3.12"\ndependencies = [\n' + dependency_lines + "\n]\n",
            encoding="utf-8")
        (runtime_source / "requirements.txt").write_text("\n".join(dependencies) + "\n", encoding="utf-8")
        runtimes.append({"name": name, "build": "CodeZip", "entrypoint": "main.py",
                         "codeLocation": f"runtimes/{name}/src/", "runtimeVersion": "PYTHON_3_12",
                         "networkMode": "PUBLIC", "protocol": "HTTP",
                         # The tested runtime requirements do not install the OTEL launcher.
                         # CDK otherwise prepends opentelemetry-instrument by default.
                         "instrumentation": {"enableOtel": False}})

    spec = {"$schema": "https://schema.agentcore.aws.dev/v1/agentcore.json",
            "name": project_name, "version": 1, "managedBy": "CDK", "runtimes": runtimes}
    for key in ("memories", "knowledgeBases", "credentials", "evaluators", "onlineEvalConfigs",
                "agentCoreGateways", "policyEngines", "configBundles", "abTests", "harnesses", "datasets", "payments"):
        spec[key] = []
    write_json(output / "agentcore" / "agentcore.json", spec)
    write_json(output / "agentcore" / "aws-targets.json",
               [{"name": "default", "account": account, "region": region}] if account else [])
    write_json(output / "player-map.json",
               [{"playerId": pid, "runtimeName": name, "projectName": project_name} for pid, name in PLAYERS])
    # This generated helper runs only when the human explicitly invokes it.
    (output / "list_arns.py").write_text(ARN_HELPER, encoding="utf-8")
    (output / "DEPLOY.txt").write_text(
        "This directory was built locally. Nothing has been deployed.\n\n"
        "Prerequisites: Python 3.12, Node.js 20+, uv, AWS CLI, npm @aws/agentcore >=0.25.0, aws-cdk.\n"
        "Use the workshop's temporary credentials and provisioned permissions.\n"
        "Install CLI tools: npm install -g @aws/agentcore aws-cdk\n"
        "Verify that `agentcore --version` is the npm CLI >=0.25.0.\n"
        + ("Before deploying, rerun build_agents.py with --account YOUR_12_DIGIT_ACCOUNT.\n" if not account else "")
        + "From this directory:\n"
        "  npm --prefix agentcore/cdk ci\n"
        "  npm --prefix agentcore/cdk run build\n"
        f"  cdk bootstrap aws://{account or 'YOUR_12_DIGIT_ACCOUNT'}/{region}\n"
        "Skip bootstrap when the event already provisioned CDKToolkit.\n"
        f"  # Set AWS_DEFAULT_REGION={region} in your shell.\n"
        "  agentcore deploy --yes\n"
        f"  python list_arns.py --region {region}\n\n"
        "Register all five Runtime ARNs in player-map.json order and run portal fitness tests.\n"
        "If the match server calls across accounts, use the organizer's exact IAM role and\n"
        "configure access for both runtime and endpoint; see PROVENANCE.md.\n"
        "Do not deploy during a match.\n", encoding="utf-8")
    return output


ARN_HELPER = '''#!/usr/bin/env python3
"""Read the five deployed Runtime ARNs; performs one explicit read-only AWS CLI call."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--region', required=True)
    args = p.parse_args()
    aws = shutil.which('aws')
    if not aws:
        raise SystemExit('AWS CLI is not on PATH.')
    result = subprocess.run([aws, 'bedrock-agentcore-control', 'list-agent-runtimes',
                             '--region', args.region, '--output', 'json'],
                            check=True, capture_output=True, text=True)
    runtimes = json.loads(result.stdout).get('agentRuntimes', [])
    mapping = json.loads((Path(__file__).parent / 'player-map.json').read_text(encoding='utf-8'))
    missing = False
    for player in mapping:
        name = player['runtimeName']
        accepted = {name, player['projectName'] + '_' + name}
        matches = [r for r in runtimes if r.get('agentRuntimeName') in accepted]
        if len(matches) != 1:
            missing = True
            print(f"Player {player['playerId']} ({name}): expected one runtime, found {len(matches)}; inspect AgentCore console.")
        else:
            print(f"Player {player['playerId']} ({name}): {matches[0]['agentRuntimeArn']}")
    if missing:
        print('Available runtime names: ' + ', '.join(r.get('agentRuntimeName', '?') for r in runtimes))
        raise SystemExit(1)

if __name__ == '__main__':
    main()
'''


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=root)
    parser.add_argument("--output", type=Path, default=root / "deployment" / "build")
    parser.add_argument("--account", help="AWS account ID only; no credentials required for the build")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1")
    parser.add_argument("--model", help="Optional exact Bedrock model/inference-profile ID; baked into copied settings")
    parser.add_argument("--project-name", default="BakuFC")
    args = parser.parse_args()
    try:
        location = build(args.source, args.output, args.account, args.region, args.model, args.project_name)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(f"Built five runtimes locally: {location}")
    print(f"Manual deployment instructions: {location / 'DEPLOY.txt'}")


if __name__ == "__main__":
    main()
