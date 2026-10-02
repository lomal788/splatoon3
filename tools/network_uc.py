"""main NSO 함수를 unicorn으로 직접 실행해 넷 직렬화(write/read)를 검증한다.

- 이미지: extracted/exefs/main.reloc.img 를 0x7100000000 에 올림(재배치 적용본).
- 스트림 객체 S: S+8 = writer/reader 객체 W, S+0x10 = ctx, S+0x18 = 패딩용 int.
  W 의 vtable 슬롯 0xa8(write bits), 0x48(read bits), 0x60(write byte/패딩), 0x70(u32), 0xb0(bytes) 를 훅으로 가로챈다.
- write 호출 → (값, 비트수) 목록 기록. read 호출 → 목록을 순서대로 공급.
사용(모듈): from network_uc import UC
"""
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
STACK = 0x10000000
HEAP = 0x20000000
STUB = 0x30000000
END = STUB + 0xF00

SLOT_NAMES = {0xA8: "wbits", 0x48: "rbits", 0xB0: "wbytes"}
# writer 스칼라 슬롯 -> 비트 수(값은 w3/x3). 0x60/0x70/0x78/0x90 은 판독으로 확인, 나머지는 크기 순서 추정
SCALAR_BITS = {0x60: 8, 0x68: 16, 0x70: 32, 0x78: 64, 0x80: 8, 0x88: 16, 0x90: 32, 0x98: 64}


class UC:
    def __init__(self):
        img = IMG.read_bytes()
        size = (len(img) + 0xFFFF) & ~0xFFFF
        self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu = self.mu
        mu.mem_map(BASE, size)
        mu.mem_write(BASE, img)
        mu.mem_map(STACK, 0x100000)
        mu.mem_map(HEAP, 0x100000)
        mu.mem_map(STUB, 0x1000)
        # FP 활성화(CPACR_EL1.FPEN)
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        # 스텁: 각 슬롯 주소에 ret
        ret = struct.pack("<I", 0xD65F03C0)
        mu.mem_write(STUB, ret * 0x400)
        self.vt = HEAP + 0x1000
        for off in range(0, 0x200, 8):
            mu.mem_write(self.vt + off, struct.pack("<Q", STUB + off))
        self.W = HEAP + 0x2000
        mu.mem_write(self.W, struct.pack("<Q", self.vt))
        self.S = HEAP + 0x3000
        mu.mem_write(self.S, struct.pack("<QQQI", 0, self.W, 0, 0))
        self.heap_next = HEAP + 0x10000
        self.log = []
        self.feed = []
        self.unknown = []
        self.feed_fn = None
        self.rlog = []
        mu.hook_add(UC_HOOK_CODE, self._hook, begin=STUB, end=STUB + 0xFFF)

    def alloc(self, n, fill=b"\0"):
        a = self.heap_next
        self.heap_next += (n + 0xF) & ~0xF
        self.mu.mem_write(a, fill * n)
        return a

    def _hook(self, mu, addr, size, user):
        if addr == END:
            return
        off = addr - STUB
        x2 = mu.reg_read(UC_ARM64_REG_X2)
        x3 = mu.reg_read(UC_ARM64_REG_X3) & 0xFFFFFFFF
        name = SLOT_NAMES.get(off)
        if name == "wbits":
            nbytes = (x3 + 7) // 8
            raw = int.from_bytes(mu.mem_read(x2, max(1, min(8, nbytes))), "little")
            val = raw & ((1 << x3) - 1) if x3 < 64 else raw
            self.log.append(("bits", x3, val))
        elif name == "rbits":
            if self.feed_fn is not None:
                v = self.feed_fn(len(self.rlog), x3)
                self.rlog.append((x3, v))
            else:
                kind, n, v = self.feed.pop(0)
                assert n == x3, (n, x3)
            nbytes = max(1, (x3 + 7) // 8)
            mu.mem_write(x2, int(v).to_bytes(8, "little")[:nbytes])
        elif off in SCALAR_BITS:
            n = SCALAR_BITS[off]
            v = mu.reg_read(UC_ARM64_REG_X3) & ((1 << n) - 1)
            self.log.append((f"s{off:#x}", n, v))
        elif name == "wbytes":
            self.log.append(("bytes", x3 * 8, 0))
        else:
            self.unknown.append(off)

    def call(self, fn, *args, fargs=()):
        mu = self.mu
        regs = [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3,
                UC_ARM64_REG_X4, UC_ARM64_REG_X5, UC_ARM64_REG_X6, UC_ARM64_REG_X7]
        for r, v in zip(regs, args):
            mu.reg_write(r, v)
        fregs = [UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_S2, UC_ARM64_REG_S3]
        for r, v in zip(fregs, fargs):
            mu.reg_write(r, struct.unpack("<I", struct.pack("<f", v))[0])
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        mu.reg_write(UC_ARM64_REG_X29, 0)
        mu.reg_write(UC_ARM64_REG_LR, END)
        mu.emu_start(fn, END, count=2_000_000)
        return mu.reg_read(UC_ARM64_REG_X0)

    def write(self, fn, obj):
        self.log = []
        self.call(fn, obj, self.S)
        return list(self.log)

    def read(self, fn, obj, items):
        self.feed = [x for x in items if x[0] == "bits"]
        self.call(fn, obj, self.S)
        left = len(self.feed)
        self.feed = []
        return left

    def f32(self, a, v):
        self.mu.mem_write(a, struct.pack("<f", v))

    def rf32(self, a):
        return struct.unpack("<f", self.mu.mem_read(a, 4))[0]

    def u32(self, a, v):
        self.mu.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))

    def ru32(self, a):
        return struct.unpack("<I", self.mu.mem_read(a, 4))[0]
