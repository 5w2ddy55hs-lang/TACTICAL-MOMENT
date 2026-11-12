# Same-state local comparison base vs K20 for possession-related scenes.
# usage: python3 -I compare_poss.py base.json k20.json label
import json,sys,math
A=json.load(open(sys.argv[1]));B=json.load(open(sys.argv[2]));label=sys.argv[3]
def k20_override(x):
  pc=x['perc']
  if not pc.get('ball') or not pc.get('ourPossession') or pc.get('visibleHolder'):return False
  ot=pc.get('observedTouch')
  own=bool(ot) and all(s.split(':')[1]==x['team'] for s in ot['players'])
  return x['team'] and not own
def summ(P):
  fr=sorted(P['frames'],key=lambda f:f['t']);ev=P['events'];t0=fr[0]['t'];T=fr[-1]['t']
  touches=[e for e in ev if e['type'] in('kick','contact')]
  first=touches[0] if touches else None
  def poss_at(t):
    r=[e for e in ev if e['type']=='restart_placement' and e['t']<=t]
    c=[e for e in touches if e['t']<=t and (e['type']=='kick' or e.get('control'))]
    if r and (not c or r[-1]['t']>=c[-1]['t']):return 'restart:%s:%s'%(r[-1].get('kind'),r[-1].get('team'))
    return ('%s(%s)'%(c[-1]['team'],c[-1]['player'])) if c else 'none'
  ctrl=[e for e in touches if e['type']=='kick' or e.get('control')]
  firstCtrl=ctrl[0] if ctrl else None
  shots=[(e['t'],e['player'],e['team']) for e in ev if e['type']=='kick' and e.get('kind')=='shoot']
  goals=[(e['t'],e.get('team')) for e in ev if e['type']=='goal']
  ov=[x for x in P['decisions'] if k20_override(x)]
  # motion summary at +1,+2,+3 s: per team, nearest outfield player to ball and goal-side count
  mot={}
  for dt in (20,40,60):
    t=t0+dt
    f=next((g for g in fr if g['t']==t),None)
    if not f:continue
    b=f['ball'];row={}
    for team in 'AB':
      gk=[p for p in f['p'] if p['id']==team+'00'][0];gx=0 if gk['x']<52.5 else 105
      me=[p for p in f['p'] if p['id'][0]==team and p['id'][1:]!='00']
      row[team]={'nearest':round(min(math.hypot(p['x']-b[0],p['y']-b[1]) for p in me),1),'goalSide':sum(abs(p['x']-gx)<abs(b[0]-gx) for p in me)}
    mot[f'+{dt//20}s']=row
  return {'firstTouch':first and (first['t'],first['player'],first['type'],first.get('kind') or ('ctrl' if first.get('control') else 'noctrl')),
   'firstControl':firstCtrl and (firstCtrl['t'],firstCtrl['player'],firstCtrl['team']),'poss+3s':poss_at(t0+60),'poss+6s':poss_at(t0+120),'possEnd':poss_at(T),
   'shots':shots,'goals':goals,'k20OverrideDecisions':len(ov),'k20OverridePlayers':sorted({x['p'] for x in ov}),'motion':mot,'identicalFrames':None}
a,b=summ(A),summ(B)
same=json.dumps(A['frames'])==json.dumps(B['frames'])
print(json.dumps({'case':label,'identicalWholeWindow':same,'base':a,'k20':b},ensure_ascii=False))
