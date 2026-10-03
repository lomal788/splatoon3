// 키보드·마우스 → PadState. 원본은 조이콘(스틱·자이로)이라 대응은 웹 이식 차이로 DESIGN.md "입력" 절에 기록.
// 고정 스텝마다 sample() 로 한 프레임 분량을 뽑는다(마우스 이동은 누적 후 소비).
// 마우스 → 조준 대응식과 근거는 docs/impl/camera.md "입력 이식 차이".
import { pitchMaxDeg, yawMaxDeg } from "../core/camera/pitch.ts";
import { Btn, emptyPad, type PadState } from "../core/input.ts";

/** 감도 기준: 원본 감도 0(k=0)의 스틱 최대 yaw 4°/프레임(240°/s)을 마우스 1600px/s 에 맞춘 값(°/px) [웹 선택]. */
export const MOUSE_BASE_DEG_PER_PX = 0.15;

export interface CameraInputSettings {
  /** 원본 카메라 감도 UI -5..+5 (0.5 단위). k = sens/5 */
  sens: number;
  /** 마우스 DPI 보정 배율(웹 전용) */
  mouseScale: number;
  /** IsReverseLR / IsReverseUD 대응 */
  invertX: boolean;
  invertY: boolean;
}

const STORE = "splatoon3.camera.";

export function defaultCameraSettings(): CameraInputSettings {
  return { sens: 0, mouseScale: 1, invertX: false, invertY: false };
}

export function loadCameraSettings(): CameraInputSettings {
  const s = defaultCameraSettings();
  try {
    const num = (k: string, lo: number, hi: number, d: number): number => {
      const v = Number(localStorage.getItem(STORE + k));
      return localStorage.getItem(STORE + k) === null || !Number.isFinite(v) ? d : Math.min(hi, Math.max(lo, v));
    };
    s.sens = Math.round(num("sens", -5, 5, 0) * 2) / 2;
    s.mouseScale = num("mouseScale", 0.05, 20, 1);
    s.invertX = localStorage.getItem(STORE + "invertX") === "1";
    s.invertY = localStorage.getItem(STORE + "invertY") === "1";
  } catch {
    /* 저장소 접근 불가: 기본값 */
  }
  return s;
}

export function saveCameraSettings(s: CameraInputSettings): void {
  try {
    localStorage.setItem(STORE + "sens", String(s.sens));
    localStorage.setItem(STORE + "mouseScale", String(s.mouseScale));
    localStorage.setItem(STORE + "invertX", s.invertX ? "1" : "0");
    localStorage.setItem(STORE + "invertY", s.invertY ? "1" : "0");
  } catch {
    /* 저장 실패는 무시 */
  }
}

/**
 * 마우스 이동(px) → [lookYaw, lookPitch](라디안).
 * lookYaw = 조준 yaw 회전량(양수 = 왼쪽, 원본 rotateY 부호), lookPitch = 피치 누적각(+0x150c) 변화량(양수 = 위).
 * 원본 감도 k 의 비율을 그대로 쓴다: yaw ∝ yawMax(k)/yawMax(0), 피치 ∝ pitchMax(k)/yawMax(0).
 */
export function mouseToLook(dx: number, dy: number, s: CameraInputSettings): [number, number] {
  const k = Math.min(1, Math.max(-1, s.sens / 5));
  const base = MOUSE_BASE_DEG_PER_PX * s.mouseScale * (Math.PI / 180);
  const yaw = -dx * base * (yawMaxDeg(k) / yawMaxDeg(0)) * (s.invertX ? -1 : 1);
  const pitch = -dy * base * (pitchMaxDeg(k) / yawMaxDeg(0)) * (s.invertY ? -1 : 1);
  return [yaw, pitch];
}

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
  settings: CameraInputSettings = loadCameraSettings();
  private readonly keys = new Set<string>();
  private readonly el: HTMLElement;
  private mouseButtons = 0;
  private dx = 0;
  private dy = 0;
  private prevHold = 0;
  private focused = true;

  constructor(el: HTMLElement) {
    this.el = el;
    addEventListener("keydown", this.onKey);
    addEventListener("keyup", this.onKey);
    addEventListener("blur", this.onBlur);
    addEventListener("focus", this.onFocus);
    document.addEventListener("pointerlockchange", this.onPointerLockChange);
    document.addEventListener("visibilitychange", this.onVisibilityChange);
    addEventListener("mouseup", this.onMouseUp);
    addEventListener("mousemove", this.onMouseMove);
    el.addEventListener("mousedown", this.onMouseDown);
    el.addEventListener("contextmenu", this.onContextMenu);
  }

  get locked(): boolean {
    return document.pointerLockElement === this.el;
  }

  /** Split a render frame's pending displacement across its remaining fixed steps.
   * No magnitude clamp: every finite displacement is consumed exactly once. */
  sample(remainingSteps = 1): PadState {
    const p = emptyPad();
    p.lookMode = "mouse";
    if (!this.ownsInput()) this.clearPending();
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
    const steps = Number.isFinite(remainingSteps) ? Math.max(1, Math.floor(remainingSteps)) : 1;
    const dx = this.dx / steps, dy = this.dy / steps;
    [p.lookYaw, p.lookPitch] = mouseToLook(dx, dy, this.settings);
    this.dx -= dx;
    this.dy -= dy;
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

  setSettings(next: CameraInputSettings): void {
    const old = this.settings;
    this.settings = {
      sens: Number.isFinite(next.sens) ? Math.round(Math.min(5, Math.max(-5, next.sens)) * 2) / 2 : old.sens,
      mouseScale: Number.isFinite(next.mouseScale) ? Math.min(20, Math.max(.05, next.mouseScale)) : old.mouseScale,
      invertX: !!next.invertX, invertY: !!next.invertY,
    };
    saveCameraSettings(this.settings);
  }

  dispose(): void {
    removeEventListener("keydown", this.onKey);
    removeEventListener("keyup", this.onKey);
    removeEventListener("blur", this.onBlur);
    removeEventListener("focus", this.onFocus);
    document.removeEventListener("pointerlockchange", this.onPointerLockChange);
    document.removeEventListener("visibilitychange", this.onVisibilityChange);
    removeEventListener("mouseup", this.onMouseUp);
    removeEventListener("mousemove", this.onMouseMove);
    this.el.removeEventListener("mousedown", this.onMouseDown);
    this.el.removeEventListener("contextmenu", this.onContextMenu);
    this.clearPending();
  }

  private onKey = (e: KeyboardEvent): void => {
    if (e.type === "keydown" && this.ownsInput()) this.keys.add(e.code);
    else this.keys.delete(e.code);
    if (e.code === "Space") e.preventDefault();
  };

  private ownsInput(): boolean {
    return this.locked && this.focused && document.visibilityState !== "hidden";
  }

  private clearPending(): void {
    this.keys.clear();
    this.mouseButtons = 0;
    this.dx = this.dy = 0;
    // Keep prevHold for one sample, so held actions receive their release edge.
  }

  private onBlur = (): void => {
    this.focused = false;
    this.clearPending();
  };
  private onFocus = (): void => { this.focused = true; };
  private onPointerLockChange = (): void => { this.clearPending(); };
  private onVisibilityChange = (): void => {
    if (document.visibilityState === "hidden") this.clearPending();
  };

  private onMouseDown = (e: MouseEvent): void => {
    if (!this.locked) {
      void this.el.requestPointerLock();
      return;
    }
    if (this.ownsInput()) this.mouseButtons |= 1 << e.button;
  };

  private onMouseUp = (e: MouseEvent): void => {
    this.mouseButtons &= ~(1 << e.button);
  };

  private onMouseMove = (e: MouseEvent): void => {
    if (!this.ownsInput()) return;
    if (Number.isFinite(e.movementX)) this.dx += e.movementX;
    if (Number.isFinite(e.movementY)) this.dy += e.movementY;
  };

  private onContextMenu = (e: Event): void => {
    e.preventDefault();
  };
}
