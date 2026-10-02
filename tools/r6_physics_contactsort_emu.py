"""[r6 physics] 접촉 목록 정렬 0x7103a6144c 원본 실행 대조 (모드 3 = 비율 f 오름차순 힙 정렬).

목록 L: +8 개수(s32), +0x28 용량(u32), +0x30 항목 배열(16 B: +0 접촉 포인터, +8 바이트 플래그), +0xc0 정렬 모드.
접촉 C: +0x60 비율 f(f32), +0x68 플래그(u16). 키(C) = (C+0x68 & 0x1060) ? C+0x60 : 0.0
탄 바디 목록은 생성 0x7103b0af78 의 0x7103b0b230~238 이 모드 3 으로 둔다.
재구현: 아래 heap_sort_mode3 (원본 명령 판독을 옮긴 1-기반 최대 힙 정렬, 불안정).
스텁 없음(잎 함수, 외부 호출 없음). 출력: analysis/completion/r6/physics_contactsort_emu.json
"""
import json, random, struct, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FN = 0x7103a6144c


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def heap_sort_mode3(items, key):
    """items: list of (id, flag). 원본 0x7103a61738~ 의 순서를 그대로 따른다."""
    a = list(items)
    n = len(a)
    if n < 2:
        return a
    A = lambda i: a[i - 1]  # 1-기반
    j = n >> 1
    while True:
        v = a[j - 1]
        pos = j
        c2 = 2 * j
        while c2 <= n:
            c = c2
            if c2 < n and key(A(c2)) < key(A(c2 + 1)):
                c = c2 + 1
            if key(A(c)) <= key(v):
                break
            a[pos - 1] = A(c)
            pos = c
            c2 = 2 * c
        a[pos - 1] = v
        if j <= 1:
            break
        j -= 1
    last = n - 1
    v = a[last]
    a[last] = a[0]
    m = n
    while m > 2:
        heap = m - 1
        pos = 1
        c2 = 2
        while True:
            c = c2
            if c2 < heap and key(A(c2)) < key(A(c2 + 1)):
                c = c2 + 1
            if key(A(c)) <= key(v):
                break
            a[pos - 1] = A(c)
            pos = c
            c2 = 2 * c
            if not c2 < m:
                break
        a[pos - 1] = v
        last -= 1
        v = a[last]
        a[last] = a[0]
        m -= 1
    a[0] = v
    return a


def run(cases=3000, seed=20261003):
    h = UC()
    mu = h.mu
    rng = random.Random(seed)
    lst = h.alloc(0x100)
    arr = h.alloc(64 * 16)
    cons = [h.alloc(0x80) for _ in range(64)]
    mism, samples, ties_cases = [], [], 0
    for ci in range(cases):
        n = rng.choice([0, 1, 2, 3, 4, 5, 7, 8, 13, 16, 31, 32, 33, 50, 64])
        pool = [0.0, 0.25, 0.5, 0.5, 1.0, f32(rng.random())]
        items, meta = [], {}
        for k in range(n):
            fv = rng.choice(pool) if rng.random() < 0.6 else f32(rng.random())
            fl = rng.choice([0x0000, 0x0002, 0x0020, 0x0040, 0x1000, 0x1062, 0x0001])
            c = cons[k]
            h.f32(c + 0x60, fv)
            mu.mem_write(c + 0x68, struct.pack("<H", fl))
            flag = rng.randrange(256)
            items.append((k, flag))
            meta[k] = (fv, fl)
            mu.mem_write(arr + 16 * k, struct.pack("<QQ", c, flag))
        cap = n if rng.random() < 0.9 else max(0, n - 2)
        mu.mem_write(lst + 8, struct.pack("<i", n))
        mu.mem_write(lst + 0x28, struct.pack("<I", cap))
        mu.mem_write(lst + 0x30, struct.pack("<Q", arr))
        mu.mem_write(lst + 0xc0, struct.pack("<I", 3))
        h.call(FN, lst)
        got = []
        for k in range(n):
            p, fl = struct.unpack("<QQ", bytes(mu.mem_read(arr + 16 * k, 16)))
            got.append((cons.index(p), fl & 0xFF))
        key = lambda e: meta[e[0]][0] if (meta[e[0]][1] & 0x1060) else 0.0
        exp = heap_sort_mode3(items, key) if (n >= 2 and n - 1 < cap) else list(items)
        keys = [key(e) for e in exp]
        if len(set(keys)) < len(keys):
            ties_cases += 1
        ok = got == exp
        row = {"case": ci, "n": n, "cap": cap, "keys_in": [key(e) for e in items], "original": got, "reimpl": exp}
        if ci < 3:
            samples.append(row)
        if not ok:
            mism.append(row)
    out = {"function": hex(FN), "mode": 3, "cases": cases, "passed": cases - len(mism),
           "cases_with_equal_keys": ties_cases, "mismatches": mism[:20], "samples": samples,
           "stubs": [], "notes": ["항목 16 B 의 플래그 바이트도 함께 이동하는지 비교", "용량 조건 count-1 < cap 불충족 시 무변경"]}
    p = ROOT / "analysis/completion/r6/physics_contactsort_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"contact sort mode3: {out['passed']}/{cases} 일치 (같은 키 포함 {ties_cases}건) -> {p}")
    return out


if __name__ == "__main__":
    run()
