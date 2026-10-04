import * as THREE from "three";
import {HOIAN_MATERIAL_END,option,parameter,textureForSlot,textureUvSelector,type FresMaterial,type TexResolver} from "./hoian.ts";
import {FORWARD_SURFACE_END,FORWARD_LIGHTING_BEGIN,FORWARD_LIGHTING_END} from "./forward.ts";
import type {CharacterParameters} from "./character_material_math.ts";

type Uniform<T>={value:T};
export interface CharacterMaterialBinding {
  ready:Promise<void>;
  stats:{material:string;mode:string;variant:string;nativeUvMatrices:boolean;textureReady:boolean;hookCompiled:number;compPaint:string;missing:string[];ordinaryConsumer:boolean};
  uniforms:Record<string,Uniform<unknown>>;
  dispose():void;
}
const enabled=(f:FresMaterial,k:string):boolean=>["True","1"].includes(option(f,k,"False"));
export function characterVariantProfile(f:FresMaterial):{kind:"painted"|"sfxFilm"|"constantFilm";paint:boolean;thickness:boolean;sfx:boolean;ao:boolean;edge:boolean;manualFresnel:boolean;transmissionMap:boolean}|null {
  const paint=option(f,"blitz_paint_type","0")==="4",thickness=enabled(f,"enable_thickness_map"),sfx=enabled(f,"enable_sfxmask"),cheap=enabled(f,"enable_cheap_sss"),film=enabled(f,"enable_transfilm"),mask=option(f,"transmission_mask","3");
  const kind=paint&&thickness?"painted":!paint&&!thickness&&!cheap&&film&&sfx&&mask==="2"?"sfxFilm":
    !paint&&!thickness&&!cheap&&film&&!sfx&&mask==="3"&&!enabled(f,"enable_transmission_map")?"constantFilm":null;
  return kind?{kind,paint,thickness,sfx,ao:enabled(f,"enable_ao"),edge:enabled(f,"enable_edge_transmission"),manualFresnel:enabled(f,"enable_manual_fresnel"),transmissionMap:enabled(f,"enable_transmission_map")}:null;
}
const vec3param=(f:FresMaterial,k:string):[number,number,number]=>{
  const v=f.params?.[k]?.value;if(!Array.isArray(v)||v.length<3)throw new Error("Character native parameter missing: "+k);
  return v.slice(0,3).map(Number) as [number,number,number];
};
export function characterParameters(f:FresMaterial):CharacterParameters {
  const scalar=(k:string):number=>{if(f.params?.[k]?.value===undefined)throw new Error("Character native parameter missing: "+k);return parameter(f,k,NaN);};
  return {transmissionRate:scalar("transmission_rate"),scatteringRate:scalar("scattering_rate"),scatterDistance:scalar("scatter_distance"),
    scatteringColor:vec3param(f,"scattering_color"),edgePower:scalar("edge_transmission_power"),filmRate:scalar("film_transmission_rate"),
    filmPower:scalar("film_transmission_power"),manualFresnel:scalar("manual_fresnel"),manualFresnelColor:vec3param(f,"manual_fresnel_color")};
}
export const CHARACTER_MATERIAL_GLSL=String.raw`
uniform vec4 hCharRates; // transmission, scattering, scatter distance, edge power
uniform vec2 hCharFilm;
uniform vec3 hCharScatter,hCharManualColor;
uniform float hCharManualFresnel,hCharReady,hCharCPIntensity,hCharCPOffset,hCharCPNormal,hCharCPTeam,hCharFilmEnabled,hCharCheap,hCharEdgeEnabled;
uniform float hLightAlpha;
varying vec3 hCharNv,hCharTangent;
float hCharScatterLobe(float voL) {
  float q=(hCharRates.y-1.)*(hCharRates.y-1.);
  return q*exp2(log2(clamp(max(-voL,.001),0.,1.))/hCharRates.y)-q*.2+.200000003;
}
float hCharEdge(float noV,float noL,float voL,float k) {
  return exp2(log2(clamp(1.-noV*clamp(-noL,0.,1.),0.,1.))*hCharRates.w)*
    hCharScatterLobe(voL)*k;
}
vec3 hCharDirect(float noL,vec3 rgb,float mask) {
  float n=clamp(noL,0.,1.),wrap=clamp(noL+hCharRates.z,0.,1.)/(1.+hCharRates.z);
  return (clamp(vec3(n)+hCharScatter,0.,1.)*wrap*rgb-n*rgb)*mask+n*rgb;
}
float hCharFilmAmount(float noV,float mask,float k) {
  return clamp(exp2(log2(clamp(max(noV,.001),0.,1.))*hCharFilm.y)*hCharFilm.x*mask,0.,1.)*k;
}
float hCharCorrection(vec3 n,vec3 nc,vec3 l,float signedPaint) {
  float c=n.y*(1.-dot(nc,l));return clamp(c*clamp(signedPaint*-7.,0.,1.)-c+1.16,0.,1.);
}
vec3 hCharDynamic(vec3 p,vec3 n,vec3 v,vec3 diffuse,vec3 f0,float roughness,float mask,float k,vec3 transmission,float tau,float aoLight) {
  ivec2 cell=clamp(ivec2((p.xz-hGridOrigin.xz)*hInvCell.xz),ivec2(0),ivec2(19));
  uint packed=texelFetch(hGrid,cell,0).r;vec3 c=vec3(0.);
  for(int slot=0;slot<4;slot++) {
    uint index=(packed>>uint(slot*8))&255u;if(index>=30u)break;
    vec3 delta=hDynPos[index].xyz-p;float distance=length(delta);vec3 l=delta/distance;
    vec4 att=hDynAtt[index];float attenuation=exp2(att.y*log2(clamp(1.-att.x*distance,0.,1.)));
    if(hDynPos[index].w!=0.)attenuation*=exp2(att.w*log2(clamp((-dot(l,hDynDir[index].xyz)-att.z)/(1.-att.z),0.,1.)));
    float noL=dot(n,l),edge=(hCharEdgeEnabled>.5?hCharEdge(dot(n,v),noL,dot(v,l),k):hCharScatterLobe(dot(v,l))*k);
    vec3 direct=hCharDirect(noL,hDynColor[index].rgb,mask)*attenuation;
    c+=direct*(diffuse*.318309873+hSpecular(f0,roughness,n,v,l))*clamp(1.-tau,0.,1.)+
      aoLight*edge*attenuation*hDynColor[index].w*transmission*tau;
  }
  return c;
}
`;
/** Selected actual character variants. Existing material calc/UV plus live RGBA light are prerequisites. */
export function applyCharacterMaterial(mat:THREE.MeshStandardMaterial,f:FresMaterial,tex:TexResolver,skipped:string[],geometry:THREE.BufferGeometry|undefined,lightAlpha:Uniform<number>):CharacterMaterialBinding|null {
  if(!enabled(f,"enable_taransmission"))return null;
  if(!mat.userData.nativeForward)throw new Error("Character material requires native forward first");
  if(mat.userData.nativeCharacterMaterial)throw new Error("Character material already attached");
  const cheap=enabled(f,"enable_cheap_sss"),film=enabled(f,"enable_transfilm");
  const profile=characterVariantProfile(f);
  if(!profile){skipped.push(mat.name+": unsupported native taransmission variant");return null;}
  if(!geometry?.hasAttribute("tangent")){skipped.push(mat.name+": native character tangent unavailable");return null;}
  const uvVerified=():boolean=>Object.values(mat.userData.hoianTexMatrices??{}).every(m=>(m as {verified:boolean}).verified);
  const p=characterParameters(f),stats={material:mat.name,mode:cheap?"cheapSSS body/face":profile.kind==="painted"?"film squid/hair":profile.kind==="sfxFilm"?"film FxM tank/harness":"film constant bottle",variant:profile.kind,nativeUvMatrices:uvVerified(),textureReady:false,hookCompiled:0,
    compPaint:profile.paint?"actual static 2cl and BFRES values; runtime material animation remains":"native selected shader has no CompPaint sample",missing:[] as string[],ordinaryConsumer:false};
  const textures:Record<string,Uniform<THREE.Texture|null>>={hCharThcTex:{value:null},hCharCPTex:{value:null},hCharMaskTex:{value:null},hCharAOTex:{value:null}};
  const uniforms:Record<string,Uniform<unknown>>={...textures,hLightAlpha:lightAlpha,hCharRates:{value:new THREE.Vector4(p.transmissionRate,p.scatteringRate,p.scatterDistance,p.edgePower)},
    hCharFilm:{value:new THREE.Vector2(p.filmRate,p.filmPower)},hCharScatter:{value:new THREE.Vector3(...p.scatteringColor)},
    hCharManualColor:{value:new THREE.Vector3(...p.manualFresnelColor)},hCharManualFresnel:{value:p.manualFresnel},hCharReady:{value:0},
    hCharCPIntensity:{value:parameter(f,"two_color_complement_paint_intensity",NaN)},hCharCPOffset:{value:parameter(f,"comp_paint_texcoord_offset",NaN)},
    hCharCPNormal:{value:parameter(f,"comp_paint_norm_intens",NaN)},hCharCPTeam:{value:parameter(f,"two_comp_paint_team",NaN)},
    hCharFilmEnabled:{value:film?1:0},hCharCheap:{value:cheap?1:0},hCharEdgeEnabled:{value:profile.edge?1:0}};
  const loads:Promise<void>[]=[];
  // Fragment texture units are limited (16 on d3d11/most GPUs). A slot holding the same FRES texture on the same
  // UV as Hoian's bound _re0 reads that sampler: identical texels, one unit (body/face _fm0=_re0 MAi, hair/squid _re2=_re0 Thc).
  const glslName:Record<string,string>={};
  const re0=textureForSlot(f,"_re0"),re0Uv=textureUvSelector(f,"texcoord_select_res0","texcoord_select_resource0");
  const slot=(key:string,s:string,selector:string,required=true,legacy?:string):void=>{
    const name=textureForSlot(f,s),i=textureUvSelector(f,selector,legacy);
    if(!name||i!==0){if(required)stats.missing.push(!name?s+" texture missing":selector+" UV"+i+" unsupported");return;}
    glslName[key]=name===re0&&re0Uv===0&&s!=="_re0"?"hResource0Tex":key;
    loads.push(tex(name).then(t=>{textures[key].value=t;if(!t)stats.missing.push(name+" unavailable");}));
  };
  const hasAO=profile.ao;
  if(profile.thickness)slot("hCharThcTex","_re2","texcoord_select_res2",true,"texcoord_select_resource2");
  if(profile.paint)slot("hCharCPTex","_cp0","texcoord_select_comppaint");
  if(cheap||profile.sfx)slot("hCharMaskTex","_fm0","texcoord_select_sfxmask");
  if(hasAO)slot("hCharAOTex","_ao0","texcoord_select_ao");
  // These consumers are sampled by applyHoian, not repeated here. Their real handles
  // are still prerequisites for declaring this character material ready.
  const calcResources=new Set<string>();
  for(let i=0;i<4;i++)if(enabled(f,"enable_calc_color"+i))for(const operand of ["A","B","C","D"]){const source=option(f,"blitz_calc_color"+i+"_"+operand,"0");if(source==="9")calcResources.add("_re0");if(source==="10")calcResources.add("_re1");
    if(source==="3"&&option(f,"blitz_calc_color"+i+"_calc_type","0")==="22"&&enabled(f,"enable_emission_map"))calcResources.add("_e0");}
  if(profile.transmissionMap)calcResources.add("_t0");
  for(const s of calcResources){const name=textureForSlot(f,s);
    if(!name)stats.missing.push(s+" material-calc texture missing");
    else loads.push(tex(name).then(t=>{if(!t)stats.missing.push(name+" material-calc unavailable");}));}
  if(geometry.hasAttribute("tangent"))(mat as unknown as {defines:Record<string,string>}).defines={...(mat as unknown as {defines?:Record<string,string>}).defines,USE_TANGENT:""};
  const prev=mat.onBeforeCompile,key=mat.customProgramCacheKey;
  const hook:THREE.MeshStandardMaterial["onBeforeCompile"]=(sh,renderer)=>{
    prev.call(mat,sh,renderer);
    for(const anchor of [HOIAN_MATERIAL_END,FORWARD_SURFACE_END,FORWARD_LIGHTING_BEGIN,FORWARD_LIGHTING_END])
      if(!sh.fragmentShader.includes(anchor))throw new Error("Character material anchor missing: "+anchor);
    Object.assign(sh.uniforms,uniforms);
    sh.vertexShader="varying vec3 hCharNv,hCharTangent;\n"+sh.vertexShader.replace("#include <defaultnormal_vertex>",
      "#include <defaultnormal_vertex>\nhCharNv=inverseTransformDirection(transformedNormal,viewMatrix);\nhCharTangent=inverseTransformDirection(transformedTangent,viewMatrix);\n");
    const own=Object.entries(glslName).filter(([k,v])=>k===v).map(([k])=>k);
    const declarations=(own.length?"uniform sampler2D "+own.join(",")+";\n":"")+CHARACTER_MATERIAL_GLSL.replace("uniform float hLightAlpha;",sh.fragmentShader.includes("uniform float hLightAlpha;")?"":"uniform float hLightAlpha;");
    const main=sh.fragmentShader.match(/void\s+main\s*\(\s*\)\s*\{/);
    if(!main||main.index===undefined)throw new Error("Character fragment entry missing");
    sh.fragmentShader=sh.fragmentShader.slice(0,main.index)+declarations+sh.fragmentShader.slice(main.index);
    sh.fragmentShader=sh.fragmentShader.replace(HOIAN_MATERIAL_END,String.raw`
      float hCMask=0.,hCFilmMask=1.,hCTMask=1.,hCK=1.,hCAO=1.,hCPaintSigned=0.;vec3 hCNc=normalize(hCharNv);
      vec3 hCTransmission=hCalcTransmission.rgb,hCUnderFilm=hCalcUnderFilm.rgb;
      if(hCharReady>.5){
        `+(profile.thickness?"hCK=1.-texture2D("+glslName.hCharThcTex+",hUV0).r;\n":"")+
          (cheap?"hCMask=texture2D("+glslName.hCharMaskTex+",hUV0).r;\n":"")+
          (profile.kind==="sfxFilm"?"hCFilmMask=texture2D("+glslName.hCharMaskTex+",hUV0).r;hCTMask=hCFilmMask;\n":"")+
          (hasAO?"hCAO=clamp(texture2D("+glslName.hCharAOTex+",hUV0).r,0.,1.);\n":"")+
          (profile.paint?String.raw`
        float cp=texture2D(hCharCPTex,hUV0).r;
        float gradient=texture2D(hCharCPTex,hUV0+vec2(hCharCPOffset)).r-texture2D(hCharCPTex,hUV0-vec2(hCharCPOffset)).r;
        hCNc=normalize(normalize(hCharNv)+hCharTangent*gradient*hCharCPNormal);
        float team=1.-hCharCPTeam,c=min(cp+hCharCPIntensity-1.,.3)+.30000001192092896;
        vec3 cc=vec3(c*(1.-abs(team)),c*max(0.,team),c*max(0.,-team));
        hCPaintSigned=max(cc.z,max(cc.x,cc.y))-.30000001192092896;
        `:"")+String.raw`
      }
      `+HOIAN_MATERIAL_END)
      .replace(FORWARD_SURFACE_END,String.raw`
        float hCTau=0.,hCNormalCorrection=1.;
        if(hCharReady>.5){
          float film=hCharFilmEnabled*hCharFilmAmount(dot(hN,hV),hCFilmMask,hCK);
          hIrradianceNormal=mix(hN,normalize(hCharNv),film);
          hDiffuse=mix(hDiffuse,hCUnderFilm,film);
          `+(profile.manualFresnel?"hF0=hCharManualFresnel*hCharManualColor;\n":"")+String.raw`
          hCTau=hCharRates.x*(hCharFilmEnabled>.5?hCTMask*(1.-film):hCMask);
          `+(profile.paint?"hCNormalCorrection=hCharCorrection(hN,hCNc,hL,hCPaintSigned);\n":"")+String.raw`
        }
      `+FORWARD_SURFACE_END);
    const begin=sh.fragmentShader.indexOf(FORWARD_LIGHTING_BEGIN),end=sh.fragmentShader.indexOf(FORWARD_LIGHTING_END);
    const old=sh.fragmentShader.slice(begin+FORWARD_LIGHTING_BEGIN.length,end);
    const native=String.raw`
      if(hCharReady>.5){
        float hCShadow=clamp(1.-((1.-hDynamicShadow(hWorldPosition,hViewDepth))+hProjectionOcclusion(hWorldPosition)),0.,1.);
        // body5549 l.589-591/697/800: AoLight = sat(1-(1-SPP.y)*clamp(viewZ+UBO36.z)*UBO36.w) — static prepass channel only.
        float hCAoLight=clamp(1.-(1.-hShadowPrePass(hWorldPosition,hViewDepth).y)*clamp(hShadowFarDepthTest-hViewDepth,0.,1.)*hAOMain,0.,1.);
        vec3 hCd=hCharDirect(dot(hN,hL),hLightColor,hCMask);
        float hCEdge=(hCharEdgeEnabled>.5?hCharEdge(dot(hN,hV),dot(hN,hL),dot(hV,hL),hCK):hCharScatterLobe(dot(hV,hL))*hCK);
        reflectedLight.indirectDiffuse=hDiffuse*(1.-hF0)*hEvaluateSH(hIrradianceNormal)*hCAO+
          hCharDynamic(hWorldPosition,hN,hV,hDiffuse,hF0,hR,hCMask,hCK,hCTransmission,hCTau,hCAoLight)*hCAO;
        reflectedLight.directDiffuse=(hDiffuse*.318309873)*hCd*hCShadow*clamp(1.-hCTau,0.,1.)*hCNormalCorrection+
          hCAoLight*hCEdge*hCTransmission*hLightAlpha*hCTau;
        reflectedLight.directSpecular=hSpecular(hF0,hR,hN,hV,hL)*hCd*hCShadow*clamp(1.-hCTau,0.,1.)*hCNormalCorrection;
        // body5549 l.624-642: cPrefilEnvMapArray[roundEven(5.5-5.5cos(pi r))](reflect) x (F0*BRDF.x+BRDF.y), x AO —
        // the same native lookup forward.ts uses (no three PMREM sampler).
        reflectedLight.indirectSpecular=hNativeEnvSpecular(hN,hV,hF0,hR)*hCAO;
      }else{
      `+old+"\n}\n";
    sh.fragmentShader=sh.fragmentShader.slice(0,begin+FORWARD_LIGHTING_BEGIN.length)+native+sh.fragmentShader.slice(end);
    stats.hookCompiled++;stats.ordinaryConsumer=stats.textureReady;stats.nativeUvMatrices=uvVerified();
  };
  const cacheKey=()=>key.call(mat)+":nativeCharacter:"+cheap+":"+film+":"+hasAO+":"+profile.kind+":"+profile.edge+":"+profile.manualFresnel+":"+JSON.stringify(glslName);
  mat.onBeforeCompile=hook;mat.customProgramCacheKey=cacheKey;
  mat.userData.nativeCharacterMaterial=true;mat.userData.characterMaterialStats=stats;mat.needsUpdate=true;
  const ready=Promise.all(loads).then(()=>{
    if(stats.missing.length){skipped.push(...stats.missing.map(s=>mat.name+": "+s));return;}
    if(profile.paint&&Number(uniforms.hCharCPIntensity.value)!==0){stats.missing.push("runtime CompPaint ink branch needs native ink uniform supply");skipped.push(mat.name+": runtime CompPaint ink branch unbound");return;}
    stats.textureReady=true;uniforms.hCharReady.value=1;mat.needsUpdate=true;
  });
  return {ready,stats,uniforms,dispose(){if(mat.onBeforeCompile===hook)mat.onBeforeCompile=prev;if(mat.customProgramCacheKey===cacheKey)mat.customProgramCacheKey=key;
    delete mat.userData.nativeCharacterMaterial;delete mat.userData.characterMaterialStats;mat.needsUpdate=true;}};
}
