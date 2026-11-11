"""Read a GLB header (no Blender): meshes, primitives, skin, animations, materials, images, triangle counts."""
import sys, json, struct


def read_glb(path):
    b = open(path, 'rb').read(); assert b[:4] == b'glTF'; n = struct.unpack('<I', b[12:16])[0]; g = json.loads(b[20:20 + n]); off = 20 + n
    binlen = struct.unpack('<I', b[off:off + 4])[0] if off < len(b) else 0
    return g, b[off + 8:off + 8 + binlen]


def info(path):
    g, _ = read_glb(path); acc = g['accessors']; out = {'nodes': len(g['nodes']), 'meshes': {}, 'skins': [], 'animations': [], 'materials': [], 'images': len(g.get('images', [])), 'triangles': 0, 'attribute_vertices': 0, 'primitives': 0}
    for m in g['meshes']:
        prims = []
        for p in m['primitives']:
            t = acc[p['indices']]['count']//3; v = acc[p['attributes']['POSITION']]['count']; out['triangles'] += t; out['attribute_vertices'] += v; out['primitives'] += 1
            prims.append({'material': g['materials'][p['material']]['name'], 'triangles': t, 'vertices': v, 'attributes': sorted(p['attributes'])})
        out['meshes'][m['name']] = prims
    for s in g.get('skins', []):
        out['skins'].append({'name': s.get('name'), 'joints': len(s['joints']), 'joint_names': [g['nodes'][j]['name'] for j in s['joints']]})
    for a in g.get('animations', []):
        ts = [acc[s['input']] for s in a['samplers']]; out['animations'].append({'name': a.get('name'), 'channels': len(a['channels']), 'seconds': round(max(t['max'][0] for t in ts), 3), 'keys': max(t['count'] for t in ts)})
    for m in g.get('materials', []):
        out['materials'].append({'name': m['name'], 'alphaMode': m.get('alphaMode', 'OPAQUE'), 'doubleSided': m.get('doubleSided', False), 'texture': 'baseColorTexture' in m.get('pbrMetallicRoughness', {})})
    return out


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(info(p), indent=1, ensure_ascii=False))
