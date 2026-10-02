// 담당: [range] — docs/impl/range.md 에 구현 상태·미확정을 기록한다. 분석 명세: docs/range/shooting_range.md.
// 시험 사격장(대전 로비 Lby_Lobby00): 표적 spl::SighterTarget(일반·대형·이동), 사격 구역 LobbyShootingArea, 시작 위치.
// 팁 시험(TipsTrial)·나무 인형·PaintedArea·기믹 스포너는 1차 범위 밖(분석만 — 문서 §1, §11).
import { f32 } from "../fmath.ts";
import type { CollisionWorld, DamageInfo, Hittable, Team } from "../types.ts";
import { Layer } from "../types.ts";
import type { System, World } from "../world.ts";
import { insideAnyArea, makeArea, updateShootLatch, type ShootingArea } from "./area.ts";
import { AREA_LOCATORS, BEND_PARAM_DEFAULTS, SIGHTER_ACTORS, SIGHTER_PARAM_DEFAULTS, SIGHTER_SHAPES, SIGHTER_TABLES, type SighterParam } from "./data.ts";
import { readActors, readRails, type PlacedActor } from "./placement.ts";
import { eulerZYXToQuat, RailMover, railMoveParam, RailPath, type Quat } from "./rail.ts";
import { SIGHTER_STATE_NAMES, SighterTarget, type RateFn } from "./target.ts";

export { SighterTarget, SighterState, DamageResult } from "./target.ts";
export { insideArea, insideAnyArea, updateShootLatch } from "./area.ts";
export { RailMover, RailPath } from "./rail.ts";

/** world.shared "range" 의 표적 한 개(표시용 읽기 전용 사본) */
export interface RangeTargetView {
  id: number;
  kind: string;
  model: string;
  pos: [number, number, number];
  rot: Quat;
  scale: number;
  team: Team;
  state: number;
  stateName: string;
  anim: string;
  animFrame: number;
  animFrames: number;
  hp: number;
  maxHp: number;
  bodiesEnabled: boolean;
  bend: { on: boolean; angleDeg: number; weight: number };
  /** vt19: 표시 대상이면 active. 거리 조건(카메라 ≤ distance)은 화면 쪽에서 */
  damageInfo: { active: boolean; value: number; isMax: boolean; pos: [number, number, number]; distance: number };
}

export interface RangeShared {
  targets: RangeTargetView[];
  areas: ShootingArea[];
  /** 본체+0x938d 에 해당: 로컬 플레이어가 사격 구역 안 */
  inShootingArea: boolean;
  /** 본체+0x938c 에 해당: 공중 4프레임 미만일 때만 inShootingArea 로 갱신되는 래치 */
  canShoot: boolean;
  startPositions: { kind: "StartPos" | "StartPosTipsTrial"; name: string; team: string; pos: [number, number, number]; rot: [number, number, number] }[];
}

export interface RangeOptions {
  /** 팁 시험 표적도 만든다(기본 false: 팁 시험 진행 로직이 없으므로 원본 일반 로비처럼 비활성) */
  includeTipsTrial?: boolean;
}

function teamOf(local: number): Team {
  // 0x71021ef388: uVar14 = (로컬 플레이어 팀 != 1) → 표적 팀
  return local !== 1 ? 1 : 0;
}

function makeRate(w: World): RateFn {
  const t = w.data.tables["damage_rate_info"] as { default?: number; rows?: Record<string, Record<string, number>> } | undefined;
  return (row, col) => {
    const r = row || "Default";
    const c = col || "Default";
    const v = t?.rows?.[r]?.[c];
    return typeof v === "number" ? f32(v) : f32(t?.default ?? 1.0);
  };
}

/** GameParameterTable 우선(에셋), 없으면 data.ts 의 원본 값 */
function sighterParams(w: World, table: string): { param: SighterParam; bend: { Kp: number; Kd: number }; maxHitPoint: number } {
  const store = w.data.params;
  if (store && store.has(table)) {
    const sp = store.get<Partial<SighterParam>>(table, "spl__SighterTargetParam");
    const bp = store.get<{ Kp?: number; Kd?: number }>(table, "spl__BendCalculatorParam");
    const dp = store.get<{ HitPointHolderArray?: { MaxHitPoint?: number }[] }>(table, "spl__DamageParam");
    return {
      param: { ...SIGHTER_PARAM_DEFAULTS, ...strip(sp) },
      bend: { Kp: f32(bp.Kp ?? BEND_PARAM_DEFAULTS.Kp), Kd: f32(bp.Kd ?? BEND_PARAM_DEFAULTS.Kd) },
      maxHitPoint: dp.HitPointHolderArray?.[0]?.MaxHitPoint ?? fallback(table).maxHitPoint,
    };
  }
  return fallback(table);
}

function strip<T extends object>(o: T): Partial<T> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(o)) if (k !== "$type" && v !== undefined) out[k] = typeof v === "number" ? f32(v) : v;
  return out as Partial<T>;
}

function fallback(table: string): { param: SighterParam; bend: { Kp: number; Kd: number }; maxHitPoint: number } {
  const chain: string[] = [];
  for (let t: string | undefined = table; t && SIGHTER_TABLES[t]; t = SIGHTER_TABLES[t].parent) chain.unshift(t);
  let param: SighterParam = { ...SIGHTER_PARAM_DEFAULTS };
  let bend = { ...BEND_PARAM_DEFAULTS };
  let maxHitPoint = 0;
  for (const t of chain) {
    const e = SIGHTER_TABLES[t];
    param = { ...param, ...e.sighter };
    if (e.bend) bend = { ...e.bend };
    if (e.maxHitPoint !== undefined) maxHitPoint = e.maxHitPoint;
  }
  return { param, bend, maxHitPoint };
}

class RangeSystem implements System {
  readonly id = "range";
  readonly opts: RangeOptions;
  targets: SighterTarget[] = [];
  /** 표적 id → Main 몸 충돌 id */
  private mainIds = new Map<number, number>();
  private registered = new Map<number, boolean>();
  areas: ShootingArea[] = [];
  private shared: RangeShared = { targets: [], areas: [], inShootingArea: false, canShoot: false, startPositions: [] };
  private world: World | null = null;
  private rate: RateFn = () => 1;

  constructor(opts: RangeOptions) {
    this.opts = opts;
  }

  init(w: World): void {
    this.world = w;
    this.rate = makeRate(w);
    const actors = readActors(w.data.placement);
    const rails = readRails(w.data.placement).map((r) => new RailPath(r));
    const localTeam = w.data.players[0]?.team ?? 0;
    for (const a of actors) {
      const spec = SIGHTER_ACTORS[a.name];
      if (spec) {
        const t = this.makeTarget(w, a, spec, rails, teamOf(localTeam));
        if (t.tipsTrial && !this.opts.includeTipsTrial) continue;
        this.targets.push(t);
        continue;
      }
      const area = AREA_LOCATORS[a.name];
      if (area) this.areas.push(makeArea(a.name, area.shape, area.scale, a.pos, a.rot, a.scale));
      if (a.name === "StartPos" || a.name === "StartPosTipsTrial") {
        const prm = a.params["spl__StartPosParam"] ?? a.params["spl__StartPosForTipsTrialParam"];
        this.shared.startPositions.push({ kind: a.name, name: String(prm?.Name ?? ""), team: a.team, pos: a.pos, rot: a.rot });
      }
    }
    this.shared.areas = this.areas;
    for (const t of this.targets) {
      const hit: Hittable = {
        id: t.id,
        team: t.team,
        rateCol: t.rateCol,
        onDamage: (info) => this.onDamage(t, info),
      };
      w.hittables.set(t.id, hit);
      this.mainIds.set(t.id, w.newId());
      this.syncCollision(w.collision, t);
    }
    w.shared.set("range", this.shared);
    this.publish();
  }

  private makeTarget(w: World, a: PlacedActor, spec: { table: string; model: string; elink: string }, rails: RailPath[], team: Team): SighterTarget {
    const prm = sighterParams(w, spec.table);
    let rail: RailMover | null = null;
    const to = a.params["spl__RailMovableSequentialHelperBancParam"]?.ToRailPoint;
    if (to !== undefined && to !== null && String(to) !== "0") {
      const key = String(to);
      for (const r of rails) {
        const i = r.indexOf(key);
        if (i >= 0) {
          rail = new RailMover(r, railMoveParam(a.params["game__RailMovableSequentialParam"]), i);
          break;
        }
      }
    }
    return new SighterTarget(w.newId(), {
      kind: a.name,
      model: spec.model,
      elink: spec.elink,
      param: prm.param,
      bend: prm.bend,
      maxHitPoint: prm.maxHitPoint,
      pos: a.pos,
      rot: eulerZYXToQuat(a.rot[0], a.rot[1], a.rot[2]),
      team,
      rail,
    });
  }

  private onDamage(t: SighterTarget, info: DamageInfo): void {
    const w = this.world;
    const out = t.receive(info, this.rate);
    // 탄 접촉 휨 충격(vt22): 접촉 속도(y=0) × BulletImpulsScaler. 속도는 DamageInfo 확장 필드 vel(프레임당)에서 — 문서 §6.3, 조정 요청.
    const vel = (info as DamageInfo & { vel?: ArrayLike<number> }).vel;
    if (vel && t.bodiesEnabled) {
      const s = t.cfg.param.BulletImpulsScaler;
      t.addBendImpulse(info.pos, [f32(f32(vel[0] * 60) * s), 0, f32(f32(vel[2] * 60) * s)], 0);
    }
    w?.events.emit({ type: "Damage", target: t.id, value: out.damage, result: out.result, critical: info.critical, pos: [info.pos[0], info.pos[1], info.pos[2]], attacker: info.attacker });
    this.flushEvents(t);
  }

  private flushEvents(t: SighterTarget): void {
    const w = this.world;
    if (!w) return;
    for (const e of t.pendingEvents) w.events.emit(e);
    t.pendingEvents.length = 0;
  }

  private syncCollision(c: CollisionWorld | null, t: SighterTarget): void {
    if (!c) return;
    const on = t.bodiesEnabled;
    const was = this.registered.get(t.id);
    const mainId = this.mainIds.get(t.id)!;
    if (!on) {
      if (was !== false) {
        c.setDynamic(t.id, null);
        c.setDynamic(mainId, null);
        this.registered.set(t.id, false);
      }
      return;
    }
    if (was === true && !t.cfg.rail) return;
    const cb = SIGHTER_SHAPES.colBullet, mn = SIGHTER_SHAPES.main;
    // ColBullet: 탄이 맞는 캡슐 → Layer.Object, Main: 플레이어를 막는 캡슐 → Layer.KeepOut (문서 §9.3, 조정 요청)
    c.setDynamic(t.id, { kind: "capsule", a: v(t.toWorld(cb.a)), b: v(t.toWorld(cb.b)), radius: f32(cb.radius * t.scale), layer: Layer.Object });
    c.setDynamic(mainId, { kind: "capsule", a: v(t.toWorld(mn.a)), b: v(t.toWorld(mn.b)), radius: f32(mn.radius * t.scale), layer: Layer.KeepOut });
    this.registered.set(t.id, true);
  }

  step(w: World): void {
    for (const t of this.targets) {
      t.step();
      this.syncCollision(w.collision, t);
      this.flushEvents(t);
    }
    // 사격 구역: 로컬 플레이어 위치가 있으면 판정(0x7102484ff8~)
    const pl = w.shared.get("player") as { pos?: ArrayLike<number>; airFrames?: number } | undefined;
    if (pl?.pos && this.areas.length) {
      const inside = insideAnyArea(this.areas, pl.pos);
      this.shared.inShootingArea = inside;
      this.shared.canShoot = updateShootLatch(this.shared.canShoot, inside, pl.airFrames ?? 0);
    }
    this.publish();
  }

  private publish(): void {
    this.shared.targets = this.targets.map((t) => ({
      id: t.id,
      kind: t.cfg.kind,
      model: t.cfg.model,
      pos: [...t.pos] as [number, number, number],
      rot: [...t.rot] as Quat,
      scale: t.scale,
      team: t.team,
      state: t.state,
      stateName: SIGHTER_STATE_NAMES[t.state],
      anim: t.anim,
      animFrame: t.animFrame,
      animFrames: t.animFrames,
      hp: t.holder.hp,
      maxHp: t.holder.max,
      bodiesEnabled: t.bodiesEnabled,
      bend: { on: t.bendAnimOn, angleDeg: t.bendAngleDeg, weight: t.bendWeight },
      damageInfo: {
        active: t.damageInfoActive,
        value: f32(t.accum / 10),
        isMax: t.holder.max <= t.accum,
        pos: t.damageInfoPos(),
        distance: t.cfg.param.DrawDamageInfoDistance,
      },
    }));
  }
}

function v(a: [number, number, number]): Float32Array {
  return new Float32Array(a);
}

export function createRangeSystem(opts: RangeOptions = {}): System {
  return new RangeSystem(opts);
}
