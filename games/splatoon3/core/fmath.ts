// 원본은 f32 연산이고 이동·탄 코드에 FMA가 없다(docs/weapon/shooter_bullet.md §5.2).
// 연산마다 f32로 반올림해야 원본과 같은 비트가 나온다.
export const f32 = Math.fround;

export type Vec3 = Float32Array;

export function v3(x = 0, y = 0, z = 0): Vec3 {
  const v = new Float32Array(3);
  v[0] = x;
  v[1] = y;
  v[2] = z;
  return v;
}

export function copy(out: Vec3, a: ArrayLike<number>): Vec3 {
  out[0] = a[0];
  out[1] = a[1];
  out[2] = a[2];
  return out;
}

export function add(out: Vec3, a: Vec3, b: Vec3): Vec3 {
  out[0] = a[0] + b[0];
  out[1] = a[1] + b[1];
  out[2] = a[2] + b[2];
  return out;
}

export function sub(out: Vec3, a: Vec3, b: Vec3): Vec3 {
  out[0] = a[0] - b[0];
  out[1] = a[1] - b[1];
  out[2] = a[2] - b[2];
  return out;
}

export function scale(out: Vec3, a: Vec3, s: number): Vec3 {
  out[0] = a[0] * s;
  out[1] = a[1] * s;
  out[2] = a[2] * s;
  return out;
}

export function dot(a: Vec3, b: Vec3): number {
  return f32(f32(f32(a[0] * b[0]) + f32(a[1] * b[1])) + f32(a[2] * b[2]));
}

export function lengthSq(a: Vec3): number {
  return dot(a, a);
}

export function length(a: Vec3): number {
  return f32(Math.sqrt(lengthSq(a)));
}

/** 원본 sead 규약: 길이가 0보다 클 때만 정규화한다. */
export function normalize(out: Vec3, a: Vec3): Vec3 {
  const l = length(a);
  if (l > 0) {
    const inv = f32(1 / l);
    out[0] = a[0] * inv;
    out[1] = a[1] * inv;
    out[2] = a[2] * inv;
  } else copy(out, a);
  return out;
}

export function clamp(x: number, lo: number, hi: number): number {
  return x < lo ? lo : x > hi ? hi : x;
}

export function lerp(a: number, b: number, t: number): number {
  return f32(a + f32(f32(b - a) * t));
}
