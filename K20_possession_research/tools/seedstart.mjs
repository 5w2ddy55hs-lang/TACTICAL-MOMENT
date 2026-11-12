// write a tick-0 save for seed (so probes can start from the beginning)
import fs from 'node:fs';import path from 'node:path';
const [I17,variant,seed,out]=process.argv.slice(2);const g=await import(path.join(I17,'research_guard.mjs'));await g.register(variant);
const e=g.create(variant,{seed:+seed,zonalDefence:false});fs.writeFileSync(out,g.save(e,variant));
