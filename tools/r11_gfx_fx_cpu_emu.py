"""r11 gfx-diff 이펙트: 이미터 CPU 원본 실행(unicorn) → web particles.ts 비교 fixture.

(a) 0x710080e4cc 이미터 로컬 SRT: 실제 Lby 46 이미터 AB0..AE8 + 합성 난수 범위, 결과 localRT(E+0x320..0x350)와 LCG.
(b) 0x710081e3e4 입자 생성(형상 함수 포함): 실제 Lby 이미터 ResEmitter 바이트 그대로, 첫 입자의 위치(형상+positionRandom)·속도(형상 방향×allDirectionVel + 지정 방향).
    velRandom(R+0xD1C)만 0으로 둔다(웹은 이 난수를 LCG 순서로 소비하지 않음). 방향표는 원본 0x7100827d04 결과.
함수 스텁 없음. 출력 tests/fixtures/r11_fx_cpu.json
"""
import json, random, struct
import numpy as np
from r7_fx_transform_emu import VM, ROOT, HEAP

from r5_player_libm_emu import symbols
from r7_fx_transform_emu import BASE, SDKBASE, tags

ID = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def bind_util(vm):
    d = (ROOT / 'extracted/exefs/main.reloc.img').read_bytes(); ss = symbols((ROOT / 'extracted/exefs/sdk.img').read_bytes()); t = tags(d)
    for tab, size in ((t.get(7, 0), t.get(8, 0)), (t.get(23, 0), t.get(2, 0))):
        for i in range(tab, tab + size, 24):
            off, inf, ad = struct.unpack_from('<QQq', d, i); no, _, _, sh, val, _ = struct.unpack_from('<IBBHQQ', d, t[6] + (inf >> 32) * 24)
            name = d[t[5] + no:d.index(b'\0', t[5] + no)].decode()
            if not sh and name.startswith('_ZN2nn4util') and not name.startswith('_ZN2nn4util6detail') and name in ss and ('Float' in name or 'Coefficients' in name):
                vm.mu.mem_write(BASE + off, struct.pack('<Q', SDKBASE + ss[name][0] + ad))


def main():
    vm = VM(); m = vm.mu; bind_util(vm); rng = random.Random(2026100412)
    res = json.loads((ROOT / 'web/games/splatoon3/tests/fixtures/r11_fx_res.json').read_text())
    tables = json.loads((ROOT / 'web/games/splatoon3/tests/fixtures/r11_fx_tables.json').read_text())
    TAB = HEAP + 0x70000
    m.mem_write(TAB, b''.join(struct.pack('<4f', *v) for v in tables['table52f8'])); vm.q(0x71057d52f8, TAB); vm.q(0x71057d52f0, TAB)
    E, R, ES, ER, A, PI, CH = [HEAP + x for x in (0, 0x2000, 0x4000, 0x5000, 0x6000, 0x7000, 0x8000)]
    srt, birth = [], []
    for key, e in res['emitters'].items():
        b = bytearray.fromhex(e['hex'])
        for k in range(3):
            vals = list(struct.unpack_from('<15f', b, 0xab0))
            if k:  # synthetic random ranges on the actual base values
                for i in (3, 4, 5, 9, 10, 11):
                    vals[i] = float(np.float32(rng.uniform(0, 2)))
            m.mem_write(E, bytes(0x900)); vm.q(E + 0xb0, R); m.mem_write(R, bytes(b)); vm.fs(R + 0xab0, vals)
            seed = rng.getrandbits(32); vm.w(E + 0xbc, seed); vm.call(0x710080e4cc, E)
            cols = np.frombuffer(bytes(m.mem_read(E + 0x320, 64)), dtype='<f4').reshape(4, 4)[:, :3].tolist()
            srt.append(dict(key=key, vals=vals, seed=seed, localRT=cols, lcg=struct.unpack('<I', bytes(m.mem_read(E + 0xbc, 4)))[0]))
        # (b) first particle of an emission
        for k in range(4):
            for p, n in ((E, 0x1000), (R, 0x1000), (ES, 0x800), (ER, 0x500), (A, 0x300), (PI, 0x100), (CH, 0x200)):
                m.mem_write(p, bytes(n))
            rb = bytearray(b); struct.pack_into('<f', rb, 0xd1c, 0.0); m.mem_write(R, bytes(rb))
            vm.q(E + 0xb0, R); vm.q(E + 0x80, ES); vm.q(E + 0x250, ER); vm.q(ER + 0x10, R); vm.w(E + 0x240, 1)
            vm.fs(E + 0x460, ID); vm.fs(E + 0x360, ID)
            for kk, off in enumerate((0, 8, 0x10, 0x18, 0x20, 0x28)):
                ptr = HEAP + 0xa000 + kk * 0x100; vm.q(A + off, ptr); m.mem_write(ptr, bytes(0x100))
            vm.fs(E + 0x7d8, struct.unpack_from('<f', b, 0xcf8)); vm.fs(E + 0x7e4, struct.unpack_from('<3f', b, 0xd60))
            vm.fs(E + 0x7cc, struct.unpack_from('<f', b, 0xcf4)); vm.fs(E + 0x7f0, struct.unpack_from('<3f', b, 0xbb0))
            vm.fs(ES + 0x160, [1, 1, 1]); vm.fs(ES + 0x240, [1]); vm.fs(ES + 0x21c, [1])
            seed = rng.getrandbits(32); m.mem_write(E + 0xb8, struct.pack('<HHI', seed & 0xffff, seed >> 16, seed))
            s0 = float(np.float32(rng.random())); index = k % 4; count = 4
            ret = vm.call(0x710081e3e4, E, 0, PI, CH, A, 0, index, count, fargs=(s0, 0, 0)) & 0xff
            pos = list(struct.unpack('<3f', bytes(m.mem_read(HEAP + 0xa000, 12)))); vel = list(struct.unpack('<3f', bytes(m.mem_read(HEAP + 0xa100, 12))))
            birth.append(dict(key=key, seed=seed, s0=s0, index=index, count=count, ret=ret, pos=pos, vel=vel,
                              counter=struct.unpack('<H', bytes(m.mem_read(E + 0xba, 2)))[0]))
    out = dict(functions=['0x710080e4cc', '0x710081e3e4'], stubs=[], srt=srt, birth=birth)
    (ROOT / 'web/games/splatoon3/tests/fixtures/r11_fx_cpu.json').write_text(json.dumps(out), encoding='utf8')
    print(len(srt), len(birth), birth[0])


if __name__ == '__main__':
    main()
