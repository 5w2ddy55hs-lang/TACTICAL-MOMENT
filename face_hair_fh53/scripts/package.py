"""FH53 packaging + extraction test.

1. Stage build outputs + scripts + docs, write SHA256SUMS.txt and INPUT_SHA256.txt, zip to build/dist/.
2. Extract the ZIP into a NEW empty folder; from the extracted copy:
   - verify every SHA256 in SHA256SUMS.txt,
   - open every .blend in a fresh Blender session (images: packed/loaded/missing),
   - import every .glb into an empty scene (mesh/material/image counts, triangle count vs GLB JSON).
3. Write build/dist/PACKAGE_VERIFICATION.json (outside the ZIP it describes).
Usage: python package.py
"""
import sys, os, json, shutil, zipfile, hashlib, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import fh53_common as fc, glb_io

ROOT = Path(__file__).resolve().parents[1]
NAME = 'TM_FH53_FACE_HAIR_CANDIDATES_20261106'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def stage(dst):
    B = fc.BUILD
    for sub in ('models', 'textures', 'images', 'renders', 'qa', 'logs'):
        shutil.copytree(B/sub, dst/sub)
    shutil.copytree(ROOT/'scripts', dst/'scripts', ignore=shutil.ignore_patterns('__pycache__'))
    for f in ('README_JA.md', 'REPORT_JA.md'):
        shutil.copy2(ROOT/f, dst/f)
    inp = fc.check_inputs(('FACE52_BLEND', 'FACE52_GLB', 'FACE52_RAW', 'REF04_BLEND', 'REF04_GLB'))
    lines = ['# Inputs used (not redistributed in this ZIP; restore them with the handoff prepare_inputs.py)']
    for k, v in inp.items():
        lines.append(f"{v['sha256']}  {k}  {Path(v['path']).name}")
    man = fc.INPUTS.parent/'INPUT_MANIFEST.json'
    (dst/'INPUT_SHA256.txt').write_text('\n'.join(lines) + '\n')
    rows = []
    for p in sorted(dst.rglob('*')):
        if p.is_file() and p.name != 'SHA256SUMS.txt':
            rows.append(f'{sha(p)}  {p.relative_to(dst).as_posix()}')
    (dst/'SHA256SUMS.txt').write_text('\n'.join(rows) + '\n')
    return len(rows)


def verify_extracted(zpath, workdir):
    ex = workdir/'extracted'; ex.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            target = (ex/info.filename).resolve()
            assert target.is_relative_to(ex.resolve())
        z.extractall(ex)
    root = ex/NAME
    res = {'extracted_to_new_empty_folder': True, 'sha_mismatch': [], 'sha_checked': 0, 'blends': {}, 'glbs': {}}
    for line in (root/'SHA256SUMS.txt').read_text().splitlines():
        h, rel = line.split('  ', 1); res['sha_checked'] += 1
        if sha(root/rel) != h:
            res['sha_mismatch'].append(rel)
    for p in sorted(root.rglob('*.blend')):
        bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.wm.open_mainfile(filepath=str(p))
        imgs = []
        for im in bpy.data.images:
            if im.users == 0:
                continue
            try:
                _ = im.pixels[0]; ok = bool(im.has_data)
            except Exception:
                ok = False
            imgs.append({'name': im.name, 'packed': im.packed_file is not None, 'loaded': ok})
        res['blends'][p.relative_to(root).as_posix()] = {'opened': True, 'blender': bpy.app.version_string, 'objects': len(bpy.data.objects),
                                                          'images': len(imgs), 'not_packed': sum(not i['packed'] for i in imgs),
                                                          'not_loaded': sum(not i['loaded'] for i in imgs)}
    for p in sorted(root.rglob('*.glb')):
        bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(p))
        tris = 0
        for ob in bpy.context.scene.objects:
            if ob.type == 'MESH':
                ob.data.calc_loop_triangles(); tris += len(ob.data.loop_triangles)
        st = glb_io.stats(p)
        res['glbs'][p.relative_to(root).as_posix()] = {'imported': True, 'mesh_objects': sum(o.type == 'MESH' for o in bpy.context.scene.objects),
                                                        'materials': len([m for m in bpy.data.materials if m.users]),
                                                        'images': len([i for i in bpy.data.images if i.users]),
                                                        'triangles_imported': tris, 'triangles_in_glb': st['triangles'], 'match': tris == st['triangles']}
    res['all_ok'] = (not res['sha_mismatch'] and all(v['not_loaded'] == 0 and v['not_packed'] == 0 for v in res['blends'].values())
                     and all(v['match'] for v in res['glbs'].values()))
    return res


def main():
    dist = fc.BUILD/'dist'; dist.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='fh53_stage_', dir=str(fc.BUILD)))
    dst = tmp/NAME; dst.mkdir()
    n = stage(dst)
    zpath = dist/f'{NAME}.zip'
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(dst.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(tmp).as_posix())
    shutil.rmtree(tmp)
    work = Path(tempfile.mkdtemp(prefix='fh53_unzip_test_', dir=str(fc.BUILD)))
    t0 = time.time(); res = verify_extracted(zpath, work); res['seconds'] = round(time.time() - t0, 1)
    shutil.rmtree(work)
    res.update({'zip': zpath.name, 'zip_bytes': zpath.stat().st_size, 'zip_sha256': sha(zpath), 'files_in_zip': n + 1})
    fc.write_json(dist/'PACKAGE_VERIFICATION.json', res)
    print(json.dumps({k: res[k] for k in ('zip', 'zip_bytes', 'zip_sha256', 'files_in_zip', 'sha_checked', 'sha_mismatch', 'all_ok', 'seconds')}, indent=1))
    print('blends', len(res['blends']), 'glbs', len(res['glbs']))


if __name__ == '__main__':
    main()
    fc.finish()
