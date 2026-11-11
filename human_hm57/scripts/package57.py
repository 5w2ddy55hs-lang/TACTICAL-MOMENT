"""HM57 packaging + extraction test.
1. Stage the build outputs, scripts and docs; write SHA256SUMS.txt; zip to $HM_BUILD/dist/.
   The main ZIP holds only original work (HM56 / HM57 / LITE renders); the staging step refuses anything under
   renders/RESEARCH_PRIVATE or named *_PRIVATE. The research side-by-side sheets go to a SEPARATE private ZIP
   (..._RESEARCH_COMPARISON_NOT_FOR_RELEASE.zip) that is never published. video/frames/ (raw PNG frames) is left out.
2. Extract the ZIP into a NEW empty folder; from the extracted copy verify every SHA256, open every .blend
   (packed images) and import every .glb into an empty scene (triangles vs GLB JSON, skin joints, animations).
3. Write $HM_BUILD/dist/PACKAGE_VERIFICATION.json (outside the ZIP it describes)."""
import sys, os, json, shutil, zipfile, hashlib, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import hm_common as hc, glb_info

ROOT = Path(__file__).resolve().parents[1]; NAME = 'TM_HM57_MATCH_PLAYER_20261111'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
PRIVATE_MARKS = ('RESEARCH_PRIVATE', 'Sakatsuku', 'Reference04', 'REF_', 'HM_RESEARCH_REF')


def stage(dst):
    B = hc.BUILD
    for sub in ('models', 'textures', 'qa', 'logs', 'images'):
        shutil.copytree(B/sub, dst/sub)
    shutil.copytree(B/'renders', dst/'renders', ignore=shutil.ignore_patterns('RESEARCH_PRIVATE', '*_PRIVATE*'))
    bad = [str(p.relative_to(dst)) for p in dst.rglob('*') if 'PRIVATE' in p.name or p.name.startswith('REF_') or 'RESEARCH' in p.name]
    assert not bad, f'research comparison material must not be in the main ZIP: {bad[:5]}'
    for lg in (dst/'logs').glob('*.log'):                 # the compare log mentions the private reference renders: drop those lines
        lg.write_text(''.join(l for l in lg.read_text(errors='replace').splitlines(True) if not any(k in l for k in PRIVATE_MARKS)))
    shutil.copytree(B/'video', dst/'video', ignore=shutil.ignore_patterns('frames'))
    if (B/'webtest/out').exists():
        wt = dst/'webtest'; wt.mkdir()
        for f in ('index.html', 'webtest57_run.mjs', 'three_version.json'):
            if (B/'webtest'/f).exists():
                shutil.copy2(B/'webtest'/f, wt/f)
        shutil.copytree(B/'webtest/out', wt/'out', ignore=shutil.ignore_patterns('play'))
    shutil.copytree(ROOT/'scripts', dst/'scripts', ignore=shutil.ignore_patterns('__pycache__', 'dev_*'))
    for f in ('README_JA.md', 'REPORT_JA.md', 'INTEGRATION_JA.md'):
        shutil.copy2(ROOT/f, dst/f)
    rows = [f'{sha(p)}  {p.relative_to(dst).as_posix()}' for p in sorted(dst.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS.txt']
    (dst/'SHA256SUMS.txt').write_text('\n'.join(rows) + '\n'); return len(rows)


def verify_extracted(zpath, workdir):
    ex = workdir/'extracted'; ex.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            assert (ex/info.filename).resolve().is_relative_to(ex.resolve())
        z.extractall(ex)
    root = ex/NAME; res = {'extracted_to_new_empty_folder': True, 'sha_mismatch': [], 'sha_checked': 0, 'blends': {}, 'glbs': {}}
    for line in (root/'SHA256SUMS.txt').read_text().splitlines():
        h, rel = line.split('  ', 1); res['sha_checked'] += 1
        if sha(root/rel) != h:
            res['sha_mismatch'].append(rel)
    for p in sorted(root.rglob('*.blend')):
        bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.wm.open_mainfile(filepath=str(p)); imgs = []
        for im in bpy.data.images:
            if im.users == 0:
                continue
            try:
                _ = im.pixels[0]; ok = bool(im.has_data)
            except Exception:
                ok = False
            imgs.append({'packed': im.packed_file is not None, 'loaded': ok})
        res['blends'][p.relative_to(root).as_posix()] = {'opened': True, 'blender': bpy.app.version_string, 'objects': len(bpy.data.objects), 'armatures': len(bpy.data.armatures), 'actions': len(bpy.data.actions),
                                                          'images': len(imgs), 'not_packed': sum(not i['packed'] for i in imgs), 'not_loaded': sum(not i['loaded'] for i in imgs)}
    for p in sorted(root.rglob('*.glb')):
        bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(p)); tris = 0
        for ob in [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.vertex_groups]:
            ob.data.calc_loop_triangles(); tris += len(ob.data.loop_triangles)
        st = glb_info.info(p); arm = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
        res['glbs'][p.relative_to(root).as_posix()] = {'imported': True, 'triangles_imported': tris, 'triangles_in_glb': st['triangles'], 'match': tris == st['triangles'], 'bones': len(arm[0].data.bones) if arm else 0,
                                                        'joints_in_glb': st['skins'][0]['joints'] if st['skins'] else 0, 'animations_in_glb': len(st['animations']), 'actions_imported': len(bpy.data.actions),
                                                        'images': len([i for i in bpy.data.images if i.users])}
    res['all_ok'] = (not res['sha_mismatch'] and all(v['not_loaded'] == 0 and v['not_packed'] == 0 for v in res['blends'].values())
                     and all(v['match'] and v['bones'] == v['joints_in_glb'] and v['actions_imported'] == v['animations_in_glb'] for v in res['glbs'].values()))
    return res


def main():
    dist = hc.BUILD/'dist'; dist.mkdir(exist_ok=True); tmp = Path(tempfile.mkdtemp(prefix='hm57_stage_', dir=str(hc.BUILD))); dst = tmp/NAME; dst.mkdir(); n = stage(dst)
    zpath = dist/f'{NAME}.zip'
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(dst.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(tmp).as_posix())
    shutil.rmtree(tmp); work = Path(tempfile.mkdtemp(prefix='hm57_unzip_test_', dir=str(hc.BUILD)))
    t0 = time.time(); res = verify_extracted(zpath, work); res['seconds'] = round(time.time() - t0, 1); shutil.rmtree(work)
    res.update({'zip': zpath.name, 'zip_bytes': zpath.stat().st_size, 'zip_sha256': sha(zpath), 'files_in_zip': n + 1}); hc.write_json(dist/'PACKAGE_VERIFICATION.json', res)
    rp = hc.BUILD/'renders/RESEARCH_PRIVATE'
    if rp.exists():                                       # private review ZIP (research reference side by side) - not for release
        pz = dist/f'{NAME}_RESEARCH_COMPARISON_NOT_FOR_RELEASE.zip'
        with zipfile.ZipFile(pz, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('README_NOT_FOR_RELEASE.txt', 'この ZIP の画像には研究用の参照モデル（ゲーム由来・公開不可）が写っています。比較確認のためだけのものです。公開物に含めないでください。\n'.encode('utf-8'))
            for p in sorted(rp.rglob('*')):
                if p.is_file():
                    z.write(p, p.relative_to(rp).as_posix())
        res['private_zip'] = {'name': pz.name, 'bytes': pz.stat().st_size, 'sha256': sha(pz)}; hc.write_json(dist/'PACKAGE_VERIFICATION.json', res)
    print(json.dumps({k: res[k] for k in ('zip', 'zip_bytes', 'zip_sha256', 'files_in_zip', 'sha_checked', 'sha_mismatch', 'all_ok', 'seconds')}, indent=1)); print('blends', len(res['blends']), 'glbs', len(res['glbs']))


if __name__ == '__main__':
    main(); hc.finish()
