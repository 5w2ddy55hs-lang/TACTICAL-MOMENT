import json,sys,gzip,collections,math
# Usage: python3 -I intended_passes.py <audit_fb.json> <input.json.gz> <out.json>
d=json.load(open(sys.argv[1]));W=json.load(gzip.open(sys.argv[2]))
rows=d['rows']
key=lambda r:(r['seed'],r['window'])
rowidx={(r['seed'],r['tick'],r['player']):r for r in rows}
it=[r for r in rows if r['status']=='generic_exhausted' and r['intended']]
passes=sorted({(r['seed'],r['window'],r['lastKick']['tick'],r['lastKick']['player'],r['player']) for r in it})
out=[]
for seed,win,kt,passer,rec in passes:
    w=[x for x in W if x['seed']==seed and x['start']==win][0]
    dec=[r for r in w['rows'] if r['channel']=='decision' and r['player']==rec and kt-6<=r['tick']<=kt+140]
    ev=[e for e in w['rows'] if e['channel']=='event' and kt<=e['tick']<=kt+160 and e['type'] in('kick','contact','restart_placement','goal','throw_pickup')]
    seq=[]
    for r in dec:
        a=rowidx.get((seed,r['tick'],rec))
        if a: seq.append((r['tick'],'R:'+{'generic_exhausted':'EX','generic_feasible':'FE','dedicated_plan':'DP'}[a['status']]+(f"{a['hitT']:.1f}" if a['hitT'] else ''),round(a['dBall'],1),round(a['along'],1),round(a['lateral'],1),a['planGate']))
        else: seq.append((r['tick'],r['decision']['kind']))
    kick=[e for e in ev if e['type']=='kick' and e['tick']==kt and e['player']==passer][0]
    nxt=[e for e in ev if e['tick']>kt and e['type'] in('kick','contact')][:4]
    firstEx=min(r['tick'] for r in it if r['seed']==seed and r['lastKick']['tick']==kt and r['player']==rec)
    out.append({'seed':seed,'window':win,'kickTick':kt,'passer':passer,'receiver':rec,'kickVel':kick.get('velocity'),'kickPos':kick.get('position'),'firstExhausted':firstEx,
                'nExhausted':sum(1 for r in it if r['seed']==seed and r['lastKick']['tick']==kt and r['player']==rec),'seq':seq,'next':[(e['tick'],e['type'],e.get('player'),e.get('team'),e.get('kind'),e.get('control')) for e in nxt],'windowEnd':w['end']})
json.dump(out,open(sys.argv[3],'w'),indent=1)
for p in out:
    v=p['kickVel'];sp=math.hypot(v['x'],v['y']) if v else None
    print(f"\n## seed {p['seed']} kick {p['kickTick']} {p['passer']}->{p['receiver']} speed {sp:.1f} vz {v['z']:.1f} firstEX {p['firstExhausted']} (+{p['firstExhausted']-p['kickTick']}t) nEX {p['nExhausted']} winEnd {p['windowEnd']}")
    print('  seq',' '.join(f"{s[0]}:{s[1]}" + (f"(d{s[2]},al{s[3]},lat{s[4]})" if len(s)>2 else '') for s in p['seq'][:22]))
    print('  next',p['next'])
