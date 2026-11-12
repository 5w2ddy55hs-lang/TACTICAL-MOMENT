# Compare base vs J19 probes started from the SAME state, from the defending team's view.
# usage: python3 -I compare_pressure.py base.json j19.json <defTeam> <label>
import json,sys,math
A=json.load(open(sys.argv[1]));B=json.load(open(sys.argv[2]));T=sys.argv[3];label=sys.argv[4]
BD={'press','intercept','receive'}
def summ(P):
  fr=sorted(P['frames'],key=lambda f:f['t']);ev=P['events'];dec=sorted(P['decisions'],key=lambda d:d['t'])
  gk=[p for p in fr[0]['p'] if p['id']==T+'00'][0];goal=0 if gk['x']<52.5 else 105
  t0=fr[0]['t'];b0=abs(fr[0]['ball'][0]-goal)
  regain=next((e for e in ev if e['type'] in('kick','contact') and e.get('team')==T and (e['type']=='kick' or e.get('control'))),None)
  rp=next((e for e in ev if e['type']=='restart_placement'),None)
  endReason='window_end';tEnd=fr[-1]['t']
  if regain and (not rp or regain['t']<=rp['t']): tEnd=regain['t'];endReason=f"regain_by_{regain['player']}"
  elif rp: tEnd=rp['t'];endReason=f"restart_{rp.get('kind')}_for_{rp.get('team')}";regain=rp if rp.get('team')==T else None
  if regain and regain is rp: regain={'t':rp['t'],'player':'restart:'+str(rp.get('kind'))}
  latest={};di=0;maxBD=0;ge3=0;same3=0;engaged=None;chasers=set();n=0;minGoal=b0
  for f in fr:
    while di<len(dec) and dec[di]['t']<=f['t']: latest[dec[di]['p']]=dec[di];di+=1
    if f['t']>tEnd or f['phase']!='play': continue
    n+=1;bx,by=f['ball'][0],f['ball'][1];minGoal=min(minGoal,abs(bx-goal))
    me=[p for p in f['p'] if p['id'][0]==T and p['id'][1:]!='00']
    bd=[p for p in me if (latest.get(p['id']) or {}).get('kind') in BD];chasers|={p['id'] for p in bd}
    maxBD=max(maxBD,len(bd));ge3+=len(bd)>=3
    tg=[(latest[p['id']]['target'] or [0,0]) for p in bd];best=max([sum(1 for u in tg if math.hypot(u[0]-v[0],u[1]-v[1])<2) for v in tg] or [0]);same3+=best>=3
    if engaged is None and any(abs(p['x']-goal)<abs(bx-goal) and math.hypot(p['x']-bx,p['y']-by)<3 for p in me): engaged=f['t']
  opp=[e for e in ev if e['type']=='kick' and e.get('team') and e['team']!=T and e['t']<=tEnd and e.get('kind') in('pass','shoot')]
  j19=[(d['t'],d['p'],'yield' if 'yield' in d['reason'] else 'engage') for d in dec if d['reason'].startswith('J19')]
  goals=[e for e in ev if e['type']=='goal']
  return {'endReason':endReason,'regain':(regain['t'],regain['player']) if regain else None,'secsToRegain':round((tEnd-t0)/20,2) if regain else None,'ballAdvanceToOwnGoal':round(b0-minGoal,1),
   'firstGoalSideWithin3m':engaged,'secsToGoalSide3m':round((engaged-t0)/20,2) if engaged else None,'maxSimultaneousBallDirected':maxBD,'ticksGe3':ge3,'ticksSameTargetGe3':same3,'distinctChasers':sorted(chasers),
   'oppPassesShotsBeforeRegain':[(e['t'],e['player'],e['kind']) for e in opp],'goals':[(e['t'],e.get('team')) for e in goals],'j19Decisions':len(j19),'j19ByPlayer':sorted({(p,k) for _,p,k in j19})}
print(json.dumps({'case':label,'defTeam':T,'base':summ(A),'j19':summ(B)},ensure_ascii=False))
