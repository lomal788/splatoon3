"""r6 gfx_stage: 팀색 Ink/InkBright 보정 0x7101174afc 를 원본 그대로 unicorn 으로 실행해
대전 로비 조명(MainLight Color (0.6706,0.8510,1.0), Intens 10)에서 하늘 항(전역 skyUp 0x71058186e4)이
출력에 영향을 주는지 확인한다.

- 함수 전체를 실행한다. 외부 호출 powf/fmodf 는 SDK 모듈(extracted/exefs/sdk.img)의 원본 함수를
  같은 unicorn 에 올려 PLT GOT(0x710576fdd0 powf, 0x710576fdc0 fmodf)를 그 주소로 바꿔 부른다(스텁 아님).
- 스텁·설정(검증 범위 밖):
  * InkColorCorrection 리소스 미로드 경로(*0x7105818878 == 0)를 탄다. 이때 계수는 전역 객체 *0x71057940a8
    (= 0x7105818f28) +0x2c LumRate, +0x38 Rate6, +0x3c Rate1, +0x40/+0x44 BrightnessOffset/Luminance 에서 읽으므로
    그 칸에 데이터 값(CorrectionInkMain 0.5/0.55/0.2, CorrectionInkSSS 0.1/0.5)을 써 둔다. MaxSaturation 은 이 경로에서 1.0
    (데이터 0.99 와 다름 — 포화 판정과 무관).
  * 0x7101176af8(InkColorCorrection 싱글턴 1회 초기화)는 가드 바이트 0x7105818888 = 1 로 건너뛴다.
  * TeamColorHueDirPeak 싱글턴은 미로드 상태 그대로(hsv 단계의 방향 반전 없음 — 같은 입력끼리 비교하므로 무관).
- 판정: 같은 입력 색·bright 에서 skyUp 을 바꿔도(초기 (0,0,0,1), 0, 무작위 0..50) 출력 16 B 가 비트 단위로 같은가.
  대조군: Intensity 4·Diffuse 1(앞 항 t=4)에서는 skyUp 에 따라 출력이 달라져야 한다(하네스 민감도 확인).
사용: PY web/tools/r6_gfx_stage_inkcorr_emu.py [건수=500] → analysis/r6_gfx_stage/inkcorr_emu.json
"""
import json, random, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import *

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_player_libm_emu import symbols

IMG = ROOT / "extracted/exefs/main.reloc.img"
SDK = ROOT / "extracted/exefs/sdk.img"
BASE = 0x7100000000
SBASE = 0x7400000000
STACK, HEAP, RET = 0x10000000, 0x20000000, 0x30000000
FN = 0x7101174afc
G = 0x7105818f28
SKY = 0x71058186e4


class Emu:
    def __init__(self):
        img = IMG.read_bytes(); sdk = SDK.read_bytes()
        mu = self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF); mu.mem_write(BASE, img)
        mu.mem_map(SBASE, (len(sdk) + 0xFFFF) & ~0xFFFF); mu.mem_write(SBASE, sdk)
        mu.mem_map(STACK, 0x100000); mu.mem_map(HEAP, 0x10000); mu.mem_map(RET, 0x1000)
        mu.mem_write(RET, struct.pack("<I", 0xD65F03C0))
        mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
        sym = symbols(sdk)
        mu.mem_write(0x710576fdd0, struct.pack("<Q", SBASE + sym["powf"][0]))
        mu.mem_write(0x710576fdc0, struct.pack("<Q", SBASE + sym["fmodf"][0]))
        mu.mem_write(0x7105818878, struct.pack("<Q", 0))
        mu.mem_write(0x7105818888, b"\x01")
        for off, v in ((0x2c, 0.5), (0x38, 0.55), (0x3c, 0.2), (0x40, 0.1), (0x44, 0.5)):
            mu.mem_write(G + off, struct.pack("<f", v))

    def run(self, rgb, pcol, pscale, flag, sky, bright):
        mu = self.mu
        OUT, IN, P = HEAP, HEAP + 0x100, HEAP + 0x200
        mu.mem_write(OUT, b"\0" * 16)
        mu.mem_write(IN, struct.pack("<4f", *rgb, 1.0))
        mu.mem_write(P, struct.pack("<Q4ffB3x", 0, *pcol, 1.0, pscale, flag))
        mu.mem_write(SKY, struct.pack("<4f", *sky))
        for i, v in enumerate((OUT, IN, P, 0, bright)):
            mu.reg_write(UC_ARM64_REG_X0 + i, v)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        mu.reg_write(UC_ARM64_REG_LR, RET)
        mu.emu_start(FN, RET, count=400000)
        return bytes(mu.mem_read(OUT, 16))


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    e = Emu(); rnd = random.Random(6)
    lobby = ((0.6706, 0.8510, 1.0), 10.0)
    ctrl = ((1.0, 1.0, 1.0), 4.0)
    res = {"fn": hex(FN), "cases": n, "lobby_same": 0, "lobby_diff": 0, "ctrl_same": 0, "ctrl_diff": 0, "examples": []}
    for k in range(n):
        rgb = tuple(rnd.random() for _ in range(3))
        bright = k & 1
        skies = [(0.0, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 0.0)] + [tuple(rnd.uniform(0, 50) for _ in range(3)) + (1.0,) for _ in range(3)]
        for tag, (pc, ps) in (("lobby", lobby), ("ctrl", ctrl)):
            outs = [e.run(rgb, pc, ps, 1, s, bright) for s in skies]
            same = all(o == outs[0] for o in outs)
            res[tag + ("_same" if same else "_diff")] += 1
            if k < 3:
                res["examples"].append({"set": tag, "in": rgb, "bright": bright,
                                        "out": [list(struct.unpack("<4f", o)) for o in outs]})
    out = ROOT / "analysis/r6_gfx_stage/inkcorr_emu.json"
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print({k: v for k, v in res.items() if k != "examples"})


if __name__ == "__main__":
    main()
