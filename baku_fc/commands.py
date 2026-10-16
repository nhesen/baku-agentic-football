"""Parse model responses as data and apply independent state-aware guards."""
from __future__ import annotations

import json
import re

from .config import Settings
from .state import World, finite, player_index
from .tactics import Plan, clamp, stopped_phase
from .formations import anchor_id

CORE = {"MOVE_TO", "PASS", "SHOOT", "PRESS_BALL", "SET_STANCE"}
ADVANCED = {"GK_DISTRIBUTE", "MARK", "INTERCEPT"}


def decode(text):
    if isinstance(text, (dict, list)):
        return text
    if not isinstance(text, str) or len(text) > 12000:
        return None
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    decoder = json.JSONDecoder(parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    try:
        return decoder.decode(cleaned)
    except (ValueError, TypeError):
        # Recover one JSON object/array from surrounding prose without eval or
        # rewriting literals inside strings. Malformed Python text is rejected.
        for i, ch in enumerate(cleaned):
            if ch not in "[{":
                continue
            try:
                value, _ = decoder.raw_decode(cleaned, i)
                return value
            except (ValueError, TypeError):
                pass
    return None


def validate(raw, w: World, p: Plan, cfg: Settings) -> dict | None:
    if isinstance(raw, list):
        if len(raw) != 1:
            return None
        raw = raw[0]
    if not isinstance(raw, dict):
        return None
    if "choice" in raw:
        idx = raw["choice"]
        if isinstance(idx, bool) or not isinstance(idx, int) or not 0 <= idx < len(p.candidates):
            return None
        return validate(p.candidates[idx], w, p, cfg)
    kind = raw.get("commandType")
    if not isinstance(kind, str) or kind not in CORE | (ADVANCED if cfg.advanced_commands else set()):
        return None
    supplied_pid = player_index(raw.get("playerId", w.pid))
    if supplied_pid != w.pid or raw.get("teamId", w.team) != w.team:
        return None
    params = raw.get("parameters", {})
    if not isinstance(params, dict):
        return None
    params = dict(params)
    # Repair the documented small-model error of flat parameter placement.
    for name in ("target_x", "target_y", "sprint", "target_player_id", "type",
                 "aim_location", "power", "intensity", "method", "tightness", "stance", "aggressive"):
        if name in raw:
            params[name] = raw[name]
    if kind in {"PASS", "SHOOT", "GK_DISTRIBUTE"} and w.status != "ME":
        return None
    if kind in {"PASS", "SHOOT", "GK_DISTRIBUTE"} and w.me and not w.me.can_kick:
        return None
    if stopped_phase(w) and kind in {"PASS", "SHOOT", "GK_DISTRIBUTE", "PRESS_BALL", "INTERCEPT", "MARK"}:
        if kind != "PASS" or w.restart_team != w.team:
            return None
    if kind == "MOVE_TO":
        x, y = finite(params.get("target_x")), finite(params.get("target_y"))
        if x is None or y is None:
            return None
        x, y = clamp(x, -cfg.pitch_half_length + 0.5, cfg.pitch_half_length - 0.5), clamp(y, -cfg.pitch_half_width + 0.5, cfg.pitch_half_width - 0.5)
        if w.pid == 0:
            x = w.sign * clamp(x * w.sign, -cfg.pitch_half_length + 0.5, -cfg.pitch_half_length + 12)
            y = clamp(y, -cfg.goal_half_width * 0.9, cfg.goal_half_width * 0.9)
        if w.pid == anchor_id(w,cfg) and not (cfg.release_anchor and w.status == "ME") and cfg.formation != "4-0":
            x = w.sign * min(x * w.sign, -3)
        params = {"target_x": round(x, 2), "target_y": round(y, 2),
                  "sprint": params.get("sprint") is True and bool(w.me and w.me.stamina >= 0.35)}
    elif kind in {"PASS", "GK_DISTRIBUTE"}:
        target = player_index(params.get("target_player_id"))
        if target == w.pid or target not in p.pass_targets:
            return None
        if kind == "GK_DISTRIBUTE":
            if w.pid != 0 or not isinstance(params.get("method", "THROW"), str) or params.get("method", "THROW") not in {"THROW", "KICK"}:
                return None
            params = {"target_player_id": target, "method": params.get("method", "THROW")}
        else:
            if params.get("type", cfg.pass_type) != cfg.pass_type:
                return None
            params = {"target_player_id": target, "type": cfg.pass_type}
    elif kind == "SHOOT":
        power = finite(params.get("power"))
        aim = params.get("aim_location")
        aims = {"TL", "TR", "BL", "BR"} | ({"CENTER"} if w.center_aim_supported else set())
        if not p.shot_allowed or power is None or not isinstance(aim, str) or aim not in aims:
            return None
        params = {"aim_location": aim, "power": clamp(power, 0.1, 1.0)}
    elif kind == "PRESS_BALL":
        intensity = finite(params.get("intensity"))
        if (w.pid == 0 or p.presser != w.pid or w.status != "OPP" or intensity is None
                or not w.me or w.me.pos.distance(w.ball) > 16 * cfg.pitch_half_length / 55):
            return None
        params = {"intensity": clamp(intensity, 0.1, 1.0)}
    elif kind == "INTERCEPT":
        if w.pid == 0 or p.presser != w.pid or w.status not in {"LOOSE", "OPP"}:
            return None
        params = {"aggressive": False}
    elif kind == "MARK":
        target = player_index(params.get("target_player_id"))
        if w.pid == 0 or target not in [o.pid for o in w.opponents] or w.status in {"ME", "TEAM"}:
            return None
        if not isinstance(params.get("tightness", "LOOSE"), str) or params.get("tightness", "LOOSE") not in {"TIGHT", "LOOSE"}:
            return None
        params = {"target_player_id": target, "tightness": params.get("tightness", "LOOSE")}
    else:
        if type(params.get("stance")) is not int or params["stance"] != 0:
            return None
        params = {"stance": 0}
    return {"commandType": kind, "playerId": w.pid, "teamId": w.team,
            "parameters": params, "duration": 1 if kind in {"PRESS_BALL", "MARK", "INTERCEPT"} else 0}
