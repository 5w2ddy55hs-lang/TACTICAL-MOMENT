# For each case: first differing ball event between K20 and L21 runs, the L21 yields before it, and what
# kind of "evident collector" was trusted (reach vs closing, alongside, opponent proximity).
import json,sys,collections
P,cl,outF=sys.argv[1],sys.argv[2],sys.argv[3]
R=json.load(open(cl));out=[];C=collections.Counter();Y=collections.Counter()
key=lambda x:(x['t'],x['type'],x.get('p'),x.get('ctrl'))
for r in R:
  if r['class']=='k20_shared':continue
  d=json.load(open(f"{P}/{r['case']}.json"));K=[x for x in d['k20']['events'] if x['type'] in('kick','contact','restart_placement','goal')];L=[x for x in d['l21']['events'] if x['type'] in('kick','contact','restart_placement','goal')]
  i=0
  while i<min(len(K),len(L)) and key(K[i])==key(L[i]):i+=1
  fk=K[i] if i<len(K) else None;fl=L[i] if i<len(L) else None
  tdiv=min([x['t'] for x in (fk,fl) if x] or [d['l21']['t0']+120])
  ys=[y for y in d['l21']['yields'] if y['t']<=tdiv]
  # characterise trusted collectors in yields before divergence
  kinds=collections.Counter()
  for y in ys:
    for q in y['collectors']:
      kinds['reach' if q['d']<=1.1 else 'closing']+=1
      if q['alongside']:kinds['alongside']+=1
      if q['nearestOppToBall']<q['d']:kinds['opponent_nearer_than_collector']+=1
  # what happened at the divergence point
  if fk and fl and fk['t']==fl['t'] and fk['p']!=fl['p']:what=f"same tick, different toucher: K20 {fk['p']}({fk['team']}) vs L21 {fl['p']}({fl['team']})"
  elif fk and (not fl or fk['t']<fl['t']):what=f"K20 touch earlier: {fk['p']}({fk['team']},{fk['type']},{'ctrl' if fk['ctrl'] else 'noctrl'}) at {fk['t']}; L21 next {fl and (fl['p'],fl['team'],fl['t'])}"
  elif fl and (not fk or fl['t']<fk['t']):what=f"L21 touch earlier: {fl['p']}({fl['team']},{fl['type']},{'ctrl' if fl['ctrl'] else 'noctrl'}) at {fl['t']}; K20 next {fk and (fk['p'],fk['team'],fk['t'])}"
  else:what='events differ in control flag only'
  yielder_in_k20=fk is not None and any(y['p']==fk.get('p') for y in ys)
  cat=None
  if not ys: cat='divergence_before_any_yield(?)'
  elif yielder_in_k20 and fk['team']==r['team'] and (fl is None or fl['team']!=r['team']): cat='yielder_touched_in_K20_but_opponent_or_none_in_L21'
  elif fl and fl['team']!=r['team'] and fk and fk['team']==r['team']: cat='own_touch_in_K20_opponent_in_L21'
  elif fl and fl['team']==r['team'] and fk and fk['team']!=r['team']: cat='opponent_in_K20_own_in_L21'
  elif fk and fl and fk['team']==fl['team']==r['team']: cat='both_own_team_different_player_or_timing'
  elif fk and fl and fk['team']==fl['team']!=r['team']: cat='both_opponent_different_player_or_timing'
  else: cat='other'
  C[(r['case'][0],cat)]+=1
  for k,v in kinds.items():Y[(r['case'][0],k)]+=v
  out.append({'case':r['case'],'team':r['team'],'divTick':tdiv,'secondsFromStart':round((tdiv-d['l21']['t0'])/20,2),'yieldsBeforeDiv':len(ys),'what':what,'category':cat,'collectorKinds':dict(kinds),'poss6':r['poss6'],'firstYield':ys[0] if ys else None})
json.dump(out,open(outF,'w'),ensure_ascii=False,indent=0)
for k,v in sorted(C.items()):print(k,v)
print('trusted-collector characteristics in yields before divergence:',dict(sorted(Y.items())))
