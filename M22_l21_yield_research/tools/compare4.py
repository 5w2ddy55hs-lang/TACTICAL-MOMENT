# 4-way fixed-scene comparison base/K20/L21/M22 from poss_probe outputs
import json,sys,math
K,L,Mdir,cases=sys.argv[1:5]
def summ(p):
  P=json.load(open(p));fr=sorted(P['frames'],key=lambda f:f['t']);ev=P['events'];t0=fr[0]['t']
  touches=[e for e in ev if e['type'] in('kick','contact')]
  def poss(t):
    r=[e for e in ev if e['type']=='restart_placement' and e['t']<=t];c=[e for e in touches if e['t']<=t and (e['type']=='kick' or e.get('control'))]
    if r and (not c or r[-1]['t']>=c[-1]['t']):return 'restart:%s:%s'%(r[-1].get('kind'),r[-1].get('team'))
    return ('%s(%s)'%(c[-1]['team'],c[-1]['player'])) if c else 'none'
  close=sum(1 for f in fr for i,a in enumerate(f['p']) for b in f['p'][i+1:] if a['id'][1:]!='00' and b['id'][1:]!='00' and a['id'][0]==b['id'][0] and math.hypot(a['x']-b['x'],a['y']-b['y'])<0.9)
  return {'poss3':poss(t0+60),'poss6':poss(t0+120),'shots':sum(1 for e in ev if e['type']=='kick' and e.get('kind')=='shoot'),'goals':sum(1 for e in ev if e['type']=='goal'),'close':close,'fr':json.dumps(P['frames'])}
for line in open(cases):
  c,t=line.split();b=summ(f'{K}/{c}_base.json');k=summ(f'{K}/{c}_k20.json');l=summ(f'{L}/{c}_l21.json');m=summ(f'{Mdir}/{c}_m22.json')
  same=lambda x:'=L21' if x['fr']==l['fr'] else ('=base' if x['fr']==b['fr'] else ('=K20' if x['fr']==k['fr'] else 'diverged'))
  r=lambda x:f"{x['poss3']}|{x['poss6']}|sh{x['shots']}|g{x['goals']}|close{x['close']}"
  print(f"| {c} | {r(b)} | {r(k)} | {r(l)} | {r(m)} ({same(m)}) |")
