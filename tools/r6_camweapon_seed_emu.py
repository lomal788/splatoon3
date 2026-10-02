"""r6 camweapon: 매치 시드 G+0xd0 → G+0xc8 이동과 사격장(LobbyVersus) 진입 때의 시드를 원본 명령으로 실행한다.

G = 게임 설정 싱글턴(SplSceneSetting, *0x71058e42f8). 묶음(0x6570 B) 두 개 C8=G+0xc8, D0=G+0xd0.

단계 (모두 원본 명령 실행):
  1) G vt 슬롯33 0x7102af0df0(G, &heap) 0x7102af0df0..0x7102af0f14 → 묶음 생성자 0x7102af0f4c + 묶음 슬롯10 초기화(하위 객체 할당)를
     원본 그대로 실행(끝의 0x7102b3d350(D0+0x30) 호출은 범위 밖).
     대전 설정 V = 묶음+0x6548 의 vtable·RandomSeed0..3 기본값 확인.
  2) 전환 작업 슬롯42 0x7103029330 의 묶음 복사 구간 0x7103029c44..0x7103029cac
     (C8 vt+0x38 = 묶음 복사 0x7102ae5810 ← D0) 를 실행 → C8 V+0xa4..+0xb0.
  3) 탄 관리자 초기화 0x71016e2fd4 의 시드 구간(0x71016e2fd4..0x71016e307c) 실행 → +0x120.
     독립 식 13a+59b+71c+97d (u32 wrap) 과 비트 비교, 무작위 표본 N건.
  4) 같은 함수의 씬 판정·오프라인 시드 구간 0x710302946c..(0x71030295e8 | 0x71030298b0) 실행:
     씬 태그 판정 0x7102b57100(Scene_Versus) 원본 + 태그 이름 이진 탐색 0x71038c4a00 원본,
     태그 표(Tag.Product.100.rstbl) 데이터를 런타임 구조 모양대로 채움.
     LobbyVersus / Vss_Yagara × 온라인 플래그(GameNet+0x195) 0/1.
스텁: operator new 0x710083d2f0(버퍼), memset/memcpy(실제 동작), __cxa_guard_acquire 0x7103e99ef0(1=초기화 실행)/release 0x7103e99f00(가드 바이트 1), 그 밖 PLT(0x7103e99000~0x7103e9e000) 0 반환,
      씬 객체 반환 0x7101323040(가짜 씬: +0x224 = 태그 행 번호).
쓰는 파일: analysis/completion/r6/camweapon_seed_emu.json
"""
import json
import random
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC, END

ROOT = Path(__file__).resolve().parents[2]
BIG = 0x40000000
GPTR = 0x71058E42F8
RNG_PTR_VAR = 0x7105997950


def w64(e, a, v): e.mu.mem_write(a, struct.pack("<Q", v))
def r64(e, a): return struct.unpack("<Q", e.mu.mem_read(a, 8))[0]
def w32(e, a, v): e.mu.mem_write(a, struct.pack("<I", v & 0xFFFFFFFF))
def r32(e, a): return struct.unpack("<I", e.mu.mem_read(a, 4))[0]


class Emu(UC):
    def __init__(self, extra=None):
        super().__init__()
        self.mu.mem_map(BIG, 0x4000000)
        self.heap_next = BIG + 0x1000
        self.log = []
        self.extra = extra or {}
        self.mu.hook_add(UC_HOOK_CODE, self._plt, begin=0x710083D2F0, end=0x710083D2F0)
        self.mu.hook_add(UC_HOOK_CODE, self._plt, begin=0x7101323040, end=0x7101323040)
        self.mu.hook_add(UC_HOOK_CODE, self._plt, begin=0x7103E99000, end=0x7103E9E000)

    def _plt(self, mu, addr, size, ud):
        x0, x1, x2 = (mu.reg_read(r) for r in (UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2))
        if addr in self.extra:
            val = self.extra[addr](x0, x1, x2)
        elif addr == 0x710083D2F0:
            val = self.alloc(max(x0, 0x10)); self.log.append("new")
        elif addr == 0x7103E99F10:
            mu.mem_write(x0, bytes([x1 & 0xFF]) * x2); val = x0; self.log.append("memset")
        elif addr == 0x7103E99F20:
            if x2:
                mu.mem_write(x0, bytes(mu.mem_read(x1, x2)))
            val = x0; self.log.append("memcpy")
        elif addr == 0x7103E99EF0:
            val = 1; self.log.append("guard_acquire")
        elif addr == 0x7103E99F00:
            mu.mem_write(x0, b""); val = 0; self.log.append("guard_release")
        elif 0x7103E99000 <= addr < 0x7103E9E000:
            val = 0; self.log.append(f"plt0:{addr:#x}")
        else:
            return
        mu.reg_write(UC_ARM64_REG_X0, val)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    def run(self, start, stop, regs):
        mu = self.mu
        for k, v in regs.items():
            mu.reg_write(k, v)
        if UC_ARM64_REG_SP not in regs:
            mu.reg_write(UC_ARM64_REG_SP, 0x10000000 + 0xE0000)
        mu.reg_write(UC_ARM64_REG_LR, END)
        mu.emu_start(start, stop, count=5_000_000)
        return mu.reg_read(UC_ARM64_REG_PC)


def build_G(e):
    w64(e, 0x71059975C0, 0)
    G = e.alloc(0x138)
    w64(e, GPTR, G)
    hp = e.alloc(8)
    pc = e.run(0x7102AF0DF0, 0x7102AF0F14, {UC_ARM64_REG_X0: G, UC_ARM64_REG_X1: hp})
    assert pc == 0x7102AF0F14, hex(pc)
    return G, r64(e, G + 0xC8), r64(e, G + 0xD0)


def seeds(e, bundle):
    v = r64(e, bundle + 0x6548)
    return [r32(e, v + o) for o in (0xA4, 0xA8, 0xAC, 0xB0)]


def set_seeds(e, bundle, s):
    v = r64(e, bundle + 0x6548)
    for o, x in zip((0xA4, 0xA8, 0xAC, 0xB0), s):
        w32(e, v + o, x)


def copy_block(e):
    pc = e.run(0x7103029C44, 0x7103029CAC, {UC_ARM64_REG_X25: GPTR})
    assert pc == 0x7103029CAC, hex(pc)


def bullet_init(e):
    mgr = e.alloc(0x400)
    pc = e.run(0x71016E2FD4, 0x71016E307C, {UC_ARM64_REG_X0: mgr, UC_ARM64_REG_X1: 0})
    assert pc == 0x71016E307C, hex(pc)
    return r32(e, mgr + 0x120), [r32(e, mgr + o) for o in (0x124, 0x128, 0x12C, 0x130)]


def indep(s):
    a, b, c, d = s
    return (13 * a + 59 * b + 71 * c + 97 * d) & 0xFFFFFFFF


def tag_data():
    import subprocess
    out = subprocess.run([sys.executable, str(ROOT / "web/tools/spl_data.py"), "cat",
                          str(ROOT / "extracted/romfs/RSDB/Tag.Product.100.rstbl.byml.zs")],
                         capture_output=True, env={"PYTHONIOENCODING": "utf-8", "SYSTEMROOT": "C:\\Windows"})
    d = json.loads(out.stdout.decode("utf-8"))
    P = d["PathList"]
    rows = [P[i:i + 3] for i in range(0, len(P), 3)]
    return rows, d["TagList"], bytes.fromhex(d["BitTable"]["__binary"])


def setup_tags(e, rows, tags, bits):
    names = e.alloc(8 * len(tags))
    for i, t in enumerate(tags):
        s = e.alloc(len(t) + 1); e.mu.mem_write(s, t.encode() + b"\0")
        w64(e, names + 8 * i, s)
    holder = e.alloc(0x200)
    obj30 = e.alloc(0x200)
    w64(e, holder + 0x30, obj30)
    w32(e, holder + 0xF4, 0)
    w64(e, obj30 + 0x50 + 0x18, names)
    w32(e, obj30 + 0x50 + 0x10, len(tags))
    w64(e, 0x71059A9D10, holder)
    bt = e.alloc(len(bits)); e.mu.mem_write(bt, bits)
    X = e.alloc(0x100); T = e.alloc(0x100)
    w64(e, X + 0x20, T)
    w64(e, T + 0x68, 1)
    w32(e, T + 0x60, len(tags))
    w64(e, T + 0x70, bt)
    w64(e, 0x710599B420, X)


def scene_case(rows, tags, bits, scene, online, rng_state):
    e = Emu()
    G, C8, D0 = build_G(e)
    setup_tags(e, rows, tags, bits)
    row = next(i for i, r in enumerate(rows) if r[0] == "Work/Scene/" and r[1] == scene)
    sc = e.alloc(0x400)
    w32(e, sc + 0x224, row)
    e.extra[0x7101323040] = lambda a, b, c: sc
    gn = e.alloc(0x400); e.mu.mem_write(gn + 0x195, bytes([online]))
    gnvar = e.alloc(8); w64(e, gnvar, gn)
    rs = e.alloc(16)
    for i, v in enumerate(rng_state):
        w32(e, rs + 4 * i, v)
    w64(e, RNG_PTR_VAR, rs)
    before = seeds(e, D0)
    w64(e, 0x71058E90F0, 0xFFFFFFFF)
    w64(e, 0x71058E90F8, 0x71048B3981)
    mu = e.mu
    for k, v in {UC_ARM64_REG_X23: gnvar, UC_ARM64_REG_X25: GPTR, UC_ARM64_REG_X20: D0, UC_ARM64_REG_X19: e.alloc(0x400),
                 UC_ARM64_REG_X22: D0 + 0x6508}.items():
        mu.reg_write(k, v)
    stop_set = (0x71030295E8, 0x71030298B0, 0x7103029638)
    mu.reg_write(UC_ARM64_REG_SP, 0x10000000 + 0xE0000)
    mu.reg_write(UC_ARM64_REG_LR, END)
    hit = []

    def stopper(mu, addr, size, ud):
        if addr in stop_set:
            hit.append(addr); mu.emu_stop()
    h = mu.hook_add(UC_HOOK_CODE, stopper, begin=0x7103029400, end=0x71030299FF)
    mu.emu_start(0x710302946C, END, count=2_000_000)
    mu.hook_del(h)
    tagcol = r32(e, 0x71058E90F0)
    is_versus = (bits[(row * len(tags) + tags.index("Scene_Versus")) >> 3] >> ((row * len(tags) + tags.index("Scene_Versus")) & 7)) & 1
    after = seeds(e, D0)
    return {
        "scene": scene, "tag_row": row, "online_flag": online,
        "stop_pc": hex(hit[0]) if hit else None,
        "tag_col_from_lookup": tagcol, "tag_col_data": tags.index("Scene_Versus"),
        "scene_versus_bit_data": is_versus,
        "D0_seeds_before": before, "D0_seeds_after": after, "rng_state": list(rng_state),
        "seeds_written": after != before,
        "seeds_eq_rng_state": after == list(rng_state),
    }


def main():
    out = {}
    e = Emu()
    G, C8, D0 = build_G(e)
    vC8, vD0 = r64(e, C8 + 0x6548), r64(e, D0 + 0x6548)
    out["build"] = {
        "C8_vtable": hex(r64(e, C8)), "D0_vtable": hex(r64(e, D0)),
        "C8_V_vtable": hex(r64(e, vC8)), "D0_V_vtable": hex(r64(e, vD0)),
        "C8_V_seeds_default": seeds(e, C8), "D0_V_seeds_default": seeds(e, D0),
        "C8_V_time": r32(e, vC8 + 0xA0), "distinct_objects": C8 != D0 and vC8 != vD0,
        "stub_log": sorted(set(e.log)),
    }
    m120, ad = bullet_init(e)
    out["bullet_init_default"] = {"plus_120": m120, "a_d": ad, "independent": indep(seeds(e, C8))}
    rnd = random.Random(20261003)
    rows = []
    cases = [[1, 0, 0, 0], [1, 2, 3, 4], [0, 0, 0, 0], [0xFFFFFFFF] * 4] + [[rnd.getrandbits(32) for _ in range(4)] for _ in range(60)]
    for s in cases:
        e = Emu()
        G, C8, D0 = build_G(e)
        set_seeds(e, D0, s)
        c8_before = seeds(e, C8)
        copy_block(e)
        c8_after = seeds(e, C8)
        m120, ad = bullet_init(e)
        rows.append({"D0_seeds": s, "C8_before": c8_before, "C8_after": c8_after, "plus_120": m120,
                     "independent": indep(s), "match": c8_after == s and ad == s and m120 == indep(s)})
    out["copy_cases"] = rows
    out["copy_all_match"] = all(r["match"] for r in rows)
    rows_t, tags, bits = tag_data()
    sc = []
    for scene in ("LobbyVersus", "Vss_Yagara", "Plaza"):
        for online in (0, 1):
            sc.append(scene_case(rows_t, tags, bits, scene, online, [0x12345678, 0x9ABCDEF0, 0x0F1E2D3C, 0x4B5A6978]))
    out["scene_cases"] = sc
    p = ROOT / "analysis/completion/r6/camweapon_seed_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("build", out["build"])
    print("bullet default", out["bullet_init_default"])
    print(f"copy {sum(r['match'] for r in rows)}/{len(rows)}")
    for r in sc:
        print(r)


if __name__ == "__main__":
    main()
