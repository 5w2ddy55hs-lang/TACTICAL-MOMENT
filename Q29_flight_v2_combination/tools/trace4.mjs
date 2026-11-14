// Q29 analysis of one opportunity recorded in 4 arms (read only; audit truth from frames, decisions from own DTO rows).
// usage: node trace4.mjs <setDir> <recDir> <opportunityId> <out.json>
// Frame tick T = state BEFORE processing T; an event with tick T happens during the processing of T.
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,REC,OID,outF]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));
const plan17=(await import(R('l21_natural/recovered/playtest_i17/source/integration_i8_standard/core/reception.mjs'))).receptionPlan;
const ARMS=['base','flight','v2','combo'];const J=x=>JSON.stringify(x);const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const rec={};for(const a of ARMS)rec[a]=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(REC,`${OID}_${a}.json.gz`))));
const out={opportunity:OID,start:rec.base.start,source:rec.base.source,firstDifference:{},arms:{}};
// 1) first differences along each factor
const pairs={passer_under_baseReceiver:['base','flight'],passer_under_V2Receiver:['v2','combo'],receiver_under_basePasser:['base','v2'],receiver_under_flightPasser:['flight','combo'],both_vs_base:['base','combo']};
for(const [name,[a,b]] of Object.entries(pairs)){const fa=new Map(rec[a].frames.map(f=>[f.tick,f])),fb=new Map(rec[b].frames.map(f=>[f.tick,f]));
 const frame=[...fa.keys()].find(t=>fb.has(t)&&J(fa.get(t))!==J(fb.get(t)))??null;
 const da=new Map(rec[a].rows.filter(r=>r.channel==='decision').map(r=>[r.tick+':'+r.player,r])),db=new Map(rec[b].rows.filter(r=>r.channel==='decision').map(r=>[r.tick+':'+r.player,r]));
 const keys=[...new Set([...da.keys(),...db.keys()])].sort((x,y)=>(+x.split(':')[0])-(+y.split(':')[0])||x.localeCompare(y));
 const k=keys.find(k=>!da.has(k)||!db.has(k)||J(da.get(k).decision)!==J(db.get(k).decision));
 const k2=keys.find(k=>!da.has(k)||!db.has(k)||da.get(k).decision.kind!==db.get(k).decision.kind||dist(da.get(k).decision.target,db.get(k).decision.target)>1e-9);
 const brief=r=>r?{kind:r.decision.kind,target:r.decision.target&&{x:+r.decision.target.x.toFixed(2),y:+r.decision.target.y.toFixed(2)},targetId:r.decision.targetId??null,reason:r.decision.reason}:null;
 out.firstDifference[name]={arms:[a,b],firstFrameDiff:frame,firstDecisionDiff:k?{key:k,[a]:brief(da.get(k)),[b]:brief(db.get(k))}:null,firstKindOrTargetDiff:k2?{key:k2,[a]:brief(da.get(k2)),[b]:brief(db.get(k2))}:null};}
// 2) per arm: passes, receiver reaction, contacts, next play
function cls(r,arm){const d=r.decision,o=r.observation;if(!['receive','intercept','press'].includes(d.kind))return d.kind;const b=o.ball;
 if(d.reception){const p17=plan17(structuredClone(o));const tag=(arm==='v2'||arm==='combo')?(p17?(dist(p17.target,d.target)<1e-9?'':'(V2で別目標)'):'(V2だけの計画)'):'';return d.kind+':DP'+d.eta.toFixed(2)+tag;}
 if(!b?.velocityKnown)return d.kind+':VU';let hit=null;for(let t=0.1;t<=2.001;t+=0.1){const q={x:clamp(b.x+clamp(b.vx,-40,40)*t*0.82,0.3,104.7),y:clamp(b.y+clamp(b.vy,-40,40)*t*0.82,0.3,67.7)};if(dist(o.self,q)<(4+o.self.abilities.pace*0.04)*t+0.8){hit=t;break;}}
 return d.kind+(hit?':FE'+hit.toFixed(1):':EX');}
for(const a of ARMS){const x=rec[a],F=new Map(x.frames.map(f=>[f.tick,f])),ev=x.rows.filter(r=>r.channel==='event'),dec=x.rows.filter(r=>r.channel==='decision');
 const P=(t,id)=>F.get(t)?.players.find(p=>p.id===id);const end=Math.max(...F.keys());
 const passes=ev.filter(e=>e.type==='kick'&&['pass','restart_kick','throw_in'].includes(e.kind)&&e.targetId).map(k=>{
  const pdr=dec.filter(r=>r.player===k.player&&r.tick<=k.tick&&(r.decision.kind===k.kind||(r.decision.ballActionIntent?.kind===k.kind&&r.decision.ballActionIntent?.targetId===k.targetId))).at(-1);
  const pd=pdr?{tick:pdr.tick,observation:pdr.observation,via:pdr.decision.kind===k.kind?'decision':'early_ball_intent',decision:pdr.decision.kind===k.kind?pdr.decision:{...pdr.decision.ballActionIntent,applyTick:pdr.decision.ballActionIntent.applyTick}}:null;
  let lead=null;if(pd){const q=pd.observation.people.find(p=>p.id===k.targetId);if(q&&Math.hypot(q.vx??0,q.vy??0)>0.3){const v={x:q.vx,y:q.vy};lead=+(((pd.decision.target.x-q.x)*v.x+(pd.decision.target.y-q.y)*v.y)/(v.x*v.x+v.y*v.y)).toFixed(2);}}
  const after=ev.filter(e=>e.tick>k.tick&&['kick','contact','restart_placement','goal','throw_pickup'].includes(e.type));const first=after[0]??null;
  const stopT=first?first.tick:end;let best=null;for(let t=k.tick;t<=stopT;t++){const f=F.get(t),p=P(t,k.targetId);if(!f||!p)continue;const d=Math.hypot(p.x-f.ball.x,p.y-f.ball.y);if(!best||d<best.d)best={d:+d.toFixed(2),tick:t};}
  const recvDec=dec.filter(r=>r.player===k.targetId&&r.tick>k.tick&&r.tick<=stopT+8).map(r=>`${r.tick}:${cls(r,a)}`);
  let minSpeed=null;for(let t=k.tick+1;t<=stopT;t++){const p=P(t,k.targetId),q=P(t-1,k.targetId);if(!p||!q)continue;const s=Math.hypot(p.x-q.x,p.y-q.y)/0.05;if(!minSpeed||s<minSpeed.v)minSpeed={v:+s.toFixed(2),tick:t};}
  const P0=P(k.tick,k.targetId),Pp=P(k.tick,k.player);
  const nextKick=ev.find(e=>e.type==='kick'&&e.tick>(first?.tick??k.tick)&&e.tick>k.tick)??null;
  return {kickTick:k.tick,passer:k.player,receiver:k.targetId,kind:k.kind,speed:+Math.hypot(k.velocity.x,k.velocity.y).toFixed(1),vz:+k.velocity.z.toFixed(2),
   passDecision:pd?{tick:pd.tick,via:pd.via,applyTick:pd.decision.applyTick,target:{x:+pd.decision.target.x.toFixed(1),y:+pd.decision.target.y.toFixed(1)},leadSeconds:lead,reason:pd.decision.reason}:null,
   lengthToTarget:pd&&Pp?+dist(Pp,pd.decision.target).toFixed(1):null,receiverDistAtKick:P0?+Math.hypot(P0.x-F.get(k.tick).ball.x,P0.y-F.get(k.tick).ball.y).toFixed(1):null,
   receiverDecisions:recvDec,receiverMinSpeed:minSpeed,trueClosest:best,
   firstAfter:first?{tick:first.tick,type:first.type,player:first.player??null,team:first.team??null,control:first.control??null,kind:first.kind??null,restart:first.type==='restart_placement'?first.kind:null}:null,
   nextKick:nextKick?{tick:nextKick.tick,player:nextKick.player,team:nextKick.team,kind:nextKick.kind,targetId:nextKick.targetId??null}:null};});
 const key=ev.filter(e=>['goal','restart_placement'].includes(e.type)).map(e=>({tick:e.tick,type:e.type,kind:e.kind??null,team:e.team??null}));
 out.arms[a]={passes,restartsAndGoals:key,controls:ev.filter(e=>e.type==='contact'&&e.control).map(e=>`${e.tick}:${e.player}`).filter((v,i,s)=>s.indexOf(v)===i),endTick:end};}
fs.writeFileSync(outF,JSON.stringify(out,null,1));
console.log('## '+OID+' start '+out.start+' (source '+out.source+')');
for(const [n,v] of Object.entries(out.firstDifference))console.log(` ${n} [${v.arms}] frame ${v.firstFrameDiff} decision ${v.firstDecisionDiff?.key??'-'} kind/target ${v.firstKindOrTargetDiff?J(v.firstKindOrTargetDiff):'-'}`);
for(const a of ARMS){console.log(` [${a}] restarts/goals ${J(out.arms[a].restartsAndGoals)}`);for(const p of out.arms[a].passes)console.log(`   kick ${p.kickTick} ${p.passer}->${p.receiver} ${p.kind} ${p.speed}m/s lead ${p.passDecision?.leadSeconds}s len ${p.lengthToTarget} recvDist ${p.receiverDistAtKick} | closest ${J(p.trueClosest)} minSpd ${J(p.receiverMinSpeed)} | first ${J(p.firstAfter)} | next ${J(p.nextKick)}\n     recv ${p.receiverDecisions.slice(0,14).join(' ')}`);}
