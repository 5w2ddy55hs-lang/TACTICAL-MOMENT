import json,gzip,sys,collections
W=json.load(gzip.open(sys.argv[1]));A=json.load(open(sys.argv[2]))
obs={}
for w in W:
    for r in w['rows']:
        if r['channel']=='decision' and r['decision']['kind']=='receive':obs[(w['seed'],r['tick'],r['player'])]=r['observation']
own=lambda x,d:x if d==1 else 105-x
c=collections.Counter()
for r in A['rows']:
    if r['status']!='generic_exhausted':continue
    o=obs[(r['seed'],r['tick'],r['player'])];p=o['self'];b=o['ball']
    role=p['role'] in('CB','FB');half=own(p['x'],p['dir'])>52.5;ahead=own(b['x'],p['dir'])>own(p['x'],p['dir'])+4 and b['vx']*p['dir']>0
    c[(role,role and half,role and half and ahead)]+=1
print('exhausted: (CB/FB, +beyond halfway, +ball ahead toward opponent goal)',c)
