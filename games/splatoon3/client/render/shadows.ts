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
});

/** Default/default.baglshpp [data]: resource overrides, distinct from constructor values. */
export const NATIVE_SHADOW_PREPASS_DEFAULT_ENV = Object.freeze({
  filterShaderType: 0, filterSampleNum: 0, pcfWidth: 5,
  useFarFade: true, dynamicFarFadeStart: 40, dynamicFarFadeEnd: 60,
});

export interface ShadowPrePassSettings {
  /** Recovered SHADER_TYPE 0/1/2/3 = 1/4/9/16 comparison samples. */
  filterShaderType: number; filterSampleNum: number; pcfWidth: number;
  useFarFade: boolean; dynamicFarFadeStart: number; dynamicFarFadeEnd: number;
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
vec2 hShadowPrePass(vec3 worldPos,float positiveViewDepth) {
  // WEB_SHADOW_POLICY retains an explicit outside-final-cascade adapter gate.
  if(hShadowAvailable<.5||positiveViewDepth>hShadowSplits.z)return vec2(1.);
  // 3750740 uploads boundary[i+1]; native comparison is strict >, with no near cutoff.
  float v=positiveViewDepth<=hShadowSplits.y?hCascadeVisibility(hShadowMap0,hShadowMatrix0,worldPos):hCascadeVisibility(hShadowMap1,hShadowMatrix1,worldPos);
  // SPP.y adds far fade. Values above 1 are retained until the forward max consumer.
  return vec2(1.,v+clamp((positiveViewDepth-hShadowFarFade.x)*hShadowFarFade.y,0.,1.));
}
float hDynamicShadow(vec3 worldPos,float positiveViewDepth) {
  vec2 spp=hShadowPrePass(worldPos,positiveViewDepth);
  return 1.-max(1.-spp.x,1.-spp.y);
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

/** NativeShadowState owns only its targets/proxy depth materials; source meshes stay untouched. */
export class NativeShadowState {
  readonly targets: [THREE.WebGLRenderTarget, THREE.WebGLRenderTarget];
  readonly cameras: [THREE.OrthographicCamera, THREE.OrthographicCamera];
  readonly uniforms: Record<string, THREE.IUniform>;
  readonly stats = { captures: 0, casters: 0, proxyDraws: 0, projected: "unconfigured" };
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
    };
  }

  /** Apply evidenced native parameters; constructor defaults are kept separate from live selection. */
  configurePrePass(settings: ShadowPrePassSettings): void {
    if(![settings.filterShaderType,settings.filterSampleNum].every(Number.isInteger)||
      ![settings.pcfWidth,settings.dynamicFarFadeStart,settings.dynamicFarFadeEnd].every(Number.isFinite)||
      settings.useFarFade&&settings.dynamicFarFadeStart===settings.dynamicFarFadeEnd)throw new Error("Invalid shadow prepass settings");
    this.prePass={...settings};this.uniforms.hShadowKernel.value=nativeShadowShaderType(settings);this.uniforms.hShadowBias.value=settings.pcfWidth;
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
    const d=new THREE.Vector3(direction[0],direction[1],direction[2]);
    if(!d.toArray().every(Number.isFinite)||d.lengthSq()===0)throw new Error("Invalid shadow light direction");d.normalize();
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
    this.shadowScene.clear();this.casters.clear();this.depthMaterials.clear();this.uniforms.hShadowAvailable.value=0;
  }
}
