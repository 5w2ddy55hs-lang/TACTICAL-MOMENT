# Corner-sequence metrics with explicit boundaries (answers the review note on the I17 audit: the old firstTouch search
# had no end, and the 10 s shot count mixed both teams). Branch agnostic (standard: corner = restart_kick; CK branch:
# corner_cross / corner_header / corner_clear / gk_punch / aerial_duel).
# One corner = restart_taken(kind corner) at T0 by team X. WINDOW = (T0, min(first later restart_placement, T0+200)]:
# it ENDS at the first restart of any kind (ball out, foul, goal -> kickoff) or after 10 s. Nothing after a restart is
# attributed to the corner; a kickoff after a goal is never counted as possession or a regain (O24).
# usage: python3 -I ck_metrics.py <out.json> <label>=<runDir>[,<runDir>...] ...
import json,sys,collections,os
AERIAL=('corner_header','corner_clear','gk_punch')
def load(d):
  ev=[];body=[]
  for l in open(d+'/events.jsonl'):
    x=json.loads(l)
    if x.get('channel')=='body_contact':body.append(x)
    elif x.get('channel','event')=='event' and 'type' in x:ev.append(x)
  return json.load(open(d+'/meta.json')),ev,body
def run_metrics(d):
  meta,ev,body=load(d);corners=[]
  placements=[e for e in ev if e['type']=='restart_placement']
  # same-team body-contact episodes (pair, gap<=3 ticks)
  eps=[];last={}
  for b in body:
    k='-'.join(sorted(b['players']));L=last.get(k)
    if L and b['tick']-L['end']<=3:L['end']=b['tick'];continue
    E={'pair':k,'tick':b['tick'],'end':b['tick'],'same':b['players'][0][0]==b['players'][1][0]};eps.append(E);last[k]=E
  for i,e in enumerate(ev):
    if e['type']!='restart_taken' or e.get('kind')!='corner':continue
    T0=e['tick'];X=e['team'];taker=e['player'];nxt=next((p for p in placements if p['tick']>T0),None)
    Tend=min(nxt['tick'] if nxt else 10**9,T0+200)
    W=[x for x in ev if T0<x['tick']<=Tend or (x['tick']==T0 and x['seq']>e['seq'])]
    touches=[x for x in W if x['type'] in('kick','contact') and x.get('player')!=taker]
    ft=touches[0] if touches else None
    duels=[x for x in W if x['type']=='aerial_duel']
    att_shots=[x for x in W if x['type']=='kick' and x.get('kind') in('shoot','corner_header') and x['team']==X]
    def_shots=[x for x in W if x['type']=='kick' and x.get('kind') in('shoot','corner_header') and x['team']!=X]
    goals=[x for x in W if x['type']=='goal']
    if goals:end='goal_'+('att' if goals[0]['team']==X else 'def')
    elif nxt and nxt['tick']<=T0+200 and nxt['kind']=='kickoff':end='period_end_cut_off'  # half-time kickoff, no goal: not attributed (O24)
    elif nxt and nxt['tick']<=T0+200:end='restart:%s:%s'%(nxt['kind'],'att' if nxt['team']==X else 'def')
    else:end='in_play_at_10s'
    mixed=collections.defaultdict(list)
    for x in W:
      if x['type']=='kick' and (x.get('simultaneous') or 1)>1:mixed[x['tick']].append(x)
    corners.append({'t':T0,'team':X,'taker':taker,'windowEnd':Tend,'end':end,
      'firstTouch':None if not ft else {'dt':ft['tick']-T0,'player':ft['player'],'side':'att' if ft['team']==X else 'def','how':ft.get('kind') if ft['type']=='kick' else ('contact_control' if ft.get('control') else 'contact_no_control')},
      'attShots':len(att_shots),'attHeaders':sum(1 for x in att_shots if x['kind']=='corner_header'),'defShots':len(def_shots),
      'goalAtt':bool(goals and goals[0]['team']==X),'goalDef':bool(goals and goals[0]['team']!=X),'ownGoal':bool(goals and goals[0].get('lastTeam') not in(None,goals[0]['team'])),
      'duelsOpposing':sum(1 for x in duels if len(set(x['teams']))>1),'duelsSameTeam':sum(1 for x in duels if len(set(x['teams']))==1),
      'sameTeamDuels':[{'t':x['tick'],'players':x['players'],'kinds':x['kinds'],'winner':x['winner'],'side':'att' if x['teams'][0]==X else 'def'} for x in duels if len(set(x['teams']))==1],
      'mixedSimultaneousTicks':sum(1 for t,L in mixed.items() if any(k['kind'] in AERIAL for k in L) and any(k['kind'] not in AERIAL for k in L)),
      'clears':sum(1 for x in W if x['type']=='kick' and x.get('kind')=='corner_clear'),'punches':sum(1 for x in W if x['type']=='kick' and x.get('kind')=='gk_punch'),
      'keeperCatch':sum(1 for x in W if x['type']=='keeper_catch'),'sameTeamBodyEpisodes':sum(1 for b in eps if b['same'] and T0<b['tick']<=Tend),'oppBodyEpisodes':sum(1 for b in eps if not b['same'] and T0<b['tick']<=Tend)})
  kc=collections.Counter(e.get('kind') for e in ev if e['type']=='kick');rp=collections.Counter(e['kind'] for e in placements)
  et=collections.Counter(e['type'] for e in ev)
  return {'run':os.path.basename(d.rstrip('/')),'seed':meta['seed'],'finalTick':meta['finalTick'],'completed':meta['finalTick']>=108000 and not meta.get('crash'),'crash':(meta.get('crash') or {}).get('message'),
    'violations':len(meta.get('violations') or []),'score':meta.get('score'),'goals':et['goal'],'shotsFoot':kc['shoot'],'cornerHeaders':kc['corner_header'],
    'restartPlacements':dict(rp),'fouls_freeKicksAndPenalties':sum(v for k,v in rp.items() if k in('direct_free_kick','indirect_free_kick','penalty')),
    'ambiguousLastTouch':et['ambiguous_last_touch'],'keeperHandOffence':et['keeper_hand_offence'],'sameTeamBodyEpisodes':sum(1 for b in eps if b['same']),'oppBodyEpisodes':sum(1 for b in eps if not b['same']),
    'aerialDuels':et['aerial_duel'],'corners':corners}
def agg(R):
  C=[c for r in R for c in r['corners']];n=len(C);ft=collections.Counter()
  for c in C:ft['none' if not c['firstTouch'] else c['firstTouch']['side']+':'+str(c['firstTouch']['how'])]+=1
  side=collections.Counter('none' if not c['firstTouch'] else c['firstTouch']['side'] for c in C)
  mins=sum(r['finalTick'] for r in R)/1200
  return {'runs':[r['run'] for r in R],'matches':len(R),'completed':sum(r['completed'] for r in R),'crashes':[(r['run'],r['finalTick'],r['crash']) for r in R if r['crash']],'matchMinutes':round(mins,1),'violations':sum(r['violations'] for r in R),
    'cornersTaken':n,'cornersPer90':round(n/mins*90,2) if mins else None,
    'firstTouchSide':dict(side),'firstTouchDetail':dict(sorted(ft.items(),key=lambda x:-x[1])),
    'cornersWithAttShot':sum(1 for c in C if c['attShots']),'attShots':sum(c['attShots'] for c in C),'attHeaders':sum(c['attHeaders'] for c in C),
    'cornersWithDefShot':sum(1 for c in C if c['defShots']),'goalsAtt':sum(c['goalAtt'] for c in C),'goalsDef':sum(c['goalDef'] for c in C),'ownGoalsInWindow':sum(c['ownGoal'] for c in C),
    'duelsOpposing':sum(c['duelsOpposing'] for c in C),'duelsSameTeam':sum(c['duelsSameTeam'] for c in C),'mixedSimultaneousTicks':sum(c['mixedSimultaneousTicks'] for c in C),
    'clears':sum(c['clears'] for c in C),'punches':sum(c['punches'] for c in C),'keeperCatch':sum(c['keeperCatch'] for c in C),
    'end':dict(collections.Counter(c['end'] for c in C).most_common()),
    'sameTeamBodyEpisodesInWindows':sum(c['sameTeamBodyEpisodes'] for c in C),'oppBodyEpisodesInWindows':sum(c['oppBodyEpisodes'] for c in C),
    'match':{'goals':sum(r['goals'] for r in R),'shotsFoot':sum(r['shotsFoot'] for r in R),'cornerHeaders':sum(r['cornerHeaders'] for r in R),'fouls_freeKicksAndPenalties':sum(r['fouls_freeKicksAndPenalties'] for r in R),
      'ambiguousLastTouch':sum(r['ambiguousLastTouch'] for r in R),'keeperHandOffence':sum(r['keeperHandOffence'] for r in R),'sameTeamBodyEpisodes':sum(r['sameTeamBodyEpisodes'] for r in R),'oppBodyEpisodes':sum(r['oppBodyEpisodes'] for r in R),
      'restartPlacements':dict(sum((collections.Counter(r['restartPlacements']) for r in R),collections.Counter()))}}
if __name__=='__main__':
  out={}
  for spec in sys.argv[2:]:
    label,dirs=spec.split('=',1);R=[run_metrics(d) for d in dirs.split(',')];out[label]={'aggregate':agg(R),'runs':R}
  json.dump(out,open(sys.argv[1],'w'),indent=1)
  for label,v in out.items():
    a=v['aggregate'];print('##',label,json.dumps({k:a[k] for k in a if k not in('runs','match')},ensure_ascii=False));print('   match',json.dumps(a['match']))
