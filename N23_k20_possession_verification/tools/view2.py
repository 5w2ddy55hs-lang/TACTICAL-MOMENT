# show per tick: decisions whose kind differs between base and K20 for the focus players, all ball events, and the
# truth distance to ball for focus players every 10 ticks
import sys,re
f,upto=sys.argv[1],int(sys.argv[2])
D={'base':{},'k20':{}};E={'base':[],'k20':[]}
for l in open(f):
  m=re.match(r'(\w+) t\+(\d+) (\S+) (\S+)(.*)',l.strip());lbl,t,who,kind,rest=m.groups();t=int(t)
  if t>upto:continue
  if who=='EVENT':E[lbl].append((t,kind+rest.split(' ctrl')[0]+' ctrl'+rest.split(' ctrl')[1].split()[0][1:] if ' ctrl' in rest else kind));continue
  tm=re.search(r'T dBall=([\d.]+)|truth dBall=([\d.]+)',rest);ev=rest.split('|')[1].strip() if '|' in rest else ''
  D[lbl][(t,who)]=(kind,rest.split('|')[0].strip(),ev,tm.group(2) if tm else '')
keys=sorted(set(D['base'])|set(D['k20']))
for k in keys:
  b=D['base'].get(k);c=D['k20'].get(k)
  if b and c and b[0]==c[0]:continue
  print(f"+{k[0]:3d} {k[1]} base={b and b[0]+' '+b[1]+' d='+b[3]} | k20={c and c[0]+' '+c[1]+' d='+c[3]} | k20 evidence: {c and c[2][:120]}")
print('-- events base:',[x for x in E['base']][:8]);print('-- events k20 :',[x for x in E['k20']][:8])
