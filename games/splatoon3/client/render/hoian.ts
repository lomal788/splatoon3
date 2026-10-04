// Known Hoian color/UV/calc consumers. Final lighting/SSS/film scope is recorded in impl/render.md.
import * as THREE from "three";
import type { MaterialTeamParams } from "./teamcolor.ts";
import type {NativeTexSrt} from "./anim/material_channels.ts";
import {nativeTexSrtRowsZeroRotation} from "./anim/material_texsrt.ts";
export interface FresMaterial {
  name?:string;
  shader?:{archive?:string;options?:Record<string,string>;samplerAssign?:Record<string,string>;attribAssign?:Record<string,string>};
  renderInfo?:Record<string,unknown>;
  params?:Record<string,{type?:string;value?:unknown}>;
  samplers?:{sampler:string;texture:string;slots:string[]}[];
}
export type TexResolver=(name:string)=>Promise<THREE.Texture|null>;
export const HOIAN_MATERIAL_END="// H_NATIVE_MATERIAL_END";
export const option=(f:FresMaterial,k:string,d:string):string=>{
  const v=f.shader?.options?.[k];return v===undefined||v==="<Default Value>"?d:v;
};
export const parameter=(f:FresMaterial,k:string,d:number):number=>{
  const v=f.params?.[k]?.value;return typeof v==="number"?Math.fround(v):Array.isArray(v)&&typeof v[0]==="number"?Math.fround(v[0]):d;
};
const vector=(f:FresMaterial,k:string,d:number[]):number[]=>{
  const v=f.params?.[k]?.value;return Array.isArray(v)?v.map(Number):d;
};
export function textureForSlot(f:FresMaterial,slot:string):string|null {return f.samplers?.find(s=>s.slots.includes(slot))?.texture??null;}
const literal=(v:number):string=>Number.isInteger(v)?v+".0":Math.fround(v).toString();
const vec=(v:number[]):string=>"vec4("+v.slice(0,4).map(literal).join(",")+")";
export interface HoianUniforms {myTeamColor:{value:THREE.Vector3};myTeamColorHueComplement:{value:THREE.Vector3};texMatrices?:Record<number,{row0:{value:THREE.Vector4};row1:{value:THREE.Vector4};verified:boolean}>}
/** Mat values animated by FMAA (tank Gauge/InkShortage): uniforms instead of compile-time literals, same initial FRES values. */
const LIVE_PARAMS:Record<string,string>={albedo_color:"hLiveAlbedo",team_color_blend:"hLiveTeamBlend",team_color_blend_alpha:"hLiveTeamBlendAlpha",emission_intensity:"hLiveEmissionIntensity"};
export function setHoianMaterialParam(mat:THREE.Material,name:string,offsets:Record<string,number>):boolean {
  const live=mat.userData.hoianLive as Record<string,{value:number|THREE.Vector4}>|undefined,u=live?.[LIVE_PARAMS[name]];
  if(!u)return false;
  for(const [key,v] of Object.entries(offsets)){const o=Number(key);
    if(u.value instanceof THREE.Vector4){if(o%4||o>12)return false;u.value.setComponent(o/4,Math.fround(v));}
    else if(o===0)u.value=Math.fround(v);else return false;}
  // Default emission path keeps three's emissive×emissiveMap: native Emm·emission_color·emission_intensity.
  const emi=mat.userData.hoianEmissionDefault as number[]|undefined;
  if(name==="emission_intensity"&&emi&&(mat as THREE.MeshStandardMaterial).isMeshStandardMaterial)
    (mat as THREE.MeshStandardMaterial).emissive.setRGB(Math.fround(emi[0]*Number(u.value)),Math.fround(emi[1]*Number(u.value)),Math.fround(emi[2]*Number(u.value)),THREE.LinearSRGBColorSpace);
  return true;
}
/** Native Mat two-vec4 matrix input. TexSrt -> matrix producer is a separate native question. */
export function setHoianTexMatrix(u:HoianUniforms,index:number,packed:readonly number[]):void {
  const m=u.texMatrices?.[index];if(!m||packed.length!==8||packed.some(v=>!Number.isFinite(v)))throw new Error("Hoian native texture matrix unavailable: "+index);
  m.row0.value.fromArray(packed.slice(0,4));m.row1.value.fromArray(packed.slice(4,8));m.verified=true;
}
/** Native callback writes six consumed floats. The unused carrier padding is web-owned zero. */
export function setHoianMaterialTexSrt(mat:THREE.MeshStandardMaterial,name:string,raw:NativeTexSrt):boolean {
  const index:Record<string,number>={tex_mtx0:0,tex_mtx1:2,tex_mtx2:3},i=index[name];
  if(i===undefined||!(mat.userData.hoianTexSrtParams as Set<string>|undefined)?.has(name))return false;
  const matrices=mat.userData.hoianTexMatrices as HoianUniforms["texMatrices"],m=matrices?.[i];if(!m)return false;
  const rows=nativeTexSrtRowsZeroRotation(raw);m.verified=!!rows;
  const stats=mat.userData.characterMaterialStats as {nativeUvMatrices:boolean}|undefined;
  if(stats)stats.nativeUvMatrices=Object.values(matrices!).every(matrix=>matrix.verified);
  if(!rows)return false;
  m.row0.value.fromArray(rows.slice(0,4));m.row1.value.set(rows[4],rows[5],0,0);return true;
}
export function textureUvSelector(f:FresMaterial,key:string,legacy?:string):number {
  return Number(option(f,key,legacy?option(f,legacy,"0"):"0"));
}
const uvAttribute=(f:FresMaterial,index:number):number=>{
  const assigned=f.shader?.attribAssign?.["_u"+index];
  const match=assigned?.match(/^_u([0-3])$/);return match?Number(match[1]):index;
};
export function calcChannel(expr:string,channel:string):string|null {
  const n=Number(channel);
  if(n===0)return expr;if(n===1)return "(vec4(1.)-("+expr+"))";
  if(n===2)return "(-("+expr+"))"; // Selected Tnk_Simple emission type22 uses -Resource0.
  const index=Math.floor(n/10)-1;
  if(index>=0&&index<4 && (n%10===0||n%10===1)) {
    const x="("+expr+")."+["x","y","z","w"][index];
    return "vec4("+(n%10===1?"1.-"+x:x)+")";
  }
  return null;
}
/** Only read sources whose native data exists. Missing C is never dropped from A*B*C. */
export function calcColorGlsl(f:FresMaterial,available:Set<number>,skipped:string[]):string {
  let code="";const temporaries=new Set<number>();
  const source=(id:number):string|null=>{
    if(id===0)return "hCalcAlbedo";if(id===1)return "hCalcRoughness";if(id===2)return "hCalcMetalness";
    if(id===3)return "hCalcEmission";if(id===5)return "hCalcUnderFilm";
    if(id===4)return "hCalcTransmission";
    if(id===9||id===10)return available.has(id)?"hResource"+(id-9):null;
    if(id===50)return "vec4(myTeamColor,1.)";
    if(id===58)return "vec4(myTeamColorHueComplement,1.)";
    if(id>=100&&id<=102)return vec(vector(f,"const_color"+(id-100),[1,1,1,1]));
    if(id===110||id===111)return "vec4("+literal(parameter(f,"const_value"+(id-110),0))+")";
    if(id>=200&&id<204&&temporaries.has(id-200))return "hCalc"+(id-200);
    return null;
  };
  for(let i=0;i<4;i++) {
    if(!["True","1"].includes(option(f,"enable_calc_color"+i,"False")))continue;
    const key="blitz_calc_color"+i+"_",type=option(f,key+"calc_type","0"),target=option(f,key+"replace_color","0");
    const S=(s:string):string|null=>{const raw=source(Number(option(f,key+s,"0")));return raw===null?null:calcChannel(raw,option(f,key+s+"_channel","0"));};
    const [a,b,c,d]=[S("A"),S("B"),S("C"),S("D")];let expression:string|null=null;
    if(type==="1"&&a&&b)expression="("+a+"+"+b+")";
    if(type==="2"&&a&&b)expression="("+a+"*"+b+")";
    // Verified selected squid3358/hair2855: (Resource0 + hue complement) * under-film color.
    if(type==="5"&&a&&b&&c)expression="(("+a+"+"+b+")*"+c+")";
    if(type==="6"&&a&&b&&c&&d)expression="("+a+"*"+b+"+"+c+"*"+d+")";
    if(type==="8"&&a&&b&&c)expression="("+a+"*"+b+"+"+c+")";
    if(type==="9"&&a&&b&&c)expression="("+a+"*"+b+"*"+c+")";
    if(type==="11"&&a&&b&&c&&d)expression="("+a+"*"+b+"*"+c+"*"+d+")";
    if(type==="22"&&a&&b&&c&&d)expression="("+a+"*"+b+"+"+c+"+"+d+")";
    if(!expression){if(type!=="0")skipped.push((f.name??"material")+": calc"+i+" type/source "+type);continue;}
    if(["True","1"].includes(option(f,key+"clamp01","False")))expression="clamp("+expression+",0.,1.)";
    code+="vec4 hCalc"+i+"="+expression+";\n";temporaries.add(i);
    const destination:Record<string,string>={"0":"hCalcAlbedo","1":"hCalcTransmission","2":"hCalcEmission","4":"hCalcRoughness","5":"hCalcMetalness","6":"hCalcOpacity","7":"hCalcUnderFilm"};
    if(destination[target])code+=destination[target]+"=hCalc"+i+";\n";
    else if(target!=="100")skipped.push((f.name??"material")+": calc"+i+" target "+target);
  }
  return code;
}
export function applyHoian(mat:THREE.MeshStandardMaterial,f:FresMaterial,team:MaterialTeamParams,tex:TexResolver,skipped:string[],geometry?:THREE.BufferGeometry):HoianUniforms|null {
  if(f.shader?.archive && f.shader.archive!=="Hoian_UBER")return null;
  const uniforms:HoianUniforms={myTeamColor:{value:new THREE.Vector3(...team.my_team_color.slice(0,3))},myTeamColorHueComplement:{value:new THREE.Vector3(...team.my_team_color_hue_complement.slice(0,3))},texMatrices:{}};
  const textures:Record<string,{value:THREE.Texture|null}>={};const uv:Set<number>=new Set([0]);
  const selectors:Record<string,number>={};
  const bind=(key:string,slot:string,select:string,legacy?:string):void=>{
    const name=textureForSlot(f,slot);if(!name)return;
    const index=textureUvSelector(f,select,legacy),attribute=uvAttribute(f,index);
    if(![0,2,3].includes(index)||(geometry&&attribute>0&&!geometry.hasAttribute("uv"+attribute))){skipped.push(mat.name+": "+select+" UV"+index+" attribute "+attribute+" unavailable");return;}
    uv.add(index);selectors[key]=index;textures[key]={value:null};
    void tex(name).then(t=>{textures[key].value=t;if(!t)skipped.push(mat.name+": texture "+name+" unavailable");mat.needsUpdate=true;});
  };
  bind("hTcl","_su0","texcoord_select_teamcolormap");
  bind("hResource0Tex","_re0","texcoord_select_res0","texcoord_select_resource0");
  bind("hResource1Tex","_re1","texcoord_select_res1","texcoord_select_resource1");
  bind("hResource2Tex","_re2","texcoord_select_res2","texcoord_select_resource2");
  bind("hTransmissionTex","_t0","texcoord_select_trsmap","texcoord_select_transmission");
  const rawCalcEmission=[0,1,2,3].some(i=>["True","1"].includes(option(f,"enable_calc_color"+i,"False"))&&option(f,"blitz_calc_color"+i+"_calc_type","0")==="22");
  if(rawCalcEmission)bind("hNativeEmissionTex","_e0","texcoord_select_emmmap");
  const pbrUV:[string,string,string][]=[["USE_MAP","vMapUv","texcoord_select_albedo"],["USE_NORMALMAP","vNormalMapUv","texcoord_select_normal"],
    ["USE_ROUGHNESSMAP","vRoughnessMapUv","texcoord_select_rghmap"],["USE_METALNESSMAP","vMetalnessMapUv","texcoord_select_mtlmap"],["USE_EMISSIVEMAP","vEmissiveMapUv","texcoord_select_emmmap"]];
  const pbrWrites:string[]=[];
  for(const [define,varying,key] of pbrUV){const index=textureUvSelector(f,key),a=uvAttribute(f,index);
    if(![0,2,3].includes(index)||(geometry&&a>0&&!geometry.hasAttribute("uv"+a))){skipped.push(mat.name+": "+key+" UV"+index+" attribute "+a+" unavailable");continue;}
    uv.add(index);pbrWrites.push("#ifdef "+define+"\n"+varying+"=hUV"+index+";\n#endif\n");}
  const d=mat as unknown as {defines:Record<string,string>};
  d.defines={...(d.defines??{}),USE_UV:""};
  for(const i of uv)if(i>0)d.defines["USE_UV"+i]="";
  const texSrtParams=new Set<string>();
  for(const i of uv){const name="tex_mtx"+(i===0?0:i===2?1:2),p=f.params?.[name]?.value as NativeTexSrt|undefined,rows=p?nativeTexSrtRowsZeroRotation(p):null;
    if(p)texSrtParams.add(name);
    uniforms.texMatrices![i]={row0:{value:rows?new THREE.Vector4().fromArray(rows.slice(0,4)):new THREE.Vector4(1,0,0,1)},row1:{value:rows?new THREE.Vector4(rows[4],rows[5],0,0):new THREE.Vector4(0,0,0,0)},verified:!!rows};
    if(!rows)skipped.push(mat.name+": "+name+" native SRT-to-Mat mode/rotation consumer remains");}
  mat.userData.hoianTexMatrices=uniforms.texMatrices;
  mat.userData.hoianTexSrtParams=texSrtParams;
  const tcm=option(f,"team_color_map_type","0"),ect=option(f,"emission_color_type","0");
  const useAlbedo=!["False","0"].includes(option(f,"enable_albedo_tex","1"));
  const alb=vector(f,"albedo_color",[1,1,1,1]),emi=vector(f,"emission_color",[1,1,1,1]),backlight=vector(f,"transmission_color_backlight",[1,1,1,1]);
  if(!useAlbedo){mat.map=null;mat.color.setRGB(1,1,1);}
  const live={hLiveAlbedo:{value:new THREE.Vector4(...[0,1,2,3].map(i=>Math.fround(alb[i]??1)))},hLiveTeamBlend:{value:parameter(f,"team_color_blend",0)},
    hLiveTeamBlendAlpha:{value:parameter(f,"team_color_blend_alpha",0)},hLiveEmissionIntensity:{value:parameter(f,"emission_intensity",0)}};
  mat.userData.hoianLive=live;
  const replace2=["0","1","2","3"].some(i=>option(f,"enable_calc_color"+i,"False")==="True"&&option(f,"blitz_calc_color"+i+"_replace_color","0")==="2");
  if(ect==="0"&&!replace2&&!rawCalcEmission)mat.userData.hoianEmissionDefault=emi.slice(0,3);
  mat.onBeforeCompile=sh=>{
    Object.assign(sh.uniforms,uniforms,textures,live);
    const available=new Set<number>();
    if(textures.hResource0Tex?.value)available.add(9);if(textures.hResource1Tex?.value)available.add(10);
    if(textures.hTransmissionTex?.value)available.add(4);
    let vertex="",fragment="",uvWrites="";
    for(const i of uv) {
      const a=uvAttribute(f,i),src=a===0?"uv":"uv"+a,m=uniforms.texMatrices![i];
      vertex+="varying vec2 hUV"+i+";\nuniform vec4 hTexRow0_"+i+",hTexRow1_"+i+";\n";fragment+="varying vec2 hUV"+i+";\n";
      sh.uniforms["hTexRow0_"+i]=m.row0;sh.uniforms["hTexRow1_"+i]=m.row1;
      uvWrites+="hUV"+i+"=vec2("+src+".x*hTexRow0_"+i+".x+"+src+".y*hTexRow0_"+i+".z+hTexRow1_"+i+".x,"+src+".x*hTexRow0_"+i+".y+"+src+".y*hTexRow0_"+i+".w+hTexRow1_"+i+".y);\n";
    }
    for(const key of Object.keys(textures))fragment+="uniform sampler2D "+key+";\n";
    fragment+="uniform vec4 hLiveAlbedo;\nuniform float hLiveTeamBlend,hLiveTeamBlendAlpha,hLiveEmissionIntensity;\n";
    const sample=(key:string):string=>"texture2D("+key+",hUV"+selectors[key]+")";
    let setup="vec4 hCalcAlbedo="+(useAlbedo?"diffuseColor":"hLiveAlbedo")+";\n";
    if(tcm==="2"&&textures.hTcl?.value)setup+="hCalcAlbedo.rgb=mix(hCalcAlbedo.rgb,myTeamColor,clamp("+sample("hTcl")+".r+hLiveTeamBlendAlpha,0.,1.));\n";
    else if(tcm==="3")setup+="hCalcAlbedo.rgb=mix(hLiveAlbedo.rgb,myTeamColor,clamp(hLiveTeamBlend,0.,1.));\n";
    setup+="vec4 hCalcRoughness=vec4(max(roughnessFactor,.0001)),hCalcMetalness=vec4(metalnessFactor),hCalcTransmission="+vec(backlight)+",hCalcUnderFilm="+vec(vector(f,"under_film_color",[1,1,1,1]))+";\n";
    const rawEmission=!!(rawCalcEmission&&textures.hNativeEmissionTex?.value);
    setup+="vec4 hCalcOpacity=vec4(diffuseColor.a),hCalcEmission="+(rawEmission?"vec4("+sample("hNativeEmissionTex")+".rgb*"+vec(emi)+".rgb,1.)":"vec4(hLiveEmissionIntensity!=0.?totalEmissiveRadiance/hLiveEmissionIntensity:vec3(0.),1.)")+";\n";
    if(available.has(9))setup+="vec4 hResource0="+sample("hResource0Tex")+";\n";
    if(available.has(10))setup+="vec4 hResource1="+sample("hResource1Tex")+";\n";
    if(available.has(4))setup+="hCalcTransmission="+sample("hTransmissionTex")+"*"+vec(backlight)+";\n";
    if(option(f,"transmission_multi_color","0")==="2")setup+="hCalcTransmission.rgb*=myTeamColor;\n";
    setup+=calcColorGlsl(f,available,skipped);
    setup+="diffuseColor.rgb=hCalcAlbedo.rgb;diffuseColor.a=hCalcOpacity.w;roughnessFactor=hCalcRoughness.x;metalnessFactor=hCalcMetalness.x;\n";
    const emiInt="hLiveEmissionIntensity";
    if(ect==="1")setup+="totalEmissiveRadiance=diffuseColor.rgb*hCalcEmission.rgb"+(rawEmission?"":"*"+emiInt)+";\n";
    else if(ect==="2")setup+="totalEmissiveRadiance=myTeamColor*"+vec(emi)+".rgb*"+emiInt+";\n";
    else if(["0","1","2","3"].some(i=>option(f,"enable_calc_color"+i,"False")==="True"&&option(f,"blitz_calc_color"+i+"_replace_color","0")==="2"))
      setup+="totalEmissiveRadiance=hCalcEmission.rgb*"+emiInt+";\n";
    setup+=HOIAN_MATERIAL_END+"\n";
    sh.vertexShader=vertex+sh.vertexShader.replace("#include <uv_vertex>","#include <uv_vertex>\n"+uvWrites+pbrWrites.join(""));
    sh.fragmentShader="uniform vec3 myTeamColor,myTeamColorHueComplement;\n"+fragment+sh.fragmentShader
      .replace("#include <emissivemap_fragment>","#include <emissivemap_fragment>\n"+setup);
    // Transmission/film values are kept for the native material consumers; full SSS isn't invented.
    if(!mat.userData.nativeCharacterMaterial&&option(f,"enable_transfilm","False")==="True")skipped.push(mat.name+": native film lighting consumer remains");
    if(!mat.userData.nativeCharacterMaterial&&option(f,"enable_taransmission","False")==="True")skipped.push(mat.name+": native taransmission/SSS lighting consumer remains");
    if(option(f,"enable_transmission","False")==="True")skipped.push(mat.name+": separate native transmission option consumer remains");
  };
  mat.customProgramCacheKey=()=>JSON.stringify({options:f.shader?.options,params:f.params,uv:[...uv],loaded:Object.entries(textures).map(([k,v])=>[k,!!v.value])});
  mat.needsUpdate=true;return uniforms;
}
export function setTeam(u:HoianUniforms,team:MaterialTeamParams):void {
  u.myTeamColor.value.fromArray(team.my_team_color);u.myTeamColorHueComplement.value.fromArray(team.my_team_color_hue_complement);
}
