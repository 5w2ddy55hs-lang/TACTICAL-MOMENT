"""FH53 provisional full-body review with the Reference04 body (NOT a join, NOT rigged, NOT animated).

* Opens the Reference04 study .blend read-only and saves a NEW review file; the source file is never written.
* Reference04's own head is hidden non-destructively: face attribute 'fh53_hide_ref_head' + a Geometry Nodes
  Delete Geometry modifier after the armature modifier (mesh data, UVs, weights and rig are unchanged).
  Hidden faces: materials SOURCE_APPEARANCE04_slot_13/14/15/16, and slot_02 faces whose lowest vertex is above
  z = 1.536 (back-of-head skin; FACE52's REF14_BackScalp takes this role).
* Head modules are parented to an Empty at the static attachment translation (0, -0.0393776, 1.5979694),
  rotation 0, scale 1. Head meshes have no bones/weights: the head does not follow the rig.
Renders: same world colour as the FACE52 review; three area lights scaled to body size; Cycles CPU seed 0.
Usage: python review_ref04.py
"""
import sys, math, json, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from mathutils import Vector
import fh53_common as fc, fh53_assemble as asm

COMBOS = ['F0_H0', 'F1_H1', 'F2_H2', 'F3_H3', 'F2_H4']
HEAD_MATS = {'SOURCE_APPEARANCE04_slot_13', 'SOURCE_APPEARANCE04_slot_14', 'SOURCE_APPEARANCE04_slot_15', 'SOURCE_APPEARANCE04_slot_16'}


def hide_ref_head(body):
    me = body.data; co = np.array([v.co[:] for v in me.vertices])
    names = [s.material.name if s.material else '' for s in body.material_slots]
    flags = []
    for p in me.polygons:
        m = names[p.material_index]; zmin = co[list(p.vertices), 2].min()
        flags.append(bool(m in HEAD_MATS or (m == 'SOURCE_APPEARANCE04_slot_02' and zmin >= 1.536 - 1e-6)))
    attr = me.attributes.new('fh53_hide_ref_head', 'BOOLEAN', 'FACE'); attr.data.foreach_set('value', flags)
    ng = bpy.data.node_groups.new('FH53_HideReferenceHead', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput'); go = ng.nodes.new('NodeGroupOutput')
    na = ng.nodes.new('GeometryNodeInputNamedAttribute'); na.data_type = 'BOOLEAN'; na.inputs['Name'].default_value = 'fh53_hide_ref_head'
    dg = ng.nodes.new('GeometryNodeDeleteGeometry'); dg.domain = 'FACE'
    ng.links.new(gi.outputs[0], dg.inputs['Geometry']); ng.links.new(na.outputs['Attribute'], dg.inputs['Selection'])
    ng.links.new(dg.outputs['Geometry'], go.inputs[0])
    mod = body.modifiers.new('FH53_HideReferenceHead (review only)', 'NODES'); mod.node_group = ng
    return int(sum(flags))


def setup_scene(size_x, size_y, samples):
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    sc.cycles.seed = 0; sc.cycles.use_denoising = False
    sc.render.resolution_x = size_x; sc.render.resolution_y = size_y; sc.render.resolution_percentage = 100
    sc.render.film_transparent = False; sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('FH53_ReviewWorld'); w.use_nodes = True; sc.world = w
    w.node_tree.nodes['Background'].inputs[0].default_value = (.22, .27, .34, 1); w.node_tree.nodes['Background'].inputs[1].default_value = .5
    target = Vector((0, 0, 1.0)); k = 5.0
    for loc, power, sz in [((.3, -.4, .5), 3, .5), ((-.35, -.2, .25), 1.25, .4), ((0, .3, .4), 2, .3)]:
        d = bpy.data.lights.new('FH53_ReviewArea', 'AREA'); d.energy = power*k*k; d.shape = 'DISK'; d.size = sz*k
        o = bpy.data.objects.new('FH53_ReviewArea', d); sc.collection.objects.link(o)
        o.location = target + Vector(loc)*k; o.rotation_euler = (target - o.location).to_track_quat('-Z', 'Y').to_euler()
    cd = bpy.data.cameras.new('FH53_ReviewCamera'); cam = bpy.data.objects.new('FH53_ReviewCamera', cd); sc.collection.objects.link(cam)
    sc.camera = cam; cd.type = 'ORTHO'
    return sc, cam


def shoot(sc, cam, loc, aim, scale, path, sx, sy):
    sc.render.resolution_x = sx; sc.render.resolution_y = sy
    cam.data.ortho_scale = scale; cam.location = loc; cam.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    return path


SHOTS = [('body_front', (0, -6, 1.0), (0, 0, .93), 2.05, 384, 768), ('body_quarterR', (4.2, -4.2, 1.1), (0, 0, .93), 2.05, 384, 768),
         ('head_front', (0, -3, 1.62), (0, 0, 1.56), .46, 384, 384), ('head_side', (3, 0, 1.62), (0, 0, 1.56), .46, 384, 384),
         ('head_back', (0, 3, 1.62), (0, 0, 1.56), .46, 384, 384)]


def main():
    fc.check_inputs(('FACE52_BLEND', 'FACE52_GLB', 'REF04_BLEND'))
    out = fc.BUILD; rdir = out/'renders/ref04'; rdir.mkdir(parents=True, exist_ok=True)
    rows = []
    # reference: Reference04 as-is (own head)
    bpy.ops.wm.open_mainfile(filepath=str(fc.REF04_BLEND))
    sc, cam = setup_scene(384, 768, 16)
    for name, loc, aim, scale, sx, sy in SHOTS:
        p = shoot(sc, cam, loc, aim, scale, rdir/f'REF04_original_{name}.png', sx, sy); rows.append({'combo': 'REF04_original_head', 'shot': name, 'png': p.name, 'sha256': fc.sha256(p)})
    # review file
    bpy.ops.wm.open_mainfile(filepath=str(fc.REF04_BLEND))
    body = bpy.data.objects['REF_SourcePlayer_reference_only']
    hidden = hide_ref_head(body)
    mount = bpy.data.objects.new('FH53_HeadMount_static_translation', None); bpy.context.scene.collection.objects.link(mount)
    mount.location = fc.REF04_HEAD_TRANSLATION; mount.empty_display_size = 0.05
    colls = {}
    for combo in COMBOS:
        fid, hid = combo.split('_')
        coll = bpy.data.collections.new(f'FH53_HEAD_{combo}'); bpy.context.scene.collection.children.link(coll); colls[combo] = coll
        for kind, mid, names in (('face', fid, [fc.FACE_OBJ, fc.BACK_OBJ]), ('hair', hid, [fc.HAIR_OBJ])):
            with bpy.data.libraries.load(str(asm.module_file(kind, mid)), link=False) as (src, dst):
                dst.objects = list(names)
            for ob in dst.objects:
                coll.objects.link(ob); ob.name = f'{combo}__{ob.name.split(".")[0]}'; ob.parent = mount
    sc, cam = setup_scene(384, 768, 16)
    for combo in COMBOS:
        for c, coll in colls.items():
            coll.hide_render = c != combo; coll.hide_viewport = c != combo
        for name, loc, aim, scale, sx, sy in SHOTS:
            p = shoot(sc, cam, loc, aim, scale, rdir/f'{combo}_{name}.png', sx, sy)
            rows.append({'combo': combo, 'shot': name, 'png': p.name, 'sha256': fc.sha256(p)})
        print('REVIEW', combo, flush=True)
    for c, coll in colls.items():
        coll.hide_render = c != 'F1_H1'; coll.hide_viewport = c != 'F1_H1'
    s = bpy.context.scene
    s['fh53_review_status'] = ('PROVISIONAL STATIC PLACEMENT FOR PROPORTION REVIEW ONLY. Not joined, no weights, head does not follow the rig, '
                               'neck seam not built, not animation-tested. Reference04 head hidden by a review-only modifier.')
    s['fh53_head_translation'] = list(fc.REF04_HEAD_TRANSLATION)
    blend = out/'models/review/TM_FH53_REVIEW_REF04_PROVISIONAL.blend'; fc.save_blend(blend)
    rec = {'blender': bpy.app.version_string, 'source_ref04_blend_sha256': fc.sha256(fc.REF04_BLEND), 'hidden_reference_head_faces': hidden,
           'head_translation': fc.REF04_HEAD_TRANSLATION, 'combos': COMBOS, 'review_blend': blend.name, 'review_blend_sha256': fc.sha256(blend),
           'renders': rows, 'scope': __doc__}
    fc.write_json(out/'qa/review_ref04.json', rec)


if __name__ == '__main__':
    main()
    fc.finish()
