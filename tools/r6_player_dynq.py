"""r6 player: dyntrace.json 조회. 사용: r6_player_dynq.py <오프셋hex> [끝hex]"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
d = json.loads((Path(__file__).resolve().parents[2] / "analysis/r6_player/dyntrace.json").read_text(encoding="utf-8"))["writes"]
lo = int(sys.argv[1], 16); hi = int(sys.argv[2], 16) if len(sys.argv) > 2 else lo + 1
for k, v in d.items():
    o = int(k, 16)
    if lo <= o < hi:
        for pc, e in v.items():
            print(k, pc, "n", e["n"], "nz", e["nz"], "size", e["size"], "vals", [hex(x) for x in e["vals"]], e["sc"][:4])
