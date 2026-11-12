import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [a,b]=process.argv.slice(2);const rd=d=>{const x=zlib.gunzipSync(fs.readFileSync(path.join(d,'pos.i16.gz')));return new Int16Array(x.buffer,x.byteOffset,x.byteLength/2);};
const A=rd(a),B=rd(b),W=47;const n=Math.min(A.length,B.length)/W;let first=-1;
for(let i=0;i<n&&first<0;i++)for(let j=0;j<W;j++)if(A[i*W+j]!==B[i*W+j]){first=i;break;}
const ev=d=>fs.readFileSync(path.join(d,'events.jsonl'),'utf8').split('\n').filter(Boolean).map(JSON.parse).filter(e=>e.type==='restart_placement'||e.type==='kick'&&e.kind!=='dribble');
const ea=ev(a).filter(e=>e.tick<=first+5).slice(-3),eb=ev(b).filter(e=>e.tick<=first+5).slice(-3);
console.log(JSON.stringify({a:path.basename(a),b:path.basename(b),firstDivergentTick:first,lastEventsA:ea.map(e=>[e.tick,e.type,e.kind,e.player??e.taker]),lastEventsB:eb.map(e=>[e.tick,e.type,e.kind,e.player??e.taker])}));
