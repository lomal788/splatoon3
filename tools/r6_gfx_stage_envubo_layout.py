"""r6 gfx_stage: gsys 환경 UBO(gsys_environment, 뷰 레코드 *(gsys+0x578) 0xd0 간격)의 멤버 선언을 원본 코드로 실행해
멤버 순서·종류·성분 수·개수·바이트 오프셋을 뽑는다.

- 실행 범위: 0x71036ae130 안의 레코드 0 선언 구간 0x71036ae468 → 레코드 공통 경로 0x71036ae374(0x71036af500 또는 0x71036af518 의 분기 대상)
  만 원본 그대로 실행한다. 이 구간은 startDeclare(0x71035b78ec, 멤버 수 w1) 한 번과 인라인 선언 35회다.
- 스텁: startDeclare 0x71035b78ec 만 대체(힙 할당 대신 표 헤더 {u64 표, u16 총수, u16 현재수} 를 만들어 레코드+0x10 에 넣고
  커서 레코드+0x38 = 0 — 원본 함수 끝부분 0x71035b79f4~0x71035b7a18 과 같은 결과).
- 입력: 레코드·gsys 객체는 0 으로 채운 가짜 메모리. 선언 구간이 읽는 것은 gsys+0x5b4(마지막 원시 블록 멤버 바이트 수) 하나이고
  0 이면 그 멤버를 선언하지 않는다. 0x70(SH 7×vec4, 환경광 관리자가 뷰 레코드 +0xa0 에 쓰는 크기)으로 둔다 — 실제 값은 생성 인자(x1+0x10) [미확인].
사용: PY web/tools/r6_gfx_stage_envubo_layout.py → analysis/r6_gfx_stage/envubo_layout.tsv
"""
import struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn.arm64_const import *

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted/exefs/main.reloc.img"
BASE = 0x7100000000
STACK, OBJ, RET = 0x10000000, 0x20000000, 0x30000000
START, END, STARTDECL = 0x71036ae468, 0x71036ae374, 0x71035b78ec

img = IMG.read_bytes()
mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF); mu.mem_write(BASE, img)
for a, n in ((STACK, 0x100000), (OBJ, 0x100000), (RET, 0x1000)):
    mu.mem_map(a, n)
mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
REC, GSYS, HDR, TBL = OBJ, OBJ + 0x1000, OBJ + 0x4000, OBJ + 0x5000
q = lambda a: struct.unpack("<Q", mu.mem_read(a, 8))[0]


def hook(uc, addr, size, ud):
    if addr == STARTDECL:
        n = uc.reg_read(UC_ARM64_REG_X1) & 0xFFFFFFFF
        rec = uc.reg_read(UC_ARM64_REG_X0)
        uc.mem_write(HDR, struct.pack("<QHH", TBL, n, 0))
        uc.mem_write(rec + 0x10, struct.pack("<Q", HDR))
        uc.mem_write(rec + 0x38, struct.pack("<I", 0))
        ud["n"] = n
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))


def bad(uc, access, addr, size, value, ud):
    print("unmapped", hex(addr), "pc", hex(uc.reg_read(UC_ARM64_REG_PC)))
    return False


ud = {}
mu.hook_add(UC_HOOK_CODE, hook, ud, STARTDECL, STARTDECL + 4)
mu.hook_add(UC_HOOK_MEM_UNMAPPED, bad)
sp = STACK + 0xF0000
fp = sp + 0xa0
mu.mem_write(GSYS + 0x5b4, struct.pack("<I", 0x70))  # 뷰 레코드 +0xa0 에 들어가는 SH 크기(0x710102a3e8 가 0x70 기록)와 같은 값
mu.mem_write(sp + 0x10, struct.pack("<QQ", REC + 0x10, REC + 0x38))
mu.mem_write(sp + 0x20, struct.pack("<Q", (fp - 0x20) | 4))
regs = {UC_ARM64_REG_SP: sp, UC_ARM64_REG_X29: fp, UC_ARM64_REG_X26: REC, UC_ARM64_REG_X27: 0,
        UC_ARM64_REG_X20: GSYS, UC_ARM64_REG_X19: 0xc, UC_ARM64_REG_X22: 6, UC_ARM64_REG_X28: 0xd0,
        UC_ARM64_REG_X23: 0, UC_ARM64_REG_X24: 1, UC_ARM64_REG_X25: 0x7104abfdc8}
for r, v in regs.items():
    mu.reg_write(r, v)
mu.emu_start(START, END, count=200000)
n = ud["n"]
cur = struct.unpack("<H", mu.mem_read(HDR + 0xa, 2))[0]
size = struct.unpack("<I", mu.mem_read(REC + 0x38, 4))[0]
lines = ["index\tkind\tcomps\tcount\tbyte_off\tvec4\tsize_B"]
for i in range(cur):
    cnt, off, comps, kind = struct.unpack("<IHHB", mu.mem_read(TBL + i * 12, 9))
    lines.append(f"{i}\t{kind}\t{comps}\t{cnt}\t{off:#x}\t[{off // 16}]{'.xyzw'[1 + (off % 16) // 4] if off % 16 else ''}\t{comps * cnt * 4}")
lines.append(f"# startDeclare n={n}, declared={cur}, cursor(end)={size:#x} ({size} B)")
txt = "\n".join(lines)
print(txt)
(ROOT / "analysis/r6_gfx_stage/envubo_layout.tsv").write_text(txt + "\n", encoding="utf-8")
