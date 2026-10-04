// Native environment reflection chain, graphics_r11_light §4:
//   0x710102ce04 base cube → 0x7101037098 Illuminate (GGXPrefilterEnvMap MRT1/FILTER2/ILLUMINATE1, 1 sample, override r = BlitzUBO0[18].x)
//   → copy back to base → SH (0x710103289c) and 12-layer prefilter (0x7101036a18, FILTER2, 400 samples for Illuminate type).
//   GGXEnvBRDF LUT = Hoian_Proc GGXEnvBRDF (1024 samples). Shader equations from analysis/gfx_r11/proc_fixed (Negate-corrected).
// Web policies (not native): layer tile sizes / 2D atlas with manual face selection, BRDF LUT 64², VdC = base-2 radical inverse.
import * as THREE from "three";
import { F, add, sub, mul, div, type V3 } from "./graphics_math.ts";

type Json = Record<string, unknown>;
const obj = (v: unknown): Json => v && typeof v === "object" ? v as Json : {};
const num = (v: unknown, d: number): number => typeof v === "number" && Number.isFinite(v) ? F(v) : F(d);

export const ILLUMINATE_NATIVE = Object.freeze({
  /** 102FF04 holder+0xC34 = 0x3de147ae */
  roughnessAdd: F(.11),
  /** 1037098 override = *(SceneCommonUBOHolder+0xb98) = BlitzUBO0[18].x (ink roughness) */
  inkRoughness: F(.05),
  /** IlluminateEnvMap ctor 0x71011aa4b4 / element ctor 0x71011abd34 */
  baseIntensity: 1, lightTexScale: 1, element: Object.freeze({ intensity: 1000, latitude: 40, longitude: 0 }),
  /** 1030288 returns without copying when the array is longer than holder capacity 0x14 */
  maxLights: 20, baseSamples: 1, layerSamples: 400, layerCount: 12, pdfTexels: 98304,
});

export interface IlluminateUBO { param: V3; color: [number, number, number, number]; lights: [number, number, number, number][] }

/** 1030288 typed read + 102FF04 UBO writer (f32 order of the decompiled writer; SDK sinf/cosf replaced by f32-rounded JS). */
export function illuminateUBO(env: unknown, mainDirection: readonly number[], mainColor: readonly number[]): IlluminateUBO | null {
  const lighting = obj(obj(obj(env).rendering).Lighting), map = obj(lighting.EnvMap);
  if (map.Type !== "Illuminate") return null;
  const il = obj(map.IlluminateEnvMap), arr = Array.isArray(il.LightArray) ? il.LightArray : [];
  const baseIntensity = num(il.BaseIntensity, ILLUMINATE_NATIVE.baseIntensity), lts = num(il.LightTexScale, ILLUMINATE_NATIVE.lightTexScale);
  const elems = arr.length > ILLUMINATE_NATIVE.maxLights ? [] : arr.map(e => {
    const o = obj(e), d = ILLUMINATE_NATIVE.element;
    return [num(o.Latitude, d.latitude), num(o.Intensity, d.intensity), num(o.LongitudeFromMainLight, d.longitude)];
  });
  const k = F(.017453292);
  const fx = F(mainDirection[0]), fz = F(mainDirection[2]);
  const lights = elems.map(([lat, intensity, lon]) => {
    let x0 = fx, z0 = fz;
    const len = F(Math.sqrt(add(mul(x0, x0), mul(z0, z0))));
    if (len > 0) { const inv = div(1, len); x0 = mul(x0, inv); z0 = mul(z0, inv); }
    const s = F(Math.sin(mul(lon, k))), c = F(Math.cos(mul(lon, k))), cl = F(Math.cos(mul(lat, k)));
    let x = mul(cl, sub(mul(x0, c), mul(z0, s))), z = mul(cl, add(mul(x0, s), mul(z0, c)));
    const sl = F(Math.sin(mul(lat, k)));
    const n = F(Math.sqrt(add(mul(z, z), add(mul(sl, sl), mul(x, x)))));
    let y = F(-sl);
    if (n > 0) { const inv = div(1, n); x = mul(x, inv); y = mul(inv, y); z = mul(z, inv); }
    return [x, y, z, mul(intensity, baseIntensity)] as [number, number, number, number];
  });
  return { param: [lts, ILLUMINATE_NATIVE.roughnessAdd, F(lights.length)], color: [0, 1, 2, 3].map(i => F(mainColor[i] ?? 1)) as [number, number, number, number], lights };
}

/** cVanDerCorputMap texel i ((i&255)+.5)/256, ((i>>8)+.5)/4: base-2 radical inverse [추정: texture content]. */
export function vanDerCorput(i: number): number {
  let b = i >>> 0;
  b = ((b << 16) | (b >>> 16)) >>> 0;
  b = (((b & 0x55555555) << 1) | ((b & 0xAAAAAAAA) >>> 1)) >>> 0;
  b = (((b & 0x33333333) << 2) | ((b & 0xCCCCCCCC) >>> 2)) >>> 0;
  b = (((b & 0x0F0F0F0F) << 4) | ((b & 0xF0F0F0F0) >>> 4)) >>> 0;
  b = (((b & 0x00FF00FF) << 8) | ((b & 0xFF00FF00) >>> 8)) >>> 0;
  return F(b / 4294967296);
}

/** Hoian_Proc GGXEnvBRDF pixel: in_attr0 = (NoV, roughness), 1024 samples, out = (Σ G(1−Fc), Σ G·Fc)/1024. */
export function ggxEnvBRDF(nov: number, roughness: number): [number, number] {
  const x = F(nov), a = mul(roughness, roughness), s = F(Math.sqrt(F(1 - mul(x, x)))), k = mul(a, .5);
  let sa = 0, sb = 0;
  for (let i = 0; i < 1024; i++) {
    const u = vanDerCorput(i);
    const t13 = div(1, add(F(u * mul(a, a) - u), 1));
    const cosH = F(Math.sqrt(F(t13 - u * t13)));
    const sp = mul(F(Math.sin(mul(i, .00613592332))), F(Math.sqrt(F(1 - cosH * cosH))));
    const voh = Math.min(1, Math.max(0, F(x * cosH + s * sp)));
    const t17 = div(1, Math.min(1, Math.max(0, cosH)));
    const nol = Math.min(1, Math.max(0, F(F(cosH * F(-(x * cosH) - s * sp)) * -2 - x)));
    const g = F(F(F(F(nol * voh) * div(1, add(k, F(x - k * x)))) * div(1, add(k, F(nol - k * nol)))) * t17);
    if (nol > 0 && g > 0) {
      const fc = F(2 ** F(voh * F(voh * -5.55473 - 6.98316002)));
      sa = F(sa + F(g - g * fc)); sb = F(sb + g * fc);
    }
  }
  return [mul(sa, .0009765625), mul(sb, .0009765625)];
}

/** 1035C4C layer roughness, t = layer/(count−1). */
export function nativeLayerRoughness(layer: number, count = ILLUMINATE_NATIVE.layerCount): number {
  if (count - 1 === 0) return 0;
  const t = div(layer, count - 1);
  return add(t, mul(sub(F(Math.sin(mul(sub(t, .92), 6.2831855))), .4817533), .13));
}
/** Hoian_UBER fragment: layer = clamp(uint(max(roundEven(roundEven(fma(cos(πr),−5.5,5.5))),0))). */
export function nativeEnvLayer(roughness: number): number {
  const v = F(F(Math.cos(mul(roughness, 3.14159274))) * -5.5 + 5.5);
  const re = (x: number): number => { const f = Math.floor(x), d = x - f; return d > .5 || (d === .5 && f % 2 !== 0) ? f + 1 : f; };
  return Math.min(11, Math.max(0, re(re(v))));
}

/** Web atlas: each layer is one row of six face tiles. */
export const PREFILTER_TILES = Object.freeze([128, 128, 64, 64, 32, 32, 16, 16, 8, 8, 8, 8]);
export const PREFILTER_ATLAS = Object.freeze({ width: 6 * 128, height: PREFILTER_TILES.reduce((a, b) => a + b, 0) });
/** Web face convention shared by the generator and the material lookup (a,b ∈ [−1,1]). */
export function faceDirection(face: number, a: number, b: number): V3 {
  switch (face) {
    case 0: return [1, b, -a]; case 1: return [-1, b, a]; case 2: return [a, 1, -b];
    case 3: return [a, -1, b]; case 4: return [a, b, 1]; default: return [-a, b, -1];
  }
}

export const FACE_GLSL = /* glsl */`
vec3 hFaceDirection(int f,vec2 ab){
  return f==0?vec3(1.,ab.y,-ab.x):f==1?vec3(-1.,ab.y,ab.x):f==2?vec3(ab.x,1.,-ab.y):
         f==3?vec3(ab.x,-1.,ab.y):f==4?vec3(ab.x,ab.y,1.):vec3(-ab.x,ab.y,-1.);
}`;

/** Material lookup (forward.ts DECL). */
export const PREFILTER_LOOKUP_GLSL = /* glsl */`
uniform sampler2D hPrefilAtlas,hEnvBRDF;
uniform vec4 hPrefilRows[12];
uniform float hPrefilAvailable;
vec3 hPrefilSample(vec3 d,int layer){
  vec3 m=abs(d);int f;vec2 ab;
  if(m.x>=m.y&&m.x>=m.z){f=d.x>0.?0:1;ab=d.x>0.?vec2(-d.z,d.y)/m.x:vec2(d.z,d.y)/m.x;}
  else if(m.y>=m.z){f=d.y>0.?2:3;ab=d.y>0.?vec2(d.x,-d.z)/m.y:vec2(d.x,d.z)/m.y;}
  else{f=d.z>0.?4:5;ab=d.z>0.?vec2(d.x,d.y)/m.z:vec2(-d.x,d.y)/m.z;}
  vec4 row=hPrefilRows[layer];
  vec2 uv=clamp(ab*.5+.5,vec2(.5/row.w),vec2(1.-.5/row.w));
  return textureLod(hPrefilAtlas,vec2((float(f)+uv.x)*row.z,row.x+uv.y*row.y),0.).rgb;
}
vec3 hNativeEnvSpecular(vec3 n,vec3 v,vec3 f0,float r){
  if(hPrefilAvailable<.5)return vec3(0.);
  float nov=max(dot(n,v),1e-8);
  vec2 b=texture2D(hEnvBRDF,vec2(nov,r)).xy;
  int layer=int(clamp(roundEven(roundEven(cos(r*3.14159274)*-5.5+5.5)),0.,11.));
  return hPrefilSample(reflect(-v,n),layer)*(f0*b.x+b.y);
}`;

/** GGXPrefilterEnvMap FILTER_TYPE 2 sampling loop (ILLUMINATE 0/1 share it). */
const PREFILTER_GLSL = /* glsl */`
uniform samplerCube cBase;uniform vec4 cParam0;uniform sampler2D cVanDerCorputMap;
vec3 hPrefilter(vec3 n){
  vec3 acc=vec3(0.);float wsum=0.;
  if(0.<cParam0.w){
    float t10=abs(n.z)>=.999?1.:0.,t12=abs(n.z)<.999?1.:0.;int cnt=int(trunc(cParam0.w));
    float a13=n.y*t10,a14=n.y*t12,a15=n.x*t12-n.z*t10,rs=inversesqrt(a13*a13+a15*a15+a14*a14);
    vec3 t=vec3(a14*-rs,a15*rs,a13*rs);
    float r=max(cParam0.x,.0001),a=r*r,a2=a*a;
    for(int i=0;i<1024;i++){ if(i>=cnt)break;
      float u=texture(cVanDerCorputMap,vec2((float(i&255)+.5)*.00390625,(float(i>>8)+.5)*.25)).x;
      float ph=float(i)/float(cnt)*6.28318548,t40=1./(u*a2-u+1.),ct=sqrt(t40-u*t40),st=sqrt(1.-ct*ct);
      float sp=sin(ph)*st,cp=cos(ph)*st;
      vec3 h=vec3(n.x*ct+t.x*cp+(n.y*t.z-n.z*t.y)*sp,n.y*ct+t.y*cp+(n.z*t.x-n.x*t.z)*sp,n.z*ct+t.z*cp+(n.x*t.y-n.y*t.x)*sp);
      float noh=dot(n,h);vec3 l=2.*noh*h-n;float nol=clamp(dot(n,l),0.,1.);
      if(nol>0.){
        float nh=max(noh,1e-8),lod=0.;
        if(r>=.01){float d=1./max(a2*nh*nh-nh*nh+1.,1e-8);float pinv=1./(float(cnt)*nh*a*d*a*d*.25*(1./nh))*${ILLUMINATE_NATIVE.pdfTexels}.;lod=max(0.,min(log2(pinv)*.5,4.));}
        acc+=nol*textureLod(cBase,l/max(abs(l.z),max(abs(l.x),abs(l.y))),lod).rgb;wsum+=nol;
      }
    }
  }
  return acc/wsum;
}`;

const ILLUMINATE_FRAGMENT = /* glsl */`
uniform sampler2D cHighlight;uniform vec4 cLightParam,cLightColor,cLightInfo[32];
varying vec3 vDir;
${PREFILTER_GLSL}
void main(){
  vec3 n=normalize(vDir),c=hPrefilter(n);int cnt=int(trunc(cLightParam.z));
  float k=1./cLightParam.x*.5,re=max(0.,clamp(max(cParam0.x+cLightParam.y,.0001),0.,1.));
  float t85=re*.5+.5,a=re*re,kk=t85*.5*t85;
  for(int i=0;i<32;i++){ if(i>=cnt)break;
    vec4 L=cLightInfo[i];
    float t99=abs(L.z)>=.999?1.:0.,t100=abs(L.z)<.999?1.:0.;
    float b101=L.y*-t99,b102=L.y*-t100,b103=L.x*-t100-L.z*-t99,rs=inversesqrt(b101*b101+b103*b103+b102*b102);
    vec3 T=vec3(b102*-rs,b103*rs,b101*rs);
    vec3 B=vec3(-L.y*T.z+L.z*T.y,-L.z*T.x+L.x*T.z,-L.x*T.y+L.y*T.x);
    vec3 hl=texture2D(cHighlight,vec2(dot(n,T)*k+.5,dot(n,B)*k+.5)).rgb;
    vec3 ld=normalize(L.xyz*-2.);
    float nl=dot(n,-L.xyz),nol=clamp(nl,0.,1.),voh=max(dot(L.xyz,-ld),1e-8),nh=max(dot(n,ld),1e-8),nh2=nh*nh,nlm=max(nl,1e-8);
    float dd=1./max(nh2*a*a-nh2+1.,1e-8);
    float w=1./(kk+(nol-kk*nol))*(1./(kk+(nlm-kk*nlm)))*a*dd*a*dd*exp2(voh*(voh*-5.55473-6.98316002))*.0795774683;
    c+=hl*(L.w*cLightColor.rgb*nol*w);
  }
  gl_FragColor=vec4(c,1.);
}`;

const LAYER_FRAGMENT = /* glsl */`
varying vec2 vUv;
${FACE_GLSL}
${PREFILTER_GLSL}
void main(){
  float fx=vUv.x*6.;int f=int(min(floor(fx),5.));
  vec2 ab=vec2(fract(fx),vUv.y)*2.-1.;
  gl_FragColor=vec4(hPrefilter(normalize(hFaceDirection(f,ab))),1.);
}`;

function vdcTexture(): THREE.DataTexture {
  const data = new Float32Array(256 * 4 * 4);
  for (let i = 0; i < 1024; i++) data[i * 4] = vanDerCorput(i);
  const t = new THREE.DataTexture(data, 256, 4, THREE.RGBAFormat, THREE.FloatType);
  t.minFilter = t.magFilter = THREE.NearestFilter; t.colorSpace = THREE.NoColorSpace; t.needsUpdate = true; return t;
}
export function brdfLUT(size = 64): THREE.DataTexture {
  const data = new Uint16Array(size * size * 4);
  for (let j = 0; j < size; j++) for (let i = 0; i < size; i++) {
    const [x, y] = ggxEnvBRDF((i + .5) / size, (j + .5) / size), o = (j * size + i) * 4;
    data[o] = THREE.DataUtils.toHalfFloat(x); data[o + 1] = THREE.DataUtils.toHalfFloat(y); data[o + 3] = 0x3c00;
  }
  const t = new THREE.DataTexture(data, size, size, THREE.RGBAFormat, THREE.HalfFloatType);
  t.minFilter = t.magFilter = THREE.LinearFilter; t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; t.colorSpace = THREE.NoColorSpace; t.needsUpdate = true;
  return t;
}
export interface HighlightData { mips: { width: number; height: number; offset: number; bytes: number }[] }
export function highlightTexture(meta: HighlightData, bytes: ArrayBuffer): THREE.DataTexture {
  const mips = meta.mips.map(m => ({ data: new Uint8Array(bytes, m.offset, m.bytes), width: m.width, height: m.height }));
  const t = new THREE.DataTexture(mips[0].data, mips[0].width, mips[0].height, THREE.RGBAFormat, THREE.UnsignedByteType);
  t.mipmaps = mips as unknown as THREE.DataTexture["mipmaps"]; t.generateMipmaps = false; t.flipY = false;
  t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter; t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  t.colorSpace = THREE.SRGBColorSpace; t.needsUpdate = true; return t;
}

export class NativeEnvironment {
  readonly vdc = vdcTexture();
  readonly brdf = brdfLUT();
  readonly atlas = new THREE.WebGLRenderTarget(PREFILTER_ATLAS.width, PREFILTER_ATLAS.height, { type: THREE.HalfFloatType, depthBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, generateMipmaps: false });
  readonly lit = new THREE.WebGLCubeRenderTarget(256, { type: THREE.HalfFloatType, generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter });
  readonly rows = PREFILTER_TILES.map(() => new THREE.Vector4());
  readonly uniforms = {
    hPrefilAtlas: { value: this.atlas.texture as THREE.Texture }, hEnvBRDF: { value: this.brdf as THREE.Texture },
    hPrefilRows: { value: this.rows }, hPrefilAvailable: { value: 0 },
  };
  readonly stats: Record<string, unknown> = { illuminate: "unconfigured", prefilter: 0, brdf: "GGXEnvBRDF port 64²" };
  private ubo: IlluminateUBO | null = null;
  private highlight: THREE.Texture | null = null;
  private readonly illuminateMaterial: THREE.ShaderMaterial;
  private readonly layerMaterial: THREE.ShaderMaterial;
  private readonly illuminateScene = new THREE.Scene();
  private readonly quadScene = new THREE.Scene();
  private readonly quadCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  constructor() {
    this.atlas.texture.colorSpace = THREE.NoColorSpace; this.lit.texture.colorSpace = THREE.LinearSRGBColorSpace;
    let y = 0;
    PREFILTER_TILES.forEach((s, i) => { this.rows[i].set(y / PREFILTER_ATLAS.height, s / PREFILTER_ATLAS.height, s / PREFILTER_ATLAS.width, s); y += s; });
    const common = { cBase: { value: null as THREE.Texture | null }, cParam0: { value: new THREE.Vector4() }, cVanDerCorputMap: { value: this.vdc } };
    this.illuminateMaterial = new THREE.ShaderMaterial({
      uniforms: { ...common, cHighlight: { value: null }, cLightParam: { value: new THREE.Vector4() }, cLightColor: { value: new THREE.Vector4() },
        cLightInfo: { value: Array.from({ length: 32 }, () => new THREE.Vector4()) } },
      vertexShader: "varying vec3 vDir;void main(){vDir=(modelMatrix*vec4(position,1.)).xyz;gl_Position=projectionMatrix*viewMatrix*vec4(vDir,1.);}",
      fragmentShader: ILLUMINATE_FRAGMENT, side: THREE.BackSide, depthTest: false, depthWrite: false, toneMapped: false,
    });
    this.layerMaterial = new THREE.ShaderMaterial({
      uniforms: { cBase: { value: null }, cParam0: { value: new THREE.Vector4() }, cVanDerCorputMap: { value: this.vdc } },
      vertexShader: "varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}",
      fragmentShader: LAYER_FRAGMENT, depthTest: false, depthWrite: false, toneMapped: false,
    });
    const box = new THREE.Mesh(new THREE.BoxGeometry(2, 2, 2), this.illuminateMaterial); box.frustumCulled = false; this.illuminateScene.add(box);
    const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.layerMaterial); quad.frustumCulled = false; this.quadScene.add(quad);
  }
  configure(env: unknown, mainDirection: readonly number[], mainColor: readonly number[], highlight: THREE.Texture | null): void {
    this.ubo = illuminateUBO(env, mainDirection, mainColor); this.highlight = highlight;
    const u = this.illuminateMaterial.uniforms;
    if (this.ubo) {
      u.cLightParam.value.set(...this.ubo.param, 0); u.cLightColor.value.fromArray(this.ubo.color);
      this.ubo.lights.forEach((l, i) => (u.cLightInfo.value as THREE.Vector4[])[i].fromArray(l));
      u.cParam0.value.set(ILLUMINATE_NATIVE.inkRoughness, 4, 1024, ILLUMINATE_NATIVE.baseSamples);
      u.cHighlight.value = highlight;
    }
    this.stats.illuminate = !this.ubo ? "EnvMap.Type is not Illuminate" : !highlight ? "highlight texture missing; base cube used" : `${this.ubo.lights.length} lights connected`;
  }
  /** Returns the cube to project/prefilter: the illuminated copy (native copy-back) or the base. */
  illuminate(renderer: THREE.WebGLRenderer, base: THREE.CubeTexture): THREE.CubeTexture {
    if (!this.ubo || !this.highlight) return base;
    this.illuminateMaterial.uniforms.cBase.value = base;
    const cam = new THREE.CubeCamera(.1, 10, this.lit);
    cam.update(renderer, this.illuminateScene);
    return this.lit.texture;
  }
  prefilter(renderer: THREE.WebGLRenderer, source: THREE.CubeTexture): void {
    const u = this.layerMaterial.uniforms, old = renderer.getRenderTarget(), auto = renderer.autoClear;
    const vp = renderer.getViewport(new THREE.Vector4()), sc = renderer.getScissor(new THREE.Vector4()), st = renderer.getScissorTest();
    try {
      u.cBase.value = source; renderer.autoClear = false; renderer.setRenderTarget(this.atlas); renderer.setScissorTest(true);
      let y = 0;
      PREFILTER_TILES.forEach((s, l) => {
        u.cParam0.value.set(nativeLayerRoughness(l), 4, 1024, ILLUMINATE_NATIVE.layerSamples);
        this.atlas.viewport.set(0, y, 6 * s, s); this.atlas.scissor.set(0, y, 6 * s, s); this.atlas.scissorTest = true;
        renderer.setRenderTarget(this.atlas); renderer.render(this.quadScene, this.quadCamera); y += s;
      });
      this.atlas.viewport.set(0, 0, PREFILTER_ATLAS.width, PREFILTER_ATLAS.height); this.atlas.scissorTest = false;
      this.uniforms.hPrefilAvailable.value = 1; this.stats.prefilter = Number(this.stats.prefilter) + 1;
    } finally {
      renderer.setRenderTarget(old); renderer.setViewport(vp); renderer.setScissor(sc); renderer.setScissorTest(st); renderer.autoClear = auto;
    }
  }
  dispose(): void {
    this.vdc.dispose(); this.brdf.dispose(); this.atlas.dispose(); this.lit.dispose(); this.highlight?.dispose();
    this.illuminateMaterial.dispose(); this.layerMaterial.dispose();
  }
}
