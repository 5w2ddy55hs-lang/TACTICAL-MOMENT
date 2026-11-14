// P25 contract on one original stop save:
//  (1) lockstep ORIGINAL ck_research (I9 guard restore) vs P25 vs P25-OFF from the save to the stop tick: per-tick stateHash;
//      RNG streams + eventDigest/eventCount every 100 ticks and on each of the last 40 ticks
//  (2) at the stop tick: ORIGINAL and OFF throw I5_CK_MIXED_GROUP_NOT_CONNECTED, P25 continues; event order of that tick and
//      per-player RNG call deltas (the draw itself is stateless)
//  (3) P25 save at the stop tick and at stop+1 -> restore -> 600 ticks: stateHash / eventDigest / RNG equal to the unbroken run
//  (4) save identity separation: ORIGINAL rejects a P25 save; P25 rejects the original save
// usage: node contract_p25.mjs <I17> <p25Dir> <offDir> <envelopeSave.json> <stopTick> <out.json>
import fs from 'node:fs';import path from 'node:path';
const [I17,BR,OFF,saveF,stopS,outF]=process.argv.slice(2);const T=+stopS;
const g=await import(path.join(I17,'research_guard.mjs'));await g.register('ck_research');
const {MatchEngine:Orig}=await import(path.join(I17,'source/integration_i8_ck_research/core/engine.mjs'));
const load=async d=>({E:(await import(path.join(d,'core/engine.mjs'))).MatchEngine,id:await import(path.join(d,'core/pass_build_identity.mjs'))});
const p25=await load(BR),off=await load(OFF);
const raw=fs.readFileSync(saveF,'utf8'),innerText=JSON.parse(raw).inner;
const relabel=id=>{const x=JSON.parse(innerText);x.schema=id.PASS_SAVE_SCHEMA;x.engine=id.PASS_ENGINE;x.buildSha256=id.PASS_BUILD_SHA256;return JSON.stringify(x);};
const evP=[];
const a=g.restore(raw,'ck_research'),b=p25.E.restore(relabel(p25.id),ev=>{if(ev.channel==='event')evP.push(ev);}),c=off.E.restore(relabel(off.id));
const rng=e=>JSON.stringify(e.exportState().players.map(p=>p.rng));const dig=e=>{const s=e.exportState();return s.eventDigest+'/'+s.eventCount;};
const out={save:path.basename(path.dirname(saveF))+'/'+path.basename(saveF),stopTick:T,restoredTick:a.tick,node:process.version};
let hashTicks=0,hashDiff=null,deepChecks=0,deepDiff=null;
while(a.tick<T){
 if(a.stateHash()!==b.stateHash()||a.stateHash()!==c.stateHash()){hashDiff=a.tick;break;}hashTicks++;
 if((a.tick-out.restoredTick)%100===0||T-a.tick<=40){deepChecks++;if(rng(a)!==rng(b)||rng(a)!==rng(c)||dig(a)!==dig(b)||dig(a)!==dig(c)){deepDiff=a.tick;break;}}
 a.step();b.step();c.step();}
out.lockstepToStop={ticksWithIdenticalStateHash:hashTicks,firstHashDifference:hashDiff,rngAndEventDigestChecks:deepChecks,firstRngOrEventDifference:deepDiff,
 atStopTick:{stateHashEqual:a.stateHash()===b.stateHash()&&a.stateHash()===c.stateHash(),rngEqual:rng(a)===rng(b)&&rng(a)===rng(c),eventDigestEqual:dig(a)===dig(b)&&dig(a)===dig(c),stateHash:b.stateHash()}};
const tryStep=e=>{try{e.step();return 'continued';}catch(x){return 'THROW:'+x.message;}};
const saveAtStop=b.save();const before=b.exportState();const calls0=Object.fromEntries(before.players.map(p=>[p.id,p.rng.calls]));const nEv=evP.length;
out.atStop={original:tryStep(a),p25Off:tryStep(c),p25:tryStep(b)};
const after=b.exportState();const delta=Object.fromEntries(after.players.map(p=>[p.id,p.rng.calls-calls0[p.id]]).filter(x=>x[1]!==0));
out.atStop.p25EventsOfThatTick=evP.slice(nEv).filter(e=>e.tick===T).map(e=>({seq:e.seq,type:e.type,kind:e.kind??null,player:e.player??e.winner??null,players:e.players??null,teams:e.teams??null,simultaneous:e.simultaneous??null,reason:e.reason??null}));
out.atStop.p25RngCallDeltaByPlayer=delta;out.atStop.ballAfter={lastTouch:after.ball.lastTouch,lastTeam:after.ball.lastTeam,lastKick:after.ball.lastKick};
const saveAfter=b.save();
const cont=(text)=>{const r=p25.E.restore(text);const m=p25.E.restore(text);return r;};
// continuity: unbroken b vs restored copies
const r0=p25.E.restore(saveAtStop),r1=p25.E.restore(saveAfter);r0.step();
let ok0=true,ok1=true;for(let i=0;i<600;i++){b.step();r0.step();r1.step();if(b.stateHash()!==r0.stateHash())ok0=false;if(b.stateHash()!==r1.stateHash())ok1=false;}
out.saveRestore={fromStopTick_600:{stateHashEqualEveryTick:ok0,eventDigestEqual:dig(b)===dig(r0),rngEqual:rng(b)===rng(r0)},fromStopPlus1_600:{stateHashEqualEveryTick:ok1,eventDigestEqual:dig(b)===dig(r1),rngEqual:rng(b)===rng(r1)},
 saveRoundTripIdentical:p25.E.restore(saveAfter).save()===saveAfter};
const tryR=(C,t)=>{try{C.restore(t);return 'ACCEPTED';}catch(e){return 'REJECTED:'+String(e.message).slice(0,60);}};
out.identity={originalRestoresP25Save:tryR(Orig,saveAfter),p25RestoresOriginalInnerSave:tryR(p25.E,innerText),offRestoresP25Save:tryR(off.E,saveAfter),p25Schema:p25.id.PASS_SAVE_SCHEMA,p25Engine:p25.id.PASS_ENGINE,offSchema:off.id.PASS_SAVE_SCHEMA};
out.activeConfig=after.config;
fs.writeFileSync(outF,JSON.stringify(out,null,1));console.log(JSON.stringify(out));
