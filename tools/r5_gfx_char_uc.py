"""r5 gfx_char 하네스 공용: network_uc.UC + PLT(외부 함수) 처리.

PLT 스텁(0x7103e99000~0x7103e9e000)에 들어오면 GOT 이름으로 분기한다.
memcpy/memmove/memset/memcmp/strlen/strcmp/strncmp/sqrtf 만 파이썬으로 실행하고,
나머지 외부 함수는 0 반환 스텁으로 두고 self.plt_stubbed 에 이름을 기록한다(스텁 범위 보고용).
"""
import math
import struct
import subprocess
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import (UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2,
                                 UC_ARM64_REG_S0, UC_ARM64_REG_LR, UC_ARM64_REG_PC)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC, STUB, BASE  # noqa: E402

PLT_LO, PLT_HI = 0x7103e99000, 0x7103e9e000


def _imports():
    out = subprocess.run([sys.executable, str(Path(__file__).parent / "player_imports.py")],
                         capture_output=True, text=True).stdout
    d = {}
    for ln in out.splitlines():
        a, n = ln.split()
        d[int(a, 16)] = n
    return d


class GUC(UC):
    def __init__(self):
        super().__init__()
        self._raw = (Path(__file__).resolve().parents[2] / "extracted" / "exefs" / "main.reloc.img").read_bytes()
        self.got = _imports()
        self.plt_stubbed = []
        self.mu.hook_add(UC_HOOK_CODE, self._plt, begin=PLT_LO, end=PLT_HI)

    def _cstr(self, a, n=0x400000):
        out = bytearray()
        while len(out) < n:
            c = self.mu.mem_read(a + len(out), 1)[0]
            if c == 0:
                break
            out.append(c)
        return bytes(out)

    def _plt(self, mu, addr, size, user):
        w0 = struct.unpack_from("<I", self._raw, addr - BASE)[0]
        if (w0 & 0x9F000000) != 0x90000000:  # adrp 가 아니면 스텁 중간
            return
        w1 = struct.unpack_from("<I", self._raw, addr + 4 - BASE)[0]
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
            a = self._cstr(x0, x2 if name == "strncmp" else 0x400000)
            b = self._cstr(x1, x2 if name == "strncmp" else 0x400000)
            ret = 0 if a == b else (1 if a > b else 0xFFFFFFFF)
        elif name == "memcmp":
            a = bytes(mu.mem_read(x0, x2)) if x2 else b""
            b = bytes(mu.mem_read(x1, x2)) if x2 else b""
            ret = 0 if a == b else (1 if a > b else 0xFFFFFFFF)
        elif name == "sqrtf":
            s = struct.unpack("<f", struct.pack("<I", mu.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF))[0]
            r = math.sqrt(s) if s >= 0 else float("nan")
            mu.reg_write(UC_ARM64_REG_S0, struct.unpack("<I", struct.pack("<f", r))[0])
        else:
            self.plt_stubbed.append(name)
        mu.reg_write(UC_ARM64_REG_X0, ret)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    def wq(self, a, v):
        self.mu.mem_write(a, struct.pack("<Q", v & 0xFFFFFFFFFFFFFFFF))

    def rq(self, a):
        return struct.unpack("<Q", self.mu.mem_read(a, 8))[0]

    def cstr(self, s):
        b = s.encode() + b"\0"
        a = self.alloc(len(b) + 16)
        self.mu.mem_write(a, b)
        return a
