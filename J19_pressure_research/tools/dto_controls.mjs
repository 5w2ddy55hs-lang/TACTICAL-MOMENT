// Decision-level controls on REAL captured DTOs (standard match, unchanged).
// For every DTO where chooseJ19 yields (A) or engages (B), perturb ONLY the observed teammates
// and check the decision responds as specified. Pure function calls; no world change.
// usage: node dto_controls.mjs <I17> <branch> <seed> <ticks> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,seedS,ticksS,outF]=process.argv.slice(2);
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {chooseJ19,pressureContext}=await import(path.join(BR,'j19_pressure_value.mjs'));
const clone=x=>JSON.parse(JSON.stringify(x));
const res={yieldCases:0,stopEffective_resumesPress:0,removeEffective_resumesPress:0,engageCases:0,addGoalSideEffective_noEngage:0,goalSideRetreating_stillEngage:0,yieldNotGoalSide:0,examples:[]};
const sink=ev=>{if(ev.channel!=='decision')return;const o=ev.observation;const d=chooseJ19(o);
 if(String(d.reason).includes('yield')){res.yieldCases++;const c=pressureContext(o);const eff=c.mates.filter(m=>m.effective).map(m=>m.id);
  if(!c.self.goalSide)res.yieldNotGoalSide++;
  // (1) the effective teammates are observed stopped (velocity 0) -> they should become ineffective unless very close
  const o1=clone(o);for(const q of o1.people)if(eff.includes(q.id)){q.vx=0;q.vy=0;}const d1=chooseJ19(o1);const c1=pressureContext(o1);const still=c1.mates.filter(m=>m.effective).length;
  if(!String(d1.reason).includes('yield'))res.stopEffective_resumesPress++;else if(res.examples.length<6)res.examples.push({t:ev.tick,p:ev.player,test:'stop',stillEffective:c1.mates.filter(m=>m.effective).map(m=>({id:m.id,gs:m.goalSide,d:+m.d.toFixed(1)}))});
  // (2) the effective teammates are no longer observed -> must press
  const o2=clone(o);o2.people=o2.people.filter(q=>!eff.includes(q.id));const d2=chooseJ19(o2);if(d2.kind==='press')res.removeEffective_resumesPress++;}
 if(String(d.reason).includes('engage')){res.engageCases++;const c=pressureContext(o);
  // (3) add an observed goal-side teammate 4 m from the ball -> should not engage
  const o3=clone(o);const b=o3.ball;const dir=o3.self.dir;const mate=o3.people.find(q=>q.team===o3.self.team&&q.role!=='GK');if(mate){mate.x=Math.max(.5,Math.min(104.5,b.x-dir*4));mate.y=b.y;mate.vx=0;mate.vy=0;mate.seenTick=o3.tick;const d3=chooseJ19(o3);if(!String(d3.reason).includes('engage'))res.addGoalSideEffective_noEngage++;}
  // (4) same goal-side teammate but 10 m away and retreating -> not effective -> engage remains
  const o4=clone(o);const m4=o4.people.find(q=>q.team===o4.self.team&&q.role!=='GK');if(m4){m4.x=Math.max(.5,Math.min(104.5,o4.ball.x-dir*10));m4.y=o4.ball.y;m4.vx=-dir*3;m4.vy=0;m4.seenTick=o4.tick;const d4=chooseJ19(o4);if(String(d4.reason).includes('engage'))res.goalSideRetreating_stillEngage++;}}};
const e=g.create('standard',{seed:+seedS,zonalDefence:false},sink);for(let i=0;i<+ticksS&&!e.finished;i++)e.step();
fs.writeFileSync(outF,JSON.stringify(res,null,1));console.log(JSON.stringify(res).slice(0,1500));
