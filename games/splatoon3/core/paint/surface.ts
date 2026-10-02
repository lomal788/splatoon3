// 도색 표면: 충돌 메시의 칠 가능 삼각형 → 평면 차트(패널) → UV 아틀라스(월드 1 단위당 8 텍셀).
// 원본은 ColPaintBuilder(패널 추출·연결·UV 매핑·픽셀 영역·수평/수직 옥트리)로 실행 중에 만든다
// (paint_and_score.md §3.2, 알고리즘 [미확정]). 여기의 차트 분할·배치는 웹 독자 방식이고,
// 원본과 맞추는 것은 밀도(8 텍셀/단위, §3.1)와 그 결과인 면적(텍셀 수)이다.
import type { World } from "../world.ts";

export const TEXELS_PER_UNIT = 8;
/** 차트 한 변 최대 텍셀(여백 포함). 큰 평면은 여러 차트로 나뉜다. */
const MAX_CHART = 1024;
/** 차트 둘레 여백 텍셀(쌍선형 표시용, 집계 제외). */
const PAD = 1;
const PAGE = 2048;

export interface RawTriangles {
  /** 삼각형마다 9개(a,b,c 정점 xyz) */
  tri: Float64Array;
  /** 삼각형마다 재질 인덱스(-1 = 모름) */
  material: Int32Array;
  paintable: Uint8Array;
  source: string;
}

export interface Chart {
  page: number;
  x0: number;
  y0: number;
  w: number;
  h: number;
  /** 텍셀 격자 원점(월드) — 텍셀 (i,j) 중심 = o + (i+0.5)/8·e1 + (j+0.5)/8·e2 */
  o: [number, number, number];
  e1: [number, number, number];
  e2: [number, number, number];
  n: [number, number, number];
  tris: number[];
}

export interface Page {
  w: number;
  h: number;
  /** RGBA8: R,G,B = 팀 0/1/2 잉크량(원본 도색 텍스처 색 채널), A = 차트 영역 255 */
  color: Uint8Array;
  /** 소유 스텐실(원본 팀비트 1/2/4, 0 = 없음) */
  stencil: Uint8Array;
  /** 칠 가능 표면 안 텍셀(집계 대상, 원본 d) */
  inside: Uint8Array;
}

export interface SurfaceMesh {
  page: number;
  positions: Float32Array;
  normals: Float32Array;
  uvs: Float32Array;
}

export class PaintSurfaces {
  readonly tris: RawTriangles;
  readonly charts: Chart[] = [];
  readonly pages: Page[] = [];
  /** 삼각형 → 차트 */
  readonly triChart: Int32Array;
  readonly meshes: SurfaceMesh[] = [];
  totalInside = 0;
  /** 감김 방향을 뒤집어 읽었는지 */
  flipped = false;
  private readonly grid = new Map<string, number[]>();
  private readonly cell = 4;
  private queryMark: Uint32Array;
  private queryStamp = 0;

  constructor(raw: RawTriangles) {
    this.tris = raw;
    const nt = raw.material.length;
    this.triChart = new Int32Array(nt).fill(-1);
    this.queryMark = new Uint32Array(0);
    this.buildCharts();
    this.packPages();
    this.rasterInside();
    this.buildGrid();
    this.buildMeshes();
    this.queryMark = new Uint32Array(this.charts.length);
  }

  /** 구(center, r)에 닿는 칠 가능 삼각형들의 차트 목록. */
  chartsInSphere(c: ArrayLike<number>, r: number): number[] {
    const out: number[] = [];
    if (++this.queryStamp === 0xffffffff) {
      this.queryMark.fill(0);
      this.queryStamp = 1;
    }
    const s = this.cell;
    const x0 = Math.floor((c[0] - r) / s), x1 = Math.floor((c[0] + r) / s);
    const y0 = Math.floor((c[1] - r) / s), y1 = Math.floor((c[1] + r) / s);
    const z0 = Math.floor((c[2] - r) / s), z1 = Math.floor((c[2] + r) / s);
    const t = this.tris.tri;
    const seen = new Set<number>();
    for (let x = x0; x <= x1; x++)
      for (let y = y0; y <= y1; y++)
        for (let z = z0; z <= z1; z++) {
          const list = this.grid.get(`${x},${y},${z}`);
          if (!list) continue;
          for (const ti of list) {
            if (seen.has(ti)) continue;
            seen.add(ti);
            const ch = this.triChart[ti];
            if (ch < 0 || this.queryMark[ch] === this.queryStamp) continue;
            if (sqDistPointTri(c, t, ti * 9) <= r * r) {
              this.queryMark[ch] = this.queryStamp;
              out.push(ch);
            }
          }
        }
    out.sort((a, b) => a - b);
    return out;
  }

  // ---- 차트 ----------------------------------------------------------------

  private buildCharts(): void {
    const { tri, paintable } = this.tris;
    const nt = paintable.length;
    const normals = new Float64Array(nt * 3);
    const area = new Float64Array(nt);
    for (let i = 0; i < nt; i++) {
      const k = i * 9;
      const ux = tri[k + 3] - tri[k], uy = tri[k + 4] - tri[k + 1], uz = tri[k + 5] - tri[k + 2];
      const vx = tri[k + 6] - tri[k], vy = tri[k + 7] - tri[k + 1], vz = tri[k + 8] - tri[k + 2];
      let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      const l = Math.hypot(nx, ny, nz);
      area[i] = l * 0.5;
      if (l > 0) {
        nx /= l;
        ny /= l;
        nz /= l;
      }
      normals[i * 3] = nx;
      normals[i * 3 + 1] = ny;
      normals[i * 3 + 2] = nz;
    }
    // 감김 방향 확인: (b−a)×(c−a) 를 앞면으로 본다. 위·아래를 향한 면적 중 아래가 70% 넘으면
    // 반대 감김 데이터로 보고 모든 법선을 뒤집는다(지형은 바닥 면적이 천장보다 크다는 가정 [근사]).
    let up = 0, down = 0;
    for (let i = 0; i < nt; i++) {
      if (!paintable[i]) continue;
      const ny = normals[i * 3 + 1];
      if (ny > 0.5) up += area[i];
      else if (ny < -0.5) down += area[i];
    }
    if (down > (up + down) * 0.7) for (let i = 0; i < normals.length; i++) normals[i] = -normals[i];
    this.flipped = down > (up + down) * 0.7;
    // 모서리 인접(정점은 1/512 격자 양자화 키로 용접 — 원본 정점 양자화 단위, collision_mesh.md §3.3)
    const vkey = (k: number) => `${Math.round(tri[k] * 512)},${Math.round(tri[k + 1] * 512)},${Math.round(tri[k + 2] * 512)}`;
    const edges = new Map<string, number[]>();
    const ekey = (a: string, b: string) => (a < b ? `${a}|${b}` : `${b}|${a}`);
    for (let i = 0; i < nt; i++) {
      if (!paintable[i] || area[i] < 1e-8) continue;
      const a = vkey(i * 9), b = vkey(i * 9 + 3), c = vkey(i * 9 + 6);
      for (const e of [ekey(a, b), ekey(b, c), ekey(c, a)]) {
        let l = edges.get(e);
        if (!l) edges.set(e, (l = []));
        l.push(i);
      }
    }
    const nb = (i: number): number[] => {
      const a = vkey(i * 9), b = vkey(i * 9 + 3), c = vkey(i * 9 + 6);
      const out: number[] = [];
      for (const e of [ekey(a, b), ekey(b, c), ekey(c, a)]) for (const j of edges.get(e) ?? []) if (j !== i) out.push(j);
      return out;
    };
    const lim = (MAX_CHART - 2 * PAD) / TEXELS_PER_UNIT;
    for (let s = 0; s < nt; s++) {
      if (!paintable[s] || area[s] < 1e-8 || this.triChart[s] >= 0) continue;
      const n: [number, number, number] = [normals[s * 3], normals[s * 3 + 1], normals[s * 3 + 2]];
      const { e1, e2 } = basis(n);
      const d = n[0] * tri[s * 9] + n[1] * tri[s * 9 + 1] + n[2] * tri[s * 9 + 2];
      const id = this.charts.length;
      const tris: number[] = [];
      let umin = Infinity, umax = -Infinity, vmin = Infinity, vmax = -Infinity;
      const ext = (i: number) => {
        let a = umin, b = umax, c = vmin, e = vmax;
        for (let k = i * 9; k < i * 9 + 9; k += 3) {
          const u = tri[k] * e1[0] + tri[k + 1] * e1[1] + tri[k + 2] * e1[2];
          const v = tri[k] * e2[0] + tri[k + 1] * e2[1] + tri[k + 2] * e2[2];
          if (u < a) a = u;
          if (u > b) b = u;
          if (v < c) c = v;
          if (v > e) e = v;
        }
        return [a, b, c, e];
      };
      const queue = [s];
      this.triChart[s] = id;
      for (let qi = 0; qi < queue.length; qi++) {
        const i = queue[qi];
        const [a, b, c, e] = ext(i);
        if (tris.length > 0 && (b - a > lim || e - c > lim)) {
          this.triChart[i] = -1;
          continue;
        }
        umin = a;
        umax = b;
        vmin = c;
        vmax = e;
        tris.push(i);
        for (const j of nb(i)) {
          if (this.triChart[j] >= 0) continue;
          const dot = normals[j * 3] * n[0] + normals[j * 3 + 1] * n[1] + normals[j * 3 + 2] * n[2];
          if (dot < 0.9999) continue;
          let coplanar = true;
          for (let k = j * 9; k < j * 9 + 9; k += 3)
            if (Math.abs(n[0] * tri[k] + n[1] * tri[k + 1] + n[2] * tri[k + 2] - d) > 2e-3) coplanar = false;
          if (!coplanar) continue;
          this.triChart[j] = id;
          queue.push(j);
        }
      }
      for (const i of tris) this.triChart[i] = id;
      const u0 = umin - PAD / TEXELS_PER_UNIT, v0 = vmin - PAD / TEXELS_PER_UNIT;
      const w = Math.ceil((umax - umin) * TEXELS_PER_UNIT) + 2 * PAD;
      const h = Math.ceil((vmax - vmin) * TEXELS_PER_UNIT) + 2 * PAD;
      const o: [number, number, number] = [
        n[0] * d + e1[0] * u0 + e2[0] * v0,
        n[1] * d + e1[1] * u0 + e2[1] * v0,
        n[2] * d + e1[2] * u0 + e2[2] * v0,
      ];
      this.charts.push({ page: -1, x0: 0, y0: 0, w, h, o, e1, e2, n, tris });
    }
  }

  /** 선반(shelf) 배치. 페이지 폭은 2048(WebGL2 최소 보장 크기) 이하로 필요한 만큼. */
  private packPages(): void {
    let texels = 0, maxW = 1;
    for (const c of this.charts) {
      texels += c.w * c.h;
      if (c.w > maxW) maxW = c.w;
    }
    const pageW = Math.max(maxW, Math.min(PAGE, Math.ceil(Math.sqrt(texels * 1.2))));
    const order = this.charts.map((_, i) => i).sort((a, b) => this.charts[b].h - this.charts[a].h || a - b);
    const heights: number[] = [];
    let page = 0, x = 0, y = 0, rowH = 0;
    heights[0] = 0;
    for (const ci of order) {
      const c = this.charts[ci];
      if (x + c.w > pageW) {
        y += rowH;
        x = 0;
        rowH = 0;
      }
      if (y + c.h > Math.max(PAGE, c.h) && y > 0) {
        page++;
        heights[page] = 0;
        x = 0;
        y = 0;
        rowH = 0;
      }
      c.page = page;
      c.x0 = x;
      c.y0 = y;
      x += c.w;
      if (c.h > rowH) rowH = c.h;
      heights[page] = Math.max(heights[page], y + c.h);
    }
    for (let p = 0; p < heights.length && this.charts.length > 0; p++) {
      const h = Math.max(1, heights[p]);
      this.pages.push({ w: pageW, h, color: new Uint8Array(pageW * h * 4), stencil: new Uint8Array(pageW * h), inside: new Uint8Array(pageW * h) });
    }
  }

  private rasterInside(): void {
    const t = this.tris.tri;
    for (const c of this.charts) {
      const pg = this.pages[c.page];
      for (let j = 0; j < c.h; j++) {
        const row = (c.y0 + j) * pg.w + c.x0;
        for (let i = 0; i < c.w; i++) pg.color[(row + i) * 4 + 3] = 255;
      }
      for (const ti of c.tris) {
        const p: number[] = [];
        for (let k = ti * 9; k < ti * 9 + 9; k += 3) {
          const dx = t[k] - c.o[0], dy = t[k + 1] - c.o[1], dz = t[k + 2] - c.o[2];
          p.push((dx * c.e1[0] + dy * c.e1[1] + dz * c.e1[2]) * TEXELS_PER_UNIT, (dx * c.e2[0] + dy * c.e2[1] + dz * c.e2[2]) * TEXELS_PER_UNIT);
        }
        const [ax, ay, bx, by, cx, cy] = p;
        const sgn = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) >= 0 ? 1 : -1;
        const i0 = Math.max(0, Math.floor(Math.min(ax, bx, cx))), i1 = Math.min(c.w - 1, Math.ceil(Math.max(ax, bx, cx)));
        const j0 = Math.max(0, Math.floor(Math.min(ay, by, cy))), j1 = Math.min(c.h - 1, Math.ceil(Math.max(ay, by, cy)));
        for (let j = j0; j <= j1; j++)
          for (let i = i0; i <= i1; i++) {
            const px = i + 0.5, py = j + 0.5;
            const w0 = sgn * ((bx - ax) * (py - ay) - (by - ay) * (px - ax));
            const w1 = sgn * ((cx - bx) * (py - by) - (cy - by) * (px - bx));
            const w2 = sgn * ((ax - cx) * (py - cy) - (ay - cy) * (px - cx));
            if (w0 >= -1e-9 && w1 >= -1e-9 && w2 >= -1e-9) {
              const idx = (c.y0 + j) * pg.w + c.x0 + i;
              if (!pg.inside[idx]) {
                pg.inside[idx] = 1;
                this.totalInside++;
              }
            }
          }
      }
    }
  }

  private buildGrid(): void {
    const t = this.tris.tri;
    const s = this.cell;
    for (let i = 0; i < this.triChart.length; i++) {
      if (this.triChart[i] < 0) continue;
      const k = i * 9;
      const x0 = Math.floor(Math.min(t[k], t[k + 3], t[k + 6]) / s), x1 = Math.floor(Math.max(t[k], t[k + 3], t[k + 6]) / s);
      const y0 = Math.floor(Math.min(t[k + 1], t[k + 4], t[k + 7]) / s), y1 = Math.floor(Math.max(t[k + 1], t[k + 4], t[k + 7]) / s);
      const z0 = Math.floor(Math.min(t[k + 2], t[k + 5], t[k + 8]) / s), z1 = Math.floor(Math.max(t[k + 2], t[k + 5], t[k + 8]) / s);
      for (let x = x0; x <= x1; x++)
        for (let y = y0; y <= y1; y++)
          for (let z = z0; z <= z1; z++) {
            const key = `${x},${y},${z}`;
            let l = this.grid.get(key);
            if (!l) this.grid.set(key, (l = []));
            l.push(i);
          }
    }
  }

  private buildMeshes(): void {
    const t = this.tris.tri;
    const per: number[][][] = this.pages.map(() => [[], [], []]);
    for (const c of this.charts) {
      const pg = this.pages[c.page];
      const [pos, nrm, uv] = per[c.page];
      for (const ti of c.tris)
        for (let k = ti * 9; k < ti * 9 + 9; k += 3) {
          pos.push(t[k], t[k + 1], t[k + 2]);
          nrm.push(c.n[0], c.n[1], c.n[2]);
          const dx = t[k] - c.o[0], dy = t[k + 1] - c.o[1], dz = t[k + 2] - c.o[2];
          const u = (dx * c.e1[0] + dy * c.e1[1] + dz * c.e1[2]) * TEXELS_PER_UNIT;
          const v = (dx * c.e2[0] + dy * c.e2[1] + dz * c.e2[2]) * TEXELS_PER_UNIT;
          uv.push((c.x0 + u) / pg.w, (c.y0 + v) / pg.h);
        }
    }
    per.forEach(([pos, nrm, uv], page) => {
      if (pos.length) this.meshes.push({ page, positions: new Float32Array(pos), normals: new Float32Array(nrm), uvs: new Float32Array(uv) });
    });
  }
}

function basis(n: [number, number, number]): { e1: [number, number, number]; e2: [number, number, number] } {
  // 벽: e1 = 수평 접선(Y × n), e2 = n × e1(위쪽). 바닥/천장: e1 = X 를 면에 투영.
  let e1: [number, number, number];
  if (Math.abs(n[1]) < 0.9) e1 = [n[2], 0, -n[0]];
  else e1 = [1 - n[0] * n[0], -n[0] * n[1], -n[0] * n[2]];
  const l = Math.hypot(e1[0], e1[1], e1[2]);
  e1 = [e1[0] / l, e1[1] / l, e1[2] / l];
  const e2: [number, number, number] = [n[1] * e1[2] - n[2] * e1[1], n[2] * e1[0] - n[0] * e1[2], n[0] * e1[1] - n[1] * e1[0]];
  return { e1, e2 };
}

/** 점과 삼각형의 최소 거리 제곱 (Ericson, Real-Time Collision Detection 5.1.5). */
function sqDistPointTri(p: ArrayLike<number>, t: Float64Array, k: number): number {
  const ax = t[k], ay = t[k + 1], az = t[k + 2];
  const abx = t[k + 3] - ax, aby = t[k + 4] - ay, abz = t[k + 5] - az;
  const acx = t[k + 6] - ax, acy = t[k + 7] - ay, acz = t[k + 8] - az;
  const apx = p[0] - ax, apy = p[1] - ay, apz = p[2] - az;
  const d1 = abx * apx + aby * apy + abz * apz, d2 = acx * apx + acy * apy + acz * apz;
  let qx: number, qy: number, qz: number;
  if (d1 <= 0 && d2 <= 0) {
    qx = ax; qy = ay; qz = az;
  } else {
    const bpx = p[0] - t[k + 3], bpy = p[1] - t[k + 4], bpz = p[2] - t[k + 5];
    const d3 = abx * bpx + aby * bpy + abz * bpz, d4 = acx * bpx + acy * bpy + acz * bpz;
    const cpx = p[0] - t[k + 6], cpy = p[1] - t[k + 7], cpz = p[2] - t[k + 8];
    const d5 = abx * cpx + aby * cpy + abz * cpz, d6 = acx * cpx + acy * cpy + acz * cpz;
    const vc = d1 * d4 - d3 * d2, vb = d5 * d2 - d1 * d6, va = d3 * d6 - d5 * d4;
    if (d3 >= 0 && d4 <= d3) {
      qx = t[k + 3]; qy = t[k + 4]; qz = t[k + 5];
    } else if (vc <= 0 && d1 >= 0 && d3 <= 0) {
      const v = d1 / (d1 - d3);
      qx = ax + abx * v; qy = ay + aby * v; qz = az + abz * v;
    } else if (d6 >= 0 && d5 <= d6) {
      qx = t[k + 6]; qy = t[k + 7]; qz = t[k + 8];
    } else if (vb <= 0 && d2 >= 0 && d6 <= 0) {
      const w = d2 / (d2 - d6);
      qx = ax + acx * w; qy = ay + acy * w; qz = az + acz * w;
    } else if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) {
      const w = (d4 - d3) / (d4 - d3 + (d5 - d6));
      qx = t[k + 3] + (t[k + 6] - t[k + 3]) * w; qy = t[k + 4] + (t[k + 7] - t[k + 4]) * w; qz = t[k + 5] + (t[k + 8] - t[k + 5]) * w;
    } else {
      const den = 1 / (va + vb + vc);
      const v = vb * den, w = vc * den;
      qx = ax + abx * v + acx * w; qy = ay + aby * v + acy * w; qz = az + abz * v + acz * w;
    }
  }
  const dx = p[0] - qx, dy = p[1] - qy, dz = p[2] - qz;
  return dx * dx + dy * dy + dz * dz;
}

// ---- 충돌 메시 → 삼각형 ------------------------------------------------------

/**
 * 칠 가능 재질 판정 [추정]. 원본은 ColPaintBuilder 가 정하고(미판독), 도색 요청 단계에서
 * 접촉 재질 플래그 (+0xb) & 0x60 이면 칠하지 않는다(paint_shape.md §7.2, 플래그 ↔ 이름 대응 미확정).
 * 이름 근거: collision_mesh.md §3.4·§4 (ForceColPaint* 태그, Water, Fence/RopeNet = SplInkThrough,
 * KeepOut/FillUp = SplKeepOutPlayer 플레이어 전용 벽, PlayerDead = 장외).
 */
export function isPaintableMaterial(name: string, tags: readonly string[], layerHitMask?: number): boolean {
  const has = (t: string) => tags.includes(t);
  if (has("ForceColPaintNotPaintable")) return false;
  if (has("ForceColPaintPaintable")) return true;
  if (name === "Water" || has("Water")) return false;
  if (name === "Fence" || name === "RopeNet" || has("Fence")) return false;
  if (layerHitMask !== undefined && (layerHitMask === 0x62 || layerHitMask === 0xe2 || layerHitMask === 0x1f0cbc7e || layerHitMask === 0x1bffffc6))
    return false;
  if (has("KeepOut") || has("FillUp") || has("PlayerDead")) return false;
  return true;
}

type Num = ArrayLike<number>;

/** LayerHitMaskEntity 이름 → 값 (collision_mesh.md §3.4 표, PhiveConfig MaskValue) [데이터] */
const LAYER_NAMES: Record<string, number> = {
  SplSolidGround: 0x1ffffffe,
  SplKeepOutPlayer: 0x62,
  SplKeepOutPlayerAndCamera: 0xe2,
  SplPlayerThrough: 0x1fffff9e,
  SplInkThrough: 0x1f0cbc7e,
  SplWater: 0x1bffffc6,
};

/**
 * 충돌 메시를 읽는다. 순서: ① world.collision 이 physics 의 MeshCollisionWorld 형태(mesh.pos/idx/mat + materials)면
 * 그것(physics 가 에셋 없이 만든 대체 평면이면 ③), ② world.data.collision {meta, bin} 의 흔한 형식,
 * ③ 평면 placeholder(y=0, 160×160 — physics 대체 평면과 같은 높이).
 */
export function readCollisionTriangles(w: World): RawTriangles {
  const cw = w.collision as unknown as
    | { fallback?: boolean; mesh?: { pos?: Num; idx?: Num; mat?: Num }; materials?: unknown[] }
    | null;
  if (cw && cw.fallback) return placeholderPlane();
  if (cw && cw.mesh && cw.mesh.pos && cw.mesh.idx) {
    // 재질은 원본 쪽 정보(태그·필터)가 더 많은 에셋 collision.json materials 를 먼저 쓴다(physics 와 같은 순서·인덱스)
    const meta = (w.data.collision as { meta?: { materials?: unknown } } | null)?.meta;
    const mats = Array.isArray(meta?.materials) ? (meta.materials as unknown[]) : (cw.materials ?? null);
    const r = buildRaw(cw.mesh.pos, cw.mesh.idx, cw.mesh.mat ?? null, mats, w, "collision");
    if (r) return r;
  }
  const fromWorld = tryMesh(w.collision as unknown, null, w);
  if (fromWorld) return fromWorld;
  const data = w.data.collision as { meta?: unknown; bin?: ArrayBuffer | null } | null;
  if (data && typeof data === "object") {
    const m = tryMesh(data.meta ?? data, data.bin ?? null, w);
    if (m) return m;
  }
  return placeholderPlane();
}

export function placeholderPlane(half = 80, tile = 10): RawTriangles {
  const n = Math.round((half * 2) / tile);
  const tri = new Float64Array(n * n * 2 * 9);
  let k = 0;
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) {
      const x0 = -half + i * tile, x1 = x0 + tile, z0 = -half + j * tile, z1 = z0 + tile;
      tri.set([x0, 0, z0, x0, 0, z1, x1, 0, z1], k);
      tri.set([x0, 0, z0, x1, 0, z1, x1, 0, z0], k + 9);
      k += 18;
    }
  const nt = n * n * 2;
  return { tri, material: new Int32Array(nt).fill(-1), paintable: new Uint8Array(nt).fill(1), source: "placeholder" };
}

function tryMesh(src: unknown, bin: ArrayBuffer | null, w: World): RawTriangles | null {
  if (!src || typeof src !== "object") return null;
  const o = src as Record<string, unknown>;
  for (const k of ["mesh", "triangles", "terrain", "layout"]) {
    const v = o[k];
    if (typeof v === "function") {
      try {
        const r = tryMesh((v as () => unknown).call(src), bin, w);
        if (r) return r;
      } catch {
        /* 다음 후보 */
      }
    } else if (v && typeof v === "object" && !ArrayBuffer.isView(v) && !Array.isArray(v)) {
      const r = tryMesh(v, bin, w);
      if (r) return r;
    }
  }
  const pos = arr(o, ["positions", "position", "vertices", "verts", "pos"], bin, "f32");
  if (!pos || pos.length < 9) return null;
  const idx = arr(o, ["indices", "index", "faces", "idx"], bin, "u32");
  const triMat = arr(o, ["triMaterial", "triMaterials", "shapeTags", "tags", "materialIndex", "triTags", "mat"], bin, "u16");
  const mats = (o.materials ?? o.materialTable ?? o.shapeTagTable) as unknown;
  return buildRaw(pos, idx, triMat, Array.isArray(mats) ? mats : null, w, "collision");
}

function buildRaw(pos: Num, idx: Num | null, triMat: Num | null, mats: unknown[] | null, w: World, source: string): RawTriangles | null {
  if (pos.length < 9) return null;
  const nt = idx ? Math.floor(idx.length / 3) : Math.floor(pos.length / 9);
  const tri = new Float64Array(nt * 9);
  for (let i = 0; i < nt; i++)
    for (let c = 0; c < 3; c++) {
      const v = idx ? idx[i * 3 + c] : i * 3 + c;
      tri[i * 9 + c * 3] = pos[v * 3];
      tri[i * 9 + c * 3 + 1] = pos[v * 3 + 1];
      tri[i * 9 + c * 3 + 2] = pos[v * 3 + 2];
    }
  const material = new Int32Array(nt).fill(-1);
  if (triMat && triMat.length >= nt) for (let i = 0; i < nt; i++) material[i] = triMat[i];
  const paintable = new Uint8Array(nt);
  const cache = new Map<number, boolean>();
  for (let i = 0; i < nt; i++) {
    const m = material[i];
    let p = cache.get(m);
    if (p === undefined) {
      p = materialPaintable(m, mats, w);
      cache.set(m, p);
    }
    paintable[i] = p ? 1 : 0;
  }
  return { tri, material, paintable, source };
}

function materialPaintable(m: number, mats: unknown, w: World): boolean {
  if (m < 0) return true;
  let name = "";
  let tags: string[] = [];
  let layer: number | undefined;
  const e = Array.isArray(mats) ? (mats[m] as Record<string, unknown> | undefined) : undefined;
  if (e && typeof e === "object") {
    if (e.paintable === false) return false;
    name = String(e.name ?? e.material ?? "");
    const fl = (e.flags ?? {}) as Record<string, unknown>;
    const t = e.userShapeTags ?? e.tags ?? fl.userShapeTags ?? [];
    tags = Array.isArray(t) ? t.map(String) : [];
    const f = e.filter as Record<string, unknown> | undefined;
    const lm = f?.layerHitMask ?? e.layerHitMask ?? fl.layerHitMask ?? e.hitMask;
    if (typeof lm === "number") layer = lm;
    else if (typeof lm === "string") layer = LAYER_NAMES[lm] ?? (/^0x[0-9a-f]+$/i.test(lm) ? parseInt(lm, 16) : undefined);
  } else if (w.collision) {
    try {
      name = w.collision.materialName(m);
    } catch {
      name = "";
    }
    tags = name.split(/[|,+ ]+/).filter(Boolean);
  }
  return isPaintableMaterial(name, tags, layer);
}

function arr(o: Record<string, unknown>, keys: string[], bin: ArrayBuffer | null, kind: "f32" | "u32" | "u16"): Num | null {
  for (const k of keys) {
    const v = o[k];
    if (!v) continue;
    if (Array.isArray(v) || ArrayBuffer.isView(v)) return v as unknown as Num;
    if (typeof v === "object" && bin) {
      const d = v as Record<string, unknown>;
      const off = Number(d.byteOffset ?? d.offset ?? 0);
      const type = String(d.type ?? d.componentType ?? kind);
      const size = /f32|float|u32|uint32|VEC3/i.test(type) || kind !== "u16" ? 4 : 2;
      const bytes = /u16|uint16|ushort/i.test(type) ? 2 : /u8|uint8/i.test(type) ? 1 : size;
      // glTF accessor 규약: positions count = 정점 수(×3), indices = 인덱스 수, triMaterial = 삼각형 수. byteLength 우선.
      const n = d.byteLength !== undefined ? Number(d.byteLength) / bytes : Number(d.count ?? d.length ?? 0) * (kind === "f32" ? 3 : 1);
      if (!(n > 0)) continue;
      if (kind === "f32") return new Float32Array(bin.slice(off, off + n * 4));
      if (bytes === 2) return new Uint16Array(bin.slice(off, off + n * 2));
      if (bytes === 1) return new Uint8Array(bin.slice(off, off + n));
      return new Uint32Array(bin.slice(off, off + n * 4));
    }
  }
  return null;
}
