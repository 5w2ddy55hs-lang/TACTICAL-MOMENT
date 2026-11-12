import json,math,sys
K=sys.argv[1]
for L in sys.argv[2:]:
  for v in ['base','k20']:
    d=json.load(open(f'{K}/probe/{L}_{v}.json'));fr=sorted(d['frames'],key=lambda f:f['t']);t0=fr[0]['t']
    ev=[(e['t'],e.get('player'),e['type'][:4],e.get('kind') or ('ctrl' if e.get('control') else 'noctrl')) for e in d['events'] if e['type'] in('kick','contact','restart_placement')]
    ctl=[e for e in d['events'] if e['type']=='contact' and e.get('control')]
    T=ctl[0]['team'] if ctl else None
    # attack switch: support/advance share among T's outfield decisions in first 2 s after control, and real forward speed
    tc=ctl[0]['t'] if ctl else t0
    dec=[x for x in d['decisions'] if x['team']==T and tc<x['t']<=tc+40 and x['p'][1:]!='00']
    sup=sum(x['kind'] in('support','advance_support','cover_exchange') for x in dec);cov=sum(x['kind']=='cover' for x in dec)
    gk=[p for p in fr[0]['p'] if p['id']==(T or 'A')+'00'][0];D=1 if gk['x']<52.5 else -1
    f0=next(f for f in fr if f['t']>=tc);f2=next((f for f in fr if f['t']>=tc+40),fr[-1])
    P0={p['id']:p for p in f0['p']};P2={p['id']:p for p in f2['p']}
    mates=[i for i in P0 if T and i[0]==T and i[1:]!='00' and i!=ctl[0]['player']]
    fwd=sum((P2[i]['x']-P0[i]['x'])*D for i in mates)/max(1,len(mates))
    print(f"{L} {v:4} ctrlTeam={T} at {tc} support/cover decisions 2s: {sup}/{cov} matesFwd2s={fwd:+.2f}m events={ev[:7]}")
