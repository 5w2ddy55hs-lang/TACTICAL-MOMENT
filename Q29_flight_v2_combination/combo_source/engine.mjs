import {ATTENTION_CONTRACT,validateAttentionEnvelope,issueOutletAttention,recordOutletAttentionSense,migrateValidatedSOC21B} from './outlet_attention.mjs';
import {MatchEngine as ParentSOC23} from '../../soc23_outlet_attention/core/engine.mjs';
import {choosePassInteraction} from './pass_interaction.mjs';
import {choosePassFlight} from './pass_flight_choice.mjs';
import {PASS_BUILD_SHA256,PASS_SAVE_SCHEMA,PASS_ENGINE,PASS_RESULT_SCHEMA} from './pass_build_identity.mjs';
import {MatchEngine as ParentSOC21B} from '../../soc21b_motor_handoff/core/engine.mjs';
import {refreshSelfKickIntent,projectSelfKickTransport,preflightSelfKickSave} from './self_kick_intent.mjs';
import {registerSelfKickTransport,refreshSelfKickTransport,selfKickTransportAppliedCommand} from './self_kick_transport.mjs';
import {registerConditional,refreshConditional,projectConditionalOrdinary,conditionalAppliedCommand} from './conditional_transport_exit.mjs';
import {projectOrdinaryTransport} from './own_transport_choice.mjs';
import {attachPendingTouchCondition,checkPendingTouchCondition} from './pending_touch_condition.mjs';
import {projectOwnTouchCarry} from './self_touch_continuity.mjs';
import {chooseEarlyExit} from './early_exit_choice.mjs';
import {MatchEngine as ParentDPG1} from '../../parent_dpg1/core/engine.mjs';
import {OPC_SAVE_CONTRACT,validateOrdinaryPassContinuityEnvelope,validateParentDPG1Envelope,migrateValidatedParentDPG1} from './ordinary_pass_continuity_identity.mjs';
import {attachOrdinaryPassContinuity,registerOrdinaryPassContinuity,applyOrdinaryPassContinuity,refreshOrdinaryPassContinuity,preflightOrdinaryPassContinuitySave} from './ordinary_pass_continuity.mjs';
import {MatchEngine as ParentEDR1} from '../../parent_edr1/core/engine.mjs';
import {DPG_SAVE_CONTRACT,validateDirectionalEnvelope,validateParentEDR1Envelope,migrateValidatedParentEDR1} from './directional_pressure_identity.mjs';
import {reviseDirectionalOrdinaryTransaction} from './directional_pressure_preference.mjs';
import {migrateValidatedParentR2,EDR_SAVE_CONTRACT as EBI_SAVE_CONTRACT,validateEarlyDribbleEnvelope as validateEarlyBallIntentEnvelope} from './early_dribble_identity.mjs';
import {migrateValidatedParentEBI1} from './guarded_reception_identity.mjs';
import {attachEarlyBallIntent,registerEarlyBallIntent,refreshBallIntentExecution,finalizeBallIntentReferences,preflightEarlyBallIntentSave,earlyMotorStoppedAfterOwnKick} from './early_ball_intent.mjs';
import {projectOwnAppliedCommand} from './timed_motor_prediction.mjs';
import {BPC_SAVE_CONTRACT,validateBodyPreparationEnvelope} from './body_preparation_identity.mjs';
import {ownMotorCommand,attachBodyPreparation,preflightBodyPreparationSave} from './body_preparation.mjs';
import {preflightWitnessedSave} from './witnessed_touch_motion.mjs';
import {preflightReleaseSave,releaseDataOnly} from './uncertain_release_contract.mjs';
import {emptyLocalTouchFeedback,inheritedBallEvidence} from './local_touch_feedback.mjs';
import {decideRecoveryConnection,evaluateRecovery} from './recovery_connection.mjs';
import {emptyRecoveryMemory,emptyRecoveryChannel,syncRecoveryScope,recoveryContext,enqueueRecovery} from './recovery_contract.mjs';
import {initializeCoachDelivery,registerCoachInput,scheduleCoachDelivery,issueCoachPlan,processCoachDeliveries,recordCoachDecision,recordCoachActionApplied} from './coach_delivery.mjs';
import {captureOverlapMotorContinuation,overlapReviewView,resolveAdvantageOverlap} from '../officials/overlap_review.mjs';
import {recordInputReceipt} from './input_receipts.mjs';
import {advantageBlock,advantageView,advantageDue,decideAdvantage,reportAdvantageBenefit} from '../officials/advantage.mjs';
import {encodePreparedContinuation,decodePreparedContinuation} from './tick_continuation.mjs';
import {activePlayers,isActive,isGoalkeeper,effectiveRole,nominateKeeper,recordParticipationTick} from './participation.mjs';
import {disciplineReviewBlock,disciplineReviewView,disciplineCardView,resolveDisciplineReview,openDeferredDisciplineReview,activateDeferredDisciplineReviews} from '../officials/discipline.mjs';
import {recordEffort} from '../shared/movement.mjs';
import {moveOfficials,officialsView} from '../officials/agents.mjs';
import {checkKeeperClock,executeKeeperRelease,keeperClockCandidate} from './keeper_hands.mjs';
import {DT,clone,canonical,fingerprint,order,dist,finiteTree} from './math.mjs';
import {createState,validateState,emit,SCHEMA,ENGINE,validateRefereeInput,validateCountdownInput} from './state.mjs';
import {sense,assertObservation} from './perception.mjs';
import {choose} from './decision_v2.mjs';
import {chooseLocalRoleHandoff as chooseZonal} from './local_role_handoff.mjs';
import {movePlayers,prepareMovement,commitMotorVelocities} from './motion.mjs';
import {HOLD_IMPULSE_EPS} from './holding.mjs';
import {collectHoldingCandidates,applyHoldingCandidate} from './general_fouls.mjs';
import {executeKicks,integrateBall} from './ball.mjs';
import {updateClock,beginRestart,repairRestartTaker,settleRuleAdvantage,finishAbandoned,completePeriod} from './rules.mjs';
import {releaseDrop,integrateDrop} from './dropped_ball.mjs';
import {restartSpotAllowed} from './restart_contract.mjs';
import {startThrow,integrateThrow,checkRestartCountdown} from './throw_in.mjs';
import {clearReturnedAccess} from './field_bounds.mjs';
import {validateCoach} from '../adapters/players.mjs';
// SOC1: unsupported special/native-reset packets remain outside prediction scope.
function socOwnCommand(a){
 if(a.bodyPreparation||a.ballActionIntent||a.ordinaryPassContinuity)return null;
 if(!a.target||![a.target.x,a.target.y].every(Number.isFinite)||a.target.x<0||a.target.x>105||a.target.y<0||a.target.y>68)return null;
 if(!Number.isSafeInteger(a.applyTick)||a.applyTick<0||!(a.observedTick===-1&&a.applyTick===0||a.observedTick>=0&&(a.applyTick===a.observedTick+2||a.kind==='wait'&&a.applyTick===a.observedTick)))return null;
 return projectOwnAppliedCommand(a);
}
function appliedCommand(p,s){return p.action.selfKickTransport?selfKickTransportAppliedCommand(p,{phase:s.phase,goalkeeper:isGoalkeeper(s,p),keeperHold:Boolean(s.keeperHold),unprepared:true,declaredHolding:activePlayers(s).some(q=>q.action.kind==='hold_opponent')}):conditionalAppliedCommand(p);}
function refreshSelfKick(p,s,sink){const scope={phase:s.phase,epoch:s.recoveryConnection.scope.epoch};refreshSelfKickIntent(p,s.tick,scope,sink);refreshSelfKickTransport(p,s.tick,scope,sink);}
export class MatchEngine {
 #s;#sink;#passPrinciples;
 constructor(options={},sink=null){if(options.passPrinciples!==undefined&&typeof options.passPrinciples!=='boolean')throw Error('PASS_PRINCIPLES_MODE');this.#passPrinciples=options.passPrinciples??true;this.#s=createState(options);this.#sink=sink;validateState(this.#s);}
 static restore(text,sink=null){
  const input=typeof text==='string'?JSON.parse(text):text;releaseDataOnly(input);
  const wrapped=clone(input);
  if(!wrapped||Object.keys(wrapped).sort().join()!==['schema','engine','buildSha256','mode','checksum','native'].sort().join()||wrapped.schema!==PASS_SAVE_SCHEMA||wrapped.engine!==PASS_ENGINE||wrapped.buildSha256!==PASS_BUILD_SHA256||!['ON','OFF'].includes(wrapped.mode))throw Error('PASS_PRINCIPLES_SAVE_IDENTITY');
  if(fingerprint({mode:wrapped.mode,native:wrapped.native})!==wrapped.checksum)throw Error('PASS_PRINCIPLES_SAVE_CHECKSUM');
  const envelope=wrapped.native;
  preflightSelfKickSave(envelope);preflightOrdinaryPassContinuitySave(envelope);preflightEarlyBallIntentSave(envelope);preflightBodyPreparationSave(envelope);preflightWitnessedSave(envelope);preflightReleaseSave(envelope);
  validateAttentionEnvelope(envelope);validateEarlyBallIntentEnvelope(envelope);validateBodyPreparationEnvelope(envelope);
  if(envelope.schema!==SCHEMA||envelope.engine!==ENGINE)throw Error('UNSUPPORTED_SAVE_SCHEMA');
  if(fingerprint(envelope.state)!==envelope.checksum)throw Error('SAVE_CHECKSUM');
  validateState(envelope.state);const engine=new MatchEngine({passPrinciples:wrapped.mode==='ON'});engine.#s=clone(envelope.state);engine.#s.players.sort(order);engine.#s.officials.sort(order);engine.#sink=sink;return engine;
 }
 static importSOC23(text,sink=null,{enabled=true}={}){const parent=ParentSOC23.restore(text);if(parent.finished)throw Error('PASS_PRINCIPLES_LIVE_IMPORT_ONLY');return MatchEngine.fromFixture(parent.exportState(),sink,{enabled});}
 // Explicit live-only migration. Historic final results remain owned by their
 // original engine; neither terminal phase is relabelled or restarted here.
 static importLegacyFLAC4(){throw Error('RCN1_REQUIRES_AUTHENTIC_PARENT_IMPORT');}
 static importRevision05(){throw Error('RCN1_REQUIRES_AUTHENTIC_PARENT_IMPORT');}
 // Explicit schema extension, NOT identity-only compatibility. No old RECOVER
 // history is inferred from pending actions, recorded DTOs or a different family.
 static importParentResearch(){throw Error('LTC1_REQUIRES_AUTHENTIC_RCN1_IMPORT');}
 static importParentRCN1(){throw Error('NAC1_REQUIRES_AUTHENTIC_LTC1_IMPORT');}
 // Only the frozen direct BPC rev2 parent may enter through explicit migration.
 static importParentLTC1(){throw Error('EBI1_REQUIRES_AUTHENTIC_BPC2_IMPORT');}
 static importParentNAC1(){throw Error('EBI1_REQUIRES_AUTHENTIC_BPC2_IMPORT');}
 static importParentLUR1(){throw Error('EBI1_REQUIRES_AUTHENTIC_BPC2_IMPORT');}
 static importParentPAI1(){throw Error('EBI1_REQUIRES_AUTHENTIC_BPC2_IMPORT');}
 static importParentTCT1(){throw Error('EBI1_REQUIRES_AUTHENTIC_BPC2_IMPORT');}
 static importParentBPC2(){throw Error('GRC1_REQUIRES_AUTHENTIC_EBI1_IMPORT');}
 static importParentEBI1(){throw Error('EDR1_REQUIRES_AUTHENTIC_R2_IMPORT');}
 static importParentR2(){throw Error('DPG1_REQUIRES_AUTHENTIC_EDR1_IMPORT');}
 static importParentEDR1(){throw Error('OPC1_REQUIRES_AUTHENTIC_DPG1_IMPORT');}
 static importParentDPG1(text,sink=null){const envelope=typeof text==='string'?JSON.parse(text):text;validateParentDPG1Envelope(envelope);const old=ParentDPG1.restore(text),s=migrateValidatedParentDPG1(old.exportState());return MatchEngine.fromFixture(s,sink);}
 // Validation fixture import is deliberately separate from supported save migration.
 static importSOC21B(text,sink=null){const parent=ParentSOC21B.restore(text);const state=migrateValidatedSOC21B(parent.exportState());return MatchEngine.fromFixture(state,sink);}
 static fromFixture(state,sink=null,{enabled=true}={}){if(typeof enabled!=='boolean')throw Error('PASS_PRINCIPLES_MODE');validateState(state);const e=new MatchEngine({passPrinciples:enabled});e.#s=clone(state);e.#s.players.sort(order);e.#s.officials.sort(order);e.#sink=sink;return e;}
 exportState(){return clone(this.#s);}
 save(){const state=this.exportState(),mode=this.#passPrinciples?'ON':'OFF',native={schema:SCHEMA,engine:ENGINE,outletAttentionContract:ATTENTION_CONTRACT,ordinaryPassContinuityContract:OPC_SAVE_CONTRACT,directionalPressureContract:DPG_SAVE_CONTRACT,bodyPreparationContract:BPC_SAVE_CONTRACT,earlyBallIntentContract:EBI_SAVE_CONTRACT,checksum:fingerprint(state),state};return JSON.stringify({schema:PASS_SAVE_SCHEMA,engine:PASS_ENGINE,buildSha256:PASS_BUILD_SHA256,mode,checksum:fingerprint({mode,native}),native});}
 validationSnapshot(){const s=this.#s;return {physical:this.physicalSnapshot(),score:clone(s.score),stats:clone(s.stats),rng:s.players.map(p=>({id:p.id,rng:clone(p.rng)}))};}
 physicalSnapshot(){return {phase:this.#s.phase,keeperHold:clone(this.#s.keeperHold),ball:clone(this.#s.ball),players:this.#s.players.map(p=>({id:p.id,x:p.x,y:p.y,vx:p.vx,vy:p.vy,saveReach:p.saveReach,role:effectiveRole(this.#s,p),goalkeeping:p.abilities.goalkeeping}))};}
 stateHash(){return fingerprint(this.#s);}
 canonicalState(){return canonical(this.#s);}
 get tick(){return this.#s.tick;}
 get blocked(){const s=this.#s;if(this.finished)return null;return clone(s.generalFouls.blocked??advantageBlock(s)??disciplineReviewBlock(s)??(!this.finished&&['A','B'].some(t=>s.participation.keepers[t]===null)?{kind:'keeper_nomination',reason:'active_goalkeeper_required',teams:['A','B'].filter(t=>s.participation.keepers[t]===null)}:null));}
 get finished(){return ['finished','abandoned'].includes(this.#s.phase);}
 get phase(){return this.#s.phase;}
 result(){const native=clone(this.#s.result);return native===null?null:{schema:PASS_RESULT_SCHEMA,engine:PASS_ENGINE,buildSha256:PASS_BUILD_SHA256,mode:this.#passPrinciples?'ON':'OFF',native};}
 view(){const s=this.#s;return {blocked:this.blocked,disciplineReviews:disciplineReviewView(s),cards:disciplineCardView(s),advantage:advantageView(s),overlapReview:overlapReviewView(s),participation:clone(s.participation),clockStop:clone(s.clockStop),tick:s.tick,seconds:s.halfTick*DT+(s.half-1)*s.config.halfTicks*DT,half:s.half,phase:s.phase,keeperHold:clone(s.keeperHold),score:clone(s.score),officials:officialsView(s),players:s.players.map(p=>({id:p.id,team:p.team,role:p.role,x:p.x,y:p.y,heading:p.heading,energy:p.energy,action:p.action.kind,active:isActive(s,p.id),goalkeeper:isGoalkeeper(s,p)})),ball:clone(s.ball),events:clone(s.events.slice(-12)),eventDigest:s.eventDigest};}
 // Input is a framework received from a coach module, not an operator's forced player action.
 scheduleCoachFramework({id,tick,team,framework,deliveries}){const s=this.#s;if(this.finished||typeof id!=='string'||!id||!Number.isInteger(tick)||tick<s.tick||(s.discipline.continuation||s.advantage.continuation||s.overlapReview.continuation||s.generalFouls.blocked||s.clockStop)&&tick===s.tick||!['A','B'].includes(team)||s.inputs.some(x=>x.id===id)||this.#usedInputId(id))throw Error('INPUT_CONTRACT');validateCoach(framework);registerCoachInput(s,{id,tick,team,framework},deliveries);s.inputs.push({id,tick,team,framework:clone(framework)});s.inputs.sort((a,b)=>a.tick-b.tick||(a.id<b.id?-1:1));}
 // Test-specified arrival; this boundary supplies no hearing model or invented RNG.
 scheduleCoachDelivery(input){const s=this.#s;if(this.finished||(s.discipline.continuation||s.advantage.continuation||s.overlapReview.continuation||s.generalFouls.blocked||s.clockStop)&&input?.tick===s.tick)throw Error('COACH_DELIVERY_PAST_BOUNDARY');scheduleCoachDelivery(s,input);}
 // Trusted referee/test harness boundary. No player action or future state input.
 scheduleRefereeStop(input){validateRefereeInput(input);const s=this.#s;if(this.finished||input.tick<s.tick||(s.discipline.continuation||s.advantage.continuation||s.overlapReview.continuation||s.generalFouls.blocked||s.clockStop)&&input.tick===s.tick||this.#usedInputId(input.id)||s.inputs.some(i=>i.id===input.id||['referee_stop','referee_countdown'].includes(i.kind)&&i.tick===input.tick))throw Error('REFEREE_INPUT_CONFLICT');s.inputs.push({...clone(input),kind:'referee_stop'});s.inputs.sort((a,b)=>a.tick-b.tick||(a.id<b.id?-1:1));}
 scheduleRestartCountdown(input){validateCountdownInput(input);const s=this.#s;if(this.finished||input.tick<s.tick||(s.discipline.continuation||s.advantage.continuation||s.overlapReview.continuation||s.generalFouls.blocked||s.clockStop)&&input.tick===s.tick||this.#usedInputId(input.id)||s.inputs.some(i=>i.id===input.id||['referee_stop','referee_countdown'].includes(i.kind)&&i.tick===input.tick))throw Error('REFEREE_INPUT_CONFLICT');s.inputs.push({...clone(input),kind:'referee_countdown'});s.inputs.sort((a,b)=>a.tick-b.tick||(a.id<b.id?-1:1));}
 #usedInputId(id){const s=this.#s;return s.discipline.requests.some(r=>r.id===id)||s.advantage.requests.some(r=>r.id===id)||s.participation.nominations.some(r=>r.inputId===id);}
 #transaction(action){const before=clone(this.#s),rows=[];let result;try{result=action(this.#s,row=>rows.push(clone(row)));for(const p of this.#s.players){refreshSelfKick(p,this.#s,row=>rows.push(clone(row)));refreshBallIntentExecution(p,this.#s.tick,row=>rows.push(clone(row)));refreshOrdinaryPassContinuity(p,this.#s.tick,{phase:this.#s.phase,goalkeeper:isGoalkeeper(this.#s,p),keeperHold:Boolean(this.#s.keeperHold),declaredHolding:activePlayers(this.#s).some(q=>q.action.kind==='hold_opponent')});}validateState(this.#s);}catch(error){this.#s=before;throw error;}for(const row of rows)this.#sink?.(row);return result;}
 resolveAdvantageOverlap(input){return this.#transaction((s,sink)=>resolveAdvantageOverlap(s,input,sink));}
 resolveDisciplineReview(input){return this.#transaction((s,sink)=>{const result=resolveDisciplineReview(s,input,sink);if(s.participation.abandonment)finishAbandoned(s,sink);else repairRestartTaker(s,sink);return result;});}
 nominateKeeper(input){return this.#transaction((s,sink)=>{if(!input||Object.keys(input).sort().join(',')!=='id,inputId,reason'||Reflect.ownKeys(input).length!==3)throw Error('PARTICIPATION_NOMINATION_INPUT');for(const k of Object.keys(input))if(!Object.hasOwn(Object.getOwnPropertyDescriptor(input,k),'value'))throw Error('PARTICIPATION_NOMINATION_INPUT');if(this.finished||s.phase!=='restart'&&!s.clockStop||s.inputs.some(i=>i.id===input.inputId)||s.discipline.requests.some(i=>i.id===input.inputId)||s.advantage.requests.some(i=>i.id===input.inputId))throw Error('PARTICIPATION_NOMINATION_INPUT');const result=nominateKeeper(s,input,sink);repairRestartTaker(s,sink);return result;});}
 decideAdvantage(input){return this.#transaction((s,sink)=>decideAdvantage(s,input,sink,{stop:(c,context)=>{applyHoldingCandidate(s,c,sink,context,{stop:true});s.advantage.continuation=null;},apply:(c,context)=>openDeferredDisciplineReview(s,c,context,sink)}));}
 reportAdvantageBenefit(input){return this.#transaction((s,sink)=>reportAdvantageBenefit(s,input,sink,{recall:(r,context)=>{const continued=Boolean(s.advantage.continuation);s.advantage.continuation=null;beginRestart(s,r.kind,r.team,r.spot,sink,'referee_judgment',context);activateDeferredDisciplineReviews(s,{stage:continued?'restart_motion':'before_tick'},sink);}}));}
 step(count=1){if(!Number.isInteger(count)||count<0||count>10000000)throw Error('INVALID_STEP_COUNT');if(this.finished)return this;if(count>0&&this.#s.generalFouls.blocked)throw Error('MATCH_BLOCKED_UNSUPPORTED_FOUL');if(count>0&&disciplineReviewBlock(this.#s))throw Error('MATCH_BLOCKED_DISCIPLINE_REVIEW');if(count>0&&this.blocked)throw Error('MATCH_BLOCKED_'+this.blocked.kind.toUpperCase());for(let k=0;k<count&&!this.finished;k++){this.#step();if(this.blocked)break;}return this;}
 #step(){let failed=false;try{return this.#stepBody();}catch(error){failed=true;throw error;}finally{for(const p of this.#s.players){refreshConditional(p,this.#s.tick,this.#s.phase,this.#sink);refreshSelfKick(p,this.#s,this.#sink);}finalizeBallIntentReferences(this.#s.players,this.#s.tick,this.#sink,failed);for(const p of this.#s.players){if(failed){try{refreshOrdinaryPassContinuity(p,this.#s.tick,{phase:this.#s.phase,goalkeeper:isGoalkeeper(this.#s,p),keeperHold:Boolean(this.#s.keeperHold),declaredHolding:activePlayers(this.#s).some(q=>q.action.kind==='hold_opponent')});}catch{}}else refreshOrdinaryPassContinuity(p,this.#s.tick,{phase:this.#s.phase,goalkeeper:isGoalkeeper(this.#s,p),keeperHold:Boolean(this.#s.keeperHold),declaredHolding:activePlayers(this.#s).some(q=>q.action.kind==='hold_opponent')});}}}
 #stepBody(){const s=this.#s;s.players.sort(order);
  if(s.halfTick===s.config.halfTicks){completePeriod(s,this.#sink);if(this.finished||this.blocked)return;}
  if(advantageDue(s)){settleRuleAdvantage(s,'deadline',this.#sink);activateDeferredDisciplineReviews(s,{stage:'before_tick'},this.#sink);if(this.blocked)return;}
  if(s.advantage.continuation){const prepared=decodePreparedContinuation(s);s.advantage.continuation=null;executeKicks(s,this.#sink,[],prepared);checkKeeperClock(s,this.#sink);executeKeeperRelease(s,this.#sink);if(s.phase==='restart')activateDeferredDisciplineReviews(s,{stage:'restart_motion'},this.#sink);if(this.blocked)return;this.#completeTick(prepared);return;}
  if(s.discipline.continuation){this.#completeTick(null);return;}
  for(const input of s.inputs.filter(x=>x.tick===s.tick)){if(input.kind==='referee_countdown'){const r=s.restart,accepted=Boolean(r&&['throw_in','goal_kick'].includes(r.kind)&&!r.countdown);recordInputReceipt(s,emit(s,'referee_countdown_received',{inputId:input.id,accepted,kind:r?.kind??null,reason:'external_referee_delay_judgment'},this.#sink));if(accepted){r.countdown={startedTick:s.tick,deadlineTick:s.tick+100};emit(s,'restart_countdown_started',{kind:r.kind,team:r.team,...r.countdown},this.#sink);}continue;}if(input.kind==='referee_stop'){
   // A straddling ball whose centre is outside the field needs a future rule
   // extension; refuse explicitly instead of moving it to an invented spot.
   const placement=restartSpotAllowed({kind:'dropped_ball',x:s.ball.x,y:s.ball.y}),accepted=s.phase==='play'&&placement;
   recordInputReceipt(s,emit(s,'referee_stop_received',{inputId:input.id,team:input.team,reason:input.reason,accepted,phase:s.phase,ignoredReason:accepted?null:s.phase!=='play'?'already_stopped':'centre_outside_field_unimplemented'},this.#sink));
   if(accepted)beginRestart(s,'dropped_ball',input.team,{x:s.ball.x,y:s.ball.y},this.#sink);continue;
  }s.coaches[input.team]=clone(input.framework);recordInputReceipt(s,emit(s,'coach_framework_received',{inputId:input.id,team:input.team,framework:input.framework},this.#sink));issueCoachPlan(s,input);}
  processCoachDeliveries(s,this.#sink);
  if(s.phase==='restart'){activateDeferredDisciplineReviews(s,{stage:'restart_motion'},this.#sink);if(this.blocked)return;}
  for(const p of s.players){refreshSelfKick(p,s,this.#sink);refreshConditional(p,s.tick,s.phase,this.#sink);refreshBallIntentExecution(p,s.tick,this.#sink);refreshOrdinaryPassContinuity(p,s.tick,{phase:s.phase,goalkeeper:isGoalkeeper(s,p),keeperHold:Boolean(s.keeperHold),declaredHolding:activePlayers(s).some(q=>q.action.kind==='hold_opponent')});}
  // Boundary A: all observers use the same pre-movement world. No actions commit until everyone senses.
  syncRecoveryScope(s);const recoverySnapshot=clone(s.recoveryConnection),recoveryOutgoing=[];
  const observations=[];for(const p of activePlayers(s))if(s.tick>=p.nextDecision){const o=sense(s,p);assertObservation(o);recordOutletAttentionSense(p,o,this.#sink);observations.push({p,o});p.nextDecision=s.tick+4+Math.floor((100-p.abilities.decision)/35);}
  for(const {p,o} of observations){
   let recoveryTransaction=null;
   if(s.config.zonalDefence&&(s.config.zonalDefenceSide==='both'||s.config.zonalDefenceSide===p.team)){
    const prior=p.recoveryMemory,context=recoveryContext(o,recoverySnapshot);
    const result=decideRecoveryConnection(o,s.config.fiveLaneBoundaries,prior,context,socOwnCommand(appliedCommand(p,s)),{kind:p.action.kind,reason:p.action.reason??null,runnerId:p.action.zonal?.runnerId??null},projectOwnTouchCarry(p,s.tick),projectConditionalOrdinary(p,s.tick),projectSelfKickTransport(p,s.tick,appliedCommand(p,s),{phase:s.phase,epoch:s.recoveryConnection.scope.epoch}));
    if(result.audit.selfKickTransport)this.#sink?.({channel:'self_kick_transport_comparison',tick:s.tick,player:p.id,...clone(result.audit.selfKickTransport)});
    if(result.audit.conditionalExit)this.#sink?.({channel:'conditional_exit_composition',tick:s.tick,player:p.id,...clone(result.audit.conditionalExit)});
    if(result.audit.ownTransport?.exitComparison)this.#sink?.({channel:'transport_exit_comparison',tick:s.tick,player:p.id,...clone(result.audit.ownTransport.exitComparison)});
    if(result.audit.ownTransport)this.#sink?.({channel:'own_transport_comparison',tick:s.tick,player:p.id,...clone(result.audit.ownTransport)});
    if(result.audit.selfTouchContinuity)this.#sink?.({channel:'self_touch_continuity',tick:s.tick,player:p.id,...clone(result.audit.selfTouchContinuity)});
    if(result.audit.preparationWork)this.#sink?.({channel:'preparation_work_comparison',tick:s.tick,player:p.id,...clone(result.audit.preparationWork)});
    if(result.audit.horizonWork)this.#sink?.({channel:'horizon_work_comparison',tick:s.tick,player:p.id,...clone(result.audit.horizonWork)});
    p.pending=result.decision;
    if(this.#passPrinciples)recoveryTransaction={prior,context,result};
    else{p.recoveryMemory=result.memory;recoveryOutgoing.push(...result.outgoing);this.#sink?.({channel:'recovery_connection',tick:s.tick,player:p.id,audit:clone(result.audit),outgoing:clone(result.outgoing)});}
   }else p.pending=choose(o);
   const directional=reviseDirectionalOrdinaryTransaction(o,{decision:p.pending});
   p.pending=directional.transaction.decision;
   this.#sink?.({channel:'directional_pressure',tick:s.tick,player:p.id,applied:directional.applied,reason:directional.reason,sharedChallenge:directional.evaluated?.sharedChallenge??null,candidates:clone(directional.evaluated?.diagnostics??[])});
   // Compose after the pure policy, before committing RCN memory or packet hashes.
   // Only the owner's applied action is projected; pending is not yet applied.
   if(this.#passPrinciples){
    const interaction=choosePassInteraction(o,p.pending,ownMotorCommand(appliedCommand(p,s)));
    p.pending=interaction.decision;
    const flight=choosePassFlight(o,p.pending);p.pending=flight.decision;
    if(recoveryTransaction){
     let {result}=recoveryTransaction;
     if(interaction.audit.selected){
      const revised=evaluateRecovery(o,p.pending,recoveryTransaction.prior,recoveryTransaction.context);
      result={...result,...revised,audit:{...revised.audit,passInteraction:clone(interaction.audit),priorPolicyAudit:clone(result.audit)}};
      p.pending=result.decision;
     }
     p.recoveryMemory=result.memory;recoveryOutgoing.push(...result.outgoing);
     this.#sink?.({channel:'recovery_connection',tick:s.tick,player:p.id,audit:clone(result.audit),outgoing:clone(result.outgoing)});
    }
    this.#sink?.({channel:'pass_principles',tick:s.tick,player:p.id,interaction:clone(interaction.audit),flight:clone(flight.audit),decision:clone(p.pending)});
   }
   const policyDecision=p.pending,command=ownMotorCommand(appliedCommand(p,s));
   // A consumed/cancelled-by-own-kick EBI root is now a braking motor, not a
   // live receive command that BPC may resurrect at a later decision.
   p.pending=earlyMotorStoppedAfterOwnKick(p)?policyDecision:attachBodyPreparation(o,command,policyDecision);
   const ownAppliedCommand=!['receive','intercept'].includes(p.pending.kind)||o.restart!==null||o.self.role==='GK'||o.self.hand?.holding||earlyMotorStoppedAfterOwnKick(p)?null:projectOwnAppliedCommand(appliedCommand(p,s));
   const receiverSelection=p.pending;
   p.pending=attachEarlyBallIntent(o,ownAppliedCommand,p.pending);
   const exitChoice=chooseEarlyExit(o,ownAppliedCommand,receiverSelection,p.pending);
   p.pending=exitChoice.decision;
   if(exitChoice.audit.reason!=='not_early_dribble')this.#sink?.({channel:'early_exit_comparison',tick:s.tick,player:p.id,...clone(exitChoice.audit)});
   p.pending=attachOrdinaryPassContinuity(o,p.pending);registerOrdinaryPassContinuity(p,p.pending,s.tick,o);refreshOrdinaryPassContinuity(p,s.tick,{phase:s.phase,goalkeeper:isGoalkeeper(s,p),keeperHold:Boolean(s.keeperHold),declaredHolding:activePlayers(s).some(q=>q.action.kind==='hold_opponent')});
   registerEarlyBallIntent(p,p.pending,s.tick,this.#sink);
   refreshBallIntentExecution(p,s.tick,this.#sink);
   this.#sink?.({channel:'early_ball_intent_composition',tick:s.tick,player:p.id,intentIssued:Object.hasOwn(p.pending,'ballActionIntent'),ownAppliedCommand:clone(ownAppliedCommand),policyDecision:clone(policyDecision),composedDecision:clone(p.pending)});
   this.#sink?.({channel:'body_preparation_composition',tick:s.tick,player:p.id,bodyPreparationIssued:Object.hasOwn(p.pending,'bodyPreparation'),sourceMotorStoppedByOwnKick:earlyMotorStoppedAfterOwnKick(p),ownMotorCommand:clone(command),policyDecision:clone(policyDecision),composedDecision:clone(p.pending)});
   p.pending=attachPendingTouchCondition(p,p.pending,s.tick);
   registerSelfKickTransport(p,p.pending,s.tick,this.#sink);refreshSelfKick(p,s,this.#sink);
   registerConditional(p,p.pending,s.tick,this.#sink);refreshConditional(p,s.tick,s.phase,this.#sink);
   issueOutletAttention(p,o,s.recoveryConnection.scope.epoch,this.#sink);
   this.#sink?.({channel:'decision',tick:s.tick,player:p.id,observation:o,decision:clone(p.pending)});recordCoachDecision(s,p,this.#sink);
  }
  s.recoveryConnection=enqueueRecovery(s.recoveryConnection,recoveryOutgoing,s.tick);
  // Boundary B: two physics ticks of action latency. No same-tick teammate intent in perception.
  for(const p of activePlayers(s))if(p.pending&&p.pending.applyTick<=s.tick){
   const cancellation=checkPendingTouchCondition(p,s.tick,{phase:s.phase,epoch:s.recoveryConnection.scope.epoch});
   if(p.pending.selfTouchCondition)this.#sink?.({channel:'pending_touch_condition',tick:s.tick,player:p.id,policy:'SOC14',...clone(cancellation),pending:clone(p.pending),retainedMotor:clone(p.action)});
   if(cancellation.cancel){if(cancellation.clearMatchingLease)p.recoveryMemory.lease=null;s.recoveryConnection=enqueueRecovery(s.recoveryConnection,cancellation.outgoing,s.tick);p.pending=null;continue;}
   applyOrdinaryPassContinuity(p,p.pending,s.tick,{phase:s.phase,epoch:s.recoveryConnection.scope.epoch,goalkeeper:isGoalkeeper(s,p),keeperHold:Boolean(s.keeperHold),declaredHolding:activePlayers(s).some(q=>q.action.kind==='hold_opponent'),unprepared:true},{events:s.events,eventCount:s.eventCount});if(p.pending.ordinaryPassContinuity){const r=p.ordinaryPassContinuityExecution.records.find(r=>r.requestId===p.pending.ordinaryPassContinuity.requestId);this.#sink?.({channel:'ordinary_pass_continuity_application',tick:s.tick,player:p.id,requestId:r.requestId,status:r.status,reason:r.reason,captureSource:r.capture?.source.currentMotorSource?.contract??(r.capture?'legacy_OPC1':null),motor:r.capture?clone(r.capture.motor):null,untilTick:r.capture?.untilTick??null,nativeCooldown:p.cooldown});}p.action=p.pending;p.pending=null;refreshBallIntentExecution(p,s.tick,this.#sink);refreshOrdinaryPassContinuity(p,s.tick,{phase:s.phase,goalkeeper:isGoalkeeper(s,p),keeperHold:Boolean(s.keeperHold),declaredHolding:activePlayers(s).some(q=>q.action.kind==='hold_opponent')});recordCoachActionApplied(s,p,this.#sink);if(p.action.ballActionIntent)this.#sink?.({channel:'early_ball_intent_applied',tick:s.tick,player:p.id,actionId:p.action.ballActionIntent.actionId,packetHash:fingerprint(p.action),status:p.ballIntentExecution.records.find(r=>r.actionId===p.action.ballActionIntent.actionId)?.status});}
  // Buffer the speculative solve: misses and zero-force gestures keep r9 ordering.
  const motorRows=[];
  let prepared=s.phase==='play'&&activePlayers(s).some(p=>p.action.kind==='hold_opponent')?prepareMovement(s,e=>motorRows.push(e)):null;
  if(prepared&&!prepared.facts.some(f=>f.impulse>HOLD_IMPULSE_EPS)){
   this.#sink?.({channel:'motor',type:'holding_attempt',tick:s.tick,status:'not_established',reason:prepared.facts.length?'no_positive_grip_impulse':'no_actual_hand_contact'});prepared=null;
  }
  if(prepared){
   for(const row of motorRows)this.#sink?.(row);
   commitMotorVelocities(s,prepared);
   const holding=collectHoldingCandidates(s,prepared.facts.filter(f=>f.impulse>HOLD_IMPULSE_EPS),this.#sink),clock=keeperClockCandidate(s);
   try{executeKicks(s,this.#sink,clock?[...holding,clock]:holding,prepared);}catch(error){if(error.message==='MATCH_BLOCKED_CONTINUING_OR_NEW_FOUL_REVIEW')captureOverlapMotorContinuation(s,prepared);throw error;}
   if(advantageBlock(s)){s.advantage.continuation=encodePreparedContinuation(s,prepared);return;}
   if(s.discipline.continuation)return;
   // A confirmed stop prevents a simultaneous hand release and its execution RNG.
   if(!clock)checkKeeperClock(s,this.#sink);
   executeKeeperRelease(s,this.#sink);
  }else{
   checkKeeperClock(s,this.#sink);executeKeeperRelease(s,this.#sink);startThrow(s,this.#sink);checkRestartCountdown(s,this.#sink,'throw_in');releaseDrop(s,this.#sink);
   executeKicks(s,this.#sink);checkRestartCountdown(s,this.#sink,'goal_kick'); // I1 imports Claude R3M deadline ordering
  }
  if(s.phase==='restart'){activateDeferredDisciplineReviews(s,{stage:'restart_motion'},this.#sink);if(this.blocked)return;}
  this.#completeTick(prepared);
 }
 #completeTick(prepared){const s=this.#s;
  const before=movePlayers(s,this.#sink,prepared);
  if(s.restart?.kind==='throw_in')integrateThrow(s,before,this.#sink);else if(s.restart?.kind==='dropped_ball')integrateDrop(s,before,this.#sink);else integrateBall(s,before,this.#sink);
  for(const p of activePlayers(s)){const old=before.find(q=>q.id===p.id);recordEffort(p,old,s.tick,DT,old.fatigueSpeed);if(dist(old,p)>9*DT+1e-7)throw Error('PLAYER_TELEPORT');for(const key of ['x','y','vx','vy','energy'])if(!Number.isFinite(p[key]))throw Error('NAN_PLAYER');}
  finiteTree(s.ball);if(s.players.length!==22||s.ball.id!=='BALL-1')throw Error('IDENTITY_LOSS');
  for(const p of s.players){refreshSelfKick(p,s,this.#sink);refreshConditional(p,s.tick,s.phase,this.#sink);refreshBallIntentExecution(p,s.tick,this.#sink);refreshOrdinaryPassContinuity(p,s.tick,{phase:s.phase,goalkeeper:isGoalkeeper(s,p),keeperHold:Boolean(s.keeperHold),declaredHolding:activePlayers(s).some(q=>q.action.kind==='hold_opponent')});}
  moveOfficials(s);clearReturnedAccess(s);s.discipline.continuation=null;recordParticipationTick(s);s.tick++;updateClock(s,this.#sink);if(s.phase==='restart'&&!s.clockStop&&!disciplineReviewBlock(s))activateDeferredDisciplineReviews(s,{stage:'before_tick'},this.#sink);
 }
}

function assertLiveMigration(state,source){
 if(state.phase==='finished')throw Error(source+'_FINISHED_SAVE_NOT_MIGRATABLE');
 if(state.phase==='abandoned')throw Error(source+'_ABANDONED_SAVE_NOT_MIGRATABLE');
 if(!['play','restart'].includes(state.phase)||state.result!==null)throw Error(source+'_LIVE_SAVE_REQUIRED');
}
