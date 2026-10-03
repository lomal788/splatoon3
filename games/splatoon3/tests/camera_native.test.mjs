import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { updateBasis, directionSlerp, mix, F } from "../core/camera/native_math.ts";
import { collisionSpring, advanceBoom, forwardCoefficient, boomPosition } from "../core/camera/boom.ts";
import { PlayerCamera, BOOM_QUERY } from "../core/camera/camera.ts";
import { blendedRig, rigPose, elevationDeg } from "../core/camera/rig.ts";
import { emptyPad } from "../core/input.ts";
const fixtures = JSON.parse(readFileSync(new URL("./fixtures/camera_native.json", import.meta.url)));
const bits = a => Array.from(new Uint32Array(Float32Array.from(a).buffer));
const floats = a => Array.from(new Float32Array(Uint32Array.from(a).buffer));
test("native camera basis: 260 original instruction cases, all columns and degenerate preservation", () => {
  const x = Float32Array.of(1,0,0), y = Float32Array.of(0,1,0), z = Float32Array.of(0,0,1);
  for (const d of fixtures.basis) {
    assert.equal(updateBasis(d.pos,d.at,x,y,z),d.updated);
    assert.equal(Buffer.from(Float32Array.from([...x,...y,...z]).buffer).toString("hex"),d.original_bits);
  }
});
test("camera normal slerp: original sead table fixtures, including opposite and zero vectors", () => {
  for (const d of fixtures.slerp) assert.deepEqual(bits(directionSlerp(d.t,d.a,d.b)),d.bits);
});
test("camera collision spring: 128 original blocks, damp/add/hold and track displacement", () => {
  for (const d of fixtures.collision_spring) {
    const s = Float32Array.from(d.spring), p = Float32Array.from(d.track);
    collisionSpring(s,p,d.input,d.body,d.vel,d.aim,d.ratio,d.hold);
    assert.deepEqual(bits([...s,...p]),d.bits);
  }
});
test("camera position gate and postmix: 128 original instruction blocks", () => {
  for (const d of fixtures.boom_gate) {
    const p = Float32Array.from(d.entry);
    boomPosition(p,d.pivot,d.dir,d.ratio,d.length,d.height,d.native,d.de0);
    assert.deepEqual(bits(p),d.bits);
    for (let i=0;i<3;i++) p[i]=mix(p[i],d.native[i],d.blend);
    assert.deepEqual(bits(p),d.finalBits);
  }
});
test("boom recovery and forward coefficient: original SDK fixtures (documented JS libm boundary)", t => {
  let exact=0,maxError=0,forwardExact=0;
  for (const row of fixtures.boom) {
    const d=row.input,s={target:d.target,ratio:d.ratio,rate:d.rate,speed:d.speed,angle:d.angle,under:0};
    advanceBoom(s,d);
    const got=[s.under,s.angle,s.speed,s.rate,s.target,s.ratio], ref=floats(row.bits);
    assert.deepEqual(bits(got),row.bits);
    if (bits(got).every((b,i)=>b===row.bits[i])) exact++;
    got.forEach((v,i)=>{maxError=Math.max(maxError,Math.abs(v-ref[i]));assert.ok(Math.abs(v-ref[i])<=1e-6,i+": "+v+" vs "+ref[i]);});
  }
  for (const d of fixtures.forward) {
    const v=forwardCoefficient(d.vel,d.aim,d.squid,d.old),ref=floats([d.bits])[0];
    assert.equal(bits([v])[0],d.bits);
    if (bits([v])[0]===d.bits) forwardExact++;
    maxError=Math.max(maxError,Math.abs(v-ref));
    assert.ok(Math.abs(v-ref)<=1e-6);
  }
  t.diagnostic("boom exact "+exact+"/128, forward exact "+forwardExact+"/128, max absolute error "+maxError);
});
test("camera executes both .3 sphere queries and carries the native layer/mask contract", () => {
  const calls=[];
  const world={sweepSphere(from,to,radius,mask,query){calls.push({from:[...from],to:[...to],radius,mask,query});return null;}};
  const c=new PlayerCamera(),pl={pos:[0,0,0],forward:[0,0,1],floorNormal:[0,1,0]};
  c.step(pl,emptyPad(),world);
  assert.equal(calls.length,2);
  for (const q of calls) { assert.equal(q.radius,F(.3));assert.deepEqual(q.query,BOOM_QUERY); }
  assert.equal(c.out.near,.2);
  assert.ok(calls[1].from.some((v,i)=>v!==calls[0].from[i]));
  assert.ok(c.out.right[0]<0);
  assert.deepEqual(bits(c.out.viewForward),bits([...c.out.viewZ].map(v=>-v)));
});
test("native query skip blend and de0 position gate do not discard the old position", () => {
  const c=new PlayerCamera(),pl={pos:[0,0,0],floorNormal:[0,1,0],native:{positionGateDe0:1}};
  c.reset(pl,false);const old=[...c.out.pos];pl.pos=[4,0,0];c.step(pl,emptyPad(),null);
  assert.equal(c.out.pos[0],old[0]);
  let queries=0;pl.native={blend1760:1};c.step(pl,emptyPad(),{sweepSphere(){queries++;return null;}});
  assert.equal(queries,0);assert.ok(c.out.pos[0]>3);
});

test("mode0 rig poses: native 128 original calls, ordinary and squid wall curves", t=>{
  let exact=0,maxError=0;
  for (const d of fixtures.rig) {
    const v=blendedRig(d.p,d.squid,d.u,{H:0,F:0,D:0,S:0},{H:0,F:0,D:0,S:0});
    assert.deepEqual(bits([v.H,v.F,v.D,v.S]),d.valueBits);
    const at=new Float32Array(3),cam=new Float32Array(3);
    rigPose(d.base,d.dir,v,elevationDeg(d.p,-7.5,60,-75),at,cam);
    const got=[...at,...cam],ref=floats(d.bits);
    assert.deepEqual(bits(got),d.bits);
    if(bits(got).every((b,i)=>b===d.bits[i])) exact++;
    got.forEach((v,i)=>{maxError=Math.max(maxError,Math.abs(v-ref[i]));assert.ok(Math.abs(v-ref[i])<=2e-6,JSON.stringify({d,i,v,ref:ref[i]}));});
  }
  t.diagnostic("rig exact "+exact+"/128, maxError "+maxError);
});
