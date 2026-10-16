"""Observable-state 5v5 tactics: four outfield players, one protected keeper.

Football principles are hypotheses here, not learned weights or calibrated xG.
Every runtime derives the same assignments from the same visible snapshot.
"""
from itertools import permutations
from .state import Point
from .tactics import clamp, onside_limit, segment_clearance, stopped_phase, profile_for


ATTACK = {"attack", "complete", "wide", "pivot"}
DEFEND = {"compact", "trigger", "high", "complete", "wide", "pivot"}


def _point(w, cfg, u, y, onside=False):
    k=cfg.pitch_half_length/50
    ceiling=cfg.pitch_half_length-4*k
    if onside and w.offside_enabled and cfg.offside_control:
        ceiling=min(ceiling,onside_limit(w,cfg)-k)
    return Point(w.sign*clamp(u,-cfg.pitch_half_length+5*k,ceiling),
                 clamp(y,-cfg.pitch_half_width+3*k,cfg.pitch_half_width-3*k))


def _assign(players, slots, preferred=()):
    """Minimum travel with a small role-continuity cost, at most 4! cases."""
    players=sorted(players,key=lambda p:p.pid)
    if not players:return {}
    best=None
    for perm in permutations(range(len(slots)),len(players)):
        score=sum(p.pos.distance(slots[i])+ (2.0 if preferred and preferred[i]!=p.pid else 0.)
                  for p,i in zip(players,perm))
        key=(score,perm)
        if best is None or key<best[0]:best=(key,perm)
    return {p.pid:slots[i] for p,i in zip(players,best[1])}


def _attack_targets(w,cfg,phase):
    h,k=cfg.pitch_half_length,cfg.pitch_half_length/50
    u,y=w.ball.x*w.sign,w.ball.y
    holder=w.owner[1] if w.owner and w.owner[0]==w.team else None
    # A single safety player remains behind the ball; cover swaps when he carries.
    anchor=2 if holder==1 else 1
    if cfg.combination_tactics != "off":
        available=[p for p in w.mine if p.pid and p.pid!=holder]
        if not any(p.pid==anchor for p in available):
            anchor=min(available,key=lambda p:(p.pos.x*w.sign,p.pid)).pid if available else None
    attacking=[p for p in w.mine if p.pid not in (0,anchor)]
    wide=cfg.phase_tactics=="wide"
    span=min(cfg.pitch_half_width*.58,(16 if wide else 12)*k)
    targets={anchor:_point(w,cfg,min(u-12*k,12*k),y*.28)} if anchor is not None else {}
    if phase=="build_up":
        # 1-2-1: two diagonal outlets and a high pivot; no forced pass count.
        positions=[(u+5*k,-span),(u+8*k,span),(u+23*k,-y*.2)]
        if cfg.phase_tactics=="pivot":
            positions=[(u-2*k,-span),(u-2*k,span),(u+28*k,0)]
    elif phase=="counter_attack":
        # Stagger runners: one short connection, two separate forward channels.
        positions=[(u+3*k,-y*.25),(u+19*k,-10*k),(u+26*k,10*k)]
    else:
        # 1-1-2: central connection behind/level with ball, ball-side support and
        # weak-side runner. The far runner narrows near goal for a cutback.
        near=1 if y>=0 else -1
        narrow=8*k if u>h*.5 else span
        positions=[(u-3*k,-y*.2),(u+14*k,near*span),(u+22*k,-near*narrow)]
        if wide:positions=[(u+2*k,-y*.2),(u+14*k,-span),(u+21*k,span)]
    slots=[_point(w,cfg,x,yy,True) for x,yy in positions]
    targets.update(_assign(attacking,slots,preferred=(2,3,4)))
    # Move into a nearby visible passing lane rather than hide behind a marker.
    for pid,pt in list(targets.items()):
        if pid==anchor:continue
        choices=[pt]+[_point(w,cfg,pt.x*w.sign+dx*k,pt.y+dy*k,True)
                      for dx,dy in ((-3,0),(0,-3),(0,3))]
        def quality(q):
            room=min((q.distance(o.pos) for o in w.opponents),default=20)
            return min(room,8)+.6*min(segment_clearance(w.ball,q,w.opponents),6)-.2*q.distance(pt)
        targets[pid]=max(choices,key=quality)
    return targets,anchor


def decision(w,cfg):
    mode=cfg.phase_tactics
    active=[p for p in w.mine if p.pid]
    k,h=cfg.pitch_half_length/50,cfg.pitch_half_length
    u,y=w.ball.x*w.sign,w.ball.y
    own=w.status in {"ME","TEAM"} or w.our_pass_in_flight
    energy=sum(p.stamina for p in active)/max(1,len(active))
    risk=profile_for(w,cfg)
    pressure=sum(o.pos.distance(w.ball)<9*k for o in w.opponents if o.pid)
    goal_side=[p for p in active if p.pos.x*w.sign<u-2*k]
    close=[p for p in active if p.pos.distance(w.ball)<13*k]
    loss_window=w.loss_age is not None and w.loss_age<=3.
    regain_window=w.gain_age is not None and w.gain_age<=4.
    targets={};anchor=1;presser=None;trigger=[]
    if stopped_phase(w):phase="restart"
    elif own:
        phase="counter_attack" if regain_window and u<h*.5 else "build_up" if u<-h*.25 else "final_third" if u>h*.4 else "progression"
    elif w.status=="LOOSE":phase="loose_ball"
    elif w.status=="UNKNOWN":phase="uncertain_recover"
    else:phase="mid_block"
    if own and mode in ATTACK and phase!="restart":
        targets,anchor=_attack_targets(w,cfg,phase)
    if not own and mode in DEFEND and phase!="restart":
        # A nearby player can engage; a distant front player must not leave his
        # cover assignment to chase an opponent across the entire pitch.
        eligible=[p for p in active if p.stamina>.35]
        nearest=min(eligible,key=lambda p:(p.pos.distance(w.ball),p.pid)) if eligible else None
        if w.status=="LOOSE":
            # Received ball trajectory is public; assign only one collector.
            if nearest:presser=nearest.pid
        elif w.status=="OPP" and nearest:
            if abs(y)>.53*cfg.pitch_half_width:trigger.append("touchline")
            if w.velocity.x*w.sign>3*k:trigger.append("ball_moving_away_from_our_goal")
            if u<-h*.3:trigger.append("danger_zone")
            if loss_window and mode in {"complete","wide","pivot"} and len(close)>=2 and goal_side and energy>.5:
                trigger.append("local_counterpress")
            high=(mode=="high" and risk!="protect") or risk=="press"
            enough_cover=len(goal_side)>=2 or (len(goal_side)>=1 and u>0)
            engage=(u<0 if mode=="compact" else bool(trigger) or high)
            maxreach=(20 if high else 14)*k
            if (engage and nearest.pos.distance(w.ball)<maxreach and
                    (enough_cover or u<-h*.55) and energy>.4):
                presser=nearest.pid
        high=((mode=="high" and risk!="protect") or risk=="press") and energy>.5
        if w.status=="OPP" and u<-h*.5:phase="low_block"
        elif not goal_side and w.status=="OPP":phase="recovery"
        elif "local_counterpress" in trigger and presser is not None:phase="counterpress"
        elif high and presser is not None:phase="high_press"
        else:phase="mid_block" if w.status=="OPP" else phase
        # Protect the centre with ball-side shifting. Two depth lines, with the
        # weak-side player tucked in; compressed further when protecting a lead.
        depth=10*k if risk=="protect" else 14*k
        back=clamp(u-14*k,-h+7*k,(-2 if high else -8)*k)
        if risk=="protect":back=max(-h+6*k,back-3*k)
        span=(7 if phase=="low_block" else 9)*k
        cy=clamp(y*.45,-9*k,9*k)
        slots=[_point(w,cfg,back,cy-span),_point(w,cfg,back,cy+span),
               _point(w,cfg,back+depth,cy-span*.8),_point(w,cfg,back+depth,cy+span*.8)]
        if presser is not None and y<0:
            slots[2],slots[3]=slots[3],slots[2]
        free=[p for p in active if p.pid!=presser]
        # The deepest two slots have priority. Keep a central rest defender even
        # when pressing high; only the farthest free slot is omitted.
        targets=_assign(free,slots[:len(free)],preferred=(1,2,3,4))
        threats=sorted((o for o in w.opponents if o.pid and o.pos.x*w.sign<u-2*k),
                       key=lambda o:(o.pos.x*w.sign+.25*abs(o.pos.y),o.pid))
        available=list(free)
        for threat in threats[:2]:
            if not available:break
            tu=threat.pos.x*w.sign
            mark=_point(w,cfg,tu-2*k,threat.pos.y)
            defender=min(available,key=lambda p:(p.pos.distance(mark),p.pid))
            # Do not drag a central covering player to a harmless distant wing.
            if abs(threat.pos.y)<cfg.pitch_half_width*.65 or tu<-h*.55:
                targets[defender.pid]=mark;available.remove(defender)
        if presser is not None:
            # Close from the central/goal side, reducing the inside passing lane.
            targets[presser]=_point(w,cfg,u-1.2*k,y*.94)
        anchor=min(free,key=lambda p:(targets.get(p.pid,p.pos).x*w.sign,p.pid)).pid if free else 1
    return {"phase":phase,"targets":targets,"anchor":anchor,"presser":presser,
            "attack_active":own and mode in ATTACK and phase!="restart",
            "defense_active":not own and mode in DEFEND and phase!="restart",
            "press_triggers":trigger,"mean_stamina":round(energy,3),
            "near_ball_teammates":len(close),"goal_side_cover":len(goal_side),
            "opponents_pressing_ball":pressure,"risk_profile":risk,
            "loss_age":w.loss_age,"gain_age":w.gain_age}
