"""모든 Har_*.pack.zs 의 Phive/Cloth/*.bphcl 천 상수 일괄 요약 [데이터].

gfx4p_bphcl.cloth_summary 를 팩마다 실행해 천 데이터별 핵심 상수(입자·고정·질량·반경·마찰·중력·감쇠·
제약 종류/개수/강성 범위·실행 순서·solver 설정)를 한 표로 모은다. 같은 bphcl 을 쓰는 팩은 묶는다.
사용: PY web/tools/r5_gfx_char_bphcl_batch.py → analysis/completion/r5/gfx_char_bphcl_all.json
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spl_data import unzs, sarc  # noqa: E402
from gfx4p_bphcl import open_bphcl, cloth_summary  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def stiff_range(cset):
    vals = []
    for key in ("links", "localConstraints", "perParticleData"):
        for ln in cset.get(key) or []:
            if isinstance(ln, dict):
                for k in ("stiffness", "bendStiffness", "stretchStiffness"):
                    if isinstance(ln.get(k), (int, float)):
                        vals.append(round(ln[k], 6))
    if isinstance(cset.get("stiffness"), (int, float)):
        vals.append(round(cset["stiffness"], 6))
    return [min(vals), max(vals)] if vals else None


def summarize(s):
    out = []
    for cd in s.get("clothDatas", []):
        for sc in cd.get("simClothDatas", []):
            pd = sc.get("particleDatas") or []
            moving = [p for p in pd if p.get("invMass")]
            info = sc.get("simulationInfo") or {}
            other = sc.get("other") or {}
            ent = {
                "cloth": cd.get("name"), "sim": sc.get("name"),
                "particles": len(pd), "fixed": len(sc.get("fixedParticles") or []),
                "mass": sorted({round(p.get("mass", 0), 6) for p in moving}),
                "radius": sorted({round(p.get("radius", 0), 6) for p in pd}),
                "friction": sorted({round(p.get("friction", 0), 6) for p in pd}),
                "gravity": info.get("gravity"), "damping": info.get("globalDampingPerSecond"),
                "totalMass": other.get("totalMass"),
                "solver": {k: other.get(k) for k in ("subSteps", "numberOfSolveIterations", "constraintExecution",
                                                     "adaptConstraintStiffness", "landscapeCollisionEnabled") if k in other},
                "constraints": [{"type": c.get("$type"), "id": c.get("constraintId"),
                                 "n": len(c.get("links") or c.get("localConstraints") or c.get("perParticleData") or []),
                                 "stiffness": stiff_range(c)} for c in sc.get("staticConstraintSets") or []],
            }
            out.append(ent)
    return out


def main():
    packs = sorted((ROOT / "extracted/romfs/Pack/Actor").glob("Har_*.pack.zs"))
    by_hash = {}
    no_cloth = []
    for p in packs:
        files = sarc(unzs(p.read_bytes()))
        items = files.items() if isinstance(files, dict) else files
        found = [(n, b) for n, b in items if str(n).endswith(".bphcl")]
        if not found:
            no_cloth.append(p.name.replace(".pack.zs", ""))
            continue
        for n, b in found:
            h = hashlib.sha1(b).hexdigest()[:12]
            if h not in by_hash:
                tf = open_bphcl(bytes(b))
                by_hash[h] = {"file": n, "packs": [], "cloths": summarize(cloth_summary(tf))}
            by_hash[h]["packs"].append(p.name.replace(".pack.zs", ""))
    out = {"packs": len(packs), "with_cloth": len(packs) - len(no_cloth), "no_cloth": no_cloth,
           "unique_bphcl": len(by_hash), "files": by_hash}
    dst = ROOT / "analysis/completion/r5/gfx_char_bphcl_all.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("packs", "with_cloth", "unique_bphcl")}, ensure_ascii=False))
    print("no_cloth:", no_cloth)


if __name__ == "__main__":
    main()
