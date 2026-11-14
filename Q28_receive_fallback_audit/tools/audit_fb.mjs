// Q28 independent read-only audit of generic receive terminal point (fallback).
// Usage: node audit_fb.mjs <I17 core dir> <fallback input.json.gz> <out.json>
// Reads saved own-observation DTOs only. Does not run matches, does not change AI.
import fs from 'node:fs';import zlib from 'node:zlib';import path from 'node:path';import {pathToFileURL} from 'node:url';
const [core,inputPath,outPath]=process.argv.slice(2);
const {choose}=await import(pathToFileURL(path.join(core,'decision.mjs')));
const {receptionPlan}=await import(pathToFileURL(path.join(core,'reception.mjs')));
const {estimatedArrival,movementLimits}=await import(pathToFileURL(path.join(core,'kinematics.mjs')));
const DT=0.05,dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const windows=JSON.parse(zlib.gunzipSync(fs.readFileSync(inputPath)));

// Gate reasons replicate reception.mjs line-by-line (diagnostic only, no new target).
function planGate(o){const p=o.self,b=o.ball;if(!b)return 'no_ball';if(b.z>=.5)return 'ball_high';if(p.role==='GK')return 'gk';if(!b.velocityKnown)return 'velocity_unknown';
 const age=(o.tick-b.seenTick)*DT;if(age<0||age>.25)return 'stale_observation';const vx=clamp(b.vx,-40,40),vy=clamp(b.vy,-40,40),speed=Math.hypot(vx,vy);if(speed<=3)return 'slow';
 const bx=b.x+vx*age,by=b.y+vy*age,dx=bx-p.x,dy=by-p.y,tc=-(dx*vx+dy*vy)/(speed*speed);if(tc<=0)return 'closest_approach_passed';if(tc>1.5)return 'closest_approach_beyond_1.5s';
 const lim=movementLimits(p);if(Math.hypot(dx+vx*tc,dy+vy*tc)>lim.speed*tc+.49)return 'closest_point_out_of_reach';return 'best_miss_over_0.8_or_plan';}
function genericPoints(o){const p=o.self,b=o.ball,pts=[];for(let t=0.1;t<=2.001;t+=0.1){const q={x:clamp(b.x+clamp(b.vx,-40,40)*t*0.82,0.3,104.7),y:clamp(b.y+clamp(b.vy,-40,40)*t*0.82,0.3,67.7)};const d=dist(p,q),lim=(4+p.abilities.pace*0.04)*t+0.8;pts.push({t,q,d,lim,ok:d<lim});}return pts;}

const rows=[],episodes=[];let nDecisions=0;const kindsAll={};
for(const w of windows){
 const dec=w.rows.filter(r=>r.channel==='decision'),ev=w.rows.filter(r=>r.channel==='event');
 const byPlayer=new Map();for(const r of dec){nDecisions++;kindsAll[r.decision.kind]=(kindsAll[r.decision.kind]||0)+1;if(!byPlayer.has(r.player))byPlayer.set(r.player,[]);byPlayer.get(r.player).push(r);}
 const kicks=ev.filter(e=>e.type==='kick'),contacts=ev.filter(e=>e.type==='contact'||e.type==='kick');
 for(const [pid,list] of byPlayer){
  let ep=null;
  for(let i=0;i<list.length;i++){const r=list[i],d=r.decision;if(d.kind!=='receive'){if(ep){ep.nextKind=d.kind;ep.nextTick=r.tick;ep=null;}continue;}
   const o=r.observation,p=o.self,b=o.ball,re=choose(o),match=re.kind===d.kind&&dist(re.target,d.target)<1e-8;
   const plan=receptionPlan(o),pts=genericPoints(o),hit=pts.find(x=>x.ok),last=pts.at(-1);
   const status=!match?'mismatch':plan?'dedicated_plan':hit?'generic_feasible':'generic_exhausted';
   const used=plan?{q:plan.target,t:plan.eta}:hit?{q:hit.q,t:hit.t}:{q:last.q,t:last.t};
   const targetOk=dist(used.q,d.target)<1e-8;
   const speed=Math.hypot(b.vx,b.vy),u={x:b.vx/speed,y:b.vy/speed},rel={x:p.x-b.x,y:p.y-b.y},along=rel.x*u.x+rel.y*u.y,lateral=Math.abs(rel.x*u.y-rel.y*u.x);
   const tAlong=(d.target.x-b.x)*u.x+(d.target.y-b.y)*u.y;
   const unclamped={x:b.x+clamp(b.vx,-40,40)*2*0.82,y:b.y+clamp(b.vy,-40,40)*2*0.82},clamped=dist(unclamped,last.q)>1e-6;
   const minGap=Math.min(...pts.map(x=>x.d-x.lim));
   const pred=estimatedArrival(p,d.target,d.eta),bodyResidual=dist(pred,d.target);
   const lastKick=[...kicks].filter(k=>k.tick<=r.tick).at(-1)??null;
   const ownSpeed=Math.hypot(p.vx,p.vy),toT={x:d.target.x-p.x,y:d.target.y-p.y},nt=Math.hypot(toT.x,toT.y),cosVel=ownSpeed>.3&&nt>0?(p.vx*toT.x+p.vy*toT.y)/(ownSpeed*nt):null;
   // future contact (audit only, after the decision): first contact/kick event by anyone, and by self, within 60 ticks or window end
   const fut=contacts.filter(e=>e.tick>=r.tick&&e.tick<r.tick+60);const firstAny=fut[0]??null,firstSelf=fut.find(e=>e.player===pid)??null;
   const row={seed:w.seed,window:w.start,windowEnd:w.end,tick:r.tick,applyTick:d.applyTick,player:pid,team:p.team,role:p.role,status,match,targetOk,eta:d.eta,
    planGate:plan?null:planGate(o),ballSpeed:speed,ballAgeTicks:o.tick-b.seenTick,ballZ:b.z,dBall:dist(p,b),along,lateral,targetAlong:tAlong,dTarget:nt,clamped,minGap,
    hitT:hit?.t??null,bodyResidual,ownSpeed,cosVel,lastKick:lastKick?{tick:lastKick.tick,player:lastKick.player,team:lastKick.team,kind:lastKick.kind,targetId:lastKick.targetId??null}:null,
    intended:lastKick?.targetId===pid,firstAny:firstAny?{tick:firstAny.tick,type:firstAny.type,player:firstAny.player,team:firstAny.team??null}:null,firstSelf:firstSelf?{tick:firstSelf.tick,type:firstSelf.type}:null,
    self:{x:p.x,y:p.y,vx:p.vx,vy:p.vy},target:d.target,ball:{x:b.x,y:b.y,vx:b.vx,vy:b.vy},score:d.score,second:d.candidates?.[1]??null};
   rows.push(row);
   if(status==='generic_exhausted'){if(!ep){ep={seed:w.seed,window:w.start,windowEnd:w.end,player:pid,team:p.team,start:r.tick,end:r.tick,n:0,rows:[],prevKind:i>0?list[i-1].decision.kind:null,prevStatus:null};episodes.push(ep);const pr=rows.at(-2);if(pr&&pr.player===pid&&pr.seed===w.seed&&i>0&&list[i-1].decision.kind==='receive')ep.prevStatus=pr.status;}ep.end=r.tick;ep.n++;ep.rows.push(rows.length-1);}
   else if(ep){ep.nextKind='receive';ep.nextStatus=status;ep.nextTick=r.tick;ep.nextHitT=row.hitT;ep=null;}
  }
  if(ep){ep.nextKind=null;ep=null;}
 }
}
fs.writeFileSync(outPath,JSON.stringify({nDecisions,kindsAll,rows,episodes}));
const c={};for(const r of rows)c[r.status]=(c[r.status]||0)+1;
console.log(JSON.stringify({nDecisions,receive:rows.length,counts:c,targetOk:rows.filter(r=>r.targetOk).length,episodes:episodes.length}));
