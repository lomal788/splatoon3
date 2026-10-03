# 슈터 조준 흔들림과 발사 타이밍

목차: [camera_feel.md](camera_feel.md). 공통 수학(난수·bias 곡선·사인표)은 [camera_feel.md §4](camera_feel.md#4-공통-수학-도구).

## 1. 기능 개요

슈터는 ZR을 누르고 있는 동안 `RepeatFrame`마다 탄을 냅니다. 탄 방향은 조준 방향을 **월드 Y축으로 무작위 각도만큼 돌린** 것입니다(수평 분산만 있음, 상하 분산 없음). 각도 크기는 서 있을 때 `Stand_DegSwerve`, 점프 직후 `Jump_DegSwerve`이고, 분포의 모양은 "bias" 값이 정합니다. bias가 작으면 거의 정중앙, 0.5면 균등, 0.5보다 크면 가장자리 쪽입니다. 연사할수록 bias가 커져 탄이 퍼지고, 손을 떼면 다시 줄어듭니다.

## 2. 분석 대상

| 항목 | 값 |
|---|---|
| 원본 | Splatoon 3 v0, main NSO (build_id 19fe149d…) |
| 클래스 | `spl::PlayerInkActionShooter` vtable 0x71056376a0 (57슬롯), `spl::WeaponShooter` vtable 0x7105652468 (75슬롯) |
| 파라미터 | `spl::WeaponShooterParam` (팩토리 0x7102811104, 방문 0x7102811224), 기어 `spl::PlayerGearSkillParam_ActionSpecUp_ReduceJumpSwerveRate` |
| 디컴파일 | `analysis/decomp/camera/batch1.c` |

## 3. 진입점과 호출 흐름

```
(플레이어 잉크 액션 갱신, 호출자 [player] 범위)
 └ 0x7102583008  PlayerInkActionShooter 발사 프레임 처리 (param_5 = 입력 바이트 [0]=트리거, [1]=차단, [2]=?)
     ├ +0xa4 카운터 감소, 0x7102584b3c (보조 갱신)
     ├ 트리거 && !차단:
     │   ├ 0x7102551530 연사 타이머(this+0x68, RepeatFrame)        → 발사 여부
     │   ├ (TripleShot 등) 0x7102580354 / TripleShotSpanFrame 처리
     │   ├ 발사 시: 0x7102580f98 흔들림각·점프bias
     │   │          난수 시드 → bias 곡선 → Y축 회전 (0x71025839a8~0x7102583c64)
     │   │          탄 생성 0x7102581ccc(일반) / 0x71025817c8(this+0x40 있을 때)
     │   │          +0x98 발사 수 ++, +0x91 패턴 인덱스 ++
     │   │          bias += Stand_DegBiasKf, min(Stand_DegBiasMax)       (0x71025843e0)
     │   │          InkRecoverStop → 0x7102353718 (잉크 회복 정지)
     │   └ 비발사: 0x71025856c8(this,0)
     ├ 아니면: 0x710258295c(this,0,..) 대기 상태 갱신
     └ 끝 (매 프레임): bias 감쇠/하한, 점프 카운터 감소           (0x71025830d0~0x71025835c4)
 vt40 0x7102580c4c  점프 시작 → 점프 카운터 = Jump_DegBiasEndFrame
 vt36 0x7102582e3c  리셋 (타이머·bias·점프 카운터 0, +0x91 무작위 초기화)
 vt49 0x71025872a4  PreDelayFrame_HumanShot 반환
 vt50 0x71025874b0  PreDelayFrame_SquidShot − SquidShotShorteningFrame 반환
```

vt40이 실제로 "점프 시작"에서 불리는지는 [미확정]입니다(필드 이름 Jump_*와 대입값으로 본 [추정]). 0x7102583008을 부르는 상위 경로는 플레이어 슬롯 19 0x7102483134 → 0x7102486a40입니다([../weapon/shooter_bullet.md](../weapon/shooter_bullet.md) §3.5). 2026-10-03 시도 [r5 camweapon]: 플레이어 코드 0x7102300000~0x7102700000의 `ldr x8,[x8,#0x140]; blr` 가상 호출 22곳을 전수 확인했으나 대부분 본체+0xa670(GrindRail) 대상이고, 잉크액션 포인터(본체+0x588/+0x678)로 vt+0x140을 부르는 곳은 없었습니다(`analysis/r5_camweapon/scan_vt140.py`, `scan_vt140b.py`). 다음 근거: 점프 상태 진입(0x7102475a54 부근)에서 잉크액션 목록을 도는 공용 호출, 또는 PlayerInkAction 기반 클래스 vt+0x140의 다른 호출 형태([player]에 요청). 2026-10-03 6차 시도 [r6 camweapon]: 범위를 0x7102200000~0x7102a00000으로 넓혀 `ldr xN,[xM,#0x140]; blr xN`을 다시 스캔했습니다. GrindRail이 아닌 후보는 0x710248680c(플레이어 슬롯19 0x7102483134 안) 한 곳이었습니다. 이곳은 대상이 [sp+0x158] = x26(0x71024839b0 저장) 객체이고 반환값을 bool로 씁니다(`tbz w0`). vt40 0x7102580c4c는 +0x88에 카운터를 쓰고 반환값을 정하지 않는 함수라(0x7102580e08 저장 → 0x7102580e24 ret), 이 호출과 맞지 않습니다 [판독]. vt40의 vtable 참조는 PlayerInkActionShooter vtable 0x71056376a0 슬롯40 한 곳뿐이고, 썽크도 없습니다. 호출자는 여전히 [미확정]입니다.

### 3.1 실제 점프 시작 호출사슬 — 8차(2026-10-03) [판독]+[실행]

`0x71024a8000` 점프 시작은 `0x71024a80b0..0x71024a80c4`에서 현재 잉크액션 **보조 인터페이스** `[B+0x588]`의 `vt+0x40`을 호출합니다. 슈터 객체 I의 +0x30 인터페이스 VT는 **0x7105637898**이고 +0x40은 **0x7102580e60**입니다. 이 썽크가 I+0x30에서 0x30을 빼고 `0x7102580c50`으로 분기합니다. Primary VT 슬롯40 `0x7102580c4c`도 같은 본문으로 분기합니다. 따라서 점프 시작에서 I+0x88에 Jump_DegBiasEndFrame을 넣는 경로가 확정되었습니다.

**2026-10-03 정정**: §3의 5·6차 기록은 primary VT+0x140만 스캔하고 "썽크도 없음"으로 적었습니다. 보조 VT+0x40의 `2580e60`을 누락한 것이 원인입니다. 이전 실패 기록은 남기되 호출자 미확정 결론은 이 절에서 해소합니다. 기존 `camera/batch1.c`의 factory/소멸자 VT 쓰기와 `move/move_jumpstart.c`를 재사용하고, 새 연결을 실제 호출사슬로 실행했습니다.

`web/tools/r8_camweapon_jump_dokan_emu.py`가 원본 jump dispatch→실제 VT→썽크→카운터 본문을 EndFrame 0..127 **128 PASS**로 확인했습니다. 정확히 I+0x30으로 들어와 I로 되돌아가는 포인터도 검사했습니다. 합성된 세대 유효 파라미터·RTTI true 경계를 사용하며 전체 점프 프레임·기어·무기 변경은 실행하지 않습니다. 증거 `analysis/completion/r8/camera_jump_dokan_emu.json`.

## 4. 구조체·필드

### 4.1 `spl::PlayerInkActionShooter` (기준 객체 = 이 컴포넌트 this) [판독]

| 오프셋 | 타입 | 의미 | writer | reader |
|---|---|---|---|---|
| +0x38 | ptr | WeaponShooter | 생성 | 전부 |
| +0x40 | ptr | 대체 탄 생성 경로 선택 | — | 0x7102583c80 |
| +0x48 / +0x58 | 핸들 | WeaponParam / VariableWeaponParam (Variable 모드면 +0x58) | 생성 | 필드 읽기 전부 |
| +0x68 | f32 | 연사 타이머 위상 phase | 0x7102551530, 발사 +1.0(Triple), 0x710258295c | 0x7102551530 |
| +0x6c | f32 | 다음 발사까지 남은 프레임 rem | 0x7102551530, 0x710258295c | 끝 감쇠 조건 |
| +0x70~+0x84 | s32×5, u8 | 타이머 카운터들, 플래그 | 0x7102551530 | 〃 |
| +0x88 | s32 | 점프 흔들림 카운터 | vt40(=EndFrame), 끝(감소), 리셋(0) | 0x7102580f98 |
| +0x8c | f32 | 누적 bias (서기) | 발사 후 +Kf, 끝 −Decrease·하한, 리셋 0 | 발사 |
| +0x90 | u8 | 발사 중 플래그 | 0x7102583008 | — |
| +0x91 | u8 | 발사 패턴 인덱스 (리셋 때 난수 바이트) | 발사 ++ / 리셋 | 탄 생성 인자 |
| +0x98 | s32 | 발사 수 | 발사 ++ | Variable 판정 |
| +0xac | s32 | Variable 관련 카운터 | 0x7102583008 | 파라미터 선택 |

### 4.2 `spl::WeaponShooter` 파라미터 멤버 (0x710289aa7c) [판독]

`+0x470 WeaponParam, +0x480 MoveParam, +0x490 CollisionParam, +0x4a0 PaintParam, +0x4b0 SplashSpawnParam, +0x4c0 SplashPaintParam, +0x4d0 DamageParam, +0x4e0 WallDropMoveParam, +0x4f0 WallDropCollisionPaintParam, +0x500 spl__SpawnBulletAdditionMovePlayerParam, +0x510 MainEffectiveRangeUpParam, +0x520 spl__PlayerGearSkillParam_ActionSpecUp_ReduceJumpSwerveRate, +0x530 DiffusionParam, +0x540 TailLength, +0x550 DiffusionTailLength, +0x560~ Variable*`.

### 4.3 `spl::WeaponShooterParam` 흔들림 관련 필드 (기준 = 파라미터 객체) [판독]

| 오프셋 | 플래그 | 필드 | 기본값 | 스플래시슈터 |
|---|---|---|---|---|
| +0x3c | 0x92 | Jump_DegBiasDecreaseStartFrame s32 | 0 | 25 |
| +0x40 | 0x93 | Jump_DegBiasEndFrame s32 | 45 | 70 |
| +0x44 | 0x91 | Jump_DegBiasMax f32 | 0 | 0.4 |
| +0x48 | 0x90 | Jump_DegSwerve f32 | 0 | 12 |
| +0x58 | 0x97 | PreDelayFrame_HumanShot s32 | 0 | 0 |
| +0x5c | 0x98 | PreDelayFrame_SquidShot s32 | 4 | 4 |
| +0x60 | 0x8a | RepeatFrame s32 | 6 | 6 |
| +0x68 | 0x99 | SquidShotShorteningFrame s32 | 0 | 1 |
| +0x6c | 0x8f | Stand_DegBiasDecrease f32 | 0.01 | 0.015 |
| +0x70 | 0x8e | Stand_DegBiasKf f32 | 0.02 | 0.01 |
| +0x74 | 0x8d | Stand_DegBiasMax f32 | 0.25 | 0.25 (기본) |
| +0x78 | 0x8c | Stand_DegBiasMin f32 | 0.1 | 0.01 |
| +0x7c | 0x8b | Stand_DegSwerve f32 | 0 | 6 |
| +0x80 | 0x9c | TripleShotSpanFrame s32 | 0 | 0 |

필드 값은 "설정됨 플래그가 켜진 가장 가까운 부모"의 값입니다([bullet] SHARED). 35개 표 전체는 `analysis/camera/shooter_swerve_table.md` (`camera_swerve.py table`).

### 4.4 기어 `ReduceJumpSwerveRate` [판독]

`+0x30 High 1.0, +0x34 Low 0.0, +0x38 Mid 0.75` (팩토리 0x710236efa4, 0x7102899e18 안의 기본 객체 0x71058d6318도 같은 값). 데이터는 7개 표가 `Mid`만 덮어씁니다.

## 5. 상태 전이와 수명

| 사건 | 처리 | 근거 |
|---|---|---|
| 장착/리셋 (vt36 0x7102582e3c) | phase·rem·카운터 0, bias 0, 점프 카운터 0, +0x90=0, +0x91=난수 바이트(플레이어 번호×100 섞은 시드), 0x710258295c(this,1,0) | [판독] |
| 매 프레임 끝 | bias = max(bias − (조건 시 Decrease), Min). 조건 = |rem−1| ≤ 0.001 **그리고** 트리거 안 누름 | [판독] |
| 매 프레임 끝 | 점프 카운터 = max(카운터 − (Q ? 1 : 2), 0). Q = `본체(+0x2c0→+0x108)+0xc0 ≥ *(0x71058bbb78)+0xa8` = **공중 프레임 ≥ 4** → 공중이면 1씩, 접지면 2씩 감소 | [판독], 의미 [추정 — 강함] (아래) |
| 발사 | 흔들림 계산 후 bias += Kf, min(Max) | [판독] |
| 점프 (vt40) | 카운터 = Jump_DegBiasEndFrame | [판독] |

Q 해소 근거 [판독]: 비교 상수 `*(0x71058bbb78)+0xa8` = 0x71058bbc20 = **4**(정적 초기화 에뮬 값, [player] `player_initemu`). 본체+0xc0은 [player]가 "공중 프레임"(airFrames)으로 해석한 0x710245f964의 `*param_3`와 같은 변수입니다 — 호출부 0x7102475a54가 `param_1(=본체+0xa5fc) − 0xa53c` = 본체+0xc0을 넘김. 같은 변수·같은 상수 4를 카메라(오징어 블렌드 비율 0.025/0.001)도 씁니다([player_camera.md](player_camera.md) §6.2). 그래서 점프 흔들림은 **공중에 있는 동안 1프레임에 1씩, 착지하면 2씩** 줄어듭니다(착지 후 빨리 회복). 웹 구현: `jumpFrames -= (airFrames >= 4) ? 1 : 2`.

리셋 직후 bias 0은 첫 프레임 끝에서 Min으로 올라갑니다. 첫 발이 리셋과 같은 프레임이면 bias 0이 쓰일 수 있습니다(b<0.001 분기 → 거의 항상 0도) [판독 결과의 추론].

## 6. 계산식

### 6.1 흔들림 각과 점프 bias (0x7102580f98) [판독]

```
swerveStand = W.getSwerve(isJump=false)                 // 0x7102899e18 → Stand_DegSwerve
swerveJump  = W.getSwerve(isJump=true)                  // Jump + (Stand − Jump) * gearRate
if jumpCnt < 1:
    swerve = swerveStand ; jumpBias = 0
else:
    t = min( float(jumpCnt) / float(EndFrame − DecreaseStartFrame), 1 )
    swerve   = swerveStand + t * (swerveJump − swerveStand)
    jumpBias = Stand_DegBiasMin + t * (Jump_DegBiasMax − Stand_DegBiasMin)
```

- 스플래시슈터: 점프 직후 카운터 70 → t=70/45→1, 25프레임 동안 12°·bias 0.4 유지, 이후 45프레임 동안 선형으로 6°·bias 0으로.
- `gearRate` = 기어 효과 함수 0x710266b660(ReduceJumpSwerveRate). 상수 57.0과 logf/expf를 쓰는 공용 능력 공식이며 [paint]가 SpecialIncreaseUp(0x7102663808)으로 판독한 식과 같은 형태입니다: `GP=min(57,주+부 포인트), x=clamp01(GP(3.3−0.027GP)/100), t=(Mid−Low)/(High−Low), f=bias(x,t), rate=Low+(High−Low)f`. 0x710266b660 자체는 상수만 확인했습니다 [판독-부분]. 기어 0이면 rate=Low=0 → 점프 흔들림 그대로.
- 0x7102899e18의 세 번째 인자(isVariable)가 참이면 WeaponParam 대신 VariableWeaponParam(+0x560)을 씁니다.

### 6.2 발사 방향 (0x71025839a8~0x7102583c64) [판독]

```
rad = debugFlag(*(0x71058bbb78)+0x15) ? 0 : swerve * 0.017453292   // 플래그 = 0 고정 [판독], 아래
rng = seedRandom(frame, a, b, c, d)          // camera_feel.md §4.1
r   = rng.getF32()
u   = (r + r) + (−1.0)                       // [-1, 1)
b   = (bias > jumpBias) ? bias : jumpBias    // fcsel gt
u'  = biasCurve(u, b)                        // camera_feel.md §4.2
ang = rad * u'
aim = 0x71024aff7c(...)                       // 조준 방향 벡터 (s0..s2 반환)
dir = rotateY(aim, ang):  x' = x·cos + z·sin,  y' = y,  z' = z·cos − x·sin   (사인표)
→ 탄 생성(dir)
```

- 회전 축은 월드 (0,1,0) 고정입니다. 조준이 위/아래를 향해도 수평면에서 돕니다 [판독].
- 디버그 플래그 — 해소(2026-10-03) [판독]: `0x71058bbb78` 블록은 정적 초기화 0x7102455db0이 채우고, `0x7102455f4c strh wzr,[x8,#0x14]`가 +0x14·+0x15를 0으로 둡니다. GOT 0x7105795dd8 경유 참조 223곳에서 +0x15 저장은 0건(`analysis/r5_camweapon/scan_got_direct.py`), 직접 참조는 정적 초기화와 이동 메인 읽기뿐입니다. 따라서 v0 제품판에서 흔들림 각은 항상 `swerve × π/180`입니다.
- 시드 입력의 정체(2026-10-03) [판독, network 재사용]: F = GameFrame 싱글턴 +0x148, a..d = 대전 설정 RandomSeed0..3([camera_feel.md](camera_feel.md) §4.1). 사격장 실제 값은 [미확정].
- 기대 분포: |u'| = |u|^e, e = −log2 b → E|각| = swerve/(e+1). bias 0.01이면 e=6.64(대부분 중앙), 0.25면 e=2, 0.5면 균등.
- 정정·추가(2026-10-03): aim 벡터 식·Shooter 파라미터 기본값은 [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md) §5.5 [판독]/기존 [실행]으로 해소. 이전 조사 범위 기록: `aim`은 카메라 시선(+0x1a4) 또는 플레이어 +0x54c를 바탕으로 0x7102551fe0이 만듭니다. 이 계산은 [bullet]과 겹치므로 여기서 더 들어가지 않았습니다 [미확정].

### 6.3 연사 타이머 (0x7102551530, 구조체 기준 = PlayerInkActionShooter+0x68) [판독]

```
c0 = max(c0,1)−1; c1 = max(c1,1)−1; c2 = max(c2,1)−1   // +0xc, +0x10, +0x14
if c0 > 0: return false
if count(+0x8) >= limit(+0x18): return false
if c1 == 0 or (flag(+0x1c) and phase < 1):
    inc = 1/RepeatFrame; phase += inc; rem = max((1−phase)/inc, 0)
if phase < 1 and |phase−1| <= 1e-5: phase = 1
if phase < 1: return false
if c1 != 0 and flag: return false
phase −= 1; return true
```

- 대기 상태(트리거 안 누름, 0x710258295c): `phase = min(phase + inc, 1 − inc)`, `rem = (1−phase)/inc` → 대기가 길면 rem=1. 다음 프레임에 누르면 phase가 1에 닿아 **바로 발사**합니다.
- `rem == 1`(±0.001)이 bias 감쇠 조건이므로, 연사를 멈춘 뒤 타이머가 대기 상태로 돌아와야 bias가 줄기 시작합니다.

### 6.4 PreDelay [판독 — 값·소비처]

정정(2026-10-03): 아래 "상태 기계 미판독" 기록은 기존 weapon 구현 분석의 원본 근거를 본문에 반영하지 않은 상태였습니다. 실제 게이트는 H=`B+4d4≥2+PreDelay_Human` 및 `B+a90≥6+(PreDelay_Squid−Shortening)`이고, PostDelay=4는 자세 타이머/오징어 잠금에 사용됩니다. 원본 주소·필드와 기존 실행 범위는 [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md) §3.5(검증 기록 [../weapon/solo_shooter.md](../weapon/solo_shooter.md)). 입력 writer와 정확 상태 집합은 별개 [미확정].

| 함수 | 반환 | 스플래시슈터 |
|---|---|---|
| vt49 0x71025872a4 | PreDelayFrame_HumanShot | 0 |
| vt50 0x71025874b0 | PreDelayFrame_SquidShot − SquidShotShorteningFrame | 4−1 = 3 |

소비처 [판독]: vt49 값은 `B+0x4d4 ≥ 2 + PreDelay_Human`, vt50 값은 `B+0xa90 ≥ 6 + (PreDelay_Squid − SquidShotShortening)` 게이트에 쓰입니다(0x7102483134 안). PostDelayFrame(4)은 자세 타이머 0x71024b28b0과 0x7102583008의 ac4/ab8 갱신에 쓰입니다([../weapon/shooter_bullet.md](../weapon/shooter_bullet.md) §3.5). 정정(2026-10-03): 이전 "상태 기계는 읽지 않았습니다 / PostDelay 용도 [미확정]"을 해소로 바꿉니다. 이름 해석("오징어에서 ZR → 변신 후 첫 발")은 동작 명세에 필요하지 않습니다.

## 7. 표현·에셋 연결

- 슈터 발사 이펙트·사운드·진동은 ELink/SLink(무기 사용자 이름 `WeaponShooterNormal`)로 나옵니다. 슈터 ELink 에셋에는 진동/쉐이크 파라미터가 없습니다([shake_rumble.md §4](shake_rumble.md#4-elink-연결)).
- 흔들림은 탄 방향만 바꿉니다. 카메라나 조준선(ShotGuideFrame)은 흔들림 각을 반영하지 않습니다 [판독: 회전 결과는 탄 생성 인자로만 전달].

## 8. 다른 기능과의 상호작용

- 네트워크: 시드가 프레임+세션 값뿐이므로, 같은 프레임 번호를 쓰면 원격 클라이언트도 같은 각을 재현할 수 있습니다. 실제로 원격 탄을 어떻게 복제하는지는 [network] 범위(`PlayerNetEvent::Bullet*`)입니다.
- 오징어→인간 발사: PreDelay_Squid만큼 늦게 첫 발. 점프 카운터는 점프 이벤트에만 반응합니다.
- Variable 무기(`Shooter_Flash` 등 VariableWeaponParam 보유): 0x710289a8b4가 참이고 +0x98≥1, +0xac==0이면 Variable 파라미터 사용.
- **블래스터** [판독 — 구조, 데이터 — 값]: 같은 PlayerInkActionShooter 경로를 탑니다. 근거: (1) 플레이어 컴포넌트 76종에 블래스터 전용 잉크액션이 없음(`analysis/player/player_components.tsv`), (2) 넷 상태의 메인 잉크액션 열거(InkActionNone, Shooter, Roller, Charger, Spinner, Slosher, Brush, Maneuver, Shelter, Stringer, Saber, SpChariot, Gachihoko)에 블래스터가 없음([network] 04 §4.3), (3) `spl::WeaponBlaster`(vtable 0x710564f4b0)는 `spl::WeaponShooter`와 생성 함수 0x710286760c를 공유하고, 파라미터 초기화 슬롯 8(0x710286801c)이 슈터 것(0x710289aa7c)을 먼저 부른 뒤 Blast 등 추가 파라미터만 더함 → WeaponParam(+0x470) 배치가 같아 0x7102899e18/0x7102580f98이 그대로 동작. 데이터상 블래스터는 `Stand_DegSwerve 0`, `Stand_DegBiasMin 0`이라 서서 쏘면 bias 0 → `b < 0.001` 분기로 **항상 정면**, 점프 직후에는 `Jump_DegSwerve 8~10`, `Jump_DegBiasMax 0.5`(= 균등 분포, 평균 |각| = DegSwerve/2)로 퍼지고 DecreaseStart 25~40프레임 뒤부터 EndFrame 70까지 줄어듭니다(`analysis/camera/shooter_swerve_table.md`). 0x7102583008 안에 블래스터 전용 분기가 있는지는 무기 종류 판별 호출을 전수 확인하지 않았습니다 [미확정-부분].
- **블래스터 외 무기의 흔들림 경로** — 2026-10-02 [camrest]:
  - 흔들림 필드(Stand_/Jump_DegSwerve·DegBias*)를 가진 파라미터 형은 `WeaponShooterParam`·`WeaponManeuverParam`·`WeaponSpinnerParam`(셋 다 같은 오프셋 +0x3c~+0x7c), `WeaponSpChariotParam`(Stand_*만, +0xac~+0xbc), `WeaponVariableShotParam`(+0x34~+0x68, 그리고 `PitchDegSwerve` +0x50·`PitchDegBias` +0x4c — **상하 흔들림 필드가 있는 유일한 형**)입니다 [데이터: `analysis/param_reflect/*.json`].
  - 연사 타이머 0x7102551530 호출자: 슈터(0x7102583008, 0x7102584fc8), 매뉴버=듀얼(0x710254d018, 0x710254e3bc), SpChariot(0x710259b7bc 두 곳), 0x710259eca4, 0x71025d6a4c, 0x7102604048 [판독: bl_callers]. 흔들림 각 함수 0x7102580f98(슈터 전용, WeaponShooter 0x7102899e18 호출)은 슈터 두 경로(0x7102583008, 0x7102585bd8)만 부릅니다 [판독].
  - **SpChariot(스페셜 크랩탱크)** [판독, `analysis/decomp/camrest/swerve_others.c` 0x710259b7bc]: 같은 시드 식(F + (a+b)·0x89, 0x1c1/0x233/0x3df, 플레이어 번호 없음), `GetSystemTick` 미사용 흔적, `u = 2r−1`, bias = this+0xa8(누적 bias), bias 곡선(logf/expf, b<0.001·|u|<0.001 처리 동일), 각 = SpChariotParam `Stand_DegSwerve`(+0xbc)·π/180, 디버그 플래그 `0x71058bbb8d`면 0, **월드 Y축 회전**(사인표) — 슈터와 같은 계산이고 점프 흔들림만 없습니다. 리셋 0x710259ad20은 슈터 리셋과 같은 방식으로 +0x91 패턴 바이트를 (플레이어 번호×100 섞은 시드)로 정합니다 [판독].
  - **매뉴버(듀얼)** [판독-부분, asm 0x710254d6dc~0x710254d9a0]: 같은 시드 상수·bias 곡선(logf/expf, −1.442695)·각도 ×0.017453292·조준 0x71024aff7c 뒤 회전 구조이고, 누적 bias가 this+0x88(슈터는 +0x8c)이며 어떤 조건에서 `this+0x88 = Stand_DegBiasMin(+0x78)`으로 되돌립니다(0x710254d6dc~0x710254d6ec, 조건 의미 [미확정] — 슬라이드 후로 추정). 흔들림 각(sp+0x28 값)의 출처와 점프 흔들림 유무는 읽지 않았습니다 [미확정].
  - **스피너** [미확정]: 리셋(0x71025c16c8)은 같은 패턴 바이트 시드(+0x79)를 쓰고, 시드 상수를 가진 0x71025c0568·0x71025c154c가 발사 흔들림 후보입니다. 읽지 않았습니다.
  - **VariableShot**(`Shooter_Flash` 등 VariableWeaponParam 무기)의 PitchDegSwerve 소비처 [미확정]: 슈터 경로(0x7102899e18의 isVariable 인자)는 Stand/Jump만 읽습니다.
- **WeaponShooterDiffusionParam**(Hero 모드 `WeaponShooterMissionLv3`만 사용) — 탄 생성 0x7102897640 [판독-부분]:
  - 필드(리플렉션 0x710280fd38, 기준 = Diffusion 파라미터 객체): `DefaultDegree`(목록, +0x30 컨테이너), `DegreeResetFrame` s32 +0x68 (기본 60), `AdditionDegreePerFrame` f32 +0x58 (2.0), `CenterDegree` f32 +0x5c (20.0), `CenterDegreeBias` f32 +0x60 (0.3), `CenterDegreeSwerve` f32 +0x64 (2.0), `SpawnSpeed` f32 +0x6c (2.2).
  - 무기(WeaponShooter) 상태: +0x5d0 마지막 발사 프레임, +0x5d4 누적 회전각, +0x5d8 목록 인덱스(s8), +0x5d9 회전 방향, +0x5da 플래그.
  - 흐름: 먼저 일반 탄 1발을 같은 정보로 생성. 그 뒤 GameFrame(+0x148) f로 `f − last ≥ DegreeResetFrame`이거나 처음이면 last=f, 누적각=0, 인덱스 = sead::Random(f) 정수 % 목록 길이. 인덱스로 `DefaultDegree[idx]`를 읽고 idx++, 누적각 += (방향 ? +1 : −1)·AdditionDegreePerFrame·(f − last). 조준 방향을 축 A(0x71012500d4가 조준과 고정 벡터 `*0x7105791978`로 만든 축) 둘레로 **−CenterDegree** 기울이고(반각 쿼터니언), 그 벡터를 조준축 둘레로 **(누적각 + DefaultDegree[idx])°** 돌립니다 → 조준 둘레 반각 CenterDegree 원뿔 위를 프레임마다 도는 방향. 그 결과를 조준의 수평 직교축(aim.z, 0, −aim.x) 둘레 ±1° 회전으로 만든 두 경계 벡터와 내적해 음수면 그 성분을 빼고 재정규화(수직 방향 퍼짐을 약 ±1°로 제한)한 뒤 두 번째 탄을 SpawnSpeed로 생성합니다.
  - **CenterDegreeBias·CenterDegreeSwerve는 v0 코드에서 결과에 영향이 없습니다** — 2026-10-02 [camrest], 전체 분석 재디컴파일 `analysis/decomp/camrest/cam_main_full.c`(0x7102897640 = 6298~7362행)와 asm(0x7102898700~0x7102898930) 판독 [판독]:
    - CenterDegreeBias(+0x60, 설정 플래그 +0x75): `|b − 0.5| > 0.001`이면 프레임 시드로 r를 뽑아 u = 2r−1, `e = ln|u|·ln b·(−1.442695)`를 계산하고, e가 범위(≤ 88, ≥ −103) **밖일 때만** `expf`(0x7103e9be20)를 부릅니다. 0x7102898824의 `bl expf` 다음 명령은 s0을 읽지 않고(x8 재적재 → 0x7102898834 `fcvtzs w19, s9`), 범위 안이면 expf 호출조차 건너뜁니다. 시드 상태는 지역 변수라 다른 난수에도 영향이 없습니다. 즉 bias 곡선 값은 계산되다 버려집니다 [판독]. 정정(2026-10-03): 이전 판의 "libm 호출의 부작용 때문에 호출만 남은 형태 [추정]"은 원인 해석이라 명세에서 뺍니다. 웹은 이 계산 전체를 생략해도 결과·난수열이 같습니다(Diffusion은 사격장 대상 무기가 아님).
    - CenterDegreeSwerve(+0x64, 플래그 +0x74): 0x7102898838·0x71028988dc에서 플래그 +0x74로 **부모 체인만 걷고**, 함수 전체 asm에서 `[x, #0x64]` 읽기가 0건입니다(같은 함수의 파라미터 읽기는 +0x58 두 번, +0x5c, +0x60, +0x68, +0x6c뿐) [판독: asm 전수].
    - 따라서 웹 구현은 두 필드를 무시해도 원본과 같습니다. 난수 소비도 없으므로 생략해도 다른 난수열이 어긋나지 않습니다 [판독].
  - 대전 무기에는 쓰이지 않으므로 웹 1차 구현에서는 생략 가능합니다.

## 9. 웹 포팅

### 9.1 모듈

| 모듈 | 책임 |
|---|---|
| `SeadRandom` | 4워드 xorshift128, `initFromShotSeed(frame,a,b,c,d)`, `nextF32()` |
| `SeadMath` | 사인표(256×4 f32, main.img에서 추출해 JSON으로 동봉), `biasCurve` |
| `ShooterSwerve` | 상태 {bias, jumpCnt}, `onJump()`, `computeShotDir(aim, frame, seeds)`, `endFrame(trigger, timerIdle, q)` |
| `RepeatTimer` | 6.3 그대로 |
| 파라미터 로더 | GameParameterTable `$parent` 체인 + 기본값 (`camera_swerve.py shooter_param`과 같은 규칙) |

### 9.2 이름 대응 (원본 확인 이름 / 웹 권장 이름)

| 원본 | 웹 권장 |
|---|---|
| PlayerInkActionShooter+0x8c | `swerve.standBias` |
| +0x88 | `swerve.jumpFrames` |
| +0x68/+0x6c | `timer.phase` / `timer.framesToReady` |
| Stand_DegSwerve 등 | 원본 필드명 그대로 |
| 0x7102580f98 | `getSwerveAndJumpBias()` |
| 0x7102551530 | `RepeatTimer.update(repeatFrame)` |

### 9.3 프레임 순서 (원본과 같게 유지)

```
onFrame(input):
  if input.trigger && !input.blocked:
      if timer.update(P.RepeatFrame):
          {swerve, jumpBias} = getSwerveAndJumpBias()
          dir = rotateY(aim, rad(swerve) * biasCurve(2r−1, max(standBias, jumpBias)))
          spawnBullet(dir)
          standBias = min(standBias + P.Stand_DegBiasKf, P.Stand_DegBiasMax)
  else:
      timer.idle()
  if |timer.framesToReady − 1| <= 0.001 && !input.trigger: standBias −= P.Stand_DegBiasDecrease
  standBias = max(standBias, P.Stand_DegBiasMin)
  jumpFrames = max(jumpFrames − (Q ? 1 : 2), 0)
```

- 모든 f32 연산은 `Math.fround`. 탄 이동 코드처럼 이 구간에도 FMA가 없어 비트 일치를 노릴 수 있습니다(asm 0x7102583a9c~0x7102583c64에 fmadd 없음 [판독]).
- 서버/클라이언트 공유: 시드 입력(프레임 번호, 세션 4정수)을 양쪽이 같은 값으로 가져야 합니다.

## 10. 검증

`PYTHONIOENCODING=utf-8 .venv/Scripts/python web/tools/camera_swerve.py selftest` → 18항목 PASS (재구현 계산·합성 테스트, 원본 실행 아님).

| 검사 | 기대 | 결과 |
|---|---|---|
| seed(0,0,0,0,0) → X=1, Y=M+2 | sead init 수식 | PASS |
| xorshift 첫 값 | 수식 일치 | PASS |
| bias 0.5 항등 / 0.25 → u² / 부호 유지 / 0.8 → u^0.3219 / |u|<0.001→0 | | PASS |
| 사인표 회전 0, ±6, 12, 37.5, −90도 | math와 1e-4 이내 | PASS |
| 스플래시슈터 30발 연사 후 bias | = Max 0.25 | PASS |
| 점프 직후 swerve / jumpBias | 12 / 0.4 | PASS |
| 점프 후 70프레임 (감소 1) | 서기 값 6 / 0 | PASS |
| RepeatFrame 6 연사 간격 | 6프레임, 대기 상태에서 누르면 0프레임째 발사 | PASS |

몬테카를로(실제 시드 함수, 프레임 0~19999): bias 0.01·6° 평균 |각| 0.788°(이론 0.785°), 0.25·6° 2.007°(2.000°), 0.4·12° 5.178°(5.168°), 0.5·6° 3.004°(3.000°). 최대 각은 정확히 swerve.

`camera_swerve.py sim WeaponShooterNormal --frames 30 --seed 1,2,3,4 --frame0 5000` 출력 앞부분 (웹 구현 비교용 기대값, 시드 값은 임의):

```
f  0 swerve=6.000 bias=0.0100 r=0.549386 u=+0.098772 ub=+0.000000 angle=+0.0000°
f  6 swerve=6.000 bias=0.0200 r=0.997975 u=+0.995951 ub=+0.977360 angle=+5.8642°
f 12 swerve=6.000 bias=0.0300 r=0.613704 u=+0.227408 ub=+0.000557 angle=+0.0033°
```

검증하지 않은 범위: 원본 실행 결과와의 비교, 시드 전역값의 실제 내용, 공중 프레임(본체+0xc0)의 증감 규칙([player] 범위), `aim` 벡터 계산, 탄 생성 함수 내부, Diffusion 무기 계산(판독-부분만).

## 11. 미확정과 필요한 근거

| 항목 | 이유 | 다음 단계 |
|---|---|---|
| ~~시드 전역 F(+0x148)와 a..d(+0x124~0x130)의 정체~~ | 해소(2026-10-03 [판독, network 재사용]): F = GameFrame, a..d = 대전 설정 RandomSeed0..3(§6.2) | 사격장 런타임 값은 [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md) §5.3 미확정 행 |
| (해소) 점프 카운터 감소 조건 Q | 본체+0xc0 = 공중 프레임, 상수 4 | §5 — 남은 것: airFrames 증감 writer는 [player] 범위 |
| vt40 호출 시점 — 8차 §3.1에서 해소 [실행] | 이전 시도: vt+0x140 가상 호출 전수 스캔(플레이어 코드) 0건(§3). 6차: 0x7102200000~0x7102a00000 재스캔, 비GrindRail 후보 0x710248680c 는 반환값을 쓰는 다른 객체(x26) 호출이라 불일치 | 점프 상태 진입 0x7102475a54 부근 공용 잉크액션 호출, [player] 요청 |
| ~~PreDelay/PostDelay 소비처~~ | 해소(2026-10-03): [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md) §3.5, 2483134/24b28b0 [판독] | 입력 writer·상태 집합은 별개 미확정 |
| ~~디버그 플래그 0x71058bbb78+0x15~~ | 해소(2026-10-03 [판독]): 정적 초기화 0, 저장 0건 → 항상 꺼짐(§6.2) | — |
| 블래스터 전용 분기 유무 | §8 참고(경로·흐름은 해소) | 0x7102583008 무기 종류 판별 호출 전수 |
| ~~Diffusion의 CenterDegreeBias/Swerve 사용처~~ | 해소(2026-10-02 [camrest]): 둘 다 결과에 영향 없음(asm 전수, §8) | — |
| 듀얼 흔들림 각 출처·점프 흔들림, 스피너 발사 흔들림, VariableShot 상하 흔들림 | SpChariot는 슈터와 같은 계산으로 해소(§8) | 0x710254d018 디컴파일, 0x71025c0568/0x71025c154c, PitchDegSwerve(+0x50) 리더 |
| ~~logf/expf 비트 일치~~ | 해소(2026-10-03 [실행]): SDK sdk.img logf/expf 원본 실행. 흔들림 bias 29,971건 중 97건(각 94건) 웹 Math 근사와 다름, 최대 14ulp([camera_feel.md](camera_feel.md) §4.2). 정정: 앞 판 "확정 불가"는 틀림 | 비트 일치가 필요하면 SDK logf/expf 이식 |
