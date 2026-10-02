"""모든 Actor 팩에서 Component/Net/*.game__NetParam 과 ActorParam의 Net 참조를 모아 JSON으로 저장.
사용: PY web/tools/network_netparam_scan.py  -> analysis/network/netparams.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spl_data import load, sarc, byml, to_json

ROOT = Path(__file__).resolve().parents[2]
ACT = ROOT / "extracted" / "romfs" / "Pack" / "Actor"
OUT = ROOT / "analysis" / "network" / "netparams.json"


def main():
    res = {}
    for p in sorted(ACT.glob("*.pack.zs")):
        try:
            files = sarc(load(p))
        except Exception as e:
            continue
        actor = p.name[:-len(".pack.zs")]
        ent = {}
        for name, data in files.items():
            if "NetParam" in name or "/Net/" in name:
                ent[name] = json.loads(to_json(byml(data)))
            elif name.startswith("Actor/") and name.endswith(".engine__actor__ActorParam.bgyml"):
                d = byml(data)
                d = json.loads(to_json(d))
                comps = d.get("Components", {}) if isinstance(d, dict) else {}
                if "Net" in comps:
                    ent["_ActorParam.Net"] = comps["Net"]
                if isinstance(d, dict) and "$parent" in d:
                    ent["_parent"] = d["$parent"]
        if ent:
            res[actor] = ent
    OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(res), "actors with Net")


if __name__ == "__main__":
    main()
