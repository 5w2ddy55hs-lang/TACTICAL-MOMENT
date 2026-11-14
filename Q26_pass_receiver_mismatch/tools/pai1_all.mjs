// For every decision row where the recorded flight-time candidate's pass target differs from the baseline on the
// IDENTICAL observation, compare the candidate target with I17's PAI1 solver and the baseline with the fixed 0.35 s lead.
// Covers pre-planned (ballActionIntent) passes and ordinary pass candidates. usage: node pai1_all.mjs <I17> <comparison.json.gz>
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [I17,CMP]=process.argv.slice(2);
const {solvePassArrivalAim}=await import(path.join(I17,'source/integration_i8_standard/core/pass_arrival_aim.mjs'));const {DT}=await import(path.join(I17,'source/integration_i8_standard/core/math.mjs'));
const A=Object.fromEntries(JSON.parse(zlib.gunzipSync(fs.readFileSync(CMP))).map(c=>[c.name,c]));
const B=A.base.rows.filter(r=>r.channel==='decision'&&r.tick<=42190),C=A.flight_candidate.rows.filter(r=>r.channel==='decision'&&r.tick<=42190);
const H=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);const rows=[];
for(let i=0;i<B.length;i++){const rb=B[i],rc=C[i];if(JSON.stringify(rb)===JSON.stringify(rc))continue;const o=rb.observation;
 const pairs=[];const bb=rb.decision.ballActionIntent,cb=rc.decision.ballActionIntent;if(bb&&cb&&bb.kind==='pass')pairs.push(['ballActionIntent',bb,cb,bb.applyTick]);
 (rb.decision.candidates||[]).forEach((x,j)=>{const y=(rc.decision.candidates||[])[j];if(x.kind==='pass'&&y&&x.target&&y.target)pairs.push(['ordinaryCandidate',x,y,o.tick+2]);});
 for(const [src,x,y,apply] of pairs){const q=o.people.find(p=>p.id===x.targetId),b=o.ball;if(!q||!b)continue;
  const f=solvePassArrivalAim({decisionTick:o.tick,plannedApplyTick:apply,DT,originObservation:{x:b.x,y:b.y,z:b.z,seenTick:b.seenTick},receiverObservation:{id:q.id,x:q.x,y:q.y,vx:q.vx,vy:q.vy,seenTick:q.seenTick}});
  const legacy={x:q.x+Math.max(-8,Math.min(8,q.vx))*.35,y:q.y+Math.max(-8,Math.min(8,q.vy))*.35};
  rows.push({tick:rb.tick,player:rb.player,src,receiver:q.id,baseMinusLegacy:+H(x.target,legacy).toFixed(3),candMinusPai1:f.aim?+H(y.target,f.aim).toFixed(3):f.status+':'+f.reason,candMinusBase:+H(y.target,x.target).toFixed(2),pai1Flight:f.nominalFlightSeconds??null});}}
fs.writeFileSync(process.argv[4]||'/dev/stdout',JSON.stringify(rows,null,1));
for(const r of rows)console.error(JSON.stringify(r));
