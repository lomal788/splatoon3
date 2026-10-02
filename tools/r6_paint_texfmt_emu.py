"""r6 paint: 도색 텍스처 포맷 비트 폭을 게임(agl) 포맷 정보표와 원본 크기 계산 함수 실행으로 확정한다.

- 포맷 정보표 0x7104abf510 (0x14 B × 0x5d, agl 포맷 번호 색인) [데이터]:
    +0..+3 채널별 비트 수(R,G,B,A 순서 그대로 저장), +4..+7 채널 순서, +8 텍셀(블록)당 바이트,
    +9 채널 수, +0xa 압축, +0xb 정규화, +0xc 부동소수, +0xd 부호 없음, +0xf/+0x10 깊이/스텐실 계열, +0x12/+0x13 블록 w/h
  (필드 의미는 표 안 일관성으로 붙임: R8/R8SN/R8UI/R8I 4행이 +0xb/+0xd 조합 4가지를 갖는 것 등)
- 원본 실행: agl 이미지 바이트 크기 함수 0x71035b519c(type, fmt, w, h, d, mips, mode) 를 mode=0(선형) 경로로 실행.
  이 경로는 +8(텍셀당 바이트)만 써서 크기를 계산하고 다른 함수를 부르지 않는다(스텁 없음).
  mode≠0 경로는 NVN 드라이버(nvnTextureBuilderGetStorageSize)를 부르므로 실행하지 않는다.
결과: analysis/paint/r6_texfmt_emu_out.json
"""
import json, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r6_paint_img import IMG, BASE, rd, u32

ROOT = Path(__file__).resolve().parents[2]
FN = 0x71035b519c
STACK, END = 0x10000000, 0x30000000
PAINT = {10: "tex0/tex1 색(규칙≠5)", 0x1d: "tex0/tex1 색(규칙 5)", 0x5b: "tex2 깊이·스텐실", 9: "높이 마스크(+0x740)"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    mu.mem_map(BASE, (len(IMG) + 0xFFFF) & ~0xFFFF); mu.mem_write(BASE, IMG)
    mu.mem_map(STACK, 0x100000); mu.mem_map(END, 0x1000)
    mu.mem_write(END, struct.pack("<I", 0xD65F03C0))
    mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)

    def call(*a):
        for r, v in zip((UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3,
                         UC_ARM64_REG_X4, UC_ARM64_REG_X5, UC_ARM64_REG_X6), a):
            mu.reg_write(r, v)
        mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000); mu.reg_write(UC_ARM64_REG_LR, END)
        mu.emu_start(FN, END, count=100000)
        return mu.reg_read(UC_ARM64_REG_X0) & 0xFFFFFFFF

    rows, n, ok = [], 0, 0
    for fmt in range(0x5d):
        rec = rd(0x7104abf510 + 0x14 * fmt, 0x14)
        bpp = rec[8]
        for (w, h) in ((3200, 3200), (400, 400), (1600, 1600), (1, 1), (37, 5)):
            got = call(1, fmt, w, h, 1, 1, 0)   # type 1 = PaintTextureData 가 쓰는 값(0x71035b1c84 첫 인자)
            n += 1; ok += got == bpp * w * h
        if fmt in PAINT:
            got = call(1, fmt, 3200, 3200, 1, 1, 0)
            rows.append(dict(agl=fmt, use=PAINT[fmt], nvn=u32(0x7104abfc54 + 4 * fmt),
                             bits=list(rec[0:4]), order=list(rec[4:8]), bytes_per_texel=bpp, channels=rec[9],
                             compressed=rec[0xa], normalized=rec[0xb], float=rec[0xc], unsigned=rec[0xd],
                             depthfmt=[rec[0xf], rec[0x10]], bytes_3200=got, bytes_per_texel_run=got / (3200 * 3200),
                             raw=rec.hex(" ")))
    out = dict(checked=n, match=ok, paint=rows)
    for r in rows:
        print(r)
    print(f"0x71035b519c mode0: {ok}/{n} = 표 +8 × w × h")
    (ROOT / "analysis/paint/r6_texfmt_emu_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
