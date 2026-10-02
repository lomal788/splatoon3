import bisect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TSV = ROOT / "analysis" / "functions" / "main.nso.tsv"


def load():
    starts, rows = [], []
    with open(TSV, encoding="utf-8") as f:
        next(f)
        for line in f:
            a, size, name, sig = line.rstrip("\n").split("\t", 3)
            starts.append(int(a, 16))
            rows.append((int(size), name))
    return starts, rows


def lookup(starts, rows, addr):
    i = bisect.bisect_right(starts, addr) - 1
    if i < 0:
        return None
    return starts[i], rows[i][0], rows[i][1]


def main():
    """Ghidra 전체 분석 함수 목록으로 주소가 속한 함수 시작을 찾는다. size는 함수 본문 바이트 수(떨어진 블록 포함)."""
    starts, rows = load()
    for q in sys.argv[1:]:
        a = int(q, 16)
        a = a if a >= 0x7100000000 else a + 0x7100000000
        r = lookup(starts, rows, a)
        print(f"{a:#x}\t" + (f"func {r[0]:#x}\tsize {r[1]}\t{r[2]}" if r else "없음"))


if __name__ == "__main__":
    main()
