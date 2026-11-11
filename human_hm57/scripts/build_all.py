"""HM57 build: textures, face / hair / body modules, assembled skinned players with original motions, and the
mobile LITE player (same skeleton / motions, region-weighted decimation, 512 / 256 px JPEG + PNG textures).
Reads no model, texture or motion file. Writes $HM_BUILD/{textures,models,qa}.
Usage: python build_all.py [--faces P0,P1,P2,P3] [--hairs H1,H2,H3,H4] [--quick] [--lite-only]
  --lite-only: run AFTER the normal build (reuses its textures); builds only the LITE players, writes qa/build_lite57.json and exits."""
import sys, time, argparse, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
import hm_common as hc, hm_body as hb, hm_head as hh, hm_hair as hx, hm_texture as tx, hm_bake as bk, hm_assemble as ha, hm_anim as an, hm_hair_textures as ht, hm_lod as lod

ap = argparse.ArgumentParser(); ap.add_argument('--faces', default='P0,P1,P2,P3'); ap.add_argument('--hairs', default='H1,H2,H3,H4'); ap.add_argument('--quick', action='store_true'); ap.add_argument('--lite-only', dest='lite_only', action='store_true')
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
FACES = A.faces.split(','); HAIRS = A.hairs.split(','); OUT = hc.BUILD; TEX = OUT/'textures'; MOD = OUT/'models'
for d in (TEX, MOD/'players', MOD/'modules', OUT/'qa'):
    d.mkdir(parents=True, exist_ok=True)
REC = {'status': hc.STATUS, 'blender': bpy.app.version_string, 'faces': {}, 'hairs': {}, 'textures': {}, 'models': {}, 'timing_s': {}}
t_all = time.time()

# ---------------------------------------------------------------- 1. geometry data
t0 = time.time(); body = hb.body_data(); heads = {f: ha.head_data(hh.FACES[f]['P']) for f in FACES}
REC['body'] = {'vertices_before_weld': int(len(body['verts'])), 'triangles': int(sum(len(f) - 2 for f in body['faces'])), 'parts': body['info'], 'bones': [b[0] for b in hb.bones()]}
for f in FACES:
    REC['faces'][f] = {'name': hh.FACES[f]['name'], 'intent_ja': hh.FACES[f]['intent_ja'], 'vertices': int(len(heads[f]['verts'])), 'triangles': int(sum(len(x) - 2 for x in heads[f]['faces'])),
                       'tone': tx.FACE_TEX[f]['tone'], 'shape_overrides': {k: v for k, v in hh.FACES[f]['P'].items() if hh.P0.get(k) != v}}
REC['timing_s']['geometry'] = round(time.time() - t0, 1)

# ---------------------------------------------------------------- 2. textures (paint -> AO bake of own geometry -> composite)
kits = ['A', 'B']
if not A.lite_only:
    t0 = time.time(); ht.make_cap(TEX/'TMH55_CAP_STRANDS_512.png'); ht.make_cards(TEX/'TMH55_CARD_STRANDS_512.png'); ht.make_edge(TEX/'TMH55_EDGE_STRANDS_512x256.png')
    tones = sorted({tx.FACE_TEX[f]['tone'] for f in FACES}); kits = ['A', 'B']
    hc.reset_scene(); bob, _ = ha.build_body(data=body); ao_b = bk.bake_ao(bob, {0: 1024, 1: 512})
    for k in kits:
        rgb, m = tx.paint_kit(body, k); tx.save_rgb(TEX/f'TM_HM57_Kit_{k}.png', tx.bleed(bk.apply_ao(rgb, ao_b[0], 0.70, (1, 1, 1), mask=m, blur=1.5), m))
    SKIN_STATS = {}
    for tn in tones:
        rgb, m = tx.paint_body_skin(body, tn); fin = bk.apply_ao(rgb, ao_b[1], 0.40, mask=m, blur=2.0); tx.save_rgb(TEX/f'TM_HM57_BodySkin_{tn}.png', tx.bleed(fin, m))   # HM57: AO 0.50 -> 0.40 with the lighter face AO (neck / arm colour match)
        SKIN_STATS['body_' + tn] = {'painted_mean_rgb': [round(float(x), 4) for x in rgb[m].mean(0)], 'final_mean_rgb': [round(float(x), 4) for x in fin[m].mean(0)]}
    for f in FACES:
        hd = heads[f]; rgb, m, r = tx.paint_head(hd, tx.FACE_TEX[f]); hc.reset_scene(); hob, _ = ha.build_head(data=hd); ao = bk.bake_ao(hob, {0: 1024})
        fin = bk.apply_ao(rgb, ao[0], 0.36, mask=m, blur=2.5, limit=np.where(r['fid'] > 0, 0.28, 1.0)); tx.save_rgb(TEX/f'TM_HM57_Head_{f}.png', tx.bleed(fin, m))
        z = r['pos'][..., 2]; neck = m & (r['fid'] == 0) & (z < -0.085) & (z > -0.135); P_ = hd['P']; sz = P_['scale'][2]
        cheek = m & (r['fid'] == 0) & (np.abs(z - 0.005*sz) < 0.012) & (np.abs(np.abs(r['pos'][..., 0]) - 0.048) < 0.010) & (r['pos'][..., 1] < -0.04)
        SKIN_STATS['head_' + f] = {'tone': tx.FACE_TEX[f]['tone'], 'neck_painted_mean_rgb': [round(float(x), 4) for x in rgb[neck].mean(0)], 'neck_final_mean_rgb': [round(float(x), 4) for x in fin[neck].mean(0)],
                                   'cheek_painted_mean_rgb': [round(float(x), 4) for x in rgb[cheek].mean(0)], 'neck_texels': int(neck.sum())}
        # colour step across the UV seam at the back of the neck (u = 0 | 1 columns of the main chart)
        rows = np.where(m[:, 2] & m[:, -3] & (r['fid'][:, 2] == 0))[0]; zz = r['pos'][rows, 2, 2]; rows = rows[(zz < -0.02) & (zz > -0.13)]
        SKIN_STATS['head_' + f]['back_seam_step_rgb_mean'] = round(float(np.abs(fin[rows, 2] - fin[rows, -3]).mean()), 4) if len(rows) else None
    for p in sorted(TEX.glob('*.png')):
        from PIL import Image
        im = Image.open(p); REC['textures'][p.name] = {'size': list(im.size), 'mode': im.mode, 'bytes': p.stat().st_size, 'sha256': hc.sha256(p)}
    REC['skin_colour'] = SKIN_STATS; REC['timing_s']['textures'] = round(time.time() - t0, 1); print('textures done', REC['timing_s'], flush=True)
# ---- LITE textures (mobile): opaque maps as 512 / 256 px JPEG (quality 88), hair maps as 256 px PNG (alpha)
LITE_SIZE = {'Kit': 512, 'Head': 512, 'BodySkin': 256, 'TMH55': 256}
if A.lite_only:
    from PIL import Image
    for p in sorted(TEX.glob('*.png')):
        if p.stem.endswith('_LITE'):
            continue
        key = next(k for k in LITE_SIZE if k in p.stem); im = Image.open(p); n = LITE_SIZE[key]; w, h = im.size; im = im.resize((n, max(1, round(n*h/w))), Image.LANCZOS)
        if p.stem.startswith('TMH55'):
            im.save(TEX/f'{p.stem}_LITE.png', optimize=True)
        else:
            im.convert('RGB').save(TEX/f'{p.stem}_LITE.jpg', quality=88, optimize=True)

# ---------------------------------------------------------------- 3. hair data per face (the cap follows each head shape)
t0 = time.time(); hair = {}
for f in FACES:
    for h in HAIRS:
        d = hx.build_hair_data(heads[f], h); hair[(f, h)] = d; REC['hairs'][f'{f}_{h}'] = dict(d['info'], vertices=int(len(d['verts'])), triangles=int(len(d['tris'])))
        print('hair', f, h, 'tris', len(d['tris']), 'cap overlap left', d['info']['cap_vs_head_overlap_pass']['remaining_overlapping_triangles'], flush=True)
REC['timing_s']['hair'] = round(time.time() - t0, 1)


# ---------------------------------------------------------------- 3b. boot points for the ground-contact pass (rest boot vertices with their dominant bone)
from mathutils import Vector
SOLE = [(max(w, key=w.get), Vector(v)) for k, (v, w) in enumerate(zip(body['verts'], body['weights'])) if any(n.startswith('boot') and r['first'] <= k < r['first'] + r['count'] for n, r in body['info'].items()) and max(w, key=w.get) in ('Foot_L', 'Foot_R', 'Toes_L', 'Toes_R', 'LowerLeg_L', 'LowerLeg_R')]   # every boot vertex (heel edge included)


# ---------------------------------------------------------------- 4. scenes
def mats(kit, tone, face, lite=False):
    sfx, ext = ('_LITE', '.jpg') if lite else ('', '.png')
    img = lambda stem: hc.load_packed_image(TEX/f'{stem}{sfx}{ext}', f'{stem}{sfx}')
    mk = hc.simple_material(f'TM_HM57_Kit_{kit}{sfx}', img(f'TM_HM57_Kit_{kit}'), double_sided=True, extras={'provenance': 'Procedural kit texture (hm_texture.paint_kit) + AO bake of HM57 geometry.'})
    ms = hc.simple_material(f'TM_HM57_BodySkin_{tone}{sfx}', img(f'TM_HM57_BodySkin_{tone}'), extras={'provenance': 'Procedural skin texture (hm_texture.paint_body_skin) + AO bake of HM57 geometry.'})
    mh = hc.simple_material(f'TM_HM57_Head_{face}{sfx}', img(f'TM_HM57_Head_{face}'), extras={'provenance': 'Procedural face texture (hm_texture.paint_head) + AO bake of HM57 geometry.'}) if face else None
    return mk, ms, mh


HEAD_TRIS = {'full': 2800, 'lite': 900}; BODY_TRIS = {'lite': 1800}; HAIR_TRIS = {}   # hair is not decimated: the LITE hair is generated at lower resolution (hm_hair lite)
IMP_SCALE = {'full': 1.0, 'lite': 0.8}  # full: importance 1 areas (face features) are never collapsed; lite: everything may simplify, by importance
LOD_LOG = {}
_HAIR_LITE = {}


def hair_lite(face, hstyle):
    if (face, hstyle) not in _HAIR_LITE:
        d = hx.build_hair_data(heads[face], hstyle, lite=True); _HAIR_LITE[(face, hstyle)] = d; LOD_LOG[f'hair_{hstyle}_lite'] = {'before': len(hair[(face, hstyle)]['tris']), 'after': len(d['tris']), 'method': 'regenerated with fewer cap rings / columns'}
    return _HAIR_LITE[(face, hstyle)]


def head_lod(hob, face, lod_):
    imp = lod.head_importance(heads[face]['P'], np.array([v.co for v in hob.data.vertices]) - hb.HEAD_PIVOT)*IMP_SCALE[lod_]; imp[lod.boundary_vertices(hob)] = 1.0
    r = lod.decimate(hob, HEAD_TRIS[lod_], imp); r.update(lod.keep_inside(hob, heads[face]['P'], hb.HEAD_PIVOT, depth=0.0010 if lod_ == 'full' else 0.0020))     # scalp stays under the hair
    LOD_LOG[f'head_{face}_{lod_}'] = r; return r


def body_lod(bob, lod_):
    if lod_ not in BODY_TRIS:
        return None
    vp = [None]*len(bob.data.vertices)
    for poly, part in zip(bob.data.polygons, body['face_part']):
        for vi in poly.vertices:
            vp[vi] = vp[vi] or part
    imp0 = lod.body_importance(np.array([v.co for v in bob.data.vertices]), vp); imp = imp0*IMP_SCALE[lod_]; imp[imp0 >= 1.0] = 1.0; imp[lod.boundary_vertices(bob)] = 1.0     # shirt / sleeves and hems are never collapsed
    r = lod.decimate(bob, BODY_TRIS[lod_], imp); LOD_LOG[f'body_{lod_}'] = r; return r


def hair_lod(xob, hstyle, lod_):
    if lod_ not in HAIR_TRIS:
        return None
    imp = np.full(len(xob.data.vertices), 0.15)
    for poly in xob.data.polygons:
        if poly.material_index > 0:                     # soft edge band and cards are locked (importance exactly 1): alpha silhouettes; collapsing them crashed bpy 4.2
            for vi in poly.vertices:
                imp[vi] = 1.0
    r = lod.decimate(xob, HAIR_TRIS[lod_], imp); LOD_LOG[f'hair_{hstyle}_{lod_}'] = r; return r


def tag(ob, role):
    ob['hm55_status'] = hc.STATUS; ob['hm55_role'] = role; ob['hm55_provenance'] = 'Mesh generated by human_hm55/scripts from authored parameters; no imported or traced mesh.'


def scene_player(face, hstyle, kit, with_actions=True, lod_='full'):
    hc.reset_scene(); tone = tx.FACE_TEX[face]['tone']; mk, ms, mh = mats(kit, tone, face, lite=lod_ == 'lite')
    bob, _ = ha.build_body(mk, ms, data=body); hob, _ = ha.build_head(mat=mh, data=heads[face]); body_lod(bob, lod_); head_lod(hob, face, lod_)
    arm = ha.build_rig(); ha.bind(bob, arm); ha.bind(hob, arm); tag(bob, 'body'); tag(hob, 'head ' + face)
    if hstyle:
        xob = ha.build_hair(hair[(face, hstyle)] if lod_ == 'full' else hair_lite(face, hstyle), ha.hair_materials(hstyle, TEX, lite=lod_ == 'lite')); hair_lod(xob, hstyle, lod_); ha.bind(xob, arm); tag(xob, 'hair ' + hstyle)
    acts = an.make_actions(arm, SOLE) if with_actions else {}
    sc = bpy.context.scene; sc['hm55_status'] = hc.STATUS; sc['hm55_player'] = f'{face}_{hstyle}_KIT{kit}'
    return arm, acts


players = [(f, h, 'A') for f in FACES for h in HAIRS] + ([] if A.quick else [(FACES[i % len(FACES)], HAIRS[i % len(HAIRS)], 'B') for i in range(min(4, len(FACES)))])
t0 = time.time()
for f, h, k in ([] if A.lite_only else players):
    name = f'{hc.PREFIX}_PLAYER_{f}_{h}_KIT{k}'; arm, acts = scene_player(f, h, k); glb = MOD/'players'/(name + '.glb'); hc.export_glb(glb, animations=True)
    REC['models'][glb.name] = {'kind': 'player', 'face': f, 'hair': h, 'kit': k, 'lod': 'full', 'bytes': glb.stat().st_size, 'sha256': hc.sha256(glb), 'actions': acts}
    if (f, h, k) in [(FACES[i % len(FACES)], HAIRS[(i + 1) % len(HAIRS)], 'A') for i in range(len(FACES))] or (f, h, k) == (FACES[0], HAIRS[0], 'A'):
        bl = MOD/'players'/(name + '.blend'); hc.save_blend(bl); REC['models'][bl.name] = {'kind': 'player_blend', 'bytes': bl.stat().st_size, 'sha256': hc.sha256(bl)}
    print('player', name, round(glb.stat().st_size/1e6, 2), 'MB', flush=True)
if A.lite_only:
    for f, h, k in players:                       # every assembled player also gets its LITE version (separate process: see --lite-only)
        name = f'{hc.PREFIX}_PLAYER_{f}_{h}_KIT{k}_LITE'; arm, acts = scene_player(f, h, k, lod_='lite'); glb = MOD/'players'/(name + '.glb'); hc.export_glb(glb, animations=True)
        REC['models'][glb.name] = {'kind': 'player', 'face': f, 'hair': h, 'kit': k, 'lod': 'lite', 'bytes': glb.stat().st_size, 'sha256': hc.sha256(glb), 'actions': acts}
        bl = MOD/'players'/(name + '.blend'); hc.save_blend(bl); REC['models'][bl.name] = {'kind': 'player_blend', 'bytes': bl.stat().st_size, 'sha256': hc.sha256(bl)}
        print('player', name, round(glb.stat().st_size/1e6, 2), 'MB', flush=True)
REC['ground_pass'] = dict(an.GROUND_LOG); REC['lod'] = {'budgets': {'head': HEAD_TRIS, 'body': BODY_TRIS, 'hair': HAIR_TRIS}, 'applied': LOD_LOG}
REC['timing_s']['players'] = round(time.time() - t0, 1)
if A.lite_only:                                  # bpy 4.2 can corrupt memory after the decimations: write the record and exit here
    hc.write_json(OUT/'qa/build_lite57.json', REC); print('LITE BUILD OK', REC['timing_s'], flush=True); hc.finish()

# ---------------------------------------------------------------- 5. modules + library
t0 = time.time()
for k in kits:
    hc.reset_scene(); mk, ms, _ = mats(k, 'T2', None); bob, _ = ha.build_body(mk, ms, data=body); arm = ha.build_rig(); ha.bind(bob, arm); tag(bob, 'body'); acts = an.make_actions(arm, SOLE)
    glb = MOD/'modules'/f'{hc.PREFIX}_BODY_KIT{k}.glb'; hc.export_glb(glb, animations=True); REC['models'][glb.name] = {'kind': 'body_module', 'bytes': glb.stat().st_size, 'sha256': hc.sha256(glb)}
for f in FACES:
    hc.reset_scene(); _, _, mh = mats('A', tx.FACE_TEX[f]['tone'], f); hob, _ = ha.build_head(mat=mh, data=heads[f]); head_lod(hob, f, 'full'); arm = ha.build_rig(); ha.bind(hob, arm); tag(hob, 'head ' + f)
    glb = MOD/'modules'/f'{hc.PREFIX}_HEAD_{f}_{hh.FACES[f]["name"]}.glb'; hc.export_glb(glb); REC['models'][glb.name] = {'kind': 'head_module', 'bytes': glb.stat().st_size, 'sha256': hc.sha256(glb)}
    for h in HAIRS:
        hc.reset_scene(); xob = ha.build_hair(hair[(f, h)], ha.hair_materials(h, TEX)); arm = ha.build_rig(); ha.bind(xob, arm); tag(xob, 'hair ' + h)
        glb = MOD/'modules'/f'{hc.PREFIX}_HAIR_{f}_{hx.STYLES[h]["label"]}.glb'; hc.export_glb(glb); REC['models'][glb.name] = {'kind': 'hair_module', 'bytes': glb.stat().st_size, 'sha256': hc.sha256(glb)}
# editable library: rig + body + every head + every hair (heads / hairs other than the first are hidden)
hc.reset_scene(); mk, ms, _ = mats('A', 'T2', None); bob, _ = ha.build_body(mk, ms, data=body); arm = ha.build_rig(); ha.bind(bob, arm); tag(bob, 'body')
for i, f in enumerate(FACES):
    _, _, mh = mats('A', tx.FACE_TEX[f]['tone'], f); hob, _ = ha.build_head(mat=mh, data=heads[f], name=f'{ha.HEAD_OBJ}_{f}'); head_lod(hob, f, 'full'); ha.bind(hob, arm); tag(hob, 'head ' + f); hob.hide_viewport = hob.hide_render = i > 0
    for j, h in enumerate(HAIRS):
        xob = ha.build_hair(hair[(f, h)], ha.hair_materials(h, TEX), name=f'{ha.HAIR_OBJ}_{f}_{h}'); ha.bind(xob, arm); tag(xob, 'hair ' + h); xob.hide_viewport = xob.hide_render = not (i == 0 and j == 0)
an.make_actions(arm, SOLE); bpy.context.scene['hm55_status'] = hc.STATUS
bl = MOD/f'{hc.PREFIX}_LIBRARY.blend'; hc.save_blend(bl); REC['models'][bl.name] = {'kind': 'library_blend', 'bytes': bl.stat().st_size, 'sha256': hc.sha256(bl)}
REC['timing_s']['modules'] = round(time.time() - t0, 1); REC['timing_s']['total'] = round(time.time() - t_all, 1)
hc.write_json(OUT/'qa/build_hm55.json', REC); print('BUILD OK', REC['timing_s'], 'models', len(REC['models']), flush=True)
hc.finish()
