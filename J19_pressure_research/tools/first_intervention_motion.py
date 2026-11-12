# Actual-motion check at the FIRST J19 intervention of a same-state local pair (only there are
# base and J19 states identical up to the decision). Compares, at +0.4/+0.8/+1.2 s:
#  - each J19-affected player's real distance to its own decision target (did motion follow?)
#  - route protection: min distance of defending outfield players (excluding pure trailers) to the
#    segment carrier -> own goal centre, and of the affected player itself
#  - engager's real distance to the carrier and whether it is goal-side
# usage: python3 -I first_intervention_motion.py base.json j19.json defTeam label
import json,sys,math
A=json.load(open(sys.argv[1]));B=json.load(open(sys.argv[2]));T=sys.argv[3];label=sys.argv[4]
def seg(px,py,ax,ay,bx,by):
  dx,dy=bx-ax,by-ay;L=dx*dx+dy*dy;t=0 if L==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L));return math.hypot(px-ax-t*dx,py-ay-t*dy)
first=min((d for d in B['decisions'] if d['reason'].startswith('J19') and d['p'][0]==T),key=lambda d:d['t'])
t0=first['t'];same=[d for d in B['decisions'] if d['t']==t0 and d['reason'].startswith('J19') and d['p'][0]==T]
fa={f['t']:f for f in A['frames']};fb={f['t']:f for f in B['frames']}
gk=[p for p in fa[t0]['p'] if p['id']==T+'00'][0];gx=0 if gk['x']<52.5 else 105
def state(F,t,pid):
  f=F[t];bx,by=f['ball'][0],f['ball'][1];op=[p for p in f['p'] if p['id'][0]!=T];car=min(op,key=lambda p:math.hypot(p['x']-bx,p['y']-by))
  me=[p for p in f['p'] if p['id'][0]==T and p['id'][1:]!='00'];P=[p for p in me if p['id']==pid][0]
  gs=[p for p in me if abs(p['x']-gx)<abs(car['x']-gx)]
  return {'carrier':car['id'],'playerRouteDist':round(seg(P['x'],P['y'],car['x'],car['y'],gx,34),2),'playerCarrierDist':round(math.hypot(P['x']-car['x'],P['y']-car['y']),2),'playerGoalSide':abs(P['x']-gx)<abs(car['x']-gx),
   'teamMinRouteDistGoalSide':round(min([seg(p['x'],p['y'],car['x'],car['y'],gx,34) for p in gs] or [99]),2),'goalSideCount':len(gs)}
out={'case':label,'firstTick':t0,'applyTick':first.get('applyTick'),'players':[]}
for d in same:
  tgt=d['target'];row={'player':d['p'],'j19':'yield' if 'yield' in d['reason'] else 'engage','target':tgt}
  for dt in (0,8,16,24):
    t=t0+dt
    if t not in fa or t not in fb: continue
    pa=[p for p in fa[t]['p'] if p['id']==d['p']][0];pb=[p for p in fb[t]['p'] if p['id']==d['p']][0]
    row[f'+{dt/20:.1f}s']={'base':{**state(fa,t,d['p']),'distToJ19Target':round(math.hypot(pa['x']-tgt[0],pa['y']-tgt[1]),2)},'j19':{**state(fb,t,d['p']),'distToJ19Target':round(math.hypot(pb['x']-tgt[0],pb['y']-tgt[1]),2)}}
  # re-decisions of this player within 0.8 s in the J19 run
  row['redecisionsWithin0.8s_j19']=[(x['t'],x['kind'],x['reason'][:24]) for x in B['decisions'] if x['p']==d['p'] and t0<x['t']<=t0+16]
  out['players'].append(row)
print(json.dumps(out,ensure_ascii=False))
