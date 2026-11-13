# Classify lost/gained possession cases from yield_probe outputs (audit-only truth used for classification).
# usage: python3 -I classify.py <probeDir> <jobs.txt> <cases_lost_gained.json> <out.json>
import json,sys,math,collections
P,jobs,casesF,outF=sys.argv[1:5]
cases=json.load(open(casesF));ref={}
for k in ('lost','gained'):
  for c in cases[k]:ref[(c['seed'],c['t'])]=c
res=[];C=collections.Counter()
def first_after(ev,t,pred):
  for x in ev:
    if x['t']>=t and pred(x):return x
  return None
for line in open(jobs):
  N,seed,T,sv,team=line.split();seed=int(seed);t=int(T)-1
  d=json.load(open(f'{P}/{N}.json'));c=ref[(seed,t)]
  match=(d['base']['poss6']==c['base'] and d['k20']['poss6']==c['k20'] and d['l21']['poss6']==c['l21'])
  opp='B' if team=='A' else 'A'
  L=d['l21'];K=d['k20'];B=d['base']
  touches=lambda R:[x for x in R['events'] if x['type'] in('kick','contact')]
  cls=None;detail={}
  if N.startswith('L') and not N.startswith('LK') or N.startswith('G'):
    # L21 vs K20 differ only via yields: inspect the first yield
    y=L['yields'][0] if L['yields'] else None
    if not y: cls='no_yield_recorded'
    else:
      ty=y['t'];col=[q['id'] for q in y['collectors']]
      tl=[x for x in touches(L) if x['t']>=ty];tk=[x for x in touches(K) if x['t']>=ty]
      fl=tl[0] if tl else None;fk=tk[0] if tk else None
      detail={'yieldTick':ty,'yielder':y['p'],'from':y['from'],'to':y['to'],'collectors':y['collectors'],'l21FirstTouchAfter':fl,'k20FirstTouchAfter':fk,'nYields':len(L['yields'])}
      colTouch=bool(fl) and fl['p'] in col
      colCtrl=colTouch and fl['ctrl']
      if fl is None: cls='no_touch_after_yield'
      elif fl['team']!=team and (fk is None or fk['team']!=team): cls='opponent_first_in_both'
      elif fl['team']!=team and fk and fk['team']==team and fk['p']==y['p']: cls='yielder_would_have_won_ball_in_K20'
      elif fl['team']!=team and fk and fk['team']==team: cls='opponent_first_in_L21_teammate_first_in_K20'
      elif colCtrl: cls='collector_controlled'
      elif colTouch and not fl['ctrl']: cls='collector_touched_no_control'
      elif fl['team']==team: cls='other_teammate_first'
      else: cls='undetermined'
      # whether the outcome difference arises long after the first yield (later divergence)
      detail['secondsYieldToEnd']=round((L['t0']+120-ty)/20,2)
  else:
    cls='k20_shared'
  key=N[:2] if N.startswith('LK') else N[0]
  C[(key,cls)]+=1
  res.append({'case':N,'seed':seed,'t':t,'team':team,'reproduced':match,'class':cls,'poss6':{'base':B['poss6'],'k20':K['poss6'],'l21':L['poss6']},**detail})
json.dump(res,open(outF,'w'),ensure_ascii=False,indent=0)
print('reproduced',sum(r['reproduced'] for r in res),'/',len(res))
for k,v in sorted(C.items()):print(k,v)
