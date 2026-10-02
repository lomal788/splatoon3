"""대전 스테이지 배치(Banc) 요약과 기믹 핵심 계산 재구현.

사용 (c:/dev/splatoon3 에서):
  PY web/tools/gimmick_stage.py summary Vss_Yagara [--json out.json]   # 레이어(모드)별 기믹·레일·스폰
  PY web/tools/gimmick_stage.py inkrail Vss_Yagara                      # 잉크레일 상태 수명 시뮬레이션
  PY web/tools/gimmick_stage.py ride [--len L]                          # 레일 탑승 속도·이탈 속도 시뮬레이션
  PY web/tools/gimmick_stage.py sponge                                  # 스펀지 크기 응답 시뮬레이션
  PY web/tools/gimmick_stage.py all                                     # 8개 스테이지 요약 + 시뮬레이션 결과를 analysis/gimmick/ 에 저장

계산식 근거는 web/docs/gimmick/*.md 참고. 판독 주소:
  InkRail 상태 갱신 0x710217b514, Connect 실행 0x710217d810(연장 1.0/프레임 = [0x71058a7764], 정적 초기화 0x71021785e0),
  피격 수명 0x710217a668, 레일 구성 0x710217f758, 탑승 갱신 0x7102628108, 최대 속도 0x7102625ef8, 이탈 속도 0x7102626adc,
  스펀지 피해 0x7102217f94/0x7102218920, 스펀지 크기 갱신 0x7102212b64.
"""
import argparse
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANC = ROOT / "extracted" / "params" / "Banc"
OUT = ROOT / "analysis" / "gimmick"
STAGES = ["Vss_Yunohana", "Vss_District00", "Vss_Yagara", "Vss_Temple00", "Vss_Scrap00",
          "Vss_Kaisou03", "Vss_Upland03", "Vss_Carousel"]
LAYERS = {"Cmn": "공통(모든 모드)", "Pnt": "나와바리(Turf)", "Var": "가치에리어(Splat Zones)",
          "Vlf": "가치야구라(Tower)", "Vgl": "가치호코(Rainmaker)", "Vcl": "가치아사리(Clam)",
          "Tcl": "트리컬러", "Day": "Day 조명", "Night": "Night 조명", "Sound": "사운드"}


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def load(stage):
    return json.load(open(BANC / f"{stage}.bcett.byml.json", encoding="utf-8"))


def short(g):
    if g.startswith("Work/Actor/"):
        return g[len("Work/Actor/"):].split(".")[0]
    return g


def rot_matrix(r):
    """Rotate(rad) → 3x3. R = Rz*Ry*Rx (XYZ 순서) [추정 — sead 관례]."""
    x, y, z = r
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[cy * cz, sx * sy * cz - cx * sz, cx * sy * cz + sx * sz],
            [cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz],
            [-sy, sx * cy, cx * cy]]


def apply(m, v):
    return [sum(m[i][j] * v[j] for j in range(3)) for i in range(3)]


START_POS = [(2.4, 0.0, 0.3), (0.8, 0.0, -0.3), (-0.8, 0.0, -0.3), (-2.4, 0.0, 0.3)]  # LocatorSpawner LocalLocator


def rail_lengths(points):
    """InkRailData(0x710217f758): 점 사이 직선 거리(f32 sqrt). UseBase(기본 true)면 첫 점 Y+0.5."""
    pts = [list(p) for p in points]
    pts[0][1] = f32(pts[0][1] + 0.5)
    segs = []
    for a, b in zip(pts, pts[1:]):
        d2 = f32(f32(f32((a[0] - b[0]) ** 2) + f32((a[1] - b[1]) ** 2)) + f32((a[2] - b[2]) ** 2))
        segs.append(f32(math.sqrt(d2)))
    total = 0.0
    for s in segs:
        total = f32(total + s)
    return pts, segs, total


def summary(stage):
    d = load(stage)
    actors = d["Actors"]
    by_hash = {a["Hash"]: a for a in actors}
    pt_rail = {}
    for r in d["Rails"]:
        for i, p in enumerate(r["Points"]):
            pt_rail[p["Hash"]] = (r, i)
    out = {"stage": stage, "layers": {}}
    for a in actors:
        lay = a.get("Layer") or "-"
        L = out["layers"].setdefault(lay, {"inkrail": [], "sponge": [], "lift": [], "spawner": [], "start": [],
                                             "keepout": 0, "playerdead": 0, "changepaintable": 0, "counts": {}})
        g = short(a["Gyaml"])
        L["counts"][g] = L["counts"].get(g, 0) + 1
        team = a.get("TeamCmp", {}).get("Team")
        if g == "InkRailOnline":
            link = a["spl__InkRailBancParam"]["LinkToPoint"]
            r, idx = pt_rail[link]
            pts, segs, total = rail_lengths([p["Translate"] for p in r["Points"]])
            L["inkrail"].append({"actor": a.get("Translate"), "rail": r["Hash"], "link_index": idx,
                                 "points": pts, "segments": segs, "length": total,
                                 "extend_frames": math.ceil(total / 1.0)})
        elif g.startswith("Sponge"):
            p = a["spl__SpongeBancParam"]
            L["sponge"].append({"actor": g, "team": team, "pos": a.get("Translate"), "rot": a.get("Rotate"),
                                "scale": a.get("Scale"), "type": p.get("Type"), "default_max": p.get("IsDefaultMax", False),
                                "safe_pos": [by_hash[h].get("Translate") for h in p.get("SafePosLinks", []) if h in by_hash]})
        elif g == "Mpt_KeepOutPlayer":
            L["keepout"] += 1
        elif g == "Mpt_PlayerDead":
            L["playerdead"] += 1
        elif "spl__LiftBancParam" in a and not (a.get("game__RailMovableSequentialParam") or
                                                a.get("spl__ailift__AILiftBancParam", {}).get("ToRailPoint")):
            L.setdefault("static_lift_parts", []).append(g)
        elif g.startswith("Lft_") or "spl__LiftBancParam" in a:
            rm = a.get("game__RailMovableSequentialParam", {})
            ai = a.get("spl__ailift__AILiftBancParam", {})
            rp = ai.get("ToRailPoint")
            rail = None
            if rp in pt_rail:
                r, _ = pt_rail[rp]
                rail = {"points": [p["Translate"] for p in r["Points"]],
                        "break_time": [p.get("game__LiftGraphRailNodeParam", {}).get("BreakTime") for p in r["Points"]],
                        "rotation": r.get("Rotation")}
            L["lift"].append({"actor": g, "team": team, "pos": a.get("Translate"), "rot": a.get("Rotate"),
                              "move": rm, "rail": rail,
                              "not_paintable": len(a["spl__LiftBancParam"].get("ToNotPaintableArea", []))})
        elif g == "LocatorSpawner":
            m = rot_matrix(a.get("Rotate", [0, 0, 0]))
            t = a.get("Translate", [0, 0, 0])
            L["spawner"].append({"team": team, "pos": t, "rot": a.get("Rotate"),
                                 "start_pos": [[round(t[i] + v, 3) for i, v in enumerate(apply(m, sp))] for sp in START_POS]})
        elif g == "LocatorVersusStart":
            L["start"].append({"team": team, "pos": a.get("Translate"), "rot": a.get("Rotate")})
        elif g == "ChangePaintableArea":
            L["changepaintable"] += 1
    return out


# ---------------- InkRail 수명 ----------------
P_INKRAIL = dict(WaitLife=100, EmitLife=4000, ConnectionSec=15.0, RequestUnemitSec=0.5,
                 IsAllowNeutral=True, IsProlongByFriend=True, IsUnemitByEnemy=True, IsUnemitByTime=True)


def inkrail_sim(length, hits, frames=1200, p=P_INKRAIL):
    """상태 0 Wait, 1 Connect, 2 RequestUnemit. hits = {frame: [(amount, team)]}.
    0x710217b514 순서: Wait→(life<=0)→Connect, Connect: acc += max/int(sec*60) → life -= floor(acc) → life<=0 → RequestUnemit,
    RequestUnemit: now >= deadline → Wait. 피격 0x710217a668: 같은 팀&Connect&Prolong 이면 +, 아니면 -, [0,max] 클램프.
    팀: 중립(3/-1)일 때 첫 피격 팀으로 정해짐(0x710217ea4c)."""
    state, team, life, mx, acc, deadline, ext = 0, 3, p["WaitLife"], p["WaitLife"], 0.0, 0, 0.0
    conn_frames = int(f32(p["ConnectionSec"] * 60.0))
    log = []
    for now in range(frames):
        for amt, t in hits.get(now, []):
            if team in (3, -1):
                team = t
            friend = p["IsProlongByFriend"] and state == 1 and t == team
            v = life + (amt if friend else -amt)
            life = 0 if v < 0 else min(v, mx)
        prev = state
        if state == 0:
            if life <= 0:
                state, acc, life, mx, ext = 1, 0.0, p["EmitLife"], p["EmitLife"], 0.0
        elif state == 1:
            if p["IsUnemitByTime"] and life > 0:
                acc = f32(acc + f32(mx / conn_frames))
                if acc >= 1.0:
                    k = math.floor(acc)
                    life = max(life - k, 0)
                    acc = f32(acc - k)
            if life <= 0:
                state, deadline = 2, int(f32(p["RequestUnemitSec"] * 60.0) + now)
        elif state == 2:
            if deadline != 0 and now >= deadline:
                state, team, life, mx = 0, 3, p["WaitLife"], p["WaitLife"]
        if state == 1:
            ext = min(f32(ext + 1.0), length)
        if state != prev:
            log.append({"frame": now, "from": prev, "to": state, "life": life, "team": team, "extend": ext})
    return log


# ---------------- 탑승 ----------------
P_RIDE = dict(PlayerAcc=0.05, PlayerSpeedMax=0.192, PlayerSpeedMax_LostArmor=0.1, PlayerAirKd=0.92,
              AccLerpNBias=0.25, BindLerpCnt=24, SpeedLimit=0.3, PlayerJumpSpeed=0.19,
              PlayerJumpRightSpeed=0.01, FinishPlayerVelRateY=0.3, PlayerVelBufferSize=5)


def bias(x, b):
    """0x7102628108 / 0x7102212b64 공통 바이어스 곡선. |b-0.5|<=0.001 이면 항등."""
    d = b - 0.5
    if -0.001 <= d and not (0.001 <= d and d != 0.001):
        return x
    ax = abs(x)
    if ax < 0.001:
        return 0.0
    if b < 0.001:
        return 1.0 if ax >= 0.999 else 0.0
    y = math.exp(math.log(ax) * math.log(b) * -1.442695)
    return y if x >= 0 else -y


def ride_sim(length, stick=1.0, align=1.0, v0=0.0, p=P_RIDE, frames=400):
    v, s, out = v0, 0.0, []
    for f in range(frames):
        v = f32(v * p["PlayerAirKd"])
        a = f32(bias(stick, p["AccLerpNBias"]) * align)
        v = f32(v + a * p["PlayerAcc"])
        vmax = p["PlayerSpeedMax"]
        v = max(-vmax, min(v, vmax))
        s = f32(s + v)
        out.append((f + 1, v, s))
        if s >= length:
            break
    return out


def exit_velocity(v_last, d, side, p=P_RIDE):
    """0x7102626adc: (vx + (-dz)*side*k, vy*FinishRateY + JumpSpeed, vz + dx*side*k), k=PlayerJumpRightSpeed."""
    k = p["PlayerJumpRightSpeed"]
    return (f32(v_last[0] + (-d[2]) * side * k), f32(v_last[1] * p["FinishPlayerVelRateY"] + p["PlayerJumpSpeed"]),
            f32(v_last[2] + d[0] * side * k))


# ---------------- 스펀지 ----------------
SPONGE = {
    "SpongeSmall_3p0_VS": dict(Scale_Max=3.0, ScaleDamageForMax=5000.0, FriendDamageCf=2.0, Scale_Bias=0.5, Scale_Kp=1.0,
                               Scale_Kd=0.0, Scale_Kf=0.25, Scale_MaxVelH=0.3, Scale_MaxVelL=0.3, Jiggle_ScalePerDamage=0.025),
    "SpongeSmall_VS": dict(Scale_Max=4.5, ScaleDamageForMax=5000.0, FriendDamageCf=2.0, Scale_Bias=0.5, Scale_Kp=1.0,
                           Scale_Kd=0.0, Scale_Kf=0.25, Scale_MaxVelH=0.3, Scale_MaxVelL=0.3, Jiggle_ScalePerDamage=0.025),
    "SpongeTall_4p5_VS": dict(Scale_Max=2.25, ScaleDamageForMax=3500.0, FriendDamageCf=3.0, Scale_Bias=0.5, Scale_Kp=1.0,
                              Scale_Kd=0.0, Scale_Kf=0.15, Scale_MaxVelH=0.3, Scale_MaxVelL=0.3, Jiggle_ScalePerDamage=0.025),
}


def sponge_sim(p, hits, team=0, frames=120, start=1.0):
    """hits = {frame: [(damage, attackerTeam)]}. 반환: 프레임별 (sLin, target, vel, cur)."""
    s_lin, target, vel, cur, out = start, start, 0.0, start, []
    smax = p["Scale_Max"]
    for f in range(frames):
        for dmg, t in hits.get(f, []):
            delta = f32((smax - 1.0) * f32(dmg / p["ScaleDamageForMax"]))
            if team not in (3, -1) and t == team:
                delta = f32(delta * p["FriendDamageCf"])
            s_lin = f32(s_lin + delta) if t == team else f32(s_lin - delta)
            s_lin = min(s_lin, smax) if s_lin >= 1.0 else 1.0
            dd = f32(s_lin - smax)
            if -0.001 <= dd and (dd < 0.001 or dd == 0.001):   # 최대치에 붙어 있을 때만 지글 (0x7102217f94)
                cur = f32(cur + min(f32(dmg * 0.0016666667 * p["Jiggle_ScalePerDamage"]), 0.25))
        r = f32((s_lin - 1.0) / (smax - 1.0))
        r = bias(r, p["Scale_Bias"])
        kf = p["Scale_Kf"]
        if kf > 0:
            nt = f32((smax - 1.0) * r + 1.0)
            target = nt if kf >= 1.0 else f32(target + (nt - target) * kf)
        vel = f32(vel * p["Scale_Kd"])
        vel = f32(vel + (target - cur) * p["Scale_Kp"])
        mv = p["Scale_MaxVelH"]
        if mv >= 0:
            if mv < vel:
                vel = mv
        elif vel < -mv:
            vel = -mv
        cur = f32(vel + cur)
        if cur < 1.0:
            cur = 1.0
        out.append((f, s_lin, target, vel, cur))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["summary", "inkrail", "ride", "sponge", "all"])
    ap.add_argument("stage", nargs="?", default="Vss_Yagara")
    ap.add_argument("--json")
    ap.add_argument("--len", type=float, default=20.0)
    a = ap.parse_args()
    if a.cmd == "summary":
        s = summary(a.stage)
        txt = json.dumps(s, ensure_ascii=False, indent=1)
        if a.json:
            Path(a.json).write_text(txt, encoding="utf-8")
        else:
            print(txt)
    elif a.cmd == "inkrail":
        s = summary(a.stage)
        for lay, L in s["layers"].items():
            for r in L["inkrail"]:
                log = inkrail_sim(r["length"], {10: [(360, 0)]})
                print(lay, "len", round(r["length"], 4), "extend_frames", r["extend_frames"], log)
    elif a.cmd == "ride":
        for f, v, s in ride_sim(a.len)[:12]:
            print(f, round(v, 6), round(s, 6))
        r = ride_sim(a.len)
        print("frames to", a.len, "=", r[-1][0])
        print("exit (v=(0.192,0,0), d=(1,0,0), side=1):", exit_velocity((0.192, 0, 0), (1, 0, 0), 1.0))
    elif a.cmd == "sponge":
        for name, p in SPONGE.items():
            o = sponge_sim(p, {0: [(360, 0)]}, team=0, frames=8)
            print(name, [(f, round(sl, 4), round(t, 4), round(v, 4), round(c, 4)) for f, sl, t, v, c in o])
            hits = {f: [(360, 0)] for f in range(0, 120, 6)}
            hits[60] = [(360, 1)]
            o = sponge_sim(p, hits, team=0, frames=90)
            print("  연사(6프레임마다 같은팀 360, 60프레임 적 360):", [(f, round(sl, 4), round(c, 4)) for f, sl, t, v, c in o if f in (0, 6, 30, 54, 59, 60, 61, 66, 89)])
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        res = {}
        for st in STAGES:
            s = summary(st)
            res[st] = s
            (OUT / f"{st}_summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
        sims = {"inkrail_Yagara_Pnt": [inkrail_sim(r["length"], {10: [(360, 0)]}, frames=1200)
                                       for r in res["Vss_Yagara"]["layers"]["Pnt"]["inkrail"]],
                "ride_len20": ride_sim(20.0)[:10] + [ride_sim(20.0)[-1]],
                "sponge": {n: sponge_sim(p, {0: [(360, 0)]}, team=0, frames=6) for n, p in SPONGE.items()}}
        (OUT / "sim_results.json").write_text(json.dumps(sims, ensure_ascii=False, indent=1), encoding="utf-8")
        print("saved", OUT)


if __name__ == "__main__":
    main()
