// Q29C: is "dribble aimed at a side-clamped target near the touchline, ball goes out" a repeating I17 structure independent
// of V2? Scan recordings for dribble kicks whose chosen carry target was clamped to the field edge (x .2/104.8 or y .2/67.8,
// from outgoing_candidates_legacy.mjs), and whether the ball left play before anyone else touched it. Read only.
// usage: node touchline_dribbles.mjs <out.json> <recording.json.gz>...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [outF,...recs]=process.argv.slice(2);const rows=[];const r2=v=>+v.toFixed(2);
for(const f of recs){const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(f)));const dec=x.rows.filter(r=>r.channel==='decision'),ev=x.rows.filter(r=>r.channel==='event');const F=new Map(x.frames.map(q=>[q.tick,q]));
 for(const k of ev.filter(e=>e.type==='kick'&&e.kind==='dribble')){const d=dec.filter(r=>r.player===k.player&&r.tick<=k.tick&&r.tick>=k.tick-6).at(-1);if(!d)continue;
  const t=d.decision.kind==='dribble'?d.decision.target:d.decision.ballActionIntent?.kind==='dribble'?d.decision.ballActionIntent.target:null;if(!t)continue;
  const clamped=Math.abs(t.y-67.8)<1e-6||Math.abs(t.y-.2)<1e-6||Math.abs(t.x-104.8)<1e-6||Math.abs(t.x-.2)<1e-6;
  const after=ev.filter(e=>e.tick>k.tick&&(e.type==='restart_placement'||e.type==='goal'||(e.type==='kick')||(e.type==='contact'&&e.control)));const nx=after[0]??null;
  const p=F.get(k.tick)?.players.find(q=>q.id===k.player);const edge=p?Math.min(p.y,68-p.y,p.x,105-p.x):null;
  rows.push({rec:path.basename(f),tick:k.tick,player:k.player,target:{x:r2(t.x),y:r2(t.y)},clamped,edgeDistance:edge==null?null:r2(edge),next:nx?{tick:nx.tick,type:nx.type,player:nx.player??null,kind:nx.kind??null}:null,outBeforeAnyTouch:!!nx&&nx.type==='restart_placement'});}}
fs.writeFileSync(outF,JSON.stringify(rows,null,1));
const c=rows.filter(r=>r.clamped),o=rows.filter(r=>r.outBeforeAnyTouch);
console.log(JSON.stringify({dribbleKicks:rows.length,clampedTarget:c.length,clampedAndOut:c.filter(r=>r.outBeforeAnyTouch).length,outBeforeAnyTouch:o.length,outWithUnclampedTarget:o.filter(r=>!r.clamped).length,nearEdgeLT4m:rows.filter(r=>r.edgeDistance!=null&&r.edgeDistance<4).length,nearEdgeLT4mClamped:rows.filter(r=>r.edgeDistance!=null&&r.edgeDistance<4&&r.clamped).length}));
for(const r of rows.filter(r=>r.clamped||r.outBeforeAnyTouch))console.log(` ${r.rec} ${r.tick} ${r.player} tgt(${r.target.x},${r.target.y}) clamped=${r.clamped} edge=${r.edgeDistance} next=${r.next?`${r.next.tick} ${r.next.type} ${r.next.player??''} ${r.next.kind??''}`:'-'} out=${r.outBeforeAnyTouch}`);
