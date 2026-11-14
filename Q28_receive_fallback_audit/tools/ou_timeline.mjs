// Q28: independent timeline for outlet_unreached A10 (decision / apply / true movement / contact). Read-only.
// Usage: node ou_timeline.mjs <I17 core dir> <suite root> <case id> <player> <fromTick> <toTick>
import fs from 'node:fs';import zlib from 'node:zlib';import path from 'node:path';import {pathToFileURL} from 'node:url';
const [core,root,caseId,pid,from,to]=process.argv.slice(2);
const {estimatedArrival}=await import(pathToFileURL(path.join(core,'kinematics.mjs')));
const c=JSON.parse(fs.readFileSync(path.join(root,'cases.json'))).cases.find(c=>c.id===caseId);
const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,c.expected))));const F=new Map(x.frames.map(f=>[f.tick,f]));
const P=t=>F.get(t)?.players.find(p=>p.id===pid);const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const dec=x.rows.filter(r=>r.channel==='decision'&&r.player===pid&&r.tick>=+from&&r.tick<=+to);
let prev=null;
for(const r of dec){const d=r.decision,o=r.observation,b=o.ball,p=o.self;
 let gen=null;if(b.velocityKnown){for(let t=0.1;t<=2.001;t+=0.1){const q={x:clamp(b.x+clamp(b.vx,-40,40)*t*0.82,0.3,104.7),y:clamp(b.y+clamp(b.vy,-40,40)*t*0.82,0.3,67.7)};gen={t,q,ok:dist(p,q)<(4+p.abilities.pace*0.04)*t+0.8};if(gen.ok)break;}}
 const u=b.velocityKnown?(s=>({x:b.vx/s,y:b.vy/s}))(Math.hypot(b.vx,b.vy)):null;
 const tgtAheadOfBall=u?((d.target.x-b.x)*u.x+(d.target.y-b.y)*u.y):null;
 const pred=Number.isFinite(d.eta)?estimatedArrival(p,d.target,d.eta):null;
 const dirT=Math.atan2(d.target.y-p.y,d.target.x-p.x)*180/Math.PI;
 const turn=prev!=null?((dirT-prev+540)%360-180):null;prev=dirT;
 const a=P(d.applyTick),a2=P(d.applyTick+4);const trueRun=a&&a2?Math.atan2(a2.y-a.y,a2.x-a.x)*180/Math.PI:null;const trueSpeed=a&&a2?Math.hypot(a2.x-a.x,a2.y-a.y)/0.2:null;
 const fb=F.get(r.tick).ball;
 console.log([r.tick,'apply',d.applyTick,d.kind,gen?(d.reception?'DP':gen.ok?'FE'+gen.t.toFixed(1):'EX'):'VU','eta',Number.isFinite(d.eta)?d.eta.toFixed(2):'-',
  'tgt',d.target.x.toFixed(1)+','+d.target.y.toFixed(1),'tgtAheadOfObsBall',tgtAheadOfBall?.toFixed(2),'dTgt',dist(p,d.target).toFixed(1),
  'bodyResid',pred?dist(pred,d.target).toFixed(2):'-','tgtDir',dirT.toFixed(0),'turn',turn?.toFixed(0),'trueRunAfterApply',trueRun?.toFixed(0),'spd',trueSpeed?.toFixed(1),
  'trueBallDist',dist(P(r.tick),fb).toFixed(2)].join(' '));}
const ev=x.rows.filter(r=>r.channel==='event'&&r.tick>=+from&&r.tick<=+to&&['kick','contact'].includes(r.type));
console.log('events',ev.map(e=>`${e.tick}:${e.type}:${e.player}:${e.kind??''}${e.control===undefined?'':':ctl='+e.control}`).join(' '));
let best=null;for(let t=+from;t<=+to;t++){const f=F.get(t),p=P(t);if(!f||!p)continue;const d=dist(p,f.ball);if(!best||d<best.d)best={d,t};}console.log('true closest',best);
