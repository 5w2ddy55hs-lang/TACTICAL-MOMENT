"""HM55 packaging + extraction test.
1. Stage the build outputs, scripts and docs; write SHA256SUMS.txt; zip to $HM_BUILD/dist/.
   Images that show the research reference model (source-derived, not releasable) are kept apart in
   review_research_comparison_NOT_FOR_RELEASE/. models/ and textures/ contain HM55 originals only.
2. Extract the ZIP into a NEW empty folder; from the extracted copy verify every SHA256, open every .blend
   (packed images) and import every .glb into an empty scene (triangles vs GLB JSON, skin joints, animations).
3. Write $HM_BUILD/dist/PACKAGE_VERIFICATION.json (outside the ZIP it describes)."""
import sys, os, json, shutil, zipfile, hashlib, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import hm_common as hc, glb_info

ROOT = Path(__file__).resolve().parents[1]; NAME = 'TM_HM55_HUMAN_MODEL_20261111'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
RESEARCH_IMAGES = ('M07_', 'M07b_')


def stage(dst):
    B = hc.BUILD
    for sub in ('models', 'textures', 'qa', 'logs'):
        shutil.copytree(B/sub, dst/sub)
    (dst/'images').mkdir(); res = dst/'review_research_comparison_NOT_FOR_RELEASE'; res.mkdir()
    for p in sorted((B/'images').glob('*.jpg')):
        shutil.copy2(p, (res if p.name.startswith(RESEARCH_IMAGES) else dst/'images')/p.name)
    for d in sorted((B/'renders').iterdir()):
        shutil.copytree(d, (res/'renders_REFERENCE' if d.name == 'REFERENCE' else dst/'renders'/d.name))
    (res/'README_JA.txt').write_text('このフォルダの画像には、研究用の参照モデル（Reference04 と FH54。ゲーム由来で公開・商用利用できません）が写っています。\n比較確認のためだけに入れています。公開物に含めないでください。\n', encoding='utf-8')
    if (B/'webtest/out').exists():
        wt = dst/'webtest'; wt.mkdir()
        for f in ('index.html', 'webtest55_run.mjs'):
            if (B/'webtest'/f).exists():
                shutil.copy2(B/'webtest'/f, wt/f)
        shutil.copytree(B/'webtest/out', wt/'out')
    shutil.copytree(ROOT/'scripts', dst/'scripts', ignore=shutil.ignore_patterns('__pycache__', 'dev_*'))
    for f in ('README_JA.md', 'REPORT_JA.md'):
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
    dist = hc.BUILD/'dist'; dist.mkdir(exist_ok=True); tmp = Path(tempfile.mkdtemp(prefix='hm55_stage_', dir=str(hc.BUILD))); dst = tmp/NAME; dst.mkdir(); n = stage(dst)
    zpath = dist/f'{NAME}.zip'
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(dst.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(tmp).as_posix())
    shutil.rmtree(tmp); work = Path(tempfile.mkdtemp(prefix='hm55_unzip_test_', dir=str(hc.BUILD)))
    t0 = time.time(); res = verify_extracted(zpath, work); res['seconds'] = round(time.time() - t0, 1); shutil.rmtree(work)
    res.update({'zip': zpath.name, 'zip_bytes': zpath.stat().st_size, 'zip_sha256': sha(zpath), 'files_in_zip': n + 1}); hc.write_json(dist/'PACKAGE_VERIFICATION.json', res)
    print(json.dumps({k: res[k] for k in ('zip', 'zip_bytes', 'zip_sha256', 'files_in_zip', 'sha_checked', 'sha_mismatch', 'all_ok', 'seconds')}, indent=1)); print('blends', len(res['blends']), 'glbs', len(res['glbs']))


if __name__ == '__main__':
    main(); hc.finish()
