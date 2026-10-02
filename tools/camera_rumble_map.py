"""ELink2 에셋의 진동/카메라 쉐이크 파라미터 추출.

입력: analysis/effect_sound/elink2_users.json ([effect_sound] 담당의 ELink2 파서 출력, 읽기만 함)
출력: analysis/camera/rumble_map.json, 표준출력 요약

사용: camera_rumble_map.py [사용자이름 접두어...]
"""
import sys, json
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:/dev/splatoon3")
SRC = ROOT / "analysis/effect_sound/elink2_users.json"
KEYS = ["CameraRumbleName", "CameraRumble", "CameraRumbleFrame", "CtrlRumbleName", "CtrlRumbleGain",
        "CtrlRumblePitch", "CtrlRumbleStretch", "CtrlRumblePattern", "CtrlRumbleExtra"]


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    rows = []
    for user, u in d.items():
        for ct in u.get("callTables", []):
            p = ct.get("params") or {}
            hit = {k: p[k] for k in KEYS if k in p}
            if hit:
                rows.append(dict(user=user, key=ct.get("key"), asset=p.get("AssetName"),
                                 condition=ct.get("condition"), **hit))
    json.dump(rows, open(ROOT / "analysis/camera/rumble_map.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pref = sys.argv[1:]
    print("진동/쉐이크 파라미터를 가진 ELink 에셋:", len(rows), "/ 사용자", len({r['user'] for r in rows}))
    print("CameraRumble 값 분포:", Counter(r.get("CameraRumble") for r in rows if "CameraRumble" in r))
    print("CameraRumbleName 분포:", Counter(r.get("CameraRumbleName") for r in rows if "CameraRumbleName" in r))
    print("CtrlRumblePattern 분포:", Counter(r.get("CtrlRumblePattern") for r in rows if "CtrlRumblePattern" in r))
    for r in rows:
        if pref and not any(r["user"].startswith(x) for x in pref):
            continue
        rest = {k: r[k] for k in KEYS if k in r}
        print(f"{r['user']:34s} {str(r['key'])[:40]:40s} {rest}")


if __name__ == "__main__":
    main()
