// Same-state paired trace (base vs K20) for named players: every decision the player makes, with the player's OWN
// possession evidence (visible holder, near friends/enemies within 2.1 m, latest witnessed touch and its age, ball age,
// ball velocity known) and the audit-only truth (distance to ball, ball speed). Ball events with positions.
// usage: node pair_trace.mjs <I17> <k20dir> <stateFile> <H> <ids,comma> <out.txt>
import fs from 'node:fs';import path from 'node:path';
const [I17,K20,stateF,HS,idsS,outF]=process.argv.slice(2);const H=+HS;const ids=new Set(idsS.split(','));
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const stdId=await import(path.join(I17,'source/integration_i8_standard/core/pass_build_identity.mjs'));
const d2=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const relabel=(t,id)=>{let x=JSON.parse(t);if(x.inner)x=JSON.parse(x.inner);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return JSON.stringify(x);};
const K=await import(path.join(K20,'engine.mjs'));const kId=await import(path.join(K20,'pass_build_identity.mjs'));
const engines={base:(t,s)=>Std.restore(relabel(t,stdId),s),k20:(t,s)=>K.MatchEngine.restore(relabel(t,kId),s)};
const text=fs.readFileSync(stateF,'utf8');const lines=[];
for(const [label,restore] of Object.entries(engines)){
 let eng;const rows=[];
 const sink=e=>{if(!eng)return;
  if(e.channel==='event'&&['kick','contact','restart_placement','goal','throw_in_play'].includes(e.type)){const s=eng.physicalSnapshot();
   rows.push(`${label} t+${e.tick-T0} EVENT ${e.type}${e.kind?':'+e.kind:''} ${e.player??e.taker??''} team=${e.team} ctrl=${e.type==='kick'||!!e.control} ball=(${s.ball.x.toFixed(1)},${s.ball.y.toFixed(1)}) v=${Math.hypot(s.ball.vx,s.ball.vy).toFixed(1)}`);}
  if(e.channel==='decision'&&ids.has(e.player)){const o=e.observation,p=o.self,b=o.ball;const s=eng.physicalSnapshot();const me=s.players.find(q=>q.id===p.id);
   let ev='no-ball';if(b){const friends=o.people.filter(q=>q.team===p.team&&q.id!==p.id),enemies=o.people.filter(q=>q.team!==p.team);
    const nf=friends.filter(q=>d2(q,b)<2.1).map(q=>q.id),ne=enemies.filter(q=>d2(q,b)<2.1).map(q=>q.id);const vh=o.people.find(q=>q.holding&&o.tick-q.seenTick<=8);
    const wt=p.observedTouch;ev=`seen:dBall=${d2(p,b).toFixed(1)} ballAge=${o.tick-b.seenTick} velKnown=${b.velocityKnown} holder=${vh?vh.id:'-'} nearF=[${nf}] nearE=[${ne}] witnessed=${wt?wt.players.map(x=>x.id+':'+x.part).join('+')+'@age'+(o.tick-wt.seenTick):'none'}`;}
   rows.push(`${label} t+${e.tick-T0} ${p.id} ${e.decision.kind}${e.decision.target?` ->(${(+e.decision.target.x).toFixed(1)},${(+e.decision.target.y).toFixed(1)})`:''} sc=${(+e.decision.score).toFixed(2)} | ${ev} | truth dBall=${d2(me,s.ball).toFixed(1)} ballV=${Math.hypot(s.ball.vx,s.ball.vy).toFixed(1)}`);}};
 let T0=0;eng=restore(text,sink);T0=eng.tick;
 for(let i=0;i<H&&!eng.finished;i++)eng.step();
 lines.push(...rows);}
fs.writeFileSync(outF,lines.join('\n')+'\n');console.log(outF,lines.length);
