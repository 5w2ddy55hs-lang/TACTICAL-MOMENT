"""Assemble a head from one face module and one hair module (both in the FACE52 head frame).

Face module ids: F0 = FACE52 face+back-scalp (unchanged, read from the FACE52 native .blend),
                 F1..F3 = TM_FH53_F*.blend.
Hair module ids: H0 = FACE52 REF09_Hair (unchanged), H1..H4 = TM_FH53_H*.blend.
"""
import sys
from pathlib import Path
import bpy
import fh53_common as fc

FACES = {'F0': 'F0_FACE52', 'F1': 'F1_LONG_ANGULAR', 'F2': 'F2_ROUND_SOFT', 'F3': 'F3_NARROW_SHARP'}
HAIRS = {'H0': 'H0_FACE52', 'H1': 'H1_STANDARD_REBUILT', 'H2': 'H2_SHORT_CROP', 'H3': 'H3_SWEPT_BACK', 'H4': 'H4_SIDE_SWEPT_FRINGE'}


def module_file(kind, mid, build=None):
    build = Path(build or fc.BUILD)
    if mid in ('F0', 'H0'):
        return fc.FACE52_BLEND
    label = FACES[mid] if kind == 'face' else HAIRS[mid]
    return build/'models'/kind/f'TM_FH53_{label}.blend'


def append_objects(path, names):
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        missing = [n for n in names if n not in src.objects]
        if missing:
            raise KeyError(f'{path.name}: missing objects {missing}')
        dst.objects = list(names)
    obs = []
    for ob in dst.objects:
        bpy.context.scene.collection.objects.link(ob); obs.append(ob)
    return obs


def assemble(face_id, hair_id, build=None, empty=True):
    if empty:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    fobs = append_objects(module_file('face', face_id, build), [fc.FACE_OBJ, fc.BACK_OBJ])
    hobs = append_objects(module_file('hair', hair_id, build), [fc.HAIR_OBJ])
    for ob in fobs + hobs:
        assert tuple(ob.location) == (0, 0, 0) and tuple(ob.rotation_euler) == (0, 0, 0) and tuple(ob.scale) == (1, 1, 1)
    sc = bpy.context.scene
    sc['fh53_combo'] = f'{FACES[face_id]} x {HAIRS[hair_id]}'
    sc['fh53_status'] = 'RESEARCH COMBINATION. Static head only: no rig, no weights, no neck join, not approved.'
    return fobs, hobs
