import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {SkyView} from '../client/render/sky.ts';
import {MapView} from '../client/render/map.ts';
import {materialTeamParams,buildTeamSets,FALLBACK_ROW} from '../client/render/teamcolor.ts';

const srgbToLinear=v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4;
/** What a shader receives from an 8-bit texel under the texture's colorSpace. */
const sampled=(byte,colorSpace)=>colorSpace===THREE.SRGBColorSpace?srgbToLinear(byte/255):byte/255;

function skyGltf(){
  const sky=new THREE.MeshStandardMaterial({name:'mSky'});sky.emissiveMap=new THREE.Texture();sky.emissiveMap.colorSpace=THREE.SRGBColorSpace;
  const sun=new THREE.MeshStandardMaterial({name:'mSun'});sun.map=new THREE.Texture();sun.map.colorSpace=THREE.SRGBColorSpace;
  const scene=new THREE.Group();scene.add(new THREE.Mesh(new THREE.PlaneGeometry(),sky),new THREE.Mesh(new THREE.PlaneGeometry(),sun));
  return {gltf:{scene},sky:sky.emissiveMap,sun:sun.map};
}

test('mSky BC6H_UFLOAT: bundle bytes are linear values; sampled as stored they match native within 8-bit+clamp',()=>{
  const fx=JSON.parse(readFileSync(new URL('./fixtures/sky_bc6h_bytes.json',import.meta.url)));
  assert.equal(fx.format,'BC6H_UFLOAT');assert.equal(fx.cases.length,256);
  const {gltf,sky,sun}=skyGltf();const view=new SkyView(gltf,null);
  assert.equal(sky.colorSpace,THREE.NoColorSpace);assert.equal(sun.colorSpace,THREE.SRGBColorSpace);
  let maxNow=0,meanBefore=0;
  for(const c of fx.cases)for(let k=0;k<3;k++){
    const ref=Math.min(c.native[k],1);
    maxNow=Math.max(maxNow,Math.abs(sampled(c.bytes[k],sky.colorSpace)-ref));
    meanBefore+=Math.abs(sampled(c.bytes[k],THREE.SRGBColorSpace)-ref)/(fx.cases.length*3);
  }
  assert.ok(maxNow<=1.25/255,'linear read max error '+maxNow);
  assert.ok(meanBefore>.05,'previous sRGB decode error '+meanBefore);
  view.dispose();
});

test('map _Emm (native BC4_UNORM) emissive maps are not sRGB-decoded; _Alb/_Emi keep sRGB',()=>{
  const map=new MapView(new THREE.Scene());
  const mk=(name,samplers,emissive)=>{
    const m=new THREE.MeshStandardMaterial({name});m.userData.hoian={shader:'Hoian_UBER/hoian_uber',options:{},samplers,params:{}};
    m.map=new THREE.Texture();m.map.name=samplers._a0;m.map.colorSpace=THREE.SRGBColorSpace;
    m.emissiveMap=new THREE.Texture();m.emissiveMap.name=emissive;m.emissiveMap.colorSpace=THREE.SRGBColorSpace;return m;
  };
  const emm=mk('Celling',{_a0:'Celling_Alb',_e0:'Celling_Emm'},'Celling_Emm');
  const emi=mk('Screen',{_a0:'Screen_Alb',_e0:'Screen_Emi'},'Screen_Emi');
  const scene=new THREE.Group();scene.add(new THREE.Mesh(new THREE.PlaneGeometry(),emm),new THREE.Mesh(new THREE.PlaneGeometry(),emi));
  const bundle={names:()=>[],has:()=>false};
  map.addVisual({scene,parser:{json:{}}},bundle,materialTeamParams(buildTeamSets(FALLBACK_ROW)[0]));
  assert.equal(emm.emissiveMap.colorSpace,THREE.NoColorSpace);
  assert.equal(emm.map.colorSpace,THREE.SRGBColorSpace);
  assert.equal(emi.emissiveMap.colorSpace,THREE.SRGBColorSpace);
  map.dispose(new THREE.Scene());
});

import {illuminateUBO,nativeLayerRoughness,nativeEnvLayer,ggxEnvBRDF,vanDerCorput,faceDirection,PREFILTER_TILES,PREFILTER_ATLAS,ILLUMINATE_NATIVE} from '../client/render/env_prefilter.ts';
const f32bits=v=>new Uint32Array(new Float32Array([v]).buffer)[0];
test('Illuminate UBO 0x710102ff04: 65 original unicorn executions (SDK sinf/cosf/sqrtf) vs web f32 port',()=>{
  const fx=JSON.parse(readFileSync(new URL('./fixtures/illuminate_emu.json',import.meta.url)));
  assert.equal(fx.fn,'0x710102ff04');assert.deepEqual(fx.stubs,['nn::os::LockMutex','nn::os::UnlockMutex']);
  let comps=0,exact=0,maxUlp=0;
  for(const c of fx.cases){
    const env={rendering:{Lighting:{EnvMap:{Type:'Illuminate',IlluminateEnvMap:{BaseIntensity:c.baseIntensity,LightTexScale:c.lightTexScale,
      LightArray:c.elems.map(([Latitude,Intensity,LongitudeFromMainLight])=>({Latitude,Intensity,LongitudeFromMainLight}))}}}}};
    const u=illuminateUBO(env,c.dir,c.color);
    assert.deepEqual(u.param.map(f32bits),c.out.paramBits);
    assert.deepEqual(u.color,c.out.color);
    u.lights.forEach((l,i)=>l.forEach((v,k)=>{comps++;const d=Math.abs(f32bits(v)-c.out.lightBits[i][k]);if(d===0)exact++;
      maxUlp=Math.max(maxUlp,Math.abs(v-c.out.lights[i][k]));}));
  }
  // JS sin/cos are not SDK sinf/cosf: cancellation near 0 gives up to 96 ulp but <1e-6 absolute.
  assert.ok(maxUlp<=1e-6,'max abs '+maxUlp);assert.ok(exact/comps>.9,'bit-exact '+exact+'/'+comps);
});
test('Lby Illuminate inputs: 18 LightArray entries with ctor defaults 1000/40/0 for missing fields',()=>{
  const env=JSON.parse(readFileSync(new URL('../assets/maps/Lby_Lobby00/env.json',import.meta.url)));
  const u=illuminateUBO(env,[0.04313143342733383,-0.56640625,-0.8229967355728149],[0.6705883145332336,0.8509804010391235,1,1]);
  assert.equal(u.lights.length,18);assert.deepEqual(u.param,[1,Math.fround(.11),18]);
  assert.deepEqual(u.lights.map(l=>l[3]),[6000,3000,...Array(16).fill(1000)]);
  assert.equal(ILLUMINATE_NATIVE.inkRoughness,Math.fround(.05));
});
test('native layer roughness endpoints and material layer selection',()=>{
  assert.ok(Math.abs(nativeLayerRoughness(0))<1e-6);assert.ok(Math.abs(nativeLayerRoughness(11)-1)<1e-6);
  for(let l=1;l<12;l++)assert.ok(nativeLayerRoughness(l)>nativeLayerRoughness(l-1));
  assert.equal(nativeEnvLayer(0),0);assert.equal(nativeEnvLayer(1),11);assert.equal(nativeEnvLayer(.5),6);
});
test('GGXEnvBRDF port: scale+bias bounded, smooth surface at normal incidence reflects F0',()=>{
  assert.equal(vanDerCorput(1),.5);assert.equal(vanDerCorput(2),.25);assert.equal(vanDerCorput(3),.75);
  const [a,b]=ggxEnvBRDF(.999,.05);assert.ok(a>.9&&a<1.01&&b<.01,a+' '+b);
  for(const nov of [.1,.5,.9])for(const r of [.1,.5,.9]){const [x,y]=ggxEnvBRDF(nov,r);assert.ok(x>=0&&y>=0&&x+y<=1.05,[nov,r,x,y].join());}
});
test('prefilter atlas face convention round-trips with the GLSL lookup rule',()=>{
  assert.equal(PREFILTER_ATLAS.height,PREFILTER_TILES.reduce((a,b)=>a+b,0));
  for(let f=0;f<6;f++)for(const [a,b] of [[.3,-.7],[-.9,.2],[0,0]]){
    const d=faceDirection(f,a,b),m=d.map(Math.abs);let g,ab;
    if(m[0]>=m[1]&&m[0]>=m[2]){g=d[0]>0?0:1;ab=d[0]>0?[-d[2]/m[0],d[1]/m[0]]:[d[2]/m[0],d[1]/m[0]];}
    else if(m[1]>=m[2]){g=d[1]>0?2:3;ab=d[1]>0?[d[0]/m[1],-d[2]/m[1]]:[d[0]/m[1],d[2]/m[1]];}
    else{g=d[2]>0?4:5;ab=d[2]>0?[d[0]/m[2],d[1]/m[2]]:[-d[0]/m[2],d[1]/m[2]];}
    assert.equal(g,f);assert.ok(Math.abs(ab[0]-a)<1e-12&&Math.abs(ab[1]-b)<1e-12);
  }
});
