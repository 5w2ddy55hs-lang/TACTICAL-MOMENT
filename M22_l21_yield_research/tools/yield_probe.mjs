// Re-run one opportunity from an identical standard state with base, K20 and L21, and trace every L21 decision
// that differs from K20 on the identical DTO (= an L21 "yield to evident collector").
// usage: node yield_probe.mjs <I17> <k20dir> <l21dir> <stateFile> <triggerTeam> <H> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,K20,L21,stateF,team,HS,outF]=process.argv.slice(2);const H=+HS;
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {choose:chooseK}=await import(path.join(K20,'decision.mjs'));
const d2=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const mk=async dir=>{const m=await import(path.join(dir,'engine.mjs'));const id=await import(path.join(dir,'pass_build_identity.mjs'));return (t,s)=>{let x=JSON.parse(t);if(x.inner)x=JSON.parse(x.inner);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return m.MatchEngine.restore(JSON.stringify(x),s);};};
const engines={base:(t,s)=>g.restore(t,'standard',s),k20:await mk(K20),l21:await mk(L21)};
const text=fs.readFileSync(stateF,'utf8');const out={};
for(const [label,restore] of Object.entries(engines)){
 const ev=[],yields=[],body=[],frames=[];
 const sink=e=>{if(e.channel==='event'&&['kick','contact','restart_placement','goal','throw_in_play'].includes(e.type))ev.push({t:e.tick,type:e.type,p:e.player??e.taker,team:e.team,kind:e.kind,ctrl:e.type==='kick'||!!e.control,mis:!!e.miscontrol,rel:e.relativeSpeed,own:e.type==='goal'?(e.lastTeam&&e.lastTeam!==e.team):undefined});
  if(e.channel==='body_contact'&&e.players[0][0]===e.players[1][0])body.push({t:e.tick,pair:e.players.slice().sort().join('-')});
  if(e.channel==='decision'&&label==='l21'){const o=e.observation;const kd=chooseK(o);if(kd.kind!==e.decision.kind){const b=o.ball,p=o.self;const db=d2(p,b);
    const col=o.people.filter(q=>q.team===p.team&&d2(q,b)<2.1&&q.seenTick===o.tick&&d2(q,b)<db).map(q=>{const d=d2(q,b)||1e-6,ux=(b.x-q.x)/d,uy=(b.y-q.y)/d,bvx=b.velocityKnown?b.vx:0,bvy=b.velocityKnown?b.vy:0;
      return {id:q.id,d:+d.toFixed(2),relClosing:+((q.vx-bvx)*ux+(q.vy-bvy)*uy).toFixed(2),qSpeed:+Math.hypot(q.vx,q.vy).toFixed(2),ballSpeed:b.velocityKnown?+Math.hypot(b.vx,b.vy).toFixed(2):null,alongside:Math.abs((q.vx-bvx)*ux+(q.vy-bvy)*uy)<0.5&&d>0.6,
       nearestOppToBall:Math.min(99,...o.people.filter(x=>x.team!==p.team).map(x=>+d2(x,b).toFixed(2)))};});
    yields.push({t:e.tick,p:e.player,from:kd.kind,to:e.decision.kind,selfD:+db.toFixed(2),ballAge:o.tick-b.seenTick,velKnown:b.velocityKnown,collectors:col});}}};
 const eng=restore(text,sink);const t0=eng.tick;
 for(let i=0;i<H&&!eng.finished;i++){eng.step();const s=eng.physicalSnapshot();if(i%2===0)frames.push({t:eng.tick,ph:s.phase,ball:[+s.ball.x.toFixed(2),+s.ball.y.toFixed(2)],p:s.players.map(q=>[q.id,+q.x.toFixed(2),+q.y.toFixed(2),+q.vx.toFixed(2),+q.vy.toFixed(2)])});}
 const ctrl=ev.filter(x=>(x.type==='kick'||x.type==='contact')&&x.ctrl);
 const possAt=t=>{const c=ctrl.filter(x=>x.t<=t0+t);const r=ev.filter(x=>x.type==='restart_placement'&&x.t<=t0+t);if(r.length&&(!c.length||r.at(-1).t>=c.at(-1).t))return 'restart:'+r.at(-1).team;return c.length?c.at(-1).team:'none';};
 out[label]={t0,poss3:possAt(60),poss6:possAt(120),events:ev,yields,sameTeamBody:body,frames};}
fs.writeFileSync(outF,JSON.stringify(out));
console.log(JSON.stringify({state:path.basename(stateF),team,base:out.base.poss6,k20:out.k20.poss6,l21:out.l21.poss6,yields:out.l21.yields.length}));
