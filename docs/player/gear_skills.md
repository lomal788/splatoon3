# 플레이어 기어(능력) 효과 계산 — 이동 관련

[movement_physics.md](movement_physics.md)의 하위 문서입니다. 기어 능력(HumanMoveUp, SquidMoveUp, OpInkEffectReduction 등)이 AP에서 실제 수치로 바뀌는 계산과, 그 결과가 저장되는 `spl::PlayerParam` 필드를 다룹니다.

## 1. 개요

- 사용자에게 보이는 동작: 인간 이동 속도 업(ヒト速)·오징어 속도 업(イカ速)·상대 잉크 영향 감소(安全靴)의 AP가 올라갈수록 속도/내성이 비선형으로 오른다.
- 원본: Splatoon 3 v0 main NSO. 함수 주소는 0x7100000000 기준.
- 결론 요약
  - AP → 효과 비율 p, 그리고 Low/Mid/High 세 값의 비선형 보간 식을 원본 명령으로 판독했고, 원본 함수를 unicorn으로 직접 실행한 결과와 파이썬 재구현이 **731건 모두 비트 단위로 일치**했다 **[실행(에뮬) + 판독]**.
  - 결과는 `spl::PlayerParam`(플레이어 본체 +0xa658) 안 +0xb0~+0x118에 캐시된다 **[판독]**.

## 2. 자료 위치

| 항목 | 위치 |
|---|---|
| 기어 파라미터 기본값 | 코드 생성자. `SplPlayer.game__GameParameterTable`에는 `$type`만 있고 값이 없다(= 생성자 기본값 사용) **[데이터]** |
| 리플렉션 결과 | `web/tools/param_reflect.py MoveVel_Human_Low ...` 출력, `analysis/param_reflect/spl__PlayerGearSkillParam_*.json` |
| 디컴파일 | `analysis/decomp/player/playerparam_gear.c` |
| 재구현 | `web/tools/player_gear.py` |
| 원본 실행 비교 | `web/tools/player_gear_emu.py` → `analysis/player/gear_emu_result.txt` |

## 3. 진입점과 호출 흐름

```
플레이어 본체 init 0x710234b580
  └ spl::PlayerParam 생성 0x710265c548 (0x260 B, vtable 0x710563dea8) → 본체 +0xa658
PlayerParam vtable 슬롯25 0x71024265a0  (GameParameterTable 바인딩)
  └ 0x7100f5e51c(table, "$type 이름")로 파라미터 객체를 찾아 PlayerParam+0x198.. 에 저장
기어 계산 함수들(호출자 0x710265ca04가 능력 열거 순서로 호출, paint 담당 판독 [판독])
  0x710265ca78  AP 집계(메인·서브 AP + 조건부 가산; 특수 능력 효과)            [판독+실행: §5.4/§10]
  0x710265df40  HumanMoveUp      → +0xb0 +0xb4 +0xb8 +0xbc
  0x710265fd48  SquidMoveUp      → +0xc0 +0xc4 +0xc8
  0x7102665ee4  OpInkEffectReduction → +0x100 ~ +0x118
  (그 밖: 0x7102660b70 InkRecoveryUp +0xcc/+0xd0, 0x71026614b8 MainInkSave +0xd4,
   0x7102662718 SubInkSave +0xd8~+0xe4, 0x7102663808 SpecialIncreaseUp +0xe8,
   0x7102663d84 RespawnSpecialGaugeSave +0xec, 0x7102664300 RespawnTimeSave +0xf0/+0xf4,
   0x7102664c48 SuperJumpTimeSave +0xf8/+0xfc, 0x7102665590 ActionSpecUp_Squid +0x13c/+0x140)
```

호출 시점은 이전 판에서 **[미확정]**이었다. 2026-10-03 5차 판독: 메인 계산 `0x7102475a54`가 **매 프레임** `0x71024761e8`에서 AP 집계 `0x710265ca78(PlayerParam)`을 부르고, 반환값이 참일 때만 `0x71024761f4`에서 `0x710265ca04`(기어 계산 11개 연속 호출 + `0x7102667b50`)를 부른다. `0x710265ca78`은 14개 능력의 (메인 + 서브) AP 합을 PlayerParam+0x3c/+0x74의 직전 값과 비교해 하나라도 다르면 참을 돌려준다(전역 바이트 `0x71058e87c8`이 0이면 거짓). 그 밖에 `0x71024744c0`(함수 `0x71024719d4`), `0x7102490f40`(`0x71024901c4`), `0x7102491dc4`(`0x7102491b68`)가 `0x710265ca04`를 조건 없이 부른다(이 세 함수의 게임 의미는 **[미확정]**). 결과가 PlayerParam에 캐시되고 이동 코드는 캐시만 읽는다 **[판독]**.

## 4. 구조체·필드

### 4.1 `spl::PlayerParam` (기준 객체: 플레이어 본체 +0xa658가 가리키는 0x260 B 객체)

| 오프셋 | 타입 | 의미 | writer | reader |
|---|---|---|---|---|
| +0x3c + id*4 | s32[14] | 장비 기본 AP(메인10 + 서브3/6 합산) | 0x710265ca78 → 0x710266db4c | 각 계산 함수 |
| +0x74 + id*4 | s32[14] | 해당 tick 조건부 보너스 AP | 0x710265ca78 | 각 계산 함수 |
| +0xac | u32 | 특수 능력 비트(값-100 번째 비트) | 장비 dirty 재집계 0x710266db4c | 0x710265ca78/0x710265fd48 |
| +0xb0 | f32 | 인간 속도(WeaponSpeedType Mid) | 0x710265df40 | 0x710245b2b4 |
| +0xb4 | f32 | 인간 속도(Slow) | 〃 | 〃 |
| +0xb8 | f32 | 인간 속도(Fast) | 〃 | 〃 |
| +0xbc | f32 | 사격 중 이동 배율(MoveVelRt_Shot) | 〃 | 0x710245b2b4 등 |
| +0xc0/+0xc4/+0xc8 | f32 | 오징어 속도 Mid/Slow/Fast | 0x710265fd48 | 0x710245b2b4, 0x7102475a54 |
| +0x100 | f32 | 적 잉크 위 점프 속도 | 0x7102665ee4 | 0x7102475a54(점프) |
| +0x104 | f32 | 적 잉크 위 이동 속도 | 〃 | 0x710245b2b4 |
| +0x108 | f32 | 적 잉크 위 사격 중 이동 속도 | 〃 | 0x710245b2b4 |
| +0x10c | f32 | 적 잉크 ShotK | 〃 | 미확정 |
| +0x110 | f32 | 적 잉크 지속 데미지/프레임 | 〃 | PlayerStepPaint 갱신 `0x710268b3b8` [판독] — [player_state.md §8.2](player_state.md), [../combat/player_life.md](../combat/player_life.md) |
| +0x114 | f32 | 적 잉크 데미지 한계 | 〃 | `0x710268b3b8` [판독] |
| +0x118 | f32 | 적 잉크 아머 HP(실제로는 적 잉크 무데미지 프레임 수 상한) | 〃 | `0x710268b3b8` [판독] — [../combat/player_life.md](../combat/player_life.md) §1 |
| +0x13c | f32 | ActionSpecUp_Squid WallJumpChargeFrm 결과(벽 점프 충전 프레임) | 0x7102665590 | 상태 결정 0x7102442354 지상 공통 H(0x8f WallJumpCharge 판정의 보간 상한) [판독, 2026-10-02 [move] 보조 분석] — [player_state.md §6.3](player_state.md) |
| +0x140 | f32 | ActionSpecUp_Squid Somersault_MoveVelKd 결과(0AP 0.85 ~ 57AP 1.0) | 0x7102665590 | 벽 점프·오징어 롤 0x7102459630: 발사 속도 ×(+0x140)^n (n = 본체+0x7dc, 10 상한) [판독] — [movement_physics.md §6.8](movement_physics.md) |
| +0x148/+0x150 | 핸들 | `PlayerGearSkillParam_MainWeaponSetting`(무기별) | 미확정 | 0x710265df40, 0x7102669b90 |
| +0x168 | ptr | 대체 계산 객체(있으면 이동 코드가 0x710264e85c 등으로 값 대체) | 0x710266d99c | 0x710245b2b4 |
| +0x180 / +0x188 | u8 / ptr | 대체 모드 플래그 / 대체 객체(0x71024fefe4 등 getter 사용) | 0x710266d99c(+0x180 = 전역 0x71058e87a4) | 이동 코드 |
| +0x198 ~ +0x200 | ptr | 기어 파라미터 객체(아래 표) | 0x71024265a0 | 계산 함수 |

| PlayerParam 오프셋 | `$type` |
|---|---|
| +0x198 | spl__PlayerGearSkillParam_HumanMoveUp |
| +0x1a0 | spl__PlayerGearSkillParam_SquidMoveUp |
| +0x1a8 | spl__PlayerGearSkillParam_InkRecoveryUp |
| +0x1b0 | spl__PlayerGearSkillParam_MainInkSave |
| +0x1b8 | spl__PlayerGearSkillParam_SubInkSave |
| +0x1c0 | spl__PlayerGearSkillParam_SpecialIncreaseUp |
| +0x1c8 | spl__PlayerGearSkillParam_RespawnTimeSave |
| +0x1d0 | spl__PlayerGearSkillParam_RespawnSpecialGaugeSave |
| +0x1d8 | spl__PlayerGearSkillParam_SuperJumpTimeSave |
| +0x1e0 | spl__PlayerBeaconSubSpecUpParam |
| +0x1e8 | spl__PlayerMissionSkillParam |
| +0x1f0 | spl__PlayerGearSkillParam_OpInkEffectReduction |
| +0x1f8 | spl__PlayerGearSkillParam_SubEffectReduction |
| +0x200 | spl__PlayerGearSkillParam_ActionSpecUp_Squid |

`+0x180`이 켜진 모드(대체 getter 0x71024fefe4/0x71024ff2a4/0x71024ff564 등, `+0x188` 객체)의 정체는 이전 판에서 **[미확정]**이었다. 해소(2026-10-02 [move], [movement_physics.md §6.1](movement_physics.md)): +0x180은 씬 플래그 `Scene_Coop`(연어런)에서 켜지고 대전·사격장에서는 0이다 **[판독+실행(에뮬)]**. +0x188이 가리키는 파라미터 타입 이름만 **[미확정]**이다.

### 4.2 능력 열거형 [데이터]

`main_strings.txt`: `None = -1 , MainInk_Save = 0 , SubInk_Save = 1 , InkRecovery_Up = 2 , HumanMove_Up = 3 , SquidMove_Up = 4 , SpecialIncrease_Up = 5 , RespawnSpecialGauge_Save = 6 , SpecialSpec_Up = 7 , RespawnTime_Save = 8 , JumpTime_Save = 9 , SubSpec_Up = 10 , OpInkEffect_Reduction = 11 , SubEffect_Reduction = 12 , Action_Up = 13 , StartAllUp = 100 , EndAllUp = 101 , MinorityUp = 102 , ComeBack = 103 , SquidMoveSpatter_Reduction = 104 , DeathMarking = 105 , ...`

계산 함수는 이 값을 상수로 넣어 AP 배열을 고른다(HumanMove 3, SquidMove 4, OpInk 11) **[판독]**.

### 4.3 기어 파라미터 기본값 (생성자 판독) [판독]

필드 순서는 항상 `High` 오프셋 < `Low` < `Mid` (예: +0x3c High, +0x40 Low, +0x44 Mid). 표의 값은 (Low, Mid, High) = (0AP, 중간 기준, 57AP).

| 파라미터 | 필드(오프셋 L/M/H) | Low | Mid | High | 결과 |
|---|---|---|---|---|---|
| HumanMoveUp `MoveVel_Human_*` | 0x40/0x44/0x3c | 0.096 | 0.12 | 0.144 | +0xb0 |
| HumanMoveUp `MoveVel_Human_Slow_*` | 0x4c/0x50/0x48 | 0.088 | 0.116 | 0.144 | +0xb4 |
| HumanMoveUp `MoveVel_Human_Fast_*` | 0x34/0x38/0x30 | 0.104 | 0.124 | 0.144 | +0xb8 |
| HumanMoveUp `MoveVelRt_Shot_*` | 0x58/0x5c/0x54 | 1.0 | 1.125 | 1.25 | +0xbc |
| SquidMoveUp `MoveVel_Stealth_*` | 0x40/0x44/0x3c | 0.192 | 0.216 | 0.24 | +0xc0 |
| SquidMoveUp `MoveVel_Stealth_Slow_*` | 0x4c/0x50/0x48 | 0.1728 | 0.216 | 0.24 | +0xc4 |
| SquidMoveUp `MoveVel_Stealth_Fast_*` | 0x34/0x38/0x30 | 0.2016 | 0.2208 | 0.24 | +0xc8 |
| OpInk `OpInk_JumpVel_*` | 0x58/0x5c/0x54 | 0.08 | 0.098 | 0.11 | +0x100 |
| OpInk `OpInk_MoveVel_*` | 0x64/0x68/0x60 | 0.024 | 0.05568 | 0.0768 | +0x104 |
| OpInk `OpInk_MoveVel_Shot_*` | 0x70/0x74/0x6c | 0.012 | 0.033 | 0.042 | +0x108 |
| OpInk `OpInk_MoveVel_ShotK_*` | 0x7c/0x80/0x78 | 0.5 | 0.75 | 1.0 | +0x10c |
| OpInk `OpInk_DamagePerFrame_*` | 0x4c/0x50/0x48 | 0.003 | 0.00225 | 0.0015 | +0x110 |
| OpInk `OpInk_DamageLmt_*` | 0x40/0x44/0x3c | 0.4 | 0.3 | 0.2 | +0x114 |
| OpInk `OpInk_ArmorHP_*` | 0x34/0x38/0x30 | 0 | 26 | 39 | +0x118 |
| ActionSpecUp_Squid `WallJumpChargeFrm_*` | 0x40/0x44/0x3c (s32) | 60 | 40 | 20 | (데이터 덮어씀: 45/18/5) |
| ActionSpecUp_Squid `Somersault_MoveVelKd_*` | 0x34/0x38/0x30 | 0.85 | 0.925 | 1.0 | +0x140 |

- "설정됨" 플래그 바이트: HumanMoveUp +0x60~+0x6b, SquidMoveUp +0x54~+0x5c, OpInk +0x84~+0x98. 플래그가 0이면 `$parent` 체인으로 올라가 값을 찾는다(bullet 담당 판독과 같은 규칙) **[판독]**.
- `PlayerGearSkillParam_MainWeaponSetting`(무기 팩마다, 70개 파일): 생성자 기본값 `Overwrite_*` 전부 -1.0(= 덮어쓰지 않음), `WeaponAccType`(+0x48) 1, `WeaponSpeedType`(+0x4c) 1 **[판독]**. 데이터 분포: WeaponSpeedType 기본(Mid) 50개, `Fast` 14개, `Slow` 6개 **[데이터]**. 열거 문자열 `Slow , Mid , Fast` → 0/1/2이며 코드의 선택(0→+0xb4, 2→+0xb8, 그 외 +0xb0)과 일치 **[판독]**.

## 5. 계산식 [판독 + 실행(에뮬)]

### 5.1 AP → 비율 p

```
ap = float(mainAP[id] + subAP[id])          // id: 0..13, 범위 밖이면 id 0 슬롯
ap = min(ap, 57.0)
p  = ap * (ap * -0.027 + 3.3) / 100.0       // f32 연산, 이 순서
p  = clamp(p, 0, 1)                          // p>1 → 1, p<0 → 0
if (id == SquidMove_Up && (PlayerParam.+0xac >> 4) & 1)   // 특수 능력 값 104(SquidMoveSpatter_Reduction) 비트
    p = clamp(p * 0.8, 0, 1)                 // 0.8 = 전역 [0x71058c034c], 정적 초기화 0x710265c230이 씀 [실행(에뮬)]
```

능력 104의 표시 이름은 이전 판에서 **[미확정]**이었다. 해소(2026-10-03 5차): `Mals/<언어>.Product.100.sarc.zs`의 `CommonMsg/Gear/GearPowerName.msbt`에서 라벨 `SquidMoveSpatter_Reduction`(열거 이름과 같은 문자열)의 값이 USen "Ninja Squid", KRko "징어닌자", JPja "イカニンジャ"다 **[데이터]**. 같은 파일에서 100 StartAllUp = "스타트 대시", 103 ComeBack = "컴백", 105 DeathMarking = "리벤지"(KRko).

### 5.2 Low/Mid/High 비선형 보간 (모든 기어 계산 함수에 인라인)

```
range = High - Low
// s = Mid가 Low..High 구간에서 차지하는 위치(클램프 역보간, 방향 무관)
if Low <= High:
    s = (Mid <= Low) ? 0 : (Mid >= High) ? 1 : (range == 0 ? 0 : (Mid - Low)/range)
else:
    t = (Mid <= High) ? 0 : (Mid >= Low) ? 1 : ((Low-High)==0 ? 0 : (Mid - High)/(Low - High))
    s = 1 - t
// k = 보간 계수
if |s - 0.5| <= 0.001:  k = p                      // 정확히는 (s-0.5) > 0.001 또는 < -0.001 일 때만 아래
else if |p| < 0.001:    k = 0
else if s < 0.001:      k = (|p| >= 0.999) ? 1 : 0
else:                   k = expf( logf(|p|) * (logf(s) * -1.442695) )   // = |p|^(-log2 s)
result = Low + range * k
```

- 상수 0.001 = 0x3a83126f, 0.999 = 0x3f7fbe77, -1.442695 = 0xbfb8aa3b **[판독]**.
- `logf`·`expf`는 SDK 임포트(PLT 0x7103e9c2a0, 0x7103e9be20). 웹에서는 `Math.log`/`Math.exp` 결과를 `Math.fround`로 감싸면 된다. 이번 비교에서 파이썬 `math.log/exp`+f32 반올림 결과가 원본 실행과 비트 일치했다 **[실행(에뮬)]**. 다만 에뮬에서도 log/exp는 파이썬으로 대신 계산했으므로 SDK 수학 라이브러리 자체의 1ulp 차이는 검증 범위 밖이었다. 정정(2026-10-03 5차): SDK logf/expf를 직접 실행하면 1740건 중 1건이 1ulp 다르다(§9 아래 교정 이력).
- HumanMoveUp Mid(0.12)는 정확히 중점이라 Human 속도는 p에 선형 **[실행(에뮬)]**.

### 5.3 사격 중 이동 배율(+0xbc)

Low/Mid/High = HumanMoveUp `MoveVelRt_Shot_*` 이지만, 무기의 `MainWeaponSetting.Overwrite_MoveVelRt_Shot_{Low,Mid,High}`(+0x40/+0x44/+0x3c)가 **0 이상**이면 그 값으로 바꾼다(필드별) **[판독]**. 같은 보간을 HumanMove AP(id 3)로 한다.

### 5.4 장비 재집계·조건부 AP 수명 (2026-10-03, r8 신규) **[판독]+[실행]**

기준 객체는 `P=PlayerParam`, `B=본체`, `A=P+0x190의 액터`다. 기존 +0x3c/+0x74를 각각 메인·서브 AP라고 부른 것은 **저장 의미를 잘못 요약한 것**이었다. 실제 `0x710266db4c`가 장비 메인·서브를 모두 +0x3c에 더하고, `0x710265ca78`은 매 tick +0x74를 지운 뒤 조건부 보너스를 쓴다. §5.1의 합산 계산은 그대로이며 이름만 정정한다. 이 결과는 이전 r5의 변화 비교/재계산 호출 판독을 재사용하고, 이번에 새로 판독·실행한 집계 분기를 추가한 것이다.

- `0x7100ff037c`가 만드는 기어 enum은 `[-1, 0..13, 100..111]`. 장비 필드는 능력 값 자체가 아닌 **enum 인덱스**다. 범위 밖 인덱스는 enum 슬롯0(None=-1)로 바뀐다. `0x71024cdd94`의 특수 능력 enum은 `[100..111]`이다. 두 초기화 함수를 원본으로 실행했다.
- `P+0x38 != 0`이면 기본 AP 14칸과 특수 비트 `P+0xac`를 0으로 지우고, `P+0x30`이 있으면 +0x100/+0x308/+0x510 세 장비를 `0x710266db4c`로 집계한 뒤 dirty byte를 0으로 한다. 장비 +0x84 메인 능력은 AP10. +0x88 포인터/+0x90 용량/+0x94 시작/+0x98 개수의 링에 저장된 stride0x78 항목 +0x70 서브 능력은 AP3이며 **메인 능력108이면 AP6**이다. 능력100..111은 AP 칸 대신 해당 특수 비트를 켠다.
- 전역 byte `0x71058e87c8==0`이면 이 집계/보너스 갱신을 하지 않고 거짓을 반환한다. writer `0x7102b56590`은 `0x7102b578e0`의 결과를 저장한다. 이 함수는 씬 비트 표가 참이거나 씬 이름이 **LobbyVersus/LobbyLocal/ShootingRange**이면 참이다. 따라서 Lby_Lobby00의 LobbyVersus는 AP 집계가 켜진다. 문자열 경계 9건을 원본으로 실행했다. 비트 표의 BYML 해석 자체는 이번 시험에서 대체하지도 실행하지도 않았으며 음수 인덱스로 문자열 경로만 선택했다.

`f=max(GameFrame+0x148,0)`이고 아래 순서대로 **같은 보너스 배열에** 더한다. 아래의 `gate=(0x71058e8774!=0 || 0x71058e8778!=0)`는 writer `0x7102b546e0` 안에서 game-rule bit와 `session+0x6548`의 rule+0x38로 계산한다. 8774는 규칙값1 또는4, 8778은 `(규칙값 & ~1)==2`가 추가 조건이다. 씬 AP 활성 byte와 이 두 rule byte를 혼동하지 않는다.

| 순서 | 조건 | 변경 및 원본 상수 |
|---|---|---|
| 1 StartAllUp(100) | 특수 bit0, gate, `f<P+0x178` | id3/4/11 각각 +30 (`58c038c/390/394`) |
| 2 EndAllUp(101) | 특수 bit1, gate, 매니저 `[*GOT5796510]` 유효 | 아래 `a`로 id0/1/2 각각 `trunc32(f32(기존 AP + f32(24*a)))`, 상수 `58c03a4/a8/ac` |
| 3 ComeBack(103) | 특수 bit3, `B+0xe54>=0`, `f<B+0xe54+1200` | id0..5 각각 +10 (`58c0368=1200`, `58c036c..380=10`) |
| 4 ForwardRoll | `[B+0xa838]+0xe94>0` | id3/4/11 각각 +30 (`58c035c/360/364`) |
| 5 boost | `[*GOT5795dd8]+0x1f!=0` 또는 `f<B+0xa5a0` | id6/8/9/11/13 각각 +57 (`58c0408`); id3/id4는 기본+보너스의 합이 최소29가 되도록 보너스 변경 (`58c0400/404`) |

EndAllUp의 `a`는 매니저 +0x50에서 현재 f를 뺀 남은 프레임이 **1800보다 작으면1, 그 외0**이다. +0x50이 INT_MIN이면 남은 프레임을 `0x7ffff`로 취급한다. 매니저+0x128 점수 객체가 있으면 그 객체 링(`+0x10d0/10d8/10dc/10e0`, stride0x80)의 **상대 팀**(+0x78 s32 count)을 사용한다. 액터 팀668=0이면 인덱스1, 그 외 인덱스0. count<=50이면 `a=max(a, min(1, f32(f32(51-count)/21)))`다. **최종 min(1,...)은 원본 `0x710265cfe4 FMIN`**이며 기존 Ghidra 출력이 이 블록을 unreachable이라 삭제했다. 이 클램프를 생략한 첫 비교에서 불일치가 났고 명령대로 복원한 후 전 건 일치했다. 1800/50/30/24는 원본 전역 58c0398/39c/3a0/3a4 등에서 읽었다.

14개 능력의 이전 `(기본AP+보너스AP)`와 새 합이 하나라도 다르면 참을 반환한다. **보너스는 매 tick 초기화**, 장비 기본 AP/특수비트는 dirty 재집계 전까지 유지한다. 따라서 ComeBack/ForwardRoll/boost가 끝나면 다음 집계 tick에 해당 가산이 사라진다. AP57 상한은 이 집계 함수가 아니라 §5.1의 AP→비율 변환에서 적용한다.

MinorityUp(102) 말미는 AP14칸을 변경하지 않는다. 별도 `P+0x17c`를 먼저0으로 하고, 원본 guard를 통과한 유효·생존 액터의 팀별 수에서 상대가 더 많으면 차1/2/3이상에 따라 1/2/3(`58c03f4/f8/fc`)에 `2 * (1/60) * 211.2`를 곱한다. 네트워크 모드의 실제 액터 목록과 해당 게이지 소비는 이번 사격장 AP14칸 집계 범위 밖이다. `P+0x168` 대체 객체의 장비 변경 요청도 별도 모드 동작이며 합성 실행에서는 null이다. 이 한계를 AP 집계 함수 전체 게임 실행으로 확대하지 않는다.

## 6. 결과 표 (재구현 = 원본 실행, 유닛/프레임)

`web/tools/player_gear.py table` 출력 일부(전체 `analysis/player/gear_table.tsv`).

| AP | p | 인간 Mid | 인간 Slow | 인간 Fast | 사격배율 | 오징어 Mid | 오징어 Slow | 오징어 Fast | 적잉크 이동 | 적잉크 점프 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0.096 | 0.088 | 0.104 | 1.0 | 0.192 | 0.1728 | 0.2016 | 0.024 | 0.08 |
| 10 | 0.303 | 0.110544 | 0.104968 | 0.11612 | 1.07575 | 0.206544 | 0.204192 | 0.213235 | 0.0459016 | 0.0924441 |
| 20 | 0.552 | 0.122496 | 0.118912 | 0.12608 | 1.138 | 0.218496 | 0.218812 | 0.222797 | 0.0580763 | 0.0993615 |
| 30 | 0.747 | 0.131856 | 0.129832 | 0.13388 | 1.18675 | 0.227856 | 0.228598 | 0.230285 | 0.0665869 | 0.104197 |
| 57 | 1 | 0.144 | 0.144 | 0.144 | 1.25 | 0.24 | 0.24 | 0.24 | 0.0768 | 0.11 |

(전 AP는 `analysis/player/gear_table.tsv`. 같은 AP를 원본 함수 에뮬 실행으로도 얻어 차이 0을 확인.)

## 7. 웹 포팅

```ts
// 원본 이름 ↔ 웹 권장 이름
// PlayerParam+0xb0/b4/b8 → gear.humanSpeed[speedType]   (speedType: 0 Slow, 1 Mid, 2 Fast)
// PlayerParam+0xc0/c4/c8 → gear.squidSpeed[speedType]
// PlayerParam+0xbc       → gear.shotMoveRate
// PlayerParam+0x100..118 → gear.opInk.{jumpVel, moveVel, moveVelShot, shotK, damagePerFrame, damageLimit, armorHp}
const f = Math.fround;
function apRate(ap: number, ninjaBit = false): number {
  let a = f(Math.min(ap, 57));
  let p = f(f(a * f(f(a * f(-0.027)) + f(3.3))) / f(100));
  p = p > 1 ? 1 : p < 0 ? 0 : p;
  if (ninjaBit) { p = f(p * f(0.8)); p = p > 1 ? 1 : p < 0 ? 0 : p; }
  return p;
}
function gearLerp(low: number, mid: number, high: number, p: number): number { /* 5.2 그대로, 모든 연산 f() */ }
```

- 서버/클라이언트 공유: 순수 함수이므로 공용 모듈로 둔다. 결과는 장비 확정 시 한 번 계산해 캐시(원본도 캐시) **[판독: 캐시] / [미확정: 재계산 시점]**.
- 기어 파라미터 값은 데이터 파일이 비어 있으므로 위 4.3 표(생성자 기본값)를 상수로 넣는다. 무기별 `MainWeaponSetting`은 각 무기 GameParameterTable에서 읽는다.

## 8. 검증 [실행(에뮬)]

`web/tools/player_gear_emu.py`:

- 합성 상태: PlayerParam 0x260 B 영역에 AP만 넣고, 파라미터 객체는 4.3 기본값 + 플래그 1. 기어 열거 표(0x71058c0458/60/68)는 0..13 항등, 특수능력 표(0x71058bc378/80/88)는 100..111로 채움. 전역 상수 구조체는 원본 정적 초기화 0x710265c230을 먼저 실행해 채움.
- 실행: 0x710265df40 / 0x710265fd48(비트 4 꺼짐·켜짐) / 0x7102665ee4를 AP 22종 × (메인만, 서브만)으로 실행.
- 결과: 출력 731개 값 모두 재구현과 차이 0 (`analysis/player/gear_emu_result.txt` 끝줄 `최대 절대 차 0.000e+00`).
- 스텁: PLT의 logf/expf/powf/sqrtf는 파이썬 f32 계산으로 대체, 그 밖의 PLT는 x0=0 반환. 열거 표는 합성(실제 표 내용·순서는 초기화 함수 0x710266e4dc, 0x71024cdd94를 실행하지 않음).
- 검증하지 않은 범위: AP 집계 0x710265ca78(조건부 가산·특수 능력), MainWeaponSetting 덮어쓰기 분기(+0x148 null로만 실행), `$parent` 체인 탐색, +0x180 대체 모드.

## 9. 미확정

| 항목 | 이유 / 필요한 근거 |
|---|---|
| 기어 계산 호출 시점 | **해소 [판독]**(2026-10-03 5차): 매 프레임 AP 변화 검사 → 변하면 재계산(§3). 남은 것: 조건 없이 재계산하는 세 호출자(`0x71024719d4`, `0x71024901c4`, `0x7102491b68`)의 게임 상황 [미확정] |
| AP 집계 세부(StartAllUp/EndAllUp/ComeBack 등 조건부 AP) | **해소 [판독]+[실행]**(2026-10-03 r8): §5.4/§10. 기본·조건부 AP 구분, 장비3개 집계·enum·모든 AP 가산 및 종료시 초기화 원본 대조 |
| 특수 능력 104의 게임 내 이름 | **해소 [데이터]**: "징어닌자"(Ninja Squid) — §5.1 |
| +0x10c(ShotK)·+0x110~+0x118의 소비처 | **부분 해소 [판독]**: +0x110/+0x114/+0x118은 PlayerStepPaint `0x710268b3b8`이 읽는다(combat 문서). +0x10c(ShotK) reader는 [미확정] — 다음: PlayerParam 포인터(본체+0xa658)를 받는 함수에서 `ldr s?, [x?, #0x10c]` |
| ActionSpecUp_Squid 두 값의 체감 의미 | **해소 [판독+실행(구간)]**(2026-10-03 정정): +0x140은 롤·벽 점프 발사 속도에 정수 n(10 상한)만큼 반복 곱한다. n은 공통 발사 꼬리에서 +1, 입력 경로에서 형태 이탈 또는 strict 90프레임 초과 시 0 — [movement_physics.md §6.8.1](movement_physics.md). +0x13c는 상태기계 H(0x8f WallJumpCharge)의 보간 상한 |

2026-10-03 보완: 특수 능력 104의 AP 비율 0.8 보정(§5.1) 외에, 목표 오징어 속도에서 `0x710266c6e4`가 0.9를 반환한다. 인자 bit0이 켜져 있으면 1을 반환한다. 원본 1088건 비트 대조 **[실행]** — [movement_physics.md §6.1.1](movement_physics.md). 표시 이름은 5차에서 해소했다(§5.1).

2026-10-03 5차 정정(§5.2·§8): "파이썬 `math.log/exp` + f32 반올림이 원본과 비트 일치"는 에뮬에서 logf/expf를 파이썬으로 대신 계산한 결과였다(§8 스텁 기록과 같음). 원본 SDK 모듈(`extracted/exefs/sdk.img`의 logf·expf)을 직접 실행해 §4.3 표 15행 × AP 0..57 × 특수 능력 비트(0/1) = 1740건을 대조하면 **1건이 1ulp 다르다**: OpInk_MoveVel_Shot(0.012/0.033/0.042) AP 50, SDK 0x3d2a7108 / 파이썬 0x3d2a7107 **[실행]**(`web/tools/r5_player_libm_emu.py`). 웹에서 비트 일치가 필요하면 SDK logf/expf 알고리즘을 옮겨야 한다.


## 10. 검증 코드·실행 결과·기대값 (r8 신규)

`web/tools/r8_player_conditional_ap_emu.py` → `analysis/completion/r8/player_conditional_ap_emu.json`: 장비 collector900건, 전체 함수 조건부 AP1700건, dirty 재집계240건, 씬 문자열9건. **출력 AP s32 및 반환값 불일치0**, null call0, 자동 메모리 페이지0. 실제 enum 초기화+실제 전역 상수+실제 함수 명령을 실행했다. mutex Lock/Unlock은 enum 초기화에서 각각2회 스텁; 게임 프레임·장비·액터·score 링·모드 byte는 명시된 합성 입력이며 네트워크/렌더링은 실행하지 않았다.

정상/반대 조건과 1799/1800 프레임, count30/50/51, 음수 프레임, INT_MIN sentinel, 여러 보너스 동시 적용, 조건 종료 후 보너스0, dirty 재집계 저장과 dirty 해제를 검사했다. EndAllUp count30은 계수1로 AP24; count50은 계수 f32(1/21)에 AP24를 곱하고 정수 절삭한다. count가 음수여도 FMIN 상한1 때문에24를 넘지 않는다.

## 11. 미확정 사항과 다음 근거 (r8)

§9 조건부 AP 집계 항목은 이번 새 원본 판독·실행으로 해소한다. +0x10c ShotK reader는 미확정으로 유지한다(다음: 실제 PlayerParam을 사용하는 본체 메인 계산의 메모리 읽기 추적). B+0xe54/P+0x178의 시작 시각 writer·특수 씬의 대체 계산 객체 수명 및 MinorityUp 실제 액터 목록/게이지 소비는 별도 동작이며 이번 합성 AP 시험이 검증하지 않는다. 기어 계산 호출자 세 함수의 게임 상황과 SDK 수학 전체 한계는 기존 §9를 유지한다. 웹은 기본AP 캐시·tick별 보너스 배열·특수비트를 분리하고, §5.4 순서와 FMIN/정수 절삭을 보존한 뒤 AP 변화 시 §3의 캐시 재계산을 실행해야 한다. 코드 변경은 하지 않았다.
