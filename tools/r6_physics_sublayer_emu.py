"""[r6 physics] 플레이어 몸체 하위 레이어(SubLayer) 선택 원본 실행 — PlayerCollision 형상 갱신 0x71024f5dd8 안 0x71024f5fc4~0x71024f60f8.

판독:
  sp = 특수 번호(본체+0x588 쌍이 같으면 본체+0x658, 다르면 +0x65c; 쌍 없음 0)
  PC+0x1c9 = (sp == 0x12) | (sp == 0x1a) | (k == 0xf)   (k = 본체+0x926c ? 0x16 : (+0x678 쌍 또는 +0x588/+0x598 쌍이 같으면 본체+0x65c, 아니면 0))
  v = 액터(본체+8)+0x7b9 ? 12 : 7
  if sp != 0x1a && 액터+0x7b9 == 0:
      if t < 1.1920929e-07 || [본체+0xa7c0](PlayerCoopZombie)+0xeec: v = 3 (SplPlayerHuman)
      elif ([본체+0xa880](PlayerDokanWarp)+0x30 - 1) < 2 (부호 없음): v = 6 (SplPlayerSquid_NoThroughFence)
      else: v = flag ? 5 (SplPlayerSquid_Invisible) : 4 (SplPlayerSquid_Visible)
  [PC+0xe3b0]+0x18 몸체 집합의 모든 몸체에 setSubLayer(v) (functor 0x7105634078 slot0 0x71024fc2d0 → 0x7103af394c),
  PC+0x58 몸체에 setSubLayer(8)
실행: 명령 구간을 원본 그대로 실행. 스텁: 몸체 집합 순회 0x71012ec970(functor+8 값 기록), setSubLayer 0x7103af394c(인자 기록),
      functor 해제 slot3(빈 반환).
결과: analysis/completion/r6/physics_sublayer_emu.json
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
                                 UC_ARM64_REG_X21, UC_ARM64_REG_X24, UC_ARM64_REG_S8, UC_ARM64_REG_SP,
                                 UC_ARM64_REG_LR, UC_ARM64_REG_PC)
from network_uc import UC, STACK  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NAMES = {3: "SplPlayerHuman", 4: "SplPlayerSquid_Visible", 5: "SplPlayerSquid_Invisible",
         6: "SplPlayerSquid_NoThroughFence", 7: "SplPlayerChariot", 8: "SplPlayerChariotShield", 12: "Enemy"}


def run(cases=4000, seed=20261003):
    e = UC()
    mu = e.mu
    q = lambda a, v: mu.mem_write(a, struct.pack("<Q", v))
    u32 = lambda a, v: mu.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))
    cap = {}

    def hook(m, a, s, d):
        if a == 0x71012ec970:
            cap["set"] = m.reg_read(UC_ARM64_REG_X0)
            cap["v"] = struct.unpack("<I", bytes(m.mem_read(m.reg_read(UC_ARM64_REG_X1) + 8, 4)))[0]
        elif a == 0x7103af394c:
            cap.setdefault("calls", []).append((m.reg_read(UC_ARM64_REG_X0), m.reg_read(UC_ARM64_REG_X1) & 0xFFFFFFFF))
        elif a == 0x71012eacc8:
            pass
        else:
            return
        m.reg_write(UC_ARM64_REG_PC, m.reg_read(UC_ARM64_REG_LR))
    for a in (0x71012ec970, 0x7103af394c, 0x71012eacc8):
        mu.hook_add(UC_HOOK_CODE, hook, begin=a, end=a)
    pc = e.alloc(0xe400); beh = e.alloc(0x200); hon = e.alloc(0xb000); actor = e.alloc(0x800)
    zombie = e.alloc(0x1000); dokan = e.alloc(0x100); comp = e.alloc(0x40); bset = e.alloc(0x20); b58 = e.alloc(0x10)
    scratch = e.alloc(0x10)
    q(pc + 0xe3a8, beh); q(beh + 0x108, hon); q(hon + 8, actor)
    q(hon + 0xa7c0, zombie); q(hon + 0xa880, dokan)
    q(pc + 0xe3b0, comp); q(comp + 0x18, bset); q(pc + 0x58, b58)
    rng = random.Random(seed)
    mism, samples, hist = [], [], {}
    for ci in range(cases):
        cap.clear()
        pair_on = rng.random() < 0.5
        same = rng.random() < 0.5
        q(hon + 0x588, 0x1111 if pair_on else 0)
        q(hon + 0x590, 0x1111 if same else 0x2222)
        q(hon + 0x598, 0x1111 if rng.random() < 0.5 else 0x3333)
        sp658 = rng.choice([0, 0x12, 0x1a, 0xf, 0x18]); sp65c = rng.choice([0, 0x12, 0x1a, 0xf, 0x1c])
        u32(hon + 0x658, sp658); u32(hon + 0x65c, sp65c)
        b926c = 1 if rng.random() < 0.1 else 0
        mu.mem_write(hon + 0x926c, bytes([b926c]))
        p678 = rng.random() < 0.3
        q(hon + 0x678, 0x4444 if p678 else 0); q(hon + 0x688, 0x4444 if rng.random() < 0.5 else 0x5555)
        a7b9 = 1 if rng.random() < 0.15 else 0
        mu.mem_write(actor + 0x7b9, bytes([a7b9]))
        t = rng.choice([0.0, 1e-8, 1.1920929e-07, 0.5, 1.0, 0.99, 1e-7])
        zeec = 1 if rng.random() < 0.15 else 0
        mu.mem_write(zombie + 0xeec, bytes([zeec]))
        dk = rng.choice([0, 1, 2, 3, 0xFFFFFFFF])
        u32(dokan + 0x30, dk)
        flag = rng.randrange(2)
        mu.mem_write(pc + 0x1c9, bytes([rng.randrange(2)]))
        mu.reg_write(UC_ARM64_REG_X19, pc); mu.reg_write(UC_ARM64_REG_X24, pc + 0xe368)
        mu.reg_write(UC_ARM64_REG_X20, flag); mu.reg_write(UC_ARM64_REG_X21, scratch)
        mu.reg_write(UC_ARM64_REG_S8, struct.unpack("<I", struct.pack("<f", t))[0])
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        mu.emu_start(0x71024f5fc4, 0x71024f60f8, count=2000)
        # 재구현
        if pair_on:
            sp = sp658 if same else sp65c
        else:
            sp = 0
        if b926c:
            k = 0x16
        elif p678 and True:
            k = None
        else:
            k = None
        p678_eq = p678 and (0x4444 == struct.unpack("<Q", bytes(mu.mem_read(hon + 0x688, 8)))[0])
        p588_eq = pair_on and (struct.unpack("<Q", bytes(mu.mem_read(hon + 0x598, 8)))[0] == 0x1111)
        if not b926c:
            k = sp65c if (p678_eq or p588_eq) else 0
        f1c9 = int(sp == 0x12) | int(sp == 0x1a) | int(k == 0xf)
        v = 12 if a7b9 else 7
        if sp != 0x1a and a7b9 == 0:
            tf = struct.unpack("<f", struct.pack("<f", t))[0]
            if tf < struct.unpack("<f", struct.pack("<f", 1.1920929e-07))[0] or zeec:
                v = 3
            elif ((dk - 1) & 0xFFFFFFFF) < 2:
                v = 6
            else:
                v = 5 if flag else 4
        got_v = cap.get("v"); got_calls = cap.get("calls", [])
        got_1c9 = mu.mem_read(pc + 0x1c9, 1)[0]
        ok = got_v == v and got_calls == [(b58, 8)] and cap.get("set") == bset and got_1c9 == f1c9
        hist[NAMES.get(v, v)] = hist.get(NAMES.get(v, v), 0) + 1
        row = {"case": ci, "sp": sp, "a7b9": a7b9, "t": t, "zombie_eec": zeec, "dokan30": dk, "flag": flag,
               "expected": v, "original": got_v, "pc58": got_calls, "pc1c9": [got_1c9, f1c9]}
        if ci < 5:
            samples.append(row)
        if not ok:
            mism.append(row)
    out = {"range": "0x71024f5fc4~0x71024f60f8 (함수 0x71024f5dd8)", "cases": cases, "passed": cases - len(mism),
           "histogram": hist, "mismatches": mism[:10], "samples": samples,
           "stubs": ["몸체 집합 순회 0x71012ec970(functor+8 값만 기록)", "setSubLayer 0x7103af394c(인자 기록)", "functor 해제 0x71012eacc8"],
           "unverified": ["setSubLayer 0x7103af394c 가 대기 버퍼(+0x90, 플래그 bit13)를 거쳐 월드 명령 처리 0x7103b07b8c 에서 F+8 bits6..11 에 쓰는 과정은 판독",
                          "flag(4번째 인자) 출처: 메인 계산 move_full_main.c 7131~7163행(본체+0x7a0·+0x789·액터 컴포넌트 상태)"]}
    p = ROOT / "analysis/completion/r6/physics_sublayer_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"sublayer select: {out['passed']}/{cases} 일치 {hist} -> {p}")
    return out


if __name__ == "__main__":
    run()
