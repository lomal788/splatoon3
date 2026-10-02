// 무기 InkAction → XLink 액션 슬롯 0 (머즐 플래시). 근거: docs/effect_sound/effect_sound.md §3.2.
//   setInkAction 0x7102864104 · 보류 적용 WeaponShooter vtable 슬롯 19 0x710286540c
export const INK_ACTION_NAMES = [
  "FireImpact",
  "FireOn",
  "FireOff",
  "FireFailed",
  "PaintOn",
  "PaintOff",
  "PaintNoInk",
  "FireCanopy",
  "RecoverCanopy",
  "SideStep",
  "StepSaber",
  "ChargeSpinner",
  "ChargeSaber",
  "BlowerInhaleOff",
  "BlowerInhaleOn",
  "Unknown",
];
const NONE = 0xf;

export interface ActionTarget {
  /** ELink·SLink 양쪽 TriggerCtrlMgr 에 (이름, 시작 프레임, 슬롯 0) — 0x710389b61c */
  changeAction(slot: string, name: string, startFrame: number): void;
}

export class InkActionState {
  /** 무기 +0x320 현재 액션(-1 = 아직 없음) */
  action = -1;
  /** +0x384 보류 */
  pending = NONE;
  /** +0x374 마지막 즉시 변경 프레임 */
  lastImpact = -1;
  /** +0x380 FireOn 연속 프레임 */
  onFrames = 0;
  private readonly targets: ActionTarget[];

  constructor(targets: ActionTarget[]) {
    this.targets = targets;
  }

  private apply(id: number): void {
    this.action = id;
    // 액션 시작 프레임 = 무기 +0x324(int) — 값의 출처는 미추적, 0 으로 둔다
    for (const t of this.targets) t.changeAction("State[0]", INK_ACTION_NAMES[id], 0);
  }

  /** 0x7102864104 */
  set(id: number, now: number): void {
    const t = Math.max(now, 0);
    if (id !== 0) {
      if (t <= this.lastImpact) return; // 같은 프레임에 FireImpact 가 있었으면 무시
      if (id < 7 || id > 10) {
        this.pending = id; // 보류(적용은 슬롯 19)
        return;
      }
    }
    if (this.action !== id) {
      this.apply(id);
      this.lastImpact = Math.max(this.lastImpact, t);
    }
  }

  /**
   * 0x710286540c: 보류 적용. FireOn 최소 유지(+0x380 < (*(무기+0x368))->vt+0x148()) 는 그 값의 출처를 못 찾아 적용하지 않는다.
   * 이 슬롯을 부르는 프레임 내 시점은 [미확정] — 웹은 프레임 끝에 부른다.
   */
  applyPending(): void {
    if (this.pending !== NONE && this.pending !== this.action) this.apply(this.pending);
    this.pending = NONE;
    this.onFrames = this.action === 1 ? this.onFrames + 1 : 0;
  }
}
