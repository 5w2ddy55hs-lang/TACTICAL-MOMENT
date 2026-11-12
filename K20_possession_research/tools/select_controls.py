# Deterministic control selection per PREREGISTERED_CONTROLS.md (truth from recorded std_off_771 run).
import json,sys,gzip,zlib,math
R=sys.argv[1]
meta=json.load(open(R+'/meta.json'));ev=[json.loads(l) for l in open(R+'/events.jsonl')]
pos=memoryview(zlib.decompress(open(R+'/pos.i16.gz','rb').read(),31)).cast('h');W=meta['posWidth'];S=meta['posScale'];ids=meta['ids']
X=lambda i,j:pos[i*W+2*j]/S;Y=lambda i,j:pos[i*W+2*j+1]/S;BX=lambda i:pos[i*W+44]/S;BY=lambda i:pos[i*W+45]/S
acts=[e for e in ev if e.get('type') in('kick','contact')]
out={}
# OWN
own=[]
for i,a in enumerate(acts):
  if a['tick']<6000:continue
  if not(a['type']=='contact' and a.get('control')):continue
  later=[b for b in acts if a['tick']<b['tick']<=a['tick']+40 and b['player']==a['player'] and b['type']=='kick' and b.get('kind') in('dribble','pass')]
  others=[b for b in acts if a['tick']<b['tick']<=a['tick']+40 and b['player']!=a['player']]
  if len(later)>=2 and not others and (not own or a['tick']-own[-1]>200): own.append(a['tick'])
  if len(own)>=3:break
out['OWN']=[[t-10,a] for t,a in zip(own,['own control'])] if False else [[t-10,'control at %d'%t] for t in own]
# CON
con=[]
for t in range(6000,meta['recordedTicks']-40):
  if len(con)>=3:break
  if con and t-con[-1]<200:continue
  b=(BX(t),BY(t));near={'A':0,'B':0}
  for j,i_ in enumerate(ids):
    if i_.endswith('00'):continue
    if math.hypot(X(t,j)-b[0],Y(t,j)-b[1])<2.1: near[i_[0]]+=1
  if near['A'] and near['B'] and any(t<a['tick']<=t+20 for a in acts): con.append(t)
out['CON']=[[t-5,'both within 2.1 at %d'%t] for t in con]
# LOOSE
loose=[]
for a in acts:
  if a['tick']<6000 or a['type']!='contact' or a.get('control'):continue
  if any(a['tick']<b['tick']<=a['tick']+20 for b in acts):continue
  if loose and a['tick']-loose[-1]<200:continue
  loose.append(a['tick'])
  if len(loose)>=3:break
out['LOOSE']=[[t,'nocontrol contact %d'%t] for t in loose]
# JP from audit analysis
an=json.load(open(R+'/analysis.json'))
jp=[e for e in an['jointPress'] if e['start']>=6000 and e['ownWin3s'] is not None][:3]
out['JP']=[[e['start'],'joint press %s win %d'%(e['players'],e['ownWin3s'])] for e in jp]
# FREE: >=2 s since last touch, two same-team players within 2.1 m
free=[];li=0;last=None
for t in range(6000,meta['recordedTicks']):
  while li<len(acts) and acts[li]['tick']<=t: last=acts[li]['tick'];li+=1
  if last is None or t-last<40:continue
  if free and t-free[-1]<200:continue
  b=(BX(t),BY(t));c={'A':0,'B':0}
  for j,i_ in enumerate(ids):
    if math.hypot(X(t,j)-b[0],Y(t,j)-b[1])<2.1: c[i_[0]]+=1
  if max(c.values())>=2: free.append(t)
  if len(free)>=3:break
out['FREE']=[[t-20,'free ball, two mates near at %d'%t] for t in free]
print(json.dumps(out))
