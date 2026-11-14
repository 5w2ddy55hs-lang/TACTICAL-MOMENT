// Is the recorded flight-time candidate aim equal to I17's own PAI1 solver (pass_arrival_aim.mjs, pure function,
// already shipped in I17 standard but wired only into the FLAC3 release path) on the passer's identical observation?
// Reads the recorded comparison (no engine run). usage: node pai1_check.mjs <I17> <comparison.json.gz>
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [I17,CMP]=process.argv.slice(2);
const {solvePassArrivalAim}=await import(path.join(I17,'source/integration_i8_standard/core/pass_arrival_aim.mjs'));const {DT}=await import(path.join(I17,'source/integration_i8_standard/core/math.mjs'));
const arms=Object.fromEntries(JSON.parse(zlib.gunzipSync(fs.readFileSync(CMP))).map(c=>[c.name,c]));
const pick=(arm,t,p)=>arms[arm].rows.find(r=>r.channel==='decision'&&r.tick===t&&r.player===p);
for(const [arm,t,p] of [['base',42188,'A05'],['flight_candidate',42188,'A05']]){
 const r=pick(arm,t,p),o=r.observation,bi=r.decision.ballActionIntent,q=o.people.find(x=>x.id===bi.targetId),b=o.ball;
 const f=solvePassArrivalAim({decisionTick:o.tick,plannedApplyTick:bi.applyTick,DT,originObservation:{x:b.x,y:b.y,z:b.z,seenTick:b.seenTick},receiverObservation:{id:q.id,x:q.x,y:q.y,vx:q.vx,vy:q.vy,seenTick:q.seenTick}});
 const legacy={x:q.x+Math.max(-8,Math.min(8,q.vx))*.35,y:q.y+Math.max(-8,Math.min(8,q.vy))*.35};
 console.log(JSON.stringify({arm,tick:t,passer:p,receiver:q.id,receiverSeen:{x:q.x,y:q.y,vx:q.vx,vy:q.vy,ageTicks:o.tick-q.seenTick},recordedAim:bi.target,legacy035:legacy,pai1:{status:f.status,reason:f.reason,aim:f.aim,flightSeconds:f.nominalFlightSeconds,launchSpeed:f.nativeNominalLaunchSpeed},
  recordedMinusPai1:f.aim?Math.hypot(bi.target.x-f.aim.x,bi.target.y-f.aim.y):null,recordedMinusLegacy:Math.hypot(bi.target.x-legacy.x,bi.target.y-legacy.y)}));}
