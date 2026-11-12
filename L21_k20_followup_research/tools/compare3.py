# 3-way same-state comparison (base / K20 / L21) of fixed scenes from poss_probe outputs.
# usage: python3 -I compare3.py <k20 probe dir> <l21 probe dir> <cases.txt>
import json,sys,math,importlib.util
spec=importlib.util.spec_from_file_location('cp',sys.argv[1]+'/../compare_poss.py')
def load(p): return json.load(open(p))
def summ(P):
  fr=sorted(P['frames'],key=lambda f:f['t']);ev=P['events'];t0=fr[0]['t'];T=fr[-1]['t']
  touches=[e for e in ev if e['type'] in('kick','contact')]
  def poss_at(t):
    r=[e for e in ev if e['type']=='restart_placement' and e['t']<=t];c=[e for e in touches if e['t']<=t and (e['type']=='kick' or e.get('control'))]
    if r and (not c or r[-1]['t']>=c[-1]['t']):return 'restart:%s:%s'%(r[-1].get('kind'),r[-1].get('team'))
    return ('%s(%s)'%(c[-1]['team'],c[-1]['player'])) if c else 'none'
  close=0
  for f in fr:
    P_=[p for p in f['p'] if p['id'][1:]!='00']
    for i in range(len(P_)):
      for j in range(i+1,len(P_)):
        a,b=P_[i],P_[j]
        if a['id'][0]==b['id'][0] and math.hypot(a['x']-b['x'],a['y']-b['y'])<0.9: close+=1
  ctrl=[e for e in touches if e['type']=='kick' or e.get('control')]
  return {'firstControl':(ctrl[0]['t'],ctrl[0]['player']) if ctrl else None,'poss3':poss_at(t0+60),'poss6':poss_at(t0+120),'shots':len([e for e in ev if e['type']=='kick' and e.get('kind')=='shoot']),'goals':len([e for e in ev if e['type']=='goal']),'mateCloseTicks':close,'frames':json.dumps(P['frames'])}
for line in open(sys.argv[3]):
  c,t=line.split()
  b=summ(load(f'{sys.argv[1]}/{c}_base.json'));k=summ(load(f'{sys.argv[1]}/{c}_k20.json'));l=summ(load(f'{sys.argv[2]}/{c}_l21.json'))
  ident=lambda x:'=base' if x['frames']==b['frames'] else ('=k20' if x is l and x['frames']==k['frames'] else 'diverged')
  row=lambda x:f"{x['poss3']}|{x['poss6']}|sh{x['shots']}|g{x['goals']}|close{x['mateCloseTicks']}"
  print(f"| {c} | {row(b)} | {row(k)} ({ident(k)}) | {row(l)} ({ident(l)}) |")
