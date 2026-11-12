// I18 research candidate (NOT adopted): own-team pass flight shape hypothesis.
// Pure function of ONE player's perception DTO. Uses only what the player has
// witnessed: its own native observed-touch memory (no kick intent/target is in
// it), its own ball estimate, remembered people positions. No future truth,
// no teammate intent, no receiver prediction, no pass-intent notification.
//
// Scope: only rewrites the upstream winner when it is the private shape
// candidate `cover|private_shape_and_possession_hypothesis`. Ball-directed
// scoring (press/intercept/receive), reception, restarts, GK, hands untouched.
import {DT,dist,clamp} from 'I17SRC/math.mjs';
import {choose,privateSupportTarget} from 'I17SRC/decision.mjs';

export const I18=Object.freeze({
 maxKickAgeS:2.5,        // staleness bound for the witnessed kick
 maxBallAgeTicks:2,      // ball observation must be fresh
 minBallSpeed:3,         // slower balls are left to the proximity rule (dribble/settled)
 horizonS:1.0,           // contest check horizon along the observed path
 pathDecay:0.82,         // same constant as decision.mjs intercept model
 opponentReach:(t)=>8*t+0.8, // conservative: unknown opponent ability treated as pace 100 (4+100*.04=8 m/s)
 opponentMemoryTicks:24  // DTO keeps remembered people up to 24 ticks; all of them are considered
});

export function flightContinuationEvidence(o){
 const no=reason=>({claim:false,reason});
 if(o.restart)return no('restart');
 if(o.self.role==='GK'||o.self.hand?.holding)return no('goalkeeper_or_hands');
 const b=o.ball;if(!b)return no('no_ball_memory');
 const t=o.self.observedTouch;if(!t)return no('no_witnessed_touch');
 if(t.players.length!==1)return no('simultaneous_touch_contested');
 const k=t.players[0];
 if(k.team!==o.self.team)return no('last_witnessed_touch_opponent');
 if(k.part!=='foot')return no('last_witnessed_touch_not_kick');
 const age=(o.tick-t.seenTick)*DT;if(age>I18.maxKickAgeS)return no('witnessed_kick_stale');
 if(o.tick-b.seenTick>I18.maxBallAgeTicks)return no('ball_not_fresh');
 const ev=b.velocityEvidence;
 if(!b.velocityKnown||!ev||ev.status!=='estimated')return no('ball_motion_unknown');
 if(!(ev.fromTick>=t.seenTick))return no('motion_not_measured_after_kick');
 const speed=Math.hypot(b.vx,b.vy);if(speed<I18.minBallSpeed)return no('slow_ball_proximity_rule');
 // possession by proximity is the upstream rule; do not override a near opponent
 if(o.people.some(q=>q.team!==o.self.team&&dist(q,b)<2.1))return no('opponent_near_ball');
 // contest: any remembered opponent able to reach the observed path within horizon
 for(let s=0.1;s<=I18.horizonS+1e-9;s+=0.1){
  const q={x:clamp(b.x+b.vx*s*I18.pathDecay,0,105),y:clamp(b.y+b.vy*s*I18.pathDecay,0,68)};
  for(const e of o.people)if(e.team!==o.self.team&&dist(e,q)<I18.opponentReach(s))return {claim:false,reason:'opponent_can_reach_path',contest:{opponent:e.id,atS:+s.toFixed(1)}};
 }
 return {claim:true,reason:'witnessed_teammate_kick_uncontested_path',kicker:k.id,kickAgeS:+age.toFixed(2),speed:+speed.toFixed(2)};
}

export function chooseI18(o){
 const d=choose(o);
 if(d.kind!=='cover'||d.reason!=='private_shape_and_possession_hypothesis')return d;
 const ev=flightContinuationEvidence(o);if(!ev.claim)return d;
 const t=privateSupportTarget(o);
 const target={x:clamp(t.x,.2,104.8),y:clamp(t.y,.2,67.8)};
 return {...d,kind:'support',target,reason:'I18_witnessed_teammate_kick_uncontested',candidates:d.candidates.map(c=>c.kind==='cover'&&c.score===d.score?{...c,kind:'support'}:c)};
}
