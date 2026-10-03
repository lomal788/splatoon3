import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {inkNearMaxWeights,inkSurfaceGate,inkSurfaceSample,inkSurfaceFrame,NATIVE_LOBBY_INK_STEP} from '../client/render/ink_surface_math.ts';
import {applyInkSurface} from '../client/render/ink_surface.ts';
import {applyForward} from '../client/render/forward.ts';
import {LightingState} from '../client/render/lighting.ts';
const fixture=JSON.parse(readFileSync(new URL('./fixtures/ink_surface_native_read.json',import.meta.url),'utf8'));
const near=(a,b,e=2e-6)=>assert.ok(Math.abs(a-b)<=e,`${a} != ${b}`);

test('native corrected 1714 assignment fixtures: all 88 gates and three channel weights',()=>{
  for(const row of fixture.cases){assert.equal(inkSurfaceGate(Math.max(...row.input.color)),row.expected.active);
    inkNearMaxWeights(row.input.color).forEach((v,i)=>near(v,row.expected.weights[i],0));}
});
test('native corrected 1714 assignment fixtures: rim colors, unnormalized normals and SH direction',()=>{
  for(const row of fixture.cases){const out=inkSurfaceSample(row.input);assert.equal(out.active,row.expected.active);
    if(!out.active)continue;
    for(const key of ['albedo','normal','irradianceNormal','emission'])out[key].forEach((v,i)=>near(v,row.expected[key][i]));
    for(const key of ['thickness','roughness','fresnel'])near(out[key],row.expected[key],1e-6);
  }
});
test('native near maximum retains both and all three tied colors without normalization',()=>{
  assert.deepEqual(inkNearMaxWeights([.5,.5,0]),[1,1,0]);
  assert.deepEqual(inkNearMaxWeights([.5,.5,.5]),[1,1,1]);
  assert.deepEqual(inkNearMaxWeights([.5,.4998,0]),[1,0,0]);
  assert.equal(inkSurfaceGate(.3005000054836273),false);assert.equal(inkSurfaceGate(.3005000352859497),true);
});
test('native world up SH and thickness mix retain nonunit values on wall and floor',()=>{
  const rows=fixture.cases.filter(r=>r.expected.active&&Math.hypot(...r.expected.normal)<.999);
  assert.ok(rows.length>50);
  for(const row of rows){const out=inkSurfaceSample(row.input);assert.ok(Math.abs(Math.hypot(...out.normal)-1)>.00001);
    near(out.irradianceNormal[1],(out.normal[1]-1)*.5+1);}
  assert.deepEqual(NATIVE_LOBBY_INK_STEP,[Math.fround(1/3200),0]);
});
test('surface animation consumes integer GameFrame and radians per frame',()=>{
  assert.deepEqual(inkSurfaceFrame(0),[Math.fround(.95),Math.fround(.75),1.75,0]);
  assert.deepEqual(inkSurfaceFrame(60.8),inkSurfaceFrame(60));
  assert.equal(inkSurfaceFrame(60)[3],1);assert.notEqual(inkSurfaceFrame(60)[2],inkSurfaceFrame(1)[2]);
});

function setup(){const texture=new THREE.DataTexture(new Uint8Array([0,0,0,255]),1,1),mat=new THREE.MeshStandardMaterial(),lighting=new LightingState();
  applyForward(mat,{shader:{archive:'Hoian_UBER',options:{enable_shading:'True'}}},lighting,null);
  const bindings={texture,ink:[[1,0,0],[0,1,0],[0,0,1]],inkBright:[[1,1,0],[0,1,1],[1,0,1]],textureStep:[1/128,0],emission:.125};
  return {mat,texture,lighting,bindings};}
test('same draw hook preserves map and native common light consumers and binds independent InkBright',()=>{
  const f=setup(),bound=applyInkSurface(f.mat,f.bindings),shader={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
  f.mat.onBeforeCompile(shader,{});
  for(const text of ['hReadInk(hInkUV','hF0=vec3(.014999999664723873)','hIrradianceNormal=hInkSurface.irradianceNormal','hDynamic(','hDynamicShadow(','hEvaluateSH(hIrradianceNormal)','hBakeLight'])assert.ok(shader.fragmentShader.includes(text),text);
  assert.ok(shader.fragmentShader.includes('#include <map_fragment>'));assert.ok(shader.vertexShader.includes('attribute vec4 paintUv;'));
  assert.equal(shader.uniforms.hInkTexture.value,f.texture);assert.deepEqual(shader.uniforms.hInkStep.value.toArray(),[1/128,0]);
  assert.deepEqual(shader.uniforms.hInkBright.value[0].toArray(),[1,1,0]);bound.updateFrame(60);assert.equal(bound.uniforms.hInkFrame.value.w,1);
  bound.dispose();f.mat.dispose();f.texture.dispose();f.lighting.dispose();
});
test('hook requires known finite inputs and restores only its own hooks without disposing caller texture',()=>{
  const f=setup(),prior=f.mat.onBeforeCompile,priorKey=f.mat.customProgramCacheKey;let disposed=0;f.texture.addEventListener('dispose',()=>disposed++);
  assert.throws(()=>applyInkSurface(f.mat,{...f.bindings,emission:undefined}),/finite env emission/);
  const bound=applyInkSurface(f.mat,f.bindings);assert.throws(()=>applyInkSurface(f.mat,f.bindings),/already attached/);
  bound.dispose();assert.equal(f.mat.onBeforeCompile,prior);assert.equal(f.mat.customProgramCacheKey,priorKey);assert.equal(disposed,0);
  f.mat.dispose();f.texture.dispose();f.lighting.dispose();
});
test('missing forward shader hook is rejected instead of silently retaining approximate paint',()=>{
  const f=setup(),bound=applyInkSurface(f.mat,f.bindings);assert.throws(()=>f.mat.onBeforeCompile({uniforms:{},vertexShader:'',fragmentShader:''},{}),/anchor missing/);
  bound.dispose();f.mat.dispose();f.texture.dispose();f.lighting.dispose();
});
