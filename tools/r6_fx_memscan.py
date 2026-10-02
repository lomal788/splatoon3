"""r6 fx: 범위 안에서 특정 오프셋 ldr/str 명령을 전수 검색(명령 단위 디코드).
사용: PY web/tools/r6_fx_memscan.py <start> <end> <off> [str|ldr|any] [reg-regex]
"""
import sys, re, struct
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
sys.stdout.reconfigure(encoding="utf-8")
IMG = open('C:/dev/splatoon3/extracted/exefs/main.reloc.img', 'rb').read()
B = 0x7100000000
s, e, off = int(sys.argv[1], 16), int(sys.argv[2], 16), int(sys.argv[3], 16)
kind = sys.argv[4] if len(sys.argv) > 4 else 'any'
rx = re.compile(sys.argv[5]) if len(sys.argv) > 5 else None
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
pat = re.compile(r'\[(\w+), #(-?0x[0-9a-f]+|\d+)\]')
for a in range(s, e, 4):
    w = IMG[a - B:a - B + 4]
    ins = next(md.disasm(w, a), None)
    if ins is None:
        continue
    m = ins.mnemonic
    if kind == 'str' and not m.startswith('st'):
        continue
    if kind == 'ldr' and not m.startswith('ld'):
        continue
    if not (m.startswith('st') or m.startswith('ld')):
        continue
    for mm in pat.finditer(ins.op_str):
        if int(mm.group(2), 0) == off:
            if rx and not rx.search(ins.op_str):
                continue
            print(hex(a), m, ins.op_str)
