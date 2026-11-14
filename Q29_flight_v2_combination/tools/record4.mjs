// Record one arm from a common start state. The start state is the exact native state of a SOURCE arm's run at <startTick>
// (source run started like the set's run.mjs: base_off.restore(input).exportState() -> source.fromFixture). The same native
// state is handed to <arm>.fromFixture. Nothing is relabelled; a rejection is reported and nothing is recorded.
// Checks: native exact after fromFixture, own save->restore, and 20 extra ticks of save equality after restore.
// usage: node record4.mjs <setDir> <inputSave> <sourceArm> <startTick> <endTick> <arm> <out.json.gz>
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import crypto from 'node:crypto';import {pathToFileURL} from 'node:url';
const [SET,inputF,src,startS,endS,arm,outF]=process.argv.slice(2);const engines=JSON.parse(fs.readFileSync(path.join(SET,'engines.json')));
const load=async a=>(await import(pathToFileURL(path.join(SET,'research',engines[a])))).MatchEngine;
const B=await load('base'),Src=await load(src),E=await load(arm);const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const input=fs.readFileSync(inputF,'utf8');const s=Src.fromFixture(B.restore(input).exportState());while(s.tick<+startS)s.step();const native=s.exportState();
const res={arm,input:path.basename(inputF),inputSha256:sha(input),sourceArm:src,startTick:+startS,startNativeSha256:sha(JSON.stringify(native)),node:process.version};
let direct;try{E.restore(input);direct='accepted';}catch(x){direct=x.message;}res.directRestoreOfInput=direct;
const rows=[],frames=[];const h=crypto.createHash('sha256');let e,closed=false;
try{e=E.fromFixture(native,r=>{if(closed)return;rows.push(structuredClone(r));h.update(JSON.stringify(r)+'\n');});res.fixture='accepted';}catch(x){res.fixture='REJECTED:'+x.message;console.log(JSON.stringify(res));process.exit(0);}
res.nativeExact=JSON.stringify(e.exportState())===JSON.stringify(native);const s0=e.save();res.ownSaveRestore=E.restore(s0).save()===s0;res.saveSchema=JSON.parse(s0).schema;
while(e.tick<+endS&&!e.finished){frames.push(e.view());e.step();}
res.endTick=e.tick;res.rows=rows.length;res.rowsSHA=h.digest('hex');closed=true;res.endNativeSHA=sha(JSON.stringify(e.exportState()));
const r=E.restore(e.save());let ok=true;for(let i=0;i<20;i++){e.step();r.step();if(e.save()!==r.save())ok=false;}res.restore20=ok;
fs.writeFileSync(outF,zlib.gzipSync(JSON.stringify({name:arm,start:+startS,source:src,frames,rows})));
console.log(JSON.stringify(res));
