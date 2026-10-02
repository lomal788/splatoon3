"""Effect/*.esetb.byml(.zs) 판독 — BYML 안의 이미터셋 목록과 내장 PTCL(VFXB) 바이너리 위치.

사용:
  PY web/tools/effect_esetb.py tree  <esetb.byml.zs> [깊이]       # 구조 요약(바이너리는 오프셋/크기만)
  PY web/tools/effect_esetb.py find  <esetb.byml.zs> <이름...>     # 이미터셋 이름 검색
  PY web/tools/effect_esetb.py ptcl  <esetb.byml.zs> <out.vfxb>    # 내장 PTCL 바이너리 추출
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import spl_data as S  # noqa: E402


class LazyByml(S.Byml):
    def container(self, t, o):
        if t == 0xA1:
            n = self.u32(o)
            return {'__bin': [o + 4, n]}
        if t == 0xA2:
            n, align = struct.unpack_from(self.e + 'II', self.d, o)
            return {'__bin': [o + 8, n], 'align': align}
        return super().container(t, o)


_cache = {}


def load(path):
    if path not in _cache:
        d = S.unzs(open(path, 'rb').read())
        _cache[path] = (d, LazyByml(d).root())
    return _cache[path]


def summarize(x, depth, maxd):
    if isinstance(x, dict):
        if '__bin' in x:
            return 'BIN@0x%x len=%d' % tuple(x['__bin'])
        if depth >= maxd:
            return 'dict(%d) keys=%s' % (len(x), list(x)[:5])
        return {k: summarize(v, depth + 1, maxd) for k, v in list(x.items())[:12]} | (
            {'...': len(x)} if len(x) > 12 else {})
    if isinstance(x, list):
        if depth >= maxd:
            return 'list(%d)' % len(x)
        return [summarize(v, depth + 1, maxd) for v in x[:4]] + (['...%d' % len(x)] if len(x) > 4 else [])
    return x


def main():
    cmd, path = sys.argv[1], sys.argv[2]
    d, root = load(path)
    if cmd == 'tree':
        md = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        print(json.dumps(summarize(root, 0, md), ensure_ascii=False, indent=1))
    elif cmd == 'find':
        esets = root.get('Esets')
        for name in sys.argv[3:]:
            if isinstance(esets, dict):
                print(name, json.dumps(summarize(esets.get(name), 0, 4), ensure_ascii=False))
            elif isinstance(esets, list):
                for i, e in enumerate(esets):
                    if name in json.dumps(e, ensure_ascii=False):
                        print(name, i, json.dumps(summarize(e, 0, 4), ensure_ascii=False))
    elif cmd == 'ptcl':
        o, n = root['PtclBin']['__bin']
        open(sys.argv[3], 'wb').write(d[o:o + n])
        print('wrote', n, 'bytes, magic', d[o:o + 8])


if __name__ == '__main__':
    main()
