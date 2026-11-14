// Same-state paired recording from a LATER common tick: run the UNCHANGED baseline from the input save up to <startTick>,
// take its exact native state, and hand that one state to the chosen arm's fromFixture (base or flight). Both arms
// therefore start from the identical state; this is NOT the original start tick and is labelled as shifted.
// usage: node record_from.mjs <setDir> <arm> <inputSave> <startTick> <ticks> <out.json.gz>
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import crypto from 'node:crypto';import {pathToFileURL} from 'node:url';
const [SET,arm,inputF,startS,ticksS,outF]=process.argv.slice(2);const engines=JSON.parse(fs.readFileSync(path.join(SET,'engines.json')));
const B=(await import(pathToFileURL(path.join(SET,'research',engines.base)))).MatchEngine,E=(await import(pathToFileURL(path.join(SET,'research',engines[arm])))).MatchEngine;
const b=B.restore(fs.readFileSync(inputF,'utf8'));while(b.tick<+startS)b.step();const native=b.exportState();
const nativeSha=crypto.createHash('sha256').update(JSON.stringify(native)).digest('hex');
const rows=[],frames=[];const e=E.fromFixture(native,r=>rows.push(structuredClone(r)));const s0=e.save();
for(let i=0;i<+ticksS&&!e.finished;i++){frames.push(e.view());e.step();}
const r=E.restore(e.save());let ok=true;for(let i=0;i<20;i++){e.step();r.step();if(e.save()!==r.save())ok=false;}
fs.writeFileSync(outF,zlib.gzipSync(JSON.stringify({name:arm,frames,rows})));
console.log(JSON.stringify({arm,input:path.basename(inputF),shiftedStartTick:+startS,startNativeSha256:nativeSha,nativeExact:JSON.stringify(E.fromFixture(native).exportState())===JSON.stringify(native),ownSaveRestore:E.restore(s0).save()===s0,restore20:ok,endTick:e.tick-20,rows:rows.length}));
