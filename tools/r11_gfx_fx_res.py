"""r11 gfx-diff 이펙트: 원본 ResEmitter(0xEF0 B) 바이트를 FIXED 패치(0x71008190fc) 뒤 그대로 덤프.

sysEmitterStaticUniformBlock.data[i] = ResEmitter + 16*i (data[103]=+0x670 colorScale, [104]=+0x680 color0 key0,
[128]=+0x800 alpha1 key0, [137]=+0x890 nearFade) — 셰이더 차등 비교의 정적 UBO 입력.
사용: PY web/tools/r11_gfx_fx_res.py [이미터셋...]  → web/games/splatoon3/tests/fixtures/r11_fx_res.json
"""
import json
import struct
import sys

import asset_common as A
import asset_fx
import vfx_emitter46 as E

DEFAULT = asset_fx.ESETS + ["WpShtrSite", "WpShtrSiteHit", "WpShtrFieldHitMarker", "WpShtrSiteSide", "WpShtrHitMarkerSide"]


def patched(d, bo):
    b = bytearray(d[bo:bo + E.SIZE])
    t = b[0xD3C:0xD40]
    pc = b[0xD40:0xD60]
    if t[0] == 0: b[0x680:0x68C] = pc[0:12]
    if t[2] == 0: b[0x700:0x704] = pc[12:16]
    if t[1] == 0: b[0x780:0x78C] = pc[16:28]
    if t[3] == 0: b[0x800:0x804] = pc[28:32]
    return bytes(b)


def main():
    want = sys.argv[1:] or DEFAULT
    v = asset_fx.vfxb()
    out = {"source": "romfs/Effect/static.Nin_NX_NVN.esetb.byml.zs VFXB v46", "size": E.SIZE,
           "patch": "0x71008190fc FIXED PColor -> key0", "emitters": {}}
    for es, name, depth, parent, bo, em in E.emitters(v, set(want)):
        out["emitters"][f"{es}/{name}"] = {"depth": depth, "parent": parent, "hex": patched(v.d, bo).hex()}
    missing = [s for s in want if not any(k.startswith(s + "/") for k in out["emitters"])]
    out["missing"] = missing
    p = A.WEB / "games/splatoon3/tests/fixtures/r11_fx_res.json"
    p.write_text(json.dumps(out, indent=0) + "\n", encoding="utf8")
    print(len(out["emitters"]), "emitters; missing", missing)


if __name__ == "__main__":
    main()
