// Save-compatibility check (read only): which engines accept which input saves, without relabelling anything.
// Engines: I17 standard (original extraction, direct class restore and via the I9 guard), the suite's base_off copy.
// For accepted pairs, the exportState() of I17 standard and base_off after restore must be identical.
// usage: node save_compat.mjs <I17> <suiteDir> <cmpDir> <out.json>
import fs from 'node:fs';import path from 'node:path';import {createHash} from 'node:crypto';
const [I17,SU,CM,outF]=process.argv.slice(2);
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const {MatchEngine:Off}=await import(path.join(SU,'research/l21_natural/recovered/l21_receive_compare/branches/base_off/engine.mjs'));
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const sha=t=>createHash('sha256').update(t).digest('hex');
const files=[...JSON.parse(fs.readFileSync(path.join(SU,'cases.json'))).cases.map(c=>path.join(SU,c.input)),...['base_start.json','baseline_start.json','receive_v2_start.json','flight_baseline_start.json','flight_candidate_start.json'].map(f=>path.join(CM,f))];
const out=[];
for(const f of files){const t=fs.readFileSync(f,'utf8');const x=JSON.parse(t);const row={file:path.relative(path.dirname(SU),f),sha256:sha(t),schema:x.schema,engine:x.engine,buildSha256:x.buildSha256};
 const tryR=(fn)=>{try{return {ok:true,e:fn()};}catch(e){return {ok:false,msg:String(e.message).slice(0,70)};}};
 const a=tryR(()=>Std.restore(t)),b=tryR(()=>Off.restore(t)),c=tryR(()=>g.restore(t,'standard'));
 row.i17StandardDirect=a.ok?'ACCEPTED':'REJECTED:'+a.msg;row.suiteBaseOff=b.ok?'ACCEPTED':'REJECTED:'+b.msg;row.i17ViaI9Guard=c.ok?'ACCEPTED':'REJECTED:'+c.msg;
 if(a.ok&&b.ok)row.exportStateIdentical=JSON.stringify(a.e.exportState())===JSON.stringify(b.e.exportState()),row.saveRoundTripIdentical=a.e.save()===b.e.save();
 out.push(row);console.log(JSON.stringify(row));}
fs.writeFileSync(outF,JSON.stringify(out,null,1));
