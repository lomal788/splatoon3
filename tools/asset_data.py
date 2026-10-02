"""데이터 번들: common/data, weapons/<id>/params|data, characters/<id>/params|data.

- param_defaults.json: analysis/param_reflect/<$type>.json 의 classes[0].defaults (생성자 기본값).
  값 읽기에 실패한 필드({"partial":true}, {"unwritten":true})는 빼고 analysis/assets_work/param_defaults_dropped.json 에 기록.
- 파라미터 표: extracted/params(Params.pack 해제본) 또는 액터 팩의 GameParameterTable 원본 JSON 그대로($parent 유지).
- RSDB·싱글턴·조합표(DamageRateInfo, HitEffect)는 필요한 형태로 압축(내용 변경 없음, 기본값 셀만 생략).

사용: PY web/tools/asset_data.py
"""
import glob
import json
from pathlib import Path

import asset_common as A

WEAPON = "Shooter_Normal_00"
CHAR = "Player00"


# param_reflect 에 없는 타입의 생성자 기본값 — player/gear_skills.md §4.3 [판독] 표 (Low/Mid/High)
GEAR_DEFAULTS = {
    "spl__PlayerGearSkillParam_HumanMoveUp": {
        "MoveVel_Human": (0.096, 0.12, 0.144), "MoveVel_Human_Slow": (0.088, 0.116, 0.144),
        "MoveVel_Human_Fast": (0.104, 0.124, 0.144), "MoveVelRt_Shot": (1.0, 1.125, 1.25)},
    "spl__PlayerGearSkillParam_SquidMoveUp": {
        "MoveVel_Stealth": (0.192, 0.216, 0.24), "MoveVel_Stealth_Slow": (0.1728, 0.216, 0.24),
        "MoveVel_Stealth_Fast": (0.2016, 0.2208, 0.24)},
    "spl__PlayerGearSkillParam_OpInkEffectReduction": {
        "OpInk_JumpVel": (0.08, 0.098, 0.11), "OpInk_MoveVel": (0.024, 0.05568, 0.0768),
        "OpInk_MoveVel_Shot": (0.012, 0.033, 0.042), "OpInk_MoveVel_ShotK": (0.5, 0.75, 1.0),
        "OpInk_DamagePerFrame": (0.003, 0.00225, 0.0015), "OpInk_DamageLmt": (0.4, 0.3, 0.2),
        "OpInk_ArmorHP": (0.0, 26.0, 39.0)},
}


# 문서에 판독된 기본값(리플렉션 표에 없거나 enum 이라 리플렉션이 못 읽는 타입). enum 은 데이터 표기 문자열
DOC_DEFAULTS = {
    "spl__BendCalculatorParam": {"Kp": 0.0, "Kd": 0.0},                                  # range/shooting_range.md §4.2
    "game__RailMovableSequentialParam": {"AttCalcType": "cInMove", "InterpolationType": "cLinear", "MoveSpeed": 1,
                                         "MoveTime": 1.0, "PatrolType": "cStop", "SpeedCalcType": "cTime",
                                         "WaitTime": 0.0},                               # gimmick/stage_misc.md §1.2
    "game__LiftGraphRailNodeParam": {"BreakTime": 0.0},                                  # 생성자 0x71012fabdc (Rotation 0)
}
# 리플렉션 도구(param_reflect.analyze)로 생성자 기본값을 직접 읽는 타입 (필드 이름 몇 개로 방문 함수를 찾음)
REFLECT_EXTRA = {"spl__SighterTargetParam": ["BombImpulsScaler", "BulletImpulsScaler", "PlayerImpulsScaler"]}


def reflect_extra():
    import param_reflect
    from xref import load_idx, load_img
    m, idx = load_img(), load_idx()
    tn_path = param_reflect.TYPE_NAMES_PATH
    tn = json.loads(tn_path.read_text()) if tn_path.exists() else {}
    out = {}
    for t, names in REFLECT_EXTRA.items():
        r = param_reflect.analyze(m, idx, names, tn)
        if r and r.get("classes"):
            out[t] = {k: v for k, v in r["classes"][0]["defaults"].items() if isinstance(v, (int, float, bool, str))}
            A.write_json(A.WORK / f"param_reflect_extra/{t}.json", r, pretty=True)
    return out


def param_defaults():
    out, dropped = {}, {}
    for f in sorted(glob.glob(str(A.ROOT / "analysis/param_reflect/*.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        cls = d.get("classes") or []
        if not cls:
            continue
        t = d.get("type") or Path(f).stem
        vals = {}
        for k, v in cls[0]["defaults"].items():
            if isinstance(v, (int, float, bool, str)):
                vals[k] = v
            else:
                dropped.setdefault(t, {})[k] = v
        out[t] = vals
    for t, v in {**DOC_DEFAULTS, **reflect_extra()}.items():
        out.setdefault(t, v)
    for t, fields in GEAR_DEFAULTS.items():
        if t in out:
            continue
        out[t] = {f"{k}_{lv}": A.f32(v) for k, vals in fields.items() for lv, v in zip(("Low", "Mid", "High"), vals)}
    A.write_json(A.WORK / "param_defaults_dropped.json", dropped, pretty=True)
    return out, dropped


def gpt_table(name, prefer=()):
    """GameParameterTable 원본 JSON. Params.pack 해제본 → 액터 팩 순."""
    f = A.PARAMS / f"Component/GameParameterTable/{name}.game__GameParameterTable.bgyml.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return A.load_ref(f"Work/Component/GameParameterTable/{name}.game__GameParameterTable.gyml", prefer)


def table_chain(name, prefer=()):
    """표와 $parent 체인 전부 → {표이름: JSON}"""
    out = {}
    while name and name not in out:
        t = gpt_table(name, prefer)
        if t is None:
            A.log("표 없음", name)
            break
        out[name] = t
        name = A.base_name(t["$parent"]) if t.get("$parent") else None
    return out


def actor_param(name, prefer=()):
    """ActorParam 과 $parent 체인을 합친 Components(자식 우선) + 체인 이름."""
    chain, comps = [], {}
    ref = f"Work/Actor/{name}.engine__actor__ActorParam.gyml"
    while ref:
        d = A.load_ref(ref, prefer + (A.base_name(ref),))
        if d is None:
            break
        chain.append(A.base_name(ref))
        for k, v in (d.get("Components") or {}).items():
            comps.setdefault(k, v)
        ref = d.get("$parent")
    return chain, comps


def phive_summary(actor, prefer=()):
    """PhysicsRef → ControllerSet → 셰이프·강체 레이어 요약(원본 값 그대로)."""
    chain, comps = actor_param(actor, prefer)
    pref = prefer + (actor,)
    phys = comps.get("PhysicsRef")
    if not phys:
        return None
    pp, seen = {}, set()
    ref = phys
    while ref and ref not in seen:
        seen.add(ref)
        d = A.load_ref(ref, pref) or {}
        for k, v in d.items():
            pp.setdefault(k, v)
        ref = d.get("$parent")
    cs_ref = pp.get("ControllerSetPath")
    cs, seen = {}, set()
    ref = cs_ref
    while ref and ref not in seen:
        seen.add(ref)
        d = A.load_ref(ref, pref) or {}
        for k, v in d.items():
            cs.setdefault(k, v)
        ref = d.get("$parent")
    shapes = {}
    for e in cs.get("ShapeNamePathAry") or []:
        shapes[e["Name"]] = {"file": A.base_name(e["FilePath"]), "param": A.load_ref(e["FilePath"], pref)}
    bodies = {}
    for e in cs.get("RigidBodyEntityNamePathAry") or []:
        bodies[e["Name"]] = {"file": A.base_name(e["FilePath"]), "param": A.load_ref(e["FilePath"], pref)}
    chars = {}
    if cs.get("PathCharacterController"):
        chars["CharacterController"] = A.load_ref(cs["PathCharacterController"], pref)
    return {"actorChain": chain, "physics": pp, "controllerSet": {k: v for k, v in cs.items()
            if k not in ("ShapeNamePathAry", "RigidBodyEntityNamePathAry")},
            "shapes": shapes, "rigidBodies": bodies, **chars}


def resolve_refs(ref, prefer=(), depth=4):
    """'Work/...gyml' 참조를 따라가 {"$ref": 이름, ...내용} 으로 펼친다($parent 는 펼쳐서 "$parentValue")."""
    d = A.load_ref(ref, prefer)
    if d is None:
        return {"$ref": ref, "$missing": True}

    def walk(v, dep):
        if isinstance(v, dict):
            return {k: (walk(x, dep) if k != "$parent" else x) for k, x in v.items()}
        if isinstance(v, list):
            return [walk(x, dep) for x in v]
        if isinstance(v, str) and v.startswith("Work/") and v.endswith(".gyml") and dep > 0:
            return resolve_refs(v, prefer, dep - 1)
        return v

    out = {"$ref": ref, **walk(d, depth)}
    if d.get("$parent") and depth > 0:
        out["$parentValue"] = resolve_refs(d["$parent"], prefer, depth - 1)
    return out


def combination_tables():
    dr = json.loads((A.ROOT / "analysis/combat/DamageRateInfoConfig.json").read_text(encoding="utf-8"))
    rows = {}
    for c in dr["CellList"].values():
        if "DamageRate" in c:
            rows.setdefault(c["RowKey"], {})[c["ColumnKey"]] = c["DamageRate"]
    allrows = sorted({c["RowKey"] for c in dr["CellList"].values()})
    allcols = sorted({c["ColumnKey"] for c in dr["CellList"].values()})
    damage = {"source": "Bootup.pack System/CombinationDataTableData/spl__DamageRateInfoConfig",
              "default": 1.0, "rowKeys": allrows, "colKeys": allcols, "rows": rows}
    he = json.loads((A.ROOT / "analysis/combat/HitEffectConfig.json").read_text(encoding="utf-8"))
    hrows = {}
    for c in he["CellList"].values():
        v = {k: c[k] for k in ("E1", "E2", "S1", "S2") if c.get(k)}
        if v:
            hrows.setdefault(c["RowKey"], {})[c["ColumnKey"]] = v
    hit = {"source": "Bootup.pack System/CombinationDataTableData/Default_spl__HitEffectConfig",
           "rowKeys": sorted({c["RowKey"] for c in he["CellList"].values()}),
           "colKeys": sorted({c["ColumnKey"] for c in he["CellList"].values()}), "rows": hrows}
    return damage, hit


def rsdb(name):
    return A.romfs_byml(f"RSDB/{name}.Product.100.rstbl.byml.zs")


def team_color():
    sing = A.pack("SingletonParam.pack.zs")

    def s(t):
        return A.byml(sing[f"Gyml/Singleton/{t}.{t}.bgyml"])

    sets = []
    for r in rsdb("TeamColorDataSet"):
        r = dict(r)
        r["name"] = A.base_name(r.pop("__RowId"))
        sets.append(r)
    offs = {A.base_name(r["__RowId"]): {k: v for k, v in r.items() if k != "__RowId"} for r in rsdb("TeamColorOffset")}
    return {
        "colorNames": ["Original", "Pale", "Bright", "Dark", "HueBright", "HueBrightHalf", "HueDark", "HueDarkHalf",
                       "Model", "Ink", "InkBright", "InkLame", "InkLameRare", "Silhouette"],
        "tagEnum": ["VersusRegular", "VersusOption", "Mission", "MissionOption", "VersusTricolor",
                    "VersusTricolorOption", "Coop", "CoopOption", "Gambit", "Blitz"],
        "dataSets": sets,
        "offsets": offs,
        "hueDirPeak": s("game__gfx__parameter__TeamColorHueDirPeak"),
        "inkColorCorrection": s("game__gfx__InkColorCorrection"),
        "inkColorCorrectionDefaults": {
            "CorrectionInkMain": {"DownBrightnessLuminanceRate": 0.35, "DownBrightnessRate6": 0.5,
                                  "DownBrightnessRate1": 0.1, "MaxSaturation": 1.0, "MinBright": 0.01},
            "CorrectionInkSSS": {"BrightnessOffset": A.f32(0.1), "BrightnessOffsetLuminance": 0.5}},
        "note": "graphics/team_color.md. inkColorCorrectionDefaults = 생성자 기본값(데이터에 없는 필드는 이 값)",
    }


def singletons():
    sing = A.pack("SingletonParam.pack.zs")
    out = {}
    for t in ("spl__VersusConstant", "spl__LobbyConstant", "spl__GearSkillTraitsParam", "game__CameraModuleParam",
              "game__RumbleModuleParam", "spl__SoundSpatialConfig", "spl__KebaInkMgrConstant",
              "spl__gfx__parameter__KebaInkPlayerReaction"):
        out[t] = A.byml(sing[f"Gyml/Singleton/{t}.{t}.bgyml"])
    return out


def phive_layers():
    c = A.romfs_byml("Phive/Config/PhiveConfig.byml.zs")
    keep = {}
    for k in ("LayerEntityCollection", "SubLayerEntityCollection", "LayerHitMaskEntityCollection",
              "SubLayerHitMaskEntityCollection", "UserShapeTagMaskCollection", "UserShapeTagCollection",
              "MaterialPresetCollection", "MaterialCollection"):
        if k in c:
            keep[k] = c[k]
    keep["note"] = "romfs/Phive/Config/PhiveConfig.byml.zs 발췌(원본 그대로). 충돌 재질 이름·레이어 비트 의미"
    return keep


def ink_tex_info():
    rows = []
    for r in rsdb("InkTexInfo"):
        r = dict(r)
        r["name"] = A.base_name(r.pop("__RowId"))
        rows.append(r)
    return {"source": "RSDB/InkTexInfo", "rows": rows}


STAMP_PREFIX = ("Shot00", "Shot01", "Shot02", "Shot03", "Shot04", "WallDrip00", "WallDrip01", "Disk", "Rectangle")


def ink_stamps():
    """Model/InkTexture.bfres 의 도색 스탬프(BC4) → R8. paint/paint_and_score.md §3.4 (Shot00_<k> 등)"""
    import base64
    import struct
    import numpy as np
    import graphics_bntx as G
    d = A.spl_data.load(A.ROMFS / "Model/InkTexture.bfres.zs")
    i = d.find(b"BNTX")
    sz = struct.unpack_from("<I", d, i + 0x1C)[0]
    out = {}
    for t in G.parse(d[i:i + sz]):
        if not t.name.startswith(STAMP_PREFIX) or t.name.startswith("DiskHD"):
            continue
        img = G.decode_layer(t)
        a = np.asarray(img)[..., 0].astype(np.uint8)
        out[t.name] = {"w": int(a.shape[1]), "h": int(a.shape[0]), "format": f"{t.format:#06x}",
                       "data": base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()}
    return dict(sorted(out.items()))   # paint 요청 형식: { 이름: {w,h,data} } (출처는 docs/impl/assets.md)


def weapon_info():
    rows = json.loads((A.ROOT / "analysis/combat/rsdb/WeaponInfoMain.json").read_text(encoding="utf-8"))
    row = next(r for r in rows if r.get("__RowId") == WEAPON)
    sub = rsdb("WeaponInfoSub")
    sp = rsdb("WeaponInfoSpecial")
    subrow = next((r for r in sub if r.get("__RowId") == row["SubWeapon"]), None)
    sprow = next((r for r in sp if r.get("__RowId") == row["SpecialWeapon"]), None)
    return {"main": row, "sub": subrow, "special": sprow}


def main():
    sizes = {}
    out = A.ASSETS
    # ---- common
    defaults, dropped = param_defaults()
    sizes["common/data/param_defaults.json"] = A.write_json(out / "common/data/param_defaults.json", defaults)
    damage, hit = combination_tables()
    sizes["common/data/damage_rate_info.json"] = A.write_json(out / "common/data/damage_rate_info.json", damage)
    sizes["common/data/hit_effect.json"] = A.write_json(out / "common/data/hit_effect.json", hit)
    sizes["common/data/team_color.json"] = A.write_json(out / "common/data/team_color.json", team_color())
    sizes["common/data/singletons.json"] = A.write_json(out / "common/data/singletons.json", singletons())
    sizes["common/data/phive_config.json"] = A.write_json(out / "common/data/phive_config.json", phive_layers())
    sizes["common/data/ink_tex_info.json"] = A.write_json(out / "common/data/ink_tex_info.json", ink_tex_info())
    sizes["common/data/ink_stamps.json"] = A.write_json(out / "common/data/ink_stamps.json", ink_stamps())
    lf = json.loads((A.ROOT / "analysis/combat/layer_filter_bullet.json").read_text(encoding="utf-8"))
    sizes["common/data/layer_filter_bullet.json"] = A.write_json(out / "common/data/layer_filter_bullet.json", lf)

    # ---- weapon
    wdir = out / f"weapons/{WEAPON}"
    info = weapon_info()
    sizes[f"weapons/{WEAPON}/data/weapon_info.json"] = A.write_json(wdir / "data/weapon_info.json", info)
    spec_actor = A.base_name(info["main"]["SpecActor"])
    _, wcomps = actor_param(spec_actor, (spec_actor,))
    tables = {}
    tables.update(table_chain(A.base_name(wcomps["GameParameterTable"]), (spec_actor,)))
    res = A.load_ref(wcomps["ActorReservation"], (spec_actor,)) if wcomps.get("ActorReservation") else None
    bullet_actors = []
    for e in (res or {}).get("RequestList", []):
        a = e.get("ActorName") or e.get("Actor") or ""
        bullet_actors.append(A.base_name(a) if "/" in a else a)
    if not bullet_actors:
        bullet_actors = ["BulletShooterBase", "BulletSplashShooter", "BulletWallDrop"]
    bullets = {}
    for b in bullet_actors:
        chain, comps = actor_param(b, (b,))
        if comps.get("GameParameterTable"):
            tables.update(table_chain(A.base_name(comps["GameParameterTable"]), (b,)))
        beh = A.load_ref(comps["Behavior"], (b,)) if comps.get("Behavior") else None
        body = resolve_refs(comps["BulletBodyRef"], (b,)) if comps.get("BulletBodyRef") else None
        bullets[b] = {"actorChain": chain, "components": comps, "behavior": beh, "bulletBody": body,
                      "bulletSetting": resolve_refs(comps["BulletSetting"], (b,)) if comps.get("BulletSetting") else None,
                      "phive": phive_summary(b, (b,))}
    bsi = {r["__RowId"]: r for r in json.loads((A.ROOT / "analysis/combat/rsdb/BulletSettingInfo.json").read_text(encoding="utf-8"))}
    bullet_setting = {b: bsi.get(b) for b in bullet_actors}
    for b in bullet_actors:
        bullets[b]["bulletSettingInfo"] = bsi.get(b)
    sizes[f"weapons/{WEAPON}/data/bullet_setting.json"] = A.write_json(wdir / "data/bullet_setting.json", {
        "source": "RSDB/BulletSettingInfo (행 = 탄 액터 이름). 컴포넌트 BulletSetting 참조 파일은 romfs 에 없음",
        "rows": bullet_setting})
    for n, t in tables.items():
        sizes[f"weapons/{WEAPON}/params/{n}.json"] = A.write_json(wdir / f"params/{n}.json", t)
    wbeh = A.load_ref(wcomps["Behavior"], (spec_actor,)) if wcomps.get("Behavior") else None
    spec = {"specActor": spec_actor, "components": wcomps, "behavior": wbeh, "actorReservation": res,
            "bullets": bullets, "tables": sorted(tables)}
    sizes[f"weapons/{WEAPON}/data/weapon_spec.json"] = A.write_json(wdir / "data/weapon_spec.json", spec)

    # ---- character (플레이어 액터 SplPlayer)
    cdir = out / f"characters/{CHAR}"
    pchain, pcomps = actor_param("SplPlayer", ("SplPlayer",))
    ptables = table_chain(A.base_name(pcomps["GameParameterTable"]), ("SplPlayer",))
    for n, t in ptables.items():
        sizes[f"characters/{CHAR}/params/{n}.json"] = A.write_json(cdir / f"params/{n}.json", t)
    extra = {}
    for k in ("BulletShotDirAllInkActionParam", "PlayerCustom", "PlayerFullModelRef", "LifeNumber", "CircleShadow"):
        if pcomps.get(k):
            extra[k] = A.load_ref(pcomps[k], ("SplPlayer",))
    player = {"actorChain": pchain, "components": pcomps, "phive": phive_summary("SplPlayer", ("SplPlayer",)),
              "componentParams": extra}
    sizes[f"characters/{CHAR}/data/player_actor.json"] = A.write_json(cdir / "data/player_actor.json", player)

    A.write_json(A.WORK / "sizes_data.json", sizes, pretty=True)
    for k, v in sizes.items():
        A.log(f"{v:>9}  {k}")
    A.log("기본값 제외 필드:", sum(len(v) for v in dropped.values()))


if __name__ == "__main__":
    main()
