"""r6 assets: Banc 액터 배치 행렬(생성 정보) 원본 실행.

대상: 0x7103d03f4c(엔트리, 생성 정보, 부모 3x4) — Banc 파서 0x7103d03768 이 채운 엔트리
(+0x00 Translate, +0x0c Rotate(rad), +0x18 Scale, +0x75 유효)를 생성 정보 +0x40 위치, +0x4c 3x3, +0x70 Scale 로 옮김.
호출: 0x7103cfcfc0 → 람다 vt 0x710575cdf0 슬롯0 0x7103d01298 → 0x7103d03f4c(엔트리, 생성 정보, 람다+0x20).
sinf/cosf(PLT 0x7103e9be40/0x7103e9be30)는 SDK(extracted/exefs/sdk.img) 원본 함수를 unicorn 으로 실행해 돌려줌.
그 밖의 PLT 는 r5_gfx_char_uc.GUC 규칙(스텁 기록). 생성 정보는 0 으로 채워 0x7103515cfc 경로(+0xa8 bit7, +0xf8)는 타지 않음.
결과: analysis/completion/r6/assets_actor_mtx_emu.json
"""
import json, math, random, struct, sys
from pathlib import Path
import numpy as np
from unicorn.arm64_const import UC_ARM64_REG_S0, UC_ARM64_REG_X0, UC_ARM64_REG_PC, UC_ARM64_REG_LR

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC  # noqa: E402
from r5_player_libm_emu import Sdk  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F = np.float32
FN = 0x7103d03f4c


class H(GUC):
    def __init__(self):
        super().__init__()
        self.sdk = Sdk()
        self.libm = []

    def _plt(self, mu, addr, size, user):
        w0 = struct.unpack_from("<I", self._raw, addr - 0x7100000000)[0]
        if (w0 & 0x9F000000) != 0x90000000:
            return
        w1 = struct.unpack_from("<I", self._raw, addr + 4 - 0x7100000000)[0]
        immlo = (w0 >> 29) & 3
        immhi = (w0 >> 5) & 0x7FFFF
        page = ((immhi << 2) | immlo) << 12
        got = (addr & ~0xFFF) + page + ((w1 >> 10) & 0xFFF) * 8
        name = self.got.get(got)
        if name in ("sinf", "cosf"):
            s = struct.unpack("<f", struct.pack("<I", mu.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF))[0]
            r = self.sdk.call(name, s)
            self.libm.append((addr, name))
            mu.reg_write(UC_ARM64_REG_S0, r)
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return
        return super()._plt(mu, addr, size, user)


def f32(x):
    return F(x)


def rot_cands(rx, ry, rz, sin, cos):
    sx, cx, sy, cy, sz, cz = sin(rx), cos(rx), sin(ry), cos(ry), sin(rz), cos(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float64)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float64)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float64)
    return {"Rz·Ry·Rx": Rz @ Ry @ Rx, "Rx·Ry·Rz": Rx @ Ry @ Rz, "Ry·Rx·Rz": Ry @ Rx @ Rz,
            "Rz·Rx·Ry": Rz @ Rx @ Ry, "Ry·Rz·Rx": Ry @ Rz @ Rx, "Rx·Rz·Ry": Rx @ Rz @ Ry}


def reimpl(T, R, P, sin, cos):
    """0x7103d03f4c 의 명령 순서를 그대로 옮긴 f32 독립 재구현(판독). P = 부모 3x4 행 우선 12 float."""
    sx, sy, sz = (F(sin(v)) for v in R)
    cx, cy, cz = (F(cos(v)) for v in R)
    p = [F(v) for v in P]
    Tx, Ty, Tz = (F(v) for v in T)
    px = p[3] + ((p[0] * Tx + Ty * p[1]) + Tz * p[2])
    py = p[7] + ((p[4] * Tx + p[5] * Ty) + p[6] * Tz)
    pz = p[11] + ((p[8] * Tx + p[9] * Ty) + p[10] * Tz)
    R00 = cy * cz; R10 = sz * cy
    sxsy = sx * sy
    R01 = sxsy * cz - sz * cx; R11 = sxsy * sz + cx * cz; R21 = sx * cy
    R12 = sy * (sz * cx) - sx * cz; R02 = sx * sz + sy * (cx * cz); R22 = cx * cy
    M00 = (p[0] * R00 + R10 * p[1]) - sy * p[2]
    M10 = (R00 * p[4] + R10 * p[5]) - sy * p[6]
    M20 = (R00 * p[8] + R10 * p[9]) - sy * p[10]
    M01 = (p[0] * R01 + p[1] * R11) + R21 * p[2]
    M11 = (R01 * p[4] + R11 * p[5]) + R21 * p[6]
    M21 = (R01 * p[8] + R11 * p[9]) + R21 * p[10]
    M02 = R22 * p[2] + (p[1] * R12 + p[0] * R02)
    M12 = (R02 * p[4] + R12 * p[5]) + R22 * p[6]
    M22 = (R02 * p[8] + R12 * p[9]) + R22 * p[10]
    return np.array([px, py, pz, M00, M01, M02, M10, M11, M12, M20, M21, M22], dtype=F)


def run_one(h, ent, parent):
    if not hasattr(h, "bufs"):
        h.bufs = (h.alloc(0x100), h.alloc(0x200), h.alloc(0x40))
    e, ci, p = h.bufs
    h.mu.mem_write(e, bytes(1) * 0x100)
    h.mu.mem_write(ci, bytes(1) * 0x200)
    for i, v in enumerate(ent["T"] + ent["R"] + ent["S"]):
        h.f32(e + 4 * i, v)
    h.mu.mem_write(e + 0x75, b"\x01")
    for i, v in enumerate(parent):
        h.f32(p + 4 * i, v)
    h.libm = []
    r = h.call(FN, e, ci, p)
    out = [h.rf32(ci + 0x40 + 4 * i) for i in range(15)]
    raw = bytes(h.mu.mem_read(ci + 0x40, 0x3c))
    return r & 0xFF, out, raw, list(h.libm)


def main():
    h = H()
    rng = random.Random(20261003)
    sdk_sin = lambda v: float(np.frombuffer(struct.pack("<I", h.sdk.call("sinf", F(v))), F)[0])
    sdk_cos = lambda v: float(np.frombuffer(struct.pack("<I", h.sdk.call("cosf", F(v))), F)[0])
    I34 = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]
    cases = []
    # 실제 데이터 표본(Lby_Lobby00 placement) + 무작위
    pl = json.loads((ROOT / "web/games/splatoon3/assets/maps/Lby_Lobby00/placement.json").read_text(encoding="utf-8"))
    for a in pl["actors"]:
        cases.append(dict(T=[float(F(x)) for x in a["pos"]], R=[float(F(x)) for x in a["rot"]], S=[float(F(x)) for x in a["scale"]], src=a["name"], parent=I34))
    for _ in range(3000):
        cases.append(dict(T=[float(F(rng.uniform(-200, 200))) for _ in range(3)], R=[float(F(rng.uniform(-math.pi * 2, math.pi * 2))) for _ in range(3)],
                          S=[float(F(rng.uniform(0.1, 4))) for _ in range(3)], src="rand", parent=I34))
    # 부모 3x4 가 단위가 아닐 때(행 우선 [r00 r01 r02 tx | ...]) 합성 규칙
    for _ in range(1000):
        pr = [rng.uniform(-math.pi, math.pi) for _ in range(3)]
        Rp = rot_cands(*pr, math.sin, math.cos)["Rz·Ry·Rx"]
        tp = [rng.uniform(-50, 50) for _ in range(3)]
        par = [float(F(Rp[0, 0])), float(F(Rp[0, 1])), float(F(Rp[0, 2])), float(F(tp[0])),
               float(F(Rp[1, 0])), float(F(Rp[1, 1])), float(F(Rp[1, 2])), float(F(tp[1])),
               float(F(Rp[2, 0])), float(F(Rp[2, 1])), float(F(Rp[2, 2])), float(F(tp[2]))]
        cases.append(dict(T=[float(F(rng.uniform(-50, 50))) for _ in range(3)], R=[float(F(rng.uniform(-3.2, 3.2))) for _ in range(3)],
                          S=[1.0, 1.0, 1.0], src="parent", parent=par))
    score = {}
    store = {"row": 0, "col": 0}
    bitexact = 0
    poserr = 0
    maxabs = 0.0
    libm_names = set()
    scale_ok = 0
    examples = []
    exact_reimpl = 0
    for c in cases:
        ok, out, raw, lm = run_one(h, c, c["parent"])
        libm_names.update(n for _, n in lm)
        pos, m9, sc = np.array(out[0:3]), np.array(out[3:12]), out[12:15]
        rx, ry, rz = c["R"]
        cand = rot_cands(rx, ry, rz, sdk_sin, sdk_cos)
        P = np.array(c["parent"], dtype=np.float64).reshape(3, 4)
        best = None
        for k, Rm in cand.items():
            for st in ("row", "col"):
                full = P[:, :3] @ Rm
                flat = full.reshape(-1) if st == "row" else full.T.reshape(-1)
                err = float(np.max(np.abs(flat - m9)))
                if best is None or err < best[0]:
                    best = (err, k, st)
        score[best[1]] = score.get(best[1], 0) + 1
        store[best[2]] += 1
        maxabs = max(maxabs, best[0])
        pexp = P[:, :3] @ np.array(c["T"]) + P[:, 3]
        if np.max(np.abs(pexp - pos)) > 1e-3 * max(1, np.max(np.abs(pexp))):
            poserr += 1
        if [float(F(x)) for x in sc] == c["S"]:
            scale_ok += 1
        # 독립 재구현(f32, 원본 명령 순서와 무관한 식) 비트 일치 여부: 부모 단위 + Rz·Ry·Rx 행 우선
        if c["parent"] == I34:
            sx, cx, sy, cy, sz, cz = (F(sdk_sin(rx)), F(sdk_cos(rx)), F(sdk_sin(ry)), F(sdk_cos(ry)), F(sdk_sin(rz)), F(sdk_cos(rz)))
            Rr = [[cy * cz, sx * sy * cz - cx * sz, cx * sy * cz + sx * sz],
                  [cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz],
                  [-sy, sx * cy, cx * cy]]
            rec = np.array([F(v) for row in Rr for v in row], dtype=F)
            if np.array_equal(rec.view(np.uint32), np.array(out[3:12], dtype=F).view(np.uint32)):
                bitexact += 1
        rec2 = reimpl(c["T"], c["R"], c["parent"], sdk_sin, sdk_cos)
        if np.array_equal(rec2.view(np.uint32), np.array(out[0:12], dtype=F).view(np.uint32)):
            exact_reimpl += 1
        if len(examples) < 6:
            examples.append(dict(src=c["src"], T=c["T"], R=c["R"], S=c["S"], out_pos=list(map(float, pos)), out_m9=list(map(float, m9)), out_scale=sc, best=best))
    res = dict(function=hex(FN), cases=len(cases), lobby_actors=len(pl["actors"]), best_order=score, storage=store,
               max_abs_err_best=maxabs, pos_mismatch=poserr, scale_copied=scale_ok,
               rzryrx_rowmajor_naive_f32_exact=bitexact, reimpl_bit_exact=exact_reimpl, libm_called=sorted(libm_names),
               plt_stubbed=sorted(set(h.plt_stubbed)), examples=examples,
               stubs="sinf/cosf = SDK 원본 함수 실행, 그 밖 PLT 없음(plt_stubbed 목록), 0x7103515cfc 경로 미진입(생성 정보 0)")
    (ROOT / "analysis/completion/r6/assets_actor_mtx_emu.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "examples"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
