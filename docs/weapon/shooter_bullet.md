# 슈터 탄 계산 (spl::BulletShooterBase)

슈터 계열 메인 무기(스플래시 슈터 등)가 쏜 잉크 탄 하나가 생성되어 날아가고 떨어지는 동안의 속도 계산, 상태 전이, 프레임 순서를 정리합니다. 도색 모양·데미지 값 계산은 각각 [../paint/paint_and_score.md](../paint/paint_and_score.md), [../combat/damage_hit.md](../combat/damage_hit.md)에서 다룹니다.

확정 수준: **[실행]** 원본 실행 / **[판독]** 원본 코드 판독 / **[데이터]** 데이터 / **[추정]** / **[미확정]**. 정정(2026-10-03): 이동 표 §10은 판독식 재구현이지만 총구·잉크·스플래시·생성 허용·꼬리 길이에는 원본 실행 근거가 있습니다. 실행/스텁 범위는 검증 기록 [solo_shooter.md](solo_shooter.md)에 모읍니다. 이전의 "모두 재구현, 원본 비교 없음"은 원본 실행 추가를 반영하지 않은 문서 상태였습니다. 2026-10-03 [r5 camweapon]: solo_shooter.md의 확정 내용(사격 게이트·잉크·PostDelay·총구·분할 번호·생성 허용)을 이 문서 §3.5·§5.5로 옮겼습니다.

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
| 디컴파일 | `analysis/decomp/bullet/BulletShooterBase_vt.c`, `BulletSimple_vt.c`, `bullet_move.c`, `WeaponShooter_vt.c`, `shot_spawn.c`, `analysis/decomp/weapon/ink_consume.c`·`shooter_ink_action.c`·`shotdir_spawnpos.c`, `analysis/decomp/completion/camera_weapon_pool.c`(0x71016e3af4), `analysis/decomp/r5_camweapon/actor_create.c`(0x7100f7f39c) |
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

**첫 명중의 age — 확정(2026-10-03, [r5 camweapon]) [판독]**: 첫 명중(첫 접촉 콜백) 때 age는 **0**입니다. 근거 사슬:
1. 프레임 순서 [판독, physics 재사용]: 탄 슬롯 18 → Phive(탄 바디 스텝 `0x7103b0a2bc`) → 접촉 큐 비우기(탄 슬롯 22 → 58/59/60) → 탄 슬롯 19/20/21. 같은 액터의 19 → 20 → 21은 한 작업 안에서 순서대로 돕니다([../physics/phive_controller.md](../physics/phive_controller.md) §6.7, SHARED `[r5 physics] 프레임 안 실행 순서 확정`).
2. 탄은 플레이어 슬롯 19(발사)에서 활성되고, 그 프레임의 단계 0(슬롯 18·Phive 스텝)은 이미 지났습니다. 따라서 탄의 첫 슬롯 18 이전에 탄 바디 스텝이 도는 일은 없습니다 [판독: 단계 0 → 단계 1 장벽 사슬].
3. 시작 처리가 age = −1을 쓰고(§3.3 위 정정), 첫 슬롯 18이 0으로 올린 뒤 `age == 0` 경로로 생성 속도를 그대로 setVelocity합니다. 생성 바디 속도는 0입니다(`0x71010036a8`).
4. 그러므로 바디가 처음 움직이는(또는 생성 위치에서 처음 겹침을 판정하는) 물리 스텝은 age 0 슬롯 18 직후이고, 그 접촉의 슬롯 22·58/59/60은 age 0을 읽습니다. 이후 접촉은 그 프레임 슬롯 18이 올린 값(n번째 이동 프레임 = age n−1)을 읽습니다.

데미지 감쇠(`ReduceStartFrame`)·반경 lerp·FriendThroughFrame은 이 age를 그대로 씁니다.

**생성 프레임의 슬롯19/20/21 — 해소(2026-10-03 6차, [r6 camweapon]) [판독]**: 새 탄은 **생성 프레임에 슬롯19/20/21을 돌지 않습니다.** 첫 실행은 다음 프레임 단계0(슬롯18)이고, 같은 프레임 단계1에서 슬롯19 → 20 → 21이 처음 돕니다.

```text
발사(플레이어 슬롯19, 단계1 그룹3) → 0x7100f7f39c → 예약 액터 활성 0x7100f7f6a4
  → 0x7103c7ea60(액터, 0xef): 액터+0x28 수면 비트 해제. 모두 풀리면 0x7103c88cd8(관리자 *0x71059a37c8, 액터)
      → 액터를 관리자 대기 목록 +0x460 + 위상(+0x4a8)·0x18 에 넣기만 함 (L[p][g] 작업 목록에는 넣지 않음)
프레임 구동 0x7103cdb41c: 0x7103c85624 → 0x7103c85b40(0x7103cdb5ec)
      → 대기 목록을 비우며 액터마다 0x7103c7f810(노드를 L[p][g]에 연결)
  → 그 뒤 0x7103c85fbc(0x7103cdb800) 가 L[p][g]로 이번 프레임 작업 그래프를 만듦
```

- 그래프는 만든 뒤에 실행되므로, 실행 중(단계1)에 활성된 탄의 노드는 그 프레임 그래프에 들어가지 않습니다. 대기 목록은 다음 프레임 구동의 `0x7103c85b40`에서 비로소 L[p][g]에 연결됩니다.
- 첫 단계0 처리 `0x7100f746b4`는 상태(+0x4d0) 1이면 `0x7100f7400c(…, 2)` 후 상태 2로 바꾸고, 같은 호출 안에서 바로 슬롯18 경로(vt+0x2d0)로 갑니다. 단계1 `0x7100f7493c`는 상태 2에서만 슬롯19~21(vt+0x2e0)을 돕니다.
- 근거 주소: 대기 목록 넣기 `0x7103c88cd8`(r5_physics/mgr5.c 74행~), 비우기 `0x7103c85b40`(0x7103c85bb0~0x7103c85f94), 구동 순서 `0x7103cdb5ec`(대기 처리) → `0x7103cdb800`(그래프 구성)입니다.
- 원본 실행은 하지 않았습니다(작업 그래프·작업자 스레드 미실행).
- 결과: 위 "첫 명중 age 0" 결론과 같습니다. 생성 프레임에는 이동·도색·소멸 처리가 없습니다.

**+0x12a == 1 검사 [판독 결과의 추론]**: 바닥/대상 콜백(슬롯 22 → 58/60)이 세운 `+0x12a = 1`은 같은 프레임 슬롯 21이 0으로 내리며 소멸을 요청합니다(위 순서 1). 다음 프레임 슬롯 18은 `+0x12a == 0`을 보므로, 위 순서에서는 슬롯 18의 `setVelocity(0)` 분기가 실행되지 않습니다. 원본 동작 재현에는 이 분기를 남겨 두되 결과에 영향이 없습니다.

**바닥 탄 보관 도색 — 확정(2026-10-03) [판독]**: 슬롯 22 → 58 → 84가 보관한 도색은 같은 프레임 슬롯 19의 슬롯 55(`0x71017510c0`)에서 실행되고, 그 뒤 슬롯 21이 소멸을 요청합니다(같은 액터의 19 → 20 → 21 순서). 따라서 바닥 탄은 **접촉 프레임에 칠하고 그 프레임 끝에 소멸 요청**됩니다. 이전 [미확정] ("슬롯 19와 21의 순서에 달려 있습니다")을 정정합니다.

> 과거 기록(정정 이유 보존): **첫 명중의 age** **[추정]**: age는 슬롯 18에서 이동 전에 증가하고 바디는 생성 때 속도 0이라, 이동으로 생기는 첫 접촉은 age 1 갱신의 물리 스텝에서 납니다. 접촉 처리(슬롯 22, 데미지가 age를 읽음)는 큐에서 나중에 실행되므로 그 사이에 다음 슬롯 18이 끼지 않으면 **age 1**, 끼면 2입니다. 슬롯 18의 `+0x12a == 1` 검사가 의미를 가지려면 접촉 처리가 슬롯 21 뒤·다음 슬롯 18 앞이어야 하므로 **age 1**로 봅니다. — 틀린 이유: age 초기값을 0으로 본 판(−1 정정 전)이었고, 접촉 처리 위치도 "슬롯 21 뒤"가 아니라 "물리 직후·슬롯 19 앞"이었습니다. 2026-10-03 앞 판의 "[미확정] 항상 0/1로 단정하지 않는다"도 위 순서 확정으로 해소했습니다.

`age == 1`에서 맞추는 크기는 플레이어 속도 가산이 포함된 발사 속도의 크기입니다(§5.5). 동작 [판독]: age 0 슬롯 54는 상태 머신 출력 대신 입력 속도를 그대로 쓰므로, age 1에 들어오는 +0x1118은 생성 속도이고 재정규화는 크기를 생성 정보 +0x48로 다시 맞추는 연산(f32 반올림 차이만 생김)입니다. 정정(2026-10-03): 이전 판의 "충돌 등을 되돌리는 용도로 보임 [추정]"은 용도 해석이라 명세에서 뺍니다. 웹은 위 연산을 그대로 하면 됩니다.

### 3.4 ShooterBase 추가 처리 (슬롯 54 재정의 `0x7101750d6c`)

1. BulletSimple 슬롯 54를 그대로 호출합니다.
2. `holdFrames >= 0`이면 표시용 값 +0x11c8~0x11dc를 `새값 + (이전값-새값)*0.6`로 감쇠 보간합니다(꼬리 표시 보간으로 추정).
3. **꼬리 점**: 탄 나이가 `BulletShooterTailLengthParam.DelayShotFrame`(기본 3) 이상이 되면 두 번째 상태 머신(+0x1210, 인터페이스 +0x1218)을 시작하고, 이후 매 프레임 같은 스텝 함수로 꼬리 속도(+0x11e0)를 갱신합니다. 꼬리 위치는 슬롯 55(`0x71017510c0`)에서 `pos + (old - pos)*0.88` 형태로 보간합니다.
4. **꼬리 길이 제한 — 확정(2026-10-03, [r5 camweapon]) [판독]+[실행]**: 슬롯 108(`0x7101753c00`)이 최대 길이를 돌려줍니다(TailLength 필드: +0x30 DelayShotFrame s32, +0x38 MaxLengthFrame s32, +0x3c StartMaxLength f32, +0x34 EndMaxLength f32, 각각 설정됨 플래그 +0x40..+0x43로 부모 사슬 조회).

   ```text
   t = f32(age - DelayShotFrame) / f32(MaxLengthFrame)     # age = 탄 +0x134
   if t >= 1:            return EndMaxLength               # 0x710175406c b.ge (NaN 은 거짓)
   if !(t > 0):          return StartMaxLength             # 0x7101754078 b.le (NaN 은 참 → Start)
   return Start + t * (End - Start)
   ```

   디컴파일된 탄 코드에서 찾은 소비처는 슬롯 47(`0x710174e90c`, 그리기 인스턴스 기록)입니다(vt+0x360 호출 검색. 같은 필드를 읽는 0x710188f364는 미판독): `꼬리 그리기 길이 = min(|꼬리 벡터|, 슬롯108())`를 인스턴스 버퍼(`*(인스턴스+0x10)+0x1f8`)의 `[idx]+4`에 씁니다(BulletShooterBase_vt.c 2938~2942행). 이동·충돌 함수(슬롯 18/54/56/58~60)는 슬롯 108을 부르지 않으므로 꼬리 길이 제한은 **표시용**입니다 [판독]. 원본 실행 `web/tools/r5_camweapon_tail_emu.py` 445/445 비트 일치(MaxLengthFrame 0·음수 경계 포함, 형식 검사·guard 스텁, 부모 사슬 미실행).

### 3.5 발사 흐름 — 플레이어·잉크액션·무기 쪽 [판독] (2026-10-03, [solo_shooter.md](solo_shooter.md)에서 옮김)

기준 객체: B = 플레이어 본체(Behavior+0x108), I = `spl::PlayerInkActionShooter`, S = 탄 생성 정보.

```text
플레이어 슬롯19 0x7102483134                        (프레임 안 위치: §3.3 순서, 탄 슬롯19/21보다 앞)
  → 입력/래치·형태 게이트 (0x7102485dc0 이후)
  → 0x7102486a40 → InkActionShooter 0x7102583008
      → 연사 타이머 0x7102551530 (../camera/aim_swerve.md §6.3)
      → 잉크 소비 0x7102492120 (§5.5)
      → 총구 0x7102552170, 조준 0x71024aff7c, 흔들림 (../camera/aim_swerve.md §6.2)
      → 탄 생성 0x71025817c8 / 생성 정보 0x71025823b0 (§5.5)
      → 회복 정지 0x7102353718, 자세 타이머 0x71024b28b0
```

**사격 게이트** [판독]+[실행(기존 에뮬)]:
- `H = B+0x4d4 ≥ 2 + PreDelay_Human`(B+0x4d4 = ZR 또는 래치 +0x530/+0x531 연속 프레임). H와 `B+0xa90 ≥ 6 + (PreDelay_Squid − SquidShotShortening)`을 모두 만족하면 메인 사격 후보입니다. 스플래시슈터는 인간 PreDelay 0, Squid − Shortening = 3이라 **누른 두 번째 프레임**, 인간 경과 **9프레임 이상**이 기준입니다. 1프레임 탭도 +0x530/+0x531 래치로 두 번째 프레임에 후보가 남습니다. B+0x4d4 입력 writer와 B+0xa90의 정확한 상태 집합은 [미확정].
- RepeatFrame 6의 타이머 초기 phase는 `1 − 1/6` = 0x3f555555, limit +0x80 = 999(생성자)입니다. 첫 유효 호출에 발사하고 이후 6호출 간격입니다.

**PostDelay 소비** [판독]: n = vt+0x118 PostDelayFrame(4). `0x71024b28b0`이 B 기준으로 `ad0 = max(ad0, 90+n−12)`, `ad4 = max(ad4, n)`, `ad8 = max(ad8, n)`, `adc = max(adc, n+4)`, `abc/ab8/ac4 = max(·, n)`, `4d8 = max(4d8, 20+n−12)`를 씁니다(특수 분기 제외). `0x7102583008`은 트리거 경로마다 ac4·ab8에 `max(기존, min(PostDelay, 6))`도 적용합니다. **PostDelayFrame 4는 회복 정지 값이 아닙니다.** 어떤 애니메이션이 각 필드를 읽는지는 플레이어 상태 문서 범위입니다.

**타이머 +0x4d8/+0x4ec/+0x524의 스택 플래그 공급원 — 진행(2026-10-03 6차, [r6 camweapon], [r5 player→weapon] 요청) [판독, 부분]**:
- 메인 계산 `0x7102475a54`는 0x7102481b08~0x7102481b44에서 `B+0x4d8 = max(·, [sp+0x3c8]·4)`, `B+0x4ec = max(·, [sp+0x3c9]·4)`, `B+0x524 = max(·, [sp+0x3ca]·4)`를 계산합니다. 같은 자리에서 +0x3cb~+0x3cf도 읽습니다.
- `sp+0x3c8..0x3cf`는 스택 객체(시작 sp+0x3a8, vtable 0x710562f3b8+0x10, 보조 vptr +8/+0x10/+0x18)의 **+0x20..+0x27 bool 8개**이고, +0x28은 u32입니다. 이 클래스의 슬롯은 같음 비교 `0x71024235c0`, 복사 `0x710242365c`, 직렬화 읽기 `0x7102423844`(bool 8칸은 각 1비트, +0x28은 2비트를 vt+0x48 비트 리더로 읽음)입니다.
- 0x7102476698이 8바이트를 0으로 지웁니다. 그 뒤 `[sp+0x4c0] == 1`일 때만 0x7102476778이 원천 객체(`[sp+0x2a8]`, 형식 정보 vt+0x18 비교 뒤 vt+0x20)를 vt+0x38(=복사)로 이 객체에 복사합니다. 함수 안에 이 칸의 다른 직접 저장은 없습니다.
- 따라서 공급원은 무기 코드가 아니라 **직렬화 가능한 8비트 플래그 레코드**(입력·네트워크 기록 계열로 보이는 형식)입니다. 무기 쪽 같은 프레임 값이 섞이는 경로는 이 함수 안에 없습니다 [판독].
- 남은 것 [미확정]: `[sp+0x4c0]`을 1로 만드는 곳과 `[sp+0x2a8]` 원천 객체의 정체(0x7102476428 `str x0` 직후 0x7102423b28, 0x71024246b4 호출 인자). [player] 범위로 넘깁니다.

**탄 생성 실패 = 예약 풀 고갈 — 확정(2026-10-03, [r5 camweapon]) [판독]**:

```text
0x71025817c8(I, …)                                  # 무기(I+0x40)·핸들(I+0x48, 세대 I+0x50) 검사 실패면 바로 반환
  0x71025823b0(...)                                  # 생성 정보 S 채우기 (§5.5)
  ok = 0x71028678b4(무기, 핸들 출력, S)
       ├ 무기+0x5e8 == 0 이면 0
       ├ 파라미터 핸들(+0x480..+0x4f0) 복사, 이름 = 무기+0x3c8
       ├ 0x71016e3af4(…) 생성 허용(아래) 거짓이면 0
       └ 0x7100f7f39c(*0x71058014e0 액터 관리자, 핸들, 이름, S, 0, 1)
            관리자+0x28 이름 트리에서 예약 풀을 찾고, 예약 액터 목록에서
            상태(+0x24) ∈ {3, 6} 이고 +0x28 < 0x200 인 첫 액터를 0x7100f7f6a4 로 활성
            없으면(풀 고갈·이름 없음) 0
  if !ok: 아래 뒤처리를 모두 건너뜀
  ok 이면: 활성 탄 핸들 목록(I+0x148, 개수 +0x158, 상한 +0x170, 넘치면 가장 오래된 항목 해제),
           +0x298 > 0 이면 추가 항목 등록,
           네트워크·관전 조건(0x71027e22bc 등)을 통과하면 무기+0x5f0 vt+0x18 로 xlink 액션
           "Fire"(Variable 아님) / "FireOn"(Variable, +0x98 ≥ 1) / "FireImpact"(Variable, +0x98 < 1) 재생
```

예약 수는 `WeaponShooterNormal` ActorReservation의 BulletShooterBase 32개입니다 [데이터]. 잉크 소비(0x7102492120)는 생성보다 먼저라 **생성이 실패해도 잉크는 이미 줄어 있습니다** [판독: 호출 순서]. 생성 허용 `0x71016e3af4`: 두 전역 모드 조건이 맞으면 ActorParam 키 비트테이블로 거부할 수 있고, 그 뒤 **local(S+0x6d) ≠ 0**, speed(S+0x48) < 0, 관리자 `*0x710580e340` == 0이면 즉시 1입니다. 원격 탄에서만 RSDB 행+8 거리·행+0xc 카메라 거리·시야 내적을 검사합니다. 이 함수에는 예약 수를 세는 명령이 없습니다 [판독]+[실행: 짧은 분기 9/9]. 모드 예외가 Lby_Lobby00에서 꺼지는 실제 전역 writer(`*0x71058e0460+0xc8`, `*0x710580e5e8+0x2c0`)는 [미확정]. 스플래시 탄(§5.4)은 다른 생성 경로 `0x7100f72aac → 0x710134a870`을 쓰며 실패 조건은 [미확정]입니다(5차 기록).

**스플래시 생성 실패 조건 — 해소(2026-10-03 6차, [r6 camweapon]) [판독]**: 스플래시 하나 생성 `0x71017540ec` 끝부분(0x7101754d14~0x7101754d9c)은 다음 순서입니다.

1. 생성 허용 `0x71016e3af4(…, S)`가 거짓이면 생성하지 않습니다. 메인 탄과 같은 함수이고, 로컬 탄이면 항상 참입니다.
2. 이름 해시 `0x71034fbdb4(S+0xa8 액터 이름, 길이, 0)`를 구합니다.
3. 컴포넌트 +0x170의 vt+0x78로 부모 액터를 얻어 `0x7100f72aac(부모, 해시, &S, 0)`을 호출합니다.

`0x7100f72aac`는 부모+0x4d4에 bit14를 세웁니다. 그리고 관리자 `*0x71058014d8`이 0이면 0을 돌려줍니다. 0이 아니면 `0x710134d6a4(관리자, 해시, 키 0)`을 부르고, 성공하면 부모 목록(+0x570)에 붙인 뒤 `0x710134a870`으로 초기화합니다.

`0x710134d6a4`는 다음 경우 0을 돌려줍니다(= 생성 실패).
- 관리자+0x60 해시 트리가 비었을 때
- 해시가 트리에 없을 때
- 해시 노드의 하위 풀 목록(+0x28/+0x30)에서, 키가 0이 아니면 같은 키를 가진 하위 풀만 보는데, 그 모든 하위 풀의 빈 칸 수(+0x70)가 0일 때

빈 칸이 있으면 첫 하위 풀의 빈 목록(+0x68)에서 하나를 꺼내고 수를 1 줄입니다. 반납은 `0x710134c5b8`(+0x70 += 1)입니다.

실패해도 스플래시 일정(남은 수 +0x11fc 감소)은 이미 진행된 뒤입니다. 실패는 그 스플래시 하나를 건너뛸 뿐입니다 [판독: 호출 순서].

하위 풀 크기와 `WeaponShooterNormal` ActorReservation의 BulletSplashShooter 32의 연결은 [미확정]입니다(다음: `*0x71058014d8`+0x60 트리 삽입 함수와 하위 풀 생성).

### 3.5.1 사격 입력 카운터의 로컬 writer — 7차(2026-10-03) [판독]+[실행]

기존 `impl/weapon.md`의 B+0x4d0 로컬 writer 미발견을 정정한다. 원본 입력 함수 `0x710249f494`의 **0x71024a0ce0~0x71024a0ec8**가 B+0x4d0을 기록한다. 기존 전체 디컴파일 `analysis/decomp/move/move_input.c`를 재사용하고 원본 명령을 대조했다. B+0x4d0은 단순 bool이 아니라 **허용된 메인 입력의 연속 호출 카운터(s32)**다. B+0x4d4와 별개다.

기준: B=본체, Sender=[B+0xa890], Side=[B+0xa678], Ink=[B+0x588]. Sender+0x54는 이미 우선순위 선택을 거친 메인 사격 입력이다. ZR 비트와 우선순위 생산은 기존 [player_state §6.1.1](../player/player_state.md)을 재사용한다.

```text
# 일반 메인 슈터 경로, 활성 특수 0x1a 예외는 이번 범위 밖
blocked = any(B[0x532..0x535]) || B[0x788] || B[0x784]
main = Sender[0x54] != 0
if main:
    main = (Ink == null || !(Ink.vt[0x130](Ink) & 1))
    if B.i32[0x4e0] > 0 && B.u8[0x4f0]: main = false
    if B.i32[0x518] > 0 && B.u8[0x528]: main = false
if 0x71024c9324(B+0xa5f9, B+0x925c, SM, ..., 1, 0) & 1:
    main = false
    B.u16[0x530] = 0
mode = Side.i32[0x38]
sideAllowed = mode in {0,3} || (mode == 2 && (0x710268662c(Side) & 1))
if !sideAllowed: B.u16[0x530] = 0
B.i32[0x4d0] = (!blocked && main && sideAllowed) ? B.i32[0x4d0]+1 : 0
```

명령의 `add w8,#1`은 32비트 덧셈이다. 포팅에서 bool 또는 임의 상한으로 바꾸지 않는다. 원본의 다른 입력 초기화 경로 `0x710249f958`는 B+0x4d0과 +0x4d4를 함께 0으로 쓴다 [판독]. 위 식은 정상 입력 writer 구간이며 함수 전체의 행동 차단·다른 형태 분기를 모두 실행한 것은 아니다.

같은 함수의 **0x710249fcb0~0x710249fdc0**에서 B의 `ab4/ab8/abc/ac0/ac4/ac8/acc/ae0/ae4/ae8/aec`를 각각 `max(s32값,1)-1`로 쓴다 [실행]+[판독]. 음수도 0으로 회복한다. 순서는 입력·오징어 요청 조건에서 감소 전 값을 소비한 다음 공통 감소 블록이다. 이는 `abc/ab4`의 단순 -1 근사에 하한 처리를 추가할 근거지만 **adc 감소 또는 a90의 상태 집합을 해소한 것은 아니다**. `ac4` 감소는 기존 판독을 실행 연결한 것이며 별도 신규 질문으로 세지 않는다.

검증 도구 `web/tools/r7_weapon_input_emu.py`: 입력 writer **1680/1680**(카운터와 530/531 래치), 감소 **1030사례×11필드=11330필드** 불일치0. 원본 분기를 실행하되 Ink vt+0x130, 24c9324, 268662c의 bool 반환은 경계 스텁으로 각각 변경했다. Sender+54는 입력으로 공급했고 특수 무기 활성은 없으며 R/A 카운터는0이다. 전체 입력 우선순위→발사→탄 생성 프레임 연결 실행은 아니다. 결과는 `analysis/completion/r7/weapon_input_emu.json`.


### 3.3.4 래퍼+0x28의 요청0 의미 — 8차(2026-10-03) [판독]+[실행]

정정: §3.3·§11의 “소멸 요청 [추정]”은 **액터 비활성 전이 요청0**으로 확정합니다. 원본은 여기서 객체를 free하지 않습니다. 요청 자체와 관리자가 활성 작업을 끊는 시점을 구분합니다.

래퍼0x7100f79574→0x7100f721b8(A,0)는 A+0x24 lifecycle4/5에서만 받습니다. A+0x28 bit11/9, A+0x4d4 bit0, A+0x4d0==3이면 거부합니다. 허용 시 A+0x4d4 bit0을 원자적으로 켜고 A+0x5c8=0을 저장해 컴포넌트34에 요청을 알립니다. bit14가0이면 **0x7103c7e8cc(A,0)**을 직접 호출합니다. bit14가1이면 원본이 형식키0x56b5ad00의 작업을 액터+0x350 메시지 큐에 넣습니다. 이 비동기 큐 분기는 기존0f721b8 판독을 재사용하며 이번 실행에서는 제외했습니다.

새 함수3c7e8cc는 lifecycle1..6에 대해 requestbit=`1<<(n&31)`을 A+0x28에 넣습니다. low8이0이고 lifecycle≠6이면 `(flags|requestbit)&~0x1800|0x800`; lifecycle6이면 `&~0x1000`입니다. 최초요청이면 관리자 대기목록에 깨우기0x7103c88cd8을 요청하고 A.vt+0xf0(A,n)으로 통지합니다. 같은 requestbit가 이미 켜지면 추가 큐 통지를 하지 않습니다.

다음 관리자 처리0x7103c7f810에서 요청0의 bit11(0x800) 경로는 **0x7103c897cc로 실행 작업을 분리**, 활성 액터 목록에서 제거, **A+0x24=6**, A.vt+0xc0을 호출합니다. 실제 게임 액터VT0x7105540368의+c0=**0x7103cc74dc**는 고유 컴포넌트 각각에 vt+0x58 종료 통지를 하고 액터vt+0x218 후처리를 수행합니다. bit9(삭제 큐·lifecycle7) 경로와 구별됩니다. 탄의 낙하/접촉 이후 “소멸”은 이 비활성화로 화면·갱신에서 빠지는 의미이며 malloc 객체 즉시삭제 의미로 쓰지 않습니다.

새 근거 `analysis/decomp/r8_camweapon/{actor_material.c,lifecycle.c,actor_end.c,body_actor.c}`; 기존 request·manager 원문은r6 actor_life.c/r5 mgr4.c 재사용. 원본 request0→flag setter→manager 전이 **80/80** 일치. 합성 lifecycle3/4/5/6·원본거부flags·pending/ownerphase를 검사하고 허용·flags·pendingbit·큐횟수, 순수flags0 허용시 lifecycle6/분리callback 순서를 대조했습니다. 스텁은 thread/mutex/enqueue·작업분리·최종callback이며 실제 컴포넌트 그래프·비동기 bit14 처리는 실행하지 않았습니다.

### 3.3.5 두 구 반경 setter 경계 — 8차(2026-10-03) [판독]+[실행]

기존VT0x710559f3f8의 **+0xd0=16cb590→wrapper+0x20(GroundOnly)**, **+0xd8=16cb5ec→wrapper+0x28(ExceptGround)** 이름 대응은 phive_batch1.c의 초기화16cb660을 재사용했습니다. 이번에는 새 **3a72f84** 전체 원본을 연결 실행했습니다. `delta=f32(new−shape+0xe4)`가 ±2^-23 안이면 그대로 두고, 그 밖(순서없는NaN 포함)은 radius setter로 전달합니다. setter의 순서: 최솟값=`world+0x21c`(월드없음0.05), 그 최솟값과 input 중 큰 값→2000 상한→결과NaN/∞이면1. +∞ input은 **2000 상한 적용 후 유한값**이므로1이 되지 않습니다. 설정 뒤 dirty처리는 shape flags와등록 상태에 따릅니다 [판독].

실행 `r8_camweapon_lifecycle_emu.py` sphere setter2개→3a72f84 **474/474** 비트 일치. shape dirtybit5를 켜 dirty큐를 제외하고 월드없음의 원본최솟값0.05 경계를 실행했습니다. 실제형상 cast·필터·월드리소스를 실행하지 않았습니다. 이 검증을 TOI 또는 stage충돌 전체 실행으로 넓히지 않습니다.

### 3.3.6 생성 헬퍼와 스플래시 벽 낙하 표 연결 — 8차(2026-10-03) [판독]+[실행]

`0x71015315d0`은 이름 hash로 등록된 **factory를 찾은 뒤 새 객체를 생성**합니다. 호출 순서는 `spl::KnockBackHelper` → `spl::BulletHitEffect` → `spl:DamageHelper`이고, factory는 각각 `0x7101e65a7c`(56바이트), `0x71016d994c`(64바이트), `0x7101e3d53c`(544바이트)입니다. 새 주소를 탄 +0x11b0/+0x158/+0x160에 저장하고 컴포넌트 intrusive list에 넣습니다. 세 번째 이름의 콜론 한 개도 원문 그대로입니다. registry 검색 자체와 객체 조회를 혼동하지 않습니다. 어느 단계에서 이름이 없으면 0을 반환하고 이미 생성한 앞 단계 객체·목록은 남습니다.

**2026-10-03 정정**: §8의 2026-10-02 문장은 DamageHelper를 탄의 헬퍼와 배타적인 HitPointHolder라고 해석했습니다. 원본은 동일 factory `0x7101e3d53c`의 새 객체를 탄 +0x160에도 소유시킵니다. 다른 액터에서 쓰인다는 사실은 이 생성 경로를 부정하지 않습니다. 이전 결론은 이 생성자를 실행하지 않고 클래스의 다른 사용처를 일반화했기 때문에 정정합니다.

`BulletSplashShooter`의 실제 VT는 `0x71055af4c8`입니다. 새 초기화 writer `0x7101811a74`는 공통 초기화 `0x7101762d44` 성공 후 탄 +0x170의 GameParameterTable `vt+0x80`에서 정확히 **WallDropMoveParam**, **WallDropCollisionPaintParam**을 찾습니다. `0x71038b3510`이 반환하는 세대 핸들을 +0x11c8/+0x11d8에, 그 핸들 +0xc의 generation을 +0x11d0/+0x11e0에 저장합니다. VT 슬롯62 `0x7101812574`는 두 쌍을 그대로 출력하고 1을 반환합니다. 슬롯61 `0x7101646b10`의 벽 낙하 생성정보 작성은 이 슬롯62를 호출하므로, 표의 이름이 있다는 사실을 넘어 **실제 슬롯61이 읽는 표**까지 연결되었습니다. 이름 검색에 실패하면 해당 포인터만 0으로 지우며 generation은 보존합니다. 공통 초기화 실패이면 두 필드는 그대로 두고 0을 반환합니다.

검증: `web/tools/r8_camweapon_helper_splash_emu.py`의 helper registry 존재 여부 8조합×16회 **128 PASS**, 벽 낙하 초기화·존재 여부·이전 값 **128 PASS**, 불일치 0. 원본 hash/tree/factory/list 저장 및 `1811a74→38b3510→1812574`를 실행했습니다. 메모리 할당·libc memset과 표의 이름 lookup은 경계 스텁이고, 핸들은 사전 할당한 정상 레코드를 공급했습니다. registry 전역 등록 생성자, 핸들 pool 느린 경로·mutex, 벽 낙하 탄의 실제 시뮬레이션은 이 실행에 포함하지 않습니다. 근거: `analysis/decomp/r8_camweapon/helper_splash.c`, `splash_bind.asm`, 기존 `bullet/BulletShooterBase_vt.c`, `analysis/completion/r8/weapon_helper_splash_emu.json`.

### 3.3.7 생성 정보의 팀·반복 필드 writer — 8차(2026-10-03) [판독]+[실행]

새 공통 binder `0x7102552da0`의 실제 호출자는 슈터 주 VT `0x71056376a0` 슬롯55(+0x1b8) `0x710258801c`입니다. 원본 ABI는 `(I, S)`이며 binder에는 `(S, I+0x2c0, I+0x2c8, I+0x38)`을 넘깁니다. Behavior가 있으면 `S+0x2c = [ [[Behavior+0x108]+8] +0x668 ]`, 즉 발사 플레이어 액터의 팀 번호를 **s32 그대로 복사**합니다. Behavior가 없으면 기존 S+0x2c를 보존합니다. 0~2로 clamp하지 않습니다. 같은 호출에서 Actor+0x798와 배치 기록+0x39로 소유 액터 ID(S+0x1c)를 만들고, 컴포넌트가 있으면 owner type(S+0x10/+0x14/+0x18)을 기록합니다. 마지막 Weapon vt+0x238의 실제 슈터 대상은 `0x7102865f18` **RET**이므로 이 슬롯에서 반복 필드를 추가 변경하지 않습니다.

**정정(2026-10-03)**: §4.5의 팀 필드는 이전에 슬롯15/106에서 배열 인덱스로 쓰인다는 소비만으로 [추정]이었습니다. 이제 위 원본 writer와 실제 슈터 호출을 연결했습니다. -1/3의 무효 처리와 0~2 팀 배열 선택은 기존 소비자 `0x71016444ec`, `0x71013405e0`, `0x7101753bb4`의 근거를 재사용합니다. writer가 잘못된 값을 교정한다는 해석은 하지 않습니다.

생성 정보 S의 +0x91/+0x92/+0x94는 I의 동명 오프셋과 다른 필드입니다. `0x71025817c8`의 `0x7102581898/0x71025818d0`은 halfword 0x0100을 S+0x91에 써 **S91=0, S92=1**로 초기화하고, `0x71025818d4`는 **S94=-1**을 씁니다. 실제 `0x71025823b0`의 `0x71025827d8..0x71025827fc`는 `0x7102580354(I)`가 참일 때만 **S94=I9c**, **S92=u8(I80)**으로 바꿉니다. 이 조건은 선택된 WeaponShooterParam의 **TripleShotSpanFrame(+0x80)>0**입니다. S91은 이 블록에서 바꾸지 않습니다. 스플래시슈터의 TripleShotSpanFrame=0(원본 파라미터)이므로 1인 연습의 해당 생성 필드는 **0/1/-1**을 유지합니다 [판독]+[데이터]. S91을 ExtraInfo 열거 VariableRepeat(8)에 대응시키는 소비자는 기존 `0x7101753b90`이며, 발사 공유 경로에서 실제 VariableRepeat를 켠다는 근거는 없습니다.

I80은 RepeatTimer(I+0x68)의 +0x18 **limit**입니다. 실제 factory `0x7102580190`의 `0x7102580230..0x7102580244`는 999를 씁니다. reset `0x7102582e3c`는 I68..I7f를 지우고 I80은 보존합니다. I9c는 reset에서 0이고, `0x710258295c` 말미 `0x7102582dc8` 주변에서 TripleShotSpanFrame>0 && I98>0이면 1 증가한 뒤 I98을 0으로 지웁니다 [판독]. **미확정 경계**: TripleShotSpanFrame>0인 다른 무기의 I80 limit 재설정 writer·그 원본 파라미터명은 아직 확보하지 못했습니다. 오프셋+80 저장 검색은 보조 인터페이스(+30), 타이머(+68) 상대 주소를 놓칠 수 있으므로 부재 증명으로 쓰지 않습니다. 다음은 슈터 초기 바인드 `0x7102395340`의 I68 타이머 설정 소비/호출자를 보되, 다른 무기의 실제 동작은 이번 범위에서 제외합니다. 이 경계는 TripleShotSpanFrame=0인 스플래시슈터 생성값 결론을 바꾸지 않습니다.

검증: `web/tools/r8_camweapon_geninfo_emu.py`, 결과 `analysis/completion/r8/weapon_geninfo_emu.json`. 원본 `258801c→2552da0→WeaponShooter vt238 RET`의 팀 6값×owner 2종×기존값16종 **192/192** 일치; 원본 조건부 writer→2580354의 Span 4값×shot 3값×limit 4값 **48/48** 일치(불일치0). ActorID pack146cb20, 형식 검사 및 자원 핸들 공급은 경계 스텁이고 조건부 실행은 정상 기본 자원(I38=null, 가변 파라미터 분기 제외)을 공급했습니다. 전체 발사 함수·자원 로더·풀/생성 복사는 실행하지 않았습니다. 근거 원문 `analysis/decomp/r8_camweapon/geninfo_common.c`, 기존 `analysis/decomp/camera/batch1.c`·`weapon/shooter_ink_action.c`, 원본 생성자 ASM입니다.

### 3.3.8 조준 예측 단계 수의 원본 이름 — 8차(2026-10-03) [판독]+[실행]

조준 예측 `0x7102548c3c`가 PlayerInkActionFree **I+0x40**의 유효 세대 핸들에서 읽는 단계 수는 **spl__WeaponFreeParam.ShotGuideFrame**입니다. 실제 factory `0x71027f3f64`는 0x38바이트 객체(VT `0x710564b668`)를 만들고 P+0x30에 **s32 8**, P+0x34에 설정됨 플래그 0을 씁니다. `0x71027f4670`의 원본 이름은 `spl__WeaponFreeParam`입니다. 원본 메타데이터 reader `0x71027f4018`은 정확히 **ShotGuideFrame** 이름, P+0x30의 int, P+0x34의 bit0, 필드 index0, 원본 기본값 포인터 `0x7104aa1b34`(8)를 연결합니다 [판독].

타입 연결은 vtable 값만으로 판정하지 않았습니다. predictor의 `0x71025490e8/0x7102549104`가 검사하는 고유 RTTI 싱글턴은 **0x71058bd9d8**이며, 실제 WeaponFreeParam의 RTTI 함수 `0x71027f4338`이 동일 객체 주소와 비교합니다. `0x710555cdc0`는 여러 RTTI 싱글턴이 공유하는 메타데이터 vtable입니다. 그 값이 같다고 파라미터 타입까지 같지는 않습니다.

**2026-10-03 정정 근거**: combat/damage_hit.md §6.7의 이전 후보 `0x71010aa70c`는 factory가 아니라 `0x71010aa5dc` 내부 ADD 명령입니다. 이 함수의 필드 reader는 **FadeType**, RTTI는 **0x71058122a0**입니다. 따라서 이를 단계 수 파라미터의 이름·factory로 연결한 결론은 잘못된 RTTI 동일시였습니다. 기존 후보의 원문은 `analysis/decomp/r8_camweapon/prediction_param.c`에 보존하고, 올바른 클래스는 `shotguide_param.c`로 구분합니다. 이름이 비슷한 타 무기 `ShotGuideShooterFrame`도 이 I+0x40 객체의 키가 아닙니다.

원본 소비 구간 `0x71025490c0..0x7102549230`은 I+0x40 핸들의 +0xc와 I+0x48 generation 일치 여부를 확인합니다. P+0x34 bit0이 켜져 있으면 P+0x30을 사용합니다. 꺼져 있고 P+0x10 연결과 P+0x18 핸들의 P+0x20 generation이 유효하면 실제 RTTI 검사 뒤 부모 객체를 따라갑니다. 명시 플래그가 켜지거나 부모 연결이 끊어진 객체의 +0x30을 `0x7102549228/0x710254922c`에서 q.steps(sp+0x88)에 복사합니다. 임의로 0~60 또는 양수로 clamp하지 않습니다 [판독]. 이후 예측 루프 `0x710175779c`는 기존 §3.3·combat §6.7 근거를 재사용하며 이번에 다시 실행한 것으로 세지 않습니다.

검증 `web/tools/r8_camweapon_shotguide_param_emu.py`, JSON `analysis/completion/r8/shotguide_param_emu.json`: 원본 factory/getName/RTTI/metadata **64 PASS**, 단계 수 소비 구간 **512 PASS**, 불일치0. 같은 메타 vtable을 쓰는 FadeType RTTI는 원본 타입 검사에서 거부됨을 확인했습니다. 자체·부모 플래그, 부모 세대의 유효/무효와 64개 s32 비트값을 조합해 q.steps의 원본 비트를 대조했습니다. 메모리 할당 및 metadata 조회 callback만 경계 스텁이며 실제 RTTI 함수는 실행했습니다. 정상 I+0x40 핸들과 부모 레코드를 합성했으므로 **I+0x40의 실제 설정 writer, 전체 2548c3c/175779c 궤적, 자원 로딩·Havok 질의는 실행하지 않았습니다**. 8은 factory 기본값이며 모든 실행 시점의 오버라이드 값이 8이라는 결론은 내리지 않습니다. 다음은 I+0x40 핸들 setter와 자원 binder입니다.

### 3.3.9 실제 슈터의 조준 표시 호출 — 8차(2026-10-03) [판독]+[실행]

**2026-10-03 정정**: §3.3.8의 Free 타입·함수 판독은 공통 Free 경로의 사실입니다. 1인 스플래시슈터의 실제 활성 객체는 Shooter이고, B+0x588이 가리키는 보조 vtable **0x7105637898의 +0x60 = 0x7102586aa0**입니다. 기존 combat §6.7이 이 호출을 Free `2549b38→2548bec`에 곧바로 연결한 것은 파생 클래스 override를 빠뜨렸습니다. 실제 슈터는 `24c0fbc→2586aa0(this−0x30)`를 호출하며, show=0이면 I+0xf0의 가운데/히트마커와 I+0x120의 바이어스를 정지합니다. show=1,predict=1이면 **2585bd8** 예측 뒤 **258683c** 표시 갱신, show=1,predict=0이면 **25864e4** 뒤 같은 표시 갱신입니다. 보조 vt+0x158 **253c9a0은 실제 RET0**이므로 이 슈터에서는 h 반전이 없습니다.

스플래시슈터의 예측 단계 수는 **I+0x48(일반)/+0x58(가변)**의 WeaponShooterParam **P+0x64 = ShotGuideFrame**, 설정 플래그 **P+0x96 bit0**입니다. 가변 자원이 활성이고 I+0x98>0, I+0xac==0일 때만 +0x58을 고르고, 그 밖에는 +0x48을 고릅니다. `25860c4..2586264`는 세대 핸들과 원본 RTTI `2813b24→1643a58`을 확인하고 부모 세대/명시 플래그를 따라간 뒤 +0x64를 q.steps(sp+0x80)에 복사합니다. 이름·공장 기본값8은 기존 reflection `analysis/param_reflect/spl__WeaponShooterParam.json` 및 FUNCS의 `2811104` 판독을 재사용하며 새 분석 수로 세지 않습니다. Free의 I+0x40/P+0x30을 실제 슈터 필드로 쓰면 안 됩니다.

정상 Main 슈터이고 활성 특수가 없는 구간의 **원본 표시 식**은 아래와 같습니다(B=플레이어 본체, G=[B+0xa898] PlayerShotGuideXLink).

```text
h = (s32(B+0xab8) <= 0) && (
    s32(B+0x4e0)>0 || B532 || B533 || B4f2 ||
    s32(B+0x518)>0 || B534 || B535 || B52a)
show = predict = !h && !b && (G+0x30 != 0)
```

b의 원본 항은 T+8>0(T=B+0xd58), PlayerDemo+0x34==0, PlayerPeriscope+0x38!=0 또는 +0xb0!=0, 리스폰 관리자 조건, PlayerVehicleSpectacle의 유효 연결 대상, PlayerPipeline+0x38!=0입니다(전체 원문은 기존 `r6_combat/c1.c`). 이번 실행은 관리자 null·차량 handle generation=-1을 공급하고 나머지 6개 gate를 각각 변경했습니다. b에 의미를 보태거나 B+0x784(오징어 요청)·메인 ZR 카운터 B+0x4d0을 위 h 식에 임의로 넣지 않습니다. 공격 입력의 정확한 raw 필드와 원본식이 근거이며 부수적인 메뉴/특수 실제 동작은 범위 밖입니다.

**G+0x30 생산자** 신규 `267f934(G,enabled)`는 rawenabled bit0를 G+0x30에 쓰고 XLink 사용자 `[G+0x38]+0xf8`의 **bit12를 enabled의 반대로** 씁니다. 이전에 enabled가 켜졌고 새 값이 꺼지면 G+0x48 ring의 유효 세대 이펙트를 정지하고 G+0x54/+0x58을 0으로 비웁니다. 기본 상태에서 enabled = **B+0x1054!=0 && s32(B+0x1058)==0**이며, down timer/행동 불가 분기에서는0, Bf34∈{2,3,4} 등의 특수 분기는 원문의 숫자를 보존합니다. B1054/B1058의 메시지 writer는 기존 PlayerBehavior `234f518`의 메시지 **0x6c2b6a01**, 새로 연결한 `234ffa8/234ffb0`에서 payload+0x40 byte/+0x44 s32를 그대로 복사합니다. payload의 게임상 이름·모든 실제 생산자는 아직 미확정입니다. Bf34 상태명도 여기서 새로 확정하지 않습니다.

실제 `258683c`는 I+0xcc 예측 종류가 바뀌거나 중앙·히트마커 핸들 둘이 모두 무효일 때 **Shooter_Center / Shooter_HitMarker**를 `2677578`에, 바이어스 종류가 바뀌거나 양쪽 핸들 둘이 모두 무효일 때 **Shooter_BiasLeft / Shooter_BiasRight**를 `267d090`에 보냅니다. 유효 핸들과 같은 종류면 새 발생을 생략하고 위치만 갱신합니다. 종류0/1/2→NoHit/HitConstant/HitEffective 키·ELink 리소스 대응은 기존 r5 근거를 재사용합니다. 이 예측 마커를 실제 명중 뒤 `16d99f4/16d9c60` HitEffect 이벤트와 혼동하지 않습니다.

검증 `r8_camweapon_shooter_shotguide_gate_emu.py`, JSON `shooter_shotguide_gate_emu.json`: **24c0fbc 전체→267f934→실제Shooter vt→258683c 876 PASS**, 실제 단계 수 소비 구간 **512 PASS**, 불일치0. 입력8bit×타이머−1/0/1, enabled/대기값/6gate/종류0·1·2를 대조했습니다. `24c7234` 및 Ink-vt140의 반환은 경계 스텁(허용), 2585bd8은 예측 종류를 공급하는 경계 스텁이며 XLink 발생·위치·정지는 요청을 캡처했습니다. 실제 renderer·전체 탄/Havok·SDK 입력 생산은 실행하지 않았습니다. 원본 RTTI는 실행하고 초기화 guard는 초기화된 정상 객체로 공급했습니다. 이 실행에서 **리스폰/차량 전체·ring 정지의 비어 있지 않은 목록·자원 오버라이드 생산자**까지 해소했다고 넓히지 않습니다. 다음은 `234f518` 메시지6c2b6a01의 실제 sender, `24c7234`의 정상 사격장 입력 연결과 원본 ELink 실행입니다.

### 3.3.10 실제 명중 요청 패킷의 접촉 선택 — 8차(2026-10-03) [판독]+[실행]

`16d99f4`의 실제 접촉 선택부터 `16d9c60`의 HitEffect 요청 생성까지 원본을 연결 실행했다. 이 절은 §3.3.9의 조준 예측 표시와 별개다. 결과 enum이 0이면 두 함수 모두 바로 돌아온다. 1~7은 접촉의 blocking bit가 없어도 첫 접촉으로 요청한다. 목록에서 P+0x68 bit1이 켜진 **첫 접촉**이 있으면 그 접촉을 택하며, 없으면 목록 첫 접촉을 쓴다. 비어 있는 목록을 안전하게 무시하는 분기는 이 함수에 없으므로 호출자가 유효 접촉을 제공해야 한다.

점 wrapper 두 side byte의 같음 `equal`과 pair record+8 bit0 `rb`를 비교한다. `rb == equal`일 때만 `position = P.position + P.depth * P.normal`로 보정하고 material=P+0x38, 나머지는 원래 위치와 P+0x48이다. `info+0x10`의 X가 NaN이면 원본 `12d4f8c`가 wrapper+0x0c(equal) 또는 +0x18(unequal)의 캐시 법선을 복사한다. X가 NaN이 아니면 info 방향 Vec3를 그대로 복사한다. 위치 보정의 float32 곱셈·덧셈 순서를 포함해 1,024건에서 패킷의 초기화된 모든 필드가 비트 일치했다. 목록·법선은 합성 입력이고 실제 Havok 접촉 생산자는 이번 실행 경계 밖이다.

| 요청 offset | 원본 내용 |
|---|---|
| +0 / +0x0c / +0x18 | 접촉 위치 / 선택 방향 / 호출자가 준 이동 방향 Vec3 |
| +0x24 / +0x28 / +0x2c | material / DamageResultType / HitEffectorType |
| +0x30 / +0x34 / +0x38 | info+0x20 / 소유 플레이어 번호 / -1 |
| +0x3c / +0x3d / +0x3e | 접촉 도색 가능 / 탄 vt+0x208 bit0 / SpawnInfo+0x6d |
| +0x40 / +0x48 / +0x50 | info+0x1c / 선택 참조 ptr / info+0x30 |

스플래시슈터의 탄은 실제 VT55a5030+0x208→`1649ba0`의 true 반환, actor wrapper VT5540810+0x78→`0f796ec`의 actor+8 반환을 실행했다. actor+0x208이 null이면 SpawnInfo+0x1c ID를 사용한다. ActorID→플레이어 인덱스 가상 호출은 0 공급 경계이고, 이후 `26437d0`은 실제 1인 SceneSetting ring을 읽어 요청+0x34=0을 냈다. Shooter40의 HitEffectorType=1 및 critical extra=17에서도 같은 값은 기존 RSDB/r6 reader 근거를 재사용한다. 기존 36,900건 데이터 reader 결과를 새 성과로 다시 세지 않는다.

추가 2,688건(7모드×384)의 원본 `12d68cc→12ed800→2c71e50→12ac5e0` 연결에서 도색 가능 플래그를 확인했다. body+0x230 없음, PaintInfo+7 disabled, kind0은 false다. PaintInfo kind2인 ObjPaint 입력은 결과 kind3이며, material null 또는 material+0x0e bit2=0이면 true, bit2=1이면 false다. material의 다른 bit는 이 분기에 영향이 없다. 원본이 material null을 true로 취급하는 것도 그대로 보존한다. RTTI vt+0x28 true와 shape native/fallback vtable, SDK mutex는 명시적인 경계 스텁이다. 실제 FieldRigidBody 타입 대응과 지형 ColPaint 결과 kind2 경로를 이 실행으로 확정하지 않는다.

근거: `analysis/decomp/r8_camweapon/hit_direction.c`(새 12d4f8c), 기존 combat/batch1·2.c/phys4/p4_resultplayer.c/r5_paint/r5_a.c 및 r8_physics/material_reader.c. `web/tools/r8_camweapon_hit_packet_chain_emu.py` → `analysis/completion/r8/hit_packet_chain_emu.json`: **1,024+2,688 PASS, 불일치 0**. `27b4704`에서 요청을 캡처했으므로 큐/컨트롤러의 실제 방출·최종 화면 히트마커 조건은 이 절에서 해소했다고 하지 않는다. nonnull 참조 ptr의 수명 관리도 이번 fixture에서는 제외했다.

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
| +0x108 | ptr | 생성 정보 객체 | 생성 경로: 채우기 `0x71025823b0` → 예약 액터 활성 `0x7100f7f6a4`에 인자로 전달 [판독]. 탄 +0x108에 저장하는 명령은 [미확정] | 여러 곳 |
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
| +0x11fc | s32 | 남은 스플래시 수(생성마다 1 감소, 0이면 생성 끝 — §5.4 [판독]+[실행]) | 슬롯 15, 슬롯 56 | 슬롯 56, 스플래시 시드 |
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
| +0x2c | s32 | 팀 번호(0~2, -1/3은 무효) | §3.3.7 원본 writer: 발사 플레이어 Actor+668 복사, 원본192PASS **[판독]+[실행]** |
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
   탄 관리자는 GOT `0x7105797f18` → 포인터 변수 `0x7105850620`이 가리키는 객체이고, 초기화 `0x71016e2fd4`가 +0x124~+0x130에 시드 a~d를 넣은 뒤 `+0x120 = 13a + 59b + 71c + 97d`로 정합니다. 원천 객체가 없으면 a~d = (1,2,3,4)이고 +0x120 = 10입니다 **[판독, network 담당]**. 원천은 `[[*0x71058e42f8(GOT 0x7105790fc0)]+0xc8]+0x6548`(대전 설정 객체)의 +0xa4..+0xb0(RandomSeed0..3)입니다 [판독: net_sync.c 0x71016e2fd4]. a~d는 송신 권한 기기가 전역 xorshift128로 만든 u32 4개를 `spl::OnlineVersusSetting`(+0x238~+0x244)으로 배포한 값입니다. 배포는 [판독], 로비가 이 값을 `[[*0x71058e42f8]+0xd0]+0x6548`의 +0xa4~+0xb0으로 복사하는 것(`0x7102d60098`)은 [실행]으로 확인했습니다. 다만 탄 관리자 초기화는 `+0xc8` 쪽 객체를 읽으며, `+0xd0 → +0xc8` 복사 지점은 아직 못 찾았습니다 **[미확정]**. 2026-10-03 시도 [r5 camweapon]: (1) `ldr xA,[xB,#0xd0]` 뒤 12명령 안 `str xA,[xB,#0xc8]` 전수 스캔 — 라이브러리 1곳(0x710383d234)뿐, (2) `ldp`/`stp` 교환 패턴 0건, (3) `x0 = [xB,#0xc8]`, `x1 = [xB,#0xd0]` 인자 호출 0건, (4) GOT 0x7105790fc0 참조 중 +0xc8·+0xd0을 함께 읽는 12곳은 모두 `+0xd0` 묶음을 잠금(G+0xf8) 아래 읽는 곳이었습니다(`analysis/r5_camweapon/scan_swap*.py`, `scan_gc8d0.py`, `scan_copy.py`). 다음 근거: 게임 설정 싱글턴 G(0x71058e42f8)의 묶음 교체 메서드(씬 전환 때 +0xc8을 다시 만드는 경로, G+0xf8 잠금 사용 함수 전수). 사격장(Lby_Lobby00)의 매치 시드 후보는 **원천 객체 없음 → +0x120 = 10**, **기본 생성 객체(RandomSeed 1,0,0,0) → +0x120 = 13**, **로비가 받은 무작위 값** 셋 중 하나이며 어느 것인지 [미확정]입니다. (이 문단은 2026-10-03 5차 기록입니다. 아래 6차 해소로 대체합니다.)

   **`+0xd0 → +0xc8` 이동과 사격장 시드 — 해소(2026-10-03 6차, [r6 camweapon]) [실행]+[판독]+[데이터]**:
   - G = `*0x71058e42f8`은 `SplSceneSetting`(vtable 0x710566c678, 이름 함수 0x7102af15a8)입니다. G 슬롯33 `0x7102af0df0`이 묶음(0x6570 B, vtable 0x710566c038) 두 개를 만들어 `+0xc8`(현재), `+0xd0`(다음)에 두고, 각 묶음의 슬롯10 초기화가 대전 설정 V(`+0x6548`, vtable 0x710566c488)를 할당합니다. V의 RandomSeed0..3 기본값은 (1, 0, 0, 0)입니다.
   - 복사 지점: 씬 전환 작업(`Transition`, vtable 0x71056a7be0) 슬롯42 `0x7103029330`의 끝부분 `0x7103029c44..0x7103029ca8`입니다. 코드는 `ldp x20, x21, [G, #0xc8]`로 C8·D0을 한 번에 읽습니다. 그리고 두 묶음의 형식 정보(vt+0x18)가 맞으면 `C8.vt+0x38(C8, D0.vt+0x20())`을 호출합니다. 이 호출이 묶음 복사 `0x7102ae5810`이고, 하위 객체 10개(+0x30, +0x6518..+0x6568)를 각자 vt+0x38로 복사합니다. 5차 스캔이 놓친 이유는 `ldr` 두 번이 아니라 `ldp` 한 번으로 두 칸을 읽고 가상 호출로 넘겼기 때문입니다.
   - 전수 확인 [판독]: GOT 0x7105790fc0의 G 참조 전부를 함수 단위 자료 흐름(`ldp` 포함)으로 추적했습니다(`web/tools/r6_camweapon_gscan.py`). C8 묶음에 쓰는 곳은 위 `0x7103029ca8` 한 곳뿐입니다. G 경로로 D0의 V+0xa4..+0xb0(RandomSeed)에 쓰는 곳은 두 곳입니다. 하나는 `0x7102d60150..0x7102d60174`(온라인: OnlineVersusSetting 수신값)이고, 다른 하나는 `0x71030295cc..0x71030295e4`(같은 전환 함수의 오프라인 분기)입니다.
   - 오프라인 분기 [판독]+[실행]: 들어가는 씬에 태그 `Scene_Versus`가 있고(`0x7102b57100`, Tag.Product 비트표) `GameNet+0x195 == 0`이면, D0 V의 RandomSeed0..3에 **전역 xorshift128 상태 4워드**(`*0x71057906a0` = 0x7105997950)를 그대로 복사합니다. 이때 next()는 부르지 않습니다. 온라인(`+0x195 ≠ 0`)이면 이 분기에서는 쓰지 않고 OVS 수신값을 씁니다.
   - **사격장(`LobbyVersus` 씬, Tag 행 4272)**: 태그는 `SceneAttr_Customize, SceneAttr_ExtraRumbleConstant, SceneAttr_News, Scene_AroundPlaza, Scene_AutoProfile, Scene_Lobby, Scene_PlazaRc`이고 `Scene_Versus`가 없습니다 [데이터]. 따라서 로비로 들어갈 때는 D0 시드를 새로 쓰지 않고, C8 ← D0 복사만 합니다 [실행]. 결론은 다음과 같습니다.
     - 부팅 뒤 대전을 거치지 않고 로비에 들어오면 D0 = 기본값 (1, 0, 0, 0)이므로 **탄 관리자 +0x120 = 13**입니다.
     - 대전을 마치고 로비로 돌아오면 **직전 대전의 시드**가 그대로 남습니다. 오프라인 대전이면 그 전환 때의 전역 xorshift128 상태 4워드, 온라인 대전이면 OVS RandomSeed0..3입니다.
     - 후보 "10"(V 없음)은 G 슬롯33 이후에는 생기지 않습니다. 묶음과 V는 같은 호출에서 함께 할당되기 때문입니다([실행] 1단계). 탄 관리자 초기화 `0x71016e2ffc`는 C8 자체를 null 검사 없이 역참조하므로 C8은 항상 있다고 전제합니다 [판독].
   - 원본 실행 `web/tools/r6_camweapon_seed_emu.py`(결과 `analysis/completion/r6/camweapon_seed_emu.json`):
     - (1) G 슬롯33 구간 `0x7102af0df0..0x7102af0f14`를 실행해 실제 묶음 2개와 V를 생성했습니다. vtable, 기본 시드 (1,0,0,0), Time 180을 확인했고, 탄 관리자 초기화 구간 `0x71016e2fd4..0x71016e307c`의 결과는 +0x120 = 13입니다.
     - (2) D0 시드 64건(경계 4건과 무작위 60건)에서 복사 구간 → 탄 관리자 초기화를 이어 실행했습니다. C8 시드, 관리자 a..d, `+0x120 = 13a+59b+71c+97d`(u32 wrap) 독립 식이 **64/64** 일치했습니다.
     - (3) `0x710302946c`부터 판정·오프라인 분기를 실행했습니다(태그 이름 이진 탐색 `0x71038c4a00`과 판정 `0x7102b57100`은 원본, 태그 표는 Tag.Product 데이터를 런타임 구조 모양으로 채움). 결과는 LobbyVersus 온·오프라인 모두 미기록, Vss_Yagara 오프라인은 전역 상태 4워드 기록, 온라인은 미기록, Plaza는 미기록입니다(6/6).
     - 스텁: operator new(버퍼), memset/memcpy(실제 동작), `__cxa_guard_acquire/release`, 그 밖 PLT 0 반환, 씬 객체 반환 `0x7101323040`(가짜 씬 +0x224 = 태그 행). 검증하지 않은 범위: 전환 함수 전체 흐름, `0x7102b3d350`(D0+0x30), 실제 부팅 순서(G 슬롯33 호출 시점), 태그 행 번호 +0x224의 writer.
   - 남은 것 [미확정]: 사격장 탄 시드의 다른 입력인 **발사 GameFrame**(GameFrame+0x148)의 로비 시작값. G 경로가 아닌 V 복사(리플레이 `0x71029e7f10`의 C8 → 리플레이 사본, 전환 case 4의 리플레이 → D0)는 리플레이 재생 전용이라 사격장 1인 연습 범위 밖입니다.

   따라서 탄 시드는 `매치 공통값(13a+59b+71c+97d) + 발사 GameFrame`입니다 **[판독]**. 매치 공통값은 위처럼 **[실행]**으로 정해집니다.
   `sead::Random` 방식(xorshift128)으로 상태 4개를 만듭니다.
   ```
   s0 = (seed ^ seed>>30)*0x6c078965 + 1
   s1 = (s0 ^ s0>>30)*0x6c078965 + 2
   s2 = (s1 ^ s1>>30)*0x6c078965 + 3
   s3 = (s2 ^ s2>>30)*0x6c078965 + 4
   next(): t = s0 ^ (s0<<11); s0=s1; s1=s2; s2=s3; s3 = t ^ (t>>8) ^ s3 ^ (s3>>19); return s3
   float01(): f32 비트 (next()>>9 | 0x3f800000) - 1.0
   ```
   전역 값과 생성 정보 값만으로 정해지므로 같은 입력이면 같은 난수열이 나옵니다 [판독]. 네트워크 동기에 쓰이는지는 사격장 1인 연습 범위 밖이고 [../network/network.md](../network/network.md) 담당입니다(2026-10-03: 범위 밖으로 분류).
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
   - **idx 출처 — 해소(2026-10-03, solo_shooter.md에서 옮김) [판독]**: `shooter_ink_action.c` 223~237·343~357행. N = `0x7102897470`이 돌려주는 스플래시 분할 수, u8 카운터 c = I+0x91(I = PlayerInkActionShooter).

     ```text
     c = N != 0 ? c % N : c
     idx = table[(N<16 ? N*16 : 0) + (c<16 ? c : 0)]      # 0x7104a9b0a1
     I+0x91 = u8(c + 1)
     0x71025817c8(..., idx, local=1, frame, ...) → 0x71025823b0 → S+0x90 = idx
     ```

     c의 초기값은 리셋 `0x7102582e3c`가 sead 시드(F + Pidx·100 + (a+b)·0x89, 0x1c1/0x233/0x3df)로 뽑은 첫 u32의 하위 바이트입니다(0x7102580780, 원문 1039~1069행). 로비의 실제 프레임·시드 값은 [미확정]. 정정(2026-10-03): 이전 판의 "고르게 퍼뜨리는 용도로 보임 [추정]"은 의도 해석이라 명세에서 뺍니다.
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
            (isLast = +0x11ed) 이면: acc(+0x11f4) += (SpawnBetweenLength/split − nearest(0x710174fe94)) · (+0x11f8), +0x11ed = 0
            remaining(+0x11fc) -= 1 ; remaining == 0 이면 반복 끝
    if forced(+0x11ee):                       # 가까운 지점 강제 생성
        +0x1208 쪽 누적(+0x1208 += 수평 거리)으로 강제 생성 하나를 같은 방식으로 처리
```
2026-10-03 보충 [판독]+[실행(기존)]: 위 반복 뒷부분(남은 수 감소·isLast 보정·강제 생성)은 BulletShooterBase_vt.c 0x71017512bc 원문 120~260행에 있고, `web/tools/weapon_splash_emu.py`가 슬롯 56 → 0x71017540ec를 원본 그대로 실행해 재구현 `weapon_splash_sim.py`와 불일치 0을 기록했습니다(SHARED `[weapon impl] 스플래시 일정·생성 확정`, 스텁: 탄 위치·형식 검사·생성 요청). +0x11f8의 의미 이름은 붙이지 않습니다.

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

추가·정정(2026-10-03): SHARED의 기존 "카메라+0x3c 기저 Z" 주소 설명은 +0x54로 정정했습니다(조준 축 a = −카메라 Z = normalize(at − pos), [../camera/player_camera.md](../camera/player_camera.md) §6.7 [실행]). 분할 번호는 §5.3, 생성 허용·실패는 §3.5, Pre/PostDelay는 §3.5입니다.

**총구 위치** `0x7102552170` [실행(기존 17/17)]+[판독] (solo_shooter.md에서 옮김):

```text
L = B+0x54c 수평 리그 시선 ; R = up × L
deg = p(B+0x558) 의 조각 3차 베지어 (p = −1/0/+1 → −70/5/75°, 접선 kMin .178 / kHor .17 / kMax .152)
U, W = 수평 전방을 deg 만큼 기울인 위·앞 축
oy = p < 0 ? oy − (0.6 − oy)·p : oy
pos = B+0x58 + (0, 1.1, 0) − 0.24·R + oy·U + 0.18·W
```

파라미터는 `spl__BulletShotDirParam`이고, `0x7102624d58`이 SplPlayer `spl__BulletShotDirAllInkActionParam` 목록에서 무기 문자열 "Shooter" 항목을 찾지만 데이터에 Shooter 항목이 없어 **코드 기본값**(Min −70 / Hor 5 / Max 75, KMin .178 / KHor .17 / KMax .152)을 씁니다 [데이터: `SplPlayer.spl__BulletShotDirAllInkActionParam.bgyml`]. 총구 피치 +5°, 카메라 리그 고각 +7.5°, 흔들림 회전은 서로 다른 계산입니다. B+0x58과 실제 플레이어 위치의 writer 연결은 [미확정].

**잉크 소비·회복** [실행(기존 weapon_ink_emu: 소비 2012 / 회복량 500 / 연사 타이머 5101 / 정지 500건 불일치 0)]+[판독] (solo_shooter.md에서 옮김):

```text
cost = f32(InkConsume * f32(MainInkSave * k))         # 스플래시슈터 k = 1(꼬마슈터 1/1.1), InkConsume .0092 (0x3c16bb99)
ok = r >= cost or abs(f32(r - cost)) <= 1e-5          # r = B+0x698 로컬 잔량. partial 허용은 B+0x6d8 모드만
if ok:
    r = f32(r - cost)                                  # partial 인 경우 0
    B+0x6b8 = B+0x6bc = 0
    if r < 회복량(0x7102491f88): r = 0
else:
    탄 발사 안 함, B+0x6ac = max(·, 30), NoInk 경로
소비 성공: 회복 정지 B+0x6a8(오징어 +0x6b0) = max(·, InkRecoverStop 20)   # 0x7102353718
회복: 세 카운터(B+0x6a8/+0x6b0/+0x6ac) 의 max < 1 일 때만. 카운터는 음수까지 내려감(0 으로 clamp 하면 원본과 다름)
회복량: Std 1/600 (0x3ada740e), 잠복 1/180 (0x3bb60b61)
```

기어 0·회복 없는 만탱크는 **108발**, 잔량 **0.006400978**입니다. 연속 소비 함수 검증이며 실제 프레임 사격 전체 검증으로 넓히지 않습니다. 잉크 도구는 가짜 본체·오프라인 전역을 쓰고 PLT 호출을 0 반환으로 스텁했습니다. MainInkSave 기어 계수의 0 GP 값은 기어 함수 쪽([../player/gear_skills.md](../player/gear_skills.md)) 근거를 따릅니다.

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
- 꼬리 점(§3.4)은 그리기 인스턴스 기록(슬롯 47 `0x710174e90c`)이 길이 `min(|꼬리 벡터|, 슬롯108)`로 버퍼 +0x1f8에 써서 표시에 쓰입니다 [판독] (2026-10-03 정정: 이전 "표시용으로 보임 [추정]"). 이펙트·사운드 연결은 [../effect_sound/effect_sound.md](../effect_sound/effect_sound.md). 발사 xlink 액션 이름은 Fire / FireOn / FireImpact(§3.5).
- 액터: `BulletShooterBase` 바디 레이어 `SplInkBullet_FriendThrough`, `BlockableLayerHitMask: HitAll` **[데이터]**. 단 탄 시작(`0x7101762f68`)과 이동(`0x7101763a10`)이 `FriendThroughFrameForPlayer`에 따라 레이어를 8(SplInkBullet) ↔ 9(FriendThrough)로 바꾸므로, 이 값이 0인 슈터 탄은 시작하자마자 레이어 8이 됩니다 **[판독, combat]**.

## 8. 다른 기능과의 상호작용

| 대상 | 연결 | 문서 |
|---|---|---|
| 도색 | 이동 거리 +0x1200으로 도색 폭(Near/Middle/Far) 보간(슬롯 84), 스플래시 탄 생성. 슬롯 84는 생성 정보 +0x6d(로컬 플래그)가 0이면 바로 돌아가므로 **복제 탄은 칠하지 않음**(칠은 발사 기기가 PaintRequest로 송신) [판독, paint] | [paint](../paint/paint_and_score.md) |
| 데미지 | 감쇠 `0x71017506d0`: `t=clamp01((age-Start+1)/max(End-Start,1))`, `dmg=trunc(Max+(Min-Max)t)` — age는 이 문서의 +0x134(슬롯 18에서 이동 전 증가). 단위 1 = 0.1 HP | [combat](../combat/damage_hit.md) |
| 헬퍼 | 슬롯 36 `0x71015315d0`이 "spl::KnockBackHelper", "spl::BulletHitEffect", "spl:DamageHelper" 이름을 참조합니다. `spl:DamageHelper`는 탄 쪽 헬퍼가 아니라 피해를 받는 액터의 HitPointHolder 컴포넌트입니다([combat](../combat/player_life.md), 2026-10-02 정정). 이 문장의 배타적 HitPointHolder 해석과 생성/조회 미확정은 **2026-10-03 §3.3.6에서 정정·해소**했습니다. 원본 factory가 탄에 세 객체를 새로 생성합니다 [실행] | combat |
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

7차 웹 반영 필요: `impl/weapon.md`의 `Fire && !Squid`를 그대로 B+4d0으로 쓰지 말고, Sender 우선순위 이후의 원본 차단/래치 조건과 연속 카운터를 보존한다. ab4/abc 등은 §3.5.1의 포화 감소를 적용한다. a90/adc/4d4와 총구 기준 B+58 연결은 아직 미확정이므로 이 결과로 대체하지 않는다. 코드와 impl 문서는 변경하지 않았다.

## 10. 검증 [재구현 계산]

`.venv/Scripts/python web/tools/bullet_shooter_sim.py WeaponShooterNormal --frames 30` (수평 발사, 위치는 `pos += vel` 근사). 이 표는 원본 실행 비교 없음. 원본 실행이 있는 부분(총구·잉크·스플래시·생성 허용·꼬리 길이)은 검증 기록 [solo_shooter.md](solo_shooter.md)에 모읍니다. 원본 바디 적분식(`fl(dt·fl(60v)) + p`)과의 차이는 `web/tools/bulletbody_integrate.py`로 잽니다(40프레임 최대 2.9e-6 유닛, 아래 표 위치값과의 차이도 이 범위).

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

7차 원본 실행 추가: `r7_weapon_input_emu.py`의 메인 입력 카운터1680건·타이머1030건(11330필드) 모두 일치. §3.5.1에 경계 스텁과 제외 조건을 명시했다. 재구현 단독 테스트와 구분한다.

8차 원본 명중 요청 추가: §3.3.10의 1,024건 접촉/패킷 및 2,688건 ObjPaint 재질 분기, 초기화 필드 비트 일치. 큐와 실제 방출은 캡처 경계이고 지형 kind2/nonnull 참조 ptr은 제외한다.

## 11. 미확정 사항과 다음 근거

8차(2026-10-03): §3.3.10은 실제 탄 명중 요청의 접촉·방향·재질·요청 플래그를 연결했다. 최종 히트마커/효과 키의 전체 질문은 아직 부분이다. 다음은 `27b4704` 큐→`27b877c` 컨트롤러→Focused/ELink/SLink 소비의 실제 요청 필드 조건이다. TypedBody vt+0x28의 실제 FieldRigidBody 대응과 ColPaint kind2는 별도 생산자 추적이 필요하다. 이 미확정을 ObjPaint 기본 재질 fixture로 대신 채우지 않는다.

7차(2026-10-03): B+4d0 로컬 writer는 §3.5.1에서 해소했다. B+4d4의 writer 전체, a90 상태 집합, adc 감소·갱신, B+58 위치 연결은 남았다. `r5_player_storescan.py 58`로 찾은 슬롯19의 2483db0은 x23 기준이며 본체라고 입증하지 못했으므로 총구 writer로 채택하지 않았다. 다음은 249f494의 B+4d4 생성과 24a2c98/슬롯19 위치 인자 추적이다.

| 항목 | 필요한 근거 |
|---|---|
| ~~위치 적분·충돌~~ | **해소**(2026-10-02): §3.2 정정, [../physics/phive_controller.md](../physics/phive_controller.md) §6.3~6.8 [판독] |
| ~~충돌 콜백 58/59 대상, 컴포넌트 0x20/0x28/0x38~~ | **해소**: §3.3 (58 바닥, 59 벽·천장, 60 Ground 외) [판독]. 0x28 = 소멸 요청은 [추정] |
| ~~접촉 반응 시퀀서의 프레임 내 위치(첫 명중 age 1/2, 슬롯 19·21 순서, 바닥 탄 보관 도색 실행 여부)~~ | **해소**(2026-10-03 [판독]): 물리 직후·슬롯 19 앞. 첫 명중 age 0, 보관 도색은 슬롯 21 소멸 요청 전 실행(§3.3) |
| 슬롯 59의 재질의 구 질의 세부(방향·길이), 슬롯 68(바디 없음 경로)·자식 탄 0x7101648824의 액터 이름 | `0x7101764ff8` 전체 분석 기준 재디컴파일(`state_redecomp.sh`), `0x7101648824`·`0x7101648650` |
| ~~분할 인덱스(생성 정보 +0x90)를 정하는 규칙~~ | 해소(2026-10-03): I+0x91 modulo N → 4a9b0a1 순열 → param_7, §5.3 [판독] |
| ~~꼬리 길이 제한(TailLengthParam의 나머지 필드)~~ | **해소**(2026-10-03 [판독]+[실행 445/445]): 슬롯 108·슬롯 47(§3.4) |
| ~~OnlineVersusSetting 시드 → 대전 설정 객체 복사 경로~~ | **해소**(2026-10-03 6차 [실행]+[판독], §5.3): 전환 슬롯42 0x7103029330의 0x7103029ca8 `C8.copy(D0)`(묶음 복사 0x7102ae5810). 사격장 = 부팅 뒤 첫 진입 13, 대전 뒤에는 직전 대전 시드(LobbyVersus에 Scene_Versus 없음). 남은 것: 로비 GameFrame 시작값 |
| 탄 생성 실패 | **해소**(2026-10-03 [판독]): 예약 풀 고갈이면 0x7100f7f39c가 0 → 메인 탄 생성 안 됨(§3.5). 스플래시 실패 조건 해소(6차 [판독], §3.5: 허용 함수 거짓·관리자 없음·해시 없음·하위 풀 빈 칸 0). 남은 것: 스플래시 하위 풀 크기와 ActorReservation 32의 연결(`*0x71058014d8`+0x60 트리 삽입), 생성 정보 → 탄 +0x108 저장 명령 |
| ~~0x28 컴포넌트 = 소멸 요청~~ — 해소(8차 §3.3.4) | 0x7100f721b8(액터 상태 전이 요청) 인자 0의 의미 — 미판독 |
| ~~새 탄의 슬롯 19/21이 생성 프레임에 도는지~~ | **해소**(2026-10-03 6차 [판독], §3.3): 돌지 않음. 활성은 관리자 대기 목록에만 넣고(0x7103c88cd8), 다음 프레임 구동이 그래프 구성 전에 연결(0x7103c85b40 → 0x7103c85fbc) |
