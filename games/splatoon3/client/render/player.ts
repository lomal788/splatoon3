// 플레이어 표시: 몸·파츠·_Hlf·오징어·무기 조립(player_assembly.md §6), 팀색(team_color.md), 애니(anim/*), 표시 모델 선택(§5.4).
import * as THREE from "three";
import type { GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Bundle } from "../assets.ts";
import { PlayerAnimator } from "./anim/animator.ts";
import type { LeafWeight } from "./anim/slot.ts";
import { applyHoian, type HoianUniforms, setTeam } from "./hoian.ts";
import { type AttachOpt, attach, bindWorld, fresOf, textureResolver } from "./model.ts";
import type { PlayerSnap } from "./shared.ts";
import type { MaterialTeamParams } from "./teamcolor.ts";

/** 파츠 결합 표(§6.3). 키 = 모델 이름 접두 */
const PART_RULES: Record<string, AttachOpt> = {
  Har: { map: { Head_Root: "Head" }, attachPart: "Head_Root" },
  Eyb: { map: { Head_Root: "Head" }, attachPart: "Head_Root" },
  Clt: { attachPart: "Skl_Root" },
  Btm: { attachPart: "Skl_Root" },
  Shs: { attachPart: "Leg_2_L" },
  Tnk: { attachPart: "Spine_3" },
  Hed: { map: { Root: "Head" }, attachPart: "Root", mode: "translate" },
};
const SHOE_MIRROR: AttachOpt = {
  attachPart: "Leg_2_L", attachBody: "Leg_2_L", mirrorX: true,
  map: { Leg_2_L: "Leg_2_R", Ankle_Assist_L: "Ankle_Assist_R", Ankle_L: "Ankle_R", Toe_L: "Toe_R" },
};
const WEAPON_RULE: AttachOpt = { map: { Root: "Weapon_R" }, attachPart: "Root", mode: "full" };

/** 하네스 선택(§6.1, 0x71026f8f38). 옷 데이터: GearInfoClothes HarnessType/IsThinHarness/IsHideHarness */
export interface Harness {
  type: "S" | "M" | "L";
  thin: boolean;
  hide: boolean;
}
/** Clt_SHT000 의 GearInfoClothes 값 [데이터: HarnessType S, IsThinHarness false, IsHideHarness false] */
const DEFAULT_HARNESS: Harness = { type: "S", thin: false, hide: false };

function harnessBone(h: Harness): string {
  return h.hide ? "Harness_Hide" : `Harness_${h.type}${h.thin ? "F" : ""}`;
}

const base = (n: string): string => n.slice(n.lastIndexOf("/") + 1).replace(/\.glb$/i, "");

interface ClipLib {
  clips: Map<string, THREE.AnimationClip>;
  mixer: THREE.AnimationMixer;
  actions: Map<string, THREE.AnimationAction>;
}

function clipInfo(lib: ClipLib) {
  return (name: string): { frames: number; loop: boolean } | null => {
    const c = lib.clips.get(name);
    if (!c) return null;
    const u = c.userData as { frames?: number; loop?: boolean };
    // FSKA FrameCount (glTF extras.frames). 없으면 길이 × 60
    return { frames: typeof u.frames === "number" ? u.frames : Math.round(c.duration * 60), loop: !!u.loop };
  };
}

function applyLeaves(lib: ClipLib, leaves: LeafWeight[]): void {
  for (const a of lib.actions.values()) {
    a.enabled = false;
    a.setEffectiveWeight(0);
  }
  for (const l of leaves) {
    if (l.type !== 3) continue; // 재질(11)·가시성(18) 애니는 미구현
    const clip = lib.clips.get(l.clip);
    if (!clip) continue;
    let a = lib.actions.get(l.clip);
    if (!a) {
      a = lib.mixer.clipAction(clip);
      a.setLoop(THREE.LoopOnce, 1);
      a.clampWhenFinished = true;
      a.play();
      lib.actions.set(l.clip, a);
    }
    a.enabled = true;
    a.paused = false;
    a.setEffectiveWeight(a.getEffectiveWeight() + l.weight);
    a.time = Math.min(Math.max(l.frame / 60, 0), clip.duration);
  }
  lib.mixer.update(0);
}

export interface PlayerViewInfo {
  placeholder: boolean;
  parts: string[];
  missingClips: string[];
  skipped: string[];
}

export class PlayerView {
  readonly root = new THREE.Group();
  /** 사람 모델(몸 + 파츠 + _Hlf + 무기)이 같은 스켈레톤을 쓴다 */
  private human: THREE.Object3D | null = null;
  private squid: THREE.Object3D | null = null;
  private bodyMeshes: THREE.Object3D[] = [];
  private hlfMeshes: THREE.Object3D[] = [];
  private gearMeshes: THREE.Object3D[] = [];
  private humanLib: ClipLib | null = null;
  private squidLib: ClipLib | null = null;
  private teamUniforms: HoianUniforms[] = [];
  animator: PlayerAnimator | null = null;
  readonly info: PlayerViewInfo = { placeholder: false, parts: [], missingClips: [], skipped: [] };
  private prev: PlayerSnap | null = null;
  private cur: PlayerSnap | null = null;

  constructor(scene: THREE.Scene) {
    this.root.name = "splatoon3.player";
    scene.add(this.root);
  }

  load(charB: Bundle | undefined, weaponB: Bundle | undefined, team: MaterialTeamParams, weaponAbbr: string, harness: Harness = DEFAULT_HARNESS): void {
    const glbs = charB ? charB.names().filter((n) => /\.glb$/i.test(n)) : [];
    const find = (re: RegExp): string | undefined => glbs.find((n) => re.test(base(n)));
    const bodyName = find(/^(body|Player0\d)$/i);
    const hlfName = find(/(^|_)hlf$/i);
    const squidName = find(/squid|octopus/i);
    if (!charB || !bodyName) {
      this.buildPlaceholder(team);
      this.root.traverse((o) => {
        if ((o as THREE.Mesh).isMesh) o.castShadow = true;
      });
      this.animator = new PlayerAnimator(() => null, () => null, weaponAbbr);
      return;
    }
    const body = charB.gltf(bodyName);
    this.human = body.scene;
    this.root.add(body.scene);
    const bodyBind = bindWorld(body.scene);
    body.scene.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) {
        o.frustumCulled = false;
        this.bodyMeshes.push(o);
      }
    });
    this.hideMouthVariants(this.bodyMeshes);
    this.teamMaterials(this.bodyMeshes, textureResolver(body, charB), team);

    // _Hlf: 같은 뼈 이름을 몸에서 복사(0x7101459154) → 몸 스켈레톤에 바로 묶는다
    if (hlfName) {
      const h = charB.gltf(hlfName);
      this.hlfMeshes = attach(body.scene, bodyBind, h.scene, { attachPart: "Skl_Root" });
      this.teamMaterials(this.hlfMeshes, textureResolver(h, charB), team);
    }
    // 파츠: 이름 접두 → 결합 규칙. 같은 종류가 여럿이면 첫 번째만
    const used = new Set<string>();
    for (const n of glbs) {
      const b = base(n);
      const kind = b.slice(0, 3);
      const rule = PART_RULES[kind];
      if (!rule || used.has(kind)) continue;
      used.add(kind);
      const g = charB.gltf(n);
      const tex = textureResolver(g, charB);
      const ms = attach(body.scene, bodyBind, g.scene, rule);
      if (kind === "Shs") ms.push(...attach(body.scene, bodyBind, g.scene, SHOE_MIRROR));
      if (kind === "Tnk") this.selectHarness(ms, harness);
      this.teamMaterials(ms, tex, team);
      this.gearMeshes.push(...ms);
      this.info.parts.push(b);
    }
    // 무기: Root → Weapon_R (full)
    const wName = weaponB?.names().find((n) => /(^|\/)model\.glb$/i.test(n)) ?? weaponB?.names().find((n) => /\.glb$/i.test(n));
    if (weaponB && wName) {
      const g = weaponB.gltf(wName);
      const ms = attach(body.scene, bodyBind, g.scene, WEAPON_RULE);
      this.teamMaterials(ms, textureResolver(g, weaponB), team);
      this.gearMeshes.push(...ms);
      this.info.parts.push(base(wName));
    } else this.gearMeshes.push(this.placeholderWeapon(body.scene, team));

    // 클립: 오징어 클립(Sqd_*)은 오징어 모델, 나머지는 사람 모델
    const humanClips = new Map<string, THREE.AnimationClip>();
    const squidClips = new Map<string, THREE.AnimationClip>();
    const addClips = (g: GLTF): void => {
      for (const c of g.animations) (/^Sqd_/.test(c.name) ? squidClips : humanClips).set(c.name, c);
    };
    addClips(body);
    for (const n of glbs) if (n !== bodyName && !PART_RULES[base(n).slice(0, 3)]) addClips(charB.gltf(n));
    this.humanLib = { clips: humanClips, mixer: new THREE.AnimationMixer(body.scene), actions: new Map() };

    if (squidName) {
      const s = charB.gltf(squidName);
      this.squid = s.scene;
      this.root.add(s.scene);
      const ms: THREE.Object3D[] = [];
      s.scene.traverse((o) => {
        if ((o as THREE.Mesh).isMesh) {
          o.frustumCulled = false;
          ms.push(o);
        }
      });
      this.teamMaterials(ms, textureResolver(s, charB), team);
      this.squidLib = { clips: squidClips, mixer: new THREE.AnimationMixer(s.scene), actions: new Map() };
    } else this.squid = this.placeholderSquid(team);
    this.root.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) o.castShadow = true;
    });
    const empty = (): null => null;
    this.animator = new PlayerAnimator(
      clipInfo(this.humanLib),
      this.squidLib ? clipInfo(this.squidLib) : empty,
      weaponAbbr,
    );
  }

  /** 입 모양 5벌 중 Mouth00 만(가시성 애니 미구현, §5.1) */
  private hideMouthVariants(ms: THREE.Object3D[]): void {
    for (const m of ms) {
      const vb = m.userData.visBone as string | undefined;
      if (/^Mouth0[1-4]_Model/.test(m.name) || (vb && /^Mouth0[1-4]_Model$/.test(vb))) m.userData.variantHidden = true;
    }
  }

  private selectHarness(ms: THREE.Object3D[], h: Harness): void {
    const want = harnessBone(h);
    for (const m of ms) {
      const vb = m.userData.visBone as string | undefined;
      if (vb && vb.startsWith("Harness_") && vb !== want) m.userData.variantHidden = true;
    }
  }

  private teamMaterials(ms: THREE.Object3D[], tex: ReturnType<typeof textureResolver>, team: MaterialTeamParams): void {
    const done = new Set<THREE.Material>();
    for (const o of ms) {
      const mesh = o as THREE.Mesh;
      for (const mat of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        if (!mat || done.has(mat) || mat.userData.__hoianDone) continue;
        done.add(mat);
        mat.userData.__hoianDone = true;
        const f = fresOf(mat);
        if (!f || !(mat as THREE.MeshStandardMaterial).isMeshStandardMaterial) continue;
        const u = applyHoian(mat as THREE.MeshStandardMaterial, f, team, tex, this.info.skipped);
        if (u) this.teamUniforms.push(u);
      }
    }
  }

  setTeam(team: MaterialTeamParams): void {
    for (const u of this.teamUniforms) setTeam(u, team);
  }

  // ---- placeholder (에셋이 없을 때) ----------------------------------------
  private buildPlaceholder(team: MaterialTeamParams): void {
    this.info.placeholder = true;
    const tc = new THREE.Color().setRGB(team.my_team_color[0], team.my_team_color[1], team.my_team_color[2], THREE.LinearSRGBColorSpace);
    const human = new THREE.Group();
    const bodyMesh = new THREE.Mesh(new THREE.CapsuleGeometry(0.3, 1.0, 6, 12), new THREE.MeshStandardMaterial({ color: 0xd9b38c }));
    bodyMesh.position.y = 0.8;
    const hair = new THREE.Mesh(new THREE.SphereGeometry(0.28, 16, 12), new THREE.MeshStandardMaterial({ color: tc }));
    hair.position.set(0, 1.45, -0.05);
    human.add(bodyMesh, hair);
    this.bodyMeshes = [bodyMesh, hair];
    this.human = human;
    this.root.add(human);
    this.gearMeshes.push(this.placeholderWeapon(human, team));
    this.squid = this.placeholderSquid(team);
  }

  private placeholderWeapon(parent: THREE.Object3D, team: MaterialTeamParams): THREE.Object3D {
    const tc = new THREE.Color().setRGB(team.my_team_color[0], team.my_team_color[1], team.my_team_color[2], THREE.LinearSRGBColorSpace);
    const w = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.12, 0.5), new THREE.MeshStandardMaterial({ color: tc }));
    const hand = parent.getObjectByName("Weapon_R");
    if (hand) hand.add(w);
    else {
      w.position.set(-0.3, 1.0, 0.3);
      parent.add(w);
    }
    return w;
  }

  private placeholderSquid(team: MaterialTeamParams): THREE.Object3D {
    const tc = new THREE.Color().setRGB(team.my_team_color[0], team.my_team_color[1], team.my_team_color[2], THREE.LinearSRGBColorSpace);
    const m = new THREE.Mesh(new THREE.SphereGeometry(0.35, 16, 12), new THREE.MeshStandardMaterial({ color: tc }));
    m.scale.set(1, 0.5, 1.4);
    m.position.y = 0.2;
    const g = new THREE.Group();
    g.add(m);
    this.root.add(g);
    return g;
  }

  // ---- 갱신 -------------------------------------------------------------
  /** 게임 프레임 1개 진행(상태 → 애니 진행·표시 결정) */
  step(snap: PlayerSnap): void {
    this.prev = this.cur ?? snap;
    this.cur = snap;
    const a = this.animator;
    if (!a) return;
    const speed = snap.animSpeed ?? snap.speed ?? this.speedFromDelta();
    const state = snap.state ?? this.fallbackState(snap, speed);
    a.step({ state, speed, dead: snap.dead, formCounter: snap.formCounter, animRate: snap.animRate });
    const miss = new Set([...a.human.missing, ...a.squid.missing]);
    this.info.missingClips = [...miss];
  }

  /**
   * physics 가 상태 번호를 아직 주지 않을 때의 임시 대응(표시 확인용, 원본 전이 규칙 아님):
   * 사람 0x56 WaitHold / 0x5f WalkHold, 오징어 0x85 Wait / 0x87 Walk, 전환은 0x82→0x84, 0x91→0x92 를
   * 원본 판정식(end < cur + 3, player_state.md §6.2)으로 거친다.
   */
  private fallbackState(s: PlayerSnap, speed: number): number {
    const a = this.animator!;
    const cur = a.state;
    const moving = speed > 0.003;
    const pr = a.active?.progress();
    const ended = (k: number): boolean => !pr || pr.end < pr.cur + k;
    const inSquid = cur === 0x84 || cur === 0x85 || cur === 0x87;
    if (s.squid) {
      if (cur === 0x82) return ended(3) ? 0x84 : 0x82;
      if (cur === 0x84 && !ended(1)) return 0x84;
      if (inSquid) return moving ? 0x87 : 0x85;
      return 0x82;
    }
    if (inSquid) return 0x91;
    if (cur === 0x91) return ended(3) ? 0x92 : 0x91;
    if (cur === 0x92 && !ended(1) && !moving) return 0x92;
    return moving ? 0x5f : 0x56;
  }

  private speedFromDelta(): number {
    if (!this.prev || !this.cur) return 0;
    return Math.hypot(this.cur.pos[0] - this.prev.pos[0], this.cur.pos[2] - this.prev.pos[2]);
  }

  /** 렌더 프레임: 위치 보간, 포즈 적용, 표시 */
  draw(alpha: number): void {
    const c = this.cur, p = this.prev ?? c;
    if (c && p) {
      this.root.position.set(lerp(p.pos[0], c.pos[0], alpha), lerp(p.pos[1], c.pos[1], alpha), lerp(p.pos[2], c.pos[2], alpha));
      let d = c.yaw - p.yaw;
      d = Math.atan2(Math.sin(d), Math.cos(d));
      this.root.rotation.y = p.yaw + d * alpha;
    }
    const a = this.animator;
    if (!a) return;
    const { body, hlf, squid } = a.disp;
    // _Hlf 모델이 번들에 없으면 그 구간은 몸으로 대신 그린다(웹 대체)
    const hlfAsBody = hlf && !this.hlfMeshes.length;
    for (const m of this.bodyMeshes) m.visible = (body || hlfAsBody) && !m.userData.variantHidden;
    for (const m of this.hlfMeshes) m.visible = hlf;
    // 파츠·무기는 사람 계산 플래그(+0x64 = body || hlf)를 따른다 [추정]
    if (this.human) {
      for (const m of this.gearMeshes) m.visible = (body || hlf) && !m.userData.variantHidden;
      this.human.visible = body || hlf;
      const s = a.springScale();
      this.human.scale.set(s[0], s[1], s[2]);
    }
    if (this.squid) this.squid.visible = squid;
    if (this.humanLib && (body || hlf)) applyLeaves(this.humanLib, a.humanLeaves(alpha));
    if (this.squidLib && squid) applyLeaves(this.squidLib, a.squidLeaves(alpha));
  }
}

const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

