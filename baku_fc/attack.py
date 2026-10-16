"""Five-player tactical candidates. Attack values are heuristics, not calibrated xG.

Four outfield slots, one goalkeeper; no champion code or weights are claimed.
"""
from __future__ import annotations
import math
from .state import Point
from .formations import support, anchor_id
from .phase_coach import decision as phase_decision
from .tactics import (Plan, clamp, command, move, stopped_phase, profile_for,
                      formation_target, onside_limit, segment_clearance, shot_facts)


def space(w, point):
    return min((point.distance(o.pos) for o in w.opponents), default=100.)


def attack_value(w, cfg, point):
    u = point.x*w.sign
    d = point.distance(Point(w.sign*cfg.pitch_half_length, 0))
    # Progress is valuable; central finishing positions receive an extra bonus.
    return .6*u + 22*math.exp(-d/18) - .12*abs(point.y)


def shape(w, cfg, mode):
    if cfg.scheme == "finish":
        return formation_target(w,cfg,mode)
    h, width, s = cfg.pitch_half_length, cfg.pitch_half_width, w.sign
    k=h/50
    u,y=w.ball.x*s,w.ball.y
    attacking=w.status in {"ME","TEAM"} or w.our_pass_in_flight
    if w.pid==0:
        ku=-h+2.5*k
        return Point(s*ku, clamp(y*(ku+h)/max(1,u+h), -cfg.goal_half_width*.85,cfg.goal_half_width*.85))
    if cfg.formation != "original":
        return support(w,cfg)
    if w.pid==1:
        tx=clamp(u-16*k,-h+10*k,-3*k)
        ty=clamp(y*.35,-9*k,9*k)
    elif cfg.release_anchor and w.status=='TEAM' and w.owner and w.owner[1]==1 and w.pid==2:
        tx,ty=clamp(u-16*k,-h+10*k,-3*k),clamp(y*.35,-9*k,9*k)
    elif cfg.scheme in {"pair","flow","direct"}:
        if w.pid==2: tx,ty=u+5*k,clamp(-y*.4,-8*k,8*k)
        else: tx,ty=u+(17 if w.pid==3 else 22)*k,(-8 if w.pid==3 else 8)*k+y*.15
    elif cfg.scheme=="chain":
        tx=u+{2:2,3:12,4:24}[w.pid]*k
        ty={2:-7,3:7,4:0}[w.pid]*k+y*.2
    else:
        tx=u+{2:8,3:12,4:23}[w.pid]*k
        ty=({2:-9,3:9,4:0}[w.pid])*k+y*.2
    if not attacking and w.pid!=1:
        tx-=12*k
    tx=clamp(tx,-h+12*k,h-7*k)
    if attacking and w.offside_enabled and cfg.offside_control and w.pid!=1:
        tx=min(tx,onside_limit(w,cfg)-1*k)
    # Search nearby support points for open receiving lanes, without adding a player.
    target=Point(s*tx,clamp(ty,-width+4*k,width-4*k))
    if attacking and w.pid!=1:
        points=[Point(s*clamp(tx+du*k,-h+12*k,min(h-7*k,onside_limit(w,cfg)-k) if w.offside_enabled and cfg.offside_control else h-7*k),
                      clamp(ty+dy*k,-width+4*k,width-4*k)) for du,dy in ((0,0),(-4,0),(0,-4),(0,4))]
        target=max(points,key=lambda pt: min(space(w,pt),8)+min(segment_clearance(w.ball,pt,w.opponents),6)*.7-.06*pt.distance(target))
    return target


def pass_menu(w,cfg):
    out=[]
    if not w.me:return out
    for mate in w.mine:
        if mate.pid==w.pid:continue
        d=w.me.pos.distance(mate.pos)
        progress=(mate.pos.x-w.me.pos.x)*w.sign
        if d<2 or d>cfg.pitch_half_length*(2 if stopped_phase(w) else 1):continue
        if progress<0 and mate.pos.x*w.sign < -cfg.pitch_half_length+14 and abs(mate.pos.y)<cfg.goal_half_width+5:continue
        if w.offside_enabled and cfg.offside_control and mate.pos.x*w.sign>onside_limit(w,cfg)+.05:continue
        lane=segment_clearance(w.me.pos,mate.pos,w.opponents)
        room=space(w,mate.pos)
        if lane<1.2 or room<1.8:continue
        # An explicit attack-value gain replaces retention as the ranking objective.
        risk=max(0,3-lane)*2+max(0,4-room)+max(0,d-25)*.12
        value=attack_value(w,cfg,mate.pos)-attack_value(w,cfg,w.me.pos)-risk-2
        if mate.pid==0:value-=12
        out.append(dict(pid=mate.pid,score=round(value,3),progress=progress,distance=d,clearance=lane,room=room))
    return sorted(out,key=lambda p:(-p['score'],p['pid']))


def presser_for(w,cfg):
    if w.status in {"ME","TEAM"} or stopped_phase(w):return None
    eligible=[p for p in w.mine if p.pid!=0 and (p.pid!=anchor_id(w,cfg) or w.ball.x*w.sign<-3)]
    if not eligible:return None
    if w.our_pass_in_flight:
        # Select the player ahead along the observed flight, rather than send
        # the passer after his own ball while the receiver retreats.
        vv=w.velocity.x*w.velocity.x+w.velocity.y*w.velocity.y
        def receive_cost(p):
            dt=clamp(((p.pos.x-w.ball.x)*w.velocity.x+(p.pos.y-w.ball.y)*w.velocity.y)/max(vv,.01),0,1.5)
            pt=Point(w.ball.x+dt*w.velocity.x,w.ball.y+dt*w.velocity.y)
            return p.pos.distance(pt)+dt*2+(5 if dt==0 else 0),p.pid
        return min(eligible,key=receive_cost).pid
    return min(eligible,key=lambda p:(p.pos.distance(w.ball),p.pid)).pid


def cover(w,cfg,presser,target):
    # Two players protect distinct threats. The last forward remains an outlet.
    if w.status!='OPP' or w.pid==4 or w.pid==presser:return target
    defenders=[p for p in w.mine if p.pid not in (0,4,presser)]
    threats=sorted([p for p in w.opponents if p.pid!=0],key=lambda p:p.pos.x*w.sign)
    assignments={}
    for opponent in threats:
        if not defenders:break
        mark=Point(opponent.pos.x-2*w.sign,opponent.pos.y)
        player=min(defenders,key=lambda p:p.pos.distance(mark))
        assignments[player.pid]=mark
        defenders.remove(player)
    return assignments.get(w.pid,target)


def plan_five(w,cfg):
    mode=profile_for(w,cfg)
    me=w.me
    target=shape(w,cfg,mode)
    presser=presser_for(w,cfg)
    target=cover(w,cfg,presser,target)
    coach=phase_decision(w,cfg) if cfg.phase_tactics != "off" else None
    if coach:
        if coach['defense_active']:presser=coach['presser']
        if w.pid!=0 and (coach['attack_active'] or coach['defense_active']):
            target=coach['targets'].get(w.pid,target)
    allowed,shot,aim=shot_facts(w,cfg)
    passes=pass_menu(w,cfg) if w.status=='ME' else []
    candidates=[]
    if not me or not me.active:
        candidates=[command(w,'SET_STANCE',{'stance':0})]
    elif w.status=='ME':
        kicks=[command(w,'PASS',{'target_player_id':p['pid'],'type':cfg.pass_type}) for p in passes[:3]]
        if w.pid==0:
            candidates=kicks+[move(w,target)]
        else:
            h=cfg.pitch_half_length
            maxu=-3 if w.pid==anchor_id(w,cfg) and not cfg.release_anchor else h-2
            # Carry toward a central finishing point; avoid touchline dead ends.
            u=me.pos.x*w.sign
            step=min(8,max(0,maxu-u))
            advance_u=max(u,min(maxu,u+step))
            points=[Point(w.sign*advance_u,clamp(me.pos.y+dy,-cfg.pitch_half_width+4,cfg.pitch_half_width-4)) for dy in (0,-5,5)]
            points.append(Point(w.sign*advance_u,me.pos.y*.65))
            def carry_value(pt):
                lane=segment_clearance(me.pos,pt,w.opponents)
                return attack_value(w,cfg,pt)-attack_value(w,cfg,me.pos)+min(lane,5)*1.2-max(0,2-lane)*4
            advance=max(points,key=carry_value)
            carry=move(w,advance,me.stamina>.4 and w.pid!=1)
            nearest=space(w,me.pos)
            shoot=command(w,'SHOOT',{'aim_location':aim,'power':1.0}) if allowed else None
            direct = cfg.scheme=='direct'
            if shoot and (cfg.early_shot or (direct and (w.pid==1 or shot['distance']<=30)) or shot['distance']<=14 or (shot['field_player_clearance']>=2.5 and nearest>6)):
                candidates.append(shoot)
            # Don't repeatedly exchange safe passes instead of carrying freely.
            valuable=[p for p in passes if p['score']>carry_value(advance)*.65 and p['progress']>3]
            if nearest<4:
                valuable=passes[:2]
            if cfg.minimal_passing:
                valuable=[p for p in passes if p['progress']>10 and p['score']>8 and p['room']>4]
                if w.pid==1 and not cfg.release_anchor:
                    valuable=passes[:2]
            candidates.extend(command(w,'PASS',{'target_player_id':p['pid'],'type':cfg.pass_type}) for p in valuable[:2])
            candidates.append(carry)
            candidates.extend(c for c in kicks if c not in candidates)
            if shoot and shoot not in candidates:candidates.append(shoot)
        if not me.can_kick:
            carries=[c for c in candidates if c['commandType']=='MOVE_TO']
            candidates=carries or [command(w,'SET_STANCE',{'stance':0})]
    elif w.pid==0:
        candidates=[move(w,target)]
        if w.status=='LOOSE' and w.ball.x*w.sign < -cfg.pitch_half_length+9 and abs(w.ball.y)<cfg.goal_half_width:
            if min(w.mine,key=lambda p:(p.pos.distance(w.ball),p.pid)).pid==0:
                candidates.insert(0,move(w,w.ball))
    elif presser==w.pid:
        if coach and coach['defense_active'] and w.status=='OPP' and me.pos.distance(w.ball)>3*cfg.pitch_half_length/50:
            candidates.append(move(w,target,me.stamina>.45))
        if w.status=='OPP' and me.pos.distance(w.ball)<=16*cfg.pitch_half_length/55:
            candidates.append(command(w,'PRESS_BALL',{'intensity':.9},1))
        speed=math.hypot(w.velocity.x,w.velocity.y)
        dt=min(.35,me.pos.distance(w.ball)/(6+speed))
        if w.our_pass_in_flight:
            vv=max(speed*speed,.01)
            dt=clamp(((me.pos.x-w.ball.x)*w.velocity.x+(me.pos.y-w.ball.y)*w.velocity.y)/vv,0,1.5)
        lead=Point(clamp(w.ball.x+w.velocity.x*dt,-cfg.pitch_half_length+1,cfg.pitch_half_length-1),
                   clamp(w.ball.y+w.velocity.y*dt,-cfg.pitch_half_width+1,cfg.pitch_half_width-1))
        candidates.append(move(w,lead,me.stamina>.35))
    else:
        candidates=[move(w,target,me.stamina>.5 and me.pos.distance(target)>6)]
    if stopped_phase(w) and me and me.active:
        candidates=[move(w,target)]
        if w.status=='ME' and w.restart_team==w.team:
            candidates=([command(w,'PASS',{'target_player_id':p['pid'],'type':cfg.pass_type}) for p in passes[:2]]
                        if me.can_kick and (w.restart_player is None or w.restart_player==w.pid) else []) or [command(w,'SET_STANCE',{'stance':0})]
    tactical_facts={k:v for k,v in coach.items() if k!='targets'} if coach else {}
    facts=dict(tactical=tactical_facts,role=('goalkeeper','anchor','pivot','second_forward' if cfg.scheme=='pair' else 'right_support','striker')[w.pid],
               scheme=cfg.scheme,formation=cfg.formation,players_per_side=5,outfield_players=4,possession=w.status,team=w.team,player=w.pid,
               attack_direction=w.sign,designated_presser=presser,score_us_them=[w.us,w.them],remaining_seconds=w.remaining,
               passes=passes,shot=shot,shape_target=[target.x,target.y],can_kick=me.can_kick if me else None,
               coach=list(w.coach),play_mode=w.play_mode,offside_enabled=w.offside_enabled,our_pass_in_flight=w.our_pass_in_flight)
    return Plan(candidates[0],tuple(candidates),facts,presser,tuple(p['pid'] for p in passes),allowed,target,mode)
