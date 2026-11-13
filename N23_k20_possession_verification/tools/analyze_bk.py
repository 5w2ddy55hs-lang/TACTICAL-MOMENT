# Classify base-vs-K20 6 s possession differences in the fast-ball scenes.
# usage: python3 -I analyze_bk.py <probeDir> <jobs.txt> <out.json>
import json,sys,math,collections
P,jobs,outF=sys.argv[1:4]
key=lambda x:(x['t'],x['type'],x.get('p'),x.get('ctrl'))
def outcome(R,team):
  ev=R['events'];t0=R['t0']
  tch=[e for e in ev if e['type'] in('kick','contact') and e['t']<=t0+120]
  first=tch[0] if tch else None
  rs=next((e for e in ev if e['type']=='restart_placement' and e['t']<=t0+120),None)
  firstCtrl=next((e for e in tch if e['ctrl']),None)
  passes=[e for e in tch if e['type']=='kick' and e.get('kind')=='pass']
  return {'firstTouch':first and (first['t']-t0,first['p'],first['team'],'ctrl' if first['ctrl'] else 'noctrl'),
   'firstControlTeam':firstCtrl and firstCtrl['team'],'firstControlDt':firstCtrl and firstCtrl['t']-t0,
   'ownPasses':sum(1 for e in passes if e['team']==team),'oppPasses':sum(1 for e in passes if e['team']!=team),
   'ballOut':rs and (rs['t']-t0,rs.get('kind'),rs.get('team')),'poss6':R['poss6']}
res=[];C=collections.Counter()
for line in open(jobs):
  name,state,team=line.split();d=json.load(open(f'{P}/probe_{name}.json'))
  B=[x for x in d['base']['events'] if x['type'] in('kick','contact','restart_placement','goal')];K=[x for x in d['k20']['events'] if x['type'] in('kick','contact','restart_placement','goal')]
  i=0
  while i<min(len(B),len(K)) and key(B[i])==key(K[i]):i+=1
  fb=B[i] if i<len(B) else None;fk=K[i] if i<len(K) else None
  tdiv=min([x['t'] for x in (fb,fk) if x] or [d['k20']['t0']+120])
  alts=[a for a in d['k20']['alterations'] if a['t']<=tdiv]
  # who touched at divergence in base and K20
  baseToucher=fb and fb.get('p');k20Toucher=fk and fk.get('p')
  involved=[a for a in alts if a['p'] in (baseToucher,k20Toucher)]
  near=[a for a in alts if a['selfD'] is not None and a['selfD']<=5]
  stale=[a for a in alts if a['witnessed'] and a['witnessed']['age']>40]
  truthOwn=[a for a in alts if a['truthLast'] and a['truthLast']['team']==a['team'] and a['truthLast']['ctrl']]
  if not alts: cat='no_K20_alteration_before_divergence'
  elif involved: cat='K20_altered_the_player_who_touches_at_divergence'
  elif near: cat='K20_altered_a_player_near_ball(<=5m)_not_the_toucher'
  else: cat='only_far_players_altered->later_branch'
  kinds=collections.Counter(a['orig']+'->'+a['now'] for a in alts)
  C[(name[:2],cat)]+=1
  res.append({'case':name,'team':team,'divergenceDt':tdiv-d['k20']['t0'],'baseAtDiv':fb and (fb['t']-d['k20']['t0'],fb.get('p'),fb.get('team'),fb['type'],fb.get('ctrl')),'k20AtDiv':fk and (fk['t']-d['k20']['t0'],fk.get('p'),fk.get('team'),fk['type'],fk.get('ctrl')),
   'category':cat,'altsBeforeDiv':len(alts),'altKinds':dict(kinds),'altTeams':dict(collections.Counter(a['team'] for a in alts)),'staleWitness(>2s)':len(stale),'truthOwnControlButUnknown':len(truthOwn),
   'firstAlt':alts[0] if alts else None,'base':outcome(d['base'],team),'k20':outcome(d['k20'],team)})
json.dump(res,open(outF,'w'),ensure_ascii=False,indent=0)
for k,v in sorted(C.items()):print(k,v)
