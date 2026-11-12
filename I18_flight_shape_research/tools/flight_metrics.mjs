// Flight-window metrics on a recorded run (recorder buffers). Normal 'pass' kicks only.
// usage: node flight_metrics.mjs <runDir> -> prints JSON summary, writes flight_metrics.json in runDir
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const dir=process.argv[2];const meta=JSON.parse(fs.readFileSync(path.join(dir,'meta.json')));
const rd=(n,T)=>{const b=zlib.gunzipSync(fs.readFileSync(path.join(dir,n)));return new T(b.buffer,b.byteOffset,b.byteLength/T.BYTES_PER_ELEMENT);};
const pos=rd('pos.i16.gz',Int16Array),dec=rd('dec.u8.gz',Uint8Array),phase=rd('phase.u8.gz',Uint8Array);
const N=22,W=meta.posWidth,S=meta.posScale,n=meta.recordedTicks,PLAY=meta.phaseCodes.indexOf('play');
const ids=meta.ids,idx=new Map(ids.map((x,i)=>[x,i]));const dict=meta.decisionDict;
const KIND=dict.map(s=>s.split('|')[0]),REASON=dict.map(s=>s.split('|').slice(1).join('|'));
const X=(i,j)=>pos[i*W+2*j]/S,Y=(i,j)=>pos[i*W+2*j+1]/S,BX=i=>pos[i*W+44]/S,BY=i=>pos[i*W+45]/S;
const evs=fs.readFileSync(path.join(dir,'events.jsonl'),'utf8').split('\n').filter(Boolean).map(l=>JSON.parse(l));
const acts=evs.filter(e=>e.type==='kick'||e.type==='contact').map(e=>({t:e.tick,p:e.player,team:e.team,kick:e.type==='kick',kind:e.kind,ctrl:!!e.control||e.type==='kick'}));
const kicks=evs.filter(e=>e.type==='kick'&&e.kind==='pass');
const dirOf=(i,team)=>X(i,team==='A'?0:11)<52.5?1:-1;
const ballDir=new Set(['press','intercept','receive','save']);
const res=[];
for(const k of kicks){const K=k.tick;if(phase[K]!==PLAY)continue;const team=k.team,opp=team==='A'?'B':'A',D=dirOf(K,team),ownGoal=D===1?0:105;
 let first=null;for(const a of acts){if(a.t<=K)continue;if(a.p===k.player&&a.t-K<=3)continue;first=a;break;}
 let t1=first?first.t:n-1;let dead=false;for(let i=K+1;i<=t1&&i<n;i++)if(phase[i]!==PLAY){t1=i;dead=true;break;}
 if(t1-K<4)continue;const tj=k.targetId!=null?idx.get(k.targetId):-1,pj=idx.get(k.player);
 const mates=[...Array(11).keys()].map(x=>x+(team==='A'?0:11)).filter(j=>j%11!==0&&j!==pj&&j!==tj);
 const kc={cover:0,support:0,i18:0,ball:0,other:0};
 for(let i=K+1;i<=t1;i++)for(const j of mates){const c=dec[i*N+j];const kk=KIND[c];if(REASON[c].startsWith('I18_'))kc.i18++;if(kk==='cover')kc.cover++;else if(['support','advance_support','cover_exchange'].includes(kk))kc.support++;else if(ballDir.has(kk))kc.ball++;else kc.other++;}
 // real movement of mates that were NOT ball-directed at kick time
 const shape=mates.filter(j=>!ballDir.has(KIND[dec[K*N+j]]));const dt=(t1-K)/20;
 const fwd=shape.length?shape.reduce((s,j)=>s+(X(t1,j)-X(K,j))*D,0)/shape.length/dt:0;
 const lat=shape.length?shape.reduce((s,j)=>s+Math.abs(Y(t1,j)-Y(K,j)),0)/shape.length/dt:0;
 const outcome=dead?'out':!first?'none':first.p===k.targetId?(first.ctrl?'target_control':'target_no_control'):first.team===team?'teammate':'opponent';
 const r={t:K,team,passer:k.player,target:k.targetId,flight:+dt.toFixed(2),outcome,kc,shapeFwdMps:+fwd.toFixed(3),shapeLatMps:+lat.toFixed(3)};
 const bx=BX(t1),by=BY(t1);
 if(outcome==='target_control'||outcome==='teammate'&&first.ctrl){
  const oppJ=[...Array(11).keys()].map(x=>x+(team==='A'?11:0));
  r.openFwd=[...Array(11).keys()].map(x=>x+(team==='A'?0:11)).filter(j=>j%11!==0&&(X(t1,j)-bx)*D>2&&Math.hypot(X(t1,j)-bx,Y(t1,j)-by)<30&&Math.min(...oppJ.map(o=>Math.hypot(X(t1,j)-X(t1,o),Y(t1,j)-Y(t1,o))))>3).length;
  const rcv=first.p;let nx=null;for(const a of acts){if(a.t<=t1)continue;if(a.t>t1+60)break;if(a.p===rcv&&a.kick){nx={who:'self',kind:a.kind,dt:(a.t-t1)/20};break;}if(a.p!==rcv){nx={who:a.team===team?'teammate':'opponent',dt:(a.t-t1)/20};break;}}
  r.next=nx;
  // team continuation: does the passing team still own the next 5s (no opponent control)?
  r.lost5s=acts.some(a=>a.t>t1&&a.t<=t1+100&&a.team===opp&&a.ctrl);
  r.shot10s=evs.some(e=>e.type==='kick'&&e.kind==='shoot'&&e.team===team&&e.tick>t1&&e.tick<=t1+200);
 }
 if(outcome==='opponent'){
  const gs=i=>{const b=Math.abs(BX(i)-ownGoal);return mates.concat(tj>=0?[tj]:[],[pj]).filter(j=>Math.abs(X(i,j)-ownGoal)<b).length;};
  const cen=i=>[...Array(11).keys()].map(x=>x+(team==='A'?0:11)).filter(j=>j%11!==0&&Math.abs(X(i,j)-ownGoal)<30&&Math.abs(Y(i,j)-34)<14).length;
  const t3=Math.min(n-1,t1+60);r.goalSideAtLoss=gs(t1);r.goalSideAt3s=gs(t3);r.centralAtLoss=cen(t1);r.centralAt3s=cen(t3);r.ballDistOwnGoalAtLoss=+Math.abs(bx-ownGoal).toFixed(1);
  r.oppShot10s=evs.some(e=>e.type==='kick'&&e.kind==='shoot'&&e.team===opp&&e.tick>t1&&e.tick<=t1+200);
  const rg=acts.find(a=>a.t>t1&&a.t<=t1+100&&a.team===team&&a.ctrl);r.regain5s=!!rg;
  // how fast shape players went off support after the loss (decision based, kind only)
  let still=0;for(const j of mates){const c=dec[Math.min(n-1,t1+10)*N+j];if(['support','advance_support'].includes(KIND[c]))still++;}r.supportStill0_5sAfterLoss=still;
 }
 res.push(r);}
const sum=(f)=>res.reduce((s,r)=>s+f(r),0);
const kcT=['cover','support','i18','ball','other'].reduce((o,k)=>(o[k]=sum(r=>r.kc[k]),o),{});const tot=kcT.cover+kcT.support+kcT.ball+kcT.other;
const tc=res.filter(r=>r.outcome==='target_control'),op=res.filter(r=>r.outcome==='opponent');
const w=res.reduce((s,r)=>s+r.flight,0);
const summary={run:path.basename(dir),passes:res.length,flightSeconds:+w.toFixed(1),
 mateDecisionShare:{cover:+(kcT.cover/tot).toFixed(3),support:+(kcT.support/tot).toFixed(3),ballDirected:+(kcT.ball/tot).toFixed(3),other:+(kcT.other/tot).toFixed(3),i18Rewrites:+(kcT.i18/tot).toFixed(3)},
 shapeFwdMps_flightWeighted:+(res.reduce((s,r)=>s+r.shapeFwdMps*r.flight,0)/w).toFixed(3),
 outcomes:res.reduce((o,r)=>(o[r.outcome]=(o[r.outcome]||0)+1,o),{}),
 targetControl:{n:tc.length,openFwdMean:+(tc.reduce((s,r)=>s+r.openFwd,0)/Math.max(1,tc.length)).toFixed(2),nextSelf:tc.filter(r=>r.next?.who==='self').length,nextSelfPass:tc.filter(r=>r.next?.who==='self'&&r.next.kind==='pass').length,nextOpp:tc.filter(r=>r.next?.who==='opponent').length,lost5s:tc.filter(r=>r.lost5s).length,shot10s:tc.filter(r=>r.shot10s).length},
 intercepted:{n:op.length,goalSideAtLossMean:+(op.reduce((s,r)=>s+r.goalSideAtLoss,0)/Math.max(1,op.length)).toFixed(2),goalSideAt3sMean:+(op.reduce((s,r)=>s+r.goalSideAt3s,0)/Math.max(1,op.length)).toFixed(2),centralAtLossMean:+(op.reduce((s,r)=>s+r.centralAtLoss,0)/Math.max(1,op.length)).toFixed(2),oppShot10s:op.filter(r=>r.oppShot10s).length,regain5s:op.filter(r=>r.regain5s).length,supportStill0_5sMean:+(op.reduce((s,r)=>s+r.supportStill0_5sAfterLoss,0)/Math.max(1,op.length)).toFixed(2)}};
fs.writeFileSync(path.join(dir,'flight_metrics.json'),JSON.stringify({summary,passes:res}));console.log(JSON.stringify(summary));
