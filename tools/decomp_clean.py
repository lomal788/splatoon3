import re
import sys

BOILER = re.compile(
    r"func_0x007103e99ef0|func_0x007103e99f00|^\s*\*pl\w+ = l(Var\d+|Ram\w+)( \+ 0x10)?;$|"
    r"^\s*(pl|pb)Var\d+ = (pl|pb)Ram\w+;$|^\s*(pl|pb)Ram\w+ = (pl|pb)Var\d+;$|"
    r"^\s*lVar\d+ = lRam0000007105(790298|794530) \+ 0x10;$"
)


def clean(lines):
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^(\s*)if \(\(\*\(byte \*\)\((?:\(long\))?(\w+) \+ (0x[0-9a-f]+)\) & 1\) == 0\) \{$", ln) or \
            re.match(r"^(\s*)if \(\(\*\(byte \*\)\((\w+) \+ (0x[0-9a-f]+)\) & 1\) == 0\) \{$", ln)
        if m and i + 3 < len(lines) and any("while" in lines[j] for j in range(i + 1, min(i + 6, len(lines)))):
            ind = m.group(1)
            depth = 0
            j = i
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0:
                    break
                j += 1
            out.append(f"{ind}/* 상속 조회: {m.group(2)} = 플래그 {m.group(3)}가 켜진 부모 파라미터 */")
            i = j + 1
            continue
        if not BOILER.search(ln):
            out.append(ln)
        i += 1
    return out


def main():
    path, *names = sys.argv[1:]
    text = open(path, encoding="utf-8").read().split("\n")
    blocks = []
    cur = None
    for ln in text:
        if ln.startswith("// ==== "):
            cur = [ln]
            blocks.append(cur)
        elif cur is not None:
            cur.append(ln)
    sys.stdout.reconfigure(encoding="utf-8")
    for b in blocks:
        addr = b[0].split()[2]
        if not names or addr in names:
            print("\n".join(clean(b)))


if __name__ == "__main__":
    main()
