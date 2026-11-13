# Build the isolated K20 research branch (witnessed-touch possession evidence) next to the I17 tree.
# usage: python3 -I build_k20.py <I17 extracted dir> <out dir>
# Only line 42 (ourPossession) of decision.mjs changes; all other modules are the originals (absolute refs).
import sys,re,hashlib,difflib
from pathlib import Path
i17=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
src=i17/'source/integration_i8_standard/core'
def refs(s,base): return re.sub(r"(from\s*['\"])(\.[^'\"]+)(['\"])",lambda m:m[1]+(base/m[2]).resolve().as_uri()+m[3],s)
dec=(src/'decision.mjs').read_text()
old="  const ourPossession=visibleHolder?visibleHolder.team===p.team:nearFriends.length>0&&!nearEnemies.length;"
assert dec.count(old)==1
new=("  // K20 research (NOT adopted): proximity alone is not possession. Require that the latest touch THIS player\n"
     "  // witnessed (own native observed-touch memory: who/team/part, no intent) was by its own team.\n"
     "  // Outfield only: the goalkeeper keeps the original rule (GK work is owned by another track).\n"
     "  const witnessedOwnTouch=p.role==='GK'||!!p.observedTouch&&p.observedTouch.players.length>0&&p.observedTouch.players.every(q=>q.team===p.team);\n"
     "  const ourPossession=visibleHolder?visibleHolder.team===p.team:nearFriends.length>0&&!nearEnemies.length&&witnessedOwnTouch;")
dec2=refs(dec.replace(old,new),src)
(out/'decision.mjs').write_text(dec2)
eng=(src/'engine.mjs').read_text();assert eng.count("import {choose} from './decision.mjs';")==1
eng=refs(eng,src).replace((src/'decision.mjs').resolve().as_uri(),'./decision.mjs').replace((src/'pass_build_identity.mjs').resolve().as_uri(),'./pass_build_identity.mjs')
(out/'engine.mjs').write_text(eng)
ident=(src/'pass_build_identity.mjs').read_text()
ident=ident.replace('TM_INTEGRATION_I8_STANDARD_SAVE/1','TM_RESEARCH_K20_POSSESSION_EVIDENCE_SAVE/1').replace('TM_INTEGRATION_I8_STANDARD_PASS_R1_CLAUDE_COUNTDOWN','TM_RESEARCH_K20_POSSESSION_EVIDENCE_ON_I8_STANDARD').replace('TM_INTEGRATION_I8_STANDARD_RESULT/1','TM_RESEARCH_K20_POSSESSION_EVIDENCE_RESULT/1')
ident=re.sub(r"(?<=['\"])[a-f0-9]{64}(?=['\"])",hashlib.sha256((dec2+eng).encode()).hexdigest(),ident)
(out/'pass_build_identity.mjs').write_text(ident)
# logical diff (relative imports kept) for review
d=''.join(difflib.unified_diff(dec.splitlines(True),dec.replace(old,new).splitlines(True),'a/core/decision.mjs','b/core/decision.mjs'))
(out/'DECISION_DIFF.patch').write_text(d)
print('built',out,sorted(p.name for p in out.iterdir()))
