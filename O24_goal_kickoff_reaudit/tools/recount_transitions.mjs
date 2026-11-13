// O24: natural-match "turnovers" of the shared audit analyzer (tools/analyze.mjs, used by the I17 audit and the
// J19/K20/L21/M22/I18 natural comparisons). A turnover = in-play controlled action (kick, or contact with control,
// throw-ins as kicks) by the other team than the previous in-play controlled action. Restarts do NOT reset the
// sequence, so after a goal the conceding team's first in-play controlled action (after its kickoff) is counted as a
// turnover "won" by the conceding team. This script re-derives the turnovers exactly as analyze.mjs does (validated
// against analysis.json tick by tick) and labels each by what lies between it and the previous in-play controlled
// action:  AFTER_GOAL (a goal event)  /  AFTER_RESTART:<kind> (another restart placement)  /  IN_PLAY.
// loserRegainTick and winnerShot10s are taken from analysis.json (unchanged definitions).
// usage: node recount_transitions.mjs <out.json> <runDir>...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const [outF,...dirs]=process.argv.slice(2);const out={};
for(const dir of dirs){
 const meta=JSON.parse(fs.readFileSync(path.join(dir,'meta.json')));const phase=zlib.gunzipSync(fs.readFileSync(path.join(dir,'phase.u8.gz')));
 const PLAY=meta.phaseCodes.indexOf('play');
 const evs=fs.readFileSync(path.join(dir,'events.jsonl'),'utf8').split('\n').filter(Boolean).map(l=>JSON.parse(l));
 const contactRows=evs.filter(e=>e.type==='contact');const kicks=evs.filter(e=>e.type==='kick');
 const touches=[];{const last=new Map();for(const c of contactRows){const L=last.get(c.player);if(L&&c.tick-L.end<=2){L.end=c.tick;L.control=L.control||c.control;continue;}
  const T={kind:'contact',tick:c.tick,end:c.tick,player:c.player,team:c.team,control:!!c.control};touches.push(T);last.set(c.player,T);}}
 const throws=evs.filter(e=>e.type==='throw_in_play').map(e=>({kind:'kick',tick:e.tick,player:e.player,team:e.team,kk:'throw_in'}));
 const actions=[...touches,...throws,...kicks.map(k=>({kind:'kick',tick:k.tick,player:k.player,team:k.team,kk:k.kind}))].sort((a,b)=>a.tick-b.tick||(a.kind==='kick')-(b.kind==='kick'));
 const goals=evs.filter(e=>e.type==='goal').map(e=>({t:e.tick,team:e.team}));const rps=evs.filter(e=>e.type==='restart_placement').map(e=>({t:e.tick,kind:e.kind,team:e.team}));
 const tov=[];let prev=0,prevT=null;
 for(const a of actions){if(phase[a.tick]!==PLAY)continue;if(!(a.kind==='kick'||a.control))continue;const t=a.team==='A'?1:2;
  if(prev&&t!==prev){const g=goals.filter(x=>x.t>prevT&&x.t<=a.tick);const r=rps.filter(x=>x.t>prevT&&x.t<=a.tick);
   const label=g.length?'AFTER_GOAL':(r.length?'AFTER_RESTART:'+r.at(-1).kind:'IN_PLAY');
   tov.push({tick:a.tick,winner:a.team,label,goalAgainstWinner:g.length?g.some(x=>x.team!==a.team):null,prevTick:prevT});}
  prev=t;prevT=a.tick;}
 const an=JSON.parse(fs.readFileSync(path.join(dir,'analysis.json')));const tr=an.transitions;
 const valid=tr.length===tov.length&&tr.every((x,i)=>x.tick===tov[i].tick&&x.winner===tov[i].winner);
 const rows=tov.map((x,i)=>({...x,loserRegain2s:!!(tr[i].loserRegainTick&&tr[i].loserRegainTick-tr[i].tick<=40),winnerShot10s:!!tr[i].winnerShot10s,gs0:tr[i].loserGoalSide[0],gs100:tr[i].loserGoalSide[2],allPlay5s:!!tr[i].allPlay5s}));
 const gsSum=f=>{const R=rows.filter(f);return {n:R.length,gs0:R.reduce((q,r)=>q+r.gs0,0),gs100:R.reduce((q,r)=>q+r.gs100,0)};};const playSeconds=an.summary.playSeconds;
 const sum=f=>rows.filter(f).length;const C={};for(const r of rows)C[r.label]=(C[r.label]||0)+1;
 out[path.basename(dir)]={validAgainstAnalysis:valid,goals:goals.length,turnovers:rows.length,byLabel:C,
  loserRegain2s:sum(r=>r.loserRegain2s),transitionsShot10s:sum(r=>r.winnerShot10s),
  afterGoal:{n:sum(r=>r.label==='AFTER_GOAL'),wonByConcedingTeam:sum(r=>r.label==='AFTER_GOAL'&&r.goalAgainstWinner),loserRegain2s:sum(r=>r.label==='AFTER_GOAL'&&r.loserRegain2s),shot10s:sum(r=>r.label==='AFTER_GOAL'&&r.winnerShot10s)},
  corrected:{turnovers:sum(r=>r.label!=='AFTER_GOAL'),loserRegain2s:sum(r=>r.label!=='AFTER_GOAL'&&r.loserRegain2s),transitionsShot10s:sum(r=>r.label!=='AFTER_GOAL'&&r.winnerShot10s)},
  playSeconds,loserGoalSideSums:{all:gsSum(r=>true),corrected:gsSum(r=>r.label!=='AFTER_GOAL'),allPlay5s:gsSum(r=>r.allPlay5s),allPlay5sCorrected:gsSum(r=>r.allPlay5s&&r.label!=='AFTER_GOAL')},
  inPlayOnly:{turnovers:sum(r=>r.label==='IN_PLAY'),loserRegain2s:sum(r=>r.label==='IN_PLAY'&&r.loserRegain2s),transitionsShot10s:sum(r=>r.label==='IN_PLAY'&&r.winnerShot10s)}};
 console.log(path.basename(dir),JSON.stringify({valid,turnovers:rows.length,afterGoal:out[path.basename(dir)].afterGoal,goals:goals.length}));}
fs.writeFileSync(outF,JSON.stringify(out,null,1));
