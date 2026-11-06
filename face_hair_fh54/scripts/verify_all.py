"""FH53 verification. Writes build/qa/verify_all.json.

1. Every saved .blend is opened in a fresh session: objects, materials, images (packed / loadable / missing).
2. Every GLB is imported into an EMPTY scene and compared triangle-by-triangle against the source Blender data
   (positions, corner normals, UVs, vertex colours) per material; material alpha mode / double-sided / image size.
3. Every face x hair combination GLB:
   - BVH triangle overlap contacts at epsilon 0 (same method as FACE52 contact_compare46: hair vs other
     primitives, hair self pairs not sharing a position),
   - dense radial probe: skin sampled on a barycentric grid; any skin point outside the hair cap,
   - hairline gap: radial height of the cap's feathered edge (vertex alpha <= 0.1) above the skin,
   - cap vertices with alpha < 0.99 over the open skull (head interior would show through).
4. Measured metrics vs FACE52 final GLB.
Static geometry only: no animation, no neck motion, no engine sorting, no temporal test.
"""
import sys, json, math, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from mathutils.bvhtree import BVHTree
import fh53_common as fc, fh53_assemble as asm, glb_io, penetration as pen

OUT = fc.BUILD


# ------------------------------------------------------------------ helpers
def scene_corner_data():
    """{material name: list of triangles [(pos(3,3), nrm(3,3), uv(3,2), col(3,4))]} from all mesh objects."""
    dg = bpy.context.evaluated_depsgraph_get(); out = {}
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH':
            continue
        me = ob.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); mw = np.array(ob.matrix_world)
        co = np.array([v.co[:] for v in me.vertices]); co = (mw[:3, :3] @ co.T).T + mw[:3, 3]
        cn = np.array([n.vector[:] for n in me.corner_normals]); cn = (np.linalg.inv(mw[:3, :3]).T @ cn.T).T
        uv = np.array([d.uv[:] for d in me.uv_layers.active.data]) if me.uv_layers else np.zeros((len(me.loops), 2))
        ca = me.color_attributes.active_color if me.color_attributes else None
        col = np.array([d.color[:] for d in ca.data]) if ca is not None and ca.domain == 'CORNER' else np.ones((len(me.loops), 4))
        for t in me.loop_triangles:
            mat = ob.material_slots[t.material_index].material.name if ob.material_slots else ''
            L = list(t.loops); V = list(t.vertices)
            out.setdefault(mat, []).append((co[V], cn[L], uv[L], col[L]))
        ob.evaluated_get(dg).to_mesh_clear()
    return out


def canon(tris):
    keyed = []
    for P, N, U, C in tris:
        r = np.round(P, 6); k = min(range(3), key=lambda i: tuple(r[i]))
        idx = [(k + j) % 3 for j in range(3)]
        keyed.append((tuple(np.round(P[idx], 6).ravel()), P[idx], N[idx], U[idx], C[idx]))
    keyed.sort(key=lambda x: x[0])
    return keyed


def compare_corner_data(a, b):
    res = {'materials_a': sorted(a), 'materials_b': sorted(b)}
    rows = {}
    for m in sorted(set(a) | set(b)):
        if m not in a or m not in b:
            rows[m] = 'missing in ' + ('import' if m not in b else 'source'); continue
        A = canon(a[m]); Bc = canon(b[m])
        if len(A) != len(Bc):
            rows[m] = f'triangle count {len(A)} vs {len(Bc)}'; continue
        PA = np.array([x[1] for x in A]); PB = np.array([x[1] for x in Bc])
        NA = np.array([x[2] for x in A]); NB = np.array([x[2] for x in Bc])
        UA = np.array([x[3] for x in A]); UB = np.array([x[3] for x in Bc])
        CA = np.array([x[4] for x in A]); CB = np.array([x[4] for x in Bc])
        NAn = NA/np.linalg.norm(NA, axis=-1, keepdims=True); NBn = NB/np.linalg.norm(NB, axis=-1, keepdims=True)
        ang = np.degrees(np.arccos(np.clip((NAn*NBn).sum(-1), -1, 1)))
        k = min(CA.shape[-1], CB.shape[-1])
        rows[m] = {'triangles': len(A), 'pos_max_abs': float(np.abs(PA-PB).max()), 'normal_max_deg': float(ang.max()),
                   'normal_corners_over_0.1deg': int((ang > 0.1).sum()), 'uv_max_abs': float(np.abs(UA-UB).max()),
                   'colour_max_abs': float(np.abs(CA[..., :k]-CB[..., :k]).max())}
    res['per_material'] = rows
    return res


def material_info():
    out = {}
    for m in bpy.data.materials:
        if m.users == 0:
            continue
        imgs = [n.image for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeTexImage' and n.image] if m.use_nodes else []
        out[m.name] = {'blend_method': m.blend_method, 'surface_render_method': getattr(m, 'surface_render_method', None),
                       'backface_culling': m.use_backface_culling,
                       'images': [{'name': i.name, 'size': list(i.size), 'has_data': bool(i.has_data)} for i in imgs]}
    return out


def check_images():
    rows = []
    for img in bpy.data.images:
        if img.users == 0:
            continue
        packed = img.packed_file is not None
        try:
            _ = img.pixels[0]; loaded = img.has_data
        except Exception:
            loaded = False
        missing = (not packed) and not (img.filepath and Path(bpy.path.abspath(img.filepath)).exists()) and img.source == 'FILE'
        rows.append({'name': img.name, 'size': list(img.size), 'packed': packed, 'loaded': bool(loaded), 'missing': bool(missing)})
    return rows


# ------------------------------------------------------------------ 1. blend reopen
def verify_blends(paths):
    out = {}
    for p in paths:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.open_mainfile(filepath=str(p))
        objs = [{'name': o.name, 'type': o.type, 'faces': len(o.data.polygons) if o.type == 'MESH' else None,
                 'location': list(o.location), 'rotation': list(o.rotation_euler), 'scale': list(o.scale)} for o in bpy.data.objects]
        imgs = check_images()
        out[p.name] = {'opened_with': bpy.app.version_string, 'file_saved_version': list(bpy.data.version), 'objects': objs,
                       'images': imgs, 'missing_images': sum(r['missing'] for r in imgs),
                       'unloadable_images': sum(not r['loaded'] for r in imgs), 'materials': material_info(), 'sha256': fc.sha256(p)}
    return out


# ------------------------------------------------------------------ 2. glb round trip
def import_glb(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    return scene_corner_data(), material_info(), check_images()


def verify_glb(path, source_loader):
    source_loader(); src = scene_corner_data()
    imp, mats, imgs = import_glb(path)
    return {'glb': path.name, 'sha256': fc.sha256(path), 'compare': compare_corner_data(src, imp), 'imported_materials': mats,
            'imported_images': imgs, 'stats': glb_io.stats(path)}


# ------------------------------------------------------------------ 3. contacts / penetration
def glb_parts(path):
    g, b = glb_io.read_glb(path); parts = {}
    for n in g['nodes']:
        if 'mesh' not in n:
            continue
        assert not any(k in n for k in ('matrix', 'translation', 'rotation', 'scale')), 'node transform present'
        for p in g['meshes'][n['mesh']]['primitives']:
            key = n['name'] + '/' + g['materials'][p['material']]['name']
            V = glb_io.accessor(g, b, p['attributes']['POSITION']).astype(float); I = glb_io.accessor(g, b, p['indices']).ravel().reshape(-1, 3)
            V = np.stack([V[:, 0], -V[:, 2], V[:, 1]], 1)      # glTF Y-up -> Blender Z-up (head frame)
            col = glb_io.accessor(g, b, p['attributes']['COLOR_0']) if 'COLOR_0' in p['attributes'] else None
            parts[key] = {'V': V, 'I': I, 'col': col}
    return parts


def contacts(parts):
    trees = {k: (BVHTree.FromPolygons([tuple(v) for v in p['V']], [tuple(int(i) for i in t) for t in p['I']], all_triangles=True, epsilon=0.0),
                 [{tuple(p['V'][i]) for i in t} for t in p['I']]) for k, p in parts.items()}
    cross = {}; selfp = {}
    for a, b in itertools.combinations(sorted(parts), 2):
        if not (a.startswith(fc.HAIR_OBJ + '/') or b.startswith(fc.HAIR_OBJ + '/')):
            continue
        pairs = set(trees[a][0].overlap(trees[b][0]))
        if a.startswith(fc.HAIR_OBJ + '/') and b.startswith(fc.HAIR_OBJ + '/'):
            pairs = {(i, j) for i, j in pairs if not trees[a][1][i] & trees[b][1][j]}     # shared edge/vertex only
        cross[a + ' | ' + b] = len(pairs)
    for k, (t, cs) in trees.items():
        if not k.startswith(fc.HAIR_OBJ + '/'):
            continue
        raw = {tuple(sorted(x)) for x in t.overlap(t) if x[0] != x[1]}
        selfp[k] = len([1 for i, j in raw if not cs[i] & cs[j]])
    return {'cross': cross, 'hair_self_nonshared': selfp,
            'hair_vs_skin_total': sum(v for k, v in cross.items() if fc.HAIR_OBJ + '/' in k and (fc.FACE_OBJ in k or fc.BACK_OBJ in k)),
            'hair_cap_vs_cards': sum(v for k, v in cross.items() if k.count(fc.HAIR_OBJ + '/') == 2 and ('_Cards' in k or 'slot_13' in k))}


def cap_key(parts):
    caps = [k for k in parts if k.startswith(fc.HAIR_OBJ + '/') and (k.endswith('_Cap') or k.endswith('_CapEdge') or k.endswith('TM18_HairCap_Detail'))]
    cards = [k for k in parts if k.startswith(fc.HAIR_OBJ + '/') and k not in caps]
    return caps, cards


def skin_geometry(parts):
    """Skin primitives as world points + BVH (face + back scalp, all materials)."""
    V = []; T = []; off = 0
    for k, p in parts.items():
        if k.startswith(fc.FACE_OBJ + '/') or k.startswith(fc.BACK_OBJ + '/'):
            V.append(p['V']); T.append(p['I'] + off); off += len(p['V'])
    V = np.concatenate(V); T = np.concatenate(T)
    return V, T


def dense_skin_points(V, T, n=8):
    bary = np.array([(i/n, j/n, 1 - i/n - j/n) for i in range(n+1) for j in range(n+1-i)])
    return np.einsum('bk,tkd->tbd', bary, V[T]).reshape(-1, 3)


def hair_checks(parts, cover_fn):
    capks, cardk = cap_key(parts); capk = ' + '.join(capks)
    off = 0; VV = []; II = []; CC = []
    for k in capks:
        q = parts[k]; VV.append(q['V']); II.append(q['I'] + off); off += len(q['V'])
        CC.append(q['col'] if q['col'] is not None and q['col'].shape[1] == 4 else np.ones((len(q['V']), 4)))
    cap = {'V': np.concatenate(VV), 'I': np.concatenate(II), 'col': np.concatenate(CC)}
    V, T = skin_geometry(parts); pts = dense_skin_points(V, T)
    dep, _ = pen.radial_depth(cap['V'], [tuple(int(i) for i in t) for t in cap['I']], pts, fc.HEAD_CENTRE)
    skin_bvh = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(int(i) for i in t) for t in T], epsilon=0.0)
    C = np.array(fc.HEAD_CENTRE)
    def height_above_skin(P):
        out = []
        from mathutils import Vector
        for p in P:
            d = p - C; r = np.linalg.norm(d); d /= r
            loc, n, i, dist = skin_bvh.ray_cast(Vector(C + d*0.5), Vector(-d), 0.5)
            out.append(r - (np.array(loc) - C) @ d if loc is not None else np.nan)
        return np.array(out)
    a = cap['col'][:, 3] if cap['col'] is not None and cap['col'].shape[1] == 4 else np.ones(len(cap['V']))
    edge = a <= 0.1
    h_edge = height_above_skin(cap['V'][edge]) if edge.any() else np.array([np.nan])
    dirs = cap['V'] - C; dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    cov = np.array([float(cover_fn(d)) for d in dirs])
    alpha_over_hole = (a < 0.99) & (cov < 0.5)
    hole_locs = [list(np.round(fc.dir_to_azel(d), 1)) for d in dirs[alpha_over_hole]][:40]
    card_h = []
    for k in cardk:
        card_h.append(height_above_skin(parts[k]['V']))
    card_h = np.concatenate(card_h) if card_h else np.array([np.nan])
    return {'cap_primitive': capk, 'skin_samples': int(len(pts)), 'skin_samples_under_cap': int(np.isfinite(dep).sum()),
            'skin_points_outside_cap': int((dep > 0).sum()), 'max_skin_outside_cap_mm': float(np.nanmax(dep)*1000) if np.isfinite(dep).any() else None,
            'min_cap_clearance_mm': float(-np.nanmax(dep)*1000) if np.isfinite(dep).any() else None,
            'hairline_edge_vertices': int(edge.sum()), 'hairline_edge_height_mm': {'min': float(np.nanmin(h_edge)*1000), 'median': float(np.nanmedian(h_edge)*1000), 'max': float(np.nanmax(h_edge)*1000)} if edge.any() else None,
            'cap_vertices_alpha_lt_0.99_over_open_skull': int(alpha_over_hole.sum()), 'open_skull_alpha_locations_azel': hole_locs,
            'card_vertex_height_above_skin_mm': {'min': float(np.nanmin(card_h)*1000), 'p50': float(np.nanmedian(card_h)*1000)} if np.isfinite(card_h).any() else None}


def main():
    inputs = fc.check_inputs()
    R = {'blender': bpy.app.version_string, 'inputs': inputs, 'scope': __doc__}
    face_blends = [asm.module_file('face', f) for f in ('F1', 'F2', 'F3', 'F1S', 'F2S', 'F3S', 'F1T', 'F2T', 'F3T')]
    hair_blends = [asm.module_file('hair', h) for h in ('H1', 'H2', 'H3', 'H4')]
    lib = OUT/'models/TM_FH54_LIBRARY_faces_hairs.blend'
    R['blend_reopen'] = verify_blends(face_blends + hair_blends + [lib])
    # 2. module GLB round trips
    R['glb_roundtrip'] = {}
    for p in face_blends + hair_blends:
        R['glb_roundtrip'][p.with_suffix('.glb').name] = verify_glb(p.with_suffix('.glb'), lambda p=p: bpy.ops.wm.open_mainfile(filepath=str(p)))
        print('ROUNDTRIP', p.name, flush=True)
    for fid, hid in itertools.product(asm.FACES, asm.HAIRS):
        g = OUT/'models/combos'/f'TM_FH54_{fid}_{hid}.glb'
        R['glb_roundtrip'][g.name] = verify_glb(g, lambda f=fid, h=hid: asm.assemble(f, h))
    # FACE52 regression: F0_H0 combo vs original FACE52 final GLB (attribute level)
    _, a = glb_io.primitives(fc.FACE52_GLB); _, b = glb_io.primitives(OUT/'models/combos/TM_FH54_F0_H0.glb')
    reg = {}
    for k in sorted(a):
        row = {}
        for attr in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'COLOR_0'):
            x, y = a[k].get(attr), b.get(k, {}).get(attr)
            if x is None or y is None:
                row[attr] = 'absent'; continue
            if x.shape[-1] != y.shape[-1]:
                k2 = min(x.shape[-1], y.shape[-1]); row[attr] = f'components {x.shape[-1]} vs {y.shape[-1]}; first {k2} maxdiff %.2e' % np.abs(x[..., :k2]-y[..., :k2]).max(); continue
            row[attr] = 'exact' if (x == y).all() else 'maxdiff %.2e' % np.abs(x.astype(float)-y.astype(float)).max()
        reg[k] = row
    R['regression_F0_H0_vs_FACE52_final'] = reg
    # 3. contacts & penetration for every combination (+ FACE52 final as baseline)
    bpy.ops.wm.open_mainfile(filepath=str(fc.FACE52_BLEND))
    hf = fc.HeadField(bpy.data.objects[fc.FACE_OBJ], bpy.data.objects[fc.BACK_OBJ], bpy.data.objects[fc.HAIR_OBJ])
    R['combos'] = {}
    base = glb_parts(fc.FACE52_GLB)
    R['FACE52_final_baseline'] = {'contacts': contacts(base), 'hair': hair_checks(base, hf.skin_cover)}
    for fid, hid in itertools.product(asm.FACES, asm.HAIRS):
        g = OUT/'models/combos'/f'TM_FH54_{fid}_{hid}.glb'; parts = glb_parts(g)
        R['combos'][f'{fid}_{hid}'] = {'glb': g.name, 'contacts': contacts(parts), 'hair': hair_checks(parts, hf.skin_cover)}
        c = R['combos'][f'{fid}_{hid}']
        print('COMBO', fid, hid, 'hair-skin contacts', c['contacts']['hair_vs_skin_total'], 'cap-cards', c['contacts']['hair_cap_vs_cards'],
              'self', c['contacts']['hair_self_nonshared'], 'skin_out', c['hair']['skin_points_outside_cap'], 'alpha_over_hole', c['hair']['cap_vertices_alpha_lt_0.99_over_open_skull'], flush=True)
    # 3b. card contacts by obstacle and position along the card (root fade band vs beyond)
    import card_contacts
    for key, c in R['combos'].items():
        c['card_contacts'] = card_contacts.classify(OUT/'models/combos'/c['glb'])
    def group(keys):
        rows = [R['combos'][k] for k in keys]
        return {'combos': keys,
                'hair_vs_skin_pairs': [r['contacts']['hair_vs_skin_total'] for r in rows],
                'cap_vs_cards_pairs': [r['contacts']['hair_cap_vs_cards'] for r in rows],
                'card_self_pairs': [sum(r['contacts']['hair_self_nonshared'].values()) for r in rows],
                'skin_points_outside_cap': [r['hair']['skin_points_outside_cap'] for r in rows],
                'alpha_over_open_skull': [r['hair']['cap_vertices_alpha_lt_0.99_over_open_skull'] for r in rows]}
    R['summary_H0_original_4'] = group([f'{f}_H0' for f in asm.FACES])
    R['summary_H1_H4_new_16'] = group([f'{f}_{h}' for f in asm.FACES for h in ('H1', 'H2', 'H3', 'H4')])
    # 4. metrics
    R['metrics'] = {'FACE52_final': glb_io.stats(fc.FACE52_GLB)}
    for p in sorted((OUT/'models').rglob('*.glb')):
        R['metrics'][p.name] = glb_io.stats(p)
    fc.write_json(OUT/'qa/verify_all.json', R)


if __name__ == '__main__':
    main()
    fc.finish()
