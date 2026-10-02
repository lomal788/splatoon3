"""r6 player: 메인 플레이어 갱신 함수 전체를 unicorn으로 실행하는 동적 추적 하네스(공용).

구성
- main.reloc.img 를 0x7100000000 에 올리고(데이터·bss 포함 0x5A00000), 정적 초기화(.init_array)를 모두 실행한다.
- 할당: PLT nn::mem::StandardAllocator::Allocate/Reallocate/Free 를 파이썬 bump 힙으로 처리한다
  (malloc 0x710083d2f0 / calloc 0x710083d360 이 이 경로를 타도록 [0x71057d5310] 을 1로 둔다).
- 널 영역 0 .. 0x400000 을 0으로 매핑한다(읽기·실행 전용, 쓰기는 버리고 self.null_writes 에 기록). 객체가 없어 vtable 이 0 인 가상 호출(blr 0 + 슬롯)은
  이 영역에 들어오고, 그 자리에서 x0 = 0 으로 반환한다(= 스텁, self.null_calls 에 호출 위치 기록).
- PLT(외부 함수)는 memcpy/memmove/memset/memcmp/strlen/strcmp/strncmp/sqrtf 와 할당만 실제 처리,
  나머지는 0 반환 스텁(self.plt_stubbed 기록).
- 매핑 안 된 주소 접근은 64 KiB 페이지를 0으로 새로 매핑하고 계속한다(self.auto_pages 기록).
- 쓰기 추적: watch(lo, hi, tag) 로 등록한 구간에 쓰는 명령 PC·오프셋·크기·값을 self.writes 에 기록.
스텁 범위: 위의 널 가상 호출, PLT 스텁, 자동 매핑 페이지(0 값) — 각 실행 결과에 개수·목록을 남긴다.
"""
import math
import struct
import sys
import zlib
from pathlib import Path

from collections import deque
from unicorn import (Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED,
                     UC_HOOK_MEM_WRITE, UC_HOOK_INTR, UC_HOOK_BLOCK, UC_HOOK_MEM_WRITE_PROT,
                     UC_PROT_READ, UC_PROT_EXEC, UcError)
from unicorn.arm64_const import *

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
RAW = ROOT / "extracted" / "exefs" / "main.img"
BASE = 0x7100000000
IMG_SIZE = 0x5A00000
TEXT_END = BASE + 0x3E9DF50
PLT_LO, PLT_HI = 0x7103E99000, 0x7103E9E000
NULL_SZ = 0x400000
HEAP = 0x2000000000
HEAP_SZ = 0x20000000
STACK = 0x7FF0000000
STACK_SZ = 0x400000
RET_MAGIC = 0x7FFFF00000
SNAP = ROOT / "analysis" / "r6_player" / "world_init.bin"

LIBM1 = {"acosf": math.acos, "asinf": math.asin, "atanf": math.atan, "sinf": math.sin, "cosf": math.cos,
         "tanf": math.tan, "logf": math.log, "expf": math.exp, "log10f": math.log10, "floorf": math.floor,
         "ceilf": math.ceil, "roundf": lambda v: float(math.floor(abs(v) + 0.5)) * (1 if v >= 0 else -1),
         "truncf": math.trunc, "log2f": math.log2, "exp2f": lambda v: 2.0 ** v}
LIBM2 = {"atan2f": math.atan2, "powf": math.pow, "fmodf": math.fmod}

XREGS = [globals()[f"UC_ARM64_REG_X{i}"] for i in range(29)]


def _imports():
    m = RAW.read_bytes()
    mod0 = struct.unpack_from("<I", m, 4)[0]
    dyn = mod0 + struct.unpack_from("<i", m, mod0 + 4)[0]
    tags = {}
    while True:
        t, v = struct.unpack_from("<qQ", m, dyn)
        dyn += 16
        if t == 0:
            break
        tags.setdefault(t, v)
    symtab, strtab = tags[6], tags[5]
    d = {}
    for r in range(tags[23], tags[23] + tags[2], 24):
        roff, info, addend = struct.unpack_from("<QQq", m, r)
        name_off = struct.unpack_from("<I", m, symtab + (info >> 32) * 24)[0]
        e = m.index(b"\0", strtab + name_off)
        d[BASE + roff] = m[strtab + name_off:e].decode()
    ia, isz = tags[25], tags[27]
    return d, (ia, isz)


class PUC:
    def __init__(self, use_snapshot=True):
        self.img = IMG.read_bytes()
        mu = self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, IMG_SIZE)
        mu.mem_write(BASE, self.img[:IMG_SIZE])
        mu.mem_map(0, NULL_SZ, UC_PROT_READ | UC_PROT_EXEC)
        mu.mem_map(HEAP, HEAP_SZ)
        mu.mem_map(STACK, STACK_SZ)
        mu.mem_map(RET_MAGIC, 0x1000)
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        self.got, self.init_array = _imports()
        self.heap_next = HEAP + 0x1000
        self.plt_stubbed = {}
        self.libm_used = {}
        self.null_calls = {}
        self.auto_pages = []
        self.watches = []
        self.writes = []
        self.code_hooks = {}
        self.faults = []
        self.cur_tag = ""
        self.blocks = deque(maxlen=48)
        self.block_hook = None
        mu.hook_add(UC_HOOK_CODE, self._plt, begin=PLT_LO, end=PLT_HI)
        mu.hook_add(UC_HOOK_CODE, self._null, begin=0, end=NULL_SZ - 1)
        mu.hook_add(UC_HOOK_MEM_UNMAPPED, self._unmapped)
        mu.hook_add(UC_HOOK_MEM_WRITE, self._wr, begin=HEAP, end=HEAP + HEAP_SZ - 1)
        mu.hook_add(UC_HOOK_INTR, self._intr)
        mu.hook_add(UC_HOOK_MEM_WRITE_PROT, self._nullwr)
        self.null_writes = {}
        self.wq(0x71057D5310, 1)
        if use_snapshot and SNAP.exists():
            self.load_snapshot()
        elif use_snapshot:
            self.run_init_array()
            self.save_snapshot()

    # ---------- 메모리 ----------
    def alloc(self, n, align=16):
        a = (self.heap_next + align - 1) & ~(align - 1)
        self.heap_next = a + ((n + 15) & ~15)
        self.mu.mem_write(a, b"\0" * n)
        return a

    def wq(self, a, v):
        self.mu.mem_write(a, struct.pack("<Q", v & 0xFFFFFFFFFFFFFFFF))

    def rq(self, a):
        return struct.unpack("<Q", self.mu.mem_read(a, 8))[0]

    def w32(self, a, v):
        self.mu.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))

    def r32(self, a):
        return struct.unpack("<I", self.mu.mem_read(a, 4))[0]

    def rs32(self, a):
        return struct.unpack("<i", self.mu.mem_read(a, 4))[0]

    def wf(self, a, v):
        self.mu.mem_write(a, struct.pack("<f", v))

    def rf(self, a):
        return struct.unpack("<f", self.mu.mem_read(a, 4))[0]

    def w8(self, a, v):
        self.mu.mem_write(a, bytes([v & 0xFF]))

    def r8(self, a):
        return self.mu.mem_read(a, 1)[0]

    def _cstr(self, a, n=0x10000):
        out = bytearray()
        while len(out) < n:
            c = self.mu.mem_read(a + len(out), 1)[0]
            if c == 0:
                break
            out.append(c)
        return bytes(out)

    # ---------- 스냅숏(정적 초기화 뒤 데이터·bss·힙) ----------
    def save_snapshot(self):
        lo = PLT_HI
        data = bytes(self.mu.mem_read(lo, BASE + IMG_SIZE - lo))
        heap = bytes(self.mu.mem_read(HEAP, self.heap_next - HEAP))
        SNAP.parent.mkdir(parents=True, exist_ok=True)
        hdr = struct.pack("<QQQ", lo, len(data), self.heap_next)
        SNAP.write_bytes(hdr + zlib.compress(data, 6) + b"HEAP" + zlib.compress(heap, 6))

    def load_snapshot(self):
        raw = SNAP.read_bytes()
        lo, n, hn = struct.unpack_from("<QQQ", raw, 0)
        body = raw[24:]
        d = zlib.decompressobj()
        data = d.decompress(body)
        rest = d.unused_data
        assert rest[:4] == b"HEAP"
        heap = zlib.decompress(rest[4:])
        self.mu.mem_write(lo, data)
        self.mu.mem_write(HEAP, heap)
        self.heap_next = hn

    def run_init_array(self):
        ia, isz = self.init_array
        fails = []
        for i in range(isz // 8):
            f = struct.unpack_from("<Q", self.img, ia + i * 8)[0]
            r = self.call(f, count=3_000_000, quiet=True)
            if r is not None:
                fails.append((f, r))
        self.init_fails = fails
        return fails

    # ---------- 훅 ----------
    def _ret0(self, mu):
        mu.reg_write(UC_ARM64_REG_X0, 0)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    def _null(self, mu, addr, size, ud):
        lr = mu.reg_read(UC_ARM64_REG_LR)
        k = (lr - 4, addr)
        self.null_calls[k] = self.null_calls.get(k, 0) + 1
        self._ret0(mu)

    def _nullwr(self, mu, access, addr, size, value, ud):
        if addr >= NULL_SZ:
            return False
        pc = mu.reg_read(UC_ARM64_REG_PC)
        self.null_writes[pc] = self.null_writes.get(pc, 0) + 1
        return True  # 널 객체 쓰기는 버린다(널 영역을 0으로 유지)

    def _intr(self, mu, intno, ud):
        pc = mu.reg_read(UC_ARM64_REG_PC)
        self.faults.append(("intr", hex(pc), intno))
        mu.emu_stop()

    def _unmapped(self, mu, access, addr, size, value, ud):
        page = addr & ~0xFFFF
        if len(self.auto_pages) > 4000:
            return False
        try:
            mu.mem_map(page, 0x10000)
        except UcError:
            return False
        self.auto_pages.append((hex(addr), hex(mu.reg_read(UC_ARM64_REG_PC)), access))
        return True

    def _blk(self, mu, a, sz, ud):
        self.blocks.append(a)
        c = self.block_counts.get(a, 0) + 1
        self.block_counts[a] = c
        if c == self.loop_limit:
            self.faults.append(("loop", hex(a)))
            mu.emu_stop()

    def trace_blocks(self, on=True, loop_limit=200_000):
        self.loop_limit = loop_limit
        self.block_counts = {}
        if on and self.block_hook is None:
            self.block_hook = self.mu.hook_add(UC_HOOK_BLOCK, self._blk)
        elif not on and self.block_hook is not None:
            self.mu.hook_del(self.block_hook)
            self.block_hook = None

    def track_funcs(self, addrs):
        """함수 진입 횟수 기록(self.entries[주소])."""
        if not hasattr(self, "entries"):
            self.entries = {}
        for a in addrs:
            self.entries.setdefault(a, 0)
            self.mu.hook_add(UC_HOOK_CODE, self._entry, begin=a, end=a)

    def _entry(self, mu, a, sz, ud):
        self.entries[a] = self.entries.get(a, 0) + 1

    def watch(self, lo, hi, tag):
        self.watches.append((lo, hi, tag))

    def _wr(self, mu, access, addr, size, value, ud):
        for lo, hi, tag in self.watches:
            if lo <= addr < hi:
                pc = mu.reg_read(UC_ARM64_REG_PC)
                self.writes.append((self.cur_tag, tag, addr - lo, size, value & ((1 << (8 * size)) - 1) if size <= 8 else value, pc))
                break

    def _plt(self, mu, addr, size, user):
        w0 = struct.unpack_from("<I", self.img, addr - BASE)[0]
        if (w0 & 0x9F000000) != 0x90000000:
            return
        w1 = struct.unpack_from("<I", self.img, addr + 4 - BASE)[0]
        immlo = (w0 >> 29) & 3
        immhi = (w0 >> 5) & 0x7FFFF
        page = ((immhi << 2) | immlo) << 12
        if page & (1 << 32):
            page -= 1 << 33
        got = (addr & ~0xFFF) + page + ((w1 >> 10) & 0xFFF) * 8
        name = self.got.get(got, f"?{got:#x}")
        x0, x1, x2 = (mu.reg_read(r) for r in (UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2))
        ret = 0
        if name in ("memcpy", "memmove"):
            if x2:
                mu.mem_write(x0, bytes(mu.mem_read(x1, x2)))
            ret = x0
        elif name == "memset":
            if x2:
                mu.mem_write(x0, bytes([x1 & 0xFF]) * x2)
            ret = x0
        elif name == "strlen":
            ret = len(self._cstr(x0))
        elif name in ("strcmp", "strncmp"):
            n = x2 if name == "strncmp" else 0x10000
            a, b = self._cstr(x0, n), self._cstr(x1, n)
            ret = 0 if a == b else (1 if a > b else 0xFFFFFFFF)
        elif name == "memcmp":
            a = bytes(mu.mem_read(x0, x2)) if x2 else b""
            b = bytes(mu.mem_read(x1, x2)) if x2 else b""
            ret = 0 if a == b else (1 if a > b else 0xFFFFFFFF)
        elif name == "sqrtf":
            s = struct.unpack("<f", struct.pack("<I", mu.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF))[0]
            r = math.sqrt(s) if s >= 0 else float("nan")
            mu.reg_write(UC_ARM64_REG_S0, struct.unpack("<I", struct.pack("<f", r))[0])
        elif name in LIBM1 or name in LIBM2:
            # libm: 파이썬 double 계산 뒤 f32 반올림(근사 — 비트 대조 용도 아님, 쓰기 추적용)
            f = lambda r: struct.unpack("<f", struct.pack("<I", mu.reg_read(r) & 0xFFFFFFFF))[0]
            a = f(UC_ARM64_REG_S0)
            try:
                r = LIBM1[name](a) if name in LIBM1 else LIBM2[name](a, f(UC_ARM64_REG_S1))
            except (ValueError, OverflowError, ZeroDivisionError):
                r = float("nan")
            try:
                bits = struct.unpack("<I", struct.pack("<f", r))[0]
            except OverflowError:
                bits = 0x7F800000 if r > 0 else 0xFF800000
            mu.reg_write(UC_ARM64_REG_S0, bits)
            self.libm_used[name] = self.libm_used.get(name, 0) + 1
        elif name == "_ZN2nn3mem17StandardAllocator8AllocateEm":
            ret = self.alloc(x1)
        elif name == "_ZN2nn3mem17StandardAllocator8AllocateEmm":
            ret = self.alloc(x1, max(16, x2))
        elif name == "_ZN2nn3mem17StandardAllocator10ReallocateEPvm":
            ret = self.alloc(x2)
            if x1:
                mu.mem_write(ret, bytes(mu.mem_read(x1, x2)))
        elif name == "__cxa_guard_acquire":
            ret = 0 if mu.mem_read(x0, 1)[0] else 1
        elif name == "__cxa_guard_release":
            mu.mem_write(x0, b"\1")
        else:
            self.plt_stubbed[name] = self.plt_stubbed.get(name, 0) + 1
        mu.reg_write(UC_ARM64_REG_X0, ret)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    # ---------- 실행 ----------
    def call(self, fn, *args, stack_args=(), fargs=(), count=20_000_000, quiet=False, sp=None):
        mu = self.mu
        for r, v in zip(XREGS, args):
            mu.reg_write(r, v & 0xFFFFFFFFFFFFFFFF)
        for i, v in enumerate(fargs):
            mu.reg_write(globals()[f"UC_ARM64_REG_S{i}"], struct.unpack("<I", struct.pack("<f", v))[0])
        top = sp if sp is not None else STACK + STACK_SZ - 0x10000
        for i, v in enumerate(stack_args):
            self.wq(top + 8 * i, v)
        mu.reg_write(UC_ARM64_REG_SP, top)
        mu.reg_write(UC_ARM64_REG_X29, 0)
        mu.reg_write(UC_ARM64_REG_LR, RET_MAGIC)
        nf = len(self.faults)
        if self.block_hook is not None:
            self.block_counts = {}
        try:
            mu.emu_start(fn, RET_MAGIC, count=count)
        except UcError as e:
            pc = mu.reg_read(UC_ARM64_REG_PC)
            self.faults.append(("err", hex(fn), hex(pc), str(e)))
            return f"{e} pc={pc:#x}"
        pc = mu.reg_read(UC_ARM64_REG_PC)
        if pc != RET_MAGIC:
            if len(self.faults) > nf:
                return f"stopped {self.faults[-1]}"
            self.faults.append(("count", hex(fn), hex(pc)))
            return f"count limit pc={pc:#x}"
        return None

    def x(self, i):
        return self.mu.reg_read(XREGS[i])
