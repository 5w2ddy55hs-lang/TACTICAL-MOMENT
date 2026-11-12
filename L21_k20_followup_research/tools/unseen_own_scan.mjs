// Scan an UNCHANGED standard match. List every outfield decision where proximity says "ours",
// K20 says "unknown" (no witnessed own-team latest touch) and audit-truth says the own team controls.
// Also track, per player, when K20 recognition would update (first later decision with witnessed own touch),
// and what the player could observe at the time (controller visible now? witnessed-touch age/identity).
// usage: node unseen_own_scan.mjs <I17> <k20branch> <seed> <ticks> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,seedS,ticksS,outF]=process.argv.slice(2);
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('standard');
const {choose:chooseStd}=await import(path.join(I17,'source/integration_i8_standard/core/decision.mjs'));
const {choose:chooseK}=await import(path.join(BR,'decision.mjs'));
const d2=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
let last=null;const rows=[];const open={};const updates=[];
const sink=ev=>{
 if(ev.channel==='event'&&(ev.type==='kick'||ev.type==='contact'))last={t:ev.tick,player:ev.player,team:ev.team,ctrl:ev.type==='kick'||!!ev.control,kind:ev.type==='kick'?ev.kind:(ev.control?'control':'touch')};
 if(ev.channel==='event'&&ev.type==='restart_placement'){last=null;for(const k of Object.keys(open))delete open[k];}
 if(ev.channel!=='decision')return;const o=ev.observation,p=o.self,b=o.ball;
 if(!b||o.restart||p.role==='GK'||p.hand?.holding)return;
 const friends=o.people.filter(q=>q.team===p.team),enemies=o.people.filter(q=>q.team!==p.team);
 const vh=o.people.find(q=>q.holding&&o.tick-q.seenTick<=8);const nf=friends.filter(q=>d2(q,b)<2.1),ne=enemies.filter(q=>d2(q,b)<2.1);
 const prox=vh?vh.team===p.team:nf.length>0&&!ne.length;const wt=p.observedTouch;const wOwn=!!wt&&wt.players.length>0&&wt.players.every(q=>q.team===p.team);
 const kOurs=vh?vh.team===p.team:prox&&wOwn;
 // close an open "unknown" interval when the player's K20 hypothesis becomes ours, or the situation changes
 if(open[ev.player]){const r=open[ev.player];if(kOurs){r.recognisedTick=ev.tick;r.recognisedBy='witnessed_own_touch';updates.push(r);delete open[ev.player];}
  else if(!prox){r.endTick=ev.tick;r.endReason='proximity_no_longer_ours';updates.push(r);delete open[ev.player];}}
 const truthOwn=!!last&&last.ctrl&&last.team===p.team;
 if(prox&&!kOurs&&truthOwn){const a=chooseStd(o),k=chooseK(o);const ctl=o.people.find(q=>q.id===last.player);
  const row={t:ev.tick,p:ev.player,team:p.team,role:p.role,controller:last.player,ctrlTick:last.t,ctrlKind:last.kind,ctrlSince:ev.tick-last.t,
   controllerVisibleNow:!!ctl&&ctl.seenTick===o.tick,controllerRemembered:!!ctl,witnessed:wt?{who:wt.players.map(x=>x.id+':'+x.team+':'+x.part),ageTicks:o.tick-wt.seenTick}:null,
   simultaneousWithOpponent:!!wt&&wt.players.some(x=>x.team!==p.team)&&wt.players.some(x=>x.team===p.team),
   selfDistBall:+d2(p,b).toFixed(1),aheadOfBall:(p.x-b.x)*p.dir>0,baseKind:a.kind,k20Kind:k.kind,kindChanged:a.kind!==k.kind};
  rows.push(row);if(!open[ev.player])open[ev.player]={p:ev.player,team:p.team,firstTick:ev.tick,controller:last.player,ctrlTick:last.t};}
};
const e=g.create('standard',{seed:+seedS,zonalDefence:false},sink);for(let i=0;i<+ticksS&&!e.finished;i++)e.step();
for(const r of Object.values(open)){r.endTick=e.tick;r.endReason='match_end';updates.push(r);}
// episodes: same team & controller, within 40 ticks
const eps=[];for(const r of rows){const L=eps.at(-1);if(L&&L.team===r.team&&L.controller===r.controller&&r.t-L.end<=40){L.end=r.t;L.n++;L.players.add(r.p);L.changed+=r.kindChanged?1:0;}else eps.push({start:r.t,end:r.t,team:r.team,controller:r.controller,ctrlTick:r.ctrlTick,n:1,changed:r.kindChanged?1:0,players:new Set([r.p])});}
const delays=updates.map(u=>({...u,delayTicks:(u.recognisedTick??u.endTick)-u.firstTick}));
const q=a=>{const s=a.slice().sort((x,y)=>x-y);return s.length?{n:s.length,p50:s[Math.floor(s.length*.5)],p90:s[Math.floor(s.length*.9)],max:s.at(-1)}:null;};
const cnt=(f)=>rows.filter(f).length;
const summary={seed:+seedS,decisions:rows.length,kindChanged:cnt(r=>r.kindChanged),kindChanges:rows.filter(r=>r.kindChanged).reduce((o,r)=>(o[r.baseKind+'->'+r.k20Kind]=(o[r.baseKind+'->'+r.k20Kind]||0)+1,o),{}),
 simultaneousWithOpponent:cnt(r=>r.simultaneousWithOpponent),controllerVisibleNow:cnt(r=>r.controllerVisibleNow),witnessedOpponentLast:cnt(r=>r.witnessed&&r.witnessed.who.every(x=>x.split(':')[1]!==r.team)),noWitness:cnt(r=>!r.witnessed),
 ctrlKinds:rows.reduce((o,r)=>(o[r.ctrlKind]=(o[r.ctrlKind]||0)+1,o),{}),episodes:eps.length,episodesWithKindChange:eps.filter(e=>e.changed>0).length,
 recognitionDelayTicks:q(delays.filter(d=>d.recognisedTick!==undefined).map(d=>d.delayTicks)),endedWithoutRecognition:delays.filter(d=>d.recognisedTick===undefined).length,endReasons:delays.reduce((o,d)=>(o[d.recognisedBy??d.endReason]=(o[d.recognisedBy??d.endReason]||0)+1,o),{})};
fs.writeFileSync(outF,JSON.stringify({summary,rows,episodes:eps.map(e=>({...e,players:[...e.players]})),updates:delays}));console.log(JSON.stringify(summary,null,1));
