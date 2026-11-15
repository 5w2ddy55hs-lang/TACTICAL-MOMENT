// Q29F: long natural run of ONE arm from an existing save (base_off.restore -> arm.fromFixture), keeping only decision and
// event rows plus per-tick ball/player positions, to search for naturally occurring situations. No edits of any state.
// usage: node record_scan.mjs <setDir> <inputSave> <arm> <ticks> <out.json.gz>
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,inputF,arm,ticksS,outF]=process.argv.slice(2);const engines=JSON.parse(fs.readFileSync(path.join(SET,'engines.json')));
const load=async a=>(await import(pathToFileURL(path.join(SET,'research',engines[a])))).MatchEngine;const Bm=await load('base'),E=await load(arm);
const native=Bm.restore(fs.readFileSync(inputF,'utf8')).exportState();const rows=[];const e=E.fromFixture(native,r=>{if(r.channel==='decision'||r.channel==='event')rows.push(structuredClone(r));});
const frames=[];const t0=e.tick;for(let i=0;i<+ticksS&&!e.finished;i++){const v=e.view();frames.push({tick:v.tick,phase:v.phase,ball:{x:v.ball.x,y:v.ball.y,z:v.ball.z,vx:v.ball.vx,vy:v.ball.vy},players:v.players.map(p=>({id:p.id,team:p.team,x:p.x,y:p.y,heading:p.heading,action:p.action}))});e.step();}
fs.writeFileSync(outF,zlib.gzipSync(JSON.stringify({name:arm,input:path.basename(inputF),start:t0,end:e.tick,frames,rows})));console.log(JSON.stringify({arm,input:path.basename(inputF),start:t0,end:e.tick,rows:rows.length,finished:e.finished}));
