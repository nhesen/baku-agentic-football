"""Configuration has no AWS calls and works without third-party dependencies."""
from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    model_id: str = "amazon.nova-micro-v1:0"
    region: str = "us-east-1"
    model_budget_ms: int = 320
    connect_timeout_s: float = 0.2
    read_timeout_s: float = 0.35
    pitch_half_length: float = 55.0
    pitch_half_width: float = 35.0
    goal_half_width: float = 3.66
    shot_max_distance: float = 24.0
    holder_max_distance: float = 4.0
    holder_separation: float = 1.0
    match_seconds: float = 0.0  # unknown until workshop confirms 120 vs 300
    profile: str = "balanced"
    pass_type: str = "GROUND"
    use_llm: bool = True
    advanced_commands: bool = True
    use_pass_model: bool = False
    pass_model_weight: float = 8.0
    experimental_tactics: bool = False
    offside_control: bool = True
    scheme: str = "diamond"
    track_transitions: bool = False
    early_shot: bool = False
    release_anchor: bool = False
    minimal_passing: bool = False
    prefer_center: bool = False
    phase_tactics: str = "off"
    combination_tactics: str = "off"
    formation: str = "original"

    def __post_init__(self):
        if self.combination_tactics not in {"off", "triangles", "give_go", "screen", "combined"}:
            raise ValueError("unknown combination tactics")
        if self.phase_tactics not in {"off", "attack", "compact", "trigger", "high", "complete", "wide", "pivot"}:
            raise ValueError("unknown phase tactics")
        if self.formation not in {"original", "1-2-1", "1-1-2", "2-1-1", "2-2", "1-1-1-1", "3-1", "1-3", "4-0"}:
            raise ValueError("formation must describe four outfield players")
        if any(type(v) is not bool for v in (self.track_transitions,self.early_shot,self.release_anchor,self.minimal_passing,self.prefer_center)):
            raise ValueError("track_transitions must be a boolean")
        if self.scheme not in {"legacy", "finish", "diamond", "pair", "chain", "flow", "direct"}:
            raise ValueError("unknown five-player scheme")
        if not isinstance(self.model_id, str) or not self.model_id.strip():
            raise ValueError("model_id must be a nonempty string")
        if not isinstance(self.region, str) or not self.region.strip():
            raise ValueError("region must be a nonempty string")
        for key in ("use_llm", "advanced_commands", "use_pass_model", "experimental_tactics", "offside_control"):
            if type(getattr(self, key)) is not bool:
                raise ValueError(f"{key} must be a JSON boolean")
        for key in ("pitch_half_length", "pitch_half_width", "goal_half_width",
                    "shot_max_distance", "holder_max_distance", "holder_separation",
                    "connect_timeout_s", "read_timeout_s", "pass_model_weight"):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 < value <= 10000:
                raise ValueError(f"{key} must be a finite positive number")
        if type(self.model_budget_ms) is not int or not 10 <= self.model_budget_ms <= 5000:
            raise ValueError("model_budget_ms must be 10..5000; include transport margin")
        if self.profile not in {"balanced", "protect", "press"}:
            raise ValueError("profile must be balanced, protect or press")
        if self.pass_type not in {"GROUND", "AERIAL", "THROUGH", "short", "long"}:
            raise ValueError("unknown PASS enum; use workshop's exact enum")
        if (isinstance(self.match_seconds, bool) or not isinstance(self.match_seconds, (int, float))
                or not math.isfinite(self.match_seconds) or not 0 <= self.match_seconds <= 86400):
            raise ValueError("match_seconds must be >= 0")
        if self.goal_half_width >= self.pitch_half_width:
            raise ValueError("goal_half_width must be smaller than pitch_half_width")


def load_settings(path: str | Path | None = None) -> Settings:
    source = Path(path) if path else Path(__file__).with_name("settings.json")
    data = json.loads(source.read_text(encoding="utf-8")) if source.exists() else {}
    unknown = set(data) - {f.name for f in fields(Settings)}
    if unknown:
        raise ValueError(f"Unknown settings: {sorted(unknown)}")
    env = {
        "BAKU_MODEL_ID": ("model_id", str), "BAKU_REGION": ("region", str),
        "BAKU_MODEL_BUDGET_MS": ("model_budget_ms", int),
        "BAKU_MATCH_SECONDS": ("match_seconds", float),
        "BAKU_PROFILE": ("profile", str), "BAKU_PASS_TYPE": ("pass_type", str),
        "BAKU_USE_LLM": ("use_llm", lambda x: x.lower() in {"1", "true", "yes"}),
    }
    for name, (key, convert) in env.items():
        if name in os.environ:
            data[key] = convert(os.environ[name])
    return Settings(**data)


def save_settings(cfg: Settings, path: str | Path):
    Path(path).write_text(json.dumps(asdict(cfg), indent=2) + "\n", encoding="utf-8")
