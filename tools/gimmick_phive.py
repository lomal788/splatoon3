"""Phive 형상(.bphsh) 헤더·재질표 판독. 삼각형 → 재질 매핑(TAG0 안 hknpMeshShape)은 collision_mesh.py.

사용: PY web/tools/gimmick_phive.py <x.bphsh 또는 x.pack.zs> [--json]
재질 이름: romfs/Phive/Config/PhiveConfig.byml.zs 의 MaterialCollection, 태그: UserShapeTagMaskCollection(MaskValue 비트).
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spl_data

ROOT = Path(__file__).resolve().parents[2]


def config():
    c = spl_data.byml((ROOT / "extracted/romfs/Phive/Config/PhiveConfig.byml.zs").read_bytes())
    mats = [m["ComponentName"] for m in c["MaterialCollection"]]
    tags = {m["MaskValue"]: m["ComponentName"] for m in c["UserShapeTagMaskCollection"]}
    return mats, tags


def parse(m):
    assert m[:6] == b"Phive\0", "not Phive"
    tag_off, mat_off, flt_off, end, tag_size, mat_size, flt_size = struct.unpack_from("<7I", m, 0x0C)
    mats = [struct.unpack_from("<IIQ", m, mat_off + i * 16) for i in range(mat_size // 16)]
    flts = [struct.unpack_from("<Q", m, flt_off + i * 8)[0] for i in range(flt_size // 8)]
    return {"tagfile": (tag_off, tag_size), "materials": mats, "filters": flts, "end": end}


def describe(p, names, tags):
    out = []
    for i, (mi, z, mask) in enumerate(p["materials"]):
        t = [n for v, n in sorted(tags.items()) if mask & v]
        out.append({"index": i, "material": names[mi] if mi < len(names) else mi, "tags": t,
                    "filter": hex(p["filters"][i]) if i < len(p["filters"]) else None})
    return out


def main():
    f = Path(sys.argv[1])
    names, tags = config()
    blobs = []
    if f.name.endswith(".pack.zs"):
        sarc = spl_data.sarc(spl_data.unzs(f.read_bytes()))
        for n, b in sarc.items():
            if n.endswith(".bphsh"):
                blobs.append((n, b))
    else:
        blobs.append((f.name, f.read_bytes()))
    res = {}
    for n, b in blobs:
        res[n] = describe(parse(b), names, tags)
    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        for n, rows in res.items():
            print(n)
            for r in rows:
                print(f"  {r['index']:2d} {r['material']:<10} {','.join(r['tags'])}")


if __name__ == "__main__":
    main()
