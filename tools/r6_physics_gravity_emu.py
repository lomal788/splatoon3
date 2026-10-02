"""[r6 physics] Phive 세계 중력 런타임 값 사슬 원본 실행.

사슬(판독):
  1) 게임 모듈 설정 팩토리 0x710344af54 case 0xf -> Phive 설정(vtable 0x71057173a8). desc = 설정+0x38
     (설정+0x60..+0x68 = desc+0x28..+0x30 = 중력, 설정+0x5c = desc+0x24 = dt)
  2) 월드 생성자 0x7103ac71c8 가 하위 월드 생성 0x7103ac6a20(struct{+8 = desc}) 을 부르고 결과를 월드+0xb8(Entity)/+0xc0(Sensor)에 둔다.
     0x7103ac6bf0~0x7103ac6c2c: 하위 월드+0x298..+0x2a0 = desc+0x28..+0x30, +0x2a4..+0x2ac = 같은 값, +0x2b0 = desc+0x5c
  3) 캐릭터 컨트롤러 상태 S 생성자 0x7103a862cc 꼬리 0x7103a86794~0x7103a86894:
     G0 = S+0x1dc = [[*0x710599dfa8]+0xe8]+0xb8 -> +0x2a4.., 방향 S+0x1e8 = normalize(sign(S+0x1f4)·G0), 실효 S+0x1f8 = S+0x1f4·G0
실행: 1) 팩토리 전체(r5_camweapon_boom_emu.step1_config 재사용), 2)·3) 명령 구간을 레지스터만 맞춰 원본 실행.
스텁: 팩토리의 malloc/memset/PLT(r5 도구와 같음). 2)·3)은 외부 호출 없음(3)의 sqrtf PLT 는 NaN 일 때만).
결과: analysis/completion/r6/physics_gravity_emu.json
"""
import json
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm64_const import UC_ARM64_REG_X19, UC_ARM64_REG_X21, UC_ARM64_REG_X24, UC_ARM64_REG_SP  # noqa: E402
from network_uc import UC, STACK  # noqa: E402
import r5_camweapon_boom_emu as boom  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def bits(x):
    return struct.pack("<f", x).hex()


def run():
    s1, cfg_bytes = boom.step1_config()
    desc_grav = struct.unpack_from("<3f", cfg_bytes, 0x60)
    desc_dt = struct.unpack_from("<I", cfg_bytes, 0x5c)[0]
    e = UC()
    mu = e.mu
    cfg = e.alloc(0x180); mu.mem_write(cfg, cfg_bytes)
    desc = cfg + 0x38
    arg = e.alloc(0x40); e.wq = lambda a, v: mu.mem_write(a, struct.pack("<Q", v))
    e.wq(arg + 8, desc)
    sub = e.alloc(0x300)
    mu.reg_write(UC_ARM64_REG_X19, arg); mu.reg_write(UC_ARM64_REG_X21, sub)
    mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
    mu.emu_start(0x7103ac6bf0, 0x7103ac6c30, count=100)
    sub_298 = [e.rf32(sub + 0x298 + 4 * k) for k in range(3)]
    sub_2a4 = [e.rf32(sub + 0x2a4 + 4 * k) for k in range(3)]
    sub_2b0 = e.ru32(sub + 0x2b0)
    module = e.alloc(0x100); world = e.alloc(0x100)
    singleton = 0x710599dfa8
    e.wq(singleton, module); e.wq(module + 0xe8, world); e.wq(world + 0xb8, sub)
    rows = []
    ok_all = True
    for scale in (1.0, 2.9387755, 0.0, -1.0):
        S = e.alloc(0x2b0)
        e.f32(S + 0x1f4, scale)
        mu.reg_write(UC_ARM64_REG_X19, S); mu.reg_write(UC_ARM64_REG_X24, singleton)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        mu.emu_start(0x7103a86794, 0x7103a86894, count=200)
        G0 = [e.rf32(S + 0x1dc + 4 * k) for k in range(3)]
        dirv = [e.rf32(S + 0x1e8 + 4 * k) for k in range(3)]
        eff = [e.rf32(S + 0x1f8 + 4 * k) for k in range(3)]
        sg = f32(1.0) if scale >= 0.0 else f32(-1.0)
        g = [f32(c * sg) for c in sub_2a4]
        n2 = f32(f32(f32(g[0] * g[0]) + f32(g[1] * g[1])) + f32(g[2] * g[2]))
        ln = f32(n2 ** 0.5)
        inv = f32(1.0 / ln) if ln > 0 else 0.0
        exp_dir = [f32(c * inv) for c in g] if ln > 0 else [0.0, 0.0, 0.0]
        exp_eff = [f32(f32(scale) * c) for c in sub_2a4]
        ok = ([bits(x) for x in G0] == [bits(x) for x in sub_2a4] and [bits(x) for x in dirv] == [bits(x) for x in exp_dir]
              and [bits(x) for x in eff] == [bits(x) for x in exp_eff])
        ok_all &= ok
        rows.append({"scale": scale, "G0": G0, "dir": dirv, "effective": eff, "match": ok})
    out = {"step1_config": {"vtable": s1["vtable"], "desc_gravity": desc_grav, "desc_gravity_bits": [bits(x) for x in desc_grav],
                            "desc_dt_bits": f"{desc_dt:08x}"},
           "step2_subworld": {"plus_298": sub_298, "plus_2a4": sub_2a4, "plus_2a4_bits": [bits(x) for x in sub_2a4],
                              "plus_2b0_bits": f"{sub_2b0:08x}"},
           "step3_state_ctor": rows, "all_match": ok_all,
           "stubs": ["step1: malloc/memset/PLT (r5_camweapon_boom_emu 와 같음)", "step2/3: 명령 구간 실행, 외부 호출 없음"],
           "unverified": ["월드 생성자가 0x7103ac6a20 결과를 월드+0xb8 에 두는 것은 판독(bb_world.c puVar8[0x17])",
                          "생성 뒤 하위 월드+0x2a4 를 바꾸는 코드: 0x7103a00000~0x7103e00000 의 add #0x2a4/str #0x2a4 전수에서 생성 1곳뿐(판독), 범위 밖 미확인"]}
    p = ROOT / "analysis/completion/r6/physics_gravity_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("desc gravity", desc_grav, "sub+0x2a4", sub_2a4, "S rows", [(r["scale"], r["effective"], r["match"]) for r in rows], "->", p)
    return out


if __name__ == "__main__":
    run()
