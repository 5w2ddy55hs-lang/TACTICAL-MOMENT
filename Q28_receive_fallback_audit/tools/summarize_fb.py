import json,sys,collections,statistics as st
d=json.load(open(sys.argv[1]))
rows=d['rows'];eps=d['episodes']
print('kinds all decisions',sorted(d['kindsAll'].items(),key=lambda x:-x[1]))
def q(v,ps=(0.1,0.25,0.5,0.75,0.9)):
    v=sorted(v);n=len(v)
    return [round(v[min(n-1,int(p*n))],2) for p in ps] if v else None
S=collections.defaultdict(list)
for r in rows:S[r['status']].append(r)
for k,v in S.items():
    print('\n==',k,len(v))
    print(' planGate',collections.Counter(r['planGate'] for r in v).most_common())
    print(' dBall q',q([r['dBall'] for r in v]),' ballSpeed q',q([r['ballSpeed'] for r in v]))
    print(' along q',q([r['along'] for r in v]),' lateral q',q([r['lateral'] for r in v]))
    print(' dTarget q',q([r['dTarget'] for r in v]),' bodyResidual q',q([r['bodyResidual'] for r in v]))
    print(' minGap q',q([r['minGap'] for r in v]))
    print(' clamped',sum(r['clamped'] for r in v),' intended(last kick targetId)',sum(r['intended'] for r in v),' ageTicks>0',sum(r['ballAgeTicks']>0 for r in v))
    print(' team of last kick == own',collections.Counter((r['lastKick'] or {}).get('team')==r['team'] if r['lastKick'] else None for r in v))
    print(' role',collections.Counter(r['role'] for r in v).most_common())
    print(' player behind ball (along<0)',sum(r['along']<0 for r in v),' target downstream of player (targetAlong>along)',sum(r['targetAlong']>r['along'] for r in v))
    print(' second cand',collections.Counter((r['second'] or {}).get('kind') for r in v).most_common(5))
    print(' score-0.65 q',q([r['score']-0.65 for r in v]))
    print(' firstSelf within 60t',sum(1 for r in v if r['firstSelf']),' firstAny team same',collections.Counter(None if not r['firstAny'] else (r['firstAny']['team']==r['team'] if r['firstAny']['team'] else 'noteam') for r in v))
# exhausted geometry classes
ex=S['generic_exhausted']
def cls(r):
    if r['clamped']:return 'boundary_clamped'
    if r['along']<0:return 'behind_ball_chasing'
    if r['along']>=0 and r['lateral']>r['along']:return 'ahead_far_lateral'
    return 'ahead_on_line_far'
print('\nexhausted classes',collections.Counter(cls(r) for r in ex).most_common())
# episodes
print('\nepisodes',len(eps))
print(' length n',collections.Counter(min(e['n'],10) for e in eps).most_common())
print(' duration ticks q',q([e['end']-e['start'] for e in eps]))
print(' prev',collections.Counter((e['prevKind'],e.get('prevStatus')) for e in eps).most_common(8))
print(' next',collections.Counter((e.get('nextKind'),e.get('nextStatus')) for e in eps).most_common(12))
# truncated by window end
print(' ends at window end (no next)',sum(1 for e in eps if e.get('nextKind') is None))
# self contact during episode or within 2 s after episode end
def evs(e):
    rs=[rows[i] for i in e['rows']]
    return rs
selfc=0;
for e in eps:
    rs=evs(e)
    if any(r['firstSelf'] for r in rs):selfc+=1
print(' episodes with own contact within 60t of any member decision',selfc)
