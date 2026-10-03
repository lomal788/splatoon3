
"""Port graphics assets only. Original/extracted are read-only; no cleanup.
Run: .venv/Scripts/python web/tools/graphics_port_assets.py
HDR decoder: analysis/port_graphics/python/imagecodecs (no 8-bit BC6H path).
"""
import copy, json, pathlib, struct, sys, hashlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = ROOT / "analysis/port_graphics"
sys.path[:0] = [str(ROOT / "web/tools"), str(WORK / "python")]
import numpy as np
import asset_common as A
import asset_model as M
import asset_map as MAP
import graphics_bntx as B

OUT = A.ASSETS / "maps/Lby_Lobby00"
M.GL = WORK / "assets_work/gl"
M.RAW = WORK / "assets_work/raw"
A.WORK = WORK / "assets_work"
A.WORK.mkdir(parents=True, exist_ok=True)

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"))+"\n", encoding="utf8")

def export_bakes():
    source = ROOT / "analysis/gfx4/bake/LobbyVersus_Day"
    data = json.loads((source / "bkdat.byaml.json").read_text(encoding="utf8"))
    textures = {}
    for t in B.parse(B.read_bntx(str(source / "textures.bntx"))):
        layers=[];blob=bytearray()
        for mip in range(t.mips):
            if t.fmt_name.startswith("BC6H"):
                a=B.decode_bc6h_float(t,0,mip)
                # BRTI RGB1; RGBA16F preserves HDR and BC6H's half precision.
                rgba=np.ones(a.shape[:2]+(4,),dtype="<f2");rgba[...,:3]=a
            elif t.fmt_name.startswith("BC5"):
                a=np.asarray(B.apply_comp(B.decode_layer(t,0,mip),t.comp),np.uint8)
                rgba=(a.astype(np.float32)/255).astype("<f2")
            else: raise ValueError(t.fmt_name)
            b=rgba.tobytes()
            layers.append({"width":rgba.shape[1],"height":rgba.shape[0],"offset":len(blob),"bytes":len(b)})
            blob.extend(b)
        name="bake/"+t.name+".rgba16f.bin"
        (OUT/name).parent.mkdir(parents=True,exist_ok=True);(OUT/name).write_bytes(blob)
        textures[t.name]={"file":name,"format":t.fmt_name,"comp":t.comp,"mips":layers}
    dump(OUT/"bake/bindings.json",{"version":1,"source":"LobbyVersus_Day.bkres","textures":textures,"DataElements":data["DataElements"]})
    print("bake",[(k,v["format"],len(v["mips"])) for k,v in textures.items()])

def enrich_model(src, model, dst):
    g,b=M.read_glb(src)
    # Preserve all original UVs, material indices and light bones.
    meta=json.loads(src.with_suffix(".meta.json").read_text(encoding="utf8"))
    original_indices={name:i for i,name in enumerate(meta["materials"])}
    bake_params={m["name"]:{k:v for k,v in m.get("extras",{}).get("fres",{}).get("params",{}).items() if k in ("gsys_bake_st0","gsys_bake_st1")} for m in g.get("materials",[])}
    M.slim(g)
    for mat in g.get("materials",[]):
        mat.setdefault("extras",{})["originalMaterialIndex"]=original_indices[mat["name"]]
        # Bake binder requires both sampler and the native shader parameter.
        if bake_params.get(mat["name"]):mat["extras"]["hoian"]["params"].update(bake_params[mat["name"]])
    for n in g.get("nodes",[]):
        if n.get("name")==model+"__model":
            n.setdefault("extras",{}).update({"originalModelName":model,"originalMaterialCount":len(original_indices)})
    M.write_glb(dst,g,b)
    return len(original_indices)

def export_map():
    backup=WORK/"previous_visual.glb"
    if not backup.exists(): backup.write_bytes((OUT/"visual.glb").read_bytes())
    banc=MAP.load_banc();groups={};holders={}
    for a in banc["Actors"]:
        if a["Gyaml"] not in MAP.VISUAL_ACTORS:continue
        trs=MAP.trs(a.get("Translate",[0,0,0]),a.get("Rotate",[0,0,0]),a.get("Scale",[1,1,1]))
        for slot,(bfres,model) in enumerate(MAP.model_refs(a["Gyaml"])):
            name=f'{a["Gyaml"]}_{a["Hash"]}_{slot}'
            guid=f'{a["Hash"]}_{slot}'
            groups.setdefault((bfres,model),[]).append((name,trs))
            holders[name]={"bakeGuid":guid,"bakeModelName":model}
    items=[]
    for (bfres,model),instances in groups.items():
        p,meta=M.convert(bfres,model)
        dst=p.with_suffix(".graphics.glb")
        count=enrich_model(p,model,dst)
        for name,_ in instances:holders[name]["originalMaterialCount"]=count
        items.append((dst,instances)); print("map",model,len(instances),"materials",count)
    merged=M.GL/"graphics_map.glb";M.merge(items,merged,root_name="Lby_Lobby00__visual",keep_anims=False)
    g,b=M.read_glb(merged)
    for n in g["nodes"]:
        if n.get("name") in holders:n.setdefault("extras",{}).update(holders[n["name"]])
    M.write_glb(merged,g,b)
    # Named bones and unused native UVs must survive optimization.
    M.gltfpack(merged,OUT/"visual.glb",extra=["-kn","-kv","-vnf"])
    g,_=M.read_glb(OUT/"visual.glb")
    mesh_count=sum(len(m["primitives"]) for m in g["meshes"])
    uv1=sum("TEXCOORD_1" in p["attributes"] for m in g["meshes"] for p in m["primitives"])
    rigs=[n["name"] for n in g["nodes"] if n.get("name","").startswith("Dynamic_SpotLight")]
    print("map output",mesh_count,"primitives",uv1,"UV1",len(rigs),"spot bones")
    assert uv1>0 and len(rigs)>=8
    return {"primitives":mesh_count,"uv1Primitives":uv1,"spotBones":rigs,"instances":holders}

def export_sky():
    p,meta=M.convert("Sky_Daytime00")
    dst=p.with_suffix(".graphics.glb");enrich_model(p,"Sky_Daytime00",dst)
    M.gltfpack(dst,OUT/"sky/Sky_Daytime00.glb",extra=["-kn","-kv","-vnf"])
    print("sky",meta["triangleCount"],"triangles")

def catalog():
    p=A.ASSETS/"catalog.json";c=json.loads(p.read_text(encoding="utf8"));e=c["bundles"]["map/Lby_Lobby00"]
    # Add only these files; preserve every other bundle/entry.
    files=set(e["files"]);files.update(str(x.relative_to(OUT)).replace("\\","/") for folder in ["bake","sky"] for x in (OUT/folder).rglob("*") if x.is_file())
    e["files"]=sorted(files);e["bytes"]=sum((OUT/f).stat().st_size for f in e["files"])
    dump(p,c)


def export_material_resources():
    import asset_ktx2 as K
    char=A.ASSETS/"characters/Player00"
    info=json.loads((char/"data/character.json").read_text(encoding="utf8"))
    targets=[]
    for key,part in info["parts"].items():
        dst=char/(key+".glb" if key in ("body","body_hlf","squid") else "parts/"+key+".glb")
        targets.append(("character/Player00",char,dst,part["bfres"],part.get("model",part["bfres"])))
    weapon=A.ASSETS/"weapons/Shooter_Normal_00"
    targets.append(("weapon/Shooter_Normal_00",weapon,weapon/"model.glb","Wmn_Shooter_NormalT","Wmn_Shooter_NormalT"))
    stats=[]
    for bundle,directory,dst,bfres,model in targets:
        if not dst.exists():continue
        src,meta=M.convert(bfres,model)
        original,_=M.read_glb(src)
        mats={m["name"]:m for m in original["materials"]}
        g,b=M.read_glb(dst)
        backup=WORK/"previous_materials"/dst.relative_to(A.ASSETS)
        backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():backup.write_bytes(dst.read_bytes())
        resource_names=set()
        for material in g["materials"]:
            native=mats.get(material["name"])
            if native is None:continue
            fres=copy.deepcopy(native.get("extras",{}).get("fres",{}))
            material.setdefault("extras",{})["fres"]=fres
            for sampler in fres.get("samplers",[]):
                if any(slot in ("_re0","_re1","_re2","_t0") for slot in sampler.get("slots",[])):
                    resource_names.add(sampler["texture"])
        M.write_glb(dst,g,b)
        files=[]
        tex=M.GL/bfres/"tex"
        for name in sorted(resource_names):
            metadata=tex/(name+".json")
            if not metadata.exists():print("missing resource",bfres,name);continue
            tm=json.loads(metadata.read_text(encoding="utf8"));png=tex/tm["files"][0]
            out=directory/"tex/resources"/(name+".ktx2")
            if not out.exists():K.encode(png,out,linear=not tm.get("format","").endswith("SRGB"),uastc=True)
            files.append(str(out.relative_to(directory)).replace("\\","/"))
        stats.append({"bundle":bundle,"file":str(dst.relative_to(directory)).replace("\\","/"),"fresMaterials":len(g["materials"]),"resources":files})
        print("materials",bfres,len(g["materials"]),"resources",len(files),flush=True)
    cat=A.ASSETS/"catalog.json";c=json.loads(cat.read_text(encoding="utf8"))
    for id in {x["bundle"] for x in stats}:
        e=c["bundles"][id];directory=A.ASSETS/e["dir"]
        e["files"]=sorted(set(e["files"])|{f for x in stats if x["bundle"]==id for f in x["resources"]})
        e["bytes"]=sum((directory/f).stat().st_size for f in e["files"])
    dump(cat,c);dump(WORK/"material_resources.json",stats)

def main():
    if "--map-only" in sys.argv:
        stats=export_map();catalog();dump(WORK/"assets.json",stats);return
    if "--materials-only" in sys.argv:
        export_material_resources();return
    export_bakes();stats=export_map();export_sky();catalog();export_material_resources()
    stats["sha256"]={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/"visual.glb",OUT/"sky/Sky_Daytime00.glb",OUT/"bake/bindings.json"]}
    dump(WORK/"assets.json",stats)

if __name__=="__main__":main()
