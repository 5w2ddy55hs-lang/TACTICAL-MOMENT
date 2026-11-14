import fs from 'node:fs';import path from 'node:path';
const [I17,variant,saveF]=process.argv.slice(2);
const {register,restore}=await import(path.join(I17,'research_guard.mjs'));await register(variant);
const evs=[];const e=restore(fs.readFileSync(saveF,'utf8'),variant,ev=>{if(ev.channel==='event'&&!['offside_phase','offside_phase_cleared','contact'].includes(ev.type))evs.push({tick:ev.tick,type:ev.type,kind:ev.kind,player:ev.player??ev.taker,team:ev.team,targetId:ev.targetId});});
let prev=null;
try{for(let i=0;i<20000;i++){prev=e.exportState();e.step();}console.log('no crash');}catch(err){const s=prev;const b=s.ball;
 console.log(JSON.stringify({error:err.message,tickBeforeStep:s.tick,half:s.half,phase:s.phase,score:s.score,restart:s.restart,ball:{x:b.x,y:b.y,z:b.z,vx:b.vx,vy:b.vy,vz:b.vz,lastTouch:b.lastTouch,lastKick:b.lastKick}}));
 const near=s.players.map(p=>({id:p.id,role:p.role,x:+p.x.toFixed(2),y:+p.y.toFixed(2),d:+Math.hypot(p.x-b.x,p.y-b.y).toFixed(2),action:p.action&&{kind:p.action.kind,targetId:p.action.targetId,applyTick:p.action.applyTick},pending:p.pending&&{kind:p.pending.kind,applyTick:p.pending.applyTick}})).sort((a,c)=>a.d-c.d).slice(0,6);
 console.log(JSON.stringify(near));console.log(JSON.stringify(evs.slice(-14)));}
