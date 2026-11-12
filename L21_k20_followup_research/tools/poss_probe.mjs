// K20 possession probe: restore a state, run [from,to]; for every decision record the possession
// hypothesis exactly as decision.mjs derives it from the player's OWN DTO, plus the player's own
// witnessed-touch memory, and (separately, audit-only) the truth: last executed touch/control.
// usage: node poss_probe.mjs <engineSpec variant:standard|branch:DIR> <I17> <stateFile> <from> <to> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [engineSpec,I17,saveF,fromS,toS,outF]=process.argv.slice(2);const from=+fromS,to=+toS;
const d2=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const recs={decisions:[],events:[],frames:[]};let collect=false;let lastTouch=null;
function perceived(o){const p=o.self,b=o.ball;if(!b)return {ball:null};
 const friends=o.people.filter(q=>q.team===p.team),enemies=o.people.filter(q=>q.team!==p.team);
 const visibleHolder=o.people.find(q=>q.holding&&o.tick-q.seenTick<=8)??null;
 const nf=friends.filter(q=>d2(q,b)<2.1),ne=enemies.filter(q=>d2(q,b)<2.1);
 const nearest=L=>{const s=L.map(q=>({id:q.id,d:+d2(q,b).toFixed(2),age:o.tick-q.seenTick})).sort((a,c)=>a.d-c.d);return s[0]??null;};
 return {ballAgeTicks:o.tick-b.seenTick,ball:[+b.x.toFixed(2),+b.y.toFixed(2)],velocityKnown:b.velocityKnown,vel:[+b.vx.toFixed(2),+b.vy.toFixed(2)],evStatus:b.velocityEvidence?.status??null,
  visibleHolder:visibleHolder?.id??null,nearFriends:nf.map(q=>q.id),nearEnemies:ne.map(q=>q.id),nearestFriend:nearest(friends),nearestEnemy:nearest(enemies),
  ourPossession:visibleHolder?visibleHolder.team===p.team:nf.length>0&&!ne.length,theirPossession:ne.length>0&&!nf.length,
  observedTouch:o.self.observedTouch?{age:o.tick-o.self.observedTouch.seenTick,players:o.self.observedTouch.players.map(x=>x.id+':'+x.team+':'+x.part)}:null,selfDistBall:+d2(p,b).toFixed(2)};}
const sink=ev=>{if(ev.channel==='event'&&(ev.type==='kick'||ev.type==='contact'))lastTouch={t:ev.tick,player:ev.player,team:ev.team,kind:ev.type==='kick'?'kick:'+ev.kind:(ev.control?'contact:control':'contact:nocontrol')};
 if(!collect)return;
 if(ev.channel==='decision'){const d=ev.decision;recs.decisions.push({t:ev.tick,p:ev.player,team:ev.observation.self.team,kind:d.kind,reason:d.reason,target:d.target?[+d.target.x.toFixed(2),+d.target.y.toFixed(2)]:null,perc:perceived(ev.observation),truthLastTouch:lastTouch});}
 else if(ev.channel==='event'&&['kick','contact','restart_placement','throw_in_play','goal'].includes(ev.type))recs.events.push({t:ev.tick,type:ev.type,kind:ev.kind,player:ev.player??ev.taker,team:ev.team,control:ev.control,targetId:ev.targetId});};
let E;
if(engineSpec.startsWith('variant:')){const g=await import(path.join(I17,'research_guard.mjs'));await g.register(engineSpec.slice(8));E={restore:(t,s)=>g.restore(t,engineSpec.slice(8),s)};}
else{const dir=engineSpec.slice(7);const m=await import(path.join(dir,'engine.mjs'));const id=await import(path.join(dir,'pass_build_identity.mjs'));
 // RESEARCH-ONLY state transplant (outer identity labels only; native state & checksum untouched)
 E={restore:(t,s)=>{let x=JSON.parse(t);if(x.inner)x=JSON.parse(x.inner);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return m.MatchEngine.restore(JSON.stringify(x),s);}};}
const e=E.restore(fs.readFileSync(saveF,'utf8'),sink);
while(e.tick<from-1)e.step();collect=true;
const snap=()=>{const s=e.exportState();recs.frames.push({t:s.tick,phase:s.phase,ball:[+s.ball.x.toFixed(2),+s.ball.y.toFixed(2),+s.ball.z.toFixed(2)],ballVel:[+s.ball.vx.toFixed(2),+s.ball.vy.toFixed(2)],p:s.players.map(p=>({id:p.id,x:+p.x.toFixed(2),y:+p.y.toFixed(2),vx:+p.vx.toFixed(2),vy:+p.vy.toFixed(2),act:p.action?.kind??null,actT:p.action?.target?[+p.action.target.x.toFixed(2),+p.action.target.y.toFixed(2)]:null,actReason:p.action?.reason??null}))});};
snap();while(e.tick<to){e.step();snap();}
recs.stateHashEnd=e.stateHash?.()??null;recs.eventDigestEnd=e.exportState().eventDigest;
fs.writeFileSync(outF,JSON.stringify(recs));console.log(JSON.stringify({out:outF,frames:recs.frames.length,decisions:recs.decisions.length,events:recs.events.length}));
