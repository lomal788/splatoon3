import { test } from "node:test";
import assert from "node:assert/strict";
import { canConsumeInk, consumeInk, INK_RECOVER_STD } from "../core/weapon/shooter.ts";
import { RepeatTimer } from "../core/weapon/swerve.ts";

const u32 = new Uint32Array(1);
const f = new Float32Array(u32.buffer);
const bits = (x) => ((f[0] = x), u32[0]);
const F = Math.fround;

test("잉크 소비량·회복량 상수 비트 (weapon_ink_emu.py)", () => {
  assert.equal(bits(F(F(0.009200000204145908) * F(1 * 1))), 0x3c16bb99);
  assert.equal(bits(INK_RECOVER_STD), 0x3ada740e);
});

test("0x7102492120: r ≥ cost 또는 |r − cost| ≤ 1e-5, 결과가 회복량 미만이면 0", () => {
  const cost = F(0.0092);
  assert.equal(consumeInk(1, cost, INK_RECOVER_STD), F(1 - cost));
  assert.equal(consumeInk(F(0.0091), cost, INK_RECOVER_STD), null);
  assert.equal(canConsumeInk(F(0.0091), cost), false);
  assert.equal(consumeInk(F(cost - 0.000005), cost, INK_RECOVER_STD), 0);
  assert.equal(consumeInk(F(cost + 0.001), cost, INK_RECOVER_STD), 0);
  let r = 1, n = 0;
  for (;;) {
    const next = consumeInk(r, cost, INK_RECOVER_STD);
    if (next === null) break;
    r = next;
    n++;
  }
  assert.equal(n, 108);
  assert.equal(r, F(0.006400978));
});

test("연사 타이머 리셋(0x710258295c(S,1,0)): phase 0x3f555555, rem 0x3f800001, 1·7·13 프레임째 발사", () => {
  const t = new RepeatTimer();
  t.limit = 999;
  t.idle(6, true, false);
  assert.equal(bits(t.phase), 0x3f555555);
  assert.equal(bits(t.rem), 0x3f800001);
  const fired = [];
  for (let i = 1; i <= 25; i++) if (t.update(6)) fired.push(i);
  assert.deepEqual(fired, [1, 7, 13, 19, 25]);
});
