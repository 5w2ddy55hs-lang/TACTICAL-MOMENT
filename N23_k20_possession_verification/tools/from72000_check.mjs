// Direct check for the late-31337 opportunities: restore save_72000.json with the L21 research engine, step to each
// manifest opportunity tick (t >= 72000) and compare stateHash and the yielder's decision (L21 vs K20 choose on the
// identical DTO) with the manifest made from the fresh run from seed.
// usage: node from72000_check.mjs <l21dir> <k20dir> <save_72000.json> <manifest.json> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [L21,K20,saveF,manF,outF]=process.argv.slice(2);
const {MatchEngine}=await import(path.join(L21,'engine.mjs'));const {choose:chooseK}=await import(path.join(K20,'decision.mjs'));
const man=JSON.parse(fs.readFileSync(manF,'utf8'));const rows=man.rows.filter(r=>r.t>=72000);const want=new Map(rows.map(r=>[r.t,r]));
let cur=null;const res=[];
const e=MatchEngine.restore(fs.readFileSync(saveF,'utf8'),ev=>{if(!cur||ev.channel!=='decision'||ev.tick!==cur.t)return;if(ev.player!==cur.pid)return;const kd=chooseK(ev.observation);cur.l21=ev.decision.kind;cur.k20=kd.kind;});
const restoredTick=e.tick,restoredHash=e.stateHash();
while(!e.finished&&e.tick<=Math.max(...want.keys())){
 if(want.has(e.tick)){const r=want.get(e.tick);cur={t:e.tick,pid:r.label.split(':')[1],hash:e.stateHash()};e.step();
  res.push({t:r.t,label:r.label,stateHashEqual:cur.hash===r.stateHash,yieldReproduced:cur.l21!==cur.k20&&cur.l21===r.decision.l21.kind&&cur.k20===r.decision.k20.kind});cur=null;}else e.step();}
const out={save:path.basename(saveF),restoredTick,restoredHash,opportunities:res.length,allStateHashEqual:res.every(r=>r.stateHashEqual),allYieldReproduced:res.every(r=>r.yieldReproduced),rows:res};
fs.writeFileSync(outF,JSON.stringify(out,null,1));console.log(JSON.stringify({restoredTick,opportunities:res.length,allStateHashEqual:out.allStateHashEqual,allYieldReproduced:out.allYieldReproduced}));
