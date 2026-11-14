# First divergence between two recordings of the same start (frames and decision rows). Read only.
# usage: python3 -I first_divergence.py <a.json.gz> <b.json.gz>
import json,gzip,sys
a=json.load(gzip.open(sys.argv[1]));b=json.load(gzip.open(sys.argv[2]))
fa={f['tick']:f for f in a['frames']};fb={f['tick']:f for f in b['frames']}
fd=next((t for t in sorted(fa) if t in fb and json.dumps(fa[t],sort_keys=True)!=json.dumps(fb[t],sort_keys=True)),None)
da=[r for r in a['rows'] if r['channel']=='decision'];db=[r for r in b['rows'] if r['channel']=='decision']
ka={(r['tick'],r['player']):r for r in da};kb={(r['tick'],r['player']):r for r in db}
diff=[k for k in sorted(set(ka)|set(kb)) if k not in ka or k not in kb or json.dumps(ka[k]['decision'],sort_keys=True)!=json.dumps(kb[k]['decision'],sort_keys=True)]
print('first frame divergence',fd)
for k in diff[:4]:
    x=ka.get(k);y=kb.get(k)
    print(' decision diff',k,'A:',x and (x['decision']['kind'],x['decision'].get('target'),x['decision'].get('reason')),'| B:',y and (y['decision']['kind'],y['decision'].get('target'),y['decision'].get('reason')))
