import json,gzip,sys,collections
W=json.load(gzip.open(sys.argv[1]))
c=collections.Counter();bp=collections.Counter()
for w in W:
    for r in w['rows']:
        if r['channel']=='decision' and r['decision']['kind']=='receive':
            c[tuple(sorted(r['decision'].keys()))]+=1
            if 'bodyPreparation' in r['decision']:bp[json.dumps(r['decision']['bodyPreparation'])[:120]]+=1
for k,v in c.most_common():print(v,k)
print(bp.most_common(5))
# decision intervals per player
iv=collections.Counter()
for w in W:
    last={}
    for r in w['rows']:
        if r['channel']=='decision':
            if r['player'] in last:iv[r['tick']-last[r['player']]]+=1
            last[r['player']]=r['tick']
print('intervals',sorted(iv.items())[:12])
