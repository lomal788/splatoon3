"""캐릭터 번들 characters/Player00/ (+ 무기 모델 weapons/<id>/model.glb).

몸 Player00(SquidF) + _Hlf(변신 과도기) + 오징어형 Player_Squid/Squid + 기본 커스터마이즈·기어 + 탱크,
클립은 ASB(AS/SplPlayer.root.asb, AS/SplPlayerSquid.root.asb) 커맨드 트리에서 사격장에 필요한 것만 골라
anim/human.glb, anim/squid.glb(뼈 + 클립만)로 낸다. 재질·가시성 애니는 data/anim_material.json(정수 프레임 베이크).

기본 장비 근거(docs/impl/assets.md §3): v0 데이터에 '초기 장비' 표시가 없어 슬롯별 최소 Id 행(모델 있는 것)을 쓴다 [추정].

사용: PY web/tools/asset_char.py
"""
import json
import subprocess

import asset_common as A
import asset_model as M

CHAR = "Player00"
WEAPON = "Shooter_Normal_00"
WEAPON_MODEL = ("Wmn_Shooter_NormalT", "Wmn_Shooter_NormalT")
WEAPON_ABBR = "Shtr"     # ASB 'Nrml' 치환 (anim_state_machine.md §3)
EMOTE = "Win01"          # ASB '@' 치환 기본값

PARTS = {  # 파일 이름: (bfres, 모델, 근거)
    "Har_SQD000_F": ("Har_SQD000_F", None, "HairInfo Id 0 (Har_SQD000), SquidF → _F"),
    "Eyb_SQD000_F": ("Eyb_SQD000_F", None, "EyebrowInfo Id 0 (Eyb_SQD000) → _F"),
    "Btm_000_F": ("Btm_000_F", None, "BottomInfo Id 0 (Btm_000) → _F"),
    "Hed_FST000": ("Hed_FST000", None, "GearInfoHead 최소 Id 1 (FST=first, IsUnisex)"),
    "Clt_TES001_F": ("Clt_TES001_F", None, "GearInfoClothes 최소 Id 1001 (IsUnisex false → _F). Clt_FST001 은 v0 에 아이콘만 있음"),
    "Shs_SLO000": ("Shs_SLO000", None, "GearInfoShoes 최소 Id 1000 (IsUnisex). 신발 FST 행 없음"),
    "Tnk_Simple": ("Tnk_Simple", None, "TankInfo Tnk_000(Id 0) → PlayerTank ModelInfo Tnk_Simple"),
}

HUMAN_CMDS = ["WaitHold", "WalkHold", "WalkBackHold", "Jump_St", "Jump", "Jump_Ed", "JumpShoot_St", "JumpShoot",
              "JumpShoot_Ed", "Shoot", "WaitShoot", "WaitShootNG", "WalkShoot", "WalkLeftShoot", "WalkRightShoot",
              "WalkBackShoot", "ToSquid", "ToHuman", "ToHuman_WallJump", "WallJump_Ar", "WallJump_Ed",
              "ToHumanRespawn", "Damage", "WaitDamage", "WalkDamage", "Repelled", "Dead", "WaterDrown", "Slip",
              "SlipSlope", "ToHumanStandby_St", "ToHumanStandby", "ToHumanStandby_Ed", "ToSquidStandby"]
BODY_MAT_ANIMS = ["Color_Eye", "Color_Skin", "Blink", "Eye_Scroll"]


def asb_json(name):
    out = A.WORK / f"asb/{name}.json"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        src = A.WORK / f"asb/{name}.root.asb"
        src.write_bytes(A.pack("SplPlayer")[f"AS/{name}.root.asb"])
        subprocess.run([str(A.PY), str(A.WEB / "tools/state_asb.py"), str(src), "--json", str(out)], check=True,
                       capture_output=True)
    return json.loads(out.read_text(encoding="utf-8"))


def leaves(asb, cmds):
    nodes = {n["i"]: n for n in asb["nodes"]}
    roots = [c["root"] for c in asb["commands"] if cmds is None or c["name"] in cmds]
    out = {3: set(), 11: set(), 18: set()}
    seen = set()

    def walk(i):
        if i in seen or i not in nodes:
            return
        seen.add(i)
        n = nodes[i]
        if n["type"] in out:
            for s in n.get("strs") or []:
                out[n["type"]].add(s.replace("Nrml", WEAPON_ABBR).replace("@", EMOTE))
        for k in n.get("kids") or []:
            walk(k["child"] if isinstance(k, dict) else k)

    for r in roots:
        walk(r)
    return out


def anim_names(bfres):
    d = A.WORK / f"dump_{bfres}.json"
    if not d.exists():
        subprocess.run([str(M.EXE), "dump", str(d), str(M.raw_bfres(bfres))], check=True, capture_output=True)
    j = json.loads(d.read_text(encoding="utf-8"))[0]
    return ({a["name"] for a in j.get("skeletalAnims", [])}, {a["name"] for a in j.get("materialAnims", [])},
            {a["name"] for a in j.get("visibilityAnims", [])})


def strip_to_skeleton(src, dst):
    g, b = M.read_glb(src)
    for k in ("meshes", "materials", "textures", "images", "samplers", "skins"):
        g.pop(k, None)
    for n in g["nodes"]:
        n.pop("mesh", None)
        n.pop("skin", None)
    return M.write_glb(dst, g, b)


def bake_mat_anims(bfres, names, out):
    names = sorted(names)
    if not names:
        return None
    subprocess.run([str(M.EXE), "anim", str(M.raw_bfres(bfres)), str(out), "--only", ",".join(names)], check=True,
                   capture_output=True)
    return json.loads(out.read_text(encoding="utf-8"))


def team_textures(glb, bfres):
    """slim 된 glb 재질 extras.hoian.teamColor 의 마스크 텍스처 이름들 → png 경로"""
    g, _ = M.read_glb(glb)
    tex = M.GL / bfres / "tex"
    out = {}
    for m in g.get("materials", []):
        tc = (m.get("extras") or {}).get("hoian", {}).get("teamColor", {})
        for k in ("maskTcl", "map2cl"):
            if tc.get(k):
                meta = tex / f"{tc[k]}.json"
                if meta.exists():
                    png = json.loads(meta.read_text(encoding="utf-8"))["files"][0]
                    out[tc[k]] = tex / png
    return out


def model_glb(bfres, model, out, extra=()):
    p, meta = M.convert(bfres, model)
    sp = p.with_suffix(".slim.glb")
    M.slim_file(p, sp)
    size = M.gltfpack(sp, out, extra=["-kn"] + list(extra))
    return sp, meta, size


GEAR_ROWS = {"head": ("GearInfoHead", "Hed_FST000"), "clothes": ("GearInfoClothes", "Clt_TES001"),
             "shoes": ("GearInfoShoes", "Shs_SLO000"), "hair": ("HairInfo", "Har_SQD000"),
             "eyebrow": ("EyebrowInfo", "Eyb_SQD000"), "bottom": ("BottomInfo", "Btm_000"), "tank": ("TankInfo", "Tnk_000")}


def gear_data(cdir, K):
    """기본 장비 RSDB 행(하네스·알파마스크 등) + GearHeadParamSet + GearAlphaMask 텍스처(ktx2)"""
    out, sizes = {"modelType": "SquidF", "parts": {}}, {}
    masks = set()
    for slot, (table, row) in GEAR_ROWS.items():
        rows = A.romfs_byml(f"RSDB/{table}.Product.100.rstbl.byml.zs")
        r = next(x for x in rows if x["__RowId"] == row)
        e = {"table": table, "row": r, "model": next((k for k in PARTS if k.startswith(row)), None)}
        if r.get("HeadParamSetPath"):
            e["headParamSet"] = A.load_ref(r["HeadParamSetPath"], (row,))
        if r.get("AlphaMaskF"):
            masks.add(r["AlphaMaskF"])
        out["parts"][slot] = e
    tex = M.GL / "GearAlphaMask" / "tex"
    M.textures("GearAlphaMask")
    out["alphaMasks"] = {}
    for mname in sorted(masks):
        meta = tex / f"{mname}_Opa.json"
        if not meta.exists():
            out["alphaMasks"][mname] = None
            continue
        png = tex / json.loads(meta.read_text(encoding="utf-8"))["files"][0]
        rel = f"tex/alphamask/{mname}_Opa.ktx2"
        sizes[rel] = K.encode(png, cdir / rel, linear=True)
        out["alphaMasks"][mname] = rel
    out["note"] = ("v0 데이터에 초기 장비 표시가 없어 슬롯별 최소 Id 행(모델 있는 것)을 골랐다 [추정]. "
                   "harness: GearInfoClothes HarnessType/IsThinHarness/IsHideHarness → 탱크 뼈 Harness_* 가시성 "
                   "(graphics/player_assembly.md §6.1). alphaMasks: GearAlphaMask <AlphaMaskF>_Opa (몸 가림, 슬롯 바인딩 [미확정])")
    return out, sizes


def main():
    import asset_ktx2 as K
    cdir = A.ASSETS / f"characters/{CHAR}"
    for sub in ("tex", "parts", "anim"):
        A.clean_dir(cdir / sub)
    A.clean_dir(A.ASSETS / f"weapons/{WEAPON}/tex")
    sizes, info = {}, {"parts": {}, "clips": {}}
    team_tex = {}

    # ---- 몸·_Hlf·오징어
    for fname, (bfres, model) in {"body": ("Player00", "Player00"), "body_hlf": ("Player00_Hlf", "Player00_Hlf"),
                                  "squid": ("Player_Squid", "Squid")}.items():
        sp, meta, sz = model_glb(bfres, model, cdir / f"{fname}.glb")
        sizes[f"{fname}.glb"] = sz
        team_tex.update({f"{fname}/{k}": v for k, v in team_textures(sp, bfres).items()})
        info["parts"][fname] = {"bfres": bfres, "model": model, "meshes": len(meta["meshes"]),
                                "bones": meta["bones"], "verts": meta["vertexCount"], "tris": meta["triangleCount"]}
    for fname, (bfres, model, why) in PARTS.items():
        sp, meta, sz = model_glb(bfres, model or bfres, cdir / f"parts/{fname}.glb")
        sizes[f"parts/{fname}.glb"] = sz
        team_tex.update({f"{fname}/{k}": v for k, v in team_textures(sp, bfres).items()})
        info["parts"][fname] = {"bfres": bfres, "why": why, "meshes": len(meta["meshes"]), "bones": meta["bones"],
                                "verts": meta["vertexCount"], "tris": meta["triangleCount"]}

    # ---- 클립 선택 (ASB)
    hasb, sasb = asb_json("SplPlayer"), asb_json("SplPlayerSquid")
    hl = leaves(hasb, set(HUMAN_CMDS))
    sl = leaves(sasb, None)
    hsk, hmat, hvis = anim_names("Player00")
    ssk, smat, svis = anim_names("Player_Squid")
    hclips = sorted(c for c in hl[3] if c in hsk)
    sclips = sorted(c for c in sl[3] if c in ssk)
    info["clips"] = {"human": hclips, "squid": sclips,
                     "humanMissing": sorted(c for c in hl[3] if c not in hsk),
                     "squidMissing": sorted(c for c in sl[3] if c not in ssk),
                     "humanCommands": HUMAN_CMDS, "squidCommands": [c["name"] for c in sasb["commands"]]}
    for fname, bfres, model, clips in (("human", "Player00", "Player00", hclips), ("squid", "Player_Squid", "Squid", sclips)):
        p, meta = M.convert(bfres, model, clips=clips, tag=f"{model}__clips")
        sk = p.with_suffix(".skel.glb")
        strip_to_skeleton(p, sk)
        sizes[f"anim/{fname}.glb"] = M.gltfpack(sk, cdir / f"anim/{fname}.glb", extra=["-kn"], textures=False)
        info["clips"][f"{fname}Frames"] = {c["name"]: c.get("frames") for c in meta.get("clips", [])}

    # ---- 재질·가시성 애니
    hm = (hl[11] | set(BODY_MAT_ANIMS)) & hmat
    hv = hl[18] & hvis
    sm = (sl[11] & smat) | ({"Sqd_Blink"} & smat)
    sv = sl[18] & svis
    mat = {"human": bake_mat_anims("Player00", hm | hv, A.WORK / "anim_Player00.json"),
           "squid": bake_mat_anims("Player_Squid", sm | sv, A.WORK / "anim_Player_Squid.json")}
    sizes["data/anim_material.json"] = A.write_json(cdir / "data/anim_material.json", mat)
    # 재질 애니 텍스처 패턴(눈 색·깜빡임)이 쓰는 텍스처 — glb 에는 첫 장만 있으므로 전부 따로 낸다
    for side, bfres in (("human", "Player00"), ("squid", "Player_Squid")):
        names = set()
        for a in (mat[side] or {}).get("materialAnims", []):
            for mv in a["materials"].values():
                for pat in (mv.get("patterns") or {}).values():
                    names |= {x[1] for x in pat}
        tex = M.GL / bfres / "tex"
        for n in sorted(names):
            if not (tex / f"{n}.json").exists():
                info.setdefault("missingPatternTextures", []).append(f"{bfres}/{n}")
                continue
            meta = json.loads((tex / f"{n}.json").read_text(encoding="utf-8"))
            png = tex / meta["files"][0]
            sub = "squid" if side == "squid" else "body"
            sizes[f"tex/{sub}/{n}.ktx2"] = K.encode(png, cdir / f"tex/{sub}/{n}.ktx2",
                                                    linear="_Alb" not in n, uastc="_Nrm" in n)

    # ---- ASB·상태표
    sizes["data/asb_SplPlayer.json"] = A.write_json(cdir / "data/asb_SplPlayer.json", hasb)
    sizes["data/asb_SplPlayerSquid.json"] = A.write_json(cdir / "data/asb_SplPlayerSquid.json", sasb)
    rows = []
    lines = (A.ROOT / "analysis/state/player_states.tsv").read_text(encoding="utf-8").splitlines()
    head = lines[0].split("\t")
    for ln in lines[1:]:
        r = dict(zip(head, ln.split("\t")))
        rows.append({"id": int(r["id"]), "human": r["human_anim"] or None, "squid": r["squid_anim"] or None,
                     "blend": int(r["w2_val"], 16) if r.get("w2_val") else None, "flags": int(r["flags"], 16)})
    sizes["data/player_states.json"] = A.write_json(cdir / "data/player_states.json", {
        "source": "analysis/state/player_states.tsv (상태 표 0x7105630270, player/player_state.md)",
        "fields": {"blend": "상태 표 w2 값(요청 때 슬롯+0xdc 블렌드 프레임) [판독: anim_state_machine §1]", "flags": "상태 플래그"},
        "states": rows})

    # ---- 팀색 마스크 텍스처 (glTF 재질 슬롯에 없는 것: Tcl/2cl)
    for name, png in sorted(team_tex.items()):
        sizes[f"tex/{name}.ktx2"] = K.encode(png, cdir / f"tex/{name}.ktx2", linear=True)
    tt = {}
    for key in sorted(team_tex):
        part, name = key.split("/", 1)
        tt.setdefault(part, {})[name] = f"tex/{part}/{name}.ktx2"
    info["teamTextures"] = tt
    info["teamTexturesNote"] = ("glb 재질 extras.hoian.teamColor.maskTcl(_su0)/map2cl(_cp0) 텍스처 이름 → 이 표의 파일. "
                                "glTF 재질 슬롯에 없는 텍스처라 따로 KTX2(선형)로 냄")
    info["patternTexturesNote"] = "재질 애니(눈 색·깜빡임) 텍스처 패턴 = tex/body/<이름>.ktx2, tex/squid/<이름>.ktx2"
    gear, gsz = gear_data(cdir, K)
    sizes.update(gsz)
    sizes["data/gear.json"] = A.write_json(cdir / "data/gear.json", gear)
    sizes["data/character.json"] = A.write_json(cdir / "data/character.json", info)

    # ---- 무기 모델
    wdir = A.ASSETS / f"weapons/{WEAPON}"
    sp, meta, sz = model_glb(*WEAPON_MODEL, wdir / "model.glb")
    sizes[f"../../weapons/{WEAPON}/model.glb"] = sz
    for name, png in sorted(team_textures(sp, WEAPON_MODEL[0]).items()):
        sizes[f"../../weapons/{WEAPON}/tex/{name}.ktx2"] = K.encode(png, wdir / f"tex/{name}.ktx2", linear=True)

    A.write_json(A.WORK / "sizes_char.json", sizes, pretty=True)
    for k, v in sizes.items():
        A.log(f"{v:>9}  characters/{CHAR}/{k}")
    A.log("human clips", len(hclips), "squid clips", len(sclips), "missing", info["clips"]["humanMissing"],
          info["clips"]["squidMissing"])


if __name__ == "__main__":
    main()
