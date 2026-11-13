# Attribute each L21-only loss/gain to whose yield preceded the first K20/L21 divergence, and what changed there.
import json,sys,collections
P,divF,outF=sys.argv[1:4]
D=json.load(open(divF));C=collections.Counter();out=[]
for r in D:
  d=json.load(open(f"{P}/{r['case']}.json"));ys=[y for y in d['l21']['yields'] if y['t']<=r['divTick']]
  last=ys[-1] if ys else None;yt=last['p'][0] if last else None
  own=yt==r['team']
  K=[x for x in d['k20']['events'] if x['type'] in('kick','contact')];L=[x for x in d['l21']['events'] if x['type'] in('kick','contact')]
  fk=next((x for x in K if x['t']>=r['divTick']),None);fl=next((x for x in L if x['t']>=r['divTick']),None)
  dt=abs((fk['t'] if fk else 1e9)-(fl['t'] if fl else 1e9))
  if not last: cat='no_yield_before_divergence'
  elif fk and fl and fk['team']==fl['team'] and dt<=4: cat='timing_only(<=4 ticks,same team)->later_branch'
  elif not own and fl and fl['team']==yt: cat='opponent_yield_then_opponent_collects(opponent_legit_gain)'
  elif own and fl and fl['team']!=r['team']: cat='own_yield_then_opponent_touch_first(L21_yield_cause_candidate)'
  elif own and fl and fl['team']==r['team']: cat='own_yield_then_own_collects'
  elif own and not fl: cat='own_yield_then_no_touch'
  else: cat='undetermined'
  C[(r['case'][0],cat)]+=1
  out.append({**r,'lastYieldTeam':yt,'ownTeamYield':own,'attribution':cat,'lastYield':last})
json.dump(out,open(outF,'w'),ensure_ascii=False,indent=0)
for k,v in sorted(C.items()):print(k,v)
