"""BNTX 부동소수 텍스처 디코더 (이펙트용 확장, graphics_bntx.py 는 수정하지 않고 가져다 씀).

graphics_bntx.py 의 FORMATS 표에 없는 nn::gfx 채널 형식 중 이펙트 VFXB(GRTF) 안에서 쓰이는 것을 푼다.
  0x15 = R16_G16_B16_A16 (8 B/텍셀). 이 게임 이펙트에서는 타입 0x05(FLOAT) 만 나온다(예 bulletshtr_vsp, splash0x_vsp, *_vfp).
  채널 형식 번호는 nn::gfx ChannelFormat 순서(…0x12 R16_G16, 0x14 R32, 0x15 R16_G16_B16_A16, 0x17 R32_G32, 0x19 R32_G32_B32_A32,
  0x1A BC1…)이며 graphics_bntx.py FORMATS 의 BC1=0x1A 와 같은 체계다. 8 B/텍셀은 imageSize 로 확인(예 10x1126 → 147,456 B 블록선형 패딩 포함,
  16 B/텍셀이면 180,160 B 이상이 필요해 불가능).

출력:
  - <이름>.npy  : float32 (H, W, 4) 원값 (half → float32, 반올림 없음)
  - <이름>.png  : 채널별 min..max 를 0..255 로 늘린 미리보기(값 확인용, 원본 표시와 무관)
  - 요약 JSON   : 채널별 min/max/mean, NaN/Inf 개수

사용:
  PY web/tools/effect_bntx_float.py info <x.bntx>                       # FLOAT/부동 형식 텍스처 목록
  PY web/tools/effect_bntx_float.py dump <x.bntx> <출력폴더> <이름...>   # 지정 텍스처 디코드
  PY web/tools/effect_bntx_float.py selftest                            # 합성 블록선형 데이터로 왕복 검사
"""
import json
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import graphics_bntx as G  # noqa: E402

FLOAT_FORMATS = {
    0x12: ("R16_G16", 4, 2, np.float16),
    0x14: ("R32", 4, 1, np.float32),
    0x15: ("R16_G16_B16_A16", 8, 4, np.float16),
    0x17: ("R32_G32", 8, 2, np.float32),
    0x19: ("R32_G32_B32_A32", 16, 4, np.float32),
}


def surface(t, layer=0, mip=0):
    layer_stride = t.image_size // max(1, t.array)
    start = t.data_off + layer * layer_stride + t.mip_offsets[mip]
    end = t.data_off + layer * layer_stride + (t.mip_offsets[mip + 1] if mip + 1 < t.mips else layer_stride)
    return t.raw[start:end]


def decode_float(t, layer=0, mip=0):
    ch = t.format >> 8
    if ch not in FLOAT_FORMATS or (t.format & 0xFF) != 5:
        raise NotImplementedError("format 0x%04X" % t.format)
    name, bpp, nc, dt = FLOAT_FORMATS[ch]
    width = max(1, t.width >> mip)
    height = max(1, t.height >> mip)
    if t.tile_mode == 1:  # pitch-linear (이펙트 텍스처에는 없음, 대비용)
        lin = bytes(surface(t, layer, mip))[:width * height * bpp]
    else:
        lin, _, _ = G.deswizzle(surface(t, layer, mip), width, height, 1, 1, bpp, t.block_height_log2, shrink=mip > 0)
    a = np.frombuffer(lin, dtype=dt).reshape(height, width, nc).astype(np.float32)
    return a


def summary(a):
    out = {"shape": list(a.shape)}
    fin = np.isfinite(a)
    out["nan"] = int(np.isnan(a).sum())
    out["inf"] = int(np.isinf(a).sum())
    chans = []
    for c in range(a.shape[2]):
        v = a[..., c][fin[..., c]]
        chans.append({"min": float(v.min()) if v.size else None, "max": float(v.max()) if v.size else None,
                      "mean": float(v.mean()) if v.size else None})
    out["channels"] = chans
    return out


def preview(a, path):
    from PIL import Image
    h, w, nc = a.shape
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., 3] = 255
    for c in range(min(nc, 4)):
        v = np.nan_to_num(a[..., c], nan=0.0, posinf=0.0, neginf=0.0)
        lo, hi = float(v.min()), float(v.max())
        rgba[..., c] = np.round((v - lo) / (hi - lo) * 255).astype(np.uint8) if hi > lo else 0
    Image.fromarray(rgba, "RGBA").save(path)


def cmd_info(path):
    for t in G.parse(G.read_bntx(path)):
        if (t.format >> 8) in FLOAT_FORMATS:
            print("%-32s 0x%04X %-16s %4dx%-5d mips %d tile %d" % (
                t.name, t.format, FLOAT_FORMATS[t.format >> 8][0], t.width, t.height, t.mips, t.tile_mode))


def cmd_dump(path, out_dir, names):
    os.makedirs(out_dir, exist_ok=True)
    res = {}
    for t in G.parse(G.read_bntx(path)):
        if t.name not in names:
            continue
        a = decode_float(t)
        np.save(os.path.join(out_dir, t.name + ".npy"), a)
        preview(a, os.path.join(out_dir, t.name + ".png"))
        res[t.name] = dict(summary(a), format="0x%04X" % t.format)
        print(t.name, json.dumps(res[t.name]))
    with open(os.path.join(out_dir, "float_textures.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


def swizzle_ref(lin, width, height, bpp, bh_log2):
    """deswizzle 의 역(합성 검사용): 선형 → 블록선형."""
    row_bytes = width * bpp
    gob_h = 1 << bh_log2
    gobs_x = G.div_up(row_bytes, 64)
    hh = G.div_up(height, 8 * gob_h) * 8 * gob_h
    out = np.zeros(gobs_x * 512 * gob_h * (hh // (8 * gob_h)), np.uint8)
    X, Y = np.meshgrid(np.arange(row_bytes), np.arange(height))
    gob_addr = (Y // (8 * gob_h)) * 512 * gob_h * gobs_x + (X // 64) * 512 * gob_h + ((Y % (8 * gob_h)) // 8) * 512
    addr = gob_addr + ((X % 64) // 32) * 256 + ((Y % 8) // 2) * 64 + ((X % 32) // 16) * 32 + (Y % 2) * 16 + (X % 16)
    out[addr.ravel()] = np.frombuffer(lin, np.uint8)
    return out.tobytes()


def cmd_selftest():
    ok = 0
    for (w, h, bh) in ((6, 83, 4), (10, 1126, 4), (17, 5, 0), (92, 40, 2)):
        rng = np.random.default_rng(w * 1000 + h)
        a = rng.standard_normal((h, w, 4)).astype(np.float16)
        sw = swizzle_ref(a.tobytes(), w, h, 8, bh)
        lin, _, _ = G.deswizzle(sw, w, h, 1, 1, 8, bh)
        b = np.frombuffer(lin, np.float16).reshape(h, w, 4)
        same = np.array_equal(a.view(np.uint16), b.view(np.uint16))
        print("roundtrip %dx%d bh=%d : %s" % (w, h, bh, "PASS" if same else "FAIL"))
        ok += same
    print("%d/4 PASS" % ok)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "info":
        cmd_info(sys.argv[2])
    elif cmd == "dump":
        cmd_dump(sys.argv[2], sys.argv[3], set(sys.argv[4:]))
    elif cmd == "selftest":
        cmd_selftest()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
