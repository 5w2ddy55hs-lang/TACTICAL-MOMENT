// Re-record one condition of the 3-version set with full frames (view per tick) and all sink rows, using the SAME
// procedure as the set's run.mjs (base_off.restore(input).exportState() -> arm.fromFixture(native,sink)).
// If an expected reference file is given, every frame hash, the row count, the all-rows SHA and the terminal native SHA
// are checked so the recording is provably the reference run. Nothing is relabelled; engines are used unchanged.
// usage: node record3.mjs <setDir> <arm base|v2|flight> <inputSave> <ticks> <out.json.gz> [expected.json]
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import crypto from 'node:crypto';import {pathToFileURL} from 'node:url';
const [SET,arm,inputF,ticksS,outF,expF]=process.argv.slice(2);const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const engines=JSON.parse(fs.readFileSync(path.join(SET,'engines.json')));
const B=(await import(pathToFileURL(path.join(SET,'research',engines.base)))).MatchEngine,E=(await import(pathToFileURL(path.join(SET,'research',engines[arm])))).MatchEngine;
const input=fs.readFileSync(inputF,'utf8');const native=B.restore(input).exportState();let direct;try{E.restore(input);direct='accepted';}catch(e){direct=e.message;}
const rows=[],frames=[];const h=crypto.createHash('sha256');let fixture='accepted',e;
try{e=E.fromFixture(native,r=>{rows.push(structuredClone(r));h.update(JSON.stringify(r)+'\n');});}catch(x){fixture='REJECTED:'+x.message;}
const res={arm,input:path.basename(inputF),inputSha256:sha(input),directRestore:direct,fixture,node:process.version};
if(e){res.nativeExact=JSON.stringify(e.exportState())===JSON.stringify(native);const s0=e.save();res.ownSaveRestore=E.restore(s0).save()===s0;
 const exp=expF?JSON.parse(fs.readFileSync(expF)):null;let frameMismatch=null;
 for(let i=0;i<+ticksS&&!e.finished;i++){const v=e.view();frames.push(v);if(exp&&frameMismatch===null&&sha(JSON.stringify(v))!==exp.frameHashes[i])frameMismatch=i;e.step();}
 res.endTick=e.tick;res.rows=rows.length;
 if(exp){res.reference={frameHashesAll:frameMismatch===null,firstFrameMismatch:frameMismatch,rowCount:rows.length===exp.rowCount,rowsSHA:h.digest('hex')===exp.rowsSHA,endNativeSHA:sha(JSON.stringify(e.exportState()))===exp.endNativeSHA};}
 fs.writeFileSync(outF,zlib.gzipSync(JSON.stringify({name:arm,frames,rows})));}
console.log(JSON.stringify(res));
