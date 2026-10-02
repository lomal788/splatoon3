"""[r6 physics] 평상시 Phive -> 게임 위치(본체+0x10) write-back 원본 실행.

경로(판독):
  액터 단계1 작업 -> 액터 vt+0x2e0 0x7100f76f78
  -> (컴포넌트[0]/[3]/[0x23] 없음) 물리 컴포넌트(컴포넌트[10])+0x18 몸체 집합 -> 0x7103a13a24(집합, &M, &v, &w)
     -> 주 몸체 0x7103a102f0(집합, 0) = 캐릭터 몸체(ctrl+0x18, 생성 0x7103a80a60 최종 vtable 0x71057468d8, IsA 0x7103a81fdc→0x7103a820c4)
     -> S+0x210 < 1 이면 M = S+0x244.., 아니면 M = 몸체+0xd8.. (3x4 행 우선, 이동 +0xc/+0x1c/+0x2c)
  -> 액터+0x4e0 functor slot0(&M). 플레이어는 0x7102456e90 이 vtable 0x71056337c0(slot0 0x71024d26f8, this = 본체)을 설치
     -> M 회전 = 본체 회전(본체+0x1c.. 열 우선), 본체+0xfa0 == 0 이면 M 이동 -= r*up
        (r = ColGround 캡슐+0xf0, up = 본체+0x28/+0x2c/+0x30)
  -> 액터+0x28c..+0x2b8 = M (0x7100f77458~)
  -> 플레이어 슬롯19 0x7102483134 첫머리(0x7102483278~0x71024832d8):
     본체+0x40 = 이전 본체+0x10, 본체+0x10 = 액터+0x28c, 본체+0x1c.. = 액터 회전(전치)
실행 1: 0x7100f76f78 를 0x7100f77730(행동 슬롯19 디스패치 직전)까지 원본 실행.
실행 2: 0x7102483278~0x71024832dc 명령 구간을 레지스터만 맞춰 원본 실행.
스텁: nn::os TLS(PLT, 0 반환), __cxa_guard_*(PLT, 0 반환 -> 정적 typeinfo 포인터를 그대로 비교), 캡슐 IsA(vt slot0) -> 1.
그 밖 main 함수 호출은 스텁(0 반환)으로 기록하고 결과에 남긴다.
결과: analysis/completion/r6/physics_writeback_emu.json
"""
import json
import random
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.arm64_const import (UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X19, UC_ARM64_REG_X20,  # noqa: E402
                                 UC_ARM64_REG_X23, UC_ARM64_REG_X28, UC_ARM64_REG_X29, UC_ARM64_REG_SP,
                                 UC_ARM64_REG_LR, UC_ARM64_REG_PC)
from r5_gfx_char_uc import GUC, PLT_LO, PLT_HI  # noqa: E402
from network_uc import BASE, STUB, STACK  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F76 = 0x7100f76f78
STOP = 0x7100f77730
ALLOW = [(0x7100f76f78, 0x7100f76f78 + 3784), (0x7103a13a24, 0x7103a13a24 + 1580),
         (0x7103a102f0, 0x7103a102f0 + 292), (0x7103a81fdc, 0x7103a81fe4), (0x7103a820c4, 0x7103a822b4),
         (0x71024d26f8, 0x71024d26f8 + 332)]
TRUE_STUB = STUB + 0x900


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def bits(x):
    return struct.pack("<f", x).hex()


class H(GUC):
    def __init__(self):
        super().__init__()
        self.stubbed = []
        self.range_mode = False
        self.mu.hook_add(UC_HOOK_CODE, self._gen)

    def _gen(self, mu, a, s, u):
        if a == TRUE_STUB:
            mu.reg_write(UC_ARM64_REG_X0, 1)
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return
        if a < BASE or PLT_LO <= a < PLT_HI or self.range_mode:
            return
        if any(lo <= a < hi for lo, hi in ALLOW):
            return
        self.stubbed.append(hex(a))
        mu.reg_write(UC_ARM64_REG_X0, 0)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))


def run(cases=1024, seed=20261003):
    h = H()
    mu = h.mu
    mu.mem_write(TRUE_STUB, struct.pack("<I", 0xD65F03C0))
    A = h.alloc
    actor = A(0x600); comps = A(0x40 * 8); phys = A(0x40); bset = A(0x140); ent = A(0x20)
    W = A(0x20); ctrl = A(0x40); body = A(0x400); X = A(0x20); Xc = A(0x40); S = A(0x2b0)
    hon = A(0xb000); pc = A(0x60); comp_sh = A(0x100); comp_arr = A(0x100); cap = A(0x100); capvt = A(0x20)
    vel_out = A(0x10); scratch20 = A(0x80); scratch19 = A(0x40)
    q = h.wq

    def u32(a, v):
        mu.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))

    q(actor + 0x208, comps); u32(actor + 0x200, 0x40)
    q(comps + 10 * 8, phys); q(phys + 0x18, bset)
    q(actor + 0x4e0, 0x71056337c0); q(actor + 0x4e8, hon)
    mu.mem_write(bset + 0x108, b"\0"); u32(bset + 0xe8, 1); q(bset + 0xf0, ent)
    mu.mem_write(ent, struct.pack("<iiiiB", 0, -1, -1, -1, 1))
    q(bset + 0x10, W); q(W + 8, ctrl); q(ctrl + 0x18, body)
    q(body, 0x71057468d8); q(body + 0x88, 4)
    q(body + 0x2f0, X); q(X + 8, Xc); q(Xc + 0x20, S)
    q(hon + 0xa690, pc); q(pc + 0x38, comp_sh); u32(pc + 0x40, 0)
    u32(comp_sh + 0xb8, 2); q(comp_sh + 0xc0, comp_arr); q(comp_arr, cap); q(cap, capvt); q(capvt, TRUE_STUB)
    q(hon + 8, actor)
    rng = random.Random(seed)
    mism, samples = [], []
    for ci in range(cases):
        r = f32(rng.choice([0.6, 1.0, 0.39, 0.3]))
        h.f32(cap + 0xf0, r)
        alpha = f32(rng.choice([1.0, 1.0, 1.5, 0.25, 0.0]))
        h.f32(S + 0x210, alpha)
        flag_fa0 = 1 if rng.random() < 0.15 else 0
        mu.mem_write(hon + 0xfa0, bytes([flag_fa0]))
        mu.mem_write(S + 0x274, bytes([1 if rng.random() < 0.2 else 0]))
        Mb = [f32(rng.uniform(-1, 1)) for _ in range(12)]
        for k in (3, 7, 11):
            Mb[k] = f32(rng.uniform(-200, 200))
        Ms = [f32(rng.uniform(-1, 1)) for _ in range(12)]
        for k in range(12):
            h.f32(body + 0xd8 + 4 * k, Mb[k])
            h.f32(S + 0x244 + 4 * k, Ms[k])
        for k in range(6):
            h.f32(body + 0x138 + 4 * k, f32(rng.uniform(-9, 9)))
            h.f32(S + 0x278 + 4 * k, f32(rng.uniform(-9, 9)))
        R = [f32(rng.uniform(-1, 1)) for _ in range(9)]
        for k in range(9):
            h.f32(hon + 0x1c + 4 * k, R[k])
        old = [f32(rng.uniform(-50, 50)) for _ in range(3)]
        for k in range(3):
            h.f32(hon + 0x10 + 4 * k, old[k])
        for off in range(0x28c, 0x2bc, 4):
            h.f32(actor + off, 0.0)
        h.range_mode = False
        mu.reg_write(UC_ARM64_REG_X0, actor); mu.reg_write(UC_ARM64_REG_X1, vel_out)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000); mu.reg_write(UC_ARM64_REG_X29, 0)
        mu.reg_write(UC_ARM64_REG_LR, STOP)
        mu.emu_start(F76, STOP, count=500000)
        got_actor = [h.rf32(actor + off) for off in range(0x28c, 0x2bc, 4)]
        M = list(Ms) if alpha < 1.0 else list(Mb)
        M[0], M[1], M[2] = R[0], R[3], R[6]
        M[4], M[5], M[6] = R[1], R[4], R[7]
        M[8], M[9], M[10] = R[2], R[5], R[8]
        if not flag_fa0:
            M[3] = f32(M[3] - f32(r * R[3]))
            M[7] = f32(M[7] - f32(r * R[4]))
            M[11] = f32(M[11] - f32(r * R[5]))
        exp_actor = [M[3], M[7], M[11], M[0], M[1], M[2], M[4], M[5], M[6], M[8], M[9], M[10]]
        h.range_mode = True
        mu.reg_write(UC_ARM64_REG_X23, hon + 0x10); mu.reg_write(UC_ARM64_REG_X28, hon)
        mu.reg_write(UC_ARM64_REG_X20, scratch20); mu.reg_write(UC_ARM64_REG_X19, scratch19)
        mu.emu_start(0x7102483278, 0x71024832dc, count=100)
        got_hon = [h.rf32(hon + 0x10 + 4 * k) for k in range(12)] + [h.rf32(hon + 0x40 + 4 * k) for k in range(3)]
        exp_hon = [got_actor[0], got_actor[1], got_actor[2],
                   got_actor[3], got_actor[6], got_actor[9], got_actor[4], got_actor[7], got_actor[10],
                   got_actor[5], got_actor[8], got_actor[11]] + old
        ok = ([bits(x) for x in got_actor] == [bits(x) for x in exp_actor]
              and [bits(x) for x in got_hon] == [bits(x) for x in exp_hon])
        row = {"case": ci, "r": r, "S210": alpha, "fa0": flag_fa0, "body_t": [Mb[3], Mb[7], Mb[11]],
               "up": [R[3], R[4], R[5]], "actor28c": got_actor[:3], "hon10": got_hon[:3], "expected": exp_actor[:3]}
        if ci < 4:
            samples.append(row)
        if not ok:
            row.update(got_actor=got_actor, exp_actor=exp_actor, got_hon=got_hon, exp_hon=exp_hon)
            mism.append(row)
    stub_set = sorted(set(h.stubbed))
    plt = sorted(set(h.plt_stubbed))
    out = {"functions": ["0x7100f76f78 (-> 0x7100f77730)", "0x7103a13a24", "0x7103a102f0", "0x7103a81fdc→0x7103a820c4 (IsA, 몸체 vtable 0x71057468d8)",
                         "0x71024d26f8", "0x7102483278~0x71024832dc"],
           "cases": cases, "passed": cases - len(mism), "mismatches": mism[:10], "samples": samples,
           "stubbed_main_calls": stub_set, "plt_stubbed": plt,
           "stubs": ["캡슐 IsA(vt slot0) -> 1", "PLT: nn::os TLS, __cxa_guard_* 0 반환"],
           "unverified": ["몸체 집합 생성이 주 칸 0 을 캐릭터 몸체로 두는 것은 판독(0x7103a08814~0x7103a08870)",
                          "functor 설치 0x7102456e90 의 호출 시점은 미실행",
                          "Havok 스텝이 몸체+0xd8 을 바꾸는 과정(솔버)"]}
    p = ROOT / "analysis/completion/r6/physics_writeback_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"write-back: {out['passed']}/{cases} 비트 일치, 스텁된 main 호출 {stub_set}, PLT {plt} -> {p}")
    return out


if __name__ == "__main__":
    run()
