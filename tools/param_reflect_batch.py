import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from param_reflect import TYPE_NAMES_PATH, analyze
from xref import ROOT, load_idx, load_img

OUT = ROOT / "analysis" / "param_reflect"


def main():
    catalog = json.loads((ROOT / "analysis" / "param_types_in_data.json").read_text(encoding="utf-8"))
    pats = sys.argv[1:]
    m = load_img()
    idx = load_idx()
    type_names = json.loads(TYPE_NAMES_PATH.read_text()) if TYPE_NAMES_PATH.exists() else {}
    OUT.mkdir(parents=True, exist_ok=True)
    sys.stdout.reconfigure(encoding="utf-8")
    for t, info in catalog.items():
        if not any(p in t for p in pats) or not info["fields"]:
            continue
        r = analyze(m, idx, info["fields"], type_names)
        if r is None:
            print(t, "visitor 없음")
            continue
        names = {f["name"] for f in r["fields"]}
        r["type"] = t
        r["data_fields_missing_in_visitor"] = sorted(set(info["fields"]) - names)
        (OUT / f"{t}.json").write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{t}: visitor {r['visitor']} fields {len(r['fields'])} classes {len(r['classes'])} missing {r['data_fields_missing_in_visitor']}")


if __name__ == "__main__":
    main()
