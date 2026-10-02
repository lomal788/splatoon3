import argparse
import json
import struct
import sys
from pathlib import Path

import zstandard

_dctx = zstandard.ZstdDecompressor()


def unzs(data):
    if data[:4] == b"\x28\xb5\x2f\xfd":
        return _dctx.decompress(data, max_output_size=1 << 31)
    return data


def load(path):
    return unzs(Path(path).read_bytes())


def sarc(data):
    assert data[:4] == b"SARC", data[:4]
    bom = data[6:8]
    e = "<" if bom == b"\xff\xfe" else ">"
    hsize, = struct.unpack_from(e + "H", data, 4)
    data_off, = struct.unpack_from(e + "I", data, 0xC)
    sfat = hsize
    assert data[sfat:sfat + 4] == b"SFAT"
    n, mult = struct.unpack_from(e + "HI", data, sfat + 6)
    sfnt = sfat + 0xC + n * 0x10
    assert data[sfnt:sfnt + 4] == b"SFNT"
    names = sfnt + 8
    out = {}
    for i in range(n):
        h, attr, s, t = struct.unpack_from(e + "IIII", data, sfat + 0xC + i * 0x10)
        if attr & 0x01000000:
            no = names + (attr & 0xFFFF) * 4
            name = data[no:data.index(b"\0", no)].decode()
        else:
            name = f"0x{h:08x}"
        out[name] = data[data_off + s:data_off + t]
    return out


class Byml:
    def __init__(self, data):
        self.d = data
        if data[:2] == b"BY":
            self.e = ">"
        elif data[:2] == b"YB":
            self.e = "<"
        else:
            raise ValueError("not BYML")
        self.ver, self.key_off, self.str_off, self.root_off = struct.unpack_from(self.e + "HIII", data, 2)
        self.keys = self.strtab(self.key_off) if self.key_off else []
        self.strs = self.strtab(self.str_off) if self.str_off else []

    def u32(self, o):
        return struct.unpack_from(self.e + "I", self.d, o)[0]

    def u24(self, o):
        b = self.d[o:o + 3]
        return int.from_bytes(b, "little" if self.e == "<" else "big")

    def strtab(self, o):
        assert self.d[o] == 0xC2
        n = self.u24(o + 1)
        out = []
        for i in range(n):
            s = o + self.u32(o + 4 + i * 4)
            out.append(self.d[s:self.d.index(b"\0", s)].decode("utf-8", "replace"))
        return out

    def root(self):
        if not self.root_off:
            return None
        return self.node(self.d[self.root_off], self.root_off, True)

    def node(self, t, v, is_off=False):
        e = self.e
        if t in (0xC0, 0xC1, 0x20, 0x21, 0xA1, 0xA2, 0xD4, 0xD5, 0xD6):
            o = v if is_off else self.u32(v)
            return self.container(t, o)
        raw = self.d[v:v + 4]
        if t == 0xA0:
            return self.strs[struct.unpack(e + "I", raw)[0]]
        if t == 0xD0:
            return bool(struct.unpack(e + "I", raw)[0])
        if t == 0xD1:
            return struct.unpack(e + "i", raw)[0]
        if t == 0xD2:
            return struct.unpack(e + "f", raw)[0]
        if t == 0xD3:
            return struct.unpack(e + "I", raw)[0]
        if t == 0xFF:
            return None
        return {"__unknown_type": hex(t), "raw": raw.hex()}

    def container(self, t, o):
        e = self.e
        if t == 0xD4:
            return struct.unpack_from(e + "q", self.d, o)[0]
        if t == 0xD5:
            return struct.unpack_from(e + "Q", self.d, o)[0]
        if t == 0xD6:
            return struct.unpack_from(e + "d", self.d, o)[0]
        if t == 0xA1:
            n = self.u32(o)
            return {"__binary": self.d[o + 4:o + 4 + n].hex()}
        if t == 0xA2:
            n, align = struct.unpack_from(e + "II", self.d, o)
            return {"__binary": self.d[o + 8:o + 8 + n].hex(), "align": align}
        assert self.d[o] == t, (hex(self.d[o]), hex(t), hex(o))
        n = self.u24(o + 1)
        if t == 0xC0:
            types = self.d[o + 4:o + 4 + n]
            vals = o + 4 + ((n + 3) & ~3)
            return [self.node(types[i], vals + i * 4) for i in range(n)]
        if t == 0xC1:
            out = {}
            for i in range(n):
                p = o + 4 + i * 8
                k = self.u24(p)
                ty = self.d[p + 3]
                out[self.keys[k]] = self.node(ty, p + 4)
            return out
        if t in (0x20, 0x21):
            ksz = 4 if t == 0x20 else 8
            out = {}
            types = o + 4 + n * (ksz + 4)
            for i in range(n):
                p = o + 4 + i * (ksz + 4)
                k = struct.unpack_from(e + ("I" if ksz == 4 else "Q"), self.d, p)[0]
                out[f"0x{k:0{ksz * 2}x}"] = self.node(self.d[types + i], p + ksz)
            return out
        raise ValueError(hex(t))


def byml(data):
    return Byml(unzs(data)).root()


def to_json(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ls")
    p.add_argument("pack")
    p = sub.add_parser("cat")
    p.add_argument("path")
    p.add_argument("member", nargs="?")
    p = sub.add_parser("unpack")
    p.add_argument("pack")
    p.add_argument("out")
    p.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.cmd == "ls":
        for k, v in sarc(load(a.pack)).items():
            print(f"{len(v):10d}  {k}")
    elif a.cmd == "cat":
        data = load(a.path)
        if a.member:
            data = unzs(sarc(data)[a.member])
        sys.stdout.reconfigure(encoding="utf-8")
        print(to_json(Byml(data).root()))
    elif a.cmd == "unpack":
        out = Path(a.out)
        for k, v in sarc(load(a.pack)).items():
            dst = out / k
            dst.parent.mkdir(parents=True, exist_ok=True)
            v = unzs(v)
            dst.write_bytes(v)
            if a.json and v[:2] in (b"YB", b"BY"):
                dst.with_name(dst.name + ".json").write_text(to_json(Byml(v).root()), encoding="utf-8")


if __name__ == "__main__":
    main()
