import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {bindMaterialChannels} from '../client/render/anim/material_binding.ts';
import {sampleMaterialClip} from '../client/render/anim/material_channels.ts';
const bank=JSON.parse(readFileSync(new URL('./fixtures/material_animation_r9_channels.json',import.meta.url),'utf8'));
const group=bank.groups.Player_Squid;
const fres=group.materials.find(m=>m.name==='M_Eye');
function setup(resolver=()=>Promise.resolve(new THREE.Texture()),consume){
 const material=new THREE.MeshStandardMaterial();material.name='M_Eye';
 const map=new THREE.Texture(),normalMap=new THREE.Texture();material.map=map;material.normalMap=normalMap;
 const originalCompile=function(s){s.vertexShader='varying vec2 hUV0;';s.fragmentShader='varying vec2 hUV0;\n#include <map_fragment>\n#include <normal_fragment_maps>\n#include <roughnessmap_fragment>';};
 material.onBeforeCompile=originalCompile;
 const key=material.customProgramCacheKey;
 const binding=bindMaterialChannels([{material,fres,tex:resolver}],group,consume);
 return {material,binding,map,normalMap,originalCompile,key};
}
test('actual Sqd_Surprise raw patterns reach real material map/normal/R roughness slots with native UV0',async()=>{
 const textures=new Map(group.clips.flatMap(c=>c.textureNames).map(n=>[n,new THREE.Texture()]));
 const x=setup(n=>Promise.resolve(textures.get(n)??null));await x.binding.ready;
 x.binding.apply([{type:11,clip:'Sqd_Surprise',frame:3,weight:1}]);
 assert.equal(x.material.map,textures.get('M_Eye_Alb.3'));assert.equal(x.material.normalMap,textures.get('M_Eye_Nrm.3'));
 const s={uniforms:{},vertexShader:'',fragmentShader:''};x.material.onBeforeCompile(s,null);
 assert.equal(s.uniforms.mCRgh.value,textures.get('M_Eye_Rgh.3'));assert.equal(s.uniforms.mCActiveR.value,1);
 assert.match(s.fragmentShader,/roughness\*texture2D\(mCRgh,hUV0\)\.r/);
 assert.match(s.fragmentShader,/mCActiveA>.5\?hUV0:vMapUv/);assert.match(s.fragmentShader,/mCActiveN>.5\?hUV0:vNormalMapUv/);
 assert.equal(x.binding.stats.patternWrites,3);assert.equal(x.binding.stats.rawSrtUnbound,true);
 assert.ok(x.binding.stats.unsupported.some(s=>s.includes('SRT-to-Mat')));
 x.binding.dispose();assert.equal(x.material.map,x.map);assert.equal(x.material.normalMap,x.normalMap);
 assert.equal(x.material.onBeforeCompile,x.originalCompile);assert.equal(x.material.customProgramCacheKey,x.key);
});
test('missing textures/weighted blends preserve existing material; dispose cancels async ownership',async()=>{
 const x=setup(()=>Promise.resolve(null));await x.binding.ready;
 x.binding.apply([{type:11,clip:'Sqd_Surprise',frame:3,weight:1}]);
 assert.equal(x.material.map,x.map);assert.equal(x.binding.stats.patternWrites,0);assert.equal(x.binding.stats.missing.length,3);
 x.binding.apply([{type:11,clip:'Sqd_Wait',frame:3,weight:.5}]);assert.ok(x.binding.stats.unsupported.some(s=>s.includes('weighted')));
 const y=setup();y.binding.dispose();await y.binding.ready;y.binding.applySample(sampleMaterialClip(group,'Sqd_Surprise',3));
 assert.equal(y.material.map,y.map);assert.equal(y.binding.stats.applied,0);
});
test('typed raw SRT is supplied only to explicit native consumer; no swimming CP/skin constant is synthesized',async()=>{
 const calls=[];const x=setup(undefined,(t,name,offsets)=>{calls.push({name,offsets});return true;});await x.binding.ready;
 x.binding.apply([{type:11,clip:'Sqd_Wait',frame:4,weight:1}]);
 assert.equal(x.binding.stats.rawSrtUnbound,false);assert.equal(calls.length,1);assert.equal(calls[0].name,'tex_mtx0');
 assert.equal(calls[0].offsets['0x04'],1);assert.deepEqual(x.binding.stats.unsupported,[]);
 assert.equal(calls.some(c=>c.name==='two_color_complement_paint_intensity'),false);
});
