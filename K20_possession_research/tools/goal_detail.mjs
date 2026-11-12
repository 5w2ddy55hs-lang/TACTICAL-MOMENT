import fs from 'node:fs';import path from 'node:path';
const [BR,stateF,to]=process.argv.slice(2);const m=await import(path.join(BR,'engine.mjs'));const id=await import(path.join(BR,'pass_build_identity.mjs'));
let x=JSON.parse(fs.readFileSync(stateF,'utf8'));if(x.inner)x=JSON.parse(x.inner);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;
const evs=[];const e=m.MatchEngine.restore(JSON.stringify(x),ev=>{if(ev.channel==='event'&&['kick','contact','goal'].includes(ev.type)&&ev.tick>=94820)evs.push({t:ev.tick,type:ev.type,p:ev.player,team:ev.team,kind:ev.kind,ctrl:ev.control,lastTouch:ev.lastTouch,lastTeam:ev.lastTeam,mis:ev.miscontrol});});
while(e.tick<+to)e.step();const seen=new Set();console.log(JSON.stringify(evs.filter(v=>{const k=v.t+v.type+v.p;if(seen.has(k))return false;seen.add(k);return true;})));
