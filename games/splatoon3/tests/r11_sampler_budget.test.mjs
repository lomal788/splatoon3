// Fragment texture-unit budget: every character/weapon/map material shader must keep ≤16 active samplers
// (MAX_TEXTURE_IMAGE_UNITS on d3d11/most GPUs; swiftshader's 32 hid the overflow).
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {applyHoian} from '../client/render/hoian.ts';
import {applyForward} from '../client/render/forward.ts';
import {applyCharacterMaterial} from '../client/render/character_material.ts';
import {applyInkSurface} from '../client/render/ink_surface.ts';
import {LightingState} from '../client/render/lighting.ts';
import {shareMaterialSamplers,fresOf} from '../client/render/model.ts';
import {bindMaterialChannels} from '../client/render/anim/material_binding.ts';
import {materialFragmentSamplers,activeSamplers,resolveIncludes,preprocess,standardDefines} from './glsl_sampler_budget.mjs';

const LIMIT=16;
const A=new URL('../assets/',import.meta.url);
const glb=p=>{const b=readFileSync(new URL(p,A));const n=b.readUInt32LE(12);return JSON.parse(b.subarray(20,20+n).toString());};
const json=p=>JSON.parse(readFileSync(new URL(p,A),'utf8'));
const team={my_team_color:[.8,.1,.05,1],my_team_color_hue_complement:[.05,.3,.7,1]};
const flush=()=>new Promise(r=>setTimeout(r,0));

function geometry(){
  const g=new THREE.BufferGeometry(),n=3;
  for(const [k,s] of [['position',3],['normal',3],['uv',2],['uv1',2],['uv2',2],['uv3',2],['tangent',4],['paintUv',2],['paintUvSwitch',1],['paintUvTangent',3]])g.setAttribute(k,new THREE.BufferAttribute(new Float32Array(n*s),s));
  return g;
}
function materials(j){
  const tex=i=>{if(i===undefined)return null;const t=new THREE.Texture();t.name=j.images[j.textures[i].extensions?.KHR_texture_basisu?.source??j.textures[i].source].name;return t;};
  return j.materials.filter(m=>m.extras?.fres||m.extras?.hoian).map(m=>{
    const p=m.pbrMetallicRoughness??{},mat=new THREE.MeshStandardMaterial();mat.name=m.name;mat.userData={...m.extras};
    mat.map=tex(p.baseColorTexture?.index);mat.normalMap=tex(m.normalTexture?.index);
    const mr=tex(p.metallicRoughnessTexture?.index);mat.roughnessMap=mr;mat.metalnessMap=mr;
    mat.aoMap=tex(m.occlusionTexture?.index);mat.emissiveMap=tex(m.emissiveTexture?.index);
    mat.metalness=p.metallicFactor??1;mat.roughness=p.roughnessFactor??1;if(m.emissiveFactor)mat.emissive.setRGB(...m.emissiveFactor);
    if(m.alphaMode==='MASK')mat.alphaTest=.5;
    return {mat,fres:fresOf(mat)};
  });
}
const resolver=()=>{const c=new Map();return async name=>{if(!c.has(name))c.set(name,Object.assign(new THREE.Texture(),{name}));return c.get(name);};};

async function characterRows(file,group){
  const lighting=new LightingState(),rows=[],targets=[],tex=resolver();
  for(const {mat,fres} of materials(glb(file))){
    const g=geometry(),skipped=[];
    const u=applyHoian(mat,fres,team,tex,skipped,g);await flush();
    applyForward(mat,fres,lighting,null);
    const b=applyCharacterMaterial(mat,fres,tex,skipped,g,lighting.uniforms.hLightAlpha);if(b)await b.ready;
    if(u)shareMaterialSamplers(mat,fres);
    targets.push({material:mat,fres,tex});rows.push({file,mat});
  }
  if(group)bindMaterialChannels(targets,group);
  return rows.map(r=>({...r,samplers:materialFragmentSamplers(r.mat,{skinning:true})}));
}

test('preprocessor/reachability counter: unreached helper functions and #ifdef-off code do not count',()=>{
  const src='uniform sampler2D a,b;\nuniform sampler2D c;\n#ifdef X\nuniform sampler2D d;\n#endif\nvec4 f(){return texture2D(b,vec2(0.));}\nvec4 g(){return texture2D(c,vec2(0.));}\nvoid main(){gl_FragColor=texture2D(a,vec2(0.))+f();}';
  assert.deepEqual(activeSamplers(src,{}),['a','b']);
});

test('character, squid, _Hlf, gear and weapon material shaders stay within 16 fragment texture units',async()=>{
  const bank=json('characters/Player00/data/anim_material_native.json').groups,tank=json('characters/Player00/data/tank_anim_native.json').material;
  const rows=[
    ...await characterRows('characters/Player00/body.glb',bank.Player00),
    ...await characterRows('characters/Player00/body_hlf.glb',bank.Player00_Hlf),
    ...await characterRows('characters/Player00/squid.glb',bank.Player_Squid),
    ...await characterRows('characters/Player00/parts/Tnk_Simple.glb',tank),
    ...await characterRows('weapons/Shooter_Normal_00/model.glb',null)];
  for(const p of ['Har_SQD000_F','Eyb_SQD000_F','Btm_000_F','Clt_TES001_F','Hed_FST000','Shs_SLO000'])rows.push(...await characterRows(`characters/Player00/parts/${p}.glb`,null));
  const over=rows.filter(r=>r.samplers.length>LIMIT).map(r=>`${r.file} ${r.mat.name}: ${r.samplers.length} ${r.samplers.join(',')}`);
  assert.deepEqual(over,[]);
  const body=rows.find(r=>r.file.endsWith('body.glb')&&r.mat.name==='M_Body');
  assert.ok(body.samplers.includes('hResource0Tex')&&!body.samplers.includes('hCharMaskTex'),'MAi read once through _re0');
  assert.ok(!body.samplers.includes('envMap')&&!body.samplers.includes('metalnessMap')&&!body.samplers.includes('mCRgh'));
  const squidEye=rows.find(r=>r.file.endsWith('squid.glb')&&r.mat.name==='M_Eye');
  assert.ok(squidEye.samplers.includes('mCRgh'),'squid eye keeps its _r0 pattern sampler');
});

test('map visual materials with bake and ink pages stay within 16 fragment texture units',async()=>{
  const lighting=new LightingState(),tex=resolver(),over=[];let n=0;
  const bake={ao:{texture:new THREE.Texture(),st:new THREE.Vector4(1,1,0,0)},light:{texture:new THREE.Texture(),st:new THREE.Vector4(1,1,0,0)}};
  for(const {mat,fres} of materials(glb('maps/Lby_Lobby00/visual.glb'))){
    const g=geometry();applyHoian(mat,fres,team,tex,[],g);await flush();applyForward(mat,fres,lighting,bake);
    const s=materialFragmentSamplers(mat);if(s.length>LIMIT)over.push(`${mat.name}: ${s.length} ${s.join(',')}`);
    const ink=mat.clone();ink.onBeforeCompile=mat.onBeforeCompile;ink.customProgramCacheKey=mat.customProgramCacheKey.bind(mat);ink.defines={...mat.defines};ink.userData={...mat.userData};
    applyInkSurface(ink,{texture:new THREE.Texture(),ink:[[1,0,0],[0,1,0],[0,0,1]],inkBright:[[1,0,0],[0,1,0],[0,0,1]],textureStep:[1/1024,0],emission:0,
      attributeNames:{uv:'paintUv',selector:'paintUvSwitch',tangent:'paintUvTangent'}});
    let si=[];
    try{si=materialFragmentSamplers(ink);}catch(e){if(!/anchor missing/.test(e.message))throw e;} // enable_shading False: no paint page
    if(si.length>LIMIT)over.push(`${mat.name}:ink: ${si.length} ${si.join(',')}`);n++;
  }
  assert.ok(n>40);assert.deepEqual(over,[]);
});

test('shared mr fetch reads metalness after metalnessmap_fragment declares it (d3d11 compile error regression)',async()=>{
  const rows=await characterRows('characters/Player00/parts/Tnk_Simple.glb',null);
  const tank=rows.find(r=>r.mat.name==='M_Body');assert.equal(tank.mat.metalnessMap,null);assert.ok(tank.mat.roughnessMap);
  const sh={uniforms:{},defines:tank.mat.defines,vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
  tank.mat.onBeforeCompile(sh,{});
  const code=preprocess(resolveIncludes(sh.fragmentShader),standardDefines(tank.mat));
  const decl=code.indexOf('float metalnessFactor'),use=code.indexOf('metalnessFactor*=texelRoughness.b');
  assert.ok(decl>=0&&use>decl,'metalnessFactor declared before the shared read');
});
