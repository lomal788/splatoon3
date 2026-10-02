"""r5 camweapon: 카메라 붐 구 반경의 런타임 값 사슬을 원본 명령으로 실행한다.

사슬 (모두 원본 명령 실행):
  1) 모듈 설정 팩토리 0x710344af54(case 0xf) → Phive 설정 객체(vtable 0x71057173a8) 생성, +0xb4/+0xb8 값
  2) Phive 월드 생성자 0x7103ac71c8 의 desc 복사 구간(0x7103ac728c..0x7103ac73ec) — desc = 설정+0x38
     → 월드+0x218/+0x21c, 월드+0x20/+0x24(dt)
  3) PlayerCamera 팩토리 0x71024d5c6c 를 *(*0x710599dfa8+0xe8)+0x21c = 2)의 값으로 실행 → 구 descriptor+0x2c
  4) 경계: 설정값 0.01/0.3/0.6/2500/inf/-inf/NaN/없음 으로 3)만 다시 실행해 독립 식
     r = min(fmaxnm(c, 0.3f), 2000f), 없음이면 c=0.05f 와 비트 비교
스텁: malloc 0x710083d2f0(버퍼 반환), memset 0x7103e99f10(0 채움), 그 밖 PLT(0x7103e99000~0x7103e9e000) 0 반환,
      0x7103585094(월드 내부 목록 초기화, 반환만), 질의 할당 0x7103a62e78, 형상 래퍼 0x7103a72e1c(인자 descriptor 캡처).
쓰는 파일: analysis/completion/r5/camweapon_boom_emu.json
"""
import json, math, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC, END

ROOT = Path(__file__).resolve().parents[2]


def w64(e, a, v): e.mu.mem_write(a, struct.pack('<Q', v))
def r64(e, a): return struct.unpack('<Q', e.mu.mem_read(a, 8))[0]
def r32(e, a): return struct.unpack('<I', e.mu.mem_read(a, 4))[0]
def fbits(x): return struct.unpack('<I', struct.pack('<f', x))[0]
def bitsf(b): return struct.unpack('<f', struct.pack('<I', b))[0]


def plt_hook(e, extra, log):
    def hook(mu, addr, size, ud):
        x0 = mu.reg_read(UC_ARM64_REG_X0); x1 = mu.reg_read(UC_ARM64_REG_X1); x2 = mu.reg_read(UC_ARM64_REG_X2)
        if addr in extra:
            val = extra[addr](x0, x1, x2)
        elif addr == 0x710083d2f0:
            val = e.alloc(max(x0, 0x10)); log.append(('malloc', hex(x0)))
        elif addr == 0x7103e99f10:
            mu.mem_write(x0, bytes([x1 & 0xff]) * x2); val = x0; log.append(('memset', hex(x2)))
        elif 0x7103e99000 <= addr < 0x7103e9e000:
            val = 0; log.append(('plt0', hex(addr)))
        else:
            return
        mu.reg_write(UC_ARM64_REG_X0, val)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
    e.mu.hook_add(UC_HOOK_CODE, hook)


def step1_config():
    e = UC(); log = []
    w64(e, 0x71059975c0, 0)
    plt_hook(e, {}, log)
    cfg = e.call(0x710344af54, 0, 0xf, 0)
    assert e.mu.reg_read(UC_ARM64_REG_PC) == END and cfg
    return {
        'vtable': hex(r64(e, cfg)),
        'plus_b4_bits': f'{r32(e, cfg + 0xb4):08x}', 'plus_b8_bits': f'{r32(e, cfg + 0xb8):08x}',
        'plus_5c_bits': f'{r32(e, cfg + 0x5c):08x}',
        'raw_38_100': bytes(e.mu.mem_read(cfg + 0x38, 0xc8)).hex(),
        'stubs': sorted(set(x[0] for x in log)),
    }, bytes(e.mu.mem_read(cfg, 0x180))


def step2_world(cfg_bytes):
    e = UC(); log = []
    cfg = e.alloc(0x180); e.mu.mem_write(cfg, cfg_bytes)
    desc = cfg + 0x38
    world = e.alloc(0x460)
    plt_hook(e, {0x7103585094: lambda a, b, c: a}, log)
    mu = e.mu
    mu.reg_write(UC_ARM64_REG_X0, world); mu.reg_write(UC_ARM64_REG_X20, desc)
    mu.reg_write(UC_ARM64_REG_SP, 0x10000000 + 0xF0000); mu.reg_write(UC_ARM64_REG_LR, END)
    mu.emu_start(0x7103ac728c, 0x7103ac73ec, count=100000)
    assert mu.reg_read(UC_ARM64_REG_PC) == 0x7103ac73ec
    return {
        'world_218_bits': f'{r32(e, world + 0x218):08x}', 'world_21c_bits': f'{r32(e, world + 0x21c):08x}',
        'world_20_bits': f'{r32(e, world + 0x20):08x}', 'world_24_bits': f'{r32(e, world + 0x24):08x}',
        'world_224_bits': f'{r32(e, world + 0x224):08x}', 'world_vtable': hex(r64(e, world)),
        'stubs': sorted(set(x[0] for x in log)),
    }, r32(e, world + 0x21c)


def step3_camera(cfg_bits):
    e = UC(); camera = e.alloc(0x1978); qmeta = e.alloc(0x300); shape = e.alloc(0x100)
    captured = []
    w64(e, 0x71059975c0, 0); w64(e, 0x710599dfa8, 0)
    if cfg_bits is not None:
        g = e.alloc(0x100); world = e.alloc(0x300)
        w64(e, 0x710599dfa8, g); w64(e, g + 0xe8, world); e.u32(world + 0x21c, cfg_bits)
    w64(e, r64(e, 0x7105791bd0), 0)
    log = []
    def shape_stub(x0, x1, x2):
        captured.append(bytes(e.mu.mem_read(x0, 0x30))); return shape
    plt_hook(e, {0x710083d2f0: lambda a, b, c: camera, 0x7103a62e78: lambda a, b, c: qmeta, 0x7103a72e1c: shape_stub}, log)
    got = e.call(0x71024d5c6c, 0)
    assert got == camera and e.mu.reg_read(UC_ARM64_REG_PC) == END and len(captured) == 1
    return struct.unpack_from('<I', captured[0], 0x2c)[0]


def independent_radius(cfg_bits):
    c = bitsf(0x3d4ccccd) if cfg_bits is None else bitsf(cfg_bits)
    lo = bitsf(0x3e99999a)
    r = lo if math.isnan(c) else max(c, lo)     # fmaxnm: NaN 이면 다른 쪽
    r = min(r, 2000.0)
    if math.isnan(r) or math.isinf(r):
        r = 1.0
    return fbits(r)


def main():
    s1, cfg_bytes = step1_config()
    s2, w21c = step2_world(cfg_bytes)
    chain_bits = step3_camera(w21c)
    rows = []
    cases = [None, w21c, fbits(0.05), fbits(0.3), 0x3e99999a, 0x3e99999b, fbits(0.6), fbits(2500.0), 0x7f800000, 0xff800000, 0x7fc00000, fbits(-1.0)]
    for c in cases:
        got = step3_camera(c); exp = independent_radius(c)
        rows.append({'config_bits': None if c is None else f'{c:08x}', 'original_radius_bits': f'{got:08x}',
                     'independent_bits': f'{exp:08x}', 'radius': bitsf(got), 'match': got == exp})
    ok = all(r['match'] for r in rows)
    out = {'step1_factory_case_0xf': s1, 'step2_world_ctor_copy': s2,
           'step3_chain_radius_bits': f'{chain_bits:08x}', 'step3_chain_radius': bitsf(chain_bits),
           'edge_cases': rows, 'all_match': ok}
    p = ROOT / 'analysis/completion/r5/camweapon_boom_emu.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('cfg+b4', s1['plus_b4_bits'], 'cfg+b8', s1['plus_b8_bits'], 'world+21c', s2['world_21c_bits'],
          'world+24', s2['world_24_bits'], 'chain radius', f'{chain_bits:08x}', bitsf(chain_bits))
    print(f"edge {sum(r['match'] for r in rows)}/{len(rows)}", 'PASS' if ok else 'FAIL')
    for r in rows: print(r)


if __name__ == '__main__':
    main()
