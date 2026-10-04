// 플레이어 표시: 몸·파츠·_Hlf·오징어·무기 조립(player_assembly.md §6), 팀색(team_color.md), 애니(anim/*), 표시 모델 선택(§5.4).
import * as THREE from "three";
import type { GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Bundle } from "../assets.ts";
import { PlayerAnimator } from "./anim/animator.ts";
import type { LeafWeight } from "./anim/slot.ts";
import { applyHoian, type HoianUniforms, setTeam, setHoianMaterialTexSrt, setHoianMaterialParam } from "./hoian.ts";
import { type AttachOpt, attach, bindWorld, fresOf, textureResolver, playerModelFile, applyNativeTextureColorSpace, manualBindSrt } from "./model.ts";
import type { PlayerSnap } from "./shared.ts";
import { materialTeamParams, type MaterialTeamParams, type TeamSet } from "./teamcolor.ts";
import type { LightingState } from "./lighting.ts";
import { applyForward } from "./forward.ts";
import { applyCharacterMaterial, type CharacterMaterialBinding } from "./character_material.ts";
import { bindMaterialChannels, type MaterialChannelBinding, type MaterialChannelTarget, type MaterialParameterConsumer } from "./anim/material_binding.ts";
import { materialClipInfo, patchTexSrt, nativeHolderClipFrame, sampleMaterialClip, sampleNativeMaterialCurve, writeNativeMaterialParam, type NativeTexSrt, type MaterialAnimationBank, type MaterialAnimationGroup, type MaterialCurve, type MaterialPatch } from "./anim/material_channels.ts";
import { TankGauge } from "./anim/tank_gauge.ts";
import { hairArrangeLocal, hairArrangeParam } from "./anim/hair_cloth.ts";

/** 파츠 결합 표(§6.3). 키 = 모델 이름 접두 */
const PART_RULES: Record<string, AttachOpt> = {
  Har: { map: { Head_Root: "Head" }, attachPart: "Head_Root" },
  Eyb: { map: { Head_Root: "Head" }, attachPart: "Head_Root" },
  Clt: { attachPart: "Skl_Root" },
  Btm: { attachPart: "Skl_Root" },
  Shs: { attachPart: "Leg_2_L" },
  Tnk: { attachPart: "Spine_3" },
  Hed: { map: { Root: "Head" }, attachPart: "Root", mode: "head" },
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

/** Player info +0x844 skin / +0x848 eye index (holders 14522b0/145249c). 0/0 = save custom ctor 0x7102a66e28
 * initial SkinColor/EyeColor (player_assembly.md §5.2). The actual Lby PlayerInfo copy path is [미확정]. */
export interface Appearance {
  skinColor: number;
  eyeColor: number;
}
const DEFAULT_APPEARANCE: Appearance = { skinColor: 0, eyeColor: 0 };

/** Hat +0x120 variation. Selected Hed_FST000 has GearInfoHead VariationNum 0; chosen-variation writer is [미확정]. */
const HAT_VARIATION = 0;
type SrtRow = Parameters<typeof manualBindSrt>[0];
interface GearData {
  parts?: {
    clothes?: { row?: { HarnessType?: Harness["type"]; IsThinHarness?: boolean; IsHideHarness?: boolean } };
    hair?: { row?: { Id?: number; __RowId?: string } };
    head?: { headParamSet?: { ManualBindSRT?: Record<string, SrtRow> } };
  };
}

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
    if (l.type !== 3) continue; // type11은 별도 원시 재질 채널 바인더가 소비. type18은 미구현.
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

type BoneParamRow = Parameters<typeof hairArrangeParam>[0] & { BoneName: string };
/** HairArrangeParam selected by key = HairInfo Id × 10000 + hat variation (data/hair_arrange.json). */
interface HairArrangeData { maps: { key: number; param: { BoneParamArray?: BoneParamRow[] } }[] }

/** PlayerTank Tnk_Simple FSKA/FMAA (raw keys, data/tank_anim_native.json). */
interface TankAnimData {
  skeletal: { Gauge: { frames: number; bones: { name: string; S: number[]; R: number[]; T: number[]; curves: MaterialCurve[] }[] } };
  material: MaterialAnimationGroup;
}

/** Only the proven native Maya/zero-rotation SRT consumer is supplied here.
 * Color_Skin selection and live CompPaint/body ink stay unbound until their writers are confirmed.
 */
const materialParameter: MaterialParameterConsumer = (target,name,offsets) => {
  if (!/^tex_mtx[012]$/.test(name)) return false;
  const raw = target.fres.params?.[name]?.value as NativeTexSrt | undefined;
  if (!raw?.Scaling || !raw.Translation || typeof raw.Rotation !== "number") return false;
  try { return setHoianMaterialTexSrt(target.material,name,patchTexSrt(raw,offsets)); }
  catch { return false; }
};
/** Tank FMAA also animates Mat scalars/vectors held as live Hoian uniforms. */
const tankParameter: MaterialParameterConsumer = (target,name,offsets) =>
  materialParameter(target,name,offsets) || setHoianMaterialParam(target.material,name,offsets);

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
  private muzzleBone: THREE.Object3D | null = null;
  private bodyMeshes: THREE.Object3D[] = [];
  private hlfMeshes: THREE.Object3D[] = [];
  private gearMeshes: THREE.Object3D[] = [];
  private humanLib: ClipLib | null = null;
  private squidLib: ClipLib | null = null;
  private teamUniforms: HoianUniforms[] = [];
  animator: PlayerAnimator | null = null;
  readonly info: PlayerViewInfo = { placeholder: false, parts: [], missingClips: [], skipped: [] };
  readonly characterMaterials: CharacterMaterialBinding[] = [];
  readonly materialAnimations: MaterialChannelBinding[] = [];
  /** Applied Color_Skin frame (holder +0x38 value as f32). */
  skinFrame: number | null = null;
  private humanMaterials: MaterialChannelBinding | null = null;
  /** PlayerTank display: gauge state, Gauge skeletal Scale bone and tank material channels. */
  tank: { gauge: TankGauge; frame: number; scaleBone: THREE.Object3D | null; scale: { S: number[]; curves: MaterialCurve[] } | null;
    binding: MaterialChannelBinding | null; group: MaterialAnimationGroup; unapplied: string[] } | null = null;
  private squidMaterials: MaterialChannelBinding | null = null;
  get materialReady(): Promise<void> { return Promise.all([...this.characterMaterials,...this.materialAnimations].map(b => b.ready)).then(() => {}); }
  private lighting: LightingState | undefined;
  private teamSet: TeamSet | undefined;
  private prev: PlayerSnap | null = null;
  private cur: PlayerSnap | null = null;

  constructor(scene: THREE.Scene) {
    this.root.name = "splatoon3.player";
    scene.add(this.root);
  }

  load(charB: Bundle | undefined, weaponB: Bundle | undefined, team: MaterialTeamParams, weaponAbbr: string, harness: Harness = DEFAULT_HARNESS, lighting?: LightingState, teamSet?: TeamSet, appearance: Appearance = DEFAULT_APPEARANCE): void {
    this.lighting = lighting; this.teamSet = teamSet;
    let headSrt: number[] | undefined;
    let hairId: number | undefined;
    if (charB?.has("data/gear.json")) {
      const gear = charB.json<GearData>("data/gear.json").parts;
      const g = gear?.clothes?.row;
      if (g?.HarnessType) harness = { type: g.HarnessType, thin: !!g.IsThinHarness, hide: !!g.IsHideHarness };
      // 0x71026e4e80 key "V%d_%s": hat variation, hair row name without "Har_". Missing key = identity.
      const hair = gear?.hair?.row?.__RowId?.replace(/^Har_/, "");
      hairId = gear?.hair?.row?.Id;
      if (hair !== undefined) headSrt = manualBindSrt(gear?.head?.headParamSet?.ManualBindSRT?.[`V${HAT_VARIATION}_${hair}`]);
    }
    const glbs = charB ? charB.names().filter((n) => /\.glb$/i.test(n)) : [];
    const find = (re: RegExp): string | undefined => playerModelFile(glbs,re);
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
    const materialBank = charB.has("data/anim_material_native.json") ? charB.json<MaterialAnimationBank>("data/anim_material_native.json") : null;
    // Color_Skin writes typed Mat values consumed at compile/bind time, so it precedes the material hooks.
    this.applySkinColor(this.bodyMeshes, materialBank?.groups.Player00, appearance.skinColor);
    const bodyTex = textureResolver(body, charB, base(bodyName), true);
    this.teamMaterials(this.bodyMeshes, bodyTex, team);
    if (materialBank?.groups.Player00) {
      this.humanMaterials = bindMaterialChannels(this.materialTargets(this.bodyMeshes, bodyTex), materialBank.groups.Player00,materialParameter);
      this.materialAnimations.push(this.humanMaterials);
      this.applyEyeColor(this.humanMaterials, materialBank.groups.Player00, appearance.eyeColor);
    }

    // _Hlf: 같은 뼈 이름을 몸에서 복사(0x7101459154) → 몸 스켈레톤에 바로 묶는다
    if (hlfName) {
      const h = charB.gltf(hlfName);
      this.hlfMeshes = attach(body.scene, bodyBind, h.scene, { attachPart: "Skl_Root" });
      const hlfTex = textureResolver(h, charB, base(hlfName), true);
      this.teamMaterials(this.hlfMeshes, hlfTex, team);
      if (materialBank?.groups.Player00_Hlf) {
        const binding = bindMaterialChannels(this.materialTargets(this.hlfMeshes, hlfTex), materialBank.groups.Player00_Hlf, materialParameter);
        this.materialAnimations.push(binding);
        this.applyEyeColor(binding, materialBank.groups.Player00_Hlf, appearance.eyeColor);
      }
    }
    // The conversion manifest names the selected native resources. A bundle's
    // alphabetical file order must not decide hair/clothes/shoes.
    const selected = charB.has("data/character.json") ?
      charB.json<{ parts?: Record<string, { bfres?: string }> }>("data/character.json").parts : undefined;
    const partNames = selected ? Object.keys(selected).filter(k => PART_RULES[k.slice(0,3)]).map(k => "parts/"+k+".glb") : glbs;
    const used = new Set<string>();
    for (const n of partNames) {
      if (!charB.has(n)) { this.info.skipped.push("selected part absent: "+n); continue; }
      const b = base(n);
      const kind = b.slice(0, 3);
      const rule = kind === "Hed" ? { ...PART_RULES.Hed, headSrt } : PART_RULES[kind];
      if (!rule || used.has(kind)) continue;
      used.add(kind);
      const g = charB.gltf(n);
      const tex = textureResolver(g, charB, b, true);
      const ms = attach(body.scene, bodyBind, g.scene, rule);
      if (kind === "Shs") ms.push(...attach(body.scene, bodyBind, g.scene, SHOE_MIRROR));
      if (kind === "Tnk") this.selectHarness(ms, harness);
      this.teamMaterials(ms, tex, team);
      if (kind === "Tnk" && charB.has("data/tank_anim_native.json")) this.bindTank(body.scene, ms, tex, charB.json<TankAnimData>("data/tank_anim_native.json"));
      if (kind === "Har" && hairId !== undefined && charB.has("data/hair_arrange.json")) this.applyHairArrange(body.scene, charB.json<HairArrangeData>("data/hair_arrange.json"), hairId);
      this.gearMeshes.push(...ms);
      this.info.parts.push(b);
    }
    // 무기: Root → Weapon_R (full)
    const wName = weaponB?.names().find((n) => /(^|\/)model\.glb$/i.test(n)) ?? weaponB?.names().find((n) => /\.glb$/i.test(n));
    if (weaponB && wName) {
      const g = weaponB.gltf(wName);
      const ms = attach(body.scene, bodyBind, g.scene, WEAPON_RULE);
      for (const m of ms) {
        const sm = m as THREE.SkinnedMesh;
        if (sm.isSkinnedMesh) this.muzzleBone ??= sm.skeleton.bones.find(b => b.name === "part:Muzzle" || b.name === "Muzzle") ?? null;
      }
      if (!this.muzzleBone) this.info.skipped.push("weapon Muzzle bone absent: visual FX uses explicit fallback");
      this.teamMaterials(ms, textureResolver(g, weaponB, undefined, true), team);
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
      const squidTex = textureResolver(s, charB, base(squidName), true);
      this.teamMaterials(ms, squidTex, team);
      if (materialBank?.groups.Player_Squid) {
        this.squidMaterials = bindMaterialChannels(this.materialTargets(ms, squidTex), materialBank.groups.Player_Squid,materialParameter);
        this.materialAnimations.push(this.squidMaterials);
      }
      this.squidLib = { clips: squidClips, mixer: new THREE.AnimationMixer(s.scene), actions: new Map() };
    } else this.squid = this.placeholderSquid(team);
    this.root.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) o.castShadow = true;
    });
    const empty = (): null => null;
    this.animator = new PlayerAnimator(
      (name,type) => type === 11 ? materialClipInfo(materialBank?.groups.Player00,name) : clipInfo(this.humanLib!)(name),
      (name,type) => type === 11 ? materialClipInfo(materialBank?.groups.Player_Squid,name) : this.squidLib ? clipInfo(this.squidLib)(name) : empty(),
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

  /** PlayerTank.root.asb slots: Gauge(0) skeletal+material and InkShortage(1) are applied. InkLock(3)/SubMarker(4)/
   * InkShortageGauge(2) need body+0x69c and the sub-weapon cost, which have no producer here: [미확정], not substituted. */
  private bindTank(root: THREE.Object3D, ms: THREE.Object3D[], tex: ReturnType<typeof textureResolver>, data: TankAnimData): void {
    const bone = data.skeletal.Gauge.bones.find(b => b.name === "Scale");
    const scaleBone = root.getObjectByName("part:Scale") ?? null;
    if (!scaleBone) this.info.skipped.push("tank Gauge: part:Scale bone absent");
    const binding = bindMaterialChannels(this.materialTargets(ms, tex), data.material, tankParameter);
    this.materialAnimations.push(binding);
    this.tank = { gauge: new TankGauge(), frame: 0, scaleBone, scale: bone ? { S: bone.S, curves: bone.curves } : null, binding, group: data.material,
      unapplied: ["InkLock: body+0x69c producer absent", "SubMarker/InkShortageGauge: sub-weapon ink cost producer absent", "M_Glass multi_normal_weight: Hoian multi-normal consumer absent"] };
  }

  /** 0x7101454544 → 0x71026df354 → 0x71026df700: applied when the selected resource changes (load here).
   * Hair+0x338/+0x348 transform swap source is [미확정] (false). Cloth/skeletal weight AnimReduceRt is stored only. */
  private applyHairArrange(root: THREE.Object3D, data: HairArrangeData, hairId: number): void {
    const map = data.maps.find(m => m.key === hairId * 10000 + HAT_VARIATION);
    if (!map) return;
    for (const row of map.param.BoneParamArray ?? []) {
      const bone = root.getObjectByName("part:" + row.BoneName) ?? root.getObjectByName(row.BoneName);
      if (!bone) { this.info.skipped.push("HairArrange bone absent: " + row.BoneName); continue; }
      const e = new THREE.Matrix4().makeRotationFromQuaternion(bone.quaternion).elements;
      const bind = [e[0], e[4], e[8], bone.position.x, e[1], e[5], e[9], bone.position.y, e[2], e[6], e[10], bone.position.z];
      const p = hairArrangeParam(row);
      const out = hairArrangeLocal(bind, [bone.scale.x, bone.scale.y, bone.scale.z], p);
      const m = out.matrix;
      bone.quaternion.setFromRotationMatrix(new THREE.Matrix4().set(m[0], m[1], m[2], 0, m[4], m[5], m[6], 0, m[8], m[9], m[10], 0, 0, 0, 0, 1));
      bone.position.set(m[3], m[7], m[11]);
      bone.scale.set(out.scale[0], out.scale[1], out.scale[2]);
      bone.userData.animReduceRt = p.animReduceRt;
    }
  }

  /** One game frame of 0x71026fb6d0 → slot18 timer. Local-player argument w2 (shortage enable) taken as 1 [미확정]. */
  private stepTank(snap: PlayerSnap): void {
    const t = this.tank;
    if (!t) return;
    if (snap.lack) t.gauge.lack();
    const remaining = snap.ink ?? 1;
    const out = t.gauge.update({ subCost: 0, remaining, lock: remaining, shortageEnabled: true });
    t.gauge.advanceShortage(materialClipInfo(t.group, "InkShortage")?.frames ?? 45);
    t.gauge.tickTimers();
    t.frame = out.gauge;
  }

  private drawTank(): void {
    const t = this.tank;
    if (!t) return;
    if (t.scaleBone && t.scale) {
      const z = t.scale.curves.find(c => c.target === "0x0C");
      t.scaleBone.scale.set(t.scale.S[0], t.scale.S[1], z ? sampleNativeMaterialCurve(z, t.frame) : t.scale.S[2]);
    }
    if (!t.binding) return;
    // Slots write different lanes of the same Mat value (tex_mtx1 X/Y): merge before the typed consumer.
    const merged = new Map<string, MaterialPatch>();
    const add = (clip: string, frame: number): void => {
      const s = sampleMaterialClip(t.group, clip, frame);
      if (!s.supported) return;
      for (const p of s.patches) {
        const m = merged.get(p.material) ?? { material: p.material, params: {}, patterns: {} };
        for (const [k, v] of Object.entries(p.params)) m.params[k] = { ...(m.params[k] ?? {}), ...v };
        merged.set(p.material, m);
      }
    };
    add("Gauge", t.frame);
    if (t.gauge.shortagePlaying) add("InkShortage", t.gauge.shortageFrame);
    const clip = t.group.clips.find(c => c.name === "Gauge")!;
    t.binding.applySample({ supported: true, clip, patches: [...merged.values()] });
  }

  /** 0x71014522b0: Color_Skin frame = skin index (inside FrameCount) on M_Body/M_Face typed params. */
  private applySkinColor(ms: THREE.Object3D[], group: MaterialAnimationGroup | undefined, index: number): void {
    const frame = nativeHolderClipFrame(group, "Color_Skin", index, 0);
    if (!frame) { this.info.skipped.push("Color_Skin clip unavailable: static FRES skin values remain"); return; }
    const sample = sampleMaterialClip(group, "Color_Skin", frame.frame);
    if (!sample.supported) { this.info.skipped.push("Color_Skin: " + sample.reason); return; }
    const done = new Set<THREE.Material>();
    for (const o of ms) for (const mat of [(o as THREE.Mesh).material].flat()) {
      const f = mat && !done.has(mat) ? fresOf(mat) : null;
      if (!f) continue;
      done.add(mat);
      const patch = sample.patches.find(p => p.material === (f.name ?? mat.name));
      if (!patch) continue;
      for (const [name, offsets] of Object.entries(patch.params))
        if (!writeNativeMaterialParam(f.params, name, offsets)) this.info.skipped.push(`Color_Skin ${patch.material}.${name}: typed parameter unavailable`);
    }
    this.skinFrame = frame.frame;
  }

  /** 0x710145249c: Color_Eye pattern frame = eye index (0..FrameCount-1). */
  private applyEyeColor(binding: MaterialChannelBinding, group: MaterialAnimationGroup, index: number): void {
    const frame = nativeHolderClipFrame(group, "Color_Eye", index, 0);
    if (!frame) return;
    void binding.ready.then(() => binding.applySample(sampleMaterialClip(group, "Color_Eye", frame.frame)));
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
        const std = mat as THREE.MeshStandardMaterial;
        for (const t of [std.map, std.emissiveMap]) if (t) applyNativeTextureColorSpace(t, t.name);
        const u = applyHoian(mat as THREE.MeshStandardMaterial, f, this.teamSet ? materialTeamParams(this.teamSet, f.renderInfo) : team, tex, this.info.skipped, mesh.geometry);
        if (this.lighting) {
          applyForward(mat as THREE.MeshStandardMaterial, f, this.lighting, null);
          const b = applyCharacterMaterial(mat as THREE.MeshStandardMaterial, f, tex, this.info.skipped, mesh.geometry, this.lighting.uniforms.hLightAlpha);
          if (b) this.characterMaterials.push(b);
        }
        if (u) this.teamUniforms.push(u);
      }
    }
  }

  private materialTargets(ms: THREE.Object3D[], tex: ReturnType<typeof textureResolver>): MaterialChannelTarget[] {
    const targets: MaterialChannelTarget[] = [];
    for (const o of ms) {
      const mesh = o as THREE.Mesh;
      for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        const fres = material && fresOf(material);
        if (fres && (material as THREE.MeshStandardMaterial).isMeshStandardMaterial) targets.push({ material: material as THREE.MeshStandardMaterial, fres, tex });
      }
    }
    return targets;
  }

  setTeam(team: MaterialTeamParams): void {
    for (const u of this.teamUniforms) setTeam(u, team);
  }

  /** Animated visual bone matrix; bullet simulation keeps its independent native spawn path. */
  muzzleMatrix(): number[] | null {
    if (!this.muzzleBone) return null;
    this.muzzleBone.updateWorldMatrix(true, false);
    return this.muzzleBone.matrixWorld.elements.slice();
  }

  dispose(): void {
    for (const binding of this.materialAnimations) binding.dispose();
    this.materialAnimations.length = 0;
    for (const binding of this.characterMaterials) binding.dispose();
    this.characterMaterials.length = 0;
    this.root.removeFromParent();
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
    a.step({ state, speed, dead: snap.dead, formCounter: snap.formCounter, animRate: snap.animRate, displayHidden: snap.displayHidden });
    this.stepTank(snap);
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
    // Wrapper channels retain their own frame counts even while B7a0 hides the model.
    this.humanMaterials?.apply(a.humanLeaves(alpha));
    this.drawTank();
    this.squidMaterials?.apply(a.squidLeaves(alpha));
  }
}

const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

