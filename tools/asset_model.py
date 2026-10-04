"""모델 변환 공용: bfres → glb(asset_bfres2gltf.exe) → 재질 extras 정리 → 합치기 → gltfpack(meshopt + KTX2).

흐름
  romfs/Model/<bfres>.bfres.zs → WORK/raw/<bfres>.bfres (끝나면 지움)
  내장 BNTX → WORK/gl/<bfres>/tex/*.png (+json)       graphics_bntx.py
  asset_bfres2gltf.exe gltf ... --model <모델> → WORK/gl/<bfres>/<모델>.glb (+meta, 합성 텍스처 .mr/.ba png)
  slim_materials: extras.fres(재질 원자료 전부, 재질당 ~20KB) → extras.hoian(표시에 쓰는 것만)
  merge(): 여러 glb 를 노드 변환과 함께 한 장면으로 (메시 공유 인스턴스)
  gltfpack: -cc(meshopt) -tc(ETC1S) -tu normal(노멀은 UASTC) -vpf -vtf(위치·UV 실수 유지) -km -ke -af 0(애니 60fps 키 유지)

도구: web/tools/bin/gltfpack.exe (meshoptimizer v1.3 공식 배포, BasisU 인코더 내장)
"""
import copy
import json
import os
import re
import shutil
import struct
import subprocess
from pathlib import Path

import numpy as np

import asset_common as A
import graphics_bntx
import graphics_convert
import spl_data

EXE = A.ROOT / "analysis/assets_work/build/bin/Release/net7.0/asset_bfres2gltf.exe"
GLTFPACK = A.BIN / "gltfpack.exe"
GL = A.WORK / "gl"
RAW = A.WORK / "raw"


# ------------------------------------------------------------------ glb io
def read_glb(path):
    b = Path(path).read_bytes()
    assert b[:4] == b"glTF"
    jl = struct.unpack_from("<I", b, 12)[0]
    g = json.loads(b[20:20 + jl])
    binb = b""
    o = 20 + jl
    if o < len(b):
        bl = struct.unpack_from("<I", b, o)[0]
        binb = b[o + 8:o + 8 + bl]
    return g, binb


def write_glb(path, g, binb):
    if binb:
        if g.get("buffers"):
            g["buffers"][0]["byteLength"] = len(binb)   # 나머지(meshopt fallback 버퍼 등)는 그대로
            g["buffers"][0].pop("uri", None)
        else:
            g["buffers"] = [{"byteLength": len(binb)}]
    js = json.dumps(g, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    js += b" " * ((-len(js)) % 4)
    binb = binb + b"\0" * ((-len(binb)) % 4)
    total = 12 + 8 + len(js) + (8 + len(binb) if binb else 0)
    out = struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(js), 0x4E4F534A) + js
    if binb:
        out += struct.pack("<II", len(binb), 0x004E4942) + binb
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(out)
    return len(out)


# ------------------------------------------------------------------ bfres → glb
def raw_bfres(bfres):
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"{bfres}.bfres"
    if not out.exists():
        out.write_bytes(spl_data.load(A.ROMFS / f"Model/{bfres}.bfres.zs"))
    return out


def textures(bfres):
    tex = GL / bfres / "tex"
    if tex.exists() and any(tex.glob("*.json")):
        return tex
    tex.mkdir(parents=True, exist_ok=True)
    try:
        data = graphics_bntx.read_bntx(str(raw_bfres(bfres)))
    except ValueError:
        return tex
    for t in graphics_bntx.parse(data):
        m = graphics_bntx.to_png(t, str(tex))
        (tex / f"{t.name}.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    return tex


def convert(bfres, model=None, clips=(), anim_from=None, tag=None):
    """→ (glb 경로, meta). 이미 있으면 재사용(clips 가 바뀌면 tag 를 달리 줄 것)."""
    model = model or bfres
    tag = tag or model
    base = GL / bfres
    out = base / f"{tag}.glb"
    meta_p = base / f"{tag}.meta.json"
    tex = textures(bfres)
    if out.exists() and meta_p.exists():
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        for c in meta.get("combine", []):
            if not (tex / c["out"]).exists():
                graphics_convert.combine(str(tex), c)
        return out, meta
    cmd = [str(EXE), "gltf", str(raw_bfres(bfres)), str(out), "--model", model, "--texdir", str(tex), "--texuri", "tex/",
           "--meta", str(meta_p)]
    if clips:
        cmd += ["--anim", str(raw_bfres(anim_from or bfres))]
        for c in clips:
            cmd += ["--clip", c]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{bfres}/{model}: {r.stderr[-2000:]}{r.stdout[-2000:]}")
    A.log(r.stdout.strip())
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    for c in meta.get("combine", []):
        if not (tex / c["out"]).exists():
            graphics_convert.combine(str(tex), c)
    return out, meta


def cleanup_raw():
    if RAW.exists():
        shutil.rmtree(RAW)


# ------------------------------------------------------------------ material extras
PARAM_KEEP = re.compile(r"^(albedo_color|emission_color|emission_intensity|roughness|metalness|opacity|team_color_.*|"
                        r"two_color_.*|two_comp_paint_team|display_team_type|under_film_color|tex_mtx\d|.*scroll.*|"
                        r"const_color\d|const_value\d|transmission_rate|scattering_rate|blitz_.*|.*_team_.*)$")
RI_KEEP = re.compile(r"^(gsys_render_state_.*|gsys_alpha_test_.*|gsys_color_blend_.*|gsys_depth_test_.*|my_team_color_.*|"
                     r"substitute_color_.*|enable_overlay_paint_on_emission|spl_model_type|paint_.*|gsys_priority_hint|"
                     r"dynamic_alpha_fadeout|blitz_.*|gsys_static_depth_shadow.*|gsys_dynamic_depth_shadow.*)$")


def slim_material(m):
    ex = (m.get("extras") or {}).get("fres")
    if not ex:
        return
    sh = ex.get("shader") or {}
    opts = {k: v for k, v in (sh.get("options") or {}).items() if v != "<Default Value>"}
    samplers = {}
    for s in ex.get("samplers") or []:
        for slot in s.get("slots") or []:
            samplers[slot] = s.get("texture")
    params = {}
    for k, v in (ex.get("params") or {}).items():
        if PARAM_KEEP.match(k):
            params[k] = v.get("value") if isinstance(v, dict) else v
    ri = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in (ex.get("renderInfo") or {}).items()
          if RI_KEEP.match(k)}
    ud = {k: (v.get("value") if isinstance(v, dict) else v) for k, v in (ex.get("userData") or {}).items()}
    tc = {k: v for k, v in (ex.get("teamColor") or {}).items() if v is not None}
    for k in ("maskTcl", "map2cl"):
        if k in tc:
            tc[k] = Path(tc[k]).stem
    # texcoord_select_<슬롯> = N → 그 슬롯을 UV N 으로 샘플 (graphics/shaders.md §3.7, 값 2 = _u2 [판독])
    slot_key = {"normal": "normalTexture", "albedo": None, "base_color": None, "ao": "occlusionTexture",
                "emission": "emissiveTexture"}
    for k, v in opts.items():
        if k.startswith("texcoord_select_") and v.isdigit():
            key = slot_key.get(k[len("texcoord_select_"):])
            ti = m.get(key) if key else None
            if ti is not None:
                ti["texCoord"] = int(v)
    hoian = {"shader": f"{sh.get('archive')}/{sh.get('model')}", "options": opts, "samplers": samplers,
             "attribAssign": {k: v for k, v in (sh.get("attribAssign") or {}).items() if v != "<Default Value>"},
             "renderInfo": ri, "params": params, "userData": ud, "teamColor": tc, "gltfUsed": ex.get("gltfUsed")}
    m["extras"] = {"hoian": hoian}


def slim(g):
    for m in g.get("materials", []):
        slim_material(m)
    return g


# ------------------------------------------------------------------ merge
def _remap_texinfo(obj, tmap):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith("Texture") and isinstance(v, dict) and "index" in v:
                v["index"] = tmap[v["index"]]
            else:
                _remap_texinfo(v, tmap)
    elif isinstance(obj, list):
        for v in obj:
            _remap_texinfo(v, tmap)


def merge(items, out_path, root_name="root", keep_anims=True, anim_prefix=False):
    """items: [(glb 경로, [ (인스턴스이름, 4x4 행렬(np, 행 우선) 또는 None), ... ])].
    같은 glb 의 메시·재질·텍스처는 한 번만 넣고 인스턴스마다 노드 트리만 복제한다."""
    out_dir = Path(out_path).parent
    G = {"asset": {"version": "2.0", "generator": "splatoon3 web/tools/asset_model.py"}, "scene": 0,
         "scenes": [{"name": root_name, "nodes": [0]}], "nodes": [{"name": root_name, "children": []}],
         "meshes": [], "materials": [], "textures": [], "images": [], "samplers": [], "accessors": [],
         "bufferViews": [], "skins": [], "animations": []}
    bins = []
    boff = 0
    for path, instances in items:
        g, binb = read_glb(path)
        src_dir = Path(path).parent
        pad = (-boff) % 16
        if pad:
            bins.append(b"\0" * pad)
            boff += pad
        bins.append(binb)
        bv0, ac0, me0, ma0, tx0, im0, sm0 = (len(G[k]) for k in
                                              ("bufferViews", "accessors", "meshes", "materials", "textures", "images", "samplers"))
        for v in g.get("bufferViews", []):
            v = dict(v)
            v["buffer"] = 0
            v["byteOffset"] = v.get("byteOffset", 0) + boff
            G["bufferViews"].append(v)
        boff += len(binb)
        for a in g.get("accessors", []):
            a = dict(a)
            if "bufferView" in a:
                a["bufferView"] += bv0
            G["accessors"].append(a)
        imap = {}
        for k, im in enumerate(g.get("images", [])):
            im = dict(im)
            if "uri" in im:
                im["uri"] = os.path.relpath(src_dir / im["uri"], out_dir).replace("\\", "/")
                same = next((j for j, x in enumerate(G["images"]) if x.get("uri") == im["uri"]), None)
                if same is not None:   # 같은 png 는 한 번만 (여러 모델이 한 bfres 텍스처를 공유)
                    imap[k] = same
                    continue
            if "bufferView" in im:
                im["bufferView"] += bv0
            G["images"].append(im)
            imap[k] = len(G["images"]) - 1
        G["samplers"] += g.get("samplers", [])
        for t in g.get("textures", []):
            t = dict(t)
            if "source" in t:
                t["source"] = imap[t["source"]]
            if "sampler" in t:
                t["sampler"] += sm0
            G["textures"].append(t)
        tmap = {i: i + tx0 for i in range(len(g.get("textures", [])))}
        for m in g.get("materials", []):
            m = copy.deepcopy(m)
            _remap_texinfo(m, tmap)
            G["materials"].append(m)
        for me in g.get("meshes", []):
            me = copy.deepcopy(me)
            for p in me["primitives"]:
                p["attributes"] = {k: v + ac0 for k, v in p["attributes"].items()}
                if "indices" in p:
                    p["indices"] += ac0
                if "material" in p:
                    p["material"] += ma0
                for t in p.get("targets", []):
                    for k in t:
                        t[k] += ac0
            G["meshes"].append(me)
        roots = g["scenes"][g.get("scene", 0)]["nodes"]
        for inst_name, mat in instances:
            n0 = len(G["nodes"])
            for n in g["nodes"]:
                n = copy.deepcopy(n)
                if "mesh" in n:
                    n["mesh"] += me0
                if "children" in n:
                    n["children"] = [c + n0 for c in n["children"]]
                if "skin" in n:
                    n["skin"] += len(G["skins"])
                G["nodes"].append(n)
            for s in g.get("skins", []):
                s = dict(s)
                s["joints"] = [j + n0 for j in s["joints"]]
                if "skeleton" in s:
                    s["skeleton"] += n0
                if "inverseBindMatrices" in s:
                    s["inverseBindMatrices"] += ac0
                G["skins"].append(s)
            if keep_anims and inst_name == instances[0][0]:
                for an in g.get("animations", []):
                    an = copy.deepcopy(an)
                    for s in an["samplers"]:
                        s["input"] += ac0
                        s["output"] += ac0
                    for c in an["channels"]:
                        c["target"]["node"] += n0
                    if anim_prefix:
                        an["name"] = f"{inst_name}/{an.get('name')}"
                    G["animations"].append(an)
            holder = {"name": inst_name, "children": [r + n0 for r in roots]}
            if mat is not None:
                holder["matrix"] = [float(x) for x in np.asarray(mat).T.reshape(-1)]
            G["nodes"].append(holder)
            G["nodes"][0]["children"].append(len(G["nodes"]) - 1)
    for k in [k for k, v in G.items() if isinstance(v, list) and not v]:
        del G[k]
    binb = b"".join(bins)
    write_glb(out_path, G, binb)
    return out_path


# ------------------------------------------------------------------ gltfpack
def gltfpack(src, dst, extra=(), textures=True):
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(GLTFPACK), "-i", str(src), "-o", str(dst), "-cc", "-vpf", "-vtf", "-km", "-ke", "-af", "0"]
    if textures:
        cmd += ["-tc", "-tu", "normal", "-tj", str(os.cpu_count() or 4)]
    cmd += list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-3000:] + r.stdout[-3000:])
    if r.stderr.strip():
        A.log("gltfpack:", r.stderr.strip()[-800:])
    # gltfpack 은 animation.extras(frames, loop, fps, scaleMode)를 버린다 → 이름으로 되돌려 넣음
    sg, _ = read_glb(src)
    ax = {a.get("name"): a["extras"] for a in sg.get("animations", []) if a.get("extras")}
    if ax:
        dg, db = read_glb(dst)
        for a in dg.get("animations", []):
            if a.get("name") in ax:
                a["extras"] = ax[a["name"]]
        write_glb(dst, dg, db)
    return Path(dst).stat().st_size


def slim_file(src, dst):
    g, b = read_glb(src)
    slim(g)
    return write_glb(dst, g, b)
