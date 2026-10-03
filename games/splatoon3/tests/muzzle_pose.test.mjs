import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {build} from '../../../node_modules/esbuild/lib/main.js';
import * as THREE from 'three';
import {muzzlePoseMatrix,nativeHeadingDotReader} from '../client/fx/muzzle.ts';
import {attach,bindWorld} from '../client/render/model.ts';
const runtime=await build({entryPoints:[fileURLToPath(new URL('../client/fx/index.ts',import.meta.url))],bundle:true,write:false,platform:'node',format:'esm',define:{__GAME_BASE__:'"/game/splatoon3/"',__DEV__:'true'},logLevel:'silent'});
const {FxSystem}=await import('data:text/javascript;base64,'+Buffer.from(runtime.outputFiles[0].contents).toString('base64'));
const fixture=JSON.parse(readFileSync(new URL('./fixtures/muzzle_heading_r9.json',import.meta.url)));
const word=new DataView(new ArrayBuffer(4));const bits=x=>{word.setFloat32(0,x,true);return word.getUint32(0,true);};

test('isolated original heading reader matches 2048 captured float32 outputs without normalizing the native rig vector',()=>{
 for(const r of fixture.rows)assert.equal(bits(nativeHeadingDotReader(r.columnX,r.rigForward)),r.expectedBits);
});

test('Muzzle pose retains bone roll and nonuniform scale, validates owner, and supplies independent copies',()=>{
 const e=new THREE.Matrix4().compose(new THREE.Vector3(3,4,5),new THREE.Quaternion().setFromEuler(new THREE.Euler(.3,.7,-.4)),new THREE.Vector3(2,3,4)).elements;
 const p={source:'Weapon_R/Root/Muzzle',owner:1,frame:4,matrix:e},m=muzzlePoseMatrix(p,1);
 assert.deepEqual(m.o,[3,4,5]);assert.deepEqual(m.x,e.slice(0,3));assert.deepEqual(m.y,e.slice(4,7));assert.deepEqual(m.z,e.slice(8,11));
 assert.equal(muzzlePoseMatrix(p,2),null);assert.equal(muzzlePoseMatrix({...p,matrix:[NaN,...e.slice(1)]},1),null);
 m.o[0]=999;assert.equal(p.matrix[12],3);
});

test('Weapon_R attachment carries the actual exported Muzzle offset through an animated hand transform',()=>{
 const data=readFileSync(new URL('../assets/weapons/Shooter_Normal_00/model.glb',import.meta.url));const n=data.readUInt32LE(12),g=JSON.parse(data.subarray(20,20+n).toString());
 const raw=g.nodes.find(n=>n.name==='Muzzle');assert(raw);const body=new THREE.Group(),hand=new THREE.Bone();hand.name='Weapon_R';body.add(hand);
 const part=new THREE.Group(),root=new THREE.Bone(),muzzle=new THREE.Bone();root.name='Root';muzzle.name='Muzzle';muzzle.position.fromArray(raw.translation);root.add(muzzle);part.add(root);part.updateMatrixWorld(true);
 const geo=new THREE.BoxGeometry(.1,.1,.1),mesh=new THREE.SkinnedMesh(geo,new THREE.MeshStandardMaterial());part.add(mesh);mesh.bind(new THREE.Skeleton([root,muzzle]));
 const bind={Weapon_R:new THREE.Matrix4()},attached=attach(body,bind,part,{map:{Root:'Weapon_R'},attachPart:'Root',mode:'full'});
 const bone=attached[0].skeleton.bones[1];assert.equal(bone.parent,hand);assert.equal(bone.name,'part:Muzzle');
 hand.position.set(8,2,1);hand.rotation.set(.3,1,-.2);body.updateMatrixWorld(true);
 const expect=hand.matrixWorld.clone().multiply(new THREE.Matrix4().makeTranslation(...raw.translation));
 bone.matrixWorld.elements.forEach((v,i)=>assert(Math.abs(v-expect.elements[i])<1e-12));
});

test('actual FxSystem consumes the visual full matrix and PositionY leaves its provider unchanged',()=>{
 const e=new THREE.Matrix4().makeRotationZ(.5).setPosition(2,3,4).elements;
 const pose={owner:1,frame:5,source:'Weapon_R/Root/Muzzle',matrix:e},world={data:{tables:{}},shared:new Map([['muzzle',pose]])};
 const data={ready:true,emitters:new Map([['sample/flash',{life:4,numEmit:1,emitRate:1}]]),emitterTex:new Map(),emitterSamplers:new Map(),emitterPrim:new Map(),textures:new Map(),prims:new Map()};
 const sys=new FxSystem(world,new THREE.PerspectiveCamera(),data);
 const m=sys.muzzleMatrix({owner:1,lastPos:[100,100,100],lastDir:[1,0,0]});assert.deepEqual(m,muzzlePoseMatrix(pose,1));
 const h=sys.play({key:'flash',name:'sample',params:{PositionY:.2}},{matrix:()=>sys.muzzleMatrix({owner:1}),color:[1,1,1]});assert(h);
 assert.deepEqual(pose.matrix,e);const actual=h.instances[0].matrix;
 actual.o.forEach((v,i)=>assert.equal(v,m.o[i]+m.y[i]*.2));assert.deepEqual(actual.x,m.x);assert.deepEqual(actual.z,m.z);
 sys.dispose();
});
