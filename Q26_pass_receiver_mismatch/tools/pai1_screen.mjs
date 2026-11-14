// Offline SCREENING (not a simulation): for every targeted pass of the unchanged baseline in the recorded windows, what
// would I17's own PAI1 arrival aim (pass_arrival_aim.mjs) have been on the passer's IDENTICAL observation, and how does
// that aim relate to things the passer did NOT know: the receiver's own current plan (its private decision target),
// the field lines, and (audit truth from the BASELINE run, i.e. opponents reacting to the baseline ball) nearby opponents.
// usage: node pai1_screen.mjs <I17> <pass_trace.json> <out.json> <label>=<file.json.gz>[:arm] ...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [I17,TRACE,outF,...specs]=process.argv.slice(2);
const {solvePassArrivalAim}=await import(path.join(I17,'source/integration_i8_standard/core/pass_arrival_aim.mjs'));const {DT}=await import(path.join(I17,'source/integration_i8_standard/core/math.mjs'));
const {nominalPassSpeed}=await import(path.join(I17,'source/integration_i8_standard/core/pass_arrival_flight.mjs'));
const trace=JSON.parse(fs.readFileSync(TRACE));const H=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);const out=[];
for(const spec of specs){const [label,rest]=spec.split('=');let [file,arm]=rest.split(':');let d=JSON.parse(zlib.gunzipSync(fs.readFileSync(file)));if(Array.isArray(d))d=d.find(c=>c.name===arm);
 const F=new Map(d.frames.map(f=>[f.tick,f]));const dec=d.rows.filter(r=>r.channel==='decision');
 for(const t of trace.filter(x=>x.window===label&&x.decision)){
  const r=dec.find(z=>z.tick===t.decision.tick&&z.player===t.passer);const o=r.observation,q=o.people.find(p=>p.id===t.receiver),b=o.ball;
  const bi=r.decision.ballActionIntent&&r.decision.ballActionIntent.kind==='pass'?r.decision.ballActionIntent:null;const apply=bi?bi.applyTick:(r.decision.applyTick??o.tick+2);
  const f=solvePassArrivalAim({decisionTick:o.tick,plannedApplyTick:apply,DT,originObservation:{x:b.x,y:b.y,z:b.z,seenTick:b.seenTick},receiverObservation:{id:q.id,x:q.x,y:q.y,vx:q.vx,vy:q.vy,seenTick:q.seenTick}});
  const base={x:t.decision.aim[0],y:t.decision.aim[1]};const row={window:label,kickTick:t.kickTick,passer:t.passer,receiver:t.receiver,outcomeBaseline:t.outcome,receiverSeenSpeed:t.passerView?.speed,
   baseline:{aim:base,launchSpeedNominal:+nominalPassSpeed(H(base,b)).toFixed(2)},pai1:{status:f.status,reason:f.reason}};
  if(f.status==='solved'){const a=f.aim,arrT=Math.round(apply+f.nominalFlightSeconds/DT);
   row.pai1={...row.pai1,aim:{x:+a.x.toFixed(2),y:+a.y.toFixed(2)},shiftFromBaseline:+H(a,base).toFixed(2),flightSeconds:+f.nominalFlightSeconds.toFixed(2),launchSpeed:+f.nativeNominalLaunchSpeed.toFixed(2),arrivalHorizontalSpeed:+f.nominalArrivalHorizontalSpeed.toFixed(2),
    distToTouchline:+Math.min(a.y,68-a.y).toFixed(2),distToByline:+Math.min(a.x,105-a.x).toFixed(2)};
   const plan=t.receiverOwnPlanAtDecision;if(plan&&plan.target){const pt={x:plan.target[0],y:plan.target[1]};const sp=Math.hypot(q.vx,q.vy),u={x:q.vx/sp,y:q.vy/sp};
    row.receiverPrivatePlan={kind:plan.kind,target:pt,pai1AimBeyondPlanAlongRun:+(((a.x-pt.x)*u.x+(a.y-pt.y)*u.y)).toFixed(2),pai1AimToPlanTarget:+H(a,pt).toFixed(2),baselineAimToPlanTarget:+H(base,pt).toFixed(2),
     receiverToPlanTargetAtDecision:plan.distToOwnTarget,secondsToReachPlanAtSeenSpeed:sp>0.05?+(plan.distToOwnTarget/sp).toFixed(2):null}}
   const fr=F.get(arrT)||F.get(Math.max(...[...F.keys()].filter(k=>k<=arrT)));
   if(fr){const opp=fr.players.filter(p=>p.team!==q.team),near=opp.map(p=>({id:p.id,d:H(p,a)})).sort((x,y)=>x.d-y.d)[0],rec=fr.players.find(p=>p.id===q.id);
    row.auditTruthAtNominalArrival={tick:fr.tick,frameIsExact:fr.tick===arrT,nearestOpponentToPai1Aim:{id:near.id,d:+near.d.toFixed(2)},receiverToPai1Aim_baselineRun:+H(rec,a).toFixed(2),nearestOpponentToBaselineAim:+Math.min(...opp.map(p=>H(p,base))).toFixed(2)};}}
  out.push(row);console.log(JSON.stringify(row));}}
fs.writeFileSync(outF,JSON.stringify(out,null,1));
