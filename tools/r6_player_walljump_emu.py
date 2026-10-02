"""r6 player: 벽 점프 차지 해제 → 0x7102458a18(벽 위 수직 점프) 원본 연결 실행 검증.

r6_player_world.World(원본 생성자·init·프레임 슬롯 16/18/19)에서 오징어(0x85)가 아군 잉크 벽(N = (0,0,1))에 붙어
ZL(sead bit2)을 누른 채 B(bit1)를 k 프레임 누르고 뗀다(스틱 (0,-1) = 벽 바깥 아님 → 0x71024593e8 거짓 → 0x7102458a18).
해제 프레임의 본체+0x754(3D 점프 y)·+0x780·+0x782·+0x781·+0x748·+0xd00 과 재구현식을 비교한다.
재구현: x = (+0x774) − 10, F = PlayerParam+0x13c(WallJumpChargeFrm), s = clamp01(x / F) (C[0x71058bc128] = 0 이므로),
        y = 0.02 + (0.25 − 0.02)·s (f32), +0x754 = max(+0x754, y), s ≥ 0.2 이면 +0x780 = +0x782 = 1.
스텁: World 문서(가짜 Phive 접촉 = 벽 접지 대체, 발밑 잉크 = 아군 대체, 벽 낙하 레이 = 적중 대체 등).
결과: analysis/r6_player/walljump_emu.json
"""
import json, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r6_player_world import World  # noqa: E402
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0

ROOT = Path(__file__).resolve().parents[2]
F32 = np.float32


def run(hold_frames, F=45.0):
    w = World(state=0x85)
    u, b = w.u, w.body
    w.start()
    w.set_contact(ground=True, normal=(0.0, 0.0, 1.0))
    w.set_paint(kind=0)
    w.set_ray(True)
    u.track_funcs([0x7102458A18, 0x7102459630])
    at_call = {}

    def on_call(mu, addr, size, ud):
        x0 = mu.reg_read(UC_ARM64_REG_X0)
        at_call.update(x0=x0, y754=u.r32(x0 + 4), c774=u.rs32(x0 + 0x24))
    u.mu.hook_add(UC_HOOK_CODE, on_call, begin=0x7102458A18, end=0x7102458A18)
    pp = u.rq(b + 0xA658)
    u.wf(pp + 0x13C, F)  # PlayerParam+0x13c(WallJumpChargeFrm) — 기어 계산을 실행하지 않았으므로 값 지정(0AP 데이터 45 등) ← 설정
    rel = 10 + hold_frames
    rec = None
    for i in range(rel + 3):
        hold = 4 | (2 if 10 <= i < rel else 0)
        trig = (4 if i == 0 else 0) | (2 if i == 10 else 0)
        w.set_pad(hold=hold, trig=trig, stick=(0.0, -1.0) if i >= rel - 2 else (0.0, 0.5))
        if i == rel:
            before = dict(c774=u.rs32(b + 0x774), y754=u.r32(b + 0x754), d00=u.r32(b + 0xD00))
        w.step(slots=(16, 18, 19))
        if i == rel:
            rec = dict(hold_frames=hold_frames, before=before, F=u.rf(pp + 0x13C),
                       at_call=dict(at_call), x0_is_B750=(at_call.get("x0") == b + 0x750), y754=u.r32(b + 0x754), b780=u.r8(b + 0x780), b781=u.r8(b + 0x781), b782=u.r8(b + 0x782),
                       y748=u.r32(b + 0x748), d00=u.r32(b + 0xD00), calls=dict((hex(k), v) for k, v in u.entries.items()))
    return rec


def expect(rec):
    if not rec["at_call"]:
        return dict(called=False)
    F = F32(rec["F"])
    x = F32(rec["at_call"]["c774"] - 10)
    s1 = F32(0.0)  # C[0x71058bc128] = 0
    if F >= s1:
        if x <= s1:
            s = F32(0)
        elif F <= x:
            s = F32(1)
        elif F32(F - s1) == 0:
            s = F32(0)
        else:
            s = F32(F32(x - s1) / F32(F - s1))
    y = F32(F32(0.02) + F32(s * F32(F32(0.25) - F32(0.02))))
    prev = np.frombuffer(struct.pack("<I", rec["at_call"]["y754"]), F32)[0]
    y754 = max(prev, y)
    latch = 1 if s >= F32(0.2) else 0
    return dict(s=float(s), y=float(y), y754_bits=struct.unpack("<I", struct.pack("<f", float(y754)))[0], latch=latch)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = []
    mis = 0
    for F in (45.0, 30.0, 18.0, 5.0):
      for k in list(range(9, 14)) + list(range(14, 70, 3)):
        r = run(k, F)
        e = expect(r)
        if e.get("called") is False:
            ok = r["before"]["c774"] < 10 and r["b780"] == 0
        else:
            ok = (r["y754"] == e["y754_bits"]) and r["b780"] == e["latch"] and r["b782"] == e["latch"] and r["x0_is_B750"]
        mis += not ok
        r["expect"] = e
        r["ok"] = ok
        rows.append(r)
        if not ok or k % 9 == 0: print(F, k, r["before"]["c774"], "F", r["F"], "y754", hex(r["y754"]), e, "780", r["b780"], r["b782"], "ok", ok, r["calls"])
    out = dict(cases=len(rows), mismatches=mis, rows=rows)
    (ROOT / "analysis/r6_player/walljump_emu.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("cases", len(rows), "mismatch", mis)


if __name__ == "__main__":
    main()
