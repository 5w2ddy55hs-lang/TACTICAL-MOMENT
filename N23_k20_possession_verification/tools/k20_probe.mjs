// From an identical state, run base and K20 (and L21 for reference); trace every K20 decision whose kind differs from
// the ORIGINAL choose() on the identical DTO, with the deciding player's own evidence and the audit-only truth.
// usage: node k20_probe.mjs <I17> <k20dir> <l21dir> <stateFile> <team> <H> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,K20,L21,stateF,team,HS,outF]=process.argv.slice(2);const H=+HS;
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const stdId=await import(path.join(I17,'source/integration_i8_standard/core/pass_build_identity.mjs'));
const {choose:chooseOrig}=await import(path.join(I17,'source/integration_i8_standard/core/decision.mjs'));
const d2=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const relabel=(t,id)=>{let x=JSON.parse(t);if(x.inner)x=JSON.parse(x.inner);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return JSON.stringify(x);};
const mk=async dir=>{const m=await import(path.join(dir,'engine.mjs'));const id=await import(path.join(dir,'pass_build_identity.mjs'));return (t,s)=>m.MatchEngine.restore(relabel(t,id),s);};
const engines={base:(t,s)=>Std.restore(relabel(t,stdId),s),k20:await mk(K20),l21:await mk(L21)};
const text=fs.readFileSync(stateF,'utf8');const out={};
for(const [label,restore] of Object.entries(engines)){
 const ev=[],alts=[],frames=[];let last=null;
 const sink=e=>{if(e.channel==='event'&&(e.type==='kick'||e.type==='contact'))last={t:e.tick,p:e.player,team:e.team,ctrl:e.type==='kick'||!!e.control};
  if(e.channel==='event'&&['kick','contact','restart_placement','goal','throw_in_play'].includes(e.type))ev.push({t:e.tick,type:e.type,p:e.player??e.taker,team:e.team,kind:e.kind,ctrl:e.type==='kick'||!!e.control});
  if(e.channel==='decision'&&label!=='base'){const o=e.observation;let a;try{a=chooseOrig(o);}catch{return;}if(a.kind===e.decision.kind||['dribble','pass'].includes(e.decision.kind)&&['dribble','pass'].includes(a.kind))return;
   const p=o.self,b=o.ball;const nf=b?o.people.filter(q=>q.team===p.team&&d2(q,b)<2.1).map(q=>({id:q.id,d:+d2(q,b).toFixed(2),age:o.tick-q.seenTick})):[];
   const wt=p.observedTouch;alts.push({t:e.tick,p:e.player,team:p.team,orig:a.kind,now:e.decision.kind,selfD:b?+d2(p,b).toFixed(2):null,ballAge:b?o.tick-b.seenTick:null,velKnown:b?.velocityKnown??null,
    witnessed:wt?{who:wt.players.map(x=>x.id+':'+x.team+':'+x.part),age:o.tick-wt.seenTick}:null,nearFriends:nf,truthLast:last});}};
 const eng=restore(text,sink);const t0=eng.tick;
 for(let i=0;i<H&&!eng.finished;i++){eng.step();if(i%2===0){const s=eng.physicalSnapshot();frames.push({t:eng.tick,ph:s.phase,ball:[+s.ball.x.toFixed(2),+s.ball.y.toFixed(2)],p:s.players.map(q=>[q.id,+q.x.toFixed(2),+q.y.toFixed(2)])});}}
 const ctrl=ev.filter(x=>(x.type==='kick'||x.type==='contact')&&x.ctrl);
 const possAt=t=>{const c=ctrl.filter(x=>x.t<=t0+t);const r=ev.filter(x=>x.type==='restart_placement'&&x.t<=t0+t);if(r.length&&(!c.length||r.at(-1).t>=c.at(-1).t))return 'restart:'+r.at(-1).team;return c.length?c.at(-1).team:'none';};
 out[label]={t0,poss3:possAt(60),poss6:possAt(120),events:ev,alterations:alts,frames};}
fs.writeFileSync(outF,JSON.stringify(out));console.log(JSON.stringify({state:path.basename(stateF),team,base:out.base.poss6,k20:out.k20.poss6,l21:out.l21.poss6,k20alts:out.k20.alterations.length}));
