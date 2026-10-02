"""PNG → KTX2(BasisU) 단독 파일. gltfpack 에 내장된 BasisU 인코더를 쓰기 위해 텍스처 하나짜리 운반용 glTF 를 만들고,
gltfpack -tc 결과 glb 의 이미지(bufferView, image/ktx2)를 그대로 꺼낸다(별도 인코더 설치 없음).

linear=True  → occlusionTexture 슬롯(attrib, 선형)    — 마스크·데이터
linear=False → baseColorTexture 슬롯(color, sRGB)    — 색
uastc=True   → UASTC(고품질), 기본 ETC1S

사용: PY web/tools/asset_ktx2.py <in.png> <out.ktx2> [--linear] [--uastc]
"""
import base64
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import asset_common as A
import asset_model as M

TRI = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0) + struct.pack("<6f", 0, 0, 1, 0, 0, 1)


def encode(png, out, linear=False, uastc=False, quality=None):
    png = Path(png)
    with tempfile.TemporaryDirectory(dir=A.WORK) as td:
        td = Path(td)
        shutil.copy(png, td / "t.png")
        tex = {"index": 0, "texCoord": 0}
        mat = {"name": "m"}
        if linear:
            mat["occlusionTexture"] = tex
            mat["pbrMetallicRoughness"] = {"baseColorFactor": [1, 1, 1, 1]}
        else:
            mat["pbrMetallicRoughness"] = {"baseColorTexture": tex}
        g = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
             "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "material": 0}]}],
             "materials": [mat], "textures": [{"source": 0}], "images": [{"uri": "t.png"}],
             "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
                            "min": [0, 0, 0], "max": [1, 1, 0]},
                           {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"}],
             "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36}, {"buffer": 0, "byteOffset": 36, "byteLength": 24}],
             "buffers": [{"byteLength": len(TRI), "uri": "data:application/octet-stream;base64," + base64.b64encode(TRI).decode()}]}
        (td / "c.gltf").write_text(json.dumps(g), encoding="utf-8")
        cmd = [str(M.GLTFPACK), "-i", str(td / "c.gltf"), "-o", str(td / "c.glb"), "-noq", "-tc"]
        if uastc:
            cmd += ["-tu"]
        if quality:
            cmd += ["-tq", str(quality)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(r.stderr + r.stdout)
        gg, b = M.read_glb(td / "c.glb")
        im = gg["images"][0]
        assert im.get("mimeType") == "image/ktx2", im
        bv = gg["bufferViews"][im["bufferView"]]
        data = b[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
    assert data[:12] == b"\xabKTX 20\xbb\r\n\x1a\n"
    return A.write_bytes(out, data)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    print(encode(a[0], a[1], linear="--linear" in sys.argv, uastc="--uastc" in sys.argv))
