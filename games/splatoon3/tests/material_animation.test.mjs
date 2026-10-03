import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {sampleNativeMaterialCurve,sampleMaterialClip,materialClipInfo,patchTexSrt,nativeSkinIndex,sampleOrdinaryMaterialLeaves} from '../client/render/anim/material_channels.ts';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const bank=read('./fixtures/material_animation_r9_channels.json');
const native=read('./fixtures/material_animation_r9_native.json');
const bits=v=>new Uint32Array(new Float32Array([v]).buffer)[0];
test('actual raw material channels match 1,212 original float/int curve executions',()=>{
 for(const x of native.samples) {
  const clip=bank.groups[x.group].clips.find(c=>c.name===x.clip);
  const c=clip.materials.find(m=>m.material===x.material).curves[x.curve];
  const value=sampleNativeMaterialCurve(c,x.frame);
  assert.equal(x.integer?value>>>0:bits(value),x.result,`${x.group}/${x.clip}/${x.curve}@${x.frame}`);
 }
 assert.equal(native.samples.length,1212);assert.deepEqual(native.faults,[]);assert.deepEqual(native.pltStubs,[]);
});
test('original Color_Skin initialized holder bounds preserve rejected frame (67 executions)',()=>{
 for(const x of native.skin) {
  const r=nativeSkinIndex(NaN,x.index,x.frames);
  const accepted=x.holder!==0x5a5a5a5a;
  assert.equal(r.accepted,accepted);
  if(accepted){assert.equal(bits(r.frame),x.frameBits);assert.deepEqual(x.calls,['anim_apply','model_flags','model_material','model_skeletal']);}
  else assert.deepEqual(x.calls,[]);
 }
 assert.equal(native.skin.length,67);
});
test('type11 metadata is FMAA-specific and does not turn ToHuman skeletal metadata into a material leaf',()=>{
 assert.deepEqual(materialClipInfo(bank.groups.Player_Squid,'Sqd_Wait'),{frames:120,loop:true});
 assert.deepEqual(materialClipInfo(bank.groups.Player_Squid,'Sqd_Surprise'),{frames:30,loop:false});
 assert.equal(materialClipInfo(bank.groups.Player_Squid,'Sqd_ToSquid'),null);
 assert.equal(sampleOrdinaryMaterialLeaves(bank.groups.Player_Squid,[{type:3,clip:'Sqd_ToHuman',frame:1,weight:1}]),null);
 assert.equal(sampleOrdinaryMaterialLeaves(bank.groups.Player_Squid,[{type:11,clip:'Sqd_Wait',frame:1,weight:.5}]).supported,false);
});
test('actual squid eye SRT and three texture patterns preserve raw integer offset9',()=>{
 const r=sampleMaterialClip(bank.groups.Player_Squid,'Sqd_Surprise',3);
 assert.equal(r.supported,true);
 assert.deepEqual(r.patches[0].patterns,{_a0:'M_Eye_Alb.3',_n0:'M_Eye_Nrm.3',_r0:'M_Eye_Rgh.3'});
 const mat=bank.groups.Player_Squid.materials.find(m=>m.name==='M_Eye');
 const s=patchTexSrt(mat.params.tex_mtx0.value,r.patches[0].params.tex_mtx0);
 assert.equal(s.Mode,'ModeMaya');assert.equal(s.Rotation,0);assert.ok(s.Scaling.X>1.7);assert.ok(s.Translation.Y>.17);
 const wait=sampleMaterialClip(bank.groups.Player_Squid,'Sqd_Wait',30);
 assert.equal(wait.supported,true);assert.equal(wait.patches[0].params.tex_mtx0['0x04'],1);
});
test('unsupported wrap/missing data remains explicit; skin sample contains no CP intensity channel',()=>{
 const r=sampleMaterialClip(bank.groups.Player00,'Color_Skin',3);
 assert.equal(r.supported,true);assert.equal(r.patches.length,2);
 assert.equal(r.patches[0].params.two_color_complement_paint_intensity,undefined);
 assert.equal(sampleMaterialClip(bank.groups.Player_Squid,'NotAvailable',0).supported,false);
 const c=bank.groups.Player_Squid.clips.find(c=>c.name==='Sqd_Surprise').materials[0].curves[0];
 assert.throws(()=>sampleNativeMaterialCurve({...c,post:'Repeat'},31),/unsupported/);
 assert.throws(()=>sampleNativeMaterialCurve(c,NaN),/finite/);
});
