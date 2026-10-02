"""r6 paint 공용 unicorn 하네스: main.reloc.img 를 원래 주소에 올리고 PLT(외부 함수)만 이름별 스텁으로 처리한다.

스텁(외부 함수만): __cxa_guard_acquire→1(초기화 진행), __cxa_guard_release/abort→0, strlen/memcpy/memmove/memset/strcmp 은 파이썬 구현,
malloc/게임 할당기 0x710083d2f0 → 범프 할당, free·뮤텍스·그 밖 PLT → 0 반환(호출 기록).
게임 함수(main 안)는 스텁하지 않는다. 추가 스텁은 호출자가 hook_fn 으로 지정.
"""
import re, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_UNMAPPED
from unicorn.arm64_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r6_paint_img import IMG, BASE

ROOT = Path(__file__).resolve().parents[2]
STACK, HEAP, END = 0x10000000, 0x20000000, 0x30000000
PLT_LO, PLT_HI = 0x7103e98000, 0x7103eb0000


def _imports():
    m = IMG
    mod0 = struct.unpack_from("<I", m, 4)[0]
    dyn = mod0 + struct.unpack_from("<i", m, mod0 + 4)[0]
    tags = {}
    while True:
        t, v = struct.unpack_from("<qQ", m, dyn); dyn += 16
        if t == 0: break
        tags.setdefault(t, v)
    symtab, strtab = tags[6], tags[5]
    out = {}
    for r in range(tags[23], tags[23] + tags[2], 24):
        roff, info, addend = struct.unpack_from("<QQq", m, r)
        no = struct.unpack_from("<I", m, symtab + (info >> 32) * 24)[0]
        out[BASE + roff] = m[strtab + no:m.index(b"\0", strtab + no)].decode()
    return out

IMPORTS = _imports()


def plt_name(addr):
    w0, w1 = struct.unpack_from("<II", IMG, addr - BASE)
    if (w0 & 0x9F000000) != 0x90000000: return None
    immlo = (w0 >> 29) & 3; immhi = (w0 >> 5) & 0x7FFFF
    imm = ((immhi << 2) | immlo) << 12
    if imm & (1 << 32): imm -= 1 << 33
    page = (addr & ~0xFFF) + imm
    off = ((w1 >> 10) & 0xFFF) * 8
    return IMPORTS.get(page + off)


class UC:
    def __init__(self, heap_size=0x4000000, hook_fn=None):
        self.mu = mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(IMG) + 0xFFFF) & ~0xFFFF); mu.mem_write(BASE, IMG)
        mu.mem_map(STACK, 0x200000); mu.mem_map(HEAP, heap_size); mu.mem_map(END, 0x1000)
        mu.mem_write(END, struct.pack("<I", 0xD65F03C0))
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        self.heap = HEAP + 0x1000
        self.calls = []
        self.hook_fn = hook_fn
        self.writes = []
        mu.hook_add(UC_HOOK_CODE, self._plt, begin=PLT_LO, end=PLT_HI)
        mu.hook_add(UC_HOOK_CODE, self._alloc, begin=0x710083d2f0, end=0x710083d2f0)

    def alloc(self, n, fill=0):
        a = self.heap; self.heap += (n + 0xF) & ~0xF
        self.mu.mem_write(a, bytes([fill]) * n); return a

    def _ret(self, v):
        mu = self.mu
        mu.reg_write(UC_ARM64_REG_X0, v & 0xFFFFFFFFFFFFFFFF)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    def _alloc(self, mu, addr, size, ud):
        self._ret(self.alloc(mu.reg_read(UC_ARM64_REG_X0)))

    def cstr(self, a):
        b = b""
        while True:
            c = bytes(self.mu.mem_read(a, 64)); i = c.find(b"\0")
            if i >= 0: return b + c[:i]
            b += c; a += 64

    def _plt(self, mu, addr, size, ud):
        name = plt_name(addr)
        if name is None: return
        x = [mu.reg_read(r) for r in (UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3)]
        self.calls.append(name)
        if self.hook_fn and self.hook_fn(self, name, x):
            return
        if name == "__cxa_guard_acquire":
            v = mu.mem_read(x[0], 1)[0]; self._ret(0 if v & 1 else 1)
        elif name == "__cxa_guard_release":
            mu.mem_write(x[0], b"\x01"); self._ret(0)
        elif name == "strlen":
            self._ret(len(self.cstr(x[0])))
        elif name in ("memcpy", "memmove"):
            mu.mem_write(x[0], bytes(mu.mem_read(x[1], x[2]))) if x[2] else None; self._ret(x[0])
        elif name == "memset":
            mu.mem_write(x[0], bytes([x[1] & 0xFF]) * x[2]) if x[2] else None; self._ret(x[0])
        elif name == "strcmp":
            a, b = self.cstr(x[0]), self.cstr(x[1]); self._ret((a > b) - (a < b))
        elif name == "malloc":
            self._ret(self.alloc(x[0]))
        else:
            self._ret(0)

    def call(self, fn, *args, count=10_000_000, fargs=()):
        mu = self.mu
        regs = [UC_ARM64_REG_X0 + i for i in range(8)]
        for r, v in zip(regs, args): mu.reg_write(r, v & 0xFFFFFFFFFFFFFFFF)
        for i, v in enumerate(fargs):
            mu.reg_write(UC_ARM64_REG_S0 + i, struct.unpack("<I", struct.pack("<f", v))[0])
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0x1F0000); mu.reg_write(UC_ARM64_REG_LR, END)
        mu.emu_start(fn, END, count=count)
        return mu.reg_read(UC_ARM64_REG_X0)

    def u64(self, a): return struct.unpack("<Q", bytes(self.mu.mem_read(a, 8)))[0]
    def u32(self, a): return struct.unpack("<I", bytes(self.mu.mem_read(a, 4)))[0]
    def f32(self, a): return struct.unpack("<f", bytes(self.mu.mem_read(a, 4)))[0]
    def w64(self, a, v): self.mu.mem_write(a, struct.pack("<Q", v & 0xFFFFFFFFFFFFFFFF))
    def w32(self, a, v): self.mu.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))
    def wf(self, a, v): self.mu.mem_write(a, struct.pack("<f", v))
