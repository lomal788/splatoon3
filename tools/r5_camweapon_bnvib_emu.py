"""r5 camweapon: bnvib 디코드를 원본 SDK(extracted/exefs/sdk.img) 함수로 실행해 독립 디코더와 비트 대조한다.

원본 함수(동적 심볼, r5_player_libm_emu.symbols 재사용):
  nn::hid::detail::ParseVibrationFile(VibrationFileInfo*, ParserContextImpl*, const void* file, size_t)   0x24aa70
  nn::hid::detail::RetrieveVibrationValue(VibrationValue*, int index, ParserContextImpl*)                  0x24ab90
두 함수 모두 다른 함수를 부르지 않는다(스텁 없음).
독립 디코더(문서 shake_rumble.md §7.1):
  u32 metaSize | u16 format(=3) | u16 rate(=200) | [meta>=0xC: u32 loopStart, u32 loopEnd] [meta>=0x10: u32 loopInterval]
  u32 dataSize @ 4+metaSize, 샘플 @ 8+metaSize, 개수 = dataSize>>2
  샘플 4바이트 {aL, fL, aH, fH}: amp = f32(byte)/255f, freq = T[code&31] * f32(10 << (code>>5)), T = SDK 표 0xaceb9c(32 f32) [데이터]
입력: analysis/camera/rumble_bnvib/*.bnvib 115개 전 샘플.
결과: analysis/completion/r5/camweapon_bnvib_emu.json
"""
import json, struct, sys
from pathlib import Path
import numpy as np
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_player_libm_emu import symbols  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SDKP = ROOT / 'extracted/exefs/sdk.img'
BASE, STACK, HEAP, END = 0x7400000000, 0x10000000, 0x20000000, 0x30000000
F = np.float32
PARSE = '_ZN2nn3hid6detail18ParseVibrationFileEPNS0_17VibrationFileInfoEPNS1_30VibrationFileParserContextImplEPKvm'
RETR = '_ZN2nn3hid6detail22RetrieveVibrationValueEPNS0_14VibrationValueEiPNS1_30VibrationFileParserContextImplE'


def main():
    d = SDKP.read_bytes()
    sym = symbols(d)
    table = np.frombuffer(d[0xaceb9c:0xaceb9c + 128], F)
    mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    mu.mem_map(BASE, (len(d) + 0xFFFF) & ~0xFFFF); mu.mem_write(BASE, d)
    mu.mem_map(STACK, 0x100000); mu.mem_map(HEAP, 0x800000); mu.mem_map(END, 0x1000)
    mu.mem_write(END, struct.pack('<I', 0xD65F03C0))
    mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)

    def call(name, *args):
        for r, v in zip((UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3), args):
            mu.reg_write(r, v)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000); mu.reg_write(UC_ARM64_REG_LR, END)
        mu.emu_start(BASE + sym[name][0], END, count=100000)
        return mu.reg_read(UC_ARM64_REG_X0)

    info, ctx, val, fbuf = HEAP, HEAP + 0x100, HEAP + 0x200, HEAP + 0x1000
    files = sorted((ROOT / 'analysis/camera/rumble_bnvib').glob('*.bnvib'))
    rows = []; total = 0; bad = 0; hdr_bad = 0
    for p in files:
        b = p.read_bytes()
        mu.mem_write(fbuf, b)
        rc = call(PARSE, info, ctx, fbuf, len(b))
        inf = struct.unpack('<IHHIIIIII', bytes(mu.mem_read(info, 0x20)))
        meta = struct.unpack_from('<I', b, 0)[0]
        dsz = struct.unpack_from('<I', b, 4 + meta)[0]
        n = dsz >> 2
        loop = meta >= 0xc
        exp_info = (meta, 3, 200, dsz, n, 1 if loop else 0,
                    struct.unpack_from('<I', b, 8)[0] if loop else 0,
                    struct.unpack_from('<I', b, 12)[0] if loop else n,
                    struct.unpack_from('<I', b, 16)[0] if meta >= 0x10 else 0)
        hok = rc == 0 and inf == exp_info
        hdr_bad += not hok
        mis = 0
        for i in range(n):
            call(RETR, val, i, ctx)
            got = bytes(mu.mem_read(val, 16))
            s = b[8 + meta + 4 * i: 8 + meta + 4 * i + 4]
            amp = lambda x: F(F(x) / F(255.0))
            frq = lambda c: F(table[c & 31] * F(10 << (c >> 5)))
            exp = struct.pack('<4f', amp(s[0]), frq(s[1]), amp(s[2]), frq(s[3]))
            total += 1
            if got != exp:
                mis += 1
        bad += mis
        rows.append(dict(file=p.name, rc=hex(rc), info=list(inf), expected_info=list(exp_info), header_match=hok,
                         samples=n, sample_mismatch=mis, loop=list(inf[5:9])))
    # 주파수 표와 10*2^(k/32) 가설의 차이(참고)
    approx = [abs(float(table[k]) - 2 ** (k / 32)) for k in range(32)]
    out = dict(files=len(files), header_mismatch=hdr_bad, samples=total, sample_mismatch=bad,
               table_hex=[f'{x:08x}' for x in np.frombuffer(d[0xaceb9c:0xaceb9c + 128], '<u4')],
               table_vs_2pow_k_over_32_max_abs=max(approx), parse_offset=hex(sym[PARSE][0]), retrieve_offset=hex(sym[RETR][0]),
               stubs='없음(두 함수 모두 리프)', rows=rows)
    q = ROOT / 'analysis/completion/r5/camweapon_bnvib_emu.json'
    q.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print('files', len(files), 'header mismatch', hdr_bad, 'samples', total, 'sample mismatch', bad,
          'table vs 2^(k/32) max abs', max(approx))
    print('loops', [(r['file'], r['loop']) for r in rows if r['loop'][0]][:20])


if __name__ == '__main__':
    main()
