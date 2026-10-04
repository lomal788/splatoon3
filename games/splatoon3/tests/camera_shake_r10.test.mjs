import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { build } from "../../../node_modules/esbuild/lib/main.js";
import { PerspectiveCamera } from "three";
import { CameraShakeMixer, admitCameraShake } from "../core/camera/shake.ts";

// Same runtime-loading path as fx_loading.test: source JSON is bundled for Node.
const runtime=await build({entryPoints:[fileURLToPath(new URL("../client/fx/index.ts",import.meta.url))],
  bundle:true,write:false,platform:"node",format:"esm",
  define:{__GAME_BASE__:'"/game/splatoon3/"',__DEV__:"true"},logLevel:"silent"});
const work=new URL("../../../../analysis/port_camera_r10/shake/",import.meta.url);
mkdirSync(work,{recursive:true});
const runtimePath=fileURLToPath(new URL("actual_fx_runtime.mjs",work));
writeFileSync(runtimePath,runtime.outputFiles[0].contents);
const {FxSystem}=await import(pathToFileURL(runtimePath).href);

const fixture=JSON.parse(readFileSync(new URL("./fixtures/camera_shake_r10_native.json",import.meta.url),"utf8"));
const bits=v=>Array.from(new Uint32Array(Float32Array.from(v).buffer));
test("r10 native whole Module trace: curve precision, owner checks, counters, loop reset and final eligibility",()=>{
  let ticks=0;
  for(const c of fixture.traces) {
    const mixer=new CameraShakeMixer({[c.name]:c.param},{capacity:1});
    // The native fixture saved owner-generation9 even in its initially stale scenario.
    let owner={generation:9};
    const h=mixer.start(c.name,()=>[0,0,0],0,c.limit,
      {gain:c.gain,followOwner:c.scenario!=="unfollowed_absent",owner:()=>owner});
    assert.ok(h);
    if(c.scenario==="stale")owner.generation=10;
    for(const row of c.trace) {
      if(c.scenario==="removed_at3" && row.tick===3)owner=null;
      if(c.scenario==="generation_at4" && row.tick===4)owner.generation=10;
      mixer.step([0,0,0]);
      const actual=mixer.inspect(h),tag=`${c.name} gain${c.gain} ${c.scenario} tick${row.tick}`;
      assert.equal(actual.frame,row.frame,`${tag} frame`);
      assert.equal(actual.elapsed,row.elapsed,`${tag} elapsed`);
      assert.equal(actual.valid,row.valid,`${tag} valid`);
      assert.equal(actual.finished,row.finished,`${tag} finished`);
      assert.deepEqual(bits(actual.output),row.output_bits,`${tag} output bits`);
      assert.deepEqual(bits(mixer.offset),row.offset_bits,`${tag} Module offset bits`);
      assert.equal(h.alive(),!row.finished,`${tag} handle`);
      ticks++;
    }
  }
  assert.equal(ticks,fixture.native_ticks);
  assert.equal(fixture.traces.length,fixture.trace_cases);
});

const loop={Curve:{Type:"Linear",Data:[1,1],MaxX:2},IsLooped:true,Scale:1};
const finite={...loop,IsLooped:false};
test("first finished slot reuse, previous serial and stale-handle stop preserve the new shake",()=>{
  const mixer=new CameraShakeMixer({loop,finite},{capacity:2,initialSerial:0xffffffff});
  const a=mixer.start("finite",()=>[0,0,0],0),b=mixer.start("loop",()=>[0,0,0],0);
  assert.equal(a.slot,0);assert.equal(a.serial,0xffffffff);assert.equal(b.slot,1);assert.equal(b.serial,0);
  assert.equal(mixer.start("loop",()=>[0,0,0],0),null);
  mixer.step([0,0,0]);mixer.step([0,0,0]);
  const c=mixer.start("loop",()=>[0,0,0],0);
  assert.equal(c.slot,0);assert.equal(c.serial,1);
  assert.equal(a.alive(),false);a.stop();
  assert.equal(c.alive(),true);assert.equal(mixer.inspect(a),null);
  // Native start leaves the finished slot's old output in place until its next update.
  assert.deepEqual(mixer.inspect(c).output,[0,1,0]);
  mixer.step([0,0,0]);assert.deepEqual([...mixer.offset],[0,2,0]);
});
test("admission gain stays latched when listener/emitter move; no repeated emitter callback",()=>{
  const mixer=new CameraShakeMixer({loop});
  let emitter=[20,0,0],calls=0;
  const h=mixer.start("loop",()=>{calls++;return emitter;},1,-1,{listener:[0,0,0]});
  assert.equal(mixer.inspect(h).gain,.5);
  emitter=[100,0,0];mixer.step([100,0,0]);
  assert.deepEqual([...mixer.offset],[0,.5,0]);assert.equal(calls,1);
});
test("parameter SafePtr generation and null value invalidate output without resetting counters",()=>{
  const mixer=new CameraShakeMixer({loop}),ref={value:loop,generation:7};
  const h=mixer.start("loop",()=>[0,0,0],0,-1,{parameterRef:ref});
  mixer.step([0,0,0]);const out=mixer.inspect(h).output;
  ref.generation=8;mixer.step([0,0,0]);
  assert.equal(h.alive(),false);assert.equal(mixer.inspect(h).frame,2);
  assert.deepEqual(mixer.inspect(h).output,out);assert.deepEqual([...mixer.offset],[0,0,0]);
  const h2=mixer.start("loop",()=>[0,0,0],0,-1,{parameterRef:ref});
  ref.value=null;mixer.step([0,0,0]);assert.equal(h2.alive(),false);
});
test("ELink40 native admissions: empty camera names ignore numeric legacy fields, including ID40 fire/hit/targets",()=>{
  const mixer=new CameraShakeMixer({Fuwa:loop});
  for(const a of fixture.elink_admissions_reused) {
    // Native40 all camera names are empty, even critical leaves with controller names.
    assert.equal(a.starts.some(s=>s.kind==="shake"),false);
    assert.equal(admitCameraShake(mixer,{...a.params,CameraRumble:5,CtrlRumblePattern:10002},
      [0,0,0],()=>[0,0,0]),null);
  }
  mixer.step([0,0,0]);assert.deepEqual([...mixer.offset],[0,0,0]);
  assert.equal(fixture.elink_admissions_reused.length,40);
});
test("Fx forwards original40 asset admissions and retains visual handles without synthesizing shot/hit shake",()=>{
  const world={data:{tables:{singletons:{game__CameraModuleParam:{Rumble:{Fuwa:loop}}}}},
    shared:new Map([["camera",{pos:[0,0,0]}]])};
  const fx=new FxSystem(world,new PerspectiveCamera(),{ready:true});
  const visual={alive:()=>true,fade:()=>{}};
  fx.spawnEset=()=>visual;
  for(const a of fixture.elink_admissions_reused) {
    assert.equal(fx.play({key:a.key,name:"test",params:a.params},{pos:[0,0,0]}),visual);
  }
  fx.shakes.step([0,0,0]);assert.deepEqual([...fx.shakes.offset],[0,0,0]);
});
test("Fx fade does not immediately cancel camera; loop owner lifetime and supplied generation are separate contracts",()=>{
  const world={data:{tables:{singletons:{game__CameraModuleParam:{Rumble:{loop,finite}}}}},
    shared:new Map([["camera",{pos:[0,0,0]}]])};
  const fx=new FxSystem(world,new PerspectiveCamera(),{ready:true});
  let alive=true,fades=0;
  const visual={alive:()=>alive,fade:()=>{fades++;}};
  fx.spawnEset=()=>visual;
  const h=fx.play({key:"test",name:"test",params:{CameraRumbleName:"loop"}},{pos:[0,0,0]});
  h.fade();assert.equal(fades,1);
  fx.shakes.step([0,0,0]);assert.deepEqual([...fx.shakes.offset],[0,1,0]);
  alive=false;fx.shakes.step([0,0,0]);assert.deepEqual([...fx.shakes.offset],[0,0,0]);
  // A supplied native-owner adapter can outlive visual emission; no lifetime extension of XHandle.
  let owner={generation:7};
  const supplied=fx.play({key:"test",name:"test",params:{CameraRumbleName:"loop"}},
    {pos:[0,0,0],cameraShakeOwner:()=>owner});
  assert.equal(supplied.alive(),false);
  fx.shakes.step([0,0,0]);assert.deepEqual([...fx.shakes.offset],[0,1,0]);
  owner.generation=8;fx.shakes.step([0,0,0]);assert.deepEqual([...fx.shakes.offset],[0,0,0]);
  fx.play({key:"test",name:"test",params:{CameraRumbleName:"finite"}},
    {pos:[0,0,0],cameraShakeOwner:()=>null});
  fx.shakes.step([0,0,0]);assert.deepEqual([...fx.shakes.offset],[0,1,0]);
});
