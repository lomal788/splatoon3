"""r6 ui 공용: 이미지·디스어셈블·vtable 칸 검색·BL 검색·unicorn 하네스(메모리 쓰기 훅)."""
import bisect
import struct
import sys
from pathlib import Path

import numpy as np
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
TSV = ROOT / "analysis" / "functions" / "main.nso.tsv"
BASE = 0x7100000000
TEXT_END = 0x3E9DF50
DATA_LO, DATA_HI = 0x3E9E000, 0x59AD000

_m = None
_w = None
_fs = None
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
md.skipdata = True


def img():
    global _m
    if _m is None:
        _m = IMG.read_bytes()
    return _m


def words():
    global _w
    if _w is None:
        _w = np.frombuffer(img()[:TEXT_END & ~3], dtype="<u4")
    return _w


def funcs():
    global _fs
    if _fs is None:
        starts, sizes = [], []
        with open(TSV, encoding="utf-8") as f:
            next(f)
            for line in f:
                a, size, *_ = line.rstrip("\n").split("\t")
                starts.append(int(a, 16))
                sizes.append(int(size))
        _fs = (starts, sizes)
    return _fs


def func_of(addr):
    s, z = funcs()
    i = bisect.bisect_right(s, addr) - 1
    return (s[i], z[i]) if i >= 0 else (None, 0)


def q(a):
    return struct.unpack_from("<Q", img(), a - BASE)[0]


def u32(a):
    return struct.unpack_from("<I", img(), a - BASE)[0]


def cstr(a, n=96):
    b = img()[a - BASE:a - BASE + n]
    return b.split(b"\0")[0].decode("utf-8", "replace")


def dis(a, n=None, end=None):
    if end is None:
        end = a + 4 * (n or 64)
    code = img()[a - BASE:end - BASE]
    return list(md.disasm(code, a))


def dis_func(a):
    s, z = func_of(a)
    # 함수 크기(떨어진 블록 포함)라 근사: 시작~시작+크기
    return dis(s, end=s + max(z, 4))


def ptr_slots(val):
    """데이터 영역에서 val 을 담은 8바이트 정렬 칸 주소."""
    m = img()
    data = m[DATA_LO:DATA_HI]
    needle = struct.pack("<Q", val)
    out = []
    p = data.find(needle)
    while p >= 0:
        if p % 8 == 0:
            out.append(BASE + DATA_LO + p)
        p = data.find(needle, p + 1)
    return out


def bl_to(target):
    w = words()
    isbl = (w & 0xFC000000) == 0x94000000
    isb = (w & 0xFC000000) == 0x14000000
    idx = np.nonzero(isbl | isb)[0]
    imm = (w[idx] & 0x03FFFFFF).astype(np.int64)
    imm = np.where(imm & (1 << 25), imm - (1 << 26), imm)
    tgt = idx.astype(np.int64) * 4 + imm * 4
    res = []
    for i in np.nonzero(tgt == target - BASE)[0]:
        a = BASE + int(idx[i]) * 4
        res.append((a, "bl" if isbl[idx[i]] else "b"))
    return res


def ldr_imm_off(off, size=8):
    """ldr xN,[xM,#off] (64비트 부호없는 오프셋) 명령 위치 배열."""
    w = words()
    if size == 8:
        mask, opc, sc = 0xFFC00000, 0xF9400000, 8
    else:
        mask, opc, sc = 0xFFC00000, 0xB9400000, 4
    imm12 = off // sc
    sel = ((w & mask) == opc) & (((w >> 10) & 0xFFF) == imm12)
    return np.nonzero(sel)[0]


def blr_after_ldr(slot_off, window=6):
    """ldr xN,[xM,#slot_off] 뒤 window 명령 안에 blr/br xN 이 있는 위치 (가상 호출 후보)."""
    w = words()
    out = []
    for i in ldr_imm_off(slot_off):
        rn = int(w[i]) & 0x1F
        for j in range(i + 1, min(i + 1 + window, len(w))):
            x = int(w[j])
            if (x & 0xFFFFFC1F) in (0xD63F0000, 0xD61F0000) and ((x >> 5) & 0x1F) == rn:
                out.append((BASE + i * 4, BASE + j * 4))
                break
            if (x & 0x1F) == rn and not ((x & 0xFFC00000) == 0xF9000000):
                break
    return out


# ---------------- unicorn ----------------
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_UNMAPPED, UC_PROT_ALL
from unicorn.arm64_const import *

XREGS = [getattr(sys.modules["unicorn.arm64_const"], f"UC_ARM64_REG_X{i}") for i in range(29)]
SREGS = [getattr(sys.modules["unicorn.arm64_const"], f"UC_ARM64_REG_S{i}") for i in range(8)]


class Emu:
    STACK, HEAP, STUB = 0x10000000, 0x20000000, 0x30000000

    def __init__(self, heap=0x400000, writable_image=True):
        m = img()
        mu = self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(m) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, m)
        # bss 여유
        end = BASE + ((len(m) + 0xFFFF) & ~0xFFFF)
        self.bss_end = end
        try:
            mu.mem_map(end, 0x2000000)
        except Exception:
            pass
        mu.mem_map(self.STACK, 0x200000)
        mu.mem_map(self.HEAP, heap)
        mu.mem_map(self.STUB, 0x10000)
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        mu.mem_write(self.STUB, struct.pack("<I", 0xD65F03C0) * 0x4000)
        self.heap_next = self.HEAP + 0x1000
        self.heap_end = self.HEAP + heap
        self.stubs = {}
        self.events = []
        mu.hook_add(UC_HOOK_CODE, self._stub_hook, begin=self.STUB, end=self.STUB + 0xFFFF)

    def alloc(self, n, fill=0):
        a = self.heap_next
        self.heap_next += (n + 0xF) & ~0xF
        assert self.heap_next < self.heap_end
        self.mu.mem_write(a, bytes([fill]) * n)
        return a

    def stub_vt(self, nslots=0x100, name="vt"):
        vt = self.alloc(nslots * 8)
        base = self.STUB + 0x100 + (len(self.stubs) * 0x800) % 0xF000
        for i in range(nslots):
            self.mu.mem_write(vt + i * 8, struct.pack("<Q", base + i * 4))
        self.stubs[(base, base + nslots * 4)] = name
        return vt

    def _stub_hook(self, mu, addr, size, user):
        for (lo, hi), name in self.stubs.items():
            if lo <= addr < hi:
                self.events.append((name, (addr - lo) // 4 * 8, mu.reg_read(UC_ARM64_REG_X0)))
                mu.reg_write(UC_ARM64_REG_X0, 0)
                return

    def patch_ret(self, addr, x0=0, log=None):
        """원본 함수 진입점에서 바로 반환(스텁). log 이름이 있으면 인자 기록."""
        def h(mu, a, s, u):
            if log:
                self.events.append((log, [mu.reg_read(r) for r in XREGS[:4]]))
            mu.reg_write(UC_ARM64_REG_X0, x0)
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_X30))
        self.mu.hook_add(UC_HOOK_CODE, h, begin=addr, end=addr)

    def call(self, fn, *args, f=(), count=5_000_000):
        mu = self.mu
        for r, v in zip(XREGS, args):
            mu.reg_write(r, v)
        for r, v in zip(SREGS, f):
            mu.reg_write(r, struct.unpack("<I", struct.pack("<f", v))[0])
        mu.reg_write(UC_ARM64_REG_SP, self.STACK + 0x1F0000)
        mu.reg_write(UC_ARM64_REG_X29, 0)
        mu.reg_write(UC_ARM64_REG_X30, self.STUB + 0xFFF0)
        mu.emu_start(fn, self.STUB + 0xFFF0, count=count)
        return mu.reg_read(UC_ARM64_REG_X0)

    def wq(self, a, v):
        self.mu.mem_write(a, struct.pack("<Q", v & 0xFFFFFFFFFFFFFFFF))

    def rq(self, a):
        return struct.unpack("<Q", self.mu.mem_read(a, 8))[0]

    def wf(self, a, v):
        self.mu.mem_write(a, struct.pack("<f", v))

    def rf(self, a):
        return struct.unpack("<f", self.mu.mem_read(a, 4))[0]

    def rs(self, a, n=64):
        return bytes(self.mu.mem_read(a, n)).split(b"\0")[0].decode("utf-8", "replace")

    def ws(self, a, s):
        self.mu.mem_write(a, s.encode() + b"\0")


def out(*a):
    print(*a)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def is_code(v):
    return BASE <= v < BASE + TEXT_END


def vt_of(slot):
    """칸 주소 → (vtable 시작, 칸 번호). 시작 = 앞쪽으로 코드 포인터가 끊기는 곳."""
    a = slot
    while is_code(q(a - 8)):
        a -= 8
    return a, (slot - a) // 8


def rtti_name(vt):
    ti = q(vt - 8)
    if ti and BASE <= ti < BASE + len(img()):
        n = q(ti + 8)
        if BASE <= n < BASE + len(img()):
            return cstr(n)
    return ""


_imports = None


def imports():
    """GOT 주소 → 외부 함수 이름 (JUMP_SLOT)."""
    global _imports
    if _imports is None:
        raw = (ROOT / "extracted" / "exefs" / "main.img").read_bytes()
        mod0 = struct.unpack_from("<I", raw, 4)[0]
        dyn = mod0 + struct.unpack_from("<i", raw, mod0 + 4)[0]
        tags = {}
        while True:
            t, v = struct.unpack_from("<qQ", raw, dyn)
            dyn += 16
            if t == 0:
                break
            tags.setdefault(t, v)
        symtab, strtab = tags[6], tags[5]
        _imports = {}
        for r in range(tags[23], tags[23] + tags[2], 24):
            roff, info, addend = struct.unpack_from("<QQq", raw, r)
            no = struct.unpack_from("<I", raw, symtab + (info >> 32) * 24)[0]
            e = raw.index(b"\0", strtab + no)
            _imports[BASE + roff] = raw[strtab + no:e].decode()
    return _imports


def plt_name(stub):
    """PLT 스텁(adrp x16; ldr x17,[x16,#o]; add; br x17) → 이름."""
    d = dis(stub, 4)
    try:
        if len(d) == 4 and d[0].mnemonic == "adrp" and d[1].mnemonic == "ldr" and d[3].mnemonic == "br":
            page = int(d[0].op_str.split("#")[1], 16)
            off = int(d[1].op_str.split("#")[1].rstrip("]"), 16)
            return imports().get(page + off)
    except (IndexError, ValueError):
        pass
    return None


def hook_libc(e, names_seen=None):
    """자주 쓰는 libc PLT 를 파이썬 구현으로 대체(memcpy/memmove/memset/strlen/strcmp)."""
    impl = {}

    def memcpy(mu):
        d, s, n = (mu.reg_read(XREGS[i]) for i in range(3))
        if n:
            mu.mem_write(d, bytes(mu.mem_read(s, n)))
    def memset(mu):
        d, c, n = (mu.reg_read(XREGS[i]) for i in range(3))
        if n:
            mu.mem_write(d, bytes([c & 0xFF]) * n)
    def strlen(mu):
        s = mu.reg_read(XREGS[0]); n = 0
        while mu.mem_read(s + n, 1)[0]:
            n += 1
        mu.reg_write(XREGS[0], n)
    def strcmp(mu):
        a, b = mu.reg_read(XREGS[0]), mu.reg_read(XREGS[1]); i = 0
        while True:
            x, y = mu.mem_read(a + i, 1)[0], mu.mem_read(b + i, 1)[0]
            if x != y or x == 0:
                mu.reg_write(XREGS[0], (x - y) & 0xFFFFFFFFFFFFFFFF); return
            i += 1
    table = {"memcpy": memcpy, "memmove": memcpy, "memset": memset, "strlen": strlen, "strcmp": strcmp}
    # PLT 영역 스캔
    w = words()
    lo = (0x7103e99000 - BASE) // 4
    hi = min((0x7103e9e000 - BASE) // 4, len(w))
    for i in range(lo, hi):
        a = BASE + i * 4
        x = int(w[i])
        if (x & 0x9F00001F) == 0x90000010:      # adrp x16
            nm = plt_name(a)
            if nm in table:
                impl[a] = table[nm]
    def h(mu, a, s, u):
        f = impl.get(a)
        if f:
            f(mu)
            if names_seen is not None:
                names_seen.append(a)
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_X30))
    for a in impl:
        e.mu.hook_add(UC_HOOK_CODE, h, begin=a, end=a)
    return impl
