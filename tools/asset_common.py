"""웹 에셋 변환 공용: 경로, 원본 데이터 읽기, JSON 쓰기, 크기 집계.

출력 루트: web/games/splatoon3/assets/ (DESIGN.md §5). 좌표·단위는 원본 그대로(Y 위, 게임 단위).
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spl_data  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]          # c:/dev/splatoon3
WEB = ROOT / "web"
ASSETS = WEB / "games/splatoon3/assets"
ROMFS = ROOT / "extracted/romfs"
PARAMS = ROOT / "extracted/params"
WORK = ROOT / "analysis/assets_work"                 # 중간 산출물(재생성 가능, 지워도 됨)
PY = ROOT / ".venv/Scripts/python.exe"
BIN = WEB / "tools/bin"

_pack_cache = {}


def pack(name):
    """Pack/Actor/<name>.pack.zs 또는 Pack 상대 경로 → {팩 안 경로: bytes}"""
    if name in _pack_cache:
        return _pack_cache[name]
    p = ROMFS / "Pack" / name if name.endswith(".pack.zs") else ROMFS / "Pack/Actor" / f"{name}.pack.zs"
    s = spl_data.sarc(spl_data.unzs(p.read_bytes())) if p.exists() else None
    _pack_cache[name] = s
    return s


def byml(b):
    return spl_data.byml(b)


def romfs_byml(rel):
    return spl_data.byml(spl_data.unzs((ROMFS / rel).read_bytes()))


def work_path(ref):
    """'Work/A/B.type.gyml' → 팩 안 경로 'A/B.type.bgyml'"""
    r = ref[5:] if ref.startswith("Work/") else ref
    if r.endswith(".gyml"):
        r = r[:-5] + ".bgyml"
    return r


def base_name(ref):
    """'Work/X/Y.type.gyml' → 'Y'"""
    b = ref.rsplit("/", 1)[-1]
    return b.split(".", 1)[0]


_index = None


def find_in_packs(inner, prefer=()):
    """팩 안 경로를 가진 첫 팩의 bytes. prefer 팩부터, 그다음 Bootup/Params/전체 액터 팩(색인)."""
    for p in prefer:
        s = pack(p)
        if s and inner in s:
            return s[inner]
    for p in ("Bootup.Nin_NX_NVN.pack.zs", "Params.pack.zs", "SingletonParam.pack.zs"):
        s = pack(p)
        if s and inner in s:
            return s[inner]
    global _index
    if _index is None:
        idx_file = WORK / "pack_index.json"
        if idx_file.exists():
            _index = json.loads(idx_file.read_text(encoding="utf-8"))
        else:
            _index = {}
            for f in sorted((ROMFS / "Pack/Actor").glob("*.pack.zs")):
                try:
                    for k in spl_data.sarc(spl_data.unzs(f.read_bytes())):
                        _index.setdefault(k, f.name[:-8])
                except Exception:
                    pass
            WORK.mkdir(parents=True, exist_ok=True)
            idx_file.write_text(json.dumps(_index), encoding="utf-8")
    owner = _index.get(inner)
    if owner:
        return pack(owner)[inner]
    return None


def load_ref(ref, prefer=()):
    b = find_in_packs(work_path(ref), prefer)
    return byml(b) if b is not None else None


def write_json(path, obj, pretty=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(obj, ensure_ascii=False, indent=1 if pretty else None,
                     separators=None if pretty else (",", ":"))
    path.write_text(txt, encoding="utf-8")
    return path.stat().st_size


def write_bytes(path, b):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b)
    return len(b)


def clean_dir(path):
    """에셋 출력 하위 폴더 비우기(재생성 전). assets/ 밖은 거부."""
    import shutil
    path = Path(path).resolve()
    assert ASSETS.resolve() in path.parents, path
    if path.exists():
        shutil.rmtree(path)


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def log(*a):
    print("[asset]", *a, flush=True)
