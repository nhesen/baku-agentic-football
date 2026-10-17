"""Offline injected-model checks: no SDK import, network, deployment or credentials."""
from __future__ import annotations

import copy
import json
import threading
import time
import unittest

from baku_fc.config import Settings
from baku_fc.engine import Engine
from test_adversarial import fixture


class InferenceAdversaries(unittest.TestCase):
    def engine(self, infer, budget=100):
        engine = Engine(default_pid=3, cfg=Settings(use_llm=True, model_budget_ms=budget), infer=infer)
        self.addCleanup(engine.close)
        return engine

    def choice_fixture(self):
        payload = fixture(pid=3)
        payload["gameState"]["ball"].update(
            isFree=False, possessionPlayerId=3, possessionTeamId=0,
            position={"x": 5, "y": 6})
        return payload

    def test_valid_choice_selects_current_menu(self):
        requests = []
        def infer(system, user):
            requests.append(json.loads(user))
            return '{"choice":0}'
        engine = self.engine(infer)
        result = engine.decide(self.choice_fixture())
        self.assertEqual(result["meta"]["source"], "model")
        self.assertEqual(result["commands"], [requests[0]["CANDIDATES"][0]])
        self.assertEqual(requests[0]["FACTS"]["player"], 3)

    def test_single_legal_candidate_skips_model(self):
        calls = []
        result = self.engine(lambda system, user: calls.append(user) or '{"choice":0}').decide(fixture(pid=0))
        self.assertEqual(result["meta"]["source"], "deterministic_singleton")
        self.assertEqual(calls, [])
        self.assertEqual(len(result["commands"]), 1)

    def test_model_exception_falls_back_without_losing_command(self):
        def infer(system, user):
            raise RuntimeError("injected unavailable model")
        result = self.engine(infer).decide(self.choice_fixture())
        self.assertEqual(result["meta"]["source"], "model_error:RuntimeError")
        self.assertEqual(len(result["commands"]), 1)
        self.assertEqual(result["commands"][0]["playerId"], 3)

    def test_invalid_choices_fall_back(self):
        for response in ('{"choice":true}', '{"choice":-1}', '{"choice":999}',
                         '{"choice":0.0}', '[]', 'not json'):
            with self.subTest(response=response):
                result = self.engine(lambda s, u, r=response: r).decide(self.choice_fixture())
                self.assertEqual(result["meta"]["source"], "invalid_model_output")
                self.assertEqual(len(result["commands"]), 1)

    def test_model_cannot_invent_a_valid_but_unlisted_move(self):
        raw = json.dumps({"commandType": "MOVE_TO", "playerId": 3, "teamId": 0,
                          "parameters": {"target_x": 54, "target_y": 34, "sprint": True}})
        result = self.engine(lambda s, u: raw).decide(self.choice_fixture())
        self.assertEqual(result["meta"]["source"], "invalid_model_output")
        self.assertNotEqual(result["commands"][0]["parameters"].get("target_y"), 34)

    def test_timeout_busy_and_late_result_do_not_queue_stale_work(self):
        release = threading.Event()
        calls = []
        calls_lock = threading.Lock()
        def infer(system, user):
            with calls_lock:
                calls.append(json.loads(user))
                sequence = len(calls)
            if sequence == 1:
                release.wait(2)
                return '{"choice":1}'
            return '{"choice":0}'
        engine = self.engine(infer, budget=10)
        try:
            first = self.choice_fixture()
            first["gameState"]["tick"] = 10
            started = time.perf_counter()
            result1 = engine.decide(first)
            self.assertEqual(result1["meta"]["source"], "timeout")
            self.assertLess(time.perf_counter() - started, 0.5)
            second = copy.deepcopy(first)
            second["gameState"]["tick"] = 11
            second["gameState"]["ball"]["position"] = {"x": 45, "y": 0}
            next(p for p in second["gameState"]["players"]
                 if p["teamCode"] == "home" and p["agentId"] == "agentId_3")["position"] = {"x": 45, "y": 0}
            result2 = engine.decide(second)
            self.assertEqual(result2["meta"]["source"], "busy")
            self.assertEqual(result2["meta"]["tick"], 11)
            self.assertNotEqual(result1["commands"], result2["commands"])
            self.assertEqual(len(calls), 1)
            release.set()
            # Wait only for the fake injected model; production never does this.
            engine._inflight.result(timeout=1)
            third = copy.deepcopy(second)
            third["gameState"]["tick"] = 12
            result3 = engine.decide(third)
            self.assertEqual(result3["meta"]["source"], "model")
            self.assertEqual(result3["meta"]["tick"], 12)
            self.assertEqual(len(calls), 2)
            self.assertEqual(result3["commands"], [calls[1]["CANDIDATES"][0]])
        finally:
            release.set()


if __name__ == "__main__":
    unittest.main()
