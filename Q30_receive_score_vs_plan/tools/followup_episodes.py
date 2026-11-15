import json,gzip,collections,os
eps=json.load(open('eval/episodes.json'))
R={'rec_f':'../q29/rec_f/','rec':'../q29/rec/','rec_d':'../q29/rec_d/','suite':'../q26/in_suite/TM_SUPPORT_SUITE/expected/'}
def load(name):
    for d in R.values():
        p=os.path.join(d,name)
        if os.path.exists(p):return json.load(gzip.open(p))
cache={};out=collections.Counter();rows=[]
for e in eps:
    x=cache.get(e['rec']) or cache.setdefault(e['rec'],load(e['rec']))
    dec=[r for r in x['rows'] if r['channel']=='decision' and r['player']==e['player'] and r['tick']>e['last']]
    nxt=next((r for r in dec if r['decision']['kind'] in('receive','intercept')),None)
    cls='possession_penalty' if e['rows'][0]['components']['ourPossession'] else 'ahead_or_distance'
    outcome=e['rows'][-1]['next'];oc='none' if not outcome or not outcome.get('player') else ('self' if outcome['player']==e['player'] else ('teammate' if outcome['team']==e['rows'][0]['team'] else 'opponent'))
    k=(cls,oc,'nextReceive:'+('none' if not nxt else ('DP' if nxt['decision'].get('reception') else 'generic')))
    out[k]+=1;rows.append({'rec':e['rec'],'player':e['player'],'first':e['first'],'last':e['last'],'class':cls,'outcome':oc,'nextReceiveTick':nxt and nxt['tick'],'delayTicks':nxt and nxt['tick']-e['first'],'nextReceiveDedicated':nxt and bool(nxt['decision'].get('reception'))})
for k,v in sorted(out.items()):print(v,k)
d=[r['delayTicks'] for r in rows if r['delayTicks'] is not None];print('delay first plan-row -> first receive decision (ticks): n',len(d),'min',min(d),'median',sorted(d)[len(d)//2],'max',max(d))
json.dump(rows,open('eval/episodes_followup.json','w'),indent=1)
