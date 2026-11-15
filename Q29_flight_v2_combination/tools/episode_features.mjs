// Q29D §4 step 1: receiver-observable features at the FIRST V2-only decision of each own-touch episode, side by side,
// so a benefit candidate (O2) and the known outs (O3, O4) can be compared. Audit-only columns are marked. Read only.
// usage: node episode_features.mjs <setDir> <out.json> <label>=<recording.json.gz>:<player>:<tick> ...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,outF,...specs]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));
const planV2=(await import(R('l21_natural/recovered/l21_receive_compare/branches/base_on/reception.mjs'))).receptionPlan;
const {movementLimits}=await import(R('l21_natural/recovered/playtest_i17/source/integration_i8_standard/core/kinematics.mjs'));
const DT=.05,clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),r2=v=>v==null?null:+v.toFixed(2);const out=[];
for(const s of specs){const [label,rest]=s.split('=');const [f,pid,tickS]=rest.split(':');const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(f)));const t=+tickS;
 const r=x.rows.find(r=>r.channel==='decision'&&r.player===pid&&r.tick===t);const o=r.observation,p=o.self,b=o.ball;const age=(o.tick-b.seenTick)*DT,vx=clamp(b.vx,-40,40),vy=clamp(b.vy,-40,40),sp=Math.hypot(vx,vy);
 const bx=b.x+vx*age,by=b.y+vy*age,tc=-((bx-p.x)*vx+(by-p.y)*vy)/(sp*sp);const v2=planV2(structuredClone(o));const L=movementLimits(p);
 const enemies=o.people.filter(q=>q.team!==p.team),friends=o.people.filter(q=>q.team===p.team&&q.id!==p.id);const dBallTo=q=>Math.hypot(q.x-b.x,q.y-b.y);
 const ne=enemies.map(q=>({id:q.id,d:dBallTo(q),age:o.tick-q.seenTick})).sort((a,c)=>a.d-c.d)[0],nf=friends.map(q=>({id:q.id,d:dBallTo(q)})).sort((a,c)=>a.d-c.d)[0];
 const edge=Math.min(p.y,68-p.y,p.x,105-p.x),ballEdge=Math.min(b.y,68-b.y,b.x,105-b.x);const u={x:vx/sp,y:vy/sp};
 // where the ball is heading relative to the nearest field edge (audit-only geometry from own observation)
 const headingToSide=Math.abs(u.y),toward=(b.y>34?u.y>0:u.y<0);
 const f0=x.frames.find(q=>q.tick===t);
 out.push({label,player:pid,tick:t,dBall:r2(Math.hypot(b.x-p.x,b.y-p.y)),ballSpeed:r2(sp),tClosest:r2(tc),v2Miss:r2(v2?.estimatedMissM),v2Rel:r2(v2?.estimatedRelativeSpeed),v2Eta:r2(v2?.eta),v2TargetDist:v2?r2(Math.hypot(v2.target.x-p.x,v2.target.y-p.y)):null,ownSpeed:r2(Math.hypot(p.vx,p.vy)),maxSpeed:r2(L.speed),nearestEnemyToBall:ne&&{id:ne.id,d:r2(ne.d),seenAge:ne.age},nearestFriendToBall:nf&&{id:nf.id,d:r2(nf.d)},selfEdgeDist:r2(edge),ballEdgeDist:r2(ballEdge),ballHeadingSideComponent:r2(headingToSide),ballTowardNearSide:toward,ballZ:r2(b.z),witnessedTouchAge:p.observedTouch?t-p.observedTouch.seenTick:null,role:p.role,ownHalf:(p.dir===1?p.x:105-p.x)<52.5,trueBallEdge_auditOnly:f0?r2(Math.min(f0.ball.y,68-f0.ball.y,f0.ball.x,105-f0.ball.x)):null});}
fs.writeFileSync(outF,JSON.stringify(out,null,1));
const keys=['dBall','ballSpeed','tClosest','v2Miss','v2Rel','v2Eta','v2TargetDist','ownSpeed','selfEdgeDist','ballEdgeDist','ballHeadingSideComponent','ballTowardNearSide','witnessedTouchAge','ownHalf'];
console.log(['label','player','tick',...keys,'nearestEnemy(d)','nearestFriend(d)'].join(' | '));for(const o of out)console.log([o.label,o.player,o.tick,...keys.map(k=>o[k]),o.nearestEnemyToBall?`${o.nearestEnemyToBall.id}(${o.nearestEnemyToBall.d})`:'-',o.nearestFriendToBall?`${o.nearestFriendToBall.id}(${o.nearestFriendToBall.d})`:'-'].join(' | '));
