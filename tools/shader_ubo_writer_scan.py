"""main 코드 범위에서 같은 기준 레지스터에 지정 오프셋들을 함께 쓰는(str) 함수를 찾는다.
사용: PY web/tools/shader_ubo_writer_scan.py <시작> <끝> <오프셋,...> [최소일치수] [창 크기(16진, 기본 0x200)]
예: ... 0x7102c00000 0x7102d00000 0x68,0x6c,0x70,0x10 3
"""
import sys, struct, collections
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_MEM
IMG = r'C:/dev/splatoon3/extracted/exefs/main.reloc.img'
BASE = 0x7100000000
s, e = int(sys.argv[1], 16), int(sys.argv[2], 16)
offs = [int(x, 16) for x in sys.argv[3].split(',')]
need = int(sys.argv[4]) if len(sys.argv) > 4 else len(offs)
WIN = int(sys.argv[5], 16) if len(sys.argv) > 5 else 0x200
img = open(IMG, 'rb').read()
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM); md.detail = True
code = img[s - BASE:e - BASE]
win = collections.deque()
hits = collections.defaultdict(set)
def stream():
    """무효 명령(코드 사이 데이터)에서 멈추지 않도록 4바이트씩 건너뛰며 계속 디스어셈블."""
    pos = 0
    while pos < len(code):
        last = None
        for ins in md.disasm(code[pos:], s + pos):
            last = ins
            yield ins
        pos = (last.address - s + 4) if last is not None else pos
        pos += 4  # 멈춘 자리(무효 워드) 건너뜀


for ins in stream():
    if ins.mnemonic.startswith('st') and ins.operands and ins.operands[-1].type == ARM64_OP_MEM:
        m = ins.operands[-1].mem
        if m.disp in offs:
            win.append((ins.address, m.base, m.disp))
    while win and ins.address - win[0][0] > WIN:
        win.popleft()
    byb = collections.defaultdict(set)
    for a, b, d in win:
        byb[b].add(d)
    for b, ds in byb.items():
        if len(ds) >= need:
            hits[win[0][0] & ~0xfff].add(min(a for a, bb, d in win if bb == b))
for k in sorted(hits):
    print(hex(k), [hex(x) for x in sorted(hits[k])][:8])
