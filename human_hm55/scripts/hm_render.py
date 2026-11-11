"""HM55 review renders: own camera / light rig (Cycles CPU, fixed seed). Orthographic cameras so sizes compare."""
import math
import bpy
from mathutils import Vector


def setup(res=(512, 512), samples=24, bg=(0.30, 0.33, 0.38), strength=0.55, ortho=0.36, target=(0, 0, 0.05), clay=False):
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples; sc.cycles.seed = 0
    sc.cycles.use_denoising = False; sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'; sc.render.film_transparent = False; sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('HM_World'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (*bg, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = strength; sc.world = w
    T = Vector(target); s = ortho/0.36
    for loc, power, size in (((0.55, -0.85, 0.75), 9.0, 0.9), ((-0.80, -0.45, 0.25), 3.0, 0.8), ((0.10, 0.90, 0.60), 5.0, 0.7)):
        d = bpy.data.lights.new('HM_Area', 'AREA'); d.energy = power*s*s; d.shape = 'DISK'; d.size = size*s
        ob = bpy.data.objects.new('HM_Area', d); sc.collection.objects.link(ob); ob.location = T + Vector(loc)*s
        ob.rotation_euler = (T - ob.location).to_track_quat('-Z', 'Y').to_euler()
    cd = bpy.data.cameras.new('HM_Cam'); cam = bpy.data.objects.new('HM_Cam', cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_start = 0.01; cd.clip_end = 50
    if clay:
        m = bpy.data.materials.new('HM_Clay'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (0.62, 0.60, 0.58, 1); b.inputs['Roughness'].default_value = 0.75
        for ob in sc.objects:
            if ob.type == 'MESH':
                ob.data.materials.clear(); ob.data.materials.append(m)
    return sc, cam, T


VIEW_DIRS = {'front': (0, -1, 0.0), 'quarter_R': (0.7, -0.7, 0.05), 'quarter_L': (-0.7, -0.7, 0.05), 'side_R': (1, 0, 0), 'side_L': (-1, 0, 0),
             'back': (0, 1, 0), 'back_quarter': (0.7, 0.7, 0.1), 'top': (0, -0.25, 1), 'low_front': (0, -1, -0.35)}


def aim(cam, target, view, dist=3.0):
    d = Vector(VIEW_DIRS[view] if isinstance(view, str) else view).normalized(); cam.location = Vector(target) + d*dist
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()


def render(sc, cam, target, views, prefix, dist=3.0):
    out = []
    for v in views:
        aim(cam, target, v, dist); sc.render.filepath = f'{prefix}_{v if isinstance(v, str) else "custom"}.png'
        bpy.ops.render.render(write_still=True); out.append(sc.render.filepath)
    return out
