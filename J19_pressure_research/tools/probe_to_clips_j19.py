# Convert paired probe files (base / i18 from the same state) into viewer clips (same format as audit viewer).
# usage: python3 -I probe_to_clips.py spec.json out.json ; spec: [{id,title,note,base,i18,focus,engineInfo}]
import json,sys
spec=json.load(open(sys.argv[1]));out=[]
KINDS=['none','press','intercept','receive','save','cover','support','advance_support','cover_exchange','restart_position','throw_position','scan','dribble','pass','gk_recover','gk_support','shoot','restart_kick','throw_in','other','support_i18','yield_j19','engage_j19']
def clip(cid,title,note,P,label,variant,focus,pair,c={}):
  fr=P['frames'];ids=[p['id'] for p in fr[0]['p']]
  latest={};tg={};decs=sorted(P['decisions'],key=lambda d:d['t']);di=0;frames=[]
  for f in fr:
    while di<len(decs) and decs[di]['t']<=f['t']:
      d=decs[di];k=d['kind'];k='yield_j19' if 'J19_trailing_yield' in d['reason'] else ('engage_j19' if 'J19_goalside_engage' in d['reason'] else (k if k in KINDS else 'other'));latest[d['p']]=KINDS.index(k);tg[d['p']]=d['target'] or [0,0];di+=1
    pos=[];[pos.extend([round(p['x']*50),round(p['y']*50)]) for p in f['p']];pos.extend([round(f['ball'][0]*50),round(f['ball'][1]*50),round(f['ball'][2]*50)])
    t=[];[t.extend([round(tg.get(i,[0,0])[0]*50),round(tg.get(i,[0,0])[1]*50)]) for i in ids]
    frames.append({'p':pos,'d':[latest.get(i,0) for i in ids],'t':t,'ph':0 if f['phase']=='play' else 1})
  ev=[]
  seen=set()
  for e in P['events']:
    if e['type']=='contact':
      key=(e['player'],e['t'])
      if key in seen: continue
      seen.add(key);ev.append({'t':e['t'],'s':f"{e['player']} touch{' ctrl' if e.get('control') else ''}{' MISCTRL' if e.get('miscontrol') else ''} rel={(e.get('rel') or 0):.1f}"})
    elif e['type']=='kick': ev.append({'t':e['t'],'s':f"{e['player']} KICK {e.get('kind')}{'→'+e['targetId'] if e.get('targetId') else ''}"})
    else: ev.append({'t':e['t'],'s':f"{e['type']} {e.get('kind') or ''} {e.get('team') or ''}"})
  claims=[d for d in P['decisions'] if d['reason'].startswith('J19_')]
  if claims: ev.append({'t':claims[0]['t'],'s':f"[J19] 最初の書換え {claims[0]['p']}（区間内 {len(claims)}判断）"})
  ev.sort(key=lambda x:x['t'])
  return {'id':cid,'title':title,'note':note,'run':label,'variant':variant,'profile':'baseline','seed':c.get('seed',771),'zonal':False,'from':fr[0]['t'],'to':fr[-1]['t'],'focus':focus,'scale':50,'ids':ids,'roles':[i for i in ids],'dict':KINDS,'reasons':KINDS,'phaseCodes':['play','restart'],'frames':frames,'events':ev,'pair':pair}
for c in spec:
  A=json.load(open(c['base']));B=json.load(open(c['j19']))
  out.append(clip(c['id'],c['title']+'：I17標準',c['note'],A,'standard（I17・既定）','standard',c.get('focus',[]),c['id']+'b',c))
  out.append(clip(c['id']+'b',c['title']+'：J19候補',c['note'],B,'J19 pressure-value 候補（隔離枝）','j19_pressure_value',c.get('focus',[]),c['id'],c))
json.dump(out,open(sys.argv[2],'w'));print('clips',len(out))
