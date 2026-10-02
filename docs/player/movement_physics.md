# 플레이어 물리·이동

Splatoon 3(v0) 플레이어의 인간/오징어 이동 속도, 잉크 위 속도 분기, 이동 입력, 속도 상한·가속, 점프 초기 속도, 공중 감쇠, 캐릭터 컨트롤러(Phive) 연결을 정리합니다. 작업 지침은 [../../분석.txt](../../분석.txt), 공용 사실은 [../README.md](../README.md)·[../02_code_and_params.md](../02_code_and_params.md).

하위 문서:
- [gear_skills.md](gear_skills.md) — 기어 능력(HumanMoveUp/SquidMoveUp/OpInkEffectReduction) AP → 수치 계산 **(원본 실행으로 비트 일치 검증 완료)**
- [player_state.md](player_state.md) — 상태 번호↔이름, 인간↔오징어 전환, 벽 수영 법선 한계, 발밑 잉크(PlayerStepPaint), 사격 중 이동 속도
- [../physics/phive_controller.md](../physics/phive_controller.md) — Phive 캐릭터 컨트롤러 단계 순서, **중력(0.008 유닛/프레임², 수직 속도 `v = 0.98v − g`)**, 게임↔Phive 속도 전달 (physics 담당)

상태: **분석 진행 중**. 웹 구현 없음. 속도 계산식 중 기어 부분만 "동작 검증(에뮬) 완료", 점프 곡선은 원본 함수 3개(수직 속도·공중 카운터·공중 보정)를 프레임 순서대로 연결 실행해 재구현과 비트 일치(§10, 함수 연결 실행이며 메인 계산 전체 실행은 아님), 나머지는 판독 단계.

> 2026-10-02 [move] 3차 갱신: 공중 프레임 카운터(+0xc0) writer·점프 프레임 순서·최종 속도 합성(0x710245aed8)·가속량 accel 전체 식·점프 버튼 유지 가산·벽 점프/오징어 롤(0x7102459630)을 판독했다. 기존 점프 곡선 두 후보(0.633/12f, 0.808/14f)는 둘 다 틀렸다 — 정정은 §6.4.

---

## 1. 기능 개요와 사용자에게 보이는 동작

- 인간 형태: 스틱으로 걷는다. 기본 속도는 무기의 `WeaponSpeedType`(Slow/Mid/Fast)과 인간 속도 업 AP로 정해진다. 적 잉크 위에서는 느려진다.
- 오징어(잠복) 형태: 아군 잉크 위에서 빠르게 헤엄치고, 잉크가 없는 바닥에서는 느리게, 적 잉크 위에서는 거의 못 움직인다. 세 경우가 발밑 잉크 비율로 **연속 혼합**된다.
- 이동 시작·정지는 즉시가 아니라 "속도 상한"이 매 프레임 목표값을 향해 비율로 다가가고, 실제 속도 벡터는 그 상한·입력 방향에서 만든 목표 벡터로 제한된 가속량만큼 끌려간다.
- 점프 초기 속도는 기본 0.115 유닛/프레임이고, 적 잉크 위에서는 낮아진다. 점프 버튼을 누르고 있는 동안 상승 중 매 프레임 0.005가 더해져 높이가 0.84(탭)~1.73(계속 유지) 유닛으로 달라진다(§6.4).
- 오징어로 벽에 붙어 점프하면 벽 법선 방향 0.192·위로 0.23으로 튀어 나가고(벽 점프), 헤엄 중 방향을 60° 넘게 꺾으며 점프하면 롤(Somersault)이 된다(§6.8).

## 2. 분석 대상과 자료 위치

| 항목 | 위치 |
|---|---|
| 원본 | `original/Splatoon 3 [0100C2500FC20000][v0].xci` → `extracted/exefs/main.reloc.img`(0x7100000000 기준) |
| 플레이어 액터 | `extracted/romfs/Pack/Actor/SplPlayer.pack.zs` → 해제본 `extracted/actor/SplPlayer/` |
| 플레이어 파라미터 표 | `extracted/params/Component/GameParameterTable/SplPlayer.game__GameParameterTable.bgyml.json` (이동 관련 기어 항목은 `$type`만 있고 값 없음 → 생성자 기본값) |
| Phive 설정 | `analysis/player/PhiveConfig.json` (`romfs/Phive/Config/PhiveConfig.byml.zs` 변환) |
| 디컴파일 | `analysis/decomp/player/*.c` (주요: `player_main_calc.c` 0x7102475a54, `player_phase.c` 0x710245b2b4 포함, `playerparam_gear.c`, `player_misc1.c`, `phive_char_components.c`) |
| bss 상수 값 | `analysis/player/bss_consts_58bb000.txt/.json` (정적 초기화 함수를 unicorn으로 실행해 추출), `consts_readers.tsv`(상수 → 읽는 함수) |
| 상수 주석이 붙은 디컴파일 | `analysis/player/*_annot.c` (`fRam...71058bbXXX/*=값*/`) |
| 컴포넌트 표 | `analysis/player/player_components.tsv` |
| 도구 | `web/tools/player_vt.py`, `player_scan.py`, `player_imports.py`, `player_initemu.py`, `player_annot.py`, `player_gear.py`, `player_gear_emu.py`, `player_move.py`, `player_bigdecomp.sh` + `ghidra_scripts/PlayerBigDecomp.java` |

## 3. 진입점과 전체 호출 흐름

### 3.1 액터 구성 [데이터]

`Actor/SplPlayer.engine__actor__ActorParam`: Behavior `spl::PlayerBehavior`, PhysicsRef → `Phive/ControllerSetParam/SplPlayer` → CharacterController `SplPlayer`(PresetTypeName `SplPlayer`, GravityScale 1.0, 강체 `Body` 질량 100, MotionProperty `SplPlayer`), 셰이프 `SplPlayer_cct` = 캡슐 2개:

| 캡슐 | CenterA | CenterB | Radius | 재질 프리셋 |
|---|---|---|---|---|
| ColGround | (0,0,0) | (0,0.7,0) | 0.6 | SplPlayerColGround |
| ColOthers | (0,-0.21,0) | (0,0.51,0) | 0.39 | SplPlayerColOthers |

Phive `CharacterComponentPresetCollection` 의 `SplPlayer` 프리셋 [데이터]:

- MoveState: `GameInAir`, `GameOnGround`, `Free`
- Update(순서대로): `GameFrameSetup`, `MoveStateUpdate`, `AirDumping`, `Rotate`, `SplJump`, `FloatWater`, `GameFollowSurface`, `SplAlongGnd`, `CliffSlip`, `ImpactAndReject`, `GameApplyVelocity`
- Result: `SplResultPlayer`, `SplResultStats`
- MotionProperties `SplPlayer`: GravityScale 1.0, MaxLinearSpeed 100, MaxAngularSpeed 200, LinearDamping 0

데이터의 GravityScale 1.0은 게임이 매 프레임 덮어쓴다(`g·3600/9.8` 또는 0). 코드의 이동 상태 배열 순서는 [0]=GameOnGround, [1]=GameInAir, [2]=Free로 `MoveStateComponents` 나열 순서와 다르다 **[판독]** — [../physics/phive_controller.md](../physics/phive_controller.md) §3.1, §4.3.

### 3.2 코드 객체 [판독]

```
spl::PlayerBehavior (vtable 0x7105632b08, 46슬롯; getName 0x7102456e7c)
  슬롯36 0x710245717c: 플레이어 본체 0xac80 B 생성(vtable 0x7105632a60) → Behavior+0x108
    본체 vtable 슬롯2 0x710234b580 = init: 컴포넌트 76개 생성, 포인터를 본체 +0xa650.. 에 저장
  슬롯15 0x7102353a18 → 0x7102472c4c(본체 여러 부분 포인터 인자)
  슬롯18 0x7102353ad0 → 0x7102475a54  ★ 프레임 메인 계산(인자 47개, 36KB 함수)
  슬롯19 0x7102353d24 → 0x7102483134(후처리 단계: 접촉·벽 0x71024abcf0 → StepPaint 0x710268b3b8 → 상태기계 0x710243e7d0 → 모델, 디컴파일 analysis/decomp/player/player_slot19.c, 호출 순서만 판독 — player_state.md §3.2)
```

컴포넌트 일부(본체 기준 오프셋, 전체는 `player_components.tsv`):

| 본체 오프셋 | 클래스 | 이동에서의 역할 |
|---|---|---|
| +0xa650 | spl::PlayerDemo | |
| +0xa658 | spl::PlayerParam (0x260 B) | 기어 계산 결과 캐시([gear_skills.md](gear_skills.md)) |
| +0xa680 | spl::PlayerInkActionSpJetpack | 특수(+0x13c 비율) |
| +0xa688 | spl::PlayerStepPaint | **발밑 잉크**: +0x3c 아군 잉크 비율(0~1), +0x54 이동용 적 잉크 비율(평활), +0x30 분류(0/1 아군, 2/3 적, 4/5 없음) — 갱신 0x710268b3b8 **[판독]**, 식은 [player_state.md §8](player_state.md) |
| +0xa690 | spl:PlayerCollision | Phive 연결. +0xe360/+0xe378 하위 객체 |
| +0xa6e8 | spl::PlayerJump | |
| +0xa7c0 | spl::PlayerCoopZombie | +0xeec 플래그면 속도 0.0576·점프 0.06 상한 |
| +0xa8a0 | spl::PlayerDamage | combat 영역 |
| +0xa8c8 | (이름 없음) 상태기계 | `[+0xa8c8]+0xc8` = 현재 상태 번호(int) |

### 3.3 프레임 흐름 [판독: 디컴파일 구조·호출 주소]

메인 계산 인자(호출부 `0x7102353ad0`): param_1 = 본체+0xa5fc, param_4 = &본체+0xc0, param_6 = 본체+0x750, param_7 = 본체+0x72c, param_8 = 본체+0xd2c, param_17 = 본체+0xe4, param_18 = 본체+0x784 … (전체 47개는 `analysis/decomp/player/player_components_vt.c` 2996행). 전체 분석 재디컴파일본: `analysis/decomp/move/move_full_main.c`(0x7102475a54, 0x71024abcf0, 0x710245b2b4, 0x710245f964).

일반 경로(데모·워프·원격 아님) 한 프레임:

```
슬롯18 0x7102475a54
 1 GravityScale = (공중≥3 && 다운 카운터 0) ? g·3600/9.8 : 0            (raw 4688~4699행)
 2 0x71024a7d00 수직 속도 갱신(+0x73c, +0x734++)                          (호출 0x710247c860)
 3 점프 판정 → 점프 속도 대입(+0x73c 또는 3D 점프 +0x754, §6.4)
      → 0x71024a8000 점프 시작(+0x734 = 0, 점프 상태 요청)                (0x7102480e00)
      → 0x710246b32c(..,1) 접지 처리(+0xc0 = 0, +0x268++)                  (raw 5799행)
    또는 벽 점프·오징어 롤 0x7102459630(§6.8)                             (0x710247e1c4, 0x7102481230, 0x7102482c04)
 4 점프 버튼 유지 가산 +0x73c += 0.005·(1−f)                              (0x7102482df8, §6.4)
 5 0x710245b2b4 목표 속도·cap·가속(이동 속도 +0x114)                      (0x710247caa4)
      └ 끝에서 0x710245f964 공중/접지 보정(이동 속도에)                     (0x710245edc0)
 6 발사 플래그 본체+0x7f8 이면 이동 속도 = 발사 벡터(본체+0x7b8, 1프레임), 사람이면 0x710245f964 한 번 더(0x710247cb48)
 7 0x710245aed8 최종 속도 합성 → 본체+0xe4[0..2] (§6.7)                   (0x710247ccc0)
 8 +0x73c > 0.001 이면 Phive 이동 상태를 InAir([1])로 강제, 0x71024f4f7c(PC, 본체+0xe4 + 본체+0x12c)
Phive 캐릭터 컨트롤러 스텝(공중: 게임 속도 그대로 적분)
슬롯19 0x7102483134 → 0x71024abcf0(0x7102484544)
    0x71024f7410: PC+0xd0 = (Phive 현재 상태 종류 0(OnGround) && 상태 S+0x20 == 1), PC+0x1d0 = 접촉 분류 0~3
    PC+0xd0 거짓 → 0x710246b574: +0xc0++(상한 9999), +0xd0++, +0xdc = min(+0xc0/24,1), +0x268 = 0
    PC+0xd0 참   → 0x710246b32c: +0xc0 = 0, +0xc8 = +0xcc = 0, +0xdc = 0, +0x268++
```

- 2→3→4→5 순서는 raw 디컴파일(`player_main_calc.c`)의 중첩 구조(수직 갱신 4925행 → 점프 5050~5800행 → 유지 가산 5862행 → 이동 6163행)로 판단했다. 점프 블록과 유지 가산은 `0x710247c8ec` 레이블 앞에서 끝나고 그 뒤 직선 코드에 `0x710245b2b4` 호출이 있다 **[판독]**.
- 공중 프레임 카운터 +0xc0 는 **슬롯19(Phive 스텝 뒤)** 에서만 증가한다. 메인 계산은 직전 프레임 슬롯19 값을 읽는다 **[판독]** (writer: `0x710246b574` 증가, `0x710246b32c`·raw 1283행 경로 0 대입).
- 슬롯19에서 접지 판정은 Phive 쪽 상태(PC+0xd0)다. 점프 프레임에 게임이 Phive 상태를 InAir로 강제하므로 같은 프레임 슬롯19에서 공중 처리(+0xc0 = 1)가 된다 **[판독]**. Phive 스텝 안에서 위로 0.115 움직이는 중에 다시 OnGround로 바뀌지 않는다는 것은 **[추정 — Phive 상태 전이 판정은 엔진 쪽, 미판독]**.

## 4. 구조체·필드·상수

### 4.1 이동 상태 블록 (기준 객체: 플레이어 본체, 0x710245b2b4 의 `param_1` = 본체+0xd2c)

| 본체 오프셋 | 타입 | 의미 | writer | reader |
|---|---|---|---|---|
| +0xc0 | s32 | **공중 프레임 수**(접지 0, Phive 스텝 뒤 공중이면 +1, 상한 9999). ≥3이면 중력, <4면 `0x710245f964` 누름 경로, ≥4면 공중 가속 감쇠(§6.3) | 슬롯19 `0x710246b574`(+1)·`0x710246b32c`(0), 점프 프레임 메인 계산 `0x710246b32c`(0) | `0x71024a7d00`, `0x710245f964`, `0x710245b2b4`, 카메라·애니 **[판독]** |
| +0xd0 | s32 | 공중 프레임 수(보조, 접지 때 0 안 됨 — `0x710246b32c`는 접지 플래그 인자 1일 때만 0) | `0x710246b574` | 접촉 정리 `0x71024abcf0` **[판독: 쓰기]** |
| +0xdc / +0xe0 | f32 | 공중 비율 min(+0xc0/24, 1) / +0xd4/24 | `0x710246b574`, `0x710246b32c`(0) | 가속 공중 보정(§6.3, `param_1[-0x314]`) **[판독]** |
| +0xe4.. | 구조체 | **최종 속도 구조체** F: F[0..2] 최종 속도, F[6..8](+0xfc), F[0xc..0xe](+0x114 이동 속도), F[0x12..0x14](+0x12c, Phive 전달 때 더함), F[0x1a..0x1c](+0x14c), F[0x1d..0x1f](+0x158 대시 패널 속도) | `0x710245aed8` | `0x71024f4f7c` **[판독]** |
| +0x114 | vec3 f32 | **이동 속도**(게임 레이어, 유닛/프레임) = F[0xc..0xe] | 메인 계산(0x710245b2b4 결과를 6163행 뒤에 되씀) | `0x710245aed8` **[판독]** |
| +0x120 | vec3 f32 | 원하는 이동 벡터 desired(0x710245b2b4 의 마지막 인자) | 메인 계산 | |
| +0x268 | s32 | 접지 프레임 수(본체+0x180 구조체 +0xe8) | `0x710246b32c` +1(상한 9999), `0x710246b574` 0 | 점프 유지 가산 조건 **[판독]** |
| +0x72c / +0x72d | u8 | 점프 버튼 누름 / 이번 프레임 눌림. `[[본체+0xa890](spl:PlayerInputSender)+0x58]` 복사, InputSender+0x58 = 패드 상태 +0x114 의 bit1 | 입력 함수 `0x710249f494` | 점프 유지 가산, 0x71024abcf0 **[판독]**, bit1 = B 버튼 **[추정 — nn::hid Npad 비트 순서]** |
| +0x734 | s32 | **점프 시작 뒤 프레임 수**(+0x72c 구조체 +8) | `0x71024a7d00` +1/프레임, `0x71024a8000`(점프 시작) 0 | 점프 재입력 대기(> 6), 공중 가속 분기, `0x710245f964` **[판독]** |
| +0x73c | f32 | **수직 속도(유닛/프레임, 위가 +)**. 점프 시 초기 속도(§6.4)가 들어가고 매 프레임 `0.98v − g` | 메인 계산 점프부, 유지 가산 `0x7102482df8`, `0x71024a7d00`, 벽 점프 `0x7102459630` | `0x710245aed8`(최종 속도 y에 더함), `0x710245b2b4`, `0x71024f4f7c` **[판독]** |
| +0x740 | f32 | 수직 합계(+0x73c + 상승 임펄스) | `0x71024a7d00` | 미추적 |
| +0x745 | u8 | 공중 수평 감쇠 0.96 선택 플래그 | 미추적, `0x710246b32c`(0) | `0x710245f964` **[판독: 사용]** |
| +0x750..+0x758 | vec3 | **3D 점프 속도 X**. 경사(바닥 법선 y < 0.6414)에서 점프하면 +0x73c 대신 (0, jump, 0)이 여기에 들어감. `0x71024a7d00`이 매 프레임 ×0.98, 공중 상태면 X.y 를 +0x73c 로 옮김 | 메인 계산 점프부(raw 5418행~), 벽 점프(0으로) | `0x71024a7d00`, `0x710245aed8` **[판독]** |
| +0x7b8.. | 구조체 | **발사(벽 점프·오징어 롤) 구조체** L: [0..2] 발사 속도, [3..5] 방향, +0x24 횟수 n(감쇠 지수, 의미 [추정]), +0x2c 속력, +0x30 시각, +0x3c/+0x3d 활성, +0x3f 오징어 상태였음, +0x40(=본체+0x7f8) 이번 프레임 적용, +0x41 벽 점프(롤 아님) | `0x7102459630` | 메인 계산(+0x7f8이면 이동 속도 대체), `0x710245f964`(롤 중 건너뜀) **[판독]** |
| +0x474, +0x478 | f32 | 이동 스틱 x, y | 0x71024a0858 근처 입력 처리 | 0x710245b2b4 |
| +0x47c | f32 | 스틱 크기 재매핑: (|stick| - 0.1)/(1-0.1) 클램프, 0.1 = [0x71058bbbe4] | 0x71024a0910 | 이동·애니(0x7102442354) |
| +0xd2c | f32 | 속도 상한 cap (유닛/프레임) | 0x710245b2b4 | 0x710245b2b4 |
| +0xd30..+0xd38 | vec3 | 카메라 기준 이동 방향(정규화) | 0x710245b2b4 | 〃 |
| +0xd3c | f32 | 입력 크기 m = |방향 합성 벡터|^4 | 0x710245b2b4 | 〃 |

### 4.2 상태 번호 집합 [판독: 사용], 이름 [데이터]

이동 코드는 상태기계 `[본체+0xa8c8]+0xc8` 값으로 오징어 속도 경로를 고른다. 다음 집합 S이면 오징어 속도(+0xc0/+0xc4/+0xc8)를 쓴다:

`0x82 ≤ s ≤ 0x90`, `0xaa ≤ s ≤ 0xac`, `s ∈ {0xed, 0xee, 0x10c}`

> 정정(이전: "상태 번호와 이름의 대응 표는 찾지 못했다"): 상태 표 `0x7105630270`(32 B × 286, 상태 변경 함수 0x7102447bfc 가 `표[state]` 로 참조)에 상태마다 ASB 커맨드 이름이 있다. 이름 = 애니 커맨드 이름이며 ASB 와 284/286 일치([player_state.md §4](player_state.md)).
>
> S 의 이름: 0x82 ToSquid(사람 모델)·0x83 ToSquid_Chariot·0x84 ToSquid(오징어 모델)·0x85 Wait·0x86 WaitStandby·0x87 Walk·0x88 Surprise·0x89 Jump_St·0x8a/0x8b Jump·0x8c Jump_Ed·0x8d/0x8e Somersault·0x8f WallJumpCharge·0x90 WallJump·0xaa~0xac DokanWarp_St/Ar/Ed·0xed PreDive·0xee Dive·0x10c CoopWaitEntryCharge. 오징어 모델이지만 S 밖: 0x91 ToHuman, 0xad DokanWarp_ToHuman, 0xb8~0xba Injection*(상태기계의 오징어 판정에는 포함). 사람 상태 예: 0x45/0x5f WalkHold, 0x56 WaitHold, 0x60 WalkShoot, 0x99 Jump_St, 0x9b Jump, 0xa6 Jump_Ed, 0xe6 Dead. 전체 표는 [player_state.md 부록](player_state.md#부록-상태-번호-표).

### 4.3 플레이어 상수 (bss, 정적 초기화 0x7102455db0 이 씀) [실행(에뮬): 값], [판독: 사용처]

| 주소 | 값 | 사용(이 문서 범위) |
|---|---|---|
| 0x71058bbb60 | 0.64144969 | 지면 판정 법선 y 임계(cos ≈ 50.1°로 추정) — 접지·벽 판정에 27회 사용 |
| 0x71058bbbe4 | 0.1 | 스틱 데드존 |
| 0x71058bbc20 | 4 (s32) | 공중 프레임 임계(이하면 접지 취급 경로) |
| 0x71058bbc38/0x71058bbc3c | 0.935 / 0.96 | 공중 수평 감쇠 |
| 0x71058bbc40 / 0x71058bbc44 | 0.92 / 0.0002 | 공중 수직 감쇠·감산 |
| 0x71058bbc60 | 0.115 | 점프 초기 속도 |
| 0x71058bbc64 | 0.07 | 점프 속도 상한(특정 조건) |
| 0x71058bbc6c/0x71058bbc70 | 0.06 | 점프 상한(바닥 조건/코옵 좀비) |
| 0x71058bbc78 | 0.7 | 점프 속도 배율(사격 상태 비율과 보간) |
| 0x71058bbc74 / 0x71058bc140 | 0.98 / 0.98 | 수직 속도(+0x73c) 감쇠 / 상승 임펄스 감쇠 (`0x71024a7d00`) |
| 0x71058bbc80 | 3 (s32) | 중력 적용 시작 공중 프레임(+0xc0 ≥ 3) |
| 0x71058bbc84 | 0.008 (비트 0x3c03126e = 0.00799999945) | **중력** 유닛/프레임² (`0x71024c9684`) — [../physics/phive_controller.md](../physics/phive_controller.md) §4 |
| 0x71058bbef8 | 1.2 | 충격·밀어냄 가속이 이동 방향과 같을 때 원하는 속도에서 빼는 배율 |
| 0x71058bbda8 | 0.096 | (인간 기본 속도와 같은 값, 사용처 0x71024abcf0 등) |
| 0x71058bbdac | 0.072 | 사격 중 기본 속도 초기값 |
| 0x71058bbdb4 | 0.192 | 오징어 기준 속도(정규화·상한 비교) |
| 0x71058bbdb8 / 0x71058bbde4 | 0.072 / 0.012 | 오징어: 무도색 / 적 잉크 속도 |
| 0x71058bbdc8 | 0.002 | 외력 속도 소거 임계 |
| 0x71058bbdcc / 0x71058bbdd0 / 0x71058bbdd4 / 0x71058bbdd8 | 0.3 / 0.1 / 0.003 / 0.1 | 상한 cap 갱신 비율(§6.2) |
| 0x71058bbdbc/0x71058bbdc0/0x71058bbdc4 | 0.94 / 0.9 / 0.2 | 외력(넉백) 속도 감쇠 |
| 0x71058bbdf8 | 4.0 | 입력 크기 지수 |
| 0x71058bbe04/0x71058bbe08/0x71058bbe0c | 0.015 / 0.01 / 0.01 | WeaponAccType 2/1/0별 가속 상수(§6.3) |
| 0x71058bbe84/88, 0x71058bbe8c, 0x71058bbea8 | 50°, 90°, 0.096, 0.02 | 경사(벽) 각도 구간 속도 제한 |
| 0x71058bbf00 / 0x71058bbf04 | 0.8 / 0.8 | 특수 상태(상태값 0x16 계열) 속도 배율 |
| 0x71058bc110 | 0.1782 | 특정 플래그 시 속도 크기 상한 |
| 0x71058bc21c/0x71058bc220 | 0.6 / 1.0 | 적 잉크 비율로 보간하는 배율(특정 상태) |
| 0x71058bc23c | 0.0576 | 코옵 좀비 상태 속도 상한 |
| 0x71058bbc88 / 0x71058bbc90 | 1 / 5 (s32) | 점프 가능 공중 프레임 상한(< 1) / 재점프 대기(+0x734 > 5+1) |
| 0x71058bbc98 / 0x71058bbc9c | 0.005 / 0.001 | 점프 버튼 유지 가산(기본 / 점프 기믹) |
| 0x71058bbca0 / 0x71058bbca4 | 0.005 / 0.002 | 점프 기믹(+0xa828+0x30) 상승 가산 |
| 0x71058bbc48 / 0x71058bbc4c | 120 / 300 (s32) | 공중 가속 감쇠가 0이 되는 공중 프레임(기본 / 점프 기믹) |
| 0x71058bbc50 / …c54 / …c58 / …c5c | 0.5 / 0.7 / 0.8 / 0.4 | 공중 가속 감쇠의 방향 보정·스틱 곡선 |
| 0x71058bbe00~0x71058bbe5c | 0.02, 0.015, 0.01×3, 0.001×2, 0.008, 0.02, 0.008, 0.016, 0.0008×2, 0.8×11 (그리고 0x71058bbdfc 0.01) | accel 분기 상수(§6.3.1) |
| 0x71058bc0bc | 60 | 오징어 롤 판정 각도(°) |
| 0x71058bc0c4 | 0.1705 | 오징어 롤 점프 속도 |
| 0x71058bc0d0 / …d4 / …d8 / …dc | 0.192 / 0.23 / 0 / 0.3 | 벽 점프 수평 속도 / 수직 기본 / 수직 가산 계수 / 수직 상한 |

전체 449개 값은 `analysis/player/bss_consts_58bb000.txt`(작성자 0x7102455db0 행).

### 4.4 단위 [판독]

- 속도는 **유닛/프레임**. 근거: 이동 함수가 Phive 쪽 가속도(초당)를 `* 0.016666668 * 0.016666668`(1/60²)로 바꿔 같은 식에 더한다(0x710245b2b4 끝부분, 0x7102475a54 점프부). 게임 고정 60 fps. 게임 → Phive 속도 전달은 ×60, 읽을 때 ×0.016666668(`0x71024f4f7c`, `player_misc1.c` 718행) **[판독]**.
- 정정(이전 표현 "Phive 쪽 가속도"): 1/60²을 곱하는 값은 중력이 아니라 **ImpactAndReject 컴포넌트(`[PC+0xe360]+0x28`)의 충격 가속도(+0x08)와 밀어냄 가속도(+0x24)** 의 합(유닛/초²)이다. 근거: PC+0xe360에 저장되는 포인터는 `0x71012eb0a0`이 이름 "CharacterUpdateImpactAndReject"로 찾은 컴포넌트이고, 그 업데이트 `0x71012adb58`이 이 두 벡터에 dt를 곱해 속도에 더한다. 상세는 [../physics/phive_controller.md](../physics/phive_controller.md) §5.2 **[판독]**.
- 길이 유닛: 플레이어 캡슐 반경 0.6, 무기 사거리(WeaponInfoMain Range 12.5) 등과 같은 계 **[데이터]**. Splatoon 2의 DU 값(인간 0.96, 오징어 1.92)의 1/10과 일치한다 **[추정]**.

## 5. 상태 전이와 수명

- 상태 변경 = 0x7102447bfc(재생 속도, 상태기계, 새 상태, 블렌드0 플래그, 강제) → 0x710244128c 적용(이전 번호 +0xcc, 블렌드 프레임은 상태 표 값). 인간↔오징어 전환은 판독됨: 0x82 사람 ToSquid → (클립 끝 3프레임 전) 0x84 오징어 ToSquid → 0x85/0x87…, 해제 시 0x91 오징어 ToHuman(강제, 블렌드 0) → 0x92~0x95 사람 ToHuman. 판정·진행 함수 0x710243e7d0(슬롯19 단계) — [player_state.md §5~6](player_state.md) **[판독]**. 형태 안 전이(0x7102442354)의 우선순위와 점프·낙하·착지 상태 선택도 판독됨(player_state.md §6.3). 점프 상태(Jump_St)는 이동 코드의 점프 시작 `0x71024a8000`이 요청한다 **[판독]**.
- 0x82/0x84 는 S 에 들어 있으므로 ToSquid 애니 첫 프레임부터 오징어 속도, 0x91 부터는 인간 속도 **[판독]**.
- 속도 상한 cap(+0xd2c)은 매 프레임 갱신되는 지속 상태다. 특수/레일/워프 상태에서 0으로 리셋되는 분기가 있다(§6.2 조건 블록) **[판독]**.

## 6. 계산식과 의사코드

### 6.1 목표 속도 (0x710245b2b4 앞부분) [판독]

```
pp = 본체.PlayerParam
speedType = pp.getWeaponSpeedType()          // 0x7102669b90: MainWeaponSetting+0x4c, 기본 1
human = speedType==2 ? pp[+0xb8] : speedType==0 ? pp[+0xb4] : pp[+0xb0]
if (특수 상태값 == 0x18) human *= (jetpack[+0x13c]*0 + 1)        // = 1
if (특수 상태값 == 0x16) human *= 0.8                             // [0x71058bbf00]

if (state ∈ S):                                  // 오징어 경로
    squid = speedType==2 ? pp[+0xc8] : speedType==0 ? pp[+0xc4] : pp[+0xc0]
    k = 0x710266c6e4(pp, 특수==0x16)             // 미판독, 기본 1로 추정
    own = stepPaint[+0x3c]; enemy = stepPaint[+0x54] (코옵좀비 플래그면 0)
    target = 0.072 + (squid*k - 0.072)*own + (0.012 - 0.072)*enemy
    if (특수==0x16) target *= 0.8
else:                                            // 인간 경로
    target = human
    if (stepPaint[+0x54] > 0 && !코옵좀비):
        op = pp[+0x104]; opShot = pp[+0x108]     // (+0x168 대체 객체 있으면 그쪽 값)
        if (op < human)      target  = human + (op - human)*enemy
        if (opShot < 0.072)  shotBase = 0.072 + (opShot - 0.072)*enemy
```

이어서 사격·특수무기·경사·좀비 등 상한 조정(0.072 클램프, 0.024 클램프, 0.0576 클램프, 경사 50~90° 보간, 적 잉크 비율에 따른 0.6~1.0 배율, 프레임 카운터 10~40 구간 감속 등)이 순서대로 적용된다. 각 분기의 진입 조건 필드 의미가 확인되지 않아 **조건은 [미확정]**, 적용 식과 상수는 **[판독]**(디컴파일 `analysis/player/f_710245b2b4.c` 263~560행).

**사격 중 이동(인간 경로)** [판독 + 데이터] — 이전 [미확정] 해소:

```
if ((본체+0x4ec > 0 || 본체+0x524 > 0) && 잉크액션 없음/vt[0x28] 거짓) && target > 0.072: target = 0.072
elif ink = [본체+0x588] (무기 잉크액션의 보조 인터페이스):
    target = ink->vt[0x30]({target, pp+0x108, stepPaint+0x54, pp+0xbc, onEnemy})
      // 슈터 = 0x71025859ac: v = WeaponShooterParam.MoveSpeed(+0x4c)·pp+0xbc;
      //   onEnemy && pp+0x108 < v 이면 v += (pp+0x108 − v)·enemy;  return min(v, target)
```

MoveSpeed 데이터: 대부분 0.072, Expert 0.055, Gravity/Long/TripleMiddle 0.06, Heavy 0.04, QuickMiddle 0.084, Short/TripleQuick 0.08. 매뉴버(0x710254e5a8)·스피너(0x71025ce43c)도 같은 식. 자세한 경로는 [player_state.md §9](player_state.md).

**PlayerParam +0x180/+0x188 대체 경로** [판독 + 실행(에뮬)] — 이전 [미확정] 해소: +0x180 은 전역 `0x71058e87a4` 를 복사한 값이고, 이 전역은 0x7102b55594 가 씬 플래그 **`Scene_Coop`**(이름 객체 0x71058e9270, 정적 초기화 0x7102b582d0 을 에뮬로 실행해 이름 확인)의 비트로 채운다. 즉 **연어런(코옵) 씬**에서는 기어 보간 캐시(+0xb0.. 등) 대신 +0x188 객체의 getter(0x71024fefe4/0x71024ff2a4/0x71024ff564, 적잉크 데미지 0x71024fe5fc/0x71024fe8bc 등)가 파라미터 구조체 필드를 `$parent` 체인과 설정 플래그로 직접 읽는다(기어 보간 없음). 대전에서는 0 이다. +0x188 이 가리키는 파라미터 타입 이름은 [미확정] — 154종 리플렉션 표에 같은 오프셋 조합이 없음.

### 6.2 속도 상한 cap 갱신 [판독]

```
// target 은 6.1 결과(이후 조정 포함), m = 입력 크기(+0xd3c), v = 이동 속도 벡터
rate = 0.3
if ((target*m)^2 <= |v|^2):          // 이미 목표 이상으로 움직이는 중
    if (0x71024c8ee8(...)):  rate = 0.03
    else:
        rate = 0.003
        if (카운터[param_8+0xc] < 1):
            rate = 0.1     (특수 상태 4 && 플래그면 0.1 [0x71058bbdd8])
            if (경사 조건 bVar6): rate = lerp(0.05, 1.0, 경사각 50°→90° 구간 비율)
cap += rate * (target - cap)
```

재구현 수렴 예(`player_move.py`, 가속 쪽 rate 0.3, 정지 → 0.096): 1프레임 30%, 3프레임 65.7%, 10프레임 97.2% **[재구현 계산]**. 실제 이동은 아래 가속 제한도 함께 받으므로 이 값이 곧 체감 가속은 아니다.

### 6.3 이동 입력과 속도 벡터 갱신 [판독], 일부 [미확정]

```
// 입력
stick = (본체+0x474, 본체+0x478)
dirRaw = stickY * camForward(본체+0x180..0x188 기반) - stickX * camRight     // 정확한 축 구성은 0x710245b880 부근
m = |dirRaw| ^ 4.0                          // powf(len, [0x71058bbdf8]=4.0)
dir = normalize(dirRaw)
desired = dir * cap * m                      // param_21

// 가속 제한
accel = §6.3.1
delta = desired - v       (경사면 법선 성분 제거, 벽 법선 성분 제거 포함)
if |delta| > accel: delta *= accel/|delta|
v += delta
v.y = min(v.y, 0.168)
0x710245f964(v)          // §6.5 — 이동 속도 y 의 공중 처리는 여기서만 바뀐다
```

#### 6.3.1 가속량 accel [판독] — 이전 [미확정] 해소

근거: `0x710245b2b4` 전체 분석 재디컴파일 `analysis/decomp/move/move_full_main.c` 11605~11985행(accel 본식·상승 보정), 12053~12187행(공중 감쇠). 기준 객체: 함수 인자 param_1 = 본체+0xd2c(cap), param_20 = 이동 속도 v, param_21 = desired. 상수는 정적 초기화 에뮬 값 **[실행(에뮬)]**.

```
m   = 본체+0x47c                                   // 데드존 재매핑 스틱 크기 0..1
o   = dot(desired, v) < 0 ? min(1, −dot(desired, v) / cap²) : 0     // 진행 반대 비율 (cap = 본체+0xd2c)
b(x, s) = (|x| < 0.001) ? 0 : sign(x)·|x|^(−log2 s)       // logf/expf 로 계산(기어 보간과 같은 꼴), s=0.5±0.001 이면 x 그대로
B   = 0.8 + 0.2·b(1 − o, 0.8)                     // 반대로 꺾을수록 작아짐(1 → 0.8)

if Jetpack 조건(0x71024c8ee8):                        // 특수 0x18 활성 등
    accel = m·((b(1−o, 0.4)·0.6 + 0.4)·0.01 − 0.002) + 0.002     // 지수 1.321928 = −log2 0.4 상수로 들어 있음
elif 본체+0xfa5 || [PC+0xe378]+0x1746:                // 의미 [미확정]
    accel = lerp(0.0008, 0.001·(0.8 + 0.2·b(1−o, 0.8)), m)        // [0x71058bbe2c]/[…e14]
elif 특수 0x1a(Chariot) 활성 && 상태 ∈ S:              // 0x710259a064/…224/…5a4 이 값 공급
    accel = lerp(f224, f5a4·(f064 + (1−f064)·b(1−o, f064)), m)
elif 사격 계열(본체+0x4d8, +0x4ec, +0x524 중 하나 > 0):
    accel = lerp(0.02, 0.02·B, m)                                 // [0x71058bbe00]/[…e20]
elif 본체+0x168 ≥ 1 && 넉백 벡터(본체+0x16c..) == 0:
    accel = lerp(0.016, 0.01·B, m)                                // [0x71058bbe10]/[…e28]
elif 0x7102458cfc(본체+0x784) ||                      // 공중 분기
     (+0x73c + +0x754 > 0.001 && +0x734 < +0x77c && StepPaint+0x30 ∉ {2,3}):
    accBase = {2: 0.015, 1: 0.01, 0: 0.01}[WeaponAccType]          // [0x71058bbe04/…e08/…e0c]
    accel = lerp(0.008·b(|v|/0.192, 0.8), accBase·B, m)           // [0x71058bbe24], 0.192 = [0x71058bbdb4]
else:                                                 // 지상 기본
    accel = lerp(0.008, 0.01·B, m)                                // [0x71058bbe1c]/[…dfc]

// 상승 보정(11966~11985행): 본체+0x7f4 == 0(발사 중 아님) 등 조건에서
w = 본체+0xdc(공중 비율) · (1 − 본체+0xa5c · clamp(+0x73c / 0.115, 0, 1))
if 특수 0x18: w *= 1 − jetpack[+0x13c]
accel = lerp(accel, 0.01, w)                                      // [0x71058bbc34]

// 밀림 보정: |desired| −= 1.2 · max(0, dir·(충격+밀어냄)/3600 + dir·본체+0x4bc..)   (§4.4, phive 문서 §5.2)
// 레일 등 외부 속도(vt+0x1b8)와 같은 방향 성분을 desired 에서 뺌

// 공중 감쇠(12053~12187행): 공중 프레임 +0xc0 ≥ 4 이고 본체+0xfa5 등 아님
d   = normalize(desired − v);  h = (dot(d, [본체+8] 행렬 열(+0x2a0,+0x2ac,+0x2b8)) + 1)·0.5
if (본체+0xad8 ≥ 1 && 상태 ∉ S) || 전역/플래그:   h = h ≤ 0.5 ? 0.5 + 0.2·(1 − 2h) : h     // [0x71058bbc50/…c54]
r   = min(|stick|, 1)                                             // 본체+0x474,+0x478
f40 = max(0.4·(1 − b(r, 0.8)), h)                                // [0x71058bbc5c], [0x71058bbc58]
f33 = 1 − min(+0xc0 / (JumpGimmick+0x30 ? 300 : 120), 1)          // [0x71058bbc4c]/[…c48]
특수 0x18이면 f40, f33 를 jetpack[+0x13c] 로 1 쪽 보간; NiceBall+0x2658·특수 0x1c(SuperLanding)·전역 플래그면 f33 = 0
accel *= f40 · f33

// 벽 쪽 감쇠: |delta| > 0.001 && 본체+0x498 > 0.01 이면 delta 와 본체+0x48c.. 방향 성분 비로 accel 을 줄임(12188~12215행)
// 마지막에 delta 의 바닥 법선(본체+0x180) 성분 제거 → 평지에서는 delta.y = 0
```

- 의미: 지상에서 스틱을 끝까지(m=1) 같은 방향으로 밀면 accel 0.01, 반대로 꺾으면 0.008~0.01 사이(B), 손을 떼면(m=0) 0.008로 감속. 공중에서는 가속 상한이 무기 WeaponAccType 값(0.01/0.015)이고, 공중 4프레임째부터 `f33`이 120프레임에 걸쳐 0이 되어 공중 조작이 점점 둔해진다 **[판독: 식] / [추정: 체감 의미]**.
- `b(1−o, 0.8)`: 0.8 = Low/Mid 보간 꼴의 s(기어 공식 §5.2와 같은 함수 인라인) **[판독]**.
- 분기 조건 필드 중 의미가 확인된 것: +0x4ec/+0x524 사격(§6.1 사격 중 이동과 같은 필드), +0x168/+0x16c 넉백 카운터·벡터(같은 함수 앞부분에서 0.94/0.9/0.2 감쇠, 크기 ≤ 0.002면 0), +0x73c/+0x754/+0x734 수직 속도·3D 점프·점프 뒤 프레임, +0x77c 점프 직후 지속 프레임(raw 5796행이 `(int)(… ·20)`로 설정) **[판독]**. +0x4d8, +0xfa5, +0xa5c, +0xad8, `0x7102458cfc` 의 게임 의미는 **[미확정]**.
- 재구현 시 순서: accel 결정 → 상승 보정 → 밀림·레일 보정 → 공중 감쇠 → 벽 감쇠 → 법선 제거 → 크기 제한 → v.y ≤ 0.168 → `0x710245f964`.

### 6.4 점프 초기 속도 (0x7102475a54, 0x710247df18~0x710247e00c) [판독]

```
jump = 0.115                                     // [0x71058bbc60]
if 코옵좀비: jump = 0.06                          // [0x71058bc240]
else:
    if (특정 상태 0xf && 조건) jump = 0x710269e674(...)
    if (카운터 본체+0xc18 > 0): jump *= lerp(1, 0.7, clamp(x[+0x138],0,1))   // 0.7 = [0x71058bbc78], 카운터 의미 미확정
    else if (...) jump *= [0x71058bc234]=1
if (조건 bVar31, 의미 미확정): jump = min(jump, 0.07)  (카운터 본체+0xbf0>0 이고 특수 상태 0x1a면 0.115)
else:
    if (enemy = stepPaint[+0x54]) > 0:
        op = pp[+0x100]                          // 적 잉크 점프 속도(기어)
        jump = min(jump, jump + (op - jump)*enemy)
    if (특정 바닥 플래그) jump = min(jump, 0.06)
    jump = min(jump, 외부 상한 콜백)
jump -= max(0, 본체+0x4c0(바닥 이동 속도 y로 추정) + (충격.y + 밀어냄.y)/3600)     // ImpactAndReject 가속(위로 밀리는 중이면 그만큼 감소)
```

적 잉크 위 0AP 점프 = min(0.115, lerp(0.115, 0.08, e)) **[판독]**. 결과는 수직 속도 본체+0x73c에 들어간다(메인 계산 줄 5413) **[판독]**.

**점프 발동 조건과 대입** [판독] (raw `player_main_calc.c` 5039~5420행, 전체 분석본 `move_full_main.c` 5330~5712행):

```
if 본체+0x72c(점프 버튼 누름) || Chariot 입력 플래그:                    // raw 5012행, 그 밖에 본체+0x1054 등
    ok = 공중 프레임 +0xc0 < 1 [0x71058bbc88]
         || bVar30 (Jetpack 조건 0x71024c8ee8 && +0x734 ≥ 25 && +0xc0 ≥ 1)
    wallKick = 입력 링 버퍼(최근 6프레임 [0x71058bc0f0]) 조건 && 0x71024593e8(...)   // 벽 점프 트리거, §6.8
    if !wallKick: ok = ok && +0x734 > 6          // [0x71058bbc90]+1 — 점프 시작 뒤 7프레임째부터 다시 가능
    canJump = ok && (wallKick || 본체+0x780 == 0)  // +0x780 의미 [미확정]
if canJump && 현재 +0x73c < jump:
    if 바닥 법선 y(본체+0x184) < 0.6414 && 오징어 벽 조건(bVar29):     // 경사·벽에서
        본체+0x750 = (0, jump, 0); 본체+0x77c = 0                       // 3D 점프 X 로
    else:
        본체+0x73c = jump
    (평지가 아니면 이동 속도 +0x114 를 바닥 법선 기준으로 돌려 y 성분 0, 크기 유지 — raw 5600~5690행)
    0x71024a8000: 점프 상태 요청(0x7102448ee4) + 본체+0x734 = 0
    0x710246b32c(..,1): +0xc0 = 0, +0x268 += 1
```

**점프 버튼 유지 가산** [판독] — 신규 (`0x7102482df8`, raw 5862~5895행):

```
if 본체+0x268 < 1 (접지 카운터 0 = 공중) && +0x73c + +0x754 > 0.001 && 본체+0x782 == 0:
    if (본체+0x72c(점프 버튼 누름) || Chariot 입력 플래그):
        if !(발사 +0x7f5 && 오징어 발사 +0x7f7):
            add = JumpGimmick(+0xa828)+0x30 ? 0.001 : 0.005·(1 − 0x710249bb60(본체+0xa2c, …))   // [0x71058bbc9c] / [0x71058bbc98]
        else add = [0x71058bc0e0] = 0
    elif 발사 +0x7f5 && +0x7f7: add = 0
    else: add 없음
    (3D 점프 중이면 +0x754 += add, 아니면 +0x73c += add)
if JumpGimmick+0x30 && +0x268 < 1 && +0x73c > 0.001:
    +0x73c += (1 − 0x710249bb60(...)) · (JumpGimmick+0x31 ? 0.002 : 0.005)                   // 점프대 계열
```

`0x710249bb60`(`analysis/decomp/move/move_jumphold.c`)은 본체+0xa38 > 0 일 때만 0이 아닌 값(그 값, 상한 처리)을 돌려준다. 평지 기본 상태에서는 0 → 가산 0.005/프레임 **[판독]**. 즉 **B(점프) 버튼을 누르고 있는 동안 상승이 길어진다**. 버튼 비트 해석(+0x72c = 패드 bit1)은 **[추정]**, 가산식은 **[판독]**.

**점프 곡선** — 이전 두 후보(1프레임째부터 중력 0.633/12f, 3프레임째부터 0.808/14f)를 **정정**. 이유: (1) 점프 프레임에는 수직 갱신(`0x71024a7d00`)이 점프 대입보다 먼저 실행되어 첫 이동량이 감쇠 없는 0.115이다, (2) 이동 속도 y(+0x118)가 `0x710245f964`로 공중 1~3프레임에 −0.002씩, 4프레임째부터 `0.92y − 0.0002`로 따로 내려가 최종 속도 y에 더해진다(§6.7), (3) 버튼 유지 가산이 있다. 상수 비트: g = 0x3c03126e(0.00799999945, 0.008의 최근접 f32보다 1ulp 작음), 점프 0x3deb851e(0.114999995), 0.98 = 0x3f7ae148.

| 입력(평지, 0AP, 스틱 중립) | 최고점 프레임(점프 프레임=1) | 최고 높이 | y ≤ 0 프레임 |
|---|---|---|---|
| 탭(점프 프레임만 누름) | 14 | 0.84145 | 30 |
| 5프레임 유지 | 16 | 1.06384 | 34 |
| 10프레임 유지 | 19 | 1.29583 | 38 |
| 계속 유지 | 30 | 1.73148 | 53 |

**[원본 실행(함수 연결)]** `web/tools/move_jump_emu.py --hold N`: `0x71024a7d00`(중력 `0x71024c9684` 포함)·`0x710246b574`·`0x710245f964`를 원본 그대로 프레임 순서대로 실행하고, 점프 대입·+0x734/+0xc0 리셋·유지 가산·Phive 적분(`y += 최종 y`)·착지(y ≤ 0)는 판독대로 대체. 재구현(같은 파일 `reimpl`)과 4경우 모두 vy·y 비트 일치(불일치 0). 결과 `analysis/move/jump_emu_hold{0,5,10,60}.json`. 메인 계산·Phive 스텝 자체는 실행하지 않았다.

### 6.5 공중/접지 보정 0x710245f964 [판독]

인자(호출 `0x710245edc0`, 기준 본체): param_1 = 본체+0xd2c, param_2 = 본체+0x7b8(발사 L), param_3 = &본체+0xc0, param_4 = 본체+0x72c, param_5 = [본체+0xa680] Jetpack, param_6 = [본체+0xa828] JumpGimmick, param_7 = 본체+0x180(바닥 법선 구조체), param_8 = 본체+0xa50, param_10 = **이동 속도 v(본체+0x114)** — 전체 분석본 `move_full_main.c` 12630행.

```
if 오징어 롤 발사 중(L+0x3c && !L+0x41 && L+0x3f && 시각 ≥ L+0x30): return        // 롤 동안 보정 없음
if (airFrames < 4):                          // [0x71058bbc20]
    if airFrames > 0 || (+0x734 == 0 && +0x73c > 0.001):      // 막 떨어짐, 또는 점프 프레임
        n = 바닥 법선(본체+0x180) (본체+0xa50+0x14 면 (0,1,0); 본체+0x1f8..(속도로 설명되지 않는 변위, player_state.md §7.3.1) 크기가 0.0019를 넘으면 그 방향과 |v| 0.012→0.002 비율로 혼합)
        v.y -= 0.002*n.y                       // [0x71058bbd8c]
        if airFrames ≥ 4 || +0x734 ≥ 4: v.xz -= 0.002*n.xz
else if (본체+0xf88+0x18 == 0 && !본체+0xfa5 && ![PC+0xe378]+0x1746):
    k = 본체+0x745 ? 0.96 : (JumpGimmick+0x30 ? 1.0 : 0.935)    // [0x71058bbc3c]/[…c38]
    (특수 0x18이면 k = k + (1-k)*jetpack[+0x13c])
    v.xz *= k
    v.y = v.y*0.92 - 0.0002                    // [0x71058bbc40]/[…c44]
```

`v.y = 0.92*v.y - 0.0002`(종단 −0.0025)는 **이동 속도 y**에 대한 보정이고, 낙하 중력은 수직 속도 +0x73c 쪽이다. 두 값은 `0x710245aed8`에서 최종 속도 y에 **더해진다**(§6.7) **[판독]**. 평지 점프에서 이동 속도 y는 점프 프레임부터 −0.002, −0.004, −0.006, −0.008(공중 0~3) 뒤 0.92 감쇠로 −0.0025 쪽으로 간다(§6.4 표에 반영).

같은 함수가 메인 계산 `0x710247cb48`에서 한 번 더 불리는데, 이때 대상은 발사 벡터(본체+0x7b8)이고 발사 프레임에만(본체+0x7f8, 오징어가 아닐 때) 쓰인다(§6.8).

> 정정(이전: "실제 낙하 가속은 Phive 캐릭터 컨트롤러(GravityScale 1.0)와 AirDumping/GameApplyVelocity 쪽에서 더해지는 것으로 보인다"): 중력은 **게임 코드가 별도 수직 속도 본체+0x73c에 더한다**(`0x71024a7d00`: `v = 0.98v`, 공중 프레임 ≥ 3이면 `v −= 0.008`). Phive 쪽은 (1) 게임이 GravityScale을 매 프레임 `0.008·3600/9.8` 또는 0으로 덮어쓰고, (2) SplPlayer의 공중 상태 GameInAir를 플레이어 초기화(`0x71024f4270`)에서 "게임이 넘긴 이동 속도를 그대로 쓰는" 모드(+0x1c=1)로 바꾸며, (3) AirDumping 계수는 0이라, 공중에서 Phive가 중력·감쇠를 더하지 않는다 **[판독]**. 근거와 단계 순서는 [../physics/phive_controller.md](../physics/phive_controller.md) §3~4.
>
> 해소(2026-10-02 [move]): 이동 벡터 y(0.92 감쇠)와 수직 속도 +0x73c는 최종 속도 합성 `0x710245aed8`에서 단순 합으로 만난다 — §6.7.

### 6.6 Phive 캐릭터 컴포넌트 [판독]

이름 → 생성자(0x7103a8367c 등록부) → vtable:

| 컴포넌트 | 크기 | vtable | 업데이트(슬롯 8) | 내용 |
|---|---|---|---|---|
| SplJump | 0x60 | 0x7105681c98 | 0x7102c6087c | 요청 플래그(+0x58)면 컴포넌트 필드 +0x38 = 요청값(+0x28); 공중 상태(종류 1)면 누적 임펄스(+0x40..)를 +0x34..로 옮기고 y ≥ -1000. **속도 인자는 건드리지 않음**(자기 필드만 갱신) |
| AirDumping | 0x40 | 0x71055744a8 | 0x71012aaa38 | 이동 상태별 계수(+0x28[상태], +0x34[상태]) × dt 로 법선/접선 성분 감쇠. **플레이어는 계수 0**(생성 시 0, `0x71024f4270`이 공중 계수를 다시 0으로 씀) |
| GameApplyVelocity | 0x58 | 0x7105574510 | 0x71012aaef8 | 최종 속도·각속도를 Phive 바디에 기록 |
| CliffSlip | 0x28 | 0x7105574590 | 0x71012ab4a8(빈 함수) | |
| GameFollowSurface | 0x60 | 0x71055745f8 | 0x71012aba18 | 발판 속도(결과 +0x3c..를 게임이 ×1/60로 읽음) |
| ImpactAndReject | 0x30(+데이터 0x68) | 0x7105574708 | 0x71012adb58 | 충격(+0x08)·밀어냄(+0x24) 가속 × dt를 속도에 더하고 감쇠 |
| SplAlongGnd | | | 생성 0x7102c5f850 | 미판독 |

실행 순서(프리셋 순서), 이동 상태(GameInAir/GameOnGround) 갱신식, 프레임 정보 구조는 [../physics/phive_controller.md](../physics/phive_controller.md) §3 **[판독]**.

### 6.7 최종 속도 합성 0x710245aed8 [판독] — 신규

호출: 메인 계산 `0x710247ccc0`(raw 6230행), 데모·워프 경로 `0x71024a7500`. 디컴파일 `analysis/decomp/move/move_compose.c`. 인자: F = 본체+0xe4(최종 속도 구조체), param_2 = 본체+0x10(위치·회전 행렬, +0xc.. 행), param_3 = 본체+0xa2c, param_4 = 본체+0x750(3D 점프), param_5 = [본체+0xa698](대시 패널), param_6 = [본체+0xa670](그라인드 레일), param_7 = 본체+0x588(특수 활성 쌍), param_9 = [본체+0xa7f0](SuperLanding), param_10 = SM, param_11 = 본체+0x72c(+0x10 = 수직 속도), param_12 = 본체+0x180.

```
// 대시 패널 속도 F[0x1d..0x1f](본체+0x158)
if !dash+0x39 || dash+0xf4:  if F[0x1d..] != 0: 이동 속도(F[0xc..], 본체+0x114) += F[0x1d..]; F[0x1d..] = 0
else: F[0x1d..] = dash+0x3c..
F[0..2] = F[0x1d..] + 이동 속도(+0x114) + F[0x1a..](+0x14c) + 3D 점프(+0x750) + F[6..8](+0xfc)
F[1]   += 수직 속도(본체+0x73c)                                   // ★ 수직 성분 합성
if SM+8(사람 ASB)의 루트 모션 노드(0x71039a0074(AS,0)+0x24) != 0: F += 본체 회전행렬 · 루트 모션
if 일반 경기 경로(세션 조건 통과):
    if [0x71058bbb83] == 0: F += 본체+0xa2c(벽·경사 보정 속도, player_state.md §7)
    F += 그라인드 레일 vt+0x1b8 속도
if 특수 활성 && 번호 0x1c(SuperLanding): F += SuperLanding+0x110.. + (0, +0xc8, 0)
elif 특수 활성 && 0x19(UltraStamp): F += (param_8+0x1d8..) − 법선 성분
if F[0x21](본체+0x168) > 0: F[0x21]--        // 넉백 카운터
```

이어서 메인 계산이 `0x71024f4f7c(PC, F[0..2] + F[0x12..0x14](본체+0x12c), 1)`로 Phive에 넘긴다(본체+0x12c는 프레임 시작에 0, raw 295행). 공중(InAir)에서는 F 전체가 이동 속도가 되고, 지상에서는 +0x73c만 빼고 넘긴다 — [../physics/phive_controller.md](../physics/phive_controller.md) §5.1.

결론: **최종 수직 속도 = 이동 속도 y(본체+0x118, §6.5 보정) + 수직 속도(+0x73c) + 3D 점프 y(+0x754) + 보조 항들(+0x100, +0x150, 루트 모션, +0xa30 …)**. 평지 점프에서는 앞의 둘만 남는다 **[판독]**.

### 6.8 벽 점프·오징어 롤 0x7102459630 [판독] — 신규

호출 3곳(`0x710247e1c4`, `0x7102481230`, `0x7102482c04`), 전체 분석본 `analysis/decomp/move/move_contact.c`. 인자: L = 본체+0x7b8(발사 구조체), param_2 = 본체+0x180(바닥 법선 — 오징어가 벽에 붙어 있으면 벽 법선), param_3 = 본체+0xe4, param_4 = [본체+0xa878](카메라), param_5 = 본체+0x474(스틱), param_6 = PlayerParam, param_8 = 본체+0x750, param_9 = 본체+0x72c, param_10 = 본체+0xa2c, param_16 = 롤 여부.

```
L.+0x3f = 상태 ∈ 0x82..0x90(오징어);  L.+0x38 = (L.+0x38+1) mod 8;  L.+0x3c = L.+0x3d = L.+0x40 = 1
L.+0x34 = 2;  L.+0x18.. = 액터 위치;  L.+0x41 = !param_16;  L.+0x30 = [[본체+8]+0x290](시각 [추정])
if param_16 (오징어 롤, 입력 링 버퍼에서 최근 방향과 60°([0x71058bc0bc]) 넘게 꺾임):
    dir = normalize(stick.y·aim + stick.x·(aim × up))       // aim = 카메라 rigForward(+0x1a4) 또는 본체+0x54c
    L[0..2] = dir · L.+0x2c(속력, writer [미확정]) · 1.0;  L[3..5] = dir
    → 메인 계산은 이어서 일반 점프를 하되 오징어였으면 jump = 0.1705 ([0x71058bc0c4])
else (벽 점프):
    L[0..2] = normalize(n.x, 0, n.z) · 0.192 ([0x71058bc0d0]);  L[3..5] = (0, −1, 0);  L.+0x54 = 15
    L.+0x58.. = 카메라 쪽 2D 방향 정규화
n = L.+0x24 (횟수, 10 상한);  L[0..2] *= PlayerParam+0x140(Somersault_MoveVelKd, 0AP 0.85 ~ 57AP 1.0) ^ n
if 벽 점프:
    본체+0xa30 = 0, 본체+0xa38..+0xa3f = 0;  3D 점프(+0x750..) = 0
    +0x73c = min(0.23 + 0·max(0, 이동 y + 3D 점프 y), 0.3)    // [0x71058bc0d4]=0.23, [0x71058bc0d8]=0, [0x71058bc0dc]=0.3
    Phive 상태 InAir 강제;  0x71024a8000(점프 시작: 상태 요청, +0x734 = 0)
(이후 본체+0xcfc+0x10 카운터 mod 8 증가(세션 조건), 본체+0xad0..+0xadc 정수들을 최소 6 등으로 올림 — 의미 [미확정])
```

- 메인 계산은 발사 프레임에 본체+0x7f8(L.+0x40)을 보고 이동 속도를 L[0..2]로 **한 프레임만** 바꾸고(사람이었으면 `0x710245f964`를 한 번 거침), cap(+0xd2c) = |L|, 플래그를 끈다(raw 6181~6195행). 다음 프레임부터는 일반 가속(§6.3)이 이 속도에서 출발한다 **[판독]**.
- 롤 동안(L.+0x3c && !L.+0x41 && L.+0x3f) `0x710245f964`가 공중 보정을 건너뛴다(§6.5) **[판독]**.
- 상수 0.23/0.3/0.192/0.1705는 **[실행(에뮬): 정적 초기화]**, 식은 **[판독]**. 0x71058bc0d8은 초기화 0x7102455db0이 `str x11(=0x3e99999a_00000000), [x8,#0x560]`으로 0을 쓴다(json 덤프에는 0이라 빠져 있음).
- 상태 연결: 벽 점프 직후 `0x71024a8000`이 점프 상태를 요청, 상태기계는 0x87 Walk 중 0x90 WallJump를 고르고 SM+0x1f4 = 게임 프레임(30프레임 안 ToHuman이면 0x95 ToHuman_WallJump) — [player_state.md §6.3](player_state.md). 오징어 롤은 0x8d/0x8e Somersault(본체+0x7f4 조건) **[판독: 상태 쪽은 [state] 보조 분석]**.

## 7. 애니메이션·이펙트·소리·카메라

- 이동 애니 블렌드: 0x7102442354(상태기계 기반, 거대 함수)가 애니 상태 객체의 속도값 `[obj+0xd4]`(플레이어 본체 아님)를 0.027/0.05 임계로 비교해 걷기/달리기 전환, 입력 크기 +0x47c>0 이면 정지 판정 임계 0.001, 아니면 0.003 **[판독: 상수], [미확정: 애니 이름 대응]**.
- 애니 리소스: `AS/SplPlayer.root.asb`, `AS/SplPlayerSquid.root.asb`(SplPlayer 팩) **[데이터]**. 상태 번호 → 상태 표 이름 = ASB 커맨드 이름으로 요청, 블렌드 프레임은 상태 표 값 **[판독]** — [player_state.md §5](player_state.md), 파일 구조 [../graphics/anim_state_machine.md](../graphics/anim_state_machine.md).
- 카메라 담당 요청 필드: +0x474/+0x478 = 이동 스틱, +0x47c = 데드존 재매핑 크기(위 4.1). 오른쪽 스틱 추정 +0xa9c/+0xaa0 은 확인하지 않음.

## 8. 다른 기능과의 상호작용

- **기어**: PlayerParam 캐시만 읽는다 → [gear_skills.md](gear_skills.md).
- **도색**: 발밑 잉크 비율은 `PlayerStepPaint`(+0xa688)의 +0x3c/+0x54. 갱신 0x710268b3b8(슬롯19 단계, 0x71024abcf0 안): 팀별 샘플 개수 c_t/N·min(N/15,1) → 아군 비율은 즉시, 적 비율은 오를 때 목표/3·내릴 때 0.25 씩, 이동용 +0x54 는 비율 +0x58(0→0.2, 10%/프레임)로 추종 **[판독]** — [player_state.md §8](player_state.md). 샘플을 채우는 도색 텍스처 조회 객체는 **[미확정]**(paint 영역).
- **벽 수영**: 오징어(S)가 아군 잉크 벽 위면 지면 법선 한계가 0.6414(50.1°) → −0.2571(104.9°)로 내려가 벽이 지면 취급된다(0x710268c3fc, 0x71024abcf0) **[판독]**. 벽 위에서는 아래쪽 vs가 −0.04 하한·×0.95로 줄고 위쪽 vs는 3D 점프 y로 넘어가며, 미끄러짐은 본체+0xa2c(상한 0.1)가 최종 속도에 더해 만든다 — [player_state.md §7.3](player_state.md). 벽 점프는 §6.8.
- **데미지**: 적 잉크 지속 데미지 값은 PlayerParam +0x110/+0x114(기어 반영). 적용 코드는 combat 영역에서도 미확정.
- **잉크레일**: gimmick 담당 판독(SHARED.md): 탑승 중 속도 0.92 감쇠·가속 0.05·최대 0.192.
- **네트워크**: PlayerNetState(Squid/Human variant) 4프레임 주기 송신(network 담당). 원격 플레이어 이동은 이 상태를 따른다 **[추정]**.

## 9. 웹 포팅 구조와 구현 순서

### 9.1 모듈

| 모듈(웹 권장 이름) | 책임 | 원본 대응 |
|---|---|---|
| `gearCalc` | AP → 기어 수치(순수 함수) | 0x710265df40 등 |
| `PlayerParamCache` | 장비 확정 시 기어 결과 캐시 | spl::PlayerParam +0xb0.. |
| `InkUnderFoot` | 발밑 아군/적 잉크 비율(0~1) | PlayerStepPaint +0x3c/+0x54 |
| `MoveController` | 목표 속도·cap·입력·속도 갱신 | 0x710245b2b4 |
| `AirController` | 공중 감쇠(이동 속도 y)·점프 판정/초기 속도·유지 가산·벽 점프/롤 | 0x710245f964, 0x7102475a54 점프부, 0x7102482df8, 0x7102459630 |
| `VerticalSpeed` | vy·jump3d·sinceJump·중력 | 0x71024a7d00, 0x71024c9684 |
| `FinalVelocity` | 이동 속도+vy+3D 점프+보조 항 합성, 바디 상태 공중 강제 | 0x710245aed8, 0x71024f4f7c |
| `ContactCounters` | 물리 뒤 공중/접지 프레임 카운터 | 0x71024abcf0 → 0x710246b574 / 0x710246b32c |
| `CharacterBody` | 충돌·중력·경사(캡슐 0.6/0.7, 법선 임계 0.6414) | Phive SplPlayer |

### 9.2 상태 객체

```ts
interface PlayerMoveState {
  vel: Vec3;          // 본체+0x114 이동 속도 (유닛/프레임)
  desired: Vec3;      // 본체+0x120
  cap: number;        // 본체+0xd2c
  dir: Vec3;          // 본체+0xd30
  inputMag: number;   // 본체+0xd3c = |dirRaw|^4
  stick: Vec2;        // 본체+0x474/0x478
  stickMag01: number; // 본체+0x47c
  airFrames: number;  // 본체+0xc0  슬롯19(물리 뒤)에서만 갱신
  groundFrames: number; // 본체+0x268
  airRatio: number;   // 본체+0xdc = min(airFrames/24, 1)
  jumpHeld: boolean;  // 본체+0x72c (+0x72d 눌린 프레임)
  sinceJump: number;  // 본체+0x734 (점프 시작 0, 수직 갱신마다 +1)
  vy: number;         // 본체+0x73c 수직 속도(위가 +)
  jump3d: Vec3;       // 본체+0x750
  launch: LaunchState;// 본체+0x7b8 벽 점프·롤 (§6.8)
  knock: { vec: Vec3; frames: number }; // 본체+0x16c / +0x168
  state: number;      // [본체+0xa8c8]+0xc8
}
```

### 9.3 프레임 순서 [판독] (§3.3)

1. 입력(`0x710249f494`): stick, stickMag01, jumpHeld/pressed, 오징어 요청(player_state.md §6).
2. 수직 갱신(`0x71024a7d00`): `sinceJump++`, `vy = 0.98·vy − (airFrames ≥ 3 ? g : 0)`, jump3d ×0.98.
3. 점프 판정(§6.4): canJump면 vy(또는 jump3d) = jump, `sinceJump = 0`, `airFrames = 0`, `groundFrames++`, 점프 상태 요청. 벽 점프·롤이면 §6.8.
4. 점프 유지 가산: 공중(groundFrames < 1)·상승 중·jumpHeld면 `vy += 0.005`.
5. 이동(`0x710245b2b4`): 목표 속도(§6.1) → cap(§6.2) → desired → accel(§6.3.1) → `vel += clamp(delta, accel)` → `vel.y ≤ 0.168` → 공중/접지 보정(§6.5).
6. 발사 프레임이면 vel = launch 벡터.
7. 최종 속도(§6.7) `final = vel + jump3d + (0, vy, 0) + 보조 항` → vy > 0.001이면 바디 상태를 공중으로.
8. 캐릭터 바디(Phive 대체)로 이동·충돌. 공중에서는 final을 그대로 1프레임 적분, 지상에서는 final − (0, vy, 0)을 지면 이동으로 — [../physics/phive_controller.md](../physics/phive_controller.md) §5.
9. 접촉 정리(슬롯19 `0x71024abcf0`): 바디가 지상(OnGround && 지지)이면 `airFrames = 0, groundFrames++`, 아니면 `airFrames++, groundFrames = 0` → StepPaint → 상태기계.

### 9.4 정밀도

- 기어 계산은 `Math.fround` 연산 단위 재현으로 원본과 비트 일치(검증됨).
- 이동 코드는 f32 연산. `0x710245b2b4`·`0x71024a7d00`·`0x710245f964` 범위에 fmadd/fmsub/fnmadd/fnmsub 명령이 없다(FMA 없음, 2026-10-02 disasm 전수) **[판독]** → 연산마다 `Math.fround`.
- 상수는 십진값이 아니라 원본 비트로 넣는다: g = 0x3c03126e, 점프 0x3deb851e는 `Math.fround(0.008)`·`Math.fround(0.115)`보다 1ulp 작다. `Math.fround(0.008)`을 쓰면 수직 속도가 점프 9프레임째부터 1ulp씩 어긋난다(`move_jump_emu.py` 작성 중 관측, §10).
- `b(x, s)`(기어·가속 곡선)는 원본이 `logf`/`expf`(PLT)로 계산하므로 브라우저 `Math.pow`와 1ulp 차이가 날 수 있다 — 기어 쪽은 같은 방식으로 비트 일치를 확인했다([gear_skills.md](gear_skills.md) §8).

## 10. 검증

| 종류 | 내용 | 결과 |
|---|---|---|
| 원본 실행(에뮬) | 정적 초기화 8057개를 unicorn으로 실행해 bss 상수 2530개 추출 (`player_initemu.py`) | 0x71058c034c = 0.8 등. 상수 값은 이 실행 결과를 근거로 함 |
| 원본 실행(에뮬) + 재구현 | 기어 함수 3개 원본 실행 vs `player_gear.py` 731값 | 차이 0 ([gear_skills.md](gear_skills.md) §8) |
| 원본 실행(함수 연결) + 재구현 | `move_jump_emu.py --hold {0,5,10,60}`: `0x71024a7d00`(+`0x71024c9684`)·`0x710246b574`·`0x710245f964` 원본을 프레임 순서대로 실행, 점프 대입·카운터 리셋·유지 가산·Phive 적분·착지는 판독대로 대체 | 4경우 30~53프레임 vy·y 비트 일치(불일치 0). §6.4 표. `analysis/move/jump_emu_hold*.json` |
| 원본 실행(단일 함수) | `0x71024c9684` 기본 상태 반환값 | 0x3c03126e(0.00799999945) |
| 재구현 계산 | `player_move.py demo`(목표 속도·cap 수렴·입력 곡선) | `analysis/player/move_demo.txt` — 원본 실행 비교는 아직 없음 |

기대값(재구현, 0AP, Mid): 인간 0.096, 적잉크 100% 위 인간 0.024, 오징어 아군잉크 0.192 / 무도색 0.072 / 적잉크 0.012, 아군·적 반반 0.102. 57AP 오징어 아군잉크 0.24. 점프(평지·탭) 최고 0.84145(14프레임), 계속 유지 1.73148(30프레임).

스텁·미검증: 이동 함수 `0x710245b2b4` 자체(목표 속도·accel)는 실행하지 않았다(본체 포인터 수십 개 필요) — accel 식은 판독. 점프 실행에서 메인 계산의 점프 판정·유지 가산(`0x7102482df8`)·Phive 스텝·착지 검출은 원본이 아니라 대체다. Phive가 점프 프레임에 공중 상태를 유지한다는 가정이 틀리면 공중 카운터가 1프레임 밀린다(§3.3).

## 11. 미확정 사항과 필요한 근거

| 항목 | 상태 | 필요한 근거 |
|---|---|---|
| 중력 값·낙하 곡선 | **해소 [판독 + 실행(함수 연결)]** | g = 0x3c03126e, `vy = 0.98vy − g`(공중 ≥ 3), +0xc0 writer = 슬롯19 `0x710246b574`/`0x710246b32c`, 점프 프레임 순서(수직 갱신 → 점프 대입 → 유지 가산 → 이동 → 합성), 최종 y = 이동 y + vy — §3.3, §6.4~6.7. 남은 것: Phive가 점프 프레임에 InAir를 유지한다는 가정 [추정] |
| 컨트롤러 단계 실행 순서 | **해소 [데이터+판독]** | 프리셋 순서대로 슬롯 8 호출(`0x7103a80560`), 이동 상태 배열 [0]=OnGround/[1]=InAir/[2]=Free — 같은 문서 §3 |
| 가속량 accel 전체 식 | **해소 [판독]** | §6.3.1. 남은 것: 분기 플래그 본체+0x4d8·+0xfa5·[PC+0xe378]+0x1746·+0xa5c·+0xad8·`0x7102458cfc`의 게임 의미 [미확정] |
| 상태 번호 ↔ 이름(인간 걷기/오징어 수영/벽 등) | **해소 [데이터+판독]** | 상태 표 0x7105630270, 형태 안 전이 조건(0x7102442354) 우선순위·요청 41곳 — [player_state.md §4, §6.3](player_state.md) |
| 벽 수영·벽 타기·벽 점프 | **해소 [판독]** | 법선 한계(player_state.md §7.2), 접촉 정리 출력 필드·벽 위 수직 속도·미끄럼·착지·천장(player_state.md §7.3), 벽 점프·롤(§6.8). 남은 것: Phive가 오징어 벽 접지를 주는지 [추정], PC·[PC+0xe378] 일부 필드, 본체+0x488 writer |
| 발밑 잉크 비율 계산 | **해소 [판독]** | 0x710268b3b8 — 샘플 수집 객체(도색 텍스처 조회)만 미확정 |
| 이동 속도 벡터 되쓰기 위치 | **해소 [판독]** | 메인 계산이 `0x710245b2b4` 결과를 본체+0x114(raw 6224행 `param_1-0xa4e8`)와 desired를 +0x120에 되씀 |
| 0x710266c6e4 (오징어 속도 배율 k) | 미판독 | 디컴파일 있음(`playerparam_gear.c`) |
| WeaponShooterParam.MoveSpeed(사격 중 이동) 적용 | **해소 [판독+데이터]** | §6.1 사격 중 이동 — 잉크액션 보조 vt[0x30] → 주 vt 슬롯35 |
| 코옵(+0x180) 대체 경로 | **해소 [판독+실행(에뮬)]** | +0x180 = 씬 플래그 `Scene_Coop`, +0x188 = 원 파라미터 직접 읽기 객체(타입 이름만 미확정) |
| 슬롯19 0x7102483134 | 호출 순서만 판독 | 고유 호출 123개 순서([player_state.md §3.2](player_state.md)): 접촉·벽(0x71024abcf0) → StepPaint → 상태기계(0x710243e7d0) → 모델. 각 단계 조건 미확정 |
| 메인 계산 0x7102475a54(7601줄) | 부분 판독 | 일반 경로 순서(§3.3)·점프·유지 가산·이동·합성·Phive 전달 판독. 데모/워프(`0x71024a7500`)·원격(PlayerRemote)·특수 무기 분기는 미판독 |
| 점프 버튼 비트 | 추정 | 본체+0x72c = InputSender+0x58 = 패드 상태 +0x114 bit1(nn::hid B로 추정). 컨트롤러 객체(`0x7103d55638` 반환) 레이아웃 판독 필요 |
| 본체+0x780/+0x782(점프 허용·유지 가산 차단 플래그) | 미확정 | writer 메인 계산(전체 분석본 1148~1154행 1, 5232/6280/6412행 해제) — [state] 보조 분석: 벽 점프 진행 관련 [추정] |
| 오징어 롤 속력 L.+0x2c(본체+0x7e4) | 미확정 | writer 미추적(`0x7102459630`은 읽기만) |
| 오징어 롤·벽 점프 횟수 L.+0x24(본체+0x7dc) 의미 | 추정(연속 횟수) | writer 미추적 |
