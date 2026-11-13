# All 194 fast-ball scenes (M22 list): how often K20 changes a decision at all, how often the ball path then differs,
# and how often the 6 s label differs. Same 6 s rule as k20_probe (last controlled touch or restart at t0+120).
# usage: python3 -I base_rate_194.py <kindsDir> <jobs.txt> <out.json>
import json,sys,collections
K,jobs,outF=sys.argv[1:4]
def poss(ev,t0,H):
  c=[e for e in ev if e[1] in('kick','contact') and e[4] and e[0]<=t0+H];r=[e for e in ev if e[1]=='restart_placement' and e[0]<=t0+H]
  if r and (not c or r[-1][0]>=c[-1][0]):return 'restart:'+r[-1][3]
  return c[-1][3] if c else 'none'
rows=[];C=collections.Counter()
for line in open(jobs):
  name,state,team=line.split();d=json.load(open(f'{K}/{name}.json'));B,Kk=d['base'],d['k20'];t0=Kk['t0']
  keep=lambda R:poss(R['ev'],t0,120) in (team,'restart:'+team)
  be=[e for e in B['ev'] if e[0]<=t0+120];ke=[e for e in Kk['ev'] if e[0]<=t0+120]
  alts=[(int(k.split(':')[0])-t0,k.split(':')[1],v[2]) for k,v in Kk['dec'].items() if v[1]==1]
  first=[a for a in alts if a[0]<4]
  bk,kk=keep(B),keep(Kk)
  r={'case':name,'team':team,'baseKeeps':bk,'k20Keeps':kk,'altsAny':len(alts),'altsFirstCycle':len(first),
     'altNearBall<=5m':sum(1 for a in alts if a[2] is not None and a[2]<=5),
     'ballEventsDiffer':be!=ke,'firstCtrlTeam':{'base':next((e[3] for e in be if e[1] in('kick','contact') and e[4]),None),'k20':next((e[3] for e in ke if e[1] in('kick','contact') and e[4]),None)}}
  rows.append(r)
  lab='same' if bk==kk else ('BK' if bk else 'KB')
  C[(lab,'K20 alteration at +0..+3' if first else ('later alteration only' if alts else 'no alteration'),'ball events differ' if be!=ke else 'ball events identical')]+=1
json.dump(rows,open(outF,'w'),indent=0)
print('6 s keep: base',sum(r['baseKeeps'] for r in rows),'K20',sum(r['k20Keeps'] for r in rows),'of',len(rows))
for k,v in sorted(C.items()):print(' ',k,v)
fc=collections.Counter(('same' if r['firstCtrlTeam']['base']==r['firstCtrlTeam']['k20'] else 'differ') for r in rows);print('first controlling team base vs K20:',dict(fc))
