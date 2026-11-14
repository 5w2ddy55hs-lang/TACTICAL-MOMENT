# Usage: python3 -I crosscheck_overlap.py <fallback input.json.gz> <suite root>
import json,gzip,sys,os
W=json.load(gzip.open(sys.argv[1]));R=sys.argv[2]
cases=json.load(open(os.path.join(R,'cases.json')))['cases']
for c in cases:
    ws=[w for w in W if w['seed']==c['seed'] and w['start']<c['end'] and c['start']<w['end']]
    if not ws:print(c['id'],'no overlap');continue
    w=ws[0];x=json.load(gzip.open(os.path.join(R,c['expected'])))
    lo,hi=max(w['start'],c['start']),min(w['end'],c['end'])
    pk={(r['tick'],r['player']):r for r in w['rows'] if r['channel']=='decision' and lo<=r['tick']<hi}
    sk={(r['tick'],r['player']):r for r in x['rows'] if r['channel']=='decision' and lo<=r['tick']<hi}
    kind_eq=sum(pk[k]['decision']['kind']==sk[k]['decision']['kind'] for k in pk if k in sk)
    rec=[k for k in pk if pk[k]['decision']['kind']=='receive' and k in sk]
    full_eq=sum(json.dumps(pk[k]['observation'],sort_keys=True)==json.dumps(sk[k]['observation'],sort_keys=True) and json.dumps(pk[k]['decision'],sort_keys=True)==json.dumps(sk[k]['decision'],sort_keys=True) for k in rec)
    pe=[(e['tick'],e['type'],e.get('player')) for e in w['rows'] if e['channel']=='event' and lo<=e['tick']<hi]
    se=[(e['tick'],e['type'],e.get('player')) for e in x['rows'] if e['channel']=='event' and lo<=e['tick']<hi]
    print(c['id'],f"overlap {lo}-{hi}",'decision keys equal',set(pk)==set(sk),len(pk),'kinds equal',kind_eq,'receive DTO+decision identical',full_eq,'/',len(rec),'events equal',pe==se,len(pe))
