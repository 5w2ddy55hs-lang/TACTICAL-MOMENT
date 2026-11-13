// Full-match scan of L21 yields (decisions where L21 differs from K20 on the identical DTO) in an L21 match,
// characterising the trusted "evident collector" from the yielder's own DTO, and labelling (audit-only) whether
// that collector actually touched/controlled the ball first, or a teammate/opponent did, within 40 ticks.
// usage: node yield_scan.mjs <I17> <k20dir> <l21dir> <seed> <ticks> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,K20,L21,seedS,ticksS,outF]=process.argv.slice(2);
const {choose:chooseK}=await import(path.join(K20,'decision.mjs'));
const {MatchEngine}=await import(path.join(L21,'engine.mjs'));
const d2=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const yields=[];const touches=[];const restarts=[];
const sink=e=>{
 if(e.channel==='event'&&(e.type==='kick'||e.type==='contact'))touches.push({t:e.tick,p:e.player,team:e.team,ctrl:e.type==='kick'||!!e.control});
 if(e.channel==='event'&&e.type==='restart_placement')restarts.push(e.tick);
 if(e.channel!=='decision')return;const o=e.observation;const kd=chooseK(o);if(kd.kind===e.decision.kind)return;
 const p=o.self,b=o.ball,db=d2(p,b);const bvx=b.velocityKnown?b.vx:0,bvy=b.velocityKnown?b.vy:0,bs=Math.hypot(bvx,bvy);
 const cols=o.people.filter(q=>q.team===p.team&&d2(q,b)<2.1&&q.seenTick===o.tick&&d2(q,b)<db).map(q=>{const d=d2(q,b)||1e-6,ux=(b.x-q.x)/d,uy=(b.y-q.y)/d;
  const own=q.vx*ux+q.vy*uy,rel=(q.vx-bvx)*ux+(q.vy-bvy)*uy,ballTowardQ=-(bvx*ux+bvy*uy);
  return {id:q.id,d:+d.toFixed(2),own:+own.toFixed(2),rel:+rel.toFixed(2),ballTowardQ:+ballTowardQ.toFixed(2),qualifies:d<=1.1||rel>=0.5};}).filter(q=>q.qualifies);
 const oppD=Math.min(99,...o.people.filter(x=>x.team!==p.team).map(x=>d2(x,b)));
 yields.push({t:e.tick,p:e.player,team:p.team,from:kd.kind,to:e.decision.kind,selfD:+db.toFixed(2),ballSpeed:+bs.toFixed(2),velKnown:b.velocityKnown,oppNearestD:+oppD.toFixed(2),cols});};
const e=new MatchEngine({seed:+seedS,zonalDefence:false},sink);for(let i=0;i<+ticksS&&!e.finished;i++)e.step();
// label outcomes
for(const y of yields){const nx=touches.find(x=>x.t>y.t&&x.t<=y.t+40);const rs=restarts.find(t=>t>y.t&&t<=y.t+40);
 const colIds=y.cols.map(c=>c.id);
 y.outcome=!nx?(rs?'dead_ball':'no_touch_40'):colIds.includes(nx.p)?(nx.ctrl?'collector_control':'collector_touch_nocontrol'):nx.p===y.p?'yielder_touched':nx.team===y.team?'other_teammate':'opponent_first';
 const c=y.cols.slice().sort((a,b)=>a.d-b.d)[0];
 y.cat=!c?'none':c.d<=1.1?'reach':(c.own>=0.5?'closing_by_own_motion':'closing_by_ball_only');
 y.fastBall=y.ballSpeed>10.7;y.oppCloserThanCollector=!!c&&y.oppNearestD<c.d;}
const C={};for(const y of yields){const k=y.cat+(y.fastBall?'|fast':'|slow')+(y.oppCloserThanCollector?'|oppCloser':'');C[k]=C[k]||{};C[k][y.outcome]=(C[k][y.outcome]||0)+1;}
fs.writeFileSync(outF,JSON.stringify({seed:+seedS,ticks:e.tick,n:yields.length,byCategory:C,yields}));console.log(JSON.stringify({seed:+seedS,n:yields.length,byCategory:C},null,1));
