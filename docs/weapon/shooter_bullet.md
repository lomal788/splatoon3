# 슈터 탄 계산 (spl::BulletShooterBase)

슈터 계열 메인 무기(스플래시 슈터 등)가 쏜 잉크 탄 하나가 생성되어 날아가고 떨어지는 동안의 속도 계산, 상태 전이, 프레임 순서를 정리합니다. 도색 모양·데미지 값 계산은 각각 [../paint/paint_and_score.md](../paint/paint_and_score.md), [../combat/damage_hit.md](../combat/damage_hit.md)에서 다룹니다.

확정 수준: **[실행]** 원본 실행 / **[판독]** 원본 코드 판독 / **[데이터]** 데이터 / **[추정]** / **[미확정]**. 이 문서의 수치 검증은 모두 "판독한 식의 재구현 계산"이고, 원본을 실행해 비교한 것은 없습니다.

## 1. 개요

- 사용자에게 보이는 동작: 탄이 일정 프레임 동안 일직선으로 빠르게 나가고(GoStraight), 짧게 급감속하며 처지고(Brake), 이후 공기저항과 중력으로 포물선을 그리며 떨어집니다(Free). 날아가는 동안 일정 거리마다 작은 스플래시 탄을 떨어뜨려 바닥을 칠하고, 탄 뒤에는 꼬리(tail)가 늦게 따라옵니다.
- 상태 이름 `GoStraight , Brake , Free`는 열거형 `spl::BulletMoveState` 문자열(`0x71048a26dc`)에서 확인했습니다 **[데이터]**. 코드에서도 상태 번호 0/1/2와 각 스텝 함수가 이 순서로 대응합니다 **[판독]** (§3).

## 2. 분석 대상

| 항목 | 값 |
|---|---|
| 원본 | Splatoon 3 v0 main NSO (`extracted/exefs/main.reloc.img`, 0x7100000000 기준) |
| 액터 | `Pack/Actor/BulletShooterBase.pack.zs` — Behavior `ClassName: spl::BulletShooterBase` |
| 무기 액터 | `Pack/Actor/WeaponShooterNormal.pack.zs` — ActorReservation으로 BulletShooterBase 32개, BulletSplashShooter 32개, BulletWallDrop 16개를 미리 생성 |
| 파라미터 | `Params.pack.zs` → `extracted/params/Component/GameParameterTable/WeaponShooter*.json`, `BulletSplashShooter.json` |
| 디컴파일 | `analysis/decomp/bullet/BulletShooterBase_vt.c`, `BulletSimple_vt.c`, `bullet_move.c`, `WeaponShooter_vt.c`, `shot_spawn.c` |
| 재구현 | `web/tools/bullet_shooter_sim.py`, 결과 `analysis/bullet/` |

## 3. 진입점과 호출 흐름 [판독]

### 3.1 클래스

| 클래스 | vtable | 비고 |
|---|---|---|
| `spl::BulletShooterBase` | `0x71055a5030` (109슬롯) | 생성 `0x710174e644`, 객체 0x1230 B |
| `spl::BulletSimple` | `0x71055a59a8` (81슬롯) | 슬롯 0~80 대부분을 ShooterBase와 공유 → 공통 탄 기반 |
| 이동 인터페이스 | `0x71055a5d28` (9슬롯) | 객체 0x10 B `{vtable, owner}`. BulletSimple 슬롯 8 `0x7101762d44`가 생성해 탄 +0x1a0(+0x1a8)에 저장 |

이동 인터페이스 슬롯은 모두 owner(탄)의 vtable로 넘기는 썽크입니다.

| 인터페이스 슬롯 | 대상 | 의미 |
|---|---|---|
| 2 `0x7101766e98` | `0x7101768170` | 초기 상태 = `GoStraightToBrakeStateFrame == 0 ? Free(2) : GoStraight(0)` |
| 3,4,5 | 탄 슬롯 88,89,90 | 상태 진입 콜백. ShooterBase에서는 빈 함수(`0x71016696b4/b8/bc`) |
| 6 `0x7101766f80` | 탄 슬롯 85 `0x71017657f4` | GoStraight 스텝 |
| 7 `0x7101766f90` | 탄 슬롯 86 `0x71017658cc` | Brake 스텝 |
| 8 `0x7101766fa0` | 탄 슬롯 87 `0x71017659a4` | Free 스텝 |

### 3.2 매 프레임 순서

탄 기반 갱신(vtable 슬롯 18, `0x71016460fc`):

```
body.slot(0x108)()                       // 물리 바디 쪽 준비 (의미 미확정)
if age >= 0: prevPos(+0x110) = 현재 위치
if !slot73():  age(+0x134) += 1          // ShooterBase 슬롯73(0x7101649bc8)은 항상 0 → 항상 증가
slot54()   // 이동 계산 (ShooterBase 0x7101750d6c → BulletSimple 0x7101763a10)
slot57()   // 0x7101764ef8: 충돌 반경 갱신 — BulletSimpleCollisionParam으로 age에서 반경 2개를 구해(0x71018a6b68 / 0x71018a6fe4) 물리 바디 슬롯 0xd0·0xd8에 설정
if byte(+0x12a)==1: setVelocity(0)
```

위치 적분(`pos += vel`)은 이 함수들 안에 없습니다. `setVelocity`(슬롯 50 `0x7101762d10`)가 탄 +0x1118에 속도를 저장하고 물리 바디(+0x138)의 슬롯 0x38로 넘깁니다.

> 정정(이전: "실제 이동·충돌은 Phive 캐릭터 컨트롤러 `BulletSimple`이 처리한다고 봅니다 [추정]"): 캐릭터 컨트롤러가 아닙니다. 탄 ControllerSet의 `CharacterControllerName: BulletSimple`에 해당하는 프리셋이 PhiveConfig에 없고 `PathCharacterController`·강체 목록도 비어 있습니다 **[데이터]**. 탄+0x138은 슬롯67(`0x7101763948`)이 만드는 **탄 바디 래퍼**(vtable `0x710559f3f8`, 바인드 `0x7101644650`)이고, 래퍼 슬롯7(=+0x38) `0x71016cb0a0`이 모든 유닛 바디의 `+0xc4`·`+0xdc`에 **속도×60(유닛/초)** 을 씁니다. 읽기는 슬롯9/10이 ×0.016666668 **[판독]**. 탄 위치는 바디 +0x94에서 읽습니다(`0x710164434c`). 래퍼의 갱신 앞뒤 훅(+0x108/+0x110)은 빈 함수입니다 **[판독]**.
>
> 정정(2026-10-02 3차, 이전: "바디 적분 미확정, `pos += vel` [추정]"): 위치는 물리 스텝마다 phive 탄 바디 스텝 `0x7103b0a2bc`가 한 번 옮깁니다. **`pos = fadd(fmul(dt, fmul(v, 60.0f)), pos)`**(성분별, FMA 아님), dt = 월드+0x24 = 0.016666668f(`0x3c888889`), 서브스텝 없음 **[판독]**. `fl(dt·fl(60v))`는 v와 같지 않은 경우가 많아(무작위 표본 61%) `pos += vel`로 계산하면 40프레임에 최대 약 3e-6 유닛 어긋납니다 **[재구현 계산, `web/tools/bulletbody_integrate.py`]**. 막는 접촉이 있으면 가장 이른 비율 f에서 `pos = p0 + f·(p1−p0)`, 바디 속도 0(반사·미끄러짐 없음) **[판독]**. 상태머신은 탄+0x1118 사본만 쓰므로 ×60/÷60 왕복 반올림의 영향을 받지 않습니다 **[판독]**. 상세는 [../physics/phive_controller.md](../physics/phive_controller.md) §6.3~6.8.

이동 후 처리(슬롯 56, §5.4)는 슬롯 21(`0x7101646544`, 물리 후 단계로 추정)에서 바디 위치(+0x94)로 `prevPos`와의 차를 잽니다. 생성 직후 바디 속도는 0이고(생성 desc 속도 0, `0x71010036a8`) 첫 이동은 첫 슬롯18(age 1)의 setVelocity 뒤 물리 스텝입니다 **[판독]**.

### 3.3 이동 계산 (BulletSimple 슬롯 54, `0x7101763a10`)

```
if holdFrames(+0x1b0) >= 1:               // 정지 프레임
    setVelocity(0); holdFrames -= 1
    if holdFrames == 0: comp(+0x170).slot(0x28)(0)
    return
v = getVelocity()                          // +0x1118
if age == 1 and slot101():                 // ShooterBase slot101(0x71016696e8)은 항상 1
    v = normalize(v) * spawnInfo.speed     // 생성 정보(+0x108) +0x48
    out = moveSM.step(v)
else:
    out = moveSM.step(v)
    if age == 0: out = v                   // 상태 머신은 진행하지만 속도는 그대로
setVelocity(out)
진행 방향으로 회전 행렬을 만들어 물리 바디에 설정 (표시·충돌 방향용)
```

> **정정 (2026-10-02, combat4 판독·메인 스레드 명령 재확인)**: 이전 판은 "age 초기값 0 → 첫 갱신이 age 1 경로"라고 적었으나 틀렸습니다. 생성 함수(`0x710174e644`)가 0을 쓴 뒤, 시작 처리(슬롯 15 → `0x7101762f68` → `0x7101645590`)가 `mov w23,#-1; str w23,[x19,#0x134]`(`0x7101645608`/`0x7101645610`)로 **age = −1**을 씁니다 **[판독]**.

따라서 첫 갱신: 슬롯 18이 `age >= 0` 검사에서 이전 위치 저장을 건너뛰고(age −1), age++ → **0**, 슬롯 54는 `age == 0` 경로라 상태 머신은 한 칸 진행하지만 속도는 생성 속도 그대로입니다. 두 번째 갱신이 age **1**이고 이때 생성 속력으로 재정규화합니다. ShooterBase 슬롯 73은 항상 0이라 age 증가가 멈추는 일은 없습니다 **[판독]**.

영향: age를 쓰는 판정(데미지 감쇠 `ReduceStartFrame/EndFrame`, 반경 lerp, FriendThroughFrame, 꼬리 시작 `DelayShotFrame`)은 "생성 후 갱신 회차 − 1"을 기준으로 계산해야 합니다.

**holdFrames(+0x1b0)를 쓰는 곳** [판독] — 생성 시 -1(슬롯 15). 그 밖에는 충돌 콜백 두 개뿐입니다.

**충돌 콜백 분배** (2026-10-02 3차 해소) [판독] — 접촉은 바디 리스너 → `PhysicsContactReactionSequencer(Entity)` 큐 → 탄 슬롯 22(`0x71017504f4`, 데미지·넉백·히트 이펙트) → `0x7101763310` 끝 → `0x7101646910`이 아래처럼 고릅니다(상세 [../physics/phive_controller.md](../physics/phive_controller.md) §6.5~6.6).

```
막는 접촉(+0x68 bit1)이 하나도 없으면 아무 콜백도 안 부름   // ShooterBase 슬롯64→슬롯63 = 0
상대 바디 레이어 != 3(Ground)        → 슬롯 60  (플레이어·오브젝트 등)
Ground, 첫 막는 접촉 법선 n.y > 0.64144969 → 슬롯 58  (바닥)
Ground, n.y <= 0.64144969            → 슬롯 59  (벽·천장)
```
법선은 탄 쪽에서 본 접촉 법선(`0x71012d4f8c`), 임계값 `[0x7105858358]` = 0.64144969(cos 50.1°)는 정적 초기화 에뮬로 얻은 값입니다 **[실행(에뮬)]**.

컴포넌트 탄+0x170 = 액터+0x518 래퍼(vtable `0x7105540810`, `{vtable, 액터}`) **[판독]**:

| 슬롯 | 함수 | 동작 |
|---|---|---|
| 0x20 | `0x7100f79560` | `액터+0x4d0 == 2` (액터 상태가 2인가) |
| 0x28 | `0x7100f79574` | `0x7100f721b8(액터, 인자)` — 액터 상태 전이 요청. 탄은 인자 0으로 부르며 낙하 소멸(슬롯 19)과 같은 호출이라 **소멸 요청**으로 봄 **[추정]** |
| 0x30 | `0x7100f79580` | &액터+0x28c(액터 위치) |
| 0x38 | `0x7100f7958c` | 액터 위치(+0x28c) = 인자 후 액터 vt+0x1f8 (위치 변경 통지) |

| 콜백 | 충돌 | 함수 | 동작 (ShooterBase) |
|---|---|---|---|
| 탄 슬롯 58 | **Ground 바닥** | `0x7101764de4` | ① 슬롯 84(`0x7101751c08`, 슈터 도색 크기 계산 → 슬롯98=1.0이라 요청을 탄+0x1150~에 **보관**). ② holdFrames = 슬롯 91 = 0. ③ 0이므로 `+0x12a == 0`이고 컴포넌트 0x20이 참이면 `+0x12a = 1` |
| 탄 슬롯 59 | **Ground 벽·천장** | `0x7101764ff8` | ① holdFrames = 슬롯 92 = **4**. ② 바디가 있으면(래퍼 slot16) 접촉점에서 현재 age의 Field 반경(`0x71018a6b68`) 구로 다시 질의해 법선 y ≤ 0.6414인 첫 면의 점·법선으로 슬롯 69(`0x7101648c78` → 자식 탄 생성 `0x7101648824`, BulletWallDrop로 추정)를 부름. 바디가 없으면 슬롯 68. ③ holdFrames ≥ 1이므로 래퍼 slot20(바디+0x90 bit1 = 충돌 끔) 후 컴포넌트 0x38(접촉점) = 액터 위치를 접촉점으로 |
| 탄 슬롯 60 | **Ground 외**(플레이어·오브젝트 등) | `0x7101765794` | 슬롯 82(=0) 이고 `+0x12a == 0`이고 컴포넌트 0x20이 참이면 `+0x12a = 1` (도색·정지 프레임 없음) |

`+0x12a` 처리 **[판독]**: 슬롯 18 끝에서 `== 1`이면 setVelocity(0), 슬롯 21(`0x7101646544`) 끝에서 0이 아니면 1 줄이고 **1→0이 되는 순간 컴포넌트 0x28(0)(소멸 요청)**. holdFrames 처리: 슬롯 54가 holdFrames ≥ 1이면 속도 0, 1 감소, 0이 되면 컴포넌트 0x28(0) — 벽에 닿은 탄은 접촉점에 붙어 4번의 슬롯 54 동안 멈춘 뒤 소멸 요청 **[판독]**.

도색 "보관 후 다음 갱신 칠함"([../paint/paint_shape.md](../paint/paint_shape.md) §7.7)과의 관계 **[판독]**: 보관은 **바닥 콜백(슬롯 58)의 슬롯 84**에서만 생기고, 실행은 슬롯 19의 슬롯 55(`0x71017510c0`)입니다. 벽 콜백(슬롯 59)의 4프레임 정지는 이 보관과 무관한 별개 경로이며, 벽 쪽 도색은 자식 탄(슬롯 69) 생성으로 이어집니다. 바닥 탄은 `+0x12a`로 다음 슬롯 21에서 소멸 요청되므로, 보관한 도색이 소멸 전에 슬롯 55에서 실행되는지는 슬롯 19와 21의 순서에 달려 있습니다 **[미확정]**.

**첫 명중의 age** **[추정]**: age는 슬롯 18에서 이동 전에 증가하고 바디는 생성 때 속도 0이라, 이동으로 생기는 첫 접촉은 age 1 갱신의 물리 스텝에서 납니다. 접촉 처리(슬롯 22, 데미지가 age를 읽음)는 큐에서 나중에 실행되므로 그 사이에 다음 슬롯 18이 끼지 않으면 **age 1**, 끼면 2입니다. 슬롯 18의 `+0x12a == 1` 검사가 의미를 가지려면 접촉 처리가 슬롯 21 뒤·다음 슬롯 18 앞이어야 하므로 **age 1**로 봅니다. 생성 위치가 처음부터 겹친 경우(속도 0 스텝의 f = 0 접촉)에 첫 슬롯 18 전에 물리 스텝이 도는지는 확인하지 못해 age 0 가능성은 남습니다 **[미확정]**.

`age == 1`에서 맞추는 크기는 플레이어 속도 가산이 포함된 발사 속도의 크기입니다(§5.5). 생성 직후 한 프레임 사이 속도가 바뀌는 경우(충돌 등)를 되돌리는 용도로 보이지만 확인하지 않았습니다 **[추정]**.

### 3.4 ShooterBase 추가 처리 (슬롯 54 재정의 `0x7101750d6c`)

1. BulletSimple 슬롯 54를 그대로 호출합니다.
2. `holdFrames >= 0`이면 표시용 값 +0x11c8~0x11dc를 `새값 + (이전값-새값)*0.6`로 감쇠 보간합니다(꼬리 표시 보간으로 추정).
3. **꼬리 점**: 탄 나이가 `BulletShooterTailLengthParam.DelayShotFrame`(기본 3) 이상이 되면 두 번째 상태 머신(+0x1210, 인터페이스 +0x1218)을 시작하고, 이후 매 프레임 같은 스텝 함수로 꼬리 속도(+0x11e0)를 갱신합니다. 꼬리 위치는 슬롯 55(`0x71017510c0`)에서 `pos + (old - pos)*0.88` 형태로 보간합니다. 꼬리 길이 제한(MaxLengthFrame, StartMaxLength, EndMaxLength)이 쓰이는 곳은 확인하지 않았습니다 **[미확정]**.

## 4. 구조체·필드·상수

### 4.1 `spl::BulletSimpleMoveParam` (`$type spl__BulletSimpleMoveParam`, GameParameterTable 키 `MoveParam`)

기준 객체: 파라미터 객체(0x68 B). 기본값은 팩토리 `0x710153bdd4`, 필드 순서·오프셋은 방문 함수 `0x710153bee0` **[판독]**. 설정됨 플래그는 +0x58+순번.

| 오프셋 | 플래그 | 타입 | 이름 | 기본값 | 스플래시슈터 | reader |
|---|---|---|---|---|---|---|
| +0x54 | 0x58 | f32 | SpawnSpeed | 2.0 | 2.2 | 무기 쪽 생성 속력(`0x710287e6b8` 등) |
| +0x50 | 0x59 | s32 | GoStraightToBrakeStateFrame | 10 | 4 | `0x71017657f4`, `0x7101768170`, 생성 속력 |
| +0x4c | 0x5a | f32 | GoStraightStateEndMaxSpeed | 10.0 | 1.4495 | `0x71017658cc` |
| +0x34 | 0x5b | f32 | BrakeGravity | 0.07 | (기본) | `0x71017658cc` |
| +0x30 | 0x5c | f32 | BrakeAirResist | 0.36 | (기본) | `0x71017658cc` |
| +0x40 | 0x5d | f32 | BrakeToFreeVelocityY | -0.15 | (기본) | `0x71017658cc` |
| +0x3c | 0x5e | f32 | BrakeToFreeVelocityXZ | 0.2355 | (기본) | `0x71017658cc` |
| +0x38 | 0x5f | s32 | BrakeToFreeStateFrame | 4 | (기본) | `0x71017658cc` |
| +0x48 | 0x60 | f32 | FreeGravity | 0.016 | 0.016 | `0x71017658cc`, `0x71017659a4` |
| +0x44 | 0x61 | f32 | FreeAirResist | 0.02 | (기본) | `0x71017658cc`, `0x71017659a4` |

값을 읽을 때는 플래그가 켜진 객체를 찾을 때까지 부모 파라미터로 올라갑니다(`$parent` 상속, [02 §2](../02_code_and_params.md)). 즉 데이터에 없는 필드는 부모 표 → 코드 기본값 순서로 정해집니다 **[판독]**.

슈터별 값(데이터에 있는 것만, 나머지는 기본값):

| 표 | SpawnSpeed | GoStraightToBrakeStateFrame | GoStraightStateEndMaxSpeed | FreeGravity |
|---|---|---|---|---|
| WeaponShooterNormal | 2.2 | 4 | 1.4495 | 0.016 |
| WeaponShooterShort | 2.0 | 2 | (`analysis/bullet/sim_summary.json` 참고) | |
| WeaponShooterLong | 3.36 | 5 | | |
| WeaponShooterBlaze / First | 2.2 | 3 | | |
| WeaponShooterPrecision | 3.92 | 2 | | |
| WeaponShooterGravity | 2.2 | 4 | | |
| BulletSplashShooter | 0.0 | 0 (→ 처음부터 Free) | 0.0 | 0.05, FreeAirResist 0.1 |

### 4.2 탄 객체 필드 (기준: `spl::BulletShooterBase` 객체, 0x1230 B)

| 오프셋 | 타입 | 의미 | writer | reader |
|---|---|---|---|---|
| +0x108 | ptr | 생성 정보 객체 | 생성 경로(미확정) | 여러 곳 |
| +0x110 | vec3 | 이전 프레임 위치 | 슬롯 18 | 슬롯 56 |
| +0x134 | s32 | age(생성 후 갱신 수) | 초기화 0(`0x710174e644` 경로), 슬롯 18 +1 | 슬롯 54/56, 꼬리 시작 |
| +0x12a | u8 | 소멸 대기 카운터(1이면 슬롯 18 끝 속도 0, 슬롯 21에서 1→0이면 소멸 요청) | 슬롯 58·60 | 슬롯 18·21 |
| +0x138 | ptr | 탄 바디 래퍼(vtable `0x710559f3f8`, physics §6) | 슬롯 67 `0x7101763948` | setVelocity 등 |
| +0x170 | ptr | 액터+0x518 래퍼(vtable `0x7105540810`, §3.3) | `0x71015318d4` | 슬롯 18·19·21·54·58~60 |
| +0x198 | u32 | 이동 상태 0/1/2 | 슬롯 15, `0x71017697f8` | `0x71017697f8` |
| +0x19c | s32 | 상태 내 프레임 | 같음 | 스텝 함수 인자 |
| +0x1a0 | ptr | 이동 인터페이스 | 슬롯 8 | `0x71017697f8` |
| +0x1b0 | s32 | 정지(hold) 프레임, 시작 시 -1 | 슬롯 15 | 슬롯 54 |
| +0x1118 | vec3 | 속도 | setVelocity | getVelocity |
| +0x1124~ | vec3 | 진행 방향 기준축 | 슬롯 15·54 | 슬롯 54 |
| +0x11e0 | vec3 | 꼬리 속도 | 슬롯 15(dir×speed), 슬롯 54 | |
| +0x11ec | u8 | 꼬리 시작됨 | 슬롯 15=0, 슬롯 54=1 | |
| +0x11f4 | f32 | 스플래시 생성용 누적 거리 | 슬롯 15·56 | 슬롯 56 |
| +0x11fc | s32 | 남은 스플래시 수(로 추정) | 슬롯 15 | 슬롯 56 |
| +0x1204 | f32 | 최고 높이로 추정. 생성(`0x710174e644`)·시작(슬롯 15)에서 -1000000.0(0xc9742400) | 슬롯 15·56 | 슬롯 56 |
| +0x1208 | f32 | 가까운 지점 강제 스플래시 거리 | 슬롯 15 | 미확정 |
| +0x1210 | u32,s32 | 꼬리 이동 상태, 상태 프레임 | 슬롯 54 | |
| +0x1218 | ptr | 꼬리 이동 인터페이스 | | |
| +0x1200(=param_1[0x240]) | f32 | 누적 이동 거리 | 슬롯 56 | 도색 폭 보간 슬롯 84 |
| +0x120c | f32 | 랜덤 각도 `rand*2π` | 슬롯 15 | 미확정(표시용 회전으로 추정) |

주의: `param_1[0x240]`은 8바이트 단위 인덱스라 바이트 오프셋 +0x1200입니다. 슬롯 15에서 `param_1[0x240] = -0x368bdc0000000000`(= u64 0xc974240000000000: +0x1200 = 0.0, +0x1204 = -1000000.0)으로 초기화하고, 슬롯 56이 하위 f32(+0x1200)에 이동 거리를 더합니다. 상위 +0x1204는 슬롯 56에서 `max(+0x1204, y)`로 갱신되어 최고 높이를 기록하는 것으로 보입니다 **[추정]**.

### 4.3 생성 정보 객체 (기준: 탄 +0x108이 가리키는 객체)

| 오프셋 | 타입 | 의미 | 근거 |
|---|---|---|---|
| +0x94, +0x98 | f32 | 부모 탄 속도의 x, z (스플래시 생성정보, weapon 구현 판독 — 이전 "분할 관련" 해석 정정) | 스플래시 생성 | 스플래시 도색 방향 |
| +0x2c | s32 | 팀 번호(0~2, -1/3은 무효) | 슬롯 15·106에서 팀 배열 인덱스로 사용 **[추정]** |
| +0x30 | vec3 | 발사 위치 | 슬롯 15에서 꼬리 위치 초기값 |
| +0x3c | vec3 | 발사 방향(단위 벡터로 추정) | 슬롯 15에서 `dir × speed` |
| +0x48 | f32 | 발사 속력 | 슬롯 15, 슬롯 54의 age 1 재정규화 |
| +0x64 | s32 | 발사 GameFrame(송신 프레임, 발사 함수 인자 w6). 탄 난수 시드에만 쓰임 | 슬롯 15 |
| +0x90 | u8 | 연사 안 탄 순번 또는 분할 인덱스 | 슬롯 15 스플래시 일정 |
| +0x98, +0x9c | | 탄 +0x11c0/+0x11c4로 복사 | 미확정 |
| +0xf0 | ptr | BulletSplashShooterSpawnParam (GameParameterTable `SplashSpawnParam`) | 슬롯 15·56·`0x710174fe94` |

## 5. 상태 전이와 계산식

### 5.1 상태 머신 (`0x71017697f8`) [판독]

```
struct MoveSM { u32 state; s32 frame; Iface* iface; }   // 탄 +0x198
step(sm, out, in):
    done = iface.step[sm.state](out, in, sm.frame)       // 표 0x7105853a00 = {0x30,0x38,0x40}
    if !done: sm.frame += 1
    else:
        sm.state += 1                                      // 3 이상이면 표 0번 사용
        iface.enter[sm.state]()                            // 표 0x7105853a38 = {0x18,0x20,0x28}
        sm.frame = 0
start(sm):                                                 // 슬롯 15 0x7101762f68
    sm.state = iface.initialState(); iface.enter[state](); sm.frame = 0; holdFrames = -1
```

Free 스텝은 항상 false를 반환하므로 Free가 마지막 상태입니다.

### 5.2 스텝 함수 [판독]

모든 연산은 f32입니다. `p`는 상속 조회를 거친 MoveParam입니다.

**GoStraight** (`0x71017657f4`)
```
out = in
return frame >= GoStraightToBrakeStateFrame - 1
```
→ GoStraight 상태에서 N(=GoStraightToBrakeStateFrame)프레임 동안 속도가 그대로이고, N번째 스텝 직후 Brake로 넘어갑니다.

**Brake** (`0x71017658cc`)
```
(x,y,z) = in
if frame == 0:                                    // Brake 첫 프레임
    if |v|² > GoStraightStateEndMaxSpeed²: v = v / |v| * GoStraightStateEndMaxSpeed
r = BrakeAirResist; g = BrakeGravity
b = (x - x*r,  y + (y*(-r) - g),  z - z*r)
if BrakeToFreeVelocityY <= b.y:            out = b; return false
if BrakeToFreeVelocityXZ² <= b.x²+b.z² and frame < BrakeToFreeStateFrame:
                                           out = b; return false
// 이 프레임 안에서 Free로 전환: 비율 t만큼 Brake, 나머지 1-t만큼 Free
t1 = (BrakeToFreeVelocityY <= y) ? min((VY - y)/(b.y - y), 1) : 0
hp = sqrt(x²+z²); t2 = 0
if VXZ <= hp:
    hn = sqrt(b.x²+b.z²)
    if hn - hp != 0: t2 = min((VXZ - hp)/(hn - hp), 1)
t3 = (frame <= BrakeToFreeStateFrame) ? 1 : 0
t  = max(t1, min(t2, t3))
i  = v + (b - v)*t                          // 성분별
fr = FreeAirResist; fg = FreeGravity; s = 1 - t
out.x = i.x + s*((i.x - i.x*fr) - i.x)
out.y = i.y + s*((i.y + (i.y*(-fr) - fg)) - i.y)
out.z = i.z + s*((i.z - i.z*fr) - i.z)
return true
```
`v`는 첫 프레임 클램프가 적용된 값입니다. 식의 덧셈·곱셈 순서는 디컴파일 그대로 옮겼습니다. 이동 코드 영역 0x7101765700~0x7101769800(4,160명령)에 `fmadd/fmsub/fnmadd/fnmsub`가 하나도 없으므로, 연산마다 f32로 반올림하면(`Math.fround`) 원본과 같은 비트 결과를 기대할 수 있습니다 **[판독]**. 단 `sqrt`는 `fsqrt`이고 NaN일 때만 라이브러리 함수(`0x7103e9bb50`)로 갑니다.

**Free** (`0x71017659a4`)
```
out = (x - x*fr,  y + (y*(-fr) - fg),  z - z*fr)
return false
```

### 5.3 시작 처리 (ShooterBase 슬롯 15, `0x710174efc0`) [판독]

1. BulletSimple 시작(`0x7101762f68`)으로 이동 상태 머신 초기화.
2. **탄별 난수 생성기**: `seed = (탄 관리자 싱글턴 +0x120의 s32, 없으면 0) + spawnInfo+0x64`.
   탄 관리자는 GOT `0x7105797f18` → 포인터 변수 `0x7105850620`이 가리키는 객체이고, 초기화 `0x71016e2fd4`가 +0x124~+0x130에 시드 a~d를 넣은 뒤 `+0x120 = 13a + 59b + 71c + 97d`로 정합니다. 원천 객체가 없으면 a~d = (1,2,3,4)이고 +0x120 = 10입니다 **[판독, network 담당]**. a~d는 송신 권한 기기가 전역 xorshift128로 만든 u32 4개를 `spl::OnlineVersusSetting`(+0x238~+0x244)으로 배포한 값입니다. 배포는 [판독], 로비가 이 값을 `[[*0x71058e42f8]+0xd0]+0x6548`의 +0xa4~+0xb0으로 복사하는 것(`0x7102d60098`)은 [실행]으로 확인했습니다. 다만 탄 관리자 초기화는 `+0xc8` 쪽 객체를 읽으며, `+0xd0 → +0xc8` 복사 지점은 아직 못 찾았습니다 **[미확정]**. 따라서 탄 시드 = `매치 공통값(13a+59b+71c+97d) + 발사 GameFrame`이라 모든 기기에서 같은 난수열이 나옵니다 **[판독, 마지막 연결 추정]**.
   `sead::Random` 방식(xorshift128)으로 상태 4개를 만듭니다.
   ```
   s0 = (seed ^ seed>>30)*0x6c078965 + 1
   s1 = (s0 ^ s0>>30)*0x6c078965 + 2
   s2 = (s1 ^ s1>>30)*0x6c078965 + 3
   s3 = (s2 ^ s2>>30)*0x6c078965 + 4
   next(): t = s0 ^ (s0<<11); s0=s1; s1=s2; s2=s3; s3 = t ^ (t>>8) ^ s3 ^ (s3>>19); return s3
   float01(): f32 비트 (next()>>9 | 0x3f800000) - 1.0
   ```
   전역 값과 생성 정보 값만으로 정해지므로 같은 입력이면 모든 기기에서 같은 난수열이 나옵니다. 네트워크 동기에 쓰이는지는 [../network/network.md](../network/network.md) 담당 범위입니다 **[추정]**.
3. **스플래시 생성 일정** (BulletSplashShooterSpawnParam):
   - `split = SplitNum`(0이면 1), `between = SpawnBetweenLength / split`, `nearest = 0x710174fe94()` = `SpawnNearestLength > 0 ? SpawnNearestLength : SpawnBetweenLength / split`.
   - `ForceSpawnNearestAddNumArray`(스플래시슈터 `[4]`)와 표 `0x7104a9b0a1`(분할 수별 16바이트 순열)로 이 탄의 `spawnInfo+0x90` 인덱스가 "가까운 지점 강제 생성" 대상인지 정합니다. 대상이면 +0x1208 = `(between - nearest) + between*(split-1) + rand*nearest`.
   - 첫 생성까지 남은 거리 +0x11f4 = `(between - nearest) + between*idx + rand*(idx==split-1 ? nearest : between)`.
   - 남은 생성 수 +0x11fc = `floor(SpawnNum) + (조건: (split-1) - (frac(SpawnNum)*split - 1) <= idx)`. 즉 `SpawnNum`의 소수부(1.5 → 0.5)를 분할 인덱스로 나눠 일부 탄만 하나 더 생성합니다.
   - 표 `0x7104a9b0a1`은 분할 수 N(1~15)마다 16바이트 행이고, 앞 N바이트가 0..N-1의 순열입니다 **[데이터]**:

     | N | 순열 |
     |---|---|
     | 2 | 1 0 |
     | 3 | 2 0 1 |
     | 4 | 3 1 2 0 |
     | 5 | 4 2 0 3 1 |
     | 6 | 5 1 4 2 0 3 |
     | 7 | 6 1 4 2 5 0 3 |
     | 8 | 7 4 1 6 3 0 5 2 |
     | 9 | 8 5 0 3 6 2 7 4 1 |
     | 10 | 9 2 5 8 1 4 7 0 3 6 |
     | 11 | 10 2 5 8 0 3 6 9 1 4 7 |
     | 12 | 11 2 7 10 4 1 9 6 3 0 8 5 |
     | 13 | 12 4 9 1 6 11 3 8 0 5 10 2 7 |
     | 14 | 13 2 7 10 0 3 6 12 9 4 1 11 8 5 |
     | 15 | 14 3 8 11 4 7 12 0 5 10 1 6 13 2 9 |

     전체 덤프는 `extracted/exefs/main.reloc.img` 0x4a9b0a1부터 16×16바이트.
   - 판정: `ForceSpawnNearestAddNumArray`의 각 값 v에 대해 `perm[N][v mod N] == idx`(idx = 생성 정보 +0x90)이면 이 탄이 "가까운 지점 강제 생성" 대상이 됩니다(+0x11ee = 1) **[판독]**. 스플래시슈터는 N = 8, 배열 [4] → perm[8][4] = 3이므로 idx 3인 탄만 대상입니다 **[재구현 계산]**.
   - 순열 모양(첫 값이 N-1이고 나머지가 고르게 흩어짐)으로 보아 연사되는 탄들의 첫 스플래시 위치를 구간 안에 고르게 퍼뜨리는 용도로 보입니다 **[추정]**. idx를 매 발사 어떻게 정하는지(발사 함수 인자 `param_7`의 출처)는 **[미확정]**입니다.
4. +0x120c = `float01() * 2π` **[판독]** (용도 미확정).
5. 꼬리 초기화: 위치 = `spawnInfo.pos`, 속도 = `spawnInfo.dir * spawnInfo.speed`, 꼬리 시작 플래그 0.

### 5.4 이동 후 처리 (슬롯 56, `0x71017512bc`) [판독]

```
d = pos - prevPos
if dot(d, vel) >= 0 and vel != 0:
    traveled(+0x1200) += |d|                 // 3D 거리 → 도색 폭 보간(슬롯 84)에 사용
    h = sqrt(dx² + dz²)                       // 수평 거리
    if remainingSplash(+0x11fc) > 0:
        acc(+0x11f4) += h
        while acc >= SpawnBetweenLength:      // 플래그 0x79 → 오프셋 0x68
            spawnSplash(0x71017540ec)
            acc -= SpawnBetweenLength
            ...(남은 수 감소 등, 이후 부분 미판독)
```
스플래시 탄은 `BulletSplashShooter`이며 그 MoveParam은 처음부터 Free(공기저항 0.1, 중력 0.05)입니다 **[데이터]**.

**스플래시 하나 생성** (`0x71017540ec(acc, h, bullet, isLast)`) **[판독]**

```
// 1) 위치: 이번 프레임 이동 구간에서 누적 거리가 SpawnBetweenLength를 넘은 지점
if |h| >= 0.0001:
    f = 1 - (acc - SpawnBetweenLength) / h
    spawnPos = prevPos + f * (pos - prevPos)         // x,y,z 각각 (디컴파일상 z 성분 식이 일부 깨져 보임, 확인 필요)
else:
    spawnPos = prevPos
// 2) 이 스플래시 전용 난수: seed = 전역(+0x120) + spawnInfo+0x64 + 남은 스플래시 수(+0x11fc)
rng = SeadRandom(seed)
// 3) 기준 방향
d = pos - prevPos (길이² < 1e-8 이면 위/아래 단위벡터로 대체)
up = 상수 벡터 *0x7105791978 (d가 수직에 가까우면 *0x71057919a0)  // 값 미덤프
side = f(d, up)   (0x71012500d4, 외적 계열로 추정)
// 4) 속도 성분
side = normalize(side) * (rng.float01() * 2X - X)       // X = RandomSpawnVelXMax(+0x58), 기본 0.055
up   = normalize(up)   * (rng.float01() * 2Y - Y)       // Y = RandomSpawnVelYMax(+0x5c), 기본 0.015
fwd  = normalize(d)    * (Zmin + (Zmax - Zmin) * rng.float01())  // +0x64 기본 0.01, +0x60 기본 0.02
sum  = side + up + fwd
→ 생성 요청: 위치 spawnPos, 방향 normalize(sum), 속력 |sum|, 액터 이름 = spawnInfo+0xa8 문자열, 팀 spawnInfo+0x2c 등
```

난수는 X → Y → Z 순서로 뽑습니다. 각 범위 조건(`-X <= X`, `Zmin <= Zmax`)이 거짓이면 그 단계에서 난수를 소비하지 않습니다. 스플래시 탄의 도색은 [../paint/paint_and_score.md](../paint/paint_and_score.md)에서 다룹니다.

### 5.5 생성 속력과 초기 속도 (무기 쪽) [판독]

**발사 속력** (`0x7102899980`, 같은 형태 `0x710287e6b8`, `0x7102892070`, `0x71028bcc94`)
```
speed = MoveParam.SpawnSpeed + 0.0 / max(MoveParam.GoStraightToBrakeStateFrame, 1)
```
분자 0.0은 디컴파일러가 반환값을 놓친 것이 아니라 명령 자체가 `fmov s1, wzr; fdiv s9, s1, s0`입니다(`0x7102899d0c`). 그러니 v0에서 **발사 속력 = SpawnSpeed**입니다 **[판독]**. (2026-10-02 정정: 이전 판에서는 "extra 미확정"으로 적었습니다.)

**생성 정보 채우기** (`0x71025823b0`, 발사 함수 `0x71025817c8`이 호출)

로컬 발사(인자 local=1, 생성 정보 +0x6d = 1):
```
v = initialVelocity(speed, aimDir, muzzleExtra(+0xe4..), playerVel, aimAxis, AdditionParam)   // 0x71026beed0
spawnInfo.pos   (+0x30) = 발사 위치
spawnInfo.dir   (+0x3c) = normalize(v)
spawnInfo.speed (+0x48) = |v|
```
복제(수신 기기, local=0): 이벤트로 받은 위치·속도를 그대로 써서 `dir = normalize(v)`, `speed = |v|`, 그리고 `+0x58 = v × GoStraightToBrakeStateFrame`(직진 구간 변위로 추정), `+0x68`에 전달값을 넣습니다.

공통: `+0x90 = 분할 인덱스(인자)`, `+0x98 = 인자1`, `+0x9c = 0`, `+0x64 = 발사 GameFrame(인자, [network] 판독)`, `+0x10/+0x14 = 팀 정보`.

**초기 속도** (`0x71026beed0`) — `SpawnBulletAdditionMovePlayerParam`(이하 A)으로 플레이어 이동 속도를 더합니다. 오프셋·플래그는 방문 함수 순번과 일치합니다(+0x30 XRate, +0x34 YMax, +0x38 YMinusRate, +0x3c YPlusRate, +0x40 ZRate, +0x44 GuideYMinusZero; 플래그 0x45~0x4a).
```
d = 조준 방향(단위), p = 플레이어 속도, a = 조준 기준 축(호출자가 어떤 행렬 열의 부호를 뒤집어 넘김)
t   = p.x*a.x + p.z*a.z                       // p.y는 무시 (식에 p.y*0.0)
pa  = a * t                                   // 축 방향 성분
if p.y > 0:                yr = A.YPlusRate
elif guide && A.GuideYMinusZero: yr = 0        // guide = 인자 (생성 정보 경로에서는 0)
else:                      yr = A.YMinusRate
vy  = min(p.y * yr, A.YMax)
v.x = d.x*speed + (p.x - pa.x)*A.XRate + pa.x*A.ZRate
v.y = d.y*speed + (0   - pa.y)*A.XRate + pa.y*A.ZRate + vy
v.z = d.z*speed + (p.z - pa.z)*A.XRate + pa.z*A.ZRate
```
즉 조준 축 방향의 플레이어 속도는 ZRate배(스플래시슈터 2.0), 그 옆 성분은 XRate배(기본 0.4), 위로 움직이면 YPlusRate배(기본 1.0)로 더해집니다. 무기 표에 A가 없으면 코드가 만든 기본 객체(XRate 0.4, YMax 100, YMinusRate 0, YPlusRate 1.0, ZRate 2.0)를 씁니다 **[판독]**.

정정(2026-10-02, weapon 구현 담당 판독·원본 실행): 이전 판의 "muzzleExtra(+0xe4~0xec)"는 플레이어 **최종 속도**(본체+0xe4)이고, 조준 축 `a` = normalize(카메라 주시점 − 카메라 위치)입니다. 발사 위치는 `0x7102552170`: 본체+0x58 + (0, 1.1, 0) + 총구 오프셋 (−0.24, 0, 0.18)을 피치 베지어 축(−70°/5°/75°)으로 돌린 값이며 원본 실행 17/17 비트 일치입니다([../impl/weapon.md](../impl/weapon.md)). 조준 흔들림은 `d`에 이미 반영돼 들어옵니다([../camera/aim_swerve.md](../camera/aim_swerve.md)).

**age 1 재정규화와의 관계**: 생성 정보의 speed는 플레이어 속도 가산이 포함된 |v|입니다. 그러니 age 1 재정규화(§3.3)는 가산분을 없애지 않고, 크기를 발사 시점 값으로 다시 맞추기만 합니다 **[판독]**. (이전 판의 "가산분 제거" 추정은 틀려서 정정했습니다.)

## 6. 의사코드 (웹 구현용)

```ts
// 원본 확인 이름은 `원본:` 주석, 나머지는 웹 권장 이름
enum MoveState { GoStraight = 0, Brake = 1, Free = 2 }   // 원본: spl::BulletMoveState

interface MoveParam {                                       // 원본: spl::BulletSimpleMoveParam
  spawnSpeed: number; goStraightToBrakeStateFrame: number; goStraightStateEndMaxSpeed: number;
  brakeGravity: number; brakeAirResist: number; brakeToFreeVelocityY: number;
  brakeToFreeVelocityXZ: number; brakeToFreeStateFrame: number; freeGravity: number; freeAirResist: number;
}

class ShooterBullet {
  age = -1;                    // 원본 +0x134 — 시작 처리가 −1을 씀(§3.3 정정)
  state: MoveState; stateFrame = 0;   // +0x198 / +0x19c
  holdFrames = -1;             // +0x1b0
  vel: Vec3; pos: Vec3; prevPos: Vec3;
  traveled = 0;                // +0x1200

  constructor(spawn: { pos: Vec3; dir: Vec3; speed: number; seed: number }, p: MoveParam) {
    this.state = p.goStraightToBrakeStateFrame === 0 ? MoveState.Free : MoveState.GoStraight;
    this.vel = scale(spawn.dir, spawn.speed);   // spawn.dir/speed = normalize/|initialVelocity(...)| (§5.5)
  }

  update(p: MoveParam, spawnSpeed: number) {     // 원본 슬롯18 → 슬롯54
    if (this.age >= 0) this.prevPos = this.pos;   // 첫 갱신(age −1)은 저장 생략
    this.age++;
    if (this.holdFrames >= 1) { this.vel = ZERO; this.holdFrames--; return; }
    let v = this.vel;
    if (this.age === 1) v = setLength(v, spawnSpeed);
    const [out, done] = STEP[this.state](p, v, this.stateFrame);   // f32 연산 유지(Math.fround)
    if (done) { this.state++; this.stateFrame = 0; } else this.stateFrame++;
    this.vel = this.age === 0 ? v : out;                           // age 0: 상태만 진행, 속도 유지
  }

  integrate() {                                          // 물리 단계 0x7103b0a2bc (충돌은 physics §7 BulletBody.step)
    const DT = Math.fround(1 / 60);
    this.pos = this.pos.map((c, i) => Math.fround(Math.fround(DT * Math.fround(this.vel[i] * 60)) + c));
  }

  postUpdate() {                                         // 원본 슬롯56
    const d = sub(this.pos, this.prevPos);
    if (dot(d, this.vel) >= 0) this.traveled += len(d);
    // 수평 거리 누적 → SpawnBetweenLength마다 스플래시 생성
  }
}
```

f32 정밀도는 `Math.fround`로 매 연산마다 맞춥니다. 재구현 `bullet_shooter_sim.py`가 같은 순서의 f32 계산을 하므로 웹 결과와 바로 비교할 수 있습니다.

## 7. 표현·에셋 연결

- 진행 방향 회전 행렬을 매 프레임 물리 바디에 넣습니다(슬롯 54 끝). 탄 모델·이펙트의 방향은 이것을 따른다고 봅니다 **[추정]**.
- 꼬리 점(§3.4)은 잉크 줄기 표시용으로 보입니다 **[추정]**. 이펙트·사운드 연결은 [../effect_sound/effect_sound.md](../effect_sound/effect_sound.md).
- 액터: `BulletShooterBase` 바디 레이어 `SplInkBullet_FriendThrough`, `BlockableLayerHitMask: HitAll` **[데이터]**. 단 탄 시작(`0x7101762f68`)과 이동(`0x7101763a10`)이 `FriendThroughFrameForPlayer`에 따라 레이어를 8(SplInkBullet) ↔ 9(FriendThrough)로 바꾸므로, 이 값이 0인 슈터 탄은 시작하자마자 레이어 8이 됩니다 **[판독, combat]**.

## 8. 다른 기능과의 상호작용

| 대상 | 연결 | 문서 |
|---|---|---|
| 도색 | 이동 거리 +0x1200으로 도색 폭(Near/Middle/Far) 보간(슬롯 84), 스플래시 탄 생성. 슬롯 84는 생성 정보 +0x6d(로컬 플래그)가 0이면 바로 돌아가므로 **복제 탄은 칠하지 않음**(칠은 발사 기기가 PaintRequest로 송신) [판독, paint] | [paint](../paint/paint_and_score.md) |
| 데미지 | 감쇠 `0x71017506d0`: `t=clamp01((age-Start+1)/max(End-Start,1))`, `dmg=trunc(Max+(Min-Max)t)` — age는 이 문서의 +0x134(슬롯 18에서 이동 전 증가). 단위 1 = 0.1 HP | [combat](../combat/damage_hit.md) |
| 헬퍼 | 슬롯 36 `0x71015315d0`이 "spl::KnockBackHelper", "spl::BulletHitEffect", "spl:DamageHelper" 이름을 참조합니다. `spl:DamageHelper`는 탄 쪽 헬퍼가 아니라 피해를 받는 액터의 HitPointHolder 컴포넌트입니다([combat](../combat/player_life.md), 2026-10-02 정정). 슬롯 36에서 각각을 생성하는지 조회하는지는 **[미확정]** | combat |
| 충돌 | 반경 = ChangeFrame 0이면 End, 아니면 `max(lerp(Init,End,clamp01(age/Change)),0.02)` (`0x71018a6b68`) | [combat](../combat/damage_hit.md) |
| 벽 | Ground 벽·천장 접촉 → 슬롯 59: 4프레임 정지 + 슬롯 69로 자식 탄 생성(BulletWallDrop로 추정, ActorReservation 16개) — §3.3 | [physics](../physics/phive_controller.md) §6.6 |
| 네트워크 | 발사자 기기만 `PlayerNetEvent::Bullet*` 송신(`0x71018b7f30`), 수신 기기는 같은 발사 함수를 비소유 플래그로 호출해 복제 탄을 시뮬레이션하며, 경과 프레임만큼 앞당기는 지연 보정은 없음(+0x64를 읽는 79곳 전수 분류, [판독]). 명중 판정은 공격자 쪽. 탄 액터에는 Net 컴포넌트가 없음 | [network](../network/network.md) |

## 9. 웹 포팅 구조와 구현 순서

1. `MoveParam` 로더: GameParameterTable JSON + `$parent` 상속 + 코드 기본값(§4.1 표). 상속 병합 규칙: 필드 단위로 "값이 있는 가장 가까운 객체" 우선.
2. `BulletMoveSM`: §5.1~5.2를 f32로 그대로 구현. `bullet_shooter_sim.py` 출력과 프레임별 일치 확인.
3. `ShooterBullet`: §3.2 순서(prevPos → age++ → 이동 → 물리 적분 → 이동 후 처리).
4. `SeadRandom`: §5.3 그대로. 시드 입력 두 개(전역 값, 생성 정보 +0x64)의 출처는 미확정이라 웹에서는 서버가 정해 배포하는 값으로 대체 가능.
5. 스플래시 생성 일정(§5.3·5.4) — 미확정 부분은 확인 후 구현.
6. 꼬리 점 — 표시 전용으로 보이므로 뒤로 미뤄도 됩니다.

브라우저·서버가 공유해야 할 로직: 이동 상태 머신(결정적), 난수 생성기. 물리 충돌은 서버 권한 여부를 네트워크 문서와 맞춰 결정합니다.

## 10. 검증 [재구현 계산]

`.venv/Scripts/python web/tools/bullet_shooter_sim.py WeaponShooterNormal --frames 30` (수평 발사, 위치는 `pos += vel` 근사). 원본 실행 비교 없음. 원본 바디 적분식(`fl(dt·fl(60v)) + p`)과의 차이는 `web/tools/bulletbody_integrate.py`로 잽니다(40프레임 최대 2.9e-6 유닛, 아래 표 위치값과의 차이도 이 범위).

| age | 상태(스텝 후) | vy | vz | z 누적 |
|---|---|---|---|---|
| 1~3 | GoStraight | 0 | 2.2 | 2.2 / 4.4 / 6.6 |
| 4 | → Brake(frame 0) | 0 | 2.2 | 8.8 |
| 5 | Brake | -0.07000 | 0.92768 (=1.4495×0.64) | 9.7277 |
| 6 | Brake | -0.11480 | 0.59372 | 10.3214 |
| 8 | Brake | -0.16182 | 0.24319 | 10.9446 |
| 9 | → Free (프레임 내 전환) | -0.17448 | 0.23120 | 11.1758 |
| 30 | Free | -0.39075 | 0.15127 | 15.0927 |

경계·반대 조건:
- 30° 위로 쏘면 9프레임째에도 Brake에 머뭅니다(`vy`가 아직 -0.15 위). 전환 조건이 수직 속도와 수평 속도·프레임 둘 다에 걸린다는 판독과 맞습니다.
- `GoStraightToBrakeStateFrame = 0`(BulletSplashShooter)이면 시작 상태가 Free입니다. 단 스플래시 탄의 age 1 재정규화 속력은 생성 정보 +0x48에서 오므로, MoveParam의 SpawnSpeed 0으로 돌린 시뮬레이션 값은 의미가 없습니다.

초기 속도(§5.5, `bullet_shooter_sim.initial_velocity`, 스플래시슈터 ZRate 2.0, 나머지 기본값, 조준 = 축 = +z):

| 플레이어 속도 | 결과 v | 해석 |
|---|---|---|
| 정지 | (0, 0, 2.2) | SpawnSpeed 그대로 |
| 전진 0.096(인간 기본 이동) | (0, 0, 2.392) | 2.2 + 0.096×ZRate 2.0 |
| 옆 0.096 | (0.0384, 0, 2.2) | 옆 성분 ×XRate 0.4 |
| 상승 0.115(점프 초기 속도) | (0, 0.115, 2.2) | ×YPlusRate 1.0 |

데이터 비교(검증 아님): RSDB `WeaponInfoMain.Range`와 Free 전환 지점 수평거리

| 무기 | Range | Free 전환 z | 차이 |
|---|---|---|---|
| Shooter_Short_00 | 8.0 | 6.870 | 1.13 |
| Shooter_Blaze_00 / First_00 | 11.0 | 9.637 | 1.36 |
| Shooter_Precision_00 | 11.7 | 10.412 | 1.29 |
| Shooter_Normal_00 | 12.5 | 11.176 | 1.32 |
| Shooter_Gravity_00 | 13.3 | 11.767 | 1.53 |
| Shooter_Long_00 | 22.5 | 20.342 | 2.16 |

순서가 일치해 단위(유닛/프레임)와 파라미터 해석이 맞다는 정황은 되지만, `Range`의 정의(UI·AI용 여부)를 모르므로 동등성 근거로 쓰지 않습니다.

스텁·가정: 이 표의 위치는 `pos += vel` 근사(원본식은 판독 완료, 위 참조)이고 충돌 없음, 발사 방향은 고정, 플레이어 속도 가산(§5.5)은 0으로 둠(정지 상태 발사). 함수 단위 식 검증이며 전체 탄 동작 검증이 아닙니다.

## 11. 미확정 사항과 다음 근거

| 항목 | 필요한 근거 |
|---|---|
| ~~위치 적분·충돌~~ | **해소**(2026-10-02): §3.2 정정, [../physics/phive_controller.md](../physics/phive_controller.md) §6.3~6.8 [판독] |
| ~~충돌 콜백 58/59 대상, 컴포넌트 0x20/0x28/0x38~~ | **해소**: §3.3 (58 바닥, 59 벽·천장, 60 Ground 외) [판독]. 0x28 = 소멸 요청은 [추정] |
| 접촉 반응 시퀀서의 프레임 내 위치(첫 명중 age 1/2, 슬롯 19·21 순서, 바닥 탄 보관 도색 실행 여부) | 시퀀서 기반 `0x7103c7e4d8`의 실행 목록과 액터 계산 단계(슬롯 18/19/21 호출부) 순서 — physics §6.7 |
| 슬롯 59의 재질의 구 질의 세부(방향·길이), 슬롯 68(바디 없음 경로)·자식 탄 0x7101648824의 액터 이름 | `0x7101764ff8` 전체 분석 기준 재디컴파일(`state_redecomp.sh`), `0x7101648824`·`0x7101648650` |
| 분할 인덱스(생성 정보 +0x90)를 정하는 규칙 | 발사 함수 `0x71025817c8` 호출자의 `param_7` |
| 꼬리 길이 제한(TailLengthParam의 나머지 필드) | 슬롯 55 이후 그리기 경로 |
| OnlineVersusSetting 시드 → 대전 설정 객체 복사 경로 | BYML `RandomSeed0..3` 경유로 추정 ([network](../network/05_events_combat.md)) |
