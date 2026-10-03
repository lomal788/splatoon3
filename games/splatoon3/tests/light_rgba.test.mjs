import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {LightingState} from '../client/render/lighting.ts';
import {staticSpotRigs} from '../client/render/dynamic_lights.ts';
const fixture=JSON.parse(readFileSync(new URL('./fixtures/light_rgba_native.json',import.meta.url),'utf8'));
const bits=v=>new Uint32Array(new Float32Array([v]).buffer)[0];

test('Env5 RGBA fourth lane survives lighting binding versus original multiply block',()=>{
 const lighting=new LightingState();
 for(const c of fixture.cases){
  const raw={rendering:{Lighting:{MainLight:{Color:{R:c.color[0],G:c.color[1],B:c.color[2],A:c.color[3]}}}}};
  lighting.configure(raw,c.color.slice(0,3),c.intensity,[0,-1,0]);
  assert.deepEqual([...lighting.uniforms.hLightColor.value.toArray(),lighting.uniforms.hLightAlpha.value].map(bits),c.bits,c.source);
 }
 lighting.dispose();
});

test('Native rig RGBA reaches dynamic UBO w rather than forced1',()=>{
 const root=new THREE.Group();root.userData.originalModelName='rigModel';
 const bone=new THREE.Object3D();bone.name='Dynamic_SpotLightB';root.add(bone);
 const lighting=new LightingState();
 const env={sceneEnv:{params:{SpotLightRig:{objects:{rig:{enable:true,AnmType:0,ModelName:'rigModel',BonePrefix:'Dynamic_SpotLightB',Color:[.5,.75,1,.25],Intensity:12,Radius:13,Angle:2,Direction:[0,-1,0]}}}}}};
 const rig=staticSpotRigs(env,root)[0];assert.equal(rig.colorAlpha,3);
 lighting.configure(env,[1,1,1],10,[0,-1,0]);lighting.bindRigs(root);
 assert.equal(lighting.uniforms.hDynColor.value[0].w,3);
 assert.deepEqual(lighting.uniforms.hDynColor.value[0].toArray(),[6,9,12,3]);
 lighting.dispose();
});
