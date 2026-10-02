import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = 0x7100000000
TEXT = 0x3E9DF50
m = (ROOT / "extracted/exefs/main.reloc.img").read_bytes()
w = np.frombuffer(m[:TEXT], dtype="<u4").astype(np.int64)
isbl = (w & 0xFC000000) == 0x94000000
isb = (w & 0xFC000000) == 0x14000000
imm = w & 0x3FFFFFF
imm = np.where(imm & 0x2000000, imm - 0x4000000, imm)
pc = np.arange(len(w), dtype=np.int64) * 4
tgt = pc + imm * 4
for a in sys.argv[1:]:
    t = int(a, 16) - BASE
    bl = np.nonzero(isbl & (tgt == t))[0]
    b = np.nonzero(isb & (tgt == t))[0]
    print(a, "bl:", " ".join(hex(BASE + int(i) * 4) for i in bl[:60]), "| b:", " ".join(hex(BASE + int(i) * 4) for i in b[:20]))
