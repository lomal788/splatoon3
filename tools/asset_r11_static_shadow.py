"""r11 gfx-diff 그림자: 로비 visual.glb 의 모델·재질별 깊이 그림자 renderInfo 표.
원본 renderInfo gsys_static_depth_shadow / gsys_static_depth_shadow_only / gsys_dynamic_depth_shadow(_only) 를
romfs/Model/<bfres>.bfres.zs 에서 asset_bfres2gltf dump 로 읽어 maps/Lby_Lobby00/data/depth_shadow.json 에 쓴다.
visual.glb 의 renderInfo 는 asset_model.RI_KEEP 가 이 키를 걸러서 없다(재빌드 없이 공급). catalog.json map/Lby_Lobby00 files 갱신.
- 정적 캐스터 수집 0x710374f950(+0x10 bit4) · 정적 깊이 그림자 패스 = gsys_static_depth_shadow 1 [데이터].
사용: .venv/Scripts/python.exe web/tools/asset_r11_static_shadow.py
"""
import json
import struct
import subprocess
import tempfile
from pathlib import Path

import asset_common as A
import spl_data

EXE = A.ROOT / "analysis/assets_work/build/bin/Release/net7.0/asset_bfres2gltf.exe"
MAP = A.ASSETS / "maps/Lby_Lobby00"
KEYS = ("gsys_static_depth_shadow", "gsys_static_depth_shadow_only", "gsys_dynamic_depth_shadow", "gsys_dynamic_depth_shadow_only")


def glb_models(path):
    b = path.read_bytes()
    n, = struct.unpack_from("<I", b, 12)
    j = json.loads(b[20:20 + n])
    return sorted({nd["extras"]["originalModelName"] for nd in j["nodes"] if (nd.get("extras") or {}).get("originalModelName")})


def bfres_of(model):
    for name in (model, model.rstrip("0123456789"), "Fld_VSLobby", "Obj_MinigameChair"):
        p = A.ROMFS / f"Model/{name}.bfres.zs"
        if p.exists():
            yield name


def main():
    models = glb_models(MAP / "visual.glb")
    out, src = {}, {}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        cache = {}
        for model in models:
            for bf in bfres_of(model):
                if bf not in cache:
                    raw = td / f"{bf}.bfres"
                    raw.write_bytes(spl_data.load(A.ROMFS / f"Model/{bf}.bfres.zs"))
                    dump = td / f"{bf}.json"
                    subprocess.run([str(EXE), "dump", str(dump), str(raw)], check=True, capture_output=True)
                    cache[bf] = json.loads(dump.read_text(encoding="utf-8"))[0]
                found = [m for m in cache[bf].get("models", []) if m["name"] == model]
                if found:
                    mats = {}
                    for mat in found[0]["materials"]:
                        ri = mat.get("renderInfo") or {}
                        mats[mat["name"]] = {k: int((ri.get(k) or ["0"])[0]) for k in KEYS}
                    out[model] = mats
                    src[model] = f"Model/{bf}.bfres.zs"
                    break
    missing = [m for m in models if m not in out]
    doc = {"source": "romfs renderInfo via asset_bfres2gltf dump (web/tools/asset_r11_static_shadow.py)",
           "bfres": src, "missing": missing, "models": out}
    dst = MAP / "data/depth_shadow.json"
    dst.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(v) for v in out.values()); s = sum(x["gsys_static_depth_shadow"] for v in out.values() for x in v.values())
    print(dst, "models", len(out), "materials", n, "static", s, "missing", missing, "bundle bytes", catalog())


def catalog():
    p = A.ASSETS / "catalog.json"; c = json.loads(p.read_text(encoding="utf-8")); e = c["bundles"]["map/Lby_Lobby00"]
    e["files"] = sorted(set(e["files"]) | {"data/depth_shadow.json"}); e["bytes"] = sum((MAP / f).stat().st_size for f in e["files"])
    p.write_text(json.dumps(c, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return e["bytes"]


if __name__ == "__main__":
    main()
