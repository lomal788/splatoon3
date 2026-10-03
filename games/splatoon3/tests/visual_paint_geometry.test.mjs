import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { rankVisualChartCandidates,partitionVisualChartTriangle,visualChartUv } from '../core/paint/visual_chart_adapter.ts';
import { bindVisualPaint } from '../client/paint/visual_geometry.ts';

const chart=(page,o,w,h,n=[0,1,0],e1=[1,0,0],e2=[0,0,1])=>({page,x0:0,y0:0,w,h,o,n,e1,e2,tris:[0]});
const triangle=[0,0,0,0,0,2,2,0,0]; // +Y winding
const area=vs=>{let a=0;for(let i=0;i<vs.length;i++){const p=vs[i],q=vs[(i+1)%vs.length];a+=p[1]*q[2]-p[2]*q[1]}return Math.abs(a)/2};
const approx=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);

test('floor visual triangle partitions across two custom atlas pages without losing or duplicating area',()=>{
  const charts=[{id:0,chart:chart(0,[0,0,0],8,16)},{id:1,chart:chart(1,[1,0,0],8,16)}];
  const pieces=partitionVisualChartTriangle(triangle,rankVisualChartCandidates(triangle,charts));
  assert.ok(pieces.some(p=>p.chartId===0));assert.ok(pieces.some(p=>p.chartId===1));
  assert.equal(pieces.filter(p=>p.chartId===null).length,0);
  approx(pieces.reduce((a,p)=>a+area(p.vertices),0),.5);
  for(const p of pieces)for(const b of p.vertices){approx(b.reduce((a,v)=>a+v,0),1);assert.ok(b.every(v=>v>=-1e-10));}
});

test('overlap chart ownership follows closest plane then ID and removes already assigned polygons',()=>{
  const near=chart(0,[0,.01,0],16,16),far=chart(1,[0,.15,0],16,16);
  const sorted=rankVisualChartCandidates(triangle,[{id:1,chart:far},{id:0,chart:near}]);
  assert.deepEqual(sorted.map(c=>c.id),[0,1]);
  const pieces=partitionVisualChartTriangle(triangle,sorted);
  assert.deepEqual(pieces.map(p=>p.chartId),[0]);approx(area(pieces[0].vertices),.5);
  assert.equal(rankVisualChartCandidates(triangle,[{id:2,chart:chart(2,[0,.20001,0],16,16)}]).length,0);
});

test('unmapped rectangle remainder retains dry geometry and wall adapter preserves UV Y convention',()=>{
  const floorPieces=partitionVisualChartTriangle(triangle,[{id:0,chart:chart(0,[0,0,0],4,4)}]);
  assert.ok(floorPieces.some(p=>p.chartId===null));
  approx(floorPieces.reduce((a,p)=>a+area(p.vertices),0),.5);
  const wall=[0,0,0,2,0,0,0,2,0];
  const ch=chart(0,[0,0,0],16,16,[0,0,1],[1,0,0],[0,1,0]);
  const selected=rankVisualChartCandidates(wall,[{id:0,chart:ch}]);assert.equal(selected.length,1);
  assert.deepEqual(visualChartUv([1,1,0],ch,16,16),[.5,.5]);
  assert.deepEqual(visualChartUv([0,0,0],ch,16,16),[0,1]);
});

function visualFixture(matrix) {
  const root=new THREE.Group();
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(triangle,3));
  g.setAttribute('normal',new THREE.Float32BufferAttribute([0,1,0,0,1,0,0,1,0],3));
  g.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,0,1,1,0],2));
  g.setAttribute('uv1',new THREE.Float32BufferAttribute([.1,.2,.1,.6,.5,.2],2));
  g.setAttribute('tangent',new THREE.Int8BufferAttribute([127,0,0,127,127,0,0,127,127,0,0,127],4,true));
  g.setAttribute('color',new THREE.Uint8BufferAttribute([255,0,0,0,255,0,0,0,255],3,true));
  const original=new THREE.MeshStandardMaterial();
  original.userData.nativeForward=true;
  original.userData.fres={shader:{archive:'Hoian_UBER',options:{blitz_paint_type:'1'}}};
  const mesh=new THREE.Mesh(g,original);mesh.name='actual_visual_floor';mesh.receiveShadow=true;
  if(matrix){mesh.matrixAutoUpdate=false;mesh.matrix.copy(matrix);}
  root.add(mesh);root.updateMatrixWorld(true);
  const origin=new THREE.Vector3().applyMatrix4(mesh.matrixWorld);
  const ch=chart(0,[origin.x,origin.y,origin.z],8,16);
  const surf={charts:[ch],pages:[{w:32,h:32}],chartsInSphere:()=>[0]};
  const clones=[];
  const binding=bindVisualPaint(root,surf,(mat,page)=>{assert.equal(mat,original);assert.equal(page,0);const clone=mat.clone();clones.push(clone);return clone});
  return{root,mesh,g,original,binding,clones};
}

test('real visual geometry keeps baked UV/normal/color/tangent interpolation and same parent transform',()=>{
  const f=visualFixture(new THREE.Matrix4().makeTranslation(3,2,-4));
  const pieces=f.root.children.filter(m=>m.userData.paintVisualGeometry);
  assert.equal(f.binding.stats.boundMeshes,1);assert.equal(f.mesh.visible,false);
  assert.ok(pieces.some(m=>m.userData.paintPage===null));
  const painted=pieces.find(m=>m.userData.paintPage===0);
  assert.ok(painted);assert.equal(painted.receiveShadow,true);
  assert.deepEqual(painted.matrix.toArray(),f.mesh.matrix.toArray());
  for(const part of pieces) {
    const attrs=part.geometry.attributes;
    assert.ok(attrs.normal&&attrs.uv&&attrs.uv1&&attrs.color&&attrs.tangent);
    for(let i=0;i<attrs.position.count;i++) {
      const x=attrs.position.getX(i),z=attrs.position.getZ(i);
      approx(attrs.uv.getX(i),x/2);approx(attrs.uv.getY(i),z/2);
      assert.ok(Math.abs(attrs.uv1.getX(i)-(.1+.2*x))<1e-7);
      assert.ok(Math.abs(attrs.uv1.getY(i)-(.2+.2*z))<1e-7);
      approx(attrs.color.getX(i)+attrs.color.getY(i)+attrs.color.getZ(i),1);
      approx(attrs.tangent.getX(i),1);approx(attrs.tangent.getW(i),1);
    }
  }
  assert.equal(painted.geometry.getAttribute('paintUv').itemSize,4);
  assert.equal(painted.geometry.getAttribute('paintUv').normalized,true);
  assert.ok(painted.geometry.getAttribute('paintUv').array instanceof Int16Array);
  assert.equal(painted.geometry.getAttribute('paintUvSwitch').getX(0),0);
  assert.equal(painted.geometry.getAttribute('paintUvTangent').getX(0),1);
  const remainder=pieces.find(m=>m.userData.paintPage===null);assert.equal(remainder.material,f.original);
  f.binding.dispose();f.binding.dispose();assert.equal(f.mesh.visible,true);assert.deepEqual(f.root.children,[f.mesh]);
  assert.equal(f.mesh.geometry,f.g);assert.equal(f.mesh.material,f.original);
  f.g.dispose();f.original.dispose();for(const clone of f.clones)clone.dispose();
});

test('uncharted native visual material is left visible and non-paint/foreign materials are untouched',()=>{
  const root=new THREE.Group();const geo=new THREE.PlaneGeometry(1,1);
  const native=new THREE.MeshStandardMaterial();native.userData.nativeForward=true;
  native.userData.fres={shader:{archive:'Hoian_UBER',options:{blitz_paint_type:'1'}}};
  const foreign=new THREE.MeshStandardMaterial();
  const a=new THREE.Mesh(geo,native),b=new THREE.Mesh(geo,foreign);root.add(a,b);
  const binding=bindVisualPaint(root,{charts:[],pages:[],chartsInSphere:()=>[]},()=>{throw Error('no mapped page expected')});
  assert.equal(binding.stats.candidateMeshes,1);assert.equal(binding.stats.boundMeshes,0);
  assert.equal(a.visible,true);assert.equal(b.visible,true);assert.deepEqual(root.children,[a,b]);
  binding.dispose();geo.dispose();native.dispose();foreign.dispose();
});
