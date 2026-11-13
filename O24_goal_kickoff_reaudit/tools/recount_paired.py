# O24: recount the "trigger team still has the ball at 3 s / 6 s" labels of the stored same-opportunity paired results
# (K20 paired_k20.mjs, L21 paired_multi.mjs, M22 paired_from_branch.mjs). Those follows STOP at the first restart
# (restart_placement) and label the window "restart:<team>" -> a conceded goal (kickoff for the conceding team) was
# counted as "kept", a scored goal as "not kept". This script only re-reads stored rows; nothing is re-simulated.
# Each row/engine/window is put in exactly one class:
#   GOAL_AGAINST, GOAL_FOR       : the first restart in the window is the kickoff after a goal (goal tick inside window)
#   PERIOD_END                   : the window ran into the half-time kickoff (kickoff, no goal) -> CUT OFF, removed from
#                                  numerator AND denominator of the corrected rate (listed separately)
#   RESTART_OWN, RESTART_OPP     : any other restart (throw-in, goal kick, corner, free kick...) for own / other team
#   CTRL_OWN, CTRL_OPP           : window ended in play, last controlled touch by own / other team
#   NO_CTRL                      : window ended in play, no controlled touch since the trigger
#   UNKNOWN                      : anything that does not fit (reported, never merged)
# OLD keep (as published) = CTRL_OWN + RESTART_OWN + (kickoff restarts for the trigger team: GOAL_AGAINST, PERIOD_END own)
# CORRECTED keep           = CTRL_OWN + RESTART_OWN over denominator n - PERIOD_END (goal-against = not kept; goal-for listed)
# usage: python3 -I recount_paired.py <out.json> <name>=<file>[,<file>...] ...
import json,sys,collections
def classify(x,k,W):
  team=k['team'];lab=x['poss3' if W==60 else 'poss6']
  if lab.startswith('restart:'):
    kind,rteam=(x['restart'] or ':').split(':')
    if rteam!=lab.split(':')[1]:return 'UNKNOWN'
    if kind=='kickoff':
      g=[q for q in x.get('goals',[]) if q['t']<=k['t']+W]
      if g:return 'GOAL_FOR' if g[0]['team']==team else 'GOAL_AGAINST'
      return 'PERIOD_END'
    return 'RESTART_OWN' if rteam==team else 'RESTART_OPP'
  if lab=='none':return 'NO_CTRL'
  if lab in('A','B'):return 'CTRL_OWN' if lab==team else 'CTRL_OPP'
  return 'UNKNOWN'
def old_keep(x,k,W):
  lab=x['poss3' if W==60 else 'poss6'];return lab==k['team'] or lab=='restart:'+k['team']
if __name__=='__main__':
  out={}
  for spec in sys.argv[2:]:
    name,files=spec.split('=',1);rows=[]
    for f in files.split(','):
      d=json.load(open(f));rows+= [r for r in d['rows'] if r['k'].get('type','change') in('change','list') and r['k'].get('team')]
    engines=[e for e in rows[0] if e!='k']
    res={'n':len(rows),'files':files.split(','),'engines':engines}
    for W,wn in((60,'3s'),(120,'6s')):
      for e in engines:
        C=collections.Counter(classify(r[e],r['k'],W) for r in rows)
        old=sum(old_keep(r[e],r['k'],W) for r in rows)
        # consistency: old keep must equal CTRL_OWN+RESTART_OWN+GOAL_AGAINST+KICKOFF_NO_GOAL(own)
        ko_own=sum(1 for r in rows if classify(r[e],r['k'],W)=='PERIOD_END' and r[e]['poss3' if W==60 else 'poss6']=='restart:'+r['k']['team'])
        new=C['CTRL_OWN']+C['RESTART_OWN']
        res[f'{wn}:{e}']={'classes':dict(sorted(C.items())),'oldKeep':old,'oldKeepCheck':C['CTRL_OWN']+C['RESTART_OWN']+C['GOAL_AGAINST']+ko_own,'correctedKeep':new,'correctedDenominator':len(rows)-C['PERIOD_END'],'periodEndCut':C['PERIOD_END'],
          'stoppedByRestartBeforeWindowEnd':sum(v for k2,v in C.items() if k2.startswith(('GOAL','RESTART','PERIOD')))}
      # paired differences (one-sided keeps) old vs corrected for every engine pair vs the first engine
      base=engines[0]
      for e in engines[1:]:
        ob=sum(1 for r in rows if old_keep(r[base],r['k'],W) and not old_keep(r[e],r['k'],W));oe=sum(1 for r in rows if old_keep(r[e],r['k'],W) and not old_keep(r[base],r['k'],W))
        nk=lambda x,k:classify(x,k,W) in('CTRL_OWN','RESTART_OWN')
        nb=sum(1 for r in rows if nk(r[base],r['k']) and not nk(r[e],r['k']));ne=sum(1 for r in rows if nk(r[e],r['k']) and not nk(r[base],r['k']))
        chg=[{'t':r['k']['t'],'team':r['k']['team'],base:classify(r[base],r['k'],W),e:classify(r[e],r['k'],W)} for r in rows if (old_keep(r[base],r['k'],W)!=old_keep(r[e],r['k'],W))!=(nk(r[base],r['k'])!=nk(r[e],r['k'])) or ((old_keep(r[base],r['k'],W) and not old_keep(r[e],r['k'],W))!=(nk(r[base],r['k']) and not nk(r[e],r['k'])))]
        res[f'{wn}:{base}_vs_{e}']={'old_onlyBase':ob,'old_onlyOther':oe,'corrected_onlyBase':nb,'corrected_onlyOther':ne,'rowsWhoseDiscordanceChanged':chg}
    out[name]=res
  json.dump(out,open(sys.argv[1],'w'),indent=1,ensure_ascii=False)
  for name,res in out.items():
    print('##',name,'n',res['n'],'engines',res['engines'])
    for W in('3s','6s'):
      print('  ',W,' | '.join(f"{e}: old {res[f'{W}:{e}']['oldKeep']} (check {res[f'{W}:{e}']['oldKeepCheck']}) -> corrected {res[f'{W}:{e}']['correctedKeep']}  GA {res[f'{W}:{e}']['classes'].get('GOAL_AGAINST',0)} GF {res[f'{W}:{e}']['classes'].get('GOAL_FOR',0)} cut {res[f'{W}:{e}']['periodEndCut']} (den {res[f'{W}:{e}']['correctedDenominator']}) UNK {res[f'{W}:{e}']['classes'].get('UNKNOWN',0)}" for e in res['engines']))
      for e in res['engines'][1:]:
        p=res[f"{W}:{res['engines'][0]}_vs_{e}"];print('     ',f"{res['engines'][0]} vs {e}: one-sided old {p['old_onlyBase']}/{p['old_onlyOther']} -> corrected {p['corrected_onlyBase']}/{p['corrected_onlyOther']}; rows changed {len(p['rowsWhoseDiscordanceChanged'])}")
  