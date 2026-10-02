// 무기 시스템 한 프레임: 탄 갱신(슬롯18) → 물리(바디 스텝) → 접촉(슬롯22→58/59/60) → 이동 후(슬롯19·21) → 사격 → 정리.
// 순서 근거·미확정은 docs/impl/weapon.md §프레임 순서.
import { f32, v3 } from "../fmath.ts";
import { Layer, type DamageInfo, type Hit, type PaintRequest, type Team } from "../types.ts";
import type { World } from "../world.ts";
import { Btn } from "../input.ts";
import { readShooter } from "./actors.ts";
import { FLOOR_NY } from "./body.ts";
import { Bullet, type BulletParams, type Contact, type SpawnInfo } from "./bullet.ts";
import { applyRate, damageRate, knockback, shooterDamage } from "./damage.ts";
import type { V3 } from "./move.ts";
import { horizontalDir, shooterDepthScale, shooterWidthHalf, splashPaintSize } from "./paint_shape.ts";
import {
  readParam, WEAPON_TABLES, type AdditionParam, type CollisionParam, type DamageParam, type MoveParam, type ShooterPaintParam,
  type SplashPaintParam, type SplashSpawnParam, type TailLengthParam, type WallDropCollisionPaintParam, type WallDropCommonParam,
  type WallDropMoveParam, type WeaponShooterParam,
} from "./params.ts";
import { canConsumeInk, consumeInk, INK_RECOVER_STD, ShooterAction, type InkPort } from "./shooter.ts";
import { cameraAxis } from "./spawn.ts";
import { scheduleSplash, splashOnMove } from "./splash.ts";
import { DEFAULT_SEEDS, seedsFrom, type MatchSeeds } from "./swerve.ts";
import { movingIntoWall, quantize, WALL_DROP_RADIUS, wallDropVelocity, WallDrop, WallDropThinOut, type WallContact, type WallDropPaint } from "./wall_drop.ts";

/** shared "bullets" 항목(표시용 읽기 전용) */
export interface BulletView {
  id: number;
  kind: "Shooter" | "Splash" | "WallDrop";
  owner: number;
  team: Team;
  pos: V3;
  prevPos: V3;
  vel: V3;
  radius: number;
  age: number;
  /** 꼬리 점(슈터) */
  tail: V3 | null;
  /** 벽 정지 중 */
  stuck: boolean;
}

/** RSDB BulletSettingInfo [데이터]: DeactivateFallHeight·DeactivateFrame·WallDropPositionStoreNum·WallDropThinOutDistance */
const BULLET_SETTING: Record<string, { fall: number; frame: number; store: number; thin: number }> = {
  BulletShooterBase: { fall: 16.0, frame: 0, store: 10, thin: 0.30000001192092896 },
  BulletSplashShooter: { fall: 41.0, frame: 0, store: 4, thin: 0.30000001192092896 },
};

interface WeaponSet {
  weapon: string;
  wsp: WeaponShooterParam;
  add: AdditionParam;
  splashSpawn: SplashSpawnParam;
  shooter: BulletParams;
  splash: BulletParams;
  wdMove: WallDropMoveParam;
  wdPaint: WallDropCollisionPaintParam;
  /** 스플래시 탄이 만드는 벽 낙하: BulletSplashShooter 표의 WallDrop* [데이터, 어느 표를 읽는지는 추정] */
  wdMoveSplash: WallDropMoveParam;
  wdPaintSplash: WallDropCollisionPaintParam;
  wdCommon: WallDropCommonParam;
  rateRow: string;
}

function loadSet(w: World, weapon: string): WeaponSet {
  const t = WEAPON_TABLES[weapon] ?? WEAPON_TABLES.Shooter_Normal_00;
  const ps = w.data.params;
  const move = readParam<MoveParam>(ps, t.main, "MoveParam", "spl__BulletSimpleMoveParam");
  const col = readParam<CollisionParam>(ps, t.main, "CollisionParam", "spl__BulletSimpleCollisionParam");
  const dmg = readParam<DamageParam>(ps, t.main, "DamageParam", "spl__BulletShooterDamageParam");
  const paint = readParam<ShooterPaintParam>(ps, t.main, "PaintParam", "spl__BulletShooterPaintParam");
  const splashPaint = readParam<SplashPaintParam>(ps, t.main, "SplashPaintParam", "spl__BulletSplashShooterPaintParam");
  const splashSpawn = readParam<SplashSpawnParam>(ps, t.main, "SplashSpawnParam", "spl__BulletSplashShooterSpawnParam");
  const tail = readParam<TailLengthParam>(ps, t.main, "TailLength", "spl__BulletShooterTailLengthParam");
  const wdPaint = readParam<WallDropCollisionPaintParam>(ps, t.main, "WallDropCollisionPaintParam", "spl__BulletWallDropCollisionPaintParam");
  const wdMove = readParam<WallDropMoveParam>(ps, t.main, "WallDropMoveParam", "spl__BulletWallDropMoveParam");
  const sMove = readParam<MoveParam>(ps, t.splash, "MoveParam", "spl__BulletSimpleMoveParam");
  const sCol = readParam<CollisionParam>(ps, t.splash, "CollisionParam", "spl__BulletSimpleCollisionParam");
  const info = w.data.tables["weapon_info"] as { main?: { DefaultDamageRateInfoRow?: string } } | undefined;
  return {
    weapon,
    wsp: readParam<WeaponShooterParam>(ps, t.main, "WeaponParam", "spl__WeaponShooterParam"),
    add: readParam<AdditionParam>(ps, t.main, "spl__SpawnBulletAdditionMovePlayerParam", "spl__SpawnBulletAdditionMovePlayerParam"),
    splashSpawn,
    shooter: { move, col, dmg, paint, splashPaint, splashSpawn, tail, wallDropColPaint: wdPaint, wallHoldFrames: 4, paintDelay: 1 },
    splash: { move: sMove, col: sCol, dmg: null, paint: null, splashPaint, splashSpawn: null, tail: null, wallDropColPaint: wdPaint, wallHoldFrames: 0, paintDelay: 0 },
    wdMove,
    wdPaint,
    wdMoveSplash: readParam<WallDropMoveParam>(ps, t.splash, "WallDropMoveParam", "spl__BulletWallDropMoveParam"),
    wdPaintSplash: readParam<WallDropCollisionPaintParam>(ps, t.splash, "WallDropCollisionPaintParam", "spl__BulletWallDropCollisionPaintParam"),
    wdCommon: readParam<WallDropCommonParam>(ps, t.wallDrop, "CommonParam", "spl__BulletWallDropCommonParam"),
    rateRow: info?.main?.DefaultDamageRateInfoRow ?? "Shooter",
  };
}

function matchSeeds(w: World): MatchSeeds {
  const s = w.data.tables["match_seed"] as { a?: number; b?: number; c?: number; d?: number } | undefined;
  if (s && [s.a, s.b, s.c, s.d].every((x) => typeof x === "number")) return seedsFrom(s.a!, s.b!, s.c!, s.d!);
  return DEFAULT_SEEDS;
}

/** 탄 슬롯105 0x71016696f8: 요청 번호 = min(max(GameFrame, 0), 0x1745d1) */
function requestStamp(frame: number): number {
  const f = frame < 0 ? 0 : frame;
  return f < 0x1745d1 ? f : 0x1745d1;
}

function toV3(a: ArrayLike<number>): V3 {
  return [a[0], a[1], a[2]];
}

export class WeaponRuntime {
  readonly set: WeaponSet;
  readonly seeds: MatchSeeds;
  readonly action: ShooterAction;
  readonly owner: number;
  readonly team: Team;
  bullets: Bullet[] = [];
  drops: WallDrop[] = [];
  readonly thin = new Map<string, WallDropThinOut>();
  /** 플레이어 쪽 잉크 필드가 없을 때의 임시 잉크(본체+0x698 대응) */
  localInk = 1;
  localRecoverStop = 0;
  respawns = -1;
  axis: V3 = [0, 0, 1];
  readonly views: BulletView[] = [];

  constructor(w: World) {
    const spec = w.data.players[0];
    this.set = loadSet(w, spec?.weapon ?? "Shooter_Normal_00");
    this.seeds = matchSeeds(w);
    const sv = readShooter(w, 0);
    this.owner = sv.id;
    this.team = sv.team;
    this.action = new ShooterAction(this.owner, this.team, this.set.wsp, w.frame, 0, this.seeds);
    for (const [k, v] of Object.entries(BULLET_SETTING)) this.thin.set(k, new WallDropThinOut(v.store, v.thin));
    w.shared.set("bullets", this.views);
  }

  step(w: World): void {
    for (const b of this.bullets) if (b.pre()) b.dead = true;
    for (const d of this.drops) d.move();
    for (const b of this.bullets) this.physics(w, b);
    for (const d of this.drops) {
      d.integrate();
      this.dropContact(w, d);
    }
    for (const b of this.bullets) if (b.contact && !b.dead) this.onContact(w, b, b.contact);
    for (const b of this.bullets) this.post19(w, b);
    for (const b of this.bullets) this.post21(w, b);
    for (const d of this.drops) d.post();
    this.fire(w);
    this.cleanup(w);
  }

  // ---- 물리(바디 스텝 0x7103b0a2bc) -------------------------------------
  private physics(w: World, b: Bullet): void {
    const p0: V3 = [0, 0, 0], p1: V3 = [0, 0, 0];
    b.body.begin(p0, p1);
    b.contact = null;
    const col = w.collision;
    const moved = p0[0] !== p1[0] || p0[1] !== p1[1] || p0[2] !== p1[2];
    if (col && !b.body.collisionOff && moved) {
      const from = v3(p0[0], p0[1], p0[2]), to = v3(p1[0], p1[1], p1[2]);
      let hit: Hit | null = b.rField > 0 ? col.sweepSphere(from, to, b.rField, Layer.Ground | Layer.Water) : null;
      if (b.rPlayer > 0) {
        const o = col.sweepSphere(from, to, b.rPlayer, Layer.Object);
        if (o && o.actor !== this.owner && (!hit || o.t < hit.t)) hit = o;
      }
      if (hit) {
        const f = Math.min(Math.max(hit.t, 0), 1);
        b.body.stopAt(p0, p1, f);
        b.contact = {
          f, point: toV3(hit.point), normal: toV3(hit.normal), layer: hit.layer, material: hit.material, actor: hit.actor,
          ground: (hit.layer & Layer.Ground) !== 0, paintable: this.paintable(w, hit),
        };
        return;
      }
    }
    b.body.commit(p1);
  }

  private paintable(w: World, h: Hit): boolean {
    if (h.actor >= 0 || (h.layer & Layer.Ground) === 0) return false;
    const m = (w.collision as unknown as { material?(i: number): { paintable?: boolean } | undefined }).material?.(h.material);
    return m?.paintable !== false;
  }

  // ---- 접촉(슬롯22 0x71017504f4 → 0x7101646910) -------------------------
  private onContact(w: World, b: Bullet, c: Contact): void {
    const dmg = b.params.dmg;
    let damaged = false;
    if (dmg && c.actor >= 0) {
      const h = w.hittables.get(c.actor);
      if (h) {
        const raw = shooterDamage(b.age, dmg);
        const sameTeam = h.team !== -1 && h.team === b.info.team;
        const value = sameTeam ? 0 : applyRate(raw, damageRate(w.data.tables, this.set.rateRow, h.rateCol));
        const vel: V3 = [b.vel[0], b.vel[1], b.vel[2]];
        const kb = knockback(value, vel, [0, 0, 0]);
        const l = Math.hypot(vel[0], vel[1], vel[2]) || 1;
        const info: DamageInfo & { knockback: V3; age: number; raw: number; bullet: number } = {
          attacker: b.info.owner, team: b.info.team, value, pos: v3(c.point[0], c.point[1], c.point[2]),
          dir: v3(vel[0] / l, vel[1] / l, vel[2] / l), rateRow: this.set.rateRow, critical: false, knockback: kb, age: b.age, raw, bullet: b.id,
        };
        if (!sameTeam) {
          h.onDamage(info);
          damaged = true;
        }
      }
    }
    const surface = !c.ground ? ((c.layer & Layer.Water) !== 0 ? "Water" : "Object") : c.normal[1] > FLOOR_NY ? "Floor" : "Wall";
    w.events.emit({
      type: "BulletHit", id: b.id, kind: b.kind, owner: b.info.owner, team: b.info.team, pos: c.point, normal: c.normal, surface,
      paintable: c.paintable, vel: [b.vel[0], b.vel[1], b.vel[2]], row: this.set.rateRow, target: c.actor >= 0 ? c.actor : undefined, damage: damaged,
    });
    if (!c.ground) this.slot60(b);
    else if (c.normal[1] > FLOOR_NY) this.slot58(w, b, c);
    else this.slot59(w, b, c);
  }

  /** 슬롯58 바닥 0x7101764de4: 슬롯84 도색 → hold = 슬롯91(0) → +0x12a = 1 */
  private slot58(w: World, b: Bullet, c: Contact): void {
    this.paintOnHit(w, b, c);
    b.hold = 0;
    if (b.dieWait === 0 && !b.dead) b.dieWait = 1;
  }

  /** 슬롯59 벽·천장 0x7101764ff8: hold = 슬롯92, 벽 낙하 자식, 충돌 끔, 위치 = 접촉점 */
  private slot59(w: World, b: Bullet, c: Contact): void {
    b.hold = b.params.wallHoldFrames;
    if (b.kind === "Shooter" || b.kind === "Splash") this.spawnWallDrop(w, b, c);
    if (b.hold >= 1) {
      b.body.collisionOff = true;
      b.showPos = [c.point[0], c.point[1], c.point[2]];
    } else if (b.dieWait === 0 && !b.dead) b.dieWait = 1;
  }

  /** 슬롯60 Ground 외 0x7101765794: +0x12a = 1 (도색·정지 없음) */
  private slot60(b: Bullet): void {
    if (b.dieWait === 0 && !b.dead) b.dieWait = 1;
  }

  /** 슬롯84: 슈터 0x7101751c08(지연 보관) / 스플래시 0x7101811b44(즉시) */
  private paintOnHit(w: World, b: Bullet, c: Contact): void {
    if (!b.info.local || !c.paintable) return;
    if (b.kind === "Shooter" && b.params.paint) {
      const p = b.params.paint;
      const wh = shooterWidthHalf(p, b.traveled);
      const ds = shooterDepthScale(p, b.info.pos, b.body.pos, b.sm.state, b.maxY);
      const dir = horizontalDir(b.vel, [0, 0, 0]);
      if (b.params.paintDelay > 0) {
        if (!b.pending) b.pending = { pos: c.point, normal: c.normal, dir, widthHalf: wh, depthScale: ds, stamp: requestStamp(w.frame) };
      } else this.paint(w, b, "Shooter", c.point, c.normal, dir, wh, ds, requestStamp(w.frame));
    } else if (b.kind === "Splash" && b.params.splashPaint) {
      const [wh, ds] = splashPaintSize(b.params.splashPaint, b.info.split !== 0, b.info.pos[1], b.body.pos[1]);
      const [dx, dz] = b.info.paintDir;
      const l = f32(Math.sqrt(f32(f32(dx * dx) + f32(dz * dz))));
      const dir: V3 = l > 0 ? [f32(dx / l), 0, f32(dz / l)] : [dx, 0, dz];
      this.paint(w, b, "Splash", c.point, c.normal, dir, wh, ds, requestStamp(w.frame));
    }
  }

  private paint(w: World, b: Bullet, kind: string, pos: V3, normal: V3, dir: V3, widthHalf: number, depthScale: number, seed: number, extra?: Record<string, unknown>): void {
    const req: PaintRequest & Record<string, unknown> = {
      team: b.info.team, owner: b.info.owner, pos: v3(pos[0], pos[1], pos[2]), normal: v3(normal[0], normal[1], normal[2]),
      dir: v3(dir[0], dir[1], dir[2]), widthHalf, depthScale, kind, seed, ...extra,
    };
    w.paint?.request(req);
  }

  // ---- 이동 후 처리 ---------------------------------------------------
  /** 슬롯19 0x71016461bc: 슬롯55(보관 도색 실행·꼬리), 낙하 소멸(DeactivateFallHeight) */
  private post19(w: World, b: Bullet): void {
    if (b.kind === "Shooter") b.tailPost();
    if (b.pending) {
      const p = b.pending;
      b.pending = null;
      this.paint(w, b, "ShooterDeferred", p.pos, p.normal, p.dir, p.widthHalf, p.depthScale, p.stamp);
    }
    const st = BULLET_SETTING[b.kind === "Shooter" ? "BulletShooterBase" : "BulletSplashShooter"];
    if (!b.fellOut && st.frame >= 0 && b.age >= st.frame) {
      if (!(f32(b.info.pos[1] - b.body.pos[1]) < f32(st.fall))) {
        b.fellOut = true;
        b.dead = true;
      }
    }
  }

  /** 슬롯21 0x7101646544: y < −10 → 소멸, 슬롯56(이동 거리·스플래시), +0x12a 감소 */
  private post21(w: World, b: Bullet): void {
    if (b.body.pos[1] < -10) b.dead = true;
    if (b.kind === "Shooter") splashOnMove(b, this.set.splashSpawn, this.seeds.sum, (info) => this.spawnSplash(w, b, info));
    if (b.dieWait !== 0) {
      b.dieWait -= 1;
      if (b.dieWait === 0) b.dead = true;
    }
  }

  private spawnSplash(w: World, parent: Bullet, info: SpawnInfo): void {
    const b = new Bullet(w.newId(), info, this.set.splash, this.seeds.sum);
    this.bullets.push(b);
    w.events.emit({ type: "BulletSpawn", id: b.id, kind: "Splash", owner: info.owner, team: info.team, pos: [...info.pos], vel: [...b.vel], parent: parent.id });
  }

  // ---- 벽 낙하 --------------------------------------------------------
  private spawnWallDrop(w: World, b: Bullet, c: Contact): void {
    if (!b.info.local) return;
    const col = w.collision;
    let point = c.point, normal = c.normal, paintable = c.paintable;
    if (col) {
      const r = Math.min(Math.max(b.rField, 0.05), 2000);
      const from = v3(b.prevPos[0], b.prevPos[1], b.prevPos[2]);
      const to = v3(f32(b.vel[0] + b.prevPos[0]), f32(b.vel[1] + b.prevPos[1]), f32(b.vel[2] + b.prevPos[2]));
      const h = col.sweepSphere(from, to, r, Layer.Ground);
      if (h && !(h.normal[1] > FLOOR_NY)) {
        point = toV3(h.point);
        normal = toV3(h.normal);
        paintable = this.paintable(w, h);
      }
    }
    if (!paintable) return;
    const vb: V3 = [b.vel[0], b.vel[1], b.vel[2]];
    if (!movingIntoWall(vb, normal)) return;
    const seed = (this.seeds.sum + b.info.frame) >>> 0;
    const splash = b.kind === "Splash";
    const q = quantize(splash ? this.set.wdMoveSplash : this.set.wdMove, splash ? this.set.wdPaintSplash : this.set.wdPaint, seed);
    if (!q) return;
    const frame = w.frame < 0 ? 0 : w.frame;
    if (col) {
      const s = v3(f32(point[0] + f32(0.1 * normal[0])), f32(point[1] + f32(0.1 * normal[1])), f32(point[2] + f32(0.1 * normal[2])));
      const e = v3(f32(s[0] - f32(0.1 * normal[0])), f32(s[1] - f32(0.1 * normal[1])), f32(s[2] - f32(0.1 * normal[2])));
      const h = col.sweepSphere(s, e, 0.1, Layer.Ground);
      if (h && !(h.normal[1] > FLOOR_NY)) {
        point = toV3(h.point);
        normal = toV3(h.normal);
      }
    }
    const body = c.actor >= 0 ? c.actor : 1;
    const thin = this.thin.get(b.kind === "Shooter" ? "BulletShooterBase" : "BulletSplashShooter");
    if (thin && !thin.admit(body, frame, point)) return;
    const pos: V3 = [f32(point[0] + f32(f32(0.05) * normal[0])), f32(point[1] + f32(f32(0.05) * normal[1])), f32(point[2] + f32(f32(0.05) * normal[2]))];
    const vel = wallDropVelocity(vb, normal, this.set.wdCommon);
    const d = new WallDrop(w.newId(), b.info.owner, b.info.team, pos, vel, [normal[0], normal[1], normal[2]], body, q, this.set.wdCommon, frame, this.seeds.sum);
    this.drops.push(d);
    w.events.emit({ type: "BulletSpawn", id: d.id, kind: "WallDrop", owner: d.owner, team: d.team, pos: [...pos], vel: [...vel], parent: b.id });
  }

  /** 벽 낙하 접촉: 반지름 0.2 구가 닿는 면(웹: 마지막 벽 법선 반대·아래 방향 레이 2개로 대신함). */
  private dropContact(w: World, d: WallDrop): void {
    const col = w.collision;
    if (!col || d.dead) return;
    const o = v3(d.pos[0], d.pos[1], d.pos[2]);
    const down = col.raycast(o, v3(0, -1, 0), WALL_DROP_RADIUS, Layer.Ground);
    if (down && down.normal[1] > FLOOR_NY) {
      const p = d.onGroundContact({ point: toV3(down.point), normal: toV3(down.normal), body: down.actor >= 0 ? down.actor : 1 });
      this.dropPaint(w, d, p);
      return;
    }
    const n = d.planeN;
    const side = col.raycast(o, v3(-n[0], -n[1], -n[2]), WALL_DROP_RADIUS, Layer.Ground);
    if (side && !(side.normal[1] > FLOOR_NY)) {
      const ct: WallContact = { point: toV3(side.point), normal: toV3(side.normal), body: side.actor >= 0 ? side.actor : 1 };
      const p = d.onWallContact(ct);
      if (p) this.dropPaint(w, d, p);
    }
  }

  private dropPaint(w: World, d: WallDrop, p: WallDropPaint): void {
    const req: PaintRequest & Record<string, unknown> = {
      team: d.team, owner: d.owner, pos: v3(p.pos[0], p.pos[1], p.pos[2]), normal: v3(p.normal[0], p.normal[1], p.normal[2]),
      dir: v3(p.dir[0], p.dir[1], p.dir[2]), widthHalf: f32(p.size * 0.5), depthScale: 1, kind: "WallDrop", seed: p.reqNo,
      seedDirect: p.seed, inkTexType: p.inkTexType, alpha: p.alpha, surface: p.kind,
    };
    w.paint?.request(req);
  }

  // ---- 사격 -----------------------------------------------------------
  private fire(w: World): void {
    const sv = readShooter(w, 0);
    if (sv.camPos && sv.camAt) {
      const a = cameraAxis(sv.camPos, sv.camAt, [0, 0, 0]);
      if (a) this.axis = a;
    }
    const pl = sv.raw;
    const respawns = pl && typeof pl.respawns === "number" ? (pl.respawns as number) : 0;
    if (respawns !== this.respawns) {
      this.respawns = respawns;
      this.action.reset(this.set.wsp, w.frame, 0, this.seeds);
      this.localInk = 1;
      this.localRecoverStop = 0;
    }
    const usePl = sv.ink !== null && pl !== null;
    const tank = (): number => (usePl ? (pl!.ink as number) : this.localInk);
    const setTank = (v: number): void => {
      if (usePl) pl!.ink = v;
      else this.localInk = v;
    };
    const stop = (n: number): void => {
      if (pl && typeof pl.inkRecoverStop === "number") pl.inkRecoverStop = Math.max(pl.inkRecoverStop as number, n);
      else this.localRecoverStop = Math.max(this.localRecoverStop, n);
    };
    let lack = false;
    const ink: InkPort = {
      can: (cost) => canConsumeInk(tank(), cost),
      consume: (cost) => {
        const next = consumeInk(tank(), cost, INK_RECOVER_STD);
        if (next === null) {
          lack = true;
          return false;
        }
        setTank(next);
        return true;
      },
      recoverStop: (frames) => stop(frames),
      lack: (frames) => {
        lack = true;
        stop(frames);
      },
      postDelay: (n) => {
        if (pl && typeof pl.squidLock === "number") pl.squidLock = Math.max(pl.squidLock as number, n);
      },
    };
    const actions: string[] = [];
    const shot = this.action.step(this.set.wsp, this.set.splashSpawn, this.set.add, {
      zr: (w.pad.hold & Btn.Fire) !== 0 && (w.pad.hold & Btn.Squid) === 0, squid: sv.blocked, pos: sv.pos, vel: sv.vel, aim: sv.aim, axis: this.axis,
      rigForward: sv.rigForward, pitch: sv.pitch, airFramesGe4: sv.airFrames >= 4, jumped: sv.jumped, frame: w.frame,
      seeds: this.seeds, spawnSpeed: this.set.shooter.move.SpawnSpeed,
    }, ink, actions);
    if (!usePl) this.localRecover();
    if (pl && typeof pl.weapon === "object" && pl.weapon) {
      const link = pl.weapon as { shooting?: boolean; moveSpeed?: number; frame?: number };
      link.shooting = this.action.firing;
      link.moveSpeed = this.set.wsp.MoveSpeed;
      link.frame = w.frame;
    }
    for (const a of actions) w.events.emit({ type: a, owner: this.owner, weapon: this.set.weapon });
    if (lack) w.events.emit({ type: "NoInk", owner: this.owner });
    if (!shot) return;
    const info: SpawnInfo = {
      kind: "Shooter", owner: this.owner, team: this.team, weapon: this.set.weapon, pos: shot.pos, dir: shot.dir, speed: shot.speed,
      extraSpeed: 0, frame: shot.frame, split: shot.split, angle: shot.angle, local: true, paintDir: [0, 0],
    };
    const b = new Bullet(w.newId(), info, this.set.shooter, this.seeds.sum);
    scheduleSplash(b, this.set.splashSpawn, this.seeds.sum);
    this.bullets.push(b);
    w.events.emit({ type: "Fire", owner: this.owner, team: this.team, pos: [...shot.pos], dir: [...shot.dir], vel: [...shot.vel], weapon: this.set.weapon, bullet: b.id });
    w.events.emit({ type: "BulletSpawn", id: b.id, kind: "Shooter", owner: this.owner, team: this.team, pos: [...shot.pos], vel: [...b.vel] });
  }

  /** 잉크 회복은 physics 담당(본체+0x698, 0x7102483134). 플레이어 쪽 필드가 없을 때만 임시로 같은 식(정지 카운터 → 기어 0 Std 1/600)을 쓴다. */
  private localRecover(): void {
    if (this.localRecoverStop > 0) this.localRecoverStop--;
    else if (this.localInk < 1) this.localInk = Math.min(f32(this.localInk + Math.min(INK_RECOVER_STD, f32(1 - this.localInk))), 1);
  }

  // ---- 정리 -----------------------------------------------------------
  private cleanup(w: World): void {
    const keep: Bullet[] = [];
    for (const b of this.bullets) {
      if (b.dead) w.events.emit({ type: "BulletDie", id: b.id, kind: b.kind, pos: [...b.body.pos] });
      else keep.push(b);
    }
    this.bullets = keep;
    const kd: WallDrop[] = [];
    for (const d of this.drops) {
      if (d.dead) w.events.emit({ type: "BulletDie", id: d.id, kind: "WallDrop", pos: [...d.pos] });
      else kd.push(d);
    }
    this.drops = kd;
    const vs = this.views;
    vs.length = 0;
    for (const b of this.bullets) {
      vs.push({
        id: b.id, kind: b.kind, owner: b.info.owner, team: b.info.team, pos: b.body.collisionOff ? b.showPos : b.body.pos, prevPos: b.prevPos,
        vel: b.vel, radius: b.rField, age: b.age, tail: b.kind === "Shooter" && b.tailStarted ? b.tailB : null, stuck: b.hold >= 1,
      });
    }
    for (const d of this.drops) {
      vs.push({ id: d.id, kind: "WallDrop", owner: d.owner, team: d.team, pos: d.pos, prevPos: d.pos, vel: d.vel, radius: WALL_DROP_RADIUS, age: d.age, tail: null, stuck: false });
    }
    const dbg = (w.shared.get("debug") as Record<string, unknown> | undefined) ?? {};
    if (!w.shared.has("debug")) w.shared.set("debug", dbg);
    dbg["weapon.bullets"] = this.bullets.length;
    dbg["weapon.drops"] = this.drops.length;
    dbg["weapon.ink"] = readShooter(w, 0).ink ?? this.localInk;
  }
}
