// 담당: [physics] — 플레이어 상수. 값은 정적 초기화 0x7102455db0 을 에뮬로 실행해 얻은 원본 비트
// (analysis/player/bss_consts_58bb000.txt) [실행(에뮬)]. 주석의 [0x…] 는 bss 주소.
// 십진 상수(Math.fround(0.008) 등)는 원본보다 1ulp 다른 것이 있으므로 반드시 비트로 넣는다(movement_physics.md §9.4).

const BUF = new ArrayBuffer(4);
const U32 = new Uint32Array(BUF);
const F32 = new Float32Array(BUF);

/** f32 비트 → 값 */
export function fb(bits: number): number {
  U32[0] = bits >>> 0;
  return F32[0];
}

// ---- 표면 분류 (player_state.md §7.1) ----
export const FLOOR_NY = fb(0x3f24360c); // [0x71058bbb60] 0.64144969 cos 50.1°
export const WALL_NY = fb(0x3daeef17); // [0x71058bbb68] 0.0854169652
export const OVERHANG_NY = fb(0xbe83a6e8); // [0x71058bbb6c] −0.257132769 (오징어 벽 수영 한계)
export const CEIL_NY = fb(0xbf127826); // [0x71058bbb70] −0.57214582
export const WALL_SAMPLE_NY = fb(0x3f3504f3); // 0.70710677 발밑 잉크를 벽에서 샘플할지 (§7.1 표)

// ---- 입력 ----
export const STICK_DEADZONE = fb(0x3dcccccd); // [0x71058bbbe4] 0.1
export const STICK_RANGE = fb(0x3f666666); // [0x71058bbbe8] 0.9 = 1 − 0.1
export const STICK_POW = fb(0x40800000); // [0x71058bbdf8] 4
export const FWD_BLEND_STEP = fb(0x3b449ba6); // [0x71058bbdf4] 0.003 (본체+0xd4c 증가량)

// ---- 공중 프레임 ----
export const AIR_DAMP_START = 4; // [0x71058bbc20] (s32)
export const AIR_RATIO_DIV = 24; // [0x71058bbc24]
export const AIR_D4_INC = 2; // [0x71058bbc2c]
export const AIR_NORMAL_SLERP = fb(0x3dcccccd); // [0x71058bbc28] 0.1 공중에서 바닥 법선을 위로 되돌리는 비율(×공중 비율)
export const AIR_NORMAL_SLERP_LAUNCH = fb(0x3e4ccccd); // [0x71058bc0e4] 0.2
export const LANDING_AIR_MIN = 8; // [0x71058bbcb8]
export const LANDING_AIR_SPAN = 32; // [0x71058bbcbc] 40 − 8
export const LANDING_SPEED = fb(0x3d75c290); // [0x71058bbcc0] 0.06
export const LANDING_STIFF_DIV = 30; // [0x71058bbcc4]
export const COUNTER_MAX = 0x270e; // 9999 상한(0x710246b32c/0x710246b574)

// ---- 수직 속도·점프 (§6.4, phive_controller.md §4) ----
export const GRAVITY = fb(0x3c03126e); // [0x71058bbc84] 0.00799999945
export const VY_DAMP = fb(0x3f7ae148); // [0x71058bbc74] 0.98
export const JUMP3D_DAMP = fb(0x3f7ae148); // [0x71058bc140] 0.98
export const GRAVITY_START = 3; // [0x71058bbc80]
export const JUMP_VEL = fb(0x3deb851e); // [0x71058bbc60] 0.114999995
export const JUMP_AIR_MAX = 1; // [0x71058bbc88] 공중 프레임 < 1 이면 점프 가능
export const JUMP_REJUMP = 5; // [0x71058bbc90] +0x734 > 5+1
export const JUMP_HOLD_ADD = fb(0x3ba3d70a); // [0x71058bbc98] 0.005
export const VY_EPS = Math.fround(0.001); // 0.001 (디컴파일 리터럴 — Ghidra 십진은 f32 왕복 표기라 fround 로 같은 비트)
export const JUMP3D_EPS = VY_EPS;

// ---- 이동 속도 (§6.1~6.3) ----
export const HUMAN_BASE = fb(0x3dc49ba6); // [0x71058bbda8] 0.096
export const SHOT_CLAMP = fb(0x3d9374bd); // [0x71058bbdac] 0.072
export const SQUID_REF = fb(0x3e449ba6); // [0x71058bbdb4] 0.192
export const SQUID_DRY = fb(0x3d9374bd); // [0x71058bbdb8] 0.072
export const SQUID_ENEMY = fb(0x3c449ba6); // [0x71058bbde4] 0.012
export const KNOCK_EPS = fb(0x3b03126f); // [0x71058bbdc8] 0.002
export const CAP_RATE_UP = fb(0x3e99999a); // [0x71058bbdcc] 0.3
export const CAP_RATE_GROUND = fb(0x3dcccccd); // [0x71058bbdd0] 0.1
export const CAP_RATE_AIR = fb(0x3b449ba6); // [0x71058bbdd4] 0.003
export const AIR_CAP_BASE = fb(0x3d23d70a); // [0x71058bbc30] 0.04
export const AIR_CAP_FRAMES_HUMAN = 90; // [0x71058bbc7c]
export const AIR_CAP_FRAMES_SQUID = 180; // [0x71058bbe64]
export const WALL_SPEED = fb(0x3dc49ba6); // [0x71058bbe8c] 0.096 오징어 벽 속도 상한
export const WALLJUMP_CHARGE_START = 10; // [0x71058bc11c]
export const WALLJUMP_CHARGE_END = 40; // [0x71058bc138]
export const WALLJUMP_CHARGE_SPEEDK = fb(0x3dcccccd); // [0x71058bc130] 0.1
export const V_Y_MAX = Math.fround(0.168); // 0.168 (0x710245b2b4 끝 리터럴)
export const UP_DELTA_LIMIT = fb(0x3e0f5c29); // [0x71058bbcac] 0.14

// 가속량 (§6.3.1)
export const ACC_GROUND_FULL = fb(0x3c23d70a); // [0x71058bbdfc] 0.01
export const ACC_SHOT = fb(0x3ca3d70a); // [0x71058bbe00] 0.02
export const ACC_TYPE2 = fb(0x3c75c290); // [0x71058bbe04] 0.015
export const ACC_TYPE1 = fb(0x3c23d70a); // [0x71058bbe08] 0.01
export const ACC_TYPE0 = fb(0x3c23d70a); // [0x71058bbe0c] 0.01
export const ACC_KNOCK_FULL = fb(0x3c23d70a); // [0x71058bbe10] 0.01
export const ACC_GROUND_BASE = fb(0x3c03126e); // [0x71058bbe1c] 0.008
export const ACC_SHOT_BASE = fb(0x3ca3d70a); // [0x71058bbe20] 0.02
export const ACC_SWIM_BASE = fb(0x3c03126e); // [0x71058bbe24] 0.008
export const ACC_KNOCK_BASE = fb(0x3c83126e); // [0x71058bbe28] 0.016
export const ACC_CURVE = fb(0x3f4ccccd); // [0x71058bbe34..0x71058bbe5c] 0.8 (B 곡선 s, 하한)
export const ACC_RISE = fb(0x3c23d70a); // [0x71058bbc34] 0.01
export const AIR_ACC_FADE = 120; // [0x71058bbc48]
export const AIR_H_A = fb(0x3f000000); // [0x71058bbc50] 0.5
export const AIR_H_B = fb(0x3f333333); // [0x71058bbc54] 0.7
export const AIR_STICK_S = fb(0x3f4ccccd); // [0x71058bbc58] 0.8
export const AIR_F40_BASE = fb(0x3ecccccd); // [0x71058bbc5c] 0.4

// 공중/접지 보정 0x710245f964 (§6.5)
export const F964_PUSH = fb(0x3b03126e); // [0x71058bbd8c] 0.002
export const F964_BLEND_HI = fb(0x3c449ba6); // [0x71058bbde0] 0.012
export const AIR_DAMP_XZ = fb(0x3f6f5c29); // [0x71058bbc38] 0.935
export const AIR_DAMP_XZ_ALT = fb(0x3f75c28f); // [0x71058bbc3c] 0.96
export const AIR_DAMP_Y = fb(0x3f6b851f); // [0x71058bbc40] 0.92
export const AIR_DAMP_Y_SUB = fb(0x3951b718); // [0x71058bbc44] 0.0002

// ---- 벽 점프·롤 (§6.8) ----
export const WALLKICK_STICK_MIN = fb(0x3ecccccd); // [0x71058bc0c8] 0.4
export const WALLKICK_ANGLE = fb(0x42700000); // [0x71058bc0cc] 60°
export const WALLKICK_H = fb(0x3e449ba6); // [0x71058bc0d0] 0.192
export const WALLKICK_V = fb(0x3e6b851f); // [0x71058bc0d4] 0.23
export const WALLKICK_VMAX = fb(0x3e99999a); // [0x71058bc0dc] 0.3
export const WALLKICK_RING = 6; // [0x71058bc0f0]

// ---- 접지 정리 (player_state.md §7.3) ----
export const SQUID_WALL_VS_MIN = fb(0xbd23d70a); // −0.04 [0x71058bbe68]
export const SQUID_WALL_VS_K_WALL = fb(0x3f733333); // 0.95 [0x71058bbe6c]
export const SQUID_WALL_VS_K_FLOOR = fb(0x3f59999a); // 0.85 [0x71058bbe70]

// ---- 발밑 잉크 (player_state.md §8) ----
export const STEP_OWN_THR_BASE = Math.fround(0.65); // 판독식 0.65 − 0.3w (비트 미확인)
export const STEP_ENEMY_THR_BASE = Math.fround(0.35); // 판독식 0.35 + 0.3w (비트 미확인)
export const STEP_THR_W = fb(0x3e99999a); // 0.3
export const STEP_ENEMY_UP_DIV = 3;
export const STEP_ENEMY_DOWN = fb(0x3e800000); // 0.25
export const STEP_MOVE_RATE_MAX = fb(0x3e4ccccd); // 0.2
export const STEP_MOVE_RATE_K = fb(0x3dcccccd); // 0.1
export const STEP_MOVE_RATE_DECAY = fb(0x3f733333); // 0.95
export const STEP_SAMPLE_FULL = 15; // 덮임 = min(N/15, 1)

// ---- 리스폰 ----
export const STATE_RESET = 0x56; // WaitHold (0x710243dcf8, type ≠ 1)
