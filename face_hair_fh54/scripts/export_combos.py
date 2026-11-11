"""FH54 (from FH53): export every face x hair combination as a head GLB, and build the module library .blend.

H0 combinations: plain Blender export, then FACE52's canonical cap primitive (taken byte-for-byte
from TM_FACE52_F0_H0.glb, identical-position check first) replaces the exported cap - the same
finishing step FACE52 used. New hairs H1-H4 have a new scalp shape: plain export only.
Usage: python export_combos.py
"""
import sys, json, time, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import fh53_common as fc, fh53_assemble as asm, glb_io


def main():
    out = fc.BUILD; inputs = fc.check_inputs(); log = {'blender': bpy.app.version_string, 'inputs': inputs, 'combos': {}}
    for fid, hid in itertools.product(asm.FACES, asm.HAIRS):
        t0 = time.time()
        asm.assemble(fid, hid)
        name = f'TM_FH54_{fid}_{hid}'
        glb = out/'models/combos'/(name + '.glb'); raw = glb.with_name(name + '_RAW.glb')
        fc.export_glb(raw if hid == 'H0' else glb)
        rec = {'face': asm.FACES[fid], 'hair': asm.HAIRS[hid],
               'face_source': asm.module_file('face', fid).name, 'hair_source': asm.module_file('hair', hid).name}
        if hid == 'H0':
            rec['canonical_cap'] = glb_io.graft_primitive(raw, fc.FACE52_GLB, fc.HAIR_OBJ, 'TM18_HairCap_Detail', glb)
            rec['raw_sha256'] = fc.sha256(raw); raw.unlink()
            rec['export'] = 'Blender glTF export + FACE52 canonical cap primitive grafted (positions verified identical)'
        else:
            rec['export'] = 'plain Blender glTF export'
        rec['glb'] = glb.name; rec['glb_sha256'] = fc.sha256(glb); rec['seconds'] = round(time.time()-t0, 2)
        log['combos'][f'{fid}_{hid}'] = rec
        print('COMBO', fid, hid, rec.get('canonical_cap', ''), flush=True)
    # ---- library .blend: every module in its own collection (F1 + H1 visible by default)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; root = sc.collection
    for kind, table, objs in (('face', asm.FACES, [fc.FACE_OBJ, fc.BACK_OBJ]), ('hair', asm.HAIRS, [fc.HAIR_OBJ])):
        for mid, label in table.items():
            coll = bpy.data.collections.new(f'{"FACE" if kind == "face" else "HAIR"}_{label}'); root.children.link(coll)
            with bpy.data.libraries.load(str(asm.module_file(kind, mid)), link=False) as (src, dst):
                dst.objects = list(objs)
            for ob in dst.objects:
                coll.objects.link(ob); ob.name = f'{mid}__{ob.name.split(".")[0]}'
            visible = mid in ('F1', 'H1')
            coll.hide_render = not visible; coll.hide_viewport = not visible
    sc['fh53_role'] = 'Module library: one collection per face/hair module, all in the FACE52 head frame (identity transforms). Show exactly one FACE_* and one HAIR_* collection.'
    sc['fh53_status'] = 'RESEARCH CANDIDATES. Not approved, not production, no rights clearance.'
    lib = out/'models/TM_FH54_LIBRARY_faces_hairs.blend'; fc.save_blend(lib)
    log['library'] = {'blend': lib.name, 'sha256': fc.sha256(lib), 'collections': [c.name for c in bpy.data.collections]}
    fc.write_json(out/'qa/export_combos.json', log)


if __name__ == '__main__':
    main()
    fc.finish()
