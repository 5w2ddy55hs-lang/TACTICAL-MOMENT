import json,gzip,sys,collections,math
W=json.load(gzip.open(sys.argv[1]));A=json.load(open(sys.argv[2]))
rows=A['rows']
ex=[r for r in rows if r['status']=='generic_exhausted']
print('exhausted eta values',collections.Counter(repr(r['eta']) for r in ex))
print('feasible t=2.0 count',sum(1 for r in rows if r['status']=='generic_feasible' and r['hitT'] and r['hitT']>1.99))
# clamped: restart or out within 60 ticks?
evs={(w['seed'],w['start']):[e for e in w['rows'] if e['channel']=='event'] for w in W}
def nxt(r,types,h=60):
    return next((e for e in evs[(r['seed'],r['window'])] if r['tick']<=e['tick']<r['tick']+h and e['type'] in types),None)
cl=[r for r in ex if r['clamped']]
c=collections.Counter()
for r in cl:
    e=nxt(r,('restart_placement','goal','throw_pickup','contact','kick'))
    c[e['type'] if e else 'none']+=1
print('clamped exhausted -> first event within 60t',c)
uc=[r for r in ex if not r['clamped']];c2=collections.Counter()
for r in uc:
    e=nxt(r,('restart_placement','goal','throw_pickup','contact','kick'));c2[e['type'] if e else 'none']+=1
print('unclamped exhausted -> first event within 60t',c2)
# concurrent: per tick per team, number of players whose latest decision is exhausted receive
st={(r['seed'],r['tick'],r['player']):r['status'] for r in rows}
conc=collections.Counter();concAny=collections.Counter();ticks=0
for w in W:
    latest={}
    dec=sorted([r for r in w['rows'] if r['channel']=='decision'],key=lambda r:r['tick'])
    i=0
    for t in range(w['start'],w['end']):
        while i<len(dec) and dec[i]['tick']<=t:
            r=dec[i];latest[r['player']]=(r['decision']['kind'],st.get((w['seed'],r['tick'],r['player'])));i+=1
        for team in 'AB':
            n=sum(1 for p,v in latest.items() if p[0]==team and v[1]=='generic_exhausted')
            m=sum(1 for p,v in latest.items() if p[0]==team and v[0]=='receive')
            conc[n]+=1;concAny[m]+=1
print('team-ticks by number of players currently on exhausted receive',sorted(conc.items()))
print('team-ticks by number of players currently on any receive',sorted(concAny.items()))
