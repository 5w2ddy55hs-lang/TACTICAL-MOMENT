// Reproduction manifest for M22 opportunities: run L21 from seed; at each trigger tick (state BEFORE the step whose
// decisions define the yield) record stateHash, save SHA-256 (optionally write the save), and the yielder's decision
// (L21 kind/target/score) vs K20 choose() on the identical DTO, plus a SHA-256 of the canonical DTO.
// usage: node opportunity_manifest.mjs <l21dir> <k20dir> <seed> <triggerFile...> --out <manifest.json> [--saves <dir> --from <tick>]
import fs from 'node:fs';import path from 'node:path';import {createHash} from 'node:crypto';
const args=process.argv.slice(2);const L21=args[0],K20=args[1],seed=+args[2];
const oi=args.indexOf('--out'),si=args.indexOf('--saves'),fi=args.indexOf('--from');
const trigFiles=args.slice(3,Math.min(...[oi,si,fi].filter(i=>i>0)));const outF=args[oi+1];const saveDir=si>0?args[si+1]:null;const fromT=fi>0?+args[fi+1]:Infinity;
const sha=s=>createHash('sha256').update(s).digest('hex');
const canon=x=>{if(Array.isArray(x))return '['+x.map(canon).join(',')+']';if(x&&typeof x==='object')return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canon(x[k])).join(',')+'}';return JSON.stringify(x);};
const {MatchEngine}=await import(path.join(L21,'engine.mjs'));const {choose:chooseK}=await import(path.join(K20,'decision.mjs'));
const trig=new Map();for(const f of trigFiles)for(const x of JSON.parse(fs.readFileSync(f)))trig.set(x.t,{...x,source:path.basename(f)});
let cur=null;const rows=[];
const e=new MatchEngine({seed,zonalDefence:false},ev=>{if(!cur||ev.channel!=='decision'||ev.tick!==cur.t)return;const pid=cur.label.split(':')[1];if(ev.player!==pid)return;
 const o=ev.observation,kd=chooseK(o),d=ev.decision;cur.decision={l21:{kind:d.kind,target:d.target?[d.target.x,d.target.y]:null,score:d.score,reason:d.reason},k20:{kind:kd.kind,target:kd.target?[kd.target.x,kd.target.y]:null,score:kd.score},yieldReproduced:kd.kind!==d.kind,dtoSha256:sha(canon(o))};});
while(!e.finished&&e.tick<=Math.max(...trig.keys())){
 if(trig.has(e.tick)){const x=trig.get(e.tick);const text=e.save();cur={t:e.tick,team:x.team,label:x.label,source:x.source,stateHash:e.stateHash(),saveSha256:sha(text),decision:null};
  if(saveDir&&e.tick>=fromT){fs.mkdirSync(saveDir,{recursive:true});const f=`l21_${seed}_opp_${e.tick}.json`;fs.writeFileSync(path.join(saveDir,f),text);cur.saveFile=f;}
  e.step();rows.push(cur);cur=null;}else e.step();}
fs.writeFileSync(outF,JSON.stringify({engine:'L21 (research, not adopted)',seed,node:process.version,platform:process.platform+' '+process.arch,count:rows.length,yieldReproducedAll:rows.every(r=>r.decision&&r.decision.yieldReproduced),rows},null,1));
console.log(JSON.stringify({seed,count:rows.length,missingDecision:rows.filter(r=>!r.decision).length,yieldNotReproduced:rows.filter(r=>r.decision&&!r.decision.yieldReproduced).length,saved:rows.filter(r=>r.saveFile).length}));
