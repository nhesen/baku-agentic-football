"""Independent possession/identity regressions derived from public match failures."""
from __future__ import annotations

import copy
import unittest

from baku_fc.config import Settings
from baku_fc.state import ContractError, normalize
from baku_fc.tactics import plan
from baku_fc.commands import validate


def fixture(pid=4, team=0):
    players = []
    for side in (0, 1):
        for player in range(5):
            players.append({
                "agentId": f"agentId_{player}",
                "teamCode": "home" if side == 0 else "away",
                "position": {"x": -40 + player * 15 if side == 0 else 40 - player * 15,
                             "y": (player - 2) * 6},
                "stamina": 1.0,
            })
    return {"teamId": team, "myPlayers": [pid], "gameState": {
        "tick": 7, "gameTime": 14, "score": {"home": 0, "away": 0},
        "ball": {"position": {"x": 20, "y": 12},
                 "velocity": {"x": 0, "y": 0}, "isFree": True},
        "players": players,
    }}


def _player(payload, team, pid):
    label = "home" if team == 0 else "away"
    return next(p for p in payload["gameState"]["players"]
                if p["teamCode"] == label and p["agentId"] == f"agentId_{pid}")


class IdentityAndPossessionAdversaries(unittest.TestCase):
    def test_same_index_opponent_possession_is_not_mine(self):
        payload = fixture()
        ball = payload["gameState"]["ball"]
        ball.pop("isFree")
        ball.update({"possessionAgentId": "agentId_4", "possessionTeamCode": "away"})
        ball["position"] = dict(_player(payload, 1, 4)["position"])
        world = normalize(payload)
        self.assertEqual(world.status, "OPP")
        self.assertEqual(world.owner, (1, 4))

    def test_ambiguous_identical_indexes_and_positions_are_unknown(self):
        payload = fixture()
        ball = payload["gameState"]["ball"]
        ball.pop("isFree")
        ball["possessionAgentId"] = "agentId_4"
        for team in (0, 1):
            _player(payload, team, 4)["position"] = {"x": 20, "y": 12}
        world = normalize(payload)
        self.assertEqual(world.status, "UNKNOWN")
        self.assertIsNone(world.owner)

    def test_conflicting_hasball_flags_cannot_enable_a_kick(self):
        payload = fixture()
        payload["gameState"]["ball"].pop("isFree")
        _player(payload, 0, 4)["hasBall"] = True
        _player(payload, 1, 4)["hasBall"] = True
        world = normalize(payload)
        self.assertEqual(world.status, "UNKNOWN")
        self.assertIsNone(world.owner)

    def test_explicit_owner_conflicting_with_single_hasball_is_unknown(self):
        payload = fixture()
        payload["gameState"]["ball"].pop("isFree")
        payload["gameState"]["ball"].update({
            "possessionAgentId": "agentId_4", "possessionTeamCode": "away",
        })
        _player(payload, 0, 4)["hasBall"] = True
        world = normalize(payload)
        self.assertEqual(world.status, "UNKNOWN")
        self.assertIsNone(world.owner)

    def test_explicit_free_clears_stale_hasball(self):
        payload = fixture()
        _player(payload, 0, 4)["hasBall"] = True
        self.assertEqual(normalize(payload).status, "LOOSE")

    def test_no_possession_metadata_is_not_possession(self):
        payload = fixture()
        payload["gameState"]["ball"].pop("isFree")
        self.assertEqual(normalize(payload).status, "UNKNOWN")

    def test_unknown_player_team_is_not_implicitly_opponent(self):
        payload = fixture()
        payload["gameState"]["players"].append({
            "agentId": "agentId_2", "position": {"x": 0, "y": 0},
        })
        world = normalize(payload)
        self.assertEqual(len(world.players), 10)

    def test_duplicate_identity_within_team_is_a_contract_error(self):
        payload = fixture()
        payload["gameState"]["players"].append(copy.deepcopy(_player(payload, 0, 4)))
        with self.assertRaises(ContractError):
            normalize(payload)

    def test_nan_ball_is_contract_error(self):
        payload = fixture()
        payload["gameState"]["ball"]["position"]["x"] = float("nan")
        with self.assertRaises(ContractError):
            normalize(payload)

    def test_fractional_and_percentage_stamina_normalize_equally(self):
        first, second = fixture(), fixture()
        _player(first, 0, 4)["stamina"] = 0.37
        _player(second, 0, 4)["stamina"] = 37
        self.assertAlmostEqual(normalize(first).me.stamina, normalize(second).me.stamina)

    def test_redcarded_player_removed_from_active_team(self):
        payload = fixture()
        _player(payload, 0, 2)["redCard"] = True
        self.assertNotIn(2, [p.pid for p in normalize(payload).mine])

    def test_old_payload_identifies_owner_by_team(self):
        payload = fixture(pid=2, team=1)
        players = payload["gameState"]["players"]
        for p in players:
            p["playerId"] = int(p.pop("agentId").rsplit("_", 1)[-1])
            p["teamId"] = 0 if p.pop("teamCode") == "home" else 1
        ball = payload["gameState"]["ball"]
        ball.pop("isFree")
        ball.update({"possessionPlayerId": 2, "possessionTeamId": 1})
        self.assertEqual(normalize(payload).status, "ME")

    def test_team_boolean_is_not_home(self):
        payload = fixture()
        payload["teamId"] = False
        with self.assertRaises(ContractError):
            normalize(payload)


class TacticalAdversaries(unittest.TestCase):
    cfg = Settings(use_llm=False)

    def opponent_owns(self, pid=4):
        payload = fixture(pid)
        ball = payload["gameState"]["ball"]
        ball.pop("isFree")
        ball.update({"possessionAgentId": "agentId_4", "possessionTeamCode": "away"})
        return payload

    def test_single_presser_selected_identically_by_all_controllers(self):
        payload = self.opponent_owns()
        selections = []
        commands = []
        for pid in range(5):
            payload["myPlayers"] = [pid]
            w = normalize(payload)
            p = plan(w, self.cfg)
            selections.append(p.presser)
            commands.append(p.fallback)
        self.assertEqual(len(set(selections)), 1)
        self.assertNotEqual(selections[0], 0)
        self.assertLessEqual(sum(c["commandType"] == "PRESS_BALL" for c in commands), 1)

    def test_keeper_never_chases_in_ordinary_press_pool(self):
        payload = self.opponent_owns(pid=0)
        _player(payload, 0, 0)["position"] = dict(payload["gameState"]["ball"]["position"])
        w = normalize(payload)
        p = plan(w, self.cfg)
        self.assertNotEqual(p.presser, 0)
        self.assertNotEqual(p.fallback["commandType"], "PRESS_BALL")

    def test_anchor_not_challenger_in_opponents_half(self):
        payload = self.opponent_owns(pid=1)
        _player(payload, 0, 1)["position"] = dict(payload["gameState"]["ball"]["position"])
        w = normalize(payload)
        self.assertNotEqual(plan(w, self.cfg).presser, 1)

    def test_teammate_possession_has_no_presser(self):
        payload = fixture(pid=2)
        payload["gameState"]["ball"].pop("isFree")
        _player(payload, 0, 4)["hasBall"] = True
        w = normalize(payload)
        p = plan(w, self.cfg)
        self.assertIsNone(p.presser)
        self.assertNotEqual(p.fallback["commandType"], "PRESS_BALL")

    def test_unknown_possession_forbids_every_kick(self):
        payload = fixture()
        payload["gameState"]["ball"].pop("isFree")
        w = normalize(payload)
        p = plan(w, self.cfg)
        for kind, params in (("PASS", {"target_player_id": 3, "type": "GROUND"}),
                             ("SHOOT", {"aim_location": "BL", "power": 0.9}),
                             ("GK_DISTRIBUTE", {"target_player_id": 3, "method": "THROW"})):
            with self.subTest(kind=kind):
                self.assertIsNone(validate({"commandType": kind, "parameters": params}, w, p, self.cfg))

    def test_distant_challenger_moves_instead_of_pressing(self):
        payload = self.opponent_owns(pid=4)
        payload["gameState"]["ball"]["position"] = {"x": 50, "y": 0}
        for pid in range(1, 5):
            _player(payload, 0, pid)["position"] = {"x": -30 + pid, "y": 0}
        w = normalize(payload)
        p = plan(w, self.cfg)
        self.assertEqual(p.presser, 4)
        self.assertEqual(p.fallback["commandType"], "MOVE_TO")

    def test_unconfirmed_center_aim_is_rejected(self):
        payload = fixture()
        payload["gameState"]["ball"].pop("isFree")
        _player(payload, 0, 4).update({"hasBall": True, "position": {"x": 45, "y": 0}})
        w = normalize(payload)
        p = plan(w, self.cfg)
        self.assertIsNone(validate({"commandType": "SHOOT", "parameters": {"aim_location": "CENTER", "power": 1}}, w, p, self.cfg))

    def test_touchline_x_only_shot_regression(self):
        payload = fixture()
        payload["gameState"]["ball"].pop("isFree")
        _player(payload, 0, 4).update({"hasBall": True, "position": {"x": 45, "y": 30}})
        w = normalize(payload)
        p = plan(w, self.cfg)
        self.assertFalse(p.shot_allowed)
        self.assertIsNone(validate({"commandType": "SHOOT", "parameters": {"aim_location": "BL", "power": 1}}, w, p, self.cfg))

    def test_home_away_mirroring_preserves_role_geometry(self):
        first = self.opponent_owns(pid=3)
        second = copy.deepcopy(first)
        second["teamId"] = 1
        second["gameState"]["ball"]["position"]["x"] *= -1
        second["gameState"]["ball"]["possessionTeamCode"] = "home"
        for player in second["gameState"]["players"]:
            player["position"]["x"] *= -1
            player["teamCode"] = "away" if player["teamCode"] == "home" else "home"
        left = plan(normalize(first), self.cfg)
        right = plan(normalize(second), self.cfg)
        self.assertEqual(left.presser, right.presser)
        self.assertEqual(left.fallback["commandType"], right.fallback["commandType"])
        self.assertAlmostEqual(left.target.x, -right.target.x)
        self.assertAlmostEqual(left.target.y, right.target.y)

    def test_all_fallbacks_pass_independent_validator(self):
        for pid in range(5):
            for status in ("LOOSE", "ME", "OPP", "UNKNOWN"):
                with self.subTest(pid=pid, status=status):
                    payload = fixture(pid)
                    if status != "LOOSE":
                        payload["gameState"]["ball"].pop("isFree")
                    if status == "ME":
                        _player(payload, 0, pid)["hasBall"] = True
                    elif status == "OPP":
                        payload["gameState"]["ball"].update({"possessionPlayerId": 2, "possessionTeamId": 1})
                    w = normalize(payload)
                    p = plan(w, self.cfg)
                    self.assertIsNotNone(validate(p.fallback, w, p, self.cfg))


if __name__ == "__main__":
    unittest.main()
