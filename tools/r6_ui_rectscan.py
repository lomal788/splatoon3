"""레이아웃 크기(+0x28/+0x2c, Layout::Build 0x7100857b58 가 lyt1+0xc/+0x10 에서 복사)를 읽고 0.5 를 곱하는 함수 찾기."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from r6_ui_lib import *

w = words()
hits = {}
for i in range(len(w)):
    x = int(w[i])
    # ldp s,s,[xn,#0x28]  : 0x2D400000 | imm7=(0x28/4)=10 <<15
    if (x & 0xFFC00000) == 0x2D400000 and ((x >> 15) & 0x7F) == 10:
        a = BASE + i * 4
        win = dis(a, 12)
        txt = " ; ".join(f"{d.mnemonic} {d.op_str}" for d in win)
        if "#0.5" in txt or "fneg" in txt:
            f, _ = func_of(a)
            hits.setdefault(f, []).append((a, txt))
for f, l in hits.items():
    for a, t in l:
        out(hex(f), hex(a), t[:300])
out(len(hits))
