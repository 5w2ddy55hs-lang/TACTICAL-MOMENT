import json,gzip,sys,os,math,collections
# Usage: python3 -I suite_passes.py <audit_suite.json> <suite root> <out.json>
A=json.load(open(sys.argv[1]));R=sys.argv[2]
cases=json.load(open(os.path.join(R,'cases.json')))['cases']
idx={(a['case'],a['tick'],a['player']):a for a in A}
out=[]
for c in cases:
    x=json.load(gzip.open(os.path.join(R,c['expected'])))
    F={f['tick']:f for f in x['frames']}
    ev=[r for r in x['rows'] if r['channel']=='event']
    kicks=[e for e in ev if e['type']=='kick' and e.get('kind') in('pass','restart_kick','shoot','dribble')]
    print(f"\n### {c['id']} seed {c['seed']} {c['start']}-{c['end']}")
    for k in kicks:
        if k.get('kind')!='pass' and k.get('kind')!='restart_kick':continue
        rec=k.get('targetId');K=k['tick']
        if not rec:continue
        nxt=[e for e in ev if e['tick']>K and e['type'] in('kick','contact')]
        first=nxt[0] if nxt else None
        endT=first['tick'] if first else c['end']
        dec=[r for r in x['rows'] if r['channel']=='decision' and r['player']==rec and K-4<=r['tick']<=endT+10]
        seq=[]
        for r in dec:
            a=idx.get((c['id'],r['tick'],rec))
            lab=r['decision']['kind'] if not a else {'generic_exhausted':'EX','generic_feasible':'FE','dedicated_plan':'DP','velocity_unknown':'VU'}[a['status']]+(f"{a['hitT']:.1f}" if a['hitT'] else '')+('' if a['kind']=='receive' else '/'+a['kind'][:3])
            extra=f"(al{a['along']:.1f},lat{a['lateral']:.1f},min{a['minTrue']['d']:.1f}@{a['minTrue']['tick']})" if a else ''
            seq.append(f"{r['tick']}:{lab}{extra}")
        # true closest receiver-ball from kick to first next touch
        best=None
        for t in range(K,endT+1):
            f=F.get(t)
            if not f:break
            p=next(p for p in f['players'] if p['id']==rec);dd=math.hypot(p['x']-f['ball']['x'],p['y']-f['ball']['y'])
            if best is None or dd<best[0]:best=(dd,t)
        v=k['velocity'];sp=math.hypot(v['x'],v['y'])
        line=f"kick {K} {k['player']}->{rec} ({k.get('kind')}) speed {sp:.1f} vz {v['z']:.1f} | first next {first and (first['tick'],first['type'],first.get('player'),first.get('control'))} | true closest {best and (round(best[0],2),best[1])}"
        print(line);print('   ',' '.join(seq[:26]))
        out.append({'case':c['id'],'kick':K,'passer':k['player'],'receiver':rec,'speed':sp,'vz':v['z'],'first':first and {'tick':first['tick'],'type':first['type'],'player':first.get('player'),'control':first.get('control')},'trueClosest':best,'seq':seq})
json.dump(out,open(sys.argv[3],'w'),indent=1)
