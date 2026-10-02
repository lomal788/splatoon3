"""원본 실행: 눈 색 적용 0x710145249c(플레이어 모델 홀더, 인자 = 눈 색 번호) — Color_Eye 재질 애니 프레임 = 번호.

이미 초기화된 애니 객체(+8 = 1)를 주어 첫 진입 초기화(0x7103674bd0 이름 조회)는 건너뛴다.
원본 그대로 실행: 0x710145249c 본문, 프레임 수 조회 0x71036751a4(가짜 FMAA: +0x58 = FrameCount).
스텁: 0x7101262c18(애니 객체 적용), 0x7103673874/0x7103674288/0x7103673fd0(모델 재질 갱신) 진입 즉시 복귀(호출 횟수만 기록).
재구현: 0 <= idx < FrameCount 이면 holder+0x3c = idx, 애니+0x1c = (f32)idx, 아니면 둘 다 그대로.
사용: PY web/tools/r5_gfx_char_eye_emu.py → analysis/completion/r5/gfx_char_eye_emu.json
"""
import json
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_LR, UC_ARM64_REG_PC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F = 0x710145249c
STUBBED = {0x7101262c18: "anim_apply", 0x7103673874: "mdl_a", 0x7103674288: "mdl_b", 0x7103673fd0: "mdl_c"}


def main():
    u = GUC()
    m = u.mu
    calls = []

    def hk(mu, addr, size, d):
        calls.append(STUBBED[addr])
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    for a in STUBBED:
        m.hook_add(UC_HOOK_CODE, hk, begin=a, end=a)

    holder = u.alloc(0x200)
    anim = u.alloc(0x80)
    model = u.alloc(0x100)
    res = u.alloc(0x200)
    handles = u.alloc(0x300)
    ents = u.alloc(0x18 * 4)
    fmaa = u.alloc(0x80)
    p1 = u.alloc(0x10)
    u.wq(holder + 0x48, anim)
    u.wq(holder + 0x28, model)
    u.wq(model + 0x58, res)
    u.wq(model + 0x60, 0)
    m.mem_write(anim + 8, b"\x01")
    u.u32(res + 0x48, 0x10)          # 핸들 수 >= 0xe → 색인 13 칸 사용
    u.wq(res + 0x50, handles)
    u.u32(handles + 0x270, (2 << 16) | 1)   # 종류 1(밑 +0xa0), 순번 2
    m.mem_write(res + 0xa0, struct.pack("<H", 1))  # 종류 1 시작 오프셋 1 → 실제 칸 3
    u.u32(res + 0x90, 4)
    u.wq(res + 0x98, ents)
    u.wq(ents + 0x18 * 3, p1)
    u.wq(p1, fmaa)
    results = []
    ok = 0
    total = 0
    for frames in (21, 22, 1, 8):
        u.u32(fmaa + 0x58, frames)
        for idx in list(range(-3, frames + 4)) + [0x7fffffff, -0x80000000]:
            sentinel_h = 0x5A5A5A5A
            sentinel_f = 0x7FC0DEAD
            u.u32(holder + 0x3c, sentinel_h)
            u.u32(anim + 0x1c, sentinel_f)
            calls.clear()
            u.call(F, holder, idx & 0xFFFFFFFF)
            got_h = u.ru32(holder + 0x3c)
            got_f = u.ru32(anim + 0x1c)
            if 0 <= idx < frames:
                exp_h, exp_f = idx, struct.unpack("<I", struct.pack("<f", float(idx)))[0]
                exp_calls = ["anim_apply", "mdl_a", "mdl_b", "mdl_c"]
            else:
                exp_h, exp_f, exp_calls = sentinel_h, sentinel_f, []
            good = got_h == exp_h and got_f == exp_f and calls == exp_calls
            ok += good
            total += 1
            if not good and len(results) < 5:
                results.append({"frames": frames, "idx": idx, "got": [got_h, got_f, list(calls)], "exp": [exp_h, exp_f, exp_calls]})
    data = json.loads((ROOT / "analysis/assets_work/anim_Player00.json").read_text(encoding="utf-8"))
    ce = [a for a in data["materialAnims"] if a["name"] == "Color_Eye"][0]
    pattern = ce["materials"]["M_Eye"]["patterns"]["_a0"]
    usable = [t for f, t in pattern if f < ce["frames"]]
    out = {"function": hex(F), "cases": total, "matches": ok, "fail_examples": results,
           "stubs": [f"{hex(a)} {n}: 진입 즉시 복귀" for a, n in STUBBED.items()] + ["첫 진입 초기화 경로(+8==0, 0x7103674bd0 이름 조회)는 실행하지 않음"],
           "plt_stubbed": sorted(set(u.plt_stubbed)),
           "data_Color_Eye": {"FrameCount": ce["frames"], "pattern_keys": len(pattern), "usable_textures": len(usable),
                              "unreachable": [t for f, t in pattern if f >= ce["frames"]]}}
    p = ROOT / "analysis/completion/r5/gfx_char_eye_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("cases", "matches", "plt_stubbed", "data_Color_Eye")}, ensure_ascii=False))
    if results:
        print(results)
    sys.exit(0 if ok == total else 1)


if __name__ == "__main__":
    main()
