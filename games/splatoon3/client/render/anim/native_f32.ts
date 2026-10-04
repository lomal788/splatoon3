// Exact single-rounding f32 helpers for original FMLA/FMADD sequences.
const F = Math.fround;
const view = new DataView(new ArrayBuffer(8));

function exact(x: number): [bigint, number] {
  view.setFloat64(0, x);
  const hi = view.getUint32(0), lo = view.getUint32(4);
  const e = (hi >>> 20) & 0x7ff;
  let m = (BigInt(hi & 0xfffff) << 32n) | BigInt(lo);
  if (e) m |= 1n << 52n;
  return [hi >>> 31 ? -m : m, (e || 1) - 1075];
}

const bitLength = (v: bigint): number => v.toString(2).length;

/** f32(a*b + c) with one rounding (ARM FMADD/FMLA on f32 lanes, round-to-nearest-even). */
export function fma32(a: number, b: number, c: number): number {
  a = F(a); b = F(b); c = F(c);
  if (!Number.isFinite(a) || !Number.isFinite(b) || !Number.isFinite(c)) return F(a * b + c);
  const [ma, ea] = exact(a), [mb, eb] = exact(b), [mc, ec] = exact(c);
  const mp = ma * mb, ep = ea + eb;
  if (mp === 0n || mc === 0n) {
    if (mp === 0n && mc === 0n) return F(a * b + c);
    if (mp === 0n) return c;
  }
  const e = Math.min(ep, ec);
  const sum = (mp << BigInt(ep - e)) + (mc << BigInt(ec - e));
  if (sum === 0n) return F(a * b + c);
  const neg = sum < 0n, mag = neg ? -sum : sum;
  // Keep 24 significant bits, but never below the f32 subnormal quantum 2^-149.
  const shift = Math.max(bitLength(mag) - 24, -149 - e);
  let q = mag;
  if (shift > 0) {
    const s = BigInt(shift), half = 1n << (s - 1n), rem = mag & ((1n << s) - 1n);
    q = mag >> s;
    if (rem > half || (rem === half && (q & 1n) === 1n)) q += 1n;
  } else if (shift < 0) q = mag << BigInt(-shift);
  const out = F(Number(q) * 2 ** (e + shift));
  return neg ? -out : out;
}
