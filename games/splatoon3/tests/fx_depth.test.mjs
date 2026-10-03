import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { FxSceneDepth } from '../client/render/fx_depth.ts';

function fixture(fail = false) {
  const depth = new FxSceneDepth(), scene = new THREE.Scene(), fx = new THREE.Group();
  fx.name = 'fx'; fx.add(new THREE.Object3D()); scene.add(fx);
  const camera = new THREE.PerspectiveCamera(55, 1, .4, 300);
  const oldTarget = new THREE.WebGLRenderTarget(3, 4), draw = [];
  const renderer = { toneMapping: THREE.ACESFilmicToneMapping, autoClear: false, shadowMap: { autoUpdate: true },
    target: oldTarget, getRenderTarget(){return this.target}, setRenderTarget(t){this.target=t},
    getDrawingBufferSize(v){return v.set(640,480)},
    render(s,c){draw.push({fxVisible:fx.visible,target:this.target,scene:s,camera:c});if(fail)throw Error('fixture draw failure')},
  };
  return {depth,scene,fx,camera,renderer,oldTarget,draw};
}

test('FX depth captures scene without sampling its own particles; restore render state', () => {
  const f=fixture();f.depth.capture(f.renderer,f.scene,f.camera);
  assert.equal(f.draw.length,1);assert.equal(f.draw[0].fxVisible,false);
  assert.equal(f.draw[0].target,f.depth.target);assert.equal(f.fx.visible,true);
  assert.equal(f.renderer.target,f.oldTarget);assert.equal(f.renderer.autoClear,false);
  assert.equal(f.renderer.toneMapping,THREE.ACESFilmicToneMapping);assert.equal(f.renderer.shadowMap.autoUpdate,true);
  assert.equal(f.depth.uniforms.uDepthNear.value,.4);assert.equal(f.depth.uniforms.uDepthFar.value,300);
  assert.deepEqual(f.depth.uniforms.uDepthResolution.value.toArray(),[640,480]);
  assert.equal(f.depth.target.depthTexture.type,THREE.UnsignedIntType);
  assert.equal(f.depth.uniforms.uDepthAvailable.value,1);f.depth.dispose();f.oldTarget.dispose();
});

test('FX depth failed draw never marks texture valid and still restores state', () => {
  const f=fixture(true);assert.throws(()=>f.depth.capture(f.renderer,f.scene,f.camera),/fixture draw failure/);
  assert.equal(f.depth.uniforms.uDepthAvailable.value,0);assert.equal(f.fx.visible,true);
  assert.equal(f.renderer.target,f.oldTarget);assert.equal(f.renderer.autoClear,false);
  assert.equal(f.renderer.shadowMap.autoUpdate,true);f.depth.dispose();f.oldTarget.dispose();
});

test('FX-free or hidden scene skips prepass rather than supplying stale depth', () => {
  const f=fixture();f.fx.visible=false;f.depth.capture(f.renderer,f.scene,f.camera);
  assert.equal(f.draw.length,0);assert.equal(f.depth.uniforms.uDepthAvailable.value,0);
  f.fx.visible=true;f.fx.clear();f.depth.capture(f.renderer,f.scene,f.camera);assert.equal(f.draw.length,0);
  f.depth.dispose();f.oldTarget.dispose();
});
