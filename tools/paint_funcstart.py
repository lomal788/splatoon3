import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import disasm
m = Path(disasm.__file__).resolve().parents[2].joinpath("extracted/exefs/main.reloc.img").read_bytes()
seen = {}
for a in sys.argv[1:]:
    off = int(a, 16) - 0x7100000000
    s = disasm.func_start(m, off)
    seen.setdefault(s, []).append(a)
for s, refs in seen.items():
    print(hex(0x7100000000 + s) if s is not None else None, " ".join(refs))
