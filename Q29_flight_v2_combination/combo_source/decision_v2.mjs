import {admissibleReceptionEvidence} from './guarded_reception.mjs';
import {outgoingCandidates} from './outgoing_candidates.mjs';
import {knownBallMotion} from './local_touch_feedback.mjs';
import {receptionPlan} from './reception_v2.mjs';
import {DT,dist,unit,clamp} from './math.mjs';
import {anchor} from './state.mjs';
import {restartPositionTarget,restartApproach} from './restart_contract.mjs';
import {throwStation} from './throw_contract.mjs';
import {goalkeeperPlan} from './goalkeeper.mjs';
// Pure policy: its sole argument is one player's perception DTO, never a world.
// All weights are provisional lab coefficients, NOT adopted A/B behavior modes.
export const choose=o=>chooseScored(o,false);
export function chooseReceptionProposal(o){const original=choose(o);if(['receive','intercept'].includes(original.kind))return original;const proposal=chooseScored(o,true);return ['receive','intercept'].includes(proposal.kind)&&proposal.reception?proposal:original;}
function chooseScored(o,propose){const p=o.self,ball=o.ball,c=o.coach,base=anchor(p,p.dir),friends=o.people.filter(q=>q.team===p.team),enemies=o.people.filter(q=>q.team!==p.team),candidates=[];
 const add=(kind,target,score,reason,extra={})=>{const margin=kind==='throw_position'?-.6:kind==='restart_position'?0:.2;candidates.push({kind,target:{x:clamp(target.x,margin,105-margin),y:clamp(target.y,margin,68-margin)},score,reason,...extra});};
 if(o.restart){const r=o.restart;
  if(r.taker===p.id&&r.kind==='throw_in'){
   const a=throwStation(r),outlets=friends.filter(q=>dist(r,q)>4&&dist(r,q)<28).sort((a,b)=>dist(r,a)-dist(r,b)||(a.id<b.id?-1:1)),q=outlets[0],target=q??{x:clamp(r.x+p.dir*10,1,104),y:r.y===0?12:56};
   if(dist(p,a)<.07&&Math.hypot(p.vx,p.vy)<.03&&o.tick>=r.readyTick)add('throw_in',target,10,'observed_throw_outlet_and_public_line',{targetId:q?.id??null});else add('throw_position',a,10,'public_throw_station');
  }else if(r.taker===p.id&&r.kind==='dropped_ball'){
   const a=restartApproach(r,p,{x:r.x+p.dir*13,y:r.y});
   add('restart_position',a,10,'public_drop_wait_for_ground');
  }else if(r.taker===p.id){const outlets=friends.filter(q=>dist(r,q)>4&&dist(r,q)<38);const q=outlets.find(q=>q.id===p.restartRecipient)||outlets.sort((a,b)=>(dist(r,a)-dist(r,b))||(a.id<b.id?-1:1))[0];
   const outlet=q||{x:clamp(r.x+p.dir*13,.2,104.8),y:34},kickDirection=unit(outlet.x-r.x,outlet.y-r.y);
   const a=restartApproach(r,p,outlet);
   const footDirection=unit(r.x-p.x,r.y-p.y),aligned=footDirection.x*kickDirection.x+footDirection.y*kickDirection.y>.35;
   const edgeApproach=dist(a,p)<.2&&dist(a,r)>=.55;
   if(dist(p,r)<.95&&(aligned||edgeApproach)&&o.tick>=r.readyTick)add('restart_kick',outlet,10,'public_restart_signal_and_approach_angle',{restartKind:r.kind,targetId:q?.id??null});
   else add('restart_position',a,10,'public_restart_approach_opposite_outlet',{targetId:q?.id??null});
  }else{const t=restartPositionTarget(p,r,{x:base.x+(r.x-52.5)*.42,y:base.y});
   add('restart_position',t,9,'public_restart_constraints');}
 }else if(p.hand?.holding){
  const outlets=friends.filter(q=>o.tick-q.seenTick<=8&&dist(p,q)>5&&dist(p,q)<35&&enemies.every(e=>dist(e,q)>2.5)).sort((a,b)=>dist(p,a)-dist(p,b)||(a.id<b.id?-1:1));
  if(p.hand.elapsedSeconds<2)add('keeper_hold',p,10,'own_hands_observation_window');
  else if(outlets.length)add('keeper_throw',outlets[0],10,'observed_available_outlet',{targetId:outlets[0].id});
  else add('keeper_drop',p,10,'no_fresh_safe_outlet_release_to_ground');
 }else if(!ball){if(p.role==='GK'){const plan=goalkeeperPlan(o,{ourPossession:false,canPlay:false});add(plan.kind,plan.target,plan.score,plan.reason);}else add('scan',base,0.4,'no_fresh_ball');}
 else {
  const bp={x:ball.x,y:ball.y},db=dist(p,bp),age=(o.tick-ball.seenTick)*DT;
  const nearFriends=friends.filter(q=>dist(q,bp)<2.1),nearEnemies=enemies.filter(q=>dist(q,bp)<2.1);
  const visibleHolder=o.people.find(q=>q.holding&&o.tick-q.seenTick<=8);
  const ourPossession=visibleHolder?visibleHolder.team===p.team:nearFriends.length>0&&!nearEnemies.length;
  const theirPossession=nearEnemies.length>0&&!nearFriends.length;
  const motion=knownBallMotion(ball),speed=motion?.speed??null;
  // A fresh nearby low ball permits an uncertain attempt, not a slow-ball or control claim.
  const uncertainAttempt=motion===null&&ball.seenTick===o.tick;
  const canPlay=!visibleHolder&&db<1.0&&age<=0.35&&ball.z<0.5&&(p.touch||motion!==null&&speed<8||uncertainAttempt);
  if(canPlay)candidates.push(...outgoingCandidates(o));
  // Prediction uses only remembered positions and finite differences, not future truth.
  let intercept=bp,eta=2.0;
  if(ball.velocityKnown){for(let t=0.1;t<=2.001;t+=0.1){const q={x:clamp(bp.x+clamp(ball.vx,-40,40)*t*0.82,0.3,104.7),y:clamp(bp.y+clamp(ball.vy,-40,40)*t*0.82,0.3,67.7)};intercept=q;eta=t;if(dist(p,q)<(4+p.abilities.pace*0.04)*t+0.8)break;}}
  const reception=!canPlay&&!visibleHolder&&!theirPossession?receptionPlan(o):null;if(reception){intercept=reception.target;eta=reception.eta;}
  const support=privateSupportTarget(o);
  const cover={x:clamp(base.x+(bp.x-52.5)*0.48-p.dir*7,3,102),y:clamp(base.y+(bp.y-34)*0.35,3,65)};
  if(p.role==='GK'){
   const plan=goalkeeperPlan(o,{ourPossession,canPlay});const {kind,target,score,reason,...evidence}=plan;
   add(kind,target,score,reason,evidence);
  }else{
   add(ourPossession?'support':'cover',ourPossession?support:cover,0.65,'private_shape_and_possession_hypothesis');
   let score=1.65-db*0.048+c.press*0.35-(ourPossession&&!(propose&&admissibleReceptionEvidence(o,nearFriends,visibleHolder,motion,reception))?1.5:0)-age*0.4;
   const aheadFriends=friends.filter(q=>dist(q,bp)+2<db).length;score-=Math.min(2,aheadFriends)*0.22;
   if(!canPlay&&!visibleHolder)add(theirPossession?'press':motion!==null&&speed>3?'receive':'intercept',intercept,score,reception?.reason??'observed_ball_eta_and_teammates',{eta,...(reception?{reception}: {})});
   if(ourPossession&&p.role==='CB'&&enemies.every(q=>dist(p,q)>9))add('advance_support',{x:support.x+p.dir*9*c.cbAdvance,y:support.y},0.55+c.cbAdvance*0.6,'cb_self_assessed_space');
   if(ourPossession&&['DM','CM'].includes(p.role)){const advancing=friends.find(q=>q.role==='CB'&&(q.x-p.x)*p.dir> -3);if(advancing)add('cover_exchange',{x:advancing.x-p.dir*9,y:advancing.y},0.92,'observed_cb_position_not_future_intent');}
  }
 }
 candidates.sort((a,b)=>b.score-a.score||(a.kind<b.kind?-1:a.kind>b.kind?1:0)||String(a.targetId??'').localeCompare(String(b.targetId??'')));
 const selected=candidates[0];return {...selected,observedTick:o.tick,applyTick:o.tick+2,candidates:candidates.map(({kind,score,targetId})=>({kind,score,targetId:targetId??null}))};
}

// Export of the original private-shape geometry. No new placement coefficient.
export function privateSupportTarget(o){const p=o.self,base=anchor(p,p.dir),bp=o.ball,c=o.coach;return {x:clamp(base.x+(bp.x-52.5)*0.60,3,102),y:clamp(34+(base.y-34)*(0.55+c.width*0.7)+(bp.y-34)*0.12,3,65)};}
