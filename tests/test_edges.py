"""Contract/version edge cases from independent code review."""
import unittest
from dataclasses import replace

from baku_fc.config import Settings
from baku_fc.engine import Engine
from test_adversarial import fixture, _player


class ReviewRegressions(unittest.TestCase):
    def decide(self, payload):
        engine = Engine(4, Settings(use_llm=False))
        self.addCleanup(engine.close)
        return engine.decide(payload)

    def test_known_stopped_phases_do_not_shoot_or_press_stale_ball(self):
        for phase in ("KickOff", "GoalReplay", "GameOver", "Paused", "BeforeKickOff", "FULL_TIME"):
            p = fixture(4)
            p["gameState"]["playMode"] = phase
            p["gameState"]["ball"].update(isFree=False, possessionAgentId="agentId_4", possessionTeamId=0)
            _player(p, 0, 4)["position"] = {"x": 44, "y": 0}
            p["gameState"]["ball"]["position"] = {"x": 44, "y": 0}
            with self.subTest(phase=phase):
                r = self.decide(p)
                self.assertEqual(r["commands"][0]["commandType"], "MOVE_TO")

    def test_finite_but_physically_absurd_coordinates_do_not_overflow(self):
        p = fixture(4)
        _player(p, 0, 4)["position"] = {"x": 1.7e308, "y": -1.7e308}
        r = self.decide(p)
        self.assertEqual(r["meta"]["source"], "contract_error")
        self.assertEqual(r["commands"], [])

    def test_boolean_settings_require_booleans(self):
        for key in ("use_llm", "advanced_commands"):
            for value in ("false", 0, 1, None):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    Settings(**{key: value})

    def test_multi_player_request_keeps_each_runtime_slot(self):
        p = fixture(4)
        p["myPlayers"] = [0, 1, 2, 3, 4]
        r = self.decide(p)
        self.assertEqual(r["commands"][0]["playerId"], 4)

    def test_late_game_switch_requires_explicit_duration(self):
        from baku_fc.state import normalize
        from baku_fc.tactics import plan
        p = fixture(4)
        p["gameState"].update(gameTime=119, score={"home": 1, "away": 0})
        cfg = Settings(use_llm=False)
        self.assertEqual(plan(normalize(p, 4, cfg), cfg).profile, "balanced")
        known = replace(cfg, match_seconds=120)
        self.assertEqual(plan(normalize(p, 4, known), known).profile, "protect")


if __name__ == "__main__":
    unittest.main()
