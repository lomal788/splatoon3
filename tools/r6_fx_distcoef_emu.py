"""r6 fx: SLink DistCoef → 감쇠 확장(+4) 연결을 원본 실행으로 확인한다.

원본 경로 [판독]:
  SLink 에셋 시작 0x7103885e44 끝에서 전역 xlink 시스템(*0x710599ada8)+0x1278 의 게임 훅 객체
  (vtable 0x71056b45a8, 생성 0x7103141e30) 슬롯 5(+0x28) = 0x710313d4ec 를 부른다.
  0x710313d4ec 가 사용자 정의 에셋 파라미터(custom 0=Shape … 8=Pan, 시작 인덱스 = PDT+0x34 = numAsset−numCustom = 20)를 읽어
  감쇠 확장 객체(0x710312b534 가 보이스별로 만듦)를 채우고 보이스 +0x200 에 넣는다.

이 하네스는 0x710313d4ec 를 원본 그대로 실행한다. 데이터는 실제 SLink 파일(slink2.Product.100.bslnk)의
ParamDefine 표·에셋 파라미터 블록·direct 값 표를 에뮬 메모리에 그대로 올려 쓴다.
  - ParamDefine 표 객체는 원본 setup 0x71038922f0 을 실행해 만든다.
  - 사용자 정의 파라미터 getter(float 0x710389331c / bool 0x7103893040 / string 0x7103892e08 / 값 해석 0x7103893490)는 원본 실행.
  - 확장 노드 할당 0x710312b534(+ 트리 삽입 0x710312b8b0)도 원본 실행.
  - UC_HOOK_MEM_WRITE 로 확장 객체·보이스·핸들 파라미터에 쓰는 PC 를 기록한다.
스텁: nn::os::Lock/UnlockMutex PLT(0x7103e99fd0/0x7103e99ff0)는 ret. 그 밖 PLT 진입은 오류로 센다.
범위 밖(실행 안 함): Shape 문자열이 있는 에셋의 형상 블록(사용자 +0x40 = 0 으로 건너뜀),
  보이스 +0x1cc == 0 경로(SpeakerBalanceType 분기), 보이스 +0x1e0 ≠ 0 경로(그룹 곡선 탐색), Curve/Random 값(제외).
사용: PY web/tools/r6_fx_distcoef_emu.py [--limit N]
"""
import struct
import sys
import json
import argparse
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from effect_xlink import XLink, load_bytes  # noqa: E402

IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
FILEB = 0x40000000
HEAP = 0x20000000
STACK = 0x10000000
END = 0x30000000

HOOK = 0x710313d4ec
PDT_SETUP = 0x71038922f0
PLT_LO, PLT_HI = 0x7103e99000, 0x7103ea0000
MUTEX = (0x7103e99fd0, 0x7103e99ff0)
G_UNIT = 0x710599a3f8          # *(*(+0)+0x10)+0x20 = 전역 단위
G_EXTMGR = 0x7105911d58         # *0x71057a42b8 이 가리키는 칸 → 관리자
G_SHAPE_GUARD = 0x710580de18
G_FLAGS = 0x7105912ac8          # 보이스 +0x1f8 비트 2..4 원천 3바이트


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def fbits(u):
    return struct.unpack('<f', struct.pack('<I', u))[0]


class Emu:
    def __init__(self, xl):
        self.xl = xl
        mu = self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        img = IMG.read_bytes()
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        fsz = (len(xl.d) + 0xFFFF) & ~0xFFFF
        mu.mem_map(FILEB, fsz)
        mu.mem_write(FILEB, xl.d)
        mu.mem_map(HEAP, 0x400000)
        mu.mem_map(STACK, 0x100000)
        mu.mem_map(END, 0x1000)
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        ret = struct.pack('<I', 0xD65F03C0)
        for a in MUTEX:
            mu.mem_write(a, ret)
        self.plt_bad = []
        mu.hook_add(UC_HOOK_CODE, self._plt, begin=PLT_LO, end=PLT_HI)
        self.writes = []
        self.watch = []
        mu.hook_add(UC_HOOK_MEM_WRITE, self._w)
        self.hp = HEAP
        # 전역 단위 객체
        self.unit_obj = self.alloc(0x40)
        self.unit_sys = self.alloc(0x40)
        self.q(self.unit_sys + 0x10, self.unit_obj)
        self.q(G_UNIT, self.unit_sys)
        self.unit = 1.0
        self.f(self.unit_obj + 0x20, self.unit)
        mu.mem_write(G_SHAPE_GUARD, b'\x01')
        mu.mem_write(G_FLAGS, b'\x00\x00\x00')
        # ParamDefine 표: 원본 setup 실행 (D+0x570 = 표 객체)
        self.D = self.alloc(0x600)
        self.call(PDT_SETUP, self.D + 0x570, FILEB + xl.pdtPos, 0)
        assert self.u32(self.D + 0x574) == xl.numAssetParam
        self.first_custom = self.u32(self.D + 0x5a4)

    # --- 메모리 도우미
    def alloc(self, n):
        a = self.hp
        self.hp += (n + 0xF) & ~0xF
        self.mu.mem_write(a, b'\0' * n)
        return a

    def q(self, a, v):
        self.mu.mem_write(a, struct.pack('<Q', v & (2**64 - 1)))

    def w32(self, a, v):
        self.mu.mem_write(a, struct.pack('<I', v & 0xffffffff))

    def f(self, a, v):
        self.mu.mem_write(a, struct.pack('<f', v))

    def u32(self, a):
        return struct.unpack('<I', self.mu.mem_read(a, 4))[0]

    def rf(self, a):
        return struct.unpack('<f', self.mu.mem_read(a, 4))[0]

    def rq(self, a):
        return struct.unpack('<Q', self.mu.mem_read(a, 8))[0]

    def _plt(self, mu, addr, size, ud):
        if addr in MUTEX:
            return
        self.plt_bad.append(addr)
        mu.emu_stop()

    def _w(self, mu, access, addr, size, value, ud):
        for lo, hi, tag in self.watch:
            if lo <= addr < hi:
                self.writes.append((tag, addr - lo, size, value & ((1 << (8 * size)) - 1) if size <= 8 else value,
                                    mu.reg_read(UC_ARM64_REG_PC)))

    def call(self, fn, *args):
        mu = self.mu
        regs = [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3]
        for r, v in zip(regs, args):
            mu.reg_write(r, v)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        mu.reg_write(UC_ARM64_REG_X29, 0)
        mu.reg_write(UC_ARM64_REG_LR, END)
        mu.emu_start(fn, END, count=500_000)
        return mu.reg_read(UC_ARM64_REG_PC)

    # --- 한 경우 실행
    def run_case(self, block_off, user_name, subj, voice_flag=1):
        """block_off: 에셋 파라미터 블록(assetTablePos 기준). subj: None(사용자+0xb8 bit0 꺼짐) 또는 값."""
        self.hp = self.hp_mark
        xl = self.xl
        # 접근자: ACC+0x18→X, X+8→D, ACC+0x10→Y, Y+0x18=0, Y+0x20→P1, P1→P2, P2+0x48 = direct 표, +0x78 = 이름표
        R = self.alloc(0x80)
        ACC = R + 0x30
        X = self.alloc(0x20)
        self.q(X + 8, self.D)
        self.q(ACC + 0x18, X)
        Y = self.alloc(0x40)
        P2 = self.alloc(0x100)
        P1 = self.alloc(0x10)
        self.q(P1, P2)
        self.q(Y + 0x20, P1)
        self.w32(Y + 0x18, 0)
        self.q(P2 + 0x48, FILEB + xl.directPos)
        self.q(P2 + 0x78, FILEB + xl.namePos)
        self.q(ACC + 0x10, Y)
        # 사용자
        U = self.alloc(0x100)
        U38 = self.alloc(0x60)
        nm = self.alloc(0x40)
        self.mu.mem_write(nm, user_name.encode() + b'\0')
        self.q(U38 + 0x10, nm)
        self.q(U38 + 0x18, R)
        self.q(U38 + 0x40, 0)
        self.q(U + 0x38, U38)
        vals = self.alloc(0x40)
        if subj is None:
            self.q(U + 0xb8, 0)
        else:
            self.q(U + 0xb8, (3 << 1) | 1)        # 인덱스 3, 유효 비트
            self.w32(vals + 3 * 4, subj)
        self.q(U + 0x80, vals)
        # 에셋 리소스
        A = self.alloc(0x40)
        self.q(A + 0x20, FILEB + xl.assetTablePos + block_off)
        # 보이스·핸들
        V = self.alloc(0x240)
        self.w32(V + 8, 0x1234)
        self.mu.mem_write(V + 0x1cc, bytes([voice_flag]))
        HH = self.alloc(0x10)
        self.q(HH, V)
        self.w32(HH + 8, 0x1234)
        P = self.alloc(0x100)
        args = self.alloc(0x30)
        for i, v in enumerate((U, HH, A, 0, P)):
            self.q(args + 8 * i, v)
        # 확장 관리자(맵) + 빈 노드 하나
        MG = self.alloc(0x80)
        self.q(G_EXTMGR, MG)
        MAP = MG + 0x20
        node = self.alloc(0x80)
        self.q(MAP + 8, node)
        self.w32(MAP + 0x18, 0)
        self.w32(MAP + 0x1c, 1)
        THIS = self.alloc(0x40)
        self.watch = [(node, node + 0x80, 'node'), (V, V + 0x240, 'voice'), (P, P + 0x100, 'hp')]
        self.writes = []
        self.plt_bad = []
        pc = self.call(HOOK, THIS, args)
        self.watch = []
        ext = node + 0x28
        return {
            'pc': pc, 'plt': list(self.plt_bad), 'writes': list(self.writes),
            'ext': ext, 'voice200': self.rq(V + 0x200),
            'ext4': self.rf(ext + 4), 'ext0': self.mu.mem_read(ext, 2), 'ext28': self.mu.mem_read(ext + 0x28, 1)[0],
            'v1ec': self.rf(V + 0x1ec), 'hpbc': self.rf(P + 0xbc), 'hpc4': self.rf(P + 0xc4),
            'hpb8': struct.unpack('<HH', self.mu.mem_read(P + 0xb8, 4)),
        }


def expect(xl, mask, vals, user_name, subj):
    """독립 재구현: 파일 값으로 기대 결과 계산(원본 코드 실행 없이)."""
    defs = xl.assetParamDefs

    def val(bit):
        if mask >> bit & 1:
            j = bin(mask & ((1 << bit) - 1)).count('1')
            raw = vals[j]
            if raw >> 24 != 0:
                return None
            u = xl.direct[raw & 0xffffff]
            return u
        return 'default'

    def fval(bit):
        v = val(bit)
        if v is None:
            return None
        if v == 'default':
            return f32(defs[bit]['default'])
        return fbits(v)

    def bval(bit):
        v = val(bit)
        if v == 'default':
            return defs[bit]['default'] & 1
        return v & 1

    e = {}
    v2, p2 = fval(22), fval(23)
    e['hpbc'] = max(v2, 0.0)
    e['hpc4'] = max(p2, 0.0)
    dc = fval(21)
    e['ext4'] = f32(1.0 / dc) if dc > 0 else 1.0
    e['ext0'] = 0 if subj == 0 else 1
    e['ext1'] = bval(24) if subj == 1 else 0
    occ = bval(25)
    if subj == 0 and (user_name.startswith('Player') or user_name.startswith('Weapon')):
        occ = 0
    e['ext28'] = occ
    ss = fval(26)
    e['v1ec'] = f32(ss * 1.0) if ss > 0 else 0.0
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    xl = XLink(load_bytes(str(ROOT / 'extracted/romfs/SLink2/slink2.Product.100.bslnk.zs')))
    emu = Emu(xl)
    emu.hp_mark = emu.hp
    print('first custom index (PDT+0x34) =', emu.first_custom, '/ numAsset', xl.numAssetParam, 'numCustom', xl.numCustomAssetParam)
    names = ['WeaponShooterNormal', 'PlayerSquid', 'HitEffect', 'Obj_Sponge']
    ok = bad = skipped = 0
    pcs = {}
    first_bad = []
    n = 0
    for off, (mask, vals) in sorted(xl.assetParamAt.items()):
        # Curve/Random 값이 있는 사용자 정의 칸은 제외(속성·난수 상태 필요)
        skip = False
        for bit in (21, 22, 23, 24, 25, 26):
            if mask >> bit & 1:
                j = bin(mask & ((1 << bit) - 1)).count('1')
                if vals[j] >> 24 != 0:
                    skip = True
        if skip:
            skipped += 1
            continue
        for user_name in names:
            for subj in (None, 0, 1, 2):
                r = emu.run_case(off, user_name, subj)
                e = expect(xl, mask, vals, user_name, subj)
                got = {'ext4': r['ext4'], 'ext0': r['ext0'][0], 'ext1': r['ext0'][1], 'ext28': r['ext28'],
                       'v1ec': r['v1ec'], 'hpbc': r['hpbc'], 'hpc4': r['hpc4']}
                good = (r['pc'] == END and not r['plt'] and r['voice200'] == r['ext'] and
                        all(struct.pack('<f', got[k]) == struct.pack('<f', e[k]) for k in ('ext4', 'v1ec', 'hpbc', 'hpc4')) and
                        all(got[k] == e[k] for k in ('ext0', 'ext1', 'ext28')))
                if good:
                    ok += 1
                else:
                    bad += 1
                    if len(first_bad) < 5:
                        first_bad.append({'off': off, 'user': user_name, 'subj': subj, 'got': got, 'exp': e,
                                          'pc': hex(r['pc']), 'plt': [hex(x) for x in r['plt']]})
                for tag, o, sz, v, pc in r['writes']:
                    if tag == 'node' and o >= 0x28:
                        pcs.setdefault(('ext+%#x' % (o - 0x28)), set()).add(hex(pc))
                    elif tag == 'voice' and o in (0x1ec, 0x200):
                        pcs.setdefault('voice+%#x' % o, set()).add(hex(pc))
                    elif tag == 'hp' and o in (0xbc, 0xc4):
                        pcs.setdefault('handle+%#x' % o, set()).add(hex(pc))
        n += 1
        if a.limit and n >= a.limit:
            break
    print('blocks run', n, 'skipped(curve/random)', skipped, 'cases ok', ok, 'bad', bad)
    for k in sorted(pcs):
        print('  writer', k, sorted(pcs[k]))
    for b in first_bad:
        print('BAD', b)
    out = ROOT / 'analysis/completion/r6/fx_distcoef_emu.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'blocks': n, 'skipped': skipped, 'ok': ok, 'bad': bad,
                               'writers': {k: sorted(v) for k, v in pcs.items()}, 'first_bad': first_bad,
                               'first_custom': emu.first_custom}, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
