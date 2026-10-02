// XLink2(ELink/SLink) 사용자 실행기. 데이터 = web/tools/effect_xlink.py dump 의 사용자 JSON 한 개.
// 규칙 근거: docs/effect_sound/xlink_format.md §3.6~4.4 (주소는 main).
//   searchAndEmit 0x710389e6e8 · Switch 0x71038978bc · Random 0x71038925a0 · Random2 0x7103892874
//   Blend 0x710388f59c · Sequence 0x7103897644 · Grid 0x71038909a4 · 값 해석 0x7103888b04
//   액션 변경 0x71038964b8 / 시작 0x7103896874 / 매 프레임 0x7103895f64
// DOM·three 를 쓰지 않는다(노드에서 직접 검증 가능). 재생은 sink 가 맡는다.

export type PropValue = number | string | boolean;

export interface XCondition {
  parent: string;
  propertyType?: string;
  compare?: string;
  value?: PropValue;
  weight?: number;
  isGlobal?: boolean;
}

export interface XContainer {
  type: string;
  children: [number, number];
  watchProperty?: string;
  isGlobal?: boolean;
  watchActionSlot?: number;
  props?: [string, string];
  values1?: PropValue[];
  values2?: PropValue[];
  table?: number[][];
}

export interface XCallTable {
  i: number;
  key: string;
  flag: number;
  duration: number;
  parent: number;
  container?: XContainer;
  condition?: XCondition;
  params?: Record<string, unknown>;
}

export interface XActionTrigger {
  callTable: number;
  key: string;
  raw: string[];
  /** assets 번들의 축약 목록에서 원래 번호 */
  _i?: number;
}

export interface XPropertyTrigger {
  callTable: number;
  key: string;
  condition?: XCondition;
  flag?: number;
}

export interface XUser {
  name?: string;
  localProperties: string[];
  userParams?: Record<string, unknown>;
  /** assets 번들은 쓰지 않는 칸을 null 로 둔다(원래 번호 유지) */
  callTables: (XCallTable | null)[];
  actionSlots: { name: string; actions: [number, number] }[];
  actions: { name: string; triggers: [number, number] }[];
  actionTriggers: XActionTrigger[];
  properties: { watchProperty: string; isGlobal: number; triggers: [number, number] }[];
  propertyTriggers: XPropertyTrigger[];
}

/** 재생 중인 에셋 하나(소리 보이스·이펙트 이벤트). sink 가 만든다. */
export interface XHandle {
  alive(): boolean;
  /** 원본 이벤트 +8 |= 0x90 (페이드 정지) */
  fade(): void;
  /** 위치 갱신(액션/속성 트리거로 유지되는 이벤트) */
  onEnd?: (cb: () => void) => void;
}

/** 값이 해석된 에셋 하나. */
export interface XAsset {
  key: string;
  name: string;
  params: Record<string, unknown>;
}

export interface XSink {
  play(a: XAsset, ctx: EmitContext): XHandle | null;
}

/** 방출 시 함께 넘기는 위치 등 호출자 정보(sink 가 해석). */
export type EmitContext = Record<string, unknown>;

export type Rand = () => number;

// ---- 비교 (§3.7: 속성 현재값 OP 조건값) -----------------------------------
const CMP: Record<string, (a: PropValue, b: PropValue) => boolean> = {
  Equal: (a, b) => a === b,
  NotEqual: (a, b) => a !== b,
  GreaterThan: (a, b) => a > b,
  GreaterThanOrEqual: (a, b) => a >= b,
  LessThan: (a, b) => a < b,
  LessThanOrEqual: (a, b) => a <= b,
};

function boolish(v: PropValue): PropValue {
  if (v === true) return "True";
  if (v === false) return "False";
  return v;
}

export function compare(cur: PropValue | undefined, cond: XCondition): boolean {
  if (cur === undefined || cond.value === undefined) return false;
  const f = CMP[cond.compare ?? "Equal"];
  if (!f) return false;
  // Enum 의 True/False 는 데이터에 문자열로 들어 있다(IsPaintable 등).
  return f(cond.propertyType === "Enum" ? boolish(cur) : cur, cond.value);
}

// ---- 값 해석 (§4.3, 0x7103888b04) ----------------------------------------
export function curveValue(
  c: { points: [number, number][]; curveType?: number },
  x: number,
): number {
  const pts = c.points;
  if (!pts.length) return 0;
  if ((c.curveType ?? 0) !== 0) return pts[pts.length - 1][1];
  for (let k = 0; k < pts.length; k++) {
    const [px, py] = pts[k];
    if (x === px) return k + 1 < pts.length && pts[k + 1][0] === px ? pts[k + 1][1] : py;
    if (x < px) {
      if (k === 0) return py;
      const [x0, y0] = pts[k - 1];
      return y0 + (x - x0) * ((py - y0) / (px - x0));
    }
  }
  return pts[pts.length - 1][1];
}

const POW: Record<string, number> = { "2": 2, "3": 3, "4": 4, "1Point5": 1.5 };

export function resolveValue(v: unknown, props: (name: string) => PropValue | undefined, rand: Rand): unknown {
  if (!v || typeof v !== "object" || Array.isArray(v)) return v;
  const o = v as Record<string, unknown>;
  if ("curve" in o) {
    const c = o.curve as { points: [number, number][]; curveType?: number; prop: string };
    const x = props(c.prop);
    // 커브의 속성이 없으면 원본은 +∞ 를 돌려주고 호출자가 처리한다 → 여기서는 첫 점 x 로 평가하지 않고 무한대.
    if (x === undefined) return Infinity;
    return curveValue(c, typeof x === "number" ? x : Number(boolish(x) === "True"));
  }
  for (const [k, x] of Object.entries(o)) {
    if (!Array.isArray(x) || x.length !== 2) continue;
    const lo = Number(x[0]), hi = Number(x[1]);
    if (k === "Random") return lo <= hi ? lo + (hi - lo) * rand() : lo;
    const m = /^Random(2|3|4|1Point5)Pow(WeightMin|WeightMax)?$/.exec(k);
    if (!m) continue;
    const n = POW[m[1]];
    if (!m[2]) {
      const h = Math.abs(hi - lo) / 2;
      const u = 2 * rand() - 1;
      const p = h * Math.abs(u) ** n;
      return lo + h + (u >= 0 ? p : -p);
    }
    if (m[2] === "WeightMin") return lo + Math.abs(hi - lo) * rand() ** n;
    return lo + Math.abs(hi - lo) * (1 - rand() ** n);
  }
  // Bitflag 등 {이름: 값} 한 칸짜리
  const ks = Object.keys(o);
  if (ks.length === 1 && typeof o[ks[0]] === "number") return o[ks[0]];
  return v;
}

// ---- 사용자 인스턴스 -------------------------------------------------------
interface TrigState {
  handle: XHandle | null;
  fired: boolean;
  handed: boolean;
  /** bit4 직전 액션 이름 일치 */
  nameOk: boolean;
}

interface SlotState {
  current: number; // action index, -1 없음
  frame: number;
  prevFrame: number;
  nameCrc: number;
  /** bit4 조건이 비교하는 직전 액션 이름 CRC32 */
  prevNameCrc: number;
  states: Map<number, TrigState>;
}

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

export function crc32(s: string): number {
  const b = new TextEncoder().encode(s);
  let c = 0xffffffff;
  for (const x of b) c = CRC_TABLE[(c ^ x) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function trigFlag(t: XActionTrigger): number {
  return parseInt(t.raw[3], 16) & 0xffff;
}
function trigStart(t: XActionTrigger): number {
  return parseInt(t.raw[0], 16) | 0;
}
function trigEnd(t: XActionTrigger): number {
  return parseInt(t.raw[2], 16) | 0;
}

export class XLinkInstance {
  readonly user: XUser;
  readonly sink: XSink;
  readonly rand: Rand;
  /** 로컬 속성 값 */
  readonly props = new Map<string, PropValue>();
  /** 전역 속성(SpecMode 등) 조회 */
  global: (name: string) => PropValue | undefined = () => undefined;
  /** 방출 시 sink 에 넘길 기본 정보(위치 등) */
  ctx: EmitContext = {};
  private readonly byKey = new Map<string, XCallTable>();
  private readonly lastPick = new Map<number, number>();
  private readonly slots = new Map<string, SlotState>();
  private readonly propTrig = new Map<number, XHandle | null>();
  /** 원래 번호 → 액션 트리거(축약 목록이면 _i 로 다시 편다) */
  private readonly trigs = new Map<number, XActionTrigger>();

  constructor(user: XUser, sink: XSink, rand: Rand = Math.random) {
    this.user = user;
    this.sink = sink;
    this.rand = rand;
    for (const c of user.callTables) if (c && c.parent === -1 && !this.byKey.has(c.key)) this.byKey.set(c.key, c);
    (user.actionTriggers ?? []).forEach((t, i) => {
      if (t) this.trigs.set(typeof t._i === "number" ? t._i : i, t);
    });
  }

  prop(name: string): PropValue | undefined {
    return this.props.has(name) ? this.props.get(name) : this.global(name);
  }

  hasKey(key: string): boolean {
    return this.byKey.has(key);
  }

  /** 0x710389e6e8: 키가 없으면 아무것도 하지 않는다. */
  searchAndEmit(key: string, ctx?: EmitContext): XHandle[] {
    const root = this.byKey.get(key);
    if (!root) return [];
    return this.start(root, ctx ?? this.ctx);
  }

  /** 콜 테이블 하나를 시작(컨테이너 규칙 §4.2). duration 규칙 포함. */
  start(ct: XCallTable, ctx: EmitContext): XHandle[] {
    const out: XHandle[] = [];
    this.run(ct, ctx, out, ct.duration);
    return out;
  }

  private kids(ct: XCallTable): XCallTable[] {
    const [a, b] = ct.container!.children;
    const r: XCallTable[] = [];
    for (let i = a; i <= b; i++) {
      const c = this.user.callTables[i];
      if (c) r.push(c);
    }
    return r;
  }

  private run(ct: XCallTable, ctx: EmitContext, out: XHandle[], duration: number): boolean {
    const k = ct.container;
    if (!k) {
      const params: Record<string, unknown> = {};
      for (const [name, v] of Object.entries(ct.params ?? {})) params[name] = resolveValue(v, (p) => this.prop(p), this.rand);
      const name = String(params.RuntimeAssetName ?? "");
      const h = this.sink.play({ key: ct.key, name, params }, ctx);
      if (!h) return false;
      out.push(h);
      // duration: 끝날 때마다 >0 이면 1 감소, 0 이 아니면 다시 start (-1 무한)  [판독 0x710389250c]
      if (duration !== 1 && duration !== 0 && h.onEnd) {
        h.onEnd(() => {
          const next = duration > 0 ? duration - 1 : duration;
          if (next !== 0) this.run(ct, ctx, out, next);
        });
      }
      return true;
    }
    const kids = this.kids(ct);
    switch (k.type) {
      case "Switch": {
        if (k.watchActionSlot) {
          const slot = this.slots.get(k.watchProperty ?? "");
          const cur = slot && slot.current >= 0 ? slot.current : -1;
          for (const c of kids) {
            if (!c.condition) return this.run(c, ctx, out, c.duration);
            const v = Number(c.condition.value);
            const ok = c.condition.compare === "NotEqual" ? cur !== v : cur === v;
            if (ok) return this.run(c, ctx, out, c.duration);
          }
          return false;
        }
        const name = k.watchProperty ?? "";
        const cur = k.isGlobal ? this.global(name) : this.prop(name);
        for (const c of kids) {
          // 조건 없는 자식을 만나면 그 자리에서 고른다(0x71038978bc)
          if (!c.condition || c.condition.parent !== "Switch") return this.run(c, ctx, out, c.duration);
          if (compare(cur, c.condition)) return this.run(c, ctx, out, c.duration);
        }
        return false;
      }
      case "Random":
      case "Random2": {
        const excl = k.type === "Random2" && kids.length > 1 ? this.lastPick.get(ct.i) : undefined;
        const cand = kids.filter((c) => c.i !== excl);
        let W = 0;
        for (const c of cand) W += c.condition?.weight ?? 0;
        if (W <= 0) return false;
        const r = W * this.rand();
        let acc = 0;
        for (const c of cand) {
          acc += c.condition?.weight ?? 0;
          if (acc > r) {
            if (k.type === "Random2") this.lastPick.set(ct.i, c.i);
            return this.run(c, ctx, out, c.duration);
          }
        }
        return false;
      }
      case "Blend": {
        let any = false;
        for (const c of kids) any = this.run(c, ctx, out, c.duration) || any;
        return any;
      }
      case "Sequence":
        return this.sequence(kids, 0, ctx, out);
      case "Grid": {
        const [p1, p2] = k.props ?? ["", ""];
        const a = (k.values1 ?? []).indexOf(this.prop(p1) as PropValue);
        const b = (k.values2 ?? []).indexOf(this.prop(p2) as PropValue);
        if (a < 0 || b < 0) return false;
        const ci = k.table?.[a]?.[b] ?? -1;
        const [lo, hi] = k.children;
        if (ci < lo || ci > hi) return false;
        const c = this.user.callTables[ci];
        return c ? this.run(c, ctx, out, c.duration) : false;
      }
      default:
        return false;
    }
  }

  /** Sequence(0x7103897644): 순번을 하나씩 올리며 자식 하나를 시작, 실패하면 건너뜀, 끝나면 다음. */
  private sequence(kids: XCallTable[], from: number, ctx: EmitContext, out: XHandle[]): boolean {
    for (let i = from; i < kids.length; i++) {
      const before = out.length;
      if (!this.run(kids[i], ctx, out, kids[i].duration)) continue;
      const h = out[out.length - 1];
      if (out.length > before && h?.onEnd) h.onEnd(() => this.sequence(kids, i + 1, ctx, out));
      return true;
    }
    return false;
  }

  // ---- 액션 슬롯 (§4.4) ----------------------------------------------------
  private slot(name: string): SlotState {
    let s = this.slots.get(name);
    if (!s) {
      s = { current: -1, frame: 0, prevFrame: 0, nameCrc: 0, prevNameCrc: 0, states: new Map() };
      this.slots.set(name, s);
    }
    return s;
  }

  private slotActions(name: string): number[] {
    const sd = (this.user.actionSlots ?? []).find((s) => s.name === name);
    if (!sd) return [];
    const r: number[] = [];
    for (let i = sd.actions[0]; i <= sd.actions[1]; i++) r.push(i);
    return r;
  }

  private triggersOf(ai: number): number[] {
    const a = this.user.actions[ai];
    if (!a) return [];
    const r: number[] = [];
    for (let i = a.triggers[0]; i <= a.triggers[1]; i++) if (this.trigs.has(i)) r.push(i);
    return r;
  }

  private assetLoops(t: XActionTrigger): boolean {
    // 에셋 속성 바이트(+2) bit1 = 반복형 에셋 [추정]. 덤프에 없으므로 duration -1 을 반복형으로 본다.
    return this.user.callTables[t.callTable]?.duration === -1;
  }

  private emitTrigger(t: XActionTrigger, st: TrigState): void {
    const ct = this.user.callTables[t.callTable];
    if (!ct) return;
    const hs = this.start(ct, this.ctx);
    st.handle = hs[0] ?? null;
    st.fired = true;
  }

  /** 0x71038964b8: 슬롯의 액션 변경. 같은 액션이면 아무것도 안 함. */
  changeAction(slotName: string, actionName: string, startFrame = 0): void {
    const s = this.slot(slotName);
    s.prevNameCrc = s.nameCrc;
    s.nameCrc = crc32(actionName);
    const ai = this.slotActions(slotName).find((i) => this.user.actions[i].name === actionName);
    if (ai === undefined) {
      this.stopSlot(s, new Set());
      s.current = -1;
      return;
    }
    if (s.current === ai) return;
    const old = s.current >= 0 ? this.triggersOf(s.current) : [];
    const handed = new Set<number>();
    const newStates = new Map<number, TrigState>();
    for (const ti of this.triggersOf(ai)) {
      const t = this.trigs.get(ti)!;
      const flag = trigFlag(t);
      const st: TrigState = { handle: null, fired: false, handed: false, nameOk: false };
      newStates.set(ti, st);
      let fire: boolean;
      if (flag & 4) fire = true;
      else if (flag & 8) fire = false;
      else if (flag & 0x10) {
        // 트리거 +0x10 = 직전 액션 이름(이름표 오프셋). 덤프에는 오프셋만 있어 이름 비교는 하지 못한다 [미구현].
        fire = false;
      } else {
        const a = trigStart(t), e = trigEnd(t);
        fire = this.assetLoops(t) ? a <= startFrame && startFrame < e : a === startFrame;
      }
      if (flag & 1) {
        // 넘겨받기: 직전 액션의 같은 에셋 트리거가 이미 발생했으면 그 이벤트를 넘겨받고 방출하지 않는다.
        for (const oi of old) {
          const o = this.trigs.get(oi)!;
          const os = s.states.get(oi);
          if (!os || os.handed || !os.fired || o.callTable !== t.callTable) continue;
          os.handed = true;
          handed.add(oi);
          st.handle = os.handle;
          os.handle = null;
          st.fired = true;
          fire = false;
          break;
        }
      }
      if (fire) this.emitTrigger(t, st);
    }
    // 넘겨받지 않은 직전 액션 이벤트 정리
    this.stopSlot(s, handed);
    s.states = newStates;
    s.current = ai;
    s.frame = startFrame;
    s.prevFrame = startFrame;
  }

  private stopSlot(s: SlotState, keep: Set<number>): void {
    for (const [ti, st] of s.states) if (!keep.has(ti)) st.handle?.fade();
  }

  /** 슬롯 이름별 현재 액션 이름 */
  currentAction(slotName: string): string | null {
    const s = this.slots.get(slotName);
    return s && s.current >= 0 ? this.user.actions[s.current].name : null;
  }

  /** 0x7103895f64: 매 프레임. 액션 프레임을 1 올리고 프레임 범위 트리거를 처리. */
  calc(): void {
    for (const s of this.slots.values()) {
      if (s.current < 0) continue;
      s.prevFrame = s.frame;
      s.frame++;
      const prev = s.prevFrame, cur = s.frame;
      for (const ti of this.triggersOf(s.current)) {
        const t = this.trigs.get(ti)!;
        const st = s.states.get(ti);
        if (!st) continue;
        const flag = trigFlag(t);
        if (flag & 0xc) continue;
        if (flag & 0x10 && !st.nameOk) continue;
        const a = trigStart(t), e = trigEnd(t);
        if (this.assetLoops(t)) {
          if (a <= cur && cur < e && !(st.handle && st.handle.alive()) && !(flag & 1 && st.fired)) this.emitTrigger(t, st);
        } else if (prev < a && a <= cur && cur < e && !(flag & 1 && st.fired)) this.emitTrigger(t, st);
        if (prev < e && e <= cur && st.handle) {
          st.handle.fade();
          st.handle = null;
        }
      }
    }
  }

  // ---- 속성 트리거 ----------------------------------------------------------
  /**
   * 속성 값을 쓰고 속성 트리거를 평가한다. 조건이 참이 되면 방출, 거짓이 되면 정지.
   * 이 게임의 속성 트리거 calc 는 판독하지 않았다 — 참고 소스(Splatoon 2 xlink2) 동작 [참고].
   */
  setProp(name: string, v: PropValue): void {
    const old = this.props.get(name);
    this.props.set(name, v);
    if (old === v) return;
    (this.user.properties ?? []).forEach((p) => {
      if (p.watchProperty !== name) return;
      for (let i = p.triggers[0]; i <= p.triggers[1]; i++) {
        const t = this.user.propertyTriggers?.[i];
        if (!t) continue;
        const ok = !t.condition || compare(v, t.condition);
        const h = this.propTrig.get(i);
        if (ok && !(h && h.alive())) {
          const ct = this.user.callTables[t.callTable];
          if (ct) this.propTrig.set(i, this.start(ct, this.ctx)[0] ?? null);
        } else if (!ok && h) {
          h.fade();
          this.propTrig.set(i, null);
        }
      }
    });
  }
}

/** 노드에서 쓰는 결정적 난수(테스트용). */
export function seededRand(seed: number): Rand {
  let x = seed >>> 0 || 1;
  return () => {
    x ^= x << 13;
    x >>>= 0;
    x ^= x >>> 17;
    x ^= x << 5;
    x >>>= 0;
    return x / 4294967296;
  };
}
