// Q30: trace one player's decisions (plan gate, receive score decomposition, hypothetical score with plan-target distance)
// and the truth (speed, ball distance, nearest opponents, pass/touch events) over a window. Read only; no candidate code.
// usage: node plan_episode_trace.mjs <setDir> <recording.json.gz> <player> <from> <to>
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,recF,PID,fromS,toS]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));const core='l21_natural/recovered/playtest_i17/source/integration_i8_standard/core/';
const {receptionPlan}=await import(R(core+'reception.mjs'));const {knownBallMotion}=await import(R(core+'local_touch_feedback.mjs'));
const DT=.05,dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),r2=v=>v==null?null:+v.toFixed(2);
const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(recF)));const F=new Map(x.frames.map(q=>[q.tick,q]));const ev=x.rows.filter(r=>r.channel==='event');
const P=(t,id)=>F.get(t)?.players.find(p=>p.id===id);const team=P(+fromS,PID)?.team;
console.log(`## ${path.basename(recF)} ${PID} ${fromS}-${toS}`);
console.log('events: '+ev.filter(e=>e.tick>=+fromS&&e.tick<=+toS&&(e.type==='kick'||(e.type==='contact'&&e.control)||e.type==='restart_placement'||e.type==='goal')).map(e=>`${e.tick}:${e.type}${e.kind?':'+e.kind:''}:${e.player??''}${e.targetId?'→'+e.targetId:''}`).filter((v,i,s)=>s.indexOf(v)===i).join(' '));
for(const r of x.rows){if(r.channel!=='decision'||r.player!==PID||r.tick<+fromS||r.tick>+toS)continue;const o=r.observation,p=o.self,ball=o.ball,d=r.decision;
 let line=`${r.tick}→${d.applyTick??'-'} ${d.kind}${d.reception?'(DP)':''}`;
 if(ball&&!o.restart){const friends=o.people.filter(q=>q.team===p.team),enemies=o.people.filter(q=>q.team!==p.team);const bp={x:ball.x,y:ball.y},db=dist(p,bp),age=(o.tick-ball.seenTick)*DT;
  const nearF=friends.filter(q=>dist(q,bp)<2.1),nearE=enemies.filter(q=>dist(q,bp)<2.1);const holder=o.people.find(q=>q.holding&&o.tick-q.seenTick<=8);const ourP=holder?holder.team===p.team:nearF.length>0&&!nearE.length,theirP=nearE.length>0&&!nearF.length;
  const motion=knownBallMotion(ball),speed=motion?.speed??null;const canPlay=!holder&&db<1&&age<=.35&&ball.z<.5&&(p.touch||motion!==null&&speed<8||(motion===null&&ball.seenTick===o.tick));
  const plan=(!canPlay&&!holder&&!theirP)?receptionPlan(structuredClone(o)):null;const ahead=friends.filter(q=>dist(q,bp)+2<db).length;
  const base=1.65+o.coach.press*.35-age*.4,sc=base-db*.048-(ourP?1.5:0)-Math.min(2,ahead)*.22;const hyp=plan?base-dist(p,plan.target)*.048-(ourP?1.5:0)-Math.min(2,ahead)*.22:null;
  const cands=(d.candidates||[]).slice(0,3).map(c=>`${c.kind}:${r2(c.score)}`).join(' ');
  line+=` | db ${r2(db)} v ${r2(speed)} age ${r2(age)} ourP ${ourP} nearF ${nearF.length} ahead ${ahead} | score ${r2(sc)} = base ${r2(base)} −db ${r2(db*.048)} −poss ${ourP?1.5:0} −ahead ${r2(Math.min(2,ahead)*.22)} | plan ${plan?`eta ${r2(plan.eta)} miss ${r2(plan.estimatedMissM)} tgtDist ${r2(dist(p,plan.target))} → hypothetical score with plan-target distance ${r2(hyp)}`:'none'} | ${cands}`;}
 const q=P(r.tick,PID),q0=P(r.tick-1,PID),fr=F.get(r.tick);if(q&&fr){const sp=q0?Math.hypot(q.x-q0.x,q.y-q0.y)/DT:null;const opp=fr.players.filter(z=>z.team!==team).map(z=>({id:z.id,d:Math.hypot(z.x-fr.ball.x,z.y-fr.ball.y)})).sort((a,b)=>a.d-b.d)[0];line+=` | truth: speed ${r2(sp)} dBall ${r2(Math.hypot(q.x-fr.ball.x,q.y-fr.ball.y))} nearestOpp ${opp?.id}(${r2(opp?.d)})`;}
 console.log(line);}
