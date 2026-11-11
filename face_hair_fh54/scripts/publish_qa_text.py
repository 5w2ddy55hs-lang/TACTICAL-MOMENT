"""Copy the text-only QA record (Markdown / JSON / logs / SHA lists) from build/ into face_hair_fh54/qa/ for git.
No models, images or textures are copied. Local absolute paths are replaced by placeholders, and Cycles progress
lines ("Fra:...") are dropped from logs. Usage: FH53_BUILD=... [other FH53_* vars] python publish_qa_text.py <dest>"""
import os, sys, re, json, zipfile
from pathlib import Path

build = Path(os.environ['FH53_BUILD']).resolve()
dest = Path(sys.argv[1]).resolve(); dest.mkdir(parents=True, exist_ok=True)
subs = []
for var in ('FH53_REFERENCE', 'FH53_REF04', 'FH53_INPUTS', 'FH53_BUILD', 'FH54_PREFIX_BUILD', 'THREE_DIR', 'PW_NODE_MODULES', 'VALIDATOR_NODE_MODULES'):
    if os.environ.get(var):
        subs.append((str(Path(os.environ[var]).resolve()), '<' + var + '>'))
repo = Path(__file__).resolve().parents[2]
subs += [(str(repo), '<REPO>'), ('/tmp/claude-0', '<TMP>'), ('/root', '<HOME>')]
subs.sort(key=lambda s: -len(s[0]))


def clean(text):
    for a, b in subs:
        text = text.replace(a, b)
    return text


TEXT = {'.md', '.json', '.txt', '.log', '.csv'}
copied = []
for src in sorted((build/'qa').iterdir()):
    if src.is_file() and src.suffix in TEXT:
        (dest/src.name).write_text(clean(src.read_text(errors='replace'))); copied.append('qa/' + src.name)
(dest/'logs').mkdir(exist_ok=True)
for src in sorted((build/'logs').glob('*.log')):
    lines = [l for l in src.read_text(errors='replace').splitlines() if not re.match(r'^\s*Fra:\d+', l)]
    (dest/'logs'/src.name).write_text(clean('\n'.join(lines) + '\n')); copied.append('logs/' + src.name)
dist = build/'dist'
if (dist/'PACKAGE_VERIFICATION.json').exists():
    (dest/'package_PACKAGE_VERIFICATION.json').write_text(clean((dist/'PACKAGE_VERIFICATION.json').read_text()))
    copied.append('dist/PACKAGE_VERIFICATION.json')
for zp in sorted(dist.glob('*.zip')):
    with zipfile.ZipFile(zp) as z:
        for info in z.infolist():
            if info.filename.count('/') == 1 and info.filename.endswith(('/SHA256SUMS.txt', '/INPUT_SHA256.txt')):
                name = info.filename.split('/')[1]
                (dest/('package_' + name)).write_text(clean(z.read(info).decode())); copied.append(zp.name + ':' + name)
(dest/'MANIFEST.json').write_text(json.dumps({'copied_from_build': copied,
    'note': 'text only; models/images/textures stay in build/ (gitignored)'}, indent=1, ensure_ascii=False) + '\n')
print('copied', len(copied))
