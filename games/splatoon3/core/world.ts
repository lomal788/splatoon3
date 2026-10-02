// 고정 60Hz 스텝 월드. 시스템은 등록 순서대로 step 된다(순서는 core/systems.ts, 근거는 DESIGN.md).
import { EventQueue } from "./events.ts";
import { emptyPad, type PadState } from "./input.ts";
import type { ParamStore } from "./params.ts";
import { SeadRandom } from "./rng.ts";
import type { CollisionWorld, Hittable, PaintWorld } from "./types.ts";

export interface System {
  readonly id: string;
  init?(w: World): void;
  step(w: World): void;
}

/** 클라이언트가 읽어 넘기는 경기 데이터(에셋에서 읽은 JSON). 코어는 fetch 하지 않는다. */
export interface MatchData {
  map: string;
  /** map placement.json */
  placement: unknown;
  /** collision.json + 이진 버퍼 */
  collision: unknown;
  params: ParamStore;
  /** data/*.json (상수·표) — 키는 파일 이름 */
  tables: Record<string, unknown>;
  players: { character: string; weapon: string; team: 0 | 1 | 2 }[];
}

export class World {
  frame = 0;
  readonly rng: SeadRandom;
  readonly events = new EventQueue();
  readonly data: MatchData;
  /** 로컬 조작 플레이어의 입력. 멀티플레이 땐 플레이어별로 바뀐다. */
  pad: PadState = emptyPad();
  readonly systems: System[] = [];
  readonly hittables = new Map<number, Hittable>();
  collision: CollisionWorld | null = null;
  paint: PaintWorld | null = null;
  /** 영역 간에 공유하는 상태(예: "player", "camera"). 키 이름은 DESIGN.md 에 등록. */
  readonly shared = new Map<string, unknown>();
  private nextId = 1;

  constructor(data: MatchData, seed = 0) {
    this.data = data;
    this.rng = new SeadRandom(seed);
  }

  newId(): number {
    return this.nextId++;
  }

  add(sys: System): void {
    this.systems.push(sys);
  }

  init(): void {
    for (const s of this.systems) s.init?.(this);
  }

  step(pad: PadState): void {
    this.pad = pad;
    this.events.clear();
    for (const s of this.systems) s.step(this);
    this.frame++;
  }
}
