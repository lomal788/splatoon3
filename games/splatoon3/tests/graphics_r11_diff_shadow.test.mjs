import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {nativeStaticShadowFit,webStaticShadowMatrix,nativeStaticShadowBounds,nativeStaticShadowVisibility,nativeStaticShadowFarFade,
  NATIVE_STATIC_SHADOW_SETTINGS,NATIVE_SHADOW_PREPASS_DEFAULT_ENV,NATIVE_SHADOW_PREPASS_DEFAULTS,NATIVE_VSM_BLUR,SHADOW_GLSL,NativeShadowState,applyNativeDepthShadowFlags} from '../client/render/shadows.ts';

const fit=JSON.parse(readFileSync(new URL('./fixtures/r11_static_shadow_fit_native.json',import.meta.url),'utf8'));
const probe=JSON.parse(readFileSync(new URL('../../../../analysis/port_common_r6/shadow/native_probe.json',import.meta.url),'utf8'));
const depth=JSON.parse(readFileSync(new URL('../assets/maps/Lby_Lobby00/data/depth_shadow.json',import.meta.url),'utf8'));
const bits=v=>new Uint32Array(new Float32Array([v]).buffer)[0];

test('static shadow fit matches original 7103754FE8 (+ sead LookAtCamera/OrthoProjection) bit for bit',()=>{
  assert.equal(fit.cases.length,49);
  for(const c of fit.cases){
    const o=nativeStaticShadowFit(c.min,c.max,c.dir);
    for(const k of ['view','proj','tex'])o[k].forEach((v,i)=>assert.equal(bits(v),bits(c.out[k][i]),`${c.name} ${k}[${i}]`));
    [o.ortho.near,o.ortho.far,o.ortho.top,o.ortho.bottom,o.ortho.left,o.ortho.right].forEach((v,i)=>assert.equal(bits(v),bits(c.out.ortho[i]),`${c.name} ortho[${i}]`));
  }
});

test('web static matrix samples the same texel as the native NVN texture matrix (v_gl = 1 - v_nvn)',()=>{
  for(const c of fit.cases.slice(0,12)){
    const o=nativeStaticShadowFit(c.min,c.max,c.dir),m=webStaticShadowMatrix(o),t=c.out.tex;
    const center=c.min.map((v,i)=>(v+c.max[i])/2);
    for(const s of [[0,0,0],[.4,-.3,.2],[-.45,.45,-.1]]){
      const p=new THREE.Vector3(...center.map((v,i)=>v+s[i]*(c.max[i]-c.min[i])));
      const q=p.clone().applyMatrix4(m),row=r=>t[r*4]*p.x+t[r*4+1]*p.y+t[r*4+2]*p.z+t[r*4+3];
      assert.ok(Math.abs(q.x-row(0))<1e-5);assert.ok(Math.abs(q.y-(1-row(1)))<1e-5);assert.ok(Math.abs(q.z-row(2))<1e-5);
      for(const v of [q.x,q.y,q.z])assert.ok(v>=-1e-5&&v<=1+1e-5,`${c.name} inside AABB maps into [0,1]`);
    }
    const g=new THREE.OrthographicCamera(o.ortho.left,o.ortho.right,o.ortho.top,o.ortho.bottom,o.ortho.near,o.ortho.far);
    g.updateProjectionMatrix();g.projectionMatrix.elements.forEach((v,i)=>{const r=i%4,col=(i/4)|0;assert.ok(Math.abs(v-o.proj[r*4+col])<=Math.abs(v)*1e-6+1e-7);});
  }
});

test('static caster AABB is the f32 union of shape spheres (710374F950) and empty input keeps no fit',()=>{
  assert.equal(nativeStaticShadowBounds([]),null);
  const b=nativeStaticShadowBounds([[1,2,3,.5],[-4,0,10,2]]);
  assert.deepEqual(b,{min:[-6,-2,2.5],max:[1.5,2.5,12]});
});

test('v216 Chebyshev visibility keeps strict lit test, no variance floor and unclamped static fade sum',()=>{
  const fade=nativeStaticShadowFarFade(NATIVE_SHADOW_PREPASS_DEFAULT_ENV,2000);assert.deepEqual(fade,[40,Math.fround(1/20)]);
  assert.equal(nativeStaticShadowVisibility([.5,.25],.5,10,fade),1);
  assert.equal(nativeStaticShadowVisibility([.5,.25],.6,10,fade),0);
  const F=Math.fround,m1=.4,m2=F(.4*.4+.01),d=.5,varc=F(F(m1)*-F(m1)+m2),t=F(d-F(m1));
  const want=F(varc*F(1/F(t*t+varc)));
  assert.equal(bits(nativeStaticShadowVisibility([m1,m2],d,10,fade)),bits(Math.fround(0+want)));
  assert.equal(nativeStaticShadowVisibility([.5,.25],.6,50,fade),Math.fround(.5));
  assert.equal(nativeStaticShadowVisibility([.5,.25],.4,60,fade),2);
  assert.equal(nativeStaticShadowVisibility([.5,.25],7,10,fade),0,'ref depth min(z,1)');
});

test('static far fade matches original 3764908 static outputs (frame +1424/+1428) bit for bit',()=>{
  let n=0;
  for(const c of probe.writer.results)if(c.enabled){
    const o=nativeStaticShadowFarFade({useFarFade:c.farFade,staticFarFadeStart:c.staticStart,staticFarFadeEnd:c.staticEnd},c.far);
    assert.equal(bits(o[0]),bits(c.output[6]),`case ${c.case}`);assert.equal(bits(o[1]),bits(c.output[7]),`case ${c.case}`);n++;
  }
  assert.equal(n,877);
});

test('static depth shadow caster table comes from original renderInfo (truss is a static, not dynamic, caster)',()=>{
  const v=depth.models.Fld_VSLobby;
  assert.equal(Object.keys(v).length,50);assert.equal(Object.values(v).filter(m=>m.gsys_static_depth_shadow===1).length,48);
  assert.deepEqual(v.TrussYellow,{gsys_static_depth_shadow:1,gsys_static_depth_shadow_only:0,gsys_dynamic_depth_shadow:0,gsys_dynamic_depth_shadow_only:0});
  assert.equal(v.SadowMtl00.gsys_static_depth_shadow_only,1);
  assert.equal(Object.values(depth.models.FldBG_LobbyDV).every(m=>m.gsys_static_depth_shadow===0),true);
  assert.equal(depth.missing.length,0);
});

test('static map settings and vsm blur constants are the original data, wired into the shared SPP max consumer',()=>{
  assert.equal(NATIVE_STATIC_SHADOW_SETTINGS.width,2048);assert.equal(NATIVE_STATIC_SHADOW_SETTINGS.blurIterations,3);
  assert.equal(NATIVE_VSM_BLUR.weights.reduce((a,w,i)=>a+w*(i?2:1),0),4096);
  assert.match(SHADOW_GLSL,/float hStaticShadowVisibility\(vec3 worldPos,float positiveViewDepth\)/);
  assert.match(SHADOW_GLSL,/return vec2\(dyn,hStaticShadowVisibility\(worldPos,positiveViewDepth\)\)/);
});

const v216=readFileSync(new URL('../../../../analysis/port_common_r6/shadow/prepass/v216.pixel.glsl',import.meta.url),'utf8');
const vsmPix=readFileSync(new URL('../../../../analysis/gfx_r11/probe/shadow/vsm/vsm__PASS-1_SAMPLER_2D_ARRAY-0.pixel.glsl',import.meta.url),'utf8');
const vsmVert=readFileSync(new URL('../../../../analysis/gfx_r11/probe/shadow/vsm/vsm__PASS-1_SAMPLER_2D_ARRAY-0.vertex.glsl',import.meta.url),'utf8');

test('v216 original expression vs CPU helper and the web GLSL branch form agree on sampled moments',()=>{
  assert.match(v216,/temp_13 = fma\(temp_11, \(0\.0 - temp_11\), temp_10\.y\)/);
  assert.match(v216,/max\(temp_12 <= temp_11 \? 1\.0 : 0\.0, min\(temp_13 \* \(1\.0 \/ fma\(temp_12 \+ \(0\.0 - temp_11\), temp_12 \+ \(0\.0 - temp_11\), temp_13\)\), 1\.0\)\)/);
  const F=Math.fround,fade=[40,F(1/20)];let n=0;
  for(let i=0;i<4000;i++){
    const m1=F(((i*7919)%1000)/1000),varc=F(((i*104729)%997)/997*.01),m2=F(m1*m1+varc),d=F(((i*31337)%1100)/1000),depth=(i%80);
    const fmaF=(a,b,c)=>F(a*b+c),t13=fmaF(m1,-m1,m2),t12=Math.min(d,1);
    const minN=(a,b)=>Number.isNaN(a)?b:Math.min(a,b),maxN=(a,b)=>Number.isNaN(a)?b:Math.max(a,b);
    const orig=F(Math.min(Math.max(F((depth-40)*fade[1]),0),1)+maxN(t12<=m1?1:0,minN(F(t13*F(1/fmaF(F(t12-m1),F(t12-m1),t13))),1)));
    const cpu=nativeStaticShadowVisibility([m1,m2],d,depth,fade);
    assert.equal(bits(cpu),bits(orig),`${i}: ${orig} vs ${cpu}`);
    const t=F(t12-m1),web=Math.min(Math.max((depth-40)*fade[1],0),1)+(t12<=m1?1:Math.max(0,Math.min(t13/(t*t+t13),1)));
    assert.ok(Math.abs(web-orig)<1e-5,`web ${i}: ${web} vs ${orig}`);n++;
  }
  assert.equal(n,4000);
});

test('web vsm blur shader carries the original vsm PASS1 taps and weights',()=>{
  for(const k of ['1.38460004','3.23077011','5.07690001'])assert.ok(vsmVert.includes(k),k);
  for(const k of ['13.0','286.0','1287.0','924.0','0.000245700008'])assert.ok(vsmPix.includes(k),k);
  const src=new NativeShadowState().staticShadow;const frag=src['blur'].fragmentShader;
  for(const k of ['1.38460004','3.23077011','5.07690001','*13.','*286.','*1287.','*924.','.000245700008'])assert.ok(frag.includes(k),k);
  const copy=src['copy'].fragmentShader;assert.match(copy,/vec4\(d,d\*d,0\.,1\.\)/);
});

test('far depth test: BlitzUBO0[36].z = ShadowPrePass is_farDepthTestDist (Default 60) gates SPP occlusion in Hoian',()=>{
  const prog=readFileSync(new URL('../../../../analysis/gfx4/programs/Fld_VSLobby__LobbyFloorConcrete.frag',import.meta.url),'utf8');
  assert.ok(prog.includes('fma(max(0.0 - temp_77.x + 1.0, 0.0 - temp_77.y + 1.0), clamp(in_attr3.w + BlitzUBO0.data[36].z, 0.0, 1.0)'));
  assert.equal(NATIVE_SHADOW_PREPASS_DEFAULTS.farDepthTestDist,1000);assert.equal(NATIVE_SHADOW_PREPASS_DEFAULT_ENV.farDepthTestDist,60);
  const s=new NativeShadowState();s.configure(null);assert.equal(s.uniforms.hShadowFarDepthTest.value,60);
  assert.match(SHADOW_GLSL,/max\(1\.-spp\.x,1\.-spp\.y\)\*clamp\(hShadowFarDepthTest-positiveViewDepth,0\.,1\.\)/);s.dispose();
});

function mockRenderer(){
  return {target:null,autoClear:false,toneMapping:THREE.ACESFilmicToneMapping,shadowMap:{autoUpdate:true},viewport:new THREE.Vector4(1,2,300,200),scissor:new THREE.Vector4(),scissorTest:true,
    color:new THREE.Color(.1,.2,.3),alpha:.5,draws:[],extensions:{has:n=>n==='OES_texture_float_linear'},
    getRenderTarget(){return this.target},setRenderTarget(t){this.target=t},getViewport(v){return v.copy(this.viewport)},setViewport(v){this.viewport.copy(v)},
    getScissor(v){return v.copy(this.scissor)},setScissor(v){this.scissor.copy(v)},getScissorTest(){return this.scissorTest},setScissorTest(v){this.scissorTest=v},
    getClearColor(c){return c.copy(this.color)},getClearAlpha(){return this.alpha},setClearColor(c,a){this.color.set(c);this.alpha=a},clear(){},
    render(scene,camera){this.draws.push({target:this.target,n:scene.children.length,camera})}};
}

test('static capture: depth -> copy -> 3x2 blur passes, native matrices on the light camera, static_only gobo hidden and not cast',()=>{
  const scene=new THREE.Scene(),model=new THREE.Group();model.userData.originalModelName='Fld_VSLobby';scene.add(model);
  const mk=(name,pos)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(2,1,2),new THREE.MeshStandardMaterial({name}));m.userData.material=name;m.position.set(...pos);model.add(m);return m;};
  const truss=mk('TrussYellow',[0,8,0]),gobo=mk('SadowMtl00',[5,9,0]),water=mk('Water00',[0,0,0]);
  const counts=applyNativeDepthShadowFlags(scene,depth);
  assert.deepEqual(counts,{static:1,staticOnly:1,dynamic:0});assert.equal(gobo.visible,false);assert.equal(gobo.userData.staticDepthShadow,undefined);assert.equal(truss.userData.staticDepthShadow,true);assert.equal(water.userData.staticDepthShadow,undefined);
  const s=new NativeShadowState();s.configure(null);const r=mockRenderer(),cam=new THREE.PerspectiveCamera(48,16/9,.1,2000);
  s.capture(r,scene,cam,[.0431,-.5664,-.823]);
  const st=s.staticShadow;assert.equal(st.stats.casters,1);assert.equal(st.stats.blurPasses,6);assert.equal(r.draws.length,8);
  assert.equal(r.draws[0].n,1,'static_only gobo is not a runtime static caster');assert.equal(s.uniforms.hStaticShadowAvailable.value,1);
  const {spheres}=st.collect(scene),b=nativeStaticShadowBounds(spheres),d=new THREE.Vector3(.0431,-.5664,-.823).normalize();
  const want=nativeStaticShadowFit(b.min,b.max,d.toArray());assert.deepEqual(st.fit.tex,want.tex);
  assert.deepEqual(s.uniforms.hStaticShadowMatrix.value.elements,webStaticShadowMatrix(want).elements);
  const lightCam=r.draws[0].camera;want.proj.forEach((v,i)=>assert.equal(lightCam.projectionMatrix.elements[(i%4)*4+((i/4)|0)],v));
  assert.equal(r.target,null);assert.equal(r.autoClear,false);assert.equal(r.scissorTest,true);assert.deepEqual(r.viewport.toArray(),[1,2,300,200]);
  assert.deepEqual(s.uniforms.hStaticShadowFarFade.value.toArray(),[40,Math.fround(1/20)]);
  s.capture(r,scene,cam,[.0431,-.5664,-.823]);assert.equal(r.draws.length,8,'static map is rendered once (is_useUpdatableStaticDepthShadow false)');
  s.dispose();
});
