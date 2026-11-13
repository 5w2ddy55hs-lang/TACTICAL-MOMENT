// Same-opportunity paired evaluation for N engines (standard + isolated branches via research-only transplant).
// Triggers on an UNCHANGED standard match:
//   change : control/kick by the other team (trigger team = new possessor)
//   free   : ball untouched >=20 ticks in play, some outfield player within 2.1 m
//   list   : explicit ticks from a JSON file [{t,team,label}] (state saved BEFORE that tick's decisions)
// Per run: possession at 3/6 s, regain by the losing side within 2/6 s, shots/goals/own goals,
// same-team body-contact episodes with the involved players' current decisions and whether each decision
// was altered relative to the ORIGINAL choose() on the identical DTO (attribution), attack-shape decisions and
// real forward movement of the trigger team over 1/2 s.
// usage: node paired_multi.mjs <I17> <seed> <maxTicks> <H> <out.json> <triggers:change,free|list:file> <label=branchDir>...
import fs from 'node:fs';import path from 'node:path';
const [I17,seedS,maxS,HS,outF,trigSpec,mainSpec,...engSpecs]=process.argv.slice(2);const H=+HS;
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const {choose:chooseOrig}=await import(path.join(I17,'source/integration_i8_standard/core/decision.mjs'));
const stdId=await import(path.join(I17,'source/integration_i8_standard/core/pass_build_identity.mjs'));
const engines=[{label:'base',restore:(t,s)=>{const x=JSON.parse(t);x.schema=stdId.PASS_SAVE_SCHEMA;x.engine=stdId.PASS_ENGINE;x.buildSha256=stdId.PASS_BUILD_SHA256;return Std.restore(JSON.stringify(x),s);}}];
for(const spec of engSpecs){const [label,dir]=spec.split('=');const m=await import(path.join(dir,'engine.mjs'));const id=await import(path.join(dir,'pass_build_identity.mjs'));
 engines.push({label,restore:(t,s)=>{const x=JSON.parse(t);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return m.MatchEngine.restore(JSON.stringify(x),s);}});}
const d2=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const ATT=new Set(['support','advance_support','cover_exchange']);
const useChange=trigSpec.includes('change'),useFree=trigSpec.includes('free');
const listT=trigSpec.startsWith('list:')?JSON.parse(fs.readFileSync(trigSpec.slice(5))):null;const listMap=new Map((listT||[]).map(x=>[x.t,x]));
let lastTeam=null,lastTouchTick=-1,trig=null;
const {MatchEngine:MainE}=await import(path.join(mainSpec.split('=')[1],'engine.mjs'));
const main=new MainE({seed:+seedS,zonalDefence:false},ev=>{if(ev.channel!=='event')return;
 if(ev.type==='kick'||ev.type==='contact'){lastTouchTick=ev.tick;if(ev.type==='kick'||ev.control){if(useChange&&lastTeam&&ev.team!==lastTeam&&!trig)trig={type:'change',t:ev.tick,team:ev.team,player:ev.player};lastTeam=ev.team;}}
 if(ev.type==='restart_placement'){lastTeam=null;lastTouchTick=ev.tick;}});
function follow(E,k,text){const acts=[];let restart=null;const goals=[];const cur={};const bodyRows=[];let attDec={1:0,2:0},altered=0,decs=0;
 const sink=ev=>{if(ev.channel==='event'){if(ev.type==='kick'||ev.type==='contact')acts.push({t:ev.tick,p:ev.player,team:ev.team,kick:ev.type==='kick',kind:ev.kind,ctrl:ev.type==='kick'||!!ev.control});if(ev.type==='restart_placement'&&!restart)restart={t:ev.tick,kind:ev.kind,team:ev.team};if(ev.type==='goal')goals.push({t:ev.tick,team:ev.team,own:!!ev.lastTeam&&ev.lastTeam!==ev.team});}
  if(ev.channel==='decision'){const o=ev.observation;let alt=false;try{const a=chooseOrig(o);alt=a.kind!==ev.decision.kind&&!(ev.decision.kind==='dribble'||ev.decision.kind==='pass');}catch{}
   cur[ev.player]={kind:ev.decision.kind,alt};decs++;if(alt)altered++;
   if(k.team&&ev.player[0]===k.team&&!ev.player.endsWith('00')&&ATT.has(ev.decision.kind)){const dt=ev.tick-k.t;if(dt<=20)attDec[1]++;if(dt<=40)attDec[2]++;}}
  if(ev.channel==='body_contact'){const [a,b]=ev.players;if(a[0]===b[0])bodyRows.push({t:ev.tick,pair:[a,b].sort().join('-'),team:a[0],ka:cur[a]?.kind??null,kb:cur[b]?.kind??null,alt:!!(cur[a]?.alt||cur[b]?.alt)});}};
 const e=E.restore(text,sink);const s0=e.physicalSnapshot();const x0=Object.fromEntries(s0.players.map(p=>[p.id,p]));let s20=null,s40=null;
 for(let i=0;i<H&&!e.finished;i++){e.step();if(i===19)s20=e.physicalSnapshot();if(i===39)s40=e.physicalSnapshot();if(restart)break;}
 // merge body-contact rows into episodes per pair (gap<=3 ticks)
 const eps=[];const lastBy={};for(const r of bodyRows){const L=lastBy[r.pair];if(L&&r.t-L.end<=3){L.end=r.t;L.alt=L.alt||r.alt;continue;}const E2={...r,end:r.t};eps.push(E2);lastBy[r.pair]=E2;}
 const ctrl=acts.filter(a=>a.ctrl);const possAt=t=>{const c=ctrl.filter(a=>a.t<=k.t+t);if(restart&&restart.t<=k.t+t&&(!c.length||restart.t>=c.at(-1).t))return 'restart:'+restart.team;return c.length?c.at(-1).team:'none';};
 const other=k.team?(k.team==='A'?'B':'A'):null;const reg=other?ctrl.find(a=>a.team===other):null;
 const fwd=s=>{if(!s||!k.team)return null;const D=s0.players.find(p=>p.id===k.team+'00').x<52.5?1:-1;const ids=s0.players.filter(p=>p.id[0]===k.team&&!p.id.endsWith('00')&&d2(p,s0.ball)>5).map(p=>p.id);return ids.length?+(ids.reduce((q,i)=>q+(s.players.find(p=>p.id===i).x-x0[i].x)*D,0)/ids.length).toFixed(2):null;};
 const pairKinds={};for(const ep of eps){const key=[ep.ka,ep.kb].sort().join('+');pairKinds[key]=(pairKinds[key]||0)+1;}
 return {poss3:possAt(60),poss6:possAt(120),regain2s:!!reg&&reg.t-k.t<=40,regain6s:!!reg,restart:restart?restart.kind+':'+restart.team:null,firstCtrl:ctrl[0]?{dt:ctrl[0].t-k.t,team:ctrl[0].team}:null,
  shots:{A:acts.filter(a=>a.kick&&a.kind==='shoot'&&a.team==='A').length,B:acts.filter(a=>a.kick&&a.kind==='shoot'&&a.team==='B').length},goals,
  sameTeamContactEps:eps.length,sameTeamContactEpsAltered:eps.filter(x=>x.alt).length,contactKinds:pairKinds,alteredDecisions:altered,decisions:decs,
  attDec1s:attDec[1],attDec2s:attDec[2],fwd1s:fwd(s20),fwd2s:fwd(s40)};}
const rows=[];const t0=Date.now();let lastFree=-1e9;
while(main.tick<+maxS&&!main.finished){
 if(listT&&listMap.has(main.tick)){const k={type:'list',...listMap.get(main.tick)};const text=main.save();const r={k};for(const E of engines)r[E.label]=follow(E,k,text);rows.push(r);}
 trig=null;main.step();if(listT)continue;const st=main.physicalSnapshot();if(st.phase!=='play')continue;
 if(useFree&&!trig&&main.tick-lastTouchTick>=20&&main.tick-lastFree>=100){const near=st.players.filter(p=>!p.id.endsWith('00')&&d2(p,st.ball)<2.1);if(near.length){trig={type:'free',t:main.tick,team:null};lastFree=main.tick;}}
 if(!trig)continue;const text=main.save();const k=trig;const r={k};for(const E of engines)r[E.label]=follow(E,k,text);rows.push(r);}
const labels=engines.map(E=>E.label);const sum={};
for(const type of ['change','free','list']){const L=rows.filter(r=>r.k.type===type);if(!L.length)continue;const o={n:L.length};
 for(const lb of labels){const S=L.map(r=>r[lb]);const c=f=>S.filter(f).length;const s=f=>+S.reduce((a,x)=>a+(f(x)??0),0).toFixed(2);
  o[lb]={triggerTeamHas6s:L.filter(r=>r[lb].poss6===r.k.team||r[lb].poss6==='restart:'+r.k.team).length,triggerTeamHas3s:L.filter(r=>r[lb].poss3===r.k.team||r[lb].poss3==='restart:'+r.k.team).length,
   regain2s:c(x=>x.regain2s),regain6s:c(x=>x.regain6s),collected3s:c(x=>x.firstCtrl&&x.firstCtrl.dt<=60),wentDead:c(x=>!!x.restart),shots:s(x=>x.shots.A+x.shots.B),goals:s(x=>x.goals.length),ownGoals:s(x=>x.goals.filter(g=>g.own).length),
   sameTeamContactEps:s(x=>x.sameTeamContactEps),sameTeamContactEpsWithAlteredDecision:s(x=>x.sameTeamContactEpsAltered),alteredDecisions:s(x=>x.alteredDecisions),attDec1s:s(x=>x.attDec1s),attDec2s:s(x=>x.attDec2s),fwd1s:+(s(x=>x.fwd1s)/Math.max(1,c(x=>x.fwd1s!==null))).toFixed(3),fwd2s:+(s(x=>x.fwd2s)/Math.max(1,c(x=>x.fwd2s!==null))).toFixed(3)};}
 sum[type]=o;}
fs.writeFileSync(outF,JSON.stringify({seed:+seedS,H,labels,wallS:Math.round((Date.now()-t0)/1000),summary:sum,rows}));console.log(JSON.stringify({seed:+seedS,wallS:Math.round((Date.now()-t0)/1000),summary:sum}));
