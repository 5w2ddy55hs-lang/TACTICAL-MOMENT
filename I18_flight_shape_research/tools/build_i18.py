# Build the isolated I18 research branch next to (not inside) the I17 source tree.
# usage: python3 -I build_i18.py <I17 extracted dir> <out dir>
# Original files are only read. Unchanged modules are referenced by absolute file URI.
import sys,re,hashlib
from pathlib import Path
i17=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
src=i17/'source/integration_i8_standard/core'
here=Path(__file__).resolve().parent
def refs(s,base):
  return re.sub(r"(from\s*['\"])(\.[^'\"]+)(['\"])",lambda m:m[1]+(base/m[2]).resolve().as_uri()+m[3],s)
cand=(here/'src/i18_flight_shape.mjs').read_text().replace("'I17SRC/",f"'{src.as_uri()}/")
(out/'i18_flight_shape.mjs').write_text(cand)
eng=(src/'engine.mjs').read_text()
orig_import="import {choose} from './decision.mjs';"
assert eng.count(orig_import)==1
eng=eng.replace(orig_import,"import {chooseI18 as choose} from './i18_flight_shape.mjs';")
eng=refs(eng,src)
eng=eng.replace((src/'i18_flight_shape.mjs').resolve().as_uri(),'./i18_flight_shape.mjs').replace((src/'pass_build_identity.mjs').resolve().as_uri(),'./pass_build_identity.mjs')
(out/'engine.mjs').write_text(eng)
ident=(src/'pass_build_identity.mjs').read_text()
ident=ident.replace('TM_INTEGRATION_I8_STANDARD_SAVE/1','TM_RESEARCH_I18_FLIGHT_SHAPE_SAVE/1').replace('TM_INTEGRATION_I8_STANDARD_PASS_R1_CLAUDE_COUNTDOWN','TM_RESEARCH_I18_FLIGHT_SHAPE_ON_I8_STANDARD').replace('TM_INTEGRATION_I8_STANDARD_RESULT/1','TM_RESEARCH_I18_FLIGHT_SHAPE_RESULT/1')
ident=re.sub(r"(?<=['\"])[a-f0-9]{64}(?=['\"])",hashlib.sha256((cand+eng).encode()).hexdigest(),ident)
(out/'pass_build_identity.mjs').write_text(ident)
# diff record vs original
import difflib
d=''.join(difflib.unified_diff((src/'engine.mjs').read_text().splitlines(True)[:60],(out/'engine.mjs').read_text().splitlines(True)[:60],'integration_i8_standard/core/engine.mjs','i18_flight_shape/engine.mjs (first 60 lines; other import paths only made absolute)'))
(out/'ENGINE_IMPORT_DIFF.txt').write_text(d)
print('built',out,'files',sorted(p.name for p in out.iterdir()))
