# Generic per-tick timeline of one pass from a recorded window: ball, receiver (speed, move direction, decision kind,
# target, distance to ball, distance to own decision target) and the two nearest opponents. Audit truth only.
# usage: python3 -I timeline_pass.py <rec.json.gz> <kickTick> <receiver> <ticksAfter> <step> <out.json>
import json,gzip,sys,math
d=json.load(gzip.open(sys.argv[1]));K=int(sys.argv[2]);R=sys.argv[3];N=int(sys.argv[4]);st=int(sys.argv[5])
F={f['tick']:f for f in d['frames']};dec={}
for r in d['rows']:
  if r['channel']=='decision':dec.setdefault(r['player'],[]).append(r)
P=lambda t,i:next(p for p in F[t]['players'] if p['id']==i)
team=P(K,R)['team'];rows=[]
for t in range(K-2,K+N+1,st):
  if t not in F or t-1 not in F:continue
  b=F[t]['ball'];p,q=P(t,R),P(t-1,R);vx,vy=(p['x']-q['x'])/.05,(p['y']-q['y'])/.05
  dd=[z for z in dec.get(R,[]) if z['tick']<=t];x=dd[-1]['decision'] if dd else {}
  tg=x.get('target');opp=sorted(((o['id'],math.hypot(o['x']-b['x'],o['y']-b['y'])) for o in F[t]['players'] if o['team']!=team),key=lambda z:z[1])[:2]
  rows.append({'dt':round((t-K)*.05,2),'ball':[round(b['x'],1),round(b['y'],1)],'ballSpeed':round(math.hypot(b['vx'],b['vy']),1),'recv':[round(p['x'],1),round(p['y'],1)],'speed':round(math.hypot(vx,vy),1),'moveDir':round(math.degrees(math.atan2(vy,vx))),
   'kind':x.get('kind'),'reason':x.get('reason'),'target':[round(tg['x'],1),round(tg['y'],1)] if tg else None,'toBall':round(math.hypot(p['x']-b['x'],p['y']-b['y']),1),'toOwnTarget':round(math.hypot(p['x']-tg['x'],p['y']-tg['y']),1) if tg else None,'opp':[(i,round(v,1)) for i,v in opp]})
json.dump(rows,open(sys.argv[6],'w'),indent=1)
for r in rows:print(f"  +{r['dt']:4.2f}s ball{r['ball']} v{r['ballSpeed']:4.1f} | {R} {str(r['kind'])[:9]:9s} spd{r['speed']:4.1f} dir{r['moveDir']:5d} toBall{r['toBall']:5.1f} tgt{r['target']} toTgt{r['toOwnTarget']} | opp {r['opp']}")
