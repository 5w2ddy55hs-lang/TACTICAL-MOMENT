import json,gzip,sys,collections,math
d=json.load(open(sys.argv[1]));W=json.load(gzip.open(sys.argv[2]))
def q(v,ps=(0.1,0.25,0.5,0.75,0.9)):
    v=sorted(v);n=len(v);return [round(v[min(n-1,int(p*n))],1) for p in ps] if v else None
cl=lambda x,a,b:max(a,min(b,x))
def ang(a,b):
    return abs(math.degrees(math.atan2(a[0]*b[1]-a[1]*b[0],a[0]*b[0]+a[1]*b[1])))
ebi={}
for w in W:
    for r in w['rows']:
        if r['channel']=='decision' and r['decision']['kind']=='receive':
            ebi[(w['seed'],r['tick'],r['player'])]=('ballActionIntent' in r['decision'],'selfTouchCondition' in r['decision'])
res=collections.defaultdict(list)
for r in d['rows']:
    if r['status']!='generic_exhausted':continue
    s=r['self'];b=r['ball']
    pts=[(cl(b['x']+cl(b['vx'],-40,40)*t*0.82,0.3,104.7),cl(b['y']+cl(b['vy'],-40,40)*t*0.82,0.3,67.7)) for t in [k/10 for k in range(1,21)]]
    vt=(r['target']['x']-s['x'],r['target']['y']-s['y']);vb=(b['x']-s['x'],b['y']-s['y'])
    spread=max(ang(vt,(p[0]-s['x'],p[1]-s['y'])) for p in pts)
    g='clamped' if r['clamped'] else ('behind' if r['along']<0 else 'ahead')
    res[g].append((ang(vt,vb),spread))
for g,v in res.items():
    print(g,len(v),'angle(target vs ball now) q',q([x[0] for x in v]),' max angle over 20 candidate points q',q([x[1] for x in v]),' share spread<10deg',round(sum(x[1]<10 for x in v)/len(v),2))
st=collections.Counter()
for r in d['rows']:
    e=ebi[(r['seed'],r['tick'],r['player'])];st[(r['status'],e)]+=1
print(st)
