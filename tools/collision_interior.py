"""hknpMeshShape GeometrySection.interiorPrimitiveBitField 데이터 분석 (판정 코드 미판독, 데이터 상관만).

검사:
  1) 비트필드 길이 == ceil(프리미티브 수 / 8) 인지 (프리미티브당 1비트)
  2) 프리미티브 i 의 비트 = bits[i>>3] >> (i&7) & 1 과 기하 특성의 상관:
     모서리(사각형 대각선 제외)를 위치 기준으로 전역 공유 집계 → 열린 모서리 유무,
     공유 모서리마다 이웃 프리미티브의 대각 정점이 내 평면 아래(볼록)/위(오목)/평면(|d|<1e-3)인지.
사용: PY web/tools/collision_interior.py <x.pack.zs|x.bphsh> [--name 이름일부]
"""
import argparse
import collections
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collision_mesh
import collision_tag0


def prim_tris(a, b, c, d):
    if c == d:
        return [(a, b, c)]
    return [(a, b, c), (a, c, d)]


def edges(tris):
    es = set()
    for t in tris:
        for i in range(3):
            es.add(tuple(sorted((t[i], t[(i + 1) % 3]))))
    if len(tris) == 2:
        es.discard(tuple(sorted((tris[0][0], tris[0][2]))))
    return es


def nrm(t):
    n = np.cross(np.subtract(t[1], t[0]), np.subtract(t[2], t[0]))
    L = np.linalg.norm(n)
    return n / L if L else n


def analyze(tf, root):
    inv = root["vertexConversionUtil"]["bitScale16Inv"][:3]
    P = []
    size_ok = size_bad = 0
    for g in tf.rel(root["geometrySections"]):
        so = np.array([collision_mesh.s32(x) for x in g["sectionOffset"]], dtype=np.int64)
        q = np.frombuffer(tf.rel_raw(g["quantizedVertices"])[0], dtype="<u2").reshape(-1, 3).astype(np.int64)
        p = (so + q).astype(np.float64) * np.array(inv, dtype=np.float64)
        prims = np.frombuffer(tf.rel_raw(g["primitives"])[0], dtype=np.uint8).reshape(-1, 4)
        bits = tf.rel_raw(g["interiorPrimitiveBitField"])[0]
        if len(bits) == (len(prims) + 7) // 8:
            size_ok += 1
        else:
            size_bad += 1
        for pi, pr in enumerate(prims):
            tris = prim_tris(*map(int, pr))
            bit = (bits[pi >> 3] >> (pi & 7)) & 1 if (pi >> 3) < len(bits) else None
            P.append((bit, [tuple(tuple(np.round(p[v], 4)) for v in t) for t in tris]))
    emap = collections.defaultdict(list)
    for idx, (_, tris) in enumerate(P):
        for t in tris:
            for i in range(3):
                emap[tuple(sorted((t[i], t[(i + 1) % 3])))].append((idx, t[(i + 2) % 3]))
    cls = collections.Counter()
    for idx, (bit, tris) in enumerate(P):
        n0 = nrm(tris[0])
        kinds = []
        for e in edges(tris):
            nb = [(j, o) for j, o in emap[e] if j != idx]
            if not nb:
                kinds.append("open")
                continue
            k = set()
            for _, o in nb:
                s = float(np.dot(n0, np.subtract(o, e[0])))
                k.add("flat" if abs(s) < 1e-3 else ("convex" if s < 0 else "concave"))
            kinds.append(k.pop() if len(k) == 1 else "mixed")
        ks = set(kinds)
        if "open" in ks:
            key = "열린 모서리 있음"
        elif ks == {"flat"}:
            key = "전부 평면"
        elif "convex" not in ks and "mixed" not in ks:
            key = "볼록 없음(오목/평면)"
        elif "concave" not in ks and "mixed" not in ks:
            key = "볼록 포함(볼록/평면)"
        else:
            key = "혼합"
        cls[(bit, key)] += 1
    return size_ok, size_bad, cls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--name")
    a = ap.parse_args()
    for nm, blob in collision_mesh.load_blobs(a.path, a.name):
        tf = collision_tag0.open_bphsh(blob)
        root_t, offs = tf.item_offsets(1)
        if root_t.name != "hknpMeshShape":
            continue
        ok, bad, cls = analyze(tf, tf.read(root_t, offs[0]))
        print(f"{nm}: 비트필드 길이 == ceil(n/8) 섹션 {ok}개, 불일치 {bad}개")
        for k, v in sorted(cls.items(), key=lambda x: (str(x[0][0]), x[0][1])):
            print(f"  bit={k[0]}  {k[1]:16s} {v}")


if __name__ == "__main__":
    main()
