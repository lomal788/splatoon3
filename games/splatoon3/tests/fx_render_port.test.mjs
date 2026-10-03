import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as THREE from "three";
import { ParticleBatch, EmitterInstance, identityMatrix } from "../client/fx/particles.ts";
import { shaderAlpha, vatColumns, decodeVatNormal, animationTime, sampleKey } from "../client/fx/shader_contract.ts";
import { applyEmitterRender } from "../client/fx/render_state.ts";
const fixture=JSON.parse(readFileSync(new URL("./fixtures/fx_native_port.json",import.meta.url)));
const near=(a,b,t=1e-10)=>assert(Math.abs(a-b)<t,`${a} != ${b}`);

test("eight original alpha consumers differ for the same inputs; alpha1 cannot substitute a missing varying",()=>{
 const expected=new Map([[1940,.042],[1897,.0825],[1885,.33],[1886,.33],[1747,.063],[1202,.0288],[1383,.09],[1385,.09]]);
 for(const [program,raw] of expected){const a=shaderAlpha(program,.7,.8,.4,.6,.2,3,.5,.25,.9,[2,-.01]);near(a.raw,raw);near(a.out,2*raw-.01);}
 near(shaderAlpha(1940,.7,.8,.4,.6,.2,100,.5,.25,.9).raw,.042);
 near(shaderAlpha(1385,.7,.8,.4,.6,.2,100,.5,.25,.9).raw,.09);
});
test("VAT reaches last column and remains there; does not loop with lifetime",()=>{
 const at0=vatColumns(6,0,1);assert.equal(at0.x0,0);assert.equal(at0.x1,1);near(at0.blend,.00006);
 const end=vatColumns(6,12,1);assert.equal(end.x0,5);assert.equal(end.x1,5);near(end.blend,.99994);
 assert.deepEqual(vatColumns(6,120,1),end);assert.deepEqual(vatColumns(6,12000,1),end);
 const mid=vatColumns(8,6,.5);assert.equal(mid.x0,3);assert.equal(mid.x1,4);near(mid.blend,.00007625000468758358,1e-12);
});
test("finite native VAT half goldens use polar component on local Y without normalization",()=>{
 assert.equal(fixture.normal.length,16);
 for(const row of fixture.normal)decodeVatNormal(row.half).forEach((v,i)=>near(v,row.normal[i],1e-8));
});
test("independent channel loop periods and HOLD key type preserve endpoints",()=>{
 near(animationTime(3,10,.5,0,2),.3);near(animationTime(3,10,.5,4,0),.75);near(animationTime(3,10,.5,2,0),.5);
 const keys=[[2,3,4,.2],[6,9,12,.8]];
 assert.deepEqual(sampleKey(keys,.1,1),[2,3,4]);assert.deepEqual(sampleKey(keys,.5,1),[2,3,4]);assert.deepEqual(sampleKey(keys,.8,1),[6,9,12]);
 sampleKey(keys,.5).forEach((x,i)=>near(x,[4,6,8][i]));
});
test("39 original emitter descriptors and all four animation channels reach the actual material",()=>{
 for(const row of fixture.rows){const b=new ParticleBatch(row.key,row.def,2,null,null,false),u=b.uniforms,m=b.mesh.material,r=row.def.nativeRender;
  assert.equal(m.transparent,!!r.blendEnable);assert.equal(m.depthWrite,!!r.depthWrite);assert.equal(m.depthTest,!!r.depthTest);
  assert.equal(m.side,r.cullMode===1?THREE.FrontSide:r.cullMode===2?THREE.BackSide:THREE.DoubleSide);
  assert.equal(u.uColorK.value[0].x,row.def.color0Keys[0][0]);assert.equal(u.uColor1K.value[0].x,row.def.color1Keys[0][0]);
  assert.equal(u.uAlphaK.value[0].x,row.def.alpha0Keys[0][0]);assert.equal(u.uAlpha1K.value[0].x,row.def.alpha1Keys[0][0]);
  assert.equal(u.uScaleN.value,row.def.numScaleKeys);assert.equal(u.uAlpha1N.value,row.def.numAlpha1Keys);
  b.dispose();
 }
});
test("native depth/cull and all six blend descriptor adapters retain separate RGB/alpha factors",()=>{
 const rows=[[THREE.SrcAlphaFactor,THREE.OneMinusSrcAlphaFactor,THREE.OneFactor,THREE.OneMinusSrcAlphaFactor,THREE.AddEquation],[THREE.SrcAlphaFactor,THREE.OneFactor,THREE.OneFactor,THREE.OneFactor,THREE.AddEquation],[THREE.SrcAlphaFactor,THREE.OneFactor,THREE.OneFactor,THREE.OneFactor,THREE.ReverseSubtractEquation],[THREE.ZeroFactor,THREE.SrcColorFactor,THREE.ZeroFactor,THREE.SrcColorFactor,THREE.AddEquation],[THREE.OneMinusDstColorFactor,THREE.OneFactor,THREE.OneMinusDstColorFactor,THREE.OneFactor,THREE.AddEquation],[THREE.OneFactor,THREE.OneMinusSrcAlphaFactor,THREE.OneFactor,THREE.OneMinusSrcAlphaFactor,THREE.AddEquation]];
 for(let mode=0;mode<6;mode++){const m=new THREE.ShaderMaterial();applyEmitterRender(m,{nativeRender:{blendEnable:true,depthTest:true,depthWrite:false,depthCompare:3,cullMode:1,blendMode:mode}});
  assert.equal(m.blending,THREE.CustomBlending);assert.deepEqual([m.blendSrc,m.blendDst,m.blendSrcAlpha,m.blendDstAlpha,m.blendEquation],rows[mode]);assert.equal(m.depthFunc,THREE.LessEqualDepth);m.dispose();}
});
test("primitive attributes survive; VAT is disabled without original row and enabled only with row+slot2",()=>{
 const g=new THREE.PlaneGeometry(1,1),count=g.getAttribute("position").count;
 g.setAttribute("color",new THREE.BufferAttribute(Float32Array.from({length:count*4},(_,i)=>i%4===3?.25:.5),4));
 g.setAttribute("tangent",new THREE.BufferAttribute(Float32Array.from({length:count*4},(_,i)=>i%4===0||i%4===3?1:0),4));
 g.setAttribute("uv1",new THREE.BufferAttribute(Float32Array.from({length:count*2},(_,i)=>i%2),2));
 const vat=new THREE.DataTexture(new Uint16Array(6*4*4),6,4,THREE.RGBAFormat,THREE.HalfFloatType);
 const make=()=>new ParticleBatch("test",{...fixture.rows.find(r=>r.def.shaderIndex===1383).def},2,null,g,false,{samplers:new Map([[2,vat]])});
 let b=make();for(const k of ["normal","tangent","color","uv1"])assert.equal(b.mesh.geometry.getAttribute(k),g.getAttribute(k));
 assert.equal(b.uniforms.uHasVat.value,1);assert.equal(b.mesh.geometry.getAttribute("vatRow").getX(1),0);
 assert.equal(b.mesh.geometry.getAttribute("fxVertexColor").getW(0),.25);b.dispose();
 g.deleteAttribute("uv1");b=make();assert.equal(b.uniforms.uHasVat.value,0);b.dispose();
 g.setAttribute("vatRow",new THREE.BufferAttribute(new Float32Array([2,0,3,1]),1));b=make();assert.equal(b.uniforms.uHasVat.value,1);assert.equal(b.mesh.geometry.getAttribute("vatRow").getX(0),2);b.dispose();g.dispose();vat.dispose();
});
test("particle texture contains birth/matrix/alive state; POS changes origin without replacing birth axes",()=>{
 const b=new ParticleBatch("test",{life:10,emitRate:1,hasEmitEnd:0,followType:2},2,null,null,false);
 const i=new EmitterInstance(b,identityMatrix([1,2,3]),[.1,.2,.3],0,0);i.step(0,()=>.5);
 const data=b.uniforms.uParticles.value.image.data;assert.deepEqual(Array.from(data.slice(0,3)),[1,2,3]);assert.equal(data[7*4+3],1);
 i.setMatrix({o:[4,5,6],x:[0,1,0],y:[1,0,0],z:[0,0,-1]});b.followPosition(i);
 assert.deepEqual(Array.from(data.slice(0,3)),[4,5,6]);assert.deepEqual(Array.from(data.slice(4,7)),[1,0,0]);i.kill();assert.equal(data[7*4+3],0);b.dispose();
});
test("zero/fractional emission does not invent one particle every interval",()=>{
 const b=new ParticleBatch("test",{life:10,emitRate:.25,hasEmitEnd:0,emitInterval:0},4,null,null,false),i=new EmitterInstance(b,identityMatrix([0,0,0]),[1,1,1],0,0);
 for(let t=0;t<3;t++)i.step(t,()=>.5);const data=b.uniforms.uParticles.value.image.data;assert.equal(data[7*4+3],0);
 i.step(3,()=>.5);assert.equal(data[7*4+3],1);b.dispose();
});

test("incomplete legacy loader cannot activate subtraction alpha shader with fabricated keys",()=>{const b=new ParticleBatch("legacy",{shaderIndex:1897},2,null,null,false);assert.equal(b.uniforms.uProgram.value,0);assert.equal(b.mesh.material.userData.contractInputsReady,false);b.dispose();});

test("native Res cull1 removes BACK, cull2 removes FRONT, with CCW front winding",()=>{
 for(const [res,nvn,side] of [[0,0,THREE.DoubleSide],[1,2,THREE.FrontSide],[2,1,THREE.BackSide]]){
  const m=new THREE.ShaderMaterial();applyEmitterRender(m,{nativeRender:{cullMode:res}});assert.equal(m.side,side);
  // Independent r8 setter value -> SDK enum labels:2 BACK,1 FRONT.
  assert.equal(nvn===2?"BACK":nvn===1?"FRONT":"NONE",res===1?"BACK":res===2?"FRONT":"NONE");m.dispose();
 }
});
