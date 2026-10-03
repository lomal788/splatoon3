import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { mainInput, inputCountdown } from "../core/weapon/input.ts";
import { consumedInk, recoverInk, stopInk, inkRecoveryRate, INK_RECOVER_STD } from "../core/weapon/ink.ts";
import { consumeInk } from "../core/weapon/shooter.ts";
import { RepeatTimer } from "../core/weapon/swerve.ts";
import { MeshCollisionWorld } from "../core/collision/world.ts";
import { TriMesh } from "../core/collision/mesh.ts";
import { Layer } from "../core/types.ts";
import { readInput, createPlayerState } from "../core/player/index.ts";
import { Btn, emptyPad } from "../core/input.ts";
const f = Math.fround, u = new Uint32Array(1), fl = new Float32Array(u.buffer);
const bits = x => ((fl[0] = x), u[0]);
const fixture = JSON.parse(readFileSync(new URL("./weapon_port_fixture.json", import.meta.url), "utf8"));
const ink = () => ({ ink: .5, inkRecoverStop: 0, inkRecoverStopNoInk: 0, inkRecoverStopSquid: 0, inkConsumeHold: 0x12345, inkStealthFrames: 9, inkStealthBlend: 1 });
test("원본 main input writer 768건 + signed 포화 감소 262건", () => {
 for (const c of fixture.input) assert.deepEqual(mainInput(c.previous, c.sender, c.gate), { frames: c.frames, clearLatches: c.clearLatches });
 for (const c of fixture.countdown) assert.equal(inputCountdown(c.input), c.result);
});
test("원본 consume 384건: 허용 오차·정수화 전 잔량·잠복 기록 초기화", () => {
 for (const c of fixture.consume) {
  const next = consumeInk(c.ink, c.cost, INK_RECOVER_STD);
  assert.equal(next !== null, c.ok);
  if (next !== null) { assert.equal(bits(next), c.bits); const s = ink(); consumedInk(s); assert.deepEqual([s.inkStealthFrames, bits(s.inkStealthBlend)], c.cleared); }
 }
});
test("원본 회복량 128건·회복 정지 128건 비트/필드 일치", () => {
 for (const c of fixture.rate) assert.equal(bits(inkRecoveryRate(c.stealth, c.stdFrames, c.stealthFrames)), c.bits);
 for (const c of fixture.stop) { const s = ink(); s[c.squid ? "inkRecoverStopSquid" : "inkRecoverStop"] = c.current; stopInk(s, c.frames, c.ok, c.squid); assert.equal(s[c.squid ? "inkRecoverStopSquid" : "inkRecoverStop"], c.stop); assert.equal(s.inkConsumeHold, c.hold); }
});
test("원본 repeat timer 256건: 위상·ready·세 카운터 일치", () => {
 for (const c of fixture.timer) { const t = new RepeatTimer(); [t.phase,t.rem,t.count,t.c0,t.c1,t.c2,t.limit] = c.input; t.flag = !!c.input[7]; assert.equal(t.update(c.repeat), c.due); assert.deepEqual([bits(t.phase),bits(t.rem)],c.bits); assert.deepEqual([t.count,t.c0,t.c1,t.c2,t.limit],c.fields); }
});
test("판독 회복 소비자: 세 카운터의 감소 전 max, 음수 진행, 잠복 잔여량", () => {
 const s=ink();s.inkRecoverStop=1;s.inkRecoverStopNoInk=-3;s.inkRecoverStopSquid=-5;
 recoverInk(s,{state:0x56,fastStealth:false,airFrames:0});assert.equal(s.ink,.5);assert.deepEqual([s.inkRecoverStop,s.inkRecoverStopNoInk,s.inkRecoverStopSquid],[0,-4,-6]);
 recoverInk(s,{state:0x56,fastStealth:false,airFrames:0});assert.equal(s.ink,f(.5+INK_RECOVER_STD));assert.equal(s.inkRecoverStop,-1);
 s.inkRecoverStop=-1;s.inkRecoverStopNoInk=1;const before=s.ink;recoverInk(s,{state:0x85,fastStealth:true,airFrames:0});assert.equal(s.ink,before);
 recoverInk(s,{state:0x85,fastStealth:true,airFrames:0});assert.equal(s.inkStealthBlend,1);assert.equal(s.ink,f(before+f(1/180)));
 recoverInk(s,{state:0x85,fastStealth:false,airFrames:0});assert.equal(s.inkStealthBlend,f(1-f(.1)));
});
test("원본 Sender 우선순위→메인 카운터: 뒤에 누른 Fire가 Squid hold보다 우선", () => {
 const p=createPlayerState(1,0);const pad=emptyPad();pad.hold=Btn.Squid;pad.trigger=Btn.Squid;readInput(p,pad);assert.equal(p.mainInputFrames,0);
 pad.hold=Btn.Squid|Btn.Fire;pad.trigger=Btn.Fire;readInput(p,pad);assert.equal(p.mainInputFrames,1);assert.equal(p.squidRequest,false);
 pad.trigger=0;readInput(p,pad);assert.equal(p.mainInputFrames,2);p.mainInputGates.denied=true;readInput(p,pad);assert.equal(p.mainInputFrames,0);assert.equal(p.clearMainLatches,true);
});
test("구 접촉 adapter: 비스듬한 벽·정지된 동적 capsule을 레이 없이 검출", () => {
 const mesh=new TriMesh(Float32Array.of(-3,-3,-3,3,-3,3,0,3,0),Uint32Array.of(0,1,2),Uint16Array.of(0));
 const col=new MeshCollisionWorld(mesh,[{name:"wall",layer:Layer.Ground,paintable:true,tags:[],hitMask:null,subMask:null}]);
 const h=col.overlapSphere(Float32Array.of(.05,0,-.05),.2,Layer.Ground);assert.equal(h.length,1);assert.ok(Math.abs(h[0].normal[0])>.6&&Math.abs(h[0].normal[2])>.6);
 col.setDynamic(77,{kind:"capsule",a:Float32Array.of(1,0,1),b:Float32Array.of(1,2,1),radius:.5,layer:Layer.Object});
 const d=col.overlapSphere(Float32Array.of(1.6,1,1),.2,Layer.Object);assert.equal(d.length,1);assert.equal(d[0].actor,77);assert.equal(d[0].t,0);assert.equal(d[0].normal[0],1);
});
