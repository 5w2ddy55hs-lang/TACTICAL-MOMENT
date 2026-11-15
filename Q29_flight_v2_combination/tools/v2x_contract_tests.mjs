// Q29E: LOCAL information-contract tests of the v2x condition, as pure functions on saved own-observation DTOs.
// These are artificial contract tests (counterfactual edits of the witnessed-touch field only), NOT match frequencies.
// Every edited DTO is re-validated with the engine's own assertObservation before use.
//  T1 stale self-witness: own&passed DTOs, age of the witnessed self touch varied -> does v2x depend on age?
//  T2 self pass: own&passed DTOs whose latest own kick was a pass/shoot -> does V2 differ from I17 there at all?
//  T3 unwitnessed other touch: own cases where V2 differs, with the witness field counterfactually set to a visible
//     other player (= "the player did witness the other's touch") and the reverse edit on the other-ball cases.
//  T4 witness older than the ball-velocity evidence interval (ball seen moving after the witnessed touch).
// usage: node v2x_contract_tests.mjs <setDir> <out.json> <recording.json.gz>...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,outF,...recs]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));
const core='l21_natural/recovered/playtest_i17/source/integration_i8_standard/core/';
const {assertObservation}=await import(R(core+'perception.mjs'));
const B='l21_natural/recovered/l21_receive_compare/branches/';
const C={i17:(await import(R(B+'base_off/decision.mjs'))).choose,v2:(await import(R(B+'base_on/decision.mjs'))).choose,v2x:(await import(R(B+'q29c_v2x/decision.mjs'))).choose};
const P={i17:(await import(R(core+'reception.mjs'))).receptionPlan,v2:(await import(R(B+'base_on/reception.mjs'))).receptionPlan,v2x:(await import(R(B+'q29c_v2x/reception.mjs'))).receptionPlan};
const DT=.05,clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),J=JSON.stringify,cl=o=>structuredClone(o);
const own=o=>!!o.self.observedTouch&&o.self.observedTouch.players.length>0&&o.self.observedTouch.players.every(q=>q.id===o.self.id);
const passed=o=>{const p=o.self,b=o.ball;if(!b?.velocityKnown)return false;const age=(o.tick-b.seenTick)*DT,vx=clamp(b.vx,-40,40),vy=clamp(b.vy,-40,40),sp=Math.hypot(vx,vy);const bx=b.x+vx*age,by=b.y+vy*age;return -((bx-p.x)*vx+(by-p.y)*vy)/(sp*sp)<=0;};
const valid=o=>{try{assertObservation(cl(o));return true;}catch(e){return 'INVALID:'+e.message;}};
const res={T1:{cases:0,ageVaried:0,v2xUnchangedByAge:0,validEdits:0,invalidEdits:0},T2:{selfPassOrShoot:0,v2PlanExists:0,chooseV2DiffersI17:0,v2xEqI17:0},T3:{ownCases:0,editedValid:0,editedInvalid:0,v2xEqV2AfterEdit:0,otherCases:0,reverseValid:0,reverseInvalid:0,v2xEqI17AfterReverse:0,anchors:[]},T4:{ownAndPassed:0,witnessOlderThanEvidenceFrom:0,v2DiffersThere:0}};
const anchors={'42130_v2.json.gz':['A05',42160],'12235_v2.json.gz':['A07',12341],'60000_base.json.gz':['B09',60049]};const anchorRows=[];
for(const f of recs){const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(f)));const kicks=x.rows.filter(r=>r.channel==='event'&&r.type==='kick');
 for(const r of x.rows){if(r.channel!=='decision'||!r.observation?.ball)continue;const o=r.observation,p=o.self;if(!o.ball.velocityKnown)continue;
  const isOwn=own(o),isPassed=passed(o);const c0={i17:J(C.i17(cl(o))),v2:J(C.v2(cl(o))),v2x:J(C.v2x(cl(o)))};const v2Diff=c0.v2!==c0.i17;
  if(isOwn&&isPassed){res.T4.ownAndPassed++;const e=o.ball.velocityEvidence;if(e?.fromTick!=null&&p.observedTouch.seenTick<e.fromTick){res.T4.witnessOlderThanEvidenceFrom++;if(v2Diff)res.T4.v2DiffersThere++;}
   const k=kicks.filter(k=>k.player===p.id&&k.tick<r.tick).at(-1);if(k&&['pass','shoot','restart_kick'].includes(k.kind)&&k.tick>=p.observedTouch.seenTick-1){res.T2.selfPassOrShoot++;if(P.v2(cl(o)))res.T2.v2PlanExists++;if(v2Diff)res.T2.chooseV2DiffersI17++;if(c0.v2x===c0.i17)res.T2.v2xEqI17++;}}
  if(isOwn&&isPassed&&v2Diff){res.T1.cases++;let allSame=true;for(const age of [1,4,12,30,61,120]){const seen=r.tick-age;if(seen<0)continue;const e=cl(o);e.self.observedTouch.seenTick=seen;const v=valid(e);if(v!==true){res.T1.invalidEdits++;continue;}res.T1.validEdits++;res.T1.ageVaried++;if(J(C.v2x(e))!==c0.v2x)allSame=false;}if(allSame)res.T1.v2xUnchangedByAge++;
   // T3 forward edit: pretend the player witnessed a touch by a visible other player at the same seenTick
   res.T3.ownCases++;const other=o.people.find(q=>q.id!==p.id&&o.tick-q.seenTick<=8);if(other){const e=cl(o);e.self.observedTouch={seenTick:p.observedTouch.seenTick,players:[{id:other.id,team:other.team,part:'foot'}]};const v=valid(e);if(v!==true)res.T3.editedInvalid++;else{res.T3.editedValid++;const w=J(C.v2x(e));if(w===c0.v2)res.T3.v2xEqV2AfterEdit++;const a=anchors[path.basename(f)];if(a&&a[0]===p.id&&a[1]===r.tick)anchorRows.push({rec:path.basename(f),player:p.id,tick:r.tick,test:'T3_forward',i17:c0.i17.slice(0,60),v2x_before:'=I17',v2x_after_edit:w===c0.v2?'=V2':'other',editedWitness:other.id});}}}
  if(!isOwn&&isPassed&&v2Diff){res.T3.otherCases++;const e=cl(o);e.self.observedTouch={seenTick:p.observedTouch?p.observedTouch.seenTick:r.tick-1,players:[{id:p.id,team:p.team,part:'foot'}]};const v=valid(e);if(v!==true)res.T3.reverseInvalid++;else{res.T3.reverseValid++;const w=J(C.v2x(e));if(w===c0.i17)res.T3.v2xEqI17AfterReverse++;}}
 }}
res.T3.anchors=anchorRows;fs.writeFileSync(outF,JSON.stringify(res,null,1));console.log(JSON.stringify(res,null,1));
