// sead::Random (xorshift128). 초기화·생성식은 docs/weapon/shooter_bullet.md §5.3, camera/aim_swerve.md.
export class SeadRandom {
  s0 = 0;
  s1 = 0;
  s2 = 0;
  s3 = 0;

  constructor(seed = 0) {
    this.init(seed);
  }

  init(seed: number): void {
    let x = seed >>> 0;
    const next = (prev: number, i: number) => (Math.imul((prev ^ (prev >>> 30)) >>> 0, 0x6c078965) + i) >>> 0;
    this.s0 = x = next(x, 1);
    this.s1 = x = next(x, 2);
    this.s2 = x = next(x, 3);
    this.s3 = next(x, 4);
  }

  /** 원본에서 상태 4개를 직접 넣는 경로(탄 관리자 시드 등)용. */
  setState(a: number, b: number, c: number, d: number): void {
    this.s0 = a >>> 0;
    this.s1 = b >>> 0;
    this.s2 = c >>> 0;
    this.s3 = d >>> 0;
  }

  u32(): number {
    const t = (this.s0 ^ (this.s0 << 11)) >>> 0;
    this.s0 = this.s1;
    this.s1 = this.s2;
    this.s2 = this.s3;
    this.s3 = (t ^ (t >>> 8) ^ this.s3 ^ (this.s3 >>> 19)) >>> 0;
    return this.s3;
  }

  /** [0,1): f32 비트 (u32>>>9 | 0x3f800000) - 1.0 */
  float01(): number {
    BITS[0] = (this.u32() >>> 9) | 0x3f800000;
    return Math.fround(FLOATS[0] - 1);
  }
}

const BUF = new ArrayBuffer(4);
const BITS = new Uint32Array(BUF);
const FLOATS = new Float32Array(BUF);
