// Q29 follow-up: why receive V2 acted first on the DRIBBLER's own next touch. Decision -> motion -> contact/kick -> pass time,
// base vs v2 (passer = base) and flight vs combo (passer = flight), from the same start. Read only; saved rows and frames.
// usage: node v2_first_touch.mjs <setDir> <recDir> <opportunity> <player> <fromTick> <toTick> <out.json>
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,REC,OID,PID,fromS,toS,outF]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));
const core='l21_natural/recovered/playtest_i17/source/integration_i8_standard/core/';
const {movementLimits,estimatedArrival}=await import(R(core+'kinematics.mjs'));
const planI17=(await import(R(core+'reception.mjs'))).receptionPlan;
const planV2=(await import(R('l21_natural/recovered/l21_receive_compare/branches/base_on/reception.mjs'))).receptionPlan;
const DT=.05,dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),r2=x=>x==null?null:+x.toFixed(2);
const rec={};for(const a of ['base','v2','flight','combo'])rec[a]=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(REC,`${OID}_${a}.json.gz`))));
// gate analysis of one own-observation DTO: why I17 plan is null / why V2 plan exists
function gates(o){const p=o.self,b=o.ball;const g={};if(!b)return {reason:'no_ball'};g.z=r2(b.z);g.velocityKnown=!!b.velocityKnown;if(!b.velocityKnown)return {...g,i17:'velocity_unknown',v2:'velocity_unknown'};
 const age=(o.tick-b.seenTick)*DT,vx=clamp(b.vx,-40,40),vy=clamp(b.vy,-40,40),sp=Math.hypot(vx,vy);g.age=r2(age);g.ballSpeed=r2(sp);g.dBall=r2(dist(p,b));
 const bx=b.x+vx*age,by=b.y+vy*age,dx=bx-p.x,dy=by-p.y,tc=-(dx*vx+dy*vy)/(sp*sp);g.tClosest=r2(tc);const lim=movementLimits(p);g.closestOffset=r2(Math.hypot(dx+vx*tc,dy+vy*tc));g.threshold=r2(3+p.abilities.control*.11);
 const i17=planI17(structuredClone(o)),v2=planV2(structuredClone(o));
 g.i17=i17?'plan':b.z>=.5?'ball_high':age>.25?'stale':sp<=3?'slow(<=3)':tc<=0?'closest_passed':tc>1.5?'closest_beyond_1.5':'unreachable_or_miss>0.8';
 g.v2=v2?`plan(miss ${r2(v2.estimatedMissM)}, rel ${r2(v2.estimatedRelativeSpeed)}, eta ${v2.eta})`:b.z>=.5?'ball_high':age>.25?'stale':sp<=3?'slow(<=3)':tc>1.5?'closest_beyond_1.5':'miss>0.49_or_rel>threshold_or_unreachable';
 // what the GENERIC search gives (I17 fallback when plan null)
 let hit=null,last=null;for(let t=.1;t<=2.001;t+=.1){const q={x:clamp(b.x+vx*t*.82,.3,104.7),y:clamp(b.y+vy*t*.82,.3,67.7)};last={t,q};if(dist(p,q)<(4+p.abilities.pace*.04)*t+.8){hit={t,q};break;}}
 g.generic=hit?`FE t=${hit.t.toFixed(1)}`:'EX';g.canPlayGeometry=dist(p,b)<1&&age<=.35&&b.z<.5&&(p.touch||sp<8);g.ownSpeed=r2(Math.hypot(p.vx,p.vy));g.touch=!!p.touch;
 return g;}
const out={opportunity:OID,player:PID,window:[+fromS,+toS],arms:{},isolation:{}};
for(const a of ['base','v2','flight','combo']){const x=rec[a],F=new Map(x.frames.map(f=>[f.tick,f]));const P=t=>F.get(t)?.players.find(p=>p.id===PID);
 const dec=x.rows.filter(r=>r.channel==='decision'&&r.player===PID&&r.tick>=+fromS&&r.tick<=+toS).map(r=>{const d=r.decision,g=gates(r.observation);
  const cand=(d.candidates||[]).map(c=>`${c.kind}${c.targetId?'→'+c.targetId:''}:${r2(c.score)}`);
  return {tick:r.tick,apply:d.applyTick,kind:d.kind,targetId:d.targetId??null,target:d.target&&{x:r2(d.target.x),y:r2(d.target.y)},eta:d.eta==null?null:r2(d.eta),dedicated:!!d.reception,reason:d.reason,ebi:d.ballActionIntent?{kind:d.ballActionIntent.kind,targetId:d.ballActionIntent.targetId??null,apply:d.ballActionIntent.applyTick}:null,
   dTarget:d.target?r2(dist(r.observation.self,d.target)):null,...g,candidates:cand};});
 const ev=x.rows.filter(r=>r.channel==='event'&&r.tick>=+fromS&&r.tick<=+toS&&(r.player===PID||r.type==='restart_placement')&&['kick','contact','restart_placement'].includes(r.type)).map(e=>({tick:e.tick,type:e.type,kind:e.kind??null,control:e.control??null,targetId:e.targetId??null,team:e.team??null}));
 const truth=[];for(let t=+fromS;t<=+toS;t++){const f=F.get(t),p=P(t),q=P(t-1);if(!f||!p)continue;truth.push({tick:t,x:r2(p.x),y:r2(p.y),speed:q?r2(Math.hypot(p.x-q.x,p.y-q.y)/DT):null,dBall:r2(Math.hypot(p.x-f.ball.x,p.y-f.ball.y)),ballSpeed:r2(Math.hypot(f.ball.vx,f.ball.vy)),ballZ:r2(f.ball.z),action:p.action});}
 out.arms[a]={decisions:dec,events:ev,truth};}
// isolation of the passer factor: frames identical between base/flight and v2/combo until which tick?
const J=JSON.stringify;for(const [n,[a,b]] of Object.entries({base_vs_flight:['base','flight'],v2_vs_combo:['v2','combo'],base_vs_v2:['base','v2']})){const fa=new Map(rec[a].frames.map(f=>[f.tick,f])),fb=new Map(rec[b].frames.map(f=>[f.tick,f]));out.isolation[n]=[...fa.keys()].find(t=>fb.has(t)&&J(fa.get(t))!==J(fb.get(t)))??null;}
fs.writeFileSync(outF,JSON.stringify(out,null,1));
console.log(`## ${OID} ${PID} ${fromS}-${toS}  first frame diff: base/flight ${out.isolation.base_vs_flight}  v2/combo ${out.isolation.v2_vs_combo}  base/v2 ${out.isolation.base_vs_v2}`);
for(const a of ['base','v2']){console.log(`[${a}] events: ${out.arms[a].events.map(e=>`${e.tick}:${e.type}${e.kind?':'+e.kind:''}${e.control!=null?':ctl='+e.control:''}${e.targetId?'→'+e.targetId:''}`).join(' ')}`);
 for(const d of out.arms[a].decisions)console.log(`  ${d.tick}→${d.apply} ${d.kind}${d.targetId?'→'+d.targetId:''}${d.dedicated?'(DP)':''}${d.ebi?' EBI:'+d.ebi.kind+'→'+d.ebi.targetId+'@'+d.ebi.apply:''} tgt(${d.target?.x},${d.target?.y}) dTgt ${d.dTarget} eta ${d.eta} | dBall ${d.dBall} v ${d.ballSpeed} tc ${d.tClosest} off ${d.closestOffset} | i17:${d.i17} v2:${d.v2} gen:${d.generic} | own ${d.ownSpeed} touch ${d.touch} canPlayGeo ${d.canPlayGeometry} | ${d.candidates.join(' ')}`);
 const tr=out.arms[a].truth.filter((r,i)=>i%2===0);console.log(`  truth(every 2 ticks): `+tr.map(r=>`${r.tick}:d${r.dBall}/s${r.speed}/${String(r.action).slice(0,4)}`).join(' '));}
