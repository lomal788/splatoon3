// 맵 표시: visual.glb 배치, 정적 메시 병합(재질·공간 칸 단위), 조명(env.json), 에셋이 없으면 격자 바닥.
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import type { GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Bundle } from "../assets.ts";
import { applyHoian } from "./hoian.ts";
import { fresOf, textureResolver } from "./model.ts";
import type { EnvLight, MaterialTeamParams } from "./teamcolor.ts";

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
 *   주 방향광 색·세기: teamColorLight.lobbyMainLight(RenderingDay MainLight Color/Intens) — MainLight→DirectionalLight 대응은 [추정, team_color.md §5.3].
 *     없으면 teamColorLight.defaultDay(기본 env DirectionalLight DiffuseColor/Intensity).
 *   방향: 로비 MainLight Latitude/Longitude → lonLatToDir (없으면 defaultDay.Direction [데이터: 기본 env]).
 *   배경색: rendering.Fog.DepthFog.Color [근사: 하늘 구(SkySphere Sky_Daytime00) 미표시 대신 원거리 안개색].
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
 * u = Longitude, v = Latitude 순서는 [추정: 이름 순서 "LongitudeLatitude", v 가 고도일 때 빛이 아래로 향함].
 * RenderingDay.MainLight 값이 이 접근자로 들어가는 경로는 [추정](Intens/Color 와 같은 형식).
 */
export function lonLatToDir(lonDeg: number, latDeg: number): [number, number, number] {
  const k = Math.fround(0.017453292);
  const u = Math.fround(lonDeg * k), v = Math.fround(latDeg * k);
  const cv = -Math.cos(v);
  return [Math.sin(u) * cv, -Math.sin(v), Math.cos(u) * cv];
}

const srgbToLinear = (c: [number, number, number]): [number, number, number] => {
  const t = new THREE.Color().setRGB(c[0], c[1], c[2], THREE.SRGBColorSpace);
  return [t.r, t.g, t.b];
};

/** 원본 Intensity → three 광원 세기 배율. 원본 HDR 합성(Hoian_ProcHDRCompose)이 미해독이라 화면 밝기 맞춤용 근사 상수 [근사] */
const LIGHT_SCALE = 0.25;
/** 그림자 카메라 반폭(유닛) [웹 전용 값] */
const SHADOW_HALF = 6;
const HEMI_INTENSITY = 1.0;

export class MapView {
  readonly root = new THREE.Group();
  readonly sun: THREE.DirectionalLight;
  readonly hemi: THREE.HemisphereLight;
  env: EnvInfo = DEFAULT_ENV;
  readonly skipped: string[] = [];
  stats = { meshesIn: 0, meshesOut: 0, triangles: 0, placeholder: false };

  constructor(scene: THREE.Scene) {
    this.root.name = MAP_ROOT_NAME;
    scene.add(this.root);
    this.sun = new THREE.DirectionalLight(0xffffff, 1);
    // 동적 그림자 근사: 플레이어 주변만(원본 gsys_dynamic_depth_shadow 캐스케이드 설정은 미해독) [근사]
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(1024, 1024);
    const sc = this.sun.shadow.camera;
    sc.left = sc.bottom = -SHADOW_HALF;
    sc.right = sc.top = SHADOW_HALF;
    sc.near = 1;
    sc.far = 200;
    this.sun.shadow.bias = -0.0005;
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
    this.sun.intensity = e.light.intensity * LIGHT_SCALE;
    this.hemi.color.setRGB(e.sky[0], e.sky[1], e.sky[2], THREE.LinearSRGBColorSpace);
    this.hemi.groundColor.setRGB(e.ground[0], e.ground[1], e.ground[2], THREE.LinearSRGBColorSpace);
    scene.background = new THREE.Color().setRGB(e.sky[0], e.sky[1], e.sky[2], THREE.LinearSRGBColorSpace);
  }

  load(scene: THREE.Scene, bundle: Bundle | undefined, team: MaterialTeamParams): void {
    if (bundle?.has("env.json")) this.env = parseEnv(bundle.json("env.json"));
    this.applyEnv(scene);
    const glbName = bundle?.names().find((n) => /(^|\/)visual\.glb$/i.test(n)) ?? bundle?.names().find((n) => /\.glb$/i.test(n));
    if (bundle && glbName) {
      const gltf = bundle.gltf(glbName);
      this.addVisual(gltf, bundle, team);
    } else this.addPlaceholder();
  }

  private addVisual(gltf: GLTF, bundle: Bundle, team: MaterialTeamParams): void {
    const tex = textureResolver(gltf, bundle);
    const seen = new Set<THREE.Material>();
    gltf.scene.updateMatrixWorld(true);
    gltf.scene.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      for (const mat of Array.isArray(m.material) ? m.material : [m.material]) {
        if (seen.has(mat)) continue;
        seen.add(mat);
        const f = fresOf(mat);
        if (f && (mat as THREE.MeshStandardMaterial).isMeshStandardMaterial) applyHoian(mat as THREE.MeshStandardMaterial, f, team, tex, this.skipped);
      }
    });
    this.root.add(mergeStatic(gltf.scene, this.stats));
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
