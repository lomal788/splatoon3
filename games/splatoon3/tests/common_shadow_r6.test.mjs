import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {NativeShadowState,NATIVE_SHADOW_PREPASS_DEFAULTS,NATIVE_SHADOW_PREPASS_DEFAULT_ENV,nativeShadowShaderType,nativeShadowFarFade} from '../client/render/shadows.ts';
const probe=JSON.parse(readFileSync(new URL('../../../../analysis/port_common_r6/shadow/native_probe.json',import.meta.url),'utf8'));
const bits=v=>new Uint32Array(new Float32Array([v]).buffer)[0];
const env=JSON.parse(readFileSync(new URL('../../../../analysis/port_common_r6/shadow/default_shadow.json',import.meta.url),'utf8'));

test('prepass defaults match original CRC named constructor value stores',()=>{
  const fields=new Map(probe.ctor.fields.map(f=>[f.name,f]));
  for(const [key,name,kind] of [['filterShaderType','is_PcfShaderType','u32'],['filterSampleNum','is_PcfSampleNum','u32'],['pcfWidth','pcfWidth','f32'],['dynamicFarFadeStart','dynamicShadowFarFadeStart','f32'],['dynamicFarFadeEnd','dynamicShadowFarFadeEnd','f32']]){
    const actual=fields.get(name);assert.ok(actual,name);assert.equal(NATIVE_SHADOW_PREPASS_DEFAULTS[key],kind==='u32'?Number(actual.u32):actual.f32);
  }
  assert.equal(NATIVE_SHADOW_PREPASS_DEFAULTS.useFarFade,false);assert.equal(Number(fields.get('is_useFarFade').u32),0);
});

test('kernel selector matches original isolated 3768940..376895C block',()=>{
  assert.equal(probe.variantBlock.pass,24);
  for(const c of probe.variantBlock.cases)assert.equal(nativeShadowShaderType({filterShaderType:c.type,filterSampleNum:c.sampleNum}),c.shaderType);
});

test('Default AAMP overrides replace constructor fade and remain separate from runtime selection',()=>{
  const fields=new Map(env.files[0].entries.map(f=>[f.name,f]));
  for(const [key,name] of [['filterShaderType','is_PcfShaderType'],['filterSampleNum','is_PcfSampleNum'],['pcfWidth','pcfWidth'],['useFarFade','is_useFarFade'],['dynamicFarFadeStart','dynamicShadowFarFadeStart'],['dynamicFarFadeEnd','dynamicShadowFarFadeEnd']])assert.equal(NATIVE_SHADOW_PREPASS_DEFAULT_ENV[key],fields.get(name).value);
  assert.equal(NATIVE_SHADOW_PREPASS_DEFAULTS.useFarFade,false);
  assert.deepEqual(nativeShadowFarFade(NATIVE_SHADOW_PREPASS_DEFAULT_ENV,2000),[40,Math.fround(1/20)]);
  const s=new NativeShadowState();s.configure({rendering:{Shadow:{ProjShadow:{Density:0}}}});
  const camera=new THREE.PerspectiveCamera(60,1,.2,2000);
  s.capture({},new THREE.Scene(),camera,[0,-1,0]);
  assert.deepEqual(s.uniforms.hShadowFarFade.value.toArray(),[40,Math.fround(1/20)]);
  s.dispose();
});

test('far fade helper matches whole original 3764908 output floats bit for bit',()=>{
  assert.equal(probe.writer.pass,1024);assert.equal(probe.writer.fail,0);
  let compared=0;
  for(const c of probe.writer.results)if(c.enabled){
    const out=nativeShadowFarFade({useFarFade:c.farFade,dynamicFarFadeStart:c.start,dynamicFarFadeEnd:c.end},c.far);
    assert.equal(bits(out[0]),bits(c.output[4]),`case ${c.case} start`);assert.equal(bits(out[1]),bits(c.output[5]),`case ${c.case} mul`);compared++;
  }
  assert.equal(compared,877);
});

test('prepass parameter overrides preserve defaults and reject degenerate frame settings',()=>{
  const s=new NativeShadowState();assert.equal(s.uniforms.hShadowKernel.value,0);assert.equal(s.uniforms.hShadowBias.value,5);
  for(let n=0;n<3;n++){s.configurePrePass({...NATIVE_SHADOW_PREPASS_DEFAULTS,filterShaderType:1,filterSampleNum:n,pcfWidth:3});assert.equal(s.uniforms.hShadowKernel.value,n+1);assert.equal(s.uniforms.hShadowBias.value,3);}
  assert.throws(()=>s.configurePrePass({...NATIVE_SHADOW_PREPASS_DEFAULTS,useFarFade:true,dynamicFarFadeStart:100,dynamicFarFadeEnd:100}),/Invalid shadow/);
  s.dispose();
});
