// Native 36ED93C / 36F1E4C / 36F2CD8 and agl bloom_mask/reduce/gaussian/compose.
import * as THREE from "three";
const F = Math.fround;
/** Preserve the renderer's default viewport/scissor definitions and target-owned active region. */
export function savePostRegion(renderer: THREE.WebGLRenderer): () => void {
  const viewport = typeof renderer.getViewport === "function" ? renderer.getViewport(new THREE.Vector4()) : null;
  const scissor = typeof renderer.getScissor === "function" ? renderer.getScissor(new THREE.Vector4()) : null;
  const test = typeof renderer.getScissorTest === "function" ? renderer.getScissorTest() : null;
  const t = renderer.getRenderTarget();
  return () => {
    if (viewport) renderer.setViewport(viewport);
    if (scissor) renderer.setScissor(scissor);
    if (test !== null) renderer.setScissorTest(test);
    renderer.setRenderTarget(t);
  };
}
export const BLOOM_NATIVE = Object.freeze({
  weight: [0.2989116907119751, 0.5866104364395142, 0.11447788774967194],
  offsets: [1.3846, 3.23077], taps: [.31621623, .07027027, .22702703],
  rgbSafetyCap: 10000, editType: 1, oldCalc: false, depthClamp: true, expand: 1, finalBlend: 1,
});
export interface BloomSetting {
  Enable?: boolean; Threshold?: number; ThresholdRange?: number; Intensity?: number;
  EnableClampedLuminance?: boolean; ClampedLuminance?: number;
  ComposeColor?: { R?: number; G?: number; B?: number; A?: number } | number[];
  EnableDepthScaling?: boolean; EnableDepthOffset?: boolean;
}
export function bloomPacket(setting?: BloomSetting, scale = 1) {
  const p = { Enable: true, Threshold: 4, ThresholdRange: 1, Intensity: 1, EnableClampedLuminance: true, ClampedLuminance: 5, ...setting };
  const den = F(F(scale) * F(p.ThresholdRange));
  const inv = den <= 0 ? 0 : F(1 / den);
  const weight = [...BLOOM_NATIVE.weight.map(v => F(inv * v)), F(F(F(scale) * F(-p.Threshold)) * inv)];
  const threshold = [F(inv * F(p.ClampedLuminance)), 0, F(p.Intensity), 10000];
  return { setting: p, weight, threshold };
}
export function bloomGameApply(next?: BloomSetting, prev: BloomSetting | undefined = next, t = 1): BloomSetting {
  const d = { Enable: true, Threshold: 4, ThresholdRange: 1, Intensity: 1, EnableClampedLuminance: true, ClampedLuminance: 5 };
  const a = { ...d, ...next }, b = { ...d, ...prev };
  const lerp = (x: number, y: number) => F(F(x) + F(F(F(y) - F(x)) * F(t)));
  return { ...a, Threshold: lerp(b.Threshold, a.Threshold), ThresholdRange: lerp(b.ThresholdRange, a.ThresholdRange), Intensity: lerp(b.Intensity, a.Intensity), ClampedLuminance: lerp(b.ClampedLuminance, a.Intensity) };
}
export function bloomExpand(value: number): number[] {
  const x = F(value); let a = F(x * 3), b = F(a - 1);
  if (x >= F(1 / 3)) { a = 1; } else { b = 0; }
  const inv = F(1 / F(F(F(a + 1) + b) + 0));
  return [inv, F(a * inv), F(b * inv), F(inv * 0)];
}
export function bloomMask(rgba: number[], packet = bloomPacket()): number[] {
  const c = rgba.slice(0, 3).map(v => Math.min(v, packet.threshold[3]));
  const w = packet.weight;
  const l = F(c[2] * w[2] + F(c[1] * w[1] + F(c[0] * w[0])));
  // Web finite black limit; native GPU RCP(0)/SAT behavior is not emulated here.
  const ratio = packet.setting.EnableClampedLuminance ? l === 0 ? 0 : Math.min(1, Math.max(0, F(packet.threshold[0] / l))) : 1;
  const gain = F(F(ratio * Math.min(1, Math.max(0, F(rgba[3] * w[3] + l)))) * packet.threshold[2]);
  return [...c, rgba[3]].map(v => F(v * gain));
}
function target(): THREE.WebGLRenderTarget {
  const t = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, depthBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
  t.texture.colorSpace = THREE.NoColorSpace; t.texture.generateMipmaps = false;
  return t;
}
const vertex = "out vec2 vUv; void main(){vUv=position.xy*.5+.5;gl_Position=vec4(position.xy,0.,1.);}";
function material(fragment: string, uniforms: Record<string, THREE.IUniform>): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({ glslVersion: THREE.GLSL3, uniforms, vertexShader: vertex, fragmentShader: fragment, depthTest: false, depthWrite: false, toneMapped: false });
}
export class NativeBloom {
  readonly maskTarget = target();
  readonly levels = Array.from({ length: 4 }, () => target());
  readonly scratch = Array.from({ length: 4 }, () => target());
  readonly maskMaterial = material(String.raw`
    uniform sampler2D source; uniform vec4 weight; uniform vec4 threshold; uniform bool clamped;
    in vec2 vUv; out vec4 result;
    void main(){vec4 h=texture(source,vUv);vec3 c=min(h.rgb,vec3(threshold.w));
      float l=c.r*weight.x+c.g*weight.y+c.b*weight.z;
      float ratio=clamped?(l==0.?0.:clamp(threshold.x/l,0.,1.)):1.;
      float g=ratio*clamp(h.a*weight.w+l,0.,1.)*threshold.z;
      result=vec4(c,h.a)*g;}
  `, { source: { value: null }, weight: { value: new THREE.Vector4() }, threshold: { value: new THREE.Vector4() }, clamped: { value: true } });
  readonly reduceMaterial = material("uniform sampler2D source; in vec2 vUv; out vec4 result; void main(){result=texture(source,vUv);}", { source: { value: null } });
  readonly gaussianMaterial = material(String.raw`
    uniform sampler2D source; uniform vec2 stepUV; in vec2 vUv; out vec4 result;
    void main(){vec4 a=texture(source,vUv-stepUV*1.3846)*.31621623;
      a=texture(source,vUv-stepUV*3.23077)*.07027027+a;
      a=texture(source,vUv)*.22702703+a;
      a=texture(source,vUv+stepUV*1.3846)*.31621623+a;
      result=texture(source,vUv+stepUV*3.23077)*.07027027+a;}
  `, { source: { value: null }, stepUV: { value: new THREE.Vector2() } });
  readonly composeMaterial = material(String.raw`
    uniform sampler2D source; uniform sampler2D destination; uniform vec3 sourceColor; uniform vec3 destinationColor;
    in vec2 vUv; out vec4 result;
    void main(){result=vec4(texture(source,vUv).rgb*sourceColor+texture(destination,vUv).rgb*destinationColor,0.);}
  `, { source: { value: null }, destination: { value: null }, sourceColor: { value: new THREE.Vector3() }, destinationColor: { value: new THREE.Vector3() } });
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.Camera();
  private readonly triangle: THREE.Mesh;
  packet = bloomPacket();
  enabled = false;
  readonly stats: Record<string, unknown> = { nativeGPUEquivalent: false, frames: 0, draws: 0, native: BLOOM_NATIVE,
    policy: "RGBA16F transport; linear/clamp sampler; native scale=1 constructor branch and DefaultDay edit_type=1/enable_old_calc=false; live view gates unverified", dof: "separate inactive pass" };
  constructor() {
    this.triangle = new THREE.Mesh(new THREE.BufferGeometry().setAttribute("position", new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3)), this.maskMaterial);
    this.triangle.frustumCulled = false; this.scene.add(this.triangle);
  }
  configure(setting?: BloomSetting, sceneAvailable = true): void {
    this.packet = bloomPacket(bloomGameApply(setting));
    const p = this.packet.setting;
    this.enabled = sceneAvailable && p.Enable && !p.EnableDepthScaling && !p.EnableDepthOffset && [...this.packet.weight, ...this.packet.threshold].every(Number.isFinite);
    this.maskMaterial.uniforms.weight.value.fromArray(this.packet.weight);
    this.maskMaterial.uniforms.threshold.value.fromArray(this.packet.threshold);
    this.maskMaterial.uniforms.clamped.value = p.EnableClampedLuminance;
    this.stats.enabled = this.enabled; this.stats.setting = p;
    this.stats.reason = !sceneAvailable ? "scene absent" : !p.Enable ? "native Enable=false" : p.EnableDepthScaling || p.EnableDepthOffset ? "unsupported native depth variant; disabled" : "native default mask / four reduce-H-V levels / inverse compose connected";
  }
  render(renderer: THREE.WebGLRenderer, source: THREE.Texture, width: number, height: number): THREE.Texture | null {
    if (!this.enabled || width < 64 || height < 64) { this.stats.lastActive = false; return null; }
    const restoreRegion = savePostRegion(renderer), oldAuto = renderer.autoClear;
    const w = ((Math.trunc(width) + 3) & ~3) >>> 2, h = ((Math.trunc(height) + 3) & ~3) >>> 2;
    this.maskTarget.setSize(w, h);
    const draw = (m: THREE.ShaderMaterial, t: THREE.WebGLRenderTarget) => { this.triangle.material = m; renderer.setRenderTarget(t); renderer.render(this.scene, this.camera); this.stats.draws = Number(this.stats.draws) + 1; };
    try {
      renderer.autoClear = false;
      this.maskMaterial.uniforms.source.value = source; draw(this.maskMaterial, this.maskTarget);
      let previous = this.maskTarget.texture;
      for (let i = 0; i < 4; i++) {
        const lw = Math.max(1, w >>> (i + 1)), lh = Math.max(1, h >>> (i + 1)), level = this.levels[i], scratch = this.scratch[i];
        level.setSize(lw, lh); scratch.setSize(lw, lh);
        this.reduceMaterial.uniforms.source.value = previous; draw(this.reduceMaterial, level);
        this.gaussianMaterial.uniforms.source.value = level.texture; this.gaussianMaterial.uniforms.stepUV.value.set(1 / lw, 0); draw(this.gaussianMaterial, scratch);
        this.gaussianMaterial.uniforms.source.value = scratch.texture; this.gaussianMaterial.uniforms.stepUV.value.set(0, 1 / lh); draw(this.gaussianMaterial, level);
        previous = level.texture;
      }
      const weights = bloomExpand(1), c = this.packet.setting.ComposeColor;
      const base = Array.isArray(c) ? c : c ? [c.R ?? 1, c.G ?? 1, c.B ?? 1, c.A ?? 1] : [1, 1, 1, 1];
      for (let i = 3; i > 0; i--) {
        const u = this.composeMaterial.uniforms;
        u.source.value = this.levels[i].texture; u.destination.value = this.levels[i - 1].texture;
        u.sourceColor.value.set(...[0, 1, 2].map(k => i === 1 ? base[k] * base[3] : i === 2 ? 1 : weights[i]) as [number, number, number]);
        u.destinationColor.value.set(...[0, 1, 2].map(k => weights[i - 1] * (i === 1 ? base[k] * base[3] : 1)) as [number, number, number]);
        draw(this.composeMaterial, this.scratch[i - 1]);
        [this.levels[i - 1], this.scratch[i - 1]] = [this.scratch[i - 1], this.levels[i - 1]];
      }
      this.stats.frames = Number(this.stats.frames) + 1; this.stats.lastActive = true;
      this.stats.sizes = [[w, h], ...this.levels.map(t => [t.width, t.height])];
      return this.levels[0].texture;
    } finally { restoreRegion(); renderer.autoClear = oldAuto; }
  }
  dispose(): void { for (const t of [this.maskTarget, ...this.levels, ...this.scratch]) t.dispose(); for (const m of [this.maskMaterial, this.reduceMaterial, this.gaussianMaterial, this.composeMaterial]) m.dispose(); this.triangle.geometry.dispose(); }
}
