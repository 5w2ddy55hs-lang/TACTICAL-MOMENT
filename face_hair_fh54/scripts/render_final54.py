"""FH54 deliverable renders (FACE52 review camera/lights, Cycles CPU seed 0, no denoise).
GLB-based sets import the exported GLB into an EMPTY scene. The face breakdown (shape-only / texture-only /
both) uses the module .blend files (S/T variants are comparison modules without combo GLBs).
Writes build/renders/<set>/*.png and build/qa/render_ledger54.json."""
import sys, os, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import fh53_common as fc, fh53_render as rr, fh53_assemble as asm

OUT = fc.BUILD/'renders'; REF = Path(os.environ['FH53_REFERENCE'])
LEDGER = []


def glb(tag):
    if tag == 'FACE52':
        return fc.FACE52_GLB
    gen, combo = tag.split(':')
    return (REF if gen == 'FH53' else fc.BUILD)/'models/combos'/f'TM_{gen}_{combo}.glb'


def load(p):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(p))


def log(png, src, setname, px, samples, light):
    LEDGER.append({'set': setname, 'png': str(Path(png).relative_to(fc.BUILD)), 'png_sha256': fc.sha256(png), 'source': Path(src).name,
                   'source_sha256': fc.sha256(src), 'blender': bpy.app.version_string, 'renderer': 'Cycles CPU', 'seed': 0,
                   'denoise': False, 'pixels': px, 'samples': samples, 'lighting': light})


def label(tag):
    return tag.replace(':', '_')


def seven(setname, tags):
    d = OUT/setname; d.mkdir(parents=True, exist_ok=True)
    for t in tags:
        p = glb(t); load(p); sc, cam, tg = rr.setup(256, 8)
        for png in rr.render_views(sc, cam, tg, str(d/label(t))):
            log(png, p, setname, 256, 8, 'studio')


def closeups(setname, tags):
    d = OUT/setname; d.mkdir(parents=True, exist_ok=True)
    for t in tags:
        for light in ('studio', 'grazing'):
            p = glb(t); load(p); sc, cam, tg = rr.setup(512, 32)
            if light == 'grazing':
                rr.grazing(sc, tg)
            for png in rr.render_closeups(sc, cam, str(d/f'{label(t)}_{light}')):
                log(png, p, setname, 512, 32, light)


def small(setname, tags):
    d = OUT/setname; d.mkdir(parents=True, exist_ok=True)
    for t in tags:
        p = glb(t)
        for px in (64, 96, 128):
            load(p); sc, cam, tg = rr.setup(px, 16)
            for png in rr.render_views(sc, cam, tg, str(d/f'{label(t)}_{px}px'), [v for v in rr.VIEWS if v[0] in ('front', 'quarter_R')]):
                log(png, p, setname, px, 16, 'studio')


def combos():
    d = OUT/'COMBOS'; d.mkdir(parents=True, exist_ok=True)
    for f, h in itertools.product(asm.FACES, asm.HAIRS):
        t = f'FH54:{f}_{h}'; p = glb(t); load(p); sc, cam, tg = rr.setup(256, 8)
        for png in rr.render_views(sc, cam, tg, str(d/label(t)), [v for v in rr.VIEWS if v[0] in ('front', 'quarter_R', 'side_L', 'back')]):
            log(png, p, 'COMBOS', 256, 8, 'studio')


def breakdown():
    d = OUT/'FACE_BREAKDOWN'; d.mkdir(parents=True, exist_ok=True)
    SH = [('face_front', (0, -.6, .04), (0, 0, .04), .16), ('face_quarterR', (.42, -.42, .05), (0, 0, .04), .16),
          ('face_quarterL', (-.42, -.42, .05), (0, 0, .04), .16), ('face_sideR', (.6, 0, .04), (0, 0, .04), .17)]
    for fid in ['F0', 'F1S', 'F1T', 'F1', 'F2S', 'F2T', 'F2', 'F3S', 'F3T', 'F3']:
        for hid in ('H0', 'H2'):
            asm.assemble(fid, hid); sc, cam, tg = rr.setup(384, 16)
            src = asm.module_file('face', fid)
            for png in rr.render_closeups(sc, cam, str(d/f'{fid}_{hid}'), SH):
                log(png, src, 'FACE_BREAKDOWN', 384, 16, 'studio')


def main():
    seven('SEVEN_faces', ['FACE52', 'FH54:F1_H0', 'FH54:F2_H0', 'FH54:F3_H0', 'FH53:F1_H0', 'FH53:F2_H0', 'FH53:F3_H0'])
    seven('SEVEN_hairs', ['FACE52'] + [f'{g}:F0_{h}' for h in ('H1', 'H2', 'H3', 'H4') for g in ('FH53', 'FH54')])
    closeups('CLOSEUPS', ['FACE52'] + [f'{g}:F0_{h}' for h in ('H1', 'H2', 'H3', 'H4') for g in ('FH53', 'FH54')] + ['FH54:F2_H2', 'FH54:F3_H3'])
    small('SMALL', ['FACE52', 'FH54:F1_H0', 'FH54:F2_H0', 'FH54:F3_H0', 'FH54:F1_H1', 'FH54:F2_H2', 'FH54:F3_H3', 'FH54:F1_H4', 'FH53:F1_H0', 'FH53:F2_H0', 'FH53:F3_H0'])
    combos()
    breakdown()
    fc.write_json(fc.BUILD/'qa/render_ledger54.json', {'count': len(LEDGER), 'renders': LEDGER,
                  'note': 'Static renders. Not a real-game, transparency-sorting, temporal or device test.'})
    print('RENDERS', len(LEDGER))


if __name__ == '__main__':
    main()
    fc.finish()
