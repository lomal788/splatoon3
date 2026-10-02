// 담당: [physics] — 삼각형 기하 질의(최근접점·레이·쓸어 넘기기). 원본은 Phive(hknp) 엔진 내부라
// 같은 결과를 내는 일반 기하로 대체한다(근사 방식은 docs/impl/physics.md "원본과 다른 점").
// 충돌 계산은 f64(JS number)로 한다. 결정성은 같은 입력 → 같은 출력으로 유지된다.

/** 3성분 배열(읽기 전용 접근만 한다). */
export type V3 = ArrayLike<number>;

export interface Closest {
  /** 거리 제곱 */
  d2: number;
  /** 삼각형 위 최근접점 */
  tx: number;
  ty: number;
  tz: number;
  /** 다른 쪽(점·선분) 위 최근접점 */
  px: number;
  py: number;
  pz: number;
}

/** 점 p 와 삼각형(a,b,c)의 최근접점 (Ericson, Real-Time Collision Detection 5.1.5 의 영역 판정). */
export function closestPointTriangle(
  px: number, py: number, pz: number,
  ax: number, ay: number, az: number,
  bx: number, by: number, bz: number,
  cx: number, cy: number, cz: number,
  out: Closest,
): Closest {
  const abx = bx - ax, aby = by - ay, abz = bz - az;
  const acx = cx - ax, acy = cy - ay, acz = cz - az;
  const apx = px - ax, apy = py - ay, apz = pz - az;
  const d1 = abx * apx + aby * apy + abz * apz;
  const d2 = acx * apx + acy * apy + acz * apz;
  let rx: number, ry: number, rz: number;
  if (d1 <= 0 && d2 <= 0) {
    rx = ax; ry = ay; rz = az;
  } else {
    const bpx = px - bx, bpy = py - by, bpz = pz - bz;
    const d3 = abx * bpx + aby * bpy + abz * bpz;
    const d4 = acx * bpx + acy * bpy + acz * bpz;
    if (d3 >= 0 && d4 <= d3) {
      rx = bx; ry = by; rz = bz;
    } else {
      const vc = d1 * d4 - d3 * d2;
      if (vc <= 0 && d1 >= 0 && d3 <= 0) {
        const v = d1 / (d1 - d3);
        rx = ax + abx * v; ry = ay + aby * v; rz = az + abz * v;
      } else {
        const cpx = px - cx, cpy = py - cy, cpz = pz - cz;
        const d5 = abx * cpx + aby * cpy + abz * cpz;
        const d6 = acx * cpx + acy * cpy + acz * cpz;
        if (d6 >= 0 && d5 <= d6) {
          rx = cx; ry = cy; rz = cz;
        } else {
          const vb = d5 * d2 - d1 * d6;
          if (vb <= 0 && d2 >= 0 && d6 <= 0) {
            const w = d2 / (d2 - d6);
            rx = ax + acx * w; ry = ay + acy * w; rz = az + acz * w;
          } else {
            const va = d3 * d6 - d5 * d4;
            if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) {
              const w = (d4 - d3) / (d4 - d3 + (d5 - d6));
              rx = bx + (cx - bx) * w; ry = by + (cy - by) * w; rz = bz + (cz - bz) * w;
            } else {
              const denom = 1 / (va + vb + vc);
              const v = vb * denom, w = vc * denom;
              rx = ax + abx * v + acx * w; ry = ay + aby * v + acy * w; rz = az + abz * v + acz * w;
            }
          }
        }
      }
    }
  }
  const dx = px - rx, dy = py - ry, dz = pz - rz;
  out.d2 = dx * dx + dy * dy + dz * dz;
  out.tx = rx; out.ty = ry; out.tz = rz;
  out.px = px; out.py = py; out.pz = pz;
  return out;
}

const tmpA: Closest = { d2: 0, tx: 0, ty: 0, tz: 0, px: 0, py: 0, pz: 0 };

/** 두 선분 (p1,q1), (p2,q2) 의 최근접점 거리 제곱. s,t 결과는 out 에. */
function segSeg(
  p1x: number, p1y: number, p1z: number, q1x: number, q1y: number, q1z: number,
  p2x: number, p2y: number, p2z: number, q2x: number, q2y: number, q2z: number,
  out: Closest,
): number {
  const d1x = q1x - p1x, d1y = q1y - p1y, d1z = q1z - p1z;
  const d2x = q2x - p2x, d2y = q2y - p2y, d2z = q2z - p2z;
  const rx = p1x - p2x, ry = p1y - p2y, rz = p1z - p2z;
  const a = d1x * d1x + d1y * d1y + d1z * d1z;
  const e = d2x * d2x + d2y * d2y + d2z * d2z;
  const f = d2x * rx + d2y * ry + d2z * rz;
  let s: number, t: number;
  const EPS = 1e-12;
  if (a <= EPS && e <= EPS) {
    s = 0; t = 0;
  } else if (a <= EPS) {
    s = 0; t = clamp01(f / e);
  } else {
    const c = d1x * rx + d1y * ry + d1z * rz;
    if (e <= EPS) {
      t = 0; s = clamp01(-c / a);
    } else {
      const b = d1x * d2x + d1y * d2y + d1z * d2z;
      const denom = a * e - b * b;
      s = denom !== 0 ? clamp01((b * f - c * e) / denom) : 0;
      t = (b * s + f) / e;
      if (t < 0) { t = 0; s = clamp01(-c / a); } else if (t > 1) { t = 1; s = clamp01((b - c) / a); }
    }
  }
  const c1x = p1x + d1x * s, c1y = p1y + d1y * s, c1z = p1z + d1z * s;
  const c2x = p2x + d2x * t, c2y = p2y + d2y * t, c2z = p2z + d2z * t;
  out.px = c1x; out.py = c1y; out.pz = c1z;
  out.tx = c2x; out.ty = c2y; out.tz = c2z;
  const dx = c1x - c2x, dy = c1y - c2y, dz = c1z - c2z;
  out.d2 = dx * dx + dy * dy + dz * dz;
  return out.d2;
}

function clamp01(x: number): number {
  return x < 0 ? 0 : x > 1 ? 1 : x;
}

const tmpB: Closest = { d2: 0, tx: 0, ty: 0, tz: 0, px: 0, py: 0, pz: 0 };

/** 선분 (p,q) 와 삼각형의 최근접점. 교차하면 d2 = 0. */
export function closestSegmentTriangle(
  px: number, py: number, pz: number, qx: number, qy: number, qz: number,
  ax: number, ay: number, az: number,
  bx: number, by: number, bz: number,
  cx: number, cy: number, cz: number,
  out: Closest,
): Closest {
  // 선분이 삼각형 면을 뚫는지
  const e1x = bx - ax, e1y = by - ay, e1z = bz - az;
  const e2x = cx - ax, e2y = cy - ay, e2z = cz - az;
  const nx = e1y * e2z - e1z * e2y, ny = e1z * e2x - e1x * e2z, nz = e1x * e2y - e1y * e2x;
  const dp = (px - ax) * nx + (py - ay) * ny + (pz - az) * nz;
  const dq = (qx - ax) * nx + (qy - ay) * ny + (qz - az) * nz;
  if ((dp <= 0 && dq >= 0) || (dp >= 0 && dq <= 0)) {
    const den = dp - dq;
    if (den !== 0) {
      const t = dp / den;
      const ix = px + (qx - px) * t, iy = py + (qy - py) * t, iz = pz + (qz - pz) * t;
      closestPointTriangle(ix, iy, iz, ax, ay, az, bx, by, bz, cx, cy, cz, tmpA);
      if (tmpA.d2 <= 1e-14) {
        out.d2 = 0;
        out.px = out.tx = ix; out.py = out.ty = iy; out.pz = out.tz = iz;
        return out;
      }
    }
  }
  let best = Infinity;
  closestPointTriangle(px, py, pz, ax, ay, az, bx, by, bz, cx, cy, cz, tmpA);
  if (tmpA.d2 < best) { best = tmpA.d2; copyC(out, tmpA); }
  closestPointTriangle(qx, qy, qz, ax, ay, az, bx, by, bz, cx, cy, cz, tmpA);
  if (tmpA.d2 < best) { best = tmpA.d2; copyC(out, tmpA); }
  segSeg(px, py, pz, qx, qy, qz, ax, ay, az, bx, by, bz, tmpB);
  if (tmpB.d2 < best) { best = tmpB.d2; copyC(out, tmpB); }
  segSeg(px, py, pz, qx, qy, qz, bx, by, bz, cx, cy, cz, tmpB);
  if (tmpB.d2 < best) { best = tmpB.d2; copyC(out, tmpB); }
  segSeg(px, py, pz, qx, qy, qz, cx, cy, cz, ax, ay, az, tmpB);
  if (tmpB.d2 < best) { best = tmpB.d2; copyC(out, tmpB); }
  return out;
}

function copyC(o: Closest, s: Closest): void {
  o.d2 = s.d2;
  o.tx = s.tx; o.ty = s.ty; o.tz = s.tz;
  o.px = s.px; o.py = s.py; o.pz = s.pz;
}

/** 레이-삼각형(Möller–Trumbore, 양면). 맞으면 거리, 아니면 -1. */
export function rayTriangle(
  ox: number, oy: number, oz: number, dx: number, dy: number, dz: number,
  ax: number, ay: number, az: number,
  bx: number, by: number, bz: number,
  cx: number, cy: number, cz: number,
): number {
  const e1x = bx - ax, e1y = by - ay, e1z = bz - az;
  const e2x = cx - ax, e2y = cy - ay, e2z = cz - az;
  const px = dy * e2z - dz * e2y, py = dz * e2x - dx * e2z, pz = dx * e2y - dy * e2x;
  const det = e1x * px + e1y * py + e1z * pz;
  if (det > -1e-12 && det < 1e-12) return -1;
  const inv = 1 / det;
  const tx = ox - ax, ty = oy - ay, tz = oz - az;
  const u = (tx * px + ty * py + tz * pz) * inv;
  if (u < 0 || u > 1) return -1;
  const qx = ty * e1z - tz * e1y, qy = tz * e1x - tx * e1z, qz = tx * e1y - ty * e1x;
  const v = (dx * qx + dy * qy + dz * qz) * inv;
  if (v < 0 || u + v > 1) return -1;
  const t = (e2x * qx + e2y * qy + e2z * qz) * inv;
  return t >= 0 ? t : -1;
}

/** 삼각형 면 법선(정규화). */
export function triNormal(
  ax: number, ay: number, az: number,
  bx: number, by: number, bz: number,
  cx: number, cy: number, cz: number,
  out: number[],
): number[] {
  const e1x = bx - ax, e1y = by - ay, e1z = bz - az;
  const e2x = cx - ax, e2y = cy - ay, e2z = cz - az;
  let nx = e1y * e2z - e1z * e2y, ny = e1z * e2x - e1x * e2z, nz = e1x * e2y - e1y * e2x;
  const l = Math.hypot(nx, ny, nz);
  if (l > 0) { nx /= l; ny /= l; nz /= l; }
  out[0] = nx; out[1] = ny; out[2] = nz;
  return out;
}
