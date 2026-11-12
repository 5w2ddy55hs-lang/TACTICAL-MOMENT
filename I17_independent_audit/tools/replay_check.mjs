// Restore a recorded save via research_guard.restore, step to a later tick, compare against recorded positions.
// Usage: node replay_check.mjs <I17dir> <runDir> <saveFile> <stepTicks>
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [I17,runDir,saveFile,stepS]=process.argv.slice(2);
const {register,restore}=await import(path.join(I17,'research_guard.mjs'));
const meta=JSON.parse(fs.readFileSync(path.join(runDir,'meta.json')));
await register(meta.variant);
const e=restore(fs.readFileSync(path.join(runDir,saveFile),'utf8'),meta.variant,null);
const b=zlib.gunzipSync(fs.readFileSync(path.join(runDir,'pos.i16.gz')));const pos=new Int16Array(b.buffer,b.byteOffset,b.byteLength/2);
const W=meta.posWidth,S=meta.posScale;let maxErr=0,checked=0;const start=e.tick;
const cmp=()=>{const p=e.physicalSnapshot(),i=e.tick;for(let j=0;j<22;j++){maxErr=Math.max(maxErr,Math.abs(Math.round(p.players[j].x*S)-pos[i*W+2*j]),Math.abs(Math.round(p.players[j].y*S)-pos[i*W+2*j+1]));}maxErr=Math.max(maxErr,Math.abs(Math.round(p.ball.x*S)-pos[i*W+44]));checked++;};
cmp();for(let k=0;k<Number(stepS);k++){e.step();cmp();}
console.log(JSON.stringify({run:path.basename(runDir),save:saveFile,startTick:start,endTick:e.tick,framesChecked:checked,maxAbsErrorUnits:maxErr,match:maxErr===0}));
