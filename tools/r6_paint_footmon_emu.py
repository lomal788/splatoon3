"""r6 paint: 플레이어 발밑 잉크 샘플 사슬의 원본 함수 실행 대조.

사슬(판독, paint_and_score.md §7):
  PlayerStepPaint 0x710268b3b8: O = *(*(*(*(S+0xe8)+8)+0x20)+0xe8), O+0x48 델리게이트 slot0 호출
  S+0xe8 writer = 바인드 0x71024319f0 (0x7102431e00): 액터 컴포넌트[10]+0x18 → +0x10 = 컨트롤러 래퍼 W
  W+8 = ctrl, ctrl+0x20 = 상태 S', S'+0xe8 = 접지 정보 O
  O+8 / O+0x48 / O+0x50 writer = SplResultPlayer 슬롯7 0x7102c5a3c8 (0x7102c5d5dc, 0x7102c5da58)
  델리게이트 vtable 0x7105681b90 slot0 = 0x7102c5ec74 → SplResultPlayer 모니터 슬롯 4개 가중 합
실행 대상(원본 그대로):
  A) 0x7102c5ec74 델리게이트(+ 0x7102c71bc4, 모니터 vt+0x60 0x7102c260c8 / vt+0x78 0x7102c26258) — 무작위 상태 N건
  B) 0x7102c71330(dt, 모니터 배열) 가중치 갱신 — 무작위 상태 N건
스텁: PLT 없음. B 에서 해제 알림 0x7100f3e094(메시지 방송)만 즉시 반환(호출 횟수만 셈), 그 인자용 전역 *0x71058150c0 은 빈 객체.
재구현: 아래 ref_delegate / ref_weight (f32, numpy).
결과: analysis/paint/r6_footmon_emu_out.json
"""
import json, random, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r6_paint_uc import UC
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X8, UC_ARM64_REG_PC, UC_ARM64_REG_LR

ROOT = Path(__file__).resolve().parents[2]
F = np.float32
MON_VT = 0x710567e9c8
DLG_VT = 0x7105681b90
N = 4000


def f2u(x): return struct.unpack("<I", struct.pack("<f", float(x)))[0]
def fcvtzu(x):
    x = float(x)
    if x != x or x <= 0: return 0
    return min(int(x), 0xFFFFFFFF)


def ref_monitor_read(mon, ent_cache, out_prev):
    """0x7102c71bc4(항목, out): 모니터 vt+0x60(0x7102c260c8: +0x40,+0x48,+0x58 유효 바이트 모두 참 — +0x50 은 안 봄)이면
    out 의 직전 값 위에 유효 바이트가 참인 칸만 vt+0x78(i) 값으로 덮고 항목 캐시(+8..+0x14)에 복사, 아니면 항목 캐시를 out 에 복사."""
    if mon["v"][0] and mon["v"][1] and mon["v"][3]:
        c = list(out_prev)
        for i in range(4):
            if mon["v"][i]: c[i] = mon["c"][i]
        return c
    return list(ent_cache)


def ref_delegate(R):
    out = [0, 0, 0, 0]; wmax = F(0); first = True
    res_slots = []
    for k in range(4):
        if not R["valid"][k]:
            res_slots.append(None); continue
        ent = next((e for e in R["ents"] if e["valid"] and e["id"] == R["id"][k]), None)
        if ent is None:
            R["valid"][k] = 0; R["cache"][k] = [0, 0, 0, 0, F(0)]; res_slots.append("miss"); continue
        c = ref_monitor_read(ent["mon"], ent["cache"], R["cache"][k][:4])
        ent["cache"] = c
        w = F(ent["w"])
        R["cache"][k] = c + [w]
        if not (w > 0):
            R["valid"][k] = 0; res_slots.append("w0"); continue
        if first:
            wmax = F(max(w, F(0))); first = False
        else:
            wmax = wmax if wmax > w else w
        out = [fcvtzu(F(F(w * F(c[i])) + F(out[i]))) for i in range(4)]
        res_slots.append("ok")
    return out, wmax


def ref_weight(A, dt):
    rate = F(A["rate"]); rel = 0
    for e in A["ents"]:
        if e["act"]:
            e["cnt"] = (e["cnt"] + 1) & 0xFFFFFFFF
            if struct.unpack("<i", struct.pack("<I", e["cnt"]))[0] >= A["frames"]:
                e["w"] = F(1.0); e["act"] = 0
            continue
        if rate == 0:
            e["w"] = F(0)
        else:
            v = F(F(e["w"]) - F(F(dt) / rate))
            v = F(0) if not (v > 0) else v
            e["w"] = v
            if v > 0: continue
        e["act"] = 0
        if e["reg"]:
            e["w"] = F(0)
            if e["mon_has"]: rel += 1
            e["reg"] = 0
    return rel


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rnd = random.Random(20261003)
    rel_calls = []

    def hook(u, name, x):
        return False
    u = UC(hook_fn=hook)
    mu = u.mu
    def on_msg(mu_, addr, size, ud):
        rel_calls.append(1)
        mu_.reg_write(UC_ARM64_REG_PC, mu_.reg_read(UC_ARM64_REG_LR))
    mu.hook_add(UC_HOOK_CODE, on_msg, begin=0x7100f3e094, end=0x7100f3e094)

    # 고정 배치 (해제 알림 경로가 읽는 전역 *0x71058150c0 +0xe0 에 빈 객체를 둠 — 알림 함수 자체는 스텁)
    G = u.alloc(0x100); u.w64(0x71058150c0, G); u.w64(G + 0xe0, u.alloc(0x100))
    R = u.alloc(0x1800); A = u.alloc(0x28); ENT = u.alloc(0x50 * 8); D = u.alloc(0x60); OUT = u.alloc(0x20)
    MONS = [u.alloc(0x180) for _ in range(8)]
    ok_a = ok_b = 0; fails = []
    for t in range(N):
        n = rnd.randint(0, 6)
        ents = []
        for j in range(n):
            mon = dict(c=[rnd.choice([0, rnd.randint(0, 3000), rnd.randint(0, 0xFFFFFFFF)]) for _ in range(4)],
                       v=[rnd.random() < 0.85 for _ in range(4)])
            ents.append(dict(mon=mon, cache=[rnd.randint(0, 5000) for _ in range(4)],
                             w=F(rnd.choice([0.0, 1.0, rnd.random(), -rnd.random(), rnd.uniform(0, 1.5)])),
                             id=rnd.randint(1, 6), valid=rnd.random() < 0.8, act=rnd.random() < 0.4,
                             cnt=rnd.randint(-1, 3) & 0xFFFFFFFF, reg=rnd.random() < 0.7, mon_has=rnd.random() < 0.5))
        Rm = dict(valid=[rnd.random() < 0.8 for _ in range(4)], id=[rnd.randint(1, 6) for _ in range(4)],
                  cache=[[rnd.randint(0, 4000) for _ in range(4)] + [F(0)] for _ in range(4)], ents=ents)
        # 메모리 쓰기
        mu.mem_write(R, b"\0" * 0x1800); mu.mem_write(ENT, b"\0" * 0x50 * 8)
        u.w64(R + 0x1368, A)
        u.w32(A, n); u.w64(A + 8, ENT); u.w32(A + 0x10, 0x10)
        rate = F(rnd.choice([1 / 6, 0.0, rnd.uniform(0.05, 1.0)])); u.w32(A + 0x14, f2u(rate))
        frames = rnd.randint(1, 3); u.w32(A + 0x18, frames); u.w32(A + 0x1c, 0); mu.mem_write(A + 0x20, b"\1")
        for j, e in enumerate(ents):
            m = MONS[j]; mu.mem_write(m, b"\0" * 0x180); u.w64(m, MON_VT)
            for i in range(4):
                u.w32(m + 0x3c + 8 * i, e["mon"]["c"][i]); mu.mem_write(m + 0x40 + 8 * i, bytes([int(e["mon"]["v"][i])]))
            if e["mon_has"]: u.w64(m + 8, 1)
            b = ENT + 0x50 * j
            u.w64(b, m)
            for i in range(4): u.w32(b + 8 + 4 * i, e["cache"][i])
            mu.mem_write(b + 0x38, bytes([int(e["act"])])); u.w32(b + 0x3c, e["cnt"]); u.w32(b + 0x40, f2u(e["w"]))
            u.w32(b + 0x44, e["id"]); mu.mem_write(b + 0x48, bytes([int(e["valid"])])); mu.mem_write(b + 0x4c, bytes([int(e["reg"])]))
        for k in range(4):
            for i in range(4): u.w32(R + 0x1370 + 0x14 * k + 4 * i, Rm["cache"][k][i])
            u.w32(R + 0x13c0 + 8 * k, Rm["id"][k]); mu.mem_write(R + 0x13c4 + 8 * k, bytes([int(Rm["valid"][k])]))
        u.w64(D + 0x48, DLG_VT); u.w64(D + 0x50, R)
        # A) 델리게이트: x0 = O+0x48, x8 = out
        mu.reg_write(UC_ARM64_REG_X8, OUT)
        u.call(0x7102c5ec74, D + 0x48)
        got = [u.u32(OUT + 4 * i) for i in range(4)] + [u.u32(OUT + 0x10)]
        exp_o, exp_w = ref_delegate(Rm)
        exp = exp_o + [f2u(exp_w)]
        got_valid = [bytes(mu.mem_read(R + 0x13c4 + 8 * k, 1))[0] for k in range(4)]
        good = got == exp and got_valid == [int(v) for v in Rm["valid"]]
        ok_a += good
        if not good and len(fails) < 10: fails.append(dict(t=t, part="A", got=got, exp=exp, gv=got_valid, ev=Rm["valid"]))
        # B) 가중치 갱신 0x7102c71330(dt=1/60)
        before = len(rel_calls)
        u.call(0x7102c71330, A, fargs=(float(F(0.016666668)),))
        A_ref = dict(rate=rate, frames=frames, ents=ents)
        rel = ref_weight(A_ref, F(0.016666668))
        gb = []; eb = []
        for j, e in enumerate(ents):
            b = ENT + 0x50 * j
            gb.append((bytes(mu.mem_read(b + 0x38, 1))[0], u.u32(b + 0x3c), u.u32(b + 0x40), bytes(mu.mem_read(b + 0x4c, 1))[0]))
            eb.append((int(e["act"]), e["cnt"], f2u(e["w"]), int(e["reg"])))
        goodb = gb == eb and (len(rel_calls) - before) == rel
        ok_b += goodb
        if not goodb and len(fails) < 10: fails.append(dict(t=t, part="B", got=gb, exp=eb, rel=(len(rel_calls) - before, rel)))
    res = dict(cases=N, delegate_match=ok_a, weight_match=ok_b, fails=fails)
    print(json.dumps(res, ensure_ascii=False, default=str)[:3000])
    (ROOT / "analysis/paint/r6_footmon_emu_out.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
