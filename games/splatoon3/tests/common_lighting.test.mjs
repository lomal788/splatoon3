import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {packReadbackSH} from '../client/render/sh_projection.ts';
import {applyForward,applyCommonShadowReceivers} from '../client/render/forward.ts';
import {LightingState} from '../client/render/lighting.ts';
import {NativeShadowState} from '../client/render/shadows.ts';
const bits=v=>new Uint32Array(new Float32Array([v]).buffer)[0];
test('native seven-texel SH packer: 128 original no-stub executions, 3584 f32 bits',()=>{
  const f=JSON.parse(readFileSync(new URL('./fixtures/common_sh_native.json',import.meta.url)));
  assert.equal(f.originalExecutions,128);assert.deepEqual(f.mismatches,[]);assert.equal(f.stubs,0);
  for(const c of f.cases)assert.deepEqual(packReadbackSH(c.texels).map(bits),c.bits);
});
test('common receiver composes with paint shader and shares depth uniforms without changing material model',()=>{
  const scene=new THREE.Scene(),l=new LightingState();l.shadows=new NativeShadowState();
  const mat=new THREE.MeshStandardMaterial();mat.onBeforeCompile=sh=>{sh.uniforms.paintTex={value:'existing'};sh.fragmentShader='//paint\n'+sh.fragmentShader;};
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(),mat);mesh.receiveShadow=true;scene.add(mesh);
  const oldVersion=mat.version;applyCommonShadowReceivers(scene,l);const v=mat.version;applyCommonShadowReceivers(scene,l);
  assert.ok(v>oldVersion);assert.equal(mat.version,v);
  const sh={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};mat.onBeforeCompile(sh,{});
  assert.equal(sh.uniforms.paintTex.value,'existing');assert.equal(sh.uniforms.hShadowMap0,l.shadows.uniforms.hShadowMap0);
  assert.ok(sh.fragmentShader.includes('if(UNROLLED_LOOP_INDEX==0&&receiveShadow)'));assert.ok(sh.fragmentShader.includes('RE_Direct('));
  assert.ok(sh.vertexShader.includes('modelMatrix*hWorld'));l.dispose();l.shadows.dispose();mesh.geometry.dispose();mat.dispose();
});
test('native forward combines bake AO/main mask with dynamic and projection without double Three shadow',()=>{
  const scene=new THREE.Scene(),l=new LightingState();l.shadows=new NativeShadowState();const mat=new THREE.MeshStandardMaterial();
  applyForward(mat,{shader:{archive:'Hoian_UBER',options:{}}},l,null);
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(),mat);mesh.receiveShadow=true;scene.add(mesh);applyCommonShadowReceivers(scene,l);
  assert.equal(mat.userData.commonShadowReceiver,undefined);
  const sh={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};mat.onBeforeCompile(sh,{});
  assert.equal(sh.uniforms.hSH,l.uniforms.hSH);assert.equal(sh.uniforms.hShadowMap1,l.shadows.uniforms.hShadowMap1);
  assert.ok(sh.fragmentShader.includes('hOccAO*hAOMain+hOccBake+(1.-hDynamicShadow'));
  assert.equal(sh.fragmentShader.includes('getShadowMask()'),false);l.dispose();l.shadows.dispose();mesh.geometry.dispose();mat.dispose();
});
