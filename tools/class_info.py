import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from disasm import disasm, func_start
from xref import BASE, ROOT, find_cstr, load_idx, load_img, refs_to


def ptrs_to(m, va):
    needle = struct.pack("<Q", va)
    out = []
    p = m.find(needle, 0x3E9E000)
    while p >= 0:
        if p % 8 == 0:
            out.append(p)
        p = m.find(needle, p + 1)
    return out


def vtable_len(m, vt):
    n = 0
    while True:
        v = struct.unpack_from("<Q", m, vt + n * 8)[0]
        if not (BASE < v < BASE + 0x3E9E000):
            return n
        n += 1


def vtable_start(m, p):
    while BASE < struct.unpack_from("<Q", m, p - 8)[0] < BASE + 0x3E9E000:
        p -= 8
    return p


def class_info(m, idx, name):
    out = {"name": name}
    for s in find_cstr(m, name):
        for src, k in refs_to(s, idx):
            getname = src - 4
            w = struct.unpack_from("<I", m, src + 4)[0]
            if w != 0xD65F03C0:
                continue
            out["getName"] = hex(BASE + getname)
            for p in ptrs_to(m, BASE + getname):
                tbl = vtable_start(m, p)
                slots = [struct.unpack_from("<Q", m, tbl + i * 8)[0] for i in range(vtable_len(m, tbl))]
                out["vtable"] = hex(BASE + tbl)
                out["slots"] = len(slots)
                out["getName_slot"] = slots.index(BASE + getname)
                out["create"] = [hex(BASE + func_start(m, s_)) for s_, k in refs_to(tbl, idx) if not k]
                return out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="+")
    ap.add_argument("--diff", action="store_true", help="첫 클래스 대비 vtable 슬롯 차이")
    a = ap.parse_args()
    m = load_img()
    idx = load_idx()
    infos = [class_info(m, idx, n) for n in a.names]
    tables = []
    for info in infos:
        print(json.dumps(info))
        main_vt = int(info["vtable"], 16) - BASE if "vtable" in info else None
        tables.append([struct.unpack_from("<Q", m, main_vt + i * 8)[0] for i in range(vtable_len(m, main_vt))] if main_vt else [])
    if a.diff and len(tables) > 1:
        n = max(len(t) for t in tables)
        print("slot  " + "  ".join(f"{x['name'][5:]:>22}" for x in infos))
        for i in range(n):
            row = [t[i] if i < len(t) else None for t in tables]
            if len(set(row)) > 1:
                print(f"{i:4d}  " + "  ".join(f"{hex(r) if r else '-':>22}" for r in row))


if __name__ == "__main__":
    main()
