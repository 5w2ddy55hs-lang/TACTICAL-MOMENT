// Q29F: find NATURAL decisions (no memory edits) where the player's witnessed-touch memory is a self touch while the
// truth shows a touch by someone else after that witnessed tick and before the decision (unwitnessed other touch).
// Reports every such DTO with: ball distance/speed, closest-approach sign, whether V2 would plan with the memory as is
// vs. if the other touch had been witnessed (pure functions), and the decision kinds. Read only.
// usage: node find_unwitnessed.mjs <setDir> <out.json> <recording.json.gz>...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,outF,...recs]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));const B='l21_natural/recovered/l21_receive_compare/branches/';
const C={i17:(await import(R(B+'base_off/decision.mjs'))).choose,v2:(await import(R(B+'base_on/decision.mjs'))).choose,v2x:(await import(R(B+'q29c_v2x/decision.mjs'))).choose};
const DT=.05,clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),J=JSON.stringify,cl=o=>structuredClone(o);const rows=[];let scanned=0,ownWitness=0;
for(const f of recs){const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(f)));const touches=x.rows.filter(r=>r.channel==='event'&&(r.type==='kick'||r.type==='contact'));
 for(const r of x.rows){if(r.channel!=='decision')continue;const o=r.observation,p=o.self,ot=p.observedTouch;scanned++;if(!ot||!ot.players.length||!ot.players.every(q=>q.id===p.id))continue;ownWitness++;
  const others=touches.filter(e=>e.player!==p.id&&e.tick>ot.seenTick&&e.tick<r.tick);if(!others.length)continue;
  const b=o.ball;let passed=null,sp=null,d=null;if(b?.velocityKnown){const age=(o.tick-b.seenTick)*DT,vx=clamp(b.vx,-40,40),vy=clamp(b.vy,-40,40);sp=Math.hypot(vx,vy);const bx=b.x+vx*age,by=b.y+vy*age;passed=-((bx-p.x)*vx+(by-p.y)*vy)/(sp*sp)<=0;d=Math.hypot(b.x-p.x,b.y-p.y);}
  const c={i17:J(C.i17(cl(o))),v2:J(C.v2(cl(o))),v2x:J(C.v2x(cl(o)))};
  rows.push({rec:path.basename(f),tick:r.tick,player:p.id,witnessSeenTick:ot.seenTick,unwitnessed:others.slice(0,4).map(e=>`${e.tick}:${e.player}:${e.type}${e.kind?':'+e.kind:''}`),ballKnown:!!b?.velocityKnown,ballSeenAge:b?r.tick-b.seenTick:null,dBall:d==null?null:+d.toFixed(2),ballSpeed:sp==null?null:+sp.toFixed(2),passed,kind:r.decision.kind,v2DiffersI17:c.v2!==c.i17,v2xDiffersV2:c.v2x!==c.v2});}}
fs.writeFileSync(outF,JSON.stringify({scanned,ownWitness,found:rows.length,rows},null,1));
console.log(JSON.stringify({scanned,ownWitness,found:rows.length,withBallKnown:rows.filter(r=>r.ballKnown).length,passedAndKnown:rows.filter(r=>r.passed).length,v2DiffersI17:rows.filter(r=>r.v2DiffersI17).length,v2xDiffersV2:rows.filter(r=>r.v2xDiffersV2).length,dBallLE4:rows.filter(r=>r.dBall!=null&&r.dBall<=4).length}));
for(const r of rows.filter(r=>r.dBall!=null&&r.dBall<=6).slice(0,40))console.log(` ${r.rec} ${r.tick} ${r.player} witness@${r.witnessSeenTick} unwitnessed ${r.unwitnessed.join(' ')} | dBall ${r.dBall} v ${r.ballSpeed} passed ${r.passed} seenAge ${r.ballSeenAge} | ${r.kind} v2≠i17 ${r.v2DiffersI17} v2x≠v2 ${r.v2xDiffersV2}`);
