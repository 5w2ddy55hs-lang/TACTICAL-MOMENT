"""FH53 shared helpers (Blender bpy + numpy).

Coordinate frame: FACE52 head-local Blender coordinates (Z up, face toward -Y), unchanged.
All new candidates are authored in this same frame; node transforms stay identity.

Environment variables (set by run_all.sh):
  FH53_INPUTS  restored_inputs folder made by prepare_inputs.py (contains CODEX/, VISUAL/)
  FH53_REF04   folder with the Reference04 .blend/.glb/.png
  FH53_BUILD   output folder (binary outputs; NOT committed to git)
"""
import os, json, hashlib, math
from pathlib import Path
import numpy as np

try:
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
except ImportError:  # allow numpy-only import for docs/tools
    bpy = None

INPUTS = Path(os.environ.get('FH53_INPUTS', '.'))
REF04 = Path(os.environ.get('FH53_REF04', '.'))
BUILD = Path(os.environ.get('FH53_BUILD', './build'))
FACE52_BLEND = INPUTS / 'CODEX/face52_work/models/TM_FACE52_F0_H0.blend'
FACE52_GLB = INPUTS / 'CODEX/face52_work/models/TM_FACE52_F0_H0.glb'
FACE52_RAW = INPUTS / 'CODEX/face52_work/models/TM_FACE52_F0_H0_RAW.glb'
REF04_BLEND = REF04 / 'Sakatsuku2002_reference04_APPEARANCE_STUDY.blend'
REF04_GLB = REF04 / 'Sakatsuku2002_reference04_APPEARANCE_STUDY.glb'
EXPECTED_SHA = {
    'FACE52_BLEND': '5197ef43a63fbbd386291b778b8090178ee71429a8cb4423bd7f4383eea749c2',
    'FACE52_GLB': 'f31adb0a69cecdadb0e60f87e6d881b842198e431d09a70b388afaddd1fd1b1a',
    'FACE52_RAW': '1b3b8de350f48a633060e5aabc6b54ad2aa6470b6eabd5f176654186416cb62b',
    'REF04_BLEND': 'ea61c3ea4ee8164293c9b629836355b33bd97adba50bd4dec6b363f224efc374',
    'REF04_GLB': '65b50b116faf820824acbed4b9ea8dd62fe5a2ce2ff7dbe751524fba524d1cdd',
}
# Static attachment translation of the whole head group onto Reference04 (Blender coordinates,
# same source files). Rotation 0, scale 1. Re-verified in qa/alignment_recheck.json.
REF04_HEAD_TRANSLATION = (0.0, -0.0393775999546051, 1.59796941280365)

HEAD_CENTRE = (0.0, -0.01, 0.07)     # analysis centre for radial maps (inside the head)
FACE_OBJ, HAIR_OBJ, BACK_OBJ = 'REF09_Face_Eyes_Mouth', 'REF09_Hair', 'REF14_BackScalp'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_inputs(keys=('FACE52_BLEND', 'FACE52_GLB', 'FACE52_RAW')):
    paths = {'FACE52_BLEND': FACE52_BLEND, 'FACE52_GLB': FACE52_GLB, 'FACE52_RAW': FACE52_RAW,
             'REF04_BLEND': REF04_BLEND, 'REF04_GLB': REF04_GLB}
    out = {}
    for k in keys:
        p = paths[k]
        if not p.exists():
            raise FileNotFoundError(f'missing input {k}: {p}')
        s = sha256(p)
        if s != EXPECTED_SHA[k]:
            raise ValueError(f'SHA mismatch {k}: {s}')
        out[k] = {'path': str(p), 'sha256': s}
    return out


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a)/(b - a), 0.0, 1.0)
    return t*t*(3 - 2*t)


# ---------------------------------------------------------------- directions / frames
def azel_to_dir(az_deg, el_deg):
    """Global analysis angles: az 0 = front (-Y), +90 = +X side, 180 = back; el up from horizontal."""
    a, e = math.radians(az_deg), math.radians(el_deg)
    return np.array([math.cos(e)*math.sin(a), -math.cos(e)*math.cos(a), math.sin(e)])


def dir_to_azel(d):
    d = np.asarray(d, float); d = d/np.linalg.norm(d, axis=-1, keepdims=True)
    az = np.degrees(np.arctan2(d[..., 0], -d[..., 1])); el = np.degrees(np.arcsin(np.clip(d[..., 2], -1, 1)))
    return az, el


class PolarFrame:
    """Polar coordinates (theta from axis, phi around axis) about a pole direction."""
    def __init__(self, pole_dir, ref_dir):
        A = np.asarray(pole_dir, float); A /= np.linalg.norm(A)
        R = np.asarray(ref_dir, float); R = R - A*(R @ A); R /= np.linalg.norm(R)
        self.A, self.R, self.B = A, R, np.cross(A, R)

    def dir(self, theta, phi):
        theta = np.asarray(theta, float); phi = np.asarray(phi, float)
        st = np.sin(theta)[..., None]
        return (np.cos(theta)[..., None]*self.A + st*(np.cos(phi)[..., None]*self.R + np.sin(phi)[..., None]*self.B))

    def polar(self, d):
        d = np.asarray(d, float); d = d/np.linalg.norm(d, axis=-1, keepdims=True)
        th = np.arccos(np.clip(d @ self.A, -1, 1))
        ph = np.arctan2(d @ self.B, d @ self.R) % (2*np.pi)
        return th, ph


# ---------------------------------------------------------------- head field
class HeadField:
    """Radial description of the FACE52 head around HEAD_CENTRE.

    r_skin(d)       outermost hit on face+back-scalp skin (ears included)
    r_skin_noear(d) same without the ear islands
    r_scalp(d)      skull proxy: skin where skin exists; inside the open top/back of the skin
                    an ellipsoid fitted to the surrounding skin plus a harmonic fill of the
                    skin-ellipsoid residual (continuous with the skin boundary)
    """
    def __init__(self, face_obj, back_obj, cap_obj=None, grid_deg=1.0):
        self.C = Vector(HEAD_CENTRE); self.Cn = np.array(HEAD_CENTRE)
        fco, ff = self._mesh(face_obj); bco, bf = self._mesh(back_obj)
        self.ear_faces = self._ear_faces(fco, ff)
        nf = len(fco); verts = fco + bco
        skin = ff + [[i+nf for i in f] for f in bf]
        noear = [f for i, f in enumerate(ff) if i not in self.ear_faces] + [[i+nf for i in f] for f in bf]
        ear = [f for i, f in enumerate(ff) if i in self.ear_faces]
        self.T_skin = BVHTree.FromPolygons(verts, skin, epsilon=0.0)
        self.T_noear = BVHTree.FromPolygons(verts, noear, epsilon=0.0)
        self.T_ear = BVHTree.FromPolygons(verts, ear, epsilon=0.0)
        self.T_cap0 = None
        if cap_obj is not None:
            hco, hf = self._mesh(cap_obj, material_index=1)
            self.T_cap0 = BVHTree.FromPolygons(hco, hf, epsilon=0.0)
        self._build_scalp(grid_deg)

    @staticmethod
    def _mesh(ob, material_index=None):
        m = ob.data; mw = ob.matrix_world
        co = [tuple(mw @ v.co) for v in m.vertices]
        faces = [list(p.vertices) for p in m.polygons if material_index is None or p.material_index == material_index]
        return co, faces

    @staticmethod
    def _ear_faces(co, faces):
        """Ear = small side islands of the face mesh below z 0.09 (FACE52 islands 8-37)."""
        import collections
        adj = collections.defaultdict(set)
        for f in faces:
            for a in f:
                adj[a].update(f)
        comp = [-1]*len(co); n = 0
        for s in range(len(co)):
            if comp[s] >= 0:
                continue
            st = [s]; comp[s] = n
            while st:
                v = st.pop()
                for w in adj[v]:
                    if comp[w] < 0:
                        comp[w] = n; st.append(w)
            n += 1
        a = np.array(co); ear_comps = set()
        for c in range(n):
            idx = [i for i in range(len(co)) if comp[i] == c]
            p = a[idx]
            if len(idx) < 40 and (p[:, 0].min() > 0.05 or p[:, 0].max() < -0.05) and p[:, 2].max() < 0.09:
                ear_comps.add(c)
        return {i for i, f in enumerate(faces) if comp[f[0]] in ear_comps}

    def _outer(self, T, d, maxr=0.5):
        d = Vector(d)
        loc, n, i, dist = T.ray_cast(self.C + d*maxr, -d, maxr)
        return (loc - self.C).length if loc is not None else float('nan')

    def r_skin(self, d):
        return self._outer(self.T_skin, d)

    def r_skin_noear(self, d):
        return self._outer(self.T_noear, d)

    def r_ear(self, d):
        return self._outer(self.T_ear, d)

    def r_cap0(self, d):
        return self._outer(self.T_cap0, d) if self.T_cap0 else float('nan')

    def _build_scalp(self, step):
        naz, nel = int(round(360/step)), int(round(180/step))
        self.g_az = (np.arange(naz) + 0.5)*step - 180.0
        self.g_el = (np.arange(nel) + 0.5)*step - 90.0
        AZ, EL = np.meshgrid(self.g_az, self.g_el)
        D = np.stack([azel_to_dir(a, e) for a, e in zip(AZ.ravel(), EL.ravel())]).reshape(nel, naz, 3)
        rs = np.array([[self.r_skin_noear(D[j, i]) for i in range(naz)] for j in range(nel)])
        self.g_skin_noear = rs
        skin = np.isfinite(rs)
        # neck/bottom: treat as skin-closed region (never needs hair); fill NaN below el -40 with nearest
        hole = (~skin) & (EL > -40)
        # --- base shape inside the hole: FACE52 cap (blurred) minus an assumed hair thickness.
        # The skin-minus-base residual is then filled harmonically, so the proxy meets the
        # skin exactly at the hole edge and follows the cap shape in the interior.
        from scipy.ndimage import gaussian_filter
        if self.T_cap0 is None:
            raise ValueError('HeadField needs the FACE52 cap for the skull proxy')
        cap = np.array([[self._outer(self.T_cap0, D[j, i]) for i in range(naz)] for j in range(nel)])
        self.g_cap0 = cap
        known = np.isfinite(cap)
        base = np.where(known, cap, np.nanmean(cap[known]))
        for _ in range(1500):         # fill cells outside the old cap (harmonic), keep known cap
            nb = self._nb(base); base = np.where(known, cap, nb)
        sig = 4.0/step
        base = gaussian_filter(np.pad(base, ((0, 0), (naz, naz)), mode='wrap'), sig)[:, naz:2*naz]
        self.CAP_THICKNESS_ASSUMED = 0.007
        base = base - self.CAP_THICKNESS_ASSUMED
        delta = np.where(skin, rs - base, 0.0)
        fixed = skin | (EL <= -40)
        delta[EL <= -40] = 0.0
        for _ in range(4000):           # Jacobi harmonic fill on the sphere grid (periodic in az)
            delta = np.where(fixed, delta, self._nb(delta))
        self.g_base = base
        self.g_scalp = np.where(skin, rs, base + delta)
        self.g_hole = hole
        # skin cover factor: 1 = skin under this direction (at least ~3 deg inside the skin),
        # 0 = open skull. Hair alpha may only fade where cover = 1, otherwise the head interior
        # shows through the semi-transparent hair.
        from scipy.ndimage import binary_erosion, gaussian_filter as gf
        core = binary_erosion(np.pad(skin, ((0, 0), (naz, naz)), mode='wrap'), iterations=int(round(3/step)))[:, naz:2*naz]
        self.g_cover = np.clip(gf(np.pad(core.astype(float), ((0, 0), (naz, naz)), mode='wrap'), 1.0/step)[:, naz:2*naz]*1.6 - 0.3, 0, 1)
        self.g_cover[EL <= -40] = 1.0

    def skin_cover(self, d):
        return np.clip(self.sample_grid(self.g_cover, np.asarray(d, float)), 0, 1)

    @staticmethod
    def _nb(a):
        return (np.roll(a, 1, 1) + np.roll(a, -1, 1) + np.vstack([a[:1], a[:-1]]) + np.vstack([a[1:], a[-1:]]))/4

    def _ray_ellipsoid(self, D):
        e = self.ellipsoid; s = np.array([e['a'], e['b'], e['c']]); c0 = np.array([0.0, e['cy'], e['cz']])
        o = (self.Cn - c0)/s; dd = D/s
        A = (dd*dd).sum(-1); Bq = 2*(dd*o).sum(-1); Cq = (o*o).sum() - 1
        return (-Bq + np.sqrt(np.maximum(Bq*Bq - 4*A*Cq, 0)))/(2*A)

    def sample_grid(self, grid, d):
        az, el = dir_to_azel(d)
        step = self.g_az[1] - self.g_az[0]
        x = (np.asarray(az) - self.g_az[0])/step; y = np.clip((np.asarray(el) - self.g_el[0])/step, 0, len(self.g_el)-1.0001)
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
        n = len(self.g_az)
        def g(yy, xx):
            return grid[yy, xx % n]
        return (g(y0, x0)*(1-fx)*(1-fy) + g(y0, x0+1)*fx*(1-fy) + g(y0+1, x0)*(1-fx)*fy + g(y0+1, x0+1)*fx*fy)

    def r_scalp(self, d):
        return float(self.sample_grid(self.g_scalp, np.asarray(d, float)))

    def point(self, d, r):
        return self.Cn + np.asarray(d, float)*r


def surface_normal(rfun, d, eps=0.03):
    """Outward normal of the radial surface P(d)=C+r(d)d by central differences (eps radians)."""
    d = np.asarray(d, float); d = d/np.linalg.norm(d)
    t1 = np.cross(d, [0, 0, 1.0]);
    if np.linalg.norm(t1) < 1e-6:
        t1 = np.cross(d, [1.0, 0, 0])
    t1 /= np.linalg.norm(t1); t2 = np.cross(d, t1)
    C = np.array(HEAD_CENTRE)
    def P(v):
        v = v/np.linalg.norm(v); return C + v*rfun(v)
    a = P(d + eps*t1) - P(d - eps*t1); b = P(d + eps*t2) - P(d - eps*t2)
    n = np.cross(a, b); n /= np.linalg.norm(n)
    return n if n @ d > 0 else -n


# ---------------------------------------------------------------- materials (glTF-importer layout)
def make_textured_material(name, image, blend='BLEND', roughness=0.9, extras=None):
    """Same node layout the glTF importer produced for FACE52 hair materials:
    BaseColor = image.rgb * vertexColor.rgb ; Alpha = image.a * vertexColor.a."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['IOR'].default_value = 1.45; bsdf.inputs['Specular IOR Level'].default_value = 0.1
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = image; tex.interpolation = 'Linear'
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    L = nt.links
    L.new(tex.outputs['Color'], mix.inputs['A_Color' if 'A_Color' in mix.inputs else 6])
    L.new(vc.outputs['Color'], mix.inputs['B_Color' if 'B_Color' in mix.inputs else 7])
    L.new(mix.outputs['Result_Color' if 'Result_Color' in mix.outputs else 2], bsdf.inputs['Base Color'])
    L.new(tex.outputs['Alpha'], mul.inputs[0]); L.new(vc.outputs['Alpha'], mul.inputs[1])
    if blend == 'OPAQUE':
        # FH54: the glTF exporter derives alphaMode from the node tree; an unlinked Alpha exports OPAQUE.
        nt.nodes.remove(mul); bsdf.inputs['Alpha'].default_value = 1.0
    else:
        L.new(mul.outputs[0], bsdf.inputs['Alpha'])
    L.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    m.blend_method = blend
    m.use_backface_culling = False; m.show_transparent_back = True
    for k, v in (extras or {}).items():
        m[k] = v
    return m


def load_packed_image(path, name, colorspace='sRGB'):
    img = bpy.data.images.load(str(path), check_existing=False); img.name = name
    img.colorspace_settings.name = colorspace; img.alpha_mode = 'STRAIGHT'
    img.pack()
    return img


def new_mesh_object(name, verts, faces, collection=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(map(float, v)) for v in verts], [], [list(map(int, f)) for f in faces])
    me.update(); ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def set_loop_attrs(me, uv_per_loop=None, col_per_loop=None, normal_per_loop=None):
    if uv_per_loop is not None:
        uvl = me.uv_layers.new(name='UVMap'); uvl.data.foreach_set('uv', np.asarray(uv_per_loop, np.float32).ravel())
    if col_per_loop is not None:
        ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
        ca.data.foreach_set('color', np.asarray(col_per_loop, np.float32).ravel())
    if normal_per_loop is not None:
        n = np.asarray(normal_per_loop, float); n /= np.linalg.norm(n, axis=1, keepdims=True)
        me.normals_split_custom_set([tuple(x) for x in n])
    me.update()


def save_blend(path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=False)


def export_glb(path, use_selection=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', export_extras=True, use_selection=use_selection)


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o)) + '\n')


def finish():
    """Successful end of a bpy script. The bpy 4.2.23 PyPI module can segfault during interpreter
    teardown (observed after all outputs were written), which would hide real results behind a
    non-zero exit code. Flush and exit 0 explicitly; genuine errors still raise before reaching here."""
    import sys as _s
    _s.stdout.flush(); _s.stderr.flush()
    os._exit(0)
