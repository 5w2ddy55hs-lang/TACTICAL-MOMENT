# Usage: python3 -I suite_roles.py <audit_suite.json> <suite root>
import json,gzip,sys,os
A=json.load(open(sys.argv[1]));R=sys.argv[2]
idx={(a['case'],a['tick'],a['player']):a for a in A}
L={'generic_exhausted':'EX','generic_feasible':'FE','dedicated_plan':'DP','velocity_unknown':'VU'}
for cid,players,lo,hi in [('far_receiver',['B05','B06','B07'],6122,6160),('mutual_recovery',['B03','B06'],24263,24280),('recovery_failure',['B05','B10'],12236,12292)]:
    c=[c for c in json.load(open(os.path.join(R,'cases.json')))['cases'] if c['id']==cid][0]
    x=json.load(gzip.open(os.path.join(R,c['expected'])))
    for pid in players:
        s=[]
        for r in x['rows']:
            if r['channel']=='decision' and r['player']==pid and lo<=r['tick']<=hi:
                a=idx.get((cid,r['tick'],pid))
                s.append(f"{r['tick']}:{r['decision']['kind'][:4]}"+(f"/{L[a['status']]}{'' if not a['hitT'] else round(a['hitT'],1)}(min{a['minTrue']['d']:.1f}@{a['minTrue']['tick']})" if a else ''))
        print(cid,pid,' '.join(s))
    ev=[r for r in x['rows'] if r['channel']=='event' and r['type'] in('kick','contact') and lo<=r['tick']<=hi+20]
    print(' events',[(e['tick'],e['type'],e['player'],e.get('kind'),e.get('control')) for e in ev])
