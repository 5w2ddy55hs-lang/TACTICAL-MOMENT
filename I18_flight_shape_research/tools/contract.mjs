// I18 contract checks: pre-claim identity with standard, first divergence = first claim, save isolation, save/restore continuity.
import fs from 'node:fs';
const W='<I17>';const g=await import(W+'/research_guard.mjs');await g.register('standard');
const {MatchEngine:B}=await import('<BRANCH>/engine.mjs');
const {MatchEngine:Std}=await import(W+'/source/integration_i8_standard/core/engine.mjs');
const out={};
for(const seed of [771,1847]){
 let firstClaim=null;const claims=[];
 const sinkB=ev=>{if(ev.channel==='decision'&&ev.decision.reason==='I18_witnessed_teammate_kick_uncontested'){claims.push(ev.tick);if(firstClaim===null)firstClaim=ev.tick;}};
 const a=g.create('standard',{seed}),b=new B({seed},sinkB);
 let firstDiff=null;
 for(let i=0;i<3000&&firstDiff===null;i++){a.step();b.step();const pa=a.physicalSnapshot(),pb=b.physicalSnapshot();if(JSON.stringify(pa)!==JSON.stringify(pb))firstDiff=a.tick;}
 out[seed]={firstClaimDecisionTick:firstClaim,firstPhysicalDifferenceTick:firstDiff,claimsBeforeDiff:claims.filter(t=>t<=(firstDiff??1e9)).length,consistent:firstClaim!==null&&firstDiff!==null&&firstDiff>firstClaim};
}
// save isolation and continuity
const b=new B({seed:771});for(let i=0;i<700;i++)b.step();const sb=b.save();
const s=g.create('standard',{seed:771});for(let i=0;i<700;i++)s.step();const ss=s.save();
const tryR=(C,t)=>{try{C.restore(t);return 'ACCEPTED';}catch(e){return 'REJECTED:'+String(e.message).slice(0,60);}};
out.standardRestoresI18Save=tryR(Std,sb);out.i18RestoresStandardSave=tryR(B,ss);
const r=B.restore(sb);for(let i=0;i<300;i++){b.step();r.step();}
out.i18SaveRestoreContinuity300=JSON.stringify(b.physicalSnapshot())===JSON.stringify(r.physicalSnapshot())&&b.stateHash()===r.stateHash();
out.i18ExportSchema=b.exportState().schema.slice(-40);out.i18Config=b.exportState().config;
console.log(JSON.stringify(out,null,1));
