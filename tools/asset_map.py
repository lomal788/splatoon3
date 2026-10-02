"""맵 번들 데이터: placement.json, collision.json + collision.bin, env.json (maps/<mapId>/).

좌표는 원본 그대로(Y 위, 게임 단위). 배치 행렬 = T · Rz·Ry·Rx · S (Rotate 라디안) — gimmick/stage_misc.md §1.5 [추정: 액터 Rotate 도 레일 규약과 같다고 봄].
충돌: 배치 액터 중 정적(Static/Kinematic, 동적 표적·NPC 제외) 충돌을 월드 좌표로 구워 한 메시로 합친다.
  - hknpMeshShape(.bphsh): collision_mesh.decode_mesh 그대로(1/512 격자, (a,b,c),(a,c,d) 분할, 삼각형별 shapeTag → 재질)
  - Box 프리미티브: 12삼각형으로 구움.  Capsule/Sphere/Cylinder: 삼각형으로 만들지 않고 collision.json "primitives" 로 냄.

사용: PY web/tools/asset_map.py [mapId]   (기본 Lby_Lobby00)
"""
import json
import math
import struct
import sys

import numpy as np

import asset_common as A
import asset_data as D
import collision_mesh
import collision_tag0
import gimmick_phive
import spl_data

MAP = "Lby_Lobby00"
SCENE_PACK = "Scene/LobbyVersus.pack.zs"
BANC = "Banc/Lby_Lobby00.bcett.byml"

# 충돌을 구울 액터(정적 지형·파츠). 표적·목상·NPC·의자(캡슐)는 동적/범위 담당이라 제외하고 placement 에 형상만 남긴다.
COLLISION_SKIP_CLASSES = {"spl::SighterTarget", "spl::WoodenFigure", "spl::NpcLobbyJudge", "spl::LobbySubSeqObjNpc",
                          "spl::ObjLobbyKeepOutPlayerInSpecial"}
COLLISION_SKIP_GYML_PREFIX = ("Npc", "SighterTarget", "WoodenFigure", "Obj_LobbyKeepOutPlayerInSpecial")
FAR_AWAY = 500.0   # Mpt_Fld_LockerEditBG(x=-1000) 같은 화면 밖 배경은 제외

SAFE = 2 ** 53


def jsafe(v):
    """u64 해시 등 2^53 이상 정수 → 문자열 (JS JSON.parse 정밀도)."""
    if isinstance(v, bool):
        return v
    if isinstance(v, int) and (v >= SAFE or v <= -SAFE):
        return str(v)
    if isinstance(v, dict):
        return {k: jsafe(x) for k, x in v.items()}
    if isinstance(v, list):
        return [jsafe(x) for x in v]
    return v


def rot_zyx(r):
    x, y, z = r
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def trs(t, r, s):
    m = np.eye(4)
    m[:3, :3] = rot_zyx(r) @ np.diag(s)
    m[:3, 3] = t
    return m


def v3(d, default=0.0):
    if d is None:
        return [default] * 3
    return [d.get("X", default), d.get("Y", default), d.get("Z", default)]


def actor_info(gyml):
    """Gyml → className, model(fmdb 이름들), phive 요약"""
    if gyml.startswith("Work/"):
        return {"className": None, "models": [], "phive": None}
    chain, comps = D.actor_param(gyml, (gyml,))
    cls = None
    if comps.get("Behavior"):
        b = A.load_ref(comps["Behavior"], (gyml,))
        cls = (b or {}).get("ClassName")
    models = []
    if comps.get("ModelInfoRef"):
        mi = A.load_ref(comps["ModelInfoRef"], (gyml,)) or {}
        if mi.get("Fmdb"):
            models.append(A.base_name(mi["Fmdb"]))
        for sm in mi.get("SubModels") or []:
            if sm.get("Fmdb"):
                models.append(A.base_name(sm["Fmdb"]))
    ph = D.phive_summary(gyml, (gyml,))
    gpt = A.base_name(comps["GameParameterTable"]) if comps.get("GameParameterTable") else None
    return {"className": cls, "actorChain": chain, "models": models, "phive": ph, "gameParameterTable": gpt,
            "components": comps}


def load_banc():
    s = A.pack(SCENE_PACK)
    return A.byml(s[BANC])


# ---------------------------------------------------------------- placement
def build_placement(banc, infos):
    actors, types = [], {}
    for a in banc["Actors"]:
        g = a["Gyaml"]
        inf = infos[g]
        params = {k: v for k, v in a.items() if k not in (
            "Gyaml", "Hash", "InstanceID", "Name", "Phive", "SRTHash", "Translate", "Rotate", "Scale", "TeamCmp",
            "Layer", "Links", "Bakeable")}
        if g not in types:
            ph = inf["phive"]
            t = {"className": inf["className"], "actorChain": inf.get("actorChain"), "models": inf["models"],
                 "gameParameterTable": inf.get("gameParameterTable")}
            if ph:
                t["phive"] = {
                    "shapes": {k: {"file": v["file"], **(v["param"] or {})} for k, v in ph["shapes"].items()},
                    "rigidBodies": {k: {"file": v["file"], **(v["param"] or {})} for k, v in ph["rigidBodies"].items()}}
            types[g] = t
        actors.append({
            "hash": str(a["Hash"]),
            "instanceId": a.get("InstanceID"),
            "name": a.get("Name"),
            "gyml": g,
            "className": inf["className"],
            "pos": a.get("Translate", [0.0, 0.0, 0.0]),
            "rot": a.get("Rotate", [0.0, 0.0, 0.0]),
            "scale": a.get("Scale", [1.0, 1.0, 1.0]),
            "team": (a.get("TeamCmp") or {}).get("Team"),
            "layers": [a["Layer"]] if a.get("Layer") else [],
            "bakeable": bool(a.get("Bakeable", False)),
            "params": jsafe(params),
            "links": [{"dst": str(l["Dst"]), "name": l.get("Name")} for l in a.get("Links") or []],
        })
    rails = jsafe(banc.get("Rails") or [])
    for r in rails:
        r["hash"] = str(r.pop("Hash"))
        for p in r.get("Points") or []:
            p["hash"] = str(p.pop("Hash"))
    return {
        "version": 1,
        "map": MAP,
        "source": f"romfs/Pack/{SCENE_PACK} {BANC}",
        "units": {"pos": "game unit (원본 그대로, Y 위)", "rot": "rad, Euler XYZ, R = Rz·Ry·Rx [추정]",
                  "hash": "u64 → 10진 문자열", "scale": "배율"},
        "actors": actors,
        "actorTypes": types,
        "rails": rails,
        "aiGroups": jsafe(banc.get("AiGroups") or []),
    }


# ---------------------------------------------------------------- collision
class MatTable:
    def __init__(self):
        self.mats, self.keys = [], {}
        self.mat_names, self.tagnames = gimmick_phive.config()
        self.cfg = spl_data.byml((A.ROMFS / "Phive/Config/PhiveConfig.byml.zs").read_bytes())
        self.presets = {p["ComponentName"]: p for p in self.cfg["MaterialPresetCollection"]}

    def add(self, material, tags, layer_mask, sub_mask, raw, body):
        tags = sorted(set(tags))
        key = (material, tuple(tags), layer_mask, sub_mask, raw, body.get("LayerEntity"), body.get("SubLayerEntity"))
        if key in self.keys:
            return self.keys[key]
        layer = classify(layer_mask)
        paintable = layer == "Ground" and "ForceColPaintNotPaintable" not in tags
        if "ForceColPaintPaintable" in tags:
            paintable = True
        self.mats.append({
            "name": material, "layer": layer, "paintable": paintable,
            "flags": {"userShapeTags": tags, "layerHitMask": layer_mask, "subLayerHitMask": sub_mask,
                      "filterRaw": raw, "bodyLayer": body.get("LayerEntity"), "bodySubLayer": body.get("SubLayerEntity"),
                      "bodyMotionType": body.get("MotionType")},
        })
        self.keys[key] = len(self.mats) - 1
        return self.keys[key]

    def from_bphsh(self, ph, tag, body):
        mi, _, mask = ph["materials"][tag]
        name = self.mat_names[mi] if mi < len(self.mat_names) else str(mi)
        tags = [nm for v, nm in sorted(self.tagnames.items()) if mask & v]
        f = collision_mesh.filter_names(self.cfg, ph["filters"][tag]) if tag < len(ph["filters"]) else \
            {"raw": None, "layerHitMask": None, "subLayerHitMask": None}
        return self.add(name, tags, f["layerHitMask"], f["subLayerHitMask"], f["raw"], body)

    def from_presets(self, presets, body):
        material, layer, sub, tags = "Undefined", "SplSolidGround", "HitAll", []
        for p in presets:
            pr = self.presets.get(p)
            if not pr:
                continue
            if pr.get("Material"):
                material = pr["Material"]
            if pr.get("LayerHitMaskEntity"):
                layer = pr["LayerHitMaskEntity"]
            if pr.get("SubLayerHitMaskEntity"):
                sub = pr["SubLayerHitMaskEntity"]
            tags += pr.get("UserShapeTagMask") or []
        return self.add(material, tags, layer, sub, "preset:" + "+".join(presets), body)


def classify(layer_mask):
    m = layer_mask or ""
    if m in ("SplSolidGround", "HitAll"):
        return "Ground"
    if m == "SplWater":
        return "Water"
    if m in ("SplKeepOutPlayer", "SplKeepOutPlayerAndCamera"):
        return "KeepOut"
    if m == "SplKeepOutBullet":
        return "KeepOutBullet"
    if m == "SplInkThrough":
        return "InkThrough"
    if m == "SplPlayerThrough":
        return "PlayerThrough"
    if m == "SplCameraThrough":
        return "CameraThrough"
    return "Other"


def bphsh_blob(actor, phsh_ref):
    stem = A.base_name(phsh_ref)
    inner = f"Phive/Shape/Dcc/{stem}.Nin_NX_NVN.bphsh"
    return A.find_in_packs(inner, (actor,)), stem


BOX_TRIS = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4),
            (1, 5, 7), (1, 7, 3)]


def build_collision(banc, infos):
    mt = MatTable()
    pos_l, tri_l, mat_l, src_l, sources, prims = [], [], [], [], [], []
    vbase = 0
    stats = []
    for a in banc["Actors"]:
        g = a["Gyaml"]
        inf = infos[g]
        t = a.get("Translate", [0, 0, 0])
        if abs(t[0]) > FAR_AWAY or abs(t[2]) > FAR_AWAY:
            continue
        if inf["className"] in COLLISION_SKIP_CLASSES or g.startswith(COLLISION_SKIP_GYML_PREFIX):
            continue
        ph = inf["phive"]
        if not ph:
            continue
        M = trs(t, a.get("Rotate", [0, 0, 0]), a.get("Scale", [1, 1, 1]))
        done_shapes = set()
        for bname, b in ph["rigidBodies"].items():
            body = b["param"] or {}
            shape = ph["shapes"].get(body.get("ShapeName", "Main"))
            if not shape or not shape["param"]:
                continue
            if body.get("LayerEntity") in ("CustomReceiver", "SplPlayer", "SplObject") and g != "Fld_VSLobby":
                # 센서·피격체(플레이어 레이어) — 지형 충돌 아님
                continue
            if shape["file"] in done_shapes:
                continue
            done_shapes.add(shape["file"])
            sp = shape["param"]
            src = len(sources)
            sources.append({"hash": str(a["Hash"]), "gyml": g, "body": bname, "shape": shape["file"]})
            ntri0 = sum(len(x) for x in tri_l)
            for pm in sp.get("PhshMesh") or []:
                blob, stem = bphsh_blob(g, pm["PhshMeshPath"])
                if blob is None:
                    A.log("bphsh 없음", g, stem)
                    continue
                info, m, phm = collision_mesh.analyze(blob)
                if m is None:
                    A.log("hknpMeshShape 아님", stem)
                    continue
                p = np.c_[m["pos"].astype(np.float64), np.ones(len(m["pos"]))] @ M.T
                pos_l.append(p[:, :3].astype(np.float32))
                tri_l.append(m["tri"].astype(np.int64) + vbase)
                cache = {}
                mats = np.empty(len(m["tag"]), np.uint16)
                for i, tg in enumerate(m["tag"].tolist()):
                    if tg not in cache:
                        cache[tg] = mt.from_bphsh(phm, tg, body)
                    mats[i] = cache[tg]
                mat_l.append(mats)
                src_l.append(np.full(len(m["tri"]), src, np.uint16))
                vbase += len(p)
            for bx in sp.get("Box") or []:
                he = np.array(v3(bx.get("HalfExtents"), 0.5))
                c = np.array(v3(bx.get("Center")))
                ot = np.array(v3(bx.get("OffsetTranslation")))
                orot = rot_zyx([math.radians(x) for x in v3(bx.get("OffsetRotation"))])
                corners = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float) * he
                local = (orot @ (corners + c).T).T + ot
                p = np.c_[local, np.ones(8)] @ M.T
                pos_l.append(p[:, :3].astype(np.float32))
                tri_l.append(np.array(BOX_TRIS, np.int64) + vbase)
                mi = mt.from_presets(bx.get("MaterialPresets") or [], body)
                mat_l.append(np.full(12, mi, np.uint16))
                src_l.append(np.full(12, src, np.uint16))
                vbase += 8
            for kind in ("Capsule", "Sphere", "Cylinder"):
                for pr in sp.get(kind) or []:
                    prims.append({"type": kind.lower(), "source": src, "actorMatrix": M.T.reshape(-1).tolist(),
                                  "material": mt.from_presets(pr.get("MaterialPresets") or [], body),
                                  "shape": {k: (v3(v) if isinstance(v, dict) else v) for k, v in pr.items()
                                            if k != "MaterialPresets"}})
            stats.append((g, bname, shape["file"], sum(len(x) for x in tri_l) - ntri0))
    pos = np.concatenate(pos_l).astype("<f4")
    tri = np.concatenate(tri_l).astype("<u4")
    mat = np.concatenate(mat_l).astype("<u2")
    src = np.concatenate(src_l).astype("<u2")
    parts, off, layout = [], 0, {}
    for name, arr, cnt in (("positions", pos, len(pos)), ("indices", tri, len(tri) * 3),
                           ("triMaterial", mat, len(mat)), ("triSource", src, len(src))):
        b = arr.tobytes()
        layout[name] = {"offset": off, "count": int(cnt),
                        "type": {"positions": "f32x3", "indices": "u32", "triMaterial": "u16", "triSource": "u16"}[name]}
        pad = (-len(b)) % 4
        parts.append(b + b"\0" * pad)
        off += len(b) + pad
    binb = b"".join(parts)
    meta = {
        "version": 1,
        "vertexCount": int(len(pos)),
        "triangleCount": int(len(tri)),
        "layout": layout,
        "materials": mt.mats,
        "sources": sources,
        "primitives": prims,
        "bounds": {"min": pos.min(0).astype(float).tolist(), "max": pos.max(0).astype(float).tolist()},
        "source": "romfs Pack/Actor/<액터>.pack.zs Phive/Shape/Dcc/*.bphsh + ShapeParam Box, 배치 Lby_Lobby00",
        "notes": [
            "positions: 월드 좌표(배치 변환 적용, 원본 단위·Y 위). 지형 Fld_VSLobby 는 배치가 원점·단위라 원본 정점 그대로(1/512 격자)",
            "indices: 삼각형 3개씩 u32. 프리미티브 (a,b,c,d) c!=d 는 (a,b,c),(a,c,d) 두 개",
            "triMaterial: materials[] 인덱스. triSource: sources[] 인덱스(어느 배치 액터·형상에서 왔는지)",
            "primitives: 삼각형으로 굽지 않은 Capsule/Sphere/Cylinder. actorMatrix = 열 우선 4x4(T·Rz·Ry·Rx·S), shape 값은 원본(Center*, Radius, OffsetTranslation, OffsetRotation[deg])",
            "layer: 삼각형 필터(LayerHitMaskEntity)로 분류. paintable: [추정] Ground 이고 ForceColPaintNotPaintable 아님",
        ],
    }
    return meta, binb, stats


# ---------------------------------------------------------------- env
def aamp_dict(d, extra=()):
    import render_aamp
    nm = render_aamp.names(extra)
    N = lambda c: nm.get(c, "0x%08x" % c)
    ver, flags, size, pio_ver, pio_off = struct.unpack_from("<5I", d, 4)
    root = 0x30 + pio_off

    def val(p, t):
        if t == 0:
            return bool(struct.unpack_from("<I", d, p)[0])
        if t == 1:
            return struct.unpack_from("<f", d, p)[0]
        if t in (2, 17):
            return struct.unpack_from("<i" if t == 2 else "<I", d, p)[0]
        if t in (3, 4, 5, 6, 16):
            n = {3: 2, 4: 3, 5: 4, 6: 4, 16: 4}[t]
            return list(struct.unpack_from("<%df" % n, d, p))
        if t in (7, 8, 15, 20):
            return d[p:d.index(b"\0", p)].decode("utf8", "replace")
        return None

    def plist(p):
        crc, a, b = struct.unpack_from("<3I", d, p)
        lo, ln, oo, on = (a & 0xFFFF) * 4, a >> 16, (b & 0xFFFF) * 4, b >> 16
        out = {}
        objs = {}
        for i in range(on):
            q = p + oo + i * 8
            ocrc, w = struct.unpack_from("<2I", d, q)
            po, pn = (w & 0xFFFF) * 4, w >> 16
            o = {}
            for j in range(pn):
                r = q + po + j * 8
                pcrc, w2 = struct.unpack_from("<2I", d, r)
                doff, t = (w2 & 0xFFFFFF) * 4, w2 >> 24
                o[N(pcrc)] = val(r + doff, t)
            objs[N(ocrc)] = o
        if objs:
            out["objects"] = objs
        for i in range(ln):
            c2, = struct.unpack_from("<I", d, p + lo + i * 12)
            sub = plist(p + lo + i * 12)
            if sub:
                out[N(c2)] = sub
        return out

    return plist(root)


def build_env():
    s = A.pack(SCENE_PACK)
    inner = spl_data.sarc(spl_data.unzs(s["Env/VSLobby.Nin_NX_NVN.genvb"]))
    extra = ["Dynamic_SpotLightA", "Fld_VSLobby", "SpotLightRig", "SpotLight", "Attenuation", "AttenuationRadius",
             "InnerAngle", "OuterAngle", "Offset", "ModelName", "BoneName", "BindModel", "BindBone"]
    lobby = aamp_dict(inner["vslobby_day.baglenv"], extra)
    rendering = A.byml(s["Gyml/LobbyVersusLockerTest.game__gfx__parameter__RenderingDay.bgyml"])
    field_env = A.byml(s["Gyml/LobbyVersus.game__gfx__parameter__FieldEnv.bgyml"])
    default_env = None
    try:
        dsarc = spl_data.sarc(spl_data.unzs((A.ROMFS / "Env/Default.Nin_NX_NVN.genvb.zs").read_bytes()))
        for k, v in dsarc.items():
            if k.endswith(".baglenv") and "day" in k.lower():
                default_env = {"file": k, "params": aamp_dict(v)}
                break
    except Exception as e:  # noqa
        A.log("Default env 실패", e)
    return {
        "version": 1,
        "map": MAP,
        "teamColorLight": {
            "note": "graphics/team_color.md §5.3: Ink/InkBright 계산에 쓰는 활성 env 의 첫 DirectionalLight. 로비 MainLight→DirectionalLight 대응은 [추정]",
            "defaultDay": {"DiffuseColor": [1.0, 1.0, 1.0, 1.0], "Intensity": 4.0, "Direction": [-0.3, -0.7, -0.6]},
            "lobbyMainLight": rendering.get("Lighting", {}).get("MainLight"),
        },
        "rendering": rendering,
        "fieldEnv": field_env,
        "sceneEnv": {"file": "Env/VSLobby.Nin_NX_NVN.genvb vslobby_day.baglenv", "params": lobby},
        "defaultEnv": default_env,
    }


# ---------------------------------------------------------------- visual
VISUAL_ACTORS = ("Fld_VSLobby", "DObj_FldObj_DoorLobby", "DObj_VSLobbyScreen", "Obj_LobbyPod", "DObj_LobbyPlayerDevice",
                 "DObj_LobbyCapsuleMachine", "DObj_LobbyMusicSelecter", "DObj_Minigame", "DObj_MinigameChairBlue",
                 "DObj_MinigameChairYellow", "Obj_LobbyProjector", "DObj_FldObj_DoorVSLobbyLocker")
PART_MODELS = {  # 움직이거나 쓰러지는 사격장 파츠: 배치하지 않고 따로 낸다(range 담당이 배치). 파일: [(bfres, 모델, 클립 넣기)]
    "Obj_SighterTarget": [("Obj_SighterTarget", "Obj_SighterTarget", True), ("Obj_SighterTarget", "Fragment00", False),
                          ("Obj_SighterTarget", "Fragment01", False)],
    "Obj_SighterTargetMove": [("Obj_SighterTarget", "Obj_SighterTargetMove", True)],
    "Obj_LobbyCopyrobot": [("Obj_LobbyCopyrobot", "Obj_LobbyCopyrobot", True)],
}


def fmdb_split(ref):
    """'Work/Model/.../<bfres>/output/<model>.fmdb' → (bfres, model)"""
    parts = ref.split("/")
    i = parts.index("output")
    return parts[i - 1], parts[-1].rsplit(".", 1)[0]


def model_refs(gyml):
    ch, comps = D.actor_param(gyml, (gyml,))
    if not comps.get("ModelInfoRef"):
        return []
    mi = A.load_ref(comps["ModelInfoRef"], (gyml,)) or {}
    refs = [mi["Fmdb"]] if mi.get("Fmdb") else []
    refs += [m["Fmdb"] for m in mi.get("SubModels") or [] if m.get("Fmdb")]
    return [fmdb_split(r) for r in refs]


def build_visual(banc, out):
    import asset_model as M
    groups = {}
    for a in banc["Actors"]:
        g = a["Gyaml"]
        if g not in VISUAL_ACTORS:
            continue
        mat = trs(a.get("Translate", [0, 0, 0]), a.get("Rotate", [0, 0, 0]), a.get("Scale", [1, 1, 1]))
        for bfres, model in model_refs(g):
            groups.setdefault((bfres, model), []).append((f"{g}_{a['Hash']}", mat))
    items = []
    for (bfres, model), inst in groups.items():
        p, meta = M.convert(bfres, model)
        sp = p.with_suffix(".slim.glb")
        M.slim_file(p, sp)
        items.append((sp, inst))
        A.log(f"visual {bfres}/{model} x{len(inst)} verts={meta['vertexCount']} tris={meta['triangleCount']}")
    merged = M.GL / f"{MAP}_visual.glb"
    M.merge(items, merged, root_name=f"{MAP}__visual", keep_anims=False)
    sizes = {"visual.glb": M.gltfpack(merged, out / "visual.glb")}
    import asset_char as C
    A.clean_dir(out / "parts")
    mat_anims = {}
    for name, models in PART_MODELS.items():
        items = []
        for bfres, model, with_clips in models:
            sk, mats, vis = C.anim_names(bfres)
            if with_clips:
                p, meta = M.convert(bfres, model, clips=sorted(sk), tag=f"{model}__clips")
            else:
                p, meta = M.convert(bfres, model)
            sp = p.with_suffix(".slim.glb")
            M.slim_file(p, sp)
            items.append((sp, [(model, None)]))
            if with_clips and mats | vis:
                mat_anims[model] = C.bake_mat_anims(bfres, mats | vis, A.WORK / f"anim_{model}.json")
        merged = M.GL / f"part_{name}.glb"
        M.merge(items, merged, root_name=name, keep_anims=True)
        sizes[f"parts/{name}.glb"] = M.gltfpack(merged, out / f"parts/{name}.glb", extra=["-kn"])
    sizes["data/parts_anim_material.json"] = A.write_json(out / "data/parts_anim_material.json", {
        "note": "사격장 파츠 재질·가시성 애니(정수 프레임 베이크). 키 = 모델 이름. 스켈레탈 클립은 parts/<모델>.glb 안 원래 이름",
        "models": mat_anims})
    return sizes


def main():
    global MAP
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    if args:
        MAP = args[0]
    out = A.ASSETS / f"maps/{MAP}"
    banc = load_banc()
    infos = {g: actor_info(g) for g in sorted({a["Gyaml"] for a in banc["Actors"]})}
    sizes = {}
    pl = build_placement(banc, infos)
    sizes["placement.json"] = A.write_json(out / "placement.json", pl)
    meta, binb, stats = build_collision(banc, infos)
    sizes["collision.bin"] = A.write_bytes(out / "collision.bin", binb)
    sizes["collision.json"] = A.write_json(out / "collision.json", meta)
    sizes["env.json"] = A.write_json(out / "env.json", build_env())
    # 범위 담당이 쓸 액터별 파라미터 표(표적·목상)
    for g in ("SighterTarget", "SighterTarget_Large", "SighterTarget_Move", "SighterTarget_TipsTrial",
              "SighterTarget_TipsTrialMove", "WoodenFigure"):
        t = infos.get(g, {}).get("gameParameterTable")
        if t:
            for n, tab in D.table_chain(t, (g,)).items():
                sizes[f"params/{n}.json"] = A.write_json(out / f"params/{n}.json", tab)
    A.write_json(A.WORK / f"collision_stats_{MAP}.json", stats, pretty=True)
    # 검증 기준(asset_verify.mjs): 지형 bphsh 를 collision_mesh.py 통계 형식으로 따로 저장
    blob = A.find_in_packs("Phive/Shape/Dcc/Fld_VSLobby.Nin_NX_NVN.bphsh", ("Fld_VSLobby",))
    info, m, ph = collision_mesh.analyze(blob)
    mt = MatTable()
    info.update(collision_mesh.stats(m, ph, mt.mat_names, mt.tagnames, mt.cfg))
    A.write_json(A.WORK / "vslobby_col.json", {"Fld_VSLobby.bphsh": info}, pretty=True)
    if "--no-visual" not in sys.argv:
        sizes.update(build_visual(banc, out))
    for k, v in sizes.items():
        A.log(f"{v:>9}  maps/{MAP}/{k}")
    A.log("collision", meta["vertexCount"], "verts", meta["triangleCount"], "tris", len(meta["materials"]), "materials",
          len(meta["primitives"]), "primitives")


if __name__ == "__main__":
    main()
