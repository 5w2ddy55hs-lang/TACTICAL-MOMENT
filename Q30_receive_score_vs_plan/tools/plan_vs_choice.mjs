// Q30: decisions where a dedicated reception plan EXISTS under the engine's own gate (not canPlay, no visible holder,
// not their possession) and is body-reachable by its own test, yet the chosen action is not receive/intercept because
// the receive score (current-ball-distance based) lost to cover/support/advance_support/cover_exchange.
// Replicates decision.mjs gating exactly; uses the recorded candidates for the actual scores. Then follows truth:
// pass target, ball closest approach, next touch. Read only.
// usage: node plan_vs_choice.mjs <setDir> <out.json> <recording.json.gz>...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,outF,...recs]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));
const core='l21_natural/recovered/playtest_i17/source/integration_i8_standard/core/';
const {receptionPlan}=await import(R(core+'reception.mjs'));const {knownBallMotion}=await import(R(core+'local_touch_feedback.mjs'));
const DT=.05,dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),r2=v=>v==null?null:+v.toFixed(2);const rows=[];let scanned=0,planned=0;
for(const f of recs){const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(f)));const F=new Map(x.frames.map(q=>[q.tick,q]));const ev=x.rows.filter(r=>r.channel==='event');const kicks=ev.filter(e=>e.type==='kick');
 for(const r of x.rows){if(r.channel!=='decision')continue;const o=r.observation,p=o?.self,ball=o?.ball;if(!o||!ball||o.restart||p.role==='GK'||p.hand?.holding)continue;scanned++;
  const friends=o.people.filter(q=>q.team===p.team),enemies=o.people.filter(q=>q.team!==p.team);const bp={x:ball.x,y:ball.y},db=dist(p,bp),age=(o.tick-ball.seenTick)*DT;
  const nearFriends=friends.filter(q=>dist(q,bp)<2.1),nearEnemies=enemies.filter(q=>dist(q,bp)<2.1);const visibleHolder=o.people.find(q=>q.holding&&o.tick-q.seenTick<=8);
  const ourPossession=visibleHolder?visibleHolder.team===p.team:nearFriends.length>0&&!nearEnemies.length;const theirPossession=nearEnemies.length>0&&!nearFriends.length;
  const motion=knownBallMotion(ball),speed=motion?.speed??null;const uncertainAttempt=motion===null&&ball.seenTick===o.tick;
  const canPlay=!visibleHolder&&db<1.0&&age<=0.35&&ball.z<0.5&&(p.touch||motion!==null&&speed<8||uncertainAttempt);
  if(canPlay||visibleHolder||theirPossession)continue;const plan=receptionPlan(structuredClone(o));if(!plan)continue;planned++;
  const d=r.decision;if(['receive','intercept'].includes(d.kind))continue;
  const aheadFriends=friends.filter(q=>dist(q,bp)+2<db).length;const cands=(d.candidates||[]).map(c=>({kind:c.kind,score:r2(c.score)}));const rc=cands.find(c=>c.kind==='receive'||c.kind==='intercept');
  const lastKick=kicks.filter(k=>k.tick<=r.tick).at(-1);const intended=lastKick?.targetId===p.id;
  // truth follow-up (audit only): closest approach of ball to this player in next 60 ticks, next touch by anyone
  let best=null;for(let t=r.tick;t<=r.tick+60;t++){const fr=F.get(t);if(!fr)break;const q=fr.players.find(z=>z.id===p.id);if(!q)break;const dd=Math.hypot(q.x-fr.ball.x,q.y-fr.ball.y);if(!best||dd<best.d)best={d:r2(dd),tick:t};}
  const next=ev.find(e=>e.tick>r.tick&&(e.type==='kick'||(e.type==='contact'&&e.control)||e.type==='restart_placement'||e.type==='goal'));
  rows.push({rec:path.basename(f),tick:r.tick,player:p.id,team:p.team,role:p.role,chosen:d.kind,receiveScore:rc?.score??null,winnerScore:cands[0]?.score??null,components:{db:r2(db),ourPossession,nearFriends:nearFriends.length,aheadFriends,age:r2(age),press:o.coach.press},plan:{eta:plan.eta,miss:r2(plan.estimatedMissM),targetDist:r2(dist(p,plan.target))},ballSpeed:r2(speed),lastKick:lastKick?{tick:lastKick.tick,player:lastKick.player,team:lastKick.team,kind:lastKick.kind,targetId:lastKick.targetId??null}:null,intended,closest:best,next:next?{tick:next.tick,type:next.type,player:next.player??null,team:next.team??null,kind:next.kind??null,control:next.control??null}:null});}}
fs.writeFileSync(outF,JSON.stringify({scanned,planned,notReceive:rows.length,rows},null,1));
const by=(k,f)=>rows.filter(f).length;
console.log(JSON.stringify({scanned,planExists:planned,planButOtherAction:rows.length,byChosen:Object.entries(rows.reduce((m,r)=>{m[r.chosen]=(m[r.chosen]||0)+1;return m;},{})),ourPossessionPenalty:by(0,r=>r.components.ourPossession),notOurPossession:by(0,r=>!r.components.ourPossession),intendedReceiver:by(0,r=>r.intended),closestLE1_5:by(0,r=>r.closest&&r.closest.d<=1.5),nextTouchSelf:by(0,r=>r.next&&r.next.player===r.player),nextTouchTeammate:by(0,r=>r.next&&r.next.player&&r.next.player!==r.player&&r.next.team===r.team),nextTouchOpponent:by(0,r=>r.next&&r.next.player&&r.next.team!==r.team),nextOutOrNone:by(0,r=>!r.next||!r.next.player)}));
