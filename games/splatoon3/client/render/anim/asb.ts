// ASB 상태머신 데이터와 평가. 근거: docs/graphics/anim_state_machine.md.
// 데이터: asb_data.json (gen/asb_gen.mjs 로 원본 SplPlayer.pack AS/*.root.asb 에서 생성), state_table.json (gen/state_table_gen.mjs).
import asbJson from "./asb_data.json";
import stateJson from "./state_table.json";
import { ASSUMED_CLIP_KEYS, nativeClipName } from "./clip_name.ts";

export type Slot =
  | { c: number | string }
  | { bb: number; k: string }
  | { fp: number }
  | { raw: number[] };

export interface AsbNode {
  t: number;
  rec?: { type: number; v: Slot }[];
  clip?: Slot;
  attach?: { events: number[]; ctrls: number[] };
  v?: Slot;
  cases?: [string | number, number][];
  kids?: (number | [number, number, number])[];
  smooth?: boolean;
  rate?: Slot;
  start?: Slot;
  end?: Slot;
  mode?: number;
  event?: number;
}

export interface FloatParam {
  bb: number;
  rate: number;
  mode: number;
  init: number;
  scale: number;
  offset: number;
  min: number;
  max: number;
}

export interface Asb {
  commands: Record<string, number>;
  nodes: AsbNode[];
  floatParams: FloatParam[];
  bb: { string: string[]; int: string[]; float: string[]; bool: string[] };
}

const data = asbJson as unknown as { human: Asb; squid: Asb };
export const HUMAN_ASB: Asb = data.human;
export const SQUID_ASB: Asb = data.squid;

/** 상태 표 행: [커맨드, 모델(0 사람/1 오징어), 블렌드 프레임, 플래그] — player_state.md 부록 */
const rows = (stateJson as unknown as { rows: Record<string, [string, number, number, number]> }).rows;

export interface StateRow {
  cmd: string;
  squid: boolean;
  blend: number;
  flags: number;
}

export function stateRow(state: number): StateRow | null {
  const r = rows[state >= 0x11e ? 0 : state]; // 0x11e 이상은 표[0] (player_state.md §4)
  return r ? { cmd: r[0], squid: r[1] === 1, blend: r[2], flags: r[3] } : null;
}

/** 블랙보드 (§2.6, §4.6). 이름으로 값을 둔다. */
export class Blackboard {
  readonly str = new Map<string, string>();
  readonly int = new Map<string, number>();
  readonly float = new Map<string, number>();
  readonly bool = new Map<string, boolean>();
}

/** 실수 파라미터 표(§2.7)의 변화율 제한 상태 — ASB(래퍼)마다 하나. */
export class FloatParamState {
  private readonly cur: number[];
  private readonly asb: Asb;
  constructor(asb: Asb) {
    this.asb = asb;
    this.cur = asb.floatParams.map((p) => p.init);
  }
  /** 매 틱: bb 값으로 변화율 제한 갱신. rate 0 은 제한 없음으로 본다 [추정]. 모드 1(각도) 감싸기는 미구현. */
  tick(bb: Blackboard, dt: number): void {
    this.asb.floatParams.forEach((p, i) => {
      const target = bb.float.get(this.asb.bb.float[p.bb]) ?? 0;
      if (p.rate > 0) {
        const lim = p.rate * dt;
        this.cur[i] += Math.max(-lim, Math.min(lim, target - this.cur[i]));
      } else this.cur[i] = target;
    });
  }
  value(i: number): number {
    const p = this.asb.floatParams[i];
    if (!p) return 0;
    return Math.max(p.min, Math.min(p.max, p.offset + p.scale * this.cur[i]));
  }
}

export function slotValue(s: Slot | undefined, asb: Asb, bb: Blackboard, fps: FloatParamState | null): number | string | boolean | undefined {
  if (!s) return undefined;
  if ("c" in s) return s.c;
  if ("fp" in s) return fps ? fps.value(s.fp) : 0;
  if ("bb" in s) {
    if (s.k === "string") return bb.str.get(asb.bb.string[s.bb]) ?? "";
    if (s.k === "int") return bb.int.get(asb.bb.int[s.bb]) ?? 0;
    if (s.k === "float") return bb.float.get(asb.bb.float[s.bb]) ?? 0;
    if (s.k === "bool") return bb.bool.get(asb.bb.bool[s.bb]) ?? false;
  }
  return undefined;
}

/** 클립 이름 치환(§3): Nrml → 무기 변형(기본 Shtr), @ → 이모트 변형(기본 Win01). */
export function resolveClipName(name: string, weaponAbbr = "Shtr", emote = "Win01"): string {
  return name.replace("Nrml", weaponAbbr).replace("@", emote);
}



/** 평가 결과 트리 */
export type Inst =
  | { k: "leaf"; node: number; t: number; clip: string; ctrl: AsbNode | null }
  | { k: "blend"; node: number; kids: [number, number, Inst][]; smooth: boolean; v: Slot | undefined }
  | { k: "sim"; node: number; kids: Inst[] }
  | { k: "seq"; node: number; kids: Inst[] };

/**
 * 커맨드 → 트리. 선택 노드(문자열·정수·bool)는 요청 시점 블랙보드로 한 번 고른다 [추정: 재평가 시점 미확정].
 * FloatBlend 는 자식을 모두 두고 가중치는 매 틱 계산한다(§4.4).
 */
export function instantiate(asb: Asb, cmd: string, bb: Blackboard, fps: FloatParamState, weaponAbbr: string, exists?: (clip: string, type: number) => boolean): Inst | null {
  const root = asb.commands[cmd];
  if (root === undefined) return null;
  const build = (i: number, depth: number): Inst | null => {
    const n = asb.nodes[i];
    if (!n || depth > 16) return null;
    switch (n.t) {
      case 3:
      case 11:
      case 18: {
        const raw = slotValue(n.clip, asb, bb, fps);
        const name = typeof raw === "string" ? raw : "";
        const ctrlIdx = n.attach?.ctrls.find((c) => asb.nodes[c]?.t === 12);
        const v = { detail: String(bb.str.get("WeaponDetail") ?? weaponAbbr), category: String(bb.str.get("WeaponCategory") ?? weaponAbbr), emote: "Win01" };
        const clip = exists ? nativeClipName(name, ASSUMED_CLIP_KEYS, v, (c) => exists(c, n.t)).clip : resolveClipName(name, weaponAbbr);
        return { k: "leaf", node: i, t: n.t, clip, ctrl: ctrlIdx === undefined ? null : asb.nodes[ctrlIdx] };
      }
      case 2: {
        // StringSelector: 일치하는 case, 없으면 その他(기본)
        const v = String(slotValue(n.v, asb, bb, fps) ?? "");
        const hit = n.cases?.find((c) => c[0] === v) ?? n.cases?.find((c) => c[0] === "その他") ?? n.cases?.[n.cases.length - 1];
        return hit ? build(hit[1], depth + 1) : null;
      }
      case 8: {
        // IntSelector: 일치하는 첫 값, 없으면 마지막 항목 [추정: 마지막 = 기본]
        const v = Number(slotValue(n.v, asb, bb, fps) ?? 0);
        const hit = n.cases?.find((c) => c[0] === v) ?? n.cases?.[n.cases.length - 1];
        return hit ? build(hit[1], depth + 1) : null;
      }
      case 21: {
        // BoolSelector: 자식 0 = 참, 1 = 거짓 [추정: WaitHold_Nrml(무기 듦) ↔ Wait]
        const v = !!slotValue(n.v, asb, bb, fps);
        const kid = n.kids?.[v ? 0 : 1];
        return typeof kid === "number" ? build(kid, depth + 1) : null;
      }
      case 6: {
        const kids: [number, number, Inst][] = [];
        for (const k of n.kids ?? []) {
          if (!Array.isArray(k)) continue;
          const c = build(k[2], depth + 1);
          if (c) kids.push([k[0], k[1], c]);
        }
        return { k: "blend", node: i, kids, smooth: !!n.smooth, v: n.v };
      }
      case 9:
      case 7: {
        const kids = (n.kids ?? []).map((k) => (typeof k === "number" ? build(k, depth + 1) : null)).filter((x): x is Inst => !!x);
        return { k: n.t === 9 ? "sim" : "seq", node: i, kids };
      }
      default:
        return null;
    }
  };
  return build(root, 0);
}

/** 노드 레코드 타입 0 = 블렌드 프레임 덮어쓰기(§2.3, §4.5). 루트 노드만 본다. */
export function nodeBlendFrames(asb: Asb, cmd: string, bb: Blackboard): number | null {
  const n = asb.nodes[asb.commands[cmd]];
  const r = n?.rec?.find((x) => x.type === 0);
  if (!r) return null;
  const v = Number(slotValue(r.v, asb, bb, null) ?? -1);
  return v >= 0 ? v : null;
}

/** FloatBlend 가중치(§4.4): [자식 인덱스, 가중치] 목록 */
export function floatBlendWeights(kids: [number, number, Inst][], x: number, smooth: boolean): [number, number][] {
  const n = kids.length;
  if (!n) return [];
  let i = kids.findIndex(([lo, hi]) => lo <= x && x < hi);
  if (i < 0) return [[x < kids[0][0] ? 0 : n - 1, 1]]; // 범위 밖: 마지막 자식(아래쪽이면 0번) [판독: "마지막 자식(또는 0번)"]
  if (i + 1 < n) {
    const [lo0, hi0] = kids[i], [lo1, hi1] = kids[i + 1];
    const lo = Math.max(lo0, lo1), hi = Math.min(hi0, hi1);
    if (hi > lo) {
      let w = (x - lo) / (hi - lo);
      if (w < 0.01) w = 0;
      if (w > 0.99) w = 1;
      if (smooth) w = ss(ss(w));
      return [[i, 1 - w], [i + 1, w]];
    }
  }
  return [[i, 1]];
}

const ss = (x: number): number => x * x * (3 - 2 * x);
