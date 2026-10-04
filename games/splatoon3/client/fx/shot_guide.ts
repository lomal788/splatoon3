// 슈터 조준 표시(ShotGuide) = xlink 이펙트. 근거: docs/combat/damage_hit.md §6.7, docs/weapon/shooter_bullet.md §3.3.9.
//   예측 0x7102548c3c → 0x710175779c: 실제 탄과 같은 규칙으로 한 발을 ShotGuideFrame 단계 흉내 내 첫 접촉으로 종류를 정한다.
//   종류 0 NoHit / 1 HitConstant(지형·리시버 없는 강체·비유효 리시버) / 2 HitEffective(상대 팀 리시버).
//   이펙트: PlayerShotGuide "Shooter_Center_<종류>" / "Shooter_HitMarker_<종류>" (0x7102677578, 키 없으면 표시 없음),
//   위치 0x71026779a8: 가운데 = 예측 점(this+0x50), 히트마커 = this+0x5c. 회전 = [this+0x108]+0x30 행렬의 3축.
import { readShooter } from "../../core/weapon/actors.ts";
import { Bullet, type BulletParams, type SpawnInfo } from "../../core/weapon/bullet.ts";
import { readParam, WEAPON_TABLES, type AdditionParam, type CollisionParam, type MoveParam, type WeaponShooterParam } from "../../core/weapon/params.ts";
import { MUZZLE_OFFSET, SHOT_DIR_DEFAULT, dirSpeed, initialVelocity, spawnPosition, cameraAxis } from "../../core/weapon/spawn.ts";
import { f32, v3 } from "../../core/fmath.ts";
import { Layer, type Team } from "../../core/types.ts";
import type { World } from "../../core/world.ts";

type V3 = [number, number, number];

export const SHOT_GUIDE_KINDS = ["NoHit", "HitConstant", "HitEffective"] as const;

/** PlayerShotGuide 콜 테이블(analysis/effect_sound/elink2_users.json) 중 슈터 가운데·히트마커 키 → RuntimeAssetName. */
export const SHOT_GUIDE_ASSETS: Record<string, string> = {
  Shooter_Center_NoHit: "WpShtrSite",
  Shooter_Center_HitConstant: "WpShtrSiteHit",
  Shooter_Center_HitEffective: "WpShtrSiteHit",
  Shooter_HitMarker_HitConstant: "WpShtrFieldHitMarker",
  Shooter_HitMarker_HitEffective: "WpShtrHitMarker",
};

export function shotGuideAsset(base: "Shooter_Center" | "Shooter_HitMarker", kind: number): string | null {
  return SHOT_GUIDE_ASSETS[`${base}_${SHOT_GUIDE_KINDS[kind] ?? "NoHit"}`] ?? null;
}

export interface ShotGuide {
  show: boolean;
  kind: number;
  /** this+0x50 */
  center: V3;
  /** this+0x5c */
  hit: V3;
  /** 첫 접촉 대상(없으면 -1) */
  target: number;
}

interface GuideParams { bullet: BulletParams; wsp: WeaponShooterParam; add: AdditionParam }
const cache = new WeakMap<object, GuideParams>();

function params(w: World, weapon: string): GuideParams {
  const key = w.data.params as unknown as object;
  const hit = cache.get(key);
  if (hit) return hit;
  const t = WEAPON_TABLES[weapon] ?? WEAPON_TABLES.Shooter_Normal_00;
  const ps = w.data.params;
  const move = readParam<MoveParam>(ps, t.main, "MoveParam", "spl__BulletSimpleMoveParam");
  const col = readParam<CollisionParam>(ps, t.main, "CollisionParam", "spl__BulletSimpleCollisionParam");
  const p: GuideParams = {
    bullet: { move, col, dmg: null, paint: null, splashPaint: null, splashSpawn: null, tail: null, wallDropColPaint: null, wallHoldFrames: 4, paintDelay: 1 },
    wsp: readParam<WeaponShooterParam>(ps, t.main, "WeaponParam", "spl__WeaponShooterParam"),
    add: readParam<AdditionParam>(ps, t.main, "spl__SpawnBulletAdditionMovePlayerParam", "spl__SpawnBulletAdditionMovePlayerParam"),
  };
  if (key) cache.set(key, p);
  return p;
}

/** 0x710175779c 의 web 대응: 탄 이동(Bullet.pre)·반경(슬롯57)·질의(Field = Ground|Water, Player = Object)를 실제 탄 경로와 같게. */
export function predictShotGuide(w: World, weapon = "Shooter_Normal_00"): ShotGuide {
  const sv = readShooter(w, 0);
  const none: ShotGuide = { show: false, kind: 0, center: [...sv.pos] as V3, hit: [...sv.pos] as V3, target: -1 };
  // show = predict: 사람 상태로 무기를 든 동안(0x71024c0fbc 의 b·h 게이트 중 오징어/사격 불가만 반영) [근사]
  if (sv.blocked) return none;
  const p = params(w, weapon);
  let axis: V3 = sv.camAxis ?? [0, 0, 1];
  if (!sv.camAxis && sv.camPos && sv.camAt) axis = cameraAxis(sv.camPos, sv.camAt, [0, 0, 0]) ?? axis;
  const pos: V3 = [0, 0, 0];
  spawnPosition(sv.pos, sv.rigForward, sv.pitch, SHOT_DIR_DEFAULT, MUZZLE_OFFSET, pos);
  const vel: V3 = [0, 0, 0];
  initialVelocity(f32(p.bullet.move.SpawnSpeed), sv.aim, sv.vel, axis, p.add, true, vel);
  const dir: V3 = [0, 0, 0];
  const speed = dirSpeed(vel, dir);
  const info: SpawnInfo = { kind: "Shooter", owner: sv.id, team: sv.team as Team, weapon, pos, dir, speed, extraSpeed: 0, frame: w.frame, split: 0, angle: 0, local: false, paintDir: [0, 0] };
  const b = new Bullet(-1, info, p.bullet, 0);
  const steps = Math.max(0, p.wsp.ShotGuideFrame | 0);
  const col = w.collision;
  const p0: V3 = [0, 0, 0], p1: V3 = [0, 0, 0];
  for (let s = 0; s < steps; s++) {
    b.pre();
    b.body.begin(p0, p1);
    if (col) {
      const from = v3(p0[0], p0[1], p0[2]), to = v3(p1[0], p1[1], p1[2]);
      const moved = p0[0] !== p1[0] || p0[1] !== p1[1] || p0[2] !== p1[2];
      let hit = b.rField > 0 ? (col.overlapSphere?.(from, b.rField, Layer.Ground | Layer.Water)[0] ?? (moved ? col.sweepSphere(from, to, b.rField, Layer.Ground | Layer.Water) : null)) : null;
      if (b.rPlayer > 0) {
        const o = col.overlapSphere?.(from, b.rPlayer, Layer.Object).find((h) => h.actor !== sv.id) ?? (moved ? col.sweepSphere(from, to, b.rPlayer, Layer.Object) : null);
        if (o && o.actor !== sv.id && (!hit || o.t < hit.t)) hit = o;
      }
      if (hit) {
        const pt: V3 = [hit.point[0], hit.point[1], hit.point[2]];
        const h = hit.actor >= 0 ? w.hittables.get(hit.actor) : undefined;
        // 0x7101a87e8c: 리시버 없음 → 1, 팀 칸 플래그(상대 팀 리시버) → 2, 아니면 1
        const kind = h ? (h.team !== sv.team ? 2 : 1) : 1;
        return { show: true, kind, center: pt, hit: pt, target: hit.actor };
      }
    }
    b.body.commit(p1);
  }
  const end: V3 = [b.body.pos[0], b.body.pos[1], b.body.pos[2]];
  return { show: true, kind: 0, center: end, hit: end, target: -1 };
}
