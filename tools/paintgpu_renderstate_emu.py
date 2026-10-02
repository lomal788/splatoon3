"""도색 렌더러 모드별 렌더 상태(0x74 B × 18) 원본 실행 추출.
0x7102c16e2c(18개 RenderState 기본 생성자 0x7103588f30) → 0x7102c16ed0(모드별 설정)을 unicorn 으로 실행하고
바인드 함수 0x7103588fcc 판독으로 얻은 필드 배치로 출력한다.
스텁: 렌더러+0x8a8 객체 vt+0x20 호출(ret), 규칙 값(*(*(*0x71058e42f8+200)+0x6548)+0x3c)은 인자로 공급.
셰이더 변형 표 등록 루프(0x71035aeb64 호출) 진입 시 정지 — 그 전 상태 설정만 실행.
사용: paintgpu_renderstate_emu.py [규칙값 ...]   (기본 1 5)"""
import struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UcError
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
STACK, HEAP, CODE = 0x10000000, 0x20000000, 0x30000000
G_RULEROOT = 0x71058E42F8

FUNC = {1: "NEVER", 2: "LESS", 3: "EQUAL", 4: "LEQUAL", 5: "GREATER", 6: "NOTEQUAL", 7: "GEQUAL", 8: "ALWAYS"}
SOP = {1: "KEEP", 2: "ZERO", 3: "REPLACE", 4: "INCR", 5: "DECR", 6: "INVERT", 7: "INCR_WRAP", 8: "DECR_WRAP"}


def run(rule):
    img = IMG.read_bytes()
    mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
    mu.mem_write(BASE, img)
    mu.mem_map(STACK, 0x100000); mu.mem_map(HEAP, 0x100000); mu.mem_map(CODE, 0x1000)
    mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
    mu.mem_write(CODE, struct.pack("<I", 0xD65F03C0) * 0x400)
    R = HEAP + 0x1000                      # 렌더러 0x958 B
    VT = HEAP + 0x100                      # 가짜 vtable: 모든 슬롯 = ret
    for i in range(0x40):
        mu.mem_write(VT + i * 8, struct.pack("<Q", CODE + 0x200))
    mu.mem_write(R + 0x8a8, struct.pack("<Q", VT))
    F, G, H = HEAP + 0x4000, HEAP + 0x5000, HEAP + 0x20000
    mu.mem_write(G_RULEROOT, struct.pack("<Q", F))
    mu.mem_write(F + 200, struct.pack("<Q", G))
    mu.mem_write(G + 0x6548, struct.pack("<Q", H))
    mu.mem_write(H + 0x3c, struct.pack("<i", rule))

    def call(fn, x0, stop=None):
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0x80000)
        mu.reg_write(UC_ARM64_REG_X0, x0)
        mu.reg_write(UC_ARM64_REG_X30, CODE + 0x100)
        hs = []
        if stop:
            def hk(m, a, s, u):
                if a == stop:
                    m.emu_stop()
            hs.append(mu.hook_add(UC_HOOK_CODE, hk))
        try:
            mu.emu_start(fn, CODE + 0x100, count=200000)
        except UcError as e:
            pc = mu.reg_read(UC_ARM64_REG_PC)
            if not (0x7102C16ED0 <= pc < 0x7102C17AE0):
                raise
            print(f"#  {hex(pc)} 에서 정지({e}) — 셰이더 표 단계 진입 전 메모리 접근")
        for h in hs:
            mu.hook_del(h)

    call(0x7102C16E2C, R)
    call(0x7102C16ED0, R, stop=0x71035AEB64)
    return [bytes(mu.mem_read(R + i * 0x74, 0x74)) for i in range(18)]


def desc(s):
    b = lambda o: s[o]
    u32 = lambda o: struct.unpack_from("<I", s, o)[0]
    blend = u32(4)
    cm = u32(0x1c)
    t0 = s[0x28:0x2e]
    d = dict(depthTest=b(0), depthWrite=b(1), depthFunc=FUNC.get(b(0x64), b(0x64)),
             stencil=b(3), sFunc=FUNC.get(b(0x6a), b(0x6a)), sRef=u32(0x20), sMask=hex(u32(0x24)),
             sOp=(SOP.get(b(0x67), b(0x67)), SOP.get(b(0x68), b(0x68)), SOP.get(b(0x69), b(0x69))),
             blendMask=hex(blend), blend0=t0.hex(), chanMask0=f"{cm & 0xf:04b}"[::-1], chanMask1=f"{(cm >> 4) & 0xf:04b}"[::-1],
             cull=b(0x65))
    return d


def main():
    rules = [int(x) for x in sys.argv[1:]] or [1, 5]
    for rule in rules:
        print(f"# 규칙값 {rule}")
        for i, s in enumerate(run(rule)):
            d = desc(s)
            print(f"mode {i:2d}: " + " ".join(f"{k}={v}" for k, v in d.items()))


if __name__ == "__main__":
    main()
