// 249f494의 메인 입력 writer 24a0ce0..24a0ec8. shooter_bullet §3.5.1 [판독+실행].
export interface MainInputGate {
  blocked: boolean; // B532..535/B788/B784
  inkBlocked: boolean; // Ink vt130 bit0
  rFrames: number; rFlag: boolean; // B4e0/B4f0
  aFrames: number; aFlag: boolean; // B518/B528
  denied: boolean; // 24c9324 bit0
  sideMode: number; sideAllowed: boolean; // Side38 / 268662c bit0
}
export const MAIN_INPUT_DEFAULT: MainInputGate = {
  blocked: false, inkBlocked: false, rFrames: 0, rFlag: false, aFrames: 0, aFlag: false,
  denied: false, sideMode: 0, sideAllowed: false,
};
export function mainInput(previous: number, senderMain: boolean, g: MainInputGate): { frames: number; clearLatches: boolean } {
  const side = g.sideMode === 0 || g.sideMode === 3 || (g.sideMode === 2 && g.sideAllowed);
  const main = senderMain && !g.inkBlocked && !(g.rFrames > 0 && g.rFlag) && !(g.aFrames > 0 && g.aFlag) && !g.denied;
  return { frames: !g.blocked && main && side ? (previous + 1) | 0 : 0, clearLatches: g.denied || !side };
}
/** 249fcb0..249fdc0. adc는 이 블록 대상이 아니다. */
export function inputCountdown(value: number): number { return Math.max(value | 0, 1) - 1; }
