"""r11 gfx-diff 그림자: 정적 깊이 그림자 맞춤 0x7103754fe8 을 unicorn 으로 원본 실행한다.
- 객체: x0 = 정적 그림자 객체(manager+0x7e8). 생성자 0x710375418c 가 두는 vtable 만 같은 값으로 둔다:
  sead LookAtCamera vtable 0x7105721238 @+0xa18(슬롯 +0x20 = 0x710358857c), OrthoProjection vtable 0x7105721438 @+0xaa8
  (슬롯 +0x58 = 0x7103589f84, +0x60 = 0x7103589b48). 나머지 필드는 fe8 이 모두 쓴 뒤 읽는다. 외부 스텁 없음.
- 입력: +0xba8 AABB min xyz, +0xbb4 max xyz (0x710374f950 이 manager+0x1390 에 쓰는 값), +0xbc0 광원 방향 xyz(manager+0x13a8).
- 출력: +0xa20 view 3x4, +0xab4 proj 4x4, +0xb40..+0xb54 near/far/top/bottom/left/right, +0xb58..+0xb94 텍스처 행렬 4행.
사용: PY web/tools/r11_gfx_static_shadow_emu.py → web/games/splatoon3/tests/fixtures/r11_static_shadow_fit_native.json
"""
import json, random, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_MEM_UNMAPPED
from unicorn.arm64_const import *
ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted/exefs/main.reloc.img"
BASE = 0x7100000000
STACK, HEAP, RET = 0x10000000, 0x20000000, 0x30000000
FIT = 0x7103754fe8
CAM_VT, PROJ_VT = 0x7105721238, 0x7105721438
OBJ = HEAP + 0x100
f = lambda v: struct.unpack('<f', struct.pack('<f', v))[0]


class Emu:
    def __init__(self):
        img = IMG.read_bytes()
        mu = self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        size = (len(img) + 0x2000000 + 0xFFFF) & ~0xFFFF
        mu.mem_map(BASE, size); mu.mem_write(BASE, img)
        mu.mem_map(STACK, 0x100000); mu.mem_map(HEAP, 0x10000); mu.mem_map(RET, 0x1000)
        mu.mem_write(RET, struct.pack("<II", 0xD65F03C0, 0xD65F03C0))
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        def bad(uc, access, addr, sz, val, ud):
            print("unmapped %x pc=%x" % (addr, uc.reg_read(UC_ARM64_REG_PC))); return False
        mu.hook_add(UC_HOOK_MEM_UNMAPPED, bad)
        self.base_obj = None

    def call(self, fn, x0):
        mu = self.mu
        mu.reg_write(UC_ARM64_REG_X0, x0)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000); mu.reg_write(UC_ARM64_REG_LR, RET)
        mu.emu_start(fn, RET, count=2000000)

    def init(self):
        self.mu.mem_write(HEAP, b"\0" * 0x10000)
        self.mu.mem_write(OBJ + 0xa18, struct.pack("<Q", CAM_VT))
        self.mu.mem_write(OBJ + 0xaa8, struct.pack("<Q", PROJ_VT))
        self.base_obj = bytes(self.mu.mem_read(OBJ, 0x4000))

    def run(self, mn, mx, d):
        mu = self.mu
        mu.mem_write(OBJ, self.base_obj)
        mu.mem_write(OBJ + 0xba8, struct.pack("<6f", *mn, *mx))
        mu.mem_write(OBJ + 0xbc0, struct.pack("<3f", *d))
        self.call(FIT, OBJ)
        rd = lambda a, n: list(struct.unpack("<%df" % n, bytes(mu.mem_read(OBJ + a, 4 * n))))
        bits = lambda a, n: list(struct.unpack("<%dI" % n, bytes(mu.mem_read(OBJ + a, 4 * n))))
        return {"view": rd(0xa20, 12), "proj": rd(0xab4, 16), "ortho": rd(0xb40, 6),
                "tex": rd(0xb58, 16), "texBits": bits(0xb58, 16)}


def main():
    e = Emu(); e.init()
    rnd = random.Random(7)
    lobby_dir = [0.04313143342733383, -0.56640625, -0.8229967355728149]
    cases = [{"name": "unit", "min": [-1, -1, -1], "max": [1, 1, 1], "dir": lobby_dir}]
    for k in range(48):
        c = [rnd.uniform(-200, 200) for _ in range(3)]
        h = [rnd.uniform(.5, 150) for _ in range(3)]
        dv = [rnd.uniform(-1, 1) for _ in range(3)]
        if k % 8 == 0: dv[1] = -abs(dv[1]) - .5
        n = sum(v * v for v in dv) ** .5
        cases.append({"name": "rand%d" % k, "min": [f(c[i] - h[i]) for i in range(3)], "max": [f(c[i] + h[i]) for i in range(3)],
                      "dir": [f(v / n) for v in dv]})
    for c in cases:
        c["out"] = e.run(c["min"], c["max"], c["dir"])
    out = ROOT / "web/games/splatoon3/tests/fixtures/r11_static_shadow_fit_native.json"
    out.write_text(json.dumps({"source": "unicorn 0x7103754fe8 fit (sead LookAtCamera/OrthoProjection vtable 원본)", "cases": cases}, indent=1), encoding="utf-8")
    print(out, len(cases)); print(json.dumps(cases[0]["out"]))


if __name__ == "__main__":
    main()
