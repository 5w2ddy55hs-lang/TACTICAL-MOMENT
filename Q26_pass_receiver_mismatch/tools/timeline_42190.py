# Same-state timeline of the 42188/42190 A05->A10 pass in the baseline and the recorded flight-time candidate:
# every 2 ticks from the kick: ball, receiver A10 (position, speed, heading of motion, current decision kind/target),
# the opponents B07 and B10, distances. Audit truth from the recorded frames; decisions from the recorded rows.
# usage: python3 -I timeline_42190.py <comparison.json.gz> <out.json>
import json,gzip,sys,math
d={c['name']:c for c in json.load(gzip.open(sys.argv[1]))};out={}
for arm in('base','flight_candidate'):
  c=d[arm];F={f['tick']:f for f in c['frames']};dec={}
  for r in c['rows']:
    if r['channel']=='decision' and r['player'] in('A10','B07','B10'):dec.setdefault(r['player'],[]).append(r)
  P=lambda t,i:next(p for p in F[t]['players'] if p['id']==i)
  rows=[]
  for t in range(42188,42262,2):
    if t not in F or t-1 not in F:continue
    b=F[t]['ball'];row={'t':t,'dt':round((t-42190)*0.05,2),'ball':[round(b['x'],1),round(b['y'],1)],'ballSpeed':round(math.hypot(b['vx'],b['vy']),1)}
    for i in('A10','B07','B10'):
      p,q=P(t,i),P(t-1,i);vx,vy=(p['x']-q['x'])/.05,(p['y']-q['y'])/.05;dd=[z for z in dec.get(i,[]) if z['tick']<=t];x=dd[-1]['decision'] if dd else {}
      row[i]={'pos':[round(p['x'],1),round(p['y'],1)],'speed':round(math.hypot(vx,vy),1),'moveDir':round(math.degrees(math.atan2(vy,vx))),'toBall':round(math.hypot(p['x']-b['x'],p['y']-b['y']),1),'kind':x.get('kind'),'target':[round(x['target']['x'],1),round(x['target']['y'],1)] if x.get('target') else None}
    rows.append(row)
  out[arm]=rows
json.dump(out,open(sys.argv[2],'w'),indent=1)
for arm,rows in out.items():
  print('##',arm)
  for r in rows[::2]:print(f"  +{r['dt']:4.1f}s ball{r['ball']} v{r['ballSpeed']:4.1f} | A10 {r['A10']['kind'][:9]:9s} spd{r['A10']['speed']:4.1f} dir{r['A10']['moveDir']:5d} toBall{r['A10']['toBall']:5.1f} tgt{r['A10']['target']} | B07 {str(r['B07']['kind'])[:8]:8s} toBall{r['B07']['toBall']:5.1f} | B10 toBall{r['B10']['toBall']:5.1f}")
