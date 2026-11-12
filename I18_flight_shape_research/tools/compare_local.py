# Compare base vs I18 probes from the SAME starting state for one key pass kick.
# usage: python3 -I compare_local.py base.json i18.json <passKickTick> <label>
# Outputs JSON lines with movement/shape at first touch, attack exit, defensive state, next play.
import json,sys,math
A=json.load(open(sys.argv[1]));B=json.load(open(sys.argv[2]));K=int(sys.argv[3]);label=sys.argv[4]
def info(P):
  fr={f['t']:f for f in P['frames']};ev=P['events'];dec=P['decisions']
  kk=[e for e in ev if e['type']=='kick' and e['t']==K]
  if not kk: return {'error':'kick not present in this run (diverged before)'}
  k=kk[0];team=k['team'];opp='B' if team=='A' else 'A'
  gk=[p for p in fr[K]['p'] if p['id']==team+'00'][0];D=1 if gk['x']<52.5 else -1;own_goal=0 if D==1 else 105
  after=[e for e in ev if e['t']>K and e['type'] in('kick','contact') and not (e['player']==k['player'] and e['t']-K<=3)]
  dead=[f['t'] for f in P['frames'] if f['t']>K and f['phase']!='play']
  first=after[0] if after else None;t1=first['t'] if first else max(fr)
  if dead and dead[0]<t1: t1=dead[0];first={'player':None,'team':None,'type':'dead'}
  P0={p['id']:p for p in fr[K]['p']};P1={p['id']:p for p in fr[t1]['p']}
  mates=[i for i in P0 if i[0]==team and i[1:]!='00' and i!=k['player'] and i!=k.get('targetId')]
  fwd=sum((P1[i]['x']-P0[i]['x'])*D for i in mates)/len(mates)
  kinds={}
  for d in dec:
    if d['p'] in mates and K<d['t']<=t1: kinds[d['kind']]=kinds.get(d['kind'],0)+1
  bx,by=fr[t1]['ball'][0],fr[t1]['ball'][1]
  oppP=[p for p in fr[t1]['p'] if p['id'][0]==opp]
  ahead=[i for i in P1 if i[0]==team and i[1:]!='00' and (P1[i]['x']-bx)*D>2 and math.hypot(P1[i]['x']-bx,P1[i]['y']-by)<30 and min(math.hypot(P1[i]['x']-q['x'],P1[i]['y']-q['y']) for q in oppP)>3]
  goal_side=lambda t:sum(1 for p in fr[t]['p'] if p['id'][0]==team and p['id'][1:]!='00' and abs(p['x']-own_goal)<abs(fr[t]['ball'][0]-own_goal))
  central=lambda t:sum(1 for p in fr[t]['p'] if p['id'][0]==team and p['id'][1:]!='00' and abs(p['x']-own_goal)<30 and abs(p['y']-34)<14)
  t3=min(max(fr),t1+60)
  nxt=[e for e in ev if e['t']>t1 and e['type']=='kick'][:4]
  shots=[e for e in ev if e['type']=='kick' and e['kind']=='shoot' and K<e['t']<=K+300]
  claims=sum(1 for d in dec if K<d['t']<=t1 and d['reason']=='I18_witnessed_teammate_kick_uncontested')
  return {'passer':k['player'],'target':k.get('targetId'),'team':team,'firstTouch':{'t':t1,'player':first and first['player'],'team':first and first['team'],'type':first and first['type'],'control':first and first.get('control')},
   'flightS':round((t1-K)/20,2),'matesMeanFwdDuringFlight':round(fwd,2),'mateDecisionKinds':kinds,'i18Claims':claims,
   'openForwardOptionsAtFirstTouch':len(ahead),'goalSideAtFirstTouch':goal_side(t1),'goalSideAt+3s':goal_side(t3),'centralGuardsAtFirstTouch':central(t1),'centralGuardsAt+3s':central(t3),
   'next4kicks':[(e['t'],e['player'],e['kind']) for e in nxt],'shotsWithin15s':[(e['t'],e['player'],e['team']) for e in shots]}
print(json.dumps({'case':label,'kick':K,'base':info(A),'i18':info(B)},ensure_ascii=False))
