// Advance an unchanged standard save to tick T and write a standard save at T (shared starting state).
import fs from 'node:fs';import path from 'node:path';
const [I17,saveF,T,out]=process.argv.slice(2);const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const e=g.restore(fs.readFileSync(saveF,'utf8'),'standard');while(e.tick<+T)e.step();fs.writeFileSync(out,g.save(e,'standard'));console.log('state',e.tick,out);
