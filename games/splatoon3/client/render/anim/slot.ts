// AS 슬롯·래퍼 재생. 근거: docs/graphics/anim_state_machine.md §4.1(엔트리·전진), §4.2(요청 프레임), §4.3(FrameController),
// §4.4(FloatBlend), §4.5(전환 블렌드). 슬롯 1(보조 상체 레이어)은 뼈 그룹 이름이 [미확정]이라 쓰지 않는다.
import {
  type Asb, type AsbNode, Blackboard, FloatParamState, type Inst,
  floatBlendWeights, instantiate, nodeBlendFrames, slotValue,
} from "./asb.ts";

/** 클립 정보 공급자: 이름 → { 프레임 수(FSKA FrameCount), 반복 } 또는 없음 */
export type ClipInfo = (name: string) => { frames: number; loop: boolean } | null;

/** 슬롯 엔트리(§4.1) */
interface Entry {
  cur: number;
  prev: number;
  rate: number;
  end: number;
  loop: boolean;
  loopStart: number;
  endOverride: number;
  skip: boolean;
}

const round4 = (x: number): number => Math.round(x * 1e4) / 1e4;

/** 0x71039ab2c4 전진 */
function advance(e: Entry, dt: number, slotRate: number): void {
  if (e.skip) {
    e.skip = false;
    return;
  }
  e.prev = e.cur;
  const f = round4(e.cur + e.rate * dt * slotRate);
  const stop = e.endOverride < 0 ? e.end : e.endOverride;
  e.cur = f;
  if (f >= e.end) {
    if (!e.loop && f >= stop) e.cur = stop;
    else if (e.end > e.loopStart) {
      const len = e.end - e.loopStart;
      e.cur = round4(f - (f >= 2 * len ? len * Math.trunc(f / len) : len));
    } else e.cur = stop;
  }
}

interface Layer {
  inst: Inst;
  entries: Map<number, Entry>;
  seq: Map<number, number>;
  t: number;
  step: number;
  w: number;
  linear: boolean;
}

export interface LeafWeight {
  clip: string;
  /** 3 스켈레탈, 11 재질, 18 가시성 */
  type: number;
  frame: number;
  weight: number;
}

/** 래퍼(SM+0x08 사람 / SM+0x10 오징어) + 슬롯 0 */
export class Wrapper {
  readonly asb: Asb;
  readonly bb: Blackboard;
  readonly fps: FloatParamState;
  /** 래퍼+8: 지금 커맨드의 상태 번호, 정지 = -1 */
  cmd = -1;
  /** 래퍼+0x38: 다른 모델로 넘어갔지만 bit3 으로 표시만 남은 상태 */
  displayOnly = false;
  /** 슬롯 rate(+0xd4) */
  slotRate = 1;
  layers: Layer[] = [];
  private readonly clipInfo: ClipInfo;
  private weaponAbbr: string;
  readonly missing = new Set<string>();

  constructor(asb: Asb, bb: Blackboard, clipInfo: ClipInfo, weaponAbbr: string) {
    this.asb = asb;
    this.bb = bb;
    this.clipInfo = clipInfo;
    this.weaponAbbr = weaponAbbr;
    this.fps = new FloatParamState(asb);
  }

  stop(): void {
    this.cmd = -1;
    this.displayOnly = false;
    this.layers.length = 0;
  }

  /** 0x7102451a90 → 0x710399e340: 커맨드 시작. 진입 프레임 cur = 0(전진 없음) — 같은 프레임 tick 에서 1 이 된다(§4.2). */
  request(state: number, cmd: string, blendFrames: number, rate: number): void {
    this.cmd = state;
    this.displayOnly = false;
    this.slotRate = rate;
    const inst = instantiate(this.asb, cmd, this.bb, this.fps, this.weaponAbbr);
    if (!inst) {
      this.layers.length = 0;
      return;
    }
    const B = nodeBlendFrames(this.asb, cmd, this.bb) ?? blendFrames;
    const layer: Layer = { inst, entries: new Map(), seq: new Map(), t: 0, step: 0, w: 0, linear: false };
    if (B < 0.01 || !this.layers.length) {
      layer.w = 1;
      layer.t = 1;
    } else layer.step = 1 / B;
    this.enter(layer, inst);
    this.layers.push(layer);
    if (this.layers.length > 4) this.layers.shift(); // 최대 4층 [추정 §4.5]
    if (layer.w >= 1) this.layers = [layer];
  }

  private enter(layer: Layer, inst: Inst): void {
    if (inst.k === "leaf") {
      const info = inst.t === 3 ? this.clipInfo(inst.clip) : null;
      if (inst.t === 3 && !info) this.missing.add(inst.clip);
      const e: Entry = { cur: 0, prev: 0, rate: 1, end: info ? info.frames : 0, loop: info ? info.loop : false, loopStart: 0, endOverride: -1, skip: false };
      if (inst.ctrl) this.applyCtrl(e, inst.ctrl, info);
      layer.entries.set(inst.node, e);
    } else if (inst.k === "blend" || inst.k === "sim") {
      for (const k of inst.k === "blend" ? inst.kids.map((x) => x[2]) : inst.kids) this.enter(layer, k);
    } else if (inst.k === "seq") {
      layer.seq.set(inst.node, 0);
      if (inst.kids[0]) this.enter(layer, inst.kids[0]);
    }
  }

  /** FrameController(종류 12, §4.3) */
  private applyCtrl(e: Entry, c: AsbNode, info: { frames: number; loop: boolean } | null): void {
    const num = (s: AsbNode["rate"]): number => Number(slotValue(s, this.asb, this.bb, this.fps) ?? 0);
    e.rate = num(c.rate);
    const start = num(c.start);
    e.cur = start;
    e.loopStart = start;
    const end = num(c.end);
    if (end >= 0) e.end = end;
    else if (info) e.end = info.frames;
    if (c.mode === 1 || c.mode === 3 || c.mode === 4) e.loop = true;
    else if (c.mode === 2) e.loop = false;
  }

  /** 래퍼 틱(0x71024507a8): 엔트리 전진 + 전환 블렌드 진행(원 dt, §4.5) */
  tick(dt: number): void {
    if (this.cmd === -1) return;
    this.fps.tick(this.bb, dt);
    for (const l of this.layers) {
      this.advanceInst(l, l.inst, dt);
      if (l.w < 1) {
        l.t = Math.min(1, l.t + l.step * dt);
        const t = l.t;
        l.w = l.linear ? t : t < 0.5 ? 2 * t * t : 1 - 2 * (1 - t) * (1 - t);
      }
    }
    const top = this.layers[this.layers.length - 1];
    if (top && top.t >= 1) this.layers = [top];
  }

  private advanceInst(l: Layer, inst: Inst, dt: number): void {
    if (inst.k === "leaf") {
      const e = l.entries.get(inst.node);
      if (e) advance(e, dt, this.slotRate);
    } else if (inst.k === "blend" || inst.k === "sim") {
      for (const k of inst.k === "blend" ? inst.kids.map((x) => x[2]) : inst.kids) this.advanceInst(l, k, dt);
    } else if (inst.k === "seq") {
      // Sequence(종류 7): 앞 자식이 끝나면 다음 자식 [추정]
      const i = l.seq.get(inst.node) ?? 0;
      const kid = inst.kids[i];
      if (!kid) return;
      this.advanceInst(l, kid, dt);
      if (i + 1 < inst.kids.length && this.finished(l, kid)) {
        l.seq.set(inst.node, i + 1);
        this.enter(l, inst.kids[i + 1]);
      }
    }
  }

  private finished(l: Layer, inst: Inst): boolean {
    if (inst.k === "leaf") {
      const e = l.entries.get(inst.node);
      return !e || (!e.loop && e.cur >= (e.endOverride < 0 ? e.end : e.endOverride));
    }
    const kids = inst.k === "blend" ? inst.kids.map((x) => x[2]) : inst.kids;
    return kids.every((k) => this.finished(l, k));
  }

  /** 활성 노드의 cur / end (0x710245064c: 종류 3 = entry.end, 기본은 활성 자식). 끝 판정용. */
  progress(): { cur: number; end: number } | null {
    const top = this.layers[this.layers.length - 1];
    if (!top) return null;
    const leaf = this.firstLeaf(top, top.inst);
    const e = leaf ? top.entries.get(leaf.node) : undefined;
    return e ? { cur: e.cur, end: e.end } : null;
  }

  private firstLeaf(l: Layer, inst: Inst): Extract<Inst, { k: "leaf" }> | null {
    if (inst.k === "leaf") return inst;
    if (inst.k === "seq") {
      const k = inst.kids[l.seq.get(inst.node) ?? 0];
      return k ? this.firstLeaf(l, k) : null;
    }
    const kids = inst.k === "blend" ? inst.kids.map((x) => x[2]) : inst.kids;
    for (const k of kids) {
      const r = this.firstLeaf(l, k);
      if (r) return r;
    }
    return null;
  }

  /** 지금 포즈에 들어가는 잎과 가중치. 층 i 가중치 = w_i · Π_{j>i}(1 − w_j). */
  leaves(alphaFrames = 0): LeafWeight[] {
    const out: LeafWeight[] = [];
    let rest = 1;
    for (let i = this.layers.length - 1; i >= 0 && rest > 1e-4; i--) {
      const l = this.layers[i];
      const lw = i === 0 ? rest : rest * l.w;
      this.collect(l, l.inst, lw, out, alphaFrames);
      rest -= lw;
    }
    return out;
  }

  private collect(l: Layer, inst: Inst, w: number, out: LeafWeight[], alphaFrames: number): void {
    if (w <= 1e-4) return;
    if (inst.k === "leaf") {
      const e = l.entries.get(inst.node);
      if (!e) return;
      // 렌더 보간: 다음 틱 위치를 미리 본다(원본에 없는 표시 전용 보간)
      let frame = e.cur;
      if (alphaFrames > 0) {
        const nx = e.cur + e.rate * alphaFrames * this.slotRate;
        frame = e.loop && e.end > e.loopStart && nx >= e.end ? nx - (e.end - e.loopStart) : Math.min(nx, e.endOverride < 0 ? e.end : e.endOverride);
      }
      out.push({ clip: inst.clip, type: inst.t, frame, weight: w });
    } else if (inst.k === "blend") {
      const x = Number(slotValue(inst.v, this.asb, this.bb, this.fps) ?? 0);
      for (const [i, bw] of floatBlendWeights(inst.kids, x, inst.smooth)) this.collect(l, inst.kids[i][2], w * bw, out, alphaFrames);
    } else if (inst.k === "sim") {
      for (const k of inst.kids) this.collect(l, k, w, out, alphaFrames);
    } else {
      const k = inst.kids[l.seq.get(inst.node) ?? 0];
      if (k) this.collect(l, k, w, out, alphaFrames);
    }
  }
}
