"""[netrest] 네트워크 잔여 항목을 원본 함수 unicorn 실행으로 확인한다.

network_uc.UC 하네스를 쓰고, PLT(외부 함수)는 코드 훅으로 즉시 반환한다
(가드 획득 0x7103e99ef0 만 1 반환, 나머지 0). 결과는 analysis/network/netrest_result.json.

검사:
 1. Rule 문자열 → 정수(0x71010c8e3c, 표 생성 0x71010c8be8)            [실행]
 2. PlayerNetState +0x188(SuperHook) 작성 0x71026a8938/0x71026a8968   [실행]
 3. 넷관리자+0x60 객체 vt+0x20 시계 getter 0x71034e56c0               [실행]
 4. pia ClockProtocol GetClock 0x710076ebf8                           [실행]
 5. 로비 → 대전 설정 복사 0x7102d60098 (0x7102d601a8 직전까지)         [실행]
 6. 리액션 카운터/종류 0x7102469fac (본체+0xcfc 구조체)                 [실행]
"""
import json
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_PC, UC_ARM64_REG_LR, UC_ARM64_REG_SP, \
    UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X29

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC, STACK, END  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PLT_LO, PLT_HI = 0x7103E99000, 0x7103E9E000
PLT_RET = {0x7103E99EF0: 1}


class UC2(UC):
    def __init__(self):
        super().__init__()
        self.mu.hook_add(UC_HOOK_CODE, self._plt, begin=PLT_LO, end=PLT_HI)

    def _plt(self, mu, addr, size, ud):
        mu.reg_write(UC_ARM64_REG_X0, PLT_RET.get(addr, 0))
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    def run_until(self, fn, until, *args):
        mu = self.mu
        regs = [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2]
        for r, v in zip(regs, args):
            mu.reg_write(r, v)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        mu.reg_write(UC_ARM64_REG_X29, 0)
        mu.reg_write(UC_ARM64_REG_LR, END)
        mu.emu_start(fn, until, count=2_000_000)

    def q(self, a, v=None):
        if v is None:
            return struct.unpack("<Q", self.mu.mem_read(a, 8))[0]
        self.mu.mem_write(a, struct.pack("<Q", v & (2 ** 64 - 1)))

    def b(self, a, v=None):
        if v is None:
            return self.mu.mem_read(a, 1)[0]
        self.mu.mem_write(a, bytes([v & 0xFF]))


def t_rule(res):
    u = UC2()
    names = ["Pnt", "Var", "Vlf", "Vgl", "Vcl", "Tcl", "Xxx"]
    out = {}
    for n in names:
        s = u.alloc(16)
        u.mu.mem_write(s, n.encode() + b"\0")
        p = u.alloc(8)
        u.q(p, s)
        dst = u.alloc(8)
        u.u32(dst, 0xDEADBEEF)
        u.call(0x71010C8E3C, dst, p)
        out[n] = u.ru32(dst)
    res["rule_enum"] = out
    ok = all(out[n] == i for i, n in enumerate(names[:6]))
    print("[1] Rule 문자열→값", out, "OK" if ok else "FAIL")
    return ok


def t_superhook(res):
    u = UC2()
    rows = []
    for f52 in (0, 1):
        for f53 in (0, 1):
            this = u.alloc(0x4000)
            u.b(this + 0x3952, f52)
            u.b(this + 0x3953, f53)
            st = u.alloc(0x200)
            u.b(st + 0x188, 0xAA)
            u.call(0x71026A8938, this, st)
            a = u.b(st + 0x188)
            u.b(st + 0x188, 0xAA)
            u.call(0x71026A8968, this + 0x30, st)
            b = u.b(st + 0x188)
            rows.append({"0x3952": f52, "0x3953": f53, "primary": a, "secondary(this+0x30)": b})
    res["superhook_188"] = rows
    ok = all(r["primary"] == r["secondary(this+0x30)"] == int(bool(r["0x3952"] or r["0x3953"])) for r in rows)
    print("[2] SuperHook +0x188 =", [(r["0x3952"], r["0x3953"], r["primary"]) for r in rows], "OK" if ok else "FAIL")
    return ok


def t_clock_getter(res):
    u = UC2()
    rows = []
    for count, idx, val in ((2, 0, 123456), (2, 1, 777), (2, 5, 999), (1, 0, 2 ** 64 - 1)):
        this = u.alloc(0x40)
        arr = u.alloc(0x1A8 * 4)
        u.u32(this + 0x30, count)
        u.q(this + 0x38, arr)
        for i in range(4):
            u.q(arr + i * 0x1A8 + 0x150, 1000 + i)
        tgt = idx if idx < count else 0
        u.q(arr + tgt * 0x1A8 + 0x150, val)
        out = u.alloc(8)
        u.q(out, 0x5555)
        r = u.call(0x71034E56C0, this, out, idx) & 0xFF
        rows.append({"count": count, "idx": idx, "val": val, "ret": r, "out": u.q(out)})
    res["clock_getter"] = rows
    ok = (rows[0]["ret"] == 1 and rows[0]["out"] == 123456 and rows[1]["out"] == 777
          and rows[2]["out"] == 999 and rows[3]["ret"] == 0 and rows[3]["out"] == 0x5555)
    print("[3] 시계 getter", [(r["count"], r["idx"], r["ret"], r["out"]) for r in rows], "OK" if ok else "FAIL")
    return ok


def t_pia_getclock(res):
    u = UC2()
    rows = []
    for state, v68, v78, v70 in ((2, 0, 1, 5_000_000), (4, 0, 1, 5_000_000), (2, 2 ** 64 - 1, 1, 7), (2, 0, 0, 9)):
        proto = u.alloc(0x80)
        u.b(proto + 0x5A, state)
        u.q(proto + 0x68, v68)
        u.b(proto + 0x78, v78)
        u.q(proto + 0x70, v70)
        out = u.alloc(8)
        u.q(out, 0x1111)
        resv = u.alloc(0x10)
        u.mu.reg_write(UC_ARM64_REG_X29, 0)
        # x8 = 결과 버퍼(간접 반환)
        from unicorn.arm64_const import UC_ARM64_REG_X8
        u.mu.reg_write(UC_ARM64_REG_X8, resv)
        u.call(0x710076EBF8, proto, out)
        rows.append({"state5a": state, "+0x68": v68, "+0x78": v78, "+0x70": v70, "out": u.q(out)})
    res["pia_getclock"] = rows
    ok = rows[0]["out"] == 5_000_000 and rows[1]["out"] == 2 ** 64 - 1 and rows[2]["out"] == 2 ** 64 - 1
    print("[4] pia GetClock", [(r["state5a"], r["out"]) for r in rows], "OK" if ok else "FAIL")
    return ok


def t_versus_copy(res):
    u = UC2()
    obj = u.alloc(0xB00)
    u.f32(obj + 0xA44, 0.0)
    u.b(obj + 0x630, 1)
    u.u32(obj + 0x84, 0x11)
    u.u32(obj + 0x460, 3)       # OVS +0x80
    u.u32(obj + 0x464, 5)       # OVS +0x84 (Rule)
    u.u32(obj + 0x468, 300)     # OVS +0x88 (Time)
    seeds = [0x12345678, 0x9ABCDEF0, 0x0BADF00D, 0xCAFEBABE]
    for i, s in enumerate(seeds):
        u.u32(obj + 0x618 + 4 * i, s)
    u.mu.mem_write(obj + 0x628, struct.pack("<HH", 0x2222, 0x3333))
    u.b(obj + 0xA0, 1)
    gamenet = u.alloc(0x300)
    u.u32(gamenet + 0x1C8, 0x77)
    u.q(0x7105825FD0, gamenet)
    holder = u.alloc(0x200)
    gs = u.alloc(0x6570)
    vs = u.alloc(0xC0)
    u.q(holder + 0xD0, gs)
    u.q(gs + 0x6548, vs)
    u.q(0x71058E42F8, holder)
    u.run_until(0x7102D60098, 0x7102D601A8, obj)
    got = {
        "+0x38": u.ru32(vs + 0x38), "+0x3c(Rule)": u.ru32(vs + 0x3C), "+0x40": u.ru32(vs + 0x40),
        "+0xa0(Time)": u.ru32(vs + 0xA0),
        "+0xa4..b0(RandomSeed0..3)": [hex(u.ru32(vs + 0xA4 + 4 * i)) for i in range(4)],
        "+0xb4": hex(struct.unpack("<H", u.mu.mem_read(vs + 0xB4, 2))[0]),
        "+0xb6": hex(struct.unpack("<H", u.mu.mem_read(vs + 0xB6, 2))[0]),
        "+0xba": u.b(vs + 0xBA), "gs+0x6508": hex(u.ru32(gs + 0x6508)),
    }
    res["versus_copy"] = got
    ok = (got["+0x3c(Rule)"] == 5 and got["+0xa0(Time)"] == 300 and got["+0x38"] == 3 and got["+0x40"] == 0x11
          and got["+0xa4..b0(RandomSeed0..3)"] == [hex(s) for s in seeds] and got["+0xb6"] == "0x2222"
          and got["+0xb4"] == "0x3333" and got["gs+0x6508"] == "0x77")
    print("[5] 로비→대전설정 복사", got, "OK" if ok else "FAIL")
    return ok


def t_reaction(res):
    u = UC2()
    kinds = {}
    for st in range(0, 0x120):
        s = u.alloc(0x20)
        u.u32(s + 8, 7)
        u.u32(s + 0x10, 0xEE)
        u.call(0x7102469FAC, s, st)
        k = u.ru32(s + 0x10)
        if u.ru32(s + 8) != 0:
            kinds["counter_fail"] = st
        if k not in (0xEE, 0):
            kinds[hex(st)] = k
    res["reaction_kind_by_state"] = kinds
    print("[6] 리액션 카운터 7→0, 종류(상태→값, 0 아닌 것만)", kinds)
    return "counter_fail" not in kinds


def main():
    res = {}
    oks = [t_rule(res), t_superhook(res), t_clock_getter(res), t_pia_getclock(res), t_versus_copy(res), t_reaction(res)]
    out = ROOT / "analysis" / "network" / "netrest_result.json"
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print("통과", sum(oks), "/", len(oks), "→", out)


if __name__ == "__main__":
    main()
