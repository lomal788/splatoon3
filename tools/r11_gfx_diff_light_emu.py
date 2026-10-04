"""r11 gfx-diff 광원: 주광 경로 4함수를 unicorn 으로 원본 실행한다.
- 0x7102b607c4(t, A, DL, B): RenderingDay MainLight Color/Intens -> DL+0x128 RGBA, +0x1a0
- 0x7102b60ea0(t, A, DL, B): Latitude/Longitude -> DL+0x1c0 방향 (sinf/cosf = SDK 원본)
- 0x71035d6500(DL, M, view): agl DirectionalLight 뷰별 갱신 -> +0x1f8[view], +0x208[view]
- 0x71036b35c0(gsys, view): Env UBO(gsys_environment 512 B) 기록. 객체는 DirectionalLight 1개 + agl Fog 2개만 둔다.
스텁: __cxa_guard_acquire(0 반환)/release, 객체 RTTI 검사 vtable+0x48(1 반환), 뷰 레코드 vtable+0x18/+0x30(즉시 반환),
RenderingDay 컨테이너 vtable+0x70(고정 포인터 반환). 출력: web/games/splatoon3/tests/fixtures/r11_gfx_diff_light_native.json
사용: PY web/tools/r11_gfx_diff_light_emu.py
"""
import json, random, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_MEM_UNMAPPED
from unicorn.arm64_const import *
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_player_libm_emu import symbols
IMG = ROOT / "extracted/exefs/main.reloc.img"; SDK = ROOT / "extracted/exefs/sdk.img"
BASE, SBASE = 0x7100000000, 0x7400000000
STACK, HEAP, RET, STUB = 0x10000000, 0x20000000, 0x30000000, 0x31000000
RET_W, MOV1, MOV0 = 0xD65F03C0, 0x52800020, 0x52800000
f = lambda v: struct.unpack('<f', struct.pack('<f', v))[0]
fb = lambda v: struct.unpack('<I', struct.pack('<f', v))[0]

class Emu:
    def __init__(self):
        img, sdk = IMG.read_bytes(), SDK.read_bytes()
        mu = self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF); mu.mem_write(BASE, img)
        mu.mem_map(SBASE, (len(sdk) + 0xFFFF) & ~0xFFFF); mu.mem_write(SBASE, sdk)
        mu.mem_map(STACK, 0x100000); mu.mem_map(HEAP, 0x40000); mu.mem_map(RET, 0x1000); mu.mem_map(STUB, 0x1000)
        mu.mem_write(RET, struct.pack("<I", RET_W))
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        sym = symbols(sdk)
        for got, name in ((0x710576fdc8, "sqrtf"), (0x710576ff38, "cosf"), (0x710576ff40, "sinf")):
            mu.mem_write(got, struct.pack("<Q", SBASE + sym[name][0]))
        mu.mem_write(0x7103e99ef0, struct.pack("<II", MOV0, RET_W))
        mu.mem_write(0x7103e99f00, struct.pack("<I", RET_W))
        self.ret1 = STUB; mu.mem_write(STUB, struct.pack("<II", MOV1, RET_W))
        self.ret0 = STUB + 8; mu.mem_write(STUB + 8, struct.pack("<II", MOV0, RET_W))
        self.faults = []
        mu.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.faults.append(hex(addr)) and False)

    def w(self, a, fmt, *v): self.mu.mem_write(a, struct.pack("<" + fmt, *v))
    def rf(self, a, n): return list(struct.unpack("<%df" % n, bytes(self.mu.mem_read(a, 4 * n))))
    def rb(self, a, n): return list(struct.unpack("<%dI" % n, bytes(self.mu.mem_read(a, 4 * n))))

    def call(self, fn, x=(), s0=None):
        mu = self.mu
        for i, v in enumerate(x): mu.reg_write(UC_ARM64_REG_X0 + i, v)
        if s0 is not None: mu.reg_write(UC_ARM64_REG_Q0, fb(s0))
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000); mu.reg_write(UC_ARM64_REG_LR, RET)
        mu.emu_start(fn, RET, count=5000000)

    def renderingday(self, base, color, intens, lat, lon, stub_slot):
        """컨테이너(vtable+0x70 -> 고정 포인터) + MainLight 블록(Color +0x30, Intens +0x44, Lat +0x48, Lon +0x4c, 설정 플래그 +0x51..+0x54)."""
        obj, vt, cont, blk = base, base + 0x100, base + 0x200, base + 0x300
        self.w(stub_slot, "IIQ", 0x58000040, RET_W, cont)
        self.w(obj, "Q", vt); self.w(vt + 0x70, "Q", stub_slot)
        self.w(cont + 0x48, "Q", blk); self.w(cont + 0x58, "B", 1)
        self.w(blk + 0x30, "4f", *color); self.w(blk + 0x44, "3f", intens, lat, lon)
        self.w(blk + 0x51, "4B", 1, 1, 1, 1)
        return obj

    def mainlight(self, color, intens, lat, lon, t=1.0):
        self.mu.mem_write(HEAP, b"\0" * 0x4000)
        a = self.renderingday(HEAP, color, intens, lat, lon, STUB + 0x40)
        b = self.renderingday(HEAP + 0x800, color, intens, lat, lon, STUB + 0x60)
        dl = HEAP + 0x2000
        self.call(0x7102b607c4, (a, dl, b), s0=t)
        self.call(0x7102b60ea0, (a, dl, b), s0=t)
        return {"diffuse": self.rf(dl + 0x128, 4), "diffuseBits": self.rb(dl + 0x128, 4), "intensity": self.rf(dl + 0x1a0, 1)[0],
                "direction": self.rf(dl + 0x1c0, 3), "directionBits": self.rb(dl + 0x1c0, 3)}

    def dl_view(self, dl, d, view_coord, m):
        self.w(dl + 0x1c0, "3f", *d); self.w(dl + 0x1e8, "B", 1 if view_coord else 0)
        a1, a2, mat = dl + 0x400, dl + 0x440, dl + 0x480
        self.w(dl + 0x1f0, "I", 1); self.w(dl + 0x1f8, "Q", a1); self.w(dl + 0x200, "I", 1); self.w(dl + 0x208, "Q", a2)
        self.w(mat, "24f", *m)
        self.call(0x71035d6500, (dl, mat, 0))
        return self.rf(a1, 3), self.rf(a2, 3), self.rb(a2, 3)

    def env_ubo(self, light, fogs):
        """light: {diffuse RGBA, second RGBA, intensity, direction, viewCoord, matrix}; fogs: [{start,end,damp,color,dir}] 2개."""
        mu = self.mu
        mu.mem_write(HEAP, b"\0" * 0x40000)
        gs, mgr, env, idx, objs, rec, vtrec, tab, data = (HEAP + o for o in (0x0, 0x800, 0x1000, 0x1100, 0x1200, 0x1400, 0x1600, 0x1800, 0x2000))
        vtobj, tids = HEAP + 0x2400, HEAP + 0x2500
        dl, fog0, fog1 = HEAP + 0x3000, HEAP + 0x4000, HEAP + 0x5000
        self.w(gs + 0x510, "Q", mgr); self.w(gs + 0x570, "I", 1); self.w(gs + 0x578, "Q", rec)
        self.w(mgr + 0x1e8, "I", 1); self.w(mgr + 0x1f0, "Q", mgr + 0x100); self.w(mgr + 0x100, "Q", env)
        self.w(env + 0x18, "I", 8); self.w(env + 0x20, "Q", idx); self.w(env + 0x30, "Q", objs)
        for gaddr, tid in ((0x7105999168, 0), (0x7105999170, 1), (0x7105999178, 2), (0x7105999180, 3), (0x7105999188, 4)):
            self.w(tids + 4 * tid, "i", tid); self.w(gaddr, "Q", tids + 4 * tid)
        self.w(idx, "8H", 0, 2, 0, 0, 0, 0, 2, 1)
        self.w(objs, "3Q", fog0, fog1, dl)
        self.w(vtobj + 0x48, "Q", self.ret1)
        rows = [l.split("\t") for l in (ROOT / "analysis/r6_gfx_stage/envubo_layout.tsv").read_text().splitlines()[1:] if not l.startswith("#")]
        for r in rows:
            i, kind, off = int(r[0]), int(r[1]), int(r[4], 16)
            self.w(tab + 12 * i + 4, "H", off); self.w(tab + 12 * i + 8, "B", kind)
        self.w(rec, "Q", vtrec); self.w(rec + 0x10, "Q", rec + 0x100); self.w(rec + 0x100, "Q", tab); self.w(rec + 0x18, "Q", data)
        self.w(rec + 0x90, "hh", -1, -1)
        for s in (0x18, 0x30): self.w(vtrec + s, "Q", self.ret1)
        self.w(dl, "Q", vtobj); self.w(dl + 0x58, "B", 1)
        self.w(dl + 0x128, "4f", *light["diffuse"]); self.w(dl + 0x150, "4f", *light["second"]); self.w(dl + 0x1a0, "f", light["intensity"])
        self.dl_view(dl, light["direction"], light["viewCoord"], light["matrix"])
        for o, fg in ((fog0, fogs[0]), (fog1, fogs[1])):
            self.w(o, "Q", vtobj); self.w(o + 0x58, "B", 1)
            self.w(o + 0x128, "f", fg["start"]); self.w(o + 0x148, "f", fg["end"]); self.w(o + 0x168, "f", fg["damp"])
            self.w(o + 0x188, "4f", *fg["color"]); self.w(o + 0x1b0, "3f", *fg["dir"])
        self.faults = []
        self.call(0x71036b35c0, (gs, 0))
        return {"env": [self.rf(data + 16 * k, 4) for k in range(32)], "bits": [self.rb(data + 16 * k, 4) for k in range(32)], "faults": self.faults}

def lobby():
    env = json.loads((ROOT / "web/games/splatoon3/assets/maps/Lby_Lobby00/env.json").read_text(encoding="utf-8"))
    ml = env["rendering"]["Lighting"]["MainLight"]; fog = env["rendering"]["Fog"]
    c = ml["Color"]
    return env, [f(c["R"]), f(c["G"]), f(c["B"]), f(c["A"])], f(ml["Intens"]), f(ml["Latitude"]), f(ml["Longitude"]), fog

def main():
    e = Emu(); rnd = random.Random(1104)
    env, color, intens, lat, lon, fog = lobby()
    ident = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0] * 2
    main_cases = [{"name": "Lby_Lobby00", "color": color, "intensity": intens, "latitude": lat, "longitude": lon}]
    for k in range(64):
        main_cases.append({"name": "rand%d" % k, "color": [f(rnd.random() * 2) for _ in range(4)], "intensity": f(rnd.uniform(0, 20)),
                           "latitude": f(rnd.uniform(-90, 90)), "longitude": f(rnd.uniform(-360, 360))})
    for c in main_cases:
        c["out"] = e.mainlight(c["color"], c["intensity"], c["latitude"], c["longitude"])
    view_cases = []
    for k in range(48):
        d = [f(rnd.uniform(-1, 1)) for _ in range(3)] if k else main_cases[0]["out"]["direction"]
        m = [f(rnd.uniform(-1, 1)) for _ in range(24)] if k else ident
        vc = bool(k % 2) if k else False
        e.mu.mem_write(HEAP, b"\0" * 0x4000)
        v1, v2, b2 = e.dl_view(HEAP + 0x3000, d, vc, m)
        view_cases.append({"direction": d, "viewCoord": vc, "matrix": m, "arr1f8": v1, "arr208": v2, "arr208Bits": b2})
    df, hf = fog["DepthFog"], fog["HeightFog"]
    rgba = lambda o: [f(o["R"]), f(o["G"]), f(o["B"]), f(o["A"])]
    base = main_cases[0]["out"]
    lobby_light = {"diffuse": base["diffuse"], "second": [1.0, 1.0, 1.0, 1.0], "intensity": base["intensity"], "direction": base["direction"], "viewCoord": False,
                   "matrix": [0.8, 0, -0.6, 3, 0.1, 0.99, 0.13, -2, 0.59, -0.14, 0.79, 7] * 2}
    lobby_fogs = [{"start": f(df["Start"]), "end": f(df["End"]), "damp": 1.0, "color": rgba(df["Color"]), "dir": [0.0, 0.0, -1.0]},
                  {"start": f(hf["Start"]), "end": f(hf["End"]), "damp": 1.0, "color": rgba(hf["Color"]), "dir": [0.0, -1.0, 0.0]}]
    env_cases = [{"name": "Lby_Lobby00", "light": lobby_light, "fogs": lobby_fogs}]
    for k in range(16):
        s = f(rnd.uniform(0, 50)); en = f(s + rnd.uniform(0.5, 500))
        env_cases.append({"name": "rand%d" % k, "light": {"diffuse": [f(rnd.random()) for _ in range(4)], "second": [f(rnd.random()) for _ in range(4)],
                          "intensity": f(rnd.uniform(0, 20)), "direction": [f(rnd.uniform(-1, 1)) for _ in range(3)], "viewCoord": False,
                          "matrix": [f(rnd.uniform(-1, 1)) for _ in range(24)]},
                          "fogs": [{"start": s, "end": en, "damp": f(rnd.uniform(0, 2)), "color": [f(rnd.random()) for _ in range(4)], "dir": [f(rnd.uniform(-1, 1)) for _ in range(3)]} for _ in range(2)]})
    for c in env_cases:
        c["out"] = e.env_ubo(c["light"], c["fogs"])
    out = ROOT / "web/games/splatoon3/tests/fixtures/r11_gfx_diff_light_native.json"
    out.write_text(json.dumps({"fns": ["0x7102b607c4", "0x7102b60ea0", "0x71035d6500", "0x71036b35c0"], "sdk": ["sinf", "cosf", "sqrtf"],
                               "stubs": ["__cxa_guard_acquire=0", "__cxa_guard_release", "obj vtable+0x48=1", "record vtable+0x18/+0x30", "RenderingDay vtable+0x70 fixed"],
                               "mainlight": main_cases, "dlView": view_cases, "envUbo": env_cases}), encoding="utf-8")
    print(json.dumps(main_cases[0]["out"])); print(json.dumps(view_cases[0]))
    o = env_cases[0]["out"]; print("faults", o["faults"])
    for k in (4, 5, 10, 11, 12, 13, 14, 15, 23): print(k, o["env"][k])

if __name__ == "__main__":
    main()
