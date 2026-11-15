// Q29C: every episode in a recording where the receive decision used a V2-only plan (I17 plan null) while the player's own
// latest WITNESSED touch was by itself (own pushed ball). Follows each episode to the next play: own touch (kick/contact),
// outgoing choice and candidates, who touches next, restarts, teammates/opponents nearby. Read only.
// usage: node own_touch_episodes.mjs <setDir> <recording.json.gz> <armLabel> <out.json>
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,recF,label,outF]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));
const planI17=(await import(R('l21_natural/recovered/playtest_i17/source/integration_i8_standard/core/reception.mjs'))).receptionPlan;
const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(recF)));const F=new Map(x.frames.map(f=>[f.tick,f]));const end=Math.max(...F.keys());
const dec=x.rows.filter(r=>r.channel==='decision'),ev=x.rows.filter(r=>r.channel==='event');const r2=v=>v==null?null:+v.toFixed(2);
const ownLast=o=>!!o.self.observedTouch&&o.self.observedTouch.players.length>0&&o.self.observedTouch.players.every(q=>q.id===o.self.id);
const P=(t,id)=>F.get(t)?.players.find(p=>p.id===id);
// mark V2-only plan decisions after own touch
const marks=dec.filter(r=>r.decision.reception&&ownLast(r.observation)&&!planI17(structuredClone(r.observation))).map(r=>({tick:r.tick,player:r.player}));
const episodes=[];for(const m of marks){const last=episodes.at(-1);if(last&&last.player===m.player&&m.tick-last.lastTick<=8){last.lastTick=m.tick;last.n++;}else episodes.push({player:m.player,firstTick:m.tick,lastTick:m.tick,n:1});}
const out=[];for(const e of episodes){const pid=e.player,team=P(e.firstTick,pid)?.team;
 const touch=ev.find(v=>v.tick>e.firstTick&&v.player===pid&&(v.type==='kick'||(v.type==='contact'&&v.control)));
 const touchTick=touch?.tick??null;const outgoing=touch?dec.filter(r=>r.player===pid&&r.tick<=touch.tick&&r.tick>e.firstTick-1).at(-1):null;
 const cand=outgoing?(outgoing.decision.candidates||[]).map(c=>`${c.kind}${c.targetId?'→'+c.targetId:''}:${r2(c.score)}`):null;
 const ebi=outgoing?.decision.ballActionIntent?{kind:outgoing.decision.ballActionIntent.kind,targetId:outgoing.decision.ballActionIntent.targetId??null}:null;
 const after=touch?ev.filter(v=>v.tick>touch.tick&&['kick','contact','restart_placement','goal'].includes(v.type)&&(v.type!=='contact'||v.control||v.player!==pid)):[];
 const next=after.find(v=>v.type!=='contact'||v.player!==pid)??null;
 const nextOther=after.find(v=>v.player&&v.player!==pid||v.type==='restart_placement'||v.type==='goal')??null;
 const f=F.get(touchTick??e.firstTick);const near=f?f.players.filter(q=>q.id!==pid).map(q=>({id:q.id,team:q.team,d:r2(Math.hypot(q.x-f.ball.x,q.y-f.ball.y))})).sort((a,b)=>a.d-b.d).slice(0,4):[];
 const p0=P(e.firstTick,pid),pt=touchTick?P(touchTick,pid):null;
 // possession outcome: first event by anyone other than pid after touch within 100 ticks
 let outcome='no_event_in_window';if(nextOther){outcome=nextOther.type==='restart_placement'?`out:${nextOther.kind}:${nextOther.team}`:nextOther.type==='goal'?'goal':(nextOther.team===team?'teammate':'opponent')+':'+nextOther.type+(nextOther.control!=null?':ctl='+nextOther.control:'');}
 out.push({arm:label,player:pid,team,episode:[e.firstTick,e.lastTick],decisions:e.n,posAtFirst:p0&&{x:r2(p0.x),y:r2(p0.y)},touch:touch?{tick:touch.tick,type:touch.type,kind:touch.kind??null,targetId:touch.targetId??null,vel:touch.velocity&&{x:r2(touch.velocity.x),y:r2(touch.velocity.y)},pos:pt&&{x:r2(pt.x),y:r2(pt.y)}}:null,
  ticksToTouch:touchTick?touchTick-e.firstTick:null,outgoingDecision:outgoing?{tick:outgoing.tick,kind:outgoing.decision.kind,ebi,candidates:cand}:null,nearestAtTouch:near,
  nextEvent:next&&{tick:next.tick,type:next.type,player:next.player??null,team:next.team??null,kind:next.kind??null,control:next.control??null},outcome,windowEnd:end});}
fs.writeFileSync(outF,JSON.stringify(out,null,1));
for(const o of out)console.log(`[${label}] ${o.player}(${o.team}) ep ${o.episode[0]}-${o.episode[1]} n${o.decisions} | touch ${o.touch?`${o.touch.tick} ${o.touch.type}${o.touch.kind?':'+o.touch.kind:''}${o.touch.targetId?'→'+o.touch.targetId:''} (+${o.ticksToTouch}t)`:'none'} | chosen ${o.outgoingDecision?`${o.outgoingDecision.tick} ${o.outgoingDecision.kind}${o.outgoingDecision.ebi?' EBI:'+o.outgoingDecision.ebi.kind+'→'+o.outgoingDecision.ebi.targetId:''}`:'-'} ${o.outgoingDecision?.candidates?.slice(0,3).join(' ')??''} | near ${o.nearestAtTouch.map(q=>q.id+':'+q.d).join(' ')} | next ${o.nextEvent?`${o.nextEvent.tick} ${o.nextEvent.type}${o.nextEvent.kind?':'+o.nextEvent.kind:''} ${o.nextEvent.player??''}`:'-'} | outcome ${o.outcome}`);
