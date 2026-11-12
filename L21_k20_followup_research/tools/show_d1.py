import json,math,sys
K=sys.argv[1]
for v in ['base','k20']:
  d=json.load(open(f'{K}/probe/D1_{v}.json'));fr={f['t']:f for f in d['frames']}
  print('#####',v,'events',[(e['t'],e.get('player'),e['type'][:5],e.get('kind') or ('ctrl' if e.get('control') else 'noctrl')) for e in d['events']][:8])
  for pid in ['B05','B01','B03','B06','B02']:
    seq=[];last=None
    for x in d['decisions']:
      if x['p']==pid and x['t']<=94830 and x['kind']!=last: seq.append(f"{x['t']}:{x['kind'][:6]}");last=x['kind']
    print(' ',pid,' '.join(seq)[:300])
  for t in range(94741,94830,8):
    f=fr[t];b=f['ball'];P={p['id']:p for p in f['p']};dd=lambda i:math.hypot(P[i]['x']-b[0],P[i]['y']-b[1])
    print('   ',t,'ball',b[:2],' '.join(f'{i}:{dd(i):.1f}' for i in ['A10','B05','B01','B03','B06','B02']))
