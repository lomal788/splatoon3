"""전체 액터 팩의 .bphsh 를 collision_mesh 로 풀어 루트 타입 분포와 bbox 대조(ShapeParam AutoCalc)를 낸다.

사용: PY web/tools/collision_scan.py [--out analysis/collision/scan_all.json]
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collision_mesh
import spl_data

ROOT = Path(__file__).resolve().parents[2]


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    types = Counter()
    rows = []
    for pk in sorted((ROOT / "extracted/romfs/Pack/Actor").glob("*.pack.zs")):
        try:
            sarc = spl_data.sarc(spl_data.unzs(pk.read_bytes()))
        except Exception:
            continue
        shapes = {n: b for n, b in sarc.items() if n.endswith(".bphsh")}
        if not shapes:
            continue
        sp = [b for n, b in sarc.items() if n.endswith(".phive__ShapeParam.bgyml")]
        auto = None
        mesh_paths = []
        if sp:
            j = spl_data.byml(sp[0])
            ac = j.get("AutoCalc") or {}
            if "Min" in ac and "Max" in ac:
                auto = ([ac["Min"][k] for k in "XYZ"], [ac["Max"][k] for k in "XYZ"])
            mesh_paths = [m.get("PhshMeshPath") for m in j.get("PhshMesh", []) or []]
        for n, b in shapes.items():
            try:
                info, m, ph = collision_mesh.analyze(b)
            except Exception as e:  # noqa: BLE001
                types["ERROR"] += 1
                rows.append({"pack": pk.name, "shape": n, "error": repr(e)})
                continue
            types[info["root_type"]] += 1
            row = {"pack": pk.name, "shape": n, "root": info["root_type"]}
            if m is not None:
                used = np.unique(m["tri"])
                bmin = m["pos"][used].min(0).tolist()
                bmax = m["pos"][used].max(0).tolist()
                row.update(tris=int(len(m["tri"])), flatQuadTris=int((m["quad"] == 3).sum()), bmin=bmin, bmax=bmax,
                           maxTag=int(m["tag"].max()) if len(m["tag"]) else None, nMat=len(ph["materials"]))
                stem = n.split("/")[-1].split(".")[0]
                if auto and len(shapes) == 1 and len(mesh_paths) == 1 and stem in (mesh_paths[0] or ""):
                    row["autoCalcDiff"] = max(max(abs(a - c) for a, c in zip(bmin, auto[0])),
                                              max(abs(a - c) for a, c in zip(bmax, auto[1])))
            rows.append(row)
    cmp_rows = [r for r in rows if "autoCalcDiff" in r]
    bad_tag = [r for r in rows if r.get("maxTag") is not None and r["maxTag"] >= r["nMat"]]
    summary = {
        "root_types": dict(types),
        "mesh_shapes": sum(1 for r in rows if "tris" in r),
        "triangles_total": sum(r.get("tris", 0) for r in rows),
        "flat_quad_triangles_total": sum(r.get("flatQuadTris", 0) for r in rows),
        "autoCalc_compared": len(cmp_rows),
        "autoCalc_max_diff": max((r["autoCalcDiff"] for r in cmp_rows), default=None),
        "autoCalc_diff_gt_0.01": [(r["pack"], r["autoCalcDiff"]) for r in cmp_rows if r["autoCalcDiff"] > 0.01],
        "shapeTag_out_of_material_table": [(r["pack"], r["maxTag"], r["nMat"]) for r in bad_tag],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if out:
        Path(out).write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=0), encoding="utf-8")


if __name__ == "__main__":
    main()
