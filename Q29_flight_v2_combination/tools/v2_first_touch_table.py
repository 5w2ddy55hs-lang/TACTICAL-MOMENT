# Compact decision -> motion -> touch -> pass table from v2_first_touch_*.json (read only).
# usage: python3 -I v2_first_touch_table.py <v2_first_touch_O?_P.json> ...
import json,sys
for f in sys.argv[1:]:
    d=json.load(open(f));print(f"\n## {d['opportunity']} {d['player']}  frames identical until: base/flight {d['isolation']['base_vs_flight']}  v2/combo {d['isolation']['v2_vs_combo']}  base/v2 {d['isolation']['base_vs_v2']}")
    v2dec=d['arms']['v2']['decisions'];first=next(x for x in v2dec if x['dedicated']);t0=first['tick']
    for a in ('base','v2'):
        A=d['arms'][a];dec=A['decisions'];tr={r['tick']:r for r in A['truth']}
        x=next(y for y in dec if y['tick']==t0)
        after=[r for r in A['truth'] if t0<=r['tick']<=t0+30]
        vmax=max(after,key=lambda r:r['speed'] or 0);under1=next((r['tick'] for r in after if r['dBall'] is not None and r['dBall']<1.0),None)
        kick=next((e for e in A['events'] if e['type']=='kick' and e['tick']>t0),None)
        pd=next((y for y in dec if y['tick']>t0 and (y['kind'] in('pass','dribble') or (y['ebi'] and y['ebi']['kind'] in('pass','dribble')))),None)
        via='decision' if pd and pd['kind'] in('pass','dribble') else 'EBI'
        how=pd and (pd['kind'] if via=='decision' else pd['ebi']['kind']+'(EBI)')
        print(f" [{a}] {t0}: {x['kind']}{'(DP)' if x['dedicated'] else ''} target {x['dTarget']}m ahead, eta {x['eta']} | i17 gate: {x['i17']} | v2: {x['v2']} | generic: {x['generic']} | own speed {x['ownSpeed']}")
        print(f"      motion: max speed {vmax['speed']} @{vmax['tick']}; first dBall<1.0 @{under1} | next kick {kick and (kick['tick'],kick['kind'],kick['targetId'])} | chosen by {pd and pd['tick']}->{pd and pd['apply']} {how} | candidates {pd and pd['candidates'][:4]}")
        trail=[(r['tick'],r['dBall'],r['speed']) for r in after if (r['tick']-t0)%4==0][:8];print(f"      trail (tick,dBall,speed): {trail}")
