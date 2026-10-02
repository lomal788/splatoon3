// [range] 로비 사격 구역 판정(0x71012496e8 Cube/Cylinder) — Lby_Lobby00 배치 값으로 재구현 검사.
import { test } from "node:test";
import assert from "node:assert/strict";
import { makeArea, insideArea, insideAnyArea, updateShootLatch } from "../core/range/area.ts";

// Banc: LobbyShootingArea 2812547714043694904, LobbyShootingArea 3387184770664961358(회전), _Cylinder 11499976769381249642
const big = makeArea("LobbyShootingArea", "Cube", 1, [20.71942138671875, 6.823498725891113, 4.904103755950928], [0, 0, 0], [41.423667907714844, 100, 78.80795288085938]);
const rotBox = makeArea("LobbyShootingArea", "Cube", 1, [-2.877645492553711, 6.823500633239746, 9.17373275756836], [0, 0.7777428030967712, 0], [14.225373268127441, 100, 24.320051193237305]);
const cyl = makeArea("LobbyShootingArea_Cylinder", "Cylinder", 1, [-12.066457748413086, -0.40415599942207336, 10.075166702270508], [0, 0, 0], [7.006455421447754, 100, 7.006455421447754]);

test("Cube: 중심·경계(≤)·바깥", () => {
  assert.ok(insideArea(big, [20, 0, 20]));
  assert.ok(insideArea(big, [20.71942138671875 + 41.423667907714844 / 2, 0, 4.9]));
  assert.ok(!insideArea(big, [20.71942138671875 + 41.423667907714844 / 2 + 0.01, 0, 4.9]));
  assert.ok(!insideArea(big, [20, 0, 4.904103755950928 + 39.5]));
  assert.ok(!insideArea(big, [20, 60, 20]));
});

test("회전된 Cube: 로컬 축 기준 판정", () => {
  // 로컬 +Z 로 12 이동한 점은 안(반 길이 12.16), 같은 거리를 월드 +Z 로 가면 로컬 x 성분이 생겨 결과가 달라진다
  const ry = 0.7777428030967712;
  const lz = 12;
  const p = [-2.877645492553711 + Math.sin(ry) * lz, 0, 9.17373275756836 + Math.cos(ry) * lz];
  assert.ok(insideArea(rotBox, p));
  assert.ok(!insideArea(rotBox, [-2.877645492553711 + 7.5 * Math.cos(ry), 0, 9.17373275756836 - 7.5 * Math.sin(ry)]));
});

test("Cylinder: 바닥 원점·높이 2·Sy·반지름 Sx(r² < R² 엄격)", () => {
  assert.ok(insideArea(cyl, [-12, 0, 10]));
  assert.ok(!insideArea(cyl, [-12, -1, 10])); // 바닥 아래
  assert.ok(!insideArea(cyl, [-12.066457748413086 + 7.1, 0, 10.075166702270508]));
  assert.ok(insideArea(cyl, [-12, 150, 10])); // 높이 200까지
});

test("구역 목록·무기 허용 래치(공중 4프레임 이상이면 유지)", () => {
  const areas = [big, rotBox, cyl];
  assert.ok(insideAnyArea(areas, [-12, 0, 10]));
  assert.ok(!insideAnyArea(areas, [-30, 0, -30]));
  assert.equal(updateShootLatch(false, true, 0), true);
  assert.equal(updateShootLatch(false, true, 3), true);
  assert.equal(updateShootLatch(false, true, 4), false);
  assert.equal(updateShootLatch(true, false, 10), true);
});
