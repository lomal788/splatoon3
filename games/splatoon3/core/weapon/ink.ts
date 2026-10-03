// 잉크 소비/정지/회복 소비자. shooter_bullet §5.5, ink_consume.c 및 player_slot19.c 재사용.
import { f32 } from "../fmath.ts";
export interface InkState {
  ink: number;
  inkRecoverStop: number; // B6a8
  inkRecoverStopNoInk: number; // B6ac
  inkRecoverStopSquid: number; // B6b0
  inkConsumeHold: number; // B6b4
  inkStealthFrames: number; // B6b8
  inkStealthBlend: number; // B6bc
}
export const INK_RECOVER_STD = f32(1 / 600);
export const INK_RECOVER_STEALTH = f32(1 / 180);
/** 2353718. 슈터 squid 인자는 0. 성공이면 B6b4도 설정한다. */
export function stopInk(s: InkState, frames: number, ok: boolean, squid = false): void {
  const key = squid ? "inkRecoverStopSquid" : "inkRecoverStop";
  s[key] = Math.max(s[key], frames | 0);
  if (ok) s.inkConsumeHold = Math.trunc(f32(f32(0.33) * f32(s[key])));
}
export function lackInk(s: InkState, frames: number): void {
  s.inkRecoverStopNoInk = Math.max(s.inkRecoverStopNoInk, frames | 0);
}
export function consumedInk(s: InkState): void { s.inkStealthFrames = 0; s.inkStealthBlend = 0; }
export function inkRecoveryRate(blend: number, stdFrames = 600, stealthFrames = 180, disabled = false): number {
  return disabled ? 0 : f32(1 / f32(blend > 0 ? stealthFrames : stdFrames));
}
export interface InkRecoveryInput {
  state: number; fastStealth: boolean; airFrames: number;
  /** 6d8 등 상위 회복 차단. 현재 일반 Lobby adapter는 false. */
  disabled?: boolean; blocked?: boolean;
  stdFrames?: number; stealthFrames?: number;
}
/** 슬롯19 248ed.. 소비 블록: 감소 전 max를 검사한 뒤 세 s32를 음수까지 감소. */
export function recoverInk(s: InkState, i: InkRecoveryInput): void {
  if (i.blocked) return;
  const stop = Math.max(s.inkRecoverStop, s.inkRecoverStopNoInk, s.inkRecoverStopSquid);
  s.inkRecoverStop = (s.inkRecoverStop - 1) | 0;
  s.inkRecoverStopNoInk = (s.inkRecoverStopNoInk - 1) | 0;
  s.inkRecoverStopSquid = (s.inkRecoverStopSquid - 1) | 0;
  if (stop >= 1) return;
  const n = i.state | 0;
  const stealthState = (n >= 0x82 && n < 0x91) || (n >= 0xaa && n < 0xad) || n === 0xed || n === 0xee || n === 0x10c;
  if (stealthState && i.fastStealth) {
    s.inkStealthFrames = (s.inkStealthFrames + 1) | 0; s.inkStealthBlend = 1;
  } else if (stealthState) {
    const next = f32(s.inkStealthBlend - (i.airFrames >= 4 ? f32(1 / 60) : f32(0.1)));
    s.inkStealthBlend = next > 0 ? next : 0;
    if (next <= 0) consumedInk(s);
  } else consumedInk(s);
  const rate = inkRecoveryRate(s.inkStealthBlend, i.stdFrames, i.stealthFrames, i.disabled);
  if (s.ink < 1) s.ink = Math.min(1, f32(s.ink + Math.min(rate, f32(1 - s.ink))));
}
