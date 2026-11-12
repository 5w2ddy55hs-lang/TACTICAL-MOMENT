import json,sys
r=json.load(open(sys.argv[1]))
def pct(a,b): return f"{100*a/b:.0f}%" if b else '-'
print('run|zonal|end|score|play_min|kicks pass/drib/shoot|opp_carry ≥3chasers|sameTarget≥3 (opp_carry)|conc ep / win3s / conceded10m|joint2 ep / win3s|centralEmpty/danger|freeBehind ep|pass tgt_ctrl/opp/other/retouch/out|tgtNeverRecv|trans goalSide 0→5s|CK n / att in box / def first / shot10s|throw-ins|own_carry 2+ teammates chasing')
for x in r:
  c=x['conc'];p=x['passes'];k=x['counts']['kickKinds'];st=x['sameTarget2m']['opp_carry']
  print('|'.join(map(str,[x['run'],x['zonal'],(x['crash'] and f"STOP@{x['crashTick']}") or x['finalTick'],f"{x['score']['A']}-{x['score']['B']}" if x['score'] else '-',round(x['playSec']/60,1),f"{k.get('pass',0)}/{k.get('dribble',0)}/{k.get('shoot',0)}",
   pct(c['opp_carry']['ge3'],c['opp_carry']['ticks']),pct(st['ge3'],st['ticks']),f"{x['concEpisodes']}/{x['concEpOwnWin3s']}/{x['concEpConceded10m']}",f"{x['jointPressEpisodes']}/{x['jointOwnWin3s']}",
   pct(x['def']['centralEmpty'],x['def']['danger']),x['freeBehindEpisodes'],f"{pct(p['target_control'],p['n'])}/{pct(p['opponent'],p['n'])}/{pct(p['teammate_other'],p['n'])}/{pct(p.get('passer_retouch',0),p['n'])}/{pct(p['out'],p['n'])}",pct(p['targetNeverReceive'],p['n']),
   f"{x['trans']['loserGoalSide0']}→{x['trans']['loserGoalSide5s']}",f"{x['corners']['n']}/{x['corners']['attInBoxMean']}/{x['corners']['firstTouchDef']}/{x['corners']['shot10s']}",x['restarts'].get('throw_in',{}).get('count'),pct(c['own_carry_teammatesChasing']['ge3']+c['own_carry_teammatesChasing']['eq2'],c['own_carry_teammatesChasing']['ticks'])])))
