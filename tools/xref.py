import argparse
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "extracted" / "exefs" / "main.img"
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
IDX = ROOT / "analysis" / "xref_adrp.npz"
BASE = 0x7100000000
TEXT_END = 0x3E9DF50
WINDOW = 8


def relocate():
    m = bytearray(RAW.read_bytes())
    mod0 = struct.unpack_from("<I", m, 4)[0]
    dyn = mod0 + struct.unpack_from("<i", m, mod0 + 4)[0]
    tags = {}
    while True:
        t, v = struct.unpack_from("<qQ", m, dyn)
        dyn += 16
        if t == 0:
            break
        tags.setdefault(t, v)
    symtab, strtab = tags[6], tags[5]
    counts = {}
    for tab, size in ((tags.get(7, 0), tags.get(8, 0)), (tags.get(23, 0), tags.get(2, 0))):
        for r in range(tab, tab + size, 24):
            roff, info, addend = struct.unpack_from("<QQq", m, r)
            rtype, rsym = info & 0xFFFFFFFF, info >> 32
            if rtype == 0x403:
                struct.pack_into("<Q", m, roff, BASE + addend)
            elif rtype in (0x401, 0x402, 0x101):
                shndx, value = struct.unpack_from("<HQ", m, symtab + rsym * 24 + 6)
                if shndx:
                    struct.pack_into("<Q", m, roff, BASE + value + (addend if rtype == 0x101 else 0))
            counts[rtype] = counts.get(rtype, 0) + 1
    IMG.write_bytes(m)
    print("relocs", {hex(k): v for k, v in counts.items()})


def load_img():
    return IMG.read_bytes()


def build():
    relocate()
    m = load_img()
    w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
    n = len(w)
    idx = np.nonzero((w & 0x9F000000) == 0x90000000)[0]
    ins = w[idx].astype(np.int64)
    rd = ins & 0x1F
    immlo = (ins >> 29) & 3
    immhi = (ins >> 5) & 0x7FFFF
    imm = (immhi << 2) | immlo
    imm = np.where(imm & (1 << 20), imm - (1 << 21), imm)
    page = ((idx.astype(np.int64) * 4) & ~0xFFF) + (imm << 12)
    srcs, tgts, kinds = [], [], []
    for k in range(1, WINDOW + 1):
        j = idx + k
        ok = j < n
        jj = np.where(ok, j, 0)
        nx = w[jj].astype(np.int64)
        rn = (nx >> 5) & 0x1F
        same = ok & (rn == rd)
        add = same & ((nx & 0xFF800000) == 0x91000000) & (((nx >> 22) & 1) == 0)
        off = (nx >> 10) & 0xFFF
        srcs.append(jj[add] * 4)
        tgts.append(page[add] + off[add])
        kinds.append(np.zeros(add.sum(), np.int8))
        ldst = same & ((nx & 0x3B000000) == 0x39000000)
        size = (nx >> 30) & 3
        vbit = (nx >> 26) & 1
        opc = (nx >> 22) & 3
        scale = np.where((vbit == 1) & (opc >= 2), 4, size)
        o2 = off << scale
        srcs.append(jj[ldst] * 4)
        tgts.append(page[ldst] + o2[ldst])
        kinds.append(np.ones(ldst.sum(), np.int8))
    src = np.concatenate(srcs)
    tgt = np.concatenate(tgts)
    kind = np.concatenate(kinds)
    order = np.argsort(tgt, kind="stable")
    np.savez(IDX, src=src[order], tgt=tgt[order], kind=kind[order])
    print("refs", len(src))


def load_idx():
    z = np.load(IDX)
    return z["src"], z["tgt"], z["kind"]


def refs_to(tgt_off, idx=None):
    src, tgt, kind = idx or load_idx()
    lo = np.searchsorted(tgt, tgt_off, "left")
    hi = np.searchsorted(tgt, tgt_off, "right")
    return [(int(src[i]), int(kind[i])) for i in range(lo, hi)]


def find_cstr(m, s):
    needle = b"\0" + s.encode() + b"\0"
    out = []
    p = m.find(needle)
    while p >= 0:
        out.append(p + 1)
        p = m.find(needle, p + 1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "str", "addr"])
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()
    if a.cmd == "build":
        build()
        return
    m = load_img()
    idx = load_idx()
    for q in a.args:
        if a.cmd == "str":
            for off in find_cstr(m, q):
                r = refs_to(off, idx)
                print(f"{q!r} @ {BASE + off:#x}: " + " ".join(f"{BASE + s:#x}{'L' if k else ''}" for s, k in r))
        else:
            off = int(q, 16) - BASE if int(q, 16) >= BASE else int(q, 16)
            r = refs_to(off, idx)
            print(f"{BASE + off:#x}: " + " ".join(f"{BASE + s:#x}{'L' if k else ''}" for s, k in r))


if __name__ == "__main__":
    main()
