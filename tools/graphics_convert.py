"""Splatoon 3 model -> web assets (sample conversion only; C: has little free space).

usage:
  graphics_convert.py <ModelName> [--clip <anim name>]... [--anim-from <ModelName>]
    romfs/Model/<ModelName>.bfres.zs
      -> analysis/graphics/raw/<ModelName>.bfres         (zstd decompressed FRES v10)
      -> analysis/graphics/web/<ModelName>/tex/*.png     (embedded textures.bntx, mip0, BRTI channel selectors applied)
      -> analysis/graphics/web/<ModelName>/<ModelName>.glb (+ .meta.json)
      -> combined textures listed in meta 'combine' (metallicRoughness: G=rough B=metal, baseAlpha: RGB=alb A=opa)
  --keep-raw: keep analysis/graphics/raw/*.bfres (deleted by default; C: has little space)
  --anim-from: skeletal clips are taken from another FRES (Player01..03 use Player00 clips, model selector 0x7102656ac8).
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

R = "C:/dev/splatoon3"
sys.path.insert(0, R + "/web/tools")
import spl_data  # noqa: E402
import graphics_bntx  # noqa: E402

EXE = R + "/analysis/graphics/build/bin/Release/net7.0/graphics_bfres2gltf.exe"


def raw(name):
    out = f"{R}/analysis/graphics/raw/{name}.bfres"
    if not os.path.exists(out):
        d = spl_data.load(f"{R}/extracted/romfs/Model/{name}.bfres.zs")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(d)
    return out


def textures(name, tex_dir):
    os.makedirs(tex_dir, exist_ok=True)
    try:
        data = graphics_bntx.read_bntx(raw(name))
    except ValueError:
        return 0
    n = 0
    for t in graphics_bntx.parse(data):
        m = graphics_bntx.to_png(t, tex_dir)
        with open(os.path.join(tex_dir, t.name + ".json"), "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=1)
        n += 1
    return n


def combine(tex_dir, c):
    out = os.path.join(tex_dir, c["out"])
    if c.get("kind") == "baseAlpha":
        a = np.asarray(Image.open(os.path.join(tex_dir, c["alpha"])).convert("RGBA"))[..., 0]
        if c.get("base"):
            b = Image.open(os.path.join(tex_dir, c["base"])).convert("RGBA")
            if b.size != (a.shape[1], a.shape[0]):
                a = np.asarray(Image.fromarray(a).resize(b.size, Image.BILINEAR))
            b = np.asarray(b).copy()
        else:
            col = np.round(np.array(c["baseColor"]) ** (1 / 2.2) * 255).astype(np.uint8)  # linear factor -> sRGB png
            b = np.zeros(a.shape + (4,), np.uint8)
            b[..., :3] = col
        b[..., 3] = a
        Image.fromarray(b, "RGBA").save(out)
    else:  # metallicRoughness
        imgs = [Image.open(os.path.join(tex_dir, c[k])).convert("RGBA") if c.get(k) else None for k in ("roughness", "metallic")]
        size = max((im.size for im in imgs if im), key=lambda s: s[0] * s[1])
        o = np.zeros((size[1], size[0], 3), np.uint8)
        o[..., 1] = np.asarray(imgs[0].resize(size, Image.BILINEAR))[..., 0] if imgs[0] else 255
        o[..., 2] = np.asarray(imgs[1].resize(size, Image.BILINEAR))[..., 0] if imgs[1] else 0
        Image.fromarray(o, "RGB").save(out)


def main():
    args = sys.argv[1:]
    name = args[0]
    clips, anim_from, keep_raw = [], None, False
    i = 1
    while i < len(args):
        if args[i] == "--clip":
            clips.append(args[i + 1]); i += 2
        elif args[i] == "--keep-raw":
            keep_raw = True; i += 1
        elif args[i] == "--anim-from":
            anim_from = args[i + 1]; i += 2
        else:
            raise SystemExit("unknown " + args[i])
    base = f"{R}/analysis/graphics/web/{name}"
    tex = base + "/tex"
    n = textures(name, tex)
    cmd = [EXE, "gltf", raw(name), f"{base}/{name}.glb", "--texdir", tex, "--texuri", "tex/", "--meta", f"{base}/{name}.meta.json"]
    if clips:
        cmd += ["--anim", raw(anim_from or name)] + sum([["--clip", c] for c in clips], [])
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    meta = json.load(open(f"{base}/{name}.meta.json", encoding="utf-8"))
    for c in meta.get("combine", []):
        combine(tex, c)
    if not keep_raw:
        for r in {name, anim_from or name}:
            p = f"{R}/analysis/graphics/raw/{r}.bfres"
            if os.path.exists(p):
                os.remove(p)
    print(f"textures {n}, combined {len(meta.get('combine', []))} -> {base}")


if __name__ == "__main__":
    main()
