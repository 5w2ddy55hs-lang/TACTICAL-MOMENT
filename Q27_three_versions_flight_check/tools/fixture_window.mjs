// For a state the candidate rejects: run the UNCHANGED baseline from the input save tick by tick and, at every tick up to
// a limit, ask whether the candidate's public fromFixture accepts the baseline's exact native state. Read only.
// usage: node fixture_window.mjs <setDir> <inputSave> <maxTicks> <out.json>
import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';
const [SET,inputF,maxS,outF]=process.argv.slice(2);const engines=JSON.parse(fs.readFileSync(path.join(SET,'engines.json')));
const B=(await import(pathToFileURL(path.join(SET,'research',engines.base)))).MatchEngine,E=(await import(pathToFileURL(path.join(SET,'research',engines.flight)))).MatchEngine;
const b=B.restore(fs.readFileSync(inputF,'utf8'));const rows=[];
for(let i=0;i<=+maxS;i++){const n=b.exportState();let r='accepted';try{E.fromFixture(n);}catch(x){r=x.message;}
 const holders=n.players.filter(p=>p.ordinaryPassContinuityExecution||p.action?.ordinaryPassContinuity).map(p=>p.id);
 rows.push({tick:b.tick,fixture:r});b.step();}
const acc=rows.filter(r=>r.fixture==='accepted').map(r=>r.tick);
fs.writeFileSync(outF,JSON.stringify({input:path.basename(inputF),rows},null,1));
const runs=[];for(const r of rows){const last=runs.at(-1);if(last&&last.fixture===r.fixture&&last.to===r.tick-1)last.to=r.tick;else runs.push({fixture:r.fixture,from:r.tick,to:r.tick});}
console.log(path.basename(inputF),JSON.stringify(runs));
