// C2: the combined decision is the exact union of the two single changes, as pure functions on saved own-observation DTOs.
// For every decision DTO in the given recordings: compute choose() of base, v2, flight and combo (read only).
// usage: node union_check.mjs <setDir> <out.json> <recording.json.gz> ...
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,outF,...recs]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));
const D={base:(await import(R('l21_natural/recovered/l21_receive_compare/branches/base_off/decision.mjs'))).choose,
 v2:(await import(R('l21_natural/recovered/l21_receive_compare/branches/base_on/decision.mjs'))).choose,
 flight:(await import(R('breakthrough_support/code/pass_prediction/source/integration_i8_standard/core/decision.mjs'))).choose,
 combo:(await import(R('q29_combo/source/integration_i8_standard/core/decision_v2.mjs'))).choose};
const J=x=>JSON.stringify(x);const tally={dtos:0,v2Differs:0,flightDiffers:0,bothDiffer:0,comboEqFlightWhenV2Same:0,comboEqV2WhenFlightSame:0,violations:0,byRecording:{}};const examples=[];
for(const f of recs){const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(f)));const t={dtos:0,v2Differs:0,flightDiffers:0,bothDiffer:0,violations:0};
 for(const r of x.rows){if(r.channel!=='decision'||!r.observation)continue;const o=r.observation,res={};for(const k in D)res[k]=J(D[k](structuredClone(o)));
  t.dtos++;const v=res.v2!==res.base,fl=res.flight!==res.base;if(v)t.v2Differs++;if(fl)t.flightDiffers++;if(v&&fl)t.bothDiffer++;
  let ok=true;if(!v){if(res.combo===res.flight)tally.comboEqFlightWhenV2Same++;else ok=false;}if(!fl){if(res.combo===res.v2)tally.comboEqV2WhenFlightSame++;else ok=false;}
  if(v&&fl&&res.combo!==res.flight&&res.combo!==res.v2)ok=false;if(!ok){t.violations++;if(examples.length<5)examples.push({rec:path.basename(f),tick:r.tick,player:r.player});}}
 for(const k of ['dtos','v2Differs','flightDiffers','bothDiffer','violations'])tally[k]+=t[k];tally.byRecording[path.basename(f)]=t;}
fs.writeFileSync(outF,JSON.stringify({tally,examples},null,1));console.log(JSON.stringify({tally,examples},null,1));
