import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { World } from "../core/world.ts";
import { ParamStore } from "../core/params.ts";
import { Layer } from "../core/types.ts";
import { WeaponRuntime } from "../core/weapon/runtime.ts";
import { createRangeSystem } from "../core/range/index.ts";
import { createWeaponSystem } from "../core/weapon/index.ts";
import { spawnPosition, SHOT_DIR_DEFAULT, MUZZLE_OFFSET } from "../core/weapon/spawn.ts";
import { Btn, emptyPad } from "../core/input.ts";

const GPT = "C:/dev/splatoon3/extracted/params/Component/GameParameterTable";
const ASSET = new URL("../assets/weapons/Shooter_Normal_00/params/", import.meta.url);

function loadTable(name) {
  const a = new URL(`${name}.json`, ASSET);
  if (existsSync(a)) return JSON.parse(readFileSync(a, "utf8"));
  const p = `${GPT}/${name}.game__GameParameterTable.bgyml.json`;
  return existsSync(p) ? JSON.parse(readFileSync(p, "utf8")) : null;
}

function params() {
  const tables = {};
  for (const n of ["WeaponShooterNormal", "BulletSplashShooter", "BulletWallDrop"]) {
    const t = loadTable(n);
    if (t) tables[n] = t;
  }
  return new ParamStore(tables, {});
}

/** 바닥 y = floorY, 벽 z = wallZ(법선 −z), 표적 구 하나를 가진 간단한 충돌 세계 */
function fakeCollision({ floorY = -10, wallZ = Infinity, target = null } = {}) {
  const v = (x, y, z) => Float32Array.of(x, y, z);
  return {
    raycast(o, d, max, mask) {
      let best = null;
      if (mask & Layer.Ground) {
        if (d[1] < 0) {
          const t = (floorY - o[1]) / d[1];
          if (t >= 0 && t <= max) best = { t, point: v(o[0] + d[0] * t, floorY, o[2] + d[2] * t), normal: v(0, 1, 0), layer: Layer.Ground, material: 0, actor: -1 };
        }
        if (d[2] > 0 && Number.isFinite(wallZ)) {
          const t = (wallZ - o[2]) / d[2];
          if (t >= 0 && t <= max && (!best || t < best.t)) best = { t, point: v(o[0] + d[0] * t, o[1] + d[1] * t, wallZ), normal: v(0, 0, -1), layer: Layer.Ground, material: 0, actor: -1 };
        }
      }
      return best;
    },
    sweepSphere(from, to, r, mask) {
      let best = null;
      const dx = to[0] - from[0], dy = to[1] - from[1], dz = to[2] - from[2];
      if (mask & Layer.Ground) {
        if (dy < 0 && from[1] - r >= floorY && to[1] - r < floorY) {
          const t = (floorY + r - from[1]) / dy;
          best = { t, point: v(from[0] + dx * t, floorY, from[2] + dz * t), normal: v(0, 1, 0), layer: Layer.Ground, material: 0, actor: -1 };
        }
        if (dz > 0 && from[2] + r <= wallZ && to[2] + r > wallZ) {
          const t = (wallZ - r - from[2]) / dz;
          if (!best || t < best.t) best = { t, point: v(from[0] + dx * t, from[1] + dy * t, wallZ), normal: v(0, 0, -1), layer: Layer.Ground, material: 0, actor: -1 };
        }
      }
      if (target && mask & Layer.Object) {
        const len = Math.hypot(dx, dy, dz);
        const ux = dx / len, uy = dy / len, uz = dz / len;
        const mx = from[0] - target.c[0], my = from[1] - target.c[1], mz = from[2] - target.c[2];
        const R = target.r + r;
        const b = mx * ux + my * uy + mz * uz, c = mx * mx + my * my + mz * mz - R * R;
        const disc = b * b - c;
        if (disc >= 0) {
          const td = -b - Math.sqrt(disc);
          if (td >= 0 && td <= len && (!best || td / len < best.t)) best = { t: td / len, point: v(from[0] + ux * td, from[1] + uy * td, from[2] + uz * td), normal: v(-ux, -uy, -uz), layer: Layer.Object, material: -1, actor: target.id };
        }
      }
      return best;
    },
    overlapSphere(o, r, mask) {
      const hits = [];
      if (mask & Layer.Ground) {
        if (Math.abs(o[1] - floorY) < r) hits.push({ t: 0, point: v(o[0], floorY, o[2]), normal: v(0, 1, 0), layer: Layer.Ground, material: 0, actor: -1 });
        if (Math.abs(o[2] - wallZ) < r) hits.push({ t: 0, point: v(o[0], o[1], wallZ), normal: v(0, 0, -1), layer: Layer.Ground, material: 0, actor: -1 });
      }
      return hits;
    },
    materialName: () => "",
    setDynamic() {},
  };
}

function makeWorld(opts = {}) {
  const w = new World({ map: "test", placement: null, collision: null, params: params(), tables: {}, players: [{ character: "Player00", weapon: "Shooter_Normal_00", team: 0 }] });
  w.collision = fakeCollision(opts);
  const paints = [];
  w.paint = { request: (r) => paints.push({ frame: w.frame, ...r }), sample: () => ({ team: -1, ratio: [0, 0, 0] }), counts: () => ({ team: [0, 0, 0], total: 0 }) };
  w.shared.set("player", { id: 1, team: 0, pos: [0, 0, 0], vel: [0, 0, 0], squid: false, airFrames: 0 });
  w.shared.set("camera", { aimDir: [0, 0, 1], rigForward: [0, 0, 1], pitchP: 0, pos: [0, 2, -4], target: [0, 2, 0] });
  const sys = createWeaponSystem();
  w.add(sys);
  w.init();
  return { w, paints };
}

function run(w, frames, fireFrames) {
  const log = [];
  for (let i = 0; i < frames; i++) {
    const pad = emptyPad();
    if (fireFrames(i)) pad.hold = Btn.Fire;
    w.step(pad);
    log.push({ frame: w.frame - 1, events: [...w.events.list], bullets: (w.shared.get("bullets") ?? []).map((b) => ({ ...b, pos: [...b.pos] })) });
  }
  return log;
}

test("사격 게이트: 리스폰 직후 사람 프레임 9 까지 차단, 이후 RepeatFrame 6 간격, 발사 위치 = 0x7102552170", () => {
  const { w } = makeWorld();
  const log = run(w, 30, () => true);
  const fires = log.filter((l) => l.events.some((e) => e.type === "Fire"));
  assert.deepEqual(fires.map((l) => l.frame), [8, 14, 20, 26]);
  const e = fires[0].events.find((x) => x.type === "Fire");
  const want = spawnPosition([0, 0, 0], [0, 0, 1], 0, SHOT_DIR_DEFAULT, MUZZLE_OFFSET, [0, 0, 0]);
  assert.deepEqual(e.pos, want);
  assert.ok(fires[0].events.some((x) => x.type === "FireImpact"));
});

test("탄 첫 갱신은 age 0(생성 속도 그대로), 발사 속도를 원본 바디 f32 식으로 적분", () => {
  const { w } = makeWorld();
  const log = run(w, 14, (i) => i >= 10 && i <= 11);
  const at = (f) => log.find((l) => l.frame === f);
  assert.ok(at(11).events.some((e) => e.type === "Fire"), "누른 지 2프레임째 발사");
  const b1 = at(12).bullets.find((b) => b.kind === "Shooter");
  const b2 = at(13).bullets.find((b) => b.kind === "Shooter");
  assert.equal(b1.age, 0);
  assert.equal(b2.age, 1);
  // sead 표의 선형 보간은 길이가 정확히 1이 아니다. z성분/속력을 임의 2.2로 고정하지 않는다.
  const f = Math.fround;
  for (let k = 0; k < 3; k++) assert.equal(b2.pos[k], f(b1.pos[k] + f(f(1 / 60) * f(b2.vel[k] * 60))));
});

test("표적 명중: age 기준 데미지 감쇠, 같은 프레임 BulletHit(Object), 다음 갱신에 소멸", () => {
  const hits = [];
  const { w } = makeWorld({ target: { id: 77, c: [-0.24, 1.1, 8], r: 0.5 } });
  w.hittables.set(77, { id: 77, team: 1, rateCol: "Default", onDamage: (info) => hits.push({ frame: w.frame, ...info }) });
  const log = run(w, 40, (i) => i >= 10 && i <= 11);
  assert.equal(hits.length, 1);
  const h = hits[0];
  assert.equal(h.value, h.raw);
  assert.ok(h.age >= 1);
  const hitLog = log.find((l) => l.events.some((e) => e.type === "BulletHit"));
  assert.equal(hitLog.events.find((e) => e.type === "BulletHit").surface, "Object");
  const die = log.find((l) => l.events.some((e) => e.type === "BulletDie" && e.kind === "Shooter"));
  assert.ok(die.frame >= hitLog.frame);
});

test("바닥 명중: 접촉 프레임에 보관, 슬롯55 에서 ShooterDeferred 도색", () => {
  const { w, paints } = makeWorld({ floorY: -0.5 });
  const log = run(w, 40, (i) => i >= 10 && i <= 11);
  const hit = log.find((l) => l.events.some((e) => e.type === "BulletHit" && e.surface === "Floor" && e.kind === "Shooter"));
  assert.ok(hit, "바닥 명중");
  const sp = paints.filter((p) => p.kind === "ShooterDeferred");
  assert.equal(sp.length, 1);
  assert.ok(sp[0].widthHalf > 0 && sp[0].depthScale >= 1);
});

test("벽 명중: 4프레임 정지 후 소멸, 벽 낙하 방울 생성·벽 도색(Shock)", () => {
  const { w, paints } = makeWorld({ wallZ: 5 });
  const log = run(w, 90, (i) => i >= 10 && i <= 11);
  const hitIdx = log.findIndex((l) => l.events.some((e) => e.type === "BulletHit" && e.surface === "Wall"));
  assert.ok(hitIdx >= 0);
  const dieIdx = log.findIndex((l) => l.events.some((e) => e.type === "BulletDie" && e.kind === "Shooter"));
  assert.equal(dieIdx - hitIdx, 4);
  assert.ok(log[hitIdx].events.some((e) => e.type === "BulletSpawn" && e.kind === "WallDrop"));
  const wd = paints.filter((p) => p.kind === "WallDrop");
  assert.ok(wd.length >= 1);
  assert.equal(wd[0].inkTexType, 0);
  assert.equal(Math.fround(wd[0].widthHalf * 2), Math.fround(3.1000001));
});

test("1프레임 탭: 래치(B+0x530)로 다음 프레임 발사", () => {
  const { w } = makeWorld();
  const log = run(w, 16, (i) => i === 12);
  const fires = log.filter((l) => l.events.some((e) => e.type === "Fire")).map((l) => l.frame);
  assert.deepEqual(fires, [13]);
});

test("오징어 상태에서는 차단, 사람으로 돌아온 뒤 9프레임째부터", () => {
  const { w } = makeWorld();
  const pl = w.shared.get("player");
  pl.squid = true;
  const log = [];
  for (let i = 0; i < 30; i++) {
    if (i === 10) pl.squid = false;
    const pad = emptyPad();
    pad.hold = Btn.Fire;
    w.step(pad);
    if (w.events.list.some((e) => e.type === "Fire")) log.push(w.frame - 1);
  }
  assert.equal(log[0], 18);
});

test("잉크: 한 발 0.0092 소비, 108발 뒤 부족(잔량 0.006400978)·NoInk, 회복 정지 20", () => {
  const { w } = makeWorld();
  const pl = w.shared.get("player");
  pl.ink = 1;
  pl.inkRecoverStop = 0;
  pl.squidLock = 0;
  let fires = 0, noInk = 0;
  for (let i = 0; i < 9 + 6 * 112; i++) {
    const pad = emptyPad();
    pad.hold = Btn.Fire;
    w.step(pad);
    if (w.events.list.some((e) => e.type === "Fire")) fires++;
    if (w.events.list.some((e) => e.type === "NoInk")) noInk++;
    if (fires === 1 && noInk === 0) assert.equal(pl.inkRecoverStop, 20);
  }
  assert.equal(fires, 108);
  assert.equal(Math.fround(pl.ink), Math.fround(0.006400978));
  assert.ok(noInk > 0);
  assert.equal(pl.inkRecoverStop, 20);
  assert.equal(pl.inkRecoverStopNoInk, 30);
  assert.equal(pl.squidLock, 4);
});


test("신규 스플래시·벽 낙하의 생성 프레임은 age -1, post 제외", () => {
 const {w}=makeWorld({wallZ:8});const log=run(w,60,i=>i>=10&&i<=11);
 for(const kind of ["Splash","WallDrop"]){const row=log.find(l=>l.events.some(e=>e.type==="BulletSpawn"&&e.kind===kind));assert.ok(row,kind);const ids=row.events.filter(e=>e.type==="BulletSpawn"&&e.kind===kind).map(e=>e.id);for(const id of ids){const b=row.bullets.find(b=>b.id===id);assert.ok(b,kind+" creation frame retained");assert.equal(b.age,-1);}}
});
test("첫 이동 age0 명중: receiver는 비1 배율을 한 번, vt22는 별도 body/sec 전달", () => {
 const {w}=makeWorld({target:{id:2,c:[-.24,1.1,2],r:.5}});w.newId();
 w.data.placement={actors:[{name:"SighterTarget",hash:"123",pos:[-.24,0,2],rot:[0,0,0],scale:[1,1,1],team:"Neutral",params:{}}]};
 w.data.tables.damage_rate_info={default:1,rows:{Shooter:{Default:.344}}};const range=createRangeSystem();range.init(w);w.systems.unshift(range);
 const t=w.shared.get("range").targets[0],seen=[],h=w.hittables.get(t.id),cb=h.onBulletContact;h.onBulletContact=x=>{seen.push({pos:[...x.pos],velocity:[...x.velocity]});cb(x);};
 const log=run(w,25,i=>i>=10&&i<=11);const row=log.find(l=>l.events.some(e=>e.type==="Damage"));assert.ok(row);const d=row.events.find(e=>e.type==="Damage");assert.equal(d.value,123);assert.equal(seen.length,1);assert.ok(seen[0].velocity[2]>130);assert.ok(seen[0].pos[2]<2);
 assert.equal(row.events.find(e=>e.type==="BulletDie"&&e.kind==="Shooter").id,row.events.find(e=>e.type==="BulletHit"&&e.kind==="Shooter").id);
 assert.ok(w.shared.get("range").targets.find(x=>x.id===t.id).bend.weight>0,"actual physics contact drives bend");
 assert.equal(row.events.find(e=>e.type==="BulletHit"&&e.kind==="Shooter").age,0);
});
test("예약 메인 풀32 고갈: RNG/소비 진행, Fire/Spawn는 발생하지 않음", () => {
 const {w}=makeWorld({floorY:-10000});const rt=new WeaponRuntime(w);rt.bullets=Array.from({length:32},()=>({kind:"Shooter"}));const pl=w.shared.get("player");pl.ink=1;
 let fire=0;for(let i=0;i<9;i++){w.pad={...emptyPad(),hold:Btn.Fire};w.events.clear();rt.fire(w);fire+=w.events.list.filter(e=>e.type==="Fire").length;w.frame++;}
 assert.equal(fire,0);assert.equal(rt.bullets.length,32);assert.equal(rt.action.shots,1);assert.equal(pl.ink,Math.fround(1-Math.fround(.0092)));assert.equal(pl.inkRecoverStop,20);
});
