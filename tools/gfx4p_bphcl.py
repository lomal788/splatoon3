"""Phive 천 물리(.bphcl = "Phive" 헤더 + Havok TAG0 SDKV 20210100 hclClothContainer) 덤프.

collision_tag0.py 가 이 파일에서 실패하는 원인: TBDY 멤버 레코드의 flags 에 0x80 비트가 켜진 멤버
(예 hclCollidable::localUnpackedPs, hkPackedVector3::values — flags 0xa0)는 flags 다음에 packed 정수
하나(관측값 3, 의미 미확정 — 원소 수가 아님: userData 는 u64 하나, values 는 이미 T[N]<hkInt16,4>)가 더 붙는다. 이걸 읽지 않으면 이후 TBDY 가 1바이트씩 어긋나
FSTR 인덱스가 범위를 벗어난다. 이 도구는 collision_tag0.TagFile 을 상속해 _types 만 고친다
(collision_tag0.py 는 고치지 않음).

사용:
  PY web/tools/gfx4p_bphcl.py <x.bphcl> types            타입 표(TNA1/TBDY)
  PY web/tools/gfx4p_bphcl.py <x.bphcl> items            ITEM 표
  PY web/tools/gfx4p_bphcl.py <x.bphcl> tree [깊이]      루트부터 객체 트리(JSON 비슷한 들여쓰기)
  PY web/tools/gfx4p_bphcl.py <x.bphcl> cloth [--json 출력]  천 시뮬 상수 요약
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collision_tag0 import Reader, TagFile, Type  # noqa: E402


class ClothTagFile(TagFile):
    def _types(self):
        tstr = [x.decode("latin1") for x in self._strings("TST1", "TSTR")]
        fstr = [x.decode("latin1") for x in self._strings("FST1", "FSTR")]
        self.tstr, self.fstr = tstr, fstr
        s = self.sec.get("TNA1") or self.sec["TNAM"]
        r = Reader(self.d, s["body"])
        n = r.packed()
        self.types = [None] + [Type(i) for i in range(1, n)]
        for i in range(1, n):
            t = self.types[i]
            t.name = tstr[r.packed()]
            for _ in range(r.packed()):
                pn = tstr[r.packed()]
                pv = r.packed()
                t.tparams.append((pn, pv))
        s = self.sec["TBDY"]
        r = Reader(self.d, s["body"])
        while r.o < s["end"]:
            ti = r.packed()
            if ti == 0:
                continue
            t = self.types[ti]
            t.parent = r.packed()
            t.flags = f = r.packed()
            if f & 1:
                t.sub = r.packed()
            if f & 2:
                t.ptr = r.packed()
            if f & 4:
                t.version = r.packed()
            if f & 8:
                t.size = r.packed()
                t.align = r.packed()
            if f & 16:
                t.abstract = r.packed()
            if f & 32:
                for _ in range(r.packed()):
                    nm = fstr[r.packed()]
                    mf = r.packed()
                    extra = r.packed() if mf & 0x80 else None
                    mo = r.packed()
                    mt = r.packed()
                    t.members.append((nm, mf, mo, mt))
                    if extra is not None:
                        t.member_extra = getattr(t, "member_extra", {})
                        t.member_extra[nm] = extra
            if f & 64:
                for _ in range(r.packed()):
                    t.interfaces.append((r.packed(), r.packed()))
            if f & 128:
                t.attr = r.packed()


def open_bphcl(path_or_bytes):
    d = path_or_bytes if isinstance(path_or_bytes, (bytes, bytearray)) else Path(path_or_bytes).read_bytes()
    if d[:4] == b"\x28\xb5\x2f\xfd":
        import zstandard
        d = zstandard.ZstdDecompressor().decompress(d, max_output_size=1 << 28)
    base = struct.unpack_from("<I", d, 0x0C)[0] if d[:6] == b"Phive\0" else 0
    return ClothTagFile(d, base)


def resolve(tf, v, depth, seen):
    """('array'|'ptr'|'str'|'rel') 를 따라가 파이썬 값으로."""
    if depth < 0:
        return v
    if isinstance(v, dict):
        return {k: resolve(tf, x, depth, seen) for k, x in v.items()}
    if isinstance(v, list):
        return [resolve(tf, x, depth, seen) for x in v]
    if isinstance(v, tuple) and v:
        if v[0] == "str":
            return tf.deref(v) if v[1] else ""
        if v[0] == "ptr":
            if not v[1]:
                return None
            it = tf.items[v[1]]
            t = tf.types[it["type"]]
            key = ("ptr", v[1])
            if key in seen:
                return f"<item {v[1]}>"
            seen = seen | {key}
            o = tf.data + it["off"]
            val = tf.read(t, o)
            # 다형 포인터: ITEM 의 실제 타입 이름을 붙인다
            if isinstance(val, dict):
                val = {"$type": tf.fullname(t), **val}
            return resolve(tf, val, depth - 1, seen)
        if v[0] == "array":
            if not v[1]:
                return []
            vals = tf.deref(v)
            it = tf.items[v[1]]
            tn = tf.fullname(tf.types[it["type"]])
            if vals and isinstance(vals[0], dict):
                vals = [{"$type": tn, **x} for x in vals]
            return resolve(tf, vals, depth - 1, seen)
        if v[0] == "rel":
            return resolve(tf, tf.rel(v) if v[2] else [], depth - 1, seen)
        if v[0] == "opaque":
            return f"<opaque {v[1]}>"
    return v


def root(tf):
    t, offs = tf.item_offsets(1)
    return tf.read(t, offs[0])


def tree(tf, depth=12):
    return resolve(tf, root(tf), depth, frozenset())


def _f(x):
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, list):
        return [_f(y) for y in x]
    if isinstance(x, dict):
        return {k: _f(v) for k, v in x.items()}
    return x


def cloth_summary(tf):
    """천 시뮬 상수 요약(원자료 필드 이름 그대로)."""
    tr = tree(tf, 14)
    out = {"sdkv": tf.sdkv, "clothDatas": []}
    for nv in tr.get("namedVariants", []):
        var = nv.get("variant")
        if not isinstance(var, dict) or "clothDatas" not in var:
            continue
        out["collidables"] = []
        for c in var.get("collidables") or []:
            c = c or {}
            sh = c.get("shape") or {}
            out["collidables"].append(_f({k: c.get(k) for k in (
                "name", "pinchDetectionRadius", "pinchDetectionPriority", "pinchDetectionEnabled",
                "virtualCollisionPointCollisionEnabled", "enabled", "transform")} | {"shape": sh}))
        for cd in var["clothDatas"]:
            cd = cd or {}
            ent = {"name": cd.get("name"), "simulationType": cd.get("simulationType"),
                   "transformSetNames": [x.get("name") for x in cd.get("transformSetDefinitions") or [] if x],
                   "bufferNames": [x.get("name") for x in cd.get("bufferDefinitions") or [] if x],
                   "operators": [(x or {}).get("$type") + ":" + str((x or {}).get("name")) for x in cd.get("operators") or []],
                   "clothStates": [], "simClothDatas": []}
            for cs in cd.get("clothStateDatas") or []:
                cs = cs or {}
                ent["clothStates"].append({"name": cs.get("name"), "operators": cs.get("operators")})
            for sc in cd.get("simClothDatas") or []:
                sc = sc or {}
                s = {"name": sc.get("name"),
                     "simulationInfo": sc.get("simulationInfo"),
                     "particleCount": len(sc.get("particleDatas") or []),
                     "particleDatas": sc.get("particleDatas"),
                     "fixedParticles": sc.get("fixedParticles"),
                     "perInstanceCollidables": sc.get("perInstanceCollidables"),
                     "collidableTransformMap": sc.get("collidableTransformMap"),
                     "staticConstraintSets": [], "simClothPoses": [],
                     "other": {k: sc.get(k) for k in sc if k not in (
                         "particleDatas", "staticConstraintSets", "simClothPoses", "triangleIndices",
                         "virtualCollisionPointsData", "landscapeCollisionData", "transferMotionData",
                         "collidableTransformMap", "perInstanceCollidables", "fixedParticles",
                         "simulationInfo", "name", "$type", "triangleFlips")},
                     "transferMotionData": sc.get("transferMotionData"),
                     "landscapeCollisionData": sc.get("landscapeCollisionData")}
                for c in sc.get("staticConstraintSets") or []:
                    s["staticConstraintSets"].append(c)
                for p in sc.get("simClothPoses") or []:
                    s["simClothPoses"].append({"name": (p or {}).get("name"),
                                               "positions": len((p or {}).get("positions") or [])})
                ent["simClothDatas"].append(s)
            out["clothDatas"].append(ent)
        out["skeleton"] = None
    return _f(out)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    tf = open_bphcl(a[0])
    mode = a[1] if len(a) > 1 else "types"
    if mode == "types":
        print("SDKV", tf.sdkv)
        for t in tf.types[1:]:
            print(f"{t.idx:3d} {tf.fullname(t):<70} parent={t.parent} sub={tf.sub_of(t):#x} "
                  f"size={tf.size_of(t)} ver={t.version}")
            ex = getattr(t, "member_extra", {})
            for nm, mf, mo, mt in t.members:
                e = f" n={ex[nm]}" if nm in ex else ""
                print(f"      +{mo:#06x} {nm:<40} T{mt} {tf.fullname(tf.types[mt])} f={mf:#x}{e}")
    elif mode == "items":
        for i, it in enumerate(tf.items):
            t = tf.types[it["type"]] if it["type"] else None
            print(i, it, tf.fullname(t) if t else None)
    elif mode == "tree":
        dep = int(a[2]) if len(a) > 2 else 12
        print(json.dumps(_f(tree(tf, dep)), ensure_ascii=False, indent=1, default=str))
    elif mode == "cloth":
        s = cloth_summary(tf)
        txt = json.dumps(s, ensure_ascii=False, indent=1, default=str)
        if "--json" in a:
            Path(a[a.index("--json") + 1]).write_text(txt, encoding="utf-8")
        else:
            print(txt)


if __name__ == "__main__":
    main()
