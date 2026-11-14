# OFF-identity at the recorded checkpoints: the P25 natural run vs the ORIGINAL ck_research run of the same seed.
# Both recorders saved every 6000 ticks. A save's `native` holds the whole state incl. per-player RNG streams and the
# event log/digest; `checksum` covers {mode,native}. Before the original's stop tick they must be identical
# (only the identity labels schema/engine/buildSha256 differ). Also compares the event stream before the stop tick.
# usage: python3 -I checkpoint_identity.py <origRunDir> <p25RunDir> <out.json>
import json,sys,os,glob,hashlib
A,B,outF=sys.argv[1:4]
ma=json.load(open(A+'/meta.json'));stop=ma['crash']['tickBeforeStep'] if ma.get('crash') else None
rows=[]
for f in sorted(glob.glob(A+'/save_*.json'),key=lambda x:int(x.split('_')[-1][:-5])):
  t=int(f.split('_')[-1][:-5]);g=B+'/'+os.path.basename(f)
  if not os.path.exists(g):rows.append({'tick':t,'p25Save':'missing'});continue
  a=json.loads(json.load(open(f))['inner']);b=json.load(open(g))
  rows.append({'tick':t,'nativeIdentical':a['native']==b['native'],'checksumIdentical':a['checksum']==b['checksum'],'modeIdentical':a['mode']==b['mode'],
    'labelsDiffer':[k for k in('schema','engine','buildSha256') if a[k]!=b[k]],'nativeSha256':hashlib.sha256(json.dumps(a['native'],sort_keys=True).encode() if not isinstance(a['native'],str) else a['native'].encode()).hexdigest()})
def events(d,upto):
  out=[]
  for l in open(d+'/events.jsonl'):
    if '"tick":' not in l:continue
    x=json.loads(l)
    if upto is not None and x['tick']>=upto:break
    out.append(l)
  return out
ea,eb=events(A,stop),events(B,stop)
res={'seed':ma['seed'],'originalStopTick':stop,'originalFinalTick':ma['finalTick'],'checkpoints':rows,'allCheckpointsIdentical':all(r.get('nativeIdentical') and r.get('checksumIdentical') for r in rows),
 'eventLinesBeforeStop':{'original':len(ea),'p25':len(eb),'identical':ea==eb}}
if stop is None:
  fa,fb=A+'/final_save.json',B+'/final_save.json'
  if os.path.exists(fa) and os.path.exists(fb):
    a=json.loads(json.load(open(fa))['inner']);b=json.load(open(fb));res['finalSaveNativeIdentical']=a['native']==b['native']
  mb=json.load(open(B+'/meta.json'));res['finalScore']={'original':ma['score'],'p25':mb['score']};res['eventDigest']={'original':ma['eventDigest'],'p25':mb['eventDigest']}
json.dump(res,open(outF,'w'),indent=1)
print(json.dumps({k:v for k,v in res.items() if k!='checkpoints'}),'checkpoints',len(rows),[r['tick'] for r in rows if not (r.get('nativeIdentical') and r.get('checksumIdentical'))])
