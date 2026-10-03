import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {BLOOM_NATIVE,bloomPacket,bloomExpand,bloomMask,NativeBloom} from '../client/render/bloom.ts';
import {HDRCompose} from '../client/render/post.ts';
const native=JSON.parse(readFileSync(new URL('../../../../analysis/port_common_r6/post/native_blocks.json',import.meta.url),'utf8'));
const defaults=JSON.parse(readFileSync(new URL('../../../../analysis/port_common_r6/post/default_bloom.json',import.meta.url),'utf8'));
const bits=v=>new Uint32Array(new Float32Array([v]).buffer)[0];
test('native UBO execution fixtures: exact f32 threshold, range, clamp, intensity and scale',()=>{
 for(const x of native.ubo_fixtures){const p=bloomPacket(x.input,x.input.scale);assert.deepEqual(p.weight.map(bits),x.weight.map(bits));assert.deepEqual(p.threshold.map(bits),x.threshold.map(bits));}
 assert.deepEqual(BLOOM_NATIVE.weight.map(bits),native.weights.map(bits));
 assert.equal(bloomPacket().threshold[0],5);assert.equal(bloomPacket().threshold[3],10000);
});
test('native Expand execution fixtures preserve negative/boundary values and f32 order',()=>{
 for(const x of native.expand_fixtures)assert.deepEqual(bloomExpand(x.Expand).map(bits),[x.colors[3],x.colors[7],x.colors[11],x.colors[15]].map(bits));
 assert.deepEqual(bloomExpand(1),[.25,.25,.5,0]);
});
test('mask uses raw HDR alpha and native ratio clamp; black finite limit explicitly web-only',()=>{
 assert.deepEqual(bloomMask([0,0,0,1]),[0,0,0,0]);
 assert.deepEqual(bloomMask([2,2,2,1]),[0,0,0,0]);
 const a=bloomMask([6,6,6,1]);for(let k=0;k<3;k++)assert.ok(Math.abs(a[k]-5)<.000002);
 const b=bloomMask([2,2,2,0]);assert.ok(b[0]>0); // Native alpha participates in threshold subtraction.
 assert.deepEqual(bloomMask([6,6,6,1],bloomPacket({EnableClampedLuminance:false})),[6,6,6,1]);
 assert.equal(bloomMask([20000,20000,20000,1],bloomPacket({EnableClampedLuminance:false}))[0],10000);
});

test('DefaultDay AAMP overrides old_calc ctor branch and depth-clamp variant has identical native code',()=>{
 assert.equal(BLOOM_NATIVE.oldCalc,defaults.values.enable_old_calc.value);
 assert.equal(BLOOM_NATIVE.depthClamp,defaults.values.enable_depth_clamp.value);
 assert.equal(BLOOM_NATIVE.editType,defaults.values.edit_type.value);assert.equal(BLOOM_NATIVE.expand,defaults.values.expand.value);
 assert.equal(BLOOM_NATIVE.finalBlend,defaults.values.finalblend.value);
 assert.equal(defaults.default_mask_variant,129);assert.equal(defaults.pixel_code_identical,true);assert.equal(defaults.vertex_code_identical,true);
});
test('default pipeline draws mask + four reduce/H/V + inverse compose, sizes align before quarter',()=>{
 const b=new NativeBloom();b.configure();let target=null;const sizes=[],old={id:'old'};target=old;
 const renderer={autoClear:true,getRenderTarget:()=>target,setRenderTarget:t=>{target=t},render:()=>sizes.push([target.width,target.height])};
 const t=b.render(renderer,new THREE.Texture(),1001,563);assert.equal(t,b.levels[0].texture);
 assert.equal(sizes.length,16);assert.deepEqual(b.stats.sizes,[[251,141],[125,70],[62,35],[31,17],[15,8]]);
 assert.equal(target,old);assert.equal(renderer.autoClear,true);assert.equal(b.stats.frames,1);
 assert.deepEqual(b.composeMaterial.uniforms.sourceColor.value.toArray(),[1,1,1]);
 assert.deepEqual(b.composeMaterial.uniforms.destinationColor.value.toArray(),[.25,.25,.25]);
 b.dispose();
});
test('native disable, small viewport, unsupported depth variants and reconfigure preserve gate',()=>{
 const b=new NativeBloom();for(const setting of [{Enable:false},{EnableDepthScaling:true},{EnableDepthOffset:true},{Threshold:NaN}]){b.configure(setting);assert.equal(b.enabled,false);}
 b.configure();assert.equal(b.render({},new THREE.Texture(),63,64),null);b.configure(undefined,false);assert.equal(b.enabled,false);b.configure();assert.equal(b.enabled,true);b.dispose();
});
test('producer restores target and autoClear after draw failure',()=>{
 const b=new NativeBloom();b.configure();let target={id:'prior'},prior=target,draws=0;
 const r={autoClear:true,getRenderTarget:()=>target,setRenderTarget:t=>{target=t},render:()=>{if(++draws===4)throw Error('fixture');}};
 assert.throws(()=>b.render(r,new THREE.Texture(),640,360),/fixture/);assert.equal(target,prior);assert.equal(r.autoClear,true);b.dispose();
});
test('external compose texture persists across scene frames and configure resets its lifetime',()=>{
 const p=new HDRCompose();p.configure({rendering:{PostEffect:{}}});const tex=new THREE.Texture();p.bindBloom(tex,2);
 let target=null,draws=0;const r={toneMapping:0,autoClear:true,getRenderTarget:()=>target,setRenderTarget:t=>{target=t},getDrawingBufferSize:v=>v.set(128,64),render:()=>draws++};
 p.render(r,new THREE.Scene(),new THREE.Camera());p.render(r,new THREE.Scene(),new THREE.Camera());
 assert.equal(draws,4);assert.equal(p.material.uniforms.bloom.value,tex);assert.equal(p.material.uniforms.bloomMode.value,2);assert.equal(p.bloom.stats.frames,0);
 p.configure({rendering:{PostEffect:{}}});p.render(r,new THREE.Scene(),new THREE.Camera());
 assert.equal(p.bloom.stats.frames,1);assert.equal(p.material.uniforms.bloomMode.value,1);p.dispose();tex.dispose();
});
test('post viewport/scissor/default scissorTest are restored on draw failure',()=>{
 const p=new HDRCompose();p.configure({rendering:{PostEffect:{}}});let target=null,view=new THREE.Vector4(2,3,111,55),scissor=new THREE.Vector4(4,5,77,33),test=true;
 const originalView=view.clone(),originalScissor=scissor.clone();
 const r={toneMapping:0,autoClear:true,getRenderTarget:()=>target,setRenderTarget:t=>{target=t},getDrawingBufferSize:v=>v.set(128,64),getViewport:v=>v.copy(view),setViewport:v=>{view.copy(v)},getScissor:v=>v.copy(scissor),setScissor:v=>{scissor.copy(v)},getScissorTest:()=>test,setScissorTest:v=>{test=v},render:()=>{view.set(0,0,1,1);scissor.set(0,0,1,1);test=false;throw Error('fixture region')}};
 assert.throws(()=>p.render(r,new THREE.Scene(),new THREE.Camera()),/fixture region/);assert.deepEqual(view,originalView);assert.deepEqual(scissor,originalScissor);assert.equal(test,true);assert.equal(target,null);p.dispose();
});
