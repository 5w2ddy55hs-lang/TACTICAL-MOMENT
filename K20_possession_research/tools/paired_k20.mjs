// Same-opportunity paired evaluation for K20. Unchanged standard match; triggers:
//  'change' = a control/kick by the other team (possession change; trigger team = new possessor)
//  'free'   = ball untouched >= 20 ticks in play and some outfield player within 2.1 m (D-1 generalisation)
// At each trigger save state, run standard and K20 (research-only transplant) for H ticks.
// usage: node paired_k20.mjs <I17> <branch> <seed> <maxTicks> <H> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,seedS,maxS,HS,outF]=process.argv.slice(2);const H=+HS;
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const {MatchEngine:Br}=await import(path.join(BR,'engine.mjs'));const id=await import(path.join(BR,'pass_build_identity.mjs'));
const transplant=t=>{const x=JSON.parse(t);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return JSON.stringify(x);};
const d2=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
let lastTeam=null,lastTouchTick=-1,trig=null;
const main=g.create('standard',{seed:+seedS,zonalDefence:false},ev=>{if(ev.channel!=='event')return;
 if(ev.type==='kick'||ev.type==='contact'){lastTouchTick=ev.tick;if(ev.type==='kick'||ev.control){if(lastTeam&&ev.team!==lastTeam&&!trig)trig={type:'change',t:ev.tick,team:ev.team,player:ev.player};lastTeam=ev.team;}}
 if(ev.type==='restart_placement'){lastTeam=null;lastTouchTick=ev.tick;}});
function follow(E,k,text){const acts=[];let restart=null;const goals=[];const cond={A:0,B:0};const latest={};
 const sink=ev=>{if(ev.channel==='event'){if(ev.type==='kick'||ev.type==='contact')acts.push({t:ev.tick,p:ev.player,team:ev.team,kick:ev.type==='kick',kind:ev.kind,ctrl:ev.type==='kick'||!!ev.control});if(ev.type==='restart_placement'&&!restart)restart={t:ev.tick,kind:ev.kind,team:ev.team};if(ev.type==='goal')goals.push({t:ev.tick,team:ev.team,ownGoal:ev.lastTeam&&ev.lastTeam!==ev.team});}
  if(ev.channel==='decision'){latest[ev.player]=ev.decision;}};
 const e=E.restore(text,sink);const s0=e.physicalSnapshot();const x0=Object.fromEntries(s0.players.map(p=>[p.id,p]));
 const dirOf=t=>s0.players.find(p=>p.id===t+'00').x<52.5?1:-1;let at40=null,at60=null;
 for(let i=0;i<H&&!e.finished;i++){e.step();if(i===39)at40=e.physicalSnapshot();if(i===59)at60=e.physicalSnapshot();if(restart)break;}
 const ctrl=acts.filter(a=>a.ctrl);const first=ctrl[0]??null;
 const possAt=t=>{const c=ctrl.filter(a=>a.t<=k.t+t);if(restart&&restart.t<=k.t+t&&(!c.length||restart.t>=c.at(-1).t))return 'restart:'+restart.team;return c.length?c.at(-1).team:'none';};
 // attack switch of the trigger team: mean forward movement of its non-ball outfield players over 2 s (real motion)
 let fwd=null;if(at40&&k.team){const T=k.team,D=dirOf(T);const ids=s0.players.filter(p=>p.id[0]===T&&!p.id.endsWith('00')&&d2(p,s0.ball)>5).map(p=>p.id);if(ids.length)fwd=+(ids.reduce((s,i)=>s+(at40.players.find(p=>p.id===i).x-x0[i].x)*D,0)/ids.length).toFixed(2);}
 // defenders goal-side at +3 s for the non-trigger team
 let gs=null;if(at60&&k.team){const O=k.team==='A'?'B':'A';const gx=dirOf(O)===1?0:105;gs=at60.players.filter(p=>p.id[0]===O&&!p.id.endsWith('00')&&Math.abs(p.x-gx)<Math.abs(at60.ball.x-gx)).length;}
 return {firstCtrl:first?{dt:first.t-k.t,team:first.team,p:first.p}:null,poss3:possAt(60),poss6:possAt(120),restart:restart?restart.kind+':'+restart.team:null,shots:{A:acts.filter(a=>a.kick&&a.kind==='shoot'&&a.team==='A').length,B:acts.filter(a=>a.kick&&a.kind==='shoot'&&a.team==='B').length},goals,triggerTeamFwd2s:fwd,otherGoalSide3s:gs};}
const rows=[];const t0=Date.now();let lastFree=-1e9;
while(main.tick<+maxS&&!main.finished){trig=null;main.step();const st=main.physicalSnapshot();if(st.phase!=='play')continue;
 if(!trig&&main.tick-lastTouchTick>=20&&main.tick-lastFree>=100){const near=st.players.filter(p=>!p.id.endsWith('00')&&d2(p,st.ball)<2.1);if(near.length){trig={type:'free',t:main.tick,team:null,near:near.map(p=>p.id)};lastFree=main.tick;}}
 if(!trig)continue;const text=main.save();const k=trig;rows.push({k,base:follow(Std,k,text),k20:follow({restore:(t,s)=>Br.restore(transplant(t),s)},k,text)});}
const by=type=>rows.filter(r=>r.k.type===type);
const cnt=(L,f)=>({base:L.filter(r=>f(r.base,r.k)).length,k20:L.filter(r=>f(r.k20,r.k)).length});
const mean=(L,f)=>{const a=L.map(r=>f(r.base)).filter(v=>v!==null),b=L.map(r=>f(r.k20)).filter(v=>v!==null);return {base:+(a.reduce((s,v)=>s+v,0)/Math.max(1,a.length)).toFixed(3),k20:+(b.reduce((s,v)=>s+v,0)/Math.max(1,b.length)).toFixed(3)};};
const diff=L=>L.filter(r=>JSON.stringify(r.base)!==JSON.stringify(r.k20)).length;
const summary={seed:+seedS,ticks:main.tick,H,wallS:Math.round((Date.now()-t0)/1000),
 change:{n:by('change').length,differs:diff(by('change')),triggerTeamHas6s:cnt(by('change'),(x,k)=>x.poss6===k.team||x.poss6==='restart:'+k.team),triggerTeamHas3s:cnt(by('change'),(x,k)=>x.poss3===k.team||x.poss3==='restart:'+k.team),triggerTeamShot:cnt(by('change'),(x,k)=>x.shots[k.team]>0),otherTeamShot:cnt(by('change'),(x,k)=>x.shots[k.team==='A'?'B':'A']>0),goalsFor:cnt(by('change'),(x,k)=>x.goals.some(g=>g.team===k.team)),goalsAgainst:cnt(by('change'),(x,k)=>x.goals.some(g=>g.team!==k.team)),ownGoals:cnt(by('change'),x=>x.goals.some(g=>g.ownGoal)),triggerTeamFwd2s:mean(by('change'),x=>x.triggerTeamFwd2s),otherGoalSide3s:mean(by('change'),x=>x.otherGoalSide3s)},
 free:{n:by('free').length,differs:diff(by('free')),collectedWithin3s:cnt(by('free'),x=>x.firstCtrl&&x.firstCtrl.dt<=60),collectedWithin6s:cnt(by('free'),x=>!!x.firstCtrl),wentDead:cnt(by('free'),x=>!!x.restart),shots:cnt(by('free'),x=>x.shots.A+x.shots.B>0),goals:cnt(by('free'),x=>x.goals.length>0),ownGoals:cnt(by('free'),x=>x.goals.some(g=>g.ownGoal)),meanCollectS:mean(by('free'),x=>x.firstCtrl?x.firstCtrl.dt/20:null)}};
fs.writeFileSync(outF,JSON.stringify({summary,rows}));console.log(JSON.stringify(summary));
