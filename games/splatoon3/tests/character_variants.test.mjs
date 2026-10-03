import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {applyCharacterMaterial,characterParameters,characterVariantProfile} from '../client/render/character_material.ts';
import {applyHoian,calcColorGlsl,calcChannel,setHoianTexMatrix,setHoianMaterialTexSrt} from '../client/render/hoian.ts';
import {LightingState} from '../client/render/lighting.ts';
import {applyForward} from '../client/render/forward.ts';
import {characterFilm,characterFilmTau,characterScatterLobe} from '../client/render/character_material_math.ts';
const rows=JSON.parse(readFileSync(new URL('./fixtures/character_variants_native.json',import.meta.url),'utf8')).rows;
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} != ${b}`);
const team={my_team_color:[.8,.2,.1,1],my_team_color_hue_complement:[.1,.4,.6,1]};
function setup(row,missing){const mat=new THREE.MeshStandardMaterial();mat.name=row.material;
 const g=new THREE.PlaneGeometry();g.setAttribute('tangent',new THREE.BufferAttribute(new Float32Array(g.attributes.position.count*4),4));
 const names=new Set(),textures=new Map(),tex=async name=>{names.add(name);if(name===missing)return null;if(!textures.has(name))textures.set(name,new THREE.Texture());return textures.get(name);};
 const skipped=[],lighting=new LightingState(),u=applyHoian(mat,row.fres,team,tex,skipped,g);applyForward(mat,row.fres,lighting,null);
 const b=applyCharacterMaterial(mat,row.fres,tex,skipped,g,lighting.uniforms.hLightAlpha);
 return {mat,g,names,textures,skipped,lighting,u,b,dispose(){b.dispose();mat.dispose();g.dispose();lighting.dispose();for(const t of textures.values())t.dispose();}};}
test('actual native option keys distinguish SFX film from texture-free bottle',()=>{
 for(const r of rows){const p=characterVariantProfile(r.fres);assert.equal(p.kind,r.label==='bottle'?'constantFilm':'sfxFilm');
  assert.equal(p.paint,false);assert.equal(p.thickness,false);assert.equal(p.edge,false);assert.equal(p.manualFresnel,false);}
});
test('native bottle needs no transmission thickness CompPaint or SFX texture',async()=>{
 const r=rows.find(r=>r.label==='bottle'),s=setup(r);try{await s.b.ready;assert.equal(s.b.stats.textureReady,true);assert.deepEqual([...s.names],[]);
  const sh={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};s.mat.onBeforeCompile(sh,{});
  assert.ok(sh.fragmentShader.includes('hCalcTransmission.rgb*=myTeamColor'));assert.ok(!sh.fragmentShader.includes('hCK=1.-texture2D'));
  assert.ok(!sh.fragmentShader.includes('hF0=hCharManualFresnel'));assert.equal(s.b.uniforms.hCharEdgeEnabled.value,0);
 }finally{s.dispose();}
});
test('tank/harness require actual FxM and Trm but no nonexistent CP/Thc',async()=>{
 for(const r of rows.filter(r=>r.label!=='bottle')){const s=setup(r);try{await s.b.ready;assert.equal(s.b.stats.textureReady,true);
  assert.ok(!s.b.stats.missing.some(x=>x.includes('_re2')||x.includes('_cp0')));assert.ok(s.names.has(r.label==='tank'?'M_Body_Fxm':'M_Harness_Fxm'));
 }finally{s.dispose();}}
 const s=setup(rows.find(r=>r.label==='tank'),'M_Body_Fxm');try{await s.b.ready;assert.equal(s.b.stats.textureReady,false);assert.ok(s.b.stats.missing.includes('M_Body_Fxm unavailable'));}finally{s.dispose();}
});
test('tank native Resource0 UV2 aliases UV0 attribute and retains separate packed matrix',async()=>{
 const s=setup(rows.find(r=>r.label==='tank'));try{await s.b.ready;assert.equal(s.b.stats.nativeUvMatrices,true);
  assert.deepEqual(s.u.texMatrices[2].row0.value.toArray(),[1,-0,0,1]);
  assert.deepEqual(s.u.texMatrices[2].row1.value.toArray(),[0,Math.fround(-.6),0,0]);
  // Actual GLB has emissiveFactor=.5. Native calc22 must begin with raw _e0, not Three's premultiplied emission.
  s.mat.emissive.setRGB(.5,.5,.5);
  setHoianTexMatrix(s.u,2,[1,0,0,1,.25,-.75,0,0]);
  const sh={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};s.mat.onBeforeCompile(sh,{});
  assert.ok(sh.vertexShader.includes('hUV2=vec2(uv.x*hTexRow0_2.x'));assert.ok(sh.fragmentShader.includes('texture2D(hResource0Tex,hUV2)'));
  assert.ok(s.names.has('M_Body_Emi'));assert.ok(sh.fragmentShader.includes('hCalcEmission=vec4(texture2D(hNativeEmissionTex,hUV0).rgb*'));
  assert.ok(!sh.fragmentShader.includes('hCalcEmission=vec4(totalEmissiveRadiance,1.)'));
  assert.equal(sh.uniforms.hTexRow1_2.value.y,-.75);assert.equal(s.b.stats.nativeUvMatrices,true);
 }finally{s.dispose();}
});
test('actual static and runtime Maya-zero native rows reject unsupported updates',async()=>{
 const row=rows.find(r=>r.label==='bottle'),s=setup(row);try{await s.b.ready;
  assert.deepEqual(s.u.texMatrices[0].row0.value.toArray(),[1,-0,0,2]);
  assert.deepEqual(s.u.texMatrices[0].row1.value.toArray(),[0,-1,0,0]);
  const raw=structuredClone(row.fres.params.tex_mtx0.value);
  assert.equal(setHoianMaterialTexSrt(s.mat,'tex_mtx7',raw),false);
  assert.equal(setHoianMaterialTexSrt(s.mat,'tex_mtx0',{...raw,Rotation:.1}),false);assert.equal(s.b.stats.nativeUvMatrices,false);
  assert.deepEqual(s.u.texMatrices[0].row1.value.toArray(),[0,-1,0,0]);
  assert.equal(setHoianMaterialTexSrt(s.mat,'tex_mtx0',{...raw,Mode:'Mode3dsMax'}),false);
  assert.equal(setHoianMaterialTexSrt(s.mat,'tex_mtx0',raw),true);assert.equal(s.b.stats.nativeUvMatrices,true);
 }finally{s.dispose();}
});
test('native type22 emission subtraction and film mask affect independent tau',()=>{
 const row=rows.find(r=>r.label==='tank'),skip=[],glsl=calcColorGlsl(row.fres,new Set([9,10,4]),skip);
 assert.ok(glsl.includes('hCalcEmission*vec4('));assert.ok(glsl.includes('hResource1'));assert.ok(glsl.includes('(-(hResource0))'));assert.equal(skip.length,0);
 assert.equal(calcChannel('resource','2'),'(-(resource))');
 const p=characterParameters(row.fres),film=characterFilm(1,.5,1,p);near(film,.44);near(characterFilmTau(film,.5,p),.543*.5*.56);
 near(characterScatterLobe(-1,.4),.488);near(characterScatterLobe(1,.4),.128000003);
});
