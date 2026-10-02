"""Havok 태그파일(TAG0, SDKV 20210100) 범용 파서.

TYPE 섹션의 리플렉션(타입 이름·멤버 이름·오프셋·형식)으로 DATA 를 해석한다.
사용: PY web/tools/collision_tag0.py <x.bphsh|x.hkx> [types|items]
"""
import struct
import sys
from pathlib import Path


def _sections(d, off, end):
    out = []
    while off + 8 <= end:
        h = struct.unpack_from(">I", d, off)[0]
        size = h & 0x3FFFFFFF
        leaf = h >> 30
        tag = d[off + 4:off + 8].decode("latin1")
        if size < 8 or off + size > end:
            break
        node = {"tag": tag, "off": off, "size": size, "body": off + 8, "end": off + size}
        if leaf == 0:
            node["children"] = _sections(d, off + 8, off + size)
        out.append(node)
        off += size
    return out


class Reader:
    def __init__(self, d, off):
        self.d, self.o = d, off

    def packed(self):
        d, o = self.d, self.o
        b = d[o]
        if b & 0x80 == 0:
            self.o += 1
            return b
        if b & 0xC0 == 0x80:
            self.o += 2
            return ((b << 8) | d[o + 1]) & 0x3FFF
        if b & 0xE0 == 0xC0:
            self.o += 3
            return ((b << 16) | (d[o + 1] << 8) | d[o + 2]) & 0x1FFFFF
        if b & 0xF8 == 0xE0:
            self.o += 4
            return int.from_bytes(d[o:o + 4], "big") & 0x07FFFFFF
        if b & 0xF8 == 0xE8:
            self.o += 5
            return int.from_bytes(d[o:o + 5], "big") & 0x07FFFFFFFF
        if b & 0xF8 == 0xF0:
            self.o += 8
            return int.from_bytes(d[o:o + 8], "big") & 0x07FFFFFFFFFFFFFF
        raise ValueError(f"packed int {b:#x} @ {o:#x}")


class Type:
    def __init__(self, idx):
        self.idx = idx
        self.name = None
        self.tparams = []
        self.parent = 0
        self.flags = 0
        self.sub = None
        self.ptr = 0
        self.version = None
        self.size = None
        self.align = None
        self.members = []
        self.interfaces = []
        self.attr = None


class TagFile:
    def __init__(self, d, base=0):
        self.d = d
        root = _sections(d, base, len(d))
        tag0 = next(s for s in root if s["tag"] == "TAG0")
        self.sec = {}

        def reg(nodes):
            for n in nodes:
                self.sec[n["tag"]] = n
                if "children" in n:
                    reg(n["children"])
        reg(tag0["children"])
        self.sdkv = d[self.sec["SDKV"]["body"]:self.sec["SDKV"]["end"]].decode("latin1")
        self.data = self.sec["DATA"]["body"]
        self._types()
        self._items()

    def _strings(self, *tags):
        for t in tags:
            if t in self.sec:
                s = self.sec[t]
                return self.d[s["body"]:s["end"]].split(b"\0")
        return []

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
                    mo = r.packed()
                    mt = r.packed()
                    t.members.append((nm, mf, mo, mt))
            if f & 64:
                for _ in range(r.packed()):
                    t.interfaces.append((r.packed(), r.packed()))
            if f & 128:
                t.attr = r.packed()

    def fullname(self, t):
        if t is None:
            return "-"
        if not t.tparams:
            return t.name
        ps = []
        for pn, pv in t.tparams:
            ps.append(self.fullname(self.types[pv]) if pn.startswith("t") and pv else str(pv))
        return f"{t.name}<{', '.join(ps)}>"

    def _up(self, t, attr, empty):
        cur = t
        while cur is not None:
            v = getattr(cur, attr)
            if v != empty:
                return v
            cur = self.types[cur.parent] if cur.parent else None
        return empty

    def size_of(self, t):
        return self._up(t, "size", None)

    def sub_of(self, t):
        return self._up(t, "sub", None) or 0

    def ptr_of(self, t):
        return self._up(t, "ptr", 0)

    def all_members(self, t):
        chain = []
        cur = t
        while cur is not None:
            chain.append(cur)
            cur = self.types[cur.parent] if cur.parent else None
        out = []
        for c in reversed(chain):
            out.extend(c.members)
        return out

    def find_type(self, name):
        return [t for t in self.types[1:] if t.name == name]

    def _items(self):
        s = self.sec["ITEM"]
        self.items = []
        for o in range(s["body"], s["end"], 12):
            a, off, cnt = struct.unpack_from("<III", self.d, o)
            self.items.append({"type": a & 0xFFFFFF, "flags": a >> 24, "off": off, "count": cnt})

    # --- 값 읽기 ---
    def read(self, t, off):
        d = self.d
        sub = self.sub_of(t)
        kind = sub & 0x1F
        if kind == 7 or (kind == 0 and self.all_members(t)):
            return {nm: self.read(self.types[mt], off + mo) for nm, mf, mo, mt in self.all_members(t)}
        if kind == 2:
            return d[off] != 0
        if kind == 4:
            nb = {0x2000: 1, 0x4000: 2, 0x8000: 4, 0x10000: 8}.get(sub & 0x3E000, self.size_of(t) or 4)
            return int.from_bytes(d[off:off + nb], "little", signed=bool(sub & 0x200))
        if kind == 5:
            sz = self.size_of(t)
            if sz == 8:
                return struct.unpack_from("<d", d, off)[0]
            if sz == 2:
                return struct.unpack_from("<e", d, off)[0]
            return struct.unpack_from("<f", d, off)[0]
        if kind == 6:
            return ("ptr", struct.unpack_from("<Q", d, off)[0])
        if kind == 3:
            return ("str", struct.unpack_from("<Q", d, off)[0])
        if kind == 8:
            if t.name in ("hkRelArrayView", "hkRelArray"):
                # 상대 배열: offset 은 이 필드 주소 기준(View: int32+int32, RelArray: int64+int32+int32)
                if t.name == "hkRelArrayView":
                    ro, n = struct.unpack_from("<ii", d, off)
                else:
                    ro, n = struct.unpack_from("<qi", d, off)
                return ("rel", off + ro if n else 0, n, self.ptr_of(t))
            if sub & 0x20:
                n = sub >> 8
                et = self.types[self.ptr_of(t)]
                es = self.size_of(et)
                return [self.read(et, off + i * es) for i in range(n)]
            return ("array", struct.unpack_from("<Q", d, off)[0], struct.unpack_from("<I", d, off + 8)[0])
        if kind == 1:
            return ("opaque", self.size_of(t))
        return ("?", sub)

    def item_offsets(self, idx):
        it = self.items[idx]
        t = self.types[it["type"]]
        es = self.size_of(t)
        base = self.data + it["off"]
        return t, [base + i * es for i in range(it["count"])]

    def rel(self, v):
        """('rel', 절대오프셋, 개수, 원소타입) → 값 목록."""
        _, o, n, ti = v
        t = self.types[ti]
        es = self.size_of(t)
        return [self.read(t, o + i * es) for i in range(n)]

    def rel_raw(self, v):
        _, o, n, ti = v
        es = self.size_of(self.types[ti])
        return self.d[o:o + es * n], es, n

    def deref(self, v):
        """('array'|'ptr', item) → 값 목록."""
        if isinstance(v, tuple) and v and v[0] in ("array", "ptr", "str") and v[1]:
            if v[0] == "str":
                it = self.items[v[1]]
                o = self.data + it["off"]
                return self.d[o:o + it["count"]].split(b"\0")[0].decode("latin1")
            t, offs = self.item_offsets(v[1])
            return [self.read(t, o) for o in offs]
        return v

    def raw(self, v):
        """배열 항목의 원시 바이트(대용량 배열 빠른 처리용)."""
        it = self.items[v[1]]
        t = self.types[it["type"]]
        es = self.size_of(t)
        o = self.data + it["off"]
        return self.d[o:o + es * it["count"]], es, it["count"]


def describe_type(tf, t):
    return (f"{t.idx:3d} {tf.fullname(t):<60} parent={t.parent} sub={tf.sub_of(t):#x} "
            f"ptr={t.ptr} size={tf.size_of(t)} ver={t.version}")


def open_bphsh(path_or_bytes):
    d = path_or_bytes if isinstance(path_or_bytes, (bytes, bytearray)) else Path(path_or_bytes).read_bytes()
    base = struct.unpack_from("<I", d, 0x0C)[0] if d[:6] == b"Phive\0" else 0
    return TagFile(d, base)


def main():
    tf = open_bphsh(sys.argv[1])
    mode = sys.argv[2] if len(sys.argv) > 2 else "types"
    print("SDKV", tf.sdkv)
    if mode == "types":
        for t in tf.types[1:]:
            print(describe_type(tf, t))
            for nm, mf, mo, mt in t.members:
                print(f"      +{mo:#06x} {nm:<32} T{mt} {tf.fullname(tf.types[mt])} f={mf:#x}")
    elif mode == "items":
        for i, it in enumerate(tf.items):
            t = tf.types[it["type"]] if it["type"] else None
            print(i, it, tf.fullname(t) if t else None)


if __name__ == "__main__":
    main()
