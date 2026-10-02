"""디컴파일 .c에 문자열·f32 상수 주석을 붙인 사본을 만든다.

사용: PY web/tools/gimmick_annot.py <입력.c> <출력.c>
- 0x71038xxxxx~0x7105xxxxxx 범위 상수가 C 문자열을 가리키면 /* "문자열" */
- 0x3c000000~0x4fffffff, 0xb...~0xc... 형태 32비트 상수는 f32 값으로 /* f=값 */
"""
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img

HEX = re.compile(r"0x([0-9a-fA-F]{6,10})\b")


def cstr(m, off):
    if not (0x3E9E000 <= off < len(m)):
        return None
    end = m.find(b"\0", off, off + 200)
    if end <= off:
        return None
    s = m[off:end]
    if len(s) < 2 or any(c < 0x20 or c > 0x7E for c in s):
        return None
    return s.decode()


PCHAIN = re.compile(r"^(\s*)if \(\(\*\(byte \*\)\(\(long\)(\w+) \+ (0x[0-9a-f]+)\) & 1\) == 0\) \{\s*$|^(\s*)if \(\(\*\(byte \*\)\((\w+) \+ (0x[0-9a-f]+)\) & 1\) == 0\) \{\s*$")


def collapse(lines):
    """파라미터 $parent 체인 탐색 블록(if((*(byte*)(p+flag)&1)==0){ while(...) } )을 한 줄로 접는다."""
    out = []
    i = 0
    while i < len(lines):
        mt = PCHAIN.match(lines[i])
        if mt and i + 3 < len(lines) and "while" in "".join(lines[i + 1:i + 6]) and "!= 0" in "".join(lines[i + 1:i + 6]):
            ind = mt.group(1) or mt.group(4) or ""
            var = mt.group(2) or mt.group(5)
            fl = int(mt.group(3) or mt.group(6), 16)
            if mt.group(5):
                fl *= 8
            depth = lines[i].count("{") - lines[i].count("}")
            j = i + 1
            while j < len(lines) and depth > 0:
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
            out.append(f"{ind}PARAM_CHAIN({var}, flag=0x{fl:x});")
            i = j
            continue
        out.append(lines[i])
        i += 1
    return out


def main():
    m = load_img()
    src, dst = sys.argv[1], sys.argv[2]
    out = []
    raw = open(src, encoding="utf-8", errors="replace").read().splitlines()
    if "--collapse" in sys.argv:
        raw = collapse(raw)
    for line in raw:
        notes = []
        for h in HEX.findall(line):
            v = int(h, 16)
            if BASE <= v < BASE + len(m):
                s = cstr(m, v - BASE)
                if s:
                    notes.append(f'"{s}"')
            elif len(h) == 8 and (0x3A000000 <= v <= 0x4F000000 or 0xBA000000 <= v <= 0xCF000000):
                f = struct.unpack("<f", struct.pack("<I", v))[0]
                notes.append(f"f={f:.7g}")
        line = line.rstrip("\n")
        if notes:
            line += "  /* " + ", ".join(notes) + " */"
        out.append(line)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
