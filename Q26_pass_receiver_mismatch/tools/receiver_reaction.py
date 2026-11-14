# For every targeted pass: the receiver's FIRST receive/intercept decision after the kick (its own observation of the moving
# ball), where that receive target lies relative to the receiver's own motion at that moment (ahead / behind / lateral),
# the receiver's speed profile from the kick to the first touch (min speed = braking), and the angle between the ball's
# initial direction and the receiver's running direction at the kick. Audit truth from frames; decisions from rows.
# usage: python3 -I receiver_reaction.py <pass_trace.json> <out.json> <label>=<file.json.gz>[:arm] ...
import json,gzip,sys,math
trace=json.load(open(sys.argv[1]));out=[]
for spec in sys.argv[3:]:
  label,rest=spec.split('=',1);f,arm=(rest.rsplit(':',1)+[None])[:2] if rest.count(':') else (rest,None)
  d=json.load(gzip.open(f))
  if isinstance(d,list):d=next(c for c in d if c['name']==arm)
  F={x['tick']:x for x in d['frames']}
  pos=lambda t,i:next((p['x'],p['y']) for p in F[t]['players'] if p['id']==i)
  def vel(t,i):
    a,b=pos(t-1,i),pos(t,i);return ((b[0]-a[0])/.05,(b[1]-a[1])/.05)
  for t in [x for x in trace if x['window']==label]:
    K=t['kickTick'];R=t['receiver'];end=t['firstNext']['tick'] if t['firstNext'] else max(F)
    if K not in F or K-1 not in F:continue
    v0=vel(K+1,R) if K+1 in F else vel(K,R);s0=math.hypot(*v0)
    k=next(r for r in d['rows'] if r['channel']=='event' and r['type']=='kick' and r['tick']==K and r['player']==t['passer'])
    bv=(k['velocity']['x'],k['velocity']['y'])
    ang=None
    if s0>0.5:ang=round(math.degrees(math.acos(max(-1,min(1,(v0[0]*bv[0]+v0[1]*bv[1])/(s0*math.hypot(*bv)))))))
    rec=next((r for r in d['rows'] if r['channel']=='decision' and r['player']==R and K<r['tick']<=end and r['decision']['kind'] in('receive','intercept')),None)
    row={'window':label,'kickTick':K,'pair':t['passer']+'->'+R,'outcome':t['outcome'],'receiverSpeedAtKick':round(s0,2),'angleBallVsRun':ang}
    if rec:
      tt=rec['tick'];p=pos(tt,R);v=vel(tt,R);s=math.hypot(*v);tg=(rec['decision']['target']['x'],rec['decision']['target']['y']);dx=(tg[0]-p[0],tg[1]-p[1])
      along=(dx[0]*v[0]+dx[1]*v[1])/s if s>0.3 else None
      row['firstReceive']={'dt':round((tt-K)*.05,2),'kind':rec['decision']['kind'],'targetDist':round(math.hypot(*dx),2),'targetAlongOwnMotion':round(along,2) if along is not None else None,'ownSpeed':round(s,2),'eta':rec['decision'].get('eta')}
    sp=[(tt,math.hypot(*vel(tt,R))) for tt in range(K+1,min(end,K+60)+1) if tt in F and tt-1 in F]
    if sp:
      m=min(sp,key=lambda z:z[1]);row['speedMinUntilTouch']={'speed':round(m[1],2),'dt':round((m[0]-K)*.05,2)}
    row['closest']=t.get('receiverClosest');out.append(row)
json.dump(out,open(sys.argv[2],'w'),indent=1)
for r in out:
  fr=r.get('firstReceive',{});print(f"{r['window'][:20]:20s} {r['kickTick']} {r['pair']} {r['outcome'][:16]:16s} spd@kick {r['receiverSpeedAtKick']:5.2f} ballVsRun {r['angleBallVsRun']} | firstReceive +{fr.get('dt')}s tgtAlongMotion {fr.get('targetAlongOwnMotion')} tgtDist {fr.get('targetDist')} | minSpeed {r.get('speedMinUntilTouch')} | closest {r['closest'] and (r['closest']['dist'],r['closest']['dt'])}")
