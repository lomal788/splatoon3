"""[camrest] TraceGauge 갱신 → AnimTransform setFrame/enable → 레이아웃 애니 적용 루프를 unicorn 으로 원본 실행해
같은 대상(Gauge 애니 2인스턴스)에 마지막으로 적용되는 값이 무엇인지 확인한다.

원본 실행 함수(재배치 이미지 그대로):
  0x71038d6748 TraceGauge 갱신(g, dt)  → 0x71038d69bc 프레임 적용 → AnimTransform vt+0xd0 = 0x71038f32e4(setFrame)
  → vt+0x20 = 0x71038f34d0(enable, 레이아웃+0x70 목록 끝으로 이동)
  0x71038f67f8 레이아웃 애니 루프(화면 슬롯73 0x71013663fc 가 호출): 목록 순서로 AnimTransform vt+0x28(Animate) 호출,
  speed≠0 이면 vt+0x18(UpdateFrame), speed==0 이면 끄고 목록에서 뺌.
스텁: AnimTransform vt+0x28(Animate) — 호출 순서와 그 시점 frame(+0x20)을 기록, vt+0x18(UpdateFrame), 레이아웃 vt+0x60/0xc0/0x148.
즉 검증 범위 = 갱신식·setFrame·목록 이동·적용 순서. Animate 가 재질 값을 실제로 쓰는 내부(0x7100852b2c → vt+0x98..0xb0)는 판독.

사용: ui_animorder_emu.py
"""
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
STACK, HEAP, STUB = 0x10000000, 0x20000000, 0x30000000
AT_VT = 0x710573b610
TRACE_UPDATE = 0x71038d6748
ANIM_LOOP = 0x71038f67f8
ENABLE = 0x71038f34d0
N = 75


def f2u(f):
    return struct.unpack("<I", struct.pack("<f", f))[0]


class Emu:
    def __init__(self, order=("A", "B")):
        img = IMG.read_bytes()
        self.img = img
        mu = self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        for a in (STACK, HEAP, STUB):
            mu.mem_map(a, 0x100000)
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        mu.mem_write(STUB, struct.pack("<I", 0xD65F03C0) * 0x4000)
        # AnimTransform vtable: 원본 슬롯 복사, 0x18/0x28 만 스텁(STUB+0x1000+off)
        self.atvt = HEAP + 0x1000
        for off in range(0, 0x100, 8):
            v = struct.unpack_from("<Q", img, AT_VT - BASE + off)[0]
            if off in (0x18, 0x28):
                v = STUB + 0x1000 + off
            mu.mem_write(self.atvt + off, struct.pack("<Q", v))
        # 레이아웃 L: vtable 전부 스텁(STUB+0x2000+off), +0x70 목록 머리, +0x88 = L 자신(AT+0x58 → L, L+0x88 → L)
        self.L = HEAP + 0x4000
        lvt = HEAP + 0x3000
        for off in range(0, 0x400, 8):
            mu.mem_write(lvt + off, struct.pack("<Q", STUB + 0x2000 + off))
        mu.mem_write(self.L, struct.pack("<Q", lvt))
        mu.mem_write(self.L + 0x70, struct.pack("<QQ", self.L + 0x70, self.L + 0x70))
        mu.mem_write(self.L + 0x88, struct.pack("<Q", self.L))
        data = HEAP + 0x5000
        mu.mem_write(data, struct.pack("<QH", 0, N))
        self.at = {}
        for i, name in enumerate(("A", "B")):
            a = HEAP + 0x6000 + i * 0x100
            mu.mem_write(a, struct.pack("<Q", self.atvt))
            mu.mem_write(a + 0x18, struct.pack("<Q", data))
            mu.mem_write(a + 0x20, struct.pack("<f", 0.0))
            mu.mem_write(a + 0x24, b"\x00")
            mu.mem_write(a + 0x40, struct.pack("<QQ", a + 0x40, a + 0x40))
            mu.mem_write(a + 0x58, struct.pack("<Q", self.L))
            self.at[name] = a
        self.name_of = {v: k for k, v in self.at.items()}
        # TraceGauge g (SuperGauge 기본값: init 뒤 target=value=trace=75, speed 2.0, 나머지 0, traceEnabled 1)
        self.g = HEAP + 0x8000
        g = self.g
        mu.mem_write(g + 0x28, struct.pack("<QQQQ", self.at["A"], self.at["B"], 0, 0))
        mu.mem_write(g + 0x48, struct.pack("<fffffffffff", N, N, N, 2.0, 0.0, 20.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        mu.mem_write(g + 0x74, b"\x01")
        self.log = []
        mu.hook_add(UC_HOOK_CODE, self._hook, begin=STUB, end=STUB + 0x3FFF)
        # 생성 순서 흉내: order 순서로 목록에 넣는다(원본 enable 실행)
        for name in order:
            self.call(ENABLE, self.at[name], 1)

    def _hook(self, uc, addr, size, _):
        off = addr - STUB
        if off == 0x1028:
            x0 = uc.reg_read(UC_ARM64_REG_X0)
            fr = struct.unpack("<f", uc.mem_read(x0 + 0x20, 4))[0]
            self.log.append((self.name_of.get(x0, hex(x0)), fr))
        elif off == 0x2148:
            uc.reg_write(UC_ARM64_REG_S0, f2u(1.0))

    def call(self, fn, x0, x1=0, s0=None):
        mu = self.mu
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0x80000)
        mu.reg_write(UC_ARM64_REG_X0, x0)
        mu.reg_write(UC_ARM64_REG_X1, x1)
        if s0 is not None:
            mu.reg_write(UC_ARM64_REG_S0, f2u(s0))
        mu.reg_write(UC_ARM64_REG_X30, STUB + 0x3F00)
        mu.emu_start(fn, STUB + 0x3F00, count=20000)

    def rd(self, off):
        return struct.unpack("<f", self.mu.mem_read(self.g + off, 4))[0]

    def list_order(self):
        out, head = [], self.L + 0x70
        node = struct.unpack("<Q", self.mu.mem_read(head + 8, 8))[0]
        while node != head and len(out) < 8:
            out.append(self.name_of.get(node - 0x40, hex(node)))
            node = struct.unpack("<Q", self.mu.mem_read(node + 8, 8))[0]
        return out

    def frame(self, target):
        self.mu.mem_write(self.g + 0x48, struct.pack("<f", target))
        self.log = []
        self.call(TRACE_UPDATE, self.g, 0, 1.0)
        before = self.list_order()
        self.call(ANIM_LOOP, self.L)
        applied = list(self.log)
        return dict(target=target, value=self.rd(0x4c), trace=self.rd(0x50), list=before, applied=applied,
                    after=self.list_order())


def scenario(order):
    e = Emu(order)
    rows = []
    shown = None
    seq = [30.0] * 4 + [75.0] * 24
    for t in seq:
        r = e.frame(t)
        if r["applied"]:
            shown = N - r["applied"][-1][1]       # Gauge 곡선: frame = N(1 - x/N) → x = N - frame
        r["shown"] = shown
        rows.append(r)
    return rows


def main():
    ok = True
    for order in (("A", "B"), ("B", "A")):
        print(f"== 초기 목록 순서 {order} (A=GaugeRatio +0x28, B=TraceRatio +0x30)")
        for i, r in enumerate(scenario(order)):
            exp = min(r["value"], r["trace"])
            good = r["shown"] is not None and abs(r["shown"] - exp) < 1e-4
            ok &= good
            if i < 6 or i % 6 == 0 or not good:
                print(f"f{i:2d} target={r['target']:5.1f} value={r['value']:6.2f} trace={r['trace']:6.2f} "
                      f"list={r['list']} applied={[(n, round(f, 3)) for n, f in r['applied']]} after={r['after']} "
                      f"shown={r['shown']} min={exp} {'PASS' if good else 'FAIL'}")
    print("ALL PASS (표시 = min(value, trace))" if ok else "SOME FAIL")


if __name__ == "__main__":
    main()
