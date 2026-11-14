import json,sys,collections,math
d=json.load(open(sys.argv[1]))
rows=d['rows'];eps=d['episodes']
def q(v,ps=(0.1,0.25,0.5,0.75,0.9)):
    v=sorted(v);n=len(v)
    return [round(v[min(n-1,int(p*n))],2) for p in ps] if v else None
ex=[r for r in rows if r['status']=='generic_exhausted']
# 1) intended receivers of the last kick
it=[r for r in ex if r['intended']]
print('intended exhausted',len(it),'planGate',collections.Counter(r['planGate'] for r in it).most_common())
print(' along<0',sum(r['along']<0 for r in it),'clamped',sum(r['clamped'] for r in it),'lastKick own team',sum(r['lastKick']['team']==r['team'] for r in it))
print(' kick kinds',collections.Counter(r['lastKick']['kind'] for r in it).most_common())
print(' since kick ticks q',q([r['tick']-r['lastKick']['tick'] for r in it]))
print(' firstAny after',collections.Counter(None if not r['firstAny'] else ('self' if r['firstAny']['player']==r['player'] else 'mate' if r['firstAny']['team']==r['team'] else 'opp') for r in it))
print(' distinct (seed,kick,player)',len({(r['seed'],r['lastKick']['tick'],r['player']) for r in it}))
# 2) cos of current velocity with direction to target
for k in ['generic_exhausted','generic_feasible','dedicated_plan']:
    v=[r['cosVel'] for r in rows if r['status']==k and r['cosVel'] is not None]
    print(k,'cosVel q',q(v),'n',len(v),' ownSpeed q',q([r['ownSpeed'] for r in rows if r['status']==k]))
# 3) consecutive receive decisions of same player: target jumps & movement direction
byp=collections.defaultdict(list)
for i,r in enumerate(rows):byp[(r['seed'],r['window'],r['player'])].append(r)
trans=collections.defaultdict(list)
for k,lst in byp.items():
    lst.sort(key=lambda r:r['tick'])
    for a,b in zip(lst,lst[1:]):
        if b['tick']-a['tick']>8:continue  # not consecutive decisions (other kinds in between)
        jump=math.dist((a['target']['x'],a['target']['y']),(b['target']['x'],b['target']['y']))
        dx=b['self']['x']-a['self']['x'];dy=b['self']['y']-a['self']['y'];m=math.hypot(dx,dy)
        tx=a['target']['x']-a['self']['x'];ty=a['target']['y']-a['self']['y'];tn=math.hypot(tx,ty)
        cos=(dx*tx+dy*ty)/(m*tn) if m>0.05 and tn>0 else None
        # direction from player to target change
        ux=b['target']['x']-b['self']['x'];uy=b['target']['y']-b['self']['y']
        ang=abs(math.degrees(math.atan2(tx*uy-ty*ux,tx*ux+ty*uy))) if tn>0 and math.hypot(ux,uy)>0 else None
        trans[(a['status'],b['status'])].append((jump,cos,ang,m/((b['tick']-a['tick'])*0.05)))
for k,v in sorted(trans.items(),key=lambda x:-len(x[1])):
    print('trans',k,len(v),'jump q',q([x[0] for x in v]),'moveCos q',q([x[1] for x in v if x[1] is not None]),'dirChange deg q',q([x[2] for x in v if x[2] is not None]),'speed q',q([x[3] for x in v]))
# 4) simultaneous exhausted receivers same team same tick
sim=collections.Counter((r['seed'],r['tick'],r['team']) for r in ex)
print('same team same tick exhausted count dist',collections.Counter(sim.values()))
allrec=collections.Counter((r['seed'],r['tick'],r['team']) for r in rows)
# 5) ahead_far_lateral subgroup detail
afl=[r for r in ex if not r['clamped'] and r['along']>=0]
print('ahead group',len(afl),'planGate',collections.Counter(r['planGate'] for r in afl).most_common(),'intended',sum(r['intended'] for r in afl))
print(' lateral q',q([r['lateral'] for r in afl]),'along q',q([r['along'] for r in afl]),'ballSpeed q',q([r['ballSpeed'] for r in afl]),'firstSelf',sum(1 for r in afl if r['firstSelf']))
hi=[r for r in ex if r['planGate']=='ball_high']
print('ball_high exhausted',len(hi),'intended',sum(r['intended'] for r in hi),'along<0',sum(r['along']<0 for r in hi),'z q',q([r['ballZ'] for r in hi]))
# 6) bodyResidual for feasible: share where body prediction misses by >2m (generic says feasible)
fe=[r for r in rows if r['status']=='generic_feasible']
print('feasible bodyResidual>2m',sum(r['bodyResidual']>2 for r in fe),'of',len(fe),' >5m',sum(r['bodyResidual']>5 for r in fe))
print('dedicated bodyResidual>0.8',sum(r['bodyResidual']>0.8 for r in rows if r['status']=='dedicated_plan'))
