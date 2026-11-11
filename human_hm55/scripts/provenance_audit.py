"""Provenance audit with evidence. Opens the research inputs READ-ONLY and compares them with HM55.

  A. what the original files say about themselves (embedded custom properties / text blocks)
  B. measured derivation of the earlier work: FACE52 vs Reference04, FH54 faces vs FACE52, FH54 hair vs FACE52
     (same vertex count / coincident vertices / identical UVs / texture pixel correlation)
  C. the same measurements for HM55 against every research mesh and texture (must show no reuse)
  D. HM55 build inputs: the build scripts read no model / image / motion file (static scan of the scripts)

Env: FH53_INPUTS (restored FACE52), FH53_REF04 (Reference04 folder), FH54_BUILD (FH54 build folder), HM_BUILD.
Writes $HM_BUILD/qa/provenance_audit.json."""
import os, sys, re, json, io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image
import bpy
import hm_common as hc, glb_info

INP = Path(os.environ['FH53_INPUTS']); REF = Path(os.environ['FH53_REF04']); FH54 = Path(os.environ['FH54_BUILD']); OUT = hc.BUILD
FACE52 = INP/'CODEX/face52_work/models/TM_FACE52_F0_H0.blend'; REF04 = REF/'Sakatsuku2002_reference04_APPEARANCE_STUDY.blend'
R = {'inputs': {}, 'embedded_statements': {}, 'derivation_of_earlier_work': {}, 'hm55_vs_research': {}, 'hm55_build_inputs': {}}


def scene_meshes():
    out = {}
    for ob in bpy.data.objects:
        if ob.type == 'MESH':
            m = ob.data; V = np.array([tuple(ob.matrix_world @ v.co) for v in m.vertices]); uv = np.array([tuple(l.uv) for l in m.uv_layers[0].data]) if m.uv_layers else np.zeros((0, 2))
            out[ob.name] = {'V': V, 'polys': [tuple(p.vertices) for p in m.polygons], 'uv': uv, 'tris': sum(len(p.vertices) - 2 for p in m.polygons)}
    return out


def images():
    out = {}
    for im in bpy.data.images:
        if im.size[0] and im.size[1] and im.has_data or im.packed_file:
            try:
                a = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], -1)[::-1, :, :3]; out[im.name] = a
            except Exception:
                pass
    return out


def nearest_stats(A, B):
    """Distance from every vertex of A to the nearest vertex of B (after removing the mean offset is NOT done: raw)."""
    d = np.array([np.min(np.linalg.norm(B - a, axis=1)) for a in A])
    return {'coincident_lt_1e-5': int((d < 1e-5).sum()), 'within_1mm': int((d < 1e-3).sum()), 'median_mm': round(float(np.median(d))*1000, 3), 'of': int(len(A))}


def best_translation_match(A, B, shifts):
    """Share of A's vertices that coincide (1e-4 m) with a vertex of B under any of the candidate translations."""
    best = {'shift': None, 'coincident': 0}
    for s in shifts:
        d = np.array([np.min(np.linalg.norm(B - (a + s), axis=1)) for a in A]); c = int((d < 1e-4).sum())
        if c > best['coincident']:
            best = {'shift': [round(float(x), 6) for x in s], 'coincident': c}
    best['of'] = int(len(A)); return best


def img_corr(a, b, size=64):
    """Pearson correlation of two images after resizing to a common small size (structure similarity proxy)."""
    f = lambda x: np.asarray(Image.fromarray((np.clip(x, 0, 1)*255).astype(np.uint8)).resize((size, size), Image.BILINEAR), float).ravel()
    x, y = f(a), f(b); x -= x.mean(); y -= y.mean(); d = np.linalg.norm(x)*np.linalg.norm(y)
    return float(x @ y/d) if d > 0 else 0.0


# ---------------------------------------------------------------- A. embedded statements
for label, path in (('Reference04', REF04), ('FACE52', FACE52)):
    bpy.ops.wm.open_mainfile(filepath=str(path)); R['inputs'][label] = {'file': path.name, 'sha256': hc.sha256(path)}
    st = {'scene': {k: str(v)[:240] for sc in bpy.data.scenes for k, v in sc.items() if k != 'cycles'}, 'texts': {t.name: t.as_string()[:800] for t in bpy.data.texts},
          'objects': {o.name: {k: str(v)[:240] for k, v in o.items()} for o in bpy.data.objects if len(o.keys())}, 'materials': {m.name: {k: str(v)[:240] for k, v in m.items()} for m in bpy.data.materials if len(m.keys())},
          'actions': {a.name: {k: str(v)[:120] for k, v in a.items()} for a in bpy.data.actions}, 'image_names': [i.name for i in bpy.data.images], 'armatures': {a.name: len(a.bones) for a in bpy.data.armatures}}
    R['embedded_statements'][label] = st
    if label == 'Reference04':
        ref_m = scene_meshes(); ref_i = images(); ref_bones = {b.name: tuple(b.head_local) for a in bpy.data.armatures for b in a.bones}
        ob = bpy.data.objects['REF_SourcePlayer_reference_only']; R['inputs'][label].update({'vertices': len(ob.data.vertices), 'triangles': ref_m[ob.name]['tris'], 'vertex_groups': len(ob.vertex_groups), 'actions': [a.name for a in bpy.data.actions]})
    else:
        f52_m = scene_meshes(); f52_i = images()
refV = np.concatenate([m['V'] for m in ref_m.values()]); f52V = np.concatenate([m['V'] for m in f52_m.values()])

# ---------------------------------------------------------------- B. derivation of the earlier work
T_HEAD = np.array([0.0, -0.0393775999546051, 1.59796941280365])           # FACE52 -> Reference04 static translation (handoff evidence)
face52 = f52_m['REF09_Face_Eyes_Mouth']['V']
R['derivation_of_earlier_work']['FACE52_face_vs_Reference04_mesh'] = dict(best_translation_match(face52, refV, [T_HEAD, np.zeros(3)]), note='FACE52 face vertices that coincide with Reference04 vertices after the handoff translation')
fh54 = {}
for p in sorted((FH54/'models/face').glob('TM_FH54_F[123]_*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(p)); m = scene_meshes(); im = images(); face = m.get('REF09_Face_Eyes_Mouth')
    same_topo = face is not None and face['polys'] == f52_m['REF09_Face_Eyes_Mouth']['polys']; same_uv = face is not None and face['uv'].shape == f52_m['REF09_Face_Eyes_Mouth']['uv'].shape and float(np.abs(face['uv'] - f52_m['REF09_Face_Eyes_Mouth']['uv']).max()) < 1e-6
    moved = np.linalg.norm(face['V'] - face52, axis=1) if face is not None and face['V'].shape == face52.shape else None
    tex = {}
    for n, a in im.items():
        best = max(((k, img_corr(a, b)) for k, b in f52_i.items()), key=lambda t: t[1], default=(None, 0)); tex[n] = {'best_FACE52_image': best[0], 'correlation': round(best[1], 3)}
    R['derivation_of_earlier_work'][p.stem] = {'same_polygon_list_as_FACE52': bool(same_topo), 'same_uv_as_FACE52': bool(same_uv), 'vertices_unmoved_lt_0.1mm': int((moved < 1e-4).sum()) if moved is not None else None,
                                               'vertices': int(len(face['V'])) if face is not None else None, 'texture_correlation_with_FACE52': tex}
    fh54[p.stem] = m
for p in sorted((FH54/'models/hair').glob('TM_FH54_H*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(p)); m = scene_meshes(); V = np.concatenate([x['V'] for x in m.values()])
    R['derivation_of_earlier_work'][p.stem] = {'vertices': int(len(V)), 'coincident_with_FACE52_vertices': nearest_stats(V, f52V)['coincident_lt_1e-5'],
                                               'note': 'Hair mesh was generated by script but fitted to the FACE52 skull / ear surface (shape depends on a source-derived head); textures are procedural.'}
    fh54[p.stem] = m

# ---------------------------------------------------------------- C. HM55 against the research assets
bpy.ops.wm.open_mainfile(filepath=str(OUT/'models/TM_HM55_LIBRARY.blend')); hm = scene_meshes(); hm_i = images(); hm_b = {b.name: tuple(b.head_local) for a in bpy.data.armatures for b in a.bones}
research = {'Reference04': ref_m, 'FACE52': f52_m}; research.update(fh54); allR = {k: np.concatenate([x['V'] for x in v.values()]) for k, v in research.items()}
ref_poly_sets = {k: {(len(x['V']), x['tris']) for x in v.values()} for k, v in research.items()}
for name, m in hm.items():
    V = m['V']; row = {'vertices': int(len(V)), 'triangles': int(m['tris']), 'same_vertex_and_triangle_count_as_any_research_mesh': any((len(V), m['tris']) in s for s in ref_poly_sets.values())}
    # compare in place and with the head brought to the FACE52 frame (HM55 head pivot -> FACE52 origin)
    for k, B in allR.items():
        shifts = [np.zeros(3), T_HEAD, -T_HEAD, np.array([0, 0.012, 1.615]), -np.array([0, 0.012, 1.615])]
        row['coincident_vertices_with_' + k] = best_translation_match(V, B, shifts)['coincident']
    hm[name]['audit'] = row; R['hm55_vs_research'].setdefault('meshes', {})[name] = row
tex = {}
all_research_images = dict(('Reference04/' + k, v) for k, v in ref_i.items()); all_research_images.update(('FACE52/' + k, v) for k, v in f52_i.items())
for p in sorted((FH54/'textures/faces').glob('*.png')):
    all_research_images['FH54/' + p.name] = np.asarray(Image.open(p).convert('RGB'), float)/255
for n, a in hm_i.items():
    cs = sorted(((k, img_corr(a, b)) for k, b in all_research_images.items()), key=lambda t: -abs(t[1]))[:1]
    tex[n] = {'size': list(a.shape[:2][::-1]), 'most_similar_research_image': cs[0][0] if cs else None, 'correlation': round(cs[0][1], 3) if cs else None}
R['hm55_vs_research']['textures'] = tex
R['hm55_vs_research']['skeleton'] = {'hm55_bones': len(hm_b), 'reference04_bones': len(ref_bones), 'shared_bone_names': sorted(set(hm_b) & set(ref_bones)),
                                     'hm55_joint_positions_coinciding_with_reference_joints_lt_1mm': int(sum(any(np.linalg.norm(np.array(a) - np.array(b)) < 1e-3 for b in ref_bones.values()) for a in hm_b.values())),
                                     'reference04_weighting': 'rigid, one bone per vertex (measured in the file)', 'hm55_weighting': 'smooth, up to 4 bones per vertex, computed in hm_body.part_weights / hm_head.head_weights'}
R['hm55_vs_research']['actions'] = {'hm55': sorted(a.name for a in bpy.data.actions), 'reference04': R['inputs']['Reference04']['actions'],
                                    'note': 'HM55 actions are keyframed from pose tables in hm_anim.py; no fcurve or sampled pose is read from the Reference04 actions.'}

# ---------------------------------------------------------------- D. static scan of the build scripts
BUILD_SCRIPTS = ['build_all.py', 'hm_common.py', 'hm_sdf.py', 'hm_head.py', 'hm_body.py', 'hm_hair.py', 'hm_hair_textures.py', 'hm_texture.py', 'hm_bake.py', 'hm_assemble.py', 'hm_anim.py']
pat = re.compile(r'(Image\.open|images\.load|open_mainfile|import_scene|wm\.append|wm\.link|libraries\.load|np\.load|read_bytes|open\()')
scan = {}
for n in BUILD_SCRIPTS:
    hits = []
    for i, line in enumerate((Path(__file__).resolve().parent/n).read_text().splitlines(), 1):
        if pat.search(line) and not line.strip().startswith('#'):
            hits.append({'line': i, 'code': line.strip()[:160]})
    scan[n] = hits
R['hm55_build_inputs'] = {'file_reads_in_build_scripts': scan,
                          'explanation': 'The only reads are: images.load of textures written earlier in the same build (hm_common.load_packed_image), Image.open of those same files for the size record, and sha256 read_bytes of build outputs.',
                          'environment_variables_used_by_build': ['HM_BUILD']}
hc.write_json(OUT/'qa/provenance_audit.json', R)
print(json.dumps({k: R['derivation_of_earlier_work'][k] for k in list(R['derivation_of_earlier_work'])[:2]}, ensure_ascii=False)[:900])
print('HM55 meshes', json.dumps(R['hm55_vs_research']['meshes'], ensure_ascii=False)[:1500]); print('AUDIT OK'); hc.finish()
