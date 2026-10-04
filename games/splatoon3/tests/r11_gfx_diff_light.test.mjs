import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {LightingState} from '../client/render/lighting.ts';
import {parseEnv, lonLatToDir} from '../client/render/map.ts';
import {norm, mul, F} from '../client/render/graphics_math.ts';
import {NativeEnvironment, ggxEnvBRDF} from '../client/render/env_prefilter.ts';
import {SH_PROJECTION_FRAGMENT} from '../client/render/sh_projection.ts';
import {Program, I} from '../../../tools/glsl_eval.mjs';
import {MOCK, DIRS} from '../../../tools/r11_gfx_diff_light_shaders.mjs';

const cpu=JSON.parse(readFileSync(new URL('./fixtures/r11_gfx_diff_light_native.json',import.meta.url),'utf8'));
const gpu=JSON.parse(readFileSync(new URL('./fixtures/r11_gfx_diff_light_shader_native.json',import.meta.url),'utf8'));
const env=JSON.parse(readFileSync(new URL('../assets/maps/Lby_Lobby00/env.json',import.meta.url),'utf8'));
const bits=v=>new Uint32Array(new Float32Array([v]).buffer)[0];
const rel=(a,b)=>Math.max(...a.map((x,i)=>Math.abs(x-b[i])/Math.max(1e-6,Math.abs(b[i]))));
const rawMain=c=>({rendering:{Lighting:{MainLight:{Color:{R:c.color[0],G:c.color[1],B:c.color[2],A:c.color[3]},Intens:c.intensity,Latitude:c.latitude,Longitude:c.longitude}}}});

test('MainLight 0x7102b607c4/0x7102b60ea0: 65 original executions reach hLightColor/hLightAlpha/hLightDirection',()=>{
  const lighting=new LightingState();
  for(const c of cpu.mainlight){
    const raw=rawMain(c),e=parseEnv(raw);
    lighting.configure(raw,e.light.color,e.light.intensity,e.direction);
    const u=lighting.uniforms,o=c.out;
    assert.deepEqual(e.light.color.map(bits),o.diffuseBits.slice(0,3),c.name);
    assert.equal(bits(e.light.intensity),bits(o.intensity),c.name);
    assert.deepEqual(u.hLightColor.value.toArray().map(bits),o.diffuse.slice(0,3).map(v=>bits(mul(o.intensity,v))),c.name);
    assert.equal(bits(u.hLightAlpha.value),bits(mul(o.intensity,o.diffuse[3])),c.name);
    // SDK sinf/cosf vs JS libm: 1 ulp-level only
    for(let k=0;k<3;k++)assert.ok(Math.abs(e.direction[k]-o.direction[k])<=2e-7,`${c.name} dir ${k}`);
  }
  assert.deepEqual(cpu.mainlight[0].out.directionBits,lonLatToDir(-3,34.5).map(bits));
});

test('agl DirectionalLight 0x71035d6500: Env[23] source (+0x208) is the normalized world direction when ViewCoordinate=0',()=>{
  for(const c of cpu.dlView){
    const world=norm(c.direction.map(F));
    const src=c.viewCoord?c.arr1f8:c.arr208;
    for(let k=0;k<3;k++)assert.ok(Math.abs(src[k]-world[k])<=2e-7,`world ${k}`);
  }
  assert.deepEqual(cpu.dlView[0].arr208Bits,lonLatToDir(-3,34.5).map(bits));
});

test('Env UBO 0x71036b35c0 (DL + 2 agl Fog, original run) vs web lighting uniforms',()=>{
  const lobby=cpu.envUbo[0].out.env;
  const e=parseEnv(env),lighting=new LightingState();
  lighting.configure(env,e.light.color,e.light.intensity,e.direction);
  const u=lighting.uniforms;
  assert.deepEqual(u.hLightColor.value.toArray().map(bits),lobby[5].slice(0,3).map(bits));
  assert.equal(bits(u.hLightAlpha.value),bits(lobby[5][3]));
  const d=norm(u.hLightDirection.value.toArray());
  for(let k=0;k<3;k++)assert.ok(Math.abs(d[k]-lobby[23][k])<=2e-7);
  assert.deepEqual(u.hDepthFog.value.toArray().map(bits),lobby[10].map(bits));
  const [s,en]=[u.hDepthRange.value.x,u.hDepthRange.value.y];
  assert.ok(Math.abs(-s/(en-s)-lobby[11][3])<1e-7&&Math.abs(1/(en-s)-lobby[12][0])<1e-9);
  assert.deepEqual(u.hHeightFog.value.toArray().map(bits),lobby[13].map(bits));
  assert.deepEqual(lobby[14].slice(0,3),[0,-1,0]);
  const [hs,he]=[u.hHeightRange.value.x,u.hHeightRange.value.y];
  assert.ok(Math.abs(-hs/(he-hs)-lobby[14][3])<1e-7&&Math.abs(1/(he-hs)-lobby[15][0])<1e-9);
  for(const c of cpu.envUbo){
    const o=c.out.env,l=c.light;
    assert.deepEqual(o[5].map(bits),l.diffuse.map(v=>bits(mul(l.intensity,v))),c.name);
    assert.equal(bits(o[4][3]),bits(l.intensity),c.name);
    const w=norm(l.direction.map(F));
    for(let k=0;k<3;k++)assert.ok(Math.abs(o[23][k]-w[k])<=2e-7,c.name);
    assert.deepEqual(o[10].map(bits),c.fogs[0].color.map(bits),c.name);
  }
});

test('GGXEnvBRDF: original Hoian_Proc pixel shader vs web CPU LUT port, 8 points',()=>{
  for(const p of gpu.brdf){
    const w=ggxEnvBRDF(p.nov,p.r);
    assert.ok(Math.abs(w[0]-p.out[0])<=2e-7&&Math.abs(w[1]-p.out[1])<=2e-7,`${p.nov},${p.r}`);
  }
});

test('GGXPrefilterEnvMap: Illuminate pass and 12-layer prefilter, original vs web GLSL on the same inputs',()=>{
  const ne=new NativeEnvironment();
  const il=new Program(ne.illuminateMaterial.fragmentShader),layer=new Program(ne.layerMaterial.fragmentShader);
  const {ubo,param0,out}=gpu.illuminate;
  DIRS.forEach((d,i)=>{
    const g={cBase:MOCK.cube,cVanDerCorputMap:MOCK.vdc,cParam0:param0,cHighlight:MOCK.highlight,cLightParam:[...ubo.param,0],cLightColor:ubo.color,
      cLightInfo:Array.from({length:32},(_,k)=>ubo.lights[k]??[0,0,0,0]),vDir:d,gl_FragColor:[0,0,0,0]};
    il.run(g);
    // faces 1/5: 1-sample LOD term fma(a2,nh²,−nh²)+1 cancels at r .05; GLSL ES 3.0 has no fma (precision boundary).
    assert.ok(rel(g.gl_FragColor.slice(0,3),out[i])<=4e-3,`illuminate face ${i}`);
    if(i===0||i===3||i===4)assert.ok(rel(g.gl_FragColor.slice(0,3),out[i])<=1e-6,`illuminate face ${i} tight`);
  });
  for(const L of gpu.layers)DIRS.forEach((d,i)=>{
    const n=norm(d.map(F)),r=layer.run({cBase:MOCK.cube,cVanDerCorputMap:MOCK.vdc,cParam0:L.param0},{},'hPrefilter',[n]);
    assert.ok(rel(r,L.out[i])<=1e-5,`layer ${L.layer} face ${i}`);
  });
});

test('IrradianceCubeMapAllToSH W128: original vs web seven-MRT fragment, 12 sample ids',()=>{
  const p=new Program(SH_PROJECTION_FRAGMENT);
  for(const s of gpu.sh){
    const g={sourceCube:MOCK.cube,sourceMip:1,sampleId:new I(s.id)};
    for(let i=0;i<7;i++)g['sh'+i]=[0,0,0,0];
    p.run(g);
    for(let i=0;i<7;i++)for(let k=0;k<4;k++)// zz term: native fma(z²,k,−c) cancels; web separate rounding (no fma in GLSL ES 3.0)
    assert.ok(Math.abs(g['sh'+i][k]-s.out[i][k])<=1e-11+2e-6*Math.abs(s.out[i][k]),`id ${s.id} sh${i}.${k}`);
  }
});

test('0x7101036d84 layer 12: BlackCube unless the counter==1 capture draws illuminate (lobby main light present)',()=>{
  const ne=new NativeEnvironment();
  ne.inkLayer(null,null,false);
  assert.equal(ne.uniforms.hPrefilInkAvailable.value,0);
  assert.equal(ne.stats.inkLayer,'BlackCube');
  const src=readFileSync(new URL('../client/render/lighting.ts',import.meta.url),'utf8');
  assert.match(src,/inkLayer\(renderer,source,pass===1\)/);
});

test('p1714 ink branch reflection: layer 12 (explicit lod 0) x (F0*brdf.x+brdf.y), web hNativeInkSpecular vs native expression',async()=>{
  const {PREFILTER_LOOKUP_GLSL,PREFILTER_INK_GLSL,PREFILTER_INK_TILE:T,PREFILTER_ATLAS:A,faceDirection}=await import('../client/render/env_prefilter.ts');
  const atlasDir=uv=>{const px=uv[0]*A.width-T.x,f=Math.floor(px/T.size),u=px/T.size-f,v=(uv[1]*A.height-T.y)/T.size;assert.ok(f>=0&&f<6&&v>=0&&v<=1);return faceDirection(f,u*2-1,v*2-1);};
  const p=new Program(PREFILTER_LOOKUP_GLSL+PREFILTER_INK_GLSL);
  const brdf=uv=>[F(.9*uv[0]+.05*uv[1]),F(.08*uv[1]+.02*(1-uv[0])),0,1];
  const ink=d=>MOCK.cube(d,0);
  for(const [n,v] of [[[0,1,0],[.3,.8,.5]],[[.2,.9,-.1],[-.4,.6,.7]],[[0,0,-1],[.1,.2,-.97]]]){
    const N=norm(n.map(F)),V=norm(v.map(F)),f0=[.015,.015,.015],r=F(.05);
    const web=p.run({hPrefilAvailable:1,hPrefilInkAvailable:1,hEnvBRDF:brdf,hPrefilAtlas:(uv,l)=>{assert.equal(l,0);return ink(atlasDir(uv));},hPrefilRows:[]},{},'hNativeInkSpecular',[N,V,f0,r]);
    // native: R = -V - 2(dot(-V,N))N ; prefil(R/maxabs(R), 12, lod 0) * fma(brdf.x, [19].x, brdf.y), brdf at (max(NoV,1e-8), -r) == web row r
    const d=-(N[0]*V[0]+N[1]*V[1]+N[2]*V[2]),R=N.map((x,k)=>-V[k]-2*d*x),m=Math.max(...R.map(Math.abs));
    const nov=Math.max(N[0]*V[0]+N[1]*V[1]+N[2]*V[2],1e-8),b=brdf([nov,r]),c=ink(R.map(x=>x/m));
    const nat=c.slice(0,3).map(x=>x*(b[0]*.015+b[1]));
    assert.ok(rel(web,nat)<=2e-6,`${web} vs ${nat}`);
  }
  const {applyInkSurface}=await import('../client/render/ink_surface.ts');
  const {applyForward}=await import('../client/render/forward.ts');
  const THREE=await import('three');
  const mat=new THREE.MeshStandardMaterial(),lighting=new LightingState();
  applyForward(mat,{shader:{archive:'Hoian_UBER',options:{enable_shading:'True'}}},lighting,null);
  applyInkSurface(mat,{texture:new THREE.DataTexture(new Uint8Array([0,0,0,255]),1,1),ink:[[1,0,0],[0,1,0],[0,0,1]],inkBright:[[1,1,0],[0,1,1],[1,0,1]],textureStep:[1/128,0],emission:.125});
  const sh={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
  mat.onBeforeCompile(sh,{});
  assert.ok(sh.fragmentShader.includes('(hInkSurface.isInk?hNativeInkSpecular(hN,hV,hF0,hR):hNativeEnvSpecular(hN,hV,hF0,hR))'));
  assert.ok(sh.fragmentShader.indexOf('vec3 hPrefilInkSample')>sh.fragmentShader.indexOf('uniform sampler2D hPrefilAtlas,hEnvBRDF'));
  assert.ok(!/samplerCube hPrefilInk/.test(sh.fragmentShader));
  assert.equal(sh.uniforms.hPrefilInkAvailable,lighting.env.uniforms.hPrefilInkAvailable);
});
