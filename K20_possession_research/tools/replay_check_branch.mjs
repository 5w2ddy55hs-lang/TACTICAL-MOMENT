// Restore an I18 branch save and compare stepped positions with the recorded run.
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [BR,runDir,saveFile,stepS]=process.argv.slice(2);const {MatchEngine}=await import(path.join(BR,'engine.mjs'));
const meta=JSON.parse(fs.readFileSync(path.join(runDir,'meta.json')));const b=zlib.gunzipSync(fs.readFileSync(path.join(runDir,'pos.i16.gz')));const pos=new Int16Array(b.buffer,b.byteOffset,b.byteLength/2);
const e=MatchEngine.restore(fs.readFileSync(path.join(runDir,saveFile),'utf8'));const W=meta.posWidth,S=meta.posScale;let mx=0;const st=e.tick;
const cmp=()=>{const p=e.physicalSnapshot(),i=e.tick;for(let j=0;j<22;j++)mx=Math.max(mx,Math.abs(Math.round(p.players[j].x*S)-pos[i*W+2*j]),Math.abs(Math.round(p.players[j].y*S)-pos[i*W+2*j+1]));mx=Math.max(mx,Math.abs(Math.round(p.ball.x*S)-pos[i*W+44]));};
cmp();for(let k=0;k<+stepS;k++){e.step();cmp();}console.log(JSON.stringify({run:path.basename(runDir),save:saveFile,from:st,to:e.tick,maxAbsErrorUnits:mx,match:mx===0}));
