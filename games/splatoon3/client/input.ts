// 키보드·마우스 → PadState. 원본은 조이콘(스틱·자이로)이라 대응은 웹 이식 차이로 DESIGN.md "입력" 절에 기록.
// 고정 스텝마다 sample() 로 한 프레임 분량을 뽑는다(마우스 이동은 누적 후 소비).
import { Btn, emptyPad, type PadState } from "../core/input.ts";

const KEYS: Record<string, number> = {
  Space: Btn.Jump,
  ShiftLeft: Btn.Squid,
  ShiftRight: Btn.Squid,
  KeyE: Btn.Sub,
  KeyQ: Btn.Special,
  KeyM: Btn.Map,
  KeyR: Btn.Reset,
};

export class InputDevice {
  /** 마우스 1픽셀당 라디안. 원본 감도와의 대응은 camera 담당이 조정한다. */
  sensitivity = 0.0025;
  invertY = false;
  private readonly keys = new Set<string>();
  private readonly el: HTMLElement;
  private mouseButtons = 0;
  private dx = 0;
  private dy = 0;
  private prevHold = 0;

  constructor(el: HTMLElement) {
    this.el = el;
    addEventListener("keydown", this.onKey);
    addEventListener("keyup", this.onKey);
    addEventListener("blur", this.onBlur);
    addEventListener("mouseup", this.onMouseUp);
    addEventListener("mousemove", this.onMouseMove);
    el.addEventListener("mousedown", this.onMouseDown);
    el.addEventListener("contextmenu", this.onContextMenu);
  }

  get locked(): boolean {
    return document.pointerLockElement === this.el;
  }

  sample(): PadState {
    const p = emptyPad();
    const k = (c: string): number => (this.keys.has(c) ? 1 : 0);
    let x = k("KeyD") - k("KeyA");
    let y = k("KeyW") - k("KeyS");
    const l = Math.hypot(x, y);
    if (l > 1) {
      x /= l;
      y /= l;
    }
    p.moveX = x;
    p.moveY = y;
    p.lookYaw = -this.dx * this.sensitivity;
    p.lookPitch = (this.invertY ? 1 : -1) * this.dy * this.sensitivity;
    this.dx = this.dy = 0;
    let hold = 0;
    for (const [code, bit] of Object.entries(KEYS)) if (this.keys.has(code)) hold |= bit;
    if (this.mouseButtons & 1) hold |= Btn.Fire; // 왼쪽 버튼 = ZR
    if (this.mouseButtons & 4) hold |= Btn.Sub; // 오른쪽 버튼 = R
    p.hold = hold;
    p.trigger = hold & ~this.prevHold;
    p.release = this.prevHold & ~hold;
    this.prevHold = hold;
    return p;
  }

  dispose(): void {
    removeEventListener("keydown", this.onKey);
    removeEventListener("keyup", this.onKey);
    removeEventListener("blur", this.onBlur);
    removeEventListener("mouseup", this.onMouseUp);
    removeEventListener("mousemove", this.onMouseMove);
    this.el.removeEventListener("mousedown", this.onMouseDown);
    this.el.removeEventListener("contextmenu", this.onContextMenu);
  }

  private onKey = (e: KeyboardEvent): void => {
    if (e.type === "keydown") this.keys.add(e.code);
    else this.keys.delete(e.code);
    if (e.code === "Space") e.preventDefault();
  };

  private onBlur = (): void => {
    this.keys.clear();
    this.mouseButtons = 0;
  };

  private onMouseDown = (e: MouseEvent): void => {
    if (!this.locked) {
      void this.el.requestPointerLock();
      return;
    }
    this.mouseButtons |= 1 << e.button;
  };

  private onMouseUp = (e: MouseEvent): void => {
    this.mouseButtons &= ~(1 << e.button);
  };

  private onMouseMove = (e: MouseEvent): void => {
    if (!this.locked) return;
    this.dx += e.movementX;
    this.dy += e.movementY;
  };

  private onContextMenu = (e: Event): void => {
    e.preventDefault();
  };
}
