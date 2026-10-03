import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {textureResolver} from '../client/render/model.ts';

test('Tank sampler resolves its model resource before a same-named embedded Player00 skin map',async()=>{
 const local=new THREE.Texture(),wrong=new THREE.Texture(),calls=[];
 const gltf={parser:{json:{images:[{name:'M_Body_MAi'}],textures:[{source:0}]},getDependency:async()=>{calls.push('embedded');return wrong;}}};
 const path='tex/resources/Tnk_Simple/M_Body_MAi.ktx2';
 const bundle={has:n=>n===path,names:()=>['tex/M_Body_MAi.ktx2',path],texture:async n=>{calls.push(n);return n===path?local:wrong;}};
 const resolve=textureResolver(gltf,bundle,'Tnk_Simple');
 assert.equal(await resolve('M_Body_MAi'),local);assert.equal(await resolve('M_Body_MAi'),local);assert.deepEqual(calls,[path]);
 assert.equal(await textureResolver(gltf,bundle)('M_Body_MAi'),wrong);
});

test('Narrow tank resources preserve original linear mask and sRGB transmission transfer functions',()=>{
 for(const [name,transfer] of [['MAi',1],['Fxm',1],['Trm',2]]){
  const b=readFileSync(new URL(`../assets/characters/Player00/tex/resources/Tnk_Simple/M_Body_${name}.ktx2`,import.meta.url));
  assert.equal(b.subarray(0,12).toString('hex'),'ab4b5458203230bb0d0a1a0a');
  const dfd=b.readUInt32LE(48);assert.equal(b[dfd+14],transfer,name);
 }
 const production=readFileSync(new URL('../assets/characters/Player00/data/anim_material_native.json',import.meta.url));
 const captured=readFileSync(new URL('./fixtures/material_animation_r9_channels.json',import.meta.url));
 assert.equal(Buffer.compare(production,captured),0);
});
