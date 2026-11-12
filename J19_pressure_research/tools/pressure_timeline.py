# Per-chaser pressure analysis from a probe (ground truth positions, audit-only).
# usage: python3 -I pressure_timeline.py probe.json defendingTeam every_n_ticks
import json,sys,math
P=json.load(open(sys.argv[1]));T=sys.argv[2];step=int(sys.argv[3]) if len(sys.argv)>3 else 10
fr={f['t']:f for f in P['frames']};ticks=sorted(fr)
BALLDIR={'press','intercept','receive'}
latest={}
decs=sorted(P['decisions'],key=lambda d:d['t']);di=0
gk=lambda f,t:[p for p in f['p'] if p['id']==t+'00'][0]
for t in ticks:
  while di<len(decs) and decs[di]['t']<=t: latest[decs[di]['p']]=decs[di];di+=1
  if (t-ticks[0])%step: continue
  f=fr[t];bx,by=f['ball'][0],f['ball'][1];D=1 if gk(f,T)['x']<52.5 else -1;goal=0 if D==1 else 105
  me=[p for p in f['p'] if p['id'][0]==T and p['id'][1:]!='00'];op=[p for p in f['p'] if p['id'][0]!=T and p['id'][1:]!='00']
  carrier=min(op,key=lambda p:math.hypot(p['x']-bx,p['y']-by));cd=math.hypot(carrier['x']-bx,carrier['y']-by)
  rows=[]
  for p in me:
    d=latest.get(p['id']);k=d['kind'] if d else '-'
    if k not in BALLDIR: continue
    dx,dy=bx-p['x'],by-p['y'];dist=math.hypot(dx,dy) or 1e-6;close=(p['vx']*dx+p['vy']*dy)/dist;rel=((p['vx']-carrier['vx'])*dx+(p['vy']-carrier['vy'])*dy)/dist;spd=math.hypot(p['vx'],p['vy'])
    gs=abs(p['x']-goal)<abs(bx-goal)
    # opponents this player is the nearest defender to (within 12 m), excluding carrier: what he leaves
    left=[]
    for o in op:
      if o is carrier: continue
      dm=math.hypot(o['x']-p['x'],o['y']-p['y'])
      if dm>12: continue
      others=[q for q in me if q is not p and math.hypot(o['x']-q['x'],o['y']-q['y'])<dm]
      if not others and abs(o['x']-goal)<abs(bx-goal)+5: left.append(f"{o['id']}@{dm:.0f}m")
    rows.append(f"{p['id']}:{k[:5]} d={dist:4.1f} v={spd:3.1f} close={close:+4.1f} rel={rel:+4.1f} {'GS' if gs else 'bh'} t*={max(0,dist-1)/max(0.5,close) if close>0 else 99:4.1f}s leaves[{','.join(left)}]")
  gsn=[f"{p['id']}:{(latest.get(p['id']) or {}).get('kind','-')[:5]} d={math.hypot(p['x']-bx,p['y']-by):.0f} v=({p['vx']:+.1f},{p['vy']:+.1f})" for p in me if abs(p['x']-goal)<abs(bx-goal) and (latest.get(p['id']) or {}).get('kind') not in BALLDIR and math.hypot(p['x']-bx,p['y']-by)<25]
  print(f"t={t} ball=({bx:.1f},{by:.1f}) carrier={carrier['id']}({cd:.1f}m) v=({carrier['vx']:+.1f},{carrier['vy']:+.1f}) dir={D}")
  for r in rows: print('   ',r)
  print('    goal-side non-chasers <25m:',' | '.join(gsn))
