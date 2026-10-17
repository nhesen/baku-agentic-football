"""Behavioral contracts for observable-state football tactics."""
import copy,sys,unittest
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[2]
PACKAGE=Path(__file__).resolve().parents[1]
if (PACKAGE/'baku_fc').is_dir():sys.path.insert(0,str(PACKAGE))
else:sys.path.insert(0,str(ROOT/'work/v5-candidate-r2'))
sys.path.insert(0,str(ROOT/'outputs/baku-football-v4/tests'))
from test_adversarial import fixture
from baku_fc.config import Settings
from baku_fc.engine import Engine
from baku_fc.state import normalize,Point
from baku_fc.phase_coach import decision
from baku_fc.tactics import plan
from baku_fc.commands import validate

class PhaseCoachTests(unittest.TestCase):
    def world(self,owner=2,team=0,x=0,y=0,**kw):
        raw=fixture(2);gs=raw['gameState']
        gs.update(playMode='OPEN_PLAY',gameTime=12,timeRemaining=100)
        for p in gs['players']:p.pop('hasBall',None)
        gs['ball'].update(isFree=False,possessionPlayerId=owner,possessionTeamId=team,position={'x':x,'y':y})
        return normalize(raw,2,Settings()),raw
    def test_phase_changes_and_legal_targets_all_modes(self):
        for mode in ('attack','compact','trigger','high','complete','wide','pivot'):
            cfg=Settings(phase_tactics=mode,scheme='flow',release_anchor=True)
            for own in (0,1):
                for u in (-35,0,32):
                    w,raw=self.world(team=own,x=u,y=20)
                    for pid in range(5):
                        ww=replace(w,pid=pid);q=plan(ww,cfg)
                        self.assertIsNotNone(validate(q.fallback,ww,q,cfg),(mode,own,u,pid))
                        self.assertLess(abs(q.target.x),cfg.pitch_half_length)
                        self.assertLess(abs(q.target.y),cfg.pitch_half_width)
    def test_five_independent_runtimes_agree_on_presser_and_targets(self):
        w,_=self.world(team=1,x=-20,y=22)
        cfg=Settings(phase_tactics='complete')
        choices=[decision(replace(w,pid=pid),cfg) for pid in range(5)]
        self.assertEqual(len({c['presser'] for c in choices}),1)
        self.assertTrue(all(c['targets']==choices[0]['targets'] for c in choices))
        self.assertNotEqual(choices[0]['presser'],0)
    def test_off_disables_phase_targets_with_separate_finish_telemetry(self):
        w,_=self.world()
        cfg=Settings(scheme='flow',release_anchor=True,phase_tactics='off')
        facts=plan(w,cfg).facts['tactical']
        self.assertTrue({'phase','attack_active','defense_active','press_triggers'}.isdisjoint(facts))
    def test_width_and_depth_with_a_cover_player(self):
        w,_=self.world(x=-25)
        d=decision(w,Settings(phase_tactics='wide'))
        self.assertEqual(d['phase'],'build_up')
        pts=list(d['targets'].values())
        self.assertGreater(max(p.y for p in pts)-min(p.y for p in pts),20)
        self.assertLess(d['targets'][d['anchor']].x,w.ball.x)
    def test_score_and_stamina_change_block(self):
        w,_=self.world(team=1,x=-5)
        cfg=Settings(phase_tactics='high')
        low=replace(w,players=tuple(replace(p,stamina=.2) for p in w.players))
        self.assertIsNone(decision(low,cfg)['presser'])
        lead=replace(w,remaining=10,us=2,them=1)
        self.assertEqual(decision(lead,cfg)['risk_profile'],'protect')
    def test_transition_memory_uses_observed_owner_and_resets_per_match(self):
        _,raw=self.world();cfg=Settings(use_llm=False,scheme='flow',track_transitions=True,phase_tactics='complete')
        e=Engine(2,cfg)
        try:
            first=e.decide(raw);self.assertIsNone(first['meta']['tactical']['loss_age'])
            raw['gameState']['gameTime']=13;raw['gameState']['ball']['possessionTeamId']=1
            lost=e.decide(raw);self.assertEqual(lost['meta']['tactical']['loss_age'],0)
            raw['gameState']['gameTime']=14;raw['gameState']['ball']['possessionTeamId']=0
            gained=e.decide(raw);self.assertEqual(gained['meta']['tactical']['gain_age'],0)
            raw['gameState']['matchId']='new-match'
            self.assertIsNone(e.decide(raw)['meta']['tactical']['gain_age'])
        finally:e.close()
    def test_mirrored_snapshot_mirrors_team_assignment(self):
        w,_=self.world(team=1,x=-12,y=20);cfg=Settings(phase_tactics='complete')
        flip=replace(w,team=1,pid=2,owner=(0,2),ball=Point(-w.ball.x,w.ball.y),velocity=Point(-w.velocity.x,w.velocity.y),players=tuple(replace(p,team=1-p.team,pos=Point(-p.pos.x,p.pos.y)) for p in w.players))
        a,b=decision(w,cfg),decision(flip,cfg)
        self.assertEqual(a['presser'],b['presser'])
        for pid in a['targets']:
            self.assertAlmostEqual(a['targets'][pid].x,-b['targets'][pid].x)
            self.assertAlmostEqual(a['targets'][pid].y,b['targets'][pid].y)
    def test_missing_players_do_not_create_phantom_slots(self):
        w,_=self.world(team=1,x=-30)
        w=replace(w,players=tuple(p for p in w.players if not(p.team==0 and p.pid in(2,4))))
        d=decision(w,Settings(phase_tactics='complete'))
        self.assertTrue(set(d['targets']).issubset({1,3}))
    def test_press_approach_is_executed_before_direct_chase(self):
        w,_=self.world(team=1,x=0,y=20)
        positions={1:Point(-25,0),2:Point(-15,5),3:Point(-10,20),4:Point(20,-10)}
        w=replace(w,pid=3,players=tuple(replace(p,pos=positions[p.pid]) if p.team==0 and p.pid else p for p in w.players))
        cfg=Settings(phase_tactics='trigger',scheme='flow',release_anchor=True)
        q=plan(w,cfg)
        self.assertEqual(q.presser,3)
        self.assertEqual(q.fallback['commandType'],'MOVE_TO')
        self.assertLess(q.fallback['parameters']['target_x'],w.ball.x)
    def test_counterpress_requires_local_support_and_cover(self):
        w,_=self.world(team=1,x=5,y=0)
        positions={1:Point(-15,0),2:Point(0,-3),3:Point(4,3),4:Point(20,-10)}
        w=replace(w,loss_age=.5,players=tuple(replace(p,pos=positions[p.pid]) if p.team==0 and p.pid else p for p in w.players))
        cfg=Settings(phase_tactics='complete')
        self.assertIn('local_counterpress',decision(w,cfg)['press_triggers'])
        self.assertNotIn('local_counterpress',decision(replace(w,loss_age=4),cfg)['press_triggers'])
        alone=replace(w,players=tuple(p for p in w.players if p.team!=0 or p.pid in(0,3)))
        self.assertNotIn('local_counterpress',decision(alone,cfg)['press_triggers'])

if __name__=='__main__':unittest.main(verbosity=2)
