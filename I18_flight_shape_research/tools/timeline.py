# Summarize a probe: for each pass kick in window, passing team's outfield players
# decision kinds/targets, observedTouch evidence, applied action, and real movement (forward = attack dir).
import json,sys,math
d=json.load(open(sys.argv[1]));frames={f['t']:f for f in d['frames']}
ev=d['events'];decs=d['decisions']
kicks=[e for e in ev if e['type']=='kick' and e['kind'] in('pass','restart_kick')]
def dirOf(team,t):
  f=frames[t];gk=[p for p in f['p'] if p['id']==team+'00'][0];return 1 if gk['x']<52.5 else -1
for k in kicks:
  t0=k['t'];team=k['team'];later=[e for e in ev if e['t']>t0 and e['player']!=k['player'] and e['type'] in('kick','contact')]
  t1=later[0]['t'] if later else max(frames);first=later[0] if later else None
  if t1-t0<6: continue
  D=dirOf(team,t0)
  print(f"\n== {t0} {k['player']} {k['kind']}->{k.get('targetId')}  first touch {t1} by {first and first['player']} ({first and first['type']}{' ctrl' if first and first.get('control') else ''})  flight {(t1-t0)/20:.2f}s dir {D}")
  for pid in [p['id'] for p in frames[t0]['p'] if p['id'][0]==team and p['id'][1:]!='00']:
    ds=[x for x in decs if x['p']==pid and t0-10<=x['t']<=t1]
    seq=' '.join(f"{x['t']}:{x['kind'][:5]}{'*' if x['dto']['observedTouch'] and x['dto']['observedTouch']['players'][0]['team']==team and x['dto']['observedTouch']['players'][0]['part']=='foot' and x['dto']['observedTouch']['seenTick']>=t0 else ''}" for x in ds)
    a0=frames[t0]['p'];a1=frames[t1]['p'];p0=[p for p in a0 if p['id']==pid][0];p1=[p for p in a1 if p['id']==pid][0]
    acts=[]
    for t in range(t0,t1+1):
      a=[p for p in frames[t]['p'] if p['id']==pid][0]['act']
      if not acts or acts[-1][1]!=a: acts.append((t,a))
    fwd=(p1['x']-p0['x'])*D
    print(f"  {pid}{'(T)' if pid==k.get('targetId') else ''} dec[{seq}] act[{' '.join(f'{t}:{a}' for t,a in acts)}] move fwd {fwd:+.1f}m lat {p1['y']-p0['y']:+.1f}")
