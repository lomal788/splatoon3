"""text 구간을 4바이트씩 끊김 없이 디스어셈블하며 정규식에 맞는 명령을 찾는다.
사용: player_scan.py <시작> <끝> <정규식> [--then <정규식2> --win N]
--then: 첫 정규식이 맞은 뒤 N명령 안에 두 번째 정규식이 맞는 경우만 출력.
"""
import argparse, re, sys
import capstone
sys.path.insert(0, __import__('os').path.dirname(__file__))
from xref import BASE, load_img

def iter_ins(m, lo, hi):
    md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    p = lo
    while p < hi:
        n = 0
        for a, s, mn, op in md.disasm_lite(m[p:hi], BASE + p):
            yield a, mn + ' ' + op
            n += 1
        p += n * 4 + 4

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('lo'); ap.add_argument('hi'); ap.add_argument('pat')
    ap.add_argument('--then'); ap.add_argument('--win', type=int, default=12)
    a = ap.parse_args()
    m = load_img()
    lo, hi = int(a.lo, 16) - BASE, int(a.hi, 16) - BASE
    p1 = re.compile(a.pat); p2 = re.compile(a.then) if a.then else None
    pend = []
    for addr, t in iter_ins(m, lo, hi):
        if p2:
            pend = [(x, tt, k - 1) for x, tt, k in pend if k > 0]
            for x, tt, k in pend:
                if p2.search(t):
                    print(hex(x), tt, '->', hex(addr), t)
            if p1.search(t):
                pend.append((addr, t, a.win))
        elif p1.search(t):
            print(hex(addr), t)

if __name__ == '__main__':
    main()
