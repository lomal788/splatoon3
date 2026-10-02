"""AAMP(.bagl*/.bgenv 등) 의 CRC32 이름 해시를 사전 공격으로 되돌린다.
사용: PY web/tools/gfx4_aamp_names.py <AAMP 파일·폴더...> [-o analysis/gfx4/aamp_names.txt]
후보: extracted/main_strings.txt 의 줄 전체·식별자 토큰·CamelCase 조각 연속 조합(1~4), 소문자/스네이크 변형,
      각 후보 + 숫자 접미사(0~63). 찾은 이름은 한 줄에 하나씩 저장(gfx4_aamp.py 가 읽음).
"""
import binascii
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def aamp_hashes(path):
    d = open(path, "rb").read()
    if d[:4] != b"AAMP":
        return set()
    pio_off = struct.unpack_from("<I", d, 0x14 + 4)[0]
    root = 0x30 + struct.unpack_from("<5I", d, 4)[4]
    hs = set()

    def plist(p):
        crc, a, b = struct.unpack_from("<3I", d, p)
        hs.add(crc)
        lo, ln, oo, on = (a & 0xFFFF) * 4, a >> 16, (b & 0xFFFF) * 4, b >> 16
        for i in range(on):
            q = p + oo + i * 8
            ocrc, w = struct.unpack_from("<2I", d, q)
            hs.add(ocrc)
            po, pn = (w & 0xFFFF) * 4, w >> 16
            for j in range(pn):
                hs.add(struct.unpack_from("<I", d, q + po + j * 8)[0])
        for i in range(ln):
            plist(p + lo + i * 12)

    plist(root)
    return hs


def files(args):
    for a in args:
        if os.path.isdir(a):
            for r, _, fs in os.walk(a):
                for f in fs:
                    yield os.path.join(r, f)
        else:
            yield a


def candidates():
    words = set()
    txt = open(os.path.join(ROOT, "extracted/main_strings.txt"), encoding="utf8", errors="replace").read()
    for line in txt.splitlines():
        if len(line) < 80:
            words.add(line)
        for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", line):
            words.add(tok)
    pieces = set()
    for w in list(words):
        parts = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", w)
        for i in range(len(parts)):
            for j in range(i + 1, min(len(parts), i + 4) + 1):
                pieces.add("".join(parts[i:j]))
        for p in parts:
            pieces.add(p)
    allw = words | pieces
    out = set()
    for w in allw:
        out.add(w)
        out.add(w.lower())
        out.add(w[:1].lower() + w[1:])
        out.add(w[:1].upper() + w[1:])
        out.add(re.sub(r"(?<!^)(?=[A-Z])", "_", w).lower())
    return out


def main():
    args = sys.argv[1:]
    outp = os.path.join(ROOT, "analysis/gfx4/aamp_names.txt")
    if "-o" in args:
        i = args.index("-o")
        outp = args[i + 1]
        del args[i:i + 2]
    hs = set()
    for f in files(args):
        try:
            hs |= aamp_hashes(f)
        except Exception:
            pass
    found = {}
    for w in candidates():
        for suf in [""] + [str(i) for i in range(64)]:
            n = w + suf
            c = binascii.crc32(n.encode()) & 0xFFFFFFFF
            if c in hs and c not in found:
                found[c] = n
    old = set()
    if os.path.exists(outp):
        old = set(open(outp, encoding="utf8").read().split())
    names = sorted(old | set(found.values()))
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    open(outp, "w", encoding="utf8").write("\n".join(names) + "\n")
    print("hashes %d, found %d, left %d -> %s" % (len(hs), len(found), len(hs - set(found)), outp))
    for c in sorted(hs - set(found)):
        print("  0x%08x" % c)


if __name__ == "__main__":
    main()
