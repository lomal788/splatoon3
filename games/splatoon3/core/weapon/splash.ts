// 스플래시 탄 생성 일정(슬롯15 0x710174efc0)·이동 후 처리(슬롯56 0x71017512bc → 0x7101751304)·스플래시 하나 생성(0x71017540ec)·
// 기준 축(0x71012500d4). asm 연산 순서 그대로 — web/tools/weapon_splash_sim.py(원본 에뮬 weapon_splash_emu.py 와 비트 일치)와 같은 식.
import { f32 } from "../fmath.ts";
import { SeadRandom } from "../rng.ts";
import type { Bullet, SpawnInfo } from "./bullet.ts";
import type { V3 } from "./move.ts";
import type { SplashSpawnParam } from "./params.ts";
import { permAt } from "./spawn.ts";

const U32 = new Uint32Array(1);
const F32 = new Float32Array(U32.buffer);
const fromBits = (b: number): number => ((U32[0] = b >>> 0), F32[0]);
const TWO_PI = fromBits(0x40c90fdb);
const EPS_H = fromBits(0x38d1b717);
const EPS_D2 = fromBits(0x322bcc76);

function len3(x: number, y: number, z: number): number {
  return f32(Math.sqrt(f32(f32(f32(x * x) + f32(y * y)) + f32(z * z))));
}

function splitOf(sp: SplashSpawnParam): number {
  return (sp.SplitNum | 0) === 0 ? 1 : sp.SplitNum | 0;
}

/** 0x710174fe94 */
export function nearestLength(sp: SplashSpawnParam, split: number): number {
  const n = f32(sp.SpawnNearestLength);
  return n > 0 ? n : f32(f32(sp.SpawnBetweenLength) / f32(split));
}

/** 탄 쪽 스플래시 상태(ShooterBase 필드) */
export interface SplashState {
  /** +0x11f4 누적 시작값 */
  acc: number;
  /** +0x11f8 */
  f8: number;
  /** +0x11fc 남은 생성 수 */
  left: number;
  /** +0x1208 가까운 지점 누적 */
  near: number;
  /** +0x11ed isLast, +0x11ee forced */
  isLast: boolean;
  forced: boolean;
}

/** 슬롯15 스플래시 일정 부분. 탄별 난수 seed = 탄관리자+0x120 + 생성정보+0x64. 반환 +0x120c(rand·2π). */
export function scheduleSplash(b: Bullet, sp: SplashSpawnParam | null, seedBase: number): void {
  if (!sp) return;
  const split = splitOf(sp);
  const idx = b.info.split & 0xff;
  const rng = new SeadRandom((seedBase + b.info.frame) >>> 0);
  const between = f32(f32(sp.SpawnBetweenLength) / f32(split));
  const near = nearestLength(sp, split);
  const bmn = f32(between - near);
  const s11 = f32(split - 1);
  const isLast = split - 1 === idx;
  let forced = false;
  for (const v of sp.ForceSpawnNearestAddNumArray ?? []) {
    if (v < 1) continue;
    const r = v - Math.trunc(v / split) * split;
    if (permAt(split, r) === idx) {
      forced = true;
      break;
    }
  }
  const st = b.splash;
  st.isLast = isLast;
  st.forced = forced;
  st.near = 0;
  if (forced) {
    const r1 = rng.float01();
    st.near = f32(bmn + f32(f32(between * s11) + f32(r1 * near)));
  }
  const r2 = rng.float01();
  const s0 = f32((isLast ? near : between) * r2);
  st.f8 = isLast || forced ? f32(s0 / near) : 0;
  st.acc = f32(bmn + f32(f32(between * f32(idx)) + s0));
  const num = f32(sp.SpawnNum);
  let n = Math.trunc(num);
  if (num < 0 && f32(n) !== num) n -= 1;
  const cond = f32(s11 - f32(f32(f32(num - f32(n)) * f32(split)) + -1)) <= f32(idx);
  st.left = n + (cond ? 1 : 0);
  const r3 = rng.float01();
  b.randAngle = f32(r3 * TWO_PI);
}

/** 0x71012500d4: c = normalize(fwd), a = normalize(up × c), b = c × a */
function frameVec(fwd: V3, up: V3): [V3, V3, V3] {
  let cx = fwd[0], cy = fwd[1], cz = fwd[2];
  const lc = len3(cx, cy, cz);
  if (lc > 0) {
    const k = f32(1 / lc);
    cx = f32(k * cx); cy = f32(k * cy); cz = f32(k * cz);
  }
  const bx = up[0], by = up[1], bz = up[2];
  let ax = f32(f32(cz * by) - f32(cy * bz));
  let ay = f32(f32(cx * bz) - f32(cz * bx));
  let az = f32(f32(cy * bx) - f32(cx * by));
  const la = f32(Math.sqrt(f32(f32(az * az) + f32(f32(ax * ax) + f32(ay * ay)))));
  if (la > 0) {
    const k = f32(1 / la);
    ax = f32(k * ax); ay = f32(k * ay); az = f32(k * az);
  }
  const nbx = f32(f32(az * cy) - f32(ay * cz));
  const nby = f32(f32(ax * cz) - f32(az * cx));
  const nbz = f32(f32(ay * cx) - f32(ax * cy));
  return [[ax, ay, az], [nbx, nby, nbz], [cx, cy, cz]];
}

function scaleTo(v: V3, val: number): V3 {
  const l = len3(v[0], v[1], v[2]);
  if (l > 0) {
    const k = f32(val / l);
    return [f32(k * v[0]), f32(k * v[1]), f32(k * v[2])];
  }
  return v;
}

/** 0x71017540ec(bullet, acc, h, isNearest) → 자식 생성정보 */
export function spawnOne(b: Bullet, sp: SplashSpawnParam, acc: number, h: number, isNearest: boolean, seedBase: number): SpawnInfo {
  const sbl = f32(sp.SpawnBetweenLength);
  const prev = b.prevPos, pos = b.body.pos;
  let sx: number, sy: number, sz: number;
  if ((h < 0 ? f32(-h) : h) >= EPS_H) {
    const f = f32(1 - f32(f32(acc - sbl) / h));
    sx = f32(prev[0] + f32(f * f32(pos[0] - prev[0])));
    sy = f32(prev[1] + f32(f * f32(pos[1] - prev[1])));
    sz = f32(prev[2] + f32(f * f32(pos[2] - prev[2])));
  } else {
    sx = prev[0]; sy = prev[1]; sz = prev[2];
  }
  const rng = new SeadRandom((seedBase + b.info.frame + b.splash.left) >>> 0);
  const X = f32(sp.RandomSpawnVelXMax), Y = f32(sp.RandomSpawnVelYMax);
  const zmin = f32(sp.RandomSpawnVelZMin), zmax = f32(sp.RandomSpawnVelZMax);
  let dx = f32(pos[0] - prev[0]), dy = f32(pos[1] - prev[1]), dz = f32(pos[2] - prev[2]);
  const d2 = f32(f32(f32(dx * dx) + f32(dy * dy)) + f32(dz * dz));
  let hz2: number;
  if (d2 < EPS_D2) {
    const s = dy > 0 ? 1 : -1;
    const z0 = f32(s * 0);
    dx = z0; dy = s; dz = z0;
    hz2 = f32(f32(z0 * z0) + f32(z0 * z0));
  } else hz2 = f32(f32(dz * dz) + f32(dx * dx));
  const up: V3 = hz2 >= EPS_D2 ? [0, 1, 0] : [1, 0, 0];
  let [side, upv, fwd] = frameVec([dx, dy, dz], up);
  let vx: number;
  if (X >= f32(-X)) vx = f32(f32(rng.float01() * f32(X + X)) - X);
  else vx = f32(-X);
  side = scaleTo(side, vx);
  let vy: number;
  if (Y >= f32(-Y)) vy = f32(f32(f32(Y + Y) * rng.float01()) - Y);
  else vy = f32(-Y);
  upv = scaleTo(upv, vy);
  let vz: number;
  if (zmax >= zmin) vz = f32(zmin + f32(f32(zmax - zmin) * rng.float01()));
  else vz = zmin;
  fwd = scaleTo(fwd, vz);
  const sum: V3 = [f32(fwd[0] + f32(side[0] + upv[0])), f32(fwd[1] + f32(side[1] + upv[1])), f32(fwd[2] + f32(side[2] + upv[2]))];
  const spd = len3(sum[0], sum[1], sum[2]);
  let dir: V3 = sum;
  if (spd > 0) {
    const k = f32(1 / spd);
    dir = [f32(sum[0] * k), f32(sum[1] * k), f32(sum[2] * k)];
  }
  const info = b.info;
  return {
    kind: "Splash", owner: info.owner, team: info.team, weapon: info.weapon, pos: [sx, sy, sz], dir, speed: spd, extraSpeed: 0,
    frame: info.frame, split: isNearest ? 1 : 0, angle: 0, local: info.local, paintDir: [b.vel[0], b.vel[2]],
  };
}

/** 슬롯56(ShooterBase): 최고 높이·이동 거리·스플래시 생성. spawn 이 null 이면 생성 없이 거리만. */
export function splashOnMove(b: Bullet, sp: SplashSpawnParam | null, seedBase: number, spawn: ((info: SpawnInfo) => void) | null): void {
  const pos = b.body.pos, prev = b.prevPos, vel = b.vel;
  if (b.sm.state !== 0) b.maxY = b.maxY > pos[1] ? b.maxY : pos[1];
  const dx = f32(pos[0] - prev[0]), dy = f32(pos[1] - prev[1]), dz = f32(pos[2] - prev[2]);
  const dot = f32(f32(dz * vel[2]) + f32(f32(dx * vel[0]) + f32(dy * vel[1])));
  if (dot < 0) return;
  if (vel[2] === 0 && vel[0] === 0 && vel[1] === 0) return;
  const dx2 = f32(dx * dx), dz2 = f32(dz * dz);
  b.traveled = f32(f32(Math.sqrt(f32(f32(dx2 + f32(dy * dy)) + dz2))) + b.traveled);
  if (!sp || !spawn) return;
  const h = f32(Math.sqrt(f32(dx2 + dz2)));
  const sbl = f32(sp.SpawnBetweenLength);
  const st = b.splash;
  if (st.left >= 1) {
    st.acc = f32(h + st.acc);
    while (st.acc >= sbl) {
      spawn(spawnOne(b, sp, st.acc, h, st.isLast, seedBase));
      st.acc = f32(st.acc - sbl);
      if (st.isLast) {
        const split = splitOf(sp);
        const between = f32(sbl / f32(split));
        st.acc = f32(st.acc + f32(f32(between - nearestLength(sp, split)) * st.f8));
        st.isLast = false;
      }
      st.left -= 1;
      if (st.left <= 0) break;
    }
  }
  if (st.forced) {
    st.near = f32(h + st.near);
    if (!(st.near < sbl)) {
      spawn(spawnOne(b, sp, st.near, h, true, seedBase));
      st.forced = false;
    }
  }
}
