// From an original ck_research stop save: run a branch copy (identity relabelled, research only) up to the stop tick and
// H ticks beyond. Records the group-resolution rows, the events, and per-tick frames (for the viewer) from T-80.
// usage: node stop_continue.mjs <branchDir> <envelopeSave.json> <stopTick> <H> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [BR,saveF,stopS,HS,outF]=process.argv.slice(2);const T=+stopS,H=+HS;
const {MatchEngine}=await import(path.join(BR,'core/engine.mjs'));const id=await import(path.join(BR,'core/pass_build_identity.mjs'));
const raw=fs.readFileSync(saveF,'utf8');const env=JSON.parse(raw);const inner=JSON.parse(env.inner??raw);
inner.schema=id.PASS_SAVE_SCHEMA;inner.engine=id.PASS_ENGINE;inner.buildSha256=id.PASS_BUILD_SHA256;
const evs=[],res=[],dec={};let rec=false;
const sink=ev=>{if(ev.channel==='p25_group_resolution')res.push(ev);
 else if(ev.channel==='decision'){dec[ev.player]={kind:ev.decision.kind,target:ev.decision.target?[+ev.decision.target.x.toFixed(2),+ev.decision.target.y.toFixed(2)]:null};}
 else if(ev.channel==='event'&&rec&&!['offside_phase','offside_phase_cleared'].includes(ev.type))evs.push({t:ev.tick,type:ev.type,kind:ev.kind,player:ev.player??ev.taker??null,team:ev.team??null,control:ev.control,players:ev.players,teams:ev.teams,kinds:ev.kinds,winner:ev.winner,simultaneous:ev.simultaneous,reason:ev.reason,velocity:ev.velocity,position:ev.position,lastTouch:ev.lastTouch,score:ev.score});};
const e=MatchEngine.restore(JSON.stringify(inner),sink);const frames=[];let err=null,hashAtStop=null;
try{while(e.tick<T+H&&!e.finished){if(e.tick>=T-80)rec=true;if(e.tick===T)hashAtStop=e.stateHash();
  if(rec){const s=e.physicalSnapshot();frames.push({t:e.tick,ph:s.phase,ball:[+s.ball.x.toFixed(2),+s.ball.y.toFixed(2),+s.ball.z.toFixed(2)],p:s.players.map(q=>[q.id,+q.x.toFixed(2),+q.y.toFixed(2),dec[q.id]?.kind??''])});}
  e.step();}}catch(x){err=x.message;}
const fin=e.exportState();
fs.writeFileSync(outF,JSON.stringify({branch:path.basename(BR),engine:id.PASS_ENGINE,save:path.basename(path.dirname(saveF))+'/'+path.basename(saveF),stopTick:T,stateHashAtStopTick:hashAtStop,error:err,endTick:e.tick,score:fin.score,violations:fin.violations?.length??null,resolutions:res,events:evs,frames}));
console.log(JSON.stringify({branch:path.basename(BR),save:path.basename(path.dirname(saveF)),stopTick:T,hashAtStop,error:err,endTick:e.tick,resolutions:res.map(r=>({t:r.tick,rule:r.rule,winner:r.winner,cands:r.candidates.map(c=>c.id+':'+c.kind)})),next:evs.filter(x=>x.t>=T&&['kick','aerial_duel','goal','restart_placement','ambiguous_last_touch'].includes(x.type)).slice(0,6).map(x=>[x.t,x.type,x.kind,x.player??x.winner,x.team])}));
