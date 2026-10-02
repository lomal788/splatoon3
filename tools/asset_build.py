"""웹 에셋 전부 다시 만들기 (한 명령).

  cd c:/dev/splatoon3
  .venv/Scripts/python web/tools/asset_build.py            # 전부 + 검증 + 중간 산출물 정리
  .venv/Scripts/python web/tools/asset_build.py data map    # 일부 단계만 (data map char fx sfx catalog verify)
  옵션 --keep : analysis/assets_work 의 중간 산출물(raw bfres, png, static.vfxb, wav)을 지우지 않음

필요: .venv(zstandard, numpy, pillow), dotnet 7 SDK(asset_bfres2gltf 빌드), node 24 + web/node_modules(three, ffmpeg-static),
      web/tools/bin/gltfpack.exe (meshoptimizer v1.3 gltfpack-windows.zip, 없으면 자동으로 받음)
"""
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

import asset_common as A

STEPS = ["data", "map", "char", "fx", "sfx", "catalog", "verify"]
GLTFPACK_URL = "https://github.com/zeux/meshoptimizer/releases/download/v1.3/gltfpack-windows.zip"


def ensure_tools():
    exe = A.BIN / "gltfpack.exe"
    if not exe.exists():
        A.BIN.mkdir(parents=True, exist_ok=True)
        z = A.BIN / "gltfpack-windows.zip"
        A.log("gltfpack 받는 중", GLTFPACK_URL)
        urllib.request.urlretrieve(GLTFPACK_URL, z)
        zipfile.ZipFile(z).extractall(A.BIN)
    conv = A.ROOT / "analysis/assets_work/build/bin/Release/net7.0/asset_bfres2gltf.exe"
    if not conv.exists():
        subprocess.run(["dotnet", "build", "-c", "Release"], cwd=A.WEB / "tools/asset_bfres2gltf", check=True)
    if not (A.WEB / "node_modules/ffmpeg-static/ffmpeg.exe").exists():
        subprocess.run(["npm", "install"], cwd=A.WEB, check=True, shell=True)


def run(step):
    t = time.time()
    if step == "verify":
        subprocess.run(["node", str(A.WEB / "tools/asset_verify.mjs")], check=True)
    else:
        mod = {"data": "asset_data", "map": "asset_map", "char": "asset_char", "fx": "asset_fx", "sfx": "asset_sfx",
               "catalog": "asset_catalog"}[step]
        m = __import__(mod)
        (m.build if step == "catalog" else m.main)()
    A.log(f"== {step} {time.time() - t:.1f}s")


def cleanup():
    w = A.WORK
    for p in ("raw", "gl", "sfx_wav", "fx_tex", "fx_prim", "splplayer_pack", "static.vfxb", "static_prim.bfres",
              "dump_Player00.json", "static_prim_dump.json", "vslobby_dump.json"):
        q = w / p
        if q.is_dir():
            shutil.rmtree(q, ignore_errors=True)
        elif q.exists():
            q.unlink()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    steps = args or STEPS
    ensure_tools()
    for s in steps:
        if s not in STEPS:
            raise SystemExit(f"단계 이름: {STEPS}")
        if s == "verify":
            run("catalog") if "catalog" not in steps else None
        run(s)
    if "--keep" not in sys.argv and not args:
        cleanup()


if __name__ == "__main__":
    sys.argv[0] = __file__
    main()
