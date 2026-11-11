"""HM55 full build: textures, face / hair / body modules, assembled skinned players with original motions.
Reads no model, texture or motion file. Writes $HM_BUILD/{textures,models,qa}.
Usage: python build_all.py [--faces P0,P1,P2,P3] [--hairs H1,H2,H3,H4] [--quick]"""
import sys, time, argparse, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
import hm_common as hc, hm_body as hb, hm_head as hh, hm_hair as hx, hm_texture as tx, hm_bake as bk, hm_assemble as ha, hm_anim as an, hm_hair_textures as ht

ap = argparse.ArgumentParser(); ap.add_argument('--faces', default='P0,P1,P2,P3'); ap.add_argument('--hairs', default='H1,H2,H3,H4'); ap.add_argument('--quick', action='store_true')
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
t0 = time.time(); ht.make_cap(TEX/'TMH55_CAP_STRANDS_512.png'); ht.make_cards(TEX/'TMH55_CARD_STRANDS_512.png'); ht.make_edge(TEX/'TMH55_EDGE_STRANDS_512x256.png')
tones = sorted({tx.FACE_TEX[f]['tone'] for f in FACES}); kits = ['A', 'B']
hc.reset_scene(); bob, _ = ha.build_body(data=body); ao_b = bk.bake_ao(bob, {0: 1024, 1: 512})
for k in kits:
    rgb, m = tx.paint_kit(body, k); tx.save_rgb(TEX/f'TM_HM55_Kit_{k}.png', tx.bleed(bk.apply_ao(rgb, ao_b[0], 0.70, (1, 1, 1), mask=m, blur=1.5), m))
SKIN_STATS = {}
for tn in tones:
    rgb, m = tx.paint_body_skin(body, tn); fin = bk.apply_ao(rgb, ao_b[1], 0.50, mask=m, blur=2.0); tx.save_rgb(TEX/f'TM_HM55_BodySkin_{tn}.png', tx.bleed(fin, m))
    SKIN_STATS['body_' + tn] = {'painted_mean_rgb': [round(float(x), 4) for x in rgb[m].mean(0)], 'final_mean_rgb': [round(float(x), 4) for x in fin[m].mean(0)]}
for f in FACES:
    hd = heads[f]; rgb, m, r = tx.paint_head(hd, tx.FACE_TEX[f]); hc.reset_scene(); hob, _ = ha.build_head(data=hd); ao = bk.bake_ao(hob, {0: 1024})
    fin = bk.apply_ao(rgb, ao[0], 0.60, mask=m, blur=2.5, limit=np.where(r['fid'] > 0, 0.28, 1.0)); tx.save_rgb(TEX/f'TM_HM55_Head_{f}.png', tx.bleed(fin, m))
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

# ---------------------------------------------------------------- 3. hair data per face (the cap follows each head shape)
t0 = time.time(); hair = {}
for f in FACES:
    for h in HAIRS:
        d = hx.build_hair_data(heads[f], h); hair[(f, h)] = d; REC['hairs'][f'{f}_{h}'] = dict(d['info'], vertices=int(len(d['verts'])), triangles=int(len(d['tris'])))
        print('hair', f, h, 'tris', len(d['tris']), 'cap overlap left', d['info']['cap_vs_head_overlap_pass']['remaining_overlapping_triangles'], flush=True)
REC['timing_s']['hair'] = round(time.time() - t0, 1)


# ---------------------------------------------------------------- 4. scenes
def mats(kit, tone, face):
    mk = hc.simple_material(f'TM_HM55_Kit_{kit}', hc.load_packed_image(TEX/f'TM_HM55_Kit_{kit}.png', f'TM_HM55_Kit_{kit}'), double_sided=True, extras={'provenance': 'Procedural kit texture (hm_texture.paint_kit) + AO bake of HM55 geometry.'})
    ms = hc.simple_material(f'TM_HM55_BodySkin_{tone}', hc.load_packed_image(TEX/f'TM_HM55_BodySkin_{tone}.png', f'TM_HM55_BodySkin_{tone}'), extras={'provenance': 'Procedural skin texture (hm_texture.paint_body_skin) + AO bake of HM55 geometry.'})
    mh = hc.simple_material(f'TM_HM55_Head_{face}', hc.load_packed_image(TEX/f'TM_HM55_Head_{face}.png', f'TM_HM55_Head_{face}'), extras={'provenance': 'Procedural face texture (hm_texture.paint_head) + AO bake of HM55 geometry.'}) if face else None
    return mk, ms, mh


def tag(ob, role):
    ob['hm55_status'] = hc.STATUS; ob['hm55_role'] = role; ob['hm55_provenance'] = 'Mesh generated by human_hm55/scripts from authored parameters; no imported or traced mesh.'


def scene_player(face, hstyle, kit, with_actions=True):
    hc.reset_scene(); tone = tx.FACE_TEX[face]['tone']; mk, ms, mh = mats(kit, tone, face)
    bob, _ = ha.build_body(mk, ms, data=body); hob, _ = ha.build_head(mat=mh, data=heads[face]); arm = ha.build_rig(); ha.bind(bob, arm); ha.bind(hob, arm); tag(bob, 'body'); tag(hob, 'head ' + face)
    if hstyle:
        xob = ha.build_hair(hair[(face, hstyle)], ha.hair_materials(hstyle, TEX)); ha.bind(xob, arm); tag(xob, 'hair ' + hstyle)
    acts = an.make_actions(arm) if with_actions else {}
    sc = bpy.context.scene; sc['hm55_status'] = hc.STATUS; sc['hm55_player'] = f'{face}_{hstyle}_KIT{kit}'
    return arm, acts


players = [(f, h, 'A') for f in FACES for h in HAIRS] + ([] if A.quick else [(FACES[i % len(FACES)], HAIRS[i % len(HAIRS)], 'B') for i in range(min(4, len(FACES)))])
t0 = time.time()
for f, h, k in players:
    name = f'{hc.PREFIX}_PLAYER_{f}_{h}_KIT{k}'; arm, acts = scene_player(f, h, k); glb = MOD/'players'/(name + '.glb'); hc.export_glb(glb, animations=True)
    REC['models'][glb.name] = {'kind': 'player', 'face': f, 'hair': h, 'kit': k, 'bytes': glb.stat().st_size, 'sha256': hc.sha256(glb), 'actions': acts}
    if (f, h, k) in [(FACES[i % len(FACES)], HAIRS[(i + 1) % len(HAIRS)], 'A') for i in range(len(FACES))] or (f, h, k) == (FACES[0], HAIRS[0], 'A'):
        bl = MOD/'players'/(name + '.blend'); hc.save_blend(bl); REC['models'][bl.name] = {'kind': 'player_blend', 'bytes': bl.stat().st_size, 'sha256': hc.sha256(bl)}
    print('player', name, round(glb.stat().st_size/1e6, 2), 'MB', flush=True)
REC['timing_s']['players'] = round(time.time() - t0, 1)

# ---------------------------------------------------------------- 5. modules + library
t0 = time.time()
for k in kits:
    hc.reset_scene(); mk, ms, _ = mats(k, 'T2', None); bob, _ = ha.build_body(mk, ms, data=body); arm = ha.build_rig(); ha.bind(bob, arm); tag(bob, 'body'); acts = an.make_actions(arm)
    glb = MOD/'modules'/f'{hc.PREFIX}_BODY_KIT{k}.glb'; hc.export_glb(glb, animations=True); REC['models'][glb.name] = {'kind': 'body_module', 'bytes': glb.stat().st_size, 'sha256': hc.sha256(glb)}
for f in FACES:
    hc.reset_scene(); _, _, mh = mats('A', tx.FACE_TEX[f]['tone'], f); hob, _ = ha.build_head(mat=mh, data=heads[f]); arm = ha.build_rig(); ha.bind(hob, arm); tag(hob, 'head ' + f)
    glb = MOD/'modules'/f'{hc.PREFIX}_HEAD_{f}_{hh.FACES[f]["name"]}.glb'; hc.export_glb(glb); REC['models'][glb.name] = {'kind': 'head_module', 'bytes': glb.stat().st_size, 'sha256': hc.sha256(glb)}
    for h in HAIRS:
        hc.reset_scene(); xob = ha.build_hair(hair[(f, h)], ha.hair_materials(h, TEX)); arm = ha.build_rig(); ha.bind(xob, arm); tag(xob, 'hair ' + h)
        glb = MOD/'modules'/f'{hc.PREFIX}_HAIR_{f}_{hx.STYLES[h]["label"]}.glb'; hc.export_glb(glb); REC['models'][glb.name] = {'kind': 'hair_module', 'bytes': glb.stat().st_size, 'sha256': hc.sha256(glb)}
# editable library: rig + body + every head + every hair (heads / hairs other than the first are hidden)
hc.reset_scene(); mk, ms, _ = mats('A', 'T2', None); bob, _ = ha.build_body(mk, ms, data=body); arm = ha.build_rig(); ha.bind(bob, arm); tag(bob, 'body')
for i, f in enumerate(FACES):
    _, _, mh = mats('A', tx.FACE_TEX[f]['tone'], f); hob, _ = ha.build_head(mat=mh, data=heads[f], name=f'{ha.HEAD_OBJ}_{f}'); ha.bind(hob, arm); tag(hob, 'head ' + f); hob.hide_viewport = hob.hide_render = i > 0
    for j, h in enumerate(HAIRS):
        xob = ha.build_hair(hair[(f, h)], ha.hair_materials(h, TEX), name=f'{ha.HAIR_OBJ}_{f}_{h}'); ha.bind(xob, arm); tag(xob, 'hair ' + h); xob.hide_viewport = xob.hide_render = not (i == 0 and j == 0)
an.make_actions(arm); bpy.context.scene['hm55_status'] = hc.STATUS
bl = MOD/f'{hc.PREFIX}_LIBRARY.blend'; hc.save_blend(bl); REC['models'][bl.name] = {'kind': 'library_blend', 'bytes': bl.stat().st_size, 'sha256': hc.sha256(bl)}
REC['timing_s']['modules'] = round(time.time() - t0, 1); REC['timing_s']['total'] = round(time.time() - t_all, 1)
hc.write_json(OUT/'qa/build_hm55.json', REC); print('BUILD OK', REC['timing_s'], 'models', len(REC['models']), flush=True)
hc.finish()
