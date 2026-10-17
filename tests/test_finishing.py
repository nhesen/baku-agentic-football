import json,sys,unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from baku_fc.state import World,Point,Player
from baku_fc.config import Settings
from baku_fc.engine import Engine
from baku_fc.attack import pass_menu,cover
from baku_fc.tactics import plan,command
from baku_fc.commands import validate
import test_phase_coach as phase_tests

class FinishingTests(unittest.TestCase):
    def cfg(self,mode):
        return Settings(use_llm=False,pitch_half_length=50,pitch_half_width=30,shot_max_distance=30,
                        scheme='flow',early_shot=True,release_anchor=True,track_transitions=True,
                        phase_tactics='attack',combination_tactics='give_go',finishing_tactics=mode)
    def world(self,pid=4,owner=(0,4),blocked=True):
        ours=[(-48,0),(-20,10),(0,-15),(5,15),(25,0)]
        opp=[(49,0),(37,0),(37,-1),(37,1),(0,25)] if blocked else [(49,0),(-10,-20),(-10,20),(0,-25),(0,25)]
        players=tuple(Player(i,t,Point(*p)) for t,ps in enumerate((ours,opp)) for i,p in enumerate(ps))
        return World(0,pid,players,Point(25,0),Point(0,0),owner,'ME' if owner==(0,pid) else 'OPP',
                     'test',10,1,None,0,0,(),'OPEN_PLAY','finishing-test')
    def cutback(self):
        w=self.world(pid=3,owner=(0,3),blocked=False)
        pos={3:Point(45,20),4:Point(40,0)}
        return replace(w,status='ME',ball=Point(45,20),players=tuple(replace(p,pos=pos[p.pid]) if p.team==0 and p.pid in pos else p for p in w.players))
    def test_blocked_shot_removed_and_independent_guard_rejects_it(self):
        w=self.world();cfg=self.cfg('shot');p=plan(w,cfg)
        self.assertFalse(p.shot_allowed)
        self.assertNotIn('SHOOT',[c['commandType'] for c in p.candidates])
        self.assertIsNone(validate(command(w,'SHOOT',{'aim_location':'BR','power':1}),w,p,cfg))
        self.assertEqual(plan(w,self.cfg('off')).fallback['commandType'],'SHOOT')
    def test_clear_long_shot_remains_available(self):
        w=self.world(blocked=False);p=plan(w,self.cfg('shot'))
        self.assertTrue(p.shot_allowed)
        self.assertEqual(p.fallback['commandType'],'SHOOT')
    def test_open_central_cutback_is_prioritized(self):
        w=self.cutback();cfg=self.cfg('cutback');p=plan(w,cfg)
        self.assertEqual(p.fallback['commandType'],'PASS')
        self.assertEqual(p.fallback['parameters']['target_player_id'],4)
        self.assertTrue(next(x for x in pass_menu(w,cfg) if x['pid']==4)['cutback'])
    def test_deep_backpass_not_given_cutback_bonus(self):
        w=self.cutback();w=replace(w,ball=Point(-10,20),players=tuple(replace(p,pos=Point(p.pos.x-55,p.pos.y)) if p.team==0 and p.pid in (3,4) else p for p in w.players))
        self.assertFalse(any(x['cutback'] for x in pass_menu(w,self.cfg('cutback'))))
    def test_cutback_geometry_mirrors(self):
        w=self.cutback();cfg=self.cfg('cutback')
        other=replace(w,team=1,owner=(1,3),ball=Point(-w.ball.x,w.ball.y),players=tuple(replace(p,team=1-p.team,pos=Point(-p.pos.x,p.pos.y)) for p in w.players))
        a,b=plan(w,cfg),plan(other,cfg)
        self.assertEqual(a.fallback['commandType'],b.fallback['commandType'])
        self.assertEqual(a.fallback['parameters'],b.fallback['parameters'])
    def test_optional_retention_model_is_called_only_when_enabled(self):
        w=self.cutback();cfg=self.cfg('off')
        with patch('baku_fc.attack.retention',return_value=.9) as fn:
            plain=pass_menu(w,cfg);fn.assert_not_called()
            enriched=pass_menu(w,replace(cfg,use_pass_model=True));self.assertTrue(fn.called)
            a=next(p for p in plain if p['pid']==4);b=next(p for p in enriched if p['pid']==4)
            self.assertAlmostEqual(b['score']-a['score'],cfg.pass_model_weight*.4,places=3)
            self.assertEqual(len(fn.call_args.args[0]),7)
    def test_opponent_release_memory_expires_and_resets(self):
        _,raw=phase_tests.PhaseCoachTests().world(team=1)
        e=Engine(2,self.cfg('cover'))
        try:
            e.decide(raw);gs=raw['gameState'];gs['gameTime']=12.3
            gs['ball'].update(isFree=True,velocity={'x':8,'y':0})
            self.assertAlmostEqual(e.decide(raw)['meta']['tactical']['opponent_release_age'],.3)
            gs['gameTime']=14
            self.assertIsNone(e.decide(raw)['meta']['tactical']['opponent_release_age'])
            gs['matchId']='next'
            self.assertIsNone(e.decide(raw)['meta']['tactical']['opponent_release_age'])
        finally:e.close()
    def test_our_release_never_gets_opponent_cover_hint(self):
        _,raw=phase_tests.PhaseCoachTests().world(team=0)
        e=Engine(2,self.cfg('cover'))
        try:
            e.decide(raw);gs=raw['gameState'];gs['gameTime']=12.2
            gs['ball'].update(isFree=True,velocity={'x':8,'y':0})
            result=e.decide(raw)
            self.assertIsNone(result['meta']['tactical']['opponent_release_age'])
            self.assertNotIn(result['commands'][0]['commandType'],('PASS','SHOOT'))
        finally:e.close()
    def test_recent_loose_cover_keeps_visible_threat_assignment(self):
        w=replace(self.world(pid=2,owner=(1,3)),opponent_release_age=.3)
        cfg=self.cfg('cover');target=Point(-10,0)
        a=cover(w,cfg,4,target)
        loose=replace(w,status='LOOSE',owner=None)
        self.assertEqual(cover(loose,cfg,4,target),a)
        self.assertEqual(cover(replace(loose,our_pass_in_flight=True),cfg,4,target),target)
    def test_restart_and_cooldown_guards_remain_effective(self):
        w=self.world(blocked=False);cfg=self.cfg('balanced')
        w=replace(w,players=tuple(replace(p,can_kick=False) if p.key==(0,4) else p for p in w.players))
        p=plan(w,cfg)
        self.assertNotIn(p.fallback['commandType'],('PASS','SHOOT'))
        self.assertIsNone(validate(command(w,'SHOOT',{'aim_location':'BR','power':1}),w,p,cfg))
        restart=replace(w,play_mode='FREE_KICK',restart_team=0,restart_player=4)
        self.assertEqual(plan(restart,cfg).fallback['commandType'],'SET_STANCE')
    def test_missing_game_clock_does_not_create_unbounded_cover(self):
        _,raw=phase_tests.PhaseCoachTests().world(team=1)
        raw['gameState'].pop('gameTime',None)
        e=Engine(2,self.cfg('cover'))
        try:
            e.decide(raw)
            raw['gameState']['ball'].update(isFree=True,velocity={'x':8,'y':0})
            self.assertIsNone(e.decide(raw)['meta']['tactical']['opponent_release_age'])
        finally:e.close()

if __name__=='__main__':unittest.main()
