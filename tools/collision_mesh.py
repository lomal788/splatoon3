"""Phive 형상(.bphsh) 안 hknpMeshShape → 삼각형·재질 매핑·glb.

형식 (Havok 2021.1 TAG0, 리플렉션은 collision_tag0.py 로 읽음):
  hknpMeshShape (+0x50 vertexConversionUtil{bitScale16, bitScale16Inv}, +0x70 shapeTagTable,
                 +0x78 topLevelTree(hkcdSimdTree), +0x90 geometrySections)
  GeometrySection(64B): sectionBvh(hknpAabb8TreeNode[]), primitives(u8 a,b,c,d), quantizedVertices(u16 x,y,z),
                        interiorPrimitiveBitField, sectionOffset s32[3], bitScale8Inv f32[3], bitOffset s16[3]
  정점 = (sectionOffset + q) * bitScale16Inv                         (AABB8 트리 박스와 일치 [데이터])
  프리미티브(a,b,c,d) [판독 0x71009372cc]: c==d → 삼각형(a,b,c); c!=d && b<=d → 삼각형 (a,b,c),(a,c,d);
                      c!=d && b>d → 4정점 평면 사각형 1개(여기서는 같은 두 삼각형으로 출력)
  프리미티브 키 = section<<9 | prim<<1 (numShapeKeyBits 15, 표 키가 전부 짝수)
  shapeTagTable = 키 오름차순 런 시작표: 키 k 의 shapeTag = 키 <= k 인 마지막 항목 (끝 0xFFFF 센티널)
  shapeTag = bphsh 재질표 인덱스 → (MaterialCollection 이름, UserShapeTag 마스크), 필터표 u64

사용:
  PY web/tools/collision_mesh.py <x.pack.zs|x.bphsh> [--glb out.glb] [--json out.json] [--name 팩안이름일부]
"""
import argparse
import bisect
import json
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collision_tag0
import gimmick_phive
import spl_data


def s32(x):
    return x - (1 << 32) if x >= 1 << 31 else x


def decode_mesh(tf, root):
    inv = root["vertexConversionUtil"]["bitScale16Inv"][:3]
    st = tf.rel(root["shapeTagTable"])
    keys = [e["meshPrimitiveKey"] for e in st]
    tags = [e["shapeTag"] for e in st]
    sections = tf.rel(root["geometrySections"])
    pos_all, tri_all, tri_tag, tri_key, tri_quad = [], [], [], [], []
    vbase = 0
    for si, g in enumerate(sections):
        so = np.array([s32(x) for x in g["sectionOffset"]], dtype=np.int64)
        q = np.frombuffer(tf.rel_raw(g["quantizedVertices"])[0], dtype="<u2").reshape(-1, 3).astype(np.int64)
        p = ((so + q).astype(np.float64) * np.array(inv, dtype=np.float64)).astype(np.float32)
        prims = np.frombuffer(tf.rel_raw(g["primitives"])[0], dtype=np.uint8).reshape(-1, 4)
        for pi, (a, b, c, d) in enumerate(prims.tolist()):
            key = (si << 9) | (pi << 1)
            k = bisect.bisect_right(keys, key) - 1
            tag = tags[k] if k >= 0 else 0xFFFF
            # 0x71009372cc: c==d → 삼각형 1개, c!=d && b<=d → 삼각형 2개(a,b,c),(a,c,d) 키 |0,|1,
            #               c!=d && b>d → 4정점 평면 사각형 1개(형상 플래그 0x400). 웹에서는 같은 두 삼각형으로 낸다.
            flat = c != d and b > d
            tri_all.append((vbase + a, vbase + b, vbase + c))
            tri_tag.append(tag)
            tri_key.append(key)
            tri_quad.append(0 if c == d else (3 if flat else 1))
            if c != d:
                tri_all.append((vbase + a, vbase + c, vbase + d))
                tri_tag.append(tag)
                tri_key.append(key if flat else key | 1)
                tri_quad.append(3 if flat else 2)
        pos_all.append(p)
        vbase += len(p)
    return {
        "pos": np.concatenate(pos_all) if pos_all else np.zeros((0, 3), np.float32),
        "tri": np.array(tri_all, dtype=np.uint32).reshape(-1, 3),
        "tag": np.array(tri_tag, dtype=np.int64),
        "key": np.array(tri_key, dtype=np.int64),
        "quad": np.array(tri_quad, dtype=np.int64),
        "sections": len(sections),
        "primitives": sum(g["primitives"][2] for g in sections),
        "shape_tag_runs": len(st),
    }


def filter_names(cfg, v):
    lo, hi = v & 0xFFFFFFFF, v >> 32
    lay = {m["MaskValue"]: m["ComponentName"] for m in cfg["LayerHitMaskEntityCollection"]}
    sub = {m["MaskValue"]: m["ComponentName"] for m in cfg.get("SubLayerHitMaskEntityCollection", [])}
    return {"raw": f"{v:#018x}", "layerHitMask": lay.get(lo, f"{lo:#x}"), "subLayerHitMask": sub.get(hi, f"{hi:#x}")}


def load_blobs(path, name_filter=None):
    f = Path(path)
    if f.name.endswith(".pack.zs"):
        sarc = spl_data.sarc(spl_data.unzs(f.read_bytes()))
        return [(n, b) for n, b in sarc.items() if n.endswith(".bphsh") and (not name_filter or name_filter in n)]
    return [(f.name, f.read_bytes())]


def analyze(blob):
    tf = collision_tag0.open_bphsh(blob)
    root_t, offs = tf.item_offsets(1)
    root = tf.read(root_t, offs[0])
    info = {"sdkv": tf.sdkv, "root_type": tf.fullname(root_t)}
    ph = gimmick_phive.parse(blob)
    info["phive_materials"] = len(ph["materials"])
    if root_t.name != "hknpMeshShape":
        info["note"] = "hknpMeshShape 아님 — 이 도구 범위 밖"
        return info, None, ph
    m = decode_mesh(tf, root)
    return info, m, ph


def stats(m, ph, mat_names, tagnames, cfg):
    pos, tri = m["pos"], m["tri"]
    used = np.unique(tri)
    bb_min = pos[used].min(0).tolist() if len(used) else None
    bb_max = pos[used].max(0).tolist() if len(used) else None
    v0, v1, v2 = pos[tri[:, 0]].astype(np.float64), pos[tri[:, 1]].astype(np.float64), pos[tri[:, 2]].astype(np.float64)
    n = np.cross(v1 - v0, v2 - v0)
    area = 0.5 * np.linalg.norm(n, axis=1)
    ny = np.divide(n[:, 1], 2 * area, out=np.zeros_like(area), where=area > 0)
    rows = []
    for t in sorted(set(m["tag"].tolist())):
        sel = m["tag"] == t
        row = {"shapeTag": t, "triangles": int(sel.sum()), "area": round(float(area[sel].sum()), 3)}
        if t < len(ph["materials"]):
            mi, _, mask = ph["materials"][t]
            row["material"] = mat_names[mi] if mi < len(mat_names) else mi
            row["userShapeTags"] = [nm for v, nm in sorted(tagnames.items()) if mask & v]
            if t < len(ph["filters"]):
                row["filter"] = filter_names(cfg, ph["filters"][t])
        tv = np.unique(tri[sel])
        row["bbox_min"] = [round(x, 4) for x in pos[tv].min(0).tolist()]
        row["bbox_max"] = [round(x, 4) for x in pos[tv].max(0).tolist()]
        row["upFacingArea(ny>0.7)"] = round(float(area[sel & (ny > 0.7)].sum()), 3)
        rows.append(row)
    return {
        "sections": m["sections"], "primitives": m["primitives"],
        "triangles": int(len(tri)), "from_triangle_pairs": int(((m["quad"] == 1) | (m["quad"] == 2)).sum()),
        "from_flat_quads": int((m["quad"] == 3).sum()),
        "vertices": int(len(pos)), "shape_tag_runs": m["shape_tag_runs"],
        "degenerate_triangles(area<1e-6)": int((area < 1e-6).sum()),
        "bbox_min": bb_min, "bbox_max": bb_max, "by_shape_tag": rows,
    }


def write_glb(path, m, ph, mat_names, tagnames, cfg):
    """재질(shapeTag)별 primitive 1개. extras 에 재질·태그·필터. 좌표는 원본 그대로(Y 위, 미터 단위 [추정])."""
    pos = m["pos"].astype(np.float32)
    groups = []
    for t in sorted(set(m["tag"].tolist())):
        idx = m["tri"][m["tag"] == t].astype(np.uint32).reshape(-1)
        groups.append((t, idx))
    bin_parts = [pos.tobytes()]
    views = [{"buffer": 0, "byteOffset": 0, "byteLength": pos.nbytes, "target": 34962}]
    acc = [{"bufferView": 0, "componentType": 5126, "count": int(len(pos)), "type": "VEC3",
            "min": pos.min(0).tolist(), "max": pos.max(0).tolist()}]
    off = pos.nbytes
    prims, mats = [], []
    palette = [(0.6, 0.6, 0.6)]
    for gi, (t, idx) in enumerate(groups):
        b = idx.tobytes()
        pad = (-len(b)) % 4
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(b), "target": 34963})
        acc.append({"bufferView": len(views) - 1, "componentType": 5125, "count": int(len(idx)), "type": "SCALAR"})
        bin_parts.append(b + b"\0" * pad)
        off += len(b) + pad
        extras = {"shapeTag": int(t)}
        if t < len(ph["materials"]):
            mi, _, mask = ph["materials"][t]
            extras["material"] = mat_names[mi] if mi < len(mat_names) else mi
            extras["userShapeTagMask"] = int(mask)
            extras["userShapeTags"] = [nm for v, nm in sorted(tagnames.items()) if mask & v]
            if t < len(ph["filters"]):
                extras["filter"] = filter_names(cfg, ph["filters"][t])
        h = (int(t) * 0.61803398875) % 1.0
        r, g, bb = [abs(((h * 6 + k) % 6) - 3) - 1 for k in (0, 4, 2)]
        col = [min(max(x, 0), 1) * 0.7 + 0.2 for x in (r, g, bb)] + [1.0]
        mats.append({"name": f"tag{t}_{extras.get('material', '')}", "extras": extras,
                     "pbrMetallicRoughness": {"baseColorFactor": col, "metallicFactor": 0, "roughnessFactor": 1},
                     "doubleSided": True})
        prims.append({"attributes": {"POSITION": 0}, "indices": len(acc) - 1, "material": len(mats) - 1,
                      "extras": extras})
    binb = b"".join(bin_parts)
    gltf = {"asset": {"version": "2.0", "generator": "splatoon3 web/tools/collision_mesh.py"},
            "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "collision"}],
            "meshes": [{"name": "collision", "primitives": prims}], "materials": mats,
            "accessors": acc, "bufferViews": views, "buffers": [{"byteLength": len(binb)}]}
    js = json.dumps(gltf, ensure_ascii=False).encode("utf-8")
    js += b" " * ((-len(js)) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binb))
    out += struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binb), 0x004E4942) + binb
    Path(path).write_bytes(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--glb")
    ap.add_argument("--json")
    ap.add_argument("--name")
    a = ap.parse_args()
    mat_names, tagnames = gimmick_phive.config()
    cfg = spl_data.byml((gimmick_phive.ROOT / "extracted/romfs/Phive/Config/PhiveConfig.byml.zs").read_bytes())
    res = {}
    for n, blob in load_blobs(a.src, a.name):
        info, m, ph = analyze(blob)
        if m is not None:
            info.update(stats(m, ph, mat_names, tagnames, cfg))
            if a.glb:
                write_glb(a.glb, m, ph, mat_names, tagnames, cfg)
        res[n] = info
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    if a.json:
        Path(a.json).write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
