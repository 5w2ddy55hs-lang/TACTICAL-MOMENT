// Same-DTO counterfactual on an UNCHANGED standard match. Per decision: choose(o) vs chooseJ19(o).
// Team-level static counterfactual per tick (positions are the baseline's; no feedback):
// in opponent-carry ticks, compare ball-directed counts / same-target overlaps / "nobody pressing".
// usage: node same_dto_j19.mjs <I17> <branch> <seed> <ticks> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,seedS,ticksS,outF]=process.argv.slice(2);
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {chooseJ19,pressureContext}=await import(path.join(BR,'j19_pressure_value.mjs'));
const {choose}=await import(path.join(I17,'source/integration_i8_standard/core/decision.mjs'));
const BD=new Set(['press','intercept','receive']);
const latest={};const changes=[];const reasons={};
const sink=ev=>{if(ev.channel!=='decision')return;const o=ev.observation;const a=choose(o),b=chooseJ19(o);
 latest[ev.player]={a,b,team:o.self.team,t:ev.tick};
 if(a.kind!==b.kind||a.reason!==b.reason){reasons[b.reason]=(reasons[b.reason]||0)+1;const c=pressureContext(o);
  changes.push({t:ev.tick,p:ev.player,team:o.self.team,from:a.kind,to:b.kind,reason:b.reason,self:c?.self,effective:c?c.mates.filter(m=>m.effective).map(m=>({id:m.id,gs:m.goalSide,d:+m.d.toFixed(1)})):null,carrier:c?.carrier?.id});}};
const e=g.create('standard',{seed:+seedS,zonalDefence:false},sink);
const team={A:{ticks:0,baseBD:0,j19BD:0,baseZeroNear:0,j19ZeroNear:0,baseGe3:0,j19Ge3:0,baseGoalSidePress:0,j19GoalSidePress:0}};team.B=JSON.parse(JSON.stringify(team.A));
const ids=e.exportState().players.map(p=>p.id);
for(let i=0;i<+ticksS&&!e.finished;i++){e.step();const s=e.physicalSnapshot();if(s.phase!=='play')continue;const b=s.ball;
 const near=s.players.map(p=>({p,d:Math.hypot(p.x-b.x,p.y-b.y)}));
 for(const T of ['A','B']){const opp=T==='A'?'B':'A';const mine=near.filter(x=>x.p.id[0]===T),theirs=near.filter(x=>x.p.id[0]===opp);
  if(!(theirs.some(x=>x.d<2.1)&&!mine.some(x=>x.d<2.1)))continue; // opponent-carry (truth, audit only)
  const R=team[T];R.ticks++;const gk=s.players.find(p=>p.id===T+'00');const goalX=gk.x<52.5?0:105;
  let ba=0,bb=0,na=0,nb=0,ga=0,gb=0;
  for(const x of mine){if(x.p.id.endsWith('00'))continue;const L=latest[x.p.id];if(!L)continue;const gs=Math.abs(x.p.x-goalX)<Math.abs(b.x-goalX);
   if(BD.has(L.a.kind)){ba++;if(x.d<15)na++;if(gs&&x.d<18)ga++;}if(BD.has(L.b.kind)){bb++;if(x.d<15)nb++;if(gs&&x.d<18)gb++;}}
  R.baseBD+=ba;R.j19BD+=bb;if(ba>=3)R.baseGe3++;if(bb>=3)R.j19Ge3++;if(na===0)R.baseZeroNear++;if(nb===0)R.j19ZeroNear++;if(ga>0)R.baseGoalSidePress++;if(gb>0)R.j19GoalSidePress++;}}
const sum=k=>team.A[k]+team.B[k];
const summary={seed:+seedS,ticks:e.tick,changes:changes.length,reasons,oppCarryTicks:sum('ticks'),meanBallDirected:{base:+(sum('baseBD')/sum('ticks')).toFixed(2),j19:+(sum('j19BD')/sum('ticks')).toFixed(2)},ge3Share:{base:+(sum('baseGe3')/sum('ticks')).toFixed(3),j19:+(sum('j19Ge3')/sum('ticks')).toFixed(3)},noBallDirectedWithin15m:{base:sum('baseZeroNear'),j19:sum('j19ZeroNear')},goalSidePresserWithin18mShare:{base:+(sum('baseGoalSidePress')/sum('ticks')).toFixed(3),j19:+(sum('j19GoalSidePress')/sum('ticks')).toFixed(3)},note:'static counterfactual: J19 decisions evaluated on baseline DTOs/positions; no physical feedback'};
fs.writeFileSync(outF,JSON.stringify({summary,changes}));console.log(JSON.stringify(summary));
