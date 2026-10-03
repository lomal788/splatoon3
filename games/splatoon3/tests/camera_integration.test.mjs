import { test } from "node:test";
import assert from "node:assert/strict";
import { PerspectiveCamera, Scene, Vector3 } from "three";
import { PlayerCamera, BOOM_QUERY, BOOM_PROBE_MASK } from "../core/camera/camera.ts";
import { createCameraView } from "../client/camera/index.ts";
import { CameraShakeMixer, shakeDistanceGain, shakeCurve } from "../core/camera/shake.ts";
import { MeshCollisionWorld } from "../core/collision/world.ts";
import { TriMesh } from "../core/collision/mesh.ts";
import { Layer } from "../core/types.ts";
import { readCamera } from "../core/player/index.ts";
import { readShooter } from "../core/weapon/actors.ts";
import { emptyPad } from "../core/input.ts";
const p={pos:[0,0,0],floorNormal:[0,1,0],forward:[0,0,1]};
test("final basis is shared with movement and shooter, including vertical/zero preservation",()=>{
  const c=new PlayerCamera();c.step(p,emptyPad(),null);
  const w={shared:new Map([["camera",c.out]]),data:{players:[{}]},events:{list:[]}};
  const aim=new Float32Array(3),right=new Float32Array(3);
  readCamera(w,aim,right);assert.deepEqual([...right],[...c.out.right]);
  assert.deepEqual(readShooter(w,0).camAxis,[...c.out.viewForward]);
});
test("render uses the native basis; world shake translates position and preserves quaternion",()=>{
  const camera=new PerspectiveCamera(),c=new PlayerCamera();c.step(p,emptyPad(),null);
  const w={shared:new Map([["camera",c.out]])},v=createCameraView({camera,scene:new Scene()});
  v.update(w,1);const before=camera.quaternion.clone(),pos=camera.position.clone();
  const dir=camera.getWorldDirection(new Vector3());
  assert.ok(dir.distanceTo(new Vector3().fromArray(c.out.viewForward))<1e-6);
  camera.userData.shakeOffset={x:.1,y:.2,z:-.3};v.update(w,1);
  assert.ok(before.equals(camera.quaternion));
  assert.ok(camera.position.distanceTo(pos.add(new Vector3(.1,.2,-.3)))<1e-9);
});
test("camera reciprocal raw mask retains camera barriers and passes player-only/CameraThrough shapes",()=>{
  const mesh=new TriMesh(Float32Array.of(-5,-5,-3,5,-5,-3,5,5,-3,-5,5,-3),Uint32Array.of(0,1,2,0,2,3),Uint16Array.of(0,0));
  const make=hitMask=>new MeshCollisionWorld(mesh,[{name:"Barrier",layer:0,paintable:false,tags:[],hitMask,subMask:0xffffffff}]);
  const a=Float32Array.of(0,0,0),b=Float32Array.of(0,0,-6);
  assert.ok(make(130).sweepSphere(a,b,.3,BOOM_PROBE_MASK,BOOM_QUERY));
  assert.equal(make(98).sweepSphere(a,b,.3,BOOM_PROBE_MASK,BOOM_QUERY),null);
  assert.equal(make(536870782).sweepSphere(a,b,.3,BOOM_PROBE_MASK,BOOM_QUERY),null);
  assert.equal(make(0).sweepSphere(a,b,.3,BOOM_PROBE_MASK,BOOM_QUERY),null);
  assert.equal(make(130).sweepSphere(a,b,.3,Layer.Ground),null);
});
test("entry bit0 preserves native normal sign, separate from web geometric normals",()=>{
  const run=flag=>{
    const c=new PlayerCamera();
    const col={sweepSphere(a,b,r){
      const stop=-3+r;
      if(a[2]<=stop || b[2]>=stop)return null;
      const t=(a[2]-stop)/(a[2]-b[2]);
      return {t,point:Float32Array.of(0,0,-3),normal:Float32Array.of(0,0,flag===1?-1:1),nativeEntryFlags:flag,layer:1,material:0,actor:-1};
    }};
    for(let i=0;i<30;i++)c.step(p,emptyPad(),col);
    return [...c.out.pos,...c.out.target,c.out.boomRatio];
  };
  assert.deepEqual(run(undefined),run(0));
  assert.deepEqual(run(0),run(1));
});
test("shake curves, named assets, distance, additive axes, loop and explicit frame limit",()=>{
  assert.equal(shakeCurve("Linear",[0,1],.25),.25);
  assert.equal(shakeCurve("Hermit",[0,0,1,0],.5),.5);
  assert.equal(shakeCurve("Hermit",[0,1,2],.5),0);
  assert.equal(shakeDistanceGain([0,0,0],[15,0,0],1),1);
  assert.equal(shakeDistanceGain([0,0,0],[20,0,0],1),.5);
  assert.equal(shakeDistanceGain([0,0,0],[25,0,0],1),0);
  const mixer=new CameraShakeMixer({a:{Curve:{Type:"Linear",Data:[1,1],MaxX:2},IsLooped:true,Scale:1},
    b:{Curve:{Type:"Linear",Data:[1,1],MaxX:2},Axis:{X:1,Y:0,Z:0},Scale:2}});
  assert.equal(mixer.start("",()=>[0,0,0]),null);
  const h=mixer.start("a",()=>[0,0,0],0,3),b=mixer.start("b",()=>[20,0,0]);
  mixer.step([0,0,0]);assert.deepEqual([...mixer.offset],[1,1,0]);
  mixer.step([0,0,0]);assert.deepEqual([...mixer.offset],[0,1,0]);assert.equal(b.alive(),false);
  mixer.step([0,0,0]);assert.deepEqual([...mixer.offset],[0,0,0]);assert.equal(h.alive(),false);
  mixer.step([0,0,0]);assert.equal(h.alive(),false);assert.deepEqual([...mixer.offset],[0,0,0]);
});
