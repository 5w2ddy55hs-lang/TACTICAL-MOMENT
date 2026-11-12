// Same-DTO counterfactual on an unchanged standard match: for every ordinary decision,
// evaluate original choose(o) and candidate chooseI18(o) on the identical DTO.
// The match itself is NOT altered. Labels (next touch team) come from later events, for audit only.
// usage: node same_dto_eval.mjs <I17dir> <branchDir> <seed> <ticks> <out.json> [extraJSON]
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,seedS,ticksS,outF,extraS]=process.argv.slice(2);const extra=extraS?JSON.parse(extraS):{};
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {chooseI18,flightContinuationEvidence}=await import(path.join(BR,'i18_flight_shape.mjs'));
const {choose}=await import(path.join(I17,'source/integration_i8_standard/core/decision.mjs'));
const rows=[];const touches=[];const reasons={};let lastKick=null;const passKicks=[];
const sink=ev=>{
 if(ev.channel==='event'){if(ev.type==='kick'){touches.push({t:ev.tick,team:ev.team,player:ev.player,kind:ev.kind});lastKick=ev;if(ev.kind==='pass')passKicks.push({t:ev.tick,team:ev.team,player:ev.player,target:ev.targetId});}
  else if(ev.type==='contact')touches.push({t:ev.tick,team:ev.team,player:ev.player,kind:ev.control?'ctrl':'touch'});
  else if(ev.type==='restart_placement')touches.push({t:ev.tick,team:null,kind:'dead:'+ev.kind});return;}
 if(ev.channel!=='decision')return;const o=ev.observation;
 const a=choose(o);if(a.kind!=='cover'||a.reason!=='private_shape_and_possession_hypothesis')return;
 const e=flightContinuationEvidence(o);reasons[e.reason]=(reasons[e.reason]||0)+1;
 const b=chooseI18(o);
 if(e.claim){const dx=b.target.x-a.target.x,dy=b.target.y-a.target.y;rows.push({t:ev.tick,p:ev.player,team:o.self.team,kicker:e.kicker,kickAgeS:e.kickAgeS,speed:e.speed,ball:[+o.ball.x.toFixed(1),+o.ball.y.toFixed(1)],coverT:[+a.target.x.toFixed(1),+a.target.y.toFixed(1)],supportT:[+b.target.x.toFixed(1),+b.target.y.toFixed(1)],fwdShift:+(dx*o.self.dir).toFixed(2),latShift:+dy.toFixed(2),selfDistToBall:+Math.hypot(o.self.x-o.ball.x,o.self.y-o.ball.y).toFixed(1),dir:o.self.dir});}
};
const e=g.create('standard',{seed:+seedS,zonalDefence:false,...extra},sink);
for(let i=0;i<+ticksS&&!e.finished;i++)e.step();
// label each claim: next touch (any) strictly after claim tick, and the last kick before claim
touches.sort((a,b)=>a.t-b.t);
for(const r of rows){const nx=touches.find(x=>x.t>r.t);r.nextTouch=nx?{t:nx.t,team:nx.team,kind:nx.kind,player:nx.player}:null;r.nextIsOpponent=nx?(nx.team!==null&&nx.team!==r.team):null;r.nextDead=nx?nx.team===null:null;const lk=[...passKicks].reverse().find(k=>k.t<=r.t);r.inOwnPassFlight=!!(lk&&lk.team===r.team&&!touches.some(x=>x.t>lk.t&&x.t<=r.t&&x.player!==lk.player));r.secondsToNext=nx?+((nx.t-r.t)/20).toFixed(2):null;}
const claims=rows.length;const opp=rows.filter(r=>r.nextIsOpponent);const own=rows.filter(r=>r.nextIsOpponent===false&&!r.nextDead);const dead=rows.filter(r=>r.nextDead);
const summary={seed:+seedS,ticks:e.tick,extra,coverDecisionsEvaluated:Object.values(reasons).reduce((a,b)=>a+b,0),evidenceReasons:reasons,claims,claimsInOwnPassFlight:rows.filter(r=>r.inOwnPassFlight).length,nextTouchOwnTeam:own.length,nextTouchOpponent:opp.length,nextDeadBall:dead.length,oppNextWithin1s:opp.filter(r=>r.secondsToNext<=1).length,medianFwdShift:(()=>{const v=rows.map(r=>r.fwdShift).sort((a,b)=>a-b);return v[Math.floor(v.length/2)]??null;})(),medianLatShift:(()=>{const v=rows.map(r=>Math.abs(r.latShift)).sort((a,b)=>a-b);return v[Math.floor(v.length/2)]??null;})()};
fs.writeFileSync(outF,JSON.stringify({summary,rows}));console.log(JSON.stringify(summary));
