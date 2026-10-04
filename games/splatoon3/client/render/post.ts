// Hoian_ProcHDRCompose tone 4 + manual EV consumer, stage_rendering §3.1/3.3.
// Native default Bloom producer and CC mode0 connected; DOF/live output flags remain separate.
import * as THREE from "three";
import { CC_WEB_POLICY, colorCorrectionPacket, colorCorrectionLUT, type ColorCorrectionLUT, type ColorCorrectionPacket, type NativeColorGrading } from "./post_math.ts";
import { NativeBloom, savePostRegion, type BloomSetting } from "./bloom.ts";

export function tone4(rgb: number[], exposure = 1): number[] {
  const x = rgb.map(v => v * exposure), l = x[0] * .2989 + x[1] * .5866 + x[2] * .1144;
  if (l === 0 && x.every(v => v === 0)) return [0, 0, 0]; // Web finite black limit for the native 0/0 expression.
  const t = 1 - Math.exp(-l);
  return x.map(v => {
    const y = v * t / l;
    return Math.min(1, Math.max(0, y + ((1 - Math.exp(-v)) - y) * t * t));
  });
}
/** Uniform-level contract from 1120eac; callers must supply verified live values to enable it. */
export interface HDRVignette {
  shape: 1 | 2;
  param: [number, number, number, number];
  color: [number, number, number, number];
  start: number;
  range: number;
}
export class HDRCompose {
  readonly bloom = new NativeBloom();
  readonly target = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, depthBuffer: true });
  readonly material: THREE.ShaderMaterial;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.Camera();
  private readonly triangle: THREE.Mesh;
  private readonly black = new THREE.DataTexture(new Uint8Array([0, 0, 0, 0]), 1, 1);
  private readonly identity = new THREE.Data3DTexture(new Uint16Array([0, 0, 0, 0x3c00]), 1, 1, 1);
  private lutTexture: THREE.Data3DTexture | null = null;
  private externalBloom: { texture: THREE.Texture; mode: 1 | 2 } | null = null;
  readonly size = new THREE.Vector2();
  exposure = 1;
  /** GAMMA 1 = native UNORM display path (+523c bit4 = SystemTask+0x464 bit0 = +0x422 sRGB-display flag, ctor 0). The canvas is UNORM. */
  gamma = 1;
  /** Exposed for actual GPU integration/reference verification. */
  ccPacket: ColorCorrectionPacket | null = null;
  ccLUT: ColorCorrectionLUT | null = null;
  readonly stats: Record<string, unknown> = {
    tone: 4, ccEnabled: false, ccMode: "native default 0", lutDimension: 8,
    lutPolicy: CC_WEB_POLICY, nativeGPUEquivalent: false,
    bloom: "native default producer connected; live view gates and NVN sampler/format remain unverified",
    dof: "unbound: native shader and live Enable remain unverified",
    vignette: "inactive: live enable and uniforms remain unverified",
    gamma: "native GAMMA 1 for UNORM display (0x71036c8c24/0x71037a46bc); Lby SystemTask+0x422 writer unverified (sRGB display would use GAMMA 0 + hardware encode)",
  };

  constructor() {
    this.target.texture.colorSpace = THREE.LinearSRGBColorSpace;
    this.target.samples = 4;
    this.black.needsUpdate = true;
    this.identity.type = THREE.HalfFloatType;
    this.identity.needsUpdate = true;
    this.material = new THREE.ShaderMaterial({
      glslVersion: THREE.GLSL3,
      uniforms: {
        hdr: { value: this.target.texture }, exposure: { value: 1 }, gammaMode: { value: 1 },
        colorLUT: { value: this.identity }, ccEnabled: { value: false }, ccCoeff: { value: new THREE.Vector2(.875, .0625) },
        bloom: { value: this.black }, bloomMode: { value: 0 },
        vignetteMode: { value: 0 }, vignetteParam: { value: new THREE.Vector4(1, 1, 0, 0) },
        vignetteColor: { value: new THREE.Vector4(0, 0, 0, 0) }, vignetteStart: { value: 0 }, vignetteRange: { value: 0 },
      },
      vertexShader: "out vec2 vUv; void main(){vUv=position.xy*.5+.5;gl_Position=vec4(position.xy,0.,1.);}",
      fragmentShader: String.raw`
        uniform sampler2D hdr; uniform float exposure; uniform int gammaMode;
        uniform highp sampler3D colorLUT; uniform bool ccEnabled; uniform vec2 ccCoeff;
        uniform sampler2D bloom; uniform int bloomMode;
        uniform int vignetteMode; uniform vec4 vignetteParam; uniform vec4 vignetteColor;
        uniform float vignetteStart; uniform float vignetteRange;
        in vec2 vUv; out vec4 postColor;
        void main() {
          vec4 h=texture(hdr,vUv); vec3 x=h.rgb*exposure;
          if(bloomMode==1)x+=texture(bloom,vUv).rgb;
          else if(bloomMode==2)x+=texture(bloom,vUv).rgb*(1.-clamp(dot(x,vec3(.2989,.5866,.1144)),0.,1.));
          float l=dot(x,vec3(.2989,.5866,.1144));
          float t=1.-exp2(l*-1.44269502);
          vec3 y=(l==0. && all(equal(x,vec3(0.)))) ? vec3(0.) : x*(t/l);
          vec3 c=clamp(y+((1.-exp2(x*-1.44269502))-y)*(t*t),0.,1.);
          if(ccEnabled)c=texture(colorLUT,c*ccCoeff.x+ccCoeff.y).rgb;
          if(vignetteMode!=0){
            vec2 p=(2.*vUv-vignetteParam.zw-1.)/vignetteParam.xy*vec2(.8716,.5625*.8716);
            float r=vignetteMode==1 ? length(p) : max(abs(p.x),abs(p.y));
            float k=1./max(vignetteRange*(vignetteMode==1?.25:1.),.001);
            float v=clamp((r+vignetteStart)*k-k,0.,1.);
            c=mix(c,vignetteColor.rgb,v*vignetteColor.a);
          }
          if(gammaMode==1)c=pow(abs(c),vec3(1./2.2));
          else if(gammaMode==2)c=pow(abs(c),vec3(2.2));
          postColor=vec4(c,h.a);
        }
      `,
      depthTest: false, depthWrite: false, toneMapped: false,
    });
    const geometry = new THREE.BufferGeometry().setAttribute("position", new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
    this.triangle = new THREE.Mesh(geometry, this.material);
    this.triangle.frustumCulled = false;
    this.scene.add(this.triangle);
  }
  configure(env: unknown): void {
    const e = env as { rendering?: { PostEffect?: { HDRExposure?: { ExposureType?: string; ManualExposure?: { Value?: number } }; ColorGrading?: NativeColorGrading; DOFGaussian?: unknown; Bloom?: BloomSetting } } };
    const post = e?.rendering?.PostEffect, hdr = post?.HDRExposure;
    this.exposure = hdr?.ExposureType === "ManualExposure" ? Math.fround(2 ** Math.fround(hdr.ManualExposure?.Value ?? 0)) : 1;
    this.lutTexture?.dispose(); this.lutTexture = null;
    this.ccPacket = colorCorrectionPacket(post?.ColorGrading);
    this.ccLUT = this.ccPacket ? colorCorrectionLUT(this.ccPacket) : null;
    if (this.ccLUT) {
      // Quantized R11/G11/B10 values survive RGBA16F transport exactly; no native alpha is used.
      const data = Uint16Array.from(this.ccLUT.rgba, v => THREE.DataUtils.toHalfFloat(v));
      const tex = new THREE.Data3DTexture(data, 8, 8, 8);
      tex.type = THREE.HalfFloatType; tex.format = THREE.RGBAFormat; tex.colorSpace = THREE.NoColorSpace;
      tex.minFilter = tex.magFilter = THREE.LinearFilter;
      tex.wrapS = tex.wrapT = tex.wrapR = THREE.ClampToEdgeWrapping;
      tex.generateMipmaps = false; tex.unpackAlignment = 1; tex.needsUpdate = true;
      this.lutTexture = tex;
    }
    this.material.uniforms.colorLUT.value = this.lutTexture ?? this.identity;
    this.material.uniforms.ccEnabled.value = !!this.ccLUT;
    this.stats.ccEnabled = !!this.ccLUT;
    this.stats.ccReason = this.ccLUT ? "native enabled Hermit2D RGB packet connected" : post?.ColorGrading?.Enable ? "unsupported/missing ColorGrading curve data" : "ColorGrading disabled/absent";
    this.stats.nativeDOF = post?.DOFGaussian ?? null;
    this.bloom.configure(post?.Bloom, !!e?.rendering);
    this.stats.nativeBloom = this.bloom.packet.setting;
    this.stats.bloomProducer = this.bloom.stats;
    this.bindBloom(null); this.setVignette(null);
  }
  /** Consume a supplied Bloom texture, or the default producer after the scene draw. */
  bindBloom(texture: THREE.Texture | null, mode: 1 | 2 = 1): void {
    this.externalBloom = texture ? { texture, mode } : null;
    this.stats.externalBloom = !!texture;
    this.applyBloom(texture, mode);
  }
  private applyBloom(texture: THREE.Texture | null, mode: 1 | 2 = 1): void {
    this.material.uniforms.bloom.value = texture ?? this.black;
    this.material.uniforms.bloomMode.value = texture ? mode : 0;
    this.stats.bloomBound = !!texture;
  }
  setVignette(value: HDRVignette | null): void {
    const u = this.material.uniforms;
    u.vignetteMode.value = value?.shape ?? 0;
    if (value) {
      u.vignetteParam.value.fromArray(value.param); u.vignetteColor.value.fromArray(value.color);
      u.vignetteStart.value = value.start; u.vignetteRange.value = value.range;
    }
    this.stats.vignetteEnabled = !!value;
  }
  render(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.Camera): void {
    renderer.getDrawingBufferSize(this.size);
    if (this.target.width !== this.size.x || this.target.height !== this.size.y) this.target.setSize(this.size.x, this.size.y);
    const old = renderer.getRenderTarget(), oldTone = renderer.toneMapping, restoreRegion = savePostRegion(renderer);
    this.material.uniforms.exposure.value = this.exposure;
    this.material.uniforms.gammaMode.value = this.gamma;
    try {
      renderer.toneMapping = THREE.NoToneMapping;
      renderer.setRenderTarget(this.target); renderer.render(scene, camera);
      if (this.externalBloom) this.applyBloom(this.externalBloom.texture, this.externalBloom.mode);
      else this.applyBloom(this.bloom.render(renderer, this.target.texture, this.size.x, this.size.y));
      renderer.setRenderTarget(old); renderer.render(this.scene, this.camera);
    } finally {
      restoreRegion(); renderer.toneMapping = oldTone;
    }
  }
  dispose(): void {
    this.target.dispose(); this.material.dispose(); this.triangle.geometry.dispose(); this.bloom.dispose();
    this.lutTexture?.dispose(); this.identity.dispose(); this.black.dispose();
  }
}
