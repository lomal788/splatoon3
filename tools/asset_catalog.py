"""assets/catalog.json 생성: 번들 폴더의 파일 목록·바이트 합·의존.

번들 id → 폴더 (DESIGN.md §5). 폴더 안 모든 파일(하위 폴더 포함)을 files 에 넣는다.
common 의 lib/(basis 트랜스코더)는 KTX2Loader 가 직접 받으므로 files 에서 뺀다.

사용: PY web/tools/asset_catalog.py
"""
import asset_common as A

BUNDLES = {
    "common": {"dir": "common/", "deps": ["sfx/common"], "exclude": ("lib/",)},
    "map/Lby_Lobby00": {"dir": "maps/Lby_Lobby00/", "deps": []},
    "character/Player00": {"dir": "characters/Player00/", "deps": ["sfx/player"]},
    "weapon/Shooter_Normal_00": {"dir": "weapons/Shooter_Normal_00/", "deps": ["effect/shooter", "sfx/shooter"]},
    "effect/shooter": {"dir": "effects/shooter/", "deps": []},
    "sfx/shooter": {"dir": "sfx/shooter/", "deps": []},
    "sfx/player": {"dir": "sfx/player/", "deps": []},
    "sfx/common": {"dir": "sfx/common/", "deps": []},
}


def build():
    out = {"version": 1, "bundles": {}}
    for bid, b in BUNDLES.items():
        d = A.ASSETS / b["dir"]
        files, total = [], 0
        if d.exists():
            for f in sorted(d.rglob("*")):
                if not f.is_file():
                    continue
                rel = f.relative_to(d).as_posix()
                if any(rel.startswith(x) for x in b.get("exclude", ())):
                    continue
                files.append(rel)
                total += f.stat().st_size
        out["bundles"][bid] = {"dir": b["dir"], "files": files, "deps": b["deps"], "bytes": total}
    A.write_json(A.ASSETS / "catalog.json", out, pretty=True)
    for bid, e in out["bundles"].items():
        A.log(f"{e['bytes']:>10}  {len(e['files']):>3} files  {bid}")
    return out


if __name__ == "__main__":
    build()
