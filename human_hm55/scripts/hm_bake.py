"""Ambient-occlusion bake of the model's own geometry (Cycles) and compositing into the painted textures."""
import numpy as np
import bpy


def bake_ao(ob, slot_sizes, samples=32, distance=0.20, margin=6):
    """slot_sizes: {material slot index: texture size}. Returns {slot: (H, W) float array, row 0 = top (v = 1)}.
    The object's materials are replaced temporarily and restored afterwards."""
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples; sc.cycles.seed = 0; sc.cycles.use_denoising = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new('HM_BakeWorld')
    sc.world.light_settings.distance = distance
    keep = [s.material for s in ob.material_slots]; imgs = {}
    for i, s in enumerate(ob.material_slots):
        m = bpy.data.materials.new('HM_bake_tmp'); m.use_nodes = True; n = m.node_tree.nodes.new('ShaderNodeTexImage')
        size = slot_sizes.get(i, 64); img = bpy.data.images.new('HM_bake_%d' % i, size, size, alpha=False, float_buffer=True); n.image = img
        m.node_tree.nodes.active = n; n.select = True; s.material = m; imgs[i] = img
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type='AO', margin=margin, use_clear=True)
    out = {}
    for i, img in imgs.items():
        if i in slot_sizes:
            a = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)[::-1, :, 0]; out[i] = a.copy()
    for s, m in zip(ob.material_slots, keep):
        tmp = s.material; s.material = m; bpy.data.materials.remove(tmp)
    for img in imgs.values():
        bpy.data.images.remove(img)
    ob.select_set(False)
    return out


def apply_ao(rgb, ao, strength=0.75, tint=(1.0, 0.93, 0.90), gamma=1.0, mask=None, blur=0.0, limit=None):
    """Darken by occlusion; the occluded part is tinted (warm for skin, neutral when tint = 1,1,1).
    blur (pixels) removes the facet steps of the low-poly bake; limit = per-texel cap of the occlusion (0..1)."""
    if blur > 0:
        from scipy.ndimage import gaussian_filter
        m = np.ones(ao.shape) if mask is None else mask.astype(float)
        ao = gaussian_filter(ao*m, blur)/np.maximum(gaussian_filter(m, blur), 1e-6)
    occ = np.clip(1 - ao, 0, 1)**gamma*strength; t = np.array(tint, float)
    if limit is not None:
        occ = np.minimum(occ, limit)
    return rgb*(1 - occ[..., None]*(1 - 0.0*t)) * (1 - occ[..., None]*(1 - t)*0.6)
