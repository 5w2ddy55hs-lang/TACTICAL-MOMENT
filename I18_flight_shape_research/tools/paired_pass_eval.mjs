// Same-opportunity paired evaluation: run an unchanged standard match; right after every
// normal 'pass' kick, save the state and run BOTH engines (standard, I18 via research-only
// transplant) from that identical state for H ticks. Compare first touch, control,
// team continuation, opponent shot, and shape movement on the same opportunity.
// usage: node paired_pass_eval.mjs <I17> <branchDir> <seed> <maxTicks> <H> <out.json> [startTick]
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,seedS,maxS,HS,outF,startS]=process.argv.slice(2);const H=+HS;
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const {MatchEngine:Br}=await import(path.join(BR,'engine.mjs'));const id=await import(path.join(BR,'pass_build_identity.mjs'));
const transplant=t=>{const x=JSON.parse(t);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return JSON.stringify(x);};
let pending=null;
const main=g.create('standard',{seed:+seedS,zonalDefence:false},ev=>{if(ev.channel==='event'&&ev.type==='kick'&&ev.kind==='pass')pending={t:ev.tick,team:ev.team,passer:ev.player,target:ev.targetId};});
function follow(E,k,saveText){const acts=[];const rw=[];
 const sink=ev=>{if(ev.channel==='event'&&(ev.type==='kick'||ev.type==='contact'))acts.push({t:ev.tick,p:ev.player,team:ev.team,kick:ev.type==='kick',kind:ev.kind,ctrl:ev.type==='kick'||!!ev.control});
  if(ev.channel==='decision'&&ev.decision.reason==='I18_witnessed_teammate_kick_uncontested')rw.push({t:ev.tick,p:ev.player});};
 const e=E.restore(saveText,sink);const s0=e.exportState();const D=s0.players.find(p=>p.id===k.team+'00').x<52.5?1:-1;
 const mates=s0.players.filter(p=>p.team===k.team&&p.id!==k.team+'00'&&p.id!==k.passer&&p.id!==k.target).map(p=>p.id);
 const x0=Object.fromEntries(s0.players.map(p=>[p.id,p.x]));let firstT=null,deadT=null,xFirst=null,phaseDeadKind=null;
 for(let i=0;i<H&&!e.finished;i++){e.step();const st=e.physicalSnapshot();
  if(deadT===null&&st.phase!=='play'){deadT=e.tick;}
  if(firstT===null){const f=acts.find(a=>!(a.p===k.passer&&a.t-k.t<=3));if(f||deadT!==null){firstT=e.tick;xFirst=Object.fromEntries(st.players.map(p=>[p.id,p.x]));}}}
 const f=acts.find(a=>!(a.p===k.passer&&a.t-k.t<=3));
 let outcome='none';if(deadT!==null&&(!f||deadT<=f.t))outcome='out';else if(f)outcome=f.p===k.target?(f.ctrl?'target_control':'target_no_control'):f.team===k.team?'teammate':'opponent';
 const opp=k.team==='A'?'B':'A';const lastCtrl=[...acts].reverse().find(a=>a.ctrl);
 const fwd=xFirst?mates.reduce((s,m)=>s+(xFirst[m]-x0[m])*D,0)/mates.length:null;
 const nextAfterFirst=f?acts.find(a=>a.t>f.t&&(a.p!==f.p||a.kick)):null;
 return {outcome,firstT:f?.t??deadT,firstP:f?.p??null,matesFwd:fwd===null?null:+fwd.toFixed(2),teamHasBallAtEnd:deadT===null&&lastCtrl?lastCtrl.team===k.team:null,oppShot:acts.some(a=>a.kick&&a.kind==='shoot'&&a.team===opp),ownShot:acts.some(a=>a.kick&&a.kind==='shoot'&&a.team===k.team),receiverNext:outcome==='target_control'&&nextAfterFirst?(nextAfterFirst.p===f.p?nextAfterFirst.kind:(nextAfterFirst.team===k.team?'teammate':'opponent')):null,dead:deadT!==null,rewrites:rw.filter(x=>x.p[0]===k.team&&x.t<=(f?.t??deadT??1e12)).length,rewritePlayers:[...new Set(rw.filter(x=>x.p[0]===k.team&&x.t<=(f?.t??deadT??1e12)).map(x=>x.p))],rewritesAfterFirstTouchAnyTeam:rw.filter(x=>x.t>(f?.t??deadT??1e12)).length};}
const rows=[];const t0=Date.now();const start=+(startS||0);
while(main.tick<+maxS&&!main.finished){pending=null;main.step();
 if(pending&&main.tick>=start){const st=main.physicalSnapshot();if(st.phase!=='play')continue;
  const text=main.save();const k=pending;const a=follow(Std,k,text);const b=follow({restore:(t,s)=>Br.restore(transplant(t),s)},k,text);
  rows.push({kick:k,base:a,i18:b});}}
const changed=rows.filter(r=>r.i18.rewrites>0);
const cmp=(L,f)=>({base:L.filter(r=>f(r.base)).length,i18:L.filter(r=>f(r.i18)).length});
const summary={seed:+seedS,ticks:main.tick,H,passes:rows.length,withRewrites:changed.length,wallS:Math.round((Date.now()-t0)/1000),
 identicalOutcomeShare:+(rows.filter(r=>JSON.stringify({...r.base,rewritesAfterFirstTouchAnyTeam:0})===JSON.stringify({...r.i18,rewrites:0,rewritePlayers:[],rewritesAfterFirstTouchAnyTeam:0})).length/rows.length).toFixed(3),
 onRewritten:{n:changed.length,target_control:cmp(changed,x=>x.outcome==='target_control'),opponent:cmp(changed,x=>x.outcome==='opponent'),teammate:cmp(changed,x=>x.outcome==='teammate'),out:cmp(changed,x=>x.outcome==='out'),teamHasBallAtEnd:cmp(changed,x=>x.teamHasBallAtEnd===true),oppShot:cmp(changed,x=>x.oppShot),ownShot:cmp(changed,x=>x.ownShot),sameOutcome:changed.filter(r=>r.base.outcome===r.i18.outcome).length,
  matesFwdMean:{base:+(changed.reduce((s,r)=>s+(r.base.matesFwd??0),0)/Math.max(1,changed.length)).toFixed(2),i18:+(changed.reduce((s,r)=>s+(r.i18.matesFwd??0),0)/Math.max(1,changed.length)).toFixed(2)}}};
fs.writeFileSync(outF,JSON.stringify({summary,rows}));console.log(JSON.stringify(summary));
