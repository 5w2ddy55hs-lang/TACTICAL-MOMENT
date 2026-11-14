// Where does receive V2 differ from the I17 reception plan, as pure functions on every saved own-observation DTO?
// Classifies each differing DTO by closest-approach sign, ball distance/speed, and whether this player's own last kick
// was the latest kick before the decision (dribbler). Also exact miss/rel values. Read only.
// usage: node v2_where_differs.mjs <setDir> <out.json> <recording.json.gz>...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,outF,...recs]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));
const core='l21_natural/recovered/playtest_i17/source/integration_i8_standard/core/';
const planI17=(await import(R(core+'reception.mjs'))).receptionPlan,planV2=(await import(R('l21_natural/recovered/l21_receive_compare/branches/base_on/reception.mjs'))).receptionPlan;
const chooseI17=(await import(R('l21_natural/recovered/l21_receive_compare/branches/base_off/decision.mjs'))).choose,chooseV2=(await import(R('l21_natural/recovered/l21_receive_compare/branches/base_on/decision.mjs'))).choose;
const DT=.05,clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),J=JSON.stringify;const rows=[];let n=0,planDiff=0,chooseDiff=0;
for(const f of recs){const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(f)));const kicks=x.rows.filter(r=>r.channel==='event'&&r.type==='kick');
 for(const r of x.rows){if(r.channel!=='decision'||!r.observation?.ball)continue;n++;const o=r.observation,p=o.self,b=o.ball;
  const a=planI17(structuredClone(o)),v=planV2(structuredClone(o));const same=J(a)===J(v);if(!same)planDiff++;
  const ca=chooseI17(structuredClone(o)),cv=chooseV2(structuredClone(o));const cd=J(ca)!==J(cv);if(cd)chooseDiff++;
  if(same&&!cd)continue;
  let tc=null,sp=null,d=null;if(b.velocityKnown){const age=(o.tick-b.seenTick)*DT,vx=clamp(b.vx,-40,40),vy=clamp(b.vy,-40,40);sp=Math.hypot(vx,vy);const bx=b.x+vx*age,by=b.y+vy*age,dx=bx-p.x,dy=by-p.y;tc=-(dx*vx+dy*vy)/(sp*sp);d=Math.hypot(b.x-p.x,b.y-p.y);}
  const lastKick=kicks.filter(k=>k.tick<r.tick).at(-1);
  rows.push({rec:path.basename(f),tick:r.tick,player:p.id,chooseDiffers:cd,chosenI17:ca.kind,chosenV2:cv.kind,tClosest:tc,dBall:d,ballSpeed:sp,ballZ:b.z,i17Plan:!!a,v2Plan:!!v,v2Miss:v?.estimatedMissM??null,v2Rel:v?.estimatedRelativeSpeed??null,lastKickBySelf:lastKick?.player===p.id,lastKickKind:lastKick?.kind??null,ticksSinceLastKick:lastKick?r.tick-lastKick.tick:null});}}
fs.writeFileSync(outF,JSON.stringify({n,planDiff,chooseDiff,rows},null,1));
const cnt=(k,f)=>rows.filter(f).length;
console.log(JSON.stringify({dtos:n,planDiffers:planDiff,chooseDiffers:chooseDiff,
 ofChooseDiff:{tClosestLE0:cnt(0,r=>r.chooseDiffers&&r.tClosest!=null&&r.tClosest<=0),tClosestGT0:cnt(0,r=>r.chooseDiffers&&r.tClosest>0),
  i17PlanNull_v2Plan:cnt(0,r=>r.chooseDiffers&&!r.i17Plan&&r.v2Plan),bothPlanDifferentTarget:cnt(0,r=>r.chooseDiffers&&r.i17Plan&&r.v2Plan),i17Plan_v2Null:cnt(0,r=>r.chooseDiffers&&r.i17Plan&&!r.v2Plan),
  lastKickBySelf:cnt(0,r=>r.chooseDiffers&&r.lastKickBySelf),lastKickBySelfDribble:cnt(0,r=>r.chooseDiffers&&r.lastKickBySelf&&r.lastKickKind==='dribble'),
  dBallLT2_5:cnt(0,r=>r.chooseDiffers&&r.dBall<2.5),ballSpeed3to6:cnt(0,r=>r.chooseDiffers&&r.ballSpeed>3&&r.ballSpeed<=6),
  kindsI17toV2:Object.entries(rows.filter(r=>r.chooseDiffers).reduce((m,r)=>{const k=r.chosenI17+'>'+r.chosenV2;m[k]=(m[k]||0)+1;return m;},{}))},
 missQuantiles:(()=>{const v=rows.filter(r=>r.chooseDiffers&&r.v2Miss!=null).map(r=>r.v2Miss).sort((a,b)=>a-b);return v.length?[v[0],v[Math.floor(v.length*.25)],v[Math.floor(v.length*.5)],v[Math.floor(v.length*.75)],v.at(-1)].map(x=>+x.toFixed(4)):null;})(),
 relMax:Math.max(...rows.filter(r=>r.chooseDiffers&&r.v2Rel!=null).map(r=>r.v2Rel)).toFixed(2)},null,1));
