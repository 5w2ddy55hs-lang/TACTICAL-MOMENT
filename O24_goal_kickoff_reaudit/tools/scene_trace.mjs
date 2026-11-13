// O24: trace one saved opportunity in base / K20 / L21 for H ticks: every 4 ticks the ball (position, speed, distance to
// each goal line centre), and for the trigger team's outfield players their decision kind + reason, own-view distance to
// the ball (goalkeeper included), and in L21 whether the decision is a yield (L21 kind differs from K20 choose() on the identical DTO).
// usage: node scene_trace.mjs <I17> <k20dir> <l21dir> <state.json> <team> <H> <out.txt>
import fs from 'node:fs';import path from 'node:path';
const [I17,K20,L21,stateF,team,HS,outF]=process.argv.slice(2);const H=+HS;
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const br=async dir=>{const {MatchEngine}=await import(path.join(dir,'engine.mjs'));const id=await import(path.join(dir,'pass_build_identity.mjs'));
 return (t,s)=>{const x=JSON.parse(t);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return MatchEngine.restore(JSON.stringify(x),s);};};
const {choose:chooseK20}=await import(path.join(K20,'decision.mjs'));
const text=fs.readFileSync(stateF,'utf8');const lines=[];
for(const [lb,restore] of Object.entries({base:(t,s)=>Std.restore(t,s),k20:await br(K20),l21:await br(L21)})){
 let eng=null,t0=0;const dec={};
 const sink=ev=>{if(!eng)return;if(ev.channel==='decision'&&ev.player[0]===team){const o=ev.observation,b=o.ball,p=o.self;let y='';if(lb==='l21'){try{y=chooseK20(o).kind!==ev.decision.kind?' YIELD':'';}catch{}}
   dec[ev.player]=`${ev.decision.kind}${y}(${b?Math.hypot(p.x-b.x,p.y-b.y).toFixed(1):'-'})`;}
  if(ev.channel==='event'&&['kick','contact','goal','restart_placement'].includes(ev.type))lines.push(`${lb} +${ev.tick-t0} EVENT ${ev.type}${ev.kind?':'+ev.kind:''} ${ev.player??ev.taker??''} ${ev.team??''}`);};
 eng=restore(text,sink);t0=eng.tick;
 for(let i=0;i<H&&!eng.finished;i++){eng.step();if(i%4===3){const s=eng.physicalSnapshot();const b=s.ball;
   lines.push(`${lb} +${i+1} ball(${b.x.toFixed(1)},${b.y.toFixed(1)}) v=${Math.hypot(b.vx,b.vy).toFixed(1)} ph=${s.phase} | `+Object.keys(dec).sort().map(k=>k+':'+dec[k]).join(' '));}}}
fs.writeFileSync(outF,lines.join('\n')+'\n');console.log(outF,lines.length);
