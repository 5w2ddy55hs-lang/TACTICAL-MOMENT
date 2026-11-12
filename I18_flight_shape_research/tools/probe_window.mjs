// I18 probe: restore a save, run to [from,to], record per tick per player:
// decision (when issued, with DTO summary), applied action, velocity, position; plus kicks/contacts.
// Usage: node probe_window.mjs <engineModuleURL|variant:standard> <I17dir> <saveFile> <from> <to> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [engineSpec,I17,saveF,fromS,toS,outF]=process.argv.slice(2);const from=+fromS,to=+toS;
const recs={decisions:[],events:[],frames:[]};let collect=false;
const summarizeDTO=o=>({tick:o.tick,ball:o.ball?{x:+o.ball.x.toFixed(2),y:+o.ball.y.toFixed(2),z:+o.ball.z.toFixed(2),seenTick:o.ball.seenTick,vx:+o.ball.vx.toFixed(2),vy:+o.ball.vy.toFixed(2),velocityKnown:o.ball.velocityKnown,ev:o.ball.velocityEvidence?{status:o.ball.velocityEvidence.status,source:o.ball.velocityEvidence.source,fromTick:o.ball.velocityEvidence.fromTick,toTick:o.ball.velocityEvidence.toTick,unknownReason:o.ball.velocityEvidence.unknownReason}:null}:null,observedTouch:o.self.observedTouch,self:{x:+o.self.x.toFixed(2),y:+o.self.y.toFixed(2)},near:o.ball?{friends:o.people.filter(q=>q.team===o.self.team&&Math.hypot(q.x-o.ball.x,q.y-o.ball.y)<2.1).map(q=>q.id),enemies:o.people.filter(q=>q.team!==o.self.team&&Math.hypot(q.x-o.ball.x,q.y-o.ball.y)<2.1).map(q=>q.id)}:null});
const sink=ev=>{if(!collect)return;if(ev.channel==='decision'){const d=ev.decision;recs.decisions.push({t:ev.tick,p:ev.player,kind:d.kind,reason:d.reason,target:d.target?[+d.target.x.toFixed(2),+d.target.y.toFixed(2)]:null,targetId:d.targetId??null,applyTick:d.applyTick,dto:summarizeDTO(ev.observation),cands:(d.candidates||[]).slice(0,4)});}
 else if(ev.channel==='event'&&['kick','contact','restart_placement','throw_in_play','goal'].includes(ev.type)){recs.events.push({t:ev.tick,type:ev.type,kind:ev.kind,player:ev.player??ev.taker,team:ev.team,targetId:ev.targetId,control:ev.control,interception:ev.interception,miscontrol:ev.miscontrol,rel:ev.relativeSpeed});}};
let E,restore;
if(engineSpec.startsWith('variant:')){const g=await import(path.join(I17,'research_guard.mjs'));await g.register(engineSpec.slice(8));E={restore:(t,s)=>g.restore(t,engineSpec.slice(8),s)};}
else if(engineSpec.startsWith('branch:')){const dir=engineSpec.slice(7);const m=await import(path.join(dir,'engine.mjs'));const id=await import(path.join(dir,'pass_build_identity.mjs'));
 // RESEARCH-ONLY state transplant: standard save -> I18 branch. Only the outer identity labels change; native state & checksum untouched.
 E={restore:(t,s)=>{let x=JSON.parse(t);if(x.inner)x=JSON.parse(x.inner);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return m.MatchEngine.restore(JSON.stringify(x),s);}};}
else{const m=await import(engineSpec);E={restore:(t,s)=>m.MatchEngine.restore(JSON.parse(t).inner??t,s)};}
const e=E.restore(fs.readFileSync(saveF,'utf8'),sink);
while(e.tick<from-1)e.step();
collect=true;
const snap=()=>{const s=e.exportState();recs.frames.push({t:s.tick,phase:s.phase,ball:[+s.ball.x.toFixed(2),+s.ball.y.toFixed(2),+s.ball.z.toFixed(2)],p:s.players.map(p=>({id:p.id,x:+p.x.toFixed(2),y:+p.y.toFixed(2),vx:+p.vx.toFixed(2),vy:+p.vy.toFixed(2),act:p.action?.kind??null,actT:p.action?.target?[+p.action.target.x.toFixed(2),+p.action.target.y.toFixed(2)]:null,actReason:p.action?.reason??null,pend:p.pending?.kind??null}))});};
snap();while(e.tick<to){e.step();snap();}
fs.writeFileSync(outF,JSON.stringify(recs));console.log(JSON.stringify({out:outF,frames:recs.frames.length,decisions:recs.decisions.length,events:recs.events.length}));
