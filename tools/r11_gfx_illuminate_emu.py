"""r11 gfx-light: Illuminate UBO writer 0x710102ff04 을 unicorn 으로 원본 실행한다.
- 입력: holder(+0xec4 BaseIntensity, +0xec8 LightTexScale, +0xed0 개수, +0xed8 원소 포인터 배열 {Latitude, Intensity, LongitudeFromMainLight}),
  DirectionalLight(+0x128 Color RGBA, +0x1c0/+0x1c8 Direction x/z).
- 외부 호출: sinf/cosf/sqrtf 는 SDK 원본(extracted/exefs/sdk.img)으로 GOT 를 바꿔 실행. nn::os::Lock/UnlockMutex 만 즉시 반환 스텁
  (UBO 갱신 목록 삽입 잠금, 출력 값과 무관).
- 출력: holder+0xc30 cLightParam(x=LightTexScale, y, z=개수), +0xc78 cLightColor, +0xcc0+16i cLightInfo[i].
사용: PY web/tools/r11_gfx_illuminate_emu.py → analysis/gfx_r11/illuminate/illuminate_emu.json
"""
import json, random, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import *
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_player_libm_emu import symbols
IMG = ROOT / "extracted/exefs/main.reloc.img"; SDK = ROOT / "extracted/exefs/sdk.img"
BASE, SBASE = 0x7100000000, 0x7400000000
STACK, HEAP, RET = 0x10000000, 0x20000000, 0x30000000
FN = 0x710102ff04
H, DL, ELEM, PTRS, MUT = HEAP, HEAP + 0x2000, HEAP + 0x3000, HEAP + 0x4000, HEAP + 0x5000
f = lambda v: struct.unpack('<f', struct.pack('<f', v))[0]

class Emu:
    def __init__(self):
        img, sdk = IMG.read_bytes(), SDK.read_bytes()
        mu = self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF); mu.mem_write(BASE, img)
        mu.mem_map(SBASE, (len(sdk) + 0xFFFF) & ~0xFFFF); mu.mem_write(SBASE, sdk)
        mu.mem_map(STACK, 0x100000); mu.mem_map(HEAP, 0x10000); mu.mem_map(RET, 0x1000)
        mu.mem_write(RET, struct.pack("<II", 0xD65F03C0, 0xD65F03C0))
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        sym = symbols(sdk)
        for got, name in ((0x710576fdc8, "sqrtf"), (0x710576ff38, "cosf"), (0x710576ff40, "sinf")):
            mu.mem_write(got, struct.pack("<Q", SBASE + sym[name][0]))
        for got in (0x710576f008, 0x710576f018):
            mu.mem_write(got, struct.pack("<Q", RET + 4))

    def run(self, color, d, base_int, tex_scale, elems):
        mu = self.mu
        mu.mem_write(HEAP, b"\0" * 0x6000)
        for o in (0xc28, 0xc70, 0xcb8):
            mu.mem_write(H + o, struct.pack("<Q", MUT))
        mu.mem_write(MUT + 0x2dc, struct.pack("<i", 0))
        mu.mem_write(H + 0xec4, struct.pack("<ff", base_int, tex_scale))
        mu.mem_write(H + 0xed0, struct.pack("<i", len(elems)))
        mu.mem_write(H + 0xed8, struct.pack("<Q", PTRS))
        for i, e in enumerate(elems):
            mu.mem_write(ELEM + 16 * i, struct.pack("<3f", *e))
            mu.mem_write(PTRS + 8 * i, struct.pack("<Q", ELEM + 16 * i))
        mu.mem_write(DL + 0x128, struct.pack("<4f", *color))
        mu.mem_write(DL + 0x1c0, struct.pack("<3f", *d))
        mu.reg_write(UC_ARM64_REG_X0, H); mu.reg_write(UC_ARM64_REG_X1, DL)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000); mu.reg_write(UC_ARM64_REG_LR, RET)
        mu.emu_start(FN, RET, count=2000000)
        rd = lambda a, n: list(struct.unpack("<%df" % n, bytes(mu.mem_read(a, 4 * n))))
        bits = lambda a, n: list(struct.unpack("<%dI" % n, bytes(mu.mem_read(a, 4 * n))))
        return {"param": rd(H + 0xc30, 3), "paramBits": bits(H + 0xc30, 3), "color": rd(H + 0xc78, 4),
                "lights": [rd(H + 0xcc0 + 16 * i, 4) for i in range(len(elems))],
                "lightBits": [bits(H + 0xcc0 + 16 * i, 4) for i in range(len(elems))]}

def lobby_elems(raw):
    out = []
    for e in raw:
        out.append((f(e.get("Latitude", 40.0)), f(e.get("Intensity", 1000.0)), f(e.get("LongitudeFromMainLight", 0.0))))
    return out

def main():
    env = json.loads((ROOT / "web/games/splatoon3/assets/maps/Lby_Lobby00/env.json").read_text(encoding="utf-8"))
    la = env["rendering"]["Lighting"]["EnvMap"]["IlluminateEnvMap"]["LightArray"]
    e = Emu(); rnd = random.Random(11)
    lobby_dir = (0.04313143342733383, -0.56640625, -0.8229967355728149)
    cases = [{"name": "Lby_Lobby00", "color": [0.6705883145332336, 0.8509804010391235, 1.0, 1.0], "dir": list(lobby_dir),
              "baseIntensity": 1.0, "lightTexScale": 1.0, "elems": [list(x) for x in lobby_elems(la)]}]
    for k in range(64):
        n = rnd.randint(1, 20)
        dv = [rnd.uniform(-1, 1) for _ in range(3)]
        cases.append({"name": "rand%d" % k, "color": [rnd.random() for _ in range(4)], "dir": [f(v) for v in dv],
                      "baseIntensity": f(rnd.uniform(0, 4)), "lightTexScale": f(rnd.uniform(.25, 4)),
                      "elems": [[f(rnd.uniform(-90, 90)), f(rnd.uniform(0, 8000)), f(rnd.uniform(-360, 720))] for _ in range(n)]})
    for c in cases:
        c["out"] = e.run([f(x) for x in c["color"]], [f(x) for x in c["dir"]], c["baseIntensity"], c["lightTexScale"], [tuple(x) for x in c["elems"]])
    out = ROOT / "analysis/gfx_r11/illuminate/illuminate_emu.json"
    out.write_text(json.dumps({"fn": hex(FN), "stubs": ["nn::os::LockMutex", "nn::os::UnlockMutex"], "sdk": ["sinf", "cosf", "sqrtf"], "cases": cases}), encoding="utf-8")
    print(json.dumps(cases[0]["out"])[:1200])

if __name__ == "__main__":
    main()
