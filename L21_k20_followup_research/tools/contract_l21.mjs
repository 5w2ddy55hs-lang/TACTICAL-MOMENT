// K20 contract: (1) per-tick full-state identity (stateHash incl. RNG streams and event log; eventDigest; rng states)
// with standard until the first differing decision; (2) save identity separation; (3) save->restore continuity;
// (4) recorded active config.
// usage: node contract_k20.mjs <I17> <branch> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,outF]=process.argv.slice(2);
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {MatchEngine:Std}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));
const {MatchEngine:K}=await import(path.join(BR,'engine.mjs'));
const out={};
for(const seed of [771,1847,31337]){
 const da={},db={};const key=d=>d.kind+'|'+(d.target?d.target.x.toFixed(4)+','+d.target.y.toFixed(4):'');
 const a=g.create('standard',{seed},ev=>{if(ev.channel==='decision')da[ev.tick+':'+ev.player]=key(ev.decision);});
 const b=new K({seed},ev=>{if(ev.channel==='decision')db[ev.tick+':'+ev.player]=key(ev.decision);});
 let firstDecisionDiff=null,firstHashDiff=null,hashChecks=0,rngEqualBefore=null,eventDigestEqualBefore=null;
 for(let i=0;i<20000&&firstHashDiff===null;i++){
  const sa=a.exportState(),sb=b.exportState();
  if(a.stateHash()!==b.stateHash()){firstHashDiff=a.tick;break;}hashChecks++;
  rngEqualBefore=JSON.stringify(sa.players.map(p=>p.rng))===JSON.stringify(sb.players.map(p=>p.rng));eventDigestEqualBefore=sa.eventDigest===sb.eventDigest&&sa.eventCount===sb.eventCount;
  a.step();b.step();
  if(firstDecisionDiff===null){for(const k of Object.keys(db))if(da[k]!==db[k]){firstDecisionDiff=k;break;}}
 }
 out[seed]={firstDecisionDifference:firstDecisionDiff,firstStateHashDifferenceTick:firstHashDiff,ticksWithIdenticalStateHash:hashChecks,rngStreamsIdenticalAtLastEqualTick:rngEqualBefore,eventDigestAndCountIdenticalAtLastEqualTick:eventDigestEqualBefore,consistent:firstDecisionDiff!==null&&firstHashDiff!==null&&+firstDecisionDiff.split(':')[0]<firstHashDiff};
}
const b=new K({seed:771});for(let i=0;i<700;i++)b.step();const sb=b.save();
const s=g.create('standard',{seed:771});for(let i=0;i<700;i++)s.step();const ss=s.save();
const tryR=(C,t)=>{try{C.restore(t);return 'ACCEPTED';}catch(e){return 'REJECTED:'+String(e.message).slice(0,60);}};
out.standardRestoresL21Save=tryR(Std,sb);out.l21RestoresStandardSave=tryR(K,ss);
const r=K.restore(sb);for(let i=0;i<600;i++){b.step();r.step();}
out.l21SaveRestoreContinuity600={stateHashEqual:b.stateHash()===r.stateHash(),eventDigestEqual:b.exportState().eventDigest===r.exportState().eventDigest,rngEqual:JSON.stringify(b.exportState().players.map(p=>p.rng))===JSON.stringify(r.exportState().players.map(p=>p.rng))};
out.l21ActiveConfig=b.exportState().config;out.l21SaveSchema=JSON.parse(sb).schema;out.l21Engine=JSON.parse(sb).engine;
fs.writeFileSync(outF,JSON.stringify(out,null,1));console.log(JSON.stringify(out,null,1));
