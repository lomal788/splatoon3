"""Splatoon 3 폰트 아카이브(romfs/Font/*.bfarc.zs = zstd SARC) 도구.
BFOTF/BFTTF 복호화 규칙은 mpj tools/ui_font.py(decrypt_bfotf) 를 그대로 옮겼다.

사용:
  ui_font.py list <x.bfarc.zs>                       파일 목록 + FCPX 구성 폰트 이름
  ui_font.py otf <x.bfarc.zs> <안 경로> <out.otf|ttf>  복호화해 저장 (헤더 sfnt 버전 출력)
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ui_sarc  # noqa: E402

BFOTF_KEYS = {0x1A879BD9: 2785117442, 0x1E1AF836: 1231165446, 0xC1DE68F3: 2364726489}


def decrypt_bfotf(b):
    magic = struct.unpack_from("<I", b, 0)[0]
    key = BFOTF_KEYS[magic]
    size = struct.unpack_from(">I", b, 4)[0] ^ key
    out = bytearray(len(b) - 8)
    for p in range(8, len(b) - 3, 4):
        struct.pack_into(">I", out, p - 8, struct.unpack_from(">I", b, p)[0] ^ key)
    return bytes(out[:size]), size


def fcpx_names(b):
    names, i = [], 0
    for ext in (b".bfotf", b".bfttf", b".bffnt"):
        i = 0
        while True:
            j = b.find(ext, i)
            if j < 0:
                break
            k = j
            while k > 0 and 32 <= b[k - 1] < 127:
                k -= 1
            names.append((j, b[k:j + 6].decode()))
            i = j + 6
    return [n for _, n in sorted(names)]


if __name__ == "__main__":
    files = ui_sarc.read_files(sys.argv[2])
    if sys.argv[1] == "list":
        for n, b in sorted(files.items()):
            extra = fcpx_names(b) if b[:4] == b"FCPX" else ""
            print(f"{len(b):>9} {n} {extra}")
    elif sys.argv[1] == "otf":
        data, size = decrypt_bfotf(files[sys.argv[3]])
        Path(sys.argv[4]).write_bytes(data)
        print(size, data[:4].hex(), data[:4])
