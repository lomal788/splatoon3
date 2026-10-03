// Scene-depth supply for FX soft-particle consumers. The separate web prepass is
// a renderer adapter; original draw-path scheduling is still unconfirmed.
import * as THREE from "three";

export class FxSceneDepth {
  readonly target: THREE.WebGLRenderTarget;
  readonly uniforms: Record<string, THREE.IUniform>;
  private readonly size = new THREE.Vector2();
  captures = 0;

  constructor() {
    const depth = new THREE.DepthTexture(1, 1, THREE.UnsignedIntType);
    depth.minFilter = depth.magFilter = THREE.NearestFilter;
    this.target = new THREE.WebGLRenderTarget(1, 1, { depthTexture: depth, depthBuffer: true });
    this.target.texture.name = "fx.scene-depth-color-unused";
    depth.name = "fx.scene-depth";
    this.uniforms = {
      uSceneDepth: { value: depth },
      uDepthNear: { value: .2 }, uDepthFar: { value: 2000 },
      uDepthResolution: { value: new THREE.Vector2(1, 1) },
      uDepthAvailable: { value: 0 },
    };
  }

  capture(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.PerspectiveCamera): void {
    const fx = scene.getObjectByName("fx");
    this.uniforms.uDepthAvailable.value = 0;
    if (!fx || !fx.visible || fx.children.length === 0 || fx.userData.needsSceneDepth === false) return;
    renderer.getDrawingBufferSize(this.size);
    if (this.target.width !== this.size.x || this.target.height !== this.size.y) this.target.setSize(this.size.x, this.size.y);
    this.uniforms.uDepthNear.value = camera.near;
    this.uniforms.uDepthFar.value = camera.far;
    this.uniforms.uDepthResolution.value.copy(this.size);
    const oldTarget = renderer.getRenderTarget(), oldTone = renderer.toneMapping;
    const oldAutoClear = renderer.autoClear, oldShadowUpdate = renderer.shadowMap.autoUpdate;
    const oldVisible = fx.visible;
    try {
      // Keep original web material alpha/discard during depth generation. Hide
      // FX to avoid sampling from, or occluding against, their own depth pass.
      fx.visible = false;
      renderer.toneMapping = THREE.NoToneMapping;
      renderer.autoClear = true;
      renderer.shadowMap.autoUpdate = false;
      renderer.setRenderTarget(this.target);
      renderer.render(scene, camera);
      this.captures++;
      this.uniforms.uDepthAvailable.value = 1;
    } finally {
      fx.visible = oldVisible;
      renderer.setRenderTarget(oldTarget);
      renderer.toneMapping = oldTone;
      renderer.autoClear = oldAutoClear;
      renderer.shadowMap.autoUpdate = oldShadowUpdate;
    }
  }
  dispose(): void { this.target.dispose(); }
}
