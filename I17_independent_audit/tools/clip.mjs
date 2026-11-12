// Extract 2D clips from recorded runs. Usage: node clip.mjs spec.json out.json
// spec: [{id,title,run,from,to,note,focus:[ids]}]  ticks are recorded indices (== engine tick)
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [specF,outF]=process.argv.slice(2);const spec=JSON.parse(fs.readFileSync(specF));const RUNS=path.dirname(specF)+'/../runs';
const cache=new Map();
function load(run){if(cache.has(run))return cache.get(run);const dir=path.join(RUNS,run);const meta=JSON.parse(fs.readFileSync(path.join(dir,'meta.json')));
 const rd=(n,T)=>{const b=zlib.gunzipSync(fs.readFileSync(path.join(dir,n)));return new T(b.buffer,b.byteOffset,b.byteLength/T.BYTES_PER_ELEMENT);};
 const evs=fs.readFileSync(path.join(dir,'events.jsonl'),'utf8').split('\n').filter(Boolean).map(l=>JSON.parse(l)).filter(e=>e.channel==='event'&&e.type!=='contact'||e.type==='contact');
 const o={meta,pos:rd('pos.i16.gz',Int16Array),dec:rd('dec.u8.gz',Uint8Array),tgt:rd('tgt.i16.gz',Int16Array),phase:rd('phase.u8.gz',Uint8Array),evs};cache.set(run,o);return o;}
const out=[];
for(const c of spec){const r=load(c.run),m=r.meta,W=m.posWidth,N=22;const from=Math.max(0,c.from),to=Math.min(m.recordedTicks-1,c.to);
 const frames=[];for(let i=from;i<=to;i++){const f=[];for(let j=0;j<W;j++)f.push(r.pos[i*W+j]);const d=[];for(let j=0;j<N;j++)d.push(r.dec[i*N+j]);const tg=[];for(let j=0;j<N;j++){tg.push(r.tgt[(i*N+j)*2],r.tgt[(i*N+j)*2+1]);}frames.push({p:f,d,t:tg,ph:r.phase[i]});}
 // events: kicks, merged contacts (first row per player per tick), restarts, goals
 const seen=new Set();const ev=[];for(const e of r.evs){if(e.tick<from||e.tick>to)continue;if(e.type==='contact'){const k=e.player+':'+e.tick;if(seen.has(k))continue;seen.add(k);ev.push({t:e.tick,s:`${e.player} touch${e.control?' ctrl':''}${e.miscontrol?' MISCTRL':''}${e.interception?' intercept':''} rel=${(e.relativeSpeed||0).toFixed(1)}`});}
  else if(e.type==='kick')ev.push({t:e.tick,s:`${e.player} KICK ${e.kind}${e.targetId?'→'+e.targetId:''}`});
  else if(['restart_placement','restart_taken','goal','throw_in_play','drop_in_play'].includes(e.type))ev.push({t:e.tick,s:`${e.type} ${e.kind??''} ${e.team??''} ${e.taker??e.player??''}`.trim()});}
 out.push({id:c.id,title:c.title,note:c.note??'',run:c.run,variant:m.variant,profile:m.profile,seed:m.seed,zonal:m.activeConfig.zonalDefence,from,to,focus:c.focus??[],scale:m.posScale,ids:m.ids,roles:m.roles,dict:m.decisionDict.map(s=>s.split('|')[0]),reasons:m.decisionDict,phaseCodes:m.phaseCodes,frames,events:ev,pair:c.pair??null});}
fs.writeFileSync(outF,JSON.stringify(out));console.log('clips',out.length,'bytes',fs.statSync(outF).size);
