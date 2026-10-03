import * as THREE from "three";
import type { Bundle } from "../assets.ts";
import type { FresMaterial } from "./hoian.ts";
export interface BakeSlot { texture:THREE.DataTexture; st:THREE.Vector4; type:number; tableIndex:number }
export interface BakeMaterial { ao:BakeSlot|null; light:BakeSlot|null }
interface Binding {MaterialName:string;OriginalMaterialIndex:number;TextureIndex:number;TexcoordScale:{X:number;Y:number};TexcoordOffset:{X:number;Y:number}}
interface ModelBinding {Guid:string;ModelName:string;OriginalMaterialCount:number;MaterialElements:Binding[]}
interface BakeData {
  textures:Record<string,{file:string;mips:{width:number;height:number;offset:number;bytes:number}[]}>;
  DataElements:{BindingSpace:number;DataType:number;TextureNames:string[];ModelElements:ModelBinding[]}[];
}
export const bakeTableIndex=(space:number,type:number):number=>((space<<2)&0x1c)|((type-1)&3);
export class BakeBindings {
  private readonly textures=new Map<string,THREE.DataTexture>();
  private data:BakeData|null=null;
  readonly stats={materials:0,ao:0,light:0,missing:[] as string[]};
  constructor(bundle:Bundle) {
    if(!bundle.has("bake/bindings.json"))return;
    this.data=bundle.json<BakeData>("bake/bindings.json");
    for(const [name,meta] of Object.entries(this.data.textures)) {
      const bytes=bundle.bytes(meta.file),first=meta.mips[0];
      const mips=meta.mips.map(m=>({data:new Uint16Array(bytes,m.offset,m.bytes/2),width:m.width,height:m.height}));
      const t=new THREE.DataTexture(mips[0].data,first.width,first.height,THREE.RGBAFormat,THREE.HalfFloatType);
      t.name=name;t.mipmaps=mips;t.generateMipmaps=false;t.flipY=false;
      t.minFilter=THREE.LinearMipmapLinearFilter;t.magFilter=THREE.LinearFilter;t.colorSpace=THREE.NoColorSpace;
      t.needsUpdate=true;this.textures.set(name,t);
    }
  }
  resolve(mesh:THREE.Mesh,mat:THREE.Material,f:FresMaterial):BakeMaterial|null {
    if(!this.data)return null;
    let holder:THREE.Object3D|null=mesh;
    while(holder && !holder.userData.bakeGuid)holder=holder.parent;
    if(!holder)return null;
    const guid=String(holder.userData.bakeGuid),name=String(holder.userData.bakeModelName),count=holder.userData.originalMaterialCount as number;
    const result:BakeMaterial={ao:null,light:null};
    for(const d of this.data.DataElements) {
      if(d.BindingSpace!==0 || (d.DataType!==3&&d.DataType!==4))continue;
      const m=d.ModelElements.find(x=>x.Guid===guid&&x.ModelName===name);
      if(!m)continue;
      if(m.OriginalMaterialCount>=0&&m.OriginalMaterialCount!==count){this.stats.missing.push(guid+": material count mismatch");continue;}
      const a=m.MaterialElements.find(x=>x.MaterialName===mat.name);
      if(!a)continue;
      if(a.OriginalMaterialIndex>=0&&a.OriginalMaterialIndex!==mat.userData.originalMaterialIndex){this.stats.missing.push(guid+"/"+mat.name+": original index mismatch");continue;}
      const sampler=d.DataType===3?"bake0":"bake1",slot=d.DataType===3?"_b0":"_b1";
      const hasSampler=f.samplers?.some(s=>s.sampler===sampler||s.slots.includes(slot));
      const param=d.DataType===3?"gsys_bake_st0":"gsys_bake_st1";
      if(!f.params?.[param]){this.stats.missing.push(guid+"/"+mat.name+": no "+param);continue;}
      if(!hasSampler){this.stats.missing.push(guid+"/"+mat.name+": no "+sampler);continue;}
      if(!mesh.geometry.hasAttribute("uv1")){this.stats.missing.push(guid+"/"+mat.name+": no native _u1");continue;}
      const t=a.TextureIndex>=0&&a.TextureIndex<d.TextureNames.length?this.textures.get(d.TextureNames[a.TextureIndex]):null;
      if(!t){this.stats.missing.push(guid+"/"+mat.name+": invalid texture index");continue;}
      const b:BakeSlot={texture:t,st:new THREE.Vector4(a.TexcoordScale.X,a.TexcoordScale.Y,a.TexcoordOffset.X,a.TexcoordOffset.Y),type:d.DataType,tableIndex:bakeTableIndex(d.BindingSpace,d.DataType)};
      if(d.DataType===3){result.ao=b;this.stats.ao++;}else{result.light=b;this.stats.light++;}
    }
    if(result.ao||result.light){this.stats.materials++;return result;}
    return null;
  }
  dispose():void {for(const t of this.textures.values())t.dispose();}
}
