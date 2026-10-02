// 담당: [fx] — docs/impl/fx.md 에 구현 상태·미확정을 기록한다.
// 코어 이벤트 → XLink SLink → WebAudio. 근거 docs/effect_sound/effect_sound.md §3, sound_resources.md.
import type * as THREE from "three";
import type { ClientContext, View } from "../context.ts";
import { DEV } from "../env.ts";
import type { World } from "../../core/world.ts";
import { fxData, type FxData } from "./data.ts";
import { HitEffectTable } from "./hiteffect.ts";
import { damageReaction, drainEvents, matchHit, num, readCamera, playerProps, readPlayer, registerEvents, squidAnim, subjective, vec, weaponUser, type PlayerRead, type V3 } from "./read.ts";
import { SoundPlayer } from "./sound.ts";
import { XLinkInstance } from "./xlink.ts";

/** 발사 xlink 컬링 R (0x71027e22bc). 기준 팀 조건의 n(팀별 구조체 +0x10)은 의미 미확정 → 0 으로 둔다. */
export const FIRE_CULL_R = 600;
/** 히트 이펙트 컬링 R (0x71027e24a8). 같은 이유로 n = 0. */
export const HIT_CULL_R = 400;

/** 플레이어 이벤트 → 액션 슬롯(이름 대응 [추정], docs/impl/fx.md §플레이어). 이벤트에 slot/action 이 있으면 그것을 쓴다. */
export const PLAYER_ACTIONS: Record<string, { slot: string; human?: string; squid?: string }[]> = {
  Jump: [{ slot: "State", human: "Human_JumpSt", squid: "Squid_JumpSt" }],
  Land: [{ slot: "State", human: "Human_JumpEd", squid: "Squid_JumpEd" }],
  ToSquid: [{ slot: "SklAnim_Human", human: "ToSquid", squid: "ToSquid" }],
  ToHuman: [{ slot: "SklAnim_Human", human: "ToHuman", squid: "ToHuman" }],
  Swim: [
    { slot: "SklAnim_Squid", squid: "Sqd_Walk" },
    { slot: "State", squid: "Squid_Move" },
  ],
};

interface BulletTrack {
  pos: V3;
  vel: V3 | null;
  team: number | null;
  owner: unknown;
}

interface HitAgg {
  key: string;
  count: number;
  pos: V3;
  owner: unknown;
  team: number | null;
}

export class AudioSystem {
  readonly data: FxData;
  readonly player: SoundPlayer;
  private readonly w: World;
  private readonly weapons = new Map<string, XLinkInstance>();
  private hitInst: XLinkInstance | null = null;
  private readonly playerInst = new Map<string, XLinkInstance>();
  private readonly bullets = new Map<unknown, BulletTrack>();
  private lastFrame = -1;
  private squidAnim: string | null = null;
  private local: PlayerRead | null = null;
  readonly missing = new Set<string>();

  constructor(ac: AudioContext, w: World, data: FxData) {
    this.w = w;
    this.data = data;
    this.player = new SoundPlayer(ac, data);
  }

  get hitTable(): HitEffectTable {
    return this.data.hit;
  }

  private slink(name: string): XLinkInstance | null {
    const u = this.data.slink.get(name);
    if (!u) {
      this.missing.add(name);
      return null;
    }
    const inst = new XLinkInstance(u, this.player);
    inst.global = (n) => (n === "SpecMode" ? "Versus" : undefined); // 사격장 SpecMode [추정]
    return inst;
  }

  private weaponInst(user: string, owner: unknown): XLinkInstance | null {
    const k = `${user}#${String(owner)}`;
    let i = this.weapons.get(k);
    if (!i) {
      const n = this.slink(user);
      if (!n) return null;
      i = n;
      this.weapons.set(k, i);
    }
    return i;
  }

  private hitEffect(): XLinkInstance | null {
    if (!this.hitInst) this.hitInst = this.slink("HitEffect");
    return this.hitInst;
  }

  private playerUser(name: string): XLinkInstance | null {
    let i = this.playerInst.get(name);
    if (!i) {
      const n = this.slink(name);
      if (!n) return null;
      i = n;
      this.playerInst.set(name, i);
    }
    return i;
  }

  /** 청자 = 카메라(shared camera 가 있으면 그 위치, 없으면 three 카메라). 원본 리스너(TargetOffset: 카메라~주시점 사이)는 계산 미판독. */
  setListener(cam: THREE.Camera): void {
    const c = readCamera(this.w);
    if (c) {
      this.player.listener = { pos: c.pos, right: c.right };
      return;
    }
    cam.updateMatrixWorld();
    const e = cam.matrixWorld.elements;
    this.player.listener = { pos: [e[12], e[13], e[14]], right: [e[0], e[1], e[2]] };
  }

  private far(pos: V3 | null, r: number): boolean {
    if (!pos) return false;
    const l = this.player.listener.pos;
    const dx = pos[0] - l[0], dy = pos[1] - l[1], dz = pos[2] - l[2];
    return r * r < dx * dx + dy * dy + dz * dz; // 엄격 부등호(정확히 R 이면 방출)
  }

  private ownerTeam(owner: unknown, e: Record<string, unknown>): number | null {
    const t = num(e.team);
    if (t !== null) return t;
    if (this.local && (owner === this.local.id || this.local.id === null)) return this.local.team;
    return null;
  }

  /** 한 게임 프레임의 이벤트 처리 */
  frame(frame: number, events: Record<string, unknown>[]): void {
    this.local = readPlayer(this.w);
    const s1 = new Map<string, HitAgg>();
    for (const e of events) {
      const type = e.type as string;
      switch (type) {
        case "Fire":
          this.onFire(e);
          break;
        case "BulletSpawn": {
          const pos = vec(e.pos);
          if (pos) this.bullets.set(e.id, { pos, vel: vec(e.vel), team: num(e.team), owner: e.owner });
          break;
        }
        case "BulletDie":
          this.bullets.delete(e.id);
          break;
        case "BulletHit":
          this.onBulletHit(e, s1);
          break;
        case "Damage":
          this.onDamage(e, s1, matchHit(events, e));
          // 표적 자신의 SLink "ダメージ" — 방출 코드 미확인, 키 이름으로 본 대응 [추정]
          if (e.target !== undefined && damageReaction(e)) this.targetKey(e, "ダメージ");
          break;
        case "Break":
          // range: Burst 진입의 ELink "Break"(0x71021f14a0). 같은 키가 SLink 표적 사용자에도 있어 함께 낸다 [추정: mode 2]
          this.targetKey(e, "Break");
          break;
        case "Jump":
        case "Land":
        case "ToSquid":
        case "ToHuman":
        case "Swim":
          this.onPlayer(type, e);
          break;
      }
    }
    // 같은 프레임의 S1 명중을 묶어 AggregateNum 과 함께 방출(0x71027b4aa4 → 0x71027b7938, 묶는 기준 미판독)
    const he = this.hitEffect();
    for (const a of s1.values()) {
      if (!he) break;
      he.props.set("AggregateNum", Math.min(a.count, 15));
      he.props.set("SubjectiveType", subjective(a.owner, a.team, this.local));
      he.searchAndEmit(a.key, { pos: a.pos });
    }
    const sa = squidAnim(this.local);
    if (sa && sa !== this.squidAnim) this.setPlayerAction("SklAnim_Squid", sa);
    this.squidAnim = sa;
    this.trackBullets();
    this.updatePlayerProps();
    for (const i of this.playerInst.values()) i.calc();
    for (const i of this.weapons.values()) i.calc();
    this.lastFrame = frame;
  }

  private readonly targets = new Map<string, XLinkInstance>();

  private targetKey(e: Record<string, unknown>, key: string): void {
    const pos = vec(e.pos);
    if (this.far(pos, HIT_CULL_R)) return;
    const want = typeof e.user === "string" ? e.user : "SighterTarget";
    const name = this.data.slink.has(want) ? want : "SighterTarget";
    let i = this.targets.get(name);
    if (!i) {
      const n = this.slink(name);
      if (!n) return;
      i = n;
      this.targets.set(name, i);
    }
    i.searchAndEmit(key, { pos });
  }

  private trackBullets(): void {
    const list = this.w.shared.get("bullets");
    if (!Array.isArray(list)) return;
    for (const b of list as Record<string, unknown>[]) {
      const id = b.id;
      const pos = vec(b.pos ?? b.position);
      if (!pos) continue;
      const t = this.bullets.get(id);
      const vel = vec(b.vel ?? b.velocity);
      if (t) {
        t.vel = vel ?? [pos[0] - t.pos[0], pos[1] - t.pos[1], pos[2] - t.pos[2]];
        t.pos = pos;
      } else this.bullets.set(id, { pos, vel, team: num(b.team), owner: b.owner });
    }
  }

  private onFire(e: Record<string, unknown>): void {
    const pos = vec(e.pos);
    if (this.far(pos, FIRE_CULL_R)) return;
    const inst = this.weaponInst(weaponUser(e.weapon), e.owner);
    if (!inst) return;
    // 키 = VariableShotRepeatStartFrame > 0 ? (+0x98 > 0 ? FireOn : FireImpact) : Fire  (0x710289a8b4) — 스플래시 슈터는 0
    const vsr = num(e.variableShotRepeatStartFrame) ?? 0;
    const key = vsr > 0 ? ((num(e.repeat) ?? 0) > 0 ? "FireOn" : "FireImpact") : "Fire";
    inst.props.set("SubjectiveType", subjective(e.owner, this.ownerTeam(e.owner, e), this.local));
    inst.searchAndEmit(key, { pos, dir: vec(e.dir) });
  }

  private hitVelocity(e: Record<string, unknown>): V3 | null {
    return vec(e.vel ?? e.velocity) ?? this.bullets.get(e.id)?.vel ?? null;
  }

  private onBulletHit(e: Record<string, unknown>, s1: Map<string, HitAgg>): void {
    const pos = vec(e.pos);
    if (this.far(pos, HIT_CULL_R)) return;
    const surface = String(e.surface ?? "Floor");
    // Object 면은 Damage 이벤트가 같은 명중을 처리한다(셀 Damaged_*). 대미지가 없는 오브젝트는 지형과 같게 본다 [추정].
    if (surface === "Object" && e.damage !== false && e.target !== undefined) return;
    const t = this.bullets.get(e.id);
    const owner = e.owner ?? t?.owner;
    const team = num(e.team) ?? t?.team ?? this.ownerTeam(owner, e);
    const water = surface === "Water";
    const cell = this.hitTable.cell(String(e.row ?? "Shooter"), "Constant", water ? "Water" : "Default");
    if (!cell) return;
    const v = this.hitVelocity(e);
    this.emitHit(cell.S1, cell.S2, pos, owner, team, v ? Math.hypot(v[0], v[1], v[2]) : 0, e.paintable !== false, s1);
  }

  private onDamage(e: Record<string, unknown>, s1: Map<string, HitAgg>, hit: Record<string, unknown> | null): void {
    const pos = vec(e.pos);
    if (this.far(pos, HIT_CULL_R)) return;
    const reaction = damageReaction(e);
    if (!reaction) return;
    const row = String(e.row ?? (e.critical ? "Shooter_CriticalHit" : hit?.row ?? "Shooter"));
    const cell = this.hitTable.cell(row, reaction, String(e.targetType ?? "Default"));
    if (!cell) return;
    const owner = e.attacker ?? e.owner ?? hit?.owner;
    const v = vec(e.vel) ?? vec(hit?.vel) ?? this.bullets.get(e.id ?? hit?.id)?.vel ?? null;
    const team = num(e.team) ?? num(hit?.team) ?? this.ownerTeam(owner, e);
    this.emitHit(cell.S1, cell.S2, pos, owner, team, v ? Math.hypot(v[0], v[1], v[2]) : 0, true, s1);
  }

  /** 0x71027b877c 의 소리 부분: S1 = 집계, S2 = 즉시(AggregateNum·Velocity·IsPaintable·SubjectiveType 을 쓰고 방출) */
  private emitHit(
    S1: string | undefined,
    S2: string | undefined,
    pos: V3 | null,
    owner: unknown,
    team: number | null,
    speed: number,
    paintable: boolean,
    s1: Map<string, HitAgg>,
  ): void {
    if (!pos) return;
    if (S1) {
      const a = s1.get(S1);
      if (a) a.count++;
      else s1.set(S1, { key: S1, count: 1, pos, owner, team });
    }
    if (S2) {
      const he = this.hitEffect();
      if (!he) return;
      he.props.set("AggregateNum", 1);
      he.props.set("Velocity", speed);
      he.props.set("IsPaintable", paintable ? "True" : "False");
      // SubjectiveType = req+0x34 플레이어(0x71027b5430). +0x34 = 공격자로 본다 [추정]
      he.props.set("SubjectiveType", subjective(owner, team, this.local));
      he.searchAndEmit(S2, { pos });
    }
  }

  private setPlayerAction(slot: string, action: string): void {
    for (const i of this.playerInst.values()) i.changeAction(slot, action);
  }

  private onPlayer(type: string, e: Record<string, unknown>): void {
    const subj = subjective(e.owner, this.ownerTeam(e.owner, e), this.local);
    const users = [`Player_${subj}`, "PlayerFoot"];
    const pos = vec(e.pos) ?? this.local?.pos ?? null;
    const insts = users.map((u) => this.playerUser(u)).filter((x): x is XLinkInstance => !!x);
    for (const i of insts) {
      i.ctx = { pos };
      i.props.set("SubjectiveType", subj);
    }
    if (typeof e.slot === "string" && typeof e.action === "string") {
      for (const i of insts) i.changeAction(e.slot, e.action);
      return;
    }
    const squid = typeof e.squid === "boolean" ? e.squid : !!this.local?.squid;
    for (const m of PLAYER_ACTIONS[type] ?? []) {
      const a = squid ? m.squid : m.human;
      if (a) for (const i of insts) i.changeAction(m.slot, a);
    }
  }

  private updatePlayerProps(): void {
    if (!this.local || !this.playerInst.size) return;
    const props = playerProps(this.w, this.local);
    for (const i of this.playerInst.values()) {
      for (const [k, v] of Object.entries(props)) i.setProp(k, v);
      if (this.local.pos) i.ctx = { pos: this.local.pos };
    }
  }

  get frameNo(): number {
    return this.lastFrame;
  }
}

export function createAudioView(ctx: ClientContext): View {
  const data = fxData(ctx.assets, ctx.world);
  const sys = new AudioSystem(ctx.audio, ctx.world, data);
  registerEvents(ctx.world, "audio");
  if (DEV) (globalThis as Record<string, unknown>).__splatoon3_audio = sys;
  let failed = 0;
  return {
    update(w) {
      // 뷰 update 는 절대 throw 하지 않는다(앱 루프 보호). 오류는 처음 몇 번만 기록.
      try {
        step(w);
      } catch (e) {
        if (failed++ < 3) console.warn("[fx] audio update 오류(건너뜀)", e);
      }
    },
  };
  function step(w: World): void {
      sys.setListener(ctx.camera);
      const evs = drainEvents(w, "audio");
      // 프레임별로 묶어 처리(고정 스텝 순서 유지). 이벤트가 없는 프레임도 액션 calc 를 돈다.
      const first = Math.max(sys.frameNo + 1, w.frame - 8);
      let k = 0;
      for (let f = first; f < w.frame; f++) {
        const list: Record<string, unknown>[] = [];
        while (k < evs.length && evs[k].frame <= f) {
          if (evs[k].frame === f || evs[k].frame < first) list.push(evs[k].e as Record<string, unknown>);
          k++;
        }
        sys.frame(f, list);
      }
      sys.player.update();
  }
}
