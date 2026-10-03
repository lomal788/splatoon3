// 컨트롤러 입력의 결정적 표현. 클라이언트(client/input.ts)가 키보드·마우스로 채우고,
// 코어는 이것만 본다. 원본 버튼 의미 대응은 DESIGN.md "입력" 절.
export const Btn = {
  Fire: 1 << 0, // ZR 메인 사격
  Jump: 1 << 1, // B
  Squid: 1 << 2, // ZL 오징어
  Sub: 1 << 3, // R 서브
  Special: 1 << 4, // R스틱 누름 스페셜
  Map: 1 << 5, // X
  Reset: 1 << 6, // (웹 전용) 시작 위치로
} as const;

export interface PadState {
  /** 왼쪽 스틱(이동), -1..1. y + = 앞(카메라 기준). */
  moveX: number;
  moveY: number;
  /** 이번 프레임의 조준 회전량(라디안). 마우스 이동이 원본 스틱/자이로를 대신한다. */
  lookYaw: number;
  lookPitch: number;
  /** Web adapter policy. Absent retains the original controller pitch-follow path. */
  lookMode?: "mouse";
  /** 누르고 있는 버튼 비트(Btn). */
  hold: number;
  /** 이번 프레임에 새로 눌린 버튼 비트. */
  trigger: number;
  /** 이번 프레임에 떼어진 버튼 비트. */
  release: number;
}

export function emptyPad(): PadState {
  return { moveX: 0, moveY: 0, lookYaw: 0, lookPitch: 0, hold: 0, trigger: 0, release: 0 };
}
