// Q29C: episodes where a receive decision used a V2-only plan (I17 plan null), split by whether the player's own latest
// WITNESSED touch was by itself ("own") or by someone else ("other"). Follows each to the next play. Read only.
// usage: node v2only_episodes.mjs <setDir> <recording.json.gz> <label> <own|other|all> <out.json>
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import {pathToFileURL} from 'node:url';
const [SET,recF,label,mode,outF]=process.argv.slice(2);const R=p=>pathToFileURL(path.join(SET,'research',p));
const planI17=(await import(R('l21_natural/recovered/playtest_i17/source/integration_i8_standard/core/reception.mjs'))).receptionPlan;
const x=JSON.parse(zlib.gunzipSync(fs.readFileSync(recF)));const F=new Map(x.frames.map(f=>[f.tick,f]));const end=Math.max(...F.keys());
const dec=x.rows.filter(r=>r.channel==='decision'),ev=x.rows.filter(r=>r.channel==='event');const r2=v=>v==null?null:+v.toFixed(2);
const ownLast=o=>!!o.self.observedTouch&&o.self.observedTouch.players.length>0&&o.self.observedTouch.players.every(q=>q.id===o.self.id);
const P=(t,id)=>F.get(t)?.players.find(p=>p.id===id);
const marks=dec.filter(r=>r.decision.reception&&!planI17(structuredClone(r.observation))).map(r=>({tick:r.tick,player:r.player,own:ownLast(r.observation),lastTouch:r.observation.self.observedTouch?.players.map(q=>q.id).join('+')??null})).filter(m=>mode==='all'||(mode==='own')===m.own);
const episodes=[];for(const m of marks){const last=episodes.at(-1);if(last&&last.player===m.player&&m.tick-last.lastTick<=8&&last.own===m.own){last.lastTick=m.tick;last.n++;}else episodes.push({player:m.player,own:m.own,lastTouch:m.lastTouch,firstTick:m.tick,lastTick:m.tick,n:1});}
const out=[];for(const e of episodes){const pid=e.player,team=P(e.firstTick,pid)?.team;
 const touch=ev.find(v=>v.tick>e.firstTick&&v.tick<=e.lastTick+60&&v.player===pid&&(v.type==='kick'||(v.type==='contact'&&v.control)));
 const firstAny=ev.find(v=>v.tick>e.firstTick&&['kick','contact','restart_placement','goal'].includes(v.type)&&(v.type!=='contact'||v.control));
 const outgoing=touch?dec.filter(r=>r.player===pid&&r.tick<=touch.tick&&r.tick>=e.firstTick).at(-1):null;
 const cand=outgoing?(outgoing.decision.candidates||[]).map(c=>`${c.kind}${c.targetId?'→'+c.targetId:''}:${r2(c.score)}`):null;
 const ebi=outgoing?.decision.ballActionIntent?{kind:outgoing.decision.ballActionIntent.kind,targetId:outgoing.decision.ballActionIntent.targetId??null}:null;
 const after=touch?ev.filter(v=>v.tick>touch.tick&&['kick','contact','restart_placement','goal'].includes(v.type)&&(v.type!=='contact'||v.control)):[];
 const nextOther=after.find(v=>(v.player&&v.player!==pid)||v.type==='restart_placement'||v.type==='goal')??null;
 const f=F.get(touch?.tick??e.firstTick);const near=f?f.players.filter(q=>q.id!==pid).map(q=>({id:q.id,team:q.team,d:r2(Math.hypot(q.x-f.ball.x,q.y-f.ball.y))})).sort((a,b)=>a.d-b.d).slice(0,4):[];
 let outcome='no_event_in_window';if(touch&&nextOther)outcome=nextOther.type==='restart_placement'?`out:${nextOther.kind}:${nextOther.team}`:nextOther.type==='goal'?'goal':(nextOther.team===team?'teammate':'opponent')+':'+nextOther.type+(nextOther.control!=null?':ctl='+nextOther.control:'');
 else if(!touch&&firstAny)outcome='no_own_touch; first event '+firstAny.tick+' '+firstAny.type+(firstAny.player?' '+firstAny.player:'')+(firstAny.kind?' '+firstAny.kind:'');
 out.push({arm:label,player:pid,team,own:e.own,lastWitnessedTouch:e.lastTouch,episode:[e.firstTick,e.lastTick],decisions:e.n,touch:touch?{tick:touch.tick,type:touch.type,kind:touch.kind??null,targetId:touch.targetId??null}:null,ticksToTouch:touch?touch.tick-e.firstTick:null,outgoingDecision:outgoing?{tick:outgoing.tick,kind:outgoing.decision.kind,ebi,candidates:cand}:null,nearestAtTouch:near,nextOther:nextOther&&{tick:nextOther.tick,type:nextOther.type,player:nextOther.player??null,team:nextOther.team??null,kind:nextOther.kind??null,control:nextOther.control??null},outcome,windowEnd:end});}
fs.writeFileSync(outF,JSON.stringify(out,null,1));
for(const o of out)console.log(`[${label}] ${o.player}(${o.team}) ${o.own?'OWN':'other:'+o.lastWitnessedTouch} ep ${o.episode[0]}-${o.episode[1]} n${o.decisions} | touch ${o.touch?`${o.touch.tick} ${o.touch.type}${o.touch.kind?':'+o.touch.kind:''}${o.touch.targetId?'→'+o.touch.targetId:''} (+${o.ticksToTouch}t)`:'none'} | chosen ${o.outgoingDecision?`${o.outgoingDecision.tick} ${o.outgoingDecision.kind}${o.outgoingDecision.ebi?' EBI:'+o.outgoingDecision.ebi.kind+'→'+o.outgoingDecision.ebi.targetId:''} ${(o.outgoingDecision.candidates||[]).slice(0,3).join(' ')}`:'-'} | near ${o.nearestAtTouch.map(q=>q.id+':'+q.d).join(' ')} | outcome ${o.outcome}`);
if(!out.length)console.log(`[${label}] no ${mode} V2-only episodes`);
