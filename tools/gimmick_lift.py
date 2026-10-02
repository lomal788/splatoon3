"""이동 발판(spl::AILiftBlitzCompatible + game::RailMovableSequential) 일정 재구현.

원본 판독(web/docs/gimmick/stage_misc.md §1):
  일정 생성 0x7101305238, 시간 평가 0x71013043d8, 이동 시간 0x7101305b40,
  구간 처리 표 0x7105577e48 = [0x71013046f4(정지), 0x7101304984(점 대기), 0x7101304cec(이동), 0x71013046f4(끝)],
  레일 어댑터 vtable 0x7105587318(+0x48 점 BreakTime, +0x50 다음 점, +0x58 이전 점, +0x68 끝 여부, +0x70 거리차, +0x78 누적거리).
시간 = 초(갱신 0x7101479f7c 에서 프레임수*0.016666668 누적).

회전(2026-10-02 3차 판독, web/docs/gimmick/stage_misc.md §1.5):
  레일 Rotation(Banc Rails[].Rotation, 라디안) → 레일 행렬 R_rail = Rz·Ry·Rx   (0x71012fecec, 열 우선 저장 +0xe8)
  점 Rotation(LiftGraphRailNodeParam.Rotation, 도)  → 점 회전 = R_rail · Rz·Ry·Rx(도→라디안)  (0x7101301d58, 점+0x34/+0x64)
  거리 s 의 행렬(어댑터 +0x90 0x710147b7a8): 위치 = 레일 위치(0x71012ffeac, 부모 변환 R1·R0ᵀ·(p−T0)+T1, LiftRail 은 단위),
     회전 = slerp(점 i 회전, 점 i+1 회전, u)  (0x7101250f0c, 쿼터니언 최단 경로)  u = 구간 안 비율(직선 구간 clamp(sLocal/len))
  점 대기/시작/끝(cInMove): 점 자세(점+0x58 = 위치+회전)
  출력 = 위 회전 × SequentialRotate(빈 파라미터면 단위, 0x71012eeb98) — 0x7101479f7c

사용: PY web/tools/gimmick_lift.py [Vss_Carousel] [--t 0,4,6,8,30,32,34,64,66]
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
f32 = lambda x: struct_f(x)  # noqa: E731


def struct_f(x):
    import struct
    return struct.unpack("<f", struct.pack("<f", x))[0]


KIND = {0: "start", 1: "break", 2: "move", 3: "end"}


def euler_zyx(rx, ry, rz):
    """Rz·Ry·Rx (0x71012fecec / 0x7101301d58 의 sin/cos 조합과 같은 식). 행 우선 3x3 로 반환."""
    sx, cx = math.sin(rx), math.cos(rx)
    sy, cy = math.sin(ry), math.cos(ry)
    sz, cz = math.sin(rz), math.cos(rz)
    return [[cy * cz, sx * sy * cz - cx * sz, cx * sy * cz + sx * sz],
            [cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz],
            [-sy, sx * cy, cx * cy]]


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mat_to_quat(m):
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        return [(m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s, 0.25 * s]
    i = max(range(3), key=lambda k: m[k][k])
    j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(1.0 + m[i][i] - m[j][j] - m[k][k]) * 2
    q = [0.0, 0.0, 0.0, 0.0]
    q[i] = 0.25 * s
    q[j] = (m[j][i] + m[i][j]) / s
    q[k] = (m[k][i] + m[i][k]) / s
    q[3] = (m[k][j] - m[j][k]) / s
    return q


def quat_to_mat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def slerp_mat(a, b, t):
    """0x7101250f0c: 쿼터니언 내적 d(±1 클램프), 각 = acos|d|, sin<1.1920929e-07 이면 선형, d<0 이면 b 부호 반전."""
    qa, qb = mat_to_quat(a), mat_to_quat(b)
    d = max(-1.0, min(1.0, sum(x * y for x, y in zip(qa, qb))))
    th = math.acos(min(abs(d), 1.0))
    st = math.sin(th)
    if abs(st) >= 1.1920929e-07:
        wa, wb = math.sin(th - th * t) / st, math.sin(th * t) / st
    else:
        wa, wb = 1.0 - t, t
    if d < 0:
        wb = -wb
    return quat_to_mat([wa * x + wb * y for x, y in zip(qa, qb)])


class Rail:
    def __init__(self, pts, breaks, closed=False, rail_rot=(0.0, 0.0, 0.0), node_rot=None):
        self.p = pts
        self.brk = breaks
        self.closed = closed
        self.n = len(pts)
        self.R = euler_zyx(*rail_rot)                              # +0xe8 (라디안)
        nr = node_rot or [None] * self.n
        self.prot = [matmul(self.R, euler_zyx(*[math.radians(v) for v in r])) if r else self.R for r in nr]
        self.dist = [0.0]
        for i in range(1, self.n):
            a, b = pts[i - 1], pts[i]
            self.dist.append(struct_f(self.dist[-1] + struct_f(math.sqrt(sum((b[k] - a[k]) ** 2 for k in range(3))))))

    def _step(self, i, d):
        j = i + d
        if self.closed:
            return j % self.n
        return min(max(j, 0), self.n - 1)

    def next(self, i, rev):        # vt+0x50 0x710147b57c
        return self._step(i, -1 if rev else 1)

    def prev(self, i, rev):        # vt+0x58 0x710147b5e4
        return self._step(i, 1 if rev else -1)

    def is_end(self, i, rev):      # vt+0x68 0x710147b694
        if self.closed:
            return False
        return i == (0 if rev else self.n - 1)

    def seg_len(self, a, b):       # vt+0x70 0x710147b6dc (flag 0)
        return struct_f(self.dist[b] - self.dist[a])

    def seg_at(self, s):           # 0x71013001f4: (i, j, u)  u = clamp(sLocal/len) (직선 구간 vt+0x28 0x71013016a0)
        s = min(max(s, 0.0), self.dist[-1])
        for i in range(1, self.n):
            if s < self.dist[i] or i == self.n - 1:
                L = self.dist[i] - self.dist[i - 1]
                u = 0.0 if L == 0 else min(max((s - self.dist[i - 1]) / L, 0.0), 1.0)
                return i - 1, i, u
        return 0, min(1, self.n - 1), 0.0

    def rot_at(self, s):           # 어댑터 +0x90 0x710147b7a8 의 회전부
        i, j, u = self.seg_at(s)
        return slerp_mat(self.prot[i], self.prot[j], u)

    def pos_at(self, s):           # 누적거리 → 위치. 직선 구간 선형(0x71012ff4xx 직선 세그먼트, 제어점 NaN) [판독]
        s = min(max(s, 0.0), self.dist[-1])
        for i in range(1, self.n):
            if s <= self.dist[i] or i == self.n - 1:
                L = self.dist[i] - self.dist[i - 1]
                u = 0.0 if L == 0 else (s - self.dist[i - 1]) / L
                return [self.p[i - 1][k] + (self.p[i][k] - self.p[i - 1][k]) * u for k in range(3)]
        return list(self.p[0])


class RailMover:
    """game::RailMovableSequential (+0x80 시작점, +0x18e8 WaitTime, +0x18ec 주기)."""

    def __init__(self, rail, prm, start=0):
        self.r = rail
        self.patrol = prm.get("PatrolType", "cStop")
        self.speed_calc = prm.get("SpeedCalcType", "cTime")
        self.interp = prm.get("InterpolationType", "cLinear")
        self.move_time = prm.get("MoveTime", 1.0)
        self.move_speed = int(prm.get("MoveSpeed", 1))
        self.wait = prm.get("WaitTime", 0.0)
        self.start = start
        self.build()

    def move_dur(self, seg, pos):  # 0x7101305b40
        if self.speed_calc == "cSpeed":
            return struct_f(self.r.seg_len(seg, pos) / float(self.move_speed))
        if self.speed_calc == "cTime":
            return self.move_time
        return 1.0

    def build(self):  # 0x7101305238
        r = self.r
        sched = []
        if r.n < 2:
            self.sched = [(0.0, 3, self.start, False)]
            self.wait_t = 0.0
            self.period = 0.0
            return
        t, kind, pos, rev = 0.0, 0, self.start, False
        self.wait_t = 0.0
        while True:
            npos, nrev = pos, rev
            if kind == 2:
                d = self.move_dur(r.prev(pos, rev), pos)
                nk = 3 if (self.patrol == "cStop" and r.is_end(pos, rev)) else 1
            elif kind == 1:
                d = r.brk[pos]
                at_end = r.is_end(pos, rev) if self.patrol == "cContinue" else False
                nrev = at_end != rev
                npos = r.next(pos, nrev)
                nk = 2
            else:  # kind 0
                d = self.wait
                self.wait_t = self.wait
                npos = r.next(pos, rev)
                nk = 2
            t2 = struct_f(t + d)
            if t < t2:
                sched.append((t, kind, pos, rev))
            t, kind, pos, rev = t2, nk, npos, nrev
            if any(e[1] == kind and e[2] == pos and e[3] == rev for e in sched):
                break
            if kind == 3:
                sched.append((t, 3, pos, rev))
                break
        self.sched = sched
        self.period = struct_f(t - self.wait_t)

    def eval_time(self, t):  # 0x71013043d8
        t = max(t, 0.0)
        if self.patrol == "cStop":
            te = min(t, self.wait_t + self.period)
        else:
            if self.period == 0:
                te = 0.0
            else:
                u = t - self.wait_t
                if u > 0:
                    u = u - self.period * int(u / self.period)
                    if u < 0:
                        u += self.period
                te = self.wait_t + u
        e = None
        for x in reversed(self.sched):
            if x[0] <= te:
                e = x
                break
        return te, e

    def position(self, t):
        te, e = self.eval_time(t)
        if e is None:
            return te, None, None, None
        start, kind, pos, rev = e
        r = self.r
        if kind == 2:  # 0x7101304cec
            seg = r.prev(pos, rev)
            d = self.move_dur(seg, pos)
            u = 1.0 if d == 0 else (te - start) / d
            if self.interp == "cSin":
                u = (math.sin(u * 3.1415927 - 1.5707964) + 1.0) * 0.5
            s = u * r.seg_len(seg, pos) + r.dist[seg]
            return te, KIND[kind], r.pos_at(s), r.rot_at(s)
        return te, KIND[kind], list(r.p[pos]), r.prot[pos]


def carousel(stage="Vss_Carousel"):
    b = json.loads((ROOT / f"extracted/params/Banc/{stage}.bcett.byml.json").read_text(encoding="utf-8"))
    pt2rail = {}
    for r in b["Rails"]:
        for i, p in enumerate(r["Points"]):
            pt2rail[p["Hash"]] = (r, i)
    out = []
    for a in b["Actors"]:
        prm = a.get("game__RailMovableSequentialParam")
        link = (a.get("spl__ailift__AILiftBancParam") or {}).get("ToRailPoint")
        if not prm or not link or link not in pt2rail:
            continue
        r, i = pt2rail[link]
        pts = [p["Translate"] for p in r["Points"]]
        brk = [(p.get("game__LiftGraphRailNodeParam") or {}).get("BreakTime", 0.0) for p in r["Points"]]
        nrot = [(p.get("game__LiftGraphRailNodeParam") or {}).get("Rotation") for p in r["Points"]]
        rail = Rail(pts, brk, r.get("IsClosed", False), tuple(r.get("Rotation", [0.0, 0.0, 0.0])), nrot)
        out.append((a, RailMover(rail, prm, i)))
    return out


def main():
    stage = next((x for x in sys.argv[1:] if x.startswith("Vss_")), "Vss_Carousel")
    ts = [0, 2, 4, 6, 8, 20, 30, 32, 34, 50, 64, 66, 68, 124]
    if "--t" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--t") + 1].split(",")]
    res = []
    seen = set()
    for a, m in carousel(stage):
        key = (a["Gyaml"], a.get("TeamCmp", {}).get("Team"))
        if key in seen:
            continue
        seen.add(key)
        row = {"actor": a["Gyaml"], "team": key[1], "layer": a["Layer"],
               "schedule": [(round(s, 4), KIND[k], p, rv) for s, k, p, rv in m.sched],
               "waitTime": m.wait_t, "period": m.period, "samples": []}
        row["actorRotate"] = a.get("Rotate", [0.0, 0.0, 0.0])
        for t in ts:
            te, k, p, R = m.position(t)
            smp = {"t": t, "t_eff": round(te, 4), "kind": k, "pos": [round(x, 4) for x in p] if p else None}
            if R:
                smp["rot"] = [[round(x, 4) + 0.0 for x in row_] for row_ in R]
                smp["yawDeg"] = round(math.degrees(math.atan2(R[0][2], R[2][2])), 3)
            row["samples"].append(smp)
        res.append(row)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
