import {playerModelFile} from "../client/render/model.ts";
import {hsvOffset} from "../client/render/teamcolor.ts";
import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {directionalSH,evalSH,hermit2D,curveSamples} from "../client/render/graphics_math.ts";
import {tone4} from "../client/render/post.ts";
import {calcChannel,calcColorGlsl} from "../client/render/hoian.ts";
import {lightGrid,coneCell} from "../client/render/dynamic_lights.ts";
import {bakeTableIndex,BakeBindings} from "../client/render/bake.ts";
import * as THREE from "three";
const fixture=JSON.parse(readFileSync(new URL("./fixtures/graphics_native.json",import.meta.url)));
const bits=x=>{const a=new Float32Array([x]);return new Uint32Array(a.buffer)[0];};
test("native directional SH: 128 original executions, bit exact",()=>{
 for(const c of fixture.directionalSH)assert.deepEqual(directionalSH(c.direction,c.color,c.samples).map(bits),c.bits);
});
test("native SH evaluation: signed coefficients and max0, 128 original executions",()=>{
 for(const c of fixture.evalSH)assert.deepEqual(evalSH(c.direction,c.sh).map(bits),c.bits);
});
test("native Hermit2D: 424 original executions, endpoints and normalized tangents",()=>{
 for(const c of fixture.hermit2D)assert.equal(bits(hermit2D(c.data,c.t)),c.bits);
 const red=fixture.hermit2D.filter(c=>c.source==="CurveColorR");
 assert.deepEqual(curveSamples(red[0].data).map(bits),red.map(c=>c.bits));
});
test("Hoian calc requires third source and preserves alpha channel inverse",()=>{
 assert.equal(calcChannel("A","41"),"vec4(1.-(A).w)");
 const f={shader:{options:{enable_calc_color0:"True",blitz_calc_color0_calc_type:"9",blitz_calc_color0_A:"50",blitz_calc_color0_B:"100",blitz_calc_color0_C:"9",blitz_calc_color0_replace_color:"4"}}};
 const skipped=[];
 assert.equal(calcColorGlsl(f,new Set(),skipped),"");assert.equal(skipped.length,1);
 const s=calcColorGlsl(f,new Set([9]),[]);
 assert.ok(s.includes("*hResource0"));assert.ok(s.includes("hCalcRoughness=hCalc0"));
});
test("dynamic lights retain first four inserts and newest LSB, no closest sort",()=>{
 const l={position:[0,0,0],direction:[0,1,0],color:[1,1,1],radius:20,halfAngle:.4,damp:1,angleDamp:1,type:0};
 const g=lightGrid(Array.from({length:6},()=>({...l})));
 assert.equal(g.lights.length,4);assert.equal(g.grid[10*20+10],0x00010203);
 assert.deepEqual(g.origin,[-100,-.5,-100]);
});
test("bake matching uses original count/index and _u1; invalid atlas doesn't silently bind",()=>{
 const raw=new Uint16Array([0x4000,0x3c00,0,0x3c00]).buffer;
 const data={textures:{T:{file:"bake/T.bin",mips:[{width:1,height:1,offset:0,bytes:8}]}},
 DataElements:[{BindingSpace:0,DataType:4,TextureNames:["T"],ModelElements:[{Guid:"123_0",ModelName:"Lobby",OriginalMaterialCount:2,
 MaterialElements:[{MaterialName:"Floor",OriginalMaterialIndex:1,TextureIndex:0,TexcoordScale:{X:.25,Y:.5},TexcoordOffset:{X:.5,Y:.25}}]}]}]};
 const bundle={has:n=>n==="bake/bindings.json",json:()=>data,bytes:()=>raw};
 const binder=new BakeBindings(bundle);
 const root=new THREE.Group();Object.assign(root.userData,{bakeGuid:"123_0",bakeModelName:"Lobby",originalMaterialCount:2});
 const mesh=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshStandardMaterial());root.add(mesh);
 mesh.geometry.setAttribute("uv1",new THREE.BufferAttribute(new Float32Array([0,0]),2));
 mesh.material.name="Floor";mesh.material.userData.originalMaterialIndex=1;
 const fres={params:{gsys_bake_st1:{value:[1,1,0,0]}},samplers:[{sampler:"bake1",texture:"dummy",slots:["_b1"]}]};
 const valid=binder.resolve(mesh,mesh.material,fres);assert.ok(valid?.light);
 assert.deepEqual(valid.light.st.toArray(),[.25,.5,.5,.25]);
 assert.equal(binder.resolve(mesh,mesh.material,{samplers:fres.samplers}),null);
 assert.equal(valid.light.texture.image.data[0],0x4000); // HDR 2.0 remains a half float.
 mesh.material.userData.originalMaterialIndex=0;assert.equal(binder.resolve(mesh,mesh.material,fres),null);
 mesh.material.userData.originalMaterialIndex=1;mesh.geometry.deleteAttribute("uv1");
 assert.equal(binder.resolve(mesh,mesh.material,fres),null);
 assert.equal(bakeTableIndex(0,3),2);assert.equal(bakeTableIndex(0,4),3);binder.dispose();
});
test("HDR tone4 keeps black finite and combines luminance/per-channel exponential",()=>{
 assert.deepEqual(tone4([0,0,0],2),[0,0,0]);
 const v=tone4([.25,1,4],2);assert.ok(v.every(x=>Number.isFinite(x)&&x>=0&&x<=1));
 assert.ok(v[0]<v[1]&&v[1]<v[2]);
 assert.notDeepEqual(v,tone4([.25,1,4],1));
});

test("point light packed grids: 32 original sequences of eight insertions",()=>{
 const f=JSON.parse(readFileSync(new URL("./fixtures/graphics_lights_native.json",import.meta.url)));
 for(const c of f.grids){const g=lightGrid(c.lights);assert.equal(g.lights.length,c.count);assert.deepEqual([...g.grid],c.grid);}
});
test("native cone consumer: 256 decisions including zero directions/center",()=>{
 const f=JSON.parse(readFileSync(new URL("./fixtures/graphics_lights_native.json",import.meta.url)));
 for(const c of f.cones)assert.equal(coneCell(c.center,c.position,c.direction,c.radius,c.angle,c.margin),c.hit,JSON.stringify(c));
});

test("team color HSV: 128 original executions with loaded hue peaks and native SDK fmodf",()=>{
 const f=JSON.parse(readFileSync(new URL("./fixtures/graphics_hsv_native.json",import.meta.url)));
 for(const c of f.cases)assert.deepEqual(hsvOffset(...c.offset,c.color).map(bits),c.bits,JSON.stringify(c));
});

test("character model selection excludes anim/squid library even when catalogue sorts it first",()=>{
 const catalog=JSON.parse(readFileSync(new URL("../assets/catalog.json",import.meta.url)));
 const files=catalog.bundles["character/Player00"].files.filter(n=>n.endsWith(".glb"));
 const selected=playerModelFile(files,/squid|octopus/i);
 assert.equal(selected,"squid.glb");
 assert.equal(playerModelFile(["anim/squid.glb"],/squid/i),undefined);
 const b=readFileSync(new URL("../assets/characters/Player00/"+selected,import.meta.url));
 const g=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)));
 assert.equal(g.meshes.length,2); // native Squid body and eye, not an animation-only root.
});
