// 도색 모양·레코드 변환 대조.
// 기대값 paint_fixture_shape.json 출처:
//   shooter/splash/rect = web/tools/paint_shape.py 재구현(같은 함수) 값,
//   record = web/tools/paintgpu_record_emu.py re_convert (원본 0x7102c11f80 실행과 600/600 일치한 재구현).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  SHOOTER_PAINT_DEFAULTS,
  centerShift,
  centerShiftLength,
  rectSize,
  shooterDepthScale,
  shooterPattern,
  shooterWidthHalf,
  splashPaint,
  wallDropSize,
} from "../core/paint/shape.ts";
import { InkTexTable, heightRange, paintSeed, patternVariant } from "../core/paint/inktex.ts";

const fx = JSON.parse(readFileSync(new URL("./paint_fixture_shape.json", import.meta.url), "utf8"));
const near = (a, b, eps, msg) => assert.ok(Math.abs(a - b) <= eps, `${msg}: ${a} vs ${b}`);

test("슈터 반폭(거리 보간) = paint_shape.py shooter_width_half", () => {
  let n = 0;
  for (const s of fx.shooter)
    for (const c of s.width) {
      near(shooterWidthHalf(s.param, c.dist), c.w, 2e-6, `${s.table} dist ${c.dist}`);
      n++;
    }
  assert.ok(n > 100);
});

test("슈터 깊이 비율(각도·BreakFree) = paint_shape.py shooter_depth_scale", () => {
  for (const s of fx.shooter)
    for (const c of s.depth) near(shooterDepthScale(s.param, c.spawn, c.pos, c.free ? 1 : 0, c.maxY), c.ds, 2e-5, `${s.table} ${JSON.stringify(c)}`);
});

test("스플래시 (w, ds) = paint_shape.py splash_paint", () => {
  for (const s of fx.splash)
    for (const c of s.cases) {
      const r = splashPaint(s.param, c.nearest, c.spawnY, c.y);
      near(r.w, c.w, 1e-6, `${s.table} w`);
      near(r.ds, c.ds, 2e-6, `${s.table} ds drop ${c.spawnY}`);
    }
});

test("사각형 W×L·중심 이동 = paint_shape.py rect_size / center_shift", () => {
  for (const c of fx.rect) {
    const { W, L } = rectSize(c.w, c.ds);
    near(W, c.W, 2e-6 * c.W, `W ${c.w} ${c.ds}`);
    near(L, c.L, 2e-6 * c.L, `L ${c.w} ${c.ds}`);
    near(centerShiftLength(W, L, 1), c.shiftLen1, 1e-5, `shift ${c.w} ${c.ds}`);
    near(L / W, c.ds, 1e-5, "L/W = ds");
  }
});

test("paint_shape.py check 의 경계 성질", () => {
  const p = SHOOTER_PAINT_DEFAULTS;
  assert.equal(shooterWidthHalf(p, 0), Math.fround(p.WidthHalfNear));
  near(shooterWidthHalf(p, 100), p.WidthHalfFar, 1e-6, "far");
  let r = rectSize(1, 1);
  near(r.W, 2, 1e-6, "W");
  near(r.L, 2, 1e-6, "L");
  r = rectSize(1, 4);
  near(r.L / r.W, 4, 1e-6, "L/W");
  near(r.W * r.L, 8, 1e-5, "W·L = 4w²√ds");
  assert.equal(centerShiftLength(2, 2, 1), 0);
  near(centerShiftLength(1, 3, 1), 1, 1e-6, "(L−W)/2");
  assert.equal(centerShiftLength(1, 3, 0), 0);
  near(shooterDepthScale(p, [0, 0, 0], [0, 0, 0], 0, 0), p.DepthScaleMin, 1e-6, "dxz 0");
  near(shooterDepthScale(p, [0, 0, 0], [10, 0, 0], 0, 0), p.DepthScaleMax, 1e-6, "flat");
  near(shooterDepthScale(p, [0, 0, 0], [1, -5, 0], 0, 0), p.DepthScaleMin, 1e-6, "steep");
});

test("패턴 경계 1.3/1.6/2.2/2.85 (0x7101765ad8, L/W 를 f32 로 비교)", () => {
  const cases = [[1.0, 0], [1.29, 0], [1.31, 1], [1.59, 1], [1.61, 2], [2.19, 2], [2.21, 3], [2.84, 3], [2.86, 4], [5, 4]];
  for (const [ds, pat] of cases) {
    const { W, L } = rectSize(1.5, ds);
    assert.equal(shooterPattern(W, L), pat, `ds ${ds}`);
  }
});

test("중심 이동 벡터: 바닥(n=+y)에서 진행 방향 쪽으로 (L−W)/2", () => {
  const out = new Float32Array(3);
  for (const [dx, dz] of [[1, 0], [0, 1], [-0.6, 0.8]]) {
    centerShift(out, [0, 1, 0], [dx, 0, dz], 1, 3, 1);
    near(out[0], dx, 1e-6, "x");
    near(out[1], 0, 1e-6, "y");
    near(out[2], dz, 1e-6, "z");
  }
  centerShift(out, [1, 0, 0], [0, 0, 1], 1, 3, 2); // 벽(n=+x): X×n = 0 → 대체 축 경로
  near(Math.hypot(out[0], out[1], out[2]), 1, 1e-6, "벽 이동 길이");
  near(out[0], 0, 1e-6, "벽 면 안");
});

test("벽 낙하 반경 양자화 (0.05 단위 + 0.001)", () => {
  near(wallDropSize(0.6), 1.2, 1e-6, "Ground 0.6 → 12×0.05×2");
  near(wallDropSize(0.65), 1.3, 1e-6, "Fall 0.65 → 13");
});

test("그리기 레코드 시드·변형 번호·높이 범위 = 0x7102c11f80 (re_convert, 원본 실행 600/600)", () => {
  for (const c of fx.record) {
    assert.equal(paintSeed(c.pos, c.n4), c.seed >>> 0, `seed ${JSON.stringify(c.pos)} ${c.n4}`);
    assert.equal(patternVariant(c.seed, c.row.PatternNum), c.variant, `variant ${c.name} seed ${c.seed}`);
    const [hmax, hmin] = heightRange(c.row, c.W, c.L);
    near(hmax, c.hmax, 0, `hmax ${c.name}`);
    near(hmin, c.hmin, 0, `hmin ${c.name}`);
  }
  // 문서 예: 시드 0 → 0x4807714d → Shot00_5
  assert.equal(patternVariant(0, 12), 5);
  // 대체 표(에셋 없음)의 Shot00~04 행이 원본 표와 같음
  const t = new InkTexTable(null);
  for (const c of fx.record.filter((r) => r.type < 5)) {
    const r = t.get(c.type);
    assert.equal(r.PatternNum, c.row.PatternNum);
    assert.equal(r.AnimationFrame, c.af);
    assert.equal(r.AnimationStep, c.as);
  }
  assert.equal(t.textureName(0, 5), "Shot00_5");
});
