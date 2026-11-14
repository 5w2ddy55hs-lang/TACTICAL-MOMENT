// Which arms' public fromFixture accept the exact native state of a SOURCE arm's run at each tick (read only).
// The source run itself is started like the set's run.mjs: base_off.restore(input).exportState() -> source.fromFixture.
// Nothing is relabelled and no check is skipped; a rejection is recorded with its message.
// usage: node fixture_accept.mjs <setDir> <inputSave> <sourceArm> <fromTick> <toTick> <arm,arm,...> [compareArm]
//   compareArm: also report whether that arm's own run (from the input) has the identical native state at each tick.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {pathToFileURL} from 'node:url';
const [SET,inputF,src,fromS,toS,armsS,cmpArm]=process.argv.slice(2);const engines=JSON.parse(fs.readFileSync(path.join(SET,'engines.json')));
const load=async a=>(await import(pathToFileURL(path.join(SET,'research',engines[a])))).MatchEngine;
const B=await load('base'),arms=armsS.split(','),E={};for(const a of [...arms,src,...(cmpArm?[cmpArm]:[])])E[a]=await load(a);
const native0=B.restore(fs.readFileSync(inputF,'utf8')).exportState();const sha=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const s=E[src].fromFixture(native0),c=cmpArm?E[cmpArm].fromFixture(native0):null;const out=[];
while(s.tick<+toS){if(s.tick>=+fromS){const n=s.exportState(),row={tick:s.tick,sourceNativeSha256:sha(n)};
  for(const a of arms){try{const e=E[a].fromFixture(n);row[a]=JSON.stringify(e.exportState())===JSON.stringify(n)?'accepted':'accepted_but_not_exact';}catch(x){row[a]=x.message;}}
  if(c)row['sameAs_'+cmpArm+'_run']=JSON.stringify(c.exportState())===JSON.stringify(n);out.push(row);}
 s.step();if(c)c.step();}
for(const r of out)console.log(JSON.stringify(r));
