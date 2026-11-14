// Reproduce one stop in the diagnostic copy (identical behaviour + observer-only row before the original throw).
// The I9 envelope save of the original ck_research run is restored by relabelling the inner save identity (research only).
// Records: the mixed group (every candidate's view/action/timing/geometry), each candidate's decision history
// (decision + ck_policy channels) over the last 80 ticks, ball events since the corner, every player within 3 m.
// usage: node stop_diag.mjs <branchDir> <envelopeSave.json> <out.json> [maxTicks]
import fs from 'node:fs';import path from 'node:path';import {createHash} from 'node:crypto';
const [BR,saveF,outF,maxS]=process.argv.slice(2);
const {MatchEngine}=await import(path.join(BR,'core/engine.mjs'));const id=await import(path.join(BR,'core/pass_build_identity.mjs'));
const raw=fs.readFileSync(saveF,'utf8');const env=JSON.parse(raw);const inner=JSON.parse(env.inner??raw);
inner.schema=id.PASS_SAVE_SCHEMA;inner.engine=id.PASS_ENGINE;inner.buildSha256=id.PASS_BUILD_SHA256;
const dec=[],evs=[];let diag=null;
const sink=ev=>{if(ev.channel==='p25_mixed_group_diag')diag=ev;
 else if(ev.channel==='decision'||ev.channel==='ck_policy'){const d=ev.decision||{};dec.push({t:ev.tick,ch:ev.channel,p:ev.player,kind:d.kind,reason:d.reason??null,target:d.target?[+d.target.x.toFixed(2),+d.target.y.toFixed(2)]:null,aim:d.aim?[+d.aim.x.toFixed(2),+d.aim.y.toFixed(2)]:null,applyTick:d.applyTick??null,observedTick:d.observedTick??null,
   ballSeen:ev.observation?.ball?{x:+ev.observation.ball.x.toFixed(2),y:+ev.observation.ball.y.toFixed(2),z:+(ev.observation.ball.z??0).toFixed(2),seenTick:ev.observation.ball.seenTick,vz:ev.observation.setPiece?.ballVz??null}:null});}
 else if(ev.channel==='event'&&!['offside_phase','offside_phase_cleared'].includes(ev.type))evs.push({t:ev.tick,type:ev.type,kind:ev.kind,player:ev.player??ev.taker??null,team:ev.team??null,control:ev.control,players:ev.players,winner:ev.winner});};
const e=MatchEngine.restore(JSON.stringify(inner),sink);const t0=e.tick;let prev=null,err=null;const ballTrack=[];
try{for(let i=0;i<+(maxS||7000)&&!e.finished;i++){prev=e.physicalSnapshot();ballTrack.push([e.tick,+prev.ball.x.toFixed(2),+prev.ball.y.toFixed(2),+prev.ball.z.toFixed(2)]);if(ballTrack.length>60)ballTrack.shift();e.step();}}catch(x){err=x.message;}
const out={save:path.basename(path.dirname(saveF))+'/'+path.basename(saveF),saveSha256:createHash('sha256').update(raw).digest('hex'),restoredTick:t0,error:err,stopTick:e.tick,node:process.version};
if(diag){const T=diag.tick,ids=new Set(diag.candidates.map(c=>c.id));const corner=[...evs].reverse().find(x=>x.type==='restart_taken'&&x.kind==='corner');
 out.diag=diag;out.cornerTakenTick=corner?.t??null;
 out.ballEventsSinceCorner=evs.filter(x=>x.t>=(corner?.t??T-200)-2&&['kick','contact','aerial_duel','restart_taken','restart_placement','goal'].includes(x.type));
 out.candidateDecisions=dec.filter(x=>ids.has(x.p)&&x.t>=T-80);
 const b=diag.ball;out.playersWithin3m=prev.players.map(p=>({id:p.id,d:+Math.hypot(p.x-b.x,p.y-b.y).toFixed(2),x:+p.x.toFixed(2),y:+p.y.toFixed(2),candidate:ids.has(p.id)})).filter(p=>p.d<=3).sort((a,c)=>a.d-c.d);
 out.nearDecisionsLast=Object.fromEntries(out.playersWithin3m.map(p=>[p.id,dec.filter(x=>x.p===p.id).slice(-2)]));
 out.ballTrackLast40=ballTrack.slice(-40);}
fs.writeFileSync(outF,JSON.stringify(out,null,1));
console.log(JSON.stringify({save:out.save,error:err,stopTick:e.tick,group:diag?.candidates.map(c=>`${c.id}:${c.view.kind}(d=${c.dist.toFixed(2)})`),ballZ:diag?.ball.z}));
