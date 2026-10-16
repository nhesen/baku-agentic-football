import sys,unittest,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'outputs/baku-football-v2/tests'))
from test_adversarial import fixture,_player
from baku_fc.config import Settings
from baku_fc.state import normalize
from baku_fc.tactics import plan
from baku_fc.commands import validate
from baku_fc.engine import Engine

class FivePlayers(unittest.TestCase):
    def held(self,pid=2):
        p=fixture(pid);gs=p['gameState'];gs.update(playMode='OPEN_PLAY',gameTime=10,tick=100,matchId='one')
        for pl in gs['players']:pl.pop('hasBall',None)
        gs['ball'].update(isFree=False,possessionPlayerId=pid,possessionTeamId=0)
        gs['ball']['position']=dict(_player(p,0,pid)['position'])
        return p
    def test_five_roles_mirrored_and_legal(self):
        for scheme in ('diamond','pair','chain','flow'):
            cfg=Settings(use_llm=False,scheme=scheme,track_transitions=True)
            for team in (0,1):
                p=self.held();p['teamId']=team
                for pid in range(5):
                    p['myPlayers']=[pid];w=normalize(p,pid,cfg);q=plan(w,cfg);c=validate(q.fallback,w,q,cfg)
                    self.assertIsNotNone(c);self.assertEqual((c['teamId'],c['playerId']),(team,pid))
                    self.assertEqual(q.facts['players_per_side'],5);self.assertEqual(q.facts['outfield_players'],4)
    def test_center_requires_explicit_engine_capability(self):
        p=self.held(4);_player(p,0,4)['position']={'x':45,'y':0};p['gameState']['ball']['position']={'x':45,'y':0}
        cfg=Settings(scheme='flow',early_shot=True,prefer_center=True)
        w=normalize(p,4,cfg);q=plan(w,cfg);self.assertNotEqual(q.fallback['parameters'].get('aim_location'),'CENTER')
        bad={'commandType':'SHOOT','parameters':{'aim_location':'CENTER','power':1}}
        self.assertIsNone(validate(bad,w,q,cfg))
        p['gameState']['rules']={'centerAimSupported':True};w=normalize(p,4,cfg);q=plan(w,cfg)
        self.assertEqual(q.fallback['parameters'].get('aim_location'),'CENTER');self.assertIsNotNone(validate(bad,w,q,cfg))
    def test_anchor_release_survives_final_command_guard(self):
        p=self.held(1);_player(p,0,1)['position']={'x':4,'y':0};p['gameState']['ball']['position']={'x':4,'y':0}
        cfg=Settings(scheme='flow',release_anchor=True,minimal_passing=True)
        w=normalize(p,1,cfg);q=plan(w,cfg)
        c=validate({'commandType':'MOVE_TO','parameters':{'target_x':12,'target_y':0}},w,q,cfg)
        self.assertEqual(c['parameters']['target_x'],12)
        p['gameState']['ball'].update(isFree=False,possessionPlayerId=3,possessionTeamId=0)
        w=normalize(p,1,cfg);q=plan(w,cfg);c=validate({'commandType':'MOVE_TO','parameters':{'target_x':12,'target_y':0}},w,q,cfg)
        self.assertLessEqual(c['parameters']['target_x'],-3)
    def test_transition_memory_resets_and_opponent_overrides(self):
        cfg=Settings(use_llm=False,scheme='flow',track_transitions=True)
        e=Engine(2,cfg);self.addCleanup(e.close)
        p=self.held();e.decide(p)
        p['gameState']['ball'].update(isFree=True,velocity={'x':15,'y':0})
        p['gameState']['gameTime']=10.1;p['gameState']['tick']=101
        from unittest.mock import patch
        import baku_fc.engine as module
        original=module.plan;seen=[]
        def observe(w,c):seen.append(w.our_pass_in_flight);return original(w,c)
        with patch.object(module,'plan',observe):
            e.decide(p)
            p['gameState']['ball'].update(isFree=False,possessionPlayerId=3,possessionTeamId=1);e.decide(p)
            p['gameState']['ball']['isFree']=True;e.decide(p)
            p['gameState']['gameTime']=0;p['gameState']['tick']=0;p['gameState']['matchId']='two';e.decide(p)
        self.assertEqual(seen,[True,False,False,False])
    def test_restart_and_cooldown_do_not_emit_illegal_kicks(self):
        p=self.held();_player(p,0,2)['canKick']=False
        cfg=Settings(use_llm=False,scheme='flow',track_transitions=True,early_shot=True,release_anchor=True)
        e=Engine(2,cfg);self.addCleanup(e.close)
        self.assertNotIn(e.decide(p)['commands'][0]['commandType'],('PASS','SHOOT','GK_DISTRIBUTE'))
        p['gameState'].update(playMode='FREE_KICK',restartTeamId=0,restartPlayerId=2)
        self.assertEqual(e.decide(p)['commands'][0]['commandType'],'SET_STANCE')

if __name__=='__main__':unittest.main(verbosity=2)
