"""r6 assets: phive ShapeParam Box 의 OffsetRotation/OffsetTranslation/Center 합성 순서를 데이터(AutoCalc AABB)로 대조.

romfs Pack/Actor/*.pack.zs 의 Phive/ShapeParam/*.phive__ShapeParam.bgyml 중 Box 1개짜리(다른 형상 없음)를 모아
후보 식으로 만든 꼭짓점 AABB 와 파일의 AutoCalc Min/Max 를 비교한다. AutoCalc 은 툴이 미리 계산해 넣은 값 [데이터].
결과: analysis/completion/r6/assets_box_autocalc.json
"""
import glob, json, math, sys
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import spl_data as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def v3(d, k, dv):
    x = d.get(k)
    if x is None:
        return np.array(dv, float)
    return np.array([x.get("X", dv[0]), x.get("Y", dv[1]), x.get("Z", dv[2])], float)


def R(deg, order):
    rx, ry, rz = (math.radians(a) for a in deg)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return {"zyx": Z @ Y @ X, "xyz": X @ Y @ Z}[order]


def main():
    rows = []
    for p in sorted(glob.glob(str(ROOT / "extracted/romfs/Pack/Actor/*.pack.zs"))):
        try:
            files = S.sarc(S.unzs(open(p, "rb").read()))
        except Exception:
            continue
        for name, data in files.items():
            if not name.endswith("phive__ShapeParam.bgyml"):
                continue
            try:
                d = S.byml(data)
            except Exception:
                continue
            boxes = d.get("Box") or []
            others = [k for k in ("Sphere", "Capsule", "Cylinder", "Polytope", "Mesh", "Compound") if d.get(k)]
            if len(boxes) != 1 or others or "AutoCalc" not in d:
                continue
            b = boxes[0]
            ac = d["AutoCalc"]
            rows.append(dict(file=name, center=v3(b, "Center", (0, 0, 0)), half=v3(b, "HalfExtents", (0.5, 0.5, 0.5)),
                             orot=v3(b, "OffsetRotation", (0, 0, 0)), otr=v3(b, "OffsetTranslation", (0, 0, 0)),
                             amin=v3(ac, "Min", (0, 0, 0)), amax=v3(ac, "Max", (0, 0, 0)), radius=b.get("ConvexRadius")))
    corners = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)
    cands = {
        "A: T + R·(C ± H)": lambda r, Rm: r["otr"] + (Rm @ (r["center"] + corners * r["half"]).T).T,
        "B: T + C + R·(±H)": lambda r, Rm: r["otr"] + r["center"] + (Rm @ (corners * r["half"]).T).T,
        "C: R·(C ± H + T)": lambda r, Rm: (Rm @ (r["center"] + corners * r["half"] + r["otr"]).T).T,
        "D: R·(C ± H) (T 무시)": lambda r, Rm: (Rm @ (r["center"] + corners * r["half"]).T).T,
        "E: C ± H (회전·T 무시)": lambda r, Rm: r["center"] + corners * r["half"],
    }
    res = {k + " " + o: 0 for k in cands for o in ("zyx", "xyz")}
    disc = []
    nontriv = 0
    for r in rows:
        informative = np.any(np.abs(r["orot"]) > 1e-6) and (np.any(np.abs(r["center"]) > 1e-6) or np.any(np.abs(r["otr"]) > 1e-6))
        nontriv += informative
        ok = []
        for k, f in cands.items():
            for o in ("zyx", "xyz"):
                pts = f(r, R(r["orot"], o))
                if np.allclose(pts.min(0), r["amin"], atol=2e-3) and np.allclose(pts.max(0), r["amax"], atol=2e-3):
                    res[k + " " + o] += 1
                    ok.append(k + " " + o)
        if informative and len(disc) < 40:
            disc.append(dict(file=r["file"], center=r["center"].tolist(), half=r["half"].tolist(), orot=r["orot"].tolist(),
                             otr=r["otr"].tolist(), amin=r["amin"].tolist(), amax=r["amax"].tolist(), match=ok))
    out = dict(boxes=len(rows), informative=int(nontriv), matches=res, informative_examples=disc)
    (ROOT / "analysis/completion/r6/assets_box_autocalc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(boxes=len(rows), informative=int(nontriv), matches=res), ensure_ascii=False, indent=1))


if __name__ == "__main__" and "--compound" not in sys.argv:
    main()


def compound():
    """여러 형상(Box/Capsule/Sphere)을 가진 ShapeParam 에서 OffsetRotation≠0 인 것만 골라 전체 AutoCalc AABB 와 후보 비교."""
    import glob as _g
    corners = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)
    seen = set()
    stat = {}
    exs = []
    n = 0
    for p in sorted(_g.glob(str(ROOT / "extracted/romfs/Pack/Actor/*.pack.zs"))):
        try:
            files = S.sarc(S.unzs(open(p, "rb").read()))
        except Exception:
            continue
        for name, data in files.items():
            if not name.endswith("phive__ShapeParam.bgyml") or name in seen:
                continue
            seen.add(name)
            d = S.byml(data)
            if "AutoCalc" not in d:
                continue
            shapes = []
            bad = False
            for k, v in d.items():
                if not isinstance(v, list):
                    continue
                for it in v:
                    if not isinstance(it, dict):
                        continue
                    if k not in ("Box", "Capsule", "Sphere"):
                        bad = True
                    shapes.append((k, it))
            if bad or not shapes:
                continue
            inform = any(np.any(np.abs(v3(it, "OffsetRotation", (0, 0, 0))) > 1e-6) and
                         (np.any(np.abs(v3(it, "OffsetTranslation", (0, 0, 0))) > 1e-6) or
                          np.any(np.abs(v3(it, "Center", (0, 0, 0))) > 1e-6) or k != "Box")
                         for k, it in shapes)
            if not inform:
                continue
            n += 1
            amin, amax = v3(d["AutoCalc"], "Min", (0, 0, 0)), v3(d["AutoCalc"], "Max", (0, 0, 0))
            ok = []
            for cand in ("A T+R·p", "B T+C+R·(±H)", "C R·(p+T)"):
                for order in ("zyx", "xyz"):
                    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
                    for k, it in shapes:
                        Rm = R(v3(it, "OffsetRotation", (0, 0, 0)), order)
                        T = v3(it, "OffsetTranslation", (0, 0, 0))
                        if k == "Box":
                            c, h = v3(it, "Center", (0, 0, 0)), v3(it, "HalfExtents", (0.5, 0.5, 0.5))
                            if cand.startswith("A"):
                                pts = T + (Rm @ (c + corners * h).T).T
                            elif cand.startswith("B"):
                                pts = T + c + (Rm @ (corners * h).T).T
                            else:
                                pts = (Rm @ (c + corners * h + T).T).T
                            rad = 0.0
                        else:
                            rad = float(it.get("Radius", 0.5 if k == "Sphere" else 0.5))
                            if k == "Sphere":
                                cs = [v3(it, "Center", (0, 0, 0))]
                            else:
                                cs = [v3(it, "CenterA", (0, 0.5, 0)), v3(it, "CenterB", (0, -0.5, 0))]
                            cs = np.array(cs)
                            pts = (Rm @ (cs + (T if cand.startswith("C") else 0)).T).T + (0 if cand.startswith("C") else T)
                        lo = np.minimum(lo, pts.min(0) - rad)
                        hi = np.maximum(hi, pts.max(0) + rad)
                    if np.allclose(lo, amin, atol=5e-3) and np.allclose(hi, amax, atol=5e-3):
                        ok.append(cand + " " + order)
            for o in ok:
                stat[o] = stat.get(o, 0) + 1
            if len(exs) < 60:
                exs.append(dict(file=name, kinds=[k for k, _ in shapes], match=ok, amin=amin.tolist(), amax=amax.tolist()))
    return dict(informative_files=n, matches=stat, examples=exs)


if __name__ == "__main__" and "--compound" in sys.argv:
    r = compound()
    p = ROOT / "analysis/completion/r6/assets_box_autocalc.json"
    j = json.loads(p.read_text(encoding="utf-8"))
    j["compound"] = r
    p.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k != "examples"}, ensure_ascii=False, indent=1))
