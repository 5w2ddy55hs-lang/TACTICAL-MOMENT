# Own-observation evidence behind K20's first-cycle (+0..+3) decision changes in all 194 fast-ball scenes, split by the
# 6 s label outcome (same / base-only keeps / K20-only keeps). Truth (next controlling team) is used ONLY as an audit label.
# usage: python3 -I evidence_194.py <probeDir> <jobs.txt> <base_rate.json> <out.json>
import json,sys,collections,statistics
P,jobs,brF,outF=sys.argv[1:5]
BR={r['case']:r for r in json.load(open(brF))}
G=collections.defaultdict(collections.Counter);ages=collections.defaultdict(list);out={}
for line in open(jobs):
  name,state,team=line.split();d=json.load(open(f'{P}/probe_{name}.json'));K=d['k20'];t0=K['t0']
  b=BR[name];lab='same' if b['baseKeeps']==b['k20Keeps'] else ('BK' if b['baseKeeps'] else 'KB')
  fc=next((e for e in d['base']['events'] if e['type'] in('kick','contact') and e['ctrl']),None)
  for a in K['alterations']:
    if a['t']-t0>=4:continue
    g=G[lab];g['alterations']+=1
    poss=a['orig'] in('support','advance_support')
    g['possession->non-possession' if poss else 'other '+a['orig']+'->'+a['now']]+=1
    if not poss:continue
    w=a['witnessed'];age=w['age']/20 if w else None
    if age is not None:ages[lab].append(age)
    g['witness '+('none' if age is None else '<=1s' if age<=1 else '1-2s' if age<=2 else '>2s')]+=1
    g['ball velocity unknown' if a['velKnown'] is False else 'ball velocity known']+=1
    g['dist '+('<=5m' if a['selfD']<=5 else '5-15m' if a['selfD']<=15 else '>15m')]+=1
    g['next control '+('none' if not fc else 'own' if fc['team']==a['team'] else 'opp')]+=1
    g['teammate within 2.1m (own view)' if a['nearFriends'] else 'no teammate within 2.1m']+=1
for lab in('same','BK','KB'):
  g=G[lab];n=g['possession->non-possession'];out[lab]=dict(g);a=ages[lab]
  out[lab]['witnessAgeMedianS']=round(statistics.median(a),2) if a else None
  print(f"[{lab}] alterations {g['alterations']} (poss->non-poss {n})")
  for k in sorted(g):
    if k in('alterations','possession->non-possession'):continue
    print(f"   {k:34s} {g[k]:5d}  {100*g[k]/max(n,1):5.1f}%")
  print('   witness age median (s):',out[lab]['witnessAgeMedianS'])
json.dump(out,open(outF,'w'),indent=1)
