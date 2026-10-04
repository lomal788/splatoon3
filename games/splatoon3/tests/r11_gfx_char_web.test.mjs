// r11 gfx-char web wiring: owner-scoped textures, native linear data textures, Color_Skin/Color_Eye holders,
// lobby team row, hat slot49 inverse, JumpVarID, tank Gauge data. Original-data checks; no invented values.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {textureResolver,headInverse,manualBindSrt,nativeLinearTextureName} from '../client/render/model.ts';
import {nativeHolderClipFrame,sampleMaterialClip,writeNativeMaterialParam,sampleNativeMaterialCurve} from '../client/render/anim/material_channels.ts';
import {selectLobbyTeamRow,lobbyTeamRow,SeadRandom,seadRandomIndex} from '../client/render/teamcolor.ts';
import {nativeJumpVarId} from '../client/render/anim/jump_var.ts';
import {TankGauge} from '../client/render/anim/tank_gauge.ts';

const A=new URL('../assets/characters/Player00/',import.meta.url);
const json=p=>JSON.parse(readFileSync(new URL(p,A),'utf8'));
const glbJson=p=>{const b=readFileSync(new URL(p,A));const n=b.readUInt32LE(12);return JSON.parse(b.subarray(20,20+n).toString());};
const F=Math.fround;

test('owner folder wins over the first same-named bundle file (Har/Eyb/body M_TeamColor_Tcl, squid M_Body_2cl)',async()=>{
  const files=json('../../catalog.json').bundles['character/Player00'].files;
  const bundle={has:n=>files.includes(n),names:()=>files,texture:async n=>Object.assign(new THREE.Texture(),{name:n})};
  const hair=textureResolver(null,bundle,'Har_SQD000_F'),body=textureResolver(null,bundle,'body'),squid=textureResolver(null,bundle,'squid');
  assert.equal((await hair('M_TeamColor_Tcl')).name,'tex/Har_SQD000_F/M_TeamColor_Tcl.ktx2');
  assert.equal((await hair('M_TeamColor_2cl')).name,'tex/Har_SQD000_F/M_TeamColor_2cl.ktx2');
  assert.equal((await body('M_TeamColor_Tcl')).name,'tex/body/M_TeamColor_Tcl.ktx2');
  assert.equal((await squid('M_Body_2cl')).name,'tex/squid/M_Body_2cl.ktx2');
  assert.equal((await squid('M_Body_Thc')).name,'tex/resources/squid/M_Body_Thc.ktx2');
  assert.equal((await squid('M_Body_Trm')).name,'tex/resources/squid/M_Body_Trm.ktx2');
  // Previous unscoped behaviour picked the eyebrow mask for the hair:
  assert.equal(files.find(n=>n.endsWith('/M_TeamColor_Tcl.ktx2')),'tex/Eyb_SQD000_F/M_TeamColor_Tcl.ktx2');
});

test('squid Thc/Trm resources keep original BC4_UNORM linear / BC1_SRGB transfer and 256² size (Player_Squid BNTX meta)',()=>{
  for(const [n,tf] of [['M_Body_Thc',1],['M_Body_Trm',2]]){
    const b=readFileSync(new URL(`tex/resources/squid/${n}.ktx2`,A));
    assert.equal(b.readUInt32LE(20),256);assert.equal(b.readUInt32LE(24),256);assert.equal(b[b.readUInt32LE(48)+14],tf);
  }
});

test('Emm/Tcl are native linear data: sRGB-tagged embedded KTX2 is sampled as stored values',async()=>{
  for(const n of ['M_Eye_Emm','M_TeamColor_Emm','M_Glass_Emm','M_Body_Tcl','M_TeamColor_Tcl'])assert.ok(nativeLinearTextureName(n));
  for(const n of ['M_Body_Alb','M_Body_Trm','M_Body_Emi','M_FST000_MltA'])assert.ok(!nativeLinearTextureName(n));
  const srgb=Object.assign(new THREE.Texture(),{colorSpace:THREE.SRGBColorSpace});
  const gltf={parser:{json:{images:[{name:'M_Eye_Emm'}],textures:[{source:0}]},getDependency:async()=>srgb}};
  assert.equal((await textureResolver(gltf,null,undefined,true)('M_Eye_Emm')).colorSpace,THREE.NoColorSpace);
  const untouched=Object.assign(new THREE.Texture(),{colorSpace:THREE.SRGBColorSpace});
  const g2={parser:{json:{images:[{name:'M_Eye_Emm'}],textures:[{source:0}]},getDependency:async()=>untouched}};
  assert.equal((await textureResolver(g2,null)('M_Eye_Emm')).colorSpace,THREE.SRGBColorSpace,'stage resolver keeps the old path');
});

test('Color_Skin holder: frame = skin index 0 replaces the static FRES skin values on M_Body/M_Face',()=>{
  const g=json('data/anim_material_native.json').groups.Player00;
  assert.deepEqual(nativeHolderClipFrame(g,'Color_Skin',0),{accepted:true,frame:0});
  assert.deepEqual(nativeHolderClipFrame(g,'Color_Skin',9),{accepted:false,frame:0});
  const body=glbJson('body.glb').materials.find(m=>m.name==='M_Body').extras.fres;
  assert.deepEqual(body.params.const_color0.value.slice(0,3).map(F),[.734,.491,.387].map(F));
  const s=sampleMaterialClip(g,'Color_Skin',0);assert.ok(s.supported);
  for(const p of s.patches.filter(p=>p.material==='M_Body'))for(const [k,v] of Object.entries(p.params))assert.ok(writeNativeMaterialParam(body.params,k,v),k);
  assert.deepEqual(body.params.const_color0.value.map(F),[1,.996,.997,1].map(F));
  assert.deepEqual(body.params.scattering_color.value.slice(0,3).map(F),[1.000785,.9743486,.9807298].map(F));
  assert.equal(F(body.params.transmission_rate.value),F(.3));assert.equal(F(body.params.edge_transmission_power.value),F(.429));
  assert.deepEqual(s.patches.map(p=>p.material).sort(),['M_Body','M_Face']);
});

test('Color_Eye holder: index 0..20 selects M_Eye_Alb.NN, 21 is rejected',()=>{
  const g=json('data/anim_material_native.json').groups.Player00;
  assert.equal(sampleMaterialClip(g,'Color_Eye',nativeHolderClipFrame(g,'Color_Eye',7).frame).patches[0].patterns._a0,'M_Eye_Alb.07');
  assert.deepEqual(nativeHolderClipFrame(g,'Color_Eye',21),{accepted:false,frame:0});
});

test('lobby team row: one VersusRegular row among 10 in table order, cached per table, never a Coop/Mission row',()=>{
  const table=json('../../common/data/team_color.json');
  const regular=table.dataSets.filter(r=>r.Tag==='VersusRegular').map(r=>r.name);
  assert.deepEqual(regular,['BlueYellow','GreenPurple','LimegreenPurple','OrangeBlue','OrangePurple','PinkGreen','TurquoisePink','TurquoiseRed','YellowBlue','YellowPurple']);
  const seen=new Set();
  for(let seed=0;seed<200;seed++){const rng=SeadRandom.fromSeed(seed),probe=SeadRandom.fromSeed(seed);
    const row=selectLobbyTeamRow(table.dataSets,rng);assert.equal(row.name,regular[seadRandomIndex(probe.nextU32(),10)]);seen.add(row.name);}
  assert.equal(seen.size,10);
  let calls=0;const a=lobbyTeamRow(table,()=>{calls++;return 5;}),b=lobbyTeamRow(table,()=>{calls++;return 6;});
  assert.equal(a,b);assert.equal(calls,1);
});

test('hat slot49: Player00 bind Head·P = I, so Head·(P·S) with identity ManualBindSRT keeps the hat upright at the head',()=>{
  const j=glbJson('body.glb');const nodes=j.nodes;const parent=new Map();
  nodes.forEach((n,i)=>(n.children??[]).forEach(c=>parent.set(c,i)));
  const local=n=>new THREE.Matrix4().compose(new THREE.Vector3(...(n.translation??[0,0,0])),new THREE.Quaternion(...(n.rotation??[0,0,0,1])),new THREE.Vector3(...(n.scale??[1,1,1])));
  const world=i=>{let m=local(nodes[i]);for(let p=parent.get(i);p!==undefined;p=parent.get(p))m=local(nodes[p]).multiply(m);return m;};
  const head=nodes.findIndex(n=>n.name==='Head');const W=world(head),HP=W.clone().multiply(headInverse());
  const e=HP.elements;const I=new THREE.Matrix4().elements;
  for(const k of [0,1,2,4,5,6,8,9,10])assert.ok(Math.abs(e[k]-I[k])<1e-5,`HP[${k}]=${e[k]}`);
  // Hed_FST000 × Har_SQD000: no V0_SQD000 key → identity (0x71026e4e80)
  const srt=json('data/gear.json').parts.head.headParamSet.ManualBindSRT;assert.equal(srt.V0_SQD000,undefined);
  assert.deepEqual(manualBindSrt(undefined),[1,0,0,0,0,1,0,0,0,0,1,0]);
  const r=manualBindSrt(srt.V0_OCT005);assert.equal(r[3],0);assert.equal(r[7],F(.01));assert.equal(r[11],F(-.05));assert.ok(Math.abs(r[0]-.95)<1e-6);
});

test('JumpVarID: prev%2+1 alternation on new jump chains, kept within a chain, 0 when slow or masked kind',()=>{
  let v=0;const seq=[];
  for(let i=0;i<4;i++){v=nativeJumpVarId(v,0x5f,0x99,.1,false);seq.push(v);}
  assert.deepEqual(seq,[1,2,1,2]);
  assert.equal(nativeJumpVarId(2,0x99,0x9b,.1,false),2);
  assert.equal(nativeJumpVarId(2,0x9b,0xa6,.1,false),2);
  assert.equal(nativeJumpVarId(2,0x5f,0x99,.03,false),0);
  assert.equal(nativeJumpVarId(2,0x5f,0x99,.1,true),0);
});

test('tank: full tank Gauge frame 0 scales the ink Scale bone to (1.4254897, 1, 2.1952798) and M_Ink team blend 1, not the static 0.5',()=>{
  const d=json('data/tank_anim_native.json'),bone=d.skeletal.Gauge.bones.find(b=>b.name==='Scale');
  const g=new TankGauge();const out=g.update({subCost:0,remaining:1,lock:1,shortageEnabled:true});
  assert.equal(out.gauge,0);
  const z=bone.curves.find(c=>c.target==='0x0C');
  assert.equal(F(bone.S[0]),F(1.4254897));assert.equal(sampleNativeMaterialCurve(z,0),F(2.1952798));
  assert.equal(sampleNativeMaterialCurve(z,100),F(F(-63*F(.009448885))+F(1.6)));
  const s=sampleMaterialClip(d.material,'Gauge',0);const ink=s.patches.find(p=>p.material==='M_Ink');
  assert.equal(ink.params.team_color_blend['0x00'],1);
  const fres=glbJson('parts/Tnk_Simple.glb').materials.find(m=>m.name==='M_Ink').extras.fres;assert.equal(F(fres.params.team_color_blend.value),.5);
  // lack → 60-frame InkShortage request, stop when the timer ends
  const t=new TankGauge();t.update({subCost:0,remaining:1,lock:1,shortageEnabled:true});t.tickTimers();
  t.lack();const r=t.update({subCost:0,remaining:0,lock:0,shortageEnabled:true});assert.deepEqual(r.requests,['InkShortage','InkShortageGauge']);assert.equal(r.tankEmpty,true);
  let stopAt=-1;for(let i=1;i<80&&stopAt<0;i++){t.tickTimers();t.advanceShortage();if(t.update({subCost:0,remaining:0,lock:0,shortageEnabled:true}).stopShortage)stopAt=i;}
  assert.equal(stopAt,60);
});
