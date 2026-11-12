import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const dir=process.argv[2];const meta=JSON.parse(fs.readFileSync(path.join(dir,'meta.json')));const a=JSON.parse(fs.readFileSync(path.join(dir,'analysis.json')));
const b=zlib.gunzipSync(fs.readFileSync(path.join(dir,'pos.i16.gz')));const pos=new Int16Array(b.buffer,b.byteOffset,b.byteLength/2);const W=47,S=50;
const X=(i,j)=>pos[i*W+2*j]/S,Y=(i,j)=>pos[i*W+2*j+1]/S;
const evs=fs.readFileSync(path.join(dir,'events.jsonl'),'utf8').split('\n').filter(Boolean).map(JSON.parse);
const kicks=evs.filter(e=>e.type==='kick');
const out=[];
for(const g of evs.filter(e=>e.type==='goal')){const shot=[...kicks].reverse().find(k=>k.tick<=g.tick);const st=shot.tick;const att=g.team,def=att==='A'?'B':'A';const di=def==='A'?0:11;const gx=X(st,di)<52.5?0:105;
 const dfd=[...Array(10).keys()].map(k=>k+di+1);const bx=pos[st*W+44]/S,by=pos[st*W+45]/S;const bd=Math.abs(bx-gx);
 const goalSide=dfd.filter(j=>Math.abs(X(st,j)-gx)<bd).length;const block=dfd.filter(j=>Math.abs(X(st,j)-gx)<bd&&Math.abs(Y(st,j)-by)<3+ (Math.abs(Y(st,j)-34)<4?3:0)).length;
 const nearShooter=Math.min(...dfd.map(j=>Math.hypot(X(st,j)-bx,Y(st,j)-by)));
 // last turnover before shot
 const tv=[...a.transitions].reverse().find(t=>t.tick<=st&&t.winner===att);const rs=[...a.restarts].reverse().find(r=>r.takenTick!=null&&r.takenTick<=st);
 const origin=(tv&&(!rs||tv.tick>rs.takenTick))?`turnover ${((st-tv.tick)/20).toFixed(1)}s before by ${tv.player}(${tv.how})`:`restart ${rs?.kind} ${((st-(rs?.takenTick??0))/20).toFixed(1)}s before`;
 out.push({goalTick:g.tick,shotTick:st,shooter:shot.player,kind:shot.kind,team:att,shotDist:+bd.toFixed(1),shotY:+by.toFixed(1),defGoalSide:goalSide,nearestDef:+nearShooter.toFixed(1),origin,gkDist:+Math.hypot(X(st,di)-bx,Y(st,di)-by).toFixed(1)});}
console.log(JSON.stringify(out));
