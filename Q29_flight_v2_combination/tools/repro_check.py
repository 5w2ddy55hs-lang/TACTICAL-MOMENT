# C4: a new recording equals an existing (reference-matched) recording over the overlapping ticks: every frame and every
# sink row with tick >= start (all channels, same order). Read only.
# usage: python3 -I repro_check.py <new.json.gz> <reference.json.gz> [label]
import json,gzip,sys
a=json.load(gzip.open(sys.argv[1]));b=json.load(gzip.open(sys.argv[2]));lab=sys.argv[3] if len(sys.argv)>3 else ''
fa={f['tick']:f for f in a['frames']};fb={f['tick']:f for f in b['frames']}
common=sorted(set(fa)&set(fb));lo,hi=common[0],common[-1]
fbad=next((t for t in common if json.dumps(fa[t],sort_keys=True)!=json.dumps(fb[t],sort_keys=True)),None)
ra=[r for r in a['rows'] if isinstance(r.get('tick'),int) and lo<=r['tick']<=hi]
rb=[r for r in b['rows'] if isinstance(r.get('tick'),int) and lo<=r['tick']<=hi]
# rows emitted at the very first common tick may include carry-over rows only in the longer run; compare from lo+1 as well
def cmp(x,y):
    n=min(len(x),len(y));i=next((k for k in range(n) if json.dumps(x[k],sort_keys=True)!=json.dumps(y[k],sort_keys=True)),None)
    return i,len(x),len(y)
i,nx,ny=cmp(ra,rb)
ra1=[r for r in ra if r['tick']>lo];rb1=[r for r in rb if r['tick']>lo];i1,nx1,ny1=cmp(ra1,rb1)
print(json.dumps({'label':lab,'ticks':[lo,hi],'frames':len(common),'firstFrameMismatch':fbad,'rowsFromStart':{'firstMismatchIndex':i,'n_new':nx,'n_ref':ny},'rowsAfterStartTick':{'firstMismatchIndex':i1,'n_new':nx1,'n_ref':ny1}}))
