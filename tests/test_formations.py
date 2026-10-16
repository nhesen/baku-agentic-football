import copy, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PACKAGE=Path(__file__).resolve().parents[1]
if (PACKAGE/'baku_fc').is_dir():
    sys.path.insert(0,str(PACKAGE))
    sys.path.insert(0,str(Path(__file__).resolve().parent))
else:
    sys.path.insert(0,str(ROOT/'work/v4-candidate'))
    sys.path.insert(0,str(ROOT/'outputs/baku-football-v3/tests'))
from test_adversarial import fixture
from baku_fc.config import Settings
from baku_fc.state import normalize
from baku_fc.tactics import plan
from baku_fc.commands import validate
from baku_fc.formations import LAYOUTS, anchor_id

class FormationContracts(unittest.TestCase):
    def state(self):
        p=fixture(2)
        gs=p['gameState'];gs.update(playMode='OPEN_PLAY',gameTime=12)
        for pl in gs['players']:pl.pop('hasBall',None)
        gs['ball'].update(isFree=False,possessionPlayerId=2,possessionTeamId=0,position={'x':0,'y':0})
        return p
    def test_eight_distinct_four_player_layouts(self):
        self.assertEqual(len(LAYOUTS),8)
        self.assertEqual(len(set(LAYOUTS.values())),8)
        for slots in LAYOUTS.values():self.assertEqual(len(slots),4)
    def test_legal_five_agents_in_all_phases_and_layouts(self):
        for formation in LAYOUTS:
            cfg=Settings(use_llm=False,scheme='flow',release_anchor=True,formation=formation)
            for status in ('own','opp','loose','restart'):
                p=self.state();gs=p['gameState']
                if status=='opp':gs['ball']['possessionTeamId']=1
                if status=='loose':gs['ball']['isFree']=True
                if status=='restart':gs.update(playMode='FREE_KICK',restartTeamId=0,restartPlayerId=2)
                for pid in range(5):
                    p['myPlayers']=[pid];w=normalize(p,pid,cfg);q=plan(w,cfg)
                    self.assertIsNotNone(validate(q.fallback,w,q,cfg),(formation,status,pid))
                    self.assertEqual(q.facts['outfield_players'],4)
                    self.assertLessEqual(abs(q.target.x),cfg.pitch_half_length)
                    self.assertLessEqual(abs(q.target.y),cfg.pitch_half_width)
    def test_mobile_anchor_is_same_for_independent_players(self):
        p=self.state();cfg=Settings(scheme='flow',formation='4-0')
        anchors=[]
        for pid in range(5):
            p['myPlayers']=[pid];w=normalize(p,pid,cfg);anchors.append(anchor_id(w,cfg))
        self.assertEqual(len(set(anchors)),1)
        self.assertNotEqual(anchors[0],2)
    def test_shape_mirrors_home_and_away(self):
        for formation in LAYOUTS:
            cfg=Settings(scheme='flow',formation=formation,release_anchor=True)
            p=self.state();q=copy.deepcopy(p);q['teamId']=1
            q['gameState']['ball']['possessionTeamId']=1
            for pl in q['gameState']['players']:
                key='teamCode' if 'teamCode' in pl else 'teamId'
                pl[key]={'home':'away','away':'home'}[pl[key]];pl['position']['x']*=-1
            for pid in range(1,5):
                p['myPlayers']=[pid];q['myPlayers']=[pid]
                a=plan(normalize(p,pid,cfg),cfg).target;b=plan(normalize(q,pid,cfg),cfg).target
                self.assertAlmostEqual(a.x,-b.x,places=7);self.assertAlmostEqual(a.y,b.y,places=7)

if __name__=='__main__':unittest.main(verbosity=2)
