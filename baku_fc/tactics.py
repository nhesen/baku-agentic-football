"""Geometric facts, legal candidate menu and a fresh emergency policy per tick.

Heuristics are a proposed baseline, not a reproduction of any champion's code.
All x constraints use attack-relative u; commands use the actual pitch x.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .config import Settings
from .state import Player, Point, World
from .learned import retention

ROLES = ("goalkeeper", "anchor", "pivot_left", "pivot_right", "striker")


def stopped_phase(w: World):
    mode = w.play_mode.lower().replace("_", "").replace(" ", "")
    return mode in {"kickoff", "beforekickoff", "aftergoal", "goal", "halftime", "fulltime",
                    "paused", "outofplay", "throwin", "cornerkick", "goalkick", "freekick",
                    "penalty", "penaltykick", "finished", "goalreplay", "gameover", "ended", "restart"}


def clamp(value, low, high):
    return max(low, min(high, value))


def command(w: World, kind: str, params: dict, duration: int = 0):
    return {"commandType": kind, "playerId": w.pid, "teamId": w.team,
            "parameters": params, "duration": duration}


def move(w: World, target: Point, sprint=False):
    return command(w, "MOVE_TO", {"target_x": round(target.x, 2), "target_y": round(target.y, 2), "sprint": bool(sprint)})


def segment_clearance(start: Point, end: Point, opponents: tuple[Player, ...], exclude_gk=False):
    dx, dy = end.x - start.x, end.y - start.y
    length2 = dx * dx + dy * dy
    clearance = 100.0
    for p in opponents:
        if exclude_gk and p.pid == 0:
            continue
        t = clamp(((p.pos.x - start.x) * dx + (p.pos.y - start.y) * dy) / length2, 0.0, 1.0) if length2 else 0.0
        nearest = Point(start.x + t * dx, start.y + t * dy)
        clearance = min(clearance, p.pos.distance(nearest))
    return clearance


@dataclass(frozen=True)
class Plan:
    fallback: dict
    candidates: tuple[dict, ...]
    facts: dict
    presser: int | None
    pass_targets: tuple[int, ...]
    shot_allowed: bool
    target: Point
    profile: str


def profile_for(w: World, cfg: Settings):
    # Do not guess late-game status from conflicting 2/5-minute documentation.
    if w.remaining is not None and w.remaining <= 25:
        if w.us > w.them:
            return "protect"
        if w.us < w.them:
            return "press"
    # Only accept exact own-coach control tokens, not arbitrary chat substrings.
    for text in reversed(w.coach):
        if text.strip().upper() in {"BAKU:PROTECT", "BAKU:BALANCED", "BAKU:PRESS"}:
            return text.strip().split(":")[-1].lower()
    return cfg.profile


def formation_target(w: World, cfg: Settings, profile: str):
    h, width, s = cfg.pitch_half_length, cfg.pitch_half_width, w.sign
    u, y = w.ball.x * s, w.ball.y
    scale = h / 55.0
    if w.pid == 0:
        keeper_u = -h + 5 * scale
        # Intersect ball-to-own-goal line with the keeper's deep x line.
        ratio = clamp((keeper_u + h) / max(u + h, 1.0), 0, 1)
        keeper_y = clamp(y * ratio, -cfg.goal_half_width * 0.85, cfg.goal_half_width * 0.85)
        return Point(s * keeper_u, keeper_y)
    shift = -6 * scale if profile == "protect" else 4 * scale if profile == "press" else 0
    attacking = w.status in {"TEAM", "ME"}
    if w.pid == 1:
        # Anchor never vacates the middle or crosses halfway.
        tx = clamp(0.30 * u - 20 * scale + min(shift, 0), -39 * scale, -8 * scale)
        ty = clamp(y * 0.28, -10 * scale, 10 * scale)
    elif w.pid in (2, 3):
        lane = -1 if w.pid == 2 else 1
        bias = -7 if w.pid == 2 else 3
        tx = clamp(u * 0.50 + (bias + (7 if attacking else -3)) * scale + shift,
                   -28 * scale, (26 if w.pid == 2 else 34) * scale)
        ty = lane * 10 * scale + y * 0.15
    else:
        tx = clamp(u + (17 if attacking else 12) * scale + shift, -4 * scale, h - 8 * scale)
        ty = clamp(-y * 0.25, -10 * scale, 10 * scale)
    if attacking and w.offside_enabled and cfg.offside_control and w.pid in (2, 3, 4):
        tx = min(tx, onside_limit(w, cfg) - 0.8 * scale)
    return Point(s * tx, clamp(ty, -width + 2, width - 2))


def designated_presser(w: World, cfg: Settings, profile: str):
    if w.status in {"ME", "TEAM"} or stopped_phase(w):
        return None
    h = cfg.pitch_half_length
    eligible = [p for p in w.mine if p.pid != 0 and
                (p.pid != 1 or (w.ball.x * w.sign < -h * 0.48 and p.pos.distance(w.ball) < h * 0.28))]
    if not eligible:
        return None
    # Stable ID tie-break gives all five independent runtimes the same decision.
    return min(eligible, key=lambda p: (p.pos.distance(w.ball), p.pid)).pid


def passing_options(w: World, cfg: Settings):
    if not w.me:
        return []
    options = []
    for p in w.mine:
        if p.pid == w.pid:
            continue
        distance = w.me.pos.distance(p.pos)
        if distance < 2.0 or distance > cfg.pitch_half_length * (2 if stopped_phase(w) else 1):
            continue
        progress = (p.pos.x - w.me.pos.x) * w.sign
        # A missed central back-pass must not have our goal behind its receiver.
        if progress < 0 and p.pos.x * w.sign < -cfg.pitch_half_length + 14 and abs(p.pos.y) < cfg.goal_half_width + 5:
            continue
        if w.offside_enabled and cfg.offside_control and p.pos.x * w.sign > onside_limit(w, cfg) + 0.05:
            continue
        clearance = segment_clearance(w.me.pos, p.pos, w.opponents)
        pressure = min((p.pos.distance(o.pos) for o in w.opponents), default=100.0)
        if clearance < 2.0 or pressure < 2.2:
            continue
        goal_gap = p.pos.distance(Point(w.sign * cfg.pitch_half_length, 0))
        score = (progress * 0.45 + min(clearance, 8) * 1.3 + min(pressure, 8) * 0.8
                 - distance * 0.12 + (4 if goal_gap < cfg.shot_max_distance else 0)
                 - (14 if p.pid == 0 else 0))
        probability = None
        if cfg.use_pass_model:
            features = [distance/(2*cfg.pitch_half_length), progress/(2*cfg.pitch_half_length),
                        min(clearance,10)/10, min(pressure,10)/10,
                        goal_gap/(2*cfg.pitch_half_length), float(p.pid==0), abs(p.pos.y)/cfg.pitch_half_width]
            probability = retention(features)
            if probability is not None:
                score += cfg.pass_model_weight * (probability - 0.5)
        options.append({"pid": p.pid, "score": round(score, 2), "distance": round(distance, 1),
                        "clearance": round(clearance, 1), "progress": round(progress, 1),
                        "predicted_retention": None if probability is None else round(probability,3)})
    return sorted(options, key=lambda o: (-o["score"], o["pid"]))


def onside_limit(w: World, cfg: Settings):
    defenders = sorted((p.pos.x * w.sign for p in w.opponents), reverse=True)
    line = defenders[1] if len(defenders) >= 2 else cfg.pitch_half_length
    return max(0.0, w.ball.x * w.sign, line)


def shot_facts(w: World, cfg: Settings):
    if not w.me:
        return False, {}, None
    target_x = w.sign * cfg.pitch_half_length
    distance = w.me.pos.distance(Point(target_x, 0))
    # Euclidean distance and real shooting angle, never x distance alone.
    allowed = (w.pid != 0 and w.status == "ME" and not stopped_phase(w) and distance <= cfg.shot_max_distance
               and abs(w.me.pos.y) <= cfg.pitch_half_width * 0.55)
    shot_y = cfg.goal_half_width * 0.75
    choices = []
    keeper = next((p for p in w.opponents if p.pid == 0), None)
    for aim, y in (("BL", -shot_y), ("BR", shot_y)):
        target = Point(target_x, y)
        clearance = segment_clearance(w.me.pos, target, w.opponents, exclude_gk=True)
        keeper_gap = abs(keeper.pos.y - y) if keeper else shot_y
        choices.append((min(clearance, 8) + keeper_gap * 0.4, aim, clearance))
    _, aim, lane = max(choices)
    if cfg.prefer_center and w.center_aim_supported:
        aim = "CENTER"
        lane = segment_clearance(w.me.pos, Point(target_x,0), w.opponents, exclude_gk=True)
    required_lane = None
    if cfg.finishing_tactics in {"shot", "balanced"}:
        # Geometric hypotheses, not calibrated xG. Keep clear long shots rather
        # than shortening the range that was useful in the V3/V5 experiments.
        required_lane = 1.0 if distance <= 13 else 1.8 if distance <= 22 else 2.5
        allowed = allowed and lane >= required_lane
    return allowed, {"required_clearance":required_lane,"distance": round(distance, 1), "field_player_clearance": round(lane, 1),
                     "aim": aim, "geometry_assumption_goal_half_width": cfg.goal_half_width}, aim


def plan(w: World, cfg: Settings) -> Plan:
    if cfg.scheme != "legacy":
        from .attack import plan_five
        return plan_five(w, cfg)
    mode = profile_for(w, cfg)
    target = formation_target(w, cfg, mode)
    presser = designated_presser(w, cfg, mode)
    me = w.me
    shot_allowed, shot, aim = shot_facts(w, cfg)
    passes = passing_options(w, cfg) if w.status == "ME" else []
    targets = tuple(p["pid"] for p in passes)
    candidates = []
    if me is None or not me.active:
        candidates = [command(w, "SET_STANCE", {"stance": 0})]
    elif w.status == "ME":
        if w.pid == 0:
            for p in passes[:3]:
                kind = "GK_DISTRIBUTE" if cfg.advanced_commands else "PASS"
                params = {"target_player_id": p["pid"]}
                params.update({"method": "THROW"} if cfg.advanced_commands else {"type": cfg.pass_type})
                candidates.append(command(w, kind, params))
            candidates.append(move(w, target))
        else:
            shoot = command(w, "SHOOT", {"aim_location": aim, "power": 0.88}) if shot_allowed else None
            threshold = 2.5 if cfg.experimental_tactics else 1.5
            if shoot and (shot["distance"] <= 12 or shot["field_player_clearance"] >= threshold):
                candidates.append(shoot)
            # MOVE_TO is the workshop's available way to carry the ball; DRIBBLE
            # belongs to another public simulator and is deliberately not emitted.
            max_u = -5 if w.pid == 1 else cfg.pitch_half_length - 7
            advance_u = max(me.pos.x * w.sign, min(me.pos.x * w.sign + 8, max_u))
            carry_options = [Point(w.sign * advance_u, clamp(me.pos.y + delta, -22, 22)) for delta in (0, -5, 5)]
            # Choose a short carrying corridor before asking the model to choose
            # between carrying, shooting and passes. This is not a physics model.
            advance = max(carry_options, key=lambda pt: segment_clearance(me.pos, pt, w.opponents))
            carry = move(w, advance, me.stamina > 0.55 and w.pid != 1)
            nearest_opp = min((me.pos.distance(o.pos) for o in w.opponents), default=100.0)
            progressive = [p for p in passes if p["progress"] >= 2]
            outlets = progressive or (passes if nearest_opp < 6 else [])
            if not outlets:
                candidates.append(carry)
            for p in (outlets if outlets else passes)[:3]:
                candidates.append(command(w, "PASS", {"target_player_id": p["pid"], "type": cfg.pass_type}))
            if carry not in candidates:
                candidates.append(carry)
            if shoot and shoot not in candidates:
                candidates.append(shoot)
    elif w.pid == 0:
        candidates.append(move(w, target))
        if cfg.experimental_tactics and w.status == "LOOSE" and w.ball.x * w.sign < -cfg.pitch_half_length + 11 and abs(w.ball.y) < 10:
            nearest = min(w.mine, key=lambda pl: (pl.pos.distance(w.ball), pl.pid))
            if nearest.pid == 0:
                candidates.insert(0, move(w, w.ball))
    elif presser == w.pid:
        if w.status == "OPP" and me.pos.distance(w.ball) <= 16 * cfg.pitch_half_length / 55:
            candidates.append(command(w, "PRESS_BALL", {"intensity": 0.9 if me.stamina >= 0.4 else 0.6}, 1))
        # Unknown ownership and loose ball require pursuit, not a fictitious kick.
        lookahead = 0.3
        bx = clamp(w.ball.x + w.velocity.x * lookahead, -cfg.pitch_half_length + 1, cfg.pitch_half_length - 1)
        by = clamp(w.ball.y + w.velocity.y * lookahead, -cfg.pitch_half_width + 1, cfg.pitch_half_width - 1)
        if w.pid == 1:
            bx = w.sign * min(bx * w.sign, -3)
        candidates.append(move(w, Point(bx, by), me.stamina > 0.4))
        candidates.append(move(w, target))
    else:
        candidates.append(move(w, target, me.stamina > 0.6 and me.pos.distance(target) > 14))
        # A second nearby support point permits model choice while preserving shape.
        alt = Point(target.x, clamp(target.y + (-3 if w.pid == 2 else 3), -28, 28))
        candidates.append(move(w, alt))
    facts = {
        "role": ROLES[w.pid], "team": w.team, "player": w.pid,
        "attack_direction": w.sign, "own_goal_x": -w.sign * cfg.pitch_half_length,
        "opponent_goal_x": w.sign * cfg.pitch_half_length,
        "possession": w.status, "ownership_evidence": w.ownership_evidence,
        "designated_presser": presser, "profile": mode, "score_us_them": [w.us, w.them],
        "remaining_seconds": w.remaining, "shot": shot, "passes": passes,
        "shape_target": [round(target.x, 1), round(target.y, 1)],
        "me": [me.pos.x, me.pos.y, me.stamina] if me else None,
        "ball": [w.ball.x, w.ball.y],
        "teammates": [[p.pid, p.pos.x, p.pos.y] for p in w.mine],
        "opponents": [[p.pid, p.pos.x, p.pos.y] for p in w.opponents],
        "coach": list(w.coach), "play_mode": w.play_mode,
        "restart_team": w.restart_team,
        "can_kick": me.can_kick if me else None, "offside_enabled": w.offside_enabled,
        "restart_player": w.restart_player,
    }
    if stopped_phase(w) and me and me.active:
        # On known stopped phases do not mistake stale possession for a shot.
        # Restart-taking requires explicit modeTeamId/restartTeamId evidence.
        candidates = [move(w, target)]
        if w.restart_team == w.team:
            outfield = [pl for pl in w.mine if pl.pid != 0]
            taker = min(outfield, key=lambda pl: (pl.pos.distance(w.ball), pl.pid)) if outfield else None
            if w.status == "ME" and passes and (w.restart_player is None or w.restart_player == w.pid):
                candidates.insert(0, command(w, "PASS", {"target_player_id": passes[0]["pid"], "type": cfg.pass_type}))
            elif taker and taker.pid == w.pid:
                candidates.insert(0, move(w, w.ball, False))
    if me and w.status == "ME" and not me.can_kick:
        # Native action cooldown blocks kicks, not movement. Under pressure
        # brace; when unmarked, continue carrying instead of repeating a kick.
        hold = command(w, "SET_STANCE", {"stance": 0})
        nearest = min((me.pos.distance(o.pos) for o in w.opponents), default=100)
        carries = [c for c in candidates if c["commandType"] == "MOVE_TO"]
        candidates = [hold] if not cfg.experimental_tactics or stopped_phase(w) or nearest < 3 or not carries else carries
    elif me and w.status == "ME" and stopped_phase(w) and w.restart_team == w.team:
        # Never dribble the restart taker while the engine requires a kick.
        kicks = [c for c in candidates if c["commandType"] == "PASS"]
        candidates = kicks or [command(w, "SET_STANCE", {"stance": 0})]
    return Plan(candidates[0], tuple(candidates), facts, presser, targets, shot_allowed, target, mode)
