// Q29D: what does the v2x condition ("own latest WITNESSED touch is self" AND tClosest<=0) actually cover, on saved DTOs?
// For each such DTO (audit only): kind of the player's own latest kick before the decision, freshness of the witnessed
// touch, and whether the truth shows a touch by someone else after that witnessed touch that the player did not witness.
// usage: node v2x_scope.mjs <out.json> <recording.json.gz>...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [outF,...recs]=process.argv.slice(2);const DT=.05,clamp=(x,a,b)=>Math.max(a,Math.min(b,x));const rows=[];
for(const f of recs){const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(f)));const ev=x.rows.filter(r=>r.channel==='event'&&['kick','contact'].includes(r.type));
 for(const r of x.rows){if(r.channel!=='decision'||!r.observation?.ball)continue;const o=r.observation,p=o.self,b=o.ball,ot=p.observedTouch;
  const own=!!ot&&ot.players.length>0&&ot.players.every(q=>q.id===p.id);if(!own||!b.velocityKnown)continue;
  const age=(o.tick-b.seenTick)*DT,vx=clamp(b.vx,-40,40),vy=clamp(b.vy,-40,40),sp=Math.hypot(vx,vy);const bx=b.x+vx*age,by=b.y+vy*age;const tc=-((bx-p.x)*vx+(by-p.y)*vy)/(sp*sp);if(!(tc<=0))continue;
  const ownKick=ev.filter(e=>e.type==='kick'&&e.player===p.id&&e.tick<r.tick).at(-1);const ownTouchAny=ev.filter(e=>e.player===p.id&&e.tick<r.tick).at(-1);
  const otherAfter=ev.filter(e=>e.player!==p.id&&e.tick>=ot.seenTick&&e.tick<r.tick&&(e.type==='kick'||e.type==='contact'));
  rows.push({rec:path.basename(f),tick:r.tick,player:p.id,decisionKind:r.decision.kind,dedicated:!!r.decision.reception,witnessedSeenTick:ot.seenTick,freshnessTicks:r.tick-ot.seenTick,ownLastKickKind:ownKick&&ownKick.tick>=ot.seenTick-1?ownKick.kind:(ownTouchAny&&ownTouchAny.tick>=ot.seenTick-1?'contact_only':'none_near_witness'),unwitnessedOtherTouch:otherAfter.length>0,unwitnessedBy:otherAfter.map(e=>e.player+':'+e.type+(e.kind?':'+e.kind:'')).slice(0,3),dBall:+Math.hypot(b.x-p.x,b.y-p.y).toFixed(2),ballSpeed:+sp.toFixed(2),tClosest:+tc.toFixed(2)});}}
fs.writeFileSync(outF,JSON.stringify(rows,null,1));
const C=(f)=>rows.filter(f).length,hist=k=>Object.entries(rows.reduce((m,r)=>{m[r[k]]=(m[r[k]]||0)+1;return m;},{})).sort((a,b)=>b[1]-a[1]);
console.log(JSON.stringify({ownAndPassed:rows.length,byOwnLastKickKind:hist('ownLastKickKind'),byDecisionKind:hist('decisionKind'),withDedicatedPlanRecorded:C(r=>r.dedicated),unwitnessedOtherTouch:C(r=>r.unwitnessedOtherTouch),freshness:{le8:C(r=>r.freshnessTicks<=8),t9_20:C(r=>r.freshnessTicks>8&&r.freshnessTicks<=20),t21_60:C(r=>r.freshnessTicks>20&&r.freshnessTicks<=60),gt60:C(r=>r.freshnessTicks>60)},dBallGT3:C(r=>r.dBall>3),ballSpeedLE3:C(r=>r.ballSpeed<=3)},null,1));
for(const r of rows.filter(r=>r.unwitnessedOtherTouch).slice(0,12))console.log(' unwitnessed:',r.rec,r.tick,r.player,r.decisionKind,'fresh',r.freshnessTicks,'by',r.unwitnessedBy.join(' '),'dBall',r.dBall,'v',r.ballSpeed);
