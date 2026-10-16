"""Four outfield support layouts; goalkeeper is deliberately excluded.

These are mobile support targets, not a claim that players remain in rigid lines.
The same pressing, marking, pass and shot rules apply to every layout.
"""
from .state import Point
from .tactics import clamp, onside_limit, segment_clearance

LAYOUTS = {
    "1-1-2": ((-16, 0), (5, 0), (17, -8), (22, 8)),
    "1-2-1": ((-16, 0), (8, -9), (12, 9), (23, 0)),
    "2-1-1": ((-14, -10), (-14, 10), (7, 0), (23, 0)),
    "2-2": ((-14, -10), (-14, 10), (18, -10), (18, 10)),
    "1-1-1-1": ((-18, 0), (-3, -7), (11, 7), (24, 0)),
    "3-1": ((-13, 0), (-10, -16), (-10, 16), (23, 0)),
    "1-3": ((-16, 0), (18, -16), (22, 0), (18, 16)),
    "4-0": ((-10, -18), (-3, -6), (3, 6), (9, 18)),
}

def anchor_id(w, cfg):
    if cfg.formation != "4-0":
        return 1
    # Everyone can advance; the deepest available teammate supplies cover.
    choices = [p for p in w.mine if p.pid != 0 and not (w.owner and p.pid == w.owner[1] and w.status in {"ME", "TEAM"})]
    return min(choices, key=lambda p: (p.pos.x*w.sign, p.pid)).pid if choices else 1

def support(w, cfg):
    k, h, width, s = cfg.pitch_half_length/50, cfg.pitch_half_length, cfg.pitch_half_width, w.sign
    attacking = w.status in {"ME", "TEAM"} or w.our_pass_in_flight
    u, y = w.ball.x*s, w.ball.y
    anchor = anchor_id(w, cfg)
    slot = w.pid-1
    if cfg.formation == "4-0":
        # Reassign lanes from observable current positions; avoid four agents
        # independently chasing the ball or rotating by an arbitrary timer.
        ordered = sorted((p for p in w.mine if p.pid), key=lambda p: (p.pos.y,p.pid))
        slot = next((i for i,p in enumerate(ordered) if p.pid==w.pid),slot)
    du, dy = LAYOUTS[cfg.formation][slot]
    tx, ty = u+du*k, dy*k+y*.2
    if w.pid == anchor and cfg.formation != "4-0":
        tx = min(tx, -3*k)
        ty = dy*k+y*.35
    if cfg.release_anchor and w.status == "TEAM" and w.owner and w.owner[1] == anchor and w.pid == 2:
        tx,ty = min(u-16*k,-3*k), y*.35
    if not attacking and w.pid != anchor:
        tx -= 12*k
    ceiling = min(h-7*k,onside_limit(w,cfg)-k) if attacking and w.offside_enabled and cfg.offside_control else h-7*k
    target = Point(s*clamp(tx,-h+12*k,ceiling),clamp(ty,-width+4*k,width-4*k))
    if attacking and w.pid != anchor:
        points=[Point(s*clamp(tx+dx*k,-h+12*k,ceiling),clamp(ty+dy*k,-width+4*k,width-4*k)) for dx,dy in ((0,0),(-4,0),(0,-4),(0,4))]
        def value(pt):
            room=min((pt.distance(o.pos) for o in w.opponents),default=100)
            return min(room,8)+min(segment_clearance(w.ball,pt,w.opponents),6)*.7-.06*pt.distance(target)
        target=max(points,key=value)
    return target
