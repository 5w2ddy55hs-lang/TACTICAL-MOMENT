// Same-DTO possession confusion on an UNCHANGED standard match (no divergence).
// For every outfield decision: original proximity hypothesis vs K20 (witnessed own-team touch required),
// against audit-only truth (last executed touch: team, control) and whether the player witnessed it.
// usage: node same_dto_k20.mjs <I17> <branch> <seed> <ticks> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,seedS,ticksS,outF]=process.argv.slice(2);
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {choose:chooseStd}=await import(path.join(I17,'source/integration_i8_standard/core/decision.mjs'));
const {choose:chooseK}=await import(path.join(BR,'decision.mjs'));
const d2=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
let last=null;const C={};const kindChange={};const unseen=[];const changes=[];let n=0;
const bump=(o,k)=>{o[k]=(o[k]||0)+1;};
const sink=ev=>{
 if(ev.channel==='event'&&(ev.type==='kick'||ev.type==='contact'))last={t:ev.tick,player:ev.player,team:ev.team,ctrl:ev.type==='kick'||!!ev.control};
 if(ev.channel==='event'&&ev.type==='restart_placement')last=null;
 if(ev.channel!=='decision')return;const o=ev.observation,p=o.self,b=o.ball;
 if(!b||o.restart||p.role==='GK'||p.hand?.holding)return;n++;
 const friends=o.people.filter(q=>q.team===p.team),enemies=o.people.filter(q=>q.team!==p.team);
 const vh=o.people.find(q=>q.holding&&o.tick-q.seenTick<=8);
 const nf=friends.filter(q=>d2(q,b)<2.1),ne=enemies.filter(q=>d2(q,b)<2.1);
 const proxOurs=vh?vh.team===p.team:nf.length>0&&!ne.length;
 const wt=p.observedTouch;const witnessedOwn=!!wt&&wt.players.length>0&&wt.players.every(q=>q.team===p.team);
 const kOurs=vh?vh.team===p.team:nf.length>0&&!ne.length&&witnessedOwn;
 const truth=!last?'none':!last.ctrl?'uncontrolled':last.team===p.team?'own_control':'opp_control';
 const witnessedLast=!!last&&!!wt&&wt.seenTick>=last.t&&wt.players.some(q=>q.id===last.player);
 const key=`prox=${proxOurs?'ours':'not'}|k20=${kOurs?'ours':'not'}|truth=${truth}|witnessedLast=${witnessedLast}`;bump(C,key);
 const a=chooseStd(o),k=chooseK(o);
 if(a.kind!==k.kind){bump(kindChange,a.kind+'->'+k.kind);if(changes.length<4000)changes.push({t:ev.tick,p:ev.player,from:a.kind,to:k.kind,truth,witnessedLast,lastTouch:last,observedTouchAgeS:wt?+((o.tick-wt.seenTick)/20).toFixed(2):null,nearFriends:nf.map(q=>q.id)});}
 if(proxOurs&&truth==='opp_control'&&!witnessedLast&&ev.tick>=6000&&(unseen.length===0||ev.tick-unseen.at(-1).t>200)&&unseen.length<3)unseen.push({t:ev.tick,p:ev.player,lastTouch:last});
};
const e=g.create('standard',{seed:+seedS,zonalDefence:false},sink);for(let i=0;i<+ticksS&&!e.finished;i++)e.step();
const proxOursKeys=Object.entries(C).filter(([k])=>k.startsWith('prox=ours'));
const summary={seed:+seedS,ticks:e.tick,outfieldDecisions:n,confusion:C,kindChanges:kindChange,changedDecisions:Object.values(kindChange).reduce((a,b)=>a+b,0),
 proxOurs_total:proxOursKeys.reduce((s,[,v])=>s+v,0),
 proxOurs_k20Not_byTruth:Object.fromEntries(['own_control','opp_control','uncontrolled','none'].map(t=>[t,proxOursKeys.filter(([k])=>k.includes('k20=not')&&k.includes('truth='+t)).reduce((s,[,v])=>s+v,0)])),
 proxOurs_k20Ours_byTruth:Object.fromEntries(['own_control','opp_control','uncontrolled','none'].map(t=>[t,proxOursKeys.filter(([k])=>k.includes('k20=ours')&&k.includes('truth='+t)).reduce((s,[,v])=>s+v,0)])),
 unseenControlsSelected:unseen};
fs.writeFileSync(outF,JSON.stringify({summary,changes}));console.log(JSON.stringify(summary,null,1));
