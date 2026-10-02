"""함수 주소 → 그 함수를 슬롯으로 가진 vtable과 클래스 이름(슬롯 2 getName 문자열).

사용: PY web/tools/combat4_owner.py <함수주소...> [--up N]
- 데이터 영역에서 함수 포인터를 담은 위치를 모두 찾고, 그 앞쪽 최대 300슬롯 안에서
  슬롯 2가 'adrp x0; add x0; ret'(문자열 반환)인 vtable 시작을 찾아 (클래스, 슬롯 번호)를 출력한다.
- 포인터가 없으면(직접 호출만 되는 함수) --up N 이면 BL 호출자 함수로 N단계까지 올라가 같은 검사를 한다.
결과는 [판독] 수준의 "소속 추정"이다: 같은 함수를 여러 vtable이 공유할 수 있다.
"""
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import func_lookup  # noqa: E402

B = 0x7100000000
ROOT = Path(__file__).resolve().parents[2]
img = (ROOT / "extracted" / "exefs" / "main.reloc.img").read_bytes()
raw = (ROOT / "extracted" / "exefs" / "main.img").read_bytes()
TEXT_END = 0x3E9DF50
q64 = np.frombuffer(img[: len(img) // 8 * 8], dtype="<u8")


def q(a):
    return struct.unpack_from("<Q", img, a - B)[0]


def u32(a):
    return struct.unpack_from("<I", raw, a - B)[0]


def strret(fn):
    try:
        i0, i1, i2 = u32(fn), u32(fn + 4), u32(fn + 8)
    except struct.error:
        return None
    if (i0 & 0x9F00001F) == 0x90000000 and (i1 & 0xFFC003FF) == 0x91000000 and i2 == 0xD65F03C0:
        immlo = (i0 >> 29) & 3
        immhi = (i0 >> 5) & 0x7FFFF
        imm = ((immhi << 2) | immlo) << 12
        if imm & (1 << 32):
            imm -= 1 << 33
        a = (fn & ~0xFFF) + imm + ((i1 >> 10) & 0xFFF)
        return raw[a - B: a - B + 100].split(b"\0")[0].decode("latin1")
    return None


def owners(fn):
    out = []
    for idx in np.nonzero(q64 == fn)[0]:
        p = B + int(idx) * 8
        if p < B + TEXT_END:
            continue
        for k in range(0, 300):
            v = p - 8 * k
            try:
                g = q(v + 16)
            except struct.error:
                break
            if not (B <= g < B + TEXT_END):
                continue
            nm = strret(g)
            if nm and (nm.startswith("spl") or nm.startswith("game") or "::" in nm or ":" in nm):
                out.append((p, v, k, nm))
                break
    return out


def bl_callers(target):
    res = []
    m = memoryview(raw)[: TEXT_END].cast("I")
    arr = np.frombuffer(raw[:TEXT_END], dtype="<u4")
    isbl = (arr & 0xFC000000) == 0x94000000
    isb = (arr & 0xFC000000) == 0x14000000
    idxs = np.nonzero(isbl | isb)[0]
    imm = (arr[idxs] & 0x03FFFFFF).astype(np.int64)
    imm = np.where(imm & 0x02000000, imm - 0x04000000, imm)
    tgt = B + idxs.astype(np.int64) * 4 + imm * 4
    for i in np.nonzero(tgt == target)[0]:
        res.append(B + int(idxs[i]) * 4)
    return res


def main():
    args = [a for a in sys.argv[1:] if a.startswith("0x")]
    up = int(sys.argv[sys.argv.index("--up") + 1]) if "--up" in sys.argv else 0
    starts, rows = func_lookup.load()
    for a in args:
        fn = int(a, 16)
        frontier = [(fn, [])]
        seen = set()
        for depth in range(up + 1):
            nxt = []
            for f, path in frontier:
                if f in seen:
                    continue
                seen.add(f)
                ow = owners(f)
                for p, v, k, nm in ow:
                    print(f"{a}: {' <- '.join(hex(x) for x in path + [f])}  vtable {v:#x} slot {k} (+{k*8:#x})  {nm}")
                if not ow and depth < up:
                    for c in bl_callers(f):
                        r = func_lookup.lookup(starts, rows, c)
                        if r:
                            nxt.append((r[0], path + [f]))
            frontier = nxt


if __name__ == "__main__":
    main()
