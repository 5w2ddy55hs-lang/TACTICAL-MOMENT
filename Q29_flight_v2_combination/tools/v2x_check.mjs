// C2 for v2x: on every saved own-observation DTO, choose(v2x) must equal choose(I17) when (own latest witnessed touch is
// self AND tClosest<=0), and equal choose(V2) otherwise. Also counts how many V2-vs-I17 differences remain under v2x.
// usage: node v2x_check.mjs <setDir> <out.json> <recording.json.gz>...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,outF,...recs]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research','l21_natural/recovered/l21_receive_compare/branches/'+p));
const C={i17:(await import(R('base_off/decision.mjs'))).choose,v2:(await import(R('base_on/decision.mjs'))).choose,v2x:(await import(R('q29c_v2x/decision.mjs'))).choose};
const DT=.05,clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),J=JSON.stringify;
const t={dtos:0,ownAndPassed:0,v2xEqI17_whenOwnAndPassed:0,v2xEqV2_otherwise:0,other:0,v2DiffI17:0,v2xDiffI17:0,v2xDiffI17_ownLast:0,violations:0};const viol=[],remaining=[];
for(const f of recs){const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(f)));for(const r of x.rows){if(r.channel!=='decision'||!r.observation?.ball)continue;const o=r.observation,p=o.self,b=o.ball;t.dtos++;
 const own=!!p.observedTouch&&p.observedTouch.players.length>0&&p.observedTouch.players.every(q=>q.id===p.id);let passed=false;
 if(b.velocityKnown){const age=(o.tick-b.seenTick)*DT,vx=clamp(b.vx,-40,40),vy=clamp(b.vy,-40,40),sp=Math.hypot(vx,vy);const bx=b.x+vx*age,by=b.y+vy*age;passed=-((bx-p.x)*vx+(by-p.y)*vy)/(sp*sp)<=0;}
 const a=J(C.i17(structuredClone(o))),v=J(C.v2(structuredClone(o))),w=J(C.v2x(structuredClone(o)));
 if(v!==a)t.v2DiffI17++;if(w!==a){t.v2xDiffI17++;if(own)t.v2xDiffI17_ownLast++;remaining.push({rec:path.basename(f),tick:r.tick,player:p.id,ownLast:own});}
 if(own&&passed){t.ownAndPassed++;if(w===a)t.v2xEqI17_whenOwnAndPassed++;else{t.violations++;viol.push({rec:path.basename(f),tick:r.tick,player:p.id,case:'own&passed'});}}
 else{t.other++;if(w===v)t.v2xEqV2_otherwise++;else{t.violations++;viol.push({rec:path.basename(f),tick:r.tick,player:p.id,case:'other'});}}}}
fs.writeFileSync(outF,JSON.stringify({tally:t,violations:viol.slice(0,10),remainingV2xDifferences:remaining},null,1));console.log(JSON.stringify(t,null,1),'violations',viol.length);
