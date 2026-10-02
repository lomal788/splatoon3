import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECOMP = ROOT / "analysis" / "decomp"
OUT = DECOMP / "INDEX.tsv"
FUNCS = ROOT / "analysis" / "notes" / "FUNCS.tsv"

HEAD = re.compile(r"^// ==== ([0-9a-fA-F]+) (\S+)")


def build():
    rows = {}
    for f in sorted(DECOMP.rglob("*.c")):
        rel = f.relative_to(DECOMP).as_posix()
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = HEAD.match(line)
                if m:
                    rows.setdefault(int(m.group(1), 16), (m.group(2), rel))
    with open(OUT, "w", encoding="utf-8") as w:
        w.write("address\tname\tfile\n")
        for a in sorted(rows):
            w.write(f"{a:x}\t{rows[a][0]}\tanalysis/decomp/{rows[a][1]}\n")
    return rows


def load():
    rows = {}
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines()[1:]:
            a, n, f = line.split("\t")
            rows[int(a, 16)] = (n, f)
    return rows


def load_funcs():
    names = {}
    if FUNCS.exists():
        for line in FUNCS.read_text(encoding="utf-8").splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].strip():
                try:
                    names.setdefault(int(parts[0], 16), []).append(parts[1:])
                except ValueError:
                    pass
    return names


def parse_addr(s):
    v = int(s, 16)
    return v if v >= 0x7100000000 else v + 0x7100000000


def main():
    ap = argparse.ArgumentParser(description="디컴파일 색인(analysis/decomp/INDEX.tsv) 갱신·조회")
    ap.add_argument("queries", nargs="*", help="주소(16진) 또는 FUNCS.tsv 이름 일부")
    ap.add_argument("--missing", action="store_true", help="색인에 없는 주소만 공백 구분으로 출력")
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args()
    rows = load() if a.no_build or a.missing else build()
    if a.missing:
        print(" ".join(f"0x{parse_addr(q):x}" for q in a.queries if parse_addr(q) not in rows))
        return
    funcs = load_funcs()
    sys.stdout.reconfigure(encoding="utf-8")
    if not a.queries:
        print(f"{len(rows)} functions indexed -> {OUT}")
        return
    for q in a.queries:
        try:
            addr = parse_addr(q)
        except ValueError:
            addr = None
        if addr is not None:
            r = rows.get(addr)
            print(f"0x{addr:x}\t{r[1] if r else '(디컴파일 없음)'}\t" + " | ".join("/".join(x) for x in funcs.get(addr, [])))
        else:
            for fa, entries in sorted(funcs.items()):
                for e in entries:
                    if q.lower() in e[0].lower():
                        r = rows.get(fa)
                        print(f"0x{fa:x}\t{'/'.join(e)}\t{r[1] if r else '(디컴파일 없음)'}")


if __name__ == "__main__":
    main()
