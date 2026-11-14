// Synthetic fixtures (same construction as the package's own i8_ck_research_duel.mjs): executeKicks() on a hand-built
// state, each case run in normal and reversed player-array order and for two seeds, then E.fromFixture(s) save/restore.
// Cases: existing opposing duel (must equal the ORIGINAL branch bit for bit), same-team aerial pairs, three aerial players
// from two teams (existing rule), aerial + ordinary foot action on a low ball (mixed), same-team mixed, single header.
// usage: node fixture_groups.mjs <I17> <p25Dir> <offDir> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,OFF,outF]=process.argv.slice(2);
const load=async d=>({E:(await import(path.join(d,'core/engine.mjs'))).MatchEngine,executeKicks:(await import(path.join(d,'core/ball.mjs'))).executeKicks});
const orig=await load(path.join(I17,'source/integration_i8_ck_research')),p25=await load(BR),off=await load(OFF);
const CASES={
 opposing_header_vs_clear:{z:1.4,acts:[['A01','corner_header',-.5],['B01','corner_clear',.5]]},
 opposing_header_vs_gk_punch:{z:1.4,acts:[['A01','corner_header',-.5],['B00','gk_punch',.5]]},
 same_team_two_headers:{z:1.4,acts:[['A01','corner_header',-.5],['A02','corner_header',.5]]},
 same_team_two_clears:{z:1.4,acts:[['B01','corner_clear',-.5],['B02','corner_clear',.5]]},
 same_team_clear_and_own_gk_punch:{z:1.4,acts:[['B01','corner_clear',-.5],['B00','gk_punch',.5]]},
 three_aerial_two_teams:{z:1.4,acts:[['A01','corner_header',-.5],['A02','corner_header',.3],['B01','corner_clear',.6]]},
 mixed_header_vs_opponent_foot_pass:{z:.4,acts:[['A01','corner_header',-.5],['B01','pass',.5]]},
 mixed_clear_and_teammate_foot_pass:{z:.4,acts:[['B01','corner_clear',-.5],['B02','pass',.5]]},
 mixed_header_vs_opponent_foot_shoot:{z:.4,acts:[['B01','corner_clear',-.5],['A01','shoot',.5]]},
 single_header_control:{z:1.4,acts:[['A01','corner_header',-.5]]},
 foot_only_two_teams_control:{z:.2,acts:[['A01','pass',-.5],['B01','pass',.5]]}};
function run(M,name,seed,reverse){const c=CASES[name];let s=new M.E({seed}).exportState();s.phase='play';s.restart=null;s.restartRestriction={kind:'corner',taker:'A10'};
 s.players.forEach((p,i)=>{p.x=20+i%11*5;p.y=i<11?10:60;p.action={kind:'wait',target:{x:p.x,y:p.y},observedTick:0,applyTick:0};});
 for(const [id,kind,offset] of c.acts){const p=s.players.find(q=>q.id===id);p.x=99+offset;p.y=34;p.action={kind,target:{x:80,y:34},aim:{x:80,y:34},observedTick:0,applyTick:0};}
 s.ball={...s.ball,x:99,y:34,z:c.z,vx:0,vy:0,vz:0};if(reverse)s.players.reverse();
 const rows=[];let err=null;try{M.executeKicks(s,ev=>{if(ev.channel==='p25_group_resolution')rows.push({rule:ev.rule,winner:ev.winner});});}catch(x){err=x.message;}
 const ev=s.events.map(e=>({type:e.type,kind:e.kind??null,player:e.player??e.winner??null,simultaneous:e.simultaneous??null,teams:e.teams??null}));
 let saveRestored=null;if(!err){const e=M.E.fromFixture(s);saveRestored=JSON.stringify(M.E.restore(e.save()).exportState())===JSON.stringify(e.exportState());}
 const cool=Object.fromEntries(c.acts.map(([id])=>[id,s.players.find(q=>q.id===id).cooldown]));
 return {error:err,resolution:rows[0]??null,events:ev,ball:err?null:{vx:s.ball.vx,vy:s.ball.vy,vz:s.ball.vz,lastTouch:s.ball.lastTouch,lastTeam:s.ball.lastTeam,lastKick:s.ball.lastKick?.player??null},cooldownSet:cool,rngCalls:Object.fromEntries(c.acts.map(([id])=>[id,s.players.find(q=>q.id===id).rng.calls])),saveRestored};}
const out=[];
for(const name of Object.keys(CASES))for(const seed of [1,17]){
 const o=run(orig,name,seed,false),a=run(p25,name,seed,false),b=run(p25,name,seed,true),f=run(off,name,seed,false);
 out.push({case:name,seed,original:o.error?('THROW:'+o.error):'ok',p25:a.error?('THROW:'+a.error):'ok',off:f.error?('THROW:'+f.error):'ok',
  p25EqualsOriginalWhereOriginalRuns:o.error?null:JSON.stringify(o)===JSON.stringify(a),offEqualsOriginal:JSON.stringify(o)===JSON.stringify(f),
  orderIndependent:JSON.stringify(a)===JSON.stringify(b),saveRestored:a.saveRestored,resolution:a.resolution,events:a.events,ball:a.ball,rngCalls:a.rngCalls});}
fs.writeFileSync(outF,JSON.stringify(out,null,1));
for(const r of out)console.log(r.case.padEnd(38),r.seed,'orig',r.original.slice(0,12).padEnd(12),'p25',r.p25.padEnd(4),'off',r.off.slice(0,8).padEnd(8),'=orig',r.p25EqualsOriginalWhereOriginalRuns,'off=orig',r.offEqualsOriginal,'order',r.orderIndependent,'save',r.saveRestored,'|',r.resolution?.rule??'-',r.resolution?.winner??'-','| kicks',r.events.filter(e=>e.type==='kick').map(e=>e.player+':'+e.kind+':sim'+e.simultaneous).join(','),'| last',r.ball?.lastTouch,r.ball?.lastTeam);
