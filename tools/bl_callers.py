import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from disasm import func_start
from xref import BASE, TEXT_END, load_img


def main():
    m = load_img()
    w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
    isbl = (w & 0xFC000000) == 0x94000000
    isb = (w & 0xFC000000) == 0x14000000
    idx = np.nonzero(isbl | isb)[0]
    imm = (w[idx] & 0x03FFFFFF).astype(np.int64)
    imm = np.where(imm & (1 << 25), imm - (1 << 26), imm)
    tgt = idx.astype(np.int64) * 4 + imm * 4
    for q in sys.argv[1:]:
        t = int(q, 16) - BASE
        for i in np.nonzero(tgt == t)[0]:
            a = int(idx[i]) * 4
            fs = func_start(m, a)
            kind = "bl" if isbl[idx[i]] else "b"
            print(f"{q} <- {kind} {BASE + a:#x} (func {BASE + fs:#x})" if fs else f"{q} <- {kind} {BASE + a:#x}")


if __name__ == "__main__":
    main()
