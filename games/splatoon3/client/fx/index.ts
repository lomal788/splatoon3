// 담당: [fx] — docs/impl/fx.md 에 구현 상태·미확정을 기록한다.
// 코어 이벤트 → 탄 파티클(OneEmitter), 머즐 플래시(InkAction → ELink State[0]), 착탄·피격 이펙트(HitEffectConfig E1/E2),
// 플레이어 ELink(SplPlayer 액션 슬롯). 근거 docs/effect_sound/effect_sound.md §3, effect_resources.md §2.2~3.
import { CameraShakeMixer, type ShakeParam } from "../../core/camera/shake.ts";
import * as THREE from "three";
import type { ClientContext, View } from "../context.ts";
import { DEV } from "../env.ts";
import { Btn } from "../../core/input.ts";
import type { World } from "../../core/world.ts";
import { fxData, type FxData } from "../audio/data.ts";
import { e2IsElinkKey, e2Kind } from "../audio/hiteffect.ts";
import { HIT_CULL_R, PLAYER_ACTIONS } from "../audio/index.ts";
import { damageReaction, drainEvents, matchHit, num, readCamera, playerProps, readPlayer, registerEvents, squidAnim, subjective, vec, weaponUser, type PlayerRead, type V3 } from "../audio/read.ts";
import { XLinkInstance, type EmitContext, type XAsset, type XHandle, type XSink } from "../audio/xlink.ts";
import { InkActionState } from "./inkaction.ts";
import { muzzlePoseMatrix } from "./muzzle.ts";
import { EmitterInstance, ParticleBatch, identityMatrix, type EmitMatrix, type ParticleInputs } from "./particles.ts";
import { HIT_ESET, WATER_ESET, floorMatrix, identityFloor, normalMatrix, pickSplash, wallMatrix } from "./splash.ts";

// 팀 색(선형): graphics/team_color.md §8 OrangeBlue Original(set0 Alpha, set1 Bravo, set2 Neutral).
// 이펙트가 14색 중 어느 것을 쓰는지는 [미확정] — Original 로 둔다. 자료(teamColors)가 오면 그것을 쓴다.
const TEAM_FALLBACK: V3[] = [
  [0.7445, 0.1332, 0.0143],
  [0.0316, 0.0415, 0.5668],
  [0.6187, 0.6187, 0.0303],
];

interface EsetHandle extends XHandle {
  instances: EmitterInstance[];
  setMatrix(m: EmitMatrix): void;
  kill(): void;
}

interface BulletFx {
  h: EsetHandle | null;
  prev: V3;
  cur: V3;
  team: number;
  vel: V3 | null;
}

interface WeaponFx {
  elink: XLinkInstance | null;
  ink: InkActionState;
  lastPos: V3 | null;
  lastDir: V3 | null;
  playerAtFire: V3 | null;
  sawOnOff: boolean;
  owner: unknown;
  team: number;
}

export class FxSystem implements XSink {
  readonly data: FxData;
  readonly root = new THREE.Group();
  private readonly w: World;
  private readonly cam: THREE.Camera;
  private readonly batches = new Map<string, ParticleBatch>();
  private readonly live: EmitterInstance[] = [];
  private readonly weapons = new Map<string, WeaponFx>();
  private readonly bullets = new Map<unknown, BulletFx>();
  private hitElink: XLinkInstance | null = null;
  private playerElink: XLinkInstance | null = null;
  private local: PlayerRead | null = null;
  private frameNo = -1;
  private squidAnim: string | null = null;
  readonly missing = new Set<string>();
  readonly log: string[] = [];
  private readonly rnd = Math.random;
  private readonly shakes: CameraShakeMixer;
  private readonly particleInputs:ParticleInputs;

  constructor(w: World, cam: THREE.Camera, data: FxData,particleInputs:ParticleInputs={}) {
    this.particleInputs=particleInputs;
    this.w = w;
    this.cam = cam;
    this.data = data;
    const singletons = w.data.tables["singletons"] as { game__CameraModuleParam?: { Rumble?: Record<string, ShakeParam> } } | undefined;
    this.shakes = new CameraShakeMixer(singletons?.game__CameraModuleParam?.Rumble ?? {});
    this.root.name = "fx";
  }

  get lastFrame(): number {
    return this.frameNo;
  }

  private note(s: string): void {
    this.log.push(`${this.frameNo}: ${s}`);
    if (this.log.length > 200) this.log.splice(0, this.log.length - 200);
  }

  teamColor(team: number): V3 {
    const tc = this.data.teamColors ?? (this.w.shared.get("teamColors") as Record<string, number[]> | undefined) ?? null;
    const c = tc?.[String(team)];
    if (Array.isArray(c) && c.length >= 3) return [c[0], c[1], c[2]];
    return TEAM_FALLBACK[team >= 0 && team < 3 ? team : 0];
  }

  private emittersOf(eset: string): string[] {
    const out: string[] = [];
    for (const k of this.data.emitters.keys()) if (k.startsWith(eset + "/")) out.push(k);
    return out;
  }

  private batch(key: string): ParticleBatch | null {
    let b = this.batches.get(key);
    if (b) return b;
    const def = this.data.emitters.get(key);
    if (!def) return null;
    const texNames = this.data.emitterTex.get(key) ?? [];
    let map: THREE.Texture | null = null;
    for (const t of texNames) {
      const tx = this.data.textures.get(t);
      if (tx) {
        map = tx;
        break;
      }
    }
    const samplerData=this.data as FxData&{emitterSamplers?:Map<string,{slot:number|null;name:string}[]>};
    const samplers=new Map<number,THREE.Texture>();
    for(const sampler of samplerData.emitterSamplers?.get(key)??[]){
      const texture=this.data.textures.get(sampler.name);
      if(texture&&sampler.slot!==null)samplers.set(sampler.slot,texture);
    }
    // Native primitive UV.z is a VAT row; missing resources retain an explicit web fallback.
    const pf = this.data.emitterPrim.get(key);
    const prim = pf ? this.data.prims.get(pf) ?? null : null;
    const sphere = key.endsWith("/ball") || key.endsWith("/ball_Copy1");
    b = new ParticleBatch(key, def, sphere ? 512 : 256, samplers.get(0)??map, prim, sphere,{...this.particleInputs,samplers});
    if(sphere&&!(b.mesh.material as THREE.Material).userData.vat?.enabled)this.missing.add(`VAT input ${key}`);
    this.batches.set(key, b);
    this.root.add(b.mesh);
    return b;
  }

  /** 이미터셋 하나 재생(ELink 에셋 실행 / OneEmitter 슬롯 추가) */
  spawnEset(eset: string, m: EmitMatrix, color: V3, delay = 0, scale = 1): EsetHandle | null {
    // Do not permanently cache placeholder geometry/keys while real assets load.
    // ready also becomes true on load failure, preserving the explicit fallback.
    if (!this.data.ready) return null;
    const keys = this.emittersOf(eset);
    if (!keys.length) {
      if (!this.missing.has(eset)) {
        this.missing.add(eset);
        this.note(`이미터 자료 없음: ${eset}`);
      }
      return null;
    }
    const now = Math.max(this.frameNo, 0);
    const insts: EmitterInstance[] = [];
    for (const k of keys) {
      const b = this.batch(k);
      if (!b) continue;
      const inst = new EmitterInstance(b, m, color, now, delay, scale);
      insts.push(inst);
      this.live.push(inst);
      // 지연 0 이면 같은 프레임에 첫 방출
      inst.step(now, this.rnd);
    }
    const ended: (() => void)[] = [];
    return {
      instances: insts,
      alive: () => insts.some((i) => !i.finishedBy(this.frameNo)),
      fade: () => insts.forEach((i) => i.stop(this.frameNo)),
      setMatrix: (mm) => insts.forEach((i) => i.setMatrix(mm)),
      kill: () => insts.forEach((i) => i.kill()),
      onEnd: (cb) => ended.push(cb),
    };
  }

  // ---- XSink: ELink 에셋 → 이미터셋 ----------------------------------------
  play(a: XAsset, ctx: EmitContext): XHandle | null {
    const p = a.params;
    const delay = typeof p.Delay === "number" && Number.isFinite(p.Delay) ? Math.max(0, p.Delay) : 0;
    const scale = typeof p.Scale === "number" && Number.isFinite(p.Scale) ? p.Scale : 1;
    const getM = ctx.matrix as (() => EmitMatrix) | undefined;
    const m = getM ? getM() : identityMatrix((ctx.pos as V3 | undefined) ?? [0, 0, 0]);
    const shakeEmitterOrigin: V3 = [...m.o];
    const py = typeof p.PositionY === "number" ? p.PositionY : 0;
    if (py) m.o = [m.o[0] + m.y[0] * py, m.o[1] + m.y[1] * py, m.o[2] + m.y[2] * py];
    const color = (ctx.color as V3 | undefined) ?? this.teamColor(0);
    this.note(`ELink ${a.key} → ${a.name}${delay ? ` delay ${delay.toFixed(2)}` : ""}`);
    const h = this.spawnEset(a.name, m, color, delay, scale);
    // 뼈(Bone) 붙은 에셋은 이미터 행렬이 뼈를 따라간다. 파티클 follow 는 이미터 followType 대로.
    if (h && getM) for (const i of h.instances) i.followFn = getM;
    const shakeName = typeof p.CameraRumbleName === "string" ? p.CameraRumbleName : "";
    const shake = shakeName ? this.shakes.start(shakeName, () => getM ? getM().o : shakeEmitterOrigin,
      typeof p.DistanceAttenuate === "number" ? p.DistanceAttenuate : 1,
      typeof p.CameraRumbleFrame === "number" ? p.CameraRumbleFrame : -1) : null;
    if (!shake) return h;
    // A finite shake continues after its visual emitter ends. Keep the existing
    // ELink handle lifetime; a shake is not an extra particle/asset owner.
    if (!h) return null;
    return {
      alive: () => h.alive(),
      fade: () => { h.fade(); if (this.shakes.parameters[shakeName]?.IsLooped) shake.stop(); },
      onEnd: cb => h.onEnd?.(cb),
    };
  }

  // ---- 무기(머즐 플래시) ------------------------------------------------------
  private weapon(owner: unknown, weaponId: unknown, team: number): WeaponFx {
    const user = weaponUser(weaponId);
    const k = `${user}#${String(owner)}`;
    let wf = this.weapons.get(k);
    if (wf) return wf;
    const u = this.data.elink.get(user);
    let el: XLinkInstance | null = null;
    if (u) {
      el = new XLinkInstance(u, this);
      el.ctx = { matrix: () => this.muzzleMatrix(wf!), color: this.teamColor(team) };
    } else this.missing.add(`ELink ${user}`);
    const ink = new InkActionState(el ? [{ changeAction: (s, n, f) => el!.changeAction(s, n, f) }] : []);
    wf = { elink: el, ink, lastPos: null, lastDir: null, playerAtFire: null, sawOnOff: false, owner, team };
    this.weapons.set(k, wf);
    return wf;
  }

  /** Animated Muzzle full matrix, or the explicit legacy bullet-position adapter when unavailable. */
  private muzzleMatrix(wf: WeaponFx): EmitMatrix {
    const pose = muzzlePoseMatrix(this.w.shared.get("muzzle"), wf.owner);
    if (pose) return pose;
    const sm = this.w.shared.get("muzzle") as Record<string, unknown> | undefined;
    let pos = vec(sm?.pos);
    let dir = vec(sm?.dir);
    if (!pos) {
      pos = wf.lastPos ?? this.local?.pos ?? [0, 0, 0];
      if (wf.lastPos && wf.playerAtFire && this.local?.pos) {
        const d = this.local.pos;
        pos = [pos[0] + d[0] - wf.playerAtFire[0], pos[1] + d[1] - wf.playerAtFire[1], pos[2] + d[2] - wf.playerAtFire[2]];
      }
    }
    if (!dir) dir = wf.lastDir ?? [0, 0, 1];
    // Legacy adapter only; the actual bone branch above preserves all three axes.
    const z = normalize(dir);
    let x = cross([0, 1, 0], z);
    if (Math.hypot(...x) < 1e-6) x = [1, 0, 0];
    x = normalize(x);
    const y = cross(z, x);
    return { o: pos, x, y, z };
  }

  /** MuzzleShotDirXZDot (0x7102578c34 끝): 총구 수평 방향 · 카메라 수평 정면(본체 +0x538 = PlayerCamera+0x1a4) */
  private muzzleDot(wf: WeaponFx): number {
    const d = wf.lastDir;
    if (!d) return 1;
    const c = readCamera(this.w);
    const e = this.cam.matrixWorld.elements;
    const f: V3 = c?.rigForward ? [c.rigForward[0], 0, c.rigForward[2]] : [-e[8], 0, -e[10]];
    let mx = d[0], mz = d[2];
    const l = Math.hypot(mx, mz);
    if (l > 0) {
      mx /= l;
      mz /= l;
    }
    const fl = Math.hypot(f[0], f[2]) || 1;
    return (mx * f[0] + mz * f[2]) / fl;
  }

  // ---- 프레임 처리 -----------------------------------------------------------
  frame(f: number, events: Record<string, unknown>[]): void {
    this.frameNo = f;
    this.local = readPlayer(this.w);
    const e1 = new Map<string, { pos: V3; n: V3; team: number; count: number }>();
    // 무기: FireOn/FireOff 이벤트가 없으면 사격 버튼으로 대신(behavior+0x40 = 사격 입력으로 봄 [추정]).
    // 원본 순서: 슈터 갱신 앞부분에서 FireOn/FireOff 요청 → 발사 → FireImpact.
    for (const wf of this.weapons.values()) if (!wf.sawOnOff) wf.ink.set(this.w.pad.hold & Btn.Fire ? 1 : 2, f);
    for (const e of events) {
      switch (e.type) {
        case "Fire":
          this.onFire(e, f);
          break;
        case "FireImpact":
        case "FireOn":
        case "FireOff": {
          const wf = this.weapon(e.owner, e.weapon, num(e.team) ?? this.local?.team ?? 0);
          wf.sawOnOff = true; // 무기가 InkAction 변경을 직접 알린다 → 입력 대체 끔
          wf.ink.set(e.type === "FireImpact" ? 0 : e.type === "FireOn" ? 1 : 2, f);
          break;
        }
        case "BulletSpawn":
          this.onBulletSpawn(e);
          break;
        case "BulletDie": {
          const b = this.bullets.get(e.id);
          b?.h?.kill();
          this.bullets.delete(e.id);
          break;
        }
        case "BulletHit":
          this.onBulletHit(e, e1);
          break;
        case "Break": {
          // 표적 ELink "Break"(SighterTarget* 사용자). 사용자 자료가 없으면 기록만.
          const u = typeof e.user === "string" ? this.data.elink.get(e.user) : undefined;
          const pos = vec(e.pos);
          if (!u || !pos) {
            this.missing.add(`ELink ${String(e.user)}`);
            break;
          }
          new XLinkInstance(u, this).searchAndEmit("Break", { matrix: () => identityMatrix(pos), color: this.teamColor(num(e.team) ?? 1) });
          break;
        }
        case "Damage":
          this.onDamage(e, e1, matchHit(events, e));
          break;
        case "Jump":
        case "Land":
        case "ToSquid":
        case "ToHuman":
        case "Swim":
          this.onPlayer(e.type as string, e);
          break;
      }
    }
    // E1 집계(0x71027b4aa4 → ELink HitEffect 인스턴스). AggregateNum = 같은 프레임 명중 수(0..15)
    if (e1.size) {
      const he = this.hitEffect();
      for (const [key, a] of e1) {
        if (!he) break;
        he.props.set("AggregateNum", Math.min(a.count, 15));
        he.searchAndEmit(key, { matrix: () => normalMatrix(a.pos, a.n, null), color: this.teamColor(a.team) });
      }
    }
    const sa = squidAnim(this.local);
    if (sa && sa !== this.squidAnim) this.playerElink?.changeAction("SklAnim_Squid", sa);
    this.squidAnim = sa;
    for (const wf of this.weapons.values()) {
      wf.ink.applyPending();
      if (wf.elink) {
        wf.elink.props.set("MuzzleShotDirXZDot", this.muzzleDot(wf));
        wf.elink.calc();
      }
    }
    this.updateBullets();
    if (this.playerElink && this.local) {
      for (const [k, v] of Object.entries(playerProps(this.w, this.local))) this.playerElink.setProp(k, v);
      this.playerElink.props.set("SubjectiveType", "Focused");
      this.playerElink.calc();
    }
    // 이미터 방출·follow
    for (const inst of this.live) {
      if (inst.followFn) inst.setMatrix(inst.followFn());
      inst.step(f, this.rnd);
      if (inst.followAll) inst.batch.follow(inst);
      else if(Number(inst.batch.def.followType)===2)inst.batch.followPosition(inst);
    }
    for (let i = this.live.length - 1; i >= 0; i--) if (this.live[i].finishedBy(f)) this.live.splice(i, 1);
    const cameraState = this.w.shared.get("camera") as { pos?: ArrayLike<number> } | undefined;
    this.shakes.step(cameraState?.pos ?? [0, 0, 0]);
    const so = this.shakes.offset;
    this.cam.userData.shakeOffset = { x: so[0], y: so[1], z: so[2] };
  }

  private onFire(e: Record<string, unknown>, f: number): void {
    const team = num(e.team) ?? this.local?.team ?? 0;
    const wf = this.weapon(e.owner, e.weapon, team);
    wf.lastPos = vec(e.pos);
    wf.lastDir = vec(e.dir);
    wf.playerAtFire = this.local?.pos ?? null;
    // 탄을 쏜 갱신에 FireImpact(0x7102579af4) — 무기가 FireImpact 이벤트를 따로 보내도 같은 프레임 중복은 무시된다
    wf.ink.set(0, f);
  }

  private onBulletSpawn(e: Record<string, unknown>): void {
    const pos = vec(e.pos);
    if (!pos) return;
    const team = num(e.team) ?? this.local?.team ?? 0;
    // 팀 -1·3 은 무시(0x7101753bb4)
    if (team === -1 || team === 3) return;
    // 슈터 탄 = 슬롯 0x000 WpShtrBullet1Emit (BulletShooterBase vt106) [판독].
    // 분열 탄(Splash) = BulletSplashShooter vt106 17ffc60 → OneEmitter slot800 WpCmnBulletSplash1Emit [판독].
    // 벽 낙하(WallDrop) 의 파티클 슬롯은 미확인 → 그리지 않는다.
    const kind = String(e.kind ?? "Shooter");
    if (kind !== "Shooter" && kind !== "Splash") {
      this.note(`탄 종류 ${kind}: 파티클 슬롯 미확인 — 표시 안 함`);
      this.bullets.set(e.id, { h: null, prev: pos, cur: pos, team, vel: vec(e.vel) });
      return;
    }
    const h = this.spawnEset(kind==="Splash"?"WpCmnBulletSplash1Emit":"WpShtrBullet1Emit", identityMatrix(pos), this.teamColor(team));
    this.bullets.set(e.id, { h, prev: pos, cur: pos, team, vel: vec(e.vel) });
  }

  private updateBullets(): void {
    const list = this.w.shared.get("bullets");
    if (Array.isArray(list)) {
      for (const b of list as Record<string, unknown>[]) {
        const pos = vec(b.pos ?? b.position);
        if (!pos) continue;
        const t = this.bullets.get(b.id);
        if (!t) continue;
        t.prev = t.cur;
        t.cur = pos;
        t.vel = vec(b.vel ?? b.velocity) ?? [pos[0] - t.prev[0], pos[1] - t.prev[1], pos[2] - t.prev[2]];
      }
    }
    for (const b of this.bullets.values()) b.h?.setMatrix(identityMatrix(b.cur));
  }

  private hitEffect(): XLinkInstance | null {
    if (!this.hitElink) {
      const u = this.data.elink.get("HitEffect");
      if (u) this.hitElink = new XLinkInstance(u, this);
    }
    return this.hitElink;
  }

  private far(pos: V3): boolean {
    const e = this.cam.matrixWorld.elements;
    const c = readCamera(this.w)?.pos ?? [e[12], e[13], e[14]];
    const dx = pos[0] - c[0], dy = pos[1] - c[1], dz = pos[2] - c[2];
    return HIT_CULL_R * HIT_CULL_R < dx * dx + dy * dy + dz * dz;
  }

  /** 0x71027b877c 의 이펙트 부분(E1 집계, E2 코드 파티클 또는 ELink 키) */
  private dispatchHit(
    cell: { E1?: string; E2?: string } | null,
    pos: V3,
    n: V3,
    v: V3 | null,
    team: number,
    paintable: boolean,
    e1: Map<string, { pos: V3; n: V3; team: number; count: number }>,
  ): void {
    if (!cell) return;
    if (team === -1 || team === 3) return;
    if (cell.E1) {
      const a = e1.get(cell.E1);
      if (a) a.count++;
      else e1.set(cell.E1, { pos, n, team, count: 1 });
    }
    const color = this.teamColor(team);
    const kind = e2Kind(cell.E2);
    if (kind === 0) {
      const s = pickSplash(n, v, paintable);
      this.note(`착탄 ${s.eset}${s.wall ? "" : ` θ=${((s.theta * 180) / Math.PI).toFixed(1)}°`}`);
      const moving = !!v && Math.hypot(v[0], v[1], v[2]) > 0;
      this.spawnEset(s.eset, s.wall ? wallMatrix(pos, n) : moving ? floorMatrix(pos, n, v!) : identityFloor(pos), color);
    } else if (kind === 1) this.spawnEset(HIT_ESET, normalMatrix(pos, n, null), color);
    else if (kind === 2) this.spawnEset(WATER_ESET, normalMatrix(pos, n, null), color);
    if (e2IsElinkKey(cell.E2)) this.hitEffect()?.searchAndEmit(cell.E2!, { matrix: () => normalMatrix(pos, n, null), color });
  }

  private bulletInfo(e: Record<string, unknown>): { team: number; v: V3 | null } {
    const b = this.bullets.get(e.id);
    const team = num(e.team) ?? b?.team ?? this.local?.team ?? 0;
    const v = vec(e.vel ?? e.velocity) ?? b?.vel ?? null;
    return { team, v };
  }

  private onBulletHit(e: Record<string, unknown>, e1: Map<string, { pos: V3; n: V3; team: number; count: number }>): void {
    const pos = vec(e.pos);
    if (!pos || this.far(pos)) return;
    const surface = String(e.surface ?? "Floor");
    if (surface === "Object" && e.damage !== false && e.target !== undefined) return;
    const n = vec(e.normal) ?? [0, 1, 0];
    const { team, v } = this.bulletInfo(e);
    const cell = this.data.hit.cell(String(e.row ?? "Shooter"), "Constant", surface === "Water" ? "Water" : "Default");
    this.dispatchHit(cell, pos, n, v, team, e.paintable !== false, e1);
  }

  private onDamage(
    e: Record<string, unknown>,
    e1: Map<string, { pos: V3; n: V3; team: number; count: number }>,
    hit: Record<string, unknown> | null,
  ): void {
    const pos = vec(e.pos);
    if (!pos || this.far(pos)) return;
    const reaction = damageReaction(e);
    if (!reaction) return;
    const row = String(e.row ?? (e.critical ? "Shooter_CriticalHit" : hit?.row ?? "Shooter"));
    const cell = this.data.hit.cell(row, reaction, String(e.targetType ?? "Default"));
    const src = hit ?? e;
    const { team, v } = this.bulletInfo(src);
    // 피격 법선: 같은 명중의 BulletHit 법선, 없으면 탄 진행 반대 방향 [추정]
    let n = vec(e.normal) ?? vec(hit?.normal);
    if (!n && v) n = normalize([-v[0], -v[1], -v[2]]);
    this.dispatchHit(cell, pos, n ?? [0, 1, 0], v, num(e.team) ?? team, true, e1);
  }

  private onPlayer(type: string, e: Record<string, unknown>): void {
    if (subjective(e.owner, num(e.team), this.local) !== "Focused") return; // 지금은 로컬 플레이어만
    if (!this.playerElink) {
      const u = this.data.elink.get("SplPlayer");
      if (!u) {
        this.missing.add("ELink SplPlayer");
        return;
      }
      this.playerElink = new XLinkInstance(u, this);
    }
    const pos = vec(e.pos) ?? this.local?.pos ?? [0, 0, 0];
    this.playerElink.ctx = { matrix: () => identityMatrix(this.local?.pos ?? pos), color: this.teamColor(this.local?.team ?? 0) };
    if (typeof e.slot === "string" && typeof e.action === "string") {
      this.playerElink.changeAction(e.slot, e.action);
      return;
    }
    const squid = typeof e.squid === "boolean" ? e.squid : !!this.local?.squid;
    for (const m of PLAYER_ACTIONS[type] ?? []) {
      const a = squid ? m.squid : m.human;
      if (a) this.playerElink.changeAction(m.slot, a);
    }
    if (type === "ToHuman") this.playerElink.changeAction("SklAnim_Squid", "Sqd_ToHuman");
    if (type === "ToSquid") this.playerElink.changeAction("SklAnim_Squid", "Sqd_ToSquid");
  }

  /** 렌더 프레임: 파티클 시각(프레임 + 보간) */
  render(alpha: number): void {
    const now = this.frameNo + alpha;
    for (const b of this.batches.values()) b.uniforms.uNow.value = now;
    this.root.userData.needsSceneDepth=this.live.some(i=>!i.finishedBy(now)&&Number(i.batch.def.shaderIndex)===1897);
    // 탄은 이전·현재 위치 사이를 보간해 그린다
    for (const b of this.bullets.values()) {
      if (!b.h) continue;
      const p: V3 = [
        b.prev[0] + (b.cur[0] - b.prev[0]) * alpha,
        b.prev[1] + (b.cur[1] - b.prev[1]) * alpha,
        b.prev[2] + (b.cur[2] - b.prev[2]) * alpha,
      ];
      for (const inst of b.h.instances) {
        inst.setMatrix(identityMatrix(p));
        inst.batch.follow(inst);
      }
    }
  }

  stats(): Record<string, number> {
    return { emitters: this.live.length, bullets: this.bullets.size, batches: this.batches.size };
  }

  dispose(): void {
    for (const b of this.batches.values()) b.dispose();
    this.root.removeFromParent();
  }
}

function normalize(a: V3): V3 {
  const l = Math.hypot(a[0], a[1], a[2]);
  return l > 0 ? [a[0] / l, a[1] / l, a[2] / l] : [0, 0, 1];
}
function cross(a: V3, b: V3): V3 {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

export function createFxView(ctx: ClientContext): View {
  const data = fxData(ctx.assets, ctx.world);
  const sys = new FxSystem(ctx.world, ctx.camera, data,{lighting:ctx.fxLighting,depth:ctx.fxDepth});
  ctx.scene.add(sys.root);
  registerEvents(ctx.world, "fx");
  if (DEV) (globalThis as Record<string, unknown>).__splatoon3_fx = sys;
  let failed = 0;
  const step = (w: World, alpha: number): void => {
      // Build ELink owners and particle batches after the shared bundle settles.
      if (!data.ready) return;
      ctx.camera.updateMatrixWorld();
      const evs = drainEvents(w, "fx");
      const first = Math.max(sys.lastFrame + 1, w.frame - 8);
      let k = 0;
      for (let f = first; f < w.frame; f++) {
        const list: Record<string, unknown>[] = [];
        while (k < evs.length && evs[k].frame <= f) {
          if (evs[k].frame === f || evs[k].frame < first) list.push(evs[k].e as Record<string, unknown>);
          k++;
        }
        sys.frame(f, list);
      }
      sys.render(alpha);
  };
  return {
    update(w, alpha) {
      // 뷰 update 는 절대 throw 하지 않는다(앱 루프 보호). 오류는 처음 몇 번만 기록.
      try {
        step(w, alpha);
      } catch (e) {
        if (failed++ < 3) console.warn("[fx] fx update 오류(건너뜀)", e);
      }
    },
    dispose() {
      sys.dispose();
    },
  };
}
