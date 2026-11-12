// J19 research candidate (NOT adopted): own-observation pressure value.
// Pure function of ONE player's perception DTO (positions/velocities this player
// observed, own abilities). No teammate intent, no world truth, no future events,
// no shared assignment, no "exactly one presser" rule.
//
// Scope (only when the opponent is perceived to hold the ball, i.e. choose() would
// use its theirPossession branch):
//  (A) trailing yield: choose()=press, I am behind the ball and cannot catch the
//      carrier within H, AND I observe at least one teammate whose pressure is
//      effective -> recover to the original private cover target.
//      If no effective teammate is observed, I keep pressing (no "everyone yields").
//  (B) goal-side engagement: choose()=cover(shape), I am goal-side within range, no
//      effective goal-side teammate is observed, and recounting only EFFECTIVE
//      teammates as "ahead" lifts the original press score over the shape score
//      (0.65) -> press/delay from the goal side. Not if my leaving would uncover an
//      observed opponent at/behind my depth that nobody else is near.
import {dist,clamp} from 'I17SRC/math.mjs';
import {choose} from 'I17SRC/decision.mjs';
import {anchor} from 'I17SRC/state.mjs';
import {DT} from 'I17SRC/math.mjs';

export const J19=Object.freeze({horizonS:1.5,challengeM:2.5,goalSideNearM:6,goalSideRangeM:15,goalSideClosingMps:1.5,trailRelClosingMps:1.0,engageRangeM:18,freshTicks:8,dangerRangeM:12,dangerCoverM:6,shapeScore:.65});
const own=(x,dir)=>dir===1?x:105-x;
const unit=(dx,dy)=>{const n=Math.hypot(dx,dy)||1;return {x:dx/n,y:dy/n};};
// copied verbatim from integration_i8_standard/core/zonal_defence.mjs (not exported there)
function pressureTarget(p,b){
 const bv=b.velocityKnown?clamp(b.vx*p.dir,-8,8):0,vy=b.velocityKnown?clamp(b.vy,-8,8):0;
 const closing=Math.max(0,p.vx*p.dir-bv),cushion=clamp(.8+.10*closing,.8,2.5);
 return {x:own(clamp(own(b.x,p.dir)+bv*.20-cushion,.3,104.7),p.dir),y:clamp(b.y+vy*.20,.3,67.7)};
}
// same formula as decision.mjs private cover candidate
const coverTarget=(p,bp)=>{const base=anchor(p,p.dir);return {x:clamp(base.x+(bp.x-52.5)*0.48-p.dir*7,3,102),y:clamp(base.y+(bp.y-34)*0.35,3,65)};};

export function pressureContext(o){
 const p=o.self,b=o.ball;
 if(o.restart||!b||p.role==='GK'||p.hand?.holding||p.touch)return null;
 if(o.tick-b.seenTick>2)return null;
 const fresh=o.people.filter(q=>o.tick-q.seenTick<=J19.freshTicks);
 if(fresh.some(q=>q.holding))return null;
 const friends=fresh.filter(q=>q.team===p.team&&q.role!=='GK'),enemies=fresh.filter(q=>q.team!==p.team);
 const nearF=o.people.filter(q=>q.team===p.team&&dist(q,b)<2.1),nearE=o.people.filter(q=>q.team!==p.team&&dist(q,b)<2.1);
 if(!(nearE.length>0&&!nearF.length))return null; // same theirPossession test as decision.mjs
 const carrier=nearE.slice().sort((a,c)=>dist(a,b)-dist(c,b)||a.id.localeCompare(c.id))[0];
 const cv={x:carrier.vx??0,y:carrier.vy??0};
 const goalSide=q=>own(q.x,p.dir)<own(b.x,p.dir);
 const vmaxSelf=4+p.abilities.pace*.04;
 const assess=(q,isSelf)=>{const d=dist(q,b),u=unit(b.x-q.x,b.y-q.y),closing=(q.vx*u.x+q.vy*u.y),away=cv.x*u.x+cv.y*u.y;
  if(goalSide(q))return {id:q.id,goalSide:true,d,closing,effective:d<=J19.goalSideNearM||(d<=J19.goalSideRangeM&&closing>=J19.goalSideClosingMps)};
  if(d<=J19.challengeM)return {id:q.id,goalSide:false,d,closing,effective:true};
  const rel=isSelf?vmaxSelf-away:closing-away;const t=rel>0?(d-1.5)/rel:Infinity;
  return {id:q.id,goalSide:false,d,closing,rel,catchS:Number.isFinite(t)?+t.toFixed(2):null,effective:isSelf?t<=J19.horizonS:(rel>=J19.trailRelClosingMps&&t<=J19.horizonS)};};
 return {p,b,carrier,friends,enemies,self:assess(p,true),mates:friends.map(q=>assess(q,false))};
}

export function chooseJ19(o){
 const d=choose(o);
 if(!['press','cover'].includes(d.kind))return d;
 const c=pressureContext(o);if(!c)return d;
 const {p,b}=c;const effMates=c.mates.filter(m=>m.effective);
 if(d.kind==='press'&&d.reason==='observed_ball_eta_and_teammates'){
  if(c.self.goalSide||c.self.effective||!effMates.length)return d;
  const t=coverTarget(p,{x:b.x,y:b.y});
  return {...d,kind:'cover',target:{x:clamp(t.x,.2,104.8),y:clamp(t.y,.2,67.8)},reason:'J19_trailing_yield_to_observed_effective_pressure'};
 }
 if(d.kind==='cover'&&d.reason==='private_shape_and_possession_hypothesis'){
  if(!c.self.goalSide||c.self.d>J19.engageRangeM)return d;
  if(effMates.some(m=>m.goalSide))return d;
  // recount the ORIGINAL press score with only effective teammates as "ahead"
  const age=(o.tick-b.seenTick)*DT,db=c.self.d;
  const aheadEff=c.mates.filter(m=>m.effective&&m.d+2<db).length;
  const score=1.65-db*0.048+o.coach.press*0.35-age*0.4-Math.min(2,aheadEff)*0.22;
  if(!(score>J19.shapeScore))return d;
  // do not step out if it uncovers an observed opponent at/behind my depth that no one else is near
  const danger=c.enemies.find(q=>q.id!==c.carrier.id&&dist(q,p)<J19.dangerRangeM&&own(q.x,p.dir)<=own(p.x,p.dir)+2&&!c.friends.some(f=>f.id!==p.id&&dist(f,q)<J19.dangerCoverM&&own(f.x,p.dir)<=own(q.x,p.dir)+1));
  if(danger)return d;
  return {...d,kind:'press',target:pressureTarget(p,b),score,reason:'J19_goalside_engage_no_effective_pressure'};
 }
 return d;
}
