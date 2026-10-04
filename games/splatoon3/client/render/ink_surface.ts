// Native ink material consumer inside the existing stage draw, not a collision overlay.
// Input atlas/geometry and PMREM/BRDF remain explicitly documented web adapters.
import * as THREE from "three";
import { INK_DAY_PARAMS, inkSurfaceFrame } from "./ink_surface_math.ts";
import type { V3 } from "./graphics_math.ts";
import { FORWARD_SURFACE_GLSL, FORWARD_SURFACE_END } from "./forward.ts";
import { PREFILTER_LOOKUP_GLSL, PREFILTER_INK_GLSL } from "./env_prefilter.ts";

export interface InkSurfaceBindings {
  texture:THREE.Texture;
  ink:readonly V3[];
  inkBright:readonly V3[];
  /** Normalized interval in the actual supplied atlas. Native 1/3200 cannot be copied into arbitrary web charts. */
  textureStep:readonly [number,number];
  /** Active env "Ink" reader. Must be supplied; an unknown live value is not invented here. */
  emission:number;
  uvAlreadyFlipped?:boolean;
  attributeNames?:{uv:string;selector:string;tangent:string};
}
export interface InkSurfaceBinding {
  uniforms:{
    hInkTexture:{value:THREE.Texture};hInkColors:{value:THREE.Vector3[]};hInkBright:{value:THREE.Vector3[]};
    hInkStep:{value:THREE.Vector2};hInkFrame:{value:THREE.Vector4};hInkEmission:{value:number};
  };
  updateFrame(frame:number):void;
  setTexture(texture:THREE.Texture):void;
  /** Atlas textures and the material are caller-owned. Only removes the hooks installed here. */
  dispose():void;
}

export const INK_SURFACE_GLSL=String.raw`
uniform sampler2D hInkTexture;
uniform vec3 hInkColors[3],hInkBright[3];
uniform vec2 hInkStep;
uniform vec4 hInkFrame;
uniform float hInkEmission;
struct HInkSurface {bool isInk;vec3 albedo;vec3 normal;vec3 irradianceNormal;};
HInkSurface hReadInk(vec2 uv,vec3 vertexNormal,vec3 materialNormal,vec3 paintTangent) {
  HInkSurface s;s.isInk=false;s.albedo=vec3(0.);s.normal=materialNormal;s.irradianceNormal=materialNormal;
  // Negative coordinates mark triangles not assigned to this web atlas. Native _pu storage does not use this sentinel.
  if(any(lessThan(uv,vec2(0.))))return s;
  vec3 c=texture2D(hInkTexture,uv).rgb;
  vec3 cv=texture2D(hInkTexture,vec2(uv.x,uv.y+hInkFrame.z*hInkStep.y)).rgb;
  vec3 cu=texture2D(hInkTexture,vec2(uv.x+hInkFrame.z*hInkStep.x,uv.y)).rgb;
  float maximum=max(c.b,max(c.r,c.g)),amount=clamp(maximum-.30000001192092896,0.,1.);
  vec3 weights=clamp(((c-vec3(maximum))+vec3(9.99999975e-5))*100000000.,0.,1.);
  s.isInk=min(amount*1000.,1.)>.5;
  if(!s.isInk)return s;
  vec3 bright=weights.b*hInkBright[2]+(weights.r*hInkBright[0]+weights.g*hInkBright[1]);
  vec3 ink=weights.b*hInkColors[2]+(weights.r*hInkColors[0]+weights.g*hInkColors[1]);
  float rim=clamp(amount*.875,0.,1.);
  s.albedo=(ink-bright*.625)*rim+bright*.625;
  vec3 nv=normalize(vertexNormal);
  vec3 du=c-cu,dv=c-cv;
  float gu=(du.b*weights.b+(du.r*weights.r+du.g*weights.g))*1.7999999523162842;
  float gv=(dv.b*weights.b+(dv.r*weights.r+dv.g*weights.g))*1.7999999523162842;
  vec3 ni=normalize(nv+(paintTangent*gu+cross(nv,paintTangent)*gv));
  float thickness=clamp(nv.y,0.,1.)*(hInkFrame.x-hInkFrame.y)+hInkFrame.y;
  // Maxwell leaves this mixture and the SH direction unnormalized.
  s.normal=(ni-materialNormal)*thickness+materialNormal;
  s.irradianceNormal=vec3(s.normal.x*.5,(s.normal.y-1.)*.5+1.,s.normal.z*.5);
  return s;
}
`;

const NORMAL_ANCHOR="#include <normal_fragment_maps>";
/** p1714 ink branch: cPrefilEnvMapArray layer 12, explicit lod 0 (env_prefilter inkLayer). */
const INK_ENV_ANCHOR="hNativeEnvSpecular(hN,hV,hF0,hR)";
/** Apply after applyHoian + applyForward. Missing native forward anchors are an error, not a silently unlit paint fallback. */
export function applyInkSurface(mat:THREE.MeshStandardMaterial,bindings:InkSurfaceBindings):InkSurfaceBinding {
  if(!mat.userData.nativeForward)throw new Error("Ink surface requires applyForward first");
  if(mat.userData.inkSurface)throw new Error("Ink surface already attached to material");
  if(bindings.ink.length!==3||bindings.inkBright.length!==3)throw new Error("Ink surface requires all three native team color slots");
  if(!Number.isFinite(bindings.emission)||bindings.textureStep.some(x=>!Number.isFinite(x)))throw new Error("Ink surface requires finite env emission and atlas intervals");
  const attrs=bindings.attributeNames??{uv:"paintUv",selector:"paintSwitch",tangent:"paintTangent"};
  for(const name of Object.values(attrs))if(!/^[a-zA-Z_][a-zA-Z_0-9]*$/.test(name))throw new Error("Invalid ink attribute name");
  const uniforms={hInkTexture:{value:bindings.texture},hInkColors:{value:bindings.ink.map(c=>new THREE.Vector3(...c))},
    hInkBright:{value:bindings.inkBright.map(c=>new THREE.Vector3(...c))},hInkStep:{value:new THREE.Vector2(...bindings.textureStep)},
    hInkFrame:{value:new THREE.Vector4(...inkSurfaceFrame(0))},hInkEmission:{value:Math.fround(bindings.emission)}};
  const prior=mat.onBeforeCompile,priorKey=mat.customProgramCacheKey;
  const hook:THREE.MeshStandardMaterial["onBeforeCompile"]=(sh,renderer)=>{
    prior.call(mat,sh,renderer);
    for(const anchor of [NORMAL_ANCHOR,FORWARD_SURFACE_GLSL,FORWARD_SURFACE_END,"hEvaluateSH(hIrradianceNormal)",PREFILTER_LOOKUP_GLSL,INK_ENV_ANCHOR])
      if(!sh.fragmentShader.includes(anchor))throw new Error("Ink surface native forward anchor missing: "+anchor);
    if(!sh.vertexShader.includes("#include <defaultnormal_vertex>")||!sh.vertexShader.includes("#include <uv_vertex>"))throw new Error("Ink surface vertex anchor missing");
    Object.assign(sh.uniforms,uniforms);
    sh.vertexShader=`attribute vec4 ${attrs.uv};\nattribute float ${attrs.selector};\nattribute vec3 ${attrs.tangent};\nvarying vec2 hInkUV;\nvarying vec3 hInkVertexNormal,hInkTangent;\n`+sh.vertexShader
      .replace("#include <uv_vertex>","#include <uv_vertex>\nhInkUV="+attrs.selector+"<0.?"+attrs.uv+".zw:"+attrs.uv+".xy;\n"+
        (bindings.uvAlreadyFlipped?"":"hInkUV.y=1.-hInkUV.y;\n"))
      .replace("#include <defaultnormal_vertex>","#include <defaultnormal_vertex>\nhInkVertexNormal=normalize(mat3(modelMatrix)*objectNormal);\nhInkTangent=mat3(modelMatrix)*"+attrs.tangent+";\n");
    sh.fragmentShader="varying vec2 hInkUV;\nvarying vec3 hInkVertexNormal,hInkTangent;\n"+INK_SURFACE_GLSL+sh.fragmentShader
      .replace(NORMAL_ANCHOR,NORMAL_ANCHOR+String.raw`
      HInkSurface hInkSurface=hReadInk(hInkUV,hInkVertexNormal,inverseTransformDirection(normal,viewMatrix),hInkTangent);
      if(hInkSurface.isInk){diffuseColor.rgb=hInkSurface.albedo;diffuseColor.a=1.;roughnessFactor=.05000000074505806;metalnessFactor=0.;
        totalEmissiveRadiance=hInkSurface.albedo*hInkEmission;
        // The environment sampler is still the existing three PMREM/BRDF adapter.
        normal=mat3(viewMatrix)*hInkSurface.normal;}
      `)
      .replace(FORWARD_SURFACE_END,String.raw`
      if(hInkSurface.isInk){hN=hInkSurface.normal;hR=.05000000074505806;hDiffuse=hInkSurface.albedo;
        hF0=vec3(.014999999664723873);hIrradianceNormal=hInkSurface.irradianceNormal;}
      `+FORWARD_SURFACE_END)
      .replace(PREFILTER_LOOKUP_GLSL,PREFILTER_LOOKUP_GLSL+PREFILTER_INK_GLSL)
      .replace(INK_ENV_ANCHOR,"(hInkSurface.isInk?hNativeInkSpecular(hN,hV,hF0,hR):hNativeEnvSpecular(hN,hV,hF0,hR))");
  };
  const key=()=>priorKey.call(mat)+":nativeInk1714:layer12:atlas:"+bindings.texture.uuid+":"+JSON.stringify(attrs)+":"+!!bindings.uvAlreadyFlipped;
  mat.onBeforeCompile=hook;mat.customProgramCacheKey=key;mat.userData.inkSurface=true;
  mat.userData.inkSurfacePolicy="Hoian 1714/946 known consumer; reflection = native layer 12 (illuminate r .05); web atlas input remains";
  mat.needsUpdate=true;
  return {uniforms,updateFrame(frame){uniforms.hInkFrame.value.fromArray(inkSurfaceFrame(frame));},setTexture(texture){uniforms.hInkTexture.value=texture;},
    dispose(){if(mat.onBeforeCompile===hook)mat.onBeforeCompile=prior;if(mat.customProgramCacheKey===key)mat.customProgramCacheKey=priorKey;
      delete mat.userData.inkSurface;delete mat.userData.inkSurfacePolicy;mat.needsUpdate=true;}};
}
export { INK_DAY_PARAMS };
