import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img


def main():
    m = load_img()
    args = sys.argv[1:]
    n = 16
    if "-n" in args:
        i = args.index("-n")
        n = int(args[i + 1], 0)
        del args[i:i + 2]
    for a in args:
        a = int(a, 16)
        for k in range(n):
            o = a - BASE + 8 * k
            v = struct.unpack_from("<Q", m, o)[0]
            print(f"{a + 8 * k:#x} [{k:2}] {v:#x}")


if __name__ == "__main__":
    main()
