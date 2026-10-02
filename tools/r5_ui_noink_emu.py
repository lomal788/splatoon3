"""r5 ui: 잉크 부족 화면(Cmn_NoInk_00, SplUICmnNoInk00Screen) 요청·갱신을 unicorn 으로 원본 실행해 독립 재구현과 비교한다.

원본 함수
  요청  0x7103276e2c(screen, kind)   ← 0x7100feb5c4(kind) 가 화면을 이름으로 찾은 뒤 부름
  갱신  0x7103277148(screen)         ← 화면 vtable 0x71056dffc8 슬롯 100(+0x320)
  상태 질의(원본 그대로 실행): vt+0x2d0 = 0x7101363e48(열림), vt+0x2d8 = 0x7101363e6c(닫힘), vt+0x2e8 = 0x7101363ec4(닫는 중)
  애니 프레임 수: 0x7100851c78(원본 그대로: *(anim+0x18)+8 u16)

스텁(검증하지 않은 범위)
  vt+0x2b0(열기)·vt+0x2b8(닫기): 호출만 기록하고 바로 돌아온다. 화면 상태 바이트(+0x16d, +0x16e)의 실제 전이(In/Out 애니 진행)는
  UI 프레임워크 몫이라 시나리오가 프레임마다 직접 넣는다(원본과 재구현에 같은 값).
  0x71013621d0(텍스트 페인에 메시지 넣기): 인자(페인 이름, 라벨)만 기록.
  애니 핸들 명령(+0x10/+0x14/+0x18)은 기록만 하고 처리(0x71013686f8)는 하지 않는다(그 함수는 ui_animcmd_emu.py 에서 별도 검증).

사용: r5_ui_noink_emu.py   (결과를 analysis/r5_ui/noink_emu.json 에도 저장)
"""
import json
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X30, \
    UC_ARM64_REG_SP, UC_ARM64_REG_PC, UC_ARM64_REG_CPACR_EL1

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE = 0x7100000000
REQ, UPD, SETTEXT = 0x7103276e2c, 0x7103277148, 0x71013621d0
STACK, HEAP, STUB = 0x10000000, 0x20000000, 0x30000000
VT = HEAP + 0x1000
S = HEAP + 0x4000                      # 화면 객체
H_FI, H_TY = HEAP + 0x2000, HEAP + 0x2100  # 애니 핸들(FrameIn, Type)
A_FI, A_TY = HEAP + 0x2200, HEAP + 0x2300  # AnimTransform 흉내
D_FI, D_TY = HEAP + 0x2400, HEAP + 0x2500  # 애니 데이터(+8 u16 프레임 수)
FI_FRAMES, TY_FRAMES = 48, 3           # Cmn_NoInk_00_FrameIn / _Type bflan frameSize [데이터]


class Orig:
    def __init__(self):
        img = IMG.read_bytes()
        mu = self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        for a in (STACK, HEAP, STUB):
            mu.mem_map(a, 0x100000)
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        mu.mem_write(STUB, struct.pack("<I", 0xD65F03C0) * 0x400)
        for off in range(0, 0x400, 8):
            mu.mem_write(VT + off, struct.pack("<Q", STUB + off))
        mu.mem_write(VT + 0x2d0, struct.pack("<Q", 0x7101363e48))
        mu.mem_write(VT + 0x2d8, struct.pack("<Q", 0x7101363e6c))
        mu.mem_write(VT + 0x2e8, struct.pack("<Q", 0x7101363ec4))
        mu.mem_write(S, struct.pack("<Q", VT))
        mu.mem_write(S + 0x28, struct.pack("<Q", HEAP + 0x6000))
        mu.mem_write(S + 0x250, struct.pack("<QQ", H_FI, H_TY))
        for h, a, d, n in ((H_FI, A_FI, D_FI, FI_FRAMES), (H_TY, A_TY, D_TY, TY_FRAMES)):
            mu.mem_write(h, struct.pack("<QQiff", 0, a, 0, 0.0, 0.0))
            mu.mem_write(a + 0x18, struct.pack("<Q", d))
            mu.mem_write(a + 0x40, struct.pack("<QQ", a + 0x40, a + 0x40))   # 목록 밖(자기 연결)
            mu.mem_write(d + 8, struct.pack("<H", n))
        self.events = []
        mu.hook_add(UC_HOOK_CODE, self._stub, begin=STUB, end=STUB + 0xFFF)
        mu.hook_add(UC_HOOK_CODE, self._settext, begin=SETTEXT, end=SETTEXT)

    def _cstr(self, p):
        return bytes(self.mu.mem_read(p, 32)).split(b"\0")[0].decode()

    def _stub(self, uc, addr, size, _):
        off = addr - STUB
        if off == 0x2b0:
            self.events.append("open")
        elif off == 0x2b8:
            self.events.append("close")

    def _settext(self, uc, addr, size, _):
        pane = self._cstr(struct.unpack("<Q", uc.mem_read(uc.reg_read(UC_ARM64_REG_X1), 8))[0])
        label = self._cstr(struct.unpack("<Q", uc.mem_read(uc.reg_read(UC_ARM64_REG_X2), 8))[0])
        self.events.append(f"text:{pane}:{label}")
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))

    def set_state(self, b16d, b16e, ty_in_list):
        self.mu.mem_write(S + 0x16d, struct.pack("<bB", b16d, b16e))
        nxt = A_TY + 0x40 if not ty_in_list else HEAP + 0x7000
        self.mu.mem_write(A_TY + 0x48, struct.pack("<Q", nxt))

    def call(self, fn, *args):
        mu = self.mu
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0x80000)
        for r, v in zip((UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2), args):
            mu.reg_write(r, v)
        mu.reg_write(UC_ARM64_REG_X30, STUB + 0xF00)
        mu.emu_start(fn, STUB + 0xF00, count=5000)

    def snap(self):
        m = self.mu
        flash, hold, timer, kind = struct.unpack("<iiii", m.mem_read(S + 0x260, 16))
        dirty = m.mem_read(S + 0x270, 1)[0]
        hcmd = []
        for h in (H_FI, H_TY):
            c, a, b = struct.unpack("<iff", m.mem_read(h + 0x10, 12))
            hcmd.append((c, a, b))
            m.mem_write(h + 0x10, struct.pack("<i", 0))   # 슬롯 73 처리(0x71013686f8)는 명령만 0으로 지우고 a/b 는 남김
        ev, self.events = self.events, []
        return dict(flash=flash, hold=hold, timer=timer, kind=kind, dirty=dirty, fi=hcmd[0], ty=hcmd[1], ev=ev)


class Reimpl:
    """디컴파일 판독을 독립적으로 옮긴 식(원본 코드 미사용)."""
    TEXT = {0: ("T_NoInk_00", "000"), 1: ("T_NoInk_01", "001"), 2: ("T_NoInk_01", "003"),
            3: ("T_NoInk_00", "002"), 4: ("T_NoInk_00", "004"), 5: ("T_NoInk_00", "004")}
    TYFRAME = {0: 0, 3: 2, 4: 3, 5: 4}

    def __init__(self):
        self.flash = self.hold = self.timer = self.kind = 0
        self.dirty = 0
        self.b16d = self.b16e = 0
        self.ty_in_list = False
        self.events, self.fi, self.ty = [], (0, 0.0, 0.0), (0, 0.0, 0.0)

    def is_open(self):
        return self.b16e == 2 and self.b16d >= 0

    def is_closed(self):
        return self.b16e == 0 and self.b16d < 1

    def is_closing(self):
        return self.b16e == 3 or (self.b16d < 0 and self.b16e in (1, 2))

    def request(self, kind):
        if self.kind != kind:
            self.kind, self.dirty = kind, 1
            f = self.TYFRAME.get(kind, 1)
            a, b = self.ty[1], self.ty[2]
            if kind == 0:
                skip = a == 0.0 and b == 0.0 and self.ty_in_list
            else:
                skip = TY_FRAMES < f or TY_FRAMES == 0 or (a == float(f) and b == 0.0 and self.ty_in_list)
            if not skip:
                self.ty = (4, float(f), 0.0)
        if not self.is_open() or self.hold == 0:
            self.timer = 40
        self.hold = 2
        if self.is_closed() or self.is_closing():
            self.flash = 0x20
            self.events.append("open")
        elif self.flash == 0:
            self.fi = (1, -1.0, 1.0)
            self.flash = FI_FRAMES

    def update(self):
        if self.dirty:
            p, l = self.TEXT.get(self.kind, ("T_NoInk_01", "003"))
            self.events.append(f"text:{p}:{l}")
            self.dirty = 0
        if self.is_open():
            if self.flash > 0:
                self.flash -= 1
            if self.timer > 0:
                self.timer -= 1
            if self.hold > 0:
                self.hold -= 1
            if self.timer < 1 and self.hold < 1:
                self.events.append("close")

    def snap(self):
        r = dict(flash=self.flash, hold=self.hold, timer=self.timer, kind=self.kind, dirty=self.dirty,
                 fi=self.fi, ty=self.ty, ev=self.events)
        self.events = []
        self.fi, self.ty = (0,) + self.fi[1:], (0,) + self.ty[1:]   # 핸들 명령만 지우고 a/b 유지
        return r


def scenario(name, frames):
    """frames: [(요청 kind 또는 None, (b16d, b16e), type 애니 목록 안 여부)] — 프레임마다 요청(있으면) → 갱신."""
    o, r = Orig(), Reimpl()
    rows, ok = [], True
    for i, (req, (d, e), inlist) in enumerate(frames):
        o.set_state(d, e, inlist)
        r.b16d, r.b16e, r.ty_in_list = d, e, inlist
        if req is not None:
            o.call(REQ, S, req)
            r.request(req)
        o.call(UPD, S)
        r.update()
        a, b = o.snap(), r.snap()
        a["fi"] = tuple(round(x, 4) if isinstance(x, float) else x for x in a["fi"])
        a["ty"] = tuple(round(x, 4) if isinstance(x, float) else x for x in a["ty"])
        same = a == b
        ok &= same
        rows.append(dict(frame=i, req=req, state=[d, e], orig=a, reimpl=b, match=same))
    return name, ok, rows


CLOSED, OPENING, OPEN, CLOSING = (0, 0), (0, 1), (0, 2), (0, 3)


def build():
    sc = []
    # 1) 슈터 잉크 부족(kind 0) 한 번: 닫힘 → 열기 요청 → 열림 → 40프레임 뒤 닫기
    f = [(0, CLOSED, False)] + [(None, OPENING, False)] * 8 + [(None, OPEN, False)] * 45
    sc.append(("kind0_single", f))
    # 2) 계속 쏘는 동안 매 프레임 요청(유지) 60프레임 후 멈춤
    f = [(0, CLOSED, False)] + [(0, OPENING, False)] * 8 + [(0, OPEN, False)] * 60 + [(None, OPEN, False)] * 10
    sc.append(("kind0_hold", f))
    # 3) 3프레임 간격 요청(hold 2 를 넘김) — 타이머 재설정 경계
    f = [(0, CLOSED, False)] + [(None, OPENING, False)] * 4
    for _ in range(20):
        f += [(0, OPEN, False), (None, OPEN, False), (None, OPEN, False)]
    f += [(None, OPEN, False)] * 45
    sc.append(("kind0_every3", f))
    # 4) 열린 동안 FrameIn 재생(flash 0 일 때) — 열림 상태에서 오랜만에 요청
    f = [(0, OPEN, False)] + [(None, OPEN, False)] * 35 + [(0, OPEN, False)] + [(None, OPEN, False)] * 5
    sc.append(("flash_replay_open", f))
    # 5) 종류 전환 0→1→2→3→4→5→6, 목록 안/밖
    f = []
    for k in (0, 1, 2, 3, 4, 5, 6, 3, 3):
        f.append((k, OPEN, False))
        f.append((None, OPEN, True))
    for k in (0, 1, 2, 3, 4, 5, 6):
        f.append((k, OPEN, True))
    sc.append(("kind_switch", f))
    # 6) 닫는 중 요청(다시 열기), 음수 b16d
    f = [(0, OPEN, False), (None, CLOSING, False), (0, CLOSING, False), (None, (-1, 2), False), (0, (-1, 1), False),
         (None, OPENING, False), (None, OPEN, False)]
    sc.append(("reopen_while_closing", f))
    return sc


def main():
    total = good = 0
    out = []
    for name, frames in build():
        n, ok, rows = scenario(name, frames)
        cnt = sum(1 for x in rows if x["match"])
        total += len(rows)
        good += cnt
        out.append(dict(name=n, frames=len(rows), match=cnt, rows=rows))
        print(f"{'PASS' if ok else 'FAIL'} {n}: {cnt}/{len(rows)}")
        if not ok:
            for x in rows:
                if not x["match"]:
                    print("  frame", x["frame"], "orig", x["orig"], "reimpl", x["reimpl"])
                    break
    print(f"합계 {good}/{total} 프레임 일치")
    dst = ROOT / "analysis" / "r5_ui" / "noink_emu.json"
    dst.write_text(json.dumps(dict(total=total, match=good, scenarios=out), ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
