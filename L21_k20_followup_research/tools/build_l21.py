# Build isolated L21 branch = K20 + chase-yield only to an evidently collecting, closer, currently seen teammate
# while K20 possession is "unknown". usage: python3 -I build_l21.py <I17> <out>
import sys,re,hashlib,difflib
from pathlib import Path
i17=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
src=i17/'source/integration_i8_standard/core'
def refs(s,base): return re.sub(r"(from\s*['\"])(\.[^'\"]+)(['\"])",lambda m:m[1]+(base/m[2]).resolve().as_uri()+m[3],s)
dec=(src/'decision.mjs').read_text()
old1="  const ourPossession=visibleHolder?visibleHolder.team===p.team:nearFriends.length>0&&!nearEnemies.length;"
new1=("  // K20 research (NOT adopted): proximity alone is not possession. Require that the latest touch THIS player\n"
      "  // witnessed (own native observed-touch memory: who/team/part, no intent) was by its own team.\n"
      "  // Outfield only: the goalkeeper keeps the original rule (GK work is owned by another track).\n"
      "  const witnessedOwnTouch=p.role==='GK'||!!p.observedTouch&&p.observedTouch.players.length>0&&p.observedTouch.players.every(q=>q.team===p.team);\n"
      "  const ourPossession=visibleHolder?visibleHolder.team===p.team:nearFriends.length>0&&!nearEnemies.length&&witnessedOwnTouch;\n"
      "  // L21 research (NOT adopted): while possession is unknown (proximity said ours, no witnessed own touch), still yield the\n"
      "  // chase to a CURRENTLY SEEN teammate that is closer to the ball and evidently collecting it (within foot reach 1.1 m or\n"
      "  // closing on the ball at >=0.5 m/s relative to the observed ball motion). Observed positions/velocities only; no intent.\n"
      "  const unknownPossession=!visibleHolder&&nearFriends.length>0&&!nearEnemies.length&&!witnessedOwnTouch;\n"
      "  const evidentCollector=unknownPossession&&nearFriends.some(q=>q.seenTick===o.tick&&dist(q,bp)<db&&(dist(q,bp)<=1.1||(()=>{const d=dist(q,bp)||1e-6,ux=(bp.x-q.x)/d,uy=(bp.y-q.y)/d,bvx=ball.velocityKnown?ball.vx:0,bvy=ball.velocityKnown?ball.vy:0;return (q.vx-bvx)*ux+(q.vy-bvy)*uy>=0.5;})()));")
assert dec.count(old1)==1
old2="   let score=1.65-db*0.048+c.press*0.35-(ourPossession&&!(propose&&admissibleReceptionEvidence(o,nearFriends,visibleHolder,motion,reception))?1.5:0)-age*0.4;"
new2="   let score=1.65-db*0.048+c.press*0.35-((ourPossession||evidentCollector)&&!(propose&&admissibleReceptionEvidence(o,nearFriends,visibleHolder,motion,reception))?1.5:0)-age*0.4;"
assert dec.count(old2)==1
mod=dec.replace(old1,new1).replace(old2,new2)
(out/'decision.mjs').write_text(refs(mod,src))
eng=(src/'engine.mjs').read_text()
eng=refs(eng,src).replace((src/'decision.mjs').resolve().as_uri(),'./decision.mjs').replace((src/'pass_build_identity.mjs').resolve().as_uri(),'./pass_build_identity.mjs')
(out/'engine.mjs').write_text(eng)
ident=(src/'pass_build_identity.mjs').read_text()
ident=ident.replace('TM_INTEGRATION_I8_STANDARD_SAVE/1','TM_RESEARCH_L21_EVIDENT_COLLECTOR_SAVE/1').replace('TM_INTEGRATION_I8_STANDARD_PASS_R1_CLAUDE_COUNTDOWN','TM_RESEARCH_L21_EVIDENT_COLLECTOR_ON_I8_STANDARD').replace('TM_INTEGRATION_I8_STANDARD_RESULT/1','TM_RESEARCH_L21_EVIDENT_COLLECTOR_RESULT/1')
ident=re.sub(r"(?<=['\"])[a-f0-9]{64}(?=['\"])",hashlib.sha256((mod+eng).encode()).hexdigest(),ident)
(out/'pass_build_identity.mjs').write_text(ident)
(out/'DECISION_DIFF_vs_I17.patch').write_text(''.join(difflib.unified_diff(dec.splitlines(True),mod.splitlines(True),'a/core/decision.mjs','b/core/decision.mjs')))
print('built',out)
