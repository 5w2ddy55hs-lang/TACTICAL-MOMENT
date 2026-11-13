// O24 targeted re-run of ONE stored same-opportunity row of paired_multi.mjs (L21 pm3, trigger type 'change').
// Rebuilds the unchanged standard main match from the seed with the SAME trigger rule (control/kick by the other team,
// reset on restart_placement), saves the state at the requested trigger exactly where paired_multi saved it (after the
// step that produced the trigger), records SHA-256 + stateHash of that state (the original run did not record them),
// then follows base / K20 / L21 from it for H ticks with the ORIGINAL stop-at-first-restart rule and checks that every
// stored label (poss3, poss6, restart, goals) reproduces. It also lists, for the L21 run, every "yield" (L21 decision kind
// differs from the K20 choose() on the identical DTO) before the first restart, and all ball events.
// usage: node rerun_change.mjs <I17> <k20dir> <l21dir> <seed> <t> <team> <storedRowsFile> <H> <outDir>
import fs from 'node:fs';import path from 'node:path';import {createHash} from 'node:crypto';
const [I17,K20,L21,seedS,tS,team,rowsF,HS,outDir]=process.argv.slice(2);const H=+HS,T=+tS;
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const sha=s=>createHash('sha256').update(s).digest('hex');
const br=async dir=>{const {MatchEngine}=await import(path.join(dir,'engine.mjs'));const id=await import(path.join(dir,'pass_build_identity.mjs'));
 return (t,s)=>{const x=JSON.parse(t);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return MatchEngine.restore(JSON.stringify(x),s);};};
const {choose:chooseK20}=await import(path.join(K20,'decision.mjs'));
const engines={base:(t,s)=>Std.restore(t,s),k20:await br(K20),l21:await br(L21)};
let lastTeam=null,trig=null;
const main=g.create('standard',{seed:+seedS,zonalDefence:false},ev=>{if(ev.channel!=='event')return;
 if(ev.type==='kick'||ev.type==='contact'){if(ev.type==='kick'||ev.control){if(lastTeam&&ev.team!==lastTeam&&!trig)trig={type:'change',t:ev.tick,team:ev.team,player:ev.player};lastTeam=ev.team;}}
 if(ev.type==='restart_placement'){lastTeam=null;}});
let text=null,k=null;
while(!main.finished&&main.tick<T+5){trig=null;main.step();const st=main.physicalSnapshot();if(st.phase!=='play')continue;if(trig&&trig.t===T&&trig.team===team){k=trig;text=main.save();break;}}
if(!text)throw Error('trigger not found');
const stored=JSON.parse(fs.readFileSync(rowsF)).rows.find(r=>r.k.t===T&&r.k.team===team);
const res={seed:+seedS,trigger:k,storedTrigger:stored.k,stateSha256:sha(text),stateHash:main.stateHash(),node:process.version,engines:{}};
fs.mkdirSync(outDir,{recursive:true});fs.writeFileSync(path.join(outDir,`state_${seedS}_${T}_${team}.json`),text);
for(const [lb,restore] of Object.entries(engines)){
 const acts=[],evs=[],goals=[],yields=[];let restart=null,eng=null;
 const sink=ev=>{if(!eng)return;
  if(ev.channel==='event'){if(ev.type==='kick'||ev.type==='contact')acts.push({t:ev.tick,p:ev.player,team:ev.team,ctrl:ev.type==='kick'||!!ev.control});
   if(['kick','contact','restart_placement','goal'].includes(ev.type))evs.push([ev.tick-k.t,ev.type,ev.kind??null,ev.player??ev.taker??null,ev.team,ev.type==='kick'||!!ev.control]);
   if(ev.type==='restart_placement'&&!restart)restart={t:ev.tick,kind:ev.kind,team:ev.team};if(ev.type==='goal')goals.push({t:ev.tick,team:ev.team,own:!!ev.lastTeam&&ev.lastTeam!==ev.team});}
  if(ev.channel==='decision'&&lb==='l21'&&!restart){let kd;try{kd=chooseK20(ev.observation);}catch{return;}if(kd.kind!==ev.decision.kind){const o=ev.observation,b=o.ball,p=o.self;yields.push([ev.tick-k.t,ev.player,kd.kind+'->'+ev.decision.kind,b?+Math.hypot(p.x-b.x,p.y-b.y).toFixed(1):null]);}}};
 eng=restore(text,sink);
 for(let i=0;i<H&&!eng.finished;i++){eng.step();if(restart)break;}
 const ctrl=acts.filter(a=>a.ctrl);const possAt=t=>{const c=ctrl.filter(a=>a.t<=k.t+t);if(restart&&restart.t<=k.t+t&&(!c.length||restart.t>=c.at(-1).t))return 'restart:'+restart.team;return c.length?c.at(-1).team:'none';};
 const got={poss3:possAt(60),poss6:possAt(120),restart:restart?restart.kind+':'+restart.team:null,goals};
 const st=stored[lb];const ok=got.poss3===st.poss3&&got.poss6===st.poss6&&got.restart===st.restart&&JSON.stringify(got.goals)===JSON.stringify(st.goals);
 res.engines[lb]={reproduced:ok,got,stored:{poss3:st.poss3,poss6:st.poss6,restart:st.restart,goals:st.goals},events:evs,l21YieldsBeforeRestart:lb==='l21'?yields:undefined};}
fs.writeFileSync(path.join(outDir,`rerun_${seedS}_${T}_${team}.json`),JSON.stringify(res,null,1));
console.log(JSON.stringify({seed:+seedS,t:T,team,trigger:k,stateSha256:res.stateSha256,reproduced:Object.fromEntries(Object.entries(res.engines).map(([a,b])=>[a,b.reproduced]))}));
