"""Normalize both public AWS payload generations without trusting player index alone."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

from .config import Settings


class ContractError(ValueError):
    """The payload cannot safely be associated with a side and a player."""


def finite(value: Any, default=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return float(value) if math.isfinite(value) else default


def team_number(value) -> int | None:
    if isinstance(value, bool):
        return None
    if value in (0, "0", "home", "HOME"):
        return 0
    if value in (1, "1", "away", "AWAY"):
        return 1
    return None


def player_index(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.rsplit("_", 1)[-1]
        if not value.isdecimal():
            return None
        value = int(value)
    return value if isinstance(value, int) and 0 <= value <= 4 else None


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def distance(self, other: Point) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


def point(raw) -> Point | None:
    if not isinstance(raw, dict):
        return None
    x, y = finite(raw.get("x")), finite(raw.get("y"))
    return Point(x, y) if x is not None and y is not None else None


@dataclass(frozen=True)
class Player:
    pid: int
    team: int
    pos: Point
    stamina: float = 1.0
    active: bool = True
    has_ball: bool | None = None
    agent_id: str = ""
    can_kick: bool = True  # Unknown cooldown retains the original AWS contract.

    @property
    def key(self):
        return self.team, self.pid


@dataclass(frozen=True)
class World:
    team: int
    pid: int
    players: tuple[Player, ...]
    ball: Point
    velocity: Point
    owner: tuple[int, int] | None
    status: str
    ownership_evidence: str
    tick: float
    time: float
    remaining: float | None
    us: int
    them: int
    coach: tuple[str, ...]
    play_mode: str
    match_id: str
    restart_team: int | None = None
    restart_player: int | None = None
    offside_enabled: bool = False  # Activate only when the engine explicitly confirms it.
    our_pass_in_flight: bool = False
    loss_age: float | None = None
    gain_age: float | None = None
    center_aim_supported: bool = False
    last_passer: int | None = None
    pass_age: float | None = None

    @property
    def me(self):
        return next((p for p in self.players if p.key == (self.team, self.pid)), None)

    @property
    def mine(self):
        return tuple(p for p in self.players if p.team == self.team and p.active)

    @property
    def opponents(self):
        return tuple(p for p in self.players if p.team != self.team and p.active)

    @property
    def sign(self):
        return 1 if self.team == 0 else -1


def _resolve_owner(ball: dict, players: list[Player], cfg: Settings):
    # Explicit free-ball wins over a stale holder field.
    if ball.get("isFree") is True:
        return None, "LOOSE", "isFree"
    declared = [p for p in players if p.has_ball is True and p.active]
    if len(declared) > 1:
        return None, "UNKNOWN", "conflicting_hasBall"
    aid = ball.get("possessionAgentId")
    idx = player_index(aid if aid is not None else ball.get("possessionPlayerId"))
    side = team_number(ball.get("possessionTeamId", ball.get("possessionTeamCode", ball.get("possessionTeam"))))
    if len(declared) == 1:
        if idx is not None and (declared[0].pid != idx or (side is not None and declared[0].team != side)):
            return None, "UNKNOWN", "conflicting_ownership_evidence"
        return declared[0].key, "HELD", "hasBall"
    if idx is not None and side is not None:
        holder = next((p for p in players if p.key == (side, idx) and p.active), None)
        return (holder.key, "HELD", "explicit_team") if holder else (None, "UNKNOWN", "holder_missing")
    if idx is not None:
        candidates = [p for p in players if p.pid == idx and p.active]
        # Some deployments use globally unique IDs, others repeat agentId_0..4.
        exact = [p for p in candidates if aid is not None and p.agent_id == str(aid)]
        if len(exact) == 1:
            return exact[0].key, "HELD", "unique_agent_id"
        b = point(ball.get("position"))
        if b:
            ranked = sorted(candidates, key=lambda p: p.pos.distance(b))
            if ranked and ranked[0].pos.distance(b) <= cfg.holder_max_distance:
                separation = ranked[1].pos.distance(b) - ranked[0].pos.distance(b) if len(ranked) > 1 else float("inf")
                if separation >= cfg.holder_separation:
                    return ranked[0].key, "HELD", "geometry_inferred"
        return None, "UNKNOWN", "ambiguous_agent_id"
    if ball.get("isFree") is False:
        return None, "UNKNOWN", "held_without_identity"
    if ("possessionAgentId" in ball and ball["possessionAgentId"] is None) or (
            "possessionPlayerId" in ball and ball["possessionPlayerId"] is None):
        return None, "LOOSE", "explicit_null_holder"
    # No ownership field is not evidence that a player has the ball.
    return None, "LOOSE" if ball.get("isFree") is True else "UNKNOWN", "missing_ownership"


def normalize(payload: dict, default_pid: int = 0, cfg: Settings | None = None) -> World:
    cfg = cfg or Settings()
    if not isinstance(payload, dict):
        raise ContractError("payload must be an object")
    data = payload.get("prompt", payload)
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (ValueError, TypeError) as exc:
            raise ContractError("prompt is not valid JSON") from exc
    if not isinstance(data, dict) or not isinstance(data.get("gameState"), dict):
        raise ContractError("gameState object is required")
    team = team_number(data.get("teamId", data.get("teamCode")))
    if team is None:
        raise ContractError("teamId must identify home(0) or away(1)")
    raw_ids = data.get("myPlayers", [default_pid])
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ContractError("myPlayers must be a nonempty list")
    ids = [player_index(i) for i in raw_ids]
    if any(i is None for i in ids):
        raise ContractError("myPlayers must contain player indexes 0..4")
    pid = ids[0] if len(ids) == 1 else default_pid if default_pid in ids else ids[0]
    gs = data["gameState"]
    ball = gs.get("ball")
    if not isinstance(ball, dict) or point(ball.get("position")) is None:
        raise ContractError("finite ball x/y coordinates are required")
    bp = point(ball["position"])
    if abs(bp.x) > cfg.pitch_half_length * 4 or abs(bp.y) > cfg.pitch_half_width * 4:
        raise ContractError("ball coordinates incompatible with configured pitch")
    bv = point(ball.get("velocity")) or Point(0, 0)
    if abs(bv.x) > 1000 or abs(bv.y) > 1000:
        raise ContractError("ball velocity outside supported physical range")
    players, seen = [], set()
    for raw in gs.get("players", []) if isinstance(gs.get("players"), list) else []:
        if not isinstance(raw, dict):
            continue
        pi = player_index(raw.get("agentId", raw.get("playerId")))
        pt = team_number(raw.get("teamCode", raw.get("teamId")))
        pos = point(raw.get("position"))
        if pi is None or pt is None or pos is None:
            continue
        if abs(pos.x) > cfg.pitch_half_length * 4 or abs(pos.y) > cfg.pitch_half_width * 4:
            raise ContractError("player coordinates incompatible with configured pitch")
        if (pt, pi) in seen:
            raise ContractError("duplicate player identity within a team")
        seen.add((pt, pi))
        stamina = finite(raw.get("stamina"), 1.0)
        stamina = min(1.0, max(0.0, stamina / 100.0 if stamina > 1.0 else stamina))
        active = not (raw.get("isEjected") is True or raw.get("redCard") is True
                      or finite(raw.get("redCards"), 0) > 0 or raw.get("active") is False)
        players.append(Player(pi, pt, pos, stamina, active,
                              raw.get("hasBall") if isinstance(raw.get("hasBall"), bool) else None,
                              str(raw.get("agentId", "")), raw.get("canKick") is not False))
    owner, status, evidence = _resolve_owner(ball, players, cfg)
    if owner:
        status = "ME" if owner == (team, pid) else "TEAM" if owner[0] == team else "OPP"
    score = gs.get("score", {})
    score = score if isinstance(score, dict) else {}
    home, away = max(0, int(finite(score.get("home"), 0))), max(0, int(finite(score.get("away"), 0)))
    time = max(0.0, finite(gs.get("gameTime"), 0))
    remaining = finite(gs.get("timeRemaining"))
    duration = finite(gs.get("matchDuration"), cfg.match_seconds)
    if remaining is None and duration > 0:
        remaining = max(0.0, duration - time)
    chat = []
    raw_chat = gs.get("teamChat", [])
    for item in raw_chat[-3:] if isinstance(raw_chat, list) else []:
        if isinstance(item, dict):
            side = team_number(item.get("teamCode", item.get("teamId")))
            if side is not None and side != team:
                continue
            item = item.get("message", item.get("text", item.get("content", "")))
        if isinstance(item, str) and item.strip():
            chat.append(item.strip()[:200])
    return World(team, pid, tuple(players), point(ball["position"]),
                 bv, owner, status, evidence,
                 finite(gs.get("tick"), 0), time, remaining,
                 home if team == 0 else away, away if team == 0 else home,
                 tuple(chat), str(gs.get("playMode", "UNKNOWN")), str(gs.get("matchId", "")),
                 team_number(gs.get("modeTeamId", gs.get("restartTeamId"))),
                 player_index(gs.get("restartPlayerId")),
                 isinstance(gs.get("rules"), dict) and gs["rules"].get("offsideEnabled") is True,
                 center_aim_supported=isinstance(gs.get("rules"),dict) and gs['rules'].get('centerAimSupported') is True)
