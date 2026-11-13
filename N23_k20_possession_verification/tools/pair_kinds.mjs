// Same state -> base and K20 for H ticks. For every decision of every player record the kind; in the K20 run also
// whether it is a K20 ALTERATION (original choose() on the identical DTO gives another kind). A base-vs-K20 kind
// difference at the same (tick, player) that is NOT an alteration is a SECONDARY branch (the player's own state/
// observation already differs). Also ball events. usage: node pair_kinds.mjs <I17> <k20dir> <stateFile> <H> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,K20,stateF,HS,outF]=process.argv.slice(2);const H=+HS;
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const stdId=await import(path.join(I17,'source/integration_i8_standard/core/pass_build_identity.mjs'));
const {choose:chooseOrig}=await import(path.join(I17,'source/integration_i8_standard/core/decision.mjs'));
const relabel=(t,id)=>{let x=JSON.parse(t);if(x.inner)x=JSON.parse(x.inner);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return JSON.stringify(x);};
const K=await import(path.join(K20,'engine.mjs'));const kId=await import(path.join(K20,'pass_build_identity.mjs'));
const text=fs.readFileSync(stateF,'utf8');const out={};
for(const [label,restore] of Object.entries({base:(t,s)=>Std.restore(relabel(t,stdId),s),k20:(t,s)=>K.MatchEngine.restore(relabel(t,kId),s)})){
 const dec={},ev=[];let eng=null;
 const sink=e=>{if(!eng)return;
  if(e.channel==='event'&&['kick','contact','restart_placement','goal'].includes(e.type))ev.push([e.tick,e.type,e.player??e.taker??null,e.team,e.type==='kick'||!!e.control]);
  if(e.channel==='decision'){let alt=0;if(label==='k20'){try{alt=chooseOrig(e.observation).kind!==e.decision.kind?1:0;}catch{alt=-1;}}
   const b=e.observation.ball,p=e.observation.self;dec[e.tick+':'+e.player]=[e.decision.kind,alt,b?+Math.hypot(p.x-b.x,p.y-b.y).toFixed(1):null];}};
 eng=restore(text,sink);const t0=eng.tick;
 for(let i=0;i<H&&!eng.finished;i++)eng.step();
 out[label]={t0,dec,ev};}
fs.writeFileSync(outF,JSON.stringify(out));
