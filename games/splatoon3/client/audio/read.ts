// fx·audio 공용: 코어 이벤트 수집(프레임 번호와 함께), world.shared 읽기, SubjectiveType.
import type { GameEvent } from "../../core/events.ts";
import { Layer } from "../../core/types.ts";
import type { World } from "../../core/world.ts";

export type V3 = [number, number, number];

export function vec(v: unknown): V3 | null {
  if (!v || typeof v !== "object") return null;
  const o = v as Record<string, number> & ArrayLike<number>;
  if (typeof o.x === "number") return [o.x, o.y, o.z];
  if (typeof o[0] === "number" && typeof o[2] === "number") return [o[0], o[1], o[2]];
  return null;
}

export const num = (x: unknown): number | null => (typeof x === "number" && Number.isFinite(x) ? x : null);

export interface FrameEvent {
  frame: number;
  e: GameEvent;
}

/**
 * 렌더 프레임 하나에 고정 스텝이 여러 번 돌면 world.step 이 앞 스텝 이벤트를 비운다(core/world.ts).
 * 이벤트를 잃지 않도록 EventQueue.clear 직전에 목록을 보관한다(같은 World 에 하나만 건다).
 * 근본 해결은 조정 요청(docs/impl/fx.md): 뷰에 스텝별 이벤트를 넘겨 주는 훅.
 */
class EventTap {
  private readonly w: World;
  private readonly hist: FrameEvent[] = [];
  private base = 0; // hist[0] 의 전체 순번
  private takenLive = 0; // 현재 list 에서 이미 hist 로 옮긴 개수
  private readonly cursors = new Map<string, number>();

  constructor(w: World) {
    this.w = w;
    const q = w.events;
    const clear = q.clear.bind(q);
    q.clear = () => {
      this.pull();
      this.takenLive = 0;
      clear();
    };
  }

  private pull(): void {
    const list = this.w.events.list;
    // clear 는 step 시작에서 부른다: 남아 있는 목록은 직전 스텝(frame-1) 것이다.
    for (let i = this.takenLive; i < list.length; i++) this.hist.push({ frame: this.w.frame - 1, e: list[i] });
    this.takenLive = list.length;
  }

  register(consumer: string): void {
    if (!this.cursors.has(consumer)) this.cursors.set(consumer, this.base + this.hist.length);
  }

  drain(consumer: string): FrameEvent[] {
    this.pull();
    this.register(consumer);
    const end = this.base + this.hist.length;
    const from = this.cursors.get(consumer)!;
    this.cursors.set(consumer, end);
    const out = this.hist.slice(from - this.base);
    let min = end;
    for (const c of this.cursors.values()) min = Math.min(min, c);
    if (min > this.base) {
      this.hist.splice(0, min - this.base);
      this.base = min;
    }
    return out;
  }
}

const taps = new WeakMap<World, EventTap>();

function tap(w: World): EventTap {
  let t = taps.get(w);
  if (!t) {
    t = new EventTap(w);
    taps.set(w, t);
  }
  return t;
}

/** 뷰 생성 때 부른다. 이 시점 이후 이벤트를 받는다. */
export function registerEvents(w: World, consumer: string): void {
  tap(w).register(consumer);
}

export function drainEvents(w: World, consumer: string): FrameEvent[] {
  return tap(w).drain(consumer);
}

/** world.shared "player"(physics 담당) — 타입 export 전이라 넓게 읽는다. 없는 필드는 null. */
export interface PlayerRead {
  id: number | null;
  pos: V3 | null;
  vel: V3 | null;
  team: number;
  squid: boolean;
  onGround: boolean | null;
  groundNormal: V3 | null;
  groundMaterial: number | null;
  inInk: boolean | null;
  /** 잉크 속 잠복(PlayerState.swimming) */
  swimming: boolean | null;
  /** 발밑 잉크 분류 PlayerStepPaint +0x30: 0/1 아군, 2/3 적, 4/5 없음 */
  stepCls: number | null;
}

export function readPlayer(w: World): PlayerRead | null {
  const p = w.shared.get("player") as Record<string, unknown> | undefined;
  if (!p || typeof p !== "object") return null;
  const b = (k: string[]): boolean | null => {
    for (const x of k) if (typeof p[x] === "boolean") return p[x] as boolean;
    return null;
  };
  return {
    id: num(p.id) ?? num(p.actor),
    pos: vec(p.pos ?? p.position),
    vel: vec(p.vel ?? p.velocity),
    team: num(p.team) ?? 0,
    squid: !!(p.squid ?? p.isSquid),
    onGround: b(["onGround", "grounded", "isGround"]),
    groundNormal: vec(p.groundNormal ?? p.gndNormal),
    groundMaterial: num(p.groundMaterial ?? p.gndMaterial),
    inInk: b(["inInk", "inFriendInk", "onFriendInk"]),
    swimming: b(["swimming"]),
    stepCls: num((p.step as Record<string, unknown> | undefined)?.cls),
  };
}

export type Subjective = "Focused" | "Friend" | "Enemy";

/** SubjectiveType: 기준 플레이어 자신 / 아군 / 적 (effect_sound.md §6 subjective). */
export function subjective(owner: unknown, ownerTeam: number | null, local: PlayerRead | null): Subjective {
  if (!local || local.id === null || owner === undefined || owner === null || owner === local.id) return "Focused";
  return ownerTeam === null || ownerTeam === local.team ? "Friend" : "Enemy";
}

/** 무기 id → XLink 사용자 이름(액터 이름). 근거: effect_sound.md §2 (Shooter_Normal_00 → WeaponShooterNormal) */
export const WEAPON_USER: Record<string, string> = {
  Shooter_Normal_00: "WeaponShooterNormal",
};

export function weaponUser(weapon: unknown): string {
  const s = typeof weapon === "string" ? weapon : "";
  if (s in WEAPON_USER) return WEAPON_USER[s];
  if (s.startsWith("Weapon")) return s;
  return "WeaponShooterNormal";
}

/**
 * 플레이어 XLink 로컬 속성(Player_* · PlayerFoot · SplPlayer)을 웹 상태에서 근사로 채운다.
 * 원본에서 이 값을 쓰는 코드는 추적하지 않았다 — 값 이름의 뜻대로 [추정]. 경계값(경사 등)은 쓰지 않는다.
 */
export function playerProps(w: World, p: PlayerRead): Record<string, string | number> {
  const out: Record<string, string | number> = {
    TransformType: p.squid ? "Squid" : "Human",
    TroubleType: "Normal",
    IsCoopFloat: "False",
    SpecialType: "NoSpecial",
    GrindRailType: "None",
  };
  if (p.vel) {
    out.MoveVelXZ = Math.hypot(p.vel[0], p.vel[2]);
    out.FallVelY = -p.vel[1];
  }
  if (p.onGround !== null) out.FieldAngleType = p.onGround ? "Plane" : "Air";
  if (p.swimming !== null) out.SquidStealth = p.swimming ? "True" : "False";
  if (p.stepCls !== null) out.GndPaintTeamType = p.stepCls < 2 ? "OnFriend" : p.stepCls < 4 ? "OnEnemy" : "OnNeutral";
  else if (p.pos && w.paint) {
    try {
      const s = w.paint.sample(new Float32Array(p.pos), 0);
      out.GndPaintTeamType = s.team < 0 ? "OnNeutral" : s.team === p.team ? "OnFriend" : "OnEnemy";
    } catch {
      // paint 미구현
    }
  }
  if (p.pos && w.collision) {
    try {
      const o = new Float32Array([p.pos[0], p.pos[1] + 0.5, p.pos[2]]);
      const h = w.collision.raycast(o, new Float32Array([0, -1, 0]), 2, Layer.Ground);
      if (h) out.GndMaterial = w.collision.materialName(h.material);
    } catch {
      // collision 미구현
    }
  }
  return out;
}

/** 오징어 애니 슬롯 액션(이동 중이면 Sqd_Walk, 아니면 Sqd_Wait) — Swim 이벤트(시작만)와 같은 조건 [추정] */
export function squidAnim(p: PlayerRead | null): string | null {
  if (!p || !p.squid) return null;
  const hv = p.vel ? Math.hypot(p.vel[0], p.vel[2]) : 0;
  return p.swimming && hv > 0.001 ? "Sqd_Walk" : "Sqd_Wait";
}

/** game::DamageResultType (core/range DamageResult) → HitEffectConfig 반응 열 이름. 0 Through 는 대미지 반응이 없다. */
export const DAMAGE_REACTION: Record<number, string> = { 4: "Invincible", 5: "Armored", 6: "Damaged", 7: "Cure" };

export function damageReaction(e: Record<string, unknown>): string | null {
  if (typeof e.reaction === "string") return e.reaction;
  const r = num(e.result);
  if (r === null) return "Damaged";
  return DAMAGE_REACTION[r] ?? null;
}

/** 같은 프레임의 BulletHit 중 Damage 와 같은 명중(대상 id 또는 위치)을 찾는다 — 탄 속도·법선·팀을 얻기 위해 */
export function matchHit(events: Record<string, unknown>[], d: Record<string, unknown>): Record<string, unknown> | null {
  const p = vec(d.pos);
  let best: Record<string, unknown> | null = null;
  let bd = Infinity;
  for (const e of events) {
    if (e.type !== "BulletHit") continue;
    if (d.target !== undefined && e.target === d.target) return e;
    const q = vec(e.pos);
    if (!p || !q) continue;
    const dd = Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]);
    if (dd < bd) {
      bd = dd;
      best = e;
    }
  }
  return bd < 1e-3 ? best : null;
}

/** world.shared "camera"(camera 담당 CameraShared): 위치·주시점·리그 수평 시선(+0x1a4 = 본체 +0x538 사본) */
export interface CameraRead {
  pos: V3;
  forward: V3;
  right: V3;
  rigForward: V3 | null;
}

export function readCamera(w: World): CameraRead | null {
  const c = w.shared.get("camera") as Record<string, unknown> | undefined;
  const pos = vec(c?.pos);
  const tg = vec(c?.target);
  if (!pos || !tg) return null;
  let f: V3 = [tg[0] - pos[0], tg[1] - pos[1], tg[2] - pos[2]];
  const l = Math.hypot(f[0], f[1], f[2]);
  f = l > 0 ? [f[0] / l, f[1] / l, f[2] / l] : [0, 0, 1];
  // 오른쪽 = forward × up (three 오른손 좌표: 카메라 -Z 가 앞, +X 가 오른쪽)
  let r: V3 = [-f[2], 0, f[0]];
  const rl = Math.hypot(r[0], r[2]);
  r = rl > 0 ? [r[0] / rl, 0, r[2] / rl] : [1, 0, 0];
  return { pos, forward: f, right: r, rigForward: vec(c?.rigForward) };
}
