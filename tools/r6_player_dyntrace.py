"""r6 player: 동적 추적 — 플레이어 본체(0xac80 B) 필드에 쓰는 명령 PC 전수 기록.

원본 생성자·init·슬롯9·슬롯15(시작 배치, 1회) → 프레임마다 PlayerBehavior 슬롯 16, 18(메인 계산), 19(후처리)를 unicorn으로 실행한다
(r6_player_world.World). 시나리오별로 패드 입력·상태 번호·접지 여부를 바꿔 여러 경로를 태운다.
UC_HOOK_MEM_WRITE 로 본체 전 구간 쓰기를 잡아 (오프셋 → PC별 횟수·값 표본)을 모은다.

결과: analysis/r6_player/dyntrace.json  (오프셋 16진 → {pc: {"n": 횟수, "vals": [표본], "nz": 0 아닌 값 횟수}})
사용: PY web/tools/r6_player_dyntrace.py [--frames N]
스텁 범위는 World 문서 문자열과 결과의 "stubs" 항목에 기록.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r6_player_world import World  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "r6_player" / "dyntrace.json"


def scenarios(frames):
    """(이름, 상태 번호, 접촉 설정 dict 또는 None, 프레임별 (hold, trig, stick) 목록). 패드 비트는 sead 패드 비트(0 A, 1 B, 2 ZL, 5 ZR, 13 L, 14 R ...)"""
    G = dict(ground=True)
    A = dict(ground=False)
    WALL = dict(ground=True, normal=(0.0, 0.0, 1.0))
    SIDE_AIR = dict(ground=False, side=True, side_normal=(0.0, 0.0, 1.0), side_point=(0.0, 0.0, 0.0))
    out = []
    hold = lambda m, st=(0.0, 1.0), n=frames: [(m, m if i == 0 else 0, st) for i in range(n)]
    out.append(("idle_air", 0x56, A, [(0, 0, (0.0, 0.0))] * frames))
    out.append(("idle_ground", 0x56, G, [(0, 0, (0.0, 0.0))] * frames))
    out.append(("walk_ground", 0x87, G, [(0, 0, (0.0, 1.0))] * frames))
    for bit in range(0, 20):
        m = 1 << bit
        seq = hold(m, n=frames // 2) + [(0, 0, (0.0, 0.8))] * (frames // 2)
        out.append((f"bit{bit}_ground", 0x56, G, seq))
    out.append(("squid_hold_ground", 0x85, G, hold(4)))
    out.append(("squid_then_shoot", 0x85, G, hold(4, n=frames // 2) + [(4 | 32, 32 if i == 0 else 0, (0.0, 1.0)) for i in range(frames // 2)]))
    out.append(("squid_wall", 0x87, WALL, hold(4)))
    out.append(("squid_wall_jumpcharge", 0x87, WALL, hold(4, n=frames // 3) + hold(4 | 2, n=frames // 3) + hold(4, n=frames // 3)))
    out.append(("squid_jump_ground", 0x87, G, [(4 | (2 if (i % 10) < 4 else 0), (2 if (i % 10) == 0 else 0), (0.0, 1.0)) for i in range(frames)]))
    out.append(("human_jump_ground", 0x56, G, [((2 if (i % 10) < 4 else 0), (2 if (i % 10) == 0 else 0), (0.0, 1.0)) for i in range(frames)]))
    out.append(("side_air", 0x56, SIDE_AIR, [(0, 0, (0.0, 1.0))] * frames))
    out.append(("squid_roll_ground", 0x87, G, [(4 | (2 if i == 12 else 0), (2 if i == 12 else 0), (0.0, 1.0) if i < 10 else (0.0, -1.0)) for i in range(frames)]))
    # 아군 잉크(발밑 분류 0) + 벽 낙하 레이 적중 대체
    OWN = dict(paint=0, ray=True)
    ENEMY = dict(paint=2, ray=True)
    out.append(("own_squid_ground", 0x85, dict(G, **OWN), hold(4)))
    out.append(("own_squid_toggle", 0x85, dict(G, **OWN), [((4 if (i // 25) % 2 == 0 else 0), (4 if i % 25 == 0 and (i // 25) % 2 == 0 else 0), (0.0, 1.0)) for i in range(frames * 2)]))
    out.append(("own_squid_wall_charge_up", 0x85, dict(WALL, **OWN), [(4 | (2 if 10 <= i < 40 else 0), (4 if i == 0 else 0) | (2 if i == 10 else 0), (0.0, 0.5) if i < 38 else (0.0, -1.0)) for i in range(frames * 2)]))
    out.append(("own_squid_wall_charge_out", 0x85, dict(WALL, **OWN), [(4 | (2 if 10 <= i < 40 else 0), (4 if i == 0 else 0) | (2 if i == 10 else 0), (0.0, 0.5) if i < 38 else (0.0, 1.0)) for i in range(frames * 2)]))
    out.append(("own_squid_wall_kick", 0x85, dict(WALL, **OWN), [(4 | (2 if i in (15, 16) else 0), (4 if i == 0 else 0) | (2 if i == 15 else 0), (0.0, 0.5) if i < 14 else (0.0, -1.0)) for i in range(frames)]))
    out.append(("enemy_squid", 0x85, dict(G, **ENEMY), hold(4)))
    out.append(("enemy_human", 0x56, dict(G, **ENEMY), [(0, 0, (0.0, 1.0))] * frames))
    out.append(("own_squid_air_side", 0x85, dict(SIDE_AIR, **OWN), hold(4)))
    out.append(("human_shoot_hold", 0x56, G, hold(32)))
    out.append(("human_sub_hold", 0x56, G, hold(1 << 14)))
    return out


def run(frames=40, ground_modes=(False,)):
    agg = {}
    meta = []
    for name, state, contact, seq in scenarios(frames):
        w = World(state=state)
        if contact:
            c = dict(contact)
            pk = c.pop("paint", None)
            ray = c.pop("ray", None)
            w.set_contact(**c)
            if pk is not None:
                w.set_paint(kind=pk, own=1.0 if pk < 2 else 0.0, enemy=1.0 if pk in (2, 3) else 0.0)
            if ray is not None:
                w.set_ray(ray)
        u = w.u
        w.watch_body()
        st = w.start()
        res = []
        for i, (hold, trig, stick) in enumerate(seq):
            w.set_pad(hold=hold, trig=trig, stick=stick)
            r = w.step(slots=(16, 18, 19))
            if any(v is not None for v in r.values()):
                res.append((i, {k: v for k, v in r.items() if v is not None}))
        for tag, _, off, size, val, pc in u.writes:
            d = agg.setdefault(off, {})
            e = d.setdefault(pc, {"n": 0, "nz": 0, "vals": [], "size": size, "sc": []})
            e["n"] += 1
            if val:
                e["nz"] += 1
            if len(e["vals"]) < 6 and val not in e["vals"]:
                e["vals"].append(val)
            if name not in e["sc"] and len(e["sc"]) < 8:
                e["sc"].append(name)
        meta.append(dict(scenario=name, state=hex(state), frames=len(seq), errors=res[:3], start=st,
                         plt_stubbed=u.plt_stubbed, libm=u.libm_used, null_calls=len(u.null_calls),
                         null_writes=sum(u.null_writes.values()), auto_pages=len(u.auto_pages),
                         forced_state0=[hex(x) for x in w.forced_state0], fakes=len(w.fakes)))
        print(name, "errors", len(res), res[:1], "writes", len(u.writes), flush=True)
    return agg, meta


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=40)
    a = ap.parse_args()
    agg, meta = run(a.frames)
    out = {"stubs": "web/tools/r6_player_world.py 문서 참고: 가짜 액터·SM·컨트롤러·Phive 엔진 객체·조작 싱글턴, 컴포넌트 상태 -1→0, "
                    "널 가상 호출 0 반환, PLT 스텁, libm 파이썬 근사",
           "meta": meta,
           "writes": {f"{off:#x}": {f"{pc:#x}": v for pc, v in sorted(d.items())} for off, d in sorted(agg.items())}}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print("saved", OUT, "offsets", len(agg))


if __name__ == "__main__":
    main()
