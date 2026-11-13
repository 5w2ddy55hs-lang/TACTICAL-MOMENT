# O24: N23 full-6 s label (pair_kinds / k20_probe: the follow does NOT stop at restarts; label at t0+120 = last
# controlled touch or later restart placement). Classes: GOAL_AGAINST / GOAL_FOR (a goal inside the 6 s, whatever
# follows), PERIOD_END (window runs into the half-time kickoff: cut off, removed from the corrected denominator),
# else RESTART_OWN / RESTART_OPP (last event a non-goal restart), CTRL_OWN / CTRL_OPP, NO_CTRL.
# OLD keep (N23 table "N23 の数え方") = label is own control or restart for own team. CORRECTED = GOAL_AGAINST not kept.
# usage: python3 -I recount_full6s.py <kindsDir> <jobs.txt> <out.json>
import json,sys,collections
K,jobs,outF=sys.argv[1:4]
def poss(ev,t0):
  c=[e for e in ev if e[1] in('kick','contact') and e[4] and e[0]<=t0+120];r=[e for e in ev if e[1]=='restart_placement' and e[0]<=t0+120]
  if r and (not c or r[-1][0]>=c[-1][0]):return 'restart:'+r[-1][3]
  return c[-1][3] if c else 'none'
def cls(R,team):
  t0=R['t0'];g=[e for e in R['ev'] if e[1]=='goal' and e[0]<=t0+120]
  if g:return 'GOAL_FOR' if g[0][3]==team else 'GOAL_AGAINST'
  p=poss(R['ev'],t0)
  rs=[e for e in R['ev'] if e[1]=='restart_placement' and e[0]<=t0+120]
  if p.startswith('restart:') and rs and rs[-1][0]==54000:return 'PERIOD_END'  # kinds files hold no restart kind; the half-time kickoff is placed at halfTicks=54000 (no goal in window)
  if p.startswith('restart:'):return 'RESTART_OWN' if p[8:]==team else 'RESTART_OPP'
  if p=='none':return 'NO_CTRL'
  return 'CTRL_OWN' if p==team else 'CTRL_OPP'
out={};rows=[]
for line in open(jobs):
  name,state,team=line.split();d=json.load(open(f'{K}/{name}.json'))
  rows.append({'case':name,'team':team,**{e:{'cls':cls(d[e],team),'oldKeep':poss(d[e]['ev'],d[e]['t0']) in(team,'restart:'+team)} for e in('base','k20')}})
for e in('base','k20'):
  C=collections.Counter(r[e]['cls'] for r in rows)
  out[e]={'classes':dict(sorted(C.items())),'oldKeep':sum(r[e]['oldKeep'] for r in rows),'correctedKeep':C['CTRL_OWN']+C['RESTART_OWN'],'correctedDenominator':len(rows)-C['PERIOD_END']}
nk=lambda r,e:r[e]['cls'] in('CTRL_OWN','RESTART_OWN')
out['oneSided']={'old':[sum(1 for r in rows if r['base']['oldKeep'] and not r['k20']['oldKeep']),sum(1 for r in rows if r['k20']['oldKeep'] and not r['base']['oldKeep'])],
 'corrected':[sum(1 for r in rows if nk(r,'base') and not nk(r,'k20')),sum(1 for r in rows if nk(r,'k20') and not nk(r,'base'))]}
out['n']=len(rows);json.dump(out,open(outF,'w'),indent=1);print(json.dumps(out,ensure_ascii=False))
