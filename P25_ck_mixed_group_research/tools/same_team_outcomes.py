# Every same-team aerial resolution in the P25 natural runs and what followed inside the corner window (bounded as in ck_metrics).
# usage: python3 -I same_team_outcomes.py <out.json> <runDir>...
import json,sys,collections,os
rows=[];C=collections.Counter()
for d in sys.argv[2:]:
  ev=[json.loads(l) for l in open(d+'/events.jsonl')];ev=[e for e in ev if e.get('channel','event')=='event' and 'type' in e]
  for i,e in enumerate(ev):
    if e['type']!='aerial_duel' or len(set(e['teams']))!=1:continue
    T=e['tick'];team=e['teams'][0];k=next(x for x in ev[i:] if x['type']=='kick' and x['tick']==T and x['player']==e['winner'])
    corner=next(x for x in reversed(ev[:i]) if x['type']=='restart_taken' and x['kind']=='corner');att=corner['team']==team
    nxt=next((x for x in ev[i:] if x['type']=='restart_placement' and x['tick']>=T),None);end=min(nxt['tick'] if nxt else 10**9,corner['tick']+200)
    W=[x for x in ev[i:] if T<=x['tick']<=end and x['seq']>k['seq']]
    goal=next((x for x in W if x['type']=='goal'),None);nt=next((x for x in W if x['type'] in('kick','contact') and x['tick']>T),None)
    if att:out='goal' if goal and goal['team']==team else ('next_touch_opponent' if nt and nt['team']!=team else ('next_touch_teammate' if nt else ('out:'+nxt['kind']+':'+('own' if nxt['team']==team else 'opp') if nxt and nxt['tick']<=end else 'no_touch_in_window')))
    else:out='conceded_goal' if goal and goal['team']!=team else ('next_touch_opponent' if nt and nt['team']!=team else ('next_touch_teammate' if nt else ('out:'+nxt['kind']+':'+('own' if nxt['team']==team else 'opp') if nxt and nxt['tick']<=end else 'no_touch_in_window')))
    rows.append({'run':os.path.basename(d),'t':T,'side':'att' if att else 'def','players':e['players'],'kinds':e['kinds'],'winner':e['winner'],'weights':e['weights'],'ballZ':round(k['position']['z'],2),'outcome':out})
    C[('att' if att else 'def',out)]+=1
json.dump(rows,open(sys.argv[1],'w'),indent=1)
print(len(rows));[print(k,v) for k,v in sorted(C.items())]
print(collections.Counter(len(r['players']) for r in rows),collections.Counter('+'.join(sorted(r['kinds'])) for r in rows))
