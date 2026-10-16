"""Optional, auditable pass-retention estimator; no external runtime dependencies."""
import json
import math
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def model():
    path = Path(__file__).with_name("pass_model.json")
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("feature_version") != 1 or len(value.get("weights", [])) != 8:
        raise ValueError("unsupported pass model")
    return value


def retention(features):
    artifact = model()
    if artifact is None:
        return None
    z = artifact["weights"][0] + sum(w*x for w,x in zip(artifact["weights"][1:],features))
    return 1 / (1 + math.exp(-max(-35, min(35,z))))
