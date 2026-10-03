// 담당: [physics] — CollisionWorld 구현(지형 메시 + 동적 충돌체).
// 입력: world.data.collision = { meta: collision.json, bin: ArrayBuffer } — 형식은 docs/impl/physics.md "충돌 데이터".
import type { Vec3 } from "../fmath.ts";
import { v3 } from "../fmath.ts";
import { Layer, type CollisionWorld, type DynamicShape, type Hit, type SphereQueryFilter } from "../types.ts";
import { LAYER_HIT_MASK, SUB_LAYER_HIT_MASK, hitsLayer, layerFromFilter, layerFromName, maskValue, PhiveLayer } from "./filter.ts";
import { TriMesh, type Penetration, type SweepResult, type TriFilter } from "./mesh.ts";

export interface MaterialInfo {
  name: string;
  /** 웹 Layer 비트 */
  layer: number;
  paintable: boolean;
  /** UserShapeTag 이름들(있으면) */
  tags: string[];
  /** Phive 원시 필터(있으면). 없으면 layer 로 대신 판정 */
  hitMask: number | null;
  subMask: number | null;
}

/** 플레이어(캐릭터 컨트롤러) 질의용 필터 정보. */
export interface BodyFilter {
  /** Phive 엔티티 레이어 번호(SplPlayer = 5) */
  layerIndex: number;
  /** 하위 레이어 번호(사람 3, 오징어 4) */
  subIndex: number;
  /** 원시 필터가 없는 재질은 이 Layer 비트로 막힘 판정 */
  fallbackMask: number;
}

interface DynEntry {
  actor: number;
  shape: DynamicShape;
}

export class MeshCollisionWorld implements CollisionWorld {
  readonly mesh: TriMesh;
  readonly materials: MaterialInfo[];
  /** 에셋이 없어 평면으로 대체 중인지 */
  readonly fallback: boolean;
  private readonly dyn = new Map<number, DynEntry>();

  constructor(mesh: TriMesh, materials: MaterialInfo[], fallback = false) {
    this.mesh = mesh;
    this.materials = materials;
    this.fallback = fallback;
  }

  materialName(material: number): string {
    return this.materials[material]?.name ?? "";
  }

  material(material: number): MaterialInfo | undefined {
    return this.materials[material];
  }

  setDynamic(actor: number, shape: DynamicShape | null): void {
    if (shape) this.dyn.set(actor, { actor, shape });
    else this.dyn.delete(actor);
  }

  private layerFilter(mask: number): TriFilter {
    const m = this.mesh.mat, mats = this.materials;
    return (tri) => ((mats[m[tri]]?.layer ?? Layer.Ground) & mask) !== 0;
  }

  /** 캐릭터 컨트롤러가 막히는 삼각형 필터. */
  bodyFilter(f: BodyFilter): TriFilter {
    const m = this.mesh.mat, mats = this.materials;
    const cache = mats.map((mt) => {
      if (mt.hitMask !== null) {
        const sub = mt.subMask ?? 0xffffffff;
        return hitsLayer(mt.hitMask, f.layerIndex) && hitsLayer(sub, f.subIndex);
      }
      return (mt.layer & f.fallbackMask) !== 0;
    });
    return (tri) => cache[m[tri]] ?? true;
  }

  raycast(origin: Vec3, dir: Vec3, maxDist: number, mask: number): Hit | null {
    let best: Hit | null = null;
    const r = this.mesh.raycast(origin[0], origin[1], origin[2], dir[0], dir[1], dir[2], maxDist, this.layerFilter(mask));
    if (r) {
      best = this.triHit(r.tri, r.t, origin[0] + dir[0] * r.t, origin[1] + dir[1] * r.t, origin[2] + dir[2] * r.t, null);
      // 메시 감김 방향과 무관하게 레이 쪽을 향하는 법선
      if (best.normal[0] * dir[0] + best.normal[1] * dir[1] + best.normal[2] * dir[2] > 0) {
        best.normal[0] = -best.normal[0]; best.normal[1] = -best.normal[1]; best.normal[2] = -best.normal[2];
      }
    }
    for (const d of this.dyn.values()) {
      if ((d.shape.layer & mask) === 0) continue;
      const t = rayShape(origin, dir, d.shape, 0);
      if (t >= 0 && t <= maxDist && (!best || t < best.t)) {
        const p = v3(origin[0] + dir[0] * t, origin[1] + dir[1] * t, origin[2] + dir[2] * t);
        best = { t, point: p, normal: shapeNormal(d.shape, p, 0), layer: d.shape.layer, material: -1, actor: d.actor };
      }
    }
    return best;
  }

  sweepSphere(from: Vec3, to: Vec3, radius: number, mask: number, query?: SphereQueryFilter): Hit | null {
    const mx = to[0] - from[0], my = to[1] - from[1], mz = to[2] - from[2];
    let best: Hit | null = null;
    const r = this.mesh.sweepSegment(from[0], from[1], from[2], from[0], from[1], from[2], radius, mx, my, mz, query ? (tri) => {
      const mt = this.materials[this.mesh.mat[tri]];
      // Stage mesh entries are Ground bodies; raw shape masks retain camera-only
      // barriers even when the legacy web layer was classified for bullets.
      if (mt?.layer === Layer.Water) return false;
      return hitsLayer(query.hitMask, PhiveLayer.Ground) &&
        (mt?.hitMask == null ? ((mt?.layer ?? Layer.Ground) & mask) !== 0 :
          hitsLayer(mt.hitMask, query.layerIndex) && hitsLayer(mt.subMask ?? 0xffffffff, query.subIndex));
    } : this.layerFilter(mask), SR);
    if (r) best = this.triHit(r.tri, r.t, r.px, r.py, r.pz, r);
    const len = Math.hypot(mx, my, mz);
    if (len > 0) {
      const dir = v3(mx / len, my / len, mz / len);
      for (const d of this.dyn.values()) {
        if (query || (d.shape.layer & mask) === 0) continue;
        const td = rayShape(from, dir, d.shape, radius);
        if (td < 0 || td > len) continue;
        const t = td / len;
        if (!best || t < best.t) {
          const c = v3(from[0] + mx * t, from[1] + my * t, from[2] + mz * t);
          const n = shapeNormal(d.shape, c, radius);
          best = { t, point: v3(c[0] - n[0] * radius, c[1] - n[1] * radius, c[2] - n[2] * radius), normal: n, layer: d.shape.layer, material: -1, actor: d.actor };
        }
      }
    }
    return best;
  }

  /** 캐릭터 몸(세로 캡슐 = 선분 a→b, 반경 r)을 motion 만큼 쓸어 넘긴다. 지형만(동적 충돌체는 플레이어를 막지 않음 [추정]). */
  sweepBody(a: ArrayLike<number>, b: ArrayLike<number>, r: number, motion: ArrayLike<number>, filter: TriFilter): SweepResult | null {
    return this.mesh.sweepSegment(a[0], a[1], a[2], b[0], b[1], b[2], r, motion[0], motion[1], motion[2], filter, SR);
  }

  overlapBody(a: ArrayLike<number>, b: ArrayLike<number>, r: number, filter: TriFilter, out: Penetration[]): Penetration[] {
    return this.mesh.overlapSegment(a[0], a[1], a[2], b[0], b[1], b[2], r, filter, out);
  }

  /** 맵 경계(낙하 판정 보조). */
  bounds(): { min: number[]; max: number[] } {
    return { min: this.mesh.min, max: this.mesh.max };
  }

  private triHit(tri: number, t: number, px: number, py: number, pz: number, s: SweepResult | null): Hit {
    const mat = this.mesh.mat[tri];
    const info = this.materials[mat];
    let nx: number, ny: number, nz: number;
    if (s) {
      nx = s.nx; ny = s.ny; nz = s.nz;
    } else {
      const a = this.mesh.vert(tri, 0, VA), b = this.mesh.vert(tri, 1, VB), c = this.mesh.vert(tri, 2, VC);
      const e1x = b[0] - a[0], e1y = b[1] - a[1], e1z = b[2] - a[2], e2x = c[0] - a[0], e2y = c[1] - a[1], e2z = c[2] - a[2];
      nx = e1y * e2z - e1z * e2y; ny = e1z * e2x - e1x * e2z; nz = e1x * e2y - e1y * e2x;
      const l = Math.hypot(nx, ny, nz) || 1;
      nx /= l; ny /= l; nz /= l;
    }
    return { t, point: v3(px, py, pz), normal: v3(nx, ny, nz), layer: info?.layer ?? Layer.Ground, material: mat, actor: -1 };
  }
}

const SR: SweepResult = { t: 0, nx: 0, ny: 0, nz: 0, px: 0, py: 0, pz: 0, tri: -1 };
const VA = [0, 0, 0], VB = [0, 0, 0], VC = [0, 0, 0];

/** 레이(정규화 방향) vs 동적 형상(반경 r 만큼 부풀림). 거리 또는 -1. 상자는 반경만큼 각 축을 늘린 근사. */
function rayShape(o: Vec3, d: Vec3, s: DynamicShape, r: number): number {
  if (s.kind === "sphere") return raySphere(o[0], o[1], o[2], d[0], d[1], d[2], s.center[0], s.center[1], s.center[2], s.radius + r);
  if (s.kind === "capsule") {
    const best = rayCapsule(o, d, s.a, s.b, s.radius + r);
    return best;
  }
  // 상자(yaw 회전): 국소 좌표로 옮겨 slab
  const c = Math.cos(-s.yaw), sn = Math.sin(-s.yaw);
  const lx = o[0] - s.center[0], ly = o[1] - s.center[1], lz = o[2] - s.center[2];
  const ox = lx * c + lz * sn, oz = -lx * sn + lz * c, oy = ly;
  const dx = d[0] * c + d[2] * sn, dz = -d[0] * sn + d[2] * c, dy = d[1];
  const hx = s.half[0] + r, hy = s.half[1] + r, hz = s.half[2] + r;
  let tmin = 0, tmax = Infinity;
  const slab = (oo: number, dd: number, h: number): boolean => {
    if (Math.abs(dd) < 1e-12) return oo >= -h && oo <= h;
    let t1 = (-h - oo) / dd, t2 = (h - oo) / dd;
    if (t1 > t2) { const t = t1; t1 = t2; t2 = t; }
    if (t1 > tmin) tmin = t1;
    if (t2 < tmax) tmax = t2;
    return tmin <= tmax;
  };
  if (!slab(ox, dx, hx) || !slab(oy, dy, hy) || !slab(oz, dz, hz)) return -1;
  return tmin;
}

function raySphere(ox: number, oy: number, oz: number, dx: number, dy: number, dz: number, cx: number, cy: number, cz: number, r: number): number {
  const mx = ox - cx, my = oy - cy, mz = oz - cz;
  const b = mx * dx + my * dy + mz * dz;
  const c = mx * mx + my * my + mz * mz - r * r;
  if (c <= 0) return 0;
  if (b > 0) return -1;
  const disc = b * b - c;
  if (disc < 0) return -1;
  return -b - Math.sqrt(disc);
}

function rayCapsule(o: Vec3, d: Vec3, a: Vec3, b: Vec3, r: number): number {
  // 원통부 + 양 끝 구
  let best = -1;
  const take = (t: number) => {
    if (t >= 0 && (best < 0 || t < best)) best = t;
  };
  take(raySphere(o[0], o[1], o[2], d[0], d[1], d[2], a[0], a[1], a[2], r));
  take(raySphere(o[0], o[1], o[2], d[0], d[1], d[2], b[0], b[1], b[2], r));
  const abx = b[0] - a[0], aby = b[1] - a[1], abz = b[2] - a[2];
  const len2 = abx * abx + aby * aby + abz * abz;
  if (len2 > 0) {
    const aox = o[0] - a[0], aoy = o[1] - a[1], aoz = o[2] - a[2];
    const dd = (d[0] * abx + d[1] * aby + d[2] * abz) / len2;
    const od = (aox * abx + aoy * aby + aoz * abz) / len2;
    const px = d[0] - abx * dd, py = d[1] - aby * dd, pz = d[2] - abz * dd;
    const qx = aox - abx * od, qy = aoy - aby * od, qz = aoz - abz * od;
    const A = px * px + py * py + pz * pz, B = 2 * (px * qx + py * qy + pz * qz), C = qx * qx + qy * qy + qz * qz - r * r;
    if (A > 1e-12) {
      const disc = B * B - 4 * A * C;
      if (disc >= 0) {
        const t = (-B - Math.sqrt(disc)) / (2 * A);
        const s = od + dd * t;
        if (s >= 0 && s <= 1) take(t);
      }
    }
  }
  return best;
}

/** 형상 표면(반경 r 부풀림) 위 점 p 에서의 바깥 법선. */
function shapeNormal(s: DynamicShape, p: Vec3, r: number): Vec3 {
  let cx: number, cy: number, cz: number;
  if (s.kind === "sphere") {
    cx = s.center[0]; cy = s.center[1]; cz = s.center[2];
  } else if (s.kind === "capsule") {
    const abx = s.b[0] - s.a[0], aby = s.b[1] - s.a[1], abz = s.b[2] - s.a[2];
    const len2 = abx * abx + aby * aby + abz * abz;
    let t = len2 > 0 ? ((p[0] - s.a[0]) * abx + (p[1] - s.a[1]) * aby + (p[2] - s.a[2]) * abz) / len2 : 0;
    t = t < 0 ? 0 : t > 1 ? 1 : t;
    cx = s.a[0] + abx * t; cy = s.a[1] + aby * t; cz = s.a[2] + abz * t;
  } else {
    const c = Math.cos(-s.yaw), sn = Math.sin(-s.yaw);
    const lx = p[0] - s.center[0], ly = p[1] - s.center[1], lz = p[2] - s.center[2];
    const x = lx * c + lz * sn, z = -lx * sn + lz * c;
    const fx = Math.abs(x) / (s.half[0] + r), fy = Math.abs(ly) / (s.half[1] + r), fz = Math.abs(z) / (s.half[2] + r);
    let nx = 0, ny = 0, nz = 0;
    if (fx >= fy && fx >= fz) nx = Math.sign(x) || 1;
    else if (fy >= fz) ny = Math.sign(ly) || 1;
    else nz = Math.sign(z) || 1;
    const cw = Math.cos(s.yaw), sw = Math.sin(s.yaw);
    return v3(nx * cw + nz * sw, ny, -nx * sw + nz * cw);
  }
  const nx = p[0] - cx, ny = p[1] - cy, nz = p[2] - cz;
  const l = Math.hypot(nx, ny, nz) || 1;
  return v3(nx / l, ny / l, nz / l);
}

// ---- 데이터 읽기 ----------------------------------------------------------

interface LayoutEntry {
  offset?: number;
  byteOffset?: number;
  count?: number;
  byteLength?: number;
}

function entry(layout: Record<string, unknown>, ...names: string[]): LayoutEntry | null {
  for (const n of names) {
    const e = layout[n];
    if (e && typeof e === "object") return e as LayoutEntry;
  }
  return null;
}

/** collision.json + collision.bin → 월드. 형식이 맞지 않으면 예외. */
export function loadCollision(meta: Record<string, unknown>, bin: ArrayBuffer): MeshCollisionWorld {
  const layout = (meta.layout ?? meta) as Record<string, unknown>;
  const pe = entry(layout, "positions", "position", "vertices");
  const ie = entry(layout, "indices", "index", "triangles");
  const me = entry(layout, "triMaterial", "triMaterials", "materials", "material");
  if (!pe || !ie) throw new Error("collision.json layout 에 positions/indices 가 없음");
  const off = (e: LayoutEntry) => e.offset ?? e.byteOffset ?? 0;
  // count 해석: positions = 정점 수, indices = 인덱스 수, triMaterial = 삼각형 수 (glTF accessor 규약).
  // byteLength 가 있으면 그것을 우선한다.
  const posFloats = pe.byteLength !== undefined ? pe.byteLength / 4 : (pe.count ?? 0) * 3;
  let idxCount = ie.byteLength !== undefined ? ie.byteLength / 4 : ie.count ?? 0;
  const triCountMeta = me ? (me.byteLength !== undefined ? me.byteLength / 2 : me.count ?? 0) : 0;
  if (me && triCountMeta * 3 !== idxCount && ie.count !== undefined && ie.count === triCountMeta) idxCount = ie.count * 3;
  let pos = new Float32Array(bin.slice(off(pe), off(pe) + posFloats * 4));
  let idx = new Uint32Array(bin.slice(off(ie), off(ie) + idxCount * 4));
  const triCount = Math.floor(idx.length / 3);
  let mat = me ? new Uint16Array(bin.slice(off(me), off(me) + triCount * 2)) : new Uint16Array(triCount);
  const mats = Array.isArray(meta.materials) ? (meta.materials as Record<string, unknown>[]).map(readMaterial) : [];
  if (mats.length === 0) mats.push(defaultMaterial("Ground"));
  // 삼각형이 아닌 기본 도형(Capsule/Sphere/Cylinder) → 다면체로 근사해 붙인다
  if (Array.isArray(meta.primitives) && meta.primitives.length) {
    const P: number[] = Array.from(pos), I: number[] = Array.from(idx), M: number[] = Array.from(mat);
    for (const prim of meta.primitives as Record<string, unknown>[]) tessellatePrimitive(prim, P, I, M);
    pos = new Float32Array(P);
    idx = new Uint32Array(I);
    mat = new Uint16Array(M);
  }
  return new MeshCollisionWorld(new TriMesh(pos, idx, mat), mats);
}

const SEG = 12;
const RINGS = 4;

/**
 * 기본 도형 1개를 삼각형으로(경도 12분할, 반구 위도 4분할). 국소점 = OffsetRotation(도, Rz·Ry·Rx)·p + OffsetTranslation,
 * 월드 = actorMatrix(열 우선 4×4)·국소점 [추정: 오프셋 적용 순서]. 반경 크기 조정은 actorMatrix 의 축척을 그대로 따른다.
 */
function tessellatePrimitive(prim: Record<string, unknown>, P: number[], I: number[], M: number[]): void {
  const type = String(prim.type ?? "");
  const sh = (prim.shape ?? {}) as Record<string, unknown>;
  const m = Array.isArray(prim.actorMatrix) && prim.actorMatrix.length === 16 ? (prim.actorMatrix as number[]) : [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  const material = typeof prim.material === "number" ? prim.material : 0;
  const ot = (Array.isArray(sh.OffsetTranslation) ? sh.OffsetTranslation : [0, 0, 0]) as number[];
  const orr = (Array.isArray(sh.OffsetRotation) ? sh.OffsetRotation : [0, 0, 0]) as number[];
  const rx = (orr[0] * Math.PI) / 180, ry = (orr[1] * Math.PI) / 180, rz = (orr[2] * Math.PI) / 180;
  const toWorld = (x: number, y: number, z: number): number => {
    const ay = y * Math.cos(rx) - z * Math.sin(rx), az0 = y * Math.sin(rx) + z * Math.cos(rx);
    const bx = x * Math.cos(ry) + az0 * Math.sin(ry), bz = -x * Math.sin(ry) + az0 * Math.cos(ry);
    const cx = bx * Math.cos(rz) - ay * Math.sin(rz), cy = bx * Math.sin(rz) + ay * Math.cos(rz);
    const lx = cx + ot[0], ly = cy + ot[1], lz = bz + ot[2];
    P.push(m[0] * lx + m[4] * ly + m[8] * lz + m[12], m[1] * lx + m[5] * ly + m[9] * lz + m[13], m[2] * lx + m[6] * ly + m[10] * lz + m[14]);
    return P.length / 3 - 1;
  };
  const vec = (k: string): number[] => (Array.isArray(sh[k]) ? (sh[k] as number[]) : [0, 0, 0]);
  const r = typeof sh.Radius === "number" ? sh.Radius : 0.5;
  let a: number[], b: number[], caps = true;
  if (type === "sphere") { a = vec("Center"); b = a; }
  else if (type === "capsule") { a = vec("CenterA"); b = vec("CenterB"); }
  else if (type === "cylinder") { a = vec("CenterA"); b = vec("CenterB"); caps = false; }
  else return;
  let ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
  const ul = Math.hypot(ux, uy, uz);
  if (ul > 1e-9) { ux /= ul; uy /= ul; uz /= ul; } else { ux = 0; uy = 1; uz = 0; }
  let px = -uy, py = ux, pz = 0;
  if (Math.hypot(px, py, pz) < 1e-6) { px = 0; py = uz; pz = -uy; }
  const pl = Math.hypot(px, py, pz);
  px /= pl; py /= pl; pz /= pl;
  const qx = uy * pz - uz * py, qy = uz * px - ux * pz, qz = ux * py - uy * px;
  const ring = (c: number[], off: number, rad: number): number[] => {
    const out: number[] = [];
    for (let i = 0; i < SEG; i++) {
      const t = (i / SEG) * Math.PI * 2, co = Math.cos(t) * rad, si = Math.sin(t) * rad;
      out.push(toWorld(c[0] + ux * off + px * co + qx * si, c[1] + uy * off + py * co + qy * si, c[2] + uz * off + pz * co + qz * si));
    }
    return out;
  };
  const band = (r1: number[], r2: number[]) => {
    for (let i = 0; i < SEG; i++) {
      const j = (i + 1) % SEG;
      I.push(r1[i], r2[i], r2[j], r1[i], r2[j], r1[j]);
      M.push(material, material);
    }
  };
  const fan = (center: number, rr: number[]) => {
    for (let i = 0; i < SEG; i++) {
      I.push(center, rr[i], rr[(i + 1) % SEG]);
      M.push(material);
    }
  };
  if (caps) {
    const rings: number[][] = [];
    for (let k = RINGS - 1; k >= 1; k--) {
      const ang = (k / RINGS) * (Math.PI / 2);
      rings.push(ring(a, -Math.sin(ang) * r, Math.cos(ang) * r));
    }
    rings.push(ring(a, 0, r));
    rings.push(ring(b, 0, r));
    for (let k = 1; k < RINGS; k++) {
      const ang = (k / RINGS) * (Math.PI / 2);
      rings.push(ring(b, Math.sin(ang) * r, Math.cos(ang) * r));
    }
    for (let i = 0; i + 1 < rings.length; i++) band(rings[i], rings[i + 1]);
    fan(toWorld(a[0] - ux * r, a[1] - uy * r, a[2] - uz * r), rings[0]);
    fan(toWorld(b[0] + ux * r, b[1] + uy * r, b[2] + uz * r), rings[rings.length - 1]);
  } else {
    const r0 = ring(a, 0, r), r1 = ring(b, 0, r);
    band(r0, r1);
    fan(toWorld(a[0], a[1], a[2]), r0);
    fan(toWorld(b[0], b[1], b[2]), r1);
  }
}

const WEB_LAYER_NAMES = new Set(["Ground", "Object", "Player", "Water", "KeepOut"]);

function readMaterial(m: Record<string, unknown>): MaterialInfo {
  const name = String(m.name ?? m.material ?? "");
  // 에셋 형식: { name, layer, paintable, flags: { userShapeTags[], layerHitMask, subLayerHitMask, filterRaw, … } }
  const flags = (m.flags ?? {}) as Record<string, unknown>;
  const filter = (m.filter ?? {}) as Record<string, unknown>;
  const tagSrc = m.tags ?? m.userShapeTags ?? flags.userShapeTags;
  const tags = Array.isArray(tagSrc) ? (tagSrc as unknown[]).map(String) : [];
  let hitMask = maskValue(m.layerHitMask ?? flags.layerHitMask ?? filter.layerHitMask ?? filter.layer, LAYER_HIT_MASK);
  let subMask = maskValue(m.subLayerHitMask ?? flags.subLayerHitMask ?? filter.subLayerHitMask ?? filter.sub, SUB_LAYER_HIT_MASK);
  // filterRaw "0x<상위 32 sub><하위 32 layer>" (collision_mesh.md §3.4 필터표 u64)
  if (typeof flags.filterRaw === "string" && /^0x[0-9a-f]{1,16}$/i.test(flags.filterRaw)) {
    const raw = BigInt(flags.filterRaw);
    if (hitMask === null) hitMask = Number(raw & 0xffffffffn);
    if (subMask === null) subMask = Number((raw >> 32n) & 0xffffffffn);
  }
  let layer: number;
  if (typeof m.layer === "number") layer = m.layer;
  else if (typeof m.layer === "string" && WEB_LAYER_NAMES.has(m.layer)) layer = layerFromName(m.layer);
  else if (hitMask !== null) layer = layerFromFilter(hitMask, name);
  else if (typeof m.layer === "string") layer = layerFromName(m.layer);
  else layer = /water/i.test(name) ? Layer.Water : Layer.Ground;
  if (tags.includes("Water")) layer = Layer.Water;
  return { name, layer, paintable: m.paintable !== false, tags, hitMask, subMask };
}

function defaultMaterial(name: string): MaterialInfo {
  return { name, layer: Layer.Ground, paintable: true, tags: [], hitMask: null, subMask: null };
}

/** 에셋이 없을 때: y = 0 의 넓은 평면 하나(웹 전용 대체, 원본 아님). */
export function fallbackPlane(half = 500): MeshCollisionWorld {
  const pos = new Float32Array([-half, 0, -half, half, 0, -half, half, 0, half, -half, 0, half]);
  const idx = new Uint32Array([0, 2, 1, 0, 3, 2]);
  const mat = new Uint16Array(2);
  return new MeshCollisionWorld(new TriMesh(pos, idx, mat), [defaultMaterial("Fallback")], true);
}

/** 플레이어(캐릭터 컨트롤러) 필터: Phive SplPlayer(5), 사람 하위 레이어 3 / 오징어 4. */
export function playerBodyFilter(squid: boolean): BodyFilter {
  return {
    layerIndex: PhiveLayer.SplPlayer,
    subIndex: squid ? 4 : 3,
    fallbackMask: Layer.Ground | Layer.Object | Layer.KeepOut,
  };
}
