// For each normal pass in an I18 run: was the intended target itself rewritten (I18 support) during flight?
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const dir=process.argv[2];const meta=JSON.parse(fs.readFileSync(path.join(dir,'meta.json')));
const b=zlib.gunzipSync(fs.readFileSync(path.join(dir,'dec.u8.gz')));const dec=new Uint8Array(b.buffer,b.byteOffset,b.byteLength);
const R=meta.decisionDict.map(s=>s.split('|').slice(1).join('|'));const idx=new Map(meta.ids.map((x,i)=>[x,i]));
const fm=JSON.parse(fs.readFileSync(path.join(dir,'flight_metrics.json')));const out=[];
for(const p of fm.passes){if(!p.target)continue;const j=idx.get(p.target);const t1=p.t+Math.round(p.flight*20);let rw=0;for(let i=p.t+1;i<=t1;i++)if(R[dec[i*22+j]].startsWith('I18_'))rw++;out.push({flight:p.flight,outcome:p.outcome,targetRewriteTicks:rw});}
console.log(JSON.stringify(out));
