// Known native shadow settings + an explicitly separate WebGL depth adapter.
// graphics/stage_rendering §3.0/5.4 and projected_shadow_runtime §3..6.
import * as THREE from "three";

/** gsys Common values [data/reading]. Its live Lobby selection remains unconfirmed. */
export const NATIVE_SHADOW_SETTINGS = Object.freeze({
  cascades: 2, width: 1024, height: 1024,
  nearValues: Object.freeze([1.5, 20, 250, 16]), far: 60,
  polygonOffset: .3, polygonScale: 5, pcfOffset: .5,
});

/** 3762450 ctor [execution], not evidence of Lobby runtime overrides. */
export const NATIVE_SHADOW_PREPASS_DEFAULTS = Object.freeze({
  filterShaderType: 0, filterSampleNum: 0, pcfWidth: 5,
  useFarFade: false, dynamicFarFadeStart: 100, dynamicFarFadeEnd: 1000,
  staticFarFadeStart: 100, staticFarFadeEnd: 1000, farDepthTestDist: 1000,
});

/** Default/default.baglshpp [data]: resource overrides, distinct from constructor values. */
export const NATIVE_SHADOW_PREPASS_DEFAULT_ENV = Object.freeze({
  filterShaderType: 0, filterSampleNum: 0, pcfWidth: 5,
  useFarFade: true, dynamicFarFadeStart: 40, dynamicFarFadeEnd: 60,
  staticFarFadeStart: 40, staticFarFadeEnd: 60, farDepthTestDist: 60,
});

export interface ShadowPrePassSettings {
  /** Recovered SHADER_TYPE 0/1/2/3 = 1/4/9/16 comparison samples. */
  filterShaderType: number; filterSampleNum: number; pcfWidth: number;
  useFarFade: boolean; dynamicFarFadeStart: number; dynamicFarFadeEnd: number;
  staticFarFadeStart?: number; staticFarFadeEnd?: number;
  /** is_farDepthTestDist (ShadowPrePass +0x7C8) -> BlitzUBO0[36].z via 7101110750 (env+0x1338 = ShadowPrePass, unconditional copy). */
  farDepthTestDist?: number;
}

/** 3764C28: filter type 1 enables sampleNum<3 -> SHADER_TYPE=sampleNum+1. */
export function nativeShadowShaderType(settings: Pick<ShadowPrePassSettings,"filterShaderType"|"filterSampleNum">): number {
  return settings.filterShaderType===1&&settings.filterSampleNum>=0&&settings.filterSampleNum<3?settings.filterSampleNum+1:0;
}

/** 3764908: disabled explicit far fade still uses camera.far start and mul=1. */
export function nativeShadowFarFade(settings: Pick<ShadowPrePassSettings,"useFarFade"|"dynamicFarFadeStart"|"dynamicFarFadeEnd">,cameraFar: number): [number,number] {
  const f=Math.fround;
  return settings.useFarFade?[f(settings.dynamicFarFadeStart),f(1/f(f(settings.dynamicFarFadeEnd)-f(settings.dynamicFarFadeStart)))]:[f(cameraFar),1];
}

/** 3764908 frame +1424/+1428 (Common cStaticShadowFarFadeStart/MulParam): same branch as the dynamic pair. */
export function nativeStaticShadowFarFade(settings: Pick<ShadowPrePassSettings,"useFarFade"|"staticFarFadeStart"|"staticFarFadeEnd">,cameraFar: number): [number,number] {
  return nativeShadowFarFade({useFarFade:settings.useFarFade,dynamicFarFadeStart:settings.staticFarFadeStart??100,dynamicFarFadeEnd:settings.staticFarFadeEnd??1000},cameraFar);
}

/** gsys Common static_sdw_* [data] and static shadow object ctor 0x710375418c [reading]. */
export const NATIVE_STATIC_SHADOW_SETTINGS = Object.freeze({
  width: 2048, mipLevels: 1, depthFormat: "Depth_32", mapFormat: "R32_G32_float",
  /** obj+0xb98 = 3 (ctor 0x710375418c); 7103755830 runs two vsm passes per iteration. */
  blurIterations: 3,
});

/** agl_technique_shdw vsm PASS1/PASS2: 7 linear taps along +-k*cInvTexSize, weights x 0.000245700008. */
export const NATIVE_VSM_BLUR = Object.freeze({
  offsets: Object.freeze([1.38460004, 3.23077011, 5.07690001]),
  weights: Object.freeze([924, 1287, 286, 13]), scale: .000245700008,
});

type V3 = readonly [number,number,number]|readonly number[];

/** 710374F950: AABB of static caster shape spheres (center +- radius), null when empty. */
export function nativeStaticShadowBounds(spheres: readonly (readonly number[])[]): {min:[number,number,number];max:[number,number,number]}|null {
  const F=Math.fround,M=3.4028234663852886e38,min:[number,number,number]=[M,M,M],max:[number,number,number]=[-M,-M,-M];
  for(const s of spheres){
    const r=F(s[3]);
    for(let i=0;i<3;i++){const lo=F(F(s[i])-r),hi=F(r+F(s[i]));if(lo<min[i])min[i]=lo;if(max[i]<hi)max[i]=hi;}
  }
  return min[0]<=max[0]&&min[1]<=max[1]&&min[2]<=max[2]?{min,max}:null;
}

export interface StaticShadowFit {
  /** sead LookAtCamera 3x4 row-major (0xa20). */
  view: number[];
  ortho: {near:number;far:number;top:number;bottom:number;left:number;right:number};
  /** OrthoProjection 4x4 row-major (0xab4). */
  proj: number[];
  /** Native texture matrix rows (0xb58..0xb94), NVN v = -0.5*y + 0.5. */
  tex: number[];
}

/** 7103754FE8 with sead LookAtCamera 710358857C and OrthoProjection 7103589F84, f32/f64 operation order kept. */
export function nativeStaticShadowFit(min: V3,max: V3,dir: V3): StaticShadowFit {
  const F=Math.fround,fma=(a:number,b:number,c:number)=>F(a*b+c);
  const c=[0,1,2].map(i=>F(F(F(max[i])+F(min[i]))*.5)),h=[0,1,2].map(i=>F(F(F(max[i])-F(min[i]))*.5));
  const at=[0,1,2].map(i=>F(c[i]+F(dir[i]))),up=[0,0,1];
  let z=[0,1,2].map(i=>F(c[i]-at[i]));
  let len=F(Math.sqrt(F(F(F(z[0]*z[0])+F(z[1]*z[1]))+F(z[2]*z[2]))));
  if(len>0){const inv=F(1/len);z=z.map(v=>F(inv*v));}
  let x=[F(F(z[2]*up[1])-F(z[1]*up[2])),F(F(z[0]*up[2])-F(z[2]*up[0])),F(F(z[1]*up[0])-F(z[0]*up[1]))];
  len=F(Math.sqrt(F(F(F(x[0]*x[0])+F(x[1]*x[1]))+F(x[2]*x[2]))));
  if(len>0){const inv=F(1/len);x=x.map(v=>F(v*inv));}
  const y=[F(F(z[1]*x[2])-F(z[2]*x[1])),F(F(z[2]*x[0])-F(z[0]*x[2])),F(F(z[0]*x[1])-F(z[1]*x[0]))];
  const tx=F((c[0]*x[0]+c[1]*x[1])+c[2]*x[2]),ty=F(c[2]*y[2]+(c[0]*y[0]+c[1]*y[1])),tz=F((c[0]*z[0]+c[1]*z[1])+c[2]*z[2]);
  const view=[x[0],x[1],x[2],-tx, y[0],y[1],y[2],-ty, z[0],z[1],z[2],-tz];
  const extent=(r:number)=>{
    const a=F(h[0]*view[r*4]),b=F(h[1]*view[r*4+1]),d=F(h[2]*view[r*4+2]),s=F(a+b),m=F(a-b);
    let e=-3.4028234663852886e38;for(const v of [F(s+d),F(m+d),F(s-d),F(m-d)]){const w=v<0?-v:v;if(w>e)e=w;}return e;
  };
  const e0=extent(0),e1=extent(1),e2=extent(2);
  const ortho={near:-e2,far:e2,top:e1,bottom:-e1,left:-e0,right:e0};
  const sx=F(F(ortho.right-ortho.left)*.5),sy=F(F(ortho.top-ortho.bottom)*.5),iz=F(1/F(ortho.far-ortho.near));
  const proj=[F(1/sx),0,0,F(F(F(ortho.left+ortho.right)*-.5)/sx), 0,F(1/sy),0,F(F(F(ortho.top+ortho.bottom)*-.5)/sy),
    0,0,F(iz*-2),F(iz*F(-F(ortho.near+ortho.far))), 0,0,0,1];
  const V=[view.slice(0,4),view.slice(4,8),view.slice(8,12)];
  const pv=[0,1,2,3].map(r=>{
    const p=proj.slice(r*4,r*4+4);
    return [0,1,2,3].map(j=>F(fma(V[2][j],p[2],fma(V[1][j],p[1],F(V[0][j]*p[0]))) + (j===3?p[3]:0)));
  });
  const tex:number[]=[];
  for(let j=0;j<4;j++){
    let r0=F(pv[0][j]*.5);r0=fma(0,pv[1][j],r0);r0=fma(0,pv[2][j],r0);tex[j]=fma(.5,pv[3][j],r0);
    let zero=F(pv[0][j]*0);let r1=fma(-.5,pv[1][j],zero);zero=fma(0,pv[1][j],zero);r1=fma(0,pv[2][j],r1);tex[4+j]=fma(.5,pv[3][j],r1);
    const r2=fma(.5,pv[2][j],zero);zero=fma(0,pv[2][j],zero);tex[8+j]=fma(.5,pv[3][j],r2);tex[12+j]=F(pv[3][j]+zero);
  }
  return {view,ortho,proj,tex};
}

/** WebGL samples render-target rows bottom-up: v_gl = 1 - v_nvn, i.e. row1 = row3 - row1 of the native texture matrix. */
export function webStaticShadowMatrix(fit: StaticShadowFit): THREE.Matrix4 {
  const t=fit.tex;
  return new THREE.Matrix4().set(t[0],t[1],t[2],t[3], t[12]-t[4],t[13]-t[5],t[14]-t[6],t[15]-t[7], t[8],t[9],t[10],t[11], t[12],t[13],t[14],t[15]);
}

/** prepass v216 SPP.w (Hoian SPP.y): Chebyshev VSM + static far fade, no variance floor and no clamp of the sum. */
export function nativeStaticShadowVisibility(moments: readonly [number,number]|readonly number[],refZ: number,positiveViewDepth: number,fade: readonly [number,number]|readonly number[]): number {
  // v216 FFMA: variance=fma(m1,-m1,m2), denominator=fma(t,t,variance) (single rounding each).
  const F=Math.fround,m1=F(moments[0]),d=Math.min(F(refZ),1),variance=F(m1*-m1+F(moments[1]));
  // Maxwell FMNMX returns the non-NaN operand (0/0 at d==m1 with zero variance).
  const minNum=(a:number,b:number)=>Number.isNaN(a)?b:Number.isNaN(b)?a:Math.min(a,b),maxNum=(a:number,b:number)=>Number.isNaN(a)?b:Number.isNaN(b)?a:Math.max(a,b);
  const t=F(d-m1),p=maxNum(d<=m1?1:0,minNum(F(variance*F(1/F(t*t+variance))),1));
  return F(Math.min(Math.max(F(F(positiveViewDepth-F(fade[0]))*F(fade[1])),0),1)+p);
}

/** Remaining Web choices; kernel/strict split/fade equations are recovered in r6. */
export const WEB_SHADOW_POLICY = Object.freeze({
  splits: Object.freeze([1.5, 20, 60]),
  fitting: "view-slice XY; caster-inclusive light Z; texel-expanded bounds",
  filtering: "native 1/4/9/16 comparison grid; nearest manual comparison adapter; NVN sampler filter unresolved",
  prePassSettings: "Default/default.baglshpp resource overrides; Lobby runtime resource-selection chain unresolved",
  outsideFar: "visibility=1 beyond final cascade; native out-of-array/border behavior unresolved",
  polygonMapping: "WebGL polygonOffset(factor=5, units=0.3); NVN equivalence unverified",
  receivingBias: 0,
  nearFarPadding: .01, // only avoids a degenerate WebGL camera slab
});

export interface ProjectedShadowFields {
  density: number; rotate: number; scale: [number, number]; trans: [number, number];
  scrollAnim: [number, number]; rotateAnim: number;
}

/** Native 2B66C54 FSUB -> FMUL -> FADD; neither input t nor result is clamped. */
export function blendProjectedShadow(a: ProjectedShadowFields, b: ProjectedShadowFields, t: number): ProjectedShadowFields {
  const f = Math.fround, mix = (x: number, y: number) => f(f(y) + f(f(f(x) - f(y)) * f(t)));
  return {
    density: mix(a.density, b.density), rotate: mix(a.rotate, b.rotate),
    scale: [mix(a.scale[0], b.scale[0]), mix(a.scale[1], b.scale[1])],
    trans: [mix(a.trans[0], b.trans[0]), mix(a.trans[1], b.trans[1])],
    scrollAnim: [mix(a.scrollAnim[0], b.scrollAnim[0]), mix(a.scrollAnim[1], b.scrollAnim[1])],
    rotateAnim: mix(a.rotateAnim, b.rotateAnim),
  };
}

/** Native 37AB8E0 separately clamps factor+4E8 and Density+5AC then f32 multiplies. */
export function projectedShadowDensity(factor: number, density: number): number {
  const clamp = (v: number) => { const x=Math.fround(v);return x>=0?Math.min(1,x):0; };
  return Math.fround(clamp(factor) * clamp(density));
}

export interface ProjectedShadowFrame {
  count: number; enabled: boolean; density: number; factor: number;
  /** The actual native producer's three vec4 rows, not reconstructed from Scale/Rotate. */
  matrixRows: readonly (readonly number[])[];
  texture: THREE.Texture;
}

export const SHADOW_GLSL = /* glsl */`
uniform sampler2D hShadowMap0,hShadowMap1,hProjShadowMap;
uniform mat4 hShadowMatrix0,hShadowMatrix1;
uniform vec3 hShadowSplits;
uniform vec2 hShadowTexel;
uniform vec2 hShadowFarFade;
uniform float hShadowKernel,hShadowBias;
uniform float hShadowAvailable,hProjShadowAvailable,hProjShadowDensity;
uniform vec4 hProjShadowRows[3];
float hShadowCompare(sampler2D tex,vec2 uv,float depth) {
  return step(depth,texture2D(tex,uv).r);
}
float hCascadeVisibility(sampler2D tex,mat4 matrix,vec3 worldPos) {
  vec4 q=matrix*vec4(worldPos,1.); vec3 s=q.xyz/q.w;
  if(any(lessThan(s.xy,vec2(0.)))||any(greaterThan(s.xy,vec2(1.)))) return 1.;
  float ref=clamp(s.z,0.,1.);
  if(hShadowKernel<.5)return hShadowCompare(tex,s.xy,ref);
  // Native offset includes projected ref depth and pcfWidth. It is not a fixed half texel.
  vec2 offset=hShadowTexel*(hShadowBias*ref);
  if(hShadowKernel<1.5)return .25*(hShadowCompare(tex,s.xy+offset*vec2(.5,.5),ref)
    +hShadowCompare(tex,s.xy+offset*vec2(-.5,.5),ref)
    +hShadowCompare(tex,s.xy+offset*vec2(.5,-.5),ref)
    +hShadowCompare(tex,s.xy+offset*vec2(-.5,-.5),ref));
  float sum=0.;
  if(hShadowKernel<2.5){
    for(int y=0;y<3;y++)for(int x=0;x<3;x++)sum+=hShadowCompare(tex,s.xy+offset*vec2(float(x)-1.,float(y)-1.),ref);
    return sum*.11111111;
  }
  for(int y=0;y<4;y++)for(int x=0;x<4;x++)sum+=hShadowCompare(tex,s.xy+offset*vec2(float(x)-1.5,float(y)-1.5),ref);
  return sum*.0625;
}
uniform sampler2D hStaticShadowMap;
uniform mat4 hStaticShadowMatrix;
uniform vec2 hStaticShadowFarFade;
uniform float hStaticShadowAvailable;
float hStaticShadowVisibility(vec3 worldPos,float positiveViewDepth) {
  if(hStaticShadowAvailable<.5)return 1.;
  // prepass v216: moments at q.xy/q.w, ref min(q.z,1), Chebyshev without variance floor, + static far fade.
  vec4 q=hStaticShadowMatrix*vec4(worldPos,1.);
  vec2 m=texture2D(hStaticShadowMap,q.xy*(1./q.w)).xy;
  float d=min(q.z,1.),v=m.y-m.x*m.x,t=d-m.x;
  float p=d<=m.x?1.:max(0.,min(v*(1./(t*t+v)),1.));
  return clamp((positiveViewDepth-hStaticShadowFarFade.x)*hStaticShadowFarFade.y,0.,1.)+p;
}
vec2 hShadowPrePass(vec3 worldPos,float positiveViewDepth) {
  // WEB_SHADOW_POLICY retains an explicit outside-final-cascade adapter gate.
  float dyn=1.;
  if(hShadowAvailable>.5&&positiveViewDepth<=hShadowSplits.z){
  // 3750740 uploads boundary[i+1]; native comparison is strict >, with no near cutoff.
  float v=positiveViewDepth<=hShadowSplits.y?hCascadeVisibility(hShadowMap0,hShadowMatrix0,worldPos):hCascadeVisibility(hShadowMap1,hShadowMatrix1,worldPos);
  // Prepass out.y (Hoian SPP.x via view swizzle 3,5,4,2) adds far fade; values above 1 are retained until the max consumer.
  dyn=v+clamp((positiveViewDepth-hShadowFarFade.x)*hShadowFarFade.y,0.,1.);
  }
  // Prepass out.w (Hoian SPP.y) = static depth shadow VSM.
  return vec2(dyn,hStaticShadowVisibility(worldPos,positiveViewDepth));
}
uniform float hShadowFarDepthTest;
float hDynamicShadow(vec3 worldPos,float positiveViewDepth) {
  vec2 spp=hShadowPrePass(worldPos,positiveViewDepth);
  // Hoian: max(1-SPP.x,1-SPP.y)*clamp(viewZ+BlitzUBO0[36].z,0,1), viewZ = Context[2].world = -depth.
  return 1.-max(1.-spp.x,1.-spp.y)*clamp(hShadowFarDepthTest-positiveViewDepth,0.,1.);
}
float hProjectionOcclusion(vec3 worldPos) {
  if(hProjShadowAvailable<.5||hProjShadowDensity==0.) return 0.;
  vec4 p=vec4(worldPos,1.);
  // Context[35..37] creates the projected coordinates; no fabricated producer.
  vec2 uv=vec2(dot(hProjShadowRows[0],p),dot(hProjShadowRows[1],p));
  return hProjShadowDensity*(1.-texture2D(hProjShadowMap,uv).r);
}
`;

const BIAS_MATRIX = new THREE.Matrix4().set(.5,0,0,.5, 0,.5,0,.5, 0,0,.5,.5, 0,0,0,1);
type DepthSource = THREE.Material & Partial<Pick<THREE.MeshStandardMaterial,
  "map"|"alphaMap"|"alphaToCoverage"|"displacementMap"|"displacementScale"|"displacementBias"|"wireframe"|"wireframeLinewidth">>;
interface Caster { source: THREE.Mesh; proxy: THREE.Mesh; }

/** World-space receiver slice corners, independent of the main camera's own near/far. */
export function shadowSliceCorners(camera: THREE.PerspectiveCamera, near: number, far: number): THREE.Vector3[] {
  camera.updateMatrixWorld(true);
  const points: THREE.Vector3[] = [];
  for (const z of [near, far]) for (const x of [-1,1]) for (const y of [-1,1]) {
    const p = new THREE.Vector3(x,y,1).applyMatrix4(camera.projectionMatrixInverse);
    p.multiplyScalar(z / -p.z).applyMatrix4(camera.matrixWorld); points.push(p);
  }
  return points;
}

function boxCorners(box: THREE.Box3): THREE.Vector3[] {
  if (box.isEmpty()) return [];
  const out: THREE.Vector3[] = [];
  for (const x of [box.min.x,box.max.x]) for (const y of [box.min.y,box.max.y]) for (const z of [box.min.z,box.max.z]) out.push(new THREE.Vector3(x,y,z));
  return out;
}

const FULLSCREEN_VERTEX=/* glsl */`varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}`;
/** agl_technique_shdw static_depth_shadow pixel: depth -> (d, d*d, 0, 1). */
const STATIC_COPY_FRAGMENT=/* glsl */`uniform sampler2D tDepth;varying vec2 vUv;
void main(){float d=texture2D(tDepth,vUv).x;gl_FragColor=vec4(d,d*d,0.,1.);}`;
/** agl_technique_shdw vsm PASS1/PASS2 vertex+pixel (identical binaries): 7 taps along +-k*cInvTexSize. */
const VSM_BLUR_FRAGMENT=/* glsl */`uniform sampler2D tSrc;uniform vec2 cInvTexSize;varying vec2 vUv;
void main(){
  vec4 t0=texture2D(tSrc,vUv-3.23077011*cInvTexSize),t1=texture2D(tSrc,vUv-5.07690001*cInvTexSize),t2=texture2D(tSrc,vUv-1.38460004*cInvTexSize);
  vec4 t3=texture2D(tSrc,vUv),t4=texture2D(tSrc,vUv+1.38460004*cInvTexSize),t5=texture2D(tSrc,vUv+3.23077011*cInvTexSize),t6=texture2D(tSrc,vUv+5.07690001*cInvTexSize);
  gl_FragColor=(t6*13.+t5*286.+t4*1287.+t3*924.+t2*1287.+t1*13.+t0*286.)*.000245700008;
}`;

/** Mesh userData contract (map.ts): staticDepthShadow, staticDepthShadowOnly, staticDepthShadowSpheres (world [x,y,z,r][]). */
export interface StaticShadowCasterData { staticDepthShadow?: boolean; staticDepthShadowOnly?: boolean; staticDepthShadowSpheres?: number[][]; }

export interface DepthShadowTable { models: Record<string, Record<string, Record<string, number>>>; }

/** renderInfo gsys_static_depth_shadow(_only)/gsys_dynamic_depth_shadow per glb model+material (data/depth_shadow.json).
 * static_only meshes are drawn only into the static depth pass; dynamic ones join the cascade casters. */
export function applyNativeDepthShadowFlags(root: THREE.Object3D,table: DepthShadowTable): {static:number;staticOnly:number;dynamic:number} {
  const count={static:0,staticOnly:0,dynamic:0};
  const modelOf=(o: THREE.Object3D|null): string|undefined=>!o?undefined:(o.userData.originalModelName as string|undefined)??modelOf(o.parent);
  root.traverse(o=>{
    const mesh=o as THREE.Mesh;if(!mesh.isMesh)return;
    const material=(mesh.userData.material as string|undefined)??(Array.isArray(mesh.material)?undefined:mesh.material.name);
    const model=modelOf(mesh),flags=model&&material?table.models[model]?.[material]:undefined;if(!flags)return;
    const u=mesh.userData as StaticShadowCasterData;
    // [추정] static_only shapes (Lby Gobo1 bake box) are kept out of the runtime static map: graphics_r11_diff_그림자.md §7.
    if(flags.gsys_static_depth_shadow_only===1){u.staticDepthShadowOnly=true;mesh.visible=false;count.staticOnly++;}
    else if(flags.gsys_static_depth_shadow===1){u.staticDepthShadow=true;count.static++;}
    if(flags.gsys_dynamic_depth_shadow===1){mesh.castShadow=true;count.dynamic++;}
  });
  return count;
}

/** Static depth shadow: 710374F950 AABB -> 7103754FE8 fit -> 2048 depth -> static_depth_shadow copy -> 7103755830 vsm blur x3. */
export class NativeStaticShadow {
  readonly uniforms: Record<string, THREE.IUniform>;
  readonly stats = { captures: 0, casters: 0, blurPasses: 0, filter: "none" };
  fit: StaticShadowFit|null = null;
  private depthTarget: THREE.WebGLRenderTarget|null = null;
  private maps: [THREE.WebGLRenderTarget,THREE.WebGLRenderTarget]|null = null;
  private readonly scene = new THREE.Scene();
  private readonly quadScene = new THREE.Scene();
  private readonly camera = new THREE.OrthographicCamera();
  private readonly quadCamera = new THREE.OrthographicCamera(-1,1,1,-1,0,1);
  private readonly copy = new THREE.ShaderMaterial({vertexShader:FULLSCREEN_VERTEX,fragmentShader:STATIC_COPY_FRAGMENT,uniforms:{tDepth:{value:null}},depthTest:false,depthWrite:false});
  private readonly blur = new THREE.ShaderMaterial({vertexShader:FULLSCREEN_VERTEX,fragmentShader:VSM_BLUR_FRAGMENT,
    uniforms:{tSrc:{value:null},cInvTexSize:{value:new THREE.Vector2(1/NATIVE_STATIC_SHADOW_SETTINGS.width,1/NATIVE_STATIC_SHADOW_SETTINGS.width)}},depthTest:false,depthWrite:false});
  private readonly quad = new THREE.Mesh(new THREE.PlaneGeometry(2,2),this.copy);
  private readonly depthMaterials = new Map<THREE.Material,THREE.MeshDepthMaterial>();
  private signature = "";

  constructor() {
    this.uniforms={hStaticShadowMap:{value:null},hStaticShadowMatrix:{value:new THREE.Matrix4()},
      hStaticShadowFarFade:{value:new THREE.Vector2(0,1)},hStaticShadowAvailable:{value:0}};
    this.quad.frustumCulled=false;this.quadScene.add(this.quad);
    this.camera.matrixAutoUpdate=false;this.camera.matrixWorldAutoUpdate=false;
  }

  /** Static casters: renderInfo gsys_static_depth_shadow 1, including shadow-only (hidden) meshes. */
  collect(scene: THREE.Scene): {casters: THREE.Mesh[]; spheres: number[][]} {
    scene.updateMatrixWorld(true);const casters: THREE.Mesh[]=[],spheres: number[][]=[];
    const shown=(o: THREE.Object3D|null): boolean=>!o||(o.visible&&shown(o.parent));
    scene.traverse(o=>{
      const mesh=o as THREE.Mesh,u=mesh.userData as StaticShadowCasterData;
      if(!mesh.isMesh||!u.staticDepthShadow||!(mesh.visible||u.staticDepthShadowOnly)||!shown(mesh.parent))return;
      casters.push(mesh);
      if(u.staticDepthShadowSpheres)spheres.push(...u.staticDepthShadowSpheres);
      else {if(!mesh.geometry.boundingSphere)mesh.geometry.computeBoundingSphere();const s=mesh.geometry.boundingSphere!.clone().applyMatrix4(mesh.matrixWorld);spheres.push([s.center.x,s.center.y,s.center.z,s.radius]);}
    });
    return {casters,spheres};
  }

  private material(source: THREE.Material): THREE.MeshDepthMaterial {
    let out=this.depthMaterials.get(source);
    if(!out){
      const m=source as DepthSource;out=new THREE.MeshDepthMaterial({depthPacking:THREE.BasicDepthPacking});
      out.map=m.map??null;out.alphaMap=m.alphaMap??null;out.alphaTest=m.alphaToCoverage?.5:m.alphaTest;out.side=m.side;
      this.depthMaterials.set(source,out);
    }
    return out;
  }

  capture(renderer: THREE.WebGLRenderer,scene: THREE.Scene,direction: THREE.Vector3): void {
    const {casters,spheres}=this.collect(scene);
    const signature=casters.map(m=>m.id).join(",")+"|"+direction.toArray().join(",");
    if(signature===this.signature)return;
    this.uniforms.hStaticShadowAvailable.value=0;this.stats.casters=casters.length;this.fit=null;
    const bounds=nativeStaticShadowBounds(spheres);
    if(!casters.length||!bounds){this.signature=signature;return;}
    const fit=nativeStaticShadowFit(bounds.min,bounds.max,direction.toArray());
    const W=NATIVE_STATIC_SHADOW_SETTINGS.width;
    if(!this.depthTarget){
      const depth=new THREE.DepthTexture(W,W,THREE.FloatType);depth.minFilter=depth.magFilter=THREE.NearestFilter;depth.name="splatoon3.shadow.static.depth32";
      this.depthTarget=new THREE.WebGLRenderTarget(W,W,{depthTexture:depth,depthBuffer:true});
      const linear=renderer.extensions.has("OES_texture_float_linear");this.stats.filter=linear?"linear":"nearest (OES_texture_float_linear missing)";
      const make=(i: number)=>{
        const t=new THREE.WebGLRenderTarget(W,W,{type:THREE.FloatType,format:THREE.RGFormat,depthBuffer:false,generateMipmaps:false,
          minFilter:linear?THREE.LinearFilter:THREE.NearestFilter,magFilter:linear?THREE.LinearFilter:THREE.NearestFilter,wrapS:THREE.ClampToEdgeWrapping,wrapT:THREE.ClampToEdgeWrapping});
        t.texture.name=`splatoon3.shadow.static.rg32f.${i}`;return t;
      };
      this.maps=[make(0),make(1)];
    }
    for(const [source,proxy] of [...this.scene.children].map(p=>[p.userData.source as THREE.Mesh,p as THREE.Mesh] as const))if(!casters.includes(source))proxy.removeFromParent();
    const present=new Set(this.scene.children.map(p=>p.userData.source as THREE.Mesh));
    for(const mesh of casters){
      if(present.has(mesh))continue;
      const proxy=mesh.clone(false) as THREE.Mesh;proxy.visible=true;proxy.matrixAutoUpdate=false;proxy.frustumCulled=false;proxy.userData={source:mesh};
      proxy.matrix.copy(mesh.matrixWorld);proxy.matrixWorld.copy(mesh.matrixWorld);
      proxy.material=Array.isArray(mesh.material)?mesh.material.map(m=>this.material(m)):this.material(mesh.material);
      this.scene.add(proxy);
    }
    const view=new THREE.Matrix4().set(...fit.view as [number,number,number,number,number,number,number,number,number,number,number,number],0,0,0,1);
    this.camera.matrixWorldInverse.copy(view);this.camera.matrixWorld.copy(view).invert();
    this.camera.projectionMatrix.set(...fit.proj as [number,number,number,number,number,number,number,number,number,number,number,number,number,number,number,number]);
    this.camera.projectionMatrixInverse.copy(this.camera.projectionMatrix).invert();
    const oldTarget=renderer.getRenderTarget(),oldAuto=renderer.autoClear,oldTone=renderer.toneMapping;
    const oldClear=renderer.getClearColor(new THREE.Color()),oldAlpha=renderer.getClearAlpha();
    const oldViewport=renderer.getViewport(new THREE.Vector4()),oldScissor=renderer.getScissor(new THREE.Vector4()),oldScissorTest=renderer.getScissorTest();
    const [a,b]=this.maps!;
    try {
      renderer.autoClear=true;renderer.toneMapping=THREE.NoToneMapping;renderer.setClearColor(0xffffff,1);renderer.setScissorTest(false);
      renderer.setRenderTarget(this.depthTarget);renderer.clear(true,true,false);renderer.render(this.scene,this.camera);
      this.copy.uniforms.tDepth.value=this.depthTarget.depthTexture;this.quad.material=this.copy;renderer.setRenderTarget(a);renderer.render(this.quadScene,this.quadCamera);
      this.quad.material=this.blur;this.stats.blurPasses=0;
      for(let i=0;i<NATIVE_STATIC_SHADOW_SETTINGS.blurIterations;i++){
        this.blur.uniforms.tSrc.value=a.texture;renderer.setRenderTarget(b);renderer.render(this.quadScene,this.quadCamera);
        this.blur.uniforms.tSrc.value=b.texture;renderer.setRenderTarget(a);renderer.render(this.quadScene,this.quadCamera);this.stats.blurPasses+=2;
      }
      this.uniforms.hStaticShadowMap.value=a.texture;(this.uniforms.hStaticShadowMatrix.value as THREE.Matrix4).copy(webStaticShadowMatrix(fit));
      this.uniforms.hStaticShadowAvailable.value=1;this.fit=fit;this.signature=signature;this.stats.captures++;
    } finally {
      renderer.setRenderTarget(oldTarget);renderer.setViewport(oldViewport);renderer.setScissor(oldScissor);renderer.setScissorTest(oldScissorTest);
      renderer.setClearColor(oldClear,oldAlpha);renderer.autoClear=oldAuto;renderer.toneMapping=oldTone;
    }
  }

  dispose(): void {
    this.depthTarget?.dispose();this.maps?.forEach(t=>t.dispose());this.depthTarget=null;this.maps=null;
    for(const m of this.depthMaterials.values())m.dispose();this.depthMaterials.clear();
    this.copy.dispose();this.blur.dispose();this.quad.geometry.dispose();this.scene.clear();
    this.uniforms.hStaticShadowAvailable.value=0;this.uniforms.hStaticShadowMap.value=null;this.signature="";
  }
}

/** NativeShadowState owns only its targets/proxy depth materials; source meshes stay untouched. */
export class NativeShadowState {
  readonly targets: [THREE.WebGLRenderTarget, THREE.WebGLRenderTarget];
  readonly cameras: [THREE.OrthographicCamera, THREE.OrthographicCamera];
  readonly uniforms: Record<string, THREE.IUniform>;
  readonly stats = { captures: 0, casters: 0, proxyDraws: 0, projected: "unconfigured" };
  readonly staticShadow = new NativeStaticShadow();
  private readonly shadowScene = new THREE.Scene();
  private readonly casters = new Map<THREE.Mesh,Caster>();
  private readonly depthMaterials = new Map<THREE.Material,THREE.MeshDepthMaterial>();
  private readonly white: THREE.DataTexture;
  private readonly matrices: [THREE.Matrix4,THREE.Matrix4] = [new THREE.Matrix4(),new THREE.Matrix4()];
  private prePass: ShadowPrePassSettings={...NATIVE_SHADOW_PREPASS_DEFAULTS};

  constructor() {
    const make = (i: number) => {
      const depth = new THREE.DepthTexture(NATIVE_SHADOW_SETTINGS.width,NATIVE_SHADOW_SETTINGS.height,THREE.UnsignedIntType);
      depth.minFilter=depth.magFilter=THREE.NearestFilter;
      depth.name=`splatoon3.shadow.cascade${i}`;
      const target=new THREE.WebGLRenderTarget(NATIVE_SHADOW_SETTINGS.width,NATIVE_SHADOW_SETTINGS.height,{depthTexture:depth,depthBuffer:true});
      target.texture.name=`splatoon3.shadow.cascade${i}.unused-color`;return target;
    };
    this.targets=[make(0),make(1)]; this.cameras=[new THREE.OrthographicCamera(),new THREE.OrthographicCamera()];
    this.white=new THREE.DataTexture(new Uint8Array([255,255,255,255]),1,1);this.white.needsUpdate=true;
    this.uniforms={
      hShadowMap0:{value:this.targets[0].depthTexture},hShadowMap1:{value:this.targets[1].depthTexture},
      hShadowMatrix0:{value:this.matrices[0]},hShadowMatrix1:{value:this.matrices[1]},
      hShadowSplits:{value:new THREE.Vector3(...WEB_SHADOW_POLICY.splits as [number,number,number])},
      hShadowTexel:{value:new THREE.Vector2(NATIVE_SHADOW_SETTINGS.pcfOffset/NATIVE_SHADOW_SETTINGS.width,NATIVE_SHADOW_SETTINGS.pcfOffset/NATIVE_SHADOW_SETTINGS.height)},
      hShadowFarFade:{value:new THREE.Vector2(0,1)},hShadowKernel:{value:0},hShadowBias:{value:NATIVE_SHADOW_PREPASS_DEFAULTS.pcfWidth},
      hShadowAvailable:{value:0},hProjShadowMap:{value:this.white},hProjShadowAvailable:{value:0},
      hProjShadowDensity:{value:0},hProjShadowRows:{value:[new THREE.Vector4(),new THREE.Vector4(),new THREE.Vector4()]},
      hShadowFarDepthTest:{value:NATIVE_SHADOW_PREPASS_DEFAULTS.farDepthTestDist},
      ...this.staticShadow.uniforms,
    };
  }

  /** Apply evidenced native parameters; constructor defaults are kept separate from live selection. */
  configurePrePass(settings: ShadowPrePassSettings): void {
    if(![settings.filterShaderType,settings.filterSampleNum].every(Number.isInteger)||
      ![settings.pcfWidth,settings.dynamicFarFadeStart,settings.dynamicFarFadeEnd].every(Number.isFinite)||
      settings.useFarFade&&settings.dynamicFarFadeStart===settings.dynamicFarFadeEnd)throw new Error("Invalid shadow prepass settings");
    this.prePass={...settings};this.uniforms.hShadowKernel.value=nativeShadowShaderType(settings);this.uniforms.hShadowBias.value=settings.pcfWidth;
    this.uniforms.hShadowFarDepthTest.value=Math.fround(settings.farDepthTestDist??NATIVE_SHADOW_PREPASS_DEFAULTS.farDepthTestDist);
  }

  configure(raw: unknown): void {
    // The web currently supplies Default environment assets. Do not substitute ctor defaults for their overrides.
    this.configurePrePass(NATIVE_SHADOW_PREPASS_DEFAULT_ENV);
    const e=raw as {rendering?:{Shadow?:{ProjShadow?:{Density?:number}}}}|null;
    const density=e?.rendering?.Shadow?.ProjShadow?.Density;
    this.uniforms.hProjShadowAvailable.value=0;this.uniforms.hProjShadowDensity.value=0;
    this.uniforms.hProjShadowMap.value=this.white;
    this.stats.projected=density===0?"native Density=0; exact no-occlusion":"frame matrix/factor unconfirmed; not fabricated";
  }

  /** Bind only an evidenced frame producer. No nonzero Density-only approximate projector. */
  bindProjectedFrame(frame: ProjectedShadowFrame): void {
    const validRows=frame.matrixRows.length===3&&frame.matrixRows.every(row=>row.length===4&&row.every(Number.isFinite));
    if (!validRows||!Number.isFinite(frame.factor)||!Number.isFinite(frame.density)) throw new Error("Invalid projected shadow frame");
    this.uniforms.hProjShadowDensity.value=frame.count>0?projectedShadowDensity(frame.factor,frame.density):0;
    this.uniforms.hProjShadowAvailable.value=frame.count>0&&frame.enabled?1:0;
    this.uniforms.hProjShadowMap.value=frame.count>0&&frame.enabled?frame.texture:this.white;
    const rows=this.uniforms.hProjShadowRows.value as THREE.Vector4[];
    frame.matrixRows.forEach((row,i)=>rows[i].fromArray(row));
    this.stats.projected="explicit matrix/factor frame bound";
  }

  private material(source: THREE.Material): THREE.MeshDepthMaterial {
    let out=this.depthMaterials.get(source);
    if (!out) {out=new THREE.MeshDepthMaterial({depthPacking:THREE.BasicDepthPacking});this.depthMaterials.set(source,out);}
    const m=source as DepthSource;
    out.visible=m.visible;out.map=m.map??null;out.alphaMap=m.alphaMap??null;
    out.alphaTest=m.alphaToCoverage ? .5 : m.alphaTest;out.opacity=m.opacity;
    out.side=m.shadowSide??m.side;out.clipShadows=m.clipShadows;out.clippingPlanes=m.clippingPlanes;out.clipIntersection=m.clipIntersection;
    out.displacementMap=m.displacementMap??null;out.displacementScale=m.displacementScale??1;out.displacementBias=m.displacementBias??0;
    out.wireframe=m.wireframe??false;out.wireframeLinewidth=m.wireframeLinewidth??1;
    out.polygonOffset=true;out.polygonOffsetFactor=NATIVE_SHADOW_SETTINGS.polygonScale;out.polygonOffsetUnits=NATIVE_SHADOW_SETTINGS.polygonOffset;
    const signature=[m.version,!!out.map,!!out.alphaMap,out.alphaTest>0,!!out.displacementMap,out.side,out.clippingPlanes?.length??0].join(":");
    if(out.userData.shadowSignature!==signature){out.userData.shadowSignature=signature;out.needsUpdate=true;}
    return out;
  }

  private syncCasters(scene: THREE.Scene,camera: THREE.PerspectiveCamera): THREE.Box3 {
    scene.updateMatrixWorld(true);const present=new Set<THREE.Mesh>(),bounds=new THREE.Box3();
    scene.traverseVisible(o=>{
      const mesh=o as THREE.Mesh;if(!mesh.isMesh||!mesh.castShadow||!mesh.layers.test(camera.layers))return;
      present.add(mesh);let entry=this.casters.get(mesh);
      if(!entry){
        const proxy=mesh.clone(false) as THREE.Mesh;proxy.matrixAutoUpdate=false;proxy.frustumCulled=false;
        proxy.castShadow=false;proxy.receiveShadow=false;proxy.name=`shadow:${mesh.name}`;
        entry={source:mesh,proxy};this.casters.set(mesh,entry);this.shadowScene.add(proxy);
      }
      const proxy=entry.proxy;proxy.geometry=mesh.geometry;proxy.matrix.copy(mesh.matrixWorld);proxy.matrixWorld.copy(mesh.matrixWorld);
      proxy.morphTargetInfluences=mesh.morphTargetInfluences;
      const srcSkin=mesh as THREE.SkinnedMesh,pSkin=proxy as THREE.SkinnedMesh;
      if(srcSkin.isSkinnedMesh){pSkin.skeleton=srcSkin.skeleton;pSkin.bindMode=srcSkin.bindMode;pSkin.bindMatrix.copy(srcSkin.bindMatrix);pSkin.bindMatrixInverse.copy(srcSkin.bindMatrixInverse);}
      proxy.material=Array.isArray(mesh.material)?mesh.material.map(m=>this.material(m)):this.material(mesh.material);
      // Box3.setFromObject reads current SkinnedMesh and morph positions, rather than stale bind-pose geometry bounds.
      bounds.union(new THREE.Box3().setFromObject(mesh,true));
    });
    for(const [source,entry] of this.casters)if(!present.has(source)){entry.proxy.removeFromParent();this.casters.delete(source);}
    this.stats.casters=present.size;return bounds;
  }

  private fit(camera: THREE.PerspectiveCamera,direction: THREE.Vector3,bounds: THREE.Box3,index: number): void {
    const [near,far]=index===0?[WEB_SHADOW_POLICY.splits[0],WEB_SHADOW_POLICY.splits[1]]:[WEB_SHADOW_POLICY.splits[1],WEB_SHADOW_POLICY.splits[2]];
    const points=shadowSliceCorners(camera,near,far),center=new THREE.Vector3();for(const p of points)center.add(p);center.multiplyScalar(1/points.length);
    const casterPoints=boxCorners(bounds),all=[...points,...casterPoints];
    let radius=0;for(const p of all)radius=Math.max(radius,p.distanceTo(center));
    const c=this.cameras[index];c.position.copy(center).addScaledVector(direction,-Math.max(radius*2,1));c.up.set(0,1,0);
    if(Math.abs(direction.y)>.999)c.up.set(0,0,1);c.lookAt(center);c.updateMatrixWorld(true);
    const receiverBox=new THREE.Box3().setFromPoints(points.map(p=>p.clone().applyMatrix4(c.matrixWorldInverse)));
    const wholeBox=new THREE.Box3().setFromPoints(all.map(p=>p.clone().applyMatrix4(c.matrixWorldInverse)));
    const width=receiverBox.max.x-receiverBox.min.x,height=receiverBox.max.y-receiverBox.min.y;
    const cx=(receiverBox.min.x+receiverBox.max.x)*.5,cy=(receiverBox.min.y+receiverBox.max.y)*.5;
    const tx=width/NATIVE_SHADOW_SETTINGS.width,ty=height/NATIVE_SHADOW_SETTINGS.height;
    const sx=Math.round(cx/tx)*tx,sy=Math.round(cy/ty)*ty;
    c.left=sx-width*.5-tx;c.right=sx+width*.5+tx;c.bottom=sy-height*.5-ty;c.top=sy+height*.5+ty;
    c.near=Math.max(WEB_SHADOW_POLICY.nearFarPadding,-wholeBox.max.z-WEB_SHADOW_POLICY.nearFarPadding);
    c.far=Math.max(c.near+WEB_SHADOW_POLICY.nearFarPadding,-wholeBox.min.z+WEB_SHADOW_POLICY.nearFarPadding);
    c.updateProjectionMatrix();this.matrices[index].copy(BIAS_MATRIX).multiply(c.projectionMatrix).multiply(c.matrixWorldInverse);
  }

  capture(renderer: THREE.WebGLRenderer,scene: THREE.Scene,camera: THREE.PerspectiveCamera,direction: readonly number[]): void {
    this.uniforms.hShadowAvailable.value=0;this.stats.proxyDraws=0;
    this.uniforms.hShadowFarFade.value.fromArray(nativeShadowFarFade(this.prePass,camera.far));
    this.uniforms.hStaticShadowFarFade.value.fromArray(nativeStaticShadowFarFade(this.prePass,camera.far));
    const d=new THREE.Vector3(direction[0],direction[1],direction[2]);
    if(!d.toArray().every(Number.isFinite)||d.lengthSq()===0)throw new Error("Invalid shadow light direction");d.normalize();
    this.staticShadow.capture(renderer,scene,d);
    const bounds=this.syncCasters(scene,camera);if(this.stats.casters===0)return;
    const oldTarget=renderer.getRenderTarget(),oldAuto=renderer.autoClear,oldTone=renderer.toneMapping,oldShadow=renderer.shadowMap.autoUpdate;
    const oldClear=renderer.getClearColor(new THREE.Color()),oldAlpha=renderer.getClearAlpha();
    const oldViewport=renderer.getViewport(new THREE.Vector4()),oldScissor=renderer.getScissor(new THREE.Vector4()),oldScissorTest=renderer.getScissorTest();
    try {
      renderer.autoClear=true;renderer.toneMapping=THREE.NoToneMapping;renderer.shadowMap.autoUpdate=false;renderer.setClearColor(0xffffff,1);renderer.setScissorTest(false);
      for(let i=0;i<2;i++){
        this.fit(camera,d,bounds,i);renderer.setRenderTarget(this.targets[i]);renderer.clear(true,true,false);renderer.render(this.shadowScene,this.cameras[i]);this.stats.proxyDraws++;
      }
      this.uniforms.hShadowAvailable.value=1;this.stats.captures++;
    } finally {
      renderer.setRenderTarget(oldTarget);renderer.setViewport(oldViewport);renderer.setScissor(oldScissor);renderer.setScissorTest(oldScissorTest);
      renderer.setClearColor(oldClear,oldAlpha);renderer.autoClear=oldAuto;renderer.toneMapping=oldTone;renderer.shadowMap.autoUpdate=oldShadow;
    }
  }

  dispose(): void {
    for(const t of this.targets)t.dispose();for(const m of this.depthMaterials.values())m.dispose();this.white.dispose();
    this.shadowScene.clear();this.casters.clear();this.depthMaterials.clear();this.uniforms.hShadowAvailable.value=0;this.staticShadow.dispose();
  }
}
