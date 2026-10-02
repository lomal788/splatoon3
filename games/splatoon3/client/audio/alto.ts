// Alto(aal) 거리 감쇠·지향성·그룹 제한. 근거: docs/effect_sound/sound_resources.md §4.2~4.3.
// 순수 계산(DOM 없음).

/** AROC 롤오프 커브 (파서 0x7103852e2c, 평가 0x7103852da4). model 1 Rational, 2 Linear, 3 Power, 그 밖 없음. */
export interface Aroc {
  model: number;
  A: number;
  B: number;
  C: number;
  D: number;
  mixMode: number;
}

/** AUDC 거리 우선순위 (평가 0x710385b148) */
export interface Audc {
  type: number;
  A: number;
  B: number;
  C: number;
  D: number;
  E: number;
}

/** AADR 음원 지향성 (설정 0x7103863788, 평가 0x7103863fe8) */
export interface Aadr {
  inner: number;
  outer: number;
  outerGain: number;
  outerFilter: number;
}

export interface AttnSet {
  volume?: Aroc;
  filter?: Aroc;
  priority?: Audc;
  directivity?: Aadr;
  culling?: { dist: number; fade: number; apply: number };
}

// 데이터: sound_resources.md §4.2 표(하위 파일 원시값). sfx.json 에 attenuation 이 있으면 그것을 쓴다.
const WpMuzzleVol: Aroc = { model: 3, A: 1.0, B: 0.0, C: 0.70794, D: 1.0, mixMode: 0 };
const CmnVol: Aroc = { model: 1, A: 1.0, B: 0.0, C: 1.0, D: 1.0, mixMode: 0 };
const CmnFlt: Aroc = { model: 1, A: 10.0, B: 0.0, C: 0.2, D: 0.0, mixMode: 1 };
const CmnPrio_High: Audc = { type: 0, A: 0.9, B: 0.41, C: 0, D: 3.0, E: 0.1 };
const CmnPrio_Low: Audc = { type: 0, A: 0.4, B: 0, C: 0, D: 3.0, E: 0.1 };
const WeaponMuzzle: Aadr = { inner: 80.0, outer: 140.0, outerGain: 0.8, outerFilter: 0 };
const Culling = { dist: 8.0, fade: 4.0, apply: 0 };

export const DEFAULT_ATTN_SETS: Record<string, AttnSet> = {
  WpMuzzle_HighSensi: { volume: WpMuzzleVol, filter: CmnFlt, priority: CmnPrio_High, directivity: WeaponMuzzle, culling: Culling },
  LowSensi: { volume: CmnVol, filter: CmnFlt, priority: CmnPrio_Low, culling: Culling },
  HitEffect: { volume: CmnVol, culling: Culling },
};

const FLT_MAX = 3.4028234663852886e38;

export function evalAroc(c: Aroc, d: number): number {
  if (c.model < 1 || c.model > 3) return c.D;
  const max = c.B === 0 ? FLT_MAX : c.B;
  let g: number;
  if (d <= c.A) g = 1;
  else {
    const x = Math.min(d, max);
    if (c.model === 1) g = c.A / (c.C * x + (1 - c.C) * c.A);
    else if (c.model === 2) g = 1 - ((x - c.A) * c.C) / (max - c.A);
    else g = Math.pow(c.A / x, c.C);
  }
  if (Math.abs(g) < 3.05e-5) g = 0;
  const out = c.mixMode === 0 ? g * c.D : 1 - g * (1 - c.D);
  return out > 1 ? 1 : out < 0 ? 0 : out;
}

export function evalAudc(c: Audc, x: number): number {
  const { type, A, B, C, D, E } = c;
  let cut: number;
  if (A < B || B > 0) cut = FLT_MAX;
  else if (A <= 0) cut = 0;
  else if (E === 0) cut = C;
  else {
    const t0 = Math.max(-B / (A - B), 3.0517578e-5);
    cut = C + D * (type === 0 ? Math.log(t0) / Math.log(E) : (1 - t0) / (1 - E));
  }
  let v: number;
  if (x <= C) v = A;
  else if (x > cut) v = 0;
  else if (E === 1) v = A;
  else if (E === 0) v = B;
  else v = B + (A - B) * (type === 0 ? Math.pow(E, (x - C) / D) : Math.max(1 - ((1 - E) * (x - C)) / D, 0));
  return Math.abs(v) < 1 / 32768 ? 0 : v;
}

/** θ = atan2(|z × v|, z·v). z = 음원 로컬 +Z(월드), v = 청자 − 음원. 반환 {gain, t} */
export function evalAadr(c: Aadr, z: ArrayLike<number>, v: ArrayLike<number>): { gain: number; t: number } {
  const o = Math.min(Math.max((c.outer * Math.PI) / 180, 0), Math.PI);
  const i = Math.min(Math.max((c.inner * Math.PI) / 180, 0), o);
  const cx = z[1] * v[2] - z[2] * v[1], cy = z[2] * v[0] - z[0] * v[2], cz = z[0] * v[1] - z[1] * v[0];
  const th = Math.atan2(Math.hypot(cx, cy, cz), z[0] * v[0] + z[1] * v[1] + z[2] * v[2]);
  if (th <= i) return { gain: 1, t: 0 };
  if (th <= o) {
    const t = (th - i) / (o - i);
    return { gain: 1 - t * (1 - c.outerGain), t };
  }
  return { gain: c.outerGain, t: 1 };
}

/** AACL 컬링 페이드(0x7103863fe8): d ≥ 컬링 거리면 0, 페이드 구간은 제곱. */
export function evalCulling(c: { dist: number; fade: number }, d: number): number {
  const edge = c.dist, w = c.fade;
  if (edge <= 0) return 1;
  if (d >= edge) return 0;
  if (w > 0 && edge - w < d) {
    const k = 1 - (d - (edge - w)) / w;
    return k * k;
  }
  return 1;
}

/**
 * 정규화 거리. 원본: d = 거리 / 전역 단위 × 배율(+0x90 × 확장+4). DistCoef 의 결합은 [미확정](§4.2.6) —
 * 문서 권고대로 d = 거리 / DistCoef 로 둔다(가정).
 */
export function normDist(dist: number, distCoef: number): number {
  return distCoef > 0 ? dist / distCoef : dist;
}

/**
 * AGST 그룹 제한기(GRP [0x16] 종류, [0x17] 개수). 종류별 정렬 비교 함수(analysis/decomp/fx/limiter*.c):
 *  1: 우선순위 내림차순, 같으면 +8 오름차순(먼저 시작한 것 우선)      — 0x7103847950 / 0x7103848c88
 *  2: 우선순위 내림차순, 같으면 +8 내림차순(나중에 시작한 것 우선)    — 0x7103847c6c
 *  3: +8 오름차순 우선(비교값 ~(+8)), 같으면 우선순위 내림차순         — 0x7103848070 / 0x7103848e34
 *  4: +8 내림차순 우선, 같으면 우선순위 내림차순                       — 0x71038482e0 / 0x7103849000
 * 정렬 뒤 앞 limitCount 개를 남기고 나머지를 멈춘다고 본다 [추정]. +8 = 시작 순번 [추정],
 * 우선순위 = +0xc4 × +0xcc × (+0x210 객체 +0x18 또는 vt+0x38) — 웹은 Priority × AUDC 거리 우선순위로 둔다 [추정].
 */
export interface GroupRule {
  limiterType: number;
  limitCount: number;
}

// 데이터: analysis/vfx/agst_grp_dump.txt (이 범위에서 쓰는 그룹만)
export const DEFAULT_GROUPS: Record<string, GroupRule> = {
  Weapon_Default: { limiterType: 0, limitCount: -1 },
  Weapon_AttackFocused: { limiterType: 0, limitCount: -1 },
  Weapon_InsLimit_00: { limiterType: 0, limitCount: -1 },
  BulletHit_ToObject: { limiterType: 4, limitCount: 1 },
  BulletHit_Aggregated: { limiterType: 4, limitCount: 1 },
  InkSpray_Focused: { limiterType: 2, limitCount: 4 },
  InkSpray_NotFocused: { limiterType: 1, limitCount: 5 },
  InkSpray_SmallDrop: { limiterType: 3, limitCount: 3 },
  Player_Voice: { limiterType: 2, limitCount: 4 },
  Player_Damage: { limiterType: 4, limitCount: 3 },
};

export interface LimitVoice {
  seq: number;
  priority: number;
}

/** 정렬 뒤 남길 순서(앞쪽이 남음). */
export function limiterOrder<T extends LimitVoice>(type: number, voices: T[]): T[] {
  const p = (v: T): number => Math.trunc(v.priority * 255);
  const cmp = (a: T, b: T): number => {
    switch (type) {
      case 1:
        return p(b) - p(a) || a.seq - b.seq;
      case 2:
        return p(b) - p(a) || b.seq - a.seq;
      case 3:
        return a.seq - b.seq || p(b) - p(a);
      case 4:
        return b.seq - a.seq || p(b) - p(a);
      default:
        return 0;
    }
  };
  return [...voices].sort(cmp);
}
