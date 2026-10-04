"""r11 gfx-diff 재질: 사격장 표적(Obj_SighterTarget.bfres) 재질이 쓰는데 parts glb 에 빠진 텍스처를 원본 그대로 번들에 넣는다.
- tex/Obj_SighterTarget/M_Body_Tcl.ktx2 : _su0 팀색 마스크. 원본 BC1_SRGB → sRGB KTX2(ETC1S). glb 는 PBR 슬롯 밖이라 gltfpack 이 버렸다.
- tex/Obj_SighterTarget/native_formats.json : bfres 내장 BNTX 전 텍스처의 원본 형식(웹이 색 공간을 원본대로 해석할 때 쓴다.
  M_Body_Rgh 가 BC1_SRGB 라 .mr 합본의 G 채널은 sRGB 부호화 값이다).
- catalog.json 의 map/Lby_Lobby00 files·bytes 갱신.
원본 폴더는 읽기만 한다. 사용: .venv/Scripts/python web/tools/asset_r11_target_tex.py
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "web/tools")]
import asset_model as M
import asset_ktx2 as K

OUT = ROOT / "web/games/splatoon3/assets/maps/Lby_Lobby00"
OWNER = "Obj_SighterTarget"


def main():
    tex = M.textures(OWNER)  # 원본 romfs Model/Obj_SighterTarget.bfres.zs 내장 BNTX → PNG(+json), graphics_bntx
    formats = {}
    for j in sorted(tex.glob("*.json")):
        m = json.loads(j.read_text(encoding="utf-8"))
        formats[m["name"]] = {"format": m["format"], "comp": m["comp"], "srgb": bool(m.get("srgb"))}
    assert formats["M_Body_Tcl"]["format"] == "BC1_SRGB", formats["M_Body_Tcl"]
    dst = OUT / "tex" / OWNER
    dst.mkdir(parents=True, exist_ok=True)
    files = []
    K.encode(tex / "M_Body_Tcl.png", dst / "M_Body_Tcl.ktx2", linear=False)
    files.append(f"tex/{OWNER}/M_Body_Tcl.ktx2")
    meta = {"source": f"romfs Model/{OWNER}.bfres.zs embedded BNTX", "textures": formats}
    (dst / "native_formats.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    files.append(f"tex/{OWNER}/native_formats.json")
    p = ROOT / "web/games/splatoon3/assets/catalog.json"
    c = json.loads(p.read_text(encoding="utf-8"))
    e = c["bundles"]["map/Lby_Lobby00"]
    e["files"] = sorted(set(e["files"]) | set(files))
    e["bytes"] = sum((OUT / f).stat().st_size for f in e["files"])
    p.write_text(json.dumps(c, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("added", files, "bundle bytes", e["bytes"])


if __name__ == "__main__":
    main()
