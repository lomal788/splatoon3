"""r11 gfx-light: 로비 환경 텍스처 두 개를 원본 그대로 번들에 넣는다(원본 폴더 읽기 전용).
- sky/mSky_Alb.bc6h.bin(+.json): Sky_Daytime00 mSky_Alb BC6H_UFLOAT 13밉의 디스위즐한 원본 블록 그대로(값 변환 없음, HDR 보존).
  웹은 EXT_texture_compression_bptc 로 GPU 가 직접 디코드한다(없으면 기존 8비트 KTX2).
- env/IlluminateEnvMap.rgba8.bin(+.json): IlluminateEnvMap.bfres 내장 64² BC1_SRGB 7밉을 RGBA8(sRGB 바이트 그대로)로 디코드.
- catalog.json 의 map/Lby_Lobby00 files·bytes 갱신.
사용: .venv/Scripts/python web/tools/asset_r11_env.py
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "web/tools")]
import numpy as np
import graphics_bntx as B
OUT = ROOT / "web/games/splatoon3/assets/maps/Lby_Lobby00"
ROM = ROOT / "extracted/romfs/Model"

def tex(bfres, name):
    return [t for t in B.parse(B.read_bntx(str(ROM / bfres))) if t.name == name][0]

def sky():
    t = tex("Sky_Daytime00.bfres.zs", "mSky_Alb"); assert t.fmt_name == "BC6H_UFLOAT", t.fmt_name
    _, bw, bh, bpp = B.FORMATS[t.format >> 8]; blob = bytearray(); mips = []
    for m in range(t.mips):
        w, h = max(1, t.width >> m), max(1, t.height >> m)
        lin, wb, hb = B.deswizzle(B.surface_bytes(t, 0, m), w, h, bw, bh, bpp, t.block_height_log2, shrink=m > 0)
        n = B.div_up(w, 4) * B.div_up(h, 4) * 16; data = bytes(lin[:n]); assert len(data) == n
        mips.append({"width": w, "height": h, "offset": len(blob), "bytes": n}); blob += data
    (OUT / "sky/mSky_Alb.bc6h.bin").write_bytes(blob)
    meta = {"source": "romfs Model/Sky_Daytime00.bfres.zs mSky_Alb", "format": "BC6H_UFLOAT", "comp": t.comp, "file": "sky/mSky_Alb.bc6h.bin", "mips": mips}
    (OUT / "sky/mSky_Alb.bc6h.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return len(blob)

def highlight():
    t = tex("IlluminateEnvMap.bfres.zs", "IlluminateEnvMap"); assert t.fmt_name == "BC1_SRGB", t.fmt_name
    blob = bytearray(); mips = []
    for m in range(t.mips):
        img = B.apply_comp(B.decode_layer(t, 0, m), t.comp); a = np.asarray(img, np.uint8)
        mips.append({"width": a.shape[1], "height": a.shape[0], "offset": len(blob), "bytes": a.nbytes}); blob += a.tobytes()
    (OUT / "env").mkdir(exist_ok=True)
    (OUT / "env/IlluminateEnvMap.rgba8.bin").write_bytes(blob)
    meta = {"source": "romfs Model/IlluminateEnvMap.bfres.zs IlluminateEnvMap", "format": "BC1_SRGB", "decoded": "RGBA8, sRGB-encoded bytes (decode with SRGBColorSpace)", "comp": t.comp, "file": "env/IlluminateEnvMap.rgba8.bin", "mips": mips}
    (OUT / "env/IlluminateEnvMap.rgba8.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return len(blob)

def catalog():
    p = ROOT / "web/games/splatoon3/assets/catalog.json"; c = json.loads(p.read_text(encoding="utf-8")); e = c["bundles"]["map/Lby_Lobby00"]
    add = ["sky/mSky_Alb.bc6h.bin", "sky/mSky_Alb.bc6h.json", "env/IlluminateEnvMap.rgba8.bin", "env/IlluminateEnvMap.rgba8.json"]
    e["files"] = sorted(set(e["files"]) | set(add)); e["bytes"] = sum((OUT / f).stat().st_size for f in e["files"])
    p.write_text(json.dumps(c, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return e["bytes"]

if __name__ == "__main__":
    print("sky", sky(), "highlight", highlight(), "bundle bytes", catalog())
