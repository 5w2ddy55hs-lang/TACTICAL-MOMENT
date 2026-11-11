"""Load an exported HM55 player GLB into an empty scene and pose it from its own (re-imported) animations."""
import bpy
import numpy as np
import hm_common as hc


def load_player(path):
    hc.reset_scene(); bpy.context.scene.render.fps = 30                      # HM55 motions are authored at 30 fps
    try:
        bpy.ops.import_scene.gltf(filepath=str(path), disable_bone_shape=True)
    except TypeError:
        bpy.ops.import_scene.gltf(filepath=str(path))
    for o in [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.vertex_groups]:
        bpy.data.objects.remove(o, do_unlink=True)                          # importer helper shapes are not part of the GLB
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE'); meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if arm.animation_data:
        for tr in list(arm.animation_data.nla_tracks):
            arm.animation_data.nla_tracks.remove(tr)
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    return arm, meshes


def action_names():
    return sorted(a.name for a in bpy.data.actions)


def pose(arm, action=None, frame=1):
    if action is None:
        if arm.animation_data:
            arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    else:
        act = next(x for x in bpy.data.actions if x.name == action or x.name.startswith(action + '_'))
        arm.animation_data_create(); arm.animation_data.action = act; bpy.context.scene.frame_set(int(frame))
    bpy.context.view_layer.update()


def world_vertices(ob):
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg); m = e.to_mesh(); V = np.array([tuple(e.matrix_world @ v.co) for v in m.vertices])
    T = []; m.calc_loop_triangles(); T = [tuple(t.vertices) for t in m.loop_triangles]; mats = [t.material_index for t in m.loop_triangles]; e.to_mesh_clear()
    return V, T, mats


def bone_head(arm, name):
    return np.array(arm.matrix_world @ arm.pose.bones[name].head)
