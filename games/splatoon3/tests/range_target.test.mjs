// [range] spl::SighterTarget 상태 기계·피격·HP·표시값 — 판독식 재구현의 합성 시나리오 검사(원본 실행 대조 아님).
import { test } from "node:test";
import assert from "node:assert/strict";
import { World } from "../core/world.ts";
import { ParamStore } from "../core/params.ts";
import { createRangeSystem, SighterState, DamageResult } from "../core/range/index.ts";

const f = Math.fround;

function placement() {
  return {
    actors: [
      { hash: "8228772978623510098", name: "SighterTarget", pos: [24.0, 0.010009765625, 22.899999618530273], rot: [-3.141592502593994, -0.0, 3.141592502593994], scale: [1, 1, 1], team: "Neutral", params: { game__RailMovableSequentialParam: {}, spl__RailMovableSequentialHelperBancParam: {} } },
      { hash: "8510551139468886273", name: "SighterTarget_Large", pos: [22.0, 0, 37.9], rot: [3.141592502593994, -0.0, -3.141592502593994], scale: [1, 1, 1], team: "Neutral", params: {} },
      { hash: "15066127630233066301", name: "SighterTarget_Move", pos: [40.27117156982422, 2.0, 14.886096954345703], rot: [0, -1.5707963705062866, 0], scale: [1, 1, 1], team: "Neutral",
        params: { game__RailMovableSequentialParam: { InterpolationType: "cSin", MoveSpeed: 7, PatrolType: "cContinue", SpeedCalcType: "cSpeed" }, spl__RailMovableSequentialHelperBancParam: { ToRailPoint: "1280356437980484485" } } },
      { hash: "7855901330750157844", name: "SighterTarget_TipsTrial", pos: [15.5, 0, 22.75], rot: [0, 0, 0], scale: [1, 1, 1], team: "Neutral", params: {} },
      { hash: "2812547714043694904", name: "LobbyShootingArea", pos: [20.71942138671875, 6.823498725891113, 4.904103755950928], rot: [0, 0, 0], scale: [41.423667907714844, 100, 78.80795288085938], team: "Neutral", params: {} },
      { hash: "654996740366154516", name: "StartPos", pos: [-0.14915037155151367, 0.01000000536441803, -11.959452629089355], rot: [0, -0.38194018602371216, 0], scale: [1, 1, 1], team: "Alpha", params: { spl__StartPosParam: {} } },
    ],
    rails: [
      { hash: "14877423949110540250", IsClosed: false, Rotation: [0, -0, 0], Points: [
        { hash: "1280356437980484485", Translate: [40, 0, 18], game__LiftGraphRailNodeParam: { Rotation: { X: 0, Y: -90, Z: 0 } } },
        { hash: "7356806808280323317", Translate: [40, 0, 3], game__LiftGraphRailNodeParam: { Rotation: { X: 0, Y: -90, Z: 0 } } },
      ] },
    ],
  };
}

function makeWorld(opts = {}, team = 0, tables = {}) {
  const w = new World({
    map: "Lby_Lobby00",
    placement: placement(),
    collision: null,
    params: new ParamStore(tables, {}),
    tables: { damage_rate_info: { default: 1.0, rows: { Shooter: {} } } },
    players: [{ character: "Player00", weapon: "Shooter_Normal_00", team }],
  });
  const dyn = new Map();
  w.collision = {
    raycast: () => null,
    sweepSphere: () => null,
    materialName: () => "",
    setDynamic: (id, shape) => (shape ? dyn.set(id, shape) : dyn.delete(id)),
  };
  w.add(createRangeSystem(opts));
  w.init();
  return { w, dyn, range: w.shared.get("range") };
}

const pad = { moveX: 0, moveY: 0, lookYaw: 0, lookPitch: 0, hold: 0, trigger: 0, release: 0 };
const hit = (w, id, value, extra = {}) =>
  w.hittables.get(id).onDamage({ attacker: 1, team: 0, value, pos: new Float32Array([24, 1, 22.9]), dir: new Float32Array([0, 0, 1]), rateRow: "Shooter", critical: false, ...extra });
const tgt = (range, kind) => range.targets.find((t) => t.kind === kind);

test("생성: 일반·대형·이동 3개, 팁 시험 제외, 팀 = 로컬 팀 반대, 충돌 2개씩", () => {
  const { range, dyn, w } = makeWorld();
  assert.deepEqual(range.targets.map((t) => t.kind), ["SighterTarget", "SighterTarget_Large", "SighterTarget_Move"]);
  for (const t of range.targets) assert.equal(t.team, 1);
  assert.equal(dyn.size, 6);
  assert.equal(w.hittables.size, 3);
  const large = tgt(range, "SighterTarget_Large");
  assert.equal(large.maxHp, 5000);
  assert.equal(large.scale, f(1.3));
  assert.equal(range.areas.length, 1);
  assert.equal(range.startPositions[0].team, "Alpha");
  const t2 = makeWorld({}, 1).range;
  assert.equal(t2.targets[0].team, 0);
  assert.equal(makeWorld({ includeTipsTrial: true }).range.targets.length, 4);
});

test("피격: 배율 적용 → DamageShot, 누계, Damage 이벤트, 30프레임 애니 뒤 Wait", () => {
  const { w, range } = makeWorld();
  const id = tgt(range, "SighterTarget").id;
  hit(w, id, 360);
  const ev = w.events.list.find((e) => e.type === "Damage");
  assert.equal(ev.value, 360);
  assert.equal(ev.result, DamageResult.Damaged);
  let n = 0;
  for (; n < 40; n++) {
    w.step(pad);
    if (tgt(w.shared.get("range"), "SighterTarget").state === SighterState.Wait) break;
  }
  const t = tgt(w.shared.get("range"), "SighterTarget");
  assert.equal(n, 30); // 31번째 스텝의 exec 에서 Wait
  assert.equal(t.hp, 640);
  assert.ok(t.damageInfo.active);
  assert.equal(t.damageInfo.value, 36);
});

test("같은 팀 탄 → Through·0", () => {
  const { w, range } = makeWorld({}, 1); // 표적 팀 0
  const id = range.targets[0].id;
  hit(w, id, 360, { team: 0 });
  assert.equal(w.events.list[0].result, DamageResult.Through);
  assert.equal(w.events.list[0].value, 0);
});

test("파괴: HP 0 → Burst(몸 끔·Break) → BurstWait(60~120 HP 채움) → Expand(45) → Wait", () => {
  const { w, range, dyn } = makeWorld();
  const id = tgt(range, "SighterTarget").id;
  for (let i = 0; i < 3; i++) hit(w, id, 360);
  w.step(pad);
  let t = tgt(w.shared.get("range"), "SighterTarget");
  assert.equal(t.state, SighterState.Burst);
  assert.ok(w.events.list.some((e) => e.type === "Break" && e.target === id));
  assert.ok(!dyn.has(id));
  assert.equal(t.damageInfo.value, 108);
  assert.ok(t.damageInfo.isMax);
  // 무적: 데미지 0, 결과 Invincible
  hit(w, id, 360);
  assert.equal(w.events.list.at(-1).result, DamageResult.Invincible);
  w.step(pad); // Brust(1프레임) 끝 → BurstWait
  t = tgt(w.shared.get("range"), "SighterTarget");
  assert.equal(t.state, SighterState.BurstWait);
  const hp = [];
  for (let i = 0; i < 125 && tgt(w.shared.get("range"), "SighterTarget").state === SighterState.BurstWait; i++) {
    w.step(pad);
    hp.push(tgt(w.shared.get("range"), "SighterTarget").hp);
  }
  assert.equal(hp[60], 0); // counter 60
  assert.equal(hp[61], Math.trunc(f(f(1 / 60) * 1000))); // counter 61 → t = 1/60
  assert.equal(hp.length, 122); // counter 121 > 120 에서 Expand
  t = tgt(w.shared.get("range"), "SighterTarget");
  assert.equal(t.state, SighterState.Expand);
  assert.equal(t.hp, 1000);
  assert.ok(dyn.has(id));
  let k = 0;
  while (tgt(w.shared.get("range"), "SighterTarget").state !== SighterState.Wait && k < 60) {
    w.step(pad);
    k++;
  }
  assert.equal(k, 45); // Expand 진입 스텝에도 애니가 1 진행 → 45스텝째 exec 에서 끝
  hit(w, id, 360);
  assert.equal(w.events.list.at(-1).result, DamageResult.Damaged);
});

test("무피격 120프레임 초과 → Flick(HP 복구·누계 0) → 24프레임 뒤 Wait", () => {
  const { w, range } = makeWorld();
  const id = tgt(range, "SighterTarget").id;
  hit(w, id, 100);
  let steps = 0;
  while (tgt(w.shared.get("range"), "SighterTarget").state !== SighterState.Flick && steps < 400) {
    w.step(pad);
    steps++;
  }
  // DamageShot 31스텝(31번째 exec 에서 Wait 진입, counter 0) + Wait 122스텝(counter 0..121, 121 > 120 에서 Flick)
  assert.equal(steps, 31 + 122);
  const t = tgt(w.shared.get("range"), "SighterTarget");
  assert.equal(t.hp, 1000);
  assert.equal(t.damageInfo.value, 0);
  assert.ok(!t.damageInfo.active);
});

test("이동 표적: 시작 점에 놓이고 레일을 따라 움직인다", () => {
  const { w, range } = makeWorld();
  assert.deepEqual(tgt(range, "SighterTarget_Move").pos, [40, 0, 18]);
  for (let i = 0; i < 64; i++) w.step(pad); // 64/60초 ≈ D/2 (15/7/2 = 1.0714초)
  const z = tgt(w.shared.get("range"), "SighterTarget_Move").pos[2];
  assert.ok(z < 11 && z > 10, String(z));
});

test("휨: 탄 속도로 충격 → 휨 무게 > 0, 방향 각", () => {
  const { w, range } = makeWorld();
  const id = tgt(range, "SighterTarget").id;
  // 표적 회전 (π,0,π) = Y축 180°: 로컬 +Z = 월드 −Z. 정면(월드 −Z 쪽)에서 +Z 로 날아온 탄
  hit(w, id, 360, { pos: new Float32Array([24, 1, 22.5]), vel: new Float32Array([0, 0, 2]) });
  w.step(pad);
  const t = tgt(w.shared.get("range"), "SighterTarget");
  assert.ok(t.bend.weight > 0);
  // 앞(로컬 +Z)에서 맞으면 뒤(로컬 −Z, 180°)로 휜다
  assert.ok(Math.abs(t.bend.angleDeg - 180) < 1, String(t.bend.angleDeg));
});

test("에셋 파라미터 표가 있으면 그 값(필드 단위 $parent 상속)", () => {
  const tables = {
    SighterTarget: { GameParameters: {
      spl__SighterTargetParam: { $type: "spl__SighterTargetParam", Scale: 1.0, BulletImpulsScaler: 1.659999966621399 },
      spl__BendCalculatorParam: { $type: "spl__BendCalculatorParam", Kd: 0.8999999761581421, Kp: 0.05000000074505806 },
      spl__DamageParam: { $type: "spl__DamageParam", HitPointHolderArray: [{ MaxHitPoint: 1000 }] },
    } },
    SighterTarget_Large: { $parent: "Work/Component/GameParameterTable/SighterTarget.game__GameParameterTable.gyml", GameParameters: {
      spl__SighterTargetParam: { $type: "spl__SighterTargetParam", Scale: 1.2999999523162842 },
      spl__DamageParam: { $type: "spl__DamageParam", HitPointHolderArray: [{ MaxHitPoint: 5000 }] },
    } },
  };
  const { range } = makeWorld({}, 0, tables);
  const large = tgt(range, "SighterTarget_Large");
  assert.equal(large.maxHp, 5000);
  assert.equal(large.scale, f(1.3));
});
