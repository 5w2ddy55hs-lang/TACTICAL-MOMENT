"""HM55 assembly: body mesh (kit + skin materials), head mesh (face + neck + ears), armature, skin weights.
Everything is generated in memory from hm_body / hm_head; nothing is imported from another model file."""
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
import hm_common as hc, hm_body as hb, hm_head as hh

BODY_OBJ, HEAD_OBJ, HAIR_OBJ, ARM_OBJ = 'TM_HM57_Body', 'TM_HM57_Head', 'TM_HM57_Hair', 'TM_HM55_Rig'


def set_weights(ob, weights):
    groups = {}
    for i, w in enumerate(weights):
        for bone, v in w.items():
            g = groups.get(bone) or ob.vertex_groups.new(name=bone); groups[bone] = g; g.add([i], float(v), 'REPLACE')


def build_body(kit_mat=None, skin_mat=None, data=None):
    d = data or hb.body_data()
    ob = hc.new_mesh_object(BODY_OBJ, d['verts'], d['faces'], d['uvs'])
    ob.data.materials.append(kit_mat or hc.simple_material('TM_HM57_Kit', color=(0.75, 0.75, 0.78, 1)))
    ob.data.materials.append(skin_mat or hc.simple_material('TM_HM57_BodySkin', color=(0.80, 0.60, 0.48, 1)))
    ob.data.polygons.foreach_set('material_index', [0 if m == 'kit' else 1 for m in d['face_material']]); set_weights(ob, d['weights'])
    # weld the shorts pelvis ring to the two leg rings (coincident duplicates by construction)
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); before = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=[bm.verts[i] for i in d['shorts_ids']], dist=1e-6); bm.to_mesh(ob.data); bm.free(); ob.data.update()
    info = dict(d['info']); info['_welded_vertices'] = before - len(ob.data.vertices)
    return ob, info


def head_data(P=None):
    """Pure data for one head variant in head-local coordinates (grid + ears), with weights and region tags."""
    P = P or hh.P0; d = hh.build_mesh_data(P); verts = [tuple(v) for v in d['verts']]; faces = list(d['faces']); uvs = [tuple(u) for u in d['uvs']]
    weights = hh.head_weights(P, d['verts']); ears = {}; fregion = ['head']*len(faces)
    for sgn in (1, -1):
        e = hh.ear_data(d['sdf'], sgn); base = len(verts); verts += [tuple(v) for v in e['verts']]; faces += [tuple(i + base for i in f) for f in e['faces']]
        uvs += [tuple(u) for u in e['uvs']]; weights += [{'Head': 1.0}]*len(e['verts']); fregion += ['ear_L' if sgn > 0 else 'ear_R']*len(e['faces'])
        ears[sgn] = {'first': base, 'count': len(e['verts']), 'frame': e['frame'], 'rim': e['rim']}
    return {'verts': np.array(verts), 'faces': faces, 'uvs': np.array(uvs), 'weights': weights, 'face_region': fregion, 'grid': d, 'ears': ears, 'P': P}


def build_head(P=None, mat=None, name=HEAD_OBJ, data=None):
    d = data or head_data(P); world = d['verts'] + hb.HEAD_PIVOT
    ob = hc.new_mesh_object(name, world, d['faces'], d['uvs'])
    ob.data.materials.append(mat or hc.simple_material('TM_HM57_HeadSkin', color=(0.80, 0.60, 0.48, 1))); set_weights(ob, d['weights'])
    return ob, d


def build_rig():
    ad = bpy.data.armatures.new('TM_HM55_Skeleton'); arm = bpy.data.objects.new(ARM_OBJ, ad); bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm; arm.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    for name, head, tail, parent in hb.bones():
        b = ad.edit_bones.new(name); b.head = head; b.tail = tail; b.roll = 0.0
        if parent:
            b.parent = ad.edit_bones[parent]; b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT'); arm.select_set(False)
    arm['hm55_status'] = hc.STATUS; arm['hm55_rig'] = 'Original 22-bone humanoid skeleton authored in hm_body.bones(); rest pose = A-pose.'
    return arm


def bind(ob, arm):
    ob.parent = arm; md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = arm; md.use_vertex_groups = True
    names = {b.name for b in arm.data.bones}
    for g in list(ob.vertex_groups):
        if g.name not in names:
            raise ValueError('vertex group without bone: ' + g.name)


# ---------------------------------------------------------------- posing helpers (rotations given in armature axes)
def rot_euler_deg(x=0.0, y=0.0, z=0.0):
    """Armature-space rotation: about X (pitch: + = toward +Y / backwards for a hanging limb), Y (roll), Z (yaw), applied X then Y then Z."""
    import math
    return (Matrix.Rotation(math.radians(z), 4, 'Z') @ Matrix.Rotation(math.radians(y), 4, 'Y') @ Matrix.Rotation(math.radians(x), 4, 'X')).to_quaternion()


def set_pose(arm, pose, frame=None, location=None):
    """pose: {bone: (x, y, z) degrees in armature axes relative to the rest pose, expressed in the parent's frame}.
    Bones not listed return to rest. location: Hips offset in armature space (metres)."""
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; q = rot_euler_deg(*pose.get(pb.name, (0, 0, 0)))
        R = pb.bone.matrix_local.to_3x3().to_quaternion()                       # bone rest orientation in armature space
        pb.rotation_quaternion = R.inverted() @ q @ R
        pb.location = (0, 0, 0)
        if pb.name == 'Hips' and location is not None:
            pb.location = pb.bone.matrix_local.to_3x3().inverted() @ Vector(location)
        if frame is not None:
            pb.keyframe_insert('rotation_quaternion', frame=frame)
            if pb.name in ('Hips', 'Root'):
                pb.keyframe_insert('location', frame=frame)
    bpy.context.view_layer.update()


def posed_vertices(ob):
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg); m = e.to_mesh()
    V = np.array([tuple(ob.matrix_world @ v.co) for v in m.vertices]); e.to_mesh_clear()
    return V


# ---------------------------------------------------------------- hair object
def hair_materials(sid, tex_dir, lite=False):
    x = '_LITE' if lite else ''
    cap = hc.load_packed_image(tex_dir/f'TMH55_CAP_STRANDS_512{x}.png', f'TMH55_CAP_STRANDS_512{x}'); card = hc.load_packed_image(tex_dir/f'TMH55_CARD_STRANDS_512{x}.png', f'TMH55_CARD_STRANDS_512{x}')
    edge = hc.load_packed_image(tex_dir/f'TMH55_EDGE_STRANDS_512x256{x}.png', f'TMH55_EDGE_STRANDS_512x256{x}'); ex = {'hm55_hair_id': sid, 'provenance': 'Procedural strand texture (hm_hair_textures.py); no source pixels.'}
    return [hc.simple_material(f'TMH55_{sid}_Cap', cap, blend='OPAQUE', double_sided=True, extras=ex),
            hc.simple_material(f'TMH55_{sid}_CapEdge', edge, blend='BLEND', double_sided=True, vertex_alpha=True, extras=ex),
            hc.simple_material(f'TMH55_{sid}_Cards', card, blend='BLEND', double_sided=True, extras=ex)]


def build_hair(data, mats, name=HAIR_OBJ):
    """data = hm_hair.build_hair_data(...) (head-local). Hair is rigid with the Head bone."""
    V = data['verts'] + hb.HEAD_PIVOT; ob = hc.new_mesh_object(name, V, data['tris'], data['uv']); me = ob.data
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set('material_index', data['tri_mat'])
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER'); ca.data.foreach_set('color', np.asarray(data['col'], np.float32).ravel())
    n = np.asarray(data['nrm'], float); n /= np.linalg.norm(n, axis=1, keepdims=True); me.normals_split_custom_set([tuple(x) for x in n]); me.update()
    set_weights(ob, [{'Head': 1.0}]*len(me.vertices))
    return ob
