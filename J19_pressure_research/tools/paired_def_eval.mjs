// Same-opportunity paired evaluation of defensive episodes. Run an unchanged standard match; at
// every possession change (control/kick by the other team), save the state and run BOTH engines
// (standard, J19 via research-only transplant: only outer identity labels rewritten) for H ticks.
// Defending team = the team that just lost the ball.
// usage: node paired_def_eval.mjs <I17> <branchDir> <seed> <maxTicks> <H> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,seedS,maxS,HS,outF]=process.argv.slice(2);const H=+HS;
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const {MatchEngine:Br}=await import(path.join(BR,'engine.mjs'));const id=await import(path.join(BR,'pass_build_identity.mjs'));
const transplant=t=>{const x=JSON.parse(t);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return JSON.stringify(x);};
const BD=new Set(['press','intercept','receive']);
let lastTeam=null,trigger=null;
const main=g.create('standard',{seed:+seedS,zonalDefence:false},ev=>{if(ev.channel==='event'&&(ev.type==='kick'||(ev.type==='contact'&&ev.control))){if(lastTeam&&ev.team!==lastTeam&&!trigger)trigger={t:ev.tick,team:ev.team,player:ev.player};lastTeam=ev.team;}if(ev.channel==='event'&&ev.type==='restart_placement')lastTeam=null;});
function follow(E,k,text){const def=k.team==='A'?'B':'A';const acts=[];const latest={};let j19=0;const j19p=new Set();let restart=null;
 const sink=ev=>{if(ev.channel==='event'){if(ev.type==='kick'||ev.type==='contact')acts.push({t:ev.tick,p:ev.player,team:ev.team,kick:ev.type==='kick',kind:ev.kind,ctrl:ev.type==='kick'||!!ev.control});if(ev.type==='restart_placement'&&!restart)restart={t:ev.tick,kind:ev.kind,team:ev.team};if(ev.type==='goal')acts.push({t:ev.tick,goal:true,team:ev.team});}
  if(ev.channel==='decision'){latest[ev.player]=ev.decision;if(String(ev.decision.reason).startsWith('J19_')&&ev.player[0]===def){j19++;j19p.add(ev.player);}}};
 const e=E.restore(text,sink);const s0=e.physicalSnapshot();const gk=s0.players.find(p=>p.id===def+'00');const goal=gk.x<52.5?0:105;const b0=Math.abs(s0.ball.x-goal);
 let carryTicks=0,carryNoBD=0,carryNoBDwithYield=0,minGoal=b0,maxBD=0,ge3=0,same3=0,noPress=0,playTicks=0,regainT=null,firstGS3=null,end=null;
 for(let i=0;i<H&&!e.finished;i++){e.step();const s=e.physicalSnapshot();
  if(regainT===null){const r=acts.find(a=>a.team===def&&a.ctrl&&!a.goal);if(r)regainT=r.t;}
  if(restart&&end===null)end=restart.t;if(regainT!==null&&end===null)end=regainT;if(end!==null)break;
  if(s.phase!=='play')continue;playTicks++;const b=s.ball;minGoal=Math.min(minGoal,Math.abs(b.x-goal));
  const me=s.players.filter(p=>p.id[0]===def&&!p.id.endsWith('00'));const bd=me.filter(p=>BD.has(latest[p.id]?.kind));maxBD=Math.max(maxBD,bd.length);if(bd.length>=3)ge3++;
  const tg=bd.map(p=>latest[p.id].target||{x:0,y:0});if(Math.max(0,...tg.map(v=>tg.filter(u=>Math.hypot(u.x-v.x,u.y-v.y)<2).length))>=3)same3++;
  // "nobody pressing": no defender within 6 m of the ball that is either goal-side or closing on it (truth geometry, audit only)
  const pressing=me.some(p=>{const d=Math.hypot(p.x-b.x,p.y-b.y);if(d>6)return false;const gs=Math.abs(p.x-goal)<Math.abs(b.x-goal);const cl=d>0?((b.x-p.x)*p.vx+(b.y-p.y)*p.vy)/d:0;return gs||cl>1;});if(!pressing)noPress++;
  const carry=s.players.some(p=>p.id[0]===k.team&&Math.hypot(p.x-b.x,p.y-b.y)<2.1)&&!me.some(p=>Math.hypot(p.x-b.x,p.y-b.y)<2.1);
  if(carry){carryTicks++;const nearBD=bd.some(p=>Math.hypot(p.x-b.x,p.y-b.y)<15);if(!nearBD){carryNoBD++;if(me.some(p=>String(latest[p.id]?.reason).includes('yield')))carryNoBDwithYield++;}}
  if(firstGS3===null&&me.some(p=>Math.abs(p.x-goal)<Math.abs(b.x-goal)&&Math.hypot(p.x-b.x,p.y-b.y)<3))firstGS3=e.tick;}
 const oppShot=acts.some(a=>a.kick&&a.kind==='shoot'&&a.team===k.team),oppGoal=acts.some(a=>a.goal&&a.team===k.team),oppPasses=acts.filter(a=>a.kick&&a.kind==='pass'&&a.team===k.team).length;
 const regainedByRestart=restart&&restart.team===def&&(regainT===null||restart.t<regainT);
 return {regain:regainT!==null&&(!restart||regainT<=restart.t)?(regainT-k.t)/20:null,regainedByRestart:!!regainedByRestart,restart:restart?restart.kind+':'+restart.team:null,advance:+(b0-minGoal).toFixed(1),maxBD,ge3,same3,noPress,playTicks,secsGS3:firstGS3===null?null:(firstGS3-k.t)/20,oppShot,oppGoal,oppPasses,carryTicks,carryNoBD,carryNoBDwithYield,j19,j19Players:[...j19p]};}
const rows=[];const t0=Date.now();
while(main.tick<+maxS&&!main.finished){trigger=null;main.step();if(!trigger)continue;const st=main.physicalSnapshot();if(st.phase!=='play')continue;
 const text=main.save();const k=trigger;rows.push({k,base:follow(Std,k,text),j19:follow({restore:(t,s)=>Br.restore(transplant(t),s)},k,text)});}
const ch=rows.filter(r=>r.j19.j19>0);
const agg=(L,f)=>({base:+L.reduce((s,r)=>s+f(r.base),0).toFixed(2),j19:+L.reduce((s,r)=>s+f(r.j19),0).toFixed(2)});
const summary={seed:+seedS,ticks:main.tick,H,episodes:rows.length,withJ19:ch.length,wallS:Math.round((Date.now()-t0)/1000),
 onChanged:{n:ch.length,regained:agg(ch,x=>x.regain!==null||x.regainedByRestart?1:0),regainedByPlay:agg(ch,x=>x.regain!==null?1:0),oppShot:agg(ch,x=>x.oppShot?1:0),oppGoal:agg(ch,x=>x.oppGoal?1:0),advanceSum:agg(ch,x=>x.advance),ge3Ticks:agg(ch,x=>x.ge3),same3Ticks:agg(ch,x=>x.same3),noPressTicks:agg(ch,x=>x.noPress),playTicks:agg(ch,x=>x.playTicks),maxBDsum:agg(ch,x=>x.maxBD),carryTicks:agg(ch,x=>x.carryTicks),carryNoBallDirectedWithin15m:agg(ch,x=>x.carryNoBD),carryNoBDwhileYieldActive:agg(ch,x=>x.carryNoBDwithYield),ge3PerPlayTick:{base:+(ch.reduce((s,r)=>s+r.base.ge3,0)/Math.max(1,ch.reduce((s,r)=>s+r.base.playTicks,0))).toFixed(3),j19:+(ch.reduce((s,r)=>s+r.j19.ge3,0)/Math.max(1,ch.reduce((s,r)=>s+r.j19.playTicks,0))).toFixed(3)}}};
fs.writeFileSync(outF,JSON.stringify({summary,rows}));console.log(JSON.stringify(summary));
