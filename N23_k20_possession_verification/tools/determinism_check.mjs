// Does calling save()/exportState()/physicalSnapshot() change a match's trajectory? Run one engine from seed
// under a given "observation regime" and record stateHash at checkpoints (computed AFTER the regime's own calls,
// and the checkpoint hashing itself is the same in every regime).
// usage: node determinism_check.mjs <engineDir|standard:I17> <seed> <maxTick> <regime> <out.json> [triggerFile]
//   regime: none | save6000 (like rec_any: physicalSnapshot every tick + save every 6000) | triggers (save at listed ticks, like paired_from_branch)
import fs from 'node:fs';import path from 'node:path';
const [spec,seedS,maxS,regime,outF,trigF]=process.argv.slice(2);
let E;if(spec.startsWith('standard:')){const I17=spec.slice(9);const {MatchEngine}=await import(path.join(I17,'source/integration_i8_standard/core/engine.mjs'));E=MatchEngine;}else{E=(await import(path.join(spec,'engine.mjs'))).MatchEngine;}
const trig=trigF?new Set(JSON.parse(fs.readFileSync(trigF)).map(x=>x.t)):new Set();
const sinkEvents=[];const e=new E({seed:+seedS,zonalDefence:false},ev=>{if(ev.channel==='event'&&ev.type==='kick')sinkEvents.push(ev.tick);});
const checkpoints={};const savesHash={};let saves=0;
for(let i=0;i<+maxS&&!e.finished;i++){
 if(regime==='save6000'&&i>0&&i%6000===0){const t=e.save();saves++;if(i===72000)savesHash[i]=t;}
 if(regime==='triggers'&&trig.has(e.tick)){e.save();saves++;}
 e.step();
 if(regime==='save6000')e.physicalSnapshot();
 if(e.tick%6000===0)checkpoints[e.tick]=e.stateHash();
}
fs.writeFileSync(outF,JSON.stringify({spec:path.basename(spec),seed:+seedS,regime,saves,checkpoints,kicks:sinkEvents.length,final:e.stateHash(),tick:e.tick}));
if(savesHash[72000])fs.writeFileSync(outF.replace('.json','_save72000.json'),savesHash[72000]);
console.log(JSON.stringify({regime,saves,tick:e.tick,final:e.stateHash()}));
