// Usage: node gate_suite.mjs <I17 core> <suite root> <case> <player> <from> <to>
import fs from 'node:fs';import zlib from 'node:zlib';import path from 'node:path';import {pathToFileURL} from 'node:url';
const [core,root,cid,pid,from,to]=process.argv.slice(2);
const {movementLimits,estimatedArrival}=await import(pathToFileURL(path.join(core,'kinematics.mjs')));
const DT=.05,clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const c=JSON.parse(fs.readFileSync(path.join(root,'cases.json'))).cases.find(c=>c.id===cid);
const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,c.expected))));
for(const r of x.rows){if(r.channel!=='decision'||r.player!==pid||r.tick<+from||r.tick>+to||r.decision.kind!=='receive')continue;const o=r.observation,p=o.self,b=o.ball;
 let g='plan_ok_or_miss';const age=(o.tick-b.seenTick)*DT,vx=clamp(b.vx,-40,40),vy=clamp(b.vy,-40,40),sp=Math.hypot(vx,vy);
 const bx=b.x+vx*age,by=b.y+vy*age,dx=bx-p.x,dy=by-p.y,tc=-(dx*vx+dy*vy)/(sp*sp),lim=movementLimits(p),off=Math.hypot(dx+vx*tc,dy+vy*tc);
 if(b.z>=.5)g='ball_high';else if(age>.25)g='stale';else if(sp<=3)g='slow';else if(tc<=0)g='closest_passed';else if(tc>1.5)g='closest_beyond_1.5s';else if(off>lim.speed*tc+.49)g='closest_point_out_of_reach';
 console.log(r.tick,r.decision.reception?'DP':'generic',g,'tClosest',tc.toFixed(2),'closestOffset',off.toFixed(2),'reachAtTc',(lim.speed*tc+.49).toFixed(2),'maxSpeed',lim.speed.toFixed(2),'ownSpeed',Math.hypot(p.vx,p.vy).toFixed(2));}
