// PlayerTank gauge display 0x71026fb6d0 (ordinary tank: +0x539..+0x53f = 0) and InkShortage timer +0x4c0.
// Native tank constants are .bss values written by static init 0x71026f5020 (read back by the r11 harness).
const F = Math.fround;

export const TANK_FOLLOW_UP = F(0.5);   // 0x71058c7118: r < remaining
export const TANK_FOLLOW_DOWN = F(0.6); // 0x71058c711c: otherwise
export const TANK_LOCK_STEP = F(0.1);   // 0x71058c7120
export const TANK_EMPTY_FRAMES = 60;    // 0x71058c7128 (also the lack write max(+0x4c0, 60))

export interface TankInput {
  /** s0: sub ink cost (body+0x678 vt+0x68, or 0) */
  subCost: number;
  /** s1: tank remaining (body+0x698) */
  remaining: number;
  /** s2: body+0x69c */
  lock: number;
  /** w2 bit0 (param_6). Its local-player source is [미확정]; true is the path where InkShortage can start. */
  shortageEnabled: boolean;
}

export interface TankFrames {
  gauge: number;            // slot0 Gauge (skeletal + material)
  inkLock: number;          // slot3 InkLock
  inkShortageGauge: number | null; // slot2 when written this frame
  subMarker: number;        // slot4 SubMarker, uses the previous frame's sub cost
  requests: string[];       // InkShortage / InkShortageGauge requests
  stopShortage: boolean;    // slot1 stop 0x710399f41c
  tankEmpty: boolean;       // xlink TankEmpty
}

export class TankGauge {
  r = 0;          // +0x520
  lockValue = 0;  // +0x524
  first = true;   // +0x538
  subCostLatched = 0; // +0x528
  subMarkerCost = 0;  // +0x534
  shortage = 0;   // +0x4c0
  subShortage = 0; // +0x4c4
  latch52c = false;
  latch52d = false;
  /** InkShortage slot1: playing state and loop frame (45f loop). */
  shortagePlaying = false;
  shortageFrame = 0;

  /** Shooter lack path 0x7102585934: tank+0x4c0 = max(tank+0x4c0, 60). */
  lack(): void {
    this.shortage = Math.max(this.shortage, TANK_EMPTY_FRAMES);
  }

  /** Slot 18 0x71026f8280 per frame: max(x, 1) - 1 for +0x4c0/+0x4c4. */
  tickTimers(): void {
    this.shortage = Math.max(this.shortage, 1) - 1;
    this.subShortage = Math.max(this.subShortage, 1) - 1;
  }

  update(inp: TankInput): TankFrames {
    const rem = F(inp.remaining), s2 = F(inp.lock);
    let r: number;
    if (this.first) { this.r = rem; this.lockValue = s2; this.first = false; r = rem; }
    else r = this.r;
    const k = r < rem ? TANK_FOLLOW_UP : TANK_FOLLOW_DOWN;
    this.r = F(r + F(F(rem - r) * k));
    // 0x71026fa8a0 slot0: (1 - r >= 0) ? (1 - r) * 100 : 0
    const g = F(1 - this.r);
    const gauge = 0 <= g ? F(g * 100) : 0;
    let L = s2;
    if (L <= this.lockValue) {
      if (L <= rem) L = rem;
      const floor = F(this.lockValue - TANK_LOCK_STEP);
      if (L < floor) L = floor;
    }
    this.lockValue = L;
    this.subCostLatched = F(inp.subCost);
    // 0x71026fb7dc..0x71026fb818: FSUB → FMIN(·,1) → FMUL 100, negative → 0 (decompiler output drops the FMIN).
    const lk = F(F(1.05) - L);
    const inkLock = lk < 0 ? 0 : F(Math.min(lk, 1) * 100);
    const out: TankFrames = { gauge, inkLock, inkShortageGauge: null, subMarker: F(this.subMarkerCost * 100), requests: [], stopShortage: false, tankEmpty: false };

    const p6 = inp.shortageEnabled;
    const i4 = this.subShortage;
    const bVar6 = 0 < i4 && p6;
    let bVar7: boolean, bVar8: boolean;
    const toBa58 = (): void => { this.latch52d = false; };
    if (this.shortage < 1 || !p6) {
      bVar7 = !this.latch52d;
      const c5 = this.latch52c;
      this.latch52c = false;
      bVar8 = !c5;
      if (bVar6) this.at9b4(i4, out); else toBa58();
    } else {
      const c4 = this.latch52d;
      bVar7 = !c4;
      bVar8 = !this.latch52c;
      if (bVar6) { this.latch52c = false; this.at9b4(i4, out); }
      else if (!this.latch52c) {
        bVar8 = true;
        this.latch52c = true;
        if (TANK_EMPTY_FRAMES <= this.shortage) out.tankEmpty = true;
        toBa58();
      } else { bVar8 = false; this.latch52d = false; }
    }
    const start = (): void => {
      out.requests.push("InkShortage", "InkShortageGauge");
      this.shortagePlaying = true;
      this.shortageFrame = 0;
    };
    const stop = (): void => { out.stopShortage = true; this.shortagePlaying = false; };
    const gauge2 = (zero: boolean): void => { out.inkShortageGauge = zero ? 0 : F(F(1 - this.subCostLatched) * 100); };
    const at_bd50 = (): void => {
      if (this.latch52c) { gauge2(true); return; }
      if (!this.latch52d) return;
      gauge2(false);
    };
    if (bVar7) {
      let b6 = this.latch52d;
      if (!this.latch52d && bVar8) b6 = this.latch52c;
      if (bVar8) { if (b6) start(); }
      else if (b6) start();
      else if (!this.latch52c) stop();
      at_bd50();
    } else if (bVar8) {
      if (!this.latch52c) { if (!this.latch52d) stop(); at_bd50(); }
      else { start(); at_bd50(); }
    } else if (!this.latch52d || !this.latch52c) { stop(); at_bd50(); }
    else gauge2(true);
    this.subMarkerCost = F(inp.subCost);
    return out;
  }

  private at9b4(i4: number, out: TankFrames): void {
    if (!this.latch52d) {
      this.latch52d = true;
      if (TANK_EMPTY_FRAMES <= i4) out.tankEmpty = true;
    }
  }

  /** InkShortage loop frame after its request; 45-frame loop clip. */
  advanceShortage(frames = 45): void {
    if (this.shortagePlaying) this.shortageFrame = (this.shortageFrame + 1) % frames;
  }
}
