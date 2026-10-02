"""BNTX 형식 분포 스캔: 지정 형식(상위 바이트)의 텍스처를 찾아 imageSize 로 텍셀당 바이트를 역산한다.
사용: PY web/tools/graphics_bntx_fmtscan.py <형식 16진, 예 0x12> [glob ...] [--max N]
기본 glob: extracted/romfs/Model/*.bfres.zs. 압축은 메모리에서만 푼다(디스크에 쓰지 않음).
출력: 파일, 텍스처 이름, 형식, 크기, mip, imageSize, 역산 bpp(블록 선형 정렬 포함 계산과 맞는 후보).
"""
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graphics_bntx import parse, div_up  # noqa: E402


def surface_size(w, h, bpp, bh_log2, mips):
    """블록 선형(GOB 64Bx8) 기준 mip 체인 크기. 각 mip은 512B 정렬, 블록 높이는 작아지면 줄어듦."""
    total = 0
    for m in range(mips):
        mw, mh = max(1, w >> m), max(1, h >> m)
        gob_h = 1 << bh_log2
        while m > 0 and gob_h > 1 and div_up(mh, 8) <= gob_h // 2:
            gob_h //= 2
        row = div_up(mw * bpp, 64) * 64
        rows = div_up(mh, 8 * gob_h) * 8 * gob_h
        total += row * rows
    return total


def all_bntx(path):
    """파일 안의 모든 BNTX(.zs 는 메모리 해제, SARC/BYML/FRES 안 내장 포함). 크기는 헤더 +0x1C."""
    import struct
    data = open(path, "rb").read()
    if data[:4] == bytes.fromhex("28b52ffd"):
        import zstandard
        data = zstandard.ZstdDecompressor().decompress(data, max_output_size=1 << 31)
    i = data.find(b"BNTX" + bytes(4))
    while i >= 0:
        size = struct.unpack_from("<I", data, i + 0x1C)[0]
        yield data[i:i + size]
        i = data.find(b"BNTX" + bytes(4), i + 4)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mx = 20
    if "--max" in sys.argv:
        mx = int(sys.argv[sys.argv.index("--max") + 1])
        args = [a for a in args if a != str(mx)]
    fmt = int(args[0], 16)
    pats = args[1:] or ["C:/dev/splatoon3/extracted/romfs/Model/*.bfres.zs"]
    found = 0
    for pat in pats:
        for f in sorted(glob.glob(pat)):
            texs = []
            for blob in all_bntx(f):
                try:
                    texs += parse(blob)
                except Exception:
                    pass
            for t in texs:
                if t.format >> 8 != fmt:
                    continue
                per_layer = t.image_size // max(1, t.array)
                cands = [b for b in (1, 2, 4, 8, 16)
                         if surface_size(t.width, t.height, b, t.block_height_log2, t.mips) <= per_layer
                         and surface_size(t.width, t.height, b * 2, t.block_height_log2, t.mips) > per_layer]
                print(f"{Path(f).name}\t{t.name}\t{t.fmt_name}\t{t.width}x{t.height}x{t.depth} arr{t.array}\tmips {t.mips}"
                      f"\timageSize {t.image_size}\tbpp후보 {cands}")
                found += 1
                if found >= mx:
                    return
    print(f"# {found}개", file=sys.stderr)


if __name__ == "__main__":
    main()
