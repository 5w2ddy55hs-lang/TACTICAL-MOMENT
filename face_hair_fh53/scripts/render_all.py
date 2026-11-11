"""FH53 deliverable renders. Every image is rendered from an exported GLB imported into an EMPTY scene
(baseline: FACE52's original TM_FACE52_F0_H0.glb), with FACE52's review camera/lights (fh53_render).
Outputs: build/renders/<set>/*.png (raw) + build/images/*.jpg (sheets; pixels pasted, never synthesised)
         build/qa/render_ledger.json (PNG SHA256 <-> model SHA256 + settings)
"""
import sys, json, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import fh53_common as fc, fh53_render as rr, fh53_assemble as asm
from contact_sheet import sheet

OUT = fc.BUILD; RD = OUT/'renders'; IMG = OUT/'images'
LEDGER = []


def model_path(fid, hid):
    if (fid, hid) == ('F0', 'H0'):
        return fc.FACE52_GLB                                   # FACE52 original final GLB (baseline)
    return OUT/'models/combos'/f'TM_FH53_{fid}_{hid}.glb'


def label(fid, hid):
    return 'FACE52_orig' if (fid, hid) == ('F0', 'H0') else f'{fid}_{hid}'


def load(fid, hid):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    p = model_path(fid, hid); bpy.ops.import_scene.gltf(filepath=str(p))
    return p


def log(png, p, setname, size, samples, lighting):
    LEDGER.append({'set': setname, 'png': str(Path(png).relative_to(OUT)), 'png_sha256': fc.sha256(png), 'model': p.name,
                   'model_sha256': fc.sha256(p), 'blender': bpy.app.version_string, 'renderer': 'Cycles CPU', 'seed': 0,
                   'denoise': False, 'pixels': size, 'samples': samples, 'lighting': lighting, 'glTF_importer': True,
                   'real_game': False})


def seven(setname, combos):
    d = RD/setname; d.mkdir(parents=True, exist_ok=True)
    for fid, hid in combos:
        p = load(fid, hid); sc, cam, tg = rr.setup(256, 8)
        for png in rr.render_views(sc, cam, tg, str(d/label(fid, hid))):
            log(png, p, setname, 256, 8, 'studio')
    rows = [label(f, h) for f, h in combos]; cols = [v[0] for v in rr.VIEWS]
    sheet(rows, cols, lambda r, c: d/f'{r}_{c}.png', IMG/f'{setname}.jpg', cell=256, col_labels=cols)


def closeups(setname, combos):
    d = RD/setname; d.mkdir(parents=True, exist_ok=True)
    for fid, hid in combos:
        for light in ('studio', 'grazing'):
            p = load(fid, hid); sc, cam, tg = rr.setup(512, 32)
            if light == 'grazing':
                rr.grazing(sc, tg)
            for png in rr.render_closeups(sc, cam, str(d/f'{label(fid, hid)}_{light}')):
                log(png, p, setname, 512, 32, light)
    for light in ('studio', 'grazing'):
        rows = [label(f, h) for f, h in combos]; cols = [c[0] for c in rr.CLOSEUPS]
        sheet(rows, cols, lambda r, c, l=light: d/f'{r}_{l}_{c}.png', IMG/f'{setname}_{light}.jpg', cell=320, col_labels=cols)


def combos_grid():
    d = RD/'combos'; d.mkdir(parents=True, exist_ok=True)
    allc = list(itertools.product(asm.FACES, asm.HAIRS))
    for fid, hid in allc:
        p = load(fid, hid); sc, cam, tg = rr.setup(256, 8)
        for png in rr.render_views(sc, cam, tg, str(d/label(fid, hid)), [v for v in rr.VIEWS if v[0] in ('front', 'quarter_R', 'side_L')]):
            log(png, p, 'combos', 256, 8, 'studio')
    for view in ('front', 'quarter_R', 'side_L'):
        sheet(list(asm.FACES), list(asm.HAIRS), lambda f, h, v=view: d/f'{label(f, h)}_{v}.png', IMG/f'COMBOS_{view}.jpg', cell=256,
              label_fn=lambda f: f'{asm.FACES[f]}  ({view}; columns = ' + ' / '.join(asm.HAIRS.values()) + ')', col_labels=list(asm.HAIRS.values()))


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    seven('SEVEN_hair_on_F0', [('F0', h) for h in asm.HAIRS])
    seven('SEVEN_face_with_H0', [(f, 'H0') for f in asm.FACES])
    closeups('CLOSEUPS_hair_on_F0', [('F0', h) for h in asm.HAIRS])
    combos_grid()
    fc.write_json(OUT/'qa/render_ledger.json', {'renders': LEDGER, 'count': len(LEDGER),
                  'note': 'Static camera renders of imported GLBs. Not a real-game, animation, transparency-sorting or temporal test.'})
    print('RENDERS', len(LEDGER))


if __name__ == '__main__':
    main()
    fc.finish()
