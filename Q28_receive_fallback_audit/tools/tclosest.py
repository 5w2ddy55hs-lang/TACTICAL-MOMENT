import json,gzip,sys,collections,math
W=json.load(gzip.open(sys.argv[1]));A=json.load(open(sys.argv[2]))
obs={}
for w in W:
    for r in w['rows']:
        if r['channel']=='decision' and r['decision']['kind']=='receive':obs[(w['seed'],r['tick'],r['player'])]=r['observation']
cl=lambda x,a,b:max(a,min(b,x))
def tc(o):
    p=o['self'];b=o['ball'];vx=cl(b['vx'],-40,40);vy=cl(b['vy'],-40,40);s2=vx*vx+vy*vy
    return -((b['x']-p['x'])*vx+(b['y']-p['y'])*vy)/s2
ex=[r for r in A['rows'] if r['status']=='generic_exhausted']
v=[tc(obs[(r['seed'],r['tick'],r['player'])]) for r in ex]
print('exhausted n',len(v),'closest approach (own linear model) before application (tc<0.1s):',sum(t<0.1 for t in v),' tc<=0:',sum(t<=0 for t in v),' 0.1..0.5:',sum(0.1<=t<0.5 for t in v),' >=0.5:',sum(t>=0.5 for t in v))
# episodes: first exhausted decision of each episode
first=[A['rows'][e['rows'][0]] for e in A['episodes']]
vf=[tc(obs[(r['seed'],r['tick'],r['player'])]) for r in first]
print('episode first EX n',len(vf),'tc<0.1',sum(t<0.1 for t in vf),' >=0.5',sum(t>=0.5 for t in vf))
it=[r for r in ex if r['intended'] and r['tick']-r['lastKick']['tick']<70]
seen=set();fi=[]
for r in sorted(it,key=lambda r:r['tick']):
    k=(r['seed'],r['lastKick']['tick'],r['player'])
    if k in seen:continue
    seen.add(k);fi.append((k,round(tc(obs[(r['seed'],r['tick'],r['player'])]),2),round(r['dBall'],1),round(r['lateral'],1)))
print('intended first EX (kick within 70t):',len(fi));[print(' ',x) for x in fi]
