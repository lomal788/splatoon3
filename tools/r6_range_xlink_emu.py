"""xlink2 ActionTriggerCtrl 매 프레임 calc(0x7103895f64)를 unicorn 으로 원본 실행해
같은 액션의 프레임이 뒤로 갈 때(표적 재피격 DamageShot 재재생) 트리거가 다시 방출되는지 확인한다.

- 이미지: extracted/exefs/main.reloc.img 를 0x7100000000 에 올림.
- 입력 구조체는 함수가 읽는 오프셋만 합성(ctrl, 사용자 인스턴스, 리소스, 트리거 표, 상태 표, 액션).
- 스텁: 방출 0x7103899c68(ret 로 덮고 인자 기록), 리소스 접근자 vt+0x10(합성 객체 반환).
  이벤트 정리 경로의 전역 객체 호출(0x710599ada8 등)은 핸들 +0x28 = 0 으로 두어 타지 않게 했다.
- 재구현(아래 ref())과 방출 호출·핸들 끄기·상태를 시나리오마다 비교한다.
"""
import json
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
OUT = ROOT / "analysis" / "r6_range" / "xlink_regress_emu.json"
BASE = 0x7100000000
FN = 0x7103895F64
EMIT = 0x7103899C68
STACK = 0x10000000
HEAP = 0x20000000
STUB = 0x30000000
END = STUB + 0xF00
RET = struct.pack("<I", 0xD65F03C0)

img = IMG.read_bytes()


class H:
    def __init__(self):
        mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        self.mu = mu
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
        mu.mem_write(BASE, img)
        mu.mem_write(EMIT, RET)
        mu.mem_map(STACK, 0x100000)
        mu.mem_map(HEAP, 0x100000)
        mu.mem_map(STUB, 0x1000)
        mu.mem_write(STUB, RET * 0x400)
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        self.nxt = HEAP
        self.emits = []
        self.q_ret = 0
        mu.hook_add(UC_HOOK_CODE, self._hk, begin=EMIT, end=EMIT)
        mu.hook_add(UC_HOOK_CODE, self._hk_stub, begin=STUB, end=STUB + 0xFFF)

    def alloc(self, n):
        a = self.nxt
        self.nxt += (n + 0xF) & ~0xF
        self.mu.mem_write(a, b"\0" * n)
        return a

    def _hk(self, mu, addr, size, user):
        self.emits.append({
            "x1": mu.reg_read(UC_ARM64_REG_X1) & 0xFFFFFFFF,
            "idx": mu.reg_read(UC_ARM64_REG_X2) & 0xFFFFFFFF,
            "x3": mu.reg_read(UC_ARM64_REG_X3),
            "x4": mu.reg_read(UC_ARM64_REG_X4),
        })

    def _hk_stub(self, mu, addr, size, user):
        if addr == STUB + 0x10:
            mu.reg_write(UC_ARM64_REG_X0, self.q_ret)

    def w64(self, a, v):
        self.mu.mem_write(a, struct.pack("<Q", v & 0xFFFFFFFFFFFFFFFF))

    def w32(self, a, v):
        self.mu.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))

    def w16(self, a, v):
        self.mu.mem_write(a, struct.pack("<H", v & 0xFFFF))

    def w8(self, a, v):
        self.mu.mem_write(a, bytes([v & 0xFF]))

    def r32(self, a):
        return struct.unpack("<i", self.mu.mem_read(a, 4))[0]

    def r64(self, a):
        return struct.unpack("<Q", self.mu.mem_read(a, 8))[0]

    def r8(self, a):
        return self.mu.mem_read(a, 1)[0]


def run(sc):
    h = H()
    n = len(sc["trig"])
    ctrl = h.alloc(0x40)
    inst = h.alloc(0x40)
    y = h.alloc(0x40)
    acc = h.alloc(0x40)
    vt = h.alloc(0x40)
    for k in range(8):
        h.w64(vt + 8 * k, STUB + 8 * k)
    res = h.alloc(0xC0)
    res8 = h.alloc(0x40)
    trig = h.alloc(0x28 * n)
    state_hdr = h.alloc(0x20)
    states = h.alloc(0x28 * n)
    act = h.alloc(0x20)
    h.w64(ctrl + 8, inst)
    h.w64(inst + 0x38, y)
    h.w64(y + 0x18, acc)
    h.w64(acc, vt)
    h.w32(acc + 0x18, 0)
    h.w64(acc + 0x20, res)
    h.w8(res + 0xB0, 1)
    h.w64(res + 0x48, trig)
    h.w64(res + 8, res8)
    h.w32(res8 + 0x1C, n)
    ures = h.alloc(0x90)
    ctb_base = h.alloc(0x30 * n)
    tab80 = h.alloc(8 * n)
    h.w64(ures + 0x28, ctb_base)
    h.w32(ures + 0x78, n)
    h.w64(ures + 0x80, tab80)
    q = h.alloc(0x40)
    qq = h.alloc(0x40)
    if sc.get("res_param", True):
        h.w64(q + 0x10, qq)
        h.w32(qq + 0x18, 0)
        h.w64(qq + 0x20, ures)
    h.q_ret = q
    handles = []
    for i, t in enumerate(sc["trig"]):
        a = trig + 0x28 * i
        h.w64(a + 8, ctb_base + 0x30 * i)
        h.w32(a + 0x10, t["start"])
        h.w32(a + 0x18, t["end"])
        h.w16(a + 0x1C, t["flag"])
        h.w64(a + 0x20, 0x1000 + i)
        h.w8(tab80 + 8 * i + 2, 2 if t.get("bit1") else 0)
        s = states + 0x28 * i
        if t.get("live"):
            hd = h.alloc(0x40)
            h.w32(hd + 0x20, 77)
            h.w64(s + 0x10, hd)
            h.w32(s + 0x18, 77)
            handles.append(hd)
        else:
            handles.append(0)
        h.w8(s + 0x24, 1 if t.get("fired") else 0)
        h.w8(s + 0x26, 1 if t.get("s26") else 0)
    h.w32(state_hdr, n)
    h.w64(state_hdr + 8, states)
    h.w64(ctrl + 0x10, state_hdr)
    h.w16(act + 8, 0)
    h.w32(act + 0xC, n - 1)
    h.w64(ctrl + 0x30, act)
    h.w32(ctrl + 0x24, sc["cur"])
    h.w32(ctrl + 0x28, sc["prev"])
    mu = h.mu
    mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
    mu.reg_write(UC_ARM64_REG_X0, ctrl)
    mu.reg_write(UC_ARM64_REG_X30, END)
    mu.emu_start(FN, END, count=200000)
    out = {"emits": [e["idx"] for e in h.emits], "emit_args_ok": all(e["x1"] == 0 and e["x3"] == 0x1000 + e["idx"] and e["x4"] == ctb_base + 0x30 * e["idx"] for e in h.emits),
           "prev_after": h.r32(ctrl + 0x28), "killed": [], "handle_cleared": [], "fired": []}
    for i, hd in enumerate(handles):
        s = states + 0x28 * i
        out["killed"].append(bool(hd) and (h.r32(hd + 8) & 0x90) == 0x90)
        out["handle_cleared"].append(bool(hd) and h.r64(s + 0x10) == 0)
        out["fired"].append(h.r8(s + 0x24))
    return out


def ref(sc):
    cur, prev = sc["cur"], sc["prev"]
    regress = cur < prev
    if regress:
        prev = -1
    emits, killed, cleared, fired = [], [], [], []
    for i, t in enumerate(sc["trig"]):
        f = t["flag"]
        kind = 1 if f & 4 else 2 if f & 8 else 3 if f & 0x10 else 0
        loop = bool(t.get("bit1")) and sc.get("res_param", True)
        live = bool(t.get("live"))
        fi = 1 if t.get("fired") else 0
        k = False
        if not (kind != 0 and not loop) and not (kind == 3 and not t.get("s26")):
            st = 0 if kind == 3 else t["start"]
            if regress and not (f & 1) and fi and live:
                k = True
                live = False
            if not loop:
                if prev < st <= cur < t["end"]:
                    if not ((f & 1) and fi):
                        emits.append(i)
                        fi = 1
            else:
                if st <= cur < t["end"] and not live:
                    if not ((f & 1) and fi):
                        emits.append(i)
                        fi = 1
            if prev < t["end"] <= cur and live:
                k = True
                live = False
        killed.append(k)
        cleared.append(k)
        fired.append(fi)
    return {"emits": emits, "emit_args_ok": True, "prev_after": cur, "killed": killed, "handle_cleared": cleared, "fired": fired}


DMG = {"start": 0, "end": 0x7FFFFFFF, "flag": 0}
SC = []
for prev in (5, 10, 30, 31):
    for bit1 in (0, 1):
        for live in (0, 1):
            SC.append({"name": f"재피격 prev={prev} bit1={bit1} live={live}", "cur": 0, "prev": prev,
                       "trig": [dict(DMG, bit1=bit1, live=live, fired=1)]})
for bit1 in (0, 1):
    SC.append({"name": f"첫 재생 prev=-1 bit1={bit1}", "cur": 0, "prev": -1, "trig": [dict(DMG, bit1=bit1, fired=0)]})
    SC.append({"name": f"같은 프레임 0→0 bit1={bit1}", "cur": 0, "prev": 0, "trig": [dict(DMG, bit1=bit1, fired=1, live=1)]})
    SC.append({"name": f"진행 5→6 bit1={bit1}", "cur": 6, "prev": 5, "trig": [dict(DMG, bit1=bit1, fired=1, live=1)]})
    SC.append({"name": f"진행 5→6 이벤트 끝남 bit1={bit1}", "cur": 6, "prev": 5, "trig": [dict(DMG, bit1=bit1, fired=1, live=0)]})
SC.append({"name": "bit0 넘겨받기형 재피격", "cur": 0, "prev": 10, "trig": [dict(DMG, flag=1, fired=1, live=1)]})
SC.append({"name": "리소스 접근자 +0x10 없음 재피격", "cur": 0, "prev": 10, "res_param": False, "trig": [dict(DMG, fired=1, live=1)]})
SC.append({"name": "구간 트리거 3..8, 10→4", "cur": 4, "prev": 10, "trig": [{"start": 3, "end": 8, "flag": 0, "fired": 1, "live": 1}]})
SC.append({"name": "구간 트리거 3..8, 2→9(끝 지남)", "cur": 9, "prev": 2, "trig": [{"start": 3, "end": 8, "flag": 0, "fired": 0, "live": 1}]})

res = []
ok = 0
for sc in SC:
    o = run(sc)
    r = ref(sc)
    same = o == r
    ok += same
    res.append({"scenario": sc["name"], "original": o, "reimpl": r, "match": same})
    print(("OK " if same else "NG ") + sc["name"], o["emits"], o["killed"], o["fired"], o["prev_after"])
print(f"{ok}/{len(SC)} 일치")
OUT.parent.mkdir(parents=True, exist_ok=True)
json.dump({"function": hex(FN), "stubs": ["0x7103899c68 방출(ret, 인자 기록)", "리소스 접근자 vt+0x10(합성 객체 반환)", "이벤트 정리 전역 호출 경로 미실행(핸들 +0x28=0)"],
           "match": f"{ok}/{len(SC)}", "results": res}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
