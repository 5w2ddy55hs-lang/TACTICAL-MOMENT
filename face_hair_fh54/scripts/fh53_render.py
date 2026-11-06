"""FH53 review renders. Camera, lights, world and view positions are copied verbatim from
FACE52's face45_work/scripts/render_review.py setup() and face52_work/scripts/render52.py /
render_closeup_hq.py, so FACE52 and the new candidates are rendered under identical conditions.
Renderer: Cycles CPU, seed 0, no denoise (as FACE52). Blender version is recorded by the caller.
"""
import math
import bpy
from mathutils import Vector

VIEWS = [('front', (0, -.6, .08)), ('quarter_R', (.42, -.42, .11)), ('quarter_L', (-.42, -.42, .11)),
         ('side_R', (.6, 0, .08)), ('side_L', (-.6, 0, .08)), ('back', (0, .6, .08)), ('top', (0, -.16, .65))]
CLOSEUPS = [('ear_R', (.6, -.12, .10), (.082, -.04, .085), .075), ('ear_L', (-.6, -.12, .10), (-.082, -.04, .085), .075),
            ('front_edge', (0, -.6, .14), (0, -.11, .12), .16), ('nape', (0, .6, .09), (0, .09, .055), .14)]
TARGET = Vector((0, 0, .067))


def setup(size, samples):
    """Identical to FACE52 render_review.setup()."""
    scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = samples
    scene.cycles.seed = 0; scene.cycles.use_denoising = False
    scene.render.resolution_x = size; scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new('ReviewWorld'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .27, .34, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5
    scene.view_settings.view_transform = 'Standard'; target = TARGET
    for loc, power, size_light in [((.3, -.4, .5), 3, .5), ((-.35, -.2, .25), 1.25, .4), ((0, .3, .4), 2, .3)]:
        data = bpy.data.lights.new('ReviewArea', 'AREA'); data.energy = power; data.shape = 'DISK'; data.size = size_light
        ob = bpy.data.objects.new('ReviewArea', data); scene.collection.objects.link(ob); ob.location = loc
        ob.rotation_euler = (target - ob.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('ReviewCamera'); cam = bpy.data.objects.new('ReviewCamera', data)
    scene.collection.objects.link(cam); scene.camera = cam; data.type = 'ORTHO'; data.ortho_scale = .32
    return scene, cam, target


def aim(cam, loc, target):
    cam.location = loc; cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()


def grazing(scene, target):
    """FACE52 'grazing' lighting variant (render52.py), applied after setup()."""
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.035, .045, .065, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .15
    for ob in scene.objects:
        if ob.type == 'LIGHT':
            ob.data.energy *= .35
    ob = next(o for o in scene.objects if o.type == 'LIGHT'); ob.location = (.45, .15, .25); ob.data.energy = 6
    ob.data.size = .18; ob.rotation_euler = (target - ob.location).to_track_quat('-Z', 'Y').to_euler()


def render_views(scene, cam, target, prefix, views=VIEWS):
    out = []
    for name, loc in views:
        aim(cam, loc, target); scene.render.filepath = f'{prefix}_{name}.png'; bpy.ops.render.render(write_still=True)
        out.append(scene.render.filepath)
    return out


def render_closeups(scene, cam, prefix, closeups=CLOSEUPS):
    out = []; keep = cam.data.ortho_scale
    for name, loc, target, scale in closeups:
        cam.data.ortho_scale = scale; aim(cam, loc, target)
        scene.render.filepath = f'{prefix}_{name}.png'; bpy.ops.render.render(write_still=True); out.append(scene.render.filepath)
    cam.data.ortho_scale = keep
    return out
