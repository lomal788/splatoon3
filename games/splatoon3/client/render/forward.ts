// Native known stage forward equations. Web PCF shadow and PMREM/BRDF are explicit boundaries.
import * as THREE from "three";
import type { FresMaterial } from "./hoian.ts";
import type { BakeMaterial } from "./bake.ts";
import type { LightingState } from "./lighting.ts";
import { SHADOW_GLSL } from "./shadows.ts";
const WORLD_VERTEX=String.raw`
  #include <worldpos_vertex>
  vec4 hWorld=vec4(transformed,1.);
  #ifdef USE_BATCHING
  hWorld=batchingMatrix*hWorld;
  #endif
  #ifdef USE_INSTANCING
  hWorld=instanceMatrix*hWorld;
  #endif
  hWorldPosition=(modelMatrix*hWorld).xyz;
`;
const DECL=String.raw`
varying vec3 hWorldPosition;
uniform vec3 hLightColor,hLightDirection;
uniform vec4 hSH[7],hBakeShadow,hDepthFog,hHeightFog;
uniform vec3 hDepthRange,hGridOrigin,hInvCell;
uniform vec2 hHeightRange;
uniform float hAOMain;
uniform highp usampler2D hGrid;
uniform vec4 hDynColor[30],hDynAtt[30],hDynPos[30],hDynDir[30];
vec3 hEvaluateSH(vec3 n) {
  vec4 v=vec4(n,1.);vec4 q=vec4(n.x*n.y,n.y*n.z,n.z*n.z,n.x*n.z);
  return max(vec3(0.),vec3(dot(hSH[0],v),dot(hSH[1],v),dot(hSH[2],v))+
    vec3(dot(hSH[3],q),dot(hSH[4],q),dot(hSH[5],q))+(n.x*n.x-n.y*n.y)*hSH[6].rgb);
}
vec3 hSpecular(vec3 f0,float r,vec3 n,vec3 v,vec3 l) {
  vec3 h=normalize(v+l);float nh=max(dot(n,h),1.e-8),nl=max(dot(n,l),1.e-8),nv=max(dot(n,v),1.e-8),vh=max(dot(v,h),1.e-8);
  float r2=r*r,r4=r2*r2,k=(r*.5+.5)*(r*.5+.5)*.5;
  float d=max(nh*nh*(r4-1.)+1.,1.e-8);
  float a=(r2/d)*(r2/d)/((k+(1.-k)*nl)*(k+(1.-k)*nv));
  float f=exp2(vh*(vh*-5.55473-6.98316002));
  return (f0+(1.-f0)*f)*a*.0795774683;
}
vec3 hDynamic(vec3 p,vec3 n,vec3 v,vec3 diffuse,vec3 f0,float r) {
  ivec2 cell=clamp(ivec2((p.xz-hGridOrigin.xz)*hInvCell.xz),ivec2(0),ivec2(19));
  uint packed=texelFetch(hGrid,cell,0).r;vec3 color=vec3(0.);
  for(int k=0;k<4;k++) {
    uint i=(packed>>uint(k*8))&255u;if(i>=30u)break;
    vec3 delta=hDynPos[i].xyz-p;float distance=length(delta);vec3 l=delta/max(distance,1.e-8);
    vec4 att=hDynAtt[i];float a=pow(clamp(1.-att.x*distance,0.,1.),att.y)*clamp(dot(n,l),0.,1.);
    if(hDynPos[i].w!=0.)a*=pow(clamp((-dot(l,hDynDir[i].xyz)-att.z)/(1.-att.z),0.,1.),att.w);
    color+=hDynColor[i].rgb*a*(diffuse*.318309873+hSpecular(f0,r,n,v,l));
  }
  return color;
}
`;
/** Stable surface hook shared by the stage and native ink material branch. */
export const FORWARD_SURFACE_GLSL=String.raw`
      vec3 hN=inverseTransformDirection(normal,viewMatrix),hV=normalize(cameraPosition-hWorldPosition),hL=normalize(-hLightDirection);
      float hR=max(roughnessFactor,.0001);
      vec3 hDiffuse=diffuseColor.rgb*(1.-metalnessFactor),hF0=mix(vec3(.04),diffuseColor.rgb,metalnessFactor);
      vec3 hIrradianceNormal=hN;
`;
export const FORWARD_SURFACE_END="// H_NATIVE_SURFACE_END";
export const FORWARD_LIGHTING_BEGIN="// H_NATIVE_LIGHTING_BEGIN";
export const FORWARD_LIGHTING_END="// H_NATIVE_LIGHTING_END";
export function applyForward(mat:THREE.MeshStandardMaterial,f:FresMaterial,lighting:LightingState,bake:BakeMaterial|null):void {
  if(f.shader?.archive!=="Hoian_UBER")return;
  const opt=f.shader.options??{};
  const enabled=opt.enable_shading!=="False" && opt.enable_shading!=="0";
  mat.userData.nativeForward=true;
  const prev=mat.onBeforeCompile,previousKey=mat.customProgramCacheKey.bind(mat);
  mat.onBeforeCompile=(sh,renderer)=>{
    prev.call(mat,sh,renderer);
    Object.assign(sh.uniforms,lighting.uniforms);
    Object.assign(sh.uniforms,lighting.shadows?.uniforms);
    sh.vertexShader="varying vec3 hWorldPosition;\n"+sh.vertexShader.replace("#include <worldpos_vertex>",WORLD_VERTEX);
    sh.fragmentShader=DECL+SHADOW_GLSL+"\n"+sh.fragmentShader;
    let sample="vec3 hBakeLight=vec3(0.);float hOccAO=0.,hOccBake=0.;\n";
    if(bake) {
      const defines=mat as unknown as {defines:Record<string,string>};
      defines.defines={...(defines.defines??{}),USE_UV1:""};
      sh.vertexShader="varying vec4 hBakeUV;\nuniform vec4 hBakeST0,hBakeST1;\n"+sh.vertexShader.replace("#include <uv_vertex>",
        "#include <uv_vertex>\nhBakeUV=vec4(uv1*hBakeST0.xy+hBakeST0.zw,uv1*hBakeST1.xy+hBakeST1.zw);");
      sh.fragmentShader="varying vec4 hBakeUV;\nuniform sampler2D hBakeAO,hBakeLightTex;\n"+sh.fragmentShader;
      sh.uniforms.hBakeST0={value:bake.ao?.st??new THREE.Vector4(1,1,0,0)};
      sh.uniforms.hBakeST1={value:bake.light?.st??new THREE.Vector4(1,1,0,0)};
      sh.uniforms.hBakeAO={value:bake.ao?.texture??null};sh.uniforms.hBakeLightTex={value:bake.light?.texture??null};
      if(bake.ao)sample+="vec2 hBK=texture2D(hBakeAO,hBakeUV.xy).xy;\nhOccAO=clamp(hBakeShadow.z*(1.-hBK.x)+hBakeShadow.w,0.,1.);hOccBake=clamp(hBakeShadow.x*(1.-hBK.y)+hBakeShadow.y,0.,1.);\n";
      if(bake.light)sample+="vec4 hBL=texture2D(hBakeLightTex,hBakeUV.zw);hBakeLight=hBL.rgb*hBL.a*32.;\n";
    }
    const accum=enabled?FORWARD_SURFACE_GLSL+FORWARD_SURFACE_END+String.raw`
      float hNoL=clamp(dot(hN,hL),0.,1.);
      `+sample+String.raw`
      // Native additive occlusion; cascade fit/filter are explicitly web policies.
      float hViewDepth=-(viewMatrix*vec4(hWorldPosition,1.)).z;
      float hShadow=clamp(1.-(hOccAO*hAOMain+hOccBake+(1.-hDynamicShadow(hWorldPosition,hViewDepth))+hProjectionOcclusion(hWorldPosition)),0.,1.);
      `+FORWARD_LIGHTING_BEGIN+String.raw`
      reflectedLight.indirectDiffuse=(hDiffuse*(1.-hF0)*(hBakeLight+hEvaluateSH(hIrradianceNormal))+
        hDynamic(hWorldPosition,hN,hV,hDiffuse,hF0,hR))*(1.-hOccAO);
      reflectedLight.directDiffuse=hDiffuse*.318309873*(hNoL*hLightColor+hBakeLight)*hShadow;
      reflectedLight.directSpecular=hSpecular(hF0,hR,hN,hV,hL)*(hNoL*hLightColor+hBakeLight)*hShadow;
      #ifdef USE_ENVMAP
      reflectedLight.indirectSpecular=getIBLRadiance(normalize(vViewPosition),normal,hR)*
        EnvironmentBRDF(normal,normalize(vViewPosition),hF0,1.,hR)*(1.-hOccAO);
      #endif
    `+FORWARD_LIGHTING_END: "reflectedLight.directDiffuse=diffuseColor.rgb;\n";
    sh.fragmentShader=sh.fragmentShader.replace("#include <lights_fragment_begin>",accum)
      .replace("#include <lights_fragment_maps>","").replace("#include <lights_fragment_end>","").replace("#include <aomap_fragment>","");
    if(enabled)sh.fragmentShader=sh.fragmentShader.replace("#include <fog_fragment>",String.raw`
      float hHeight=clamp((hWorldPosition.y-hHeightRange.x)/(hHeightRange.y-hHeightRange.x),0.,1.)*hHeightFog.a;
      vec3 hFogColor=mix(gl_FragColor.rgb,hHeightFog.rgb,hHeight);
      float hD=length(hWorldPosition-cameraPosition);
      float hS=clamp((hD-hDepthRange.x)/(hDepthRange.y-hDepthRange.x),0.,1.);
      float hDepth=clamp(1.-exp(-hS*hDepthRange.z),0.,1.)*hDepthFog.a;
      gl_FragColor.rgb=mix(hFogColor,hDepthFog.rgb,hDepth);
    `);
  };
  if(bake) (mat as unknown as {defines:Record<string,string>}).defines={...((mat as unknown as {defines:Record<string,string>}).defines??{}),USE_UV1:""};
  mat.customProgramCacheKey=()=>previousKey()+":nativeForward:commonShadow:"+enabled+":"+!!bake?.ao+":"+!!bake?.light;
  mat.needsUpdate=true;
}

/** Web PBR receivers (paint overlays/placeholders) share the same depth supply.
 * Their native material shaders remain separate work; this does not promote them to Hoian.
 */
export function applyCommonShadowReceivers(scene:THREE.Scene,lighting:LightingState):void {
  if(!lighting.shadows)return;
  scene.traverseVisible(o=>{
    const mesh=o as THREE.Mesh;if(!mesh.isMesh||!mesh.receiveShadow)return;
    for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]){
      const mat=material as THREE.MeshStandardMaterial;
      if(!mat.isMeshStandardMaterial||mat.userData.nativeForward||mat.userData.commonShadowReceiver)continue;
      const prev=mat.onBeforeCompile,key=mat.customProgramCacheKey.bind(mat);
      mat.onBeforeCompile=(sh,renderer)=>{
        prev.call(mat,sh,renderer);Object.assign(sh.uniforms,lighting.shadows!.uniforms);
        sh.vertexShader="varying vec3 hWorldPosition;\n"+sh.vertexShader.replace("#include <worldpos_vertex>",WORLD_VERTEX);
        sh.fragmentShader="varying vec3 hWorldPosition;\n"+SHADOW_GLSL+sh.fragmentShader;
        const chunk=THREE.ShaderChunk.lights_fragment_begin.replace(
          "getDirectionalLightInfo( directionalLight, directLight );",
          "getDirectionalLightInfo( directionalLight, directLight );\nif(UNROLLED_LOOP_INDEX==0&&receiveShadow)directLight.color*=clamp(hDynamicShadow(hWorldPosition,-(viewMatrix*vec4(hWorldPosition,1.)).z)-hProjectionOcclusion(hWorldPosition),0.,1.);"
        );
        sh.fragmentShader=sh.fragmentShader.replace("#include <lights_fragment_begin>",chunk);
      };
      mat.customProgramCacheKey=()=>key()+":commonShadowReceiver";
      mat.userData.commonShadowReceiver=true;mat.needsUpdate=true;
    }
  });
}
