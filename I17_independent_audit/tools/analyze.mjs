// Independent audit analyzer for one recorded run directory. Reads only recorder outputs.
// Definitions are audit definitions, not engine semantics; see README in audit pack.
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const dir=process.argv[2];
const meta=JSON.parse(fs.readFileSync(path.join(dir,'meta.json')));
const rd=(n,T)=>{const b=zlib.gunzipSync(fs.readFileSync(path.join(dir,n)));return new T(b.buffer,b.byteOffset,b.byteLength/T.BYTES_PER_ELEMENT);};
const tgtB=rd('tgt.i16.gz',Int16Array),pos=rd('pos.i16.gz',Int16Array),dec=rd('dec.u8.gz',Uint8Array),phase=rd('phase.u8.gz',Uint8Array);
const N=22,W=meta.posWidth,S=meta.posScale,n=meta.recordedTicks;
const ids=meta.ids,roles=meta.roles,team=ids.map(i=>i[0]),idx=new Map(ids.map((x,i)=>[x,i]));
const dict=meta.decisionDict,kindOf=dict.map(s=>s.split('|')[0]),reasonOf=dict.map(s=>s.split('|').slice(1).join('|'));
const PLAY=meta.phaseCodes.indexOf('play');
// position of entity j at recorded index i (index i = state after i steps; tick == i)
const X=(i,j)=>pos[i*W+2*j]/S,Y=(i,j)=>pos[i*W+2*j+1]/S,BX=i=>pos[i*W+2*N]/S,BY=i=>pos[i*W+2*N+1]/S,BZ=i=>pos[i*W+2*N+2]/S;
const K=(i,j)=>kindOf[dec[i*N+j]],R=(i,j)=>reasonOf[dec[i*N+j]];
const d2=(ax,ay,bx,by)=>Math.hypot(ax-bx,ay-by);
const evs=fs.readFileSync(path.join(dir,'events.jsonl'),'utf8').split('\n').filter(Boolean).map(l=>JSON.parse(l));
// ---- team direction: A attacks +x in half 1. Detect half 2 start from kickoff placement after long non-play.
const kickoffs=evs.filter(e=>e.type==='restart_placement'&&e.kind==='kickoff').map(e=>e.tick);
const halftimeTick=(()=>{let h=null;for(let i=1;i<n;i++){if(meta.phaseCodes[phase[i]]&&!['play','restart'].includes(meta.phaseCodes[phase[i]])){h=i;break;}}return h;})();
// use observed GK positions instead (robust): A GK x<52.5 => A dir +1
const dirAt=(i,t)=>{const gk=t==='A'?0:11;return X(i,gk)<52.5?1:-1;};
const ownGoalX=(i,t)=>dirAt(i,t)===1?0:105;
const clock=t=>{const sec=t/20;return `${Math.floor(sec/60)}:${String(Math.floor(sec%60)).padStart(2,'0')}`;};
// ---- touches
const contactRows=evs.filter(e=>e.type==='contact');
const kicks=evs.filter(e=>e.type==='kick');
// merge contact rows: same player, tick gap<=2 => one touch episode
const touches=[];{const last=new Map();for(const c of contactRows){const L=last.get(c.player);if(L&&c.tick-L.end<=2){L.end=c.tick;L.rows++;L.control=L.control||c.control;L.miscontrol=L.miscontrol||c.miscontrol;L.interception=L.interception||c.interception;L.maxRel=Math.max(L.maxRel,c.relativeSpeed||0);continue;}
 const T={kind:'contact',tick:c.tick,end:c.tick,player:c.player,team:c.team,rows:1,control:!!c.control,miscontrol:!!c.miscontrol,interception:!!c.interception,maxRel:c.relativeSpeed||0,gkSave:!!c.gkSaveContact,intentional:!!c.intentional};touches.push(T);last.set(c.player,T);}}
const throwsAsKicks=evs.filter(e=>e.type==='throw_in_play').map(e=>({kind:'kick',tick:e.tick,end:e.tick,player:e.player,team:e.team,kk:'throw_in',targetId:null,v:e.velocity}));
const actions=[...touches,...throwsAsKicks,...kicks.map(k=>({kind:'kick',tick:k.tick,end:k.tick,player:k.player,team:k.team,kk:k.kind,targetId:k.targetId??null,v:k.velocity}))].sort((a,b)=>a.tick-b.tick||(a.kind==='kick')-(b.kind==='kick'));
// body contacts merge per pair gap<=3
const bodyRows=evs.filter(e=>e.channel==='body_contact');const bodyEp=[];{const last=new Map();for(const b of bodyRows){const k=b.players.slice().sort().join('-');const L=last.get(k);if(L&&b.tick-L.end<=3){L.end=b.tick;L.rows++;L.maxImp=Math.max(L.maxImp,b.impulse);continue;}const E={pair:k,tick:b.tick,end:b.tick,rows:1,maxImp:b.impulse,sameTeam:b.players[0][0]===b.players[1][0]};bodyEp.push(E);last.set(k,E);}}
// ---- possession timeline: control signal = kick or contact with control
const passTgt=new Int16Array(n).fill(-1);let curTgt=-1;
const ctrl=new Int8Array(n).fill(0),carrier=new Int16Array(n).fill(-1),state=new Uint8Array(n); // state:0 none/dead 1 carry 2 pass_flight 3 loose
{let ai=0,cur=0,car=-1,st=0;for(let i=0;i<n;i++){while(ai<actions.length&&actions[ai].tick<=i){const a=actions[ai++];const t=a.team==='A'?1:2;
  if(a.kind==='kick'){cur=t;car=idx.get(a.player);passTgt[i]=-1;curTgt=a.targetId!=null?idx.get(a.targetId):-1;st=(a.kk==='throw_in'||a.kk==='pass'||a.kk==='restart_kick'||a.kk==='shoot'||a.kk==='cross'||a.kk==='corner_cross'||a.kk==='clear')?2:1;}
  else if(a.control){cur=t;car=idx.get(a.player);st=1;}else{st=3;car=-1;}}
 if(phase[i]!==PLAY){if(i>0&&phase[i-1]===PLAY){st=0;car=-1;cur=0;}ctrl[i]=0;carrier[i]=-1;state[i]=0;continue;}
 // carry lapses if carrier >2.5m from ball
 if(st===1&&car>=0&&d2(X(i,car),Y(i,car),BX(i),BY(i))>2.5)st=3;
 ctrl[i]=cur;carrier[i]=car;state[i]=st;passTgt[i]=st===2?curTgt:-1;}}
const playTicks=[...phase].filter(p=>p===PLAY).length;
const ballDirected=new Set(['press','intercept','receive','save']);
const isGK=j=>roles[j]==='GK';
const teamIdx={A:[...Array(11).keys()],B:[...Array(11).keys()].map(x=>x+11)};
const other=t=>t==='A'?'B':'A';
// ================= 1. concentration
const conc={A:{},B:{}};const concEp=[];const jointEp=[];
const ctxName=(i,t)=>{const tc=t==='A'?1:2;if(state[i]===0)return 'dead';if(state[i]===1)return ctrl[i]===tc?'own_carry':'opp_carry';if(state[i]===2)return ctrl[i]===tc?'own_pass_flight':'opp_pass_flight';return 'loose';};
for(const t of ['A','B']){const C=conc[t];let ep=null,jep=null;
 for(let i=0;i<n;i++){if(phase[i]!==PLAY){if(ep){concEp.push(ep);ep=null;}if(jep){jointEp.push(jep);jep=null;}continue;}
  const ctx=ctxName(i,t);const chasers=teamIdx[t].filter(j=>!isGK(j)&&ballDirected.has(K(i,j))&&j!==carrier[i]&&j!==passTgt[i]);
  const bx=BX(i),by=BY(i);const near5=teamIdx[t].filter(j=>!isGK(j)&&d2(X(i,j),Y(i,j),bx,by)<5).length;
  if(ctx==='opp_carry'||ctx==='loose'||ctx==='opp_pass_flight'){const g=ownGoalX(i,t);const ds=chasers.map(j=>d2(X(i,j),Y(i,j),bx,by)).sort((a,b)=>a-b);for(let r=0;r<ds.length;r++){const b=ds[r]<5?'<5':ds[r]<10?'5-10':ds[r]<15?'10-15':ds[r]<25?'15-25':'25+';const kk='rank'+Math.min(r+1,4)+'_'+ctx+':'+b;C[kk]=(C[kk]||0)+1;}
   const behind=chasers.filter(j=>Math.abs(X(i,j)-g)>Math.abs(bx-g)+1).length;C['chaserNotGoalSide_'+ctx]=(C['chaserNotGoalSide_'+ctx]||0)+behind;C['chaserTotal_'+ctx]=(C['chaserTotal_'+ctx]||0)+chasers.length;}
  {let best=0;for(const a of chasers){const ax=tgtB[(i*N+a)*2]/S,ay=tgtB[(i*N+a)*2+1]/S;let c=0;for(const b of chasers){if(d2(ax,ay,tgtB[(i*N+b)*2]/S,tgtB[(i*N+b)*2+1]/S)<2)c++;}best=Math.max(best,c);}const sk='sameTarget2m_'+ctx+':'+Math.min(best,4);C[sk]=(C[sk]||0)+1;}
  {const out=teamIdx[t].filter(j=>!isGK(j)&&j!==carrier[i]);const km={};for(const j of out){const k=K(i,j);const g=ballDirected.has(k)?'ball':['support','advance_support','cover_exchange'].includes(k)?'attackShape':k==='cover'?'cover':'other';km[g]=(km[g]||0)+1;}for(const[g,v] of Object.entries(km)){const mk='mode_'+ctx+':'+g;C[mk]=(C[mk]||0)+v;}}
  const key=ctx+':'+Math.min(chasers.length,4);C[key]=(C[key]||0)+1;C['near5_'+ctx+':'+Math.min(near5,4)]=(C['near5_'+ctx+':'+Math.min(near5,4)]||0)+1;
  const excess=chasers.length>=3&&ctx!=='own_carry'||chasers.length>=2&&ctx==='own_carry';
  if(excess){if(!ep)ep={team:t,start:i,end:i,ctx,players:new Set(),maxN:0,ball:[+bx.toFixed(1),+by.toFixed(1)],ctxs:{}};ep.end=i;chasers.forEach(j=>ep.players.add(ids[j]));ep.maxN=Math.max(ep.maxN,chasers.length);if(!ep.detail){const g=ownGoalX(i,t);ep.detail=chasers.map(j=>({id:ids[j],k:K(i,j),d:+d2(X(i,j),Y(i,j),bx,by).toFixed(1),goalSide:Math.abs(X(i,j)-g)<Math.abs(bx-g)}));}ep.ctxs[ctx]=(ep.ctxs[ctx]||0)+1;}
  else if(ep){concEp.push(ep);ep=null;}
  if(ctx==='opp_carry'&&chasers.length===2){if(!jep)jep={team:t,start:i,end:i,players:new Set(chasers.map(j=>ids[j])),ball:[+bx.toFixed(1),+by.toFixed(1)]};jep.end=i;}else if(jep){jointEp.push(jep);jep=null;}
 }if(ep)concEp.push(ep);if(jep)jointEp.push(jep);}
// outcome of episode: next team in control after start within 3s, and ball progress toward this team's goal
const nextCtrlAfter=(i,within)=>{for(const a of actions){if(a.tick<i)continue;if(a.tick>i+within)break;if(a.kind==='kick'||a.control)return {team:a.team,player:a.player,tick:a.tick,how:a.kind==='kick'?a.kk:'control'};}return null;};
function epOutcome(ep){const t=ep.team;const s=ep.start;const o=nextCtrlAfter(s,60);const g=ownGoalX(s,t);const b0=Math.abs(BX(s)-g);const e3=Math.min(n-1,s+60);const b3=Math.abs(BX(e3)-g);
 // central/behind cover at start: non-chasing outfield goal-side of ball within central corridor
 const chasers=new Set(ep.players);const gs=teamIdx[t].filter(j=>!isGK(j)&&!chasers.has(ids[j])&&Math.abs(X(s,j)-g)<b0&&Math.abs(Y(s,j)-34)<14);
 let ownWin=null,oppPass=null;for(const a of actions){if(a.tick<s)continue;if(a.tick>s+60)break;if(a.team===t&&(a.kind==='kick'||a.control)&&ownWin===null)ownWin=a.tick;if(a.team!==t&&a.kind==='kick'&&a.kk==='pass'&&oppPass===null&&ownWin===null)oppPass=a.tick;}
 return {ownWin3s:ownWin,oppPassFirst:oppPass,ballGain3s:+(b0-b3).toFixed(1),nextCtrl:o,ballToOwnGoalBefore:+b0.toFixed(1),after3s:+b3.toFixed(1),centralGoalSideNonChasers:gs.length,phaseAfter:meta.phaseCodes[phase[e3]]};}
const concEpOut=concEp.filter(e=>e.end-e.start>=10).map(e=>({...e,players:[...e.players],dur:(e.end-e.start+1)/20,clock:clock(e.start),...epOutcome(e)}));
const jointOut=jointEp.filter(e=>e.end-e.start>=10).map(e=>({...e,players:[...e.players],dur:(e.end-e.start+1)/20,clock:clock(e.start),...epOutcome(e)}));
// ================= 2. defence: centre/behind and pressure while opponent has ball
const recentRestart=new Uint8Array(n);for(let i=1;i<n;i++){if(phase[i-1]!==PLAY&&phase[i]===PLAY){for(let k=i;k<Math.min(n,i+60);k++)recentRestart[k]=1;}}
const def={A:{},B:{}};const centralEp=[],centralOpen={A:null,B:null};const behindEp=[];
for(const t of ['A','B']){const D=def[t];let ep=null;const opp=other(t);
 for(let i=0;i<n;i++){if(phase[i]!==PLAY||!(ctxName(i,t)==='opp_carry'||ctxName(i,t)==='opp_pass_flight')){if(ep){behindEp.push(ep);ep=null;}continue;}
  D.ticks=(D.ticks||0)+1;const g=ownGoalX(i,t),dir=g===0?1:-1;const bx=BX(i),by=BY(i);const bd=Math.abs(bx-g);
  const out=teamIdx[t].filter(j=>!isGK(j));const goalSide=out.filter(j=>Math.abs(X(i,j)-g)<bd).length;D['goalSide:'+Math.min(goalSide,10)]=(D['goalSide:'+Math.min(goalSide,10)]||0)+1;
  if(bd<40){D.danger=(D.danger||0)+1;
   const chase=new Set(out.filter(j=>ballDirected.has(K(i,j))));
   const central=out.filter(j=>!chase.has(j)&&Math.abs(X(i,j)-g)<Math.min(bd,30)&&Math.abs(Y(i,j)-34)<14).length;if(central===0&&!recentRestart[i]){D.centralEmpty=(D.centralEmpty||0)+1;const ce=centralOpen[t];if(ce&&ce.end>=i-2)ce.end=i;else{if(ce)centralEp.push(ce);centralOpen[t]={team:t,start:i,end:i,ball:[+bx.toFixed(1),+by.toFixed(1)],chasers:[...chase].map(j=>ids[j]),goalSideAll:goalSide};}}
   // deepest outfield defender distance to goal
   const deep=Math.min(...out.map(j=>Math.abs(X(i,j)-g)));
   const runners=teamIdx[opp].filter(j=>!isGK(j)&&Math.abs(X(i,j)-g)<deep-0.5&&Math.abs(X(i,j)-g)>=bd-0.5&&Math.abs(X(i,j)-g)<35&&d2(X(i,j),Y(i,j),bx,by)>3&&!recentRestart[i]&&out.every(k=>d2(X(i,k),Y(i,k),X(i,j),Y(i,j))>4));
   // runners beyond deepest defender but not ahead of ball (onside by ball) and unmarked (>4m)
   if(runners.length){D.freeBehind=(D.freeBehind||0)+1;if(!ep)ep={team:t,start:i,end:i,runners:new Set(),ball:[+bx.toFixed(1),+by.toFixed(1)]};ep.end=i;runners.forEach(j=>ep.runners.add(ids[j]));}else if(ep){behindEp.push(ep);ep=null;}
  }else if(ep){behindEp.push(ep);ep=null;}
  // pressure on carrier
  if(state[i]===1&&carrier[i]>=0){const c=carrier[i];const nd=Math.min(...out.map(j=>d2(X(i,j),Y(i,j),X(i,c),Y(i,c))));D.carryTicks=(D.carryTicks||0)+1;if(nd>5)D.carrierFree5=(D.carrierFree5||0)+1;if(nd>5&&bd<40)D.carrierFree5Danger=(D.carrierFree5Danger||0)+1;}
 }if(ep)behindEp.push(ep);}
for(const t of ['A','B'])if(centralOpen[t])centralEp.push(centralOpen[t]);
const shotKicks=kicks.filter(k=>k.kind==='shoot');const centralOut=centralEp.filter(e=>e.end-e.start>=10).map(e=>({...e,dur:(e.end-e.start+1)/20,clock:clock(e.start),oppShot5s:shotKicks.find(k=>k.team!==e.team&&k.tick>=e.start&&k.tick<=e.end+100)?.tick??null}));
const behindOut=behindEp.filter(e=>e.end-e.start>=10).map(e=>({...e,runners:[...e.runners],dur:(e.end-e.start+1)/20,clock:clock(e.start),next:nextCtrlAfter(e.start,100)}));
// ================= 3. transitions
const turnovers=[];{let prev=0;for(const a of actions){if(phase[a.tick]!==PLAY)continue;if(!(a.kind==='kick'||a.control))continue;const t=a.team==='A'?1:2;if(prev&&t!==prev)turnovers.push({tick:a.tick,winner:a.team,player:a.player,how:a.kind==='kick'?a.kk:'control'});prev=t;}}
// reset prev on restarts handled loosely: turnovers right after restart are excluded below
const trans=turnovers.map(tv=>{const L=other(tv.winner);const i0=tv.tick;const at=k=>Math.min(n-1,i0+k);const g=ownGoalX(i0,L);
 const gs=k=>{const i=at(k);const bd=Math.abs(BX(i)-g);return teamIdx[L].filter(j=>!isGK(j)&&Math.abs(X(i,j)-g)<bd).length;};
 const attackMode=k=>{const i=at(k);return teamIdx[L].filter(j=>!isGK(j)&&['support','advance_support','cover_exchange'].includes(K(i,j))).length;};
 const winAttack=k=>{const i=at(k);return teamIdx[tv.winner].filter(j=>!isGK(j)&&['support','advance_support'].includes(K(i,j))).length;};
 const prog=Math.abs(BX(i0)-g)-Math.abs(BX(at(100))-g);
 let shot=null;for(const k of kicks){if(k.tick<=i0)continue;if(k.tick>i0+200)break;if(k.kind==='shoot'&&k.team===tv.winner){shot=k.tick;break;}}
 let regain=null;for(const a of actions){if(a.tick<=i0)continue;if(a.tick>i0+200)break;if((a.kind==='kick'||a.control)&&a.team===L){regain=a.tick;break;}}
 const allPlay=[...Array(101).keys()].every(k=>phase[at(k)]===PLAY);
 return {...tv,clock:clock(i0),ballDistLoserGoal:+Math.abs(BX(i0)-g).toFixed(1),loserGoalSide:[gs(0),gs(40),gs(100)],loserAttackModeAt:[attackMode(0),attackMode(10),attackMode(20),attackMode(40)],winnerSupportAt:[winAttack(0),winAttack(20),winAttack(40)],progress5s:+prog.toFixed(1),winnerShot10s:shot,loserRegainTick:regain,allPlay5s:allPlay};});
// ================= 4. pass -> reception -> next play
const passKinds=new Set(['pass','restart_kick','cross','corner_cross','through','long_pass']);
const throwPlays=evs.filter(e=>e.type==='throw_in_play');
const throwTid=[];for(const l of fs.readFileSync(path.join(dir,'decisions.jsonl'),'utf8').split('\n')){if(!l)continue;const x=JSON.parse(l);if(x.k.startsWith('throw_in|'))throwTid.push(x);}
const throwKicks=evs.filter(e=>e.type==='throw_in_play').map(e=>{const d=throwTid.filter(x=>x.p===e.player&&x.t<=e.tick).at(-1);return {tick:e.tick,player:e.player,team:e.team,kind:'throw_in',targetId:d?.tid??null,velocity:e.velocity};});
const passes=[];
for(const k of [...kicks,...throwKicks].sort((a,b)=>a.tick-b.tick)){if(!passKinds.has(k.kind)&&k.kind!=='throw_in')continue;const t0=k.tick;let first=null;
 for(const a of actions){if(a.tick<=t0)continue;if(a.player===k.player&&a.tick-t0<=3)continue;first=a;break;}
 // out of play before first touch?
 let outTick=null;for(let i=t0+1;i<n&&(!first||i<first.tick);i++){if(phase[i]!==PLAY){outTick=i;break;}}
 const tgt=k.targetId,tj=tgt!=null?idx.get(tgt):null;
 const rec={tick:t0,clock:clock(t0),passer:k.player,team:k.team,kind:k.kind,target:tgt,speed:k.velocity?+Math.hypot(k.velocity.x,k.velocity.y).toFixed(2):null,vz:k.velocity?+k.velocity.z.toFixed(2):null};
 if(tj!=null){rec.targetDist=+d2(X(t0,tj),Y(t0,tj),BX(t0),BY(t0)).toFixed(1);}
 if(outTick!=null){rec.outcome='out_of_play';rec.firstTick=outTick;const rp=evs.find(e=>e.type==='restart_placement'&&e.tick>=outTick-3);rec.outRestart=rp?{kind:rp.kind,team:rp.team}:null;}
 else if(!first){rec.outcome='none';}
 else{rec.firstTick=first.tick;rec.flight=(first.tick-t0)/20;rec.first=first.player;const ft=first.team;
  if(first.player===k.player)rec.outcome='passer_retouch';
  else if(first.player===tgt)rec.outcome=(first.kind==='kick'||first.control)?'target_control':'target_no_control';
  else if(ft===k.team)rec.outcome=(first.kind==='kick'||first.control)?'teammate_other_control':'teammate_other_no_control';
  else rec.outcome=(first.kind==='kick'||first.control)?'opponent_control':'opponent_contact';
  if(first.kind==='contact')rec.firstRel=+first.maxRel.toFixed(2);
 }
 // receiver behaviour during flight
 if(tj!=null){const end=rec.firstTick??Math.min(n-1,t0+60);let recv=0,tot=0,firstRecv=null;const kinds={};for(let i=t0+1;i<=end;i++){tot++;const kk=K(i,tj);kinds[kk]=(kinds[kk]||0)+1;if(kk==='receive'||kk==='intercept'){recv++;if(firstRecv===null)firstRecv=i-t0;}}rec.targetKindAtKick=K(t0,tj);rec.targetReceiveShare=tot?+(recv/tot).toFixed(2):null;rec.targetFirstReceiveTicks=firstRecv;rec.targetKinds=kinds;
  if(rec.firstTick!=null){rec.targetDistAtFirst=+d2(X(rec.firstTick,tj),Y(rec.firstTick,tj),BX(rec.firstTick),BY(rec.firstTick)).toFixed(1);}
 }
 // next play after target/teammate control
 if(rec.outcome==='target_control'||rec.outcome==='teammate_other_control'){const r=first.player;let nxt=null;for(const a of actions){if(a.tick<=first.tick)continue;if(a.player===r&&a.kind==='kick'){nxt={who:'self',kind:a.kk,tick:a.tick};break;}if(a.player!==r&&(a.kind==='kick'||a.control||a.kind==='contact')){nxt={who:a.team===k.team?'teammate':'opponent',player:a.player,control:!!(a.kind==='kick'||a.control),tick:a.tick};break;}}
  let out2=null;for(let i=first.tick+1;i<n&&(!nxt||i<nxt.tick);i++){if(phase[i]!==PLAY){out2=i;break;}}
  rec.next=out2!=null?{who:'out',tick:out2}:nxt;if(rec.next)rec.nextDelay=(rec.next.tick-first.tick)/20;
  if(first.kind==='kick')rec.firstTouchWasKick=first.kk;
 }
 passes.push(rec);}
// ================= 5. restarts & corners
const placements=evs.filter(e=>e.type==='restart_placement');
const taken=evs.filter(e=>['restart_taken','throw_in_play','drop_in_play'].includes(e.type));
const restarts=placements.map(p=>{const tk=taken.find(t=>t.tick>=p.tick);return {kind:p.kind,team:p.team,taker:p.taker,tick:p.tick,clock:clock(p.tick),takenTick:tk?.tick??null,wait:tk?(tk.tick-p.tick)/20:null};});
const inPA=(x,y,g)=>Math.abs(x-g)<=16.5&&y>=13.84&&y<=54.16;
const corners=restarts.filter(r=>r.kind==='corner').map(r=>{const i=r.takenTick??r.tick;const tt=r.team,dt=other(tt);const gx=BX(r.tick)<52.5?0:105; // attacked goal
 const att=teamIdx[tt].filter(j=>inPA(X(i,j),Y(i,j),gx)).map(j=>ids[j]),dfd=teamIdx[dt].filter(j=>inPA(X(i,j),Y(i,j),gx)).map(j=>ids[j]);
 const first=kicks.find(k=>k.tick>=i&&k.tick<=i+5);const seq=[];let shot=null,goal=null;for(const a of actions){if(a.tick<i)continue;if(a.tick>i+200)break;if(seq.length<8&&(a.kind==='kick'||a.control||a.kind==='contact'))seq.push(`${a.tick}:${a.player}:${a.kind==='kick'?a.kk:(a.control?'ctrl':'touch')}`);if(a.kind==='kick'&&a.kk==='shoot'&&!shot)shot={tick:a.tick,player:a.player,team:a.team};}
 const g=evs.find(e=>e.type==='goal'&&e.tick>=i&&e.tick<=i+200);let end=null;for(let k=i+1;k<Math.min(n,i+400);k++){if(phase[k]!==PLAY){end={tick:k,restart:restarts.find(x=>x.tick>=k-5)?.kind??null};break;}}
 const firstTouchOther=actions.find(a=>a.tick>i+2&&a.player!==r.taker);
 const pv=actions.filter(a=>a.tick<=r.tick).slice(-2).map(a=>({tick:a.tick,player:a.player,team:a.team,what:a.kind==='kick'?a.kk:(a.control?'ctrl':(a.gkSave?'gk_save':'touch'))}));
 const last=pv.at(-1);const origin=!last?'unknown':last.team===tt?'attacker_last':(last.what==='touch'&&pv.length>1&&pv[0].team===dt&&['pass','dribble'].includes(pv[0].what)?'defender_own_pass_or_dribble_then_uncontrolled_touch':last.what==='touch'?'defender_uncontrolled_touch':last.what==='gk_save'?'gk_save':'defender_'+last.what);
 return {...r,prevTouches:pv,origin,attInBox:att.length,defInBox:dfd.length,attBox:att,firstKick:first?{kind:first.kind,target:first.targetId,speed:+Math.hypot(first.velocity.x,first.velocity.y).toFixed(1),vz:+first.velocity.z.toFixed(1)}:null,firstTouchTeam:firstTouchOther?.team??null,firstTouchPlayer:firstTouchOther?.player??null,seq,shot10s:shot,goal10s:g?{team:g.team,tick:g.tick}:null,deadAgain:end};});
// play/dead accounting
const phaseTicks={};for(let i=0;i<n;i++){const p=meta.phaseCodes[phase[i]];phaseTicks[p]=(phaseTicks[p]||0)+1;}
const restartByKind={};for(const r of restarts){const o=restartByKind[r.kind]??={count:0,waits:[]};o.count++;if(r.wait!=null)o.waits.push(r.wait);}
for(const o of Object.values(restartByKind)){o.waits.sort((a,b)=>a-b);o.medianWait=o.waits[Math.floor(o.waits.length/2)]??null;o.maxWait=o.waits.at(-1)??null;delete o.waits;}
const goals=evs.filter(e=>e.type==='goal').map(g=>({tick:g.tick,clock:clock(g.tick),team:g.team,scorer:g.lastTouch}));
const shots=kicks.filter(k=>k.kind==='shoot').map(k=>({tick:k.tick,clock:clock(k.tick),player:k.player,team:k.team}));
// per player ball-fixation: share of play ticks ball-directed while >15m from ball
const fix={};for(let j=0;j<N;j++){if(isGK(j))continue;let far=0,bd=0;for(let i=0;i<n;i++){if(phase[i]!==PLAY)continue;if(ballDirected.has(K(i,j))){bd++;if(d2(X(i,j),Y(i,j),BX(i),BY(i))>15)far++;}}fix[ids[j]]={ballDirectedShare:+(bd/playTicks).toFixed(3),farShare:+(far/playTicks).toFixed(3)};}
const flips=(()=>{const last={},f={};for(const l of fs.readFileSync(path.join(dir,'decisions.jsonl'),'utf8').split('\n')){if(!l)continue;const x=JSON.parse(l);const k=x.k.split('|')[0];if(!['support','advance_support','cover'].includes(k))continue;const g=k==='cover'?'d':'a';if(last[x.p]&&last[x.p]!==g)f[x.p]=(f[x.p]||0)+1;last[x.p]=g;}const v=ids.filter((x,j)=>!isGK(j)).map(x=>f[x]||0);return +(v.reduce((a,b)=>a+b,0)/v.length/(playTicks/1200)).toFixed(2);})();
const modeShare={};for(const t of ['A','B']){for(const [k,v] of Object.entries(conc[t]))if(k.startsWith('mode_')){modeShare[k]=(modeShare[k]||0)+v;}}
const summary={supportCoverFlipsPerPlayerPerPlayMin:flips,turnoversPerPlayMin:+(turnovers.length/(playTicks/1200)).toFixed(2),modeShare,run:path.basename(dir),variant:meta.variant,profile:meta.profile,seed:meta.seed,activeConfig:meta.activeConfig,finalTick:meta.finalTick,score:meta.score,result:meta.result,violations:meta.violations?.length,phaseTicks,playSeconds:playTicks/20,
 counts:{contactRows:contactRows.length,touchEpisodes:touches.length,bodyContactRows:bodyRows.length,bodyContactEpisodes:bodyEp.length,bodyContactEpisodesSameTeam:bodyEp.filter(e=>e.sameTeam).length,kicks:kicks.length,kickKinds:kicks.reduce((o,k)=>(o[k.kind]=(o[k.kind]||0)+1,o),{}),shots:shots.length,goals:goals.length,turnovers:turnovers.length},
 concentration:conc,concEpisodes:concEpOut.length,concEpisodeSeconds:+concEpOut.reduce((s,e)=>s+e.dur,0).toFixed(1),jointPressEpisodes:jointOut.length,defence:def,freeBehindEpisodes:behindOut.length,centralEmptyEpisodes:centralOut.length,centralEmptyEpisodesShot:centralOut.filter(e=>e.oppShot5s).length,restartByKind,corners:corners.length,goals,shots,
 passes:{total:passes.length,outcomes:passes.reduce((o,p)=>(o[p.kind+':'+p.outcome]=(o[p.kind+':'+p.outcome]||0)+1,o),{})},fixation:fix,stats:meta.stats};
fs.writeFileSync(path.join(dir,'analysis.json'),JSON.stringify({summary,concEpisodes:concEpOut,jointPress:jointOut,freeBehind:behindOut,centralEmpty:centralOut,transitions:trans,passes,restarts,corners,bodyEpisodes:bodyEp},null,0));
console.log(JSON.stringify(summary).slice(0,4000));
