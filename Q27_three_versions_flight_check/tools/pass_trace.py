# Per-pass trace: what the PASSER knew at its decision (own observation DTO only) vs what the RECEIVER actually did
# (audit-only truth from the public frames, plus the receiver's own decisions/observations), the ball, and opponents.
# Works on any recorded window of the shape {frames:[view per tick], rows:[sink rows incl. 'event','decision']}.
# Frame i = state BEFORE processing tick frames[i].tick; an event with tick T happens during the processing of T.
# usage: python3 -I pass_trace.py <out.json> <label>=<file.json.gz>[:<armName>] ...
import json,gzip,sys,math
DT=0.05
def load(spec):
  label,f=spec.split('=',1);arm=None
  if f.endswith(':base') or ':' in f.split('/')[-1]:f,arm=f.rsplit(':',1)
  d=json.load(gzip.open(f))
  if isinstance(d,list):d=next(c for c in d if c['name']==arm)
  return label,d
def H(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def trace(label,d):
  F={f['tick']:f for f in d['frames']};T0=min(F);T1=max(F)
  pos=lambda t,pid:next(((p['x'],p['y']) for p in F[t]['players'] if p['id']==pid),None) if t in F else None
  team={p['id']:p['team'] for p in d['frames'][0]['players']}
  ballp=lambda t:(F[t]['ball']['x'],F[t]['ball']['y'],F[t]['ball']['z']) if t in F else None
  vel=lambda t,pid:(lambda a,b:((b[0]-a[0])/DT,(b[1]-a[1])/DT) if a and b else None)(pos(t-1,pid) or pos(t,pid),pos(t,pid) if pos(t-1,pid) else pos(t+1,pid))
  ev=[r for r in d['rows'] if r['channel']=='event'];dec=[r for r in d['rows'] if r['channel']=='decision']
  out=[]
  for k in ev:
    if k['type']!='kick' or k.get('kind')!='pass' or not k.get('targetId'):continue
    K=k['tick'];P=k['player'];R=k['targetId'];side=team[P]
    # originating decision: latest passer decision (plain pass or pre-planned ballActionIntent) to this receiver applied by K
    src=None
    for r in dec:
      if r['player']!=P or r['tick']>K:continue
      x=r['decision'];bi=x.get('ballActionIntent')
      if x.get('kind')=='pass' and x.get('targetId')==R and x.get('applyTick',K)<=K:src=(r,x,'ordinary_pass_decision')
      elif bi and bi.get('kind')=='pass' and bi.get('targetId')==R and bi.get('applyTick',K)<=K:src=(r,bi,'early_ball_intent('+str(x.get('kind'))+')')
    row={'window':label,'kickTick':K,'passer':P,'receiver':R,'team':side}
    if src:
      r,x,how=src;o=r['observation'];q=next((p for p in o['people'] if p['id']==R),None);tD=r['tick']
      aim=(x['target']['x'],x['target']['y'])
      row['decision']={'tick':tD,'how':how,'reason':x.get('reason'),'aim':[round(aim[0],2),round(aim[1],2)],'aimDistFromBall':round(H(aim,(o['ball']['x'],o['ball']['y'])),2) if o.get('ball') else None}
      if q:
        v=(q['vx'],q['vy']);sp=math.hypot(*v);age=o['tick']-q['seenTick']
        lead=((aim[0]-q['x'])*v[0]+(aim[1]-q['y'])*v[1])/(sp*sp) if sp>0.05 else None
        row['passerView']={'receiverPos':[round(q['x'],2),round(q['y'],2)],'receiverVel':[round(v[0],2),round(v[1],2)],'speed':round(sp,2),'ageTicks':age,'impliedLeadSeconds':round(lead,3) if lead is not None else None}
        tp=pos(tD,R);tv=vel(tD,R)
        if tp:row['truthAtDecision']={'receiverPos':[round(tp[0],2),round(tp[1],2)],'receiverVel':[round(tv[0],2),round(tv[1],2)] if tv else None,'posErr':round(H(tp,(q['x'],q['y'])),2),'velErr':round(H(tv,v),2) if tv else None}
        # the receiver's own plan at the passer's decision tick (private to the receiver)
        own=[z for z in dec if z['player']==R and z['tick']<=tD];own=own[-1] if own else None
        if own:row['receiverOwnPlanAtDecision']={'tick':own['tick'],'kind':own['decision']['kind'],'target':[round(own['decision']['target']['x'],2),round(own['decision']['target']['y'],2)] if own['decision'].get('target') else None,'distToOwnTarget':round(H(tp,(own['decision']['target']['x'],own['decision']['target']['y'])),2) if own['decision'].get('target') and tp else None}
    # ball after the kick
    bv=(k['velocity']['x'],k['velocity']['y']);row['kick']={'origin':[round(k['position']['x'],2),round(k['position']['y'],2)],'speed':round(math.hypot(*bv),2),'passerTruthPos':[round(k['playerPosition']['x'],2),round(k['playerPosition']['y'],2)]}
    nxt=next((e for e in ev if e['tick']>K and (e['type'] in('kick','contact') and not (e.get('player')==P and e['tick']-K<=3) or e['type'] in('restart_placement','goal'))),None)
    end=nxt['tick'] if nxt else T1
    row['firstNext']={'tick':nxt['tick'],'dt':round((nxt['tick']-K)*DT,2),'type':nxt['type'],'player':nxt.get('player') or nxt.get('taker'),'team':nxt.get('team'),'kind':nxt.get('kind'),'control':nxt.get('control')} if nxt else None
    if nxt:
      o_=('out' if nxt['type'] in('restart_placement','goal') else ('target' if nxt.get('player')==R else ('teammate' if nxt.get('team')==side else 'opponent')))
      if o_ in('target','teammate','opponent'):o_+=('_control' if (nxt['type']=='kick' or nxt.get('control')) else '_no_control')
      row['outcome']=o_
    else:row['outcome']='window_end'
    # receiver vs ball during flight
    ts=[t for t in range(K+1,end+1) if t in F]
    if ts:
      dd=[(t,H(pos(t,R),ballp(t)[:2])) for t in ts];tm,dm=min(dd,key=lambda z:z[1])
      row['receiverClosest']={'tick':tm,'dt':round((tm-K)*DT,2),'dist':round(dm,2),'ballZ':round(ballp(tm)[2],2)}
      if src:
        # ball arrival near the aim: tick of closest ball approach to the aim
        ta,da=min(((t,H(ballp(t)[:2],aim)) for t in ts),key=lambda z:z[1])
        rp=pos(ta,R);row['ballNearAim']={'tick':ta,'dt':round((ta-K)*DT,2),'ballToAim':round(da,2),'receiverToAim':round(H(rp,aim),2)}
        if q and sp>0.05:
          u=(v[0]/sp,v[1]/sp);dx=(rp[0]-aim[0],rp[1]-aim[1])
          row['ballNearAim']['receiverAheadOfAimAlongSeenRun']=round(dx[0]*u[0]+dx[1]*u[1],2);row['ballNearAim']['receiverLateral']=round(-dx[0]*u[1]+dx[1]*u[0],2)
          # constant-velocity prediction of the passer vs truth at that time
          tau=(ta-o['tick'])*DT+age*DT;pred=(q['x']+v[0]*tau,q['y']+v[1]*tau);row['ballNearAim']['constVelPredErr']=round(H(pred,rp),2)
          ex=(rp[0]-pred[0],rp[1]-pred[1]);row['ballNearAim']['constVelErrAlongRun']=round(ex[0]*u[0]+ex[1]*u[1],2)
      # receiver's own decisions during the flight (compressed) and when it first saw the moving ball
      rs=[z for z in dec if z['player']==R and K<z['tick']<=end];seq=[]
      for z in rs:
        kk=z['decision']['kind']
        if not seq or seq[-1][1]!=kk:seq.append((z['tick']-K,kk))
      row['receiverDecisionsAfterKick']=seq[:8]
      fs=next((z for z in rs if z['observation'].get('ball') and z['observation']['ball']['seenTick']>K and z['observation']['ball'].get('velocityKnown')),None)
      row['receiverFirstSawMovingBall']=None if not fs else {'decisionDt':round((fs['tick']-K)*DT,2),'kind':fs['decision']['kind']}
      rv=vel(K,R);row['truthAtKick']={'receiverPos':[round(pos(K,R)[0],2),round(pos(K,R)[1],2)],'receiverVel':[round(rv[0],2),round(rv[1],2)] if rv else None,'receiverSpeed':round(math.hypot(*rv),2) if rv else None,'heading':next((p.get('heading') for p in F[K]['players'] if p['id']==R),None) if K in F else None}
      # opponents
      opp=[p['id'] for p in d['frames'][0]['players'] if p['team']!=side]
      od=[(t,o2,H(pos(t,o2),ballp(t)[:2])) for t in ts for o2 in opp];tt,oo,dmin=min(od,key=lambda z:z[2])
      row['opponentClosest']={'player':oo,'tick':tt,'dt':round((tt-K)*DT,2),'dist':round(dmin,2),'receiverDistThen':round(H(pos(tt,R),ballp(tt)[:2]),2)}
      if row['outcome'].startswith('opponent'):
        z=[z for z in dec if z['player']==nxt['player'] and z['tick']<=nxt['tick']];row['opponentDecisionBeforeTouch']=z[-1]['decision']['kind'] if z else None
    out.append(row)
  return out
if __name__=='__main__':
  res=[]
  for spec in sys.argv[2:]:
    label,d=load(spec);res+=trace(label,d)
  json.dump(res,open(sys.argv[1],'w'),indent=1,ensure_ascii=False)
  for r in res:
    pv=r.get('passerView',{});bn=r.get('ballNearAim',{})
    print(f"{r['window']:22s} {r['kickTick']} {r['passer']}->{r['receiver']} {r.get('decision',{}).get('how','?')[:28]:28s} lead={pv.get('impliedLeadSeconds')} seenSpd={pv.get('speed')} kickSpd={r['kick']['speed']} aimDist={r.get('decision',{}).get('aimDistFromBall')} | ballNearAim dt={bn.get('dt')} recvAhead={bn.get('receiverAheadOfAimAlongSeenRun')} lat={bn.get('receiverLateral')} cvErr={bn.get('constVelPredErr')} | closest {r.get('receiverClosest',{}).get('dist')}@{r.get('receiverClosest',{}).get('dt')} | opp {r.get('opponentClosest',{}).get('player')} {r.get('opponentClosest',{}).get('dist')} | {r['outcome']} {r['firstNext'] and (r['firstNext']['player'],r['firstNext']['dt'])}")
