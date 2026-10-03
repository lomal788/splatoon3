import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {HDRCompose} from '../client/render/post.ts';
import {colorCorrectionPacket,colorCorrectionLUT,ccHSV,encodeUnsignedFloat,decodeUnsignedFloat,packRGB111110,unpackRGB111110,sampleColorLUT} from '../client/render/post_math.ts';
const fixture=JSON.parse(readFileSync(new URL('./fixtures/post_native_port.json',import.meta.url),'utf8'));
const bits=x=>new Uint32Array(new Float32Array([x]).buffer)[0];
const packet=colorCorrectionPacket(fixture.setting);
const env={rendering:{PostEffect:{ColorGrading:fixture.setting,HDRExposure:{ExposureType:'ManualExposure',ManualExposure:{Value:1}},DOFGaussian:{Level:.5,Start:484,End:900,FarCancel:20}}}};
test('native CPU CC packet: headers, HSV, 24 RGB bits, RGB terminal duplicate, Gamma/count',()=>{
 assert.deepEqual(packet.headers,fixture.headers);assert.equal(packet.count,fixture.count);
 assert.deepEqual(packet.params[0].map(bits),fixture.params[0].map(bits));
 for(let i=1;i<=9;i++)assert.deepEqual(packet.params[i].slice(0,3).map(bits),fixture.params[i].slice(0,3).map(bits));
 assert.deepEqual(packet.params[10],fixture.params[10]);
});
test('unsupported or disabled grading cannot silently invent a LUT',()=>{
 assert.equal(colorCorrectionPacket(undefined),null);
 assert.equal(colorCorrectionPacket({...fixture.setting,Enable:false}),null);
 assert.equal(colorCorrectionPacket({...fixture.setting,CurveColorR:{Type:'Unknown',Data:[0,0,0,1,1,1]}}),null);
 assert.equal(colorCorrectionPacket({...fixture.setting,CurveColorR:{Type:'Hermit2D',Data:[0,0,0,0,1,1]}}),null);
 assert.equal(colorCorrectionPacket({...fixture.setting,Hue:NaN}),null);
});
test('native shader HSV min-channel ties cover all six sectors and neutral gate',()=>{
 const cases=[[1,0,0],[1,1,0],[0,1,0],[0,1,1],[0,0,1],[1,0,1],[.5,.5,.5],[0,0,0]];
 for(const c of cases){const out=ccHSV(c,[0,1,1.0625,0]);for(let i=0;i<3;i++)assert.ok(Math.abs(out[i]-c[i]*1.0625)<.0005);}
 // Native +1000 wraps hue to an f32 grid: preserve it instead of replacing with RGB*Value.
 assert.notDeepEqual(ccHSV([.9,.33,.1],[0,1,1.0625,0]),[.9,.33,.1].map(v=>Math.fround(v*1.0625)));
});
test('RGB11/11/10 nearest-even web policy: exponents, mantissas, zeros/subnormals/overflow',()=>{
 assert.equal(encodeUnsignedFloat(1,6),15<<6);assert.equal(encodeUnsignedFloat(1,5),15<<5);
 assert.equal(encodeUnsignedFloat(1+1/128,6),15<<6); // exact halfway, even lower
 assert.equal(encodeUnsignedFloat(1+3/128,6),(15<<6)+2); // even upper
 assert.equal(encodeUnsignedFloat(1+1/64,5),15<<5);
 assert.equal(decodeUnsignedFloat(1,6),2**-20);assert.equal(decodeUnsignedFloat(1,5),2**-19);
 assert.equal(encodeUnsignedFloat(2**-14,6),64);
 assert.equal(encodeUnsignedFloat(-1,6),0);assert.equal(encodeUnsignedFloat(-0,6),0);
 assert.equal(encodeUnsignedFloat(Infinity,6),31<<6);assert.equal(encodeUnsignedFloat(1e9,5),31<<5);
 assert.ok(Number.isNaN(decodeUnsignedFloat(encodeUnsignedFloat(NaN,6),6)));
 assert.deepEqual(unpackRGB111110(packRGB111110([1,.5,.25])),[1,.5,.25]);
});
test('8 cubed RGB LUT has independent B-axis and survives RGBA16F transport without another quantization',()=>{
 const lut=colorCorrectionLUT(packet);assert.equal(lut.packed.length,512);assert.equal(lut.rgba.length,2048);
 assert.deepEqual([...lut.rgba.slice(0,4)],[0,0,0,1]);
 assert.deepEqual([...lut.rgba.slice(-4)],[1,1,1,1]);
 for(let i=0;i<lut.packed.length;i++)assert.deepEqual(unpackRGB111110(lut.packed[i]),[...lut.rgba.slice(i*4,i*4+3)]);
 for(const v of lut.rgba)assert.equal(bits(THREE.DataUtils.fromHalfFloat(THREE.DataUtils.toHalfFloat(v))),bits(v));
 assert.ok(lut.rgba[(8*8*7)*4+2]>.9);
 // Native f32 +1000 hue wrap leaves a small R component for pure blue.
 assert.ok(lut.rgba[(8*8*7)*4]>0&&lut.rgba[(8*8*7)*4]<.0005);
 assert.ok(lut.rgba[7*4]>.9);assert.equal(lut.rgba[7*4+2],0);
});
test('declared web linear/clamp reference reproduces every texel center and bounded edges',()=>{
 const lut=colorCorrectionLUT(packet);
 for(let z=0;z<8;z++)for(let y=0;y<8;y++)for(let x=0;x<8;x++){
  const i=(x+8*(y+8*z))*4,c=sampleColorLUT(lut,[x/7,y/7,z/7]);
  for(let k=0;k<3;k++)assert.ok(Math.abs(c[k]-lut.rgba[i+k])<1e-12);
 }
 assert.deepEqual(sampleColorLUT(lut,[-1,-4,-2]),[0,0,0]);
 assert.deepEqual(sampleColorLUT(lut,[2,3,4]),[1,1,1]);
});
test('actual post configure consumes Lby grading and preserves HDR aliases; no invented Bloom/DOF/vignette',()=>{
 const post=new HDRCompose();post.configure(env);const u=post.material.uniforms;
 assert.equal(post.exposure,2);assert.equal(post.gamma,1);assert.equal(u.hdr.value,post.target.texture);
 assert.equal(u.ccEnabled.value,true);assert.equal(u.colorLUT.value.image.width,8);assert.equal(u.colorLUT.value.image.depth,8);
 assert.equal(u.colorLUT.value.type,THREE.HalfFloatType);assert.equal(u.colorLUT.value.generateMipmaps,false);
 assert.equal(u.colorLUT.value.minFilter,THREE.LinearFilter);assert.equal(u.colorLUT.value.wrapR,THREE.ClampToEdgeWrapping);
 assert.deepEqual(u.ccCoeff.value.toArray(),[.875,.0625]);assert.equal(post.stats.nativeGPUEquivalent,false);
 assert.equal(u.bloomMode.value,0);assert.equal(u.vignetteMode.value,0);assert.equal(post.stats.nativeDOF.Start,484);
 assert.equal(post.stats.nativeBloom.Enable,true);assert.equal(post.stats.nativeBloom.Threshold,4);post.dispose();
});
test('configure enable→disable→enable releases prior LUT and clears optional compose bindings',()=>{
 const post=new HDRCompose();post.configure(env);let disposed=0;post.material.uniforms.colorLUT.value.addEventListener('dispose',()=>disposed++);
 post.bindBloom(new THREE.Texture(),2);post.setVignette({shape:2,param:[1,1,0,0],color:[0,0,0,1],start:0,range:1});
 post.configure({rendering:{PostEffect:{ColorGrading:{...fixture.setting,Enable:false}}}});
 assert.equal(disposed,1);assert.equal(post.ccLUT,null);assert.equal(post.material.uniforms.ccEnabled.value,false);
 assert.equal(post.material.uniforms.bloomMode.value,0);assert.equal(post.material.uniforms.vignetteMode.value,0);
 post.configure(env);assert.equal(post.ccLUT.packed.length,512);post.dispose();
});
for(const fail of [0,1,2])test(`actual post restores target/tone state with draw failure ${fail}`,()=>{
 const post=new HDRCompose();post.configure(env);const saved=new THREE.WebGLRenderTarget(2,2);let target=saved,draws=0;
 const renderer={toneMapping:THREE.ACESFilmicToneMapping,getDrawingBufferSize:v=>v.set(640,480),getRenderTarget:()=>target,setRenderTarget:t=>{target=t},render:()=>{draws++;if(fail&&draws===fail)throw Error('fixture draw failure')}};
 if(fail)assert.throws(()=>post.render(renderer,new THREE.Scene(),new THREE.Camera()),/fixture draw failure/);else post.render(renderer,new THREE.Scene(),new THREE.Camera());
 assert.equal(target,saved);assert.equal(renderer.toneMapping,THREE.ACESFilmicToneMapping);
 assert.equal(post.target.width,640);assert.equal(post.material.uniforms.exposure.value,2);assert.equal(post.material.uniforms.gammaMode.value,1);
 post.dispose();saved.dispose();
});
