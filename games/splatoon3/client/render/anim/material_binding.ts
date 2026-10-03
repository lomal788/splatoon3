import * as THREE from "three";
import {option,type FresMaterial,type TexResolver} from "../hoian.ts";
import {sampleOrdinaryMaterialLeaves,type MaterialAnimationGroup,type MaterialPatch,type MaterialSample} from "./material_channels.ts";

export interface MaterialChannelTarget {material:THREE.MeshStandardMaterial;fres:FresMaterial;tex:TexResolver}
/** Return false for an unimplemented native typed parameter consumer. */
export type MaterialParameterConsumer=(target:MaterialChannelTarget,name:string,offsets:Record<string,number>)=>boolean;
export interface MaterialChannelBinding {
  ready:Promise<void>;
  stats:{applied:number;patternWrites:number;missing:string[];unsupported:string[];lastClip:string|null;rawSrtUnbound:boolean;hooks:number};
  apply(leaves:{type:number;clip:string;frame:number;weight:number}[]):void;
  applySample(sample:MaterialSample|null):void;
  dispose():void;
}

/** Raw pattern slots bind the existing model textures; _r0 reads original R, not glTF packed G.
 * Nonidentity TexSrt requires a separately proven matrix consumer. It is never guessed here.
 */
export function bindMaterialChannels(targets:MaterialChannelTarget[],group:MaterialAnimationGroup,consume?:MaterialParameterConsumer):MaterialChannelBinding {
  const unique=targets.filter((t,i)=>targets.findIndex(x=>x.material===t.material)===i);
  const stats={applied:0,patternWrites:0,missing:[] as string[],unsupported:[] as string[],lastClip:null as string|null,rawSrtUnbound:false,hooks:0};
  const report=(list:string[],s:string):void=>{if(!list.includes(s))list.push(s);};
  let disposed=false;
  const records=unique.map(target=>{
    const mat=target.material,prev=mat.onBeforeCompile,key=mat.customProgramCacheKey;
    const original={map:mat.map,normalMap:mat.normalMap};
    const uniforms={mCActiveA:{value:0},mCActiveN:{value:0},mCActiveR:{value:0},mCRgh:{value:null as THREE.Texture|null}};
    const textures=new Map<string,THREE.Texture|null>();
    // Patterns share the original material sampler. Resolver-owned textures remain owned by the resolver.
    const hook:THREE.MeshStandardMaterial["onBeforeCompile"]=(shader,renderer)=>{
      prev.call(mat,shader,renderer);Object.assign(shader.uniforms,uniforms);
      if(!shader.vertexShader.includes("varying vec2 hUV0;")||!shader.fragmentShader.includes("varying vec2 hUV0;"))
        throw new Error("Material pattern hook requires Hoian native UV0: "+mat.name);
      shader.fragmentShader="uniform float mCActiveA,mCActiveN,mCActiveR;\nuniform sampler2D mCRgh;\n"+shader.fragmentShader
        .replace("#include <map_fragment>",THREE.ShaderChunk.map_fragment.replaceAll("vMapUv","(mCActiveA>.5?hUV0:vMapUv)"))
        .replace("#include <normal_fragment_maps>",THREE.ShaderChunk.normal_fragment_maps.replaceAll("vNormalMapUv","(mCActiveN>.5?hUV0:vNormalMapUv)"))
        .replace("#include <roughnessmap_fragment>",
        "#include <roughnessmap_fragment>\nif(mCActiveR>.5)roughnessFactor=roughness*texture2D(mCRgh,hUV0).r;\n");
      stats.hooks++;
    };
    const cacheKey=()=>key.call(mat)+":nativeFMAAPatternR";
    mat.onBeforeCompile=hook;mat.customProgramCacheKey=cacheKey;mat.needsUpdate=true;
    return {target,original,uniforms,textures,prev,key,hook,cacheKey};
  });
  const referenced=new Set(group.clips.flatMap(c=>c.textureNames));
  const ready=Promise.all(records.flatMap(r=>[...referenced].map(async name=>{
    try {const t=await r.target.tex(name);if(!disposed)r.textures.set(name,t);}
    catch(e){if(!disposed){r.textures.set(name,null);report(stats.missing,"texture resolver failed: "+name+" "+String(e));}}
  }))).then(()=>{});
  function parameter(r:typeof records[number],patch:MaterialPatch):void {
    for(const [name,offsets] of Object.entries(patch.params)) {
      if(consume?.(r.target,name,offsets))continue;
      if(name.startsWith("tex_mtx")) {
        // A supplied raw SRT update alone does not establish native Mat rows.
        stats.rawSrtUnbound=true;
        report(stats.unsupported,patch.material+": "+name+" native SRT-to-Mat consumer unbound");
      } else report(stats.unsupported,patch.material+": native parameter consumer unbound: "+name);
    }
  }
  function applySample(sample:MaterialSample|null):void {
    if(disposed||!sample)return;
    if(!sample.supported){report(stats.unsupported,sample.reason);return;}
    stats.lastClip=sample.clip.name;
    for(const patch of sample.patches) {
      const selected=records.filter(r=>(r.target.fres.name??r.target.material.name)===patch.material);
      if(!selected.length){report(stats.missing,"native material target unavailable: "+patch.material);continue;}
      for(const r of selected) {
        parameter(r,patch);
        for(const [slot,name] of Object.entries(patch.patterns)) {
          const tex=r.textures.get(name);
          if(!tex){report(stats.missing,"native pattern texture unavailable: "+name);continue;}
          const f=r.target.fres,mat=r.target.material;
          if(slot==="_a0"&&!["False","0"].includes(option(f,"enable_albedo_tex","1"))){if(mat.map!==tex){mat.map=tex;mat.needsUpdate=true;}r.uniforms.mCActiveA.value=1;stats.patternWrites++;}
          else if(slot==="_n0"&&!["False","0"].includes(option(f,"enable_normal_map","1"))){if(mat.normalMap!==tex){mat.normalMap=tex;mat.needsUpdate=true;}r.uniforms.mCActiveN.value=1;stats.patternWrites++;}
          else if(slot==="_r0"&&["True","1"].includes(option(f,"enable_roughness_map","False"))){r.uniforms.mCRgh.value=tex;r.uniforms.mCActiveR.value=1;stats.patternWrites++;}
          else report(stats.unsupported,patch.material+": native pattern slot consumer unavailable: "+slot);
        }
        stats.applied++;
      }
    }
  }
  return {ready,stats,apply(leaves){applySample(sampleOrdinaryMaterialLeaves(group,leaves));},applySample,dispose(){
    if(disposed)return;disposed=true;
    for(const r of records){const mat=r.target.material;if(mat.onBeforeCompile===r.hook)mat.onBeforeCompile=r.prev;
      if(mat.customProgramCacheKey===r.cacheKey)mat.customProgramCacheKey=r.key;
      mat.map=r.original.map;mat.normalMap=r.original.normalMap;mat.needsUpdate=true;}
  }};
}
