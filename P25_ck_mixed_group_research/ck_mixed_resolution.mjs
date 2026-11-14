// P25 research (NOT adopted): adjudication of the corner groups the I5 CK branch left "not connected".
// The original branch resolves ONE case: >=2 aerial corner actions (corner_header / corner_clear / gk_punch) from BOTH
// teams -> cornerDuel(): one physical contact, winner by a stateless ability-weighted draw; and stops the match
// (I5_CK_MIXED_GROUP_NOT_CONNECTED) for every other group that contains a corner action.
// Every player in such a group has already passed the unchanged physical gates of executeKicks (horizontal reach
// <= 1.1 m, the height window of its own action, cooldown, release window) and the unchanged legality rulings.
// P25 connects the remaining groups with the two rules the engine already has, and adds no new coefficient:
//  rule 'same_team_aerial'  all actions aerial, one team: the ball is met by ONE head/fist. Same stateless draw and
//                           weights as cornerDuel (same hash key), so it is order independent and consumes no RNG.
//                           The others jumped for the same ball and miss it (cooldown as in the existing duel).
//  rule 'mixed_simultaneous' an aerial action and an ordinary foot action (pass/shoot/dribble) meet a low ball in the
//                           same tick (only possible for ball height 0.30-0.45 m): the standard engine rule for
//                           simultaneous reachable attempts applies unchanged - all contribute equal impulses, no
//                           single last toucher (ball.lastTouch = null). Returns null here; ball.mjs then averages.
import {cornerDuel,duelUniform} from './ck_duel.mjs';
export const P25_ENABLED=true;
const AERIAL=['corner_header','corner_clear','gk_punch'];
export function resolveCornerGroup(s,attempts){
 const existing=cornerDuel(s,attempts);if(existing)return {...existing,rule:'opposing_aerial_duel_existing'};
 if(attempts.length<2||!attempts.every(a=>AERIAL.includes(a.kind)))return null;
 const order=attempts.slice().sort((a,b)=>a.p.id<b.p.id?-1:a.p.id>b.p.id?1:0),weights=order.map(a=>a.kind==='gk_punch'?a.p.abilities.goalkeeping:(a.p.abilities.acceleration+a.p.abilities.control)/2);
 const total=weights.reduce((x,y)=>x+y,0),draw=duelUniform(s.seed,s.tick,order.map(a=>a.p.id))*total;let acc=0,winner=order.at(-1);
 for(let i=0;i<order.length;i++){acc+=weights[i];if(draw<acc){winner=order[i];break;}}return {order,weights,draw,winner,rule:'same_team_aerial'};}
