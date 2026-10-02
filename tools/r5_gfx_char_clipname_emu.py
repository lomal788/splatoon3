"""원본 ASB 클립 이름 해석기 0x710244d0b0(플레이어 AS 래퍼+0x40 해석기, vt 0x71056328f8 슬롯2) 실행.

스텁: 바인더 이름 조회(해석기+8 객체 vt+0x18 = 원래 0x710244b414)만 파이썬 훅으로 바꾼다.
  훅은 넘어온 이름을 기록하고, 주어진 '존재하는 클립' 집합에 있으면 0, 없으면 -1 을 돌려준다.
문자열 치환 0x710351c964, 결과 캐시 0x710244dfc4 는 원본 그대로 실행(PLT memcpy/strlen 만 파이썬).
재구현(아래 resolve)은 디컴파일 판독으로 독립 작성한 후보 순서식이고, 원본 실행의 조회 순서·최종 반환 이름과 비교한다.
사용: PY web/tools/r5_gfx_char_clipname_emu.py  → analysis/completion/r5/gfx_char_clipname_emu.json
"""
import itertools
import json
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC, STUB  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F = 0x710244d0b0
LOOKUP = STUB + 0x700

CHAIN = [("BBll", "Slsh"), ("Glng", "Spnr"), ("Brush", "Brsh"), ("Twins", "Mnvr"),
         ("Umbrella", "Shlt"), ("Nrml", "Shtr")]


def resolve(name, keys, cat, det, emo, clips):
    """판독식 재구현: (조회한 이름 목록, 반환 이름)."""
    tried = []

    def look(n):
        n = n[:0x3f]
        tried.append(n)
        return n in clips

    if "WeaponVariation" in keys:
        for v in (det, cat):
            n = name.replace("Nrml", v, 1)
            if look(n):
                return tried, n[:0x3f]
    if "EmoteVariation" in keys:
        for v in (emo, "Win01"):
            n = name.replace("@", v, 1)
            if look(n):
                return tried, n[:0x3f]
    for a, b in CHAIN:
        n = name.replace(a, b, 1)
        if look(n):
            return tried, n[:0x3f]
    return tried, name


def main():
    u = GUC()
    m = u.mu
    state = {"clips": set(), "log": []}

    def hook(mu, addr, size, data):
        p = mu.reg_read(UC_ARM64_REG_X2)
        s = u._cstr(u.rq(p)).decode()
        state["log"].append((mu.reg_read(UC_ARM64_REG_X1) & 0xFF, s))
        mu.reg_write(UC_ARM64_REG_X0, 0 if s in state["clips"] else 0xFFFFFFFF)

    m.hook_add(UC_HOOK_CODE, hook, begin=LOOKUP, end=LOOKUP)

    binder = u.alloc(0x40)
    bvt = u.alloc(0x100)
    u.wq(binder, bvt)
    u.wq(bvt + 0x18, LOOKUP)

    keystr = {k: u.cstr(k) for k in ("WeaponVariation", "EmoteVariation", "AnimationDriven", "Other")}

    def make_resolver(cat, det, emo):
        r = u.alloc(0x300)
        u.wq(r + 8, binder)
        u.wq(r + 0x10, u.cstr(cat))
        u.wq(r + 0x18, u.cstr(det))
        u.wq(r + 0x20, u.cstr(emo))
        ring = u.alloc(0x58 * 4)
        for i in range(4):
            u.wq(ring + 0x58 * i + 8, u.alloc(0x40))
            u.u32(ring + 0x58 * i + 0x10, 0x40)
        u.wq(r + 0x28, ring)
        u.u32(r + 0x30, 4)
        u.u32(r + 0x34, 0)
        u.u32(r + 0x38, 0)
        u.wq(r + 0x1a8, u.alloc(0x40))
        u.u32(r + 0x1b0, 0x40)
        return r

    lst = u.alloc(0x20)
    arr = u.alloc(0x40)
    p = u.alloc(0x20)
    nbuf = u.alloc(0x100)

    def call(r, name, keys, kind):
        u.u32(lst, len(keys))
        for i, k in enumerate(keys):
            u.wq(arr + 8 * i, keystr[k])
        u.wq(lst + 8, arr)
        m.mem_write(nbuf, name.encode() + b"\0")
        u.wq(p, nbuf)
        u.wq(p + 8, lst)
        m.mem_write(p + 0x10, bytes([kind]))
        m.mem_write(r + 0x1fc, b"\x01")  # 캐시 무효화(매 호출 새로 해석)
        state["log"] = []
        ret = u.call(F, r, p)
        return [s for _, s in state["log"]], [k for k, _ in state["log"]], u._cstr(ret).decode()

    # 실제 데이터: Player00 스켈레탈 클립 이름(1044) — 슈터 배치
    anim = json.loads((ROOT / "analysis/assets_work/anim_Player00.json").read_text(encoding="utf-8"))
    p00 = {x["name"] if isinstance(x, dict) else x for x in anim["skeletal"]}
    asb = json.loads((ROOT / "analysis/assets_work/asb/SplPlayer.json").read_text(encoding="utf-8"))
    leaf_names = sorted({s for n in asb["nodes"] if n["type"] in (3,) for s in n["strs"]})

    results = []
    mism = 0
    total = 0
    # A) 실제 사람 ASB 잎 이름 × 키 조합 × 슈터(Shtr/Shtr) × Player00 클립 집합
    key_sets = [[], ["WeaponVariation"], ["EmoteVariation"], ["WeaponVariation", "EmoteVariation"],
                ["WeaponVariation", "EmoteVariation", "AnimationDriven"]]
    r = make_resolver("Shtr", "Shtr", "Win01")
    state["clips"] = p00
    for name in leaf_names:
        for keys in key_sets:
            got_try, kinds, got_ret = call(r, name, keys, 0)
            exp_try, exp_ret = resolve(name, keys, "Shtr", "Shtr", "Win01", p00)
            total += 1
            ok = got_try == exp_try and got_ret == exp_ret and all(k == 1 for k in kinds)
            mism += not ok
            if not ok and len(results) < 20:
                results.append({"name": name, "keys": keys, "orig": [got_try, got_ret], "reimpl": [exp_try, exp_ret]})
    # B) 합성: 무기 변형·이모트·자리표시자별, 존재 집합을 바꿔 각 단계에서 멈추는지
    synth = ["Walk_Nrml", "Emote_@", "Shoot_BBll", "Shoot_Glng", "Hold_Brush", "Hold_Twins", "Hold_Umbrella", "Plain"]
    variants = [("Shtr", "Shtr", "Win01"), ("Rllr", "RllrHeavy", "Win02"), ("Mnvr", "MnvrDual", "Lose01")]
    for (cat, det, emo) in variants:
        r = make_resolver(cat, det, emo)
        for name in synth:
            cands = list(dict.fromkeys(resolve(name, ["WeaponVariation", "EmoteVariation"], cat, det, emo, set())[0] + [name]))
            for keys in key_sets:
                for k in range(len(cands) + 1):
                    clips = set(cands[k:k + 1])
                    state["clips"] = clips
                    for kind in (0, 1):
                        got_try, kinds, got_ret = call(r, name, keys, kind)
                        exp_try, exp_ret = resolve(name, keys, cat, det, emo, clips)
                        total += 1
                        ok = got_try == exp_try and got_ret == exp_ret and all(x == (kind ^ 1) for x in kinds)
                        mism += not ok
                        if not ok and len(results) < 20:
                            results.append({"name": name, "keys": keys, "cat": cat, "det": det, "emo": emo,
                                            "clips": sorted(clips), "kind": kind,
                                            "orig": [got_try, got_ret], "reimpl": [exp_try, exp_ret]})
    # 사례: WalkBackHold_Nrml
    r = make_resolver("Shtr", "Shtr", "Win01")
    state["clips"] = p00
    wbh = call(r, "WalkBackHold_Nrml", ["WeaponVariation", "EmoteVariation"], 0)
    wbs = call(r, "WaitHold_Nrml", ["WeaponVariation"], 0)
    out = {
        "function": hex(F),
        "cases": total, "matches": total - mism, "mismatch_examples": results,
        "stubs": ["binder lookup vt+0x18 (원래 0x710244b414): 이름 기록 + 집합 포함 여부만 반환"],
        "plt_python": ["memcpy", "memmove", "memcmp", "strlen"], "plt_stubbed": sorted(set(u.plt_stubbed)),
        "not_executed": ["바인더 실제 조회(0x710244b414 → 0x71036c29ec 리소스 사전)", "AS 잎 진입 0x71039d3608", "키 목록 출처(ASB 노드 → param_2[1])"],
        "example_WalkBackHold_Nrml": {"tried": wbh[0], "returned": wbh[2]},
        "example_WaitHold_Nrml": {"tried": wbs[0], "returned": wbs[2]},
    }
    p = ROOT / "analysis/completion/r5/gfx_char_clipname_emu.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("cases", "matches", "plt_stubbed", "example_WalkBackHold_Nrml", "example_WaitHold_Nrml")}, ensure_ascii=False))
    if results:
        print(json.dumps(results[:3], ensure_ascii=False))
    sys.exit(1 if mism else 0)


if __name__ == "__main__":
    main()
