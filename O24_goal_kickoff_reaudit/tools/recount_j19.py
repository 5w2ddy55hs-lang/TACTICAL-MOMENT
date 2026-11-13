# O24: recount J19 same-opportunity "regain within 6 s (in play or by restart)" from stored rows (paired_def_eval.mjs).
# The follow STOPS at the first restart or the first regain in play. "regainedByRestart" = first restart awarded to the
# defending team -> after a goal by the attacking team the kickoff goes to the defenders and was counted as a regain.
# Classes per row/engine (exactly one): REGAIN_PLAY, RESTART_DEF_AFTER_OPP_GOAL (the flaw), RESTART_DEF_OTHER,
# RESTART_ATT (restart to attackers, incl. after a defender goal), NO_REGAIN_WINDOW_END, UNKNOWN.
# usage: python3 -I recount_j19.py <out.json> <paired_*.json>...
import json,sys,collections
rows=[]
for f in sys.argv[2:]:rows+=json.load(open(f))['rows']
def cls(x,k):
  dfn='B' if k['team']=='A' else 'A'
  if x['regain'] is not None:return 'REGAIN_PLAY'
  if x['restart']:
    kind,team=x['restart'].split(':')
    if team==dfn:
      if kind=='kickoff' and x['oppGoal']:return 'RESTART_DEF_AFTER_OPP_GOAL'
      if kind=='kickoff':return 'UNKNOWN'
      return 'RESTART_DEF_OTHER'
    return 'RESTART_ATT'
  return 'NO_REGAIN_WINDOW_END'
out={}
for sub,sel in (('all',lambda r:True),('onChanged(J19 intervened)',lambda r:r['j19']['j19']>0)):
  R=[r for r in rows if sel(r)];o={'n':len(R)}
  for e in('base','j19'):
    C=collections.Counter(cls(r[e],r['k']) for r in R)
    old=sum(1 for r in R if r[e]['regain'] is not None or r[e]['regainedByRestart'])
    o[e]={'classes':dict(sorted(C.items())),'oldRegained':old,'oldCheck':C['REGAIN_PLAY']+C['RESTART_DEF_AFTER_OPP_GOAL']+C['RESTART_DEF_OTHER'],'correctedRegained':C['REGAIN_PLAY']+C['RESTART_DEF_OTHER'],'regainInPlay':C['REGAIN_PLAY']}
  out[sub]=o
json.dump(out,open(sys.argv[1],'w'),indent=1)
for sub,o in out.items():
  print(sub,'n',o['n']);[print('  ',e,o[e]) for e in('base','j19')]
