// Q28: which EXISTING processing would address generic-exhausted receive decisions, evaluated as pure functions
// on the same saved DTOs (read-only; not a run; states would diverge in a real run).
// Usage: node existing_cover.mjs <I17 core dir> <V2 reception.mjs> <fallback input.json.gz> <audit_fb.json> <out.json>
import fs from 'node:fs';import zlib from 'node:zlib';import path from 'node:path';import {pathToFileURL} from 'node:url';
const [core,v2path,inputPath,auditPath,outPath]=process.argv.slice(2);
const {chooseZonal}=await import(pathToFileURL(path.join(core,'zonal_defence.mjs')));
const {receptionPlan:planV2}=await import(pathToFileURL(v2path));
const W=JSON.parse(zlib.gunzipSync(fs.readFileSync(inputPath))),A=JSON.parse(fs.readFileSync(auditPath));
const obs=new Map();for(const w of W)for(const r of w.rows)if(r.channel==='decision'&&r.decision.kind==='receive')obs.set(w.seed+':'+r.tick+':'+r.player,r.observation);
const res=[],c={};
for(const r of A.rows){const o=obs.get(r.seed+':'+r.tick+':'+r.player);let v2=null,z=null,err=null;
 try{v2=planV2(o);}catch(e){err='v2:'+e.message;}
 try{const zd=chooseZonal(o);z={kind:zd.kind,reason:zd.reason};}catch(e){err=(err?err+';':'')+'zonal:'+e.message;}
 const k=r.status+'|v2:'+(v2?'plan':'null')+'|zonal:'+(z?z.reason:'err');c[k]=(c[k]||0)+1;
 res.push({seed:r.seed,tick:r.tick,player:r.player,status:r.status,v2:v2?{t:v2.eta,miss:v2.estimatedMissM,rel:v2.estimatedRelativeSpeed,target:v2.target}:null,zonal:z,err});}
fs.writeFileSync(outPath,JSON.stringify(res));
const byStatus={};for(const r of res){const s=byStatus[r.status]??={n:0,v2plan:0,zonalReasons:{}};s.n++;if(r.v2)s.v2plan++;const zr=r.zonal?.reason??'err';s.zonalReasons[zr]=(s.zonalReasons[zr]||0)+1;}
console.log(JSON.stringify(byStatus,null,1));console.log('errors',res.filter(r=>r.err).length,res.find(r=>r.err)?.err);
