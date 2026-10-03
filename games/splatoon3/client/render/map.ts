// 맵 표시: visual.glb 배치, 정적 메시 병합(재질·공간 칸 단위), 조명(env.json), 에셋이 없으면 격자 바닥.
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import type { GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Bundle } from "../assets.ts";
import { applyHoian } from "./hoian.ts";
import { fresOf, textureResolver } from "./model.ts";
import type { EnvLight, MaterialTeamParams, TeamSet } from "./teamcolor.ts";
import { materialTeamParams } from "./teamcolor.ts";
import { BakeBindings } from "./bake.ts";
import { applyForward } from "./forward.ts";
import { LightingState } from "./lighting.ts";
import { SkyView } from "./sky.ts";
import { NativeShadowState } from "./shadows.ts";

/** 맵 루트 이름(다른 영역이 scene.getObjectByName 으로 찾는다 — paint 표시 등) */
export const MAP_ROOT_NAME = "splatoon3.map";

/**
 * 웹에서 쓰는 조명 값. 원본 기본 env(`Env/Default.Nin_NX_NVN.genvb.zs` 낮 DirectionalLight "Main"):
 * DiffuseColor (1,1,1), Intensity 4.0, Direction (−0.3,−0.7,−0.6) [데이터 — team_color.md §5.3].
 */
export interface EnvInfo {
  light: EnvLight;
  /** 빛이 나아가는 방향(원본 Direction) */
  direction: [number, number, number];
  /** 하늘·땅 색(선형) — 헤미스피어 근사 */
  sky: [number, number, number];
  ground: [number, number, number];
  source: string;
}

const DEFAULT_ENV: EnvInfo = {
  light: { color: [1, 1, 1], intensity: 4.0, skyUp: null },
  direction: [-0.3, -0.7, -0.6],
  // 하늘/땅 색은 원본 값이 없다(Env 블록 미해독) — 표시용 근사 [근사]
  sky: [0.55, 0.6, 0.7],
  ground: [0.25, 0.23, 0.2],
  source: "default (Env/Default 낮 DirectionalLight)",
};

type Json = Record<string, unknown>;
const arr3 = (v: unknown): [number, number, number] | null => {
  if (Array.isArray(v) && v.length >= 3 && v.every((x) => typeof x === "number")) return [v[0], v[1], v[2]];
  if (v && typeof v === "object") {
    const o = v as Json;
    const r = o.R ?? o.r ?? o.x, g = o.G ?? o.g ?? o.y, b = o.B ?? o.b ?? o.z;
    if ([r, g, b].every((x) => typeof x === "number")) return [r as number, g as number, b as number];
  }
  return null;
};
const pick = (o: Json | undefined, ...keys: string[]): unknown => {
  if (!o) return undefined;
  for (const k of keys) if (o[k] !== undefined) return o[k];
  return undefined;
};

/**
 * env.json(에셋 담당 형식, docs/impl/assets.md) → EnvInfo.
 *   주 방향광 색·세기: RenderingDay MainLight → env writer [graphics/renderparam_runtime §6].
 *     없으면 teamColorLight.defaultDay(기본 env DirectionalLight DiffuseColor/Intensity).
 *   방향: 로비 MainLight Latitude/Longitude → lonLatToDir (없으면 defaultDay.Direction [데이터: 기본 env]).
 *   sky/ground fields are placeholder colors only. Actual lobby uses the native Sky_Daytime00 and linear shader fog.
 */
export function parseEnv(env: unknown): EnvInfo {
  if (!env || typeof env !== "object") return DEFAULT_ENV;
  const e = env as Json;
  const out: EnvInfo = { ...DEFAULT_ENV, light: { ...DEFAULT_ENV.light }, source: "env.json" };
  const tcl = e.teamColorLight as Json | undefined;
  const day = tcl?.defaultDay as Json | undefined;
  const rendering = e.rendering as Json | undefined;
  const lobby = (tcl?.lobbyMainLight ?? (rendering?.Lighting as Json | undefined)?.MainLight) as Json | undefined;
  const dc = arr3(pick(day, "DiffuseColor"));
  const di = pick(day, "Intensity");
  const dd = arr3(pick(day, "Direction"));
  if (dc) out.light.color = dc;
  if (typeof di === "number") out.light.intensity = di;
  if (dd) out.direction = dd;
  const lc = arr3(pick(lobby, "Color"));
  const li = pick(lobby, "Intens");
  if (lc) out.light.color = lc;
  if (typeof li === "number") out.light.intensity = li;
  const lat = pick(lobby, "Latitude"), lon = pick(lobby, "Longitude");
  const ll = typeof lat === "number" && typeof lon === "number";
  if (ll) out.direction = lonLatToDir(lon, lat);
  out.source = `env.json (${lc ? "lobby MainLight" : dc ? "defaultDay" : "default"} 색·세기, ${ll ? "lobby MainLight 위도·경도" : dd ? "defaultDay" : "default"} 방향)`;
  const fog = ((rendering?.Fog as Json | undefined)?.DepthFog as Json | undefined)?.Color;
  const fc = arr3(fog);
  if (fc) out.sky = srgbToLinear(fc);
  return out;
}

/**
 * env 접근자 MainLightDirLongitudeLatitude set 0x710104dea8 [판독]: 입력 vec2 (u, v) 도 → DirectionalLight+0x1c0 (Direction)
 *   = (−sin(u)·cos(v), −sin(v), −cos(u)·cos(v)), 도→라디안 0.017453292, sinf/cosf 임포트.
 * Longitude/Latitude writer and typed RenderingDay consumer: graphics/renderparam_runtime §6.
 * SDK sinf/cosf are approximated by f32-rounded JS libm; whole bit identity is not claimed.
 */
export function lonLatToDir(lonDeg: number, latDeg: number): [number, number, number] {
  const k = Math.fround(0.017453292);
  const u = Math.fround(lonDeg * k), v = Math.fround(latDeg * k);
  const cv = -Math.cos(v);
  return [Math.fround(Math.fround(Math.sin(u)) * Math.fround(cv)), Math.fround(-Math.sin(v)), Math.fround(Math.fround(Math.cos(u)) * Math.fround(cv))];
}

const srgbToLinear = (c: [number, number, number]): [number, number, number] => {
  const t = new THREE.Color().setRGB(c[0], c[1], c[2], THREE.SRGBColorSpace);
  return [t.r, t.g, t.b];
};

const HEMI_INTENSITY = 0.0; // Native startup SH replaces the arbitrary hemisphere colors.

export class MapView {
  readonly root = new THREE.Group();
  readonly sun: THREE.DirectionalLight;
  readonly hemi: THREE.HemisphereLight;
  env: EnvInfo = DEFAULT_ENV;
  readonly lighting = new LightingState();
  readonly shadows = new NativeShadowState();
  bakes: BakeBindings | null = null;
  sky: SkyView | null = null;
  /** Paint owns its atlas/hooks; restore its replacements before disposing the stage. */
  disposePaint?: () => void;
  environmentReady = false;
  readonly skipped: string[] = [];
  stats = { meshesIn: 0, meshesOut: 0, triangles: 0, placeholder: false };

  constructor(scene: THREE.Scene) {
    this.root.name = MAP_ROOT_NAME;
    scene.add(this.root);
    this.sun = new THREE.DirectionalLight(0xffffff, 1);
    // Two depth targets are supplied by shadows.ts; the sun remains the direct light.
    this.sun.castShadow = false;
    this.lighting.shadows = this.shadows;
    this.hemi = new THREE.HemisphereLight(0xffffff, 0x444444, HEMI_INTENSITY);
    scene.add(this.sun, this.sun.target, this.hemi);
    this.applyEnv(scene);
  }

  /** 그림자 영역을 대상(플레이어) 위치로 옮긴다 */
  follow(p: THREE.Vector3): void {
    const d = new THREE.Vector3(...this.env.direction).normalize();
    this.sun.target.position.copy(p);
    this.sun.position.copy(p).addScaledVector(d, -100);
  }

  applyEnv(scene: THREE.Scene): void {
    const e = this.env;
    this.follow(new THREE.Vector3());
    this.sun.color.setRGB(e.light.color[0], e.light.color[1], e.light.color[2], THREE.LinearSRGBColorSpace);
    this.sun.intensity = e.light.intensity;
    this.hemi.color.setRGB(e.sky[0], e.sky[1], e.sky[2], THREE.LinearSRGBColorSpace);
    this.hemi.groundColor.setRGB(e.ground[0], e.ground[1], e.ground[2], THREE.LinearSRGBColorSpace);
    scene.background = new THREE.Color().setRGB(e.sky[0], e.sky[1], e.sky[2], THREE.LinearSRGBColorSpace);
  }

  load(scene: THREE.Scene, bundle: Bundle | undefined, team: MaterialTeamParams, set?: TeamSet): void {
    if (bundle?.has("env.json")) this.env = parseEnv(bundle.json("env.json"));
    this.applyEnv(scene);
    const raw = bundle?.has("env.json") ? bundle.json("env.json") : null;
    this.lighting.configure(raw, this.env.light.color, this.env.light.intensity, this.env.direction);
    this.shadows.configure(raw);
    if (bundle) this.bakes = new BakeBindings(bundle);
    const glbName = bundle?.names().find((n) => /(^|\/)visual\.glb$/i.test(n)) ?? bundle?.names().find((n) => /\.glb$/i.test(n));
    if (bundle && glbName) {
      const gltf = bundle.gltf(glbName);
      this.addVisual(gltf, bundle, team, set);
    } else this.addPlaceholder();
    if (bundle?.has("sky/Sky_Daytime00.glb")) {
      this.sky = new SkyView(bundle.gltf("sky/Sky_Daytime00.glb"), raw);
      scene.add(this.sky.root);
      scene.background = null;
    }
  }

  private addVisual(gltf: GLTF, bundle: Bundle, team: MaterialTeamParams, set?: TeamSet): void {
    const tex = textureResolver(gltf, bundle);
    gltf.scene.updateMatrixWorld(true);
    // Bone-bound rigs must be read before static geometry is merged.
    this.lighting.bindRigs(gltf.scene);
    const clones = new Map<string, THREE.Material>();
    gltf.scene.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      const materials = Array.isArray(m.material) ? m.material : [m.material];
      const updated = materials.map(original => {
        const f = fresOf(original);
        if (!f || !(original as THREE.MeshStandardMaterial).isMeshStandardMaterial) return original;
        const bake = this.bakes?.resolve(m, original, f) ?? null;
        const key = original.uuid + ":" + (bake?.ao?.st.toArray().join(",") ?? "") + ":" + (bake?.light?.st.toArray().join(",") ?? "");
        let mat = clones.get(key);
        if (!mat) {
          mat = original.clone();
          clones.set(key, mat);
          applyHoian(mat as THREE.MeshStandardMaterial, f, set ? materialTeamParams(set, f.renderInfo) : team, tex, this.skipped, m.geometry);
          applyForward(mat as THREE.MeshStandardMaterial, f, this.lighting, bake);
        }
        return mat;
      });
      m.material = Array.isArray(m.material) ? updated : updated[0];
    });
    this.root.add(mergeStatic(gltf.scene, this.stats));
  }

  async captureEnvironment(renderer: THREE.WebGLRenderer, scene: THREE.Scene): Promise<void> {
    this.environmentReady=false;
    try {await this.lighting.capture(renderer, scene, this.root, this.sky?.root ?? null, capture => this.sky?.setCapture(capture));}
    finally {this.environmentReady=true;}
  }

  dispose(scene: THREE.Scene): void {
    this.disposePaint?.();this.disposePaint=undefined;
    scene.remove(this.root);
    if (this.sky) scene.remove(this.sky.root);
    this.sky?.dispose(); this.lighting.dispose(); this.shadows.dispose(); this.bakes?.dispose();
    const materials = new Set<THREE.Material>();
    this.root.traverse(o => {
      if (!(o as THREE.Mesh).isMesh) return;
      const m = o as THREE.Mesh;
      m.geometry.dispose();
      for (const mat of Array.isArray(m.material) ? m.material : [m.material]) materials.add(mat);
    });
    for (const m of materials) m.dispose();
  }

  private addPlaceholder(): void {
    this.stats.placeholder = true;
    const g = new THREE.PlaneGeometry(200, 200).rotateX(-Math.PI / 2);
    const floor = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0x8a8f96, roughness: 0.9 }));
    floor.receiveShadow = true;
    floor.name = "placeholder_floor";
    const grid = new THREE.GridHelper(200, 200, 0x444444, 0x666666);
    grid.position.y = 0.002;
    this.root.add(floor, grid);
  }
}

/** 칸 크기(유닛). 병합해도 프러스텀 컬링이 칸 단위로 남도록 [웹 전용 값] */
const CELL = 40;

/**
 * 정적 메시 병합: (재질, 속성 구성, 공간 칸) 이 같은 메시를 하나로. 스킨·모프·다중 재질 메시는 그대로 둔다.
 * 병합 메시는 원래 이름 목록을 userData.sources 에 남긴다.
 */
function mergeStatic(src: THREE.Object3D, stats: MapView["stats"]): THREE.Object3D {
  const out = new THREE.Group();
  out.name = "visual";
  const groups = new Map<string, { mat: THREE.Material; geos: THREE.BufferGeometry[]; names: string[] }>();
  const keep: THREE.Object3D[] = [];
  const c = new THREE.Vector3();
  src.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    stats.meshesIn++;
    if ((m as THREE.SkinnedMesh).isSkinnedMesh || Array.isArray(m.material) || m.geometry.morphAttributes.position || !m.visible) {
      keep.push(m);
      return;
    }
    const g = m.geometry.clone().applyMatrix4(m.matrixWorld);
    if (m.matrixWorld.determinant() < 0) {
      // 음의 행렬식: 감김 반전을 인덱스로 되돌린다
      const idx = g.index;
      if (idx) for (let i = 0; i < idx.count; i += 3) {
        const a = idx.getX(i + 1);
        idx.setX(i + 1, idx.getX(i + 2));
        idx.setX(i + 2, a);
      }
    }
    g.computeBoundingBox();
    g.boundingBox!.getCenter(c);
    const sig = Object.keys(g.attributes).sort().join(",") + (g.index ? ":i" : ":n");
    const key = `${m.material.uuid}|${sig}|${Math.floor(c.x / CELL)},${Math.floor(c.y / CELL)},${Math.floor(c.z / CELL)}`;
    let e = groups.get(key);
    if (!e) groups.set(key, (e = { mat: m.material, geos: [], names: [] }));
    e.geos.push(g);
    e.names.push(m.name);
  });
  for (const e of groups.values()) {
    const merged = e.geos.length === 1 ? e.geos[0] : mergeGeometries(e.geos, false);
    // 속성 형식이 달라 병합이 안 되면 따로 둔다
    const list: [THREE.BufferGeometry, string[]][] = merged ? [[merged, e.names]] : e.geos.map((g, i) => [g, [e.names[i]]]);
    for (const [g, names] of list) {
      g.computeBoundingSphere();
      const mesh = new THREE.Mesh(g, e.mat);
      mesh.receiveShadow = true;
      mesh.name = names.length === 1 ? names[0] : `merged(${names.length})`;
      mesh.userData.sources = names;
      mesh.matrixAutoUpdate = false;
      out.add(mesh);
      stats.meshesOut++;
      stats.triangles += (g.index ? g.index.count : g.attributes.position.count) / 3;
    }
  }
  for (const k of keep) {
    k.receiveShadow = true;
    k.removeFromParent();
    k.matrixAutoUpdate = false;
    k.matrix.copy(k.matrixWorld);
    out.add(k);
    stats.meshesOut++;
  }
  return out;
}
