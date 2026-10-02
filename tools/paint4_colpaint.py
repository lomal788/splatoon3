"""ColPaint(지형 도색) 아틀라스 생성 규칙 재구현 — 원본 판독 기반(web/docs/paint/colpaint_atlas.md).

원본 함수 대응(전부 main 0x7100000000 기준):
  classify(n)          0x7102bd7918  법선 → 방향 클래스 0..41(0x29), 실패 0xff
  basis(d)             0x7102bd7b2c  방향 클래스 → (B0, B1, B2) 투영 기저(B2 = 대표 법선)
  slab_mask(tri, d)    0x7102c0638c  깊이 슬랩 비트(32칸, 6.25 단위, [-200, 200))
  touch(a, b)          0x7102c05444  두 삼각형이 정점 하나라도 공유(거리 < 0.001)
  tri_filter(...)      0x7102c0725c  메시 삼각형 → 프리즘(재질 21/22 제외, NotPaintable 제외, YPlus → 0x28)
  extract_panels(...)  0x7102bf7ce8  같은 방향 + 슬랩 겹침 + 정점 공유로 연결된 삼각형 묶음 = 패널
  merge_panels(...)    0x7102bf88d0  (u,v) AABB가 겹치고 깊이 중심 차 < 0.2 또는 깊이 범위 겹침이면 병합
  reproject(p, d)      0x7102bf9850  패널 AABB(+0x3c..)를 다른 방향 기저의 AABB로 변환(8 꼭짓점)
  horiz_area(panels)   0x7102bfda20  수평 묶음 픽셀 영역: 패널마다 ceil(크기*8) 텍셀, 중심*8 배치, 전체 ceil
  Packer               0x7102c105bc / 0x7102c104f8 / 0x7102c0ec20  기요틴 패킹, 빈칸 목록 = 높이 오름차순
f32 순서는 디스어셈블 순서를 따름. libm(atan2f/cosf/sinf)은 파이썬 double 계산 후 f32 반올림(원본 nn libm과 1ulp 차이 가능).

사용:
  PY web/tools/paint4_colpaint.py yagara [--out analysis/paint4/yagara_panels.json]
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

f32 = np.float32
FLT_MAX = f32(3.4028235e38)
PI4 = f32(0.7853982)


def _atan2(y, x):
    return f32(math.atan2(float(y), float(x)))


def _cos(a):
    return f32(math.cos(float(a)))


def _sin(a):
    return f32(math.sin(float(a)))


def _sqrt(v):
    return f32(np.sqrt(f32(v)))


def _fcvtzs(v):
    v = float(v)
    if math.isnan(v):
        return 0
    if v >= 2147483647:
        return 2147483647
    if v <= -2147483648:
        return -2147483648
    return int(v)  # 0 방향 절삭


def classify(n):
    """0x7102bd7918: 법선 → 방향 클래스(u8). 0..7 = 거의 위(방위 8), 8..15 = 33.75°, 16..23 = 56.25°,
    24..31 = 90°(벽), 32..39 = 135°, 0x28 = 위(n.y > 0.999), 0x29 = 아래, 0xff = 실패."""
    x, y, z = f32(n[0]), f32(n[1]), f32(n[2])
    l2 = f32(f32(x * x) + f32(y * y))
    l2 = f32(l2 + f32(z * z))
    ln = _sqrt(l2)
    if ln > f32(0):
        inv = f32(f32(1) / ln)
        x, y, z = f32(x * inv), f32(y * inv), f32(z * inv)
    if not (y <= f32(0.999)):
        return 0x28
    s = _sqrt(f32(f32(1) - f32(y * y)))
    e = _atan2(-y, s)
    t = f32(f32(f32(e + f32(1.5707964)) + f32(0.3926991)) / PI4)
    k = (_fcvtzs(t) & 0xFFFFFFFF) % 5
    if k == 1:
        c = 2 if f32(e + f32(1.5707964)) <= PI4 else 3
    else:
        c = k + 1 if k < 2 else k + 2
        if c == 6:
            return 0x29
    h = _sqrt(f32(f32(x * x) + f32(z * z)))
    zz, xx = f32(-z), f32(-x)
    if h > f32(0):
        ih = f32(f32(1) / h)
        zz, xx = f32(ih * zz), f32(ih * xx)
    if h >= f32(1.1920929e-07):
        a = _atan2(xx, zz)
        az = _fcvtzs(f32(f32(f32(a + f32(3.1415927)) + f32(0.3926991)) / PI4)) & 7
    else:
        az = 0xFF
    return (az + c * 8 - 8) & 0xFF


def _theta_phi(d):
    th = f32(-0.7853982) if (d & 0xFE) == 0x28 else f32(f32(d & 7) * PI4)
    if d == 0x28:
        ph = f32(0)
    else:
        u = 6 if d == 0x29 else ((d if d < 0x80 else d - 0x100) >> 3) + 1
        if (u & 0x3FFFFFFE) == 2:
            ph = f32(0.5890486) if u == 2 else f32(0.98174775)
        else:
            ph = f32(f32(u - 2) * PI4)
    return th, ph


def _cross(a, b):
    return (f32(f32(a[1] * b[2]) - f32(a[2] * b[1])), f32(f32(a[2] * b[0]) - f32(a[0] * b[2])),
            f32(f32(a[0] * b[1]) - f32(a[1] * b[0])))


def _norm(v):
    l2 = f32(f32(f32(v[0] * v[0]) + f32(v[1] * v[1])) + f32(v[2] * v[2]))
    ln = _sqrt(l2)
    if ln > f32(0):
        i = f32(f32(1) / ln)
        return (f32(i * v[0]), f32(i * v[1]), f32(i * v[2])), ln
    return v, ln


def basis(d):
    """0x7102bd7b2c: (B0, B1, B2). B2 = 대표 법선, (B0, B1) = 도색 평면 축. UV 투영 = (B0·p, B1·p), 깊이 = B2·p."""
    if d > 0x29:
        return (f32(1), f32(0), f32(0)), (f32(0), f32(1), f32(0)), (f32(0), f32(0), f32(1))
    if d < 8:
        b2 = (f32(0), f32(1), f32(0))
        th = f32(f32(d & 7) * PI4)
        c, s = _cos(th), _sin(th)
        b1, _ = _norm((f32(-s), f32(0), f32(-c)))
        b0 = _cross(b1, b2)
        return b0, b1, b2
    th, ph = _theta_phi(d)
    c, s = _cos(th), _sin(th)
    cp, sp = _cos(ph), _sin(ph)
    b2 = (f32(s * sp), cp, f32(c * sp))
    b0 = (f32(b2[2] - f32(cp * f32(0))), f32(f32(b2[0] * f32(0)) - f32(b2[2] * f32(0))), f32(f32(cp * f32(0)) - b2[0]))
    b0, ln = _norm(b0)
    if not (ln >= f32(1.1920929e-07)):
        b0 = (f32(1), f32(0), f32(0))
    b1 = _cross(b0, b2)
    # 0x7102bd7b2c 끝: B1 = (B0.z*B2.y - B0.y*B2.z, B0.x*B2.z - B0.z*B2.x, B0.y*B2.x - B0.x*B2.y) = B2 × B0
    b1 = (f32(f32(b0[2] * b2[1]) - f32(b0[1] * b2[2])), f32(f32(b0[0] * b2[2]) - f32(b0[2] * b2[0])),
          f32(f32(b0[1] * b2[0]) - f32(b0[0] * b2[1])))
    return b0, b1, b2


def slab_normal(d):
    """0x7102c0638c 안의 법선: basis() 와 달리 0..7 도 일반 식(φ = −45°)을 탄다(원본 그대로)."""
    th, ph = _theta_phi(d)
    c, s = _cos(th), _sin(th)
    cp, sp = _cos(ph), _sin(ph)
    return f32(s * sp), cp, f32(c * sp)


def slab_mask(tri, d):
    """0x7102c0638c: 꼭짓점 깊이 k = clamp(int((n·v + 200)/6.25), 0, 31), min..max 비트를 켬."""
    nx, ny, nz = slab_normal(d)
    ks = []
    for v in tri:
        dot = f32(f32(f32(f32(v[0]) * nx) + f32(ny * f32(v[1]))) + f32(nz * f32(v[2])))
        k = _fcvtzs(f32(f32(dot + f32(200)) / f32(6.25)))
        k = 31 if k > 30 else k
        k = 0 if k < 0 else k
        ks.append(k)
    lo, hi = min(ks), max(ks)
    m = 0
    for b in range(lo, hi + 1):
        m |= 1 << (b & 31)
    return m


def touch(a, b):
    """0x7102c05444: 9쌍 정점 거리 중 하나라도 < 0.001."""
    for p in a:
        for q in b:
            dx, dy, dz = f32(f32(p[0]) - f32(q[0])), f32(f32(p[1]) - f32(q[1])), f32(f32(p[2]) - f32(q[2]))
            if _sqrt(f32(f32(f32(dx * dx) + f32(dy * dy)) + f32(dz * dz))) < f32(0.001):
                return True
    return False


def tri_normal(v0, v1, v2):
    """0x7102c0725c: n = (v1−v0)... 원본은 (e1 × e2) 를 (e1=v1−v0, e2=v2−v0) 순서로 계산."""
    e1 = tuple(f32(f32(v1[i]) - f32(v0[i])) for i in range(3))
    e2 = tuple(f32(f32(v2[i]) - f32(v0[i])) for i in range(3))
    n = (f32(f32(e1[1] * e2[2]) - f32(e1[2] * e2[1])), f32(f32(e1[2] * e2[0]) - f32(e1[0] * e2[2])),
         f32(f32(e1[0] * e2[1]) - f32(e1[1] * e2[0])))
    return _norm(n)


MAT_FENCE, MAT_ROPENET = 21, 22
BIT_YPLUS, BIT_NOTPAINTABLE = 1 << 48, 1 << 50


def tri_filter(mat_index, tag_mask, v0, v1, v2):
    """0x7102c0725c: 프리즘이 되면 방향 클래스, 아니면 None."""
    if mat_index in (MAT_FENCE, MAT_ROPENET):
        return None
    n, ln = tri_normal(v0, v1, v2)
    if ln == f32(0):
        return None
    d = classify(n)
    if d == 0xFF or (tag_mask & BIT_NOTPAINTABLE):
        return None
    if tag_mask & BIT_YPLUS:
        d = 0x28
    return d


def project_aabb(d, tris):
    b0, b1, b2 = basis(d)
    lo = [FLT_MAX] * 3
    hi = [-FLT_MAX] * 3
    for t in tris:
        for v in t:
            for i, b in enumerate((b0, b1, b2)):
                w = f32(f32(f32(b[0] * f32(v[0])) + f32(b[1] * f32(v[1]))) + f32(b[2] * f32(v[2])))
                lo[i] = min(lo[i], w)
                hi[i] = max(hi[i], w)
    return lo, hi


def extract_panels(prisms):
    """0x7102bf7ce8 + 콜백 0x7102bf92cc: 방향별로 (슬랩 겹침 && 정점 공유) 연결 성분.
    prisms: [(d, tri, mask)] → 패널 [(d, [prism 인덱스])]. 순회 순서·옥트리는 결과 분할에 영향 없음(연결 성분)."""
    by_dir = {}
    for i, (d, tri, m) in enumerate(prisms):
        by_dir.setdefault(d, []).append(i)
    panels = []
    for d in sorted(by_dir):
        idx = by_dir[d]
        parent = {i: i for i in idx}

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        vmap = {}
        for i in idx:
            for v in prisms[i][1]:
                key = (round(float(v[0]) * 1000), round(float(v[1]) * 1000), round(float(v[2]) * 1000))
                vmap.setdefault(key, []).append(i)
        for i in idx:
            cand = set()
            for v in prisms[i][1]:
                kx, ky, kz = (round(float(v[0]) * 1000), round(float(v[1]) * 1000), round(float(v[2]) * 1000))
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        for oz in (-1, 0, 1):
                            cand.update(vmap.get((kx + ox, ky + oy, kz + oz), ()))
            for j in cand:
                if j <= i or not (prisms[i][2] & prisms[j][2]):
                    continue
                if touch(prisms[i][1], prisms[j][1]):
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        parent[rj] = ri
        groups = {}
        for i in idx:
            groups.setdefault(find(i), []).append(i)
        for g in groups.values():
            panels.append({"dir": d, "prisms": sorted(g)})
    for p in panels:
        lo, hi = project_aabb(p["dir"], [prisms[i][1] for i in p["prisms"]])
        p["lo"], p["hi"] = lo, hi
    return panels


def _overlap(a_lo, a_hi, b_lo, b_hi):
    return b_lo <= a_hi and b_hi >= a_lo


def merge_panels(panels):
    """0x7102bf88d0: 같은 방향에서 A 를 기준으로 B 의 (u,v) 범위가 겹치고
    |깊이 중심 차| < 0.2 또는 깊이 범위가 겹치면 B 를 A 에 합침(A 확장 후 다시 검사). 첫 5120개만 '합쳐짐' 표시."""
    out = []
    for d in sorted(set(p["dir"] for p in panels)):
        lst = [dict(p) for p in panels if p["dir"] == d]
        dead = set()
        i = 0
        while i < len(lst):
            if i in dead:
                i += 1
                continue
            a = lst[i]
            merged = False
            for j, b in enumerate(lst):
                if j == i or j in dead:
                    continue
                if not (_overlap(a["lo"][0], a["hi"][0], b["lo"][0], b["hi"][0])
                        and _overlap(a["lo"][1], a["hi"][1], b["lo"][1], b["hi"][1])):
                    continue
                ca = f32(f32(a["lo"][2] + a["hi"][2]) * f32(0.5))
                cb = f32(f32(b["lo"][2] + b["hi"][2]) * f32(0.5))
                if abs(f32(ca - cb)) < f32(0.2) or (b["lo"][2] <= a["hi"][2] and a["lo"][2] <= b["hi"][2]):
                    a["prisms"] = a["prisms"] + b["prisms"]
                    a["lo"] = [min(a["lo"][k], b["lo"][k]) for k in range(3)]
                    a["hi"] = [max(a["hi"][k], b["hi"][k]) for k in range(3)]
                    dead.add(j)
                    merged = True
                    break
            if not merged:
                i += 1
        out += [p for k, p in enumerate(lst) if k not in dead]
    return out


def reproject(lo, hi, d0, mlo, mhi, d1):
    """0x7102bf9850(panel+0x20, &d1): 매핑 AABB(+0x3c..+0x50)를 방향 d1 기저의 AABB로 바꾼다.
    중심은 원래 AABB(+0x20..+0x34), 반경은 매핑 AABB. d0 == d1 이거나 매핑 AABB가 비면 그대로(d1 만 기록)."""
    mlo, mhi = list(mlo), list(mhi)
    if d0 == d1 or not (mlo[0] <= mhi[0] and mlo[1] <= mhi[1] and mlo[2] <= mhi[2]):
        return (mlo + mhi), d1
    A = basis(d0)
    C = basis(d1)

    def dot(a, c):
        return f32(f32(f32(a[0] * c[0]) + f32(a[1] * c[1])) + f32(a[2] * c[2]))
    M = [[dot(A[i], C[k]) for i in range(3)] for k in range(3)]  # M[k][i] = A_i·C_k
    half = [f32(f32(mhi[i] - mlo[i]) * f32(0.5)) for i in range(3)]
    ctr = [f32(f32(lo[i] + hi[i]) * f32(0.5)) for i in range(3)]
    nlo, nhi = [FLT_MAX] * 3, [-FLT_MAX] * 3
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                p = [f32(half[0] + ctr[0]) if sx > 0 else f32(ctr[0] - half[0]),
                     f32(half[1] + ctr[1]) if sy > 0 else f32(ctr[1] - half[1]),
                     f32(half[2] + ctr[2]) if sz > 0 else f32(ctr[2] - half[2])]
                for k in range(3):
                    v = f32(f32(f32(M[k][0] * p[0]) + f32(M[k][1] * p[1])) + f32(M[k][2] * p[2]))
                    nlo[k] = min(nlo[k], v)
                    nhi[k] = max(nhi[k], v)
    return (nlo + nhi), d1


def ceil_pos(v):
    """원본의 (int)v + (0 <= v && v != (int)v) 올림(음수는 0 방향 절삭)."""
    i = _fcvtzs(v)
    return i + (1 if (f32(v) >= f32(0) and f32(v) != f32(i)) else 0)


def panel_texels(lo, hi):
    """패널 한 장의 텍셀 사각형 크기(0x7102bfda20/0x7102bfe07c 공통): ceil((max−min)·8)."""
    return ceil_pos(f32(f32(hi[0] - lo[0]) * f32(8))), ceil_pos(f32(f32(hi[1] - lo[1]) * f32(8)))


def tri_texel_area(d, tri):
    """투영 평면에서 삼각형 면적 × 64 (텍셀 수 근사; 실제 수는 래스터화 규칙에 따름)."""
    b0, b1, _ = basis(d)
    pts = [(float(b0[0]) * v[0] + float(b0[1]) * v[1] + float(b0[2]) * v[2],
            float(b1[0]) * v[0] + float(b1[1]) * v[1] + float(b1[2]) * v[2]) for v in tri]
    (ax, ay), (bx, by), (cx, cy) = pts
    return abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay)) * 0.5 * 64.0


class Packer:
    """0x7102c0ec20(초기 빈칸) + 0x7102c105bc(배치) + 0x7102c104f8(빈칸 삽입).
    빈칸 목록은 높이 오름차순(같은 높이면 먼저 들어온 것 앞). 배치 = 목록 앞에서부터 처음 맞는 빈칸의 왼쪽 아래."""

    def __init__(self, size_units=400, tiles=1):
        s = ceil_pos(f32(size_units))
        s = 1 if s < 2 else s
        self.tex = s * 8
        step = (s * 8) // tiles
        self.free = []
        for i in range(tiles):
            for j in range(tiles):
                self.free.insert(0, [f32(i * step), f32(j * step), f32((i + 1) * step), f32((j + 1) * step)])

    def _insert(self, r):
        h = f32(r[3] - r[1])
        self.free.append(r)
        for k, n in enumerate(self.free[:-1]):
            if f32(n[3] - n[1]) > h:
                self.free.pop()
                self.free.insert(k, r)
                break

    def place(self, w, h):
        w, h = f32(w), f32(h)
        if not (f32(w * h) > f32(0)):
            return None
        for k, r in enumerate(self.free):
            if w <= f32(r[2] - r[0]) and h <= f32(r[3] - r[1]):
                break
        else:
            return None
        x0, y0, x1, y1 = r
        inv = f32(f32(1) / f32(self.tex))
        uv = (f32(x0 * inv), f32(y0 * inv), f32(f32(x0 + w) * inv), f32(f32(y0 + h) * inv))
        if f32(f32(x1 - x0) - w) <= f32(f32(y1 - y0) - h):
            top = [f32(x0 + f32(0)), f32(h + y0), x1, y1]
            right = [f32(w + x0), f32(y0 + f32(0)), f32(x0 + f32(x1 - x0)), f32(y0 + h)]
        else:
            top = [f32(x0 + f32(0)), f32(h + y0), f32(x0 + w), f32(y0 + f32(y1 - y0))]
            right = [f32(w + x0), f32(y0 + f32(0)), x1, y1]
        del self.free[k]
        for nr in (top, right):
            if f32(f32(nr[2] - nr[0]) * f32(nr[3] - nr[1])) >= f32(1):
                self._insert(nr)
        return uv, (x0, y0)


def load_mesh(pack):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import collision_mesh
    blobs = collision_mesh.load_blobs(pack)
    info, m, ph = collision_mesh.analyze(blobs[0][1])
    return m, ph


def build(pack, limit=None):
    m, ph = load_mesh(pack)
    pos, tri, tag = m["pos"], m["tri"], m["tag"]
    prisms, skipped = [], {"fence_ropenet": 0, "notpaintable": 0, "degenerate": 0, "fail": 0}
    for ti, (a, b, c) in enumerate(tri.tolist()):
        if limit and ti >= limit:
            break
        t = int(tag[ti])
        mi, _, mask = ph["materials"][t] if t < len(ph["materials"]) else (0, 0, 0)
        v = (tuple(pos[a]), tuple(pos[b]), tuple(pos[c]))
        if mi in (MAT_FENCE, MAT_ROPENET):
            skipped["fence_ropenet"] += 1
            continue
        if mask & BIT_NOTPAINTABLE:
            skipped["notpaintable"] += 1
            continue
        d = tri_filter(mi, mask, *v)
        if d is None:
            skipped["degenerate" if tri_normal(*v)[1] == f32(0) else "fail"] += 1
            continue
        prisms.append((d, v, slab_mask(v, d), ti))
    panels = extract_panels([(p[0], p[1], p[2]) for p in prisms])
    merged = merge_panels(panels)
    return prisms, panels, merged, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", nargs="?", default="yagara")
    ap.add_argument("--out")
    a = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    pack = root / "extracted/romfs/Pack/Actor" / f"Fld_{a.stage.capitalize()}.pack.zs"
    prisms, panels, merged, skipped = build(pack)
    hist = {}
    for p in prisms:
        hist[p[0]] = hist.get(p[0], 0) + 1
    tex_area = sum(tri_texel_area(p[0], p[1]) for p in prisms)
    rect = 0
    for p in merged:
        w, h = panel_texels(p["lo"], p["hi"])
        rect += w * h
    res = {"triangles_to_prisms": len(prisms), "skipped": skipped, "dir_hist": {hex(k): v for k, v in sorted(hist.items())},
           "panels_extracted": len(panels), "panels_after_merge": len(merged),
           "projected_area_texels(sum tri area*64)": round(tex_area), "panel_rect_texels(sum ceil(w*8)*ceil(h*8))": rect,
           "atlas_texels(3200^2)": 3200 * 3200}
    print(json.dumps(res, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps({"summary": res, "panels": [
            {"dir": p["dir"], "n": len(p["prisms"]), "lo": [float(x) for x in p["lo"]], "hi": [float(x) for x in p["hi"]],
             "texels": panel_texels(p["lo"], p["hi"])} for p in merged]}, indent=0), encoding="utf-8")


if __name__ == "__main__":
    main()
