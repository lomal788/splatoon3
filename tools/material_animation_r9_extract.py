"""Stage selected raw FRES material channels; no game asset writes.

Uses the existing BfresLibrary/Gfx dump as a reader, preserving raw curve keys.
All generated project/intermediate/output files stay under analysis/port_graphics_r9.
No integer-frame bake or interpolation is used to fill an unknown channel.
"""
from pathlib import Path
import hashlib, json, subprocess, sys
import zstandard

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/port_graphics_r9/material_anim'
BUILD=ROOT/'analysis/assets_work/build/bin/Release/net7.0'
CS=r'''
using System.Text.Json.Nodes;
using BfresLibrary;
using Gfx;
var groups=new JsonObject();
foreach(var name in new[]{"Player00","Player_Squid","Player00_Hlf"}) {
  var res=new ResFile(Path.Combine(args[0],name+".bfres"));
  var wanted=new HashSet<string>(new[]{"ToSquid","ToHuman","ToHuman_KeepCharge","ToHuman_WallJump","Wait","Wait_Shtr","Shoot_Shtr","Color_Skin","Color_Eye","Blink","Eye_Scroll","Sqd_ToSquid","Sqd_ToHuman","Sqd_Wait","Sqd_Walk","Sqd_Surprise","Sqd_Blink"});
  var all=res.MatAnims().Values;
  var clips=new JsonArray(all.Where(a=>wanted.Contains(a.Name)).Select(a=> {
    var o=Dump.MaterialAnim(a,true);
    var ds=(JsonArray)o["materials"];
    for(int i=0;i<a.MaterialAnimDataList.Count;i++) {
      var cs=(JsonArray)ds[i]["curves"];
      for(int k=0;k<a.MaterialAnimDataList[i].Curves.Count;k++) {
        var c=a.MaterialAnimDataList[i].Curves[k];
        cs[k]["offsetInt"]=(int)c.Offset;
        cs[k]["deltaInt"]=(int)c.Delta;
        cs[k]["flags"]=(int)c.CurveType|(int)c.FrameType|(int)c.KeyType|((int)c.PreWrap<<8)|((int)c.PostWrap<<12);
      }
    }
    return (JsonNode)o;
  }).ToArray());
  var mats=new JsonArray(res.Models.Values.SelectMany(m=>m.Materials.Values).Select(m=>(JsonNode)Dump.Material(m)).ToArray());
  groups[name]=new JsonObject{["clipNames"]=J.Arr(all.Select(a=>a.Name)),["clips"]=clips,["materials"]=mats};
}
J.Write(args[1],new JsonObject{["schema"]=1,["groups"]=groups});
Console.WriteLine("selected raw channels exported");
'''

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    proj=OUT/'reader';proj.mkdir(exist_ok=True)
    refs=''.join(f'<Reference Include="{n}"><HintPath>{(BUILD/(n+".dll")).as_posix()}</HintPath></Reference>' for n in ['asset_bfres2gltf','BfresLibrary','Syroot.Maths','Syroot.BinaryData','Syroot.NintenTools.NSW.Bntx','Newtonsoft.Json'])
    (proj/'reader.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net7.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><RollForward>Major</RollForward><InvariantGlobalization>true</InvariantGlobalization></PropertyGroup><ItemGroup>'+refs+'</ItemGroup></Project>',encoding='utf-8')
    (proj/'Program.cs').write_text(CS,encoding='utf-8')
    hashes={}
    for name in ['Player00','Player_Squid','Player00_Hlf']:
        p=ROOT/'extracted/romfs/Model'/f'{name}.bfres.zs'
        data=zstandard.ZstdDecompressor().decompress(p.read_bytes())
        (OUT/f'{name}.bfres').write_bytes(data)
        hashes[name]={'romfs':p.relative_to(ROOT).as_posix(),'compressedSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'rawSHA256':hashlib.sha256(data).hexdigest()}
    subprocess.run(['dotnet','build',str(proj/'reader.csproj'),'-c','Release','--nologo'],cwd=ROOT,check=True)
    target=OUT/'material_channels.proposed.json'
    subprocess.run(['dotnet',str(proj/'bin/Release/net7.0/reader.dll'),str(OUT),str(target)],cwd=ROOT,check=True)
    d=json.loads(target.read_text(encoding='utf-8'));d['sources']=hashes
    target.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:{'total':len(g['clipNames']),'selected':[a['name'] for a in g['clips']]} for k,g in d['groups'].items()},ensure_ascii=False))

if __name__=='__main__':main()
