"""r5 camweapon: BulletShooterBase 슬롯108 0x7101753c00(꼬리 최대 길이)을 원본 실행해 독립 식과 비트 비교.

독립 식(문서 shooter_bullet.md §3.4):
  t = f32(f32(age - Delay) / f32(MaxLengthFrame))
  t >= 1 -> End ; t <= 0 또는 NaN -> Start ; 그 밖 Start + t*(End - Start)  (0x710175406c b.ge, 0x7101754078 b.le)
스텁: 파라미터 형식 검사 vt[0] -> 1(가짜 코드 mov w0,#1;ret), __cxa_guard_acquire(0x7103e99ef0) -> 0,
      설정됨 플래그(+0x40..+0x43)는 모두 1 로 두어 부모 사슬 걷기는 실행하지 않음(부모 상속은 이 검증 범위 밖).
쓰는 파일: analysis/completion/r5/camweapon_tail_emu.json
"""
import json, random, struct, sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC, END

ROOT = Path(__file__).resolve().parents[2]
F = np.float32


def w64(e, a, v): e.mu.mem_write(a, struct.pack('<Q', v))


def independent(age, delay, maxf, start, end):
    with np.errstate(all='ignore'):
        t = F(F(np.int32(age - delay)) / F(maxf))
    if t >= F(1):                       # b.ge: NaN 은 거짓
        return F(end)
    if not (t > F(0)):                  # b.le: NaN 은 참 -> Start
        return F(start)
    return F(F(start) + F(t * F(F(end) - F(start))))


def main():
    e = UC()
    code = e.alloc(0x10)
    e.mu.mem_write(code, struct.pack('<II', 0x52800020, 0xD65F03C0))  # mov w0,#1 ; ret
    vt = e.alloc(0x40); w64(e, vt, code)
    param = e.alloc(0x80); w64(e, param, vt)
    e.mu.mem_write(param + 0x40, b'\x01\x01\x01\x01')
    handle = e.alloc(0x20); w64(e, handle, param); e.u32(handle + 0xc, 7)
    info = e.alloc(0x200); w64(e, info + 0x140, handle); e.u32(info + 0x148, 7)
    bullet = e.alloc(0x1300); w64(e, bullet + 0x108, info)

    def hook(mu, addr, size, ud):
        if addr == 0x7103e99ef0 or 0x7103e99000 <= addr < 0x7103e9e000:
            mu.reg_write(UC_ARM64_REG_X0, 0); mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
    e.mu.hook_add(UC_HOOK_CODE, hook, begin=0x7103e99000, end=0x7103e9e000)

    rnd = random.Random(1753)
    cases = []
    for age in range(-1, 40):
        cases.append((age, 3, 6, 0.0, 1.0))
    for _ in range(400):
        cases.append((rnd.randint(-2, 120), rnd.randint(0, 20), rnd.randint(1, 60), rnd.uniform(-5, 20), rnd.uniform(-5, 20)))
    cases += [(5, 3, 0, 1.5, 4.0), (3, 3, 0, 1.5, 4.0), (1, 3, 0, 1.5, 4.0), (5, 3, -4, 1.5, 4.0)]
    rows = []; ok = 0
    for age, delay, maxf, start, end in cases:
        e.u32(bullet + 0x134, age & 0xffffffff)
        e.u32(param + 0x30, delay); e.u32(param + 0x38, maxf & 0xffffffff)
        e.f32(param + 0x3c, start); e.f32(param + 0x34, end)
        e.call(0x7101753c00, bullet)
        assert e.mu.reg_read(UC_ARM64_REG_PC) == END
        got = e.mu.reg_read(UC_ARM64_REG_S0) & 0xffffffff
        exp = struct.unpack('<I', struct.pack('<f', independent(age, delay, maxf, F(start), F(end))))[0]
        m = got == exp; ok += m
        rows.append({'age': age, 'delay': delay, 'maxLengthFrame': maxf, 'start': float(F(start)), 'end': float(F(end)),
                     'original_bits': f'{got:08x}', 'independent_bits': f'{exp:08x}', 'match': m})
    out = {'function': '0x7101753c00', 'cases': len(rows), 'match': ok, 'rows': rows,
           'stubs': ['param vt[0] type check -> 1', '__cxa_guard_acquire -> 0', 'parent chain not walked (flags set)']}
    p = ROOT / 'analysis/completion/r5/camweapon_tail_emu.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'tail max length 0x7101753c00: {ok}/{len(rows)} bit match')
    for r in rows:
        if not r['match']: print('MISMATCH', r)


if __name__ == '__main__':
    main()
