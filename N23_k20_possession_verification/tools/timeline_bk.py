# Per-case timeline for base-vs-K20 6 s possession differences:
# first K20 decision difference -> first actual position difference -> first ball-event difference -> next play.
# First-pass rule-based class (written while first reading these 33 cases; superseded by classify_n23.py):
#   OUT_FIRST      : the first differing ball event is a restart (ball out of play) in either engine
#   TEAM_AT_FIRST  : the first differing ball touch is by different teams in the two engines
#       .direct     -> the player whose touch differs (own-team toucher absent/present) had a K20-altered decision before it
#       .indirect   -> no altered decision for those touchers (other branch came first)
#   SAME_TEAM_FIRST: the first differing touch is by the same team (timing/player shift); the 6 s difference arises later
#   NONE           : no differing ball event within 6 s (difference only at the 6 s label)
# usage: python3 -I timeline_bk.py <probeDir> <jobs.txt> <out.json>
import json,sys,math,collections
P,jobs,outF=sys.argv[1:4]
TOUCH=('kick','contact');BALL=('kick','contact','restart_placement','goal')
key=lambda x:(x['t'],x['type'],x.get('p'),x.get('ctrl'))
def firstMove(B,K):
  for fb,fk in zip(B['frames'],K['frames']):
    pb={q[0]:(q[1],q[2]) for q in fb['p']};pk={q[0]:(q[1],q[2]) for q in fk['p']}
    moved=sorted(i for i in pb if math.hypot(pb[i][0]-pk[i][0],pb[i][1]-pk[i][1])>0.005)
    if moved:return fb['t'],moved,{i:round(math.hypot(pb[i][0]-fb['ball'][0],pb[i][1]-fb['ball'][1]),2) for i in moved}
  return None,[],{}
def firstBall(B,K):
  for fb,fk in zip(B['frames'],K['frames']):
    if math.hypot(fb['ball'][0]-fk['ball'][0],fb['ball'][1]-fk['ball'][1])>0.005:return fb['t']
  return None
def nextPlay(R,team,after):
  ev=[e for e in R['events'] if e['type'] in BALL and e['t']>=after and e['t']<=R['t0']+120]
  seq=[];
  for e in ev:
    if e['type']=='restart_placement':seq.append('OUT(%s→%s)'%('?',e['team']));break
    if e['type']=='goal':seq.append('GOAL');break
    tag=('own' if e['team']==team else 'opp')+('-'+e['kind'] if e['type']=='kick' and e.get('kind') else ('-ctrl' if e['ctrl'] else '-touch'))
    seq.append('%+d:%s:%s'%(e['t']-R['t0'],e['p'],tag))
  return seq[:6]
res=[];C=collections.Counter()
for line in open(jobs):
  name,state,team=line.split();d=json.load(open(f'{P}/probe_{name}.json'));Bs,Ks=d['base'],d['k20'];t0=Ks['t0']
  B=[x for x in Bs['events'] if x['type'] in BALL];K=[x for x in Ks['events'] if x['type'] in BALL]
  i=0
  while i<min(len(B),len(K)) and key(B[i])==key(K[i]):i+=1
  fb=B[i] if i<len(B) else None;fk=K[i] if i<len(K) else None
  tdiv=min([x['t'] for x in (fb,fk) if x] or [t0+121])
  alts=Ks['alterations'];a1=alts[0] if alts else None
  mt,moved,movedD=firstMove(Bs,Ks);bt=firstBall(Bs,Ks)
  altBefore=lambda pid,t:[a for a in alts if a['p']==pid and a['t']<=t]
  # classify
  if fb is None and fk is None: cls='NONE'
  elif (fb and fb['type'] in('restart_placement','goal')) or (fk and fk['type'] in('restart_placement','goal')):cls='OUT_FIRST'
  else:
    # team of the first differing touch in each engine (the engine with the later event: its own first touch from that index)
    tb=fb['team'] if fb else None;tk=fk['team'] if fk else None
    if tb==tk: cls='SAME_TEAM_FIRST'
    else:
      touchers=[x['p'] for x in (fb,fk) if x]
      direct=any(altBefore(p,tdiv) for p in touchers)
      cls='TEAM_AT_FIRST.'+('direct' if direct else 'indirect')
  # first team-level divergence: first index where the sequence of touching TEAMS differs (collapsing repeats)
  def teamseq(R):
    s=[];
    for e in R['events']:
      if e['t']>t0+120:break
      if e['type'] in TOUCH:
        if not s or s[-1][0]!=e['team']:s.append((e['team'],e['t']-t0,e['p']))
      elif e['type']=='restart_placement':s.append(('OUT>'+str(e['team']),e['t']-t0,None));break
    return s
  sb,sk=teamseq(Bs),teamseq(Ks);j=0
  while j<min(len(sb),len(sk)) and sb[j][0]==sk[j][0]:j+=1
  teamDiv={'index':j,'base':sb[j] if j<len(sb) else None,'k20':sk[j] if j<len(sk) else None}
  C[(name[:2],cls)]+=1
  r={'case':name,'team':team,'class':cls,
   'firstDecisionDiff':a1 and {'dt':a1['t']-t0,'p':a1['p'],'team':a1['team'],'change':a1['orig']+'->'+a1['now'],'selfD':a1['selfD'],'witnessed':a1['witnessed'],'velKnown':a1['velKnown'],'ballAge':a1['ballAge']},
   'firstMoveDiff':{'dt':mt-t0 if mt else None,'players':moved,'distToBall':movedD,'allAltered':all(altBefore(p,mt) for p in moved) if mt else None},
   'firstBallPosDiff':bt-t0 if bt else None,
   'firstBallEventDiff':{'dt':tdiv-t0,'base':fb and [fb['t']-t0,fb.get('p'),fb.get('team'),fb['type'],fb.get('kind')],'k20':fk and [fk['t']-t0,fk.get('p'),fk.get('team'),fk['type'],fk.get('kind')],
     'touchersAlteredBefore':{x['p']:[a['orig']+'->'+a['now']+'@%+d'%(a['t']-t0) for a in altBefore(x['p'],tdiv)][-3:] for x in (fb,fk) if x and x.get('p')}},
   'firstTeamSequenceDiff':teamDiv,
   'nextPlay':{'base':nextPlay(Bs,team,tdiv),'k20':nextPlay(Ks,team,tdiv)},
   'poss6':{'base':Bs['poss6'],'k20':Ks['poss6']},
   'altsBeforeBallDiff':{'n':len([a for a in alts if a['t']<=tdiv]),'byTeam':dict(collections.Counter(a['team'] for a in alts if a['t']<=tdiv)),
     'witnessAgeOver2s':sum(1 for a in alts if a['t']<=tdiv and a['witnessed'] and a['witnessed']['age']>40),'noWitness':sum(1 for a in alts if a['t']<=tdiv and not a['witnessed']),
     'witnessedOppOrMixed':sum(1 for a in alts if a['t']<=tdiv and a['witnessed'] and any(w.split(':')[1]!=a['team'] for w in a['witnessed']['who'])),
     'velUnknown':sum(1 for a in alts if a['t']<=tdiv and a['velKnown'] is False),
     'truthOwnCtrl':sum(1 for a in alts if a['t']<=tdiv and a['truthLast'] and a['truthLast']['team']==a['team'] and a['truthLast']['ctrl'])}}
  res.append(r)
json.dump(res,open(outF,'w'),ensure_ascii=False,indent=1)
for k,v in sorted(C.items()):print(k,v)
for r in res:
  f=r['firstDecisionDiff'];m=r['firstMoveDiff'];b=r['firstBallEventDiff']
  print(f"{r['case']:16s} {r['class']:24s} dec@{f['dt']:+d} {f['p']}({f['team']}) {f['change']} {f['selfD']}m wit={f['witnessed'] and (f['witnessed']['who'],f['witnessed']['age'])} | move@{m['dt']:+d} {m['players'][:3]} | ballpos@{r['firstBallPosDiff']} | ev base={b['base']} k20={b['k20']} alt={b['touchersAlteredBefore']} | teamDiv={r['firstTeamSequenceDiff']['base']} vs {r['firstTeamSequenceDiff']['k20']} | p6 {r['poss6']['base']}/{r['poss6']['k20']}")
