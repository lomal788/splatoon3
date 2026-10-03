import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { NativeShadowState, NATIVE_SHADOW_SETTINGS, WEB_SHADOW_POLICY, blendProjectedShadow, projectedShadowDensity, shadowSliceCorners, SHADOW_GLSL } from '../client/render/shadows.ts';

const bits=v=>new Uint32Array(new Float32Array([v]).buffer)[0];
const approx=(a,b,epsilon=1e-6)=>assert.ok(Math.abs(a-b)<epsilon,`${a} != ${b}`);
function rendererFixture(failAt=0) {
  const renderer={target:new THREE.WebGLRenderTarget(17,19),autoClear:false,toneMapping:THREE.ACESFilmicToneMapping,
    shadowMap:{autoUpdate:true},viewport:new THREE.Vector4(2,3,500,400),scissor:new THREE.Vector4(4,5,300,200),scissorTest:true,
    color:new THREE.Color(.2,.3,.4),alpha:.6,draw:[],clears:[],
    getRenderTarget(){return this.target},setRenderTarget(t){this.target=t;this.viewport.set(0,0,t?.width??800,t?.height??600)},
    getViewport(v){return v.copy(this.viewport)},setViewport(v){this.viewport.copy(v)},getScissor(v){return v.copy(this.scissor)},setScissor(v){this.scissor.copy(v)},
    getScissorTest(){return this.scissorTest},setScissorTest(v){this.scissorTest=v},getClearColor(c){return c.copy(this.color)},getClearAlpha(){return this.alpha},
    setClearColor(c,a){this.color.set(c);this.alpha=a},clear(...args){this.clears.push(args)},
    render(scene,camera){this.draw.push({scene,camera,target:this.target,children:[...scene.children]});if(this.draw.length===failAt)throw Error('depth draw failed')},
  };
  return renderer;
}
function setup(failAt=0) {
  const state=new NativeShadowState(),scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(60,16/9,.2,2000);
  camera.position.set(1,3,8);camera.lookAt(0,1,0);camera.updateMatrixWorld(true);
  const caster=new THREE.Mesh(new THREE.BoxGeometry(1,2,1),new THREE.MeshStandardMaterial());caster.castShadow=true;caster.position.set(0,1,0);scene.add(caster);
  const renderer=rendererFixture(failAt);return {state,scene,camera,caster,renderer};
}
function dispose(f) {f.state.dispose();f.renderer.getRenderTarget()?.dispose();f.caster.geometry.dispose();f.caster.material.dispose()}

test('native Common settings keep static 2048 shadow distinct from dynamic two 1024 targets',()=>{
  const state=new NativeShadowState();assert.equal(NATIVE_SHADOW_SETTINGS.cascades,2);
  assert.equal(state.targets.length,2);assert.deepEqual(state.targets.map(t=>[t.width,t.height]),[[1024,1024],[1024,1024]]);
  assert.deepEqual(NATIVE_SHADOW_SETTINGS.nearValues,[1.5,20,250,16]);assert.equal(NATIVE_SHADOW_SETTINGS.far,60);
  assert.equal(state.uniforms.hShadowTexel.value.x,.5/1024);assert.equal(state.uniforms.hShadowTexel.value.y,.5/1024);
  assert.deepEqual(WEB_SHADOW_POLICY.splits,[1.5,20,60]);assert.equal(WEB_SHADOW_POLICY.receivingBias,0);
  for(const t of state.targets){assert.equal(t.depthTexture.type,THREE.UnsignedIntType);assert.equal(t.depthTexture.minFilter,THREE.NearestFilter)}state.dispose();
});

test('native projected Density consumer separately clamps both factors and rounds product to f32',()=>{
  for(const [factor,density,want] of [[-2,2,0],[2,-.1,0],[2,2,1],[.5,.25,.125],[.25,100,.25],[3,0,0]])assert.equal(bits(projectedShadowDensity(factor,density)),bits(want));
  assert.equal(bits(projectedShadowDensity(.3,.7)),bits(Math.fround(Math.fround(.3)*Math.fround(.7))));
  // FCSEL's >=0 branch retains signed zero; Math.max(0,x) would erase it.
  assert.equal(bits(projectedShadowDensity(-0,.5)),0x80000000);assert.equal(bits(projectedShadowDensity(.5,-0)),0x80000000);
});

test('native projected apply preserves f32 operation order and unclamped extrapolation',()=>{
  const a={density:2,rotate:-1,scale:[3,4],trans:[5,6],scrollAnim:[7,8],rotateAnim:9};
  const b={density:-2,rotate:1,scale:[-3,-4],trans:[-5,-6],scrollAnim:[-7,-8],rotateAnim:-9};
  assert.deepEqual(blendProjectedShadow(a,b,0),b);assert.deepEqual(blendProjectedShadow(a,b,1),a);
  assert.equal(blendProjectedShadow(a,b,2).density,6);assert.equal(blendProjectedShadow(a,b,-1).density,-6);
  const x={...a,density:901247.5},y={...b,density:.01953125},t=.30000001192092896;
  assert.equal(bits(blendProjectedShadow(x,y,t).density),bits(Math.fround(Math.fround(y.density)+Math.fround(Math.fround(Math.fround(x.density)-Math.fround(y.density))*Math.fround(t)))));
});

test('Density zero skips unresolved projector; nonzero resource alone invents no matrix or factor',()=>{
  const state=new NativeShadowState();state.configure({rendering:{Shadow:{ProjShadow:{Density:0,Scale:[.05,.05]}}}});
  assert.match(state.stats.projected,/Density=0/);assert.equal(state.uniforms.hProjShadowAvailable.value,0);assert.equal(state.uniforms.hProjShadowDensity.value,0);
  state.configure({rendering:{Shadow:{ProjShadow:{Density:.9}}}});assert.match(state.stats.projected,/unconfirmed/);assert.equal(state.uniforms.hProjShadowAvailable.value,0);state.dispose();
});

test('explicit projected frame retains count/enabled default-texture gates and original matrix rows',()=>{
  const state=new NativeShadowState(),texture=new THREE.Texture(),matrixRows=[[1,2,3,4],[5,6,7,8],[9,10,11,12]];
  const frame={count:1,enabled:true,density:2,factor:.25,matrixRows,texture};state.bindProjectedFrame(frame);
  assert.equal(state.uniforms.hProjShadowAvailable.value,1);assert.equal(state.uniforms.hProjShadowDensity.value,.25);assert.equal(state.uniforms.hProjShadowMap.value,texture);
  assert.deepEqual(state.uniforms.hProjShadowRows.value.map(r=>r.toArray()),matrixRows);
  state.bindProjectedFrame({...frame,enabled:false});assert.equal(state.uniforms.hProjShadowAvailable.value,0);assert.notEqual(state.uniforms.hProjShadowMap.value,texture);
  assert.equal(state.uniforms.hProjShadowDensity.value,.25);state.bindProjectedFrame({...frame,count:0});assert.equal(state.uniforms.hProjShadowDensity.value,0);
  assert.throws(()=>state.bindProjectedFrame({...frame,matrixRows:[[1,2]]}),/Invalid projected/);state.dispose();texture.dispose();
});

test('view slice corners use projection and camera pose, including off-center view offsets',()=>{
  const camera=new THREE.PerspectiveCamera(60,16/9,.2,2000);camera.setViewOffset(1920,1080,300,100,1000,600);camera.position.set(3,4,5);camera.lookAt(-2,1,-4);
  const points=shadowSliceCorners(camera,1.5,20);assert.equal(points.length,8);
  points.forEach((p,i)=>{
    const local=p.clone().applyMatrix4(camera.matrixWorldInverse);approx(-local.z,i<4?1.5:20);
    const clip=p.clone().project(camera);approx(Math.abs(clip.x),1);approx(Math.abs(clip.y),1);
  });
});

test('two caster depth passes restore renderer state and fit every receiver corner',()=>{
  const f=setup(),{state,renderer,camera}=f,oldTarget=renderer.target;state.capture(renderer,f.scene,camera,[.0431,-.5664,-.8230]);
  assert.equal(renderer.draw.length,2);assert.deepEqual(renderer.draw.map(d=>d.target),state.targets);
  assert.equal(state.uniforms.hShadowAvailable.value,1);assert.equal(state.stats.captures,1);assert.equal(state.stats.casters,1);assert.equal(state.stats.proxyDraws,2);
  assert.equal(renderer.target,oldTarget);assert.equal(renderer.autoClear,false);assert.equal(renderer.toneMapping,THREE.ACESFilmicToneMapping);assert.equal(renderer.shadowMap.autoUpdate,true);
  assert.deepEqual(renderer.viewport.toArray(),[2,3,500,400]);assert.deepEqual(renderer.scissor.toArray(),[4,5,300,200]);assert.equal(renderer.scissorTest,true);approx(renderer.alpha,.6);
  for(let i=0;i<2;i++)for(const p of shadowSliceCorners(camera,i?20:1.5,i?60:20)){
    const q=p.clone().applyMatrix4(state.uniforms[`hShadowMatrix${i}`].value);for(const v of q.toArray())assert.ok(v>=-1e-7&&v<=1+1e-7,`cascade ${i} receiver outside ${q.toArray()}`);
  }
  assert.equal(f.caster.material.polygonOffset,false);assert.equal(f.caster.visible,true);dispose(f);
});

test('failed second cascade never supplies partial or stale maps and restores renderer state',()=>{
  const f=setup(2),oldTarget=f.renderer.target;assert.throws(()=>f.state.capture(f.renderer,f.scene,f.camera,[0,-1,-1]),/depth draw failed/);
  assert.equal(f.state.uniforms.hShadowAvailable.value,0);assert.equal(f.state.stats.captures,0);assert.equal(f.renderer.target,oldTarget);assert.equal(f.renderer.shadowMap.autoUpdate,true);
  assert.equal(f.renderer.scissorTest,true);assert.deepEqual(f.renderer.viewport.toArray(),[2,3,500,400]);dispose(f);
});

test('only visible castShadow meshes render; static baked receivers and hidden parents do not cast',()=>{
  const f=setup(),staticMesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());staticMesh.receiveShadow=true;f.scene.add(staticMesh);
  const hidden=new THREE.Group(),hiddenCaster=f.caster.clone();hiddenCaster.castShadow=true;hidden.add(hiddenCaster);hidden.visible=false;f.scene.add(hidden);
  f.state.capture(f.renderer,f.scene,f.camera,[0,-1,-1]);assert.equal(f.state.stats.casters,1);
  f.caster.visible=false;f.state.capture(f.renderer,f.scene,f.camera,[0,-1,-1]);assert.equal(f.state.stats.casters,0);assert.equal(f.state.uniforms.hShadowAvailable.value,0);assert.equal(f.state.stats.proxyDraws,0);
  f.caster.visible=true;f.state.capture(f.renderer,f.scene,f.camera,[0,-1,-1]);assert.equal(f.state.stats.casters,1);assert.equal(f.state.uniforms.hShadowAvailable.value,1);
  dispose(f);staticMesh.geometry.dispose();staticMesh.material.dispose();
});

test('depth proxies preserve cutout maps, displacement, side, transforms and native polygon settings without source mutation',()=>{
  const f=setup(),m=f.caster.material,map=new THREE.Texture(),alpha=new THREE.Texture(),disp=new THREE.Texture();
  Object.assign(m,{map,alphaMap:alpha,alphaTest:.42,opacity:.8,side:THREE.DoubleSide,displacementMap:disp,displacementScale:2,displacementBias:-1});
  f.caster.position.set(11,2,-4);f.state.capture(f.renderer,f.scene,f.camera,[0,-1,-1]);const proxy=f.renderer.draw[0].children[0],depth=proxy.material;
  assert.equal(proxy.geometry,f.caster.geometry);assert.deepEqual(proxy.matrix.toArray(),f.caster.matrixWorld.toArray());
  assert.equal(depth.map,map);assert.equal(depth.alphaMap,alpha);assert.equal(depth.alphaTest,.42);assert.equal(depth.opacity,.8);assert.equal(depth.side,THREE.DoubleSide);
  assert.equal(depth.displacementMap,disp);assert.equal(depth.displacementScale,2);assert.equal(depth.displacementBias,-1);
  assert.equal(depth.polygonOffsetFactor,5);assert.equal(depth.polygonOffsetUnits,.3);assert.equal(m.polygonOffset,false);
  dispose(f);map.dispose();alpha.dispose();disp.dispose();
});

test('SkinnedMesh and morph proxies retain live skeleton, binding and morph influences',()=>{
  const f=setup();f.caster.castShadow=false;
  const geometry=new THREE.BoxGeometry(1,2,1),n=geometry.attributes.position.count;
  geometry.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(new Uint16Array(n*4),4));const weights=new Float32Array(n*4);for(let i=0;i<n;i++)weights[i*4]=1;
  geometry.setAttribute('skinWeight',new THREE.Float32BufferAttribute(weights,4));geometry.morphAttributes.position=[geometry.attributes.position.clone()];
  const skin=new THREE.SkinnedMesh(geometry,new THREE.MeshStandardMaterial()),bone=new THREE.Bone();skin.add(bone);skin.bind(new THREE.Skeleton([bone]));skin.castShadow=true;
  skin.position.set(4,2,-3);skin.morphTargetInfluences[0]=.7;bone.position.set(0,.5,0);f.scene.add(skin);f.scene.updateMatrixWorld(true);skin.skeleton.update();
  f.state.capture(f.renderer,f.scene,f.camera,[0,-1,-1]);const proxy=f.renderer.draw[0].children[0];
  assert.equal(proxy.isSkinnedMesh,true);assert.equal(proxy.skeleton,skin.skeleton);assert.equal(proxy.morphTargetInfluences,skin.morphTargetInfluences);
  assert.deepEqual(proxy.bindMatrix.toArray(),skin.bindMatrix.toArray());assert.deepEqual(proxy.matrix.toArray(),skin.matrixWorld.toArray());
  dispose(f);geometry.dispose();skin.material.dispose();
});

test('shadow shaders expose separate dynamic illumination and projected occlusion rather than multiplying indirect light',()=>{
  assert.match(SHADOW_GLSL,/float hDynamicShadow\(vec3 worldPos,float positiveViewDepth\)/);
  assert.match(SHADOW_GLSL,/hProjShadowDensity\*\(1\.-texture2D/);assert.match(SHADOW_GLSL,/WEB_SHADOW_POLICY/);
  assert.doesNotMatch(SHADOW_GLSL,/getShadowMask|reflectedLight/);
});
