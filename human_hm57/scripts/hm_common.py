"""HM57 shared helpers. HM57 = match-presentation revision of HM56 (original, script-authored human model for TACTICAL MOMENT).

Nothing in this folder reads the Reference04 / FACE52 / FH54 meshes, textures, rig or motions as build input.
The research reference (Reference04) is opened only by compare57.py / proportions57.py, and only when
$HM_RESEARCH_REF is set, to render private side-by-side checks; those renders never go to git or public outputs.

Frame: Blender, Z up, metres, character faces -Y, +X is the character's left... (viewer's right from the
front). Output folder: $HM_BUILD (binary outputs, not committed to git).
"""
import os, sys, json, hashlib, math
from pathlib import Path
import numpy as np

try:
    import bpy
except ImportError:
    bpy = None

BUILD = Path(os.environ.get('HM_BUILD', Path(__file__).resolve().parents[1]/'build'))
PREFIX = 'TM_HM57'
STATUS = 'ORIGINAL CANDIDATE (HM57, match-presentation revision of HM56) authored by scripts in human_hm57/scripts. Not approved, not formally adopted.'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o)) + '\n')


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a)/(b - a), 0.0, 1.0)
    return t*t*(3 - 2*t)


def lerp(a, b, t):
    return a + (b - a)*t


def pchip(xs, ys):
    """Monotone cubic interpolator (numpy only), clamped outside the range."""
    xs = np.asarray(xs, float); ys = np.asarray(ys, float); h = np.diff(xs); d = np.diff(ys)/h; m = np.zeros_like(xs)
    for i in range(1, len(xs) - 1):
        if d[i-1]*d[i] > 0:
            w1 = 2*h[i] + h[i-1]; w2 = h[i] + 2*h[i-1]; m[i] = (w1 + w2)/(w1/d[i-1] + w2/d[i])
    m[0] = d[0]; m[-1] = d[-1]
    def f(x):
        x = np.clip(np.asarray(x, float), xs[0], xs[-1]); i = np.clip(np.searchsorted(xs, x) - 1, 0, len(xs) - 2)
        t = (x - xs[i])/h[i]; t2 = t*t; t3 = t2*t
        return (2*t3 - 3*t2 + 1)*ys[i] + (t3 - 2*t2 + t)*h[i]*m[i] + (-2*t3 + 3*t2)*ys[i+1] + (t3 - t2)*h[i]*m[i+1]
    return f


# ------------------------------------------------------------------ Blender helpers
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def new_mesh_object(name, verts, faces, uv_per_loop=None, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(map(float, v)) for v in verts], [], [list(map(int, f)) for f in faces]); me.update()
    if uv_per_loop is not None:
        uvl = me.uv_layers.new(name='UVMap'); uvl.data.foreach_set('uv', np.asarray(uv_per_loop, np.float32).ravel())
    if smooth:
        me.polygons.foreach_set('use_smooth', [True]*len(me.polygons))
    me.update(); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def load_packed_image(path, name, colorspace='sRGB'):
    img = bpy.data.images.load(str(path), check_existing=False); img.name = name
    img.colorspace_settings.name = colorspace; img.alpha_mode = 'STRAIGHT'; img.pack()
    return img


def simple_material(name, image=None, color=(0.8, 0.8, 0.8, 1), blend='OPAQUE', roughness=0.85, double_sided=False, vertex_alpha=False, extras=None):
    """Principled material in the layout the glTF exporter understands. An unlinked Alpha exports OPAQUE."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Specular IOR Level'].default_value = 0.15; bsdf.inputs['Base Color'].default_value = color
    if image is not None:
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = image; tex.interpolation = 'Linear'
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        if blend != 'OPAQUE':
            if vertex_alpha:
                vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'; mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
                nt.links.new(tex.outputs['Alpha'], mul.inputs[0]); nt.links.new(vc.outputs['Alpha'], mul.inputs[1]); nt.links.new(mul.outputs[0], bsdf.inputs['Alpha'])
            else:
                nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    m.blend_method = 'BLEND' if blend == 'BLEND' else 'OPAQUE'
    m.use_backface_culling = not double_sided
    m['hm55_status'] = STATUS
    for k, v in (extras or {}).items():
        m[k] = v
    return m


def save_blend(path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    try:
        bpy.ops.file.pack_all()
    except RuntimeError:
        pass
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=False)


def export_glb(path, animations=False, selection=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', export_extras=True, use_selection=selection,
                              export_animations=animations, export_skins=True, export_def_bones=False, export_yup=True,
                              **({'export_animation_mode': 'ACTIONS', 'export_force_sampling': True, 'export_optimize_animation_size': False} if animations else {}))


def finish():
    """bpy 4.2.23 (PyPI) can segfault at interpreter teardown after all outputs are written; exit explicitly."""
    sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
