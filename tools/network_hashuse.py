"""등록된 넷 이벤트/상태 타입의 hash32 상수가 코드에서 만들어지는 위치를 모두 찾아 함수별로 묶는다.
(등록 함수·자기 vtable 함수 제외) -> analysis/network/hashuse.tsv
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img
from disasm import func_start
from network_constscan import find_const32

ROOT = Path(__file__).resolve().parents[2]


def main():
    m = load_img()
    w = np.frombuffer(m[:TEXT_END & ~3], dtype="<u4")
    rows = list(csv.DictReader(open(ROOT / "analysis/network/nettypes.tsv", encoding="utf-8"), delimiter="\t"))
    out = open(ROOT / "analysis/network/hashuse.tsv", "w", encoding="utf-8", newline="")
    out.write("kind\tname\thash32\tsite\tfunc\n")
    for r in rows:
        h = int(r["hash32"], 16)
        own = set()
        for k in ("write", "read", "getname", "reset", "equals", "copy", "bits_a", "bits_b"):
            if r[k]:
                own.add(int(r[k], 16))
        for site in find_const32(w, h):
            f = func_start(m, site, 0x40000)
            fa = BASE + f if f is not None else 0
            out.write(f"{r['kind']}\t{r['name']}\t{r['hash32']}\t{BASE + site:#x}\t{fa:#x}\n")
    out.close()


if __name__ == "__main__":
    main()
