import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {applyCharacterMaterial,characterParameters} from '../client/render/character_material.ts';
import {applyHoian,calcColorGlsl} from '../client/render/hoian.ts';
import {applyForward} from '../client/render/forward.ts';
import {LightingState} from '../client/render/lighting.ts';
import {characterDirectColor,characterEdge,characterFilm,characterNormalCorrection,characterBacklight} from '../client/render/character_material_math.ts';
const fixture=JSON.parse(readFileSync(new URL('./fixtures/character_material_native.json',import.meta.url),'utf8'));
const near=(a,b,e=1e-6)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}`);
test('body sideways wrapped light and added backlight preserve original counterexample',()=>{
  const p=characterParameters(fixture.rows[0].fres),direct=characterDirectColor(0,[1,1,1],1,p);
  direct.forEach((x,i)=>near(x,[.13,.0766666667,.0733333333][i]));
  const t=[.753,.16*.277,.12*.266],back=characterBacklight(0,0,1,1,t,1,.3,1,p);
  back.forEach((x,i)=>near(x,[.01626480,.000957312,.000689472][i]));
});
test('RGB direct mask and RGBA alpha backlight have independent native consumers',()=>{
  const p=characterParameters(fixture.rows[0].fres);
  assert.deepEqual(characterDirectColor(-.1,[10,20,30],0,p),[0,0,0]);
  assert.ok(characterDirectColor(-.1,[10,20,30],1,p).every(x=>x>0));
  assert.deepEqual(characterBacklight(.5,-1,-1,1,[1,2,3],0,.3,1,p),[0,0,0]);
  assert.deepEqual(characterBacklight(.5,-1,-1,0,[1,2,3],10,.3,1,p),[0,0,0]);
});
test('film includes thickness after its clamp and changes tau, not pixel opacity',()=>{
  const p=characterParameters(fixture.rows[2].fres);
  near(characterFilm(1,1,.25,p),Math.fround(.9)*.25);
  assert.equal(characterFilm(1,0,1,p),0);assert.equal(characterFilm(1,1,0,p),0);
  assert.ok(characterEdge(.6,-.5,-.8,1,p)>0);
  assert.equal(characterNormalCorrection(1,0,-.3),1);
  near(characterNormalCorrection(1,0,0),.16);
});
test('selected squid/hair type5 reads under-film and hue-complement source without dropping operands',()=>{
  for(const row of fixture.rows.slice(2)){const skipped=[],code=calcColorGlsl(row.fres,new Set([9,4]),skipped);
    assert.ok(code.includes('myTeamColorHueComplement'));assert.ok(code.includes('hCalcUnderFilm'));assert.ok(code.includes('hResource0'));
    assert.equal(skipped.filter(x=>x.includes('type/source 5')).length,0);}
});
test('actual four GLB material hooks consume mask thickness transmission film normals and alpha',async()=>{
  for(const row of fixture.rows){const mat=new THREE.MeshStandardMaterial(),geometry=new THREE.PlaneGeometry(2,2);
    geometry.setAttribute('tangent',new THREE.BufferAttribute(new Float32Array(geometry.attributes.position.count*4).fill(1),4));
    const textures=new Map(),tex=async name=>{if(!textures.has(name))textures.set(name,new THREE.Texture());return textures.get(name);},lighting=new LightingState(),skipped=[];
    const team={my_team_color:[.8,.1,.05,1],my_team_color_hue_complement:[.05,.3,.7,1]};
    applyHoian(mat,row.fres,team,tex,skipped,geometry);applyForward(mat,row.fres,lighting,null);
    const b=applyCharacterMaterial(mat,row.fres,tex,skipped,geometry,lighting.uniforms.hLightAlpha);assert.ok(b,row.label);await b.ready;
    assert.equal(b.stats.textureReady,true);const sh={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};mat.onBeforeCompile(sh,{});
    for(const text of ['hCharDirect(', 'hCharEdge(', 'hCharDynamic(', 'hCharCorrection(', 'hCNc=normalize', 'hLightAlpha*hCTau', 'hDynColor[index].w', 'hCalcTransmission.rgb'])assert.ok(sh.fragmentShader.includes(text),row.label+': '+text);
    assert.equal(b.stats.hookCompiled,1);assert.equal(b.stats.ordinaryConsumer,true);assert.equal(sh.uniforms.hLightAlpha,lighting.uniforms.hLightAlpha);
    if(['squid','hair'].includes(row.label))assert.ok(sh.fragmentShader.includes('hCUnderFilm=hCalcUnderFilm.rgb'));
    assert.ok(!skipped.some(x=>x.includes('native taransmission/SSS lighting consumer remains')));
    b.dispose();geometry.dispose();mat.dispose();lighting.dispose();for(const t of textures.values())t.dispose();
  }
});
test('missing native texture prevents consumer activation and absent tangent is diagnosed',async()=>{
  const mat=new THREE.MeshStandardMaterial(),g=new THREE.PlaneGeometry(),f=fixture.rows[0].fres,skipped=[],lighting=new LightingState();
  applyHoian(mat,f,{my_team_color:[1,1,1,1],my_team_color_hue_complement:[1,1,1,1]},async()=>null,skipped,g);applyForward(mat,f,lighting,null);
  assert.equal(applyCharacterMaterial(mat,f,async()=>null,skipped,g,lighting.uniforms.hLightAlpha),null);
  g.setAttribute('tangent',new THREE.BufferAttribute(new Float32Array(g.attributes.position.count*4),4));
  const b=applyCharacterMaterial(mat,f,async()=>null,skipped,g,lighting.uniforms.hLightAlpha);await b.ready;assert.equal(b.stats.textureReady,false);assert.ok(b.stats.missing.length>0);
  b.dispose();g.dispose();mat.dispose();lighting.dispose();
});
