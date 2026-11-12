# usage: python3 -I crossrun.py <agg.json> <runsDir>  -> condition totals (JSON on stdout)
import json,os,sys,collections
rows=json.load(open(sys.argv[1]));R=sys.argv[2];out={}
for grp,pred in [('std_off',lambda r:r['variant']=='standard' and not r['zonal']),('std_on',lambda r:r['variant']=='standard' and r['zonal']),('ck_off',lambda r:r['variant']=='ck_research')]:
  rs=[r for r in rows if pred(r)];S=lambda f:sum(f(r) for r in rs);c=lambda ctx,k:S(lambda r:r['conc'][ctx][k])
  o={'runs':[r['run'] for r in rs],'matches':len(rs),'playMin':round(S(lambda r:r['playSec'])/60,1),'simMin':round(S(lambda r:r['finalTick'])/1200,1)}
  t=c('opp_carry','ticks');o['oppCarry_ge3']=round(100*c('opp_carry','ge3')/t,1);o['oppCarry_eq2']=round(100*c('opp_carry','eq2')/t,1);o['oppCarry_le1']=round(100*(c('opp_carry','eq1')+c('opp_carry','eq0'))/t,1)
  o['sameTarget_ge3_oppCarry']=round(100*S(lambda r:r['sameTarget2m']['opp_carry']['ge3'])/S(lambda r:r['sameTarget2m']['opp_carry']['ticks']),1)
  oc='own_carry_teammatesChasing';o['ownCarry_2plus_chasing']=round(100*(c(oc,'ge3')+c(oc,'eq2'))/c(oc,'ticks'),1)
  for k,f in [('concEp','concEpisodes'),('concEpOppCarryStart','concEpOppCarryStart'),('concWin3s','concEpOwnWin3s'),('concConceded10m','concEpConceded10m'),('joint','jointPressEpisodes'),('jointWin3s','jointOwnWin3s'),('jointConceded10m','jointConceded10m'),('centralEmptyEp','centralEmptyEpisodes'),('centralEmptyEpShot','centralEmptyEpisodesShot'),('freeBehind','freeBehindEpisodes')]: o[k]=S(lambda r:r[f])
  o['flipsPerMin']=round(S(lambda r:r['flips'])/len(rs),1);o['turnoversPerMin']=round(S(lambda r:r['turnoversPerMin'])/len(rs),1)
  ms=collections.Counter()
  for r in rs: ms.update(r['modeShare'])
  for ctx in ['own_carry','own_pass_flight','opp_carry']:
    tot=sum(v for k,v in ms.items() if k.startswith('mode_'+ctx+':'));o['mode_'+ctx]={k.split(':')[1]:round(100*v/tot,1) for k,v in ms.items() if k.startswith('mode_'+ctx+':')}
  P=lambda k:S(lambda r:r['passes'][k]);n=P('n');o['passes']=n
  o['pass_pct']={k:round(100*P(k)/n,1) for k in ['target_control','target_no_control','teammate_other','passer_retouch','opponent','out']};o['targetNeverReceive_pct']=round(100*P('targetNeverReceive')/n,1)
  o['tc_next']={k:P(k) for k in ['tc_next_self','tc_next_opp','tc_next_team','tc_next_out']}
  o['throwIns']={k:S(lambda r:r['throwIns'][k]) for k in ['n','target_control','opponent','out','outToOppCorner','targetNeverReceive']}
  co=collections.Counter()
  for r in rs: co.update(r['corners']['origins'])
  o['corners']=S(lambda r:r['corners']['n']);o['cornerOrigins']=dict(co)
  for k,f in [('cornerShot10s','shot10s'),('cornerGoal10s','goal10s'),('cornerAttFirst','firstTouchAtt')]: o[k]=S(lambda r:r['corners'][f])
  o['cornerAttInBoxMean']=round(S(lambda r:r['corners']['attInBoxMean']*r['corners']['n'])/max(1,o['corners']),2)
  o['goals']=S(lambda r:sum((r['score'] or {'A':0,'B':0}).values()));o['shots']=S(lambda r:r['shots'])
  gl=collections.Counter()
  for r in rs:
    for l in open(os.path.join(R,r['run'],'events.jsonl')):
      if '"type":"goal"' in l:
        e=json.loads(l);gl['scorer_team' if e['lastTeam']==e['team'] else ('none' if e['lastTouch'] is None else ('conceding_GK' if e['lastTouch'][1:]=='00' else 'conceding_outfield'))]+=1
  o['goalLastTouch']=dict(gl)
  o['restartMin']=round(S(lambda r:r['phaseTicks'].get('restart',0))/1200,1)
  o['stops']=[(r['run'],r['crash'],r['crashTick']) for r in rs if r['crash']]
  out[grp]=o
print(json.dumps(out,ensure_ascii=False,indent=1))
