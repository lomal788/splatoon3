import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import lz4.block
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nca_romfs import Nca, RomfsView, load_keys, romfs_walk, verify_ivfc, xts_decrypt_header

CONTENT_TYPES = {0: "Program", 1: "Meta", 2: "Control", 3: "Manual", 4: "Data", 5: "PublicData"}
KAEK = {0: "key_area_key_application", 1: "key_area_key_ocean", 2: "key_area_key_system"}


def hfs0(f, base):
    f.seek(base)
    magic, n, strsz = struct.unpack("<4sII4x", f.read(16))
    assert magic in (b"HFS0", b"PFS0"), (magic, hex(base))
    esz = 0x40 if magic == b"HFS0" else 0x18
    ents = f.read(n * esz)
    strs = f.read(strsz)
    data = base + 16 + n * esz + strsz
    out = []
    for i in range(n):
        off, size, name_off = struct.unpack_from("<QQI", ents, i * esz)
        name = strs[name_off:strs.index(b"\0", name_off)].decode()
        out.append((name, data + off, size))
    return out


def xci_partitions(f):
    f.seek(0x100)
    assert f.read(4) == b"HEAD"
    f.seek(0x130)
    root_off, root_size = struct.unpack("<QQ", f.read(16))
    parts = {}
    for name, off, size in hfs0(f, root_off):
        parts[name] = hfs0(f, off)
    return parts


def nca_info(f, off, keys):
    f.seek(off)
    hdr = xts_decrypt_header(f.read(0xC00), keys["header_key"])
    assert hdr[0x200:0x204] == b"NCA3"
    dist, ctype, kg_old, kaek_idx = hdr[0x204], hdr[0x205], hdr[0x206], hdr[0x207]
    size, title_id = struct.unpack_from("<QQ", hdr, 0x208)
    sdk = hdr[0x21C:0x220][::-1]
    kg = max(kg_old, hdr[0x220])
    rights = hdr[0x230:0x240]
    gen = kg - 1 if kg > 0 else 0
    kek = keys[f"{KAEK[kaek_idx]}_{gen:02x}"]
    dec = Cipher(algorithms.AES(kek), modes.ECB()).decryptor()
    area = dec.update(hdr[0x300:0x340]) + dec.finalize()
    return {
        "type": CONTENT_TYPES.get(ctype, ctype),
        "dist": dist,
        "size": size,
        "title_id": f"{title_id:016x}",
        "sdk": ".".join(str(b) for b in sdk),
        "keygen": kg,
        "rights_id_zero": rights == b"\0" * 16,
        "content_key": area[0x20:0x30],
    }


def nso_decompress(data):
    assert data[:4] == b"NSO0"
    flags = struct.unpack_from("<I", data, 0xC)[0]
    segs = []
    for i in range(3):
        foff, moff, msize = struct.unpack_from("<III", data, 0x10 + i * 0x10)
        csize = struct.unpack_from("<I", data, 0x60 + i * 4)[0]
        sha = data[0xA0 + i * 0x20:0xC0 + i * 0x20]
        raw = data[foff:foff + csize]
        if flags & (1 << i):
            raw = lz4.block.decompress(raw, uncompressed_size=msize)
        ok = hashlib.sha256(raw).digest() == sha if flags & (1 << (i + 3)) else None
        segs.append((moff, msize, raw, ok))
    bss = struct.unpack_from("<I", data, 0x3C)[0]
    end = max(m + s for m, s, _, _ in segs)
    img = bytearray(end + bss)
    for moff, msize, raw, _ in segs:
        img[moff:moff + msize] = raw
    return bytes(img), [(hex(m), hex(s), ok) for m, s, _, ok in segs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xci")
    ap.add_argument("--keys", required=True)
    ap.add_argument("cmd", choices=["info", "exefs", "pfs", "romfs-verify", "romfs-list", "romfs-extract"])
    ap.add_argument("--nca", help="NCA 이름 앞부분")
    ap.add_argument("--section", type=int, default=0)
    ap.add_argument("--out")
    a = ap.parse_args()
    keys = load_keys(a.keys)
    f = open(a.xci, "rb")
    parts = xci_partitions(f)
    if a.cmd == "info":
        rows = []
        for pname, ents in parts.items():
            for name, off, size in ents:
                row = {"partition": pname, "name": name, "offset": hex(off), "size": size}
                if name.endswith(".nca"):
                    info = nca_info(f, off, keys)
                    row.update({k: v for k, v in info.items() if k != "content_key"})
                    nca = Nca(a.xci, keys["header_key"], info["content_key"], off)
                    row["sections"] = [{"index": s["index"], "offset": hex(s["offset"]), "size": hex(s["size"]),
                                        "fs_type": s["fs_type"], "hash_type": s["hash_type"],
                                        "enc_type": s["enc_type"]} for s in nca.sections]
                rows.append(row)
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return
    name, off, size = next(e for e in parts["secure"] if e[0].startswith(a.nca))
    info = nca_info(f, off, keys)
    nca = Nca(a.xci, keys["header_key"], info["content_key"], off)
    if a.cmd.startswith("romfs"):
        sec = next(s for s in nca.sections if s["hash_type"] == 3)
        if a.cmd == "romfs-verify":
            for b in verify_ivfc(nca, sec):
                print("  BAD level", b[0], "block", b[1], "section_off", hex(b[2]))
            return
        view = RomfsView(nca, sec)
        files = sorted(romfs_walk(view))
        if a.cmd == "romfs-list":
            for p, foff, fsize in files:
                print(f"{fsize:12d}  {p}")
            print(len(files), "files", sum(x[2] for x in files), "bytes", file=sys.stderr)
            return
        out = Path(a.out)
        for i, (p, foff, fsize) in enumerate(files):
            dst = out / p.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            with open(dst, "wb") as w:
                pos = 0
                while pos < fsize:
                    n = min(64 << 20, fsize - pos)
                    w.write(view.read(foff + pos, n))
                    pos += n
            if i % 1000 == 0:
                print(f"{i}/{len(files)} {p}", flush=True)
        print("done", len(files))
        return
    sec = next(s for s in nca.sections if s["index"] == a.section)
    fs = sec["fs"]
    if sec["hash_type"] == 2:
        pfs_off, pfs_size = struct.unpack_from("<QQ", fs, 0x8 + 0x38)
    else:
        raise SystemExit("not a PFS0 section")
    hdr = nca.read(sec, pfs_off, 0x10)
    magic, n, strsz = struct.unpack("<4sII4x", hdr)
    assert magic == b"PFS0", magic
    table = nca.read(sec, pfs_off, 0x10 + n * 0x18 + strsz)
    strs = table[0x10 + n * 0x18:]
    data0 = pfs_off + 0x10 + n * 0x18 + strsz
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        foff, fsize, noff = struct.unpack_from("<QQI", table, 0x10 + i * 0x18)
        fname = strs[noff:strs.index(b"\0", noff)].decode()
        data = nca.read(sec, data0 + foff, fsize)
        (out / fname).write_bytes(data)
        line = f"{fname} {fsize}"
        if a.cmd == "exefs" and data[:4] == b"NSO0":
            img, segs = nso_decompress(data)
            (out / f"{fname}.img").write_bytes(img)
            line += f" -> {fname}.img {len(img):#x} segs={segs} build_id={data[0x40:0x60].hex()}"
        print(line)


if __name__ == "__main__":
    main()
