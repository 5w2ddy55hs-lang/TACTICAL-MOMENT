import {DT,dist,clamp,angleDelta} from './math.mjs';
import {estimatedArrival,movementLimits} from './kinematics.mjs';
// R07 RECEIVER POLICY - EXPERIMENT ONLY; runs only on this player's perception.
// No true-world future position, contact events, or direct action/score injection.
const POLICY = 'r07b';
const CONTROL_BUFFER_MPS=POLICY==='r07b'?0.45:0;
const SPATIAL_OFFSETS=POLICY==='r07b'?
 [[0,0,'flight'],[.35,0,'lead_035'],[-.35,0,'trail_035'],[0,.35,'left_035'],[0,-.35,'right_035']]:
 [[0,0,'flight']];
export function receptionPlan(o){
 const p=o.self,b=o.ball;if(!b||b.z>=.5||p.role==='GK')return null;
 // No velocity candidate means the caller retains its generic observed-position intercept.
 if(!b.velocityKnown)return null;
 const age=(o.tick-b.seenTick)*DT;if(age<0||age>.25)return null;
 const vx=clamp(b.vx,-40,40),vy=clamp(b.vy,-40,40),speed=Math.hypot(vx,vy);if(speed<=3)return null;
 const bx=b.x+vx*age,by=b.y+vy*age,dx=bx-p.x,dy=by-p.y,tClosest=-(dx*vx+dy*vy)/(speed*speed);
 if(tClosest>1.5)return null;
 const limits=movementLimits(p);if(tClosest>0&&Math.hypot(dx+vx*tClosest,dy+vy*tClosest)>limits.speed*tClosest+.49)return null;
 const ux=vx/speed,uy=vy/speed,options=[];
 const threshold=3+p.abilities.control*.11;
 for(let k=2;k<=30;k++){
  const t=k*DT,point={x:bx+vx*t,y:by+vy*t};
  for(const [along,lateral,label] of SPATIAL_OFFSETS){
   const target={x:point.x+ux*along-uy*lateral,y:point.y+uy*along+ux*lateral};
   if(target.x<.3||target.x>104.7||target.y<.3||target.y>67.7)continue;
   const q=estimatedArrival(p,target,t),miss=dist(q,point),relative=Math.hypot(vx-q.vx,vy-q.vy);
   const facing=Math.max(0,Math.abs(angleDelta(Math.atan2(-vy,-vx),p.heading))-.28*Math.max(0,k-2));
   // Candidate search is driven by available belief only. Even a low predicted
   // closing speed is not a guarantee of contact/control after action latency.
   const clearancePenalty=Math.max(0,miss-.49)*8;
   const relativePenalty=POLICY==='r07a'?Math.max(0,relative-threshold)*1.5:
     Math.max(0,relative-(threshold-CONTROL_BUFFER_MPS))*2.0;
   const timePenalty=t*.1,facePenalty=facing*.1;
   const cost=clearancePenalty+relativePenalty+timePenalty+facePenalty;
   options.push({target,t,miss,relative,facing,cost,label,predictedVelocity:{x:q.vx,y:q.vy}});
  }
 }
 options.sort((a,b)=>a.cost-b.cost||a.t-b.t||a.label.localeCompare(b.label));const best=options[0];if(!best||best.miss>.8)return null;
 if(tClosest<=0&&(best.miss>.49||best.relative>threshold))return null;
 return {target:best.target,eta:best.t,estimatedMissM:best.miss,estimatedRelativeSpeed:best.relative,
  estimatedFacingError:best.facing,predictedApproachVelocity:best.predictedVelocity,observedBallHeight:b.z,
  experimentPolicy:POLICY,controlBufferMps:CONTROL_BUFFER_MPS,optionCount:options.length,
  optionFamily:best.label,model:'perceived_velocity_local_braking_candidates',reason:'R07_perceived_contact_cost_no_future_truth'};
}
