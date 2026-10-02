// 담당: [physics] — 삼각형 메시 + BVH. 원본 hknpMeshShape 의 섹션 BVH 는 쓰지 않고 새로 만든다
// (docs/gimmick/collision_mesh.md §3.3 "웹은 BVH를 새로 만들면 됩니다").
import { closestSegmentTriangle, rayTriangle, type Closest } from "./geom.ts";

const LEAF = 4;

export interface SweepResult {
  /** 이동 비율 0..1 */
  t: number;
  /** 접촉 법선(삼각형 → 형상 쪽, 정규화) */
  nx: number;
  ny: number;
  nz: number;
  /** 삼각형 위 접촉점 */
  px: number;
  py: number;
  pz: number;
  tri: number;
}

export interface Penetration {
  tri: number;
  /** 밀어낼 방향(정규화)과 깊이 */
  nx: number;
  ny: number;
  nz: number;
  depth: number;
  px: number;
  py: number;
  pz: number;
}

export type TriFilter = (tri: number) => boolean;

export class TriMesh {
  readonly pos: Float32Array;
  readonly idx: Uint32Array;
  readonly mat: Uint16Array;
  readonly triCount: number;
  /** 노드: min xyz, max xyz */
  private nb: Float64Array;
  /** 노드: 왼쪽 자식(내부) 또는 -(시작+1)(잎), 오른쪽 자식 또는 개수 */
  private nl: Int32Array;
  private nr: Int32Array;
  private order: Uint32Array;
  private nodeCount = 0;
  readonly min = [0, 0, 0];
  readonly max = [0, 0, 0];

  constructor(pos: Float32Array, idx: Uint32Array, mat: Uint16Array) {
    this.pos = pos;
    this.idx = idx;
    this.mat = mat;
    this.triCount = Math.floor(idx.length / 3);
    const n = this.triCount;
    const cap = Math.max(1, 2 * Math.ceil(n / LEAF) * 2);
    this.nb = new Float64Array(cap * 6);
    this.nl = new Int32Array(cap);
    this.nr = new Int32Array(cap);
    this.order = new Uint32Array(n);
    for (let i = 0; i < n; i++) this.order[i] = i;
    const cen = new Float64Array(n * 3);
    const tb = new Float64Array(n * 6);
    for (let i = 0; i < n; i++) {
      let mnx = Infinity, mny = Infinity, mnz = Infinity, mxx = -Infinity, mxy = -Infinity, mxz = -Infinity;
      for (let k = 0; k < 3; k++) {
        const v = idx[i * 3 + k] * 3;
        const x = pos[v], y = pos[v + 1], z = pos[v + 2];
        if (x < mnx) mnx = x; if (y < mny) mny = y; if (z < mnz) mnz = z;
        if (x > mxx) mxx = x; if (y > mxy) mxy = y; if (z > mxz) mxz = z;
      }
      tb[i * 6] = mnx; tb[i * 6 + 1] = mny; tb[i * 6 + 2] = mnz;
      tb[i * 6 + 3] = mxx; tb[i * 6 + 4] = mxy; tb[i * 6 + 5] = mxz;
      cen[i * 3] = (mnx + mxx) * 0.5; cen[i * 3 + 1] = (mny + mxy) * 0.5; cen[i * 3 + 2] = (mnz + mxz) * 0.5;
    }
    if (n > 0) this.build(0, n, tb, cen);
    else this.nodeCount = 0;
    if (this.nodeCount > 0) {
      for (let k = 0; k < 3; k++) {
        this.min[k] = this.nb[k];
        this.max[k] = this.nb[3 + k];
      }
    }
  }

  private build(start: number, end: number, tb: Float64Array, cen: Float64Array): number {
    const node = this.nodeCount++;
    if (node >= this.nl.length) this.grow();
    let mnx = Infinity, mny = Infinity, mnz = Infinity, mxx = -Infinity, mxy = -Infinity, mxz = -Infinity;
    let cmnx = Infinity, cmny = Infinity, cmnz = Infinity, cmxx = -Infinity, cmxy = -Infinity, cmxz = -Infinity;
    for (let i = start; i < end; i++) {
      const t = this.order[i];
      const o = t * 6;
      if (tb[o] < mnx) mnx = tb[o]; if (tb[o + 1] < mny) mny = tb[o + 1]; if (tb[o + 2] < mnz) mnz = tb[o + 2];
      if (tb[o + 3] > mxx) mxx = tb[o + 3]; if (tb[o + 4] > mxy) mxy = tb[o + 4]; if (tb[o + 5] > mxz) mxz = tb[o + 5];
      const c = t * 3;
      if (cen[c] < cmnx) cmnx = cen[c]; if (cen[c + 1] < cmny) cmny = cen[c + 1]; if (cen[c + 2] < cmnz) cmnz = cen[c + 2];
      if (cen[c] > cmxx) cmxx = cen[c]; if (cen[c + 1] > cmxy) cmxy = cen[c + 1]; if (cen[c + 2] > cmxz) cmxz = cen[c + 2];
    }
    const b = node * 6;
    this.nb[b] = mnx; this.nb[b + 1] = mny; this.nb[b + 2] = mnz;
    this.nb[b + 3] = mxx; this.nb[b + 4] = mxy; this.nb[b + 5] = mxz;
    const count = end - start;
    const ex = cmxx - cmnx, ey = cmxy - cmny, ez = cmxz - cmnz;
    if (count <= LEAF || (ex <= 0 && ey <= 0 && ez <= 0)) {
      this.nl[node] = -(start + 1);
      this.nr[node] = count;
      return node;
    }
    const axis = ex >= ey && ex >= ez ? 0 : ey >= ez ? 1 : 2;
    const mid = (start + end) >> 1;
    this.nthElement(start, end, mid, axis, cen);
    const l = this.build(start, mid, tb, cen);
    const r = this.build(mid, end, tb, cen);
    this.nl[node] = l;
    this.nr[node] = r;
    return node;
  }

  private grow(): void {
    const cap = this.nl.length * 2;
    const nb = new Float64Array(cap * 6); nb.set(this.nb); this.nb = nb;
    const nl = new Int32Array(cap); nl.set(this.nl); this.nl = nl;
    const nr = new Int32Array(cap); nr.set(this.nr); this.nr = nr;
  }

  /** order[start..end) 를 axis 중심값 기준으로 k 번째가 제자리에 오도록 (quickselect). */
  private nthElement(start: number, end: number, k: number, axis: number, cen: Float64Array): void {
    const o = this.order;
    let lo = start, hi = end - 1;
    while (lo < hi) {
      const pv = cen[o[(lo + hi) >> 1] * 3 + axis];
      let i = lo, j = hi;
      while (i <= j) {
        while (cen[o[i] * 3 + axis] < pv) i++;
        while (cen[o[j] * 3 + axis] > pv) j--;
        if (i <= j) {
          const t = o[i]; o[i] = o[j]; o[j] = t;
          i++; j--;
        }
      }
      if (k <= j) hi = j;
      else if (k >= i) lo = i;
      else break;
    }
  }

  /** AABB 와 겹치는 잎의 삼각형마다 cb. */
  query(mnx: number, mny: number, mnz: number, mxx: number, mxy: number, mxz: number, cb: (tri: number) => void): void {
    if (this.nodeCount === 0) return;
    const stack: number[] = [0];
    const nb = this.nb;
    while (stack.length) {
      const n = stack.pop()!;
      const b = n * 6;
      if (nb[b] > mxx || nb[b + 1] > mxy || nb[b + 2] > mxz || nb[b + 3] < mnx || nb[b + 4] < mny || nb[b + 5] < mnz) continue;
      const l = this.nl[n];
      if (l < 0) {
        const s = -l - 1, c = this.nr[n];
        for (let i = s; i < s + c; i++) cb(this.order[i]);
      } else {
        stack.push(l, this.nr[n]);
      }
    }
  }

  vert(tri: number, k: number, out: number[]): number[] {
    const v = this.idx[tri * 3 + k] * 3;
    out[0] = this.pos[v]; out[1] = this.pos[v + 1]; out[2] = this.pos[v + 2];
    return out;
  }

  /** 레이: 가장 가까운 삼각형. */
  raycast(ox: number, oy: number, oz: number, dx: number, dy: number, dz: number, maxDist: number, filter: TriFilter | null): { t: number; tri: number } | null {
    const ex = ox + dx * maxDist, ey = oy + dy * maxDist, ez = oz + dz * maxDist;
    let best = maxDist, bestTri = -1;
    const p = this.pos, ix = this.idx;
    this.query(Math.min(ox, ex), Math.min(oy, ey), Math.min(oz, ez), Math.max(ox, ex), Math.max(oy, ey), Math.max(oz, ez), (tri) => {
      if (filter && !filter(tri)) return;
      const a = ix[tri * 3] * 3, b = ix[tri * 3 + 1] * 3, c = ix[tri * 3 + 2] * 3;
      const t = rayTriangle(ox, oy, oz, dx, dy, dz, p[a], p[a + 1], p[a + 2], p[b], p[b + 1], p[b + 2], p[c], p[c + 1], p[c + 2]);
      if (t >= 0 && t <= best) {
        if (t < best || tri < bestTri) { best = t; bestTri = tri; }
      }
    });
    return bestTri >= 0 ? { t: best, tri: bestTri } : null;
  }

  /**
   * 선분(a→b, 반경 r) 형상이 motion 만큼 움직일 때 처음 닿는 비율.
   * 보수적 전진(conservative advancement): 선분-삼각형 거리 d 에서 (d − r)/|motion| 만큼씩 전진하므로 뚫고 지나가지 않는다.
   * 처음부터 겹친 삼각형은 운동이 그 삼각형에서 멀어지면 무시, 가까워지면 t = 0 으로 돌려준다.
   */
  sweepSegment(
    ax: number, ay: number, az: number, bx: number, by: number, bz: number, r: number,
    mx: number, my: number, mz: number, filter: TriFilter | null, out: SweepResult,
  ): SweepResult | null {
    const mlen = Math.hypot(mx, my, mz);
    const mnx = Math.min(ax, bx) - r + Math.min(0, mx), mny = Math.min(ay, by) - r + Math.min(0, my), mnz = Math.min(az, bz) - r + Math.min(0, mz);
    const mxx = Math.max(ax, bx) + r + Math.max(0, mx), mxy = Math.max(ay, by) + r + Math.max(0, my), mxz = Math.max(az, bz) + r + Math.max(0, mz);
    let bestT = 2, bestGap = Infinity;
    const p = this.pos, ix = this.idx;
    const c: Closest = CL;
    // 같은 t 면 더 가까운(간격이 작은) 삼각형 — 이웃 삼각형 모서리의 기울어진 법선을 피한다
    const better = (t: number, gap: number, tri: number) =>
      t < bestT - 1e-12 || (t <= bestT + 1e-12 && (gap < bestGap - 1e-12 || (gap <= bestGap + 1e-12 && tri < out.tri)));
    this.query(mnx, mny, mnz, mxx, mxy, mxz, (tri) => {
      if (filter && !filter(tri)) return;
      const ia = ix[tri * 3] * 3, ib = ix[tri * 3 + 1] * 3, ic = ix[tri * 3 + 2] * 3;
      const t0x = p[ia], t0y = p[ia + 1], t0z = p[ia + 2];
      const t1x = p[ib], t1y = p[ib + 1], t1z = p[ib + 2];
      const t2x = p[ic], t2y = p[ic + 1], t2z = p[ic + 2];
      let t = 0;
      for (let it = 0; it < 64; it++) {
        const ox = mx * t, oy = my * t, oz = mz * t;
        closestSegmentTriangle(ax + ox, ay + oy, az + oz, bx + ox, by + oy, bz + oz, t0x, t0y, t0z, t1x, t1y, t1z, t2x, t2y, t2z, c);
        const d = Math.sqrt(c.d2);
        const gap = d - r;
        if (gap <= SWEEP_EPS) {
          let nx = c.px - c.tx, ny = c.py - c.ty, nz = c.pz - c.tz;
          let nl = Math.hypot(nx, ny, nz);
          if (nl < 1e-9) {
            // 선분이 면을 뚫은 상태: 면 법선(운동 반대쪽)
            const e1x = t1x - t0x, e1y = t1y - t0y, e1z = t1z - t0z, e2x = t2x - t0x, e2y = t2y - t0y, e2z = t2z - t0z;
            nx = e1y * e2z - e1z * e2y; ny = e1z * e2x - e1x * e2z; nz = e1x * e2y - e1y * e2x;
            nl = Math.hypot(nx, ny, nz) || 1;
            if ((nx * mx + ny * my + nz * mz) > 0) nl = -nl;
          }
          nx /= nl; ny /= nl; nz /= nl;
          // 이미 겹친 상태에서 멀어지는 운동이면 무시
          if (nx * mx + ny * my + nz * mz >= 0) return;
          if (better(t, gap, tri)) {
            bestT = t;
            bestGap = gap;
            out.t = t; out.nx = nx; out.ny = ny; out.nz = nz;
            out.px = c.tx; out.py = c.ty; out.pz = c.tz; out.tri = tri;
          }
          return;
        }
        if (mlen <= 0) return;
        t += gap / mlen;
        if (t > 1 || t > bestT + 1e-12) return;
      }
      // 수렴하지 않으면(스치는 운동) 현재 t 를 보수적 접촉으로 쓴다
      const gapEnd = Math.sqrt(c.d2) - r;
      if (t <= 1 && better(t, gapEnd, tri)) {
        let nx = c.px - c.tx, ny = c.py - c.ty, nz = c.pz - c.tz;
        const nl = Math.hypot(nx, ny, nz) || 1;
        nx /= nl; ny /= nl; nz /= nl;
        if (nx * mx + ny * my + nz * mz >= 0) return;
        bestT = t;
        bestGap = gapEnd;
        out.t = t; out.nx = nx; out.ny = ny; out.nz = nz;
        out.px = c.tx; out.py = c.ty; out.pz = c.tz; out.tri = tri;
      }
    });
    return bestT <= 1 ? out : null;
  }

  /** 선분 형상과 겹친 삼각형들(깊이 > 0). */
  overlapSegment(ax: number, ay: number, az: number, bx: number, by: number, bz: number, r: number, filter: TriFilter | null, out: Penetration[]): Penetration[] {
    out.length = 0;
    const p = this.pos, ix = this.idx;
    const c = CL;
    this.query(Math.min(ax, bx) - r, Math.min(ay, by) - r, Math.min(az, bz) - r, Math.max(ax, bx) + r, Math.max(ay, by) + r, Math.max(az, bz) + r, (tri) => {
      if (filter && !filter(tri)) return;
      const ia = ix[tri * 3] * 3, ib = ix[tri * 3 + 1] * 3, ic = ix[tri * 3 + 2] * 3;
      closestSegmentTriangle(ax, ay, az, bx, by, bz, p[ia], p[ia + 1], p[ia + 2], p[ib], p[ib + 1], p[ib + 2], p[ic], p[ic + 1], p[ic + 2], c);
      if (c.d2 >= r * r) return;
      const d = Math.sqrt(c.d2);
      let nx = c.px - c.tx, ny = c.py - c.ty, nz = c.pz - c.tz;
      let nl = d;
      if (nl < 1e-9) {
        const e1x = p[ib] - p[ia], e1y = p[ib + 1] - p[ia + 1], e1z = p[ib + 2] - p[ia + 2];
        const e2x = p[ic] - p[ia], e2y = p[ic + 1] - p[ia + 1], e2z = p[ic + 2] - p[ia + 2];
        nx = e1y * e2z - e1z * e2y; ny = e1z * e2x - e1x * e2z; nz = e1x * e2y - e1y * e2x;
        nl = Math.hypot(nx, ny, nz) || 1;
      }
      out.push({ tri, nx: nx / nl, ny: ny / nl, nz: nz / nl, depth: r - d, px: c.tx, py: c.ty, pz: c.tz });
    });
    out.sort((a, b) => b.depth - a.depth || a.tri - b.tri);
    return out;
  }
}

const SWEEP_EPS = 1e-4;
const CL: Closest = { d2: 0, tx: 0, ty: 0, tz: 0, px: 0, py: 0, pz: 0 };
