"""Behind-the-ear hairline check for H2 / H3 (the late FH54 fix: hairline moved below the corner of the FACE52 skin
opening at az +-125 deg, el -7 deg). Same camera, light, samples for every column:
  FH53 (extracted FH53 ZIP)  |  FH54 before the fix (optional, $FH54_PREFIX_BUILD)  |  FH54 final ($FH53_BUILD)
The two pre-fix combo GLBs are copied to build/models/superseded/ so the "before" renders stay reproducible.
Writes build/renders/BEHIND_EAR/*.png, build/qa/render_ledger_behind_ear.json and build/images/M07c_behind_ear.jpg."""
import sys, os, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
import fh53_common as fc, fh53_render as rr

REF = Path(os.environ['FH53_REFERENCE']); PRE = os.environ.get('FH54_PREFIX_BUILD')
OUT = fc.BUILD/'renders/BEHIND_EAR'; OUT.mkdir(parents=True, exist_ok=True)
C = np.array(fc.HEAD_CENTRE)


def shot(name, az, el, dist=0.45, r=0.07, scale=0.09):
    d = fc.azel_to_dir(az, el)
    return (name, tuple(C + dist*d), tuple(C + r*d), scale)


SHOTS = [shot('behind_ear_L', 128, -8), shot('behind_ear_R', -128, -8)]
HAIRS = ('H2', 'H3')


def sources():
    src = []
    for h in HAIRS:
        src.append(('FH53', h, REF/'models/combos'/f'TM_FH53_F0_{h}.glb'))
        if PRE:
            keep = fc.BUILD/'models/superseded'/f'TM_FH54_F0_{h}_before_behind_ear_fix.glb'
            keep.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(Path(PRE)/'models/combos'/f'TM_FH54_F0_{h}.glb', keep)
            src.append(('FH54pre', h, keep))
        src.append(('FH54', h, fc.BUILD/'models/combos'/f'TM_FH54_F0_{h}.glb'))
    return src


def main():
    ledger = []
    for gen, h, p in sources():
        bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(p))
        sc, cam, tg = rr.setup(384, 32)
        for png in rr.render_closeups(sc, cam, str(OUT/f'{gen}_F0_{h}'), SHOTS):
            ledger.append({'png': str(Path(png).relative_to(fc.BUILD)), 'png_sha256': fc.sha256(png), 'source': p.name, 'source_sha256': fc.sha256(p),
                           'blender': bpy.app.version_string, 'renderer': 'Cycles CPU', 'seed': 0, 'denoise': False, 'pixels': 384, 'samples': 32, 'lighting': 'studio'})
    fc.write_json(fc.BUILD/'qa/render_ledger_behind_ear.json', {'count': len(ledger), 'renders': ledger,
                  'note': 'FH54pre = output of the same FH54 pipeline before the H2/H3 behind-ear hairline change (kept in models/superseded/).'})
    import compose54 as cp
    gens = ['FH53'] + (['FH54pre'] if PRE else []) + ['FH54']
    names = {'FH53': 'FH53', 'FH54pre': 'FH54 修正前', 'FH54': 'FH54 最終'}
    rows = [[OUT/f'{g}_F0_{h}_behind_ear_{s}.png' for g in gens] for h in HAIRS for s in ('L', 'R')]
    labels = [[f'{h} 耳の後ろ{"（左）" if s == "L" else "（右）"}  {names[g]}' for g in gens] for h in HAIRS for s in ('L', 'R')]
    cell = 1080//len(gens)
    cp.grid(None, '耳の後ろの生え際（H2・H3、顔F0、同じカメラ・照明）', rows, len(gens), (cell, cell), 'M07c_behind_ear.jpg',
            note='修正前 = 生え際を頭蓋の開口の角より下へ移す前の、同じ手順の出力', cell_labels=labels)
    print('BEHIND_EAR', len(ledger))


if __name__ == '__main__':
    main()
    fc.finish()
