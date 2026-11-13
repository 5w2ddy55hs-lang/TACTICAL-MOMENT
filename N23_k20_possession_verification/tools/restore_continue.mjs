import fs from 'node:fs';import path from 'node:path';
const [dir,saveF,to]=process.argv.slice(2);const {MatchEngine}=await import(path.join(dir,'engine.mjs'));
const e=MatchEngine.restore(fs.readFileSync(saveF,'utf8'));const h0=e.stateHash();const t0=e.tick;const cp={};
while(e.tick<+to&&!e.finished){e.step();if(e.tick%6000===0)cp[e.tick]=e.stateHash();}
console.log(JSON.stringify({save:path.basename(saveF),restoredTick:t0,restoredHash:h0,checkpoints:cp,final:e.stateHash()}));
