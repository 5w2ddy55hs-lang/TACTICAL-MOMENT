# Build an isolated full copy of the I17 CK research branch (source/integration_i8_ck_research) outside the I17 tree.
# usage: python3 -I build_p25.py <I17 extracted dir> <out dir> <mode>
#   mode diag : behaviour identical to the original; only adds an observer-only sink row before the original throw
#   mode p25  : the P25 candidate (see ball.mjs patch below); feature switch config-free: module constant P25_ENABLED
#   mode off  : P25 code present but P25_ENABLED=false (must behave exactly like the original incl. the throw)
# The copy is self-contained (the branch has no imports outside its own directory). Only core/ball.mjs,
# core/ck_mixed_resolution.mjs (new, p25/off) and core/pass_build_identity.mjs differ from the original.
import sys,re,hashlib,shutil,difflib
from pathlib import Path
i17=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();mode=sys.argv[3]
src=i17/'source/integration_i8_ck_research'
if out.exists():shutil.rmtree(out)
shutil.copytree(src,out)
# The branch imports 8 sibling modules (../../parent_*, ../../soc2*). In the copy those imports point at the read-only
# originals by absolute file:// URI (import path only; no other byte changes). Listed as 'import-path only' below.
relinked=[]
for p in sorted(out.rglob('*.mjs')):
  t=p.read_text();rel=p.relative_to(out)
  t2=re.sub(r"((?:from|import)\s*['\"])(\.\./\.\./[^'\"]+)(['\"])",lambda m:m[1]+((src/rel).parent/m[2]).resolve().as_uri()+m[3],t)
  if t2!=t:p.write_text(t2);relinked.append(str(rel))
ball=(src/'core/ball.mjs').read_text()
THROW="if(candidates.length>1&&candidates.some(p=>CORNER_KICKS.includes(views.get(p.id).kind))&&!aerialChallenge)throw Error('I5_CK_MIXED_GROUP_NOT_CONNECTED');"
assert ball.count(THROW)==1
DIAG=("if(candidates.length>1&&candidates.some(p=>CORNER_KICKS.includes(views.get(p.id).kind))&&!aerialChallenge){"
 "sink?.({channel:'p25_mixed_group_diag',observerOnly:true,tick:s.tick,phase:s.phase,restartRestriction:s.restartRestriction?{...s.restartRestriction}:null,"
 "ball:{x:b.x,y:b.y,z:b.z,vx:b.vx,vy:b.vy,vz:b.vz,lastTouch:b.lastTouch,lastTeam:b.lastTeam,lastKick:b.lastKick?{...b.lastKick}:null},"
 "candidates:candidates.map(p=>{const a=views.get(p.id);return {id:p.id,team:p.team,role:p.role,goalkeeper:isGoalkeeper(s,p),x:p.x,y:p.y,vx:p.vx,vy:p.vy,dist:dist(p,b),cooldown:p.cooldown,headReach:cornerHeadReach(p),"
 "view:{kind:a.kind,reason:a.reason??null,target:a.target?{x:a.target.x,y:a.target.y}:null,aim:a.aim?{x:a.aim.x,y:a.aim.y}:null,targetId:a.targetId??null,observedTick:a.observedTick??null,applyTick:a.applyTick??null},"
 "action:{kind:p.action.kind,reason:p.action.reason??null,observedTick:p.action.observedTick??null,applyTick:p.action.applyTick??null},viewIsAction:a===p.action};})});"
 "throw Error('I5_CK_MIXED_GROUP_NOT_CONNECTED');}")
if mode=='diag':
  new=ball.replace(THROW,DIAG);names=('DIAG',)
else:
  patch=(Path(__file__).parent/'p25_ball_patch.py').read_text();ns={}
  exec(patch,ns);new=ns['apply'](ball,THROW,mode=='p25');names=('P25' if mode=='p25' else 'P25OFF',)
  (out/'core/ck_mixed_resolution.mjs').write_text(ns['MODULE'])
(out/'core/ball.mjs').write_text(new)
ident=(src/'core/pass_build_identity.mjs').read_text()
tag={'diag':'P25_CK_DIAG','p25':'P25_CK_MIXED_RESOLUTION','off':'P25_CK_MIXED_RESOLUTION_OFF'}[mode]
ident=ident.replace('TM_INTEGRATION_I8_CK_RESEARCH_SAVE/1',f'TM_RESEARCH_{tag}_SAVE/1').replace('TM_INTEGRATION_I8_CK_RESEARCH_PASS_R1_CLAUDE_COUNTDOWN',f'TM_RESEARCH_{tag}_ON_I8_CK_RESEARCH').replace('TM_INTEGRATION_I8_CK_RESEARCH_RESULT/1',f'TM_RESEARCH_{tag}_RESULT/1')
extra=(out/'core/ck_mixed_resolution.mjs').read_text() if (out/'core/ck_mixed_resolution.mjs').exists() else ''
ident=re.sub(r"(?<=['\"])[a-f0-9]{64}(?=['\"])",hashlib.sha256((new+extra).encode()).hexdigest(),ident,count=1)
(out/'core/pass_build_identity.mjs').write_text(ident)
d=''.join(difflib.unified_diff(ball.splitlines(True),new.splitlines(True),'a/integration_i8_ck_research/core/ball.mjs','b/core/ball.mjs'))
(out/'BALL_DIFF.patch').write_text(d)
# every other file must be byte-identical to the original branch
changed=[str(p.relative_to(out)) for p in out.rglob('*') if p.is_file() and p.name!='BALL_DIFF.patch' and (not (src/p.relative_to(out)).exists() or (src/p.relative_to(out)).read_bytes()!=p.read_bytes())]
print('built',mode,out,'changed/new files:',sorted(c for c in changed if c not in relinked),'| import-path only:',relinked)
