// L21 vs M22 per-tick identity until first decision difference; report that decision's DTO evidence.
import path from 'node:path';
const [L21,M22,seedS]=process.argv.slice(2);const {MatchEngine:A}=await import(path.join(L21,'engine.mjs'));const {MatchEngine:B}=await import(path.join(M22,'engine.mjs'));
const da={},db={};let ob=null;const key=d=>JSON.stringify(d);
const a=new A({seed:+seedS},e=>{if(e.channel==='decision')da[e.tick+':'+e.player]=key(e.decision);});
const b=new B({seed:+seedS},e=>{if(e.channel==='decision'){db[e.tick+':'+e.player]=key(e.decision);ob=ob||{};ob[e.tick+':'+e.player]=e.observation;}});
let first=null,hash=null,n=0;
for(let i=0;i<30000&&hash===null;i++){if(a.stateHash()!==b.stateHash()){hash=a.tick;break;}n++;a.step();b.step();if(!first)for(const k of Object.keys(db))if(da[k]!==db[k]){first=k;break;}ob={};}
console.log(JSON.stringify({seed:+seedS,ticksIdentical:n,firstDecisionDifference:first,firstHashDifferenceTick:hash,consistent:!!first&&+first.split(':')[0]<hash}));
