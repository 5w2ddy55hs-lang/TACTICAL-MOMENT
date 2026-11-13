# Final N23 classification of base-vs-K20 6 s possession differences. NOTE: these rules were fixed AFTER a first look at the
# 33 M22 cases (timeline_bk.py output), then applied unchanged to all 116 of 194 scenes whose ball events differ:
#  1) first ball-event difference (kick/contact/restart/goal; same order compare)
#  2) branches before it: K20 ALTERATION = K20 kind differs from original choose() on the identical DTO;
#     SECONDARY = base and K20 kinds differ at the same (tick, player) while the K20 decision equals the original choose()
#  3) chain at the first difference:
#     DIRECT     - a toucher at the first difference had a K20 alteration, and no toucher had a secondary branch before it
#     SECONDARY  - a toucher had a secondary branch before it (it reacted to an already different situation)
#     UNRESOLVED - touchers had neither (difference reached the ball through others' positions/ball path only)
#  4) 6 s label: SETTLED_AT_FIRST if after the first difference neither run has a further change of controlling team
#     (or restart) before 6 s; otherwise LATER (a later contest/reception decides the label)
#  final: K20_DIRECT = DIRECT & SETTLED_AT_FIRST ; UNDETERMINED = UNRESOLVED (path to the first ball difference not identified);
#         OTHER_BRANCH_FIRST = SECONDARY, or DIRECT whose 6 s label is decided by a LATER contest/reception
# usage: python3 -I classify_n23.py <kindsDir> <jobs.txt> <out.json>
import json,sys,collections
K,jobs,outF=sys.argv[1:4]
def teamline(ev,t0,after):
  s=[]
  for t,ty,p,team,ctrl in ev:
    if t<after or t>t0+120:continue
    if ty=='restart_placement' or ty=='goal':s.append(('R:'+str(team),t-t0));break
    if ctrl and (not s or s[-1][0]!=team):s.append((team,t-t0))
  return s
res=[];C=collections.Counter();D=collections.Counter()
for line in open(jobs):
  name,state,team=line.split();d=json.load(open(f'{K}/{name}.json'));B,Kk=d['base'],d['k20'];t0=Kk['t0']
  be=[e for e in B['ev'] if e[0]<=t0+120];ke=[e for e in Kk['ev'] if e[0]<=t0+120];i=0
  while i<min(len(be),len(ke)) and be[i]==ke[i]:i+=1
  fb=be[i] if i<len(be) else None;fk=ke[i] if i<len(ke) else None
  tdiv=min([x[0] for x in (fb,fk) if x] or [t0+121])
  alts=[];sec=[]
  for k,(kk,alt,dk) in Kk['dec'].items():
    t,p=k.split(':');t=int(t)
    if alt==1:alts.append((t,p,dk))
    b=B['dec'].get(k)
    if b and b[0]!=kk and alt==0:sec.append((t,p,b[0]+'->'+kk,dk))
  alts.sort();sec.sort()
  touchers={x[2] for x in (fb,fk) if x and x[2]}
  tAlt=[a for a in alts if a[1] in touchers and a[0]<tdiv];tSec=[s for s in sec if s[1] in touchers and s[0]<tdiv]

  chain='SECONDARY' if tSec else ('DIRECT' if tAlt else 'UNRESOLVED')
  lb=teamline(B['ev'],t0,tdiv);lk=teamline(Kk['ev'],t0,tdiv)
  settled=len(lb)<=1 and len(lk)<=1
  final='K20_DIRECT' if chain=='DIRECT' and settled else ('UNDETERMINED' if chain=='UNRESOLVED' else 'OTHER_BRANCH_FIRST')
  firstSec=sec[0] if sec else None
  C[(name[:2],final)]+=1;D[(name[:2],chain,'settled' if settled else 'later')]+=1
  res.append({'case':name,'team':team,'final':final,'chain':chain,'labelSettledAtFirstDifference':settled,
    'firstBallEventDiff':{'dt':tdiv-t0,'base':fb and [fb[0]-t0]+fb[1:],'k20':fk and [fk[0]-t0]+fk[1:]},
    'touchers':sorted(touchers),'toucherAlterations':[[a[0]-t0,a[1],a[2]] for a in tAlt][-3:],'toucherSecondary':[[s[0]-t0,s[1],s[2],s[3]] for s in tSec][:3],
    'firstAlteration':alts and [alts[0][0]-t0,alts[0][1],alts[0][2]],'firstSecondaryAnyPlayer':firstSec and [firstSec[0]-t0,firstSec[1],firstSec[2],firstSec[3]],
    'secondaryBeforeDiff':len([s for s in sec if s[0]<tdiv]),'alterationsBeforeDiff':len([a for a in alts if a[0]<tdiv]),
    'controlSequenceAfterDiff':{'base':lb,'k20':lk}})
json.dump(res,open(outF,'w'),ensure_ascii=False,indent=1)
print('final:');[print(' ',k,v) for k,v in sorted(C.items())]
print('chain x label:');[print(' ',k,v) for k,v in sorted(D.items())]
for r in res:
  print(f"{r['case']:16s} {r['final']:18s} {r['chain']:10s} div@{r['firstBallEventDiff']['dt']:+d} touchers={r['touchers']} alt={r['toucherAlterations']} sec={r['toucherSecondary'][:2]} firstSecAny={r['firstSecondaryAnyPlayer']} | after: base={r['controlSequenceAfterDiff']['base']} k20={r['controlSequenceAfterDiff']['k20']}")
