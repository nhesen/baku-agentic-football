import sys,unittest
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_phase_coach as phase_tests
from baku_fc.config import Settings
from baku_fc.phase_coach import decision
from baku_fc.combinations import enhance,angular_gap
from baku_fc.engine import Engine
from baku_fc.state import Point
from baku_fc.tactics import plan
from baku_fc.commands import validate


class CombinationTests(unittest.TestCase):
    def world(self,**kw):return phase_tests.PhaseCoachTests().world(**kw)
    def cfg(self,mode):return Settings(use_llm=False,phase_tactics='attack',scheme='flow',
                                     release_anchor=True,track_transitions=True,combination_tactics=mode)
    def test_transfer_starts_run_and_opponent_or_new_match_clears_it(self):
        _,raw=self.world(owner=3);e=Engine(2,self.cfg('give_go'))
        try:
            self.assertFalse(e.decide(raw)['meta']['tactical']['pass_and_move'])
            raw['gameState']['gameTime']=12.7
            raw['gameState']['ball']['possessionPlayerId']=4
            got=e.decide(raw)['meta']['tactical']
            self.assertEqual(got['last_passer'],3);self.assertTrue(got['pass_and_move'])
            raw['gameState']['gameTime']=13
            raw['gameState']['ball']['possessionTeamId']=1
            self.assertIsNone(e.decide(raw)['meta']['tactical']['last_passer'])
            raw['gameState']['matchId']='different'
            raw['gameState']['ball']['possessionTeamId']=0
            self.assertIsNone(e.decide(raw)['meta']['tactical']['last_passer'])
        finally:e.close()
    def test_loose_ball_never_invents_completed_pass(self):
        _,raw=self.world(owner=3);e=Engine(2,self.cfg('give_go'))
        try:
            e.decide(raw);raw['gameState']['gameTime']=12.3
            raw['gameState']['ball']['isFree']=True
            result=e.decide(raw)
            self.assertFalse(result['meta']['tactical']['pass_and_move'])
            self.assertNotIn(result['commands'][0]['commandType'],('PASS','SHOOT'))
        finally:e.close()
    def test_anchor_and_keeper_do_not_make_give_go_runs(self):
        w,_=self.world(owner=4)
        cfg=self.cfg('give_go')
        for pid in (0,1):
            ww=replace(w,last_passer=pid,pass_age=.5)
            d=enhance(ww,cfg,decision(ww,cfg))
            self.assertFalse(d['pass_and_move'])
    def test_removed_anchor_replaced_by_active_outfielder(self):
        w,_=self.world(owner=4)
        w=replace(w,players=tuple(p for p in w.players if p.key!=(0,1)))
        cfg=self.cfg('triangles');d=decision(w,cfg)
        self.assertIn(d['anchor'],(2,3))
        self.assertTrue(set(d['targets']).issubset({2,3,4}))
    def test_screen_exists_without_press_trigger_and_has_goal_side_target(self):
        w,_=self.world(team=1,x=10,y=0)
        cfg=self.cfg('screen');d=enhance(w,cfg,decision(w,cfg))
        self.assertIn(d['presser'],range(1,5));self.assertTrue(d['defense_active'])
        self.assertLess(d['targets'][d['presser']].x,w.ball.x)
    def test_all_runtimes_agree_and_commands_remain_legal_both_sides(self):
        w,_=self.world(team=1,x=-10,y=15)
        for mode in ('triangles','give_go','screen','combined'):
            cfg=self.cfg(mode)
            ds=[enhance(replace(w,pid=i),cfg,decision(replace(w,pid=i),cfg)) for i in range(5)]
            self.assertTrue(all(d['targets']==ds[0]['targets'] for d in ds))
            for own in (False,True):
                ww=replace(w,owner=(0,4) if own else (1,4),status='TEAM' if own else 'OPP')
                for pid in range(5):
                    x=replace(ww,pid=pid);p=plan(x,cfg)
                    self.assertIsNotNone(validate(p.fallback,x,p,cfg),(mode,own,pid))
    def test_angle_distinguishes_same_ray_from_separate_lanes(self):
        o=Point(0,0)
        self.assertAlmostEqual(angular_gap(o,Point(5,5),Point(10,10)),0)
        self.assertGreater(angular_gap(o,Point(5,5),Point(5,-5)),1.5)


if __name__=='__main__':unittest.main()
