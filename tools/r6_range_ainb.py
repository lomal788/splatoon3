import json
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")

SRC = sys.argv[1] if len(sys.argv) > 1 else "C:/dev/splatoon3/analysis/range/pack_LobbyVersus/Logic/Lby_Lobby00_5bad.logic.root.ainb"
OUT = sys.argv[2] if len(sys.argv) > 2 else "C:/dev/splatoon3/analysis/r6_range/lby_lobby00_5bad_ainb.json"

d = open(SRC, "rb").read()


def u32(a):
    return struct.unpack_from("<I", d, a)[0]


def i16(a):
    return struct.unpack_from("<h", d, a)[0]


hdr = struct.unpack_from("<4sI27I", d, 0)
magic, version = hdr[0], hdr[1]
(fname_off, cmd_count, node_count, precon_count, attach_count, out_count,
 glob_off, str_off, resolve_off, imm_off, resident_off, io_off, multi_off,
 attach_off, attach_idx_off, exb_off, child_rep_off, precon_off, x50, x54, x58,
 embed_off, cat_off, x64, entry_off, x6c, hash_off) = hdr[2:]
assert magic == b"AIB " and version == 0x404


def s(o):
    e = d.index(b"\0", str_off + o)
    return d[str_off + o:e].decode("utf-8")


TYPES = ["int", "bool", "float", "string", "vec3f", "udt"]

imm_tab = [u32(imm_off + 4 * i) for i in range(6)] + [io_off]
imm = {t: [] for t in TYPES}
for ti, t in enumerate(TYPES):
    a, e = imm_tab[ti], imm_tab[ti + 1]
    size = {"int": 12, "bool": 12, "float": 12, "string": 12, "vec3f": 20, "udt": 16}[t]
    while a < e:
        name = s(u32(a))
        if t == "udt":
            cls = s(u32(a + 4))
            flags = u32(a + 8)
            val = u32(a + 12)
            imm[t].append({"name": name, "class": cls, "flags": flags, "value": val})
        else:
            flags = u32(a + 4)
            raw = d[a + 8:a + size]
            if t == "int":
                val = struct.unpack("<i", raw)[0]
            elif t == "bool":
                val = bool(struct.unpack("<I", raw)[0])
            elif t == "float":
                val = struct.unpack("<f", raw)[0]
            elif t == "string":
                val = s(struct.unpack("<I", raw)[0])
            else:
                val = list(struct.unpack("<3f", raw))
            imm[t].append({"name": name, "flags": flags, "value": val})
        a += size

io_tab = [u32(io_off + 4 * i) for i in range(12)] + [multi_off]
inputs = {t: [] for t in TYPES}
outputs = {t: [] for t in TYPES}
for k in range(12):
    t = TYPES[k // 2]
    is_in = k % 2 == 0
    a, e = io_tab[k], io_tab[k + 1]
    while a < e:
        if is_in:
            name = s(u32(a))
            if t == "udt":
                cls = s(u32(a + 4))
                b = a + 8
            else:
                cls = None
                b = a + 4
            node, param = i16(b), i16(b + 2)
            flags = u32(b + 4)
            if t == "vec3f":
                dv = list(struct.unpack_from("<3f", d, b + 8))
                size = (b + 20) - a
            else:
                raw = u32(b + 8)
                if t == "float":
                    dv = struct.unpack_from("<f", d, b + 8)[0]
                elif t == "string":
                    dv = s(raw)
                elif t == "int":
                    dv = struct.unpack_from("<i", d, b + 8)[0]
                elif t == "bool":
                    dv = bool(raw)
                else:
                    dv = raw
                size = (b + 12) - a
            ent = {"name": name, "node": node, "param": param, "flags": flags, "default": dv}
            if cls:
                ent["class"] = cls
            if node <= -100:
                mi = -100 - node
                ent["multi"] = [
                    {"node": i16(multi_off + 8 * (mi + j)), "param": i16(multi_off + 8 * (mi + j) + 2),
                     "flags": u32(multi_off + 8 * (mi + j) + 4)}
                    for j in range(param)
                ]
            inputs[t].append(ent)
            a += size
        else:
            w = u32(a)
            ent = {"name": s(w & 0x3FFFFFFF), "flags": w >> 30}
            if t == "udt":
                ent["class"] = s(u32(a + 4))
                a += 8
            else:
                a += 4
            outputs[t].append(ent)

precons = [struct.unpack_from("<HH", d, precon_off + 4 * i) for i in range(precon_count)]

nodes = []
for n in range(node_count):
    a = 0x74 + 0x18 * cmd_count + 0x38 * n
    (ntype, idx, nattach, flags, _p, name_off, name_hash, body, exb_cnt, exb_sz,
     multi_cnt, _p2, base_attach, base_pre, pre_cnt, x30) = struct.unpack_from("<HHHBBIIIHHHHIHHI", d, a)
    guid = d[a + 0x28:a + 0x38].hex()
    nd = {"index": idx, "type": ntype, "class": s(name_off), "flags": flags, "guid": guid,
          "preconditions": precons[base_pre:base_pre + pre_cnt]}
    pairs = struct.unpack_from("<12I", d, body)
    nd["imm"] = {}
    for ti, t in enumerate(TYPES):
        i0, c = pairs[2 * ti], pairs[2 * ti + 1]
        if c:
            nd["imm"].update({e["name"]: e["value"] for e in imm[t][i0:i0 + c]})
    io = struct.unpack_from("<24I", d, body + 0x30)
    nd["in"] = {}
    nd["out"] = {}
    for k in range(12):
        t = TYPES[k // 2]
        i0, c = io[2 * k], io[2 * k + 1]
        if not c:
            continue
        if k % 2 == 0:
            for e in inputs[t][i0:i0 + c]:
                src = [(m["node"], m["param"]) for m in e["multi"]] if "multi" in e else [(e["node"], e["param"])]
                nd["in"][e["name"]] = {"type": t, "src": src, "default": e["default"]}
        else:
            for j, e in enumerate(outputs[t][i0:i0 + c]):
                nd["out"][e["name"]] = {"type": t, "local_index": j, "flags": e["flags"]}
    lk = struct.unpack_from("<20B", d, body + 0x90)
    links = []
    ptr = body + 0xa4
    total = sum(lk[2 * i] for i in range(10))
    offs = [u32(ptr + 4 * i) for i in range(total)]
    q = 0
    for lt in range(10):
        for _ in range(lk[2 * lt]):
            la = offs[q]
            q += 1
            links.append({"type": lt, "node": u32(la), "name": s(u32(la + 4))})
    nd["links"] = links
    nodes.append(nd)

result = {"file": s(fname_off), "category": s(cat_off), "node_count": node_count,
          "header": {"precondition_count": precon_count, "embed_off": embed_off, "entry_off": entry_off},
          "nodes": nodes}
import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def out_name(node, param, typ):
    if node < 0:
        return None
    nd = nodes[node]
    for nm, o in nd["out"].items():
        if o["type"] == typ and o["local_index"] == param:
            return nm
    return "?%d" % param


for nd in nodes:
    head = "#%d %s %s" % (nd["index"], nd["class"], json.dumps(nd["imm"], ensure_ascii=False))
    print(head)
    for nm, i in nd["in"].items():
        srcs = ["#%d.%s" % (a, out_name(a, b, i["type"])) for a, b in i["src"] if a >= 0]
        print("    in  %s(%s) <- %s" % (nm, i["type"], ", ".join(srcs) if srcs else "-"))
    for nm, o in nd["out"].items():
        print("    out %s(%s)" % (nm, o["type"]))
    for l in nd["links"]:
        print("    link%d -> #%d %s" % (l["type"], l["node"], l["name"]))
