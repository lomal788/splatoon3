import re
import sys

GUARD = re.compile(r"^\s*if \(\(\(DAT_\w+ & 1\) == 0\) &&")


def fold(lines):
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^(\s*)if \(\(\*\(byte \*\)\((?:\(long\))?(\w+) \+ (0x[0-9a-f]+)\) & 1\) == 0\) \{$", ln)
        m2 = re.match(r"^(\s*)if \(\(\(?bVar\d+ & 1\) == 0\)\)? \{$", ln)
        mw = re.match(r"^(\s*)while \(", ln)
        if (m or m2) and any("while" in lines[j] for j in range(i + 1, min(i + 3, len(lines)))) and \
                any("__cxa_guard_acquire" in lines[j] for j in range(i + 1, min(i + 12, len(lines)))):
            ind = (m or m2).group(1)
            depth = 0
            j = i
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0:
                    break
                j += 1
            tag = f"{m.group(2)} flag {m.group(3)}" if m else "flag"
            out.append(f"{ind}/* parent chain: {tag} */")
            i = j + 1
            continue
        if mw and any("__cxa_guard_acquire" in lines[j] for j in range(i + 1, min(i + 10, len(lines)))):
            ind = mw.group(1)
            depth = 0
            j = i
            started = False
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if "{" in lines[j]:
                    started = True
                if started and depth == 0:
                    break
                j += 1
            out.append(f"{ind}/* parent chain (while) */")
            i = j + 1
            continue
        if GUARD.match(ln):
            depth = 0
            j = i
            started = False
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if "{" in lines[j]:
                    started = True
                if started and depth == 0:
                    break
                j += 1
            i = j + 1
            continue
        out.append(ln)
        i += 1
    return out


def main():
    path, *names = sys.argv[1:]
    names = [n.lower().replace("0x", "") for n in names]
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
        addr = b[0].split()[2].lower()
        if not names or addr in names:
            print("\n".join(fold(b)))


if __name__ == "__main__":
    main()
