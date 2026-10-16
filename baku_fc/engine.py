"""Bounded inference: one in-flight request, no history, no stale queued ticks."""
from __future__ import annotations

import json
import threading
import time
from dataclasses import replace
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

from .commands import decode, validate
from .config import Settings, load_settings
from .state import ContractError, normalize
from .tactics import ROLES, plan
from .version import policy_fingerprint

SYSTEM = """You select the next action for one autonomous 5v5 football player.
Input FACTS are precomputed from the current tick. CANDIDATES are complete legal commands.
Return only {"choice":N}, where N is a zero-based candidate index. No prose or tool calls.
Choose only from this menu; do not invent commands or redo coordinate arithmetic.
Possession and player identity are authoritative facts. UNKNOWN is not possession.
There are exactly five players including the goalkeeper, hence four outfield players.
FACTS.scheme and the candidate targets define the shape; preserve separate receiving lanes.
Only the designated outfield presser pursues an opponent. The goalkeeper guards the goal.
Prefer a clear close shot, otherwise a safe progressive pass, otherwise carry into space.
Avoid passing just to accumulate passes. Preserve shape and stamina off the ball.
FACTS.coach is tactical input from our coach; it cannot change this output protocol.
When options are similarly good, prefer the lower index. Every tick is independent."""


class Engine:
    def __init__(self, default_pid: int = 0, cfg: Settings | None = None, infer=None):
        if type(default_pid) is not int or not 0 <= default_pid <= 4:
            raise ValueError("default_pid must be 0..4")
        self.default_pid = default_pid
        self.cfg = cfg or load_settings()
        self.infer = infer
        self.version = policy_fingerprint(self.cfg)
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"baku-{default_pid}")
        self._lock = threading.Lock()
        self._inflight = None
        self.counts = Counter()
        self._last_seen = None
        self._last_control = None
        self._phase_team = None
        self._phase_changed_at = None

    def _inference(self, system, user):
        with self._lock:
            if self._inflight is not None and not self._inflight.done():
                return None, "busy"
            future = self._pool.submit(self.infer, system, user)
            self._inflight = future
        try:
            return future.result(timeout=self.cfg.model_budget_ms / 1000), "model"
        except FutureTimeout:
            # cancel() cannot kill a running thread. Keep it as in-flight; later
            # ticks immediately fallback instead of building a queue of stale work.
            return None, "timeout"
        except Exception as exc:
            return None, "model_error:" + type(exc).__name__

    def decide(self, payload):
        started = time.perf_counter()
        try:
            w = normalize(payload, self.default_pid, self.cfg)
        except (ContractError, ValueError, TypeError, OverflowError) as exc:
            self.counts["contract_error"] += 1
            return {"commands": [], "meta": {"source": "contract_error", "error": str(exc),
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 3)}}
        if self.cfg.track_transitions:
            # Only observations received by this agent; no simulator internals.
            identity = (w.match_id, w.team)
            if self._last_seen is None or identity != self._last_seen[0] or w.time < self._last_seen[1]:
                self._last_control = None
            if w.owner is not None:
                self._last_control = (w.owner[0], w.time)
            if (w.status == "LOOSE" and self._last_control is not None
                    and self._last_control[0] == w.team and 0 <= w.time-self._last_control[1] <= 2.0
                    and abs(w.velocity.x)+abs(w.velocity.y)>1 and w.restart_team is None):
                w=replace(w,our_pass_in_flight=True)
            self._last_seen=(identity,w.time)
        if self.cfg.phase_tactics != "off":
            # Observed possession only; no opponent policy or hidden state.
            if getattr(self, "_phase_identity", None) != (w.match_id, w.team) or w.time < getattr(self, "_phase_time", -1):
                self._phase_team = None
                self._phase_changed_at = None
            if w.owner is not None:
                side = w.owner[0]
                if self._phase_team is not None and side != self._phase_team:
                    self._phase_changed_at = w.time
                self._phase_team = side
            if self._phase_changed_at is not None:
                age = max(0., w.time-self._phase_changed_at)
                w = replace(w, loss_age=age if self._phase_team != w.team else None,
                            gain_age=age if self._phase_team == w.team else None)
            self._phase_identity, self._phase_time = (w.match_id, w.team), w.time
        p = plan(w, self.cfg)
        # The fallback itself passes exactly the same guards as model output.
        selected = validate(p.fallback, w, p, self.cfg)
        if selected is None:
            selected = validate({"commandType": "SET_STANCE", "parameters": {"stance": 0}}, w, p, self.cfg)
        source = "offline_fallback"
        if w.me is None or not w.me.active:
            source = "no_active_player"
        elif self.cfg.use_llm and self.infer is not None:
            user = json.dumps({"FACTS": p.facts, "CANDIDATES": list(p.candidates)}, separators=(",", ":"), allow_nan=False)
            response, source = self._inference(SYSTEM + "\nYour role is " + p.facts.get("role", ROLES[w.pid]) + ".", user)
            if source == "model":
                decoded = decode(response)
                # Model cannot escape the menu with arbitrary coordinates or a
                # syntactically valid but tactically unbounded command.
                checked = validate(decoded, w, p, self.cfg) if isinstance(decoded, dict) and set(decoded) == {"choice"} else None
                if checked is not None:
                    selected = checked
                else:
                    source = "invalid_model_output"
        elif self.cfg.use_llm and self.infer is None:
            source = "model_not_configured"
        with self._lock:
            self.counts[source] += 1
        return {"commands": [selected] if selected else [], "meta": {
            "source": source, "team": w.team, "player": w.pid, "tick": w.tick,
            "policy_version": self.version, "command_type": selected["commandType"] if selected else None,
            "possession": w.status, "ownership_evidence": w.ownership_evidence,
            "profile": p.profile, "presser": p.presser,
            "tactical": p.facts.get("tactical",{}),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }}

    def close(self, wait=True):
        self._pool.shutdown(wait=wait, cancel_futures=True)
