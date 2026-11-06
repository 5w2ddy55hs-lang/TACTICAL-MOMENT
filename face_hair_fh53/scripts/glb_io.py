"""Minimal GLB reader for verification (numpy only, no Blender)."""
import json, struct, hashlib
from pathlib import Path
import numpy as np
DT = {5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_glb(path):
    b = Path(path).read_bytes(); assert b[:4] == b'glTF' and struct.unpack_from('<II', b, 4) == (2, len(b))
    chunks = {}; p = 12
    while p < len(b):
        n, t = struct.unpack_from('<II', b, p); p += 8; chunks[t] = b[p:p+n]; p += n
    return json.loads(chunks[0x4E4F534A]), chunks.get(0x004E4942, b'')


def accessor(g, b, i):
    a = g['accessors'][i]; assert 'sparse' not in a
    v = g['bufferViews'][a['bufferView']]; dt = np.dtype(DT[a['componentType']]); w = WIDTH[a['type']]
    stride = v.get('byteStride', w*dt.itemsize)
    out = np.ndarray((a['count'], w), dtype=dt, buffer=b, offset=v.get('byteOffset', 0)+a.get('byteOffset', 0), strides=(stride, dt.itemsize)).copy()
    if a.get('normalized'):
        out = out.astype(float)/np.iinfo(dt).max
    return out


def primitives(path):
    """{node/material: {attr: corner-expanded array (ntri,3,w)}} plus summary."""
    g, b = read_glb(path); out = {}
    for n in g['nodes']:
        if 'mesh' not in n:
            continue
        for p in g['meshes'][n['mesh']]['primitives']:
            ids = accessor(g, b, p['indices']).ravel().astype(int)
            key = n.get('name', '?') + '/' + g['materials'][p['material']]['name']
            out[key] = {k: accessor(g, b, i)[ids].reshape(-1, 3, WIDTH[g['accessors'][i]['type']]) for k, i in p['attributes'].items()}
            out[key]['_vertex_count'] = g['accessors'][p['attributes']['POSITION']]['count']
    return g, out


def stats(path):
    g, prims = primitives(path)
    tri = sum(v['POSITION'].shape[0] for v in prims.values())
    verts = sum(v['_vertex_count'] for v in prims.values())
    imgs = []
    _, b = read_glb(path)
    for im in g.get('images', []):
        v = g['bufferViews'][im['bufferView']]; data = b[v.get('byteOffset', 0):v.get('byteOffset', 0)+v['byteLength']]
        w, h = struct.unpack('>II', data[16:24]) if data[:4] == b'\x89PNG' else (None, None)
        imgs.append({'name': im.get('name'), 'mime': im.get('mimeType'), 'bytes': len(data), 'w': w, 'h': h, 'sha256': hashlib.sha256(data).hexdigest()})
    return {'triangles': tri, 'attribute_vertices': verts, 'primitives': len(prims), 'materials': len(g.get('materials', [])),
            'images': imgs, 'nodes': [n.get('name') for n in g['nodes']],
            'material_modes': {m['name']: {'alphaMode': m.get('alphaMode', 'OPAQUE'), 'doubleSided': m.get('doubleSided', False)} for m in g.get('materials', [])}}


def _write_glb(path, g, buf):
    import copy
    while len(buf) % 4:
        buf.append(0)
    g['buffers'][0]['byteLength'] = len(buf)
    j = json.dumps(g, separators=(',', ':')).encode(); j += b' '*((-len(j)) % 4)
    body = struct.pack('<II', len(j), 0x4E4F534A) + j + struct.pack('<II', len(buf), 0x004E4942) + bytes(buf)
    Path(path).write_bytes(struct.pack('<4sII', b'glTF', 2, len(body) + 12) + body)


def graft_primitive(target, source, node_name, material_name, out):
    """Replace one primitive of `target` with the byte-identical primitive of `source`
    (same approach as FACE52 build49_v3.canonical_cap). Requires identical corner-expanded
    POSITION first; returns a record of what was compared/replaced."""
    import copy
    g, b0 = read_glb(target); s, sb = read_glb(source); buf = bytearray(b0)
    def find(gg, bb):
        node = next(n for n in gg['nodes'] if n.get('name') == node_name)
        mesh = gg['meshes'][node['mesh']]
        pi = next(i for i, p in enumerate(mesh['primitives']) if gg['materials'][p['material']]['name'] == material_name)
        return mesh, pi
    sm, spi = find(s, sb); tm, tpi = find(g, b0); sp = sm['primitives'][spi]; tp = tm['primitives'][tpi]
    def corners(gg, bb, p, attr):
        return accessor(gg, bb, p['attributes'][attr])[accessor(gg, bb, p['indices']).ravel()]
    rec = {}
    for attr in ('POSITION', 'TEXCOORD_0', 'COLOR_0', 'NORMAL'):
        if attr in sp['attributes'] and attr in tp['attributes']:
            a = corners(s, sb, sp, attr); c = corners(g, b0, tp, attr)
            rec[attr] = 'exact' if a.shape == c.shape and (a == c).all() else ('maxdiff %.3e' % np.abs(a.astype(float) - c.astype(float)).max() if a.shape == c.shape else 'shape differs')
    if rec.get('POSITION') != 'exact':
        raise ValueError('graft refused: positions differ ' + str(rec))
    vm = {}; am = {}
    def clone(ai):
        if ai in am:
            return am[ai]
        a = copy.deepcopy(s['accessors'][ai]); vi = a['bufferView']
        if vi not in vm:
            v = copy.deepcopy(s['bufferViews'][vi]); off = v.get('byteOffset', 0); raw = sb[off:off+v['byteLength']]
            while len(buf) % 4:
                buf.append(0)
            v['byteOffset'] = len(buf); v['buffer'] = 0; vm[vi] = len(g['bufferViews']); g['bufferViews'].append(v); buf.extend(raw)
        a['bufferView'] = vm[vi]; am[ai] = len(g['accessors']); g['accessors'].append(a); return am[ai]
    new = copy.deepcopy(sp); new['material'] = tp['material']; new['indices'] = clone(sp['indices'])
    new['attributes'] = {k: clone(v) for k, v in sp['attributes'].items()}; tm['primitives'][tpi] = new
    _write_glb(out, g, buf)
    rec['replaced'] = f'{node_name}/{material_name}'
    return rec
