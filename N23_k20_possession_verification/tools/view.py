import sys,re
f,players,upto=sys.argv[1],sys.argv[2].split(','),int(sys.argv[3])
B={};K={}
for l in open(f):
  m=re.match(r'(\w+) t\+(\d+) (\S+) (\S+)',l)
  lbl,t,who=m.group(1),int(m.group(2)),m.group(3)
  if t>upto:continue
  if who!='EVENT' and who not in players:continue
  key=(t,who if who!='EVENT' else 'EV'+l.split()[3]+l.split()[4])
  short=re.sub(r' \| truth','  T',l.strip().split(' ',2)[2]).replace('seen:','').replace('velKnown','vK').replace('witnessed','W')
  (B if lbl=='base' else K).setdefault(t,[]).append(short)
for t in sorted(set(B)|set(K)):
  b=B.get(t,[]);k=K.get(t,[])
  if b==k:print(f'+{t:3d} SAME ',' || '.join(b)[:230]);continue
  for x in b:print(f'+{t:3d} BASE ',x[:230])
  for x in k:print(f'+{t:3d} K20  ',x[:230])
