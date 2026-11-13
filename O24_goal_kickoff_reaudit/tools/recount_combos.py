# O24: M22 section 1 table: combinations of "kept at 6 s" (base / K20 / L21) on the 1,154 same opportunities
# (stored pm3 rows, follow stops at the first restart). OLD = as published; CORRECTED = goal-against kickoff not kept.
# usage: python3 -I recount_combos.py <out.json> <pm3 files...>
import json,sys,collections
sys.path.insert(0,__file__.rsplit('/',1)[0]);from recount_paired import classify,old_keep
rows=[];[rows.extend(json.load(open(f))['rows']) for f in sys.argv[2:]]
rows=[r for r in rows if r['k'].get('type')=='change' and r['k'].get('team')]
def combo(r,f):return '/'.join('保持' if f(r[e],r['k']) else '喪失' for e in('base','k20','l21'))
nk=lambda x,k:classify(x,k,120) in('CTRL_OWN','RESTART_OWN')
ok=lambda x,k:old_keep(x,k,120)
O=collections.Counter(combo(r,ok) for r in rows);N=collections.Counter(combo(r,nk) for r in rows)
moved=[{'t':r['k']['t'],'team':r['k']['team'],'old':combo(r,ok),'corrected':combo(r,nk),'classes':{e:classify(r[e],r['k'],120) for e in('base','k20','l21')}} for r in rows if combo(r,ok)!=combo(r,nk)]
json.dump({'n':len(rows),'old':dict(O),'corrected':dict(N),'moved':moved},open(sys.argv[1],'w'),ensure_ascii=False,indent=1)
for k in sorted(set(O)|set(N)):print(k,O[k],'->',N[k])
print('moved',len(moved));[print(' ',m) for m in moved]
