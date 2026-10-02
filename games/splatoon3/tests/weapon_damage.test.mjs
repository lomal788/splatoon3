import { test } from "node:test";
import assert from "node:assert/strict";
import { applyRate, bulletRadius, damageRate, shooterDamage } from "../core/weapon/damage.ts";

const SPLATTERSHOT = { ValueMax: 360, ValueMin: 180, ReduceStartFrame: 8, ReduceEndFrame: 40 };

test("스플래시슈터 데미지 감쇠 경계 (combat_damage.py weapon Shooter_Normal_00)", () => {
  for (let age = 0; age <= 7; age++) assert.equal(shooterDamage(age, SPLATTERSHOT), 360, `age ${age}`);
  assert.equal(shooterDamage(8, SPLATTERSHOT), 354);
  assert.equal(shooterDamage(9, SPLATTERSHOT), 348);
  assert.equal(shooterDamage(10, SPLATTERSHOT), 343);
  assert.equal(shooterDamage(38, SPLATTERSHOT), 185);
  for (const age of [39, 40, 60, 100]) assert.equal(shooterDamage(age, SPLATTERSHOT), 180, `age ${age}`);
});

test("감쇠 합성 경계 (combat_damage.py selftest)", () => {
  const p = { ValueMax: 180, ValueMin: 120, ReduceStartFrame: 8, ReduceEndFrame: 8 };
  assert.equal(shooterDamage(7, p), 180);
  assert.equal(shooterDamage(8, p), 120);
  const inv = { ValueMax: 100, ValueMin: 200, ReduceStartFrame: 0, ReduceEndFrame: 10 };
  assert.equal(shooterDamage(4, inv), 150);
});

test("충돌 반경: ChangeFrame 0 이면 End, 아니면 하한 0.02", () => {
  assert.equal(bulletRadius(5, 0.5, Math.fround(0.2), 0), Math.fround(0.2));
  assert.equal(bulletRadius(10, 0.0, 0.0, 10), Math.fround(0.02));
  assert.equal(bulletRadius(5, 0.0, 1.0, 10), 0.5);
});

test("수신 배율: (rate+1e-5) 엡실론, 상한 99998, 표 없으면 1.0", () => {
  assert.equal(applyRate(843, 0.344), 290);
  assert.equal(applyRate(360, 0.7), 252);
  assert.equal(applyRate(200000, 1), 99998);
  assert.equal(damageRate(undefined, "Shooter", "Default"), 1);
  assert.equal(damageRate({ damage_rate: { "Shooter___BulletUmbrellaCanopyNormal": 0.7 } }, "Shooter", "BulletUmbrellaCanopyNormal"), 0.7);
  assert.equal(damageRate({ damage_rate_info: { default: 1, rows: { Shooter: { BulletUmbrellaCanopyNormal: 0.7 } } } }, "Shooter", "BulletUmbrellaCanopyNormal"), 0.7);
  assert.equal(damageRate({ damage_rate_info: { default: 1, rows: { Shooter: {} } } }, "Shooter", "Default"), 1);
  assert.equal(damageRate({ DamageRateInfoConfig: { CellList: { "Shooter___X": { DamageRate: 2 } } } }, "Shooter", "X"), 2);
});
