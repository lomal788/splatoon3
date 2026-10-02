"""효과음 번들 sfx/<group>/: *.ogg(Opus) + sfx.json.

원본: SLink2(romfs/... slink2.Product.100.bslnk, effect_xlink.py) 사용자 트리 중 사격장에 필요한 키만 골라
  호출 표(callTables)를 원래 번호 그대로 남기고(쓰지 않는 칸은 null, 범위 children [첫, 끝] 유지)
  RuntimeAssetName → Sound/Resource/*.bars.zs 의 BWAV(DSP-ADPCM) → 자체 디코드(PCM16) → ffmpeg(libopus) .ogg
  DistanceParamSetName → Sound/Attenuation 아카이브의 AATN + 커브(AROC/AUDC/AADR/AACL) 값

PlayerFoot 의 GndMaterial 분기는 로비 충돌 재질(maps/Lby_Lobby00/collision.json materials[].name)에 없는 재질 분기를
  {"pruned": true} 로 남기고 소리를 빼서 크기를 줄인다(그 재질 위에서는 소리 없음 — 이 맵에는 없음).

사용: PY web/tools/asset_sfx.py
"""
import json
import struct
import subprocess
import wave
import zlib

import asset_common as A
import sound_alto
import sound_bars

SLINK = A.ROOT / "analysis/effect_sound/slink2.Product.100.bslnk"
FFMPEG = A.WEB / "node_modules/ffmpeg-static/ffmpeg.exe"
RES = A.ROMFS / "Sound/Resource"

PLAYER_SKIP = ("Super", "Sp", "ナイス", "ジェットパック", "チャクチ", "イクラ", "スフィア", "カニ", "ショクワンダー", "サメ",
               "ガチホコ", "大ジャンプ", "Grind", "グラインド", "レール", "Aim", "Umbrella", "チャージキープ", "Devil",
               "Marking", "RainCloud", "Signal", "Attention", "Coop", "マッチ開始", "スポナー", "D1_", "D3_", "D5", "Demo",
               "Armor", "ミッション", "ヤカン", "Inhole", "OutSplash", "パイプライン", "ForcedShutdown", "ステージ開始",
               "ウキワ", "射出", "DeadSteam", "時間終了", "GyroPitchBase", "SquidBeakon", "投てき失敗")
GROUPS = {
    "shooter": {"WeaponShooterNormal": None},
    "player": {"Player_Focused": "player", "PlayerFoot": ["FootMainL", "FootMainR", "FootUpL", "FootUpR", "FootInkL",
                                                          "FootInkR", "FootUpInkL", "FootUpInkR", "SlipSlope", "ジャンプ", "着地"],
               "PlayerTank": None},
    "common": {"HitEffect": ["ヒット", "ヒット_短減衰", "3連ヒット", "クリティカルヒット", "ノーダメージ", "飛沫", "インクヒット",
                             "インクヒット_多量", "インク被弾", "水没", "水没_大"],
               "SighterTarget": None, "WoodenFigure": None},
}
# DESIGN.md §4 이벤트 → (그룹, 사용자, 키). 키 선택은 이름 기반 [추정]
EVENTS = {
    "Fire": [("shooter", "WeaponShooterNormal", "Fire")],
    "BulletHit": [("common", "HitEffect", "インクヒット")],
    "Damage": [("common", "HitEffect", "ヒット"), ("common", "SighterTarget", "ダメージ")],
    "Jump": [("player", "PlayerFoot", "ジャンプ"), ("player", "Player_Focused", "インクからジャンプする")],
    "Land": [("player", "PlayerFoot", "着地"), ("player", "Player_Focused", "InkLand")],
    "ToSquid": [("player", "Player_Focused", "イカに変身"), ("player", "Player_Focused", "ヒト状態からインクに潜る")],
    "ToHuman": [("player", "Player_Focused", "ヒトに変身")],
    "Swim": [("player", "Player_Focused", "インクの中を泳ぐ"), ("player", "Player_Focused", "イカで泳ぐ単発音")],
}

_idx = None


def sound_index():
    global _idx
    if _idx is None:
        p = A.ROOT / "analysis/effect_sound/sound_index.json"
        _idx = json.loads(p.read_text(encoding="utf-8"))
    return _idx


def user_json(name):
    p = A.WORK / f"xlink/slink_{name}.json"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(A.PY), str(A.WEB / "tools/effect_xlink.py"), "user", str(SLINK), name, "--json", str(p)],
                       check=True, capture_output=True)
    return json.loads(p.read_text(encoding="utf-8"))


def kids(c):
    ch = (c.get("container") or {}).get("children")
    if not ch:
        return []
    return list(range(ch[0], ch[1] + 1))


def select(user, keys, keep_materials):
    ct = user["callTables"]
    if keys == "player":
        keys = [c["key"] for c in ct if c["parent"] == -1 and not any(s in c["key"] for s in PLAYER_SKIP)]
    elif keys is None:
        keys = [c["key"] for c in ct if c["parent"] == -1]
    keep, pruned = set(), set()

    def walk(i):
        if i in keep:
            return
        keep.add(i)
        c = ct[i]
        cont = c.get("container") or {}
        for k in kids(c):
            ck = ct[k]
            cond = ck.get("condition") or {}
            if (cont.get("watchProperty") == "GndMaterial" and cond.get("compare") == "Equal"
                    and cond.get("value") not in keep_materials):
                pruned.add(k)
                continue
            walk(k)

    roots = {}
    for c in ct:
        if c["parent"] == -1 and c["key"] in keys:
            roots[c["key"]] = c["i"]
            walk(c["i"])
    tables = []
    for c in ct:
        if c["i"] in keep:
            tables.append({k: v for k, v in c.items() if k != "guid"})
        elif c["i"] in pruned:
            tables.append({"i": c["i"], "key": c["key"], "parent": c["parent"], "condition": c.get("condition"),
                           "pruned": True})
        else:
            tables.append(None)
    while tables and tables[-1] is None:
        tables.pop()
    trig = [dict(t, _i=n) for n, t in enumerate(user.get("actionTriggers", [])) if t["callTable"] in keep]
    ptrig = [t for t in user.get("propertyTriggers", []) if t["callTable"] in keep]
    assets = sorted({c["params"]["RuntimeAssetName"] for c in ct if c["i"] in keep and c.get("params")
                     and c["params"].get("RuntimeAssetName")})
    out = {"localProperties": user["localProperties"], "userParams": user["userParams"], "roots": roots,
           "callTables": tables, "actionSlots": user.get("actionSlots", []), "actions": user.get("actions", []),
           "actionTriggers": trig, "properties": user.get("properties", []), "propertyTriggers": ptrig}
    dsets = sorted({c["params"]["DistanceParamSetName"] for c in ct if c["i"] in keep and c.get("params")
                    and c["params"].get("DistanceParamSetName")} | (
        {user["userParams"]["DistanceParamSetName"]} if user["userParams"].get("DistanceParamSetName") else set()))
    return out, assets, dsets, len(pruned)


# ------------------------------------------------------------------ DSP-ADPCM
def dsp_decode(d, o, ch):
    """BWAV 채널 → PCM16 리스트 (Nintendo DSP-ADPCM, 8바이트 프레임 = 헤더 1 + 14 니블)"""
    p = o + 0x10 + 0x4c * ch
    codec, pan, rate, n_np, n = struct.unpack_from("<HHIII", d, p)
    coef = struct.unpack_from("<16h", d, p + 0x10)
    start, = struct.unpack_from("<I", d, p + 0x34)
    h1, h2 = struct.unpack_from("<hh", d, p + 0x46)
    base = o + start
    if codec == 0:
        return list(struct.unpack_from(f"<{n}h", d, base)), rate
    out = []
    frames = (n + 13) // 14
    for f in range(frames):
        q = base + f * 8
        ps = d[q]
        scale = 1 << (ps & 0xF)
        c1, c2 = coef[(ps >> 4) * 2], coef[(ps >> 4) * 2 + 1]
        for j in range(14):
            if len(out) >= n:
                break
            b = d[q + 1 + (j >> 1)]
            nib = (b >> 4) if (j & 1) == 0 else (b & 0xF)
            if nib >= 8:
                nib -= 16
            s = ((nib * scale) << 11) + 1024 + c1 * h1 + c2 * h2 >> 11
            s = -32768 if s < -32768 else (32767 if s > 32767 else s)
            out.append(s)
            h2, h1 = h1, s
    return out, rate


_bars = {}


def bars(fname):
    if fname not in _bars:
        d = sound_bars.load(str(RES / fname))
        _bars[fname] = (d, sound_bars.parse_bars(d))
    return _bars[fname]


def export_sound(name, out_dir):
    ents = sound_index().get(name)
    if not ents:
        return None
    fname = ents[0]["file"]
    d, b = bars(fname)
    e = next(x for x in b["entries"] if x["amta"]["name"] == name)
    w = e["bwav"]
    o = e["bwavOff"]
    chans = []
    rate = None
    for c in range(len(w["channels"])):
        pcm, rate = dsp_decode(d, o, c)
        chans.append(pcm)
    n = min(len(c) for c in chans)
    peak = max(abs(x) for c in chans for x in c[:n]) / 32768 if n else 0.0
    amta_peak = (e["amta"].get("data") or {}).get("f", [None])[0]
    wav = A.WORK / f"sfx_wav/{name}.wav"
    wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav), "wb") as wf:
        wf.setnchannels(len(chans))
        wf.setsampwidth(2)
        wf.setframerate(rate)
        inter = bytearray()
        for i in range(n):
            for c in chans:
                inter += struct.pack("<h", c[i])
        wf.writeframes(bytes(inter))
    ogg = out_dir / f"{name}.ogg"
    ogg.parent.mkdir(parents=True, exist_ok=True)
    kbps = 64 if len(chans) == 1 else 96
    r = subprocess.run([str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav), "-c:a", "libopus",
                        "-b:a", f"{kbps}k", "-vbr", "on", "-application", "audio", str(ogg)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    pre_skip, granule = ogg_info(ogg.read_bytes())
    c0 = w["channels"][0]
    return {"file": f"{name}.ogg", "bars": fname, "sampleRate": rate, "channels": len(chans), "samples": n,
            "duration": n / rate, "loop": None if c0["loopEnd"] is None else {
                "start": c0["loopStart"] / rate, "end": c0["loopEnd"] / rate, "startSample": c0["loopStart"],
                "endSample": c0["loopEnd"]},
            "prefetch": bool(w["prefetch"]), "opusPreSkip": pre_skip, "opusDuration": (granule - pre_skip) / 48000,
            "decodedPeak": round(peak, 6), "amtaPeak": amta_peak, "bytes": ogg.stat().st_size}


def ogg_info(b):
    """Ogg Opus: OpusHead pre-skip, 마지막 페이지 granule position"""
    i = b.find(b"OpusHead")
    pre = struct.unpack_from("<H", b, i + 10)[0]
    last = b.rfind(b"OggS")
    gran = struct.unpack_from("<q", b, last + 6)[0]
    return pre, gran


def attenuation(name, arc):
    p = f"Attenuation/{name}.baatn"
    if p not in arc:
        return None
    refs = sound_alto.aatn(arc[p])
    out = {"refs": refs, "curves": {}}
    for slot, v in refs.items():
        nm = v[0] if isinstance(v, tuple) else v
        if not isinstance(nm, str) or not nm:
            continue
        for ext in ("baroc", "baudc", "baadr", "baacl"):
            q = f"Attenuation/{nm}.{ext}"
            if q in arc:
                d = arc[q]
                if ext == "baroc":
                    c = sound_alto.aroc_parse(d)
                elif ext == "baudc":
                    c = sound_alto.audc_parse(d)
                else:
                    n = (len(d) - 8) // 4
                    c = {"f32": list(struct.unpack_from(f"<{n}f", d, 8))}
                out["curves"][nm] = {"kind": ext[2:].upper(), **c}
    return out


def main():
    col = json.loads((A.ASSETS / "maps/Lby_Lobby00/collision.json").read_text(encoding="utf-8"))
    mats = sorted({m["name"] for m in col["materials"]})
    arc = sound_alto.files()
    all_sizes = {}
    for group, users in GROUPS.items():
        out = A.ASSETS / f"sfx/{group}"
        A.clean_dir(out)
        doc = {"version": 1, "group": group, "users": {}, "assets": {}, "attenuation": {},
               "notes": ["users[*].callTables = SLink 호출 표 원래 번호(쓰지 않는 칸 null, children = [첫, 끝] 범위). 평가 규칙 effect_sound/xlink_format.md",
                         "params 의 Volume/Pitch 값 형식: {Random:[a,b]} 균등, {Random2Pow:[a,b]} 등, {curve:{prop, points}} 선형 보간 (xlink_format.md §4.2·4.3)",
                         "Delay 단위 = 프레임 [추정], Pitch = 재생 비율 [추정] (sound_resources.md §5)",
                         "assets[이름].opusPreSkip: Opus 인코더 앞 패딩(48kHz 샘플). 대부분 브라우저 decodeAudioData 가 잘라 줌",
                         "pruned: 로비 충돌에 없는 GndMaterial 분기(소리 파일 생략)"],
               "lobbyMaterials": mats}
        names, dsets = set(), set()
        for uname, keys in users.items():
            u = user_json(uname)
            sel, assets, ds, npruned = select(u, keys, set(mats))
            sel["prunedBranches"] = npruned
            doc["users"][uname] = sel
            names |= set(assets)
            dsets |= set(ds)
        for nm in sorted(names):
            info = export_sound(nm, out)
            doc["assets"][nm] = info
            if info:
                all_sizes[f"sfx/{group}/{info['file']}"] = info["bytes"]
        for ds in sorted(dsets):
            doc["attenuation"][ds] = attenuation(ds, arc)
        doc["events"] = {ev: [{"user": u, "key": k} for g, u, k in lst if g == group] for ev, lst in EVENTS.items()
                         if any(g == group for g, _, _ in lst)}
        all_sizes[f"sfx/{group}/sfx.json"] = A.write_json(out / "sfx.json", doc)
        miss = [n for n, v in doc["assets"].items() if v is None]
        bad = [n for n, v in doc["assets"].items() if v and v["amtaPeak"] and abs(v["decodedPeak"] - v["amtaPeak"]) > 1e-3]
        A.log(group, "assets", len(names), "missing", miss, "peak mismatch", bad[:10])
    A.write_json(A.WORK / "sizes_sfx.json", all_sizes, pretty=True)
    tot = {}
    for k, v in all_sizes.items():
        g = k.split("/")[1]
        tot[g] = tot.get(g, 0) + v
    A.log("bytes", tot)


if __name__ == "__main__":
    main()
