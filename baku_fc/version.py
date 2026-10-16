"""Fingerprint code plus effective settings; includes no account credentials."""
import hashlib
import json
from dataclasses import asdict
from pathlib import Path


def policy_fingerprint(cfg):
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    if getattr(cfg, "use_pass_model", False):
        artifact = Path(__file__).with_name("pass_model.json")
        digest.update(b"pass_model.json")
        digest.update(artifact.read_bytes() if artifact.exists() else b"missing")
    digest.update(json.dumps(asdict(cfg), sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()[:16]
