// WebAudio 재생기 = XLink SLink 의 sink. 근거: docs/effect_sound/sound_resources.md §4.2(감쇠), §4.3(그룹), §5(파라미터).
import type { FxData } from "./data.ts";
import { evalAadr, evalAroc, evalAudc, limiterOrder, normDist, type AttnSet } from "./alto.ts";
import type { EmitContext, XAsset, XHandle, XSink } from "./xlink.ts";

type V3 = [number, number, number];

export interface Listener {
  pos: V3;
  /** 청자 오른쪽 축(패닝용) */
  right: V3;
}

interface Voice {
  seq: number;
  group: string;
  priority: number;
  src: AudioBufferSourceNode | null;
  gain: GainNode;
  pan: StereoPannerNode;
  pos: V3 | null;
  /** 음원 로컬 +Z(월드). AADR 지향성용 */
  z: V3 | null;
  set: AttnSet | null;
  distCoef: number;
  base: number;
  ended: boolean;
  endCbs: (() => void)[];
  virtualUntil: number;
  name: string;
}

export interface SoundLogEntry {
  t: number;
  key: string;
  name: string;
  vol: number;
  pitch: number;
  dist: number | null;
  gain: number;
  group: string;
  played: boolean;
}

/** 소리가 없을 때 시간 흐름만 흉내 내는 길이(초). Sequence 진행용 — 원본 값 아님(웹 개발용). */
const VIRTUAL_LEN = 0.3;

export class SoundPlayer implements XSink {
  private readonly ac: AudioContext;
  private readonly data: FxData;
  private readonly out: GainNode;
  private readonly voices: Voice[] = [];
  private seq = 0;
  listener: Listener = { pos: [0, 0, 0], right: [1, 0, 0] };
  readonly log: SoundLogEntry[] = [];

  constructor(ac: AudioContext, data: FxData) {
    this.ac = ac;
    this.data = data;
    this.out = ac.createGain();
    this.out.connect(ac.destination);
  }

  private dist(pos: V3 | null): number | null {
    if (!pos) return null;
    const l = this.listener.pos;
    return Math.hypot(pos[0] - l[0], pos[1] - l[1], pos[2] - l[2]);
  }

  /** 거리·지향성 이득 (0x7103863fe8 순서: 볼륨 AROC → 지향성 곱). AACL 컬링은 +0x50 = 0 이라 곱하지 않음. */
  private spatial(v: Voice): { gain: number; pan: number } {
    if (!v.pos || !v.set) return { gain: 1, pan: 0 };
    const l = this.listener.pos;
    const dx = l[0] - v.pos[0], dy = l[1] - v.pos[1], dz = l[2] - v.pos[2];
    const d = normDist(Math.hypot(dx, dy, dz), v.distCoef);
    let g = v.set.volume ? evalAroc(v.set.volume, d) : 1;
    if (v.set.directivity && v.z) g *= evalAadr(v.set.directivity, v.z, [dx, dy, dz]).gain;
    if (Math.abs(g) <= 3.05e-5) g = 0;
    // 패닝: 원본 스피커 배분 식은 판독하지 않았다. 청자 오른쪽 축 성분으로 근사(웹 근사).
    const len = Math.hypot(dx, dy, dz);
    const r = this.listener.right;
    const pan = len > 1e-6 ? -(dx * r[0] + dy * r[1] + dz * r[2]) / len : 0;
    return { gain: g, pan: Math.max(-1, Math.min(1, pan)) };
  }

  play(a: XAsset, ctx: EmitContext): XHandle | null {
    const p = a.params;
    const num = (k: string, d: number): number => {
      const x = p[k];
      return typeof x === "number" && Number.isFinite(x) ? x : d;
    };
    const vol = num("Volume", 1);
    const pitch = num("Pitch", 1);
    const delayF = num("Delay", 0);
    const setName = String(p.DistanceParamSetName ?? "");
    const set = setName ? this.data.attn[setName] ?? null : null;
    const distCoef = num("DistCoef", 10);
    const group = String(p.GroupName ?? ctx.group ?? "");
    const pos = (ctx.pos as V3 | undefined) ?? null;
    const z = (ctx.dir as V3 | undefined) ?? null;
    const buf = this.data.sounds.get(a.name) ?? null;
    const now = this.ac.currentTime;

    const gain = this.ac.createGain();
    const pan = this.ac.createStereoPanner();
    gain.connect(pan).connect(this.out);
    const v: Voice = {
      seq: ++this.seq,
      group,
      priority: 0,
      src: null,
      gain,
      pan,
      pos,
      z,
      set,
      distCoef,
      base: vol,
      ended: false,
      endCbs: [],
      virtualUntil: 0,
      name: a.name,
    };
    const sp = this.spatial(v);
    // 우선순위(제한기 정렬값): Priority × AUDC 거리 우선순위 [추정, alto.ts 참고]
    const dd = this.dist(pos);
    v.priority = num("Priority", 0.5) * (set?.priority && dd !== null ? evalAudc(set.priority, normDist(dd, distCoef)) : 1);
    gain.gain.value = vol * sp.gain;
    pan.pan.value = sp.pan;
    const when = now + Math.max(0, delayF) / 60; // Delay 단위 = 프레임 [추정]
    if (buf) {
      const src = this.ac.createBufferSource();
      src.buffer = buf;
      src.playbackRate.value = pitch > 0 ? pitch : 1; // Pitch = 재생 속도 비율 [추정]
      src.connect(gain);
      src.onended = () => this.finish(v);
      src.start(when);
      v.src = src;
    } else {
      v.virtualUntil = when + VIRTUAL_LEN;
    }
    this.voices.push(v);
    this.log.push({ t: now, key: a.key, name: a.name, vol, pitch, dist: dd, gain: sp.gain, group, played: !!buf });
    if (this.log.length > 200) this.log.splice(0, this.log.length - 200);
    this.applyLimit(group);
    return {
      alive: () => !v.ended,
      fade: () => this.stop(v),
      onEnd: (cb) => {
        if (v.ended) cb();
        else v.endCbs.push(cb);
      },
    };
  }

  private applyLimit(group: string): void {
    const rule = this.data.groups[group];
    if (!rule || rule.limiterType <= 0 || rule.limitCount < 0) return;
    const live = this.voices.filter((x) => x.group === group && !x.ended);
    if (live.length <= rule.limitCount) return;
    const order = limiterOrder(rule.limiterType, live);
    for (const x of order.slice(rule.limitCount)) this.stop(x);
  }

  private stop(v: Voice): void {
    if (v.ended) return;
    if (v.src) {
      // 원본 페이드 시간은 미확인 — 클릭을 피하는 짧은 램프(웹 근사)
      const t = this.ac.currentTime;
      v.gain.gain.cancelScheduledValues(t);
      v.gain.gain.setValueAtTime(v.gain.gain.value, t);
      v.gain.gain.linearRampToValueAtTime(0, t + 0.01);
      try {
        v.src.stop(t + 0.012);
      } catch {
        this.finish(v);
      }
    } else this.finish(v);
  }

  private finish(v: Voice): void {
    if (v.ended) return;
    v.ended = true;
    v.gain.disconnect();
    v.pan.disconnect();
    const cbs = v.endCbs.splice(0);
    for (const cb of cbs) cb();
  }

  /** 매 프레임: 청자 이동에 따른 감쇠 재계산(원본도 음원 계산을 매 프레임 한다), 가상 보이스 종료. */
  update(): void {
    const t = this.ac.currentTime;
    for (const v of this.voices) {
      if (v.ended) continue;
      if (!v.src && t >= v.virtualUntil) {
        this.finish(v);
        continue;
      }
      if (v.pos && v.set) {
        const sp = this.spatial(v);
        v.gain.gain.setTargetAtTime(v.base * sp.gain, t, 0.01);
        v.pan.pan.setTargetAtTime(sp.pan, t, 0.01);
      }
    }
    for (let i = this.voices.length - 1; i >= 0; i--) if (this.voices[i].ended) this.voices.splice(i, 1);
  }

  activeCount(): number {
    return this.voices.length;
  }
}
