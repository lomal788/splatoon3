import { test } from "node:test";
import assert from "node:assert/strict";
import { SeadRandom } from "../core/rng.ts";
import { ParamStore } from "../core/params.ts";

test("sead::Random 초기화식과 float01 범위", () => {
  const r = new SeadRandom(10);
  const a = r.u32(), b = r.u32();
  assert.notEqual(a, b);
  const r2 = new SeadRandom(10);
  assert.equal(r2.u32(), a);
  for (let i = 0; i < 1000; i++) {
    const f = r.float01();
    assert.ok(f >= 0 && f < 1);
  }
});

test("ParamStore: 필드 단위 $parent 상속 → 기본값", () => {
  const p = new ParamStore(
    {
      Child: { $parent: "Work/Component/GameParameterTable/Base.game__GameParameterTable.gyml", GameParameters: { MoveParam: { $type: "T", A: 1 } } },
      Base: { GameParameters: { MoveParam: { $type: "T", B: 2, A: 9 } } },
    },
    { T: { A: 0, B: 0, C: 3 } },
  );
  assert.deepEqual(p.get("Child", "MoveParam"), { A: 1, B: 2, C: 3, $type: "T" });
});
