"""r5 fx: Alto 그룹 제한기 적용 0x71038473e8 원본 실행 대조 (정렬 뒤 어느 보이스가 남는지).

원본: 0x71038473e8(limiter, list) → 종류 1 정렬(vt slot3 0x7103847950, 비교 0x7103848c88) → 앞에서 limitCount 개는
limiter 비트 해제(비트가 모두 0 이 되면 핸들 상태 3→4), 나머지는 limiter+0xc==0 이면 0x710383cffc(핸들 종류 1 = 정지,
그 밖 = 비트 세움+일시정지), 아니면 0x710383d940(0,0) 즉시 정지.
재구현(독립): 우선순위 key = int(f32(f32(c4*cc)*factor)*255) 내림차순, 같으면 +8 오름차순으로 정렬하고 위 규칙 적용.
스텁: nn::os::Lock/UnlockMutex PLT(0x7103e99fd0/0x7103e99ff0) no-op, 0x71037dfde4(핸들 정지)·0x71037e019c(핸들 일시정지)·
0x710383da0c(페이드 정지)·0x71037dca78·0x7103862298 은 호출 기록만. 정렬·비교·분기·비트·상태 기록은 원본 그대로 실행.
"""
import json, random, struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_LR, UC_ARM64_REG_PC
from network_uc import UC

ROOT = Path(__file__).resolve().parents[2]
f = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
STUBS = {0x7103e99fd0: 'lock', 0x7103e99ff0: 'unlock', 0x71037dfde4: 'handle_stop', 0x71037e019c: 'handle_pause',
         0x710383da0c: 'fade_stop', 0x71037dca78: 'detach', 0x7103862298: 'misc'}
VPTR1 = 0x7105734878 + 0x10
NODE = 0x230


def main():
    u = UC(); m = u.mu
    calls = []
    def hook(mu, addr, size, ud):
        calls.append((STUBS[addr], mu.reg_read(UC_ARM64_REG_X0)))
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
    for a in STUBS:
        m.hook_add(UC_HOOK_CODE, hook, begin=a, end=a)
    rng = random.Random(0x71038473e8)
    lim = u.alloc(0x40); lst = u.alloc(0x20)
    voices = [u.alloc(0x260) for _ in range(12)]
    handles = [u.alloc(0x80) for _ in range(12)]
    exts = [u.alloc(0x20) for _ in range(12)]
    stats = {'cases': 0, 'survive': 0, 'stopped': 0, 'paused': 0, 'skipped_flag': 0}
    for case in range(600):
        n = rng.randint(1, 12)
        limit = rng.choice([-1, 0, 1, 2, 3, 4, 6, n, n + 1])
        hard = rng.random() < 0.3      # limiter+0xc (GRP [0x18] byte3)
        bit = rng.randint(0, 3)
        m.mem_write(lim, b'\0' * 0x40)
        m.mem_write(lim, struct.pack('<Q', VPTR1)); u.u32(lim + 8, limit)
        m.mem_write(lim + 0xc, bytes([1 if hard else 0, 0, 0])); u.f32(lim + 0x10, 0.2); u.u32(lim + 0x14, bit)
        vs = []
        used = set()
        for i in range(n):
            v, h, e = voices[i], handles[i], exts[i]
            m.mem_write(v, b'\0' * 0x260); m.mem_write(h, b'\0' * 0x80); m.mem_write(e, b'\0' * 0x20)
            while True:
                c4 = f(rng.choice([0.25, 0.5, 0.75, 1.0, rng.uniform(0, 1)])); cc = f(rng.uniform(0.1, 1.0)); fac = f(rng.choice([1.0, rng.uniform(0.2, 1)]))
                order = rng.randint(0, 40)
                key = int(f(f(f(c4 * cc) * fac) * 255))
                if (key, order) not in used: used.add((key, order)); break
            state = rng.choice([1, 2, 3, 3, 4, 6, 7])
            bits = rng.choice([0, 0, 1 << bit])
            htype = rng.choice([1, 1, 2])
            flag = 2 if rng.random() < 0.1 else 0
            u.u32(v + 4, state); u.u32(v + 8, order); m.mem_write(v + 0xe, bytes([bits]))
            u.f32(v + 0xc4, c4); u.f32(v + 0xcc, cc); m.mem_write(v + 0x210, struct.pack('<Q', e)); u.f32(e + 0x18, fac)
            m.mem_write(v + 0x1f8, bytes([flag])); m.mem_write(v + 0xe0, struct.pack('<Q', h))
            u.u32(h + 0x10, 3); u.u32(h + 0x14, htype); u.u32(h + 0x24, 0x55)
            vs.append(dict(v=v, h=h, key=key, order=order, state=state, bits=bits, htype=htype, flag=flag))
        # 리스트(센티넬 lst: +0 마지막, +8 첫째, +0x10 개수, +0x14 노드 오프셋)
        rng.shuffle(vs)
        prev = lst
        for x in vs:
            node = x['v'] + NODE
            m.mem_write(prev + 8, struct.pack('<Q', node)); m.mem_write(node, struct.pack('<Q', prev)); prev = node
        m.mem_write(prev + 8, struct.pack('<Q', lst)); m.mem_write(lst, struct.pack('<Q', prev))
        u.u32(lst + 0x10, n); u.u32(lst + 0x14, NODE)
        calls.clear()
        u.call(0x71038473e8, lim, lst)
        # 원본 결과 읽기
        got_order = []
        p = struct.unpack('<Q', m.mem_read(lst + 8, 8))[0]
        while p != lst:
            got_order.append(p - NODE); p = struct.unpack('<Q', m.mem_read(p + 8, 8))[0]
        # 기대값 (limit < 0 이면 정렬 없음)
        if limit > 0:
            exp_sorted = sorted(vs, key=lambda x: (-x['key'], x['order']))
            assert got_order == [x['v'] for x in exp_sorted], (case, 'order')
            seq = exp_sorted
        else:
            assert got_order == [x['v'] for x in vs], (case, 'order-unsorted')
            seq = vs
        exp_calls = []
        cnt = 0
        for x in seq:
            v = x['v']
            bits_now = m.mem_read(v + 0xe, 1)[0]; st_now = struct.unpack('<I', m.mem_read(v + 4, 4))[0]
            hst = struct.unpack('<I', m.mem_read(x['h'] + 0x10, 4))[0]
            if limit < 0:
                if (x['state'] & ~1) != 6:
                    exp_bits = x['bits'] & ~(1 << bit)
                    assert bits_now == exp_bits
                    if x['bits'] and not exp_bits:
                        exp_calls += [('lock', x['h'] + 0x48), ('unlock', x['h'] + 0x48)]
                        assert hst == 4
                continue
            if limit == 0:
                if not (x['flag'] & 2) and x['htype'] != 0:
                    exp_calls += handle_suppress(x, hard, bit, m, stats)
                continue
            if x['flag'] & 2:
                stats['skipped_flag'] += 1
                assert bits_now == x['bits'] and st_now == x['state']
                continue
            if cnt < limit:
                if (x['state'] & ~1) != 6:
                    exp_bits = x['bits'] & ~(1 << bit)
                    assert bits_now == exp_bits, (case, 'bits')
                    if x['bits'] and not exp_bits:
                        exp_calls += [('lock', x['h'] + 0x48), ('unlock', x['h'] + 0x48)]
                        assert hst == 4
                stats['survive'] += 1
            else:
                exp_calls += handle_suppress(x, hard, bit, m, stats)
            cnt += 1
        got_calls = [(k, a) for k, a in calls]
        assert got_calls == exp_calls, (case, got_calls, exp_calls)
        stats['cases'] += 1
    out = {'cases_bit_match': stats['cases'], 'survivors': stats['survive'], 'stopped': stats['stopped'], 'paused': stats['paused'],
           'flag_skipped': stats['skipped_flag'], 'limiter_type': 1,
           'stubs': [f'{hex(a)} {k}' for a, k in STUBS.items()],
           'limits': ['종류 2~4 정렬은 실행 안 함(비교 함수는 기존 completion_limiter_compare_emu.py 2304건)',
                      'limiter+0xe 타이머 분기(fade 0.2s)는 꺼진 상태만', '핸들 정지/일시정지 함수 내부는 스텁']}
    (ROOT / 'analysis/completion/r5').mkdir(parents=True, exist_ok=True)
    (ROOT / 'analysis/completion/r5/fx_limiter_core_emu.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False))


def handle_suppress(x, hard, bit, m, stats):
    """0x710383cffc / 0x710383d940(0,0) 의 기대 호출 (독립 재구현)."""
    st = x['state']
    if (st & ~1) == 6:
        return []
    if hard:
        stats['stopped'] += 1
        return [('fade_stop', x['v'])] if st > 2 else [('handle_stop', x['h'])]
    if x['htype'] == 1:
        stats['stopped'] += 1
        return [('handle_stop', x['h'])] if st < 3 else [('fade_stop', x['v'])]
    stats['paused'] += 1
    return [('handle_pause', x['h'])] if x['bits'] == 0 else []


if __name__ == '__main__':
    main()
