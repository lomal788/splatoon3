"""UI 애니 핸들 명령 처리 0x71013686f8 을 unicorn 으로 원본 실행해 명령 코드 → AnimTransform 호출을 기록한다.

핸들(0x?? B, 생성 0x7101363ef4): +0 vtable, +8 AnimTransform*, +0x10 명령(s32), +0x14 f32, +0x18 f32.
가짜 AnimTransform: +0 가짜 vtable(슬롯마다 ret 스텁), +0x18 → 애니 데이터(+8 u16 프레임 수, +0xa u8 루프 플래그),
+0x20 frame f32, +0x24 enable u8, +0x40/+0x48 리스트 노드(자기 자신), +0x50 speed f32, +0x58 → 레이아웃 흉내(+0x88 → 객체, +0x70 리스트).
AnimTransform 가상 호출(vt+0x20/0xc0/0xc8/0xd0/0xe0/0xe8)은 스텁에서 슬롯·x1·s0 을 기록하고 바로 돌아온다(구현은 실행하지 않음).
즉 검증 범위 = 명령 분기(점프 표 0x7104a9972a)와 각 분기가 넘기는 인자. AnimTransform 각 슬롯 내부 동작은 디컴파일 판독.

사용: ui_animcmd_emu.py
"""
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
FUNC = 0x71013686f8
STACK, HEAP, STUB = 0x10000000, 0x20000000, 0x30000000


def run(cmd, f14, f18, nframes=75, loop=1):
    img = IMG.read_bytes()
    mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
    mu.mem_write(BASE, img)
    for a in (STACK, HEAP, STUB):
        mu.mem_map(a, 0x100000)
    mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
    mu.mem_write(STUB, struct.pack("<I", 0xD65F03C0) * 0x400)
    vt = HEAP + 0x1000
    for off in range(0, 0x400, 8):
        mu.mem_write(vt + off, struct.pack("<Q", STUB + off))
    anim, data, lay, handle = HEAP + 0x2000, HEAP + 0x3000, HEAP + 0x4000, HEAP + 0x5000
    mu.mem_write(data, struct.pack("<QHB", 0, nframes, loop))
    mu.mem_write(anim, struct.pack("<Q", vt))
    mu.mem_write(anim + 0x18, struct.pack("<Q", data))
    mu.mem_write(anim + 0x20, struct.pack("<f", 12.5))          # 현재 프레임(임의)
    mu.mem_write(anim + 0x24, b"\x01")
    mu.mem_write(anim + 0x40, struct.pack("<QQ", anim + 0x40, anim + 0x40))
    mu.mem_write(anim + 0x50, struct.pack("<f", 1.0))
    mu.mem_write(anim + 0x58, struct.pack("<Q", lay))
    mu.mem_write(lay + 0x88, struct.pack("<Q", lay + 0x100))
    mu.mem_write(lay + 0x170, struct.pack("<QQ", lay + 0x170, lay + 0x170))
    mu.mem_write(handle, struct.pack("<QQiff", 0, anim, cmd, f14, f18))
    calls = []

    def hook(uc, addr, size, _):
        slot = addr - STUB
        s0 = struct.unpack("<f", struct.pack("<I", uc.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF))[0]
        calls.append((hex(slot), uc.reg_read(UC_ARM64_REG_X1) & 0xFFFFFFFF, round(s0, 4)))
    mu.hook_add(UC_HOOK_CODE, hook, begin=STUB, end=STUB + 0xFFF)
    sp = STACK + 0x80000
    mu.reg_write(UC_ARM64_REG_SP, sp)
    mu.reg_write(UC_ARM64_REG_X0, handle)
    mu.reg_write(UC_ARM64_REG_X30, STUB + 0xF00)
    mu.emu_start(FUNC, STUB + 0xF00, count=2000)
    calls = [c for c in calls if c[0] != hex(0xF00)]
    h = mu.mem_read(handle + 0x10, 12)
    a = mu.mem_read(anim + 0x20, 8)
    a50 = struct.unpack("<f", mu.mem_read(anim + 0x50, 4))[0]
    return dict(cmd=cmd, calls=calls, handle_cmd_after=struct.unpack("<i", h[:4])[0],
                anim_frame=round(struct.unpack("<f", a[:4])[0], 4), anim_enable=a[4], anim_speed=a50)


def main():
    rows = []
    for cmd in range(0, 13):
        r = run(cmd, -1.0 if cmd == 1 else 30.0, 2.0)
        rows.append(r)
        print(r)
    exp = {1: "0xc0", 2: "0xc8", 3: "0xc8", 4: "0xd0", 5: "0xd0", 6: "0xe0", 7: "0xe8", 9: "0x20"}
    ok = True
    for r in rows:
        want = exp.get(r["cmd"])
        got = [c[0] for c in r["calls"]]
        if want:
            good = want in got
        else:
            good = all(c not in ("0xc0", "0xc8", "0xd0", "0xe0", "0xe8") for c in got)
        if r["cmd"] <= 11:
            good = good and r["handle_cmd_after"] == (0 if r["cmd"] != 0 else 0)
        ok &= good
        print(("PASS " if good else "FAIL ") + f"cmd {r['cmd']}: {got} frame={r['anim_frame']} en={r['anim_enable']} speed={r['anim_speed']}")
    print("ALL PASS" if ok else "SOME FAIL")


if __name__ == "__main__":
    main()
