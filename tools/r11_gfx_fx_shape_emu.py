"""r11 gfx-diff 이펙트: nn::vfx 형상 함수 원본 실행(unicorn) → web client/fx/shapes.ts 비교 fixture.

형상 0 0x710081fa94, 1 0x710081facc, 2 0x710081fcac, 12 0x7100821c28, 13 0x7100821cb0, 14 0x7100821dec.
입력: 합성 ResEmitter 필드 + 실제 Lby 형상2 이미터 값(Watersplash/juuji/Side). 방향표는 원본 0x7100827d04 실행 결과.
함수 스텁 없음(형상 함수 본체 그대로). 출력 tests/fixtures/r11_fx_shapes.json
"""
import json, random, struct
from unicorn.arm64_const import *
from r7_fx_transform_emu import VM, ROOT, HEAP, BASE, SDKBASE, tags
from r5_player_libm_emu import symbols

FN = {0: 0x710081fa94, 1: 0x710081facc, 2: 0x710081fcac, 12: 0x7100821c28, 13: 0x7100821cb0, 14: 0x7100821dec}
f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]


def main():
    vm = VM(); m = vm.mu; rng = random.Random(2026100411)
    d = (ROOT / 'extracted/exefs/main.reloc.img').read_bytes(); ss = symbols((ROOT / 'extracted/exefs/sdk.img').read_bytes()); t = tags(d); bound = []
    for tab, size in ((t.get(7, 0), t.get(8, 0)), (t.get(23, 0), t.get(2, 0))):
        for i in range(tab, tab + size, 24):
            off, inf, ad = struct.unpack_from('<QQq', d, i); no, _, _, sh, val, _ = struct.unpack_from('<IBBHQQ', d, t[6] + (inf >> 32) * 24)
            name = d[t[5] + no:d.index(b'\0', t[5] + no)].decode()
            if not sh and name.startswith('_ZN2nn4util') and not name.startswith('_ZN2nn4util6detail') and name in ss and ('Float' in name or 'Coefficients' in name):
                m.mem_write(BASE + off, struct.pack('<Q', SDKBASE + ss[name][0] + ad)); bound.append(name)
    tables = json.loads((ROOT / 'web/games/splatoon3/tests/fixtures/r11_fx_tables.json').read_text())
    TAB = HEAP + 0x70000
    m.mem_write(TAB, b''.join(struct.pack('<4f', *v) for v in tables['table52f8']))
    vm.q(0x71057d52f8, TAB)
    E, R, ER = HEAP, HEAP + 0x2000, HEAP + 0x4000
    POS, DIR = HEAP + 0x6000, HEAP + 0x6100
    res = json.loads((ROOT / 'web/games/splatoon3/tests/fixtures/r11_fx_res.json').read_text())
    real = []
    for k, e in res['emitters'].items():
        b = bytes.fromhex(e['hex'])
        if b[0xb80] in FN and b[0xb80] != 0:
            real.append((k, b))
    cases = []
    for c in range(600):
        vt = [0, 1, 2, 12, 13, 14][c % 6]
        rec = dict(volumeType=vt, sweepStartRandom=rng.choice([0, 1]), sweepLongitude=f32(rng.choice([6.2831854820251465, rng.uniform(0.1, 6)])),
                   sweepStart=f32(rng.uniform(-3, 3)), sweepRandom=f32(rng.choice([0, rng.uniform(0, 1)])), lineCenter=f32(rng.uniform(-1, 1)),
                   lineLength=f32(rng.uniform(0, 3)), volumeRadius=[f32(rng.uniform(0, 2)) for _ in range(3)], divisionMode=rng.choice([0, 0, 1, 2]),
                   divisionCount=rng.randint(1, 8), divisionRandom=rng.choice([0, 0, 30, 100]), lineDivisionCount=rng.randint(1, 8), lineDivisionRandom=rng.choice([0, 50]))
        src = None
        if c < len(real) * 4:
            src, b = real[c % len(real)]
            vt = b[0xb80]
            rec = dict(volumeType=vt, sweepStartRandom=b[0xb81], sweepLongitude=struct.unpack_from('<f', b, 0xb88)[0], sweepStart=struct.unpack_from('<f', b, 0xb90)[0],
                       sweepRandom=struct.unpack_from('<f', b, 0xb94)[0], lineCenter=struct.unpack_from('<f', b, 0xb9c)[0], lineLength=struct.unpack_from('<f', b, 0xba0)[0],
                       volumeRadius=list(struct.unpack_from('<3f', b, 0xba4)), divisionMode=struct.unpack_from('<I', b, 0xbbc)[0], divisionCount=struct.unpack_from('<i', b, 0xbc8)[0],
                       divisionRandom=struct.unpack_from('<I', b, 0xbcc)[0], lineDivisionCount=struct.unpack_from('<i', b, 0xbd0)[0], lineDivisionRandom=struct.unpack_from('<I', b, 0xbd4)[0])
        for p, n in ((E, 0x900), (R, 0x1000), (ER, 0x100), (POS, 0x200)):
            m.mem_write(p, bytes(n))
        vm.q(E + 0xb0, R); vm.q(E + 0x250, ER); vm.q(ER + 0x10, R)
        m.mem_write(R + 0xb80, bytes([vt, rec['sweepStartRandom']]))
        vm.fs(R + 0xb88, [rec['sweepLongitude']]); vm.fs(R + 0xb90, [rec['sweepStart']]); vm.fs(R + 0xb94, [rec['sweepRandom']])
        vm.fs(R + 0xb9c, [rec['lineCenter']]); vm.fs(R + 0xba0, [rec['lineLength']]); vm.fs(R + 0xba4, rec['volumeRadius'])
        vm.w(R + 0xbbc, rec['divisionMode']); vm.w(R + 0xbc8, rec['divisionCount']); vm.w(R + 0xbcc, rec['divisionRandom'])
        vm.w(R + 0xbd0, rec['lineDivisionCount']); vm.w(R + 0xbd4, rec['lineDivisionRandom'])
        seed = rng.getrandbits(32); seq = rng.randint(0, 9)
        m.mem_write(E + 0xb8, struct.pack('<HHI', seed & 0xffff, seed >> 16, seed)); vm.w(E + 0x40, seq)
        S = E + 0x760; adv = f32(rng.uniform(-1, 1)); fs = [f32(rng.uniform(0.5, 2)) for _ in range(3)]
        vm.fs(S + 0x6c, [adv]); vm.fs(S + 0x90, fs)
        s0 = f32(rng.random()); index = rng.randint(0, 9); count = rng.randint(1, 10)
        try:
            ret = vm.call(FN[vt], POS, DIR, E, index, count, S, fargs=(s0,)) & 0xff
        except Exception as ex:
            print('FAIL case', c, vt, rec, hex(m.reg_read(UC_ARM64_REG_PC)), ex); raise
        pos = list(struct.unpack('<4f', bytes(m.mem_read(POS, 16)))); dr = list(struct.unpack('<4f', bytes(m.mem_read(DIR, 16))))
        lcg = struct.unpack('<I', bytes(m.mem_read(E + 0xbc, 4)))[0]; ctr = struct.unpack('<H', bytes(m.mem_read(E + 0xba, 2)))[0]
        seq2 = struct.unpack('<i', bytes(m.mem_read(E + 0x40, 4)))[0]
        cases.append(dict(source=src, res=rec, seed=seed, seq=seq, adv=adv, formScale=fs, s0=s0, index=index, count=count,
                          ret=ret, pos=pos[:3], dir=dr[:3], lcg=lcg, counter=ctr, seqAfter=seq2))
    out = dict(boundImports=sorted(set(bound)), functions={str(k): hex(v) for k, v in FN.items()}, stubs=[], cases=cases)
    (ROOT / 'web/games/splatoon3/tests/fixtures/r11_fx_shapes.json').write_text(json.dumps(out), encoding='utf8')
    print(len(cases), 'cases; real', len(real), [k for k, _ in real])


if __name__ == '__main__':
    main()
