// Aggregate analysis.json from all runs into one table (JSON + markdown)
import fs from 'node:fs';import path from 'node:path';
const RUNS=process.argv[2];const out=process.argv[3];
const rows=[];
for(const d of fs.readdirSync(RUNS).sort()){const f=path.join(RUNS,d,'analysis.json');if(!fs.existsSync(f))continue;const a=JSON.parse(fs.readFileSync(f));const s=a.summary;const meta=JSON.parse(fs.readFileSync(path.join(RUNS,d,'meta.json')));
 const sum=(o,pred)=>Object.entries(o).filter(([k])=>pred(k)).reduce((x,[,v])=>x+v,0);
 const C={};for(const t of ['A','B']){const c=s.concentration[t];
  for(const ctx of ['opp_carry','opp_pass_flight','loose','own_pass_flight','own_carry']){const tot=sum(c,k=>k.startsWith(ctx+':'));C[t+'_'+ctx]={ticks:tot,ge3:sum(c,k=>k===ctx+':3'||k===ctx+':4'),eq2:c[ctx+':2']||0,eq1:c[ctx+':1']||0,eq0:c[ctx+':0']||0};}}
 const agg=ctx=>{const t=C['A_'+ctx].ticks+C['B_'+ctx].ticks;return {ticks:t,ge3:C['A_'+ctx].ge3+C['B_'+ctx].ge3,eq2:C['A_'+ctx].eq2+C['B_'+ctx].eq2,eq1:C['A_'+ctx].eq1+C['B_'+ctx].eq1,eq0:C['A_'+ctx].eq0+C['B_'+ctx].eq0};};
 const ownCarry=agg('own_carry');const st=(ctx)=>{let t=0,g3=0,g2=0;for(const T of ['A','B']){const c=s.concentration[T];for(const k of [0,1,2,3,4]){const v=c['sameTarget2m_'+ctx+':'+k]||0;t+=v;if(k>=3)g3+=v;if(k===2)g2+=v;}}return {ticks:t,eq2:g2,ge3:g3};};const sameT={opp_carry:st('opp_carry'),loose:st('loose'),opp_pass_flight:st('opp_pass_flight'),own_pass_flight:st('own_pass_flight')};
 const D={danger:0,centralEmpty:0,freeBehind:0,carry:0,carrierFree5:0,carrierFree5Danger:0};for(const t of ['A','B']){const x=s.defence[t];D.danger+=x.danger||0;D.centralEmpty+=x.centralEmpty||0;D.freeBehind+=x.freeBehind||0;D.carry+=x.carryTicks||0;D.carrierFree5+=x.carrierFree5||0;D.carrierFree5Danger+=x.carrierFree5Danger||0;}
 const P=a.passes.filter(p=>p.kind==='pass');const po=k=>P.filter(p=>p.outcome===k).length;
 const tc=P.filter(p=>p.outcome==='target_control');const nx=k=>tc.filter(p=>p.next?.who===k).length;
 const oppCtrl=P.filter(p=>p.outcome==='opponent_control'||p.outcome==='opponent_contact');
 const noRecv=P.filter(p=>p.targetReceiveShare===0).length;
 const tr=a.transitions.filter(x=>x.allPlay5s);
 const corners=a.corners;
 rows.push({run:d,variant:s.variant,profile:s.profile,zonal:s.activeConfig.zonalDefence,seed:s.seed,extra:meta.extraOptions??{},crash:meta.crash?.message??null,crashTick:meta.crash?.engineTick??null,finalTick:s.finalTick,score:s.score,result:s.result?.reason??s.result?.kind??(s.result?'set':null),violations:s.violations,playSec:s.playSeconds,phaseTicks:s.phaseTicks,
  counts:s.counts,
  conc:{opp_carry:agg('opp_carry'),opp_pass_flight:agg('opp_pass_flight'),loose:agg('loose'),own_pass_flight_nonTarget:agg('own_pass_flight'),own_carry_teammatesChasing:ownCarry},sameTarget2m:sameT,flips:s.supportCoverFlipsPerPlayerPerPlayMin,turnoversPerMin:s.turnoversPerPlayMin,modeShare:s.modeShare,concEpisodes:s.concEpisodes,concEpisodeSeconds:s.concEpisodeSeconds,jointPressEpisodes:s.jointPressEpisodes,
  concEpOwnWin3s:a.concEpisodes.filter(e=>e.ownWin3s!=null).length,concEpOppPassFirst:a.concEpisodes.filter(e=>e.oppPassFirst!=null).length,concEpConceded10m:a.concEpisodes.filter(e=>e.ballGain3s>=10).length,concEpOppCarryStart:a.concEpisodes.filter(e=>e.ctx==='opp_carry').length,
  jointOwnWin3s:a.jointPress.filter(e=>e.ownWin3s!=null).length,jointOppPassFirst:a.jointPress.filter(e=>e.oppPassFirst!=null).length,jointConceded10m:a.jointPress.filter(e=>e.ballGain3s>=10).length,
  def:D,freeBehindEpisodes:s.freeBehindEpisodes,centralEmptyEpisodes:s.centralEmptyEpisodes,centralEmptyEpisodesShot:s.centralEmptyEpisodesShot,shotsTotal:s.counts.shots,
  passes:{n:P.length,target_control:po('target_control'),target_no_control:po('target_no_control'),teammate_other:po('teammate_other_control')+po('teammate_other_no_control'),passer_retouch:po('passer_retouch'),opponent:oppCtrl.length,out:po('out_of_play'),none:po('none'),
   tc_next_self:nx('self'),tc_next_opp:nx('opponent'),tc_next_team:nx('teammate'),tc_next_out:nx('out'),targetNeverReceive:noRecv,
   tcNextSelfKinds:tc.filter(p=>p.next?.who==='self').reduce((o,p)=>(o[p.next.kind]=(o[p.next.kind]||0)+1,o),{}),
   medianNextDelay:(()=>{const v=tc.filter(p=>p.next?.who==='self').map(p=>p.nextDelay).sort((a,b)=>a-b);return v[Math.floor(v.length/2)]??null;})()},
  trans:{n:tr.length,loserAttackModeAt1s:+(tr.reduce((x,t)=>x+t.loserAttackModeAt[2],0)/Math.max(1,tr.length)).toFixed(2),loserGoalSide0:+(tr.reduce((x,t)=>x+t.loserGoalSide[0],0)/Math.max(1,tr.length)).toFixed(2),loserGoalSide5s:+(tr.reduce((x,t)=>x+t.loserGoalSide[2],0)/Math.max(1,tr.length)).toFixed(2),shot10s:tr.filter(t=>t.winnerShot10s).length,regained2s:tr.filter(t=>t.loserRegainTick&&t.loserRegainTick-t.tick<=40).length},
  restarts:s.restartByKind,
  corners:{origins:corners.reduce((o,c)=>(o[c.origin]=(o[c.origin]||0)+1,o),{}),n:corners.length,attInBoxMean:corners.length?+(corners.reduce((x,c)=>x+c.attInBox,0)/corners.length).toFixed(2):null,defInBoxMean:corners.length?+(corners.reduce((x,c)=>x+c.defInBox,0)/corners.length).toFixed(2):null,firstTouchAtt:corners.filter(c=>c.firstTouchTeam===c.team).length,firstTouchDef:corners.filter(c=>c.firstTouchTeam&&c.firstTouchTeam!==c.team).length,shot10s:corners.filter(c=>c.shot10s).length,goal10s:corners.filter(c=>c.goal10s).length,firstKickKinds:corners.reduce((o,c)=>{const k=c.firstKick?.kind??'none';o[k]=(o[k]||0)+1;return o;},{}),medianWait:s.restartByKind.corner?.medianWait??null,maxWait:s.restartByKind.corner?.maxWait??null},
  throwIns:(()=>{const Tw=a.passes.filter(p=>p.kind==='throw_in');const c=k=>Tw.filter(p=>p.outcome===k).length;return {n:Tw.length,target_control:c('target_control'),opponent:c('opponent_control')+c('opponent_contact'),out:c('out_of_play'),outToOppCorner:Tw.filter(p=>p.outcome==='out_of_play'&&p.outRestart?.kind==='corner'&&p.outRestart.team!==p.team).length,targetNeverReceive:Tw.filter(p=>p.targetReceiveShare===0).length};})(),
  goals:s.goals,shots:s.counts.shots});}
fs.writeFileSync(out,JSON.stringify(rows,null,1));console.log('rows',rows.length);
