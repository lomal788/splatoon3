"""이벤트(0x71012f8808)·상태(0x71012f8db8) 등록 표 + vtable 슬롯(write/read 등) TSV.
사용: PY web/tools/network_typetable.py > analysis/network/nettypes.tsv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import load_img
from network_typereg import scan, ctor_vtable, vt_slots, SLOTS


def main():
    m = load_img()
    sys.stdout.reconfigure(encoding="utf-8")
    print("kind\tname\tobj_size\tbits_min\tbits_max\thash32\tentry\tctor\tvtable\t" + "\t".join(SLOTS.values()))
    for kind, tgt in (("event", 0x71012F8808), ("state", 0x71012F8DB8)):
        for r in scan(m, tgt):
            ctor = int(r["sp0"], 16) if r["sp0"] else None
            vt = ctor_vtable(m, ctor) if ctor else None
            sl = vt_slots(m, vt) if vt else {}
            print("\t".join(str(x) for x in [kind, r["name"], r["w3"], r["w4"], r["w5"], r["hash32"], r["entry"], r["sp0"], hex(vt) if vt else None]
                            + [hex(sl[k]) if k in sl else "" for k in SLOTS]))


if __name__ == "__main__":
    main()
