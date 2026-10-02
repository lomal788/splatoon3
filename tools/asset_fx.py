"""이펙트 번들 effects/shooter/: emitters.json + tex/*.ktx2 (+ VAT .bin, 프리미티브 prim/*.glb).

원본: romfs/Effect/static.Nin_NX_NVN.esetb.byml.zs → PtclBin(VFXB v46) → 이미터 필드(vfx_emitter46.FIELDS, effect_sound/effect_resources.md §2.2)
  텍스처: VFXB GRTF 안 BNTX, 이미터 바이너리의 GTNT ID 일치(effect_vfxb46.scan_ids)로 샘플러 슬롯(0xD90 + 0x20·i)
  프리미티브: VFXB G3PR 안 BFRES. G3NT i 번째 ↔ BFRES 모델 i 번째 [추정: 개수 185 = 185 일치]

사용: PY web/tools/asset_fx.py
"""
import json
import subprocess

import numpy as np

import asset_common as A
import asset_ktx2 as K
import asset_model as M
import effect_bntx_float
import effect_vfxb as V
import effect_vfxb46
import graphics_bntx
import vfx_emitter46 as E

GROUP = "shooter"
ESETS = ["WpShtrBullet1Emit", "WpShtrMzfNml", "WpCmnBulletSplash1Emit",
         "CmnFloorSplash1Emit", "CmnFloorSplashNear1Emit", "CmnFloorSplashDist1Emit",
         "CmnNPFloorSplash1Emit", "CmnNPFloorSplashNear1Emit", "CmnNPFloorSplashDist1Emit",
         "CmnWallSplash1Emit", "CmnNpWallSplash1Emit",
         "WpCmnHit", "WpCmnHitEffective", "WpCmnHitCritical", "WpCmnHitInvalid", "WpCmnWaterSplash",
         "WpShtrHitMarker"]
CALC = {0: "CPU", 1: "GPU_TIME", 2: "GPU_SO"}
FOLLOW = {0: "ALL", 1: "NONE", 2: "POS"}
BILLBOARD = {3: "POLYGON_XY", 4: "POLYGON_XZ"}
ROT = {4: "YZX", 6: "ZXY"}
TYPE3 = {0: "FIXED", 1: "RANDOM", 2: "ANIM"}


def vfxb():
    p = A.WORK / "static.vfxb"
    if not p.exists():
        subprocess.run([str(A.PY), str(A.WEB / "tools/effect_esetb.py"), "ptcl",
                        str(A.ROMFS / "Effect/static.Nin_NX_NVN.esetb.byml.zs"), str(p)], check=True, capture_output=True)
    return V.Vfxb(str(p))


def trim(keys, n):
    return [[round(x, 6) for x in k] for k in keys[:max(n, 1)]]


def web_row(rec):
    """effect_resources.md §2.2.6 표의 열 + 애니 키"""
    return {
        "calc": CALC.get(rec["calcType"], rec["calcType"]),
        "follow": FOLLOW.get(rec["followType"], rec["followType"]),
        "life": rec["life"], "lifeRandom": rec["lifeRandom"], "infiniteLife": bool(rec["infiniteLife"]),
        "emission": {k: rec[k] for k in ("hasEmitEnd", "emitStart", "emitDuration", "emitRate", "emitRateRandom",
                                         "emitInterval", "emitIntervalRandom", "emitTiming", "positionRandom",
                                         "isEmitDistEnabled", "emitDistUnit", "emitDistMin", "emitDistMax")},
        "velocity": {k: rec[k] for k in ("allDirectionVel", "designatedDirScale", "designatedDir", "diffusionDirAngle",
                                         "xzDiffusion", "diffusionVel", "velRandom", "emitterVelInherit",
                                         "emitterVelInheritMax", "isWorldOrientedVelocity")},
        "gravity": {"dir": rec["gravityDir"], "scale": rec["gravityScale"], "world": bool(rec["isWorldGravity"])},
        "airRegist": rec["airRegist"], "momentumRandom": rec["momentumRandom"],
        "scale": {"base": rec["particleScale"], "randomPct": rec["particleScaleRandom"],
                  "keys": trim(rec["scaleKeys"], rec["numScaleKeys"]), "numKeys": rec["numScaleKeys"]},
        "rotate": {k: rec[k] for k in ("rotateInit", "rotateInitRand", "rotateAdd", "rotateAddRand", "rotateRegist",
                                       "staticFlags1")},
        "billboard": BILLBOARD.get(rec["billboardType"], rec["billboardType"]),
        "rotType": ROT.get(rec["rotType"], rec["rotType"]),
        "color": {"scale": rec["colorScale"],
                  "color0": {"type": TYPE3.get(rec["color0Type"]), "keys": trim(rec["color0Keys"], rec["numColor0Keys"])},
                  "alpha0": {"type": TYPE3.get(rec["alpha0Type"]), "keys": trim(rec["alpha0Keys"], rec["numAlpha0Keys"])},
                  "color1": {"type": TYPE3.get(rec["color1Type"]), "keys": trim(rec["color1Keys"], rec["numColor1Keys"])},
                  "alpha1": {"type": TYPE3.get(rec["alpha1Type"]), "keys": trim(rec["alpha1Keys"], rec["numAlpha1Keys"])},
                  "loopRate": rec["loopRate_c0_a0_c1_a1_scale"], "loopRandom": rec["loopRandom_c0_a0_c1_a1_scale"]},
        "fade": {k: rec[k] for k in ("fadeInFrames", "fadeOutFrames", "fadeInCurve", "fadeOutCurve", "fadeInMin",
                                     "fadeOutMin")},
        "emitterTransform": {k: rec[k] for k in ("emitterTrans", "emitterTransRand", "emitterRotate",
                                                 "emitterRotateRand", "emitterScale")},
        "volume": {k: rec[k] for k in ("volumeType", "volumeRadius", "volumeFormScale", "sweepLongitude",
                                       "sweepLatitude", "sweepStart", "caliberRatio")},
        "pivotOffset": rec["pivotOffset"], "drawPath": rec["drawPath"], "shaderIndex": rec["shaderIndex"],
        "randomSeedType": rec["randomSeedType"], "randomSeed": rec["randomSeed"],
    }


def main():
    out = A.ASSETS / f"effects/{GROUP}"
    for sub in ("tex", "prim"):
        A.clean_dir(out / sub)
    v = vfxb()
    texmap = {t["id"]: t["name"] for t in v.tex_desc}
    primidx = {t["id"]: i for i, t in enumerate(v.prim_desc)}
    prim_bfres = A.WORK / "static_prim.bfres"
    prim_bfres.write_bytes(v.bfres)
    dump = A.WORK / "static_prim_dump.json"
    if not dump.exists():
        subprocess.run([str(M.EXE), "dump", str(dump), str(prim_bfres)], check=True, capture_output=True)
    prim_names = [m["name"] for m in json.loads(dump.read_text(encoding="utf-8"))[0]["models"]]

    sets, need_tex, need_prim = {}, set(), set()
    for es, name, depth, parent, bo, em in E.emitters(v, set(ESETS)):
        rec = {"eset": es, "depth": depth, "parent": parent}
        for off, t, fname, _why in E.FIELDS:
            rec[fname] = E.read_field(v.d, bo, off, t)
        buf = v.d[bo:bo + E.SIZE]
        texs = []
        for off, tname in effect_vfxb46.scan_ids(buf, texmap):
            o = int(off, 16)
            slot = (o - 0xD90) // 0x20 if 0xD90 <= o < 0xE50 and (o - 0xD90) % 0x20 == 0 else None
            texs.append({"slot": slot, "offset": off, "name": tname})
            need_tex.add(tname)
        prim = None
        for off, _ in effect_vfxb46.scan_ids(buf, {k: "" for k in primidx}):
            pid = int.from_bytes(buf[int(off, 16):int(off, 16) + 8], "little")
            i = primidx[pid]
            prim = {"offset": off, "id": f"{pid:#x}", "index": i, "model": prim_names[i] if i < len(prim_names) else None}
            if prim["model"]:
                need_prim.add(prim["model"])
                prim["file"] = f"prim/{prim['model']}.glb"
        row = {"name": name, "depth": depth, "parent": parent, "attrs": [a.magic for a in em.attrs],
               **web_row(rec), "textures": texs, "primitive": prim,
               "fields": {k: x for k, x in rec.items() if not k.endswith("Keys")}}
        sets.setdefault(es, []).append(row)
    missing = [s for s in ESETS if s not in sets]

    # ---- 텍스처
    bntx = graphics_bntx.parse(v.bntx)
    texinfo, sizes = {}, {}
    tmp = A.WORK / "fx_tex"
    tmp.mkdir(parents=True, exist_ok=True)
    for t in bntx:
        if t.name not in need_tex:
            continue
        if (t.format >> 8) in effect_bntx_float.FLOAT_FORMATS:
            a = effect_bntx_float.decode_float(t)
            b = a.astype("<f2").tobytes()
            sizes[f"tex/{t.name}.bin"] = A.write_bytes(out / f"tex/{t.name}.bin", b)
            texinfo[t.name] = {"file": f"tex/{t.name}.bin", "kind": "vat", "format": "rgba16f",
                               "width": int(a.shape[1]), "height": int(a.shape[0]),
                               "note": "R16G16B16A16 FLOAT 원값(half, 행 우선 y=정점, x=시간 열) effect_resources.md §2.1"}
            continue
        m = graphics_bntx.to_png(t, str(tmp))
        png = tmp / m["files"][0]
        normal = t.name.endswith("_nrm")
        sizes[f"tex/{t.name}.ktx2"] = K.encode(png, out / f"tex/{t.name}.ktx2", linear=True, uastc=normal)
        texinfo[t.name] = {"file": f"tex/{t.name}.ktx2", "kind": "normal" if normal else "mask",
                           "width": t.width, "height": t.height, "srcFormat": f"{t.format:#06x}",
                           "colorSpace": "linear", "channelsNote": "BC4→R, BC5→RG (PNG 경유, 나머지 채널 0/255)"}
    # ---- 프리미티브
    for pm in sorted(need_prim):
        glb = A.WORK / f"fx_prim/{pm}.glb"
        glb.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(M.EXE), "gltf", str(prim_bfres), str(glb), "--model", pm, "--all"], check=True,
                       capture_output=True)
        g, b = M.read_glb(glb)
        for me in g.get("meshes", []):
            for p in me["primitives"]:
                at = p["attributes"]
                if "_C0" in at and "COLOR_0" not in at:
                    at["COLOR_0"] = at.pop("_C0")
        for k in ("materials", "textures", "images", "samplers"):
            g.pop(k, None)
        for me in g.get("meshes", []):
            for p in me["primitives"]:
                p.pop("material", None)
        M.write_glb(glb, g, b)
        sizes[f"prim/{pm}.glb"] = M.gltfpack(glb, out / f"prim/{pm}.glb", extra=["-kn", "-kv"], textures=False)

    xl = json.loads((A.ROOT / "analysis/effect_sound/elink_WeaponShooterNormal.json").read_text(encoding="utf-8"))
    triggers = []
    for at in xl.get("actionTriggers", []):
        ct = xl["callTables"][at["callTable"]]
        triggers.append({"actions": [a["name"] for a in xl["actions"] if xl["actionTriggers"].index(at) in a["triggers"]],
                         "eset": ct["params"].get("RuntimeAssetName"), "bone": ct["params"].get("Bone"),
                         "delay": ct["params"].get("Delay"), "matrix": ct["params"].get("Matrix")})
    doc = {
        "version": 1,
        "group": GROUP,
        "source": "romfs/Effect/static.Nin_NX_NVN.esetb.byml.zs PtclBin(VFXB v46)",
        "units": {"time": "frame(60fps)", "angle": "rad", "pct": "%"},
        "enums": {"calc": CALC, "follow": FOLLOW, "billboard": BILLBOARD, "rotType": ROT, "colorType": TYPE3},
        "notes": [
            "행 = effect_resources.md §2.2.6 웹 재현값 표의 열(calc/follow/life/emission/velocity/gravity/scale/rotate/billboard + 애니 키). fields = 판독 필드 전체 원값",
            "애니 키 [x,y,z,t] (t = 수명 비율), 개수만큼 잘라 냄. GPU_TIME 운동식은 effect_resources.md §2.2.5",
            "팀 잉크 색은 런타임에 곱함 [추정] — common/data/team_color.json",
            "prim/*.glb: VFXB G3PR 프리미티브. G3NT i ↔ BFRES 모델 i 대응은 [추정](개수 일치). 정점색 _c0 → COLOR_0",
        ],
        "splashKind": {"T0": 0.5235988, "T1": 1.0471976, "wallNormalY": 0.64144969,
                       "rule": "a = π/2 − |π/2 − θ|; kind = a < T0 ? 0(Floor) : a >= T1 ? 2(Dist) : 1(Near); 법선 y ≤ wallNormalY → 벽 슬롯 (effect_resources.md §3.1)"},
        "oneEmitterSlots": {"WpShtrBullet1Emit": {"n": 40, "count": 100}, "WpCmnBulletSplash1Emit": {"n": 40, "count": 160},
                            "floorSplash": {"n": 40, "count": 80}, "wallSplash": {"n": 40, "count": 80},
                            "WpCmnHit": {"n": 40, "count": 80}, "WpCmnWaterSplash": {"n": 40, "count": 80}},
        "weaponTriggers": triggers,
        "emitterSets": sets,
        "textures": texinfo,
        "missingEmitterSets": missing,
    }
    sizes["emitters.json"] = A.write_json(out / "emitters.json", doc)
    A.write_json(A.WORK / "sizes_fx.json", sizes, pretty=True)
    for k, s in sizes.items():
        A.log(f"{s:>9}  effects/{GROUP}/{k}")
    A.log("esets", len(sets), "missing", missing, "tex", len(texinfo), "prim", sorted(need_prim))


if __name__ == "__main__":
    main()
