// 플레이어 애니 구동: 상태 번호 → ASB 커맨드(사람/오징어 래퍼), 블랙보드 공급, 표시 모델 선택(몸/_Hlf/오징어).
// 근거: player_state.md §4·§5.3·§6.2, anim_state_machine.md §4, player_assembly.md §5.4.
// 이 파일은 표시만 결정한다. 상태 전이(ToSquid→0x84 등)는 core/player(physics)의 일이고, 여기서는 받은 상태 번호를 따른다.
import { Blackboard, HUMAN_ASB, SQUID_ASB, stateRow } from "./asb.ts";
import { type ClipInfo, type LeafWeight, Wrapper } from "./slot.ts";
import { nativeJumpVarId } from "./jump_var.ts";
import { nativeSmDisplay, nativeHolderDisplay, type DisplayResetTarget } from "../../../core/player/display.ts";

export interface AnimInput {
  state: number;
  /** SM+0xd4 이동 애니 속도값(유닛/프레임). 없으면 수평 속력 */
  speed: number;
  dead: boolean;
  /** physics 가 SM+0xf0 을 주면 그 값 */
  formCounter: number | null;
  /** physics 가 요청 재생 속도를 주면 그 값 */
  animRate: number | null;
  /** B7a0 supplied by the simulation. Absent is the legacy display adapter. */
  displayHidden?: boolean | null;
}

export interface Display {
  body: boolean;
  hlf: boolean;
  squid: boolean;
}

const BIT3 = 0x8, BIT17 = 0x20000, BIT18 = 0x40000;
/** (c) 사람·오징어 둘 다 켜졌을 때 오징어를 끄는 상태 (player_assembly.md §5.4) */

export class PlayerAnimator {
  readonly bb = new Blackboard();
  readonly human: Wrapper;
  readonly squid: Wrapper;
  active: Wrapper | null = null;
  state = -1;
  prevState = -1;
  /** SM+0xf0 */
  f0 = 0;
  /** SM+0xe0 (MoveSpeedRt) */
  moveSpeedRt = 0;
  disp: Display = { body: true, hlf: false, squid: false };
  /** Native binder reset targets; type11/live material setter is still unbound. Wrappers continue ticking. */
  displayResets: DisplayResetTarget[] = [];
  /** 몸 튀어나옴 스프링 0x71014586a0: x, v */
  spring = { x: 0, v: 0 };
  readonly rival: boolean;
  /** Active wrapper +0x10 (blackboard JumpVarID). */
  jumpVarId = 0;
  /** Main weapon kind K in mask 0x0637b2ef (K-4 < 27). Shooter K = 1/2/8 [추정] is outside it. */
  weaponKindMasked = false;

  constructor(humanClips: ClipInfo, squidClips: ClipInfo, weaponAbbr: string, rival = false) {
    this.rival = rival;
    this.human = new Wrapper(HUMAN_ASB, this.bb, humanClips, weaponAbbr);
    this.squid = new Wrapper(SQUID_ASB, this.bb, squidClips, weaponAbbr);
    // 블랙보드 고정값 (anim_state_machine.md §4.6)
    this.bb.bool.set("EquipWeaponMain", true); // 메인 무기 있음 [추정: 슈터 = 참]
    // Selected ordinary shooter supplies Shtr/Shtr to both wrappers and BB (native 2491758/249cb60/24bb240).
    // This practice view keeps its selected weapon; holder-null/reset source lifetimes remain separate.
    this.bb.str.set("WeaponCategory", weaponAbbr);
    this.bb.str.set("WeaponDetail", weaponAbbr);
    this.bb.int.set("JumpVarID", 0); // 초기화 0x710243dcf8 가 0
    this.bb.float.set("StainFrm", 0); // 유일한 쓰기가 0.0
  }

  /** 한 게임 프레임(60Hz). 원본 순서: 상태 판정 → 블랙보드 공급 → 래퍼 틱 → 표시 플래그 */
  step(inp: AnimInput): void {
    if (inp.state !== this.state) this.change(inp.state, inp);
    else if (this.state === 0x87 && inp.animRate === null) this.squid.slotRate = requestRate(0x87, inp.speed); // 매 프레임 갱신 [추정]
    this.supplyBlackboard(inp);
    if (inp.formCounter === null) this.counterA();
    else this.f0 = inp.formCounter;
    this.human.tick(1);
    this.squid.tick(1);
    this.displayFlags(inp);
    this.tickSpring();
  }

  private change(s: number, inp: AnimInput): void {
    const row = stateRow(s);
    this.prevState = this.state;
    this.state = s;
    if (!row || !row.cmd) return;
    const target = row.squid ? this.squid : this.human;
    const other = row.squid ? this.human : this.squid;
    // 표시만 남은 래퍼는 다음 요청에서 정지 [추정]
    if (other.displayOnly) other.stop();
    if (other.cmd !== -1) {
      if (row.flags & BIT3) other.displayOnly = true; // 이전 ASB 유지(래퍼+0x38=1)
      else other.stop(); // 0x710244f084
    }
    // SM+0xf0 다른 쓰기(§5.4 (a))
    if (inp.formCounter === null) {
      if (s === 0x82 || s === 0x83) this.f0 = Math.max(this.f0, 30);
      else if (s === 0x91) this.f0 = 90;
      else if (s === 0x96 && this.prevState === 0x86) this.f0 = 140;
      else if (s === 0xe9 || s === 0xea) this.f0 = 107;
    }
    if (s >= 0x99 && s <= 0xa9) {
      this.jumpVarId = nativeJumpVarId(this.jumpVarId, this.prevState, s, inp.speed, this.weaponKindMasked);
      this.bb.int.set("JumpVarID", this.jumpVarId);
    }
    target.request(s, row.cmd, row.blend, inp.animRate ?? requestRate(s, inp.speed));
    this.active = target;
  }

  /** 0x710246cb58 블랙보드 공급(§4.6) */
  private supplyBlackboard(inp: AnimInput): void {
    // MoveSpeedRt: e0 += 0.2·(목표 − e0), 목표 = clamp((v − 0.027)/0.023, 0, 1). 사람 이동 상태 0x5e~0x81 이 아니면 0
    if (this.state >= 0x5e && this.state <= 0x81) {
      const target = Math.max(0, Math.min(1, (inp.speed - 0.027) / 0.023));
      this.moveSpeedRt += 0.2 * (target - this.moveSpeedRt);
    } else this.moveSpeedRt = 0;
    this.bb.float.set("MoveSpeedRt", this.moveSpeedRt);
  }

  /** (a) 0x710243e7d0 끝 — 과도기 카운터 */
  private counterA(): void {
    const s = this.state;
    if (s >= 0x82 && s <= 0x84) this.f0 += 10;
    else {
      const fl = stateRow(s)?.flags ?? 0;
      if (fl & BIT17) this.f0 = Math.min(this.f0, 70);
      if (fl & BIT18) this.f0 = Math.min(this.f0, 83); // 보조 상태의 bit18 은 미반영
      this.f0 = Math.max(this.f0, 1) - 1;
    }
  }

  /** (b) 0x710243e2dc + (c) 홀더 0x71014595b0 */
  private displayFlags(inp: AnimInput): void {
    const before = this.disp;
    const old = { ...before, rail: false };
    const sm = nativeSmDisplay({ hidden: inp.displayHidden ?? false, humanCommand: this.human.cmd !== -1,
      squidCommand: this.squid.cmd !== -1, formCounter: this.f0, modelKind: this.rival ? 4 : 0,
      dead: inp.dead, state: this.state, old });
    this.f0 = sm.formCounter;
    this.displayResets = sm.reset;
    // Ordinary local practice holder adapter: life/timing/special producers are absent.
    // Whole consumer is tested independently; these adapter inputs are not native runtime captures.
    let { body, hlf, squid } = nativeHolderDisplay(sm.flags, { state: this.state, previousState: this.prevState,
      cur: this.active?.progress()?.cur ?? 1, old, de0: 0, df0: 0, e04: 0, e0c: 0, e1c: 0, d60: 0, d5c: 0,
      life30: false, life31: false, life35: !inp.dead, life38: 0, debug: false,
      special: 0, selected: false, specialDisabled: false });
    // 아무 모델도 켜지지 않은 초기 프레임: 몸
    if (!body && !hlf && !squid && !inp.dead && this.state < 0) body = true;
    this.disp = { body, hlf, squid };
    // 몸만 보이는 상태로 바뀌는 순간(0→1) 스프링 시작 [추정: 트리거 해석]
    if (body && !before.body) {
      this.spring.x = -0.03;
      this.spring.v += 0.02;
    }
  }

  /** 0x71014586a0: v = (v − 0.2x)·0.8; x += v */
  private tickSpring(): void {
    const s = this.spring;
    s.v = (s.v - 0.2 * s.x) * 0.8;
    s.x += s.v;
  }

  /** 몸·_Hlf 스케일: +0x268/+0x270 = 1 + 1.5x, +0x26c = 1 + x [축 대응은 추정] */
  springScale(): [number, number, number] {
    const x = this.spring.x;
    return [1 + 1.5 * x, 1 + x, 1 + 1.5 * x];
  }

  humanLeaves(alpha: number): LeafWeight[] {
    return this.human.cmd === -1 ? [] : this.human.leaves(alpha);
  }

  squidLeaves(alpha: number): LeafWeight[] {
    return this.squid.cmd === -1 ? [] : this.squid.leaves(alpha);
  }
}

/**
 * 상태 요청 재생 속도(0x7102447bfc 의 rate). 판독된 것만:
 *   0x87 오징어 Walk: v ≤ 0.001 ? 0.05 : v ≥ 0.04 ? 1 : 0.05 + 0.95(v−0.001)/0.039 (player_state.md §6.3 I2)
 *   착지 0x8c 1.0, 0xa6/0xa7 0.7 (§6.3 착지)
 * 나머지(사람 걷기 재생 속도식 등)는 [미확정] → 1.
 */
function requestRate(s: number, v: number): number {
  if (s === 0x87) return v <= 0.001 ? 0.05 : v >= 0.04 ? 1 : 0.05 + (0.95 * (v - 0.001)) / 0.039;
  if (s === 0xa6 || s === 0xa7) return 0.7;
  return 1;
}
