"""Testable coaching hypotheses; no hidden state, extra players or learned xG."""
import math
from .state import Point
from .phase_coach import _point, _assign
from .tactics import segment_clearance, stopped_phase


def angular_gap(origin,a,b):
    ax,ay=a.x-origin.x,a.y-origin.y
    bx,by=b.x-origin.x,b.y-origin.y
    aa,bb=math.hypot(ax,ay),math.hypot(bx,by)
    return math.acos(max(-1.,min(1.,(ax*bx+ay*by)/max(aa*bb,1e-9))))


def enhance(w,cfg,original):
    d=dict(original);d['targets']=dict(original['targets'])
    mode=cfg.combination_tactics
    d.update(combination=mode,pass_and_move=False,delay_only=False,
             last_passer=w.last_passer,pass_age=w.pass_age)
    if stopped_phase(w):return d
    k=cfg.pitch_half_length/50
    active=[p for p in w.mine if p.pid]
    holder=w.owner[1] if w.owner and w.owner[0]==w.team else None
    if d['attack_active']:
        if mode in {'triangles','combined'}:
            # Improve separate passing bearings, not a prescribed 70-degree rule.
            # Slots keep their depth/safety roles; only small local shifts occur.
            for pid,pt in list(sorted(d['targets'].items())):
                if pid in (d['anchor'],holder):continue
                others=[q for j,q in d['targets'].items() if j not in (pid,holder)]
                choices=[_point(w,cfg,pt.x*w.sign+du*k,pt.y+dy*k,True)
                         for du,dy in ((0,0),(-3,0),(3,0),(0,-5),(0,5))]
                def quality(q):
                    angle=min((angular_gap(w.ball,q,t) for t in others),default=1.)
                    room=min((q.distance(o.pos) for o in w.opponents),default=10.)
                    spacing=min((q.distance(t) for t in others),default=10.)
                    return (2.5*min(angle,1.2)+.6*min(segment_clearance(w.ball,q,w.opponents),6)
                            +.4*min(room,8)+.25*min(spacing,10)-.22*q.distance(pt))
                d['targets'][pid]=max(choices,key=quality)
        if mode in {'give_go','combined'} and w.last_passer not in (None,0,d['anchor'],holder):
            runner=next((p for p in active if p.pid==w.last_passer),None)
            if runner and w.pass_age is not None and w.pass_age<=2.5:
                # The return pass is still the ordinary visible-position PASS.
                # Moving diagonally creates the option without forcing a pass.
                u,y=w.ball.x*w.sign,w.ball.y
                candidates=[_point(w,cfg,u+du*k,y+dy*k,True)
                            for du,dy in ((8,-8),(8,8),(14,-6),(14,6))]
                others=[q for j,q in d['targets'].items() if j not in (runner.pid,holder)]
                def quality(q):
                    room=min((q.distance(o.pos) for o in w.opponents),default=10.)
                    spacing=min((q.distance(t) for t in others),default=10.)
                    return (min(room,8)+.7*min(segment_clearance(w.ball,q,w.opponents),6)
                            +.3*min(spacing,10)-.12*runner.pos.distance(q))
                d['targets'][runner.pid]=max(candidates,key=quality)
                d['pass_and_move']=True
    elif mode in {'screen','combined'} and w.status=='OPP' and active:
        # One defender delays; partners recover goal-side and protect the centre.
        # Always assign a screen even when no hard-press trigger is available.
        u,y=w.ball.x*w.sign,w.ball.y
        eligible=[p for p in active if p.stamina>.25] or active
        marker=min(eligible,key=lambda p:(p.pos.distance(w.ball)+
                    (3*k if p.pos.x*w.sign>u+2*k else 0),p.pid))
        free=[p for p in active if p.pid!=marker.pid]
        covered=sum(p.pos.x*w.sign<u-2*k for p in free)>=1
        engage=covered or u<-cfg.pitch_half_length*.65
        distance=(1.2 if engage else 3.5)*k
        goal=Point(-w.sign*cfg.pitch_half_length,0)
        length=max(w.ball.distance(goal),1.)
        screen=Point(w.ball.x+(goal.x-w.ball.x)*distance/length,
                     w.ball.y+(goal.y-w.ball.y)*distance/length)
        # Compact partners, retain one forward outlet outside the danger zone.
        back=max(-cfg.pitch_half_length+6*k,min(u-12*k,-5*k))
        cy=max(-8*k,min(8*k,y*.35))
        slots=[_point(w,cfg,back,cy-7*k),_point(w,cfg,back,cy+7*k),
               _point(w,cfg,u+(12 if u>-15*k else -4)*k,-y*.25,True)]
        targets=_assign(free,slots[:len(free)],preferred=(1,2,4))
        threats=sorted((o for o in w.opponents if o.pid and o.pos.x*w.sign<u-2*k),
                       key=lambda o:(o.pos.x*w.sign+.3*abs(o.pos.y),o.pid))
        available=list(free)
        for threat in threats[:2]:
            if not available:break
            if abs(threat.pos.y)>cfg.pitch_half_width*.7 and threat.pos.x*w.sign>-25*k:continue
            mark=_point(w,cfg,threat.pos.x*w.sign-2*k,threat.pos.y*.95)
            defender=min(available,key=lambda p:(p.pos.distance(mark),p.pid))
            targets[defender.pid]=mark;available.remove(defender)
        targets[marker.pid]=screen
        d.update(targets=targets,presser=marker.pid,defense_active=True,
                 phase='delay_and_cover',delay_only=not engage,
                 anchor=min(free,key=lambda p:(targets[p.pid].x*w.sign,p.pid)).pid if free else marker.pid)
    return d
