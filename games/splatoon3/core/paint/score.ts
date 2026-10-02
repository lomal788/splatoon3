// 칠 포인트 환산. 근거: docs/paint/paint_and_score.md §4.2 (팀 0x7103092a4c, 플레이어 결과·HUD 같은 식) [판독].
const F = Math.fround;

/** 팀 p = fcvtzu(count × 0.015625 × 0.3030303) = count / 64 / 3.3, 음수면 0. */
export function teamPoint(count: number): number {
  const v = F(F(F(count) * F(0.015625)) * F(0.3030303));
  return v > 0 ? Math.trunc(v) : 0;
}

/** 플레이어 p = (int)(paintTexels / 211.2). */
export function playerPoint(texels: number): number {
  return Math.trunc(F(F(texels) / F(211.2)));
}
