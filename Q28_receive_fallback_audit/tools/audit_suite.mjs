// Q28: classify generic reach search per decision in the 7-scene suite (saved records only, no engine run).
// Usage: node audit_suite.mjs <I17 core dir> <suite root> <out.json>
import fs from 'node:fs';import zlib from 'node:zlib';import path from 'node:path';import {pathToFileURL} from 'node:url';
const [core,root,outPath]=process.argv.slice(2);
const {choose}=await import(pathToFileURL(path.join(core,'decision.mjs')));
const {receptionPlan}=await import(pathToFileURL(path.join(core,'reception.mjs')));
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const cases=JSON.parse(fs.readFileSync(path.join(root,'cases.json'))).cases,out=[];
for(const c of cases){const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,c.expected))));const F=new Map(x.frames.map(f=>[f.tick,f]));
 const pos=(t,id)=>{const f=F.get(t);if(!f)return null;const p=f.players.find(p=>p.id===id);return p?{x:p.x,y:p.y}:null;};
 for(const r of x.rows){if(r.channel!=='decision')continue;const d=r.decision,o=r.observation;if(!['receive','intercept','press'].includes(d.kind))continue;
  const b=o.ball,p=o.self;let status='velocity_unknown',hitT=null,t=null;
  const re=choose(o),match=re.kind===d.kind&&dist(re.target,d.target)<1e-8;
  const plan=d.reception?receptionPlan(o):null;
  if(b.velocityKnown){let hit=null,last=null;for(let tt=0.1;tt<=2.001;tt+=0.1){const q={x:clamp(b.x+clamp(b.vx,-40,40)*tt*0.82,0.3,104.7),y:clamp(b.y+clamp(b.vy,-40,40)*tt*0.82,0.3,67.7)};last={q,t:tt};if(dist(p,q)<(4+p.abilities.pace*0.04)*tt+0.8){hit={q,t:tt};break;}}
   status=d.reception?'dedicated_plan':hit?'generic_feasible':'generic_exhausted';hitT=hit?.t??null;}
  const fr=F.get(r.tick),ball=fr?.ball;const speed=Math.hypot(b.vx??0,b.vy??0),u=speed>0?{x:b.vx/speed,y:b.vy/speed}:{x:0,y:0},along=(p.x-b.x)*u.x+(p.y-b.y)*u.y,lateral=Math.abs((p.x-b.x)*u.y-(p.y-b.y)*u.x);
  // audit-only truth: min true player-ball distance over next 40 ticks
  let best=null;for(let k=r.tick;k<=r.tick+40;k++){const f=F.get(k),q=pos(k,p.id);if(!f||!q)break;const dd=Math.hypot(q.x-f.ball.x,q.y-f.ball.y);if(!best||dd<best.d)best={d:dd,tick:k};}
  out.push({case:c.id,seed:c.seed,tick:r.tick,applyTick:d.applyTick,player:p.id,team:p.team,kind:d.kind,status,match,hitT,eta:d.eta,target:d.target,reason:d.reason,
   self:{x:p.x,y:p.y,vx:p.vx,vy:p.vy},obsBall:{x:b.x,y:b.y,vx:b.vx??null,vy:b.vy??null,z:b.z,known:b.velocityKnown,age:o.tick-b.seenTick},trueBall:ball?{x:ball.x,y:ball.y,z:ball.z,vx:ball.vx,vy:ball.vy}:null,
   truePosApply:pos(d.applyTick,p.id),along,lateral,ballSpeed:speed,minTrue:best});}}
fs.writeFileSync(outPath,JSON.stringify(out));
const s={};for(const r of out){const k=r.case+'|'+r.kind+'|'+r.status;s[k]=(s[k]||0)+1;}
console.log(JSON.stringify({n:out.length,mismatch:out.filter(r=>!r.match).length,byCaseKindStatus:s},null,1));
