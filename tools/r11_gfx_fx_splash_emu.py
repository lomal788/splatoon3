"""r11 gfx-diff 이펙트: 착탄 0x71027b877c 원본 실행 → 바닥/벽 Splash·Hit 코드 이미터의 슬롯과 3×4 행렬 fixture.

r8_hiteffect_consume_emu.py 의 원본 큐/컨트롤러 준비를 그대로 재사용(exec), 정적 초기화 0x710124f5f0(속도0 회전)과
0x71027b42a0(벽 기준 0x71058cc928)을 원본 실행한 뒤, 무작위 법선·속도·칠 가능 여부로 0x71027b4704 → 0x71027b877c.
최종 코드 이미터 0x710137f558(슬롯·행렬)만 캡처 경계. 출력 tests/fixtures/r11_fx_splash.json
"""
import json, struct, random, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
s = {'__file__': str(ROOT / 'web/tools/r8_hiteffect_consume_emu.py')}
source = (ROOT / 'web/tools/r8_hiteffect_consume_emu.py').read_text(encoding='utf-8'); head, tail = source.split('\ne=E(', 1); exec(head, s)
E, R = s['E'], s['R']; UC_ARM64_REG_PC = s['UC_ARM64_REG_PC']
def _safe(f):
    def g(a, b):
        try: return f(a, b)
        except ValueError: return float('nan')
    return g
HOSTMATH = {'asinf': _safe(lambda a, b: math.asin(a)), 'acosf': _safe(lambda a, b: math.acos(a)), 'atan2f': _safe(lambda a, b: math.atan2(a, b)),
            'sinf': _safe(lambda a, b: math.sin(a)), 'cosf': _safe(lambda a, b: math.cos(a)), 'sqrtf': _safe(lambda a, b: math.sqrt(a))}
class I(E):
    hostmath = {}
    def _block(self, mu, a, size, user):
        if R.PLT_LO <= a < R.PLT_HI:
            name = self._plt_name(a)
            if name in ['_ZN2nn3err18ErrorResultVariantC1Ev', '_ZN2nn3ldn15MakeIpv4AddressEhhhh']:
                self.mathlog[name] += 1; mu.reg_write(UC_ARM64_REG_PC, self.sdkbase + self.syms[name][0]); return
            if name in HOSTMATH:
                # libm boundary: SDK asinf/acosf/atan2f chain into unrelocated SDK internals here -> host f32 libm
                a = struct.unpack('<f', struct.pack('<I', mu.reg_read(s['UC_ARM64_REG_S0']) & 0xffffffff))[0]
                b = struct.unpack('<f', struct.pack('<I', mu.reg_read(s['UC_ARM64_REG_S1']) & 0xffffffff))[0]
                r = HOSTMATH[name](a, b)
                self.hostmath[name] = self.hostmath.get(name, 0) + 1
                mu.reg_write(s['UC_ARM64_REG_S0'], struct.unpack('<I', struct.pack('<f', r))[0]); mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(s['UC_ARM64_REG_LR'])); return
        super()._block(mu, a, size, user)
s['I'] = I; exec('\ne=I(' + tail.split('# queue copy/formula')[0], s)
e = s['e']; G = s['G']; W = s['W']; req = s['req']; packet = s['packet']; cells = s['cells']; results = s['results']
e.call(0x710124f5f0, [])
# floor kind thresholds read by 0x71018b4f74 (0x7105858590/94): capture call args instead of relying on uninitialized globals
from unicorn import UC_HOOK_CODE
floor_calls = []
def _floor_hook(mu, addr, size, ud):
    th = struct.unpack('<f', struct.pack('<I', mu.reg_read(s['UC_ARM64_REG_S0']) & 0xffffffff))[0]
    p4 = mu.reg_read(s['UC_ARM64_REG_X2']); team = mu.reg_read(s['UC_ARM64_REG_W1']); paint = mu.reg_read(s['UC_ARM64_REG_W3']) & 1
    floor_calls.append({'theta': th, 'info': list(struct.unpack('<12f', bytes(mu.mem_read(p4, 48)))), 'paint': paint, 'team': team})
e.mu.hook_add(UC_HOOK_CODE, _floor_hook, begin=0x71018b4f74, end=0x71018b4f74)
def _kind_hook(mu, addr, size, ud):
    if floor_calls: floor_calls[-1]['kind'] = mu.reg_read(s['UC_ARM64_REG_X23'])
e.mu.hook_add(UC_HOOK_CODE, _kind_hook, begin=0x71018b4ff4, end=0x71018b4ff4)
# static init block of 0x7105858588..0x7105858594 (floor kind thresholds) from its original code 0x71018b2278..0x71018b229c
e.mu.emu_start(0x71018b2278, 0x71018b229c)
thresholds = struct.unpack('<2f', bytes(e.mu.mem_read(0x7105858590, 8)))
# static init 0x71027b42a0: run only its straight-line threshold store block (0x71027b4378..0x71027b43ac)
e.mu.emu_start(0x71027b4378, 0x71027b43ac)
wall = struct.unpack('<f', bytes(e.mu.mem_read(0x71058cc928, 4)))[0]
rng = random.Random(2026100414)
f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
def unit():
    while True:
        v = [rng.uniform(-1, 1) for _ in range(3)]; l = math.sqrt(sum(x * x for x in v))
        if 0.1 < l <= 1: return [f32(x / l) for x in v]
cases = []
for k in range(1500):
    if k % 5 == 0: n = [0.0, 1.0, 0.0]
    elif k % 5 == 1: n = unit(); n[1] = abs(n[1]) * 0.5; l = math.sqrt(sum(x * x for x in n)); n = [f32(x / l) for x in n]
    else: n = unit(); n[1] = abs(n[1]); l = math.sqrt(sum(x * x for x in n)); n = [f32(x / l) for x in n]
    vel = [f32(rng.uniform(-3, 3)) for _ in range(3)] if k % 7 else [0.0, 0.0, 0.0]
    paint = rng.choice([0, 1]); pos = [f32(rng.uniform(-50, 50)) for _ in range(3)]
    res = 1  # Constant → E2 Splash cell (Shooter___Constant_Default)
    b = packet(res, 0, 0, paint, n, vel); struct.pack_into('<3f', b, 0, *pos)
    e.mu.mem_write(req, bytes(b)); e.call(0x71027b4704, [G, req]); node = e.r64(G + 0x50) - 0x60
    e.events = []; e.emitters = []; floor_calls.clear()
    try:
        e.call(0x71027b877c, [W, node, 1])
    except Exception as ex:
        pc = e.mu.reg_read(s['UC_ARM64_REG_PC']); lr = e.mu.reg_read(s['UC_ARM64_REG_LR'])
        print('FAIL', k, n, vel, hex(pc), hex(lr), R.PLT_LO <= lr < R.PLT_HI and e._plt_name(lr)); raise
    em = [{'slot': x['slot'], 'matrix': list(struct.unpack('<12f', bytes.fromhex(x['matrix_hex'])))} for x in e.emitters]
    cases.append({'normal': n, 'vel': vel, 'paint': paint, 'pos': pos, 'emitters': em, 'floor': list(floor_calls)})
    e.w64(G + 0x50, G + 0x50); e.w64(G + 0x58, G + 0x50); e.w32(G + 0x60, 0); e.w64(node, e.r64(G + 0x68)); e.w64(G + 0x68, node)
out = {'function': '0x71027b877c', 'floorThresholds': thresholds, 'init': ['0x710124f5f0', '0x71027b4378..0x71027b43ac (static init 0x71027b42a0 threshold stores)'], 'wallNormalY': wall, 'cell': 'Shooter___Constant_Default',
       'capturedBoundary': '0x710137f558 (slot, 3x4 row-major matrix); 0x71018b4f74 entry args (theta, info[pos3 + 9], paintable)', 'hostLibm': I.hostmath, 'cases': cases}
(ROOT / 'web/games/splatoon3/tests/fixtures/r11_fx_splash.json').write_text(json.dumps(out), encoding='utf8')
from collections import Counter
print('wall', wall, Counter(len(c['emitters']) for c in cases), Counter(x['slot'] for c in cases for x in c['emitters']).most_common(12))
