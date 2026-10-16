import unittest
from test_adversarial import fixture, _player
from baku_fc.config import Settings
from baku_fc.state import normalize
from baku_fc.tactics import plan, passing_options
from baku_fc.engine import Engine


class MatchRegressions(unittest.TestCase):
    def held(self, pid=2):
        p=fixture(pid);p["gameState"]["playMode"]="OPEN_PLAY"
        p["gameState"]["ball"].update(isFree=False,possessionPlayerId=pid,possessionTeamId=0)
        return p
    def decide(self,p,pid=2):
        e=Engine(pid,Settings(use_llm=False));self.addCleanup(e.close)
        return e.decide(p)["commands"][0]
    def test_cooldown_blocks_kicks_under_pressure(self):
        p=self.held();_player(p,0,2)["canKick"]=False
        self.assertNotIn(self.decide(p)["commandType"],{"PASS","SHOOT","GK_DISTRIBUTE"})
    def test_explicit_restart_taker_must_kick_not_dribble(self):
        p=self.held();p["gameState"].update(playMode="FREE_KICK",modeTeamId=0,restartPlayerId=2)
        self.assertEqual(self.decide(p)["commandType"],"PASS")
    def test_restart_cooldown_holds_instead_of_rejected_kicks(self):
        p=self.held();p["gameState"].update(playMode="FREE_KICK",modeTeamId=0,restartPlayerId=2)
        _player(p,0,2)["canKick"]=False
        self.assertEqual(self.decide(p)["commandType"],"SET_STANCE")
    def test_dangerous_goalkeeper_backpass_is_masked(self):
        p=self.held();_player(p,0,2)["position"]={"x":-25,"y":8}
        _player(p,0,0)["position"]={"x":-51,"y":0}
        w=normalize(p,2,Settings())
        self.assertNotIn(0,[x["pid"] for x in passing_options(w,Settings())])
    def test_offside_rule_is_explicit_and_masks_receiver(self):
        p=self.held();_player(p,0,2)["position"]={"x":0,"y":-10}
        _player(p,0,4)["position"]={"x":44,"y":-10}
        for i in range(5): _player(p,1,i)["position"]={"x":15+i,"y":20}
        p["gameState"]["ball"]["position"]={"x":0,"y":-10}
        cfg=Settings();self.assertIn(4,[x["pid"] for x in passing_options(normalize(p,2,cfg),cfg)])
        p["gameState"]["rules"]={"offsideEnabled":True}
        self.assertNotIn(4,[x["pid"] for x in passing_options(normalize(p,2,cfg),cfg)])
    def test_anchor_with_ball_does_not_walk_back_to_cap(self):
        p=self.held(1);_player(p,0,1)["position"]={"x":5,"y":0}
        p["gameState"]["ball"]["position"]={"x":5,"y":0}
        w=normalize(p,1,Settings());q=plan(w,Settings())
        for c in q.candidates:
            if c["commandType"]=="MOVE_TO":self.assertGreaterEqual(c["parameters"]["target_x"],5)


if __name__=="__main__":unittest.main()
