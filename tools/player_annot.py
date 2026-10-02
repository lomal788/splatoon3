"""디컴파일 .c 안의 bss 전역(fRam/iRam/uRam/bRam/DAT_)에 player_initemu.py로 뽑은 초기값을 주석으로 붙인다.

사용: player_annot.py <입력.c> <출력.c> <상수.json...>
"""
import json
import re
import struct
import sys
from pathlib import Path


def main():
    src, dst, *jsons = sys.argv[1:]
    vals = {}
    for j in jsons:
        for k, v in json.loads(Path(j).read_text(encoding="utf-8")).items():
            vals[int(k, 16)] = v["u32"]

    def rep(m):
        kind, addr = m.group(1), int(m.group(2), 16)
        base = addr & ~3
        if base not in vals:
            return m.group(0) + "/*=0*/" if kind in "fi" else m.group(0)
        u = vals[base]
        if kind == "f":
            return f"{m.group(0)}/*={struct.unpack('<f', struct.pack('<I', u))[0]:.9g}*/"
        if kind in ("i", "u"):
            return f"{m.group(0)}/*={struct.unpack('<i', struct.pack('<I', u))[0]}*/"
        return m.group(0) + f"/*=0x{u:08x}*/"

    text = Path(src).read_text(encoding="utf-8")
    text = re.sub(r"\b([fiub])Ram000000(7105[0-9a-f]{6})\b", rep, text)
    Path(dst).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
