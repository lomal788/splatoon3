"""r11 gfx-diff 후처리: RenderingDay Bloom 적용 0x7102b699c0 을 unicorn 으로 실행해 블룸 객체(env+0x2ab8) 기록값을 본다.

관심: +0x5a0(clamped_luminance 칸). 명령 0x7102b6a394/0x7102b6a49c..4b0 판독식은
  +0x5a0 = f32(B.ClampedLuminance(+0x30) + f32(f32(A.Intensity(+0x60) - B.ClampedLuminance) * t))
A = x0 쪽(new), B = x2 쪽(old). 모든 '설정됨' 플래그(+0xa0..+0xaf)를 켜서 $parent 상속 탐색(가드·RTTI 호출)은 타지 않는다.
사용: python web/tools/r11_post_bloom_apply_emu.py → analysis/gfx_r11/diff/post/bloom_apply_native.json
"""
import json, random, struct, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_gfx_stage_emu import Emu, fbits

ROOT = Path(__file__).resolve().parents[2]
F = np.float32
FIELDS = {"Intensity": 0x60, "ClampedLuminance": 0x30, "Threshold": 0x94, "ThresholdRange": 0x98}


def make_param(e, vals):
    p = e.alloc(0x100)
    e.w(p, "64s", b"\0" * 64)
    for k, o in FIELDS.items(): e.w(p + o, "f", vals[k])
    e.w(p + 0x34, "4f", 1, 1, 1, 1)
    e.w(p + 0x64, "4f", .816, .816, .816, 1); e.w(p + 0x74, "4f", .094, .094, .094, 1); e.w(p + 0x84, "4f", .953, .953, .953, 1)
    e.w(p + 0x9c, "BB", 1, vals.get("EnableClampedLuminance", 1))
    for o in range(0xa0, 0xb0): e.w(p + o, "B", 1)
    code = e.alloc(0x20); e.w(code, "IIQ", 0x58000040, 0xD65F03C0, p)
    vt = e.alloc(0x100); e.w(vt + 0x98, "Q", code)
    obj = e.alloc(0x20); e.w(obj, "Q", vt)
    return obj


def run_case(e, t, a, b):
    e.reset_heap()
    env = e.alloc(0x3000); blm = e.alloc(0x800)
    e.w(env + 0x2ab8, "Q", blm)
    oa, ob = make_param(e, a), make_param(e, b)
    e.call(0x7102b699c0, x=(oa, env, ob), s=(t,))
    r = lambda o: e.r(blm + o, "f")[0]
    return {"0x48": r(0x48), "0x68": r(0x68), "0x88": r(0x88), "0x5a0": r(0x5a0)}


def expect(t, a, b):
    lerp = lambda x, y: float(F(F(x) + F(F(F(y) - F(x)) * F(t))))
    return {"0x48": lerp(b["Threshold"], a["Threshold"]), "0x68": lerp(b["ThresholdRange"], a["ThresholdRange"]),
            "0x88": lerp(b["Intensity"], a["Intensity"]), "0x5a0": lerp(b["ClampedLuminance"], a["Intensity"])}


if __name__ == "__main__":
    e = Emu(); rng = random.Random(20261004)
    default = {"Intensity": 1.0, "ClampedLuminance": 5.0, "Threshold": 4.0, "ThresholdRange": 1.0}
    cases = [(1.0, default, default), (0.0, default, default), (.5, default, default)]
    for _ in range(256):
        rv = lambda: {k: float(F(rng.uniform(-2, 12))) for k in FIELDS}
        cases.append((float(F(rng.choice([0, 1, rng.random(), rng.uniform(-1, 2)]))), rv(), rv()))
    out = []; bad = 0
    for t, a, b in cases:
        got = run_case(e, t, a, b); want = expect(t, a, b)
        ok = all(fbits(got[k]) == fbits(want[k]) for k in got)
        bad += not ok
        out.append({"t": t, "A": a, "B": b, "native": got, "readExpr": want, "match": ok})
    res = {"function": "0x7102b699c0", "cases": len(out), "mismatch": bad, "lobby_t1_A_eq_B_default": out[0]["native"],
           "stubs": "vtable+0x98 getter 만 합성(파라미터 구조체 포인터 반환), 상속 탐색 경로 미실행", "results": out}
    p = ROOT / "analysis/gfx_r11/diff/post/bloom_apply_native.json"
    p.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("function", "cases", "mismatch", "lobby_t1_A_eq_B_default")}, indent=1))
    print("t0:", out[1]["native"], "t.5:", out[2]["native"])
