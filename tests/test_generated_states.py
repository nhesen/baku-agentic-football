"""Reproducible generated-state checks, not a football physics simulator."""
import json
import random
import unittest

from baku_fc.commands import validate
from baku_fc.config import Settings
from baku_fc.state import normalize
from baku_fc.tactics import plan


class GeneratedStateProperties(unittest.TestCase):
    def test_1000_mirrored_role_snapshots_have_finite_legal_fallbacks(self):
        rng = random.Random(17102026)
        cfg = Settings(use_llm=False)
        for n in range(100):
            players = [{"playerId": pid, "teamId": team,
                        "position": {"x": rng.uniform(-54, 54), "y": rng.uniform(-34, 34)},
                        "stamina": rng.random()} for team in (0, 1) for pid in range(5)]
            holder = rng.choice(players) if n % 3 else None
            ball = {"position": dict(holder["position"]) if holder else {"x": rng.uniform(-50, 50), "y": rng.uniform(-30, 30)},
                    "isFree": holder is None, "velocity": {"x": rng.uniform(-8, 8), "y": rng.uniform(-8, 8)}}
            if holder:
                ball.update(possessionPlayerId=holder["playerId"], possessionTeamId=holder["teamId"])
            gs = {"players": players, "ball": ball, "playMode": "OPEN_PLAY", "gameTime": 30}
            for team in (0, 1):
                for pid in range(5):
                    payload = {"teamId": team, "myPlayers": [pid], "gameState": gs}
                    w = normalize(payload, pid, cfg)
                    p = plan(w, cfg)
                    cmd = validate(p.fallback, w, p, cfg)
                    self.assertIsNotNone(cmd, (n, team, pid))
                    json.dumps(cmd, allow_nan=False)
                    self.assertEqual(cmd["teamId"], team)
                    self.assertEqual(cmd["playerId"], pid)
                    if cmd["commandType"] == "MOVE_TO":
                        if pid == 0:
                            self.assertLessEqual(cmd["parameters"]["target_x"] * w.sign, -43)
                        if pid == 1:
                            self.assertLessEqual(cmd["parameters"]["target_x"] * w.sign, -3)


if __name__ == "__main__":
    unittest.main()
