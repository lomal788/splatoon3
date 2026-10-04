"""r11 gfx-diff 이펙트: 방출 0x710081b784 원본 실행(unicorn) 프레임 루프 → 방출 프레임·개수 fixture.

0x710081e070(실제 입자 생성)만 스텁: 호출 프레임과 개수를 기록하고 E+1(방출함 플래그)=1. 0x710080e9a4(다음 간격)·
0x710080eed8·fmodf는 원본 그대로(fmodf 는 PLT라 스텁). 호출 조건(0x710081c0b8 의 B38/끝 시각/E+1 게이트)은
판독대로 재현: hasEmitEnd==0 이거나 age < start+duration 이거나 아직 방출 안 함일 때 호출. 초기 E+0x58/5c/60 = 0
[가정]: E+0x60 = 0x710080e9a4 결과, E+0x58 = E+0x60(첫 시작 프레임 방출), E+0x5c = 0 — 초기화 writer 미확인. 출력 tests/fixtures/r11_fx_emit.json
"""
import json, math, random, struct
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r7_fx_transform_emu import VM, ROOT, HEAP

FN = 0x710081b784; E070 = 0x710081e070


def main():
    vm = VM(); m = vm.mu; rng = random.Random(2026100413)
    calls = []
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM); md.detail = True
    code = bytes(m.mem_read(FN, 0x900))
    bls = {i.operands[0].imm for i in md.disasm(code, FN) if i.mnemonic == 'bl'}
    def hook(mu, addr, size, ud):
        if True:
            calls.append(mu.reg_read(UC_ARM64_REG_X2) & 0xffffffff)
            mu.mem_write(mu.reg_read(UC_ARM64_REG_X0), b'\x01')
            mu.reg_write(UC_ARM64_REG_X0, 0); mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
    def fmod_hook(mu, addr, size, ud):
        a = struct.unpack('<f', struct.pack('<I', mu.reg_read(UC_ARM64_REG_S0) & 0xffffffff))[0]
        b = struct.unpack('<f', struct.pack('<I', mu.reg_read(UC_ARM64_REG_S1) & 0xffffffff))[0]
        r = math.fmod(a, b) if b != 0 and math.isfinite(a) and not math.isnan(b) else float('nan')
        mu.reg_write(UC_ARM64_REG_S0, struct.unpack('<I', struct.pack('<f', r))[0]); mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
    stubbed = ['0x710081fa90:thunk e070 sink', '0x7103e9bb40:fmodf']
    m.hook_add(UC_HOOK_CODE, hook, begin=0x710081fa90, end=0x710081fa94)
    m.hook_add(UC_HOOK_CODE, fmod_hook, begin=0x7103e9bb40, end=0x7103e9bb44)
    E, R, ES = HEAP, HEAP + 0x2000, HEAP + 0x4000
    plans = [dict(interval=0, irand=0, rate=1.0, rrand=0, hasEnd=1, start=0, dur=1, vt=0),
             dict(interval=4, irand=0, rate=1.0, rrand=0, hasEnd=0, start=0, dur=1, vt=0),
             dict(interval=6, irand=0, rate=1.0, rrand=0, hasEnd=0, start=0, dur=1, vt=0),
             dict(interval=1, irand=0, rate=2.0, rrand=0, hasEnd=1, start=0, dur=1, vt=0),
             dict(interval=5, irand=0, rate=1.0, rrand=0, hasEnd=1, start=0, dur=1, vt=0),
             dict(interval=10, irand=0, rate=1.0, rrand=0, hasEnd=1, start=0, dur=1, vt=2),
             dict(interval=2, irand=0, rate=1.0, rrand=0, hasEnd=1, start=3, dur=9, vt=0),
             dict(interval=0, irand=0, rate=1.0, rrand=0, hasEnd=0, start=0, dur=1, vt=0)]
    out = []
    for p in plans:
        for a, n in ((E, 0x900), (R, 0x1000), (ES, 0x400)):
            m.mem_write(a, bytes(n))
        vm.q(E + 0xb0, R); vm.q(E + 0x80, ES)
        m.mem_write(R + 0xb80, bytes([p['vt']])); m.mem_write(R + 0xb38, bytes([p['hasEnd']]))
        vm.w(R + 0xb3c, p['start']); vm.w(R + 0xb44, p['dur']); vm.fs(R + 0xb48, [p['rate']]); vm.w(R + 0xb4c, p['rrand'])
        vm.w(R + 0xb50, p['interval']); vm.w(R + 0xb54, p['irand'])
        vm.fs(E + 0x79c, [p['rate']]); vm.fs(E + 0x64, [1]); vm.fs(E + 0x68, [1]); vm.fs(ES + 0x7c, [1]); vm.fs(ES + 0x80, [1])
        vm.w(E + 0xbc, rng.getrandbits(32))
        vm.call(0x710080e9a4, E, E + 0x60)  # initial interval via the original interval function
        m.mem_write(E + 0x58, bytes(m.mem_read(E + 0x60, 4)))  # [가정] accum = interval -> first started frame emits
        frames = []
        for f in range(40):
            vm.fs(E + 0x4c, [f])
            emitted = m.mem_read(E + 1, 1)[0]
            started = p['start'] <= f
            ended = p['hasEnd'] and f >= p['start'] + p['dur']
            if started and (not ended or not emitted):
                calls.clear()
                vm.call(FN, E + 0x58, E + 0x5c, E + 0x60, E + 1, E, 0, fargs=(1.0, float(p['start'])))
                for c in calls:
                    frames.append([f, c])
        out.append(dict(plan=p, emits=frames))
    (ROOT / 'web/games/splatoon3/tests/fixtures/r11_fx_emit.json').write_text(json.dumps(dict(function=hex(FN), stubs=sorted(set(stubbed)), cases=out)), encoding='utf8')
    for o in out:
        print(o['plan'], o['emits'][:8])


if __name__ == '__main__':
    main()
