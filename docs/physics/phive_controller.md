# Phive 물리 계층 — 캐릭터 컨트롤러·중력·탄 바디

플레이어 이동과 슈터 탄이 게임 코드에서 계산한 속도를 Phive(Havok hknp 기반 물리 래퍼)로 넘기는 경로, Phive 캐릭터 컨트롤러가 한 스텝 안에서 속도를 만드는 순서, 중력이 실제로 어디서 더해지는지를 정리합니다. 작업 지침은 [../../분석.txt](../../분석.txt), 공용 사실은 [../README.md](../README.md)·[../02_code_and_params.md](../02_code_and_params.md).

이 문서를 쓰는 문서:
- [../player/movement_physics.md](../player/movement_physics.md) — 플레이어 목표 속도·가속·점프(§6.4~6.6, §11이 이 문서로 연결)
- [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md) — 슈터 탄 이동(§3.2, §11)

확정 수준: **[실행]** 원본 실행 / **[판독]** 원본 코드 판독 / **[데이터]** 데이터 / **[추정]** / **[미확정]**. 이 문서의 수치 검증은 "판독한 식의 재구현 계산"과 "정적 초기화 에뮬 실행으로 얻은 상수값"뿐이며, 이동·중력 함수 자체를 원본으로 실행해 비교한 것은 없습니다.

상태: 분석 진행 중(4차: 플레이어 몸체·캡슐·접지 판정·상태 전이는 [character_controller.md](character_controller.md). 중력·컨트롤러 파이프라인·탄 바디 적분·충돌 응답·충돌 콜백 분배 판독, 접촉 처리 시점의 프레임 내 위치는 추정). 웹 구현 없음.

---

## 1. 요약 (먼저 읽을 결론)

| 질문 | 결론 | 수준 |
|---|---|---|
| 플레이어 중력값 | **g = 0.008 유닛/프레임²** (bss `0x71058bbc84` = 비트 0x3c03126e, 정적 초기화 `0x7102455db0`이 씀). 상태에 따라 0(특수 0x1c SuperLanding, Periscope 조건), ×0.2~1.0(특수 0x18 Jetpack), ×외부 계수(특수 0x1b Skewer) | 값 [실행(에뮬)], 사용 [판독], 원본 함수 단독 실행 반환값 0x3c03126e [실행] |
| 중력을 더하는 곳 | **게임 코드**. 플레이어 수직 속도 `본체+0x73c`(위가 +)를 매 프레임 `v = 0.98·v − g`로 갱신(`0x71024a7d00`). 중력은 공중 프레임 카운터 `본체+0xc0` ≥ 3이고 다운 계열 카운터가 모두 0일 때만 뺀다. +0xc0은 슬롯19(Phive 스텝 뒤)에서 공중이면 +1, 접지면 0 | [판독] |
| 점프 곡선 | 점프 프레임 이동량 0.115(감쇠 전), 공중 1·2프레임은 감쇠만, 3부터 중력. 최종 y 속도 = vy + 이동 속도 y(별도 −0.002/0.92 보정) + 버튼 유지 가산 0.005/프레임. 평지 탭 최고 0.84145(14프레임), 계속 유지 1.73148(30프레임) | [원본 실행(함수 연결)] — [../player/movement_physics.md](../player/movement_physics.md) §6.4 |
| Phive 세계 중력과의 관계 | 게임이 매 프레임 컨트롤러 GravityScale = `g·60·60/9.8`(조건 불충족 시 0)로 설정(`0x7102475a54`→ctrl vt `0x1e8`). 하지만 SplPlayer의 공중 상태(GameInAir)는 플레이어 초기화에서 "게임 속도를 그대로 쓰는" 모드로 바뀌어(`0x71024f4270`) 공중에서는 Phive가 중력을 더하지 않는다 | [판독] |
| AirDumping 계수 | 생성자에서 전부 0, 플레이어 초기화에서 공중 상태 계수를 다시 0으로 씀 → 플레이어에게는 효과 없음 | [판독] |
| 컨트롤러 단계 순서 | 데이터 `SplPlayer` 프리셋 순서 그대로: GameFrameSetup → MoveStateUpdate → AirDumping → Rotate → SplJump → FloatWater → GameFollowSurface → SplAlongGnd → CliffSlip → ImpactAndReject → GameApplyVelocity. 실행기 `0x7103a80560`이 배열 순서로 슬롯 8을 호출 | [데이터]+[판독] |
| 이동 코드의 "Phive 가속도 × 1/60²" | 중력이 아니라 **ImpactAndReject 컴포넌트의 충격·밀어냄 가속도**(유닛/초²) 두 개(`+0x08`, `+0x24`)의 합을 1프레임 속도 변화로 바꾼 것 | [판독] (기존 player 문서의 "Phive 가속도" 표현 정정) |
| 단위 변환 | 게임 속도(유닛/프레임) → Phive ×60(유닛/초), Phive → 게임 ×0.016666668. 가속도(유닛/초²) → 프레임당 속도 변화 ×1/3600 | [판독] |
| 탄의 위치 갱신 주체 | 캐릭터 컨트롤러가 아니다. 탄의 ControllerSet에는 `CharacterControllerName: BulletSimple`만 있고 그 이름의 프리셋·`PathCharacterController`가 없다. 탄 `+0x138`은 탄 바디 래퍼(vtable `0x710559f3f8`)이고 속도를 ×60 해서 바디 `+0xc4`·`+0xdc`에 쓴다 | [데이터]+[판독] (기존 shooter 문서의 "Phive 캐릭터 컨트롤러 BulletSimple이 처리" [추정] 정정) |
| 탄 위치 적분식 | 탄 바디(phive 탄 바디 클래스 vtable `0x7105749990`, 0x198 B)의 스텝 `0x7103b0a2bc`가 **`p1 = fadd(fmul(dt, body+0xc4), p0)`**(성분별, FMA 아님), dt = 월드+0x24 = **0.016666668f(0x3c888889)**. 서브스텝 없음(물리 스텝마다 바디 1회). `body+0xc4 = fmul(v, 60.0f)`이므로 `pos += vel`과 같은 값이 아니라 **수 ulp 다를 수 있음**(재구현: 40프레임 최대 2.9e-6 유닛) | [판독] (2026-10-02 해소, 기존 `pos += vel` [추정]을 정정) |
| 탄 충돌 시 처리 | 시작점 p0→끝점 p1 쓸어 넘기기(넓은 단계 AABB = 두 위치 형상 AABB 합) 후 접촉마다 비율 f(+0x60). 막는 접촉 중 가장 작은 f에서 **`pos = p0 + f·(p1−p0)`, `body+0xc4 = 0`**. 반사·미끄러짐 없음 | [판독] |
| 플레이어 몸체·접지 판정 (4차) | 동적 강체(질량 100, 회전 없음)를 Havok 솔버가 움직이고, 결과 컴포넌트 SplResultPlayer(`[PC+0xe378]`, 슬롯7 `0x7102c5a3c8`)가 접촉에서 지지(S+0x20)를 정해 OnGround↔InAir를 바꾼다. 재질 Character는 지형과 마찰·반발 0, 최대 경사 75°, 계단 높이 0.2, 점프 상승 중 바닥 접촉 무시 — [character_controller.md](character_controller.md) | [판독]+[데이터] |
| 탄 충돌 콜백 | 접촉은 바디 리스너(`0x7105553ae0`) → `PhysicsContactReactionSequencer(Entity)` 큐 → 탄 슬롯22 → `0x7101646910`이 상대 레이어·법선으로 **슬롯58 = Ground 바닥(n.y > 0.6414)**, **슬롯59 = Ground 벽·천장(n.y ≤ 0.6414)**, **슬롯60 = Ground 외(플레이어·오브젝트)** 로 나눔 | [판독]+[실행(에뮬): 임계값] |

---

## 2. 자료 위치

| 항목 | 위치 |
|---|---|
| Phive 설정 | `analysis/player/PhiveConfig.json` (`romfs/Phive/Config/PhiveConfig.byml.zs`): `CharacterComponentPresetCollection`, `MotionPropertiesCollection` |
| 플레이어 ControllerSet | `extracted/actor/SplPlayer/Phive/ControllerSetParam/SplPlayer.phive__ControllerSetParam.bgyml.json`, `CharacterControllerParam/SplPlayer…json`(GravityScale 1.0, PresetTypeName SplPlayer), `CharacterMatterRigidBodyParam/SplPlayer…json`(MotionProperty SplPlayer, Mass 100) |
| 탄 ControllerSet | `extracted/actor/BulletShooterBase/Phive/ControllerSetParam/BulletShooterBase…json`(`$parent` BulletEmpty, `CharacterControllerName: BulletSimple`), `Gyml/BulletShooterBase.game__BulletBodyControllerEntityParam…json`(UnitArray 1개) |
| 디컴파일 | `analysis/decomp/physics/phive_batch1.c`(컨트롤러 컴포넌트·이동 상태·탄 바디 래퍼), `phive_batch2.c`(게임↔Phive 속도 전달·중력값·ImpactAndReject), `phive_batch3.c`(수직 속도 갱신·점프 높이 역산), 기존 `analysis/decomp/player/phive_char_components.c` |
| 상수 | `analysis/player/bss_consts_58bb000.txt` (정적 초기화 에뮬 결과) |
| 디컴파일(탄 바디) | `analysis/decomp/bulletbody/bb_batch1.c`(BulletBodyComponent), `bb_batch2.c`(유닛 엔티티·리스너), `bb_phive1.c`(phive 탄 바디 클래스·스텝 `0x7103b0a2bc`), `bb_phive2.c`(관리자 스텝·쓸어 넘기기 캐스트), `bb_phive3.c`·`bb_world.c`(월드), `bb_contact.c`, `bb_event*.c`·`bb_queue*.c`(접촉 반응 큐) |
| 도구 | `web/tools/physics_memscan.py`(오프셋별 ldr/str/ldp/stp/ldur/stur 전수 검색), `web/tools/physics_jump.py`(수직 속도 재구현 — 역산 모델용, §4.4 정정), `web/tools/move_jump_emu.py`(점프 곡선 원본 함수 연결 실행, [move]), `web/tools/bulletbody_integrate.py`(탄 바디 적분 재구현·`pos+=vel` 차이), `web/tools/bulletbody_immscan.py`(movz 즉시값 전수 검색) |
| 산출물 | `analysis/physics/jump_curve.json`, `analysis/physics/scan_*.txt`, `analysis/bulletbody/integrate_compare.json`, `analysis/bulletbody/bss_5858340.json`(접촉 법선 임계값 정적 초기화 에뮬) |

## 3. 플레이어 캐릭터 컨트롤러

### 3.1 객체 연결 [판독]

기준 객체를 섞지 않도록 경로 전체를 적습니다. "본체" = 플레이어 본체(PlayerBehavior+0x108, 0xac80 B).

```
본체+0xa690 → PlayerCollision(이하 PC)
  PC+0xe340  Rotate 컴포넌트 포인터           (조회 0x71012411f0, 이름 "CharacterUpdateRotate")
  PC+0xe348  AirDumping 컴포넌트 포인터       (조회 0x71017301b8, "CharacterUpdateAirDumping")
  PC+0xe350  GameFollowSurface 컴포넌트 포인터 (조회 0x7101730324, "CharacterUpdateFollowSurface")
  PC+0xe358  GameFrameSetup 컴포넌트 포인터   (조회 0x7101baf574, "CharacterUpdateFrameSetup")
  PC+0xe360  ImpactAndReject 컴포넌트 포인터  (조회 0x71012eb0a0, "CharacterUpdateImpactAndReject")
  PC+0xe3b8  컨트롤러 래퍼 W
     W+8 = ctrl  (phive 캐릭터 컨트롤러, vtable 0x7105746dd0, 72슬롯)
        ctrl+0x18 = 강체(선속도 +0x138, 쓰기 0x7103ae2890)
        ctrl+0x20 = 상태 S (0x2a8 B, vtable 0x7105746d80, 생성 0x7103a862cc)
        ctrl+0x40 = 이동 상태 관리자 M: +0x28/+0x30/+0x38 = 상태 객체[0..2], +0x40 = 현재 번호, +0x44 = 이전 번호
```

PC+0xe340~+0xe360의 포인터 표는 `0x71024f2e5c`가 `x28 = PC+0xe340`에 순서대로 저장합니다(`0x71024f3d3c`~`0x71024f3d6c`).

이동 상태 배열 순서는 **[0]=OnGround 계열(종류 0), [1]=InAir 계열(종류 1), [2]=Free(종류 2)** 입니다 **[판독]**. 근거: 상태 객체 `+8`의 종류 값(GameOnGround 생성 `0x71012a9740`은 0, GameInAir 생성 `0x71012a97d0`은 1), SplJump(`0x7102c6087c`)가 `상태[현재]+8 == 1`이면 공중 처리, 플레이어 초기화(`0x71024f4270`)가 `M+0x30`(=[1]) 객체의 `+0x14`·`+0x1c`를 쓰는데 이 오프셋은 0x20 B인 GameInAir에만 있다(GameOnGround는 0x18 B). 데이터 프리셋의 `MoveStateComponents` 나열 순서(GameInAir, GameOnGround, Free)와는 다릅니다.

### 3.2 ctrl vtable (0x7105746dd0) 중 이 문서에서 쓰는 슬롯 [판독]

| 슬롯 오프셋 | 함수 | 의미 |
|---|---|---|
| 0x38 / 0x40 | `0x7103a87acc` / `0x7103a87ad8` | 이동 방향(단위벡터) S+0x168 읽기/쓰기(바뀌면 S+0x18 bit1) |
| 0x48 / 0x50 | `0x7103a87b78` / `0x7103a87b84` | 위쪽 벡터 S+0x174 읽기/쓰기 |
| 0x58 / 0x60 | `0x7103a87ba0` / `0x7103a87bac` | 이동 속력 S+0x180 읽기/쓰기 |
| 0x68 | `0x7103a87be8` | **이동 속도 설정**: v를 정규화해 방향(0x40)과 크기(0x60)로 나눠 저장 |
| 0x70~0x98 | `0x7103a87cbc`… | S+0x184/+0x188/+0x18c 쓰기([-1,1] 클램프)·읽기 |
| 0x128 / 0x130 | `0x7103a87348` / `0x7103a873c0` | 강체 선속도 읽기(ctrl+0x18 → +0x138) / 쓰기(`0x7103ae2890`) |
| 0x1d8~0x1f8 | `0x7103a87884`~`0x7103a879c0` | 중력(§4.3) |
| 0x200 | `0x7103a87ac0` | 중력 방향 S+0x1e8 |

### 3.3 업데이트 실행기와 프레임 정보 [판독]

`0x7103a80560`(캐릭터 하나):
```
if (컨트롤러 비활성 조건들) return
vel = {0...}                 // 0x38 B: [0..2] 선속도, [3..5] 각속도, [6..8], [9..11] 임펄스 몫
frame = {0...}; frame.up = (0,1,0) 기본
for comp in 컴포넌트 배열(ctrl 노드 +0x38, 개수 +0x30):
    if (특정 플래그 && comp+0x18 == 1) skip
    comp.vt[0x40](comp, ctx, &vel, &frame)       // 슬롯 8 = update
```
배열은 프리셋 `UpdateComponents` 순서로 만들어진다고 봅니다 **[추정: 생성 순서는 팩토리 0x7103a8367c가 이름별로 만드는 것까지만 판독]**. SplPlayer 프리셋 순서는 §1 표.

프레임 정보(GameFrameSetup `0x71012acf60`이 채움, 기준: 위 `frame` 지역 구조체):

| 오프셋 | 값 | 출처 |
|---|---|---|
| +0x00 | 현재 강체 선속도(유닛/초) | ctrl vt 0x128 |
| +0x0c | 각속도 | ctrl vt 0x150 |
| +0x18 | 중력 가속도 벡터(유닛/초²) | ctrl vt 0x1f0 = S+0x1f8 |
| +0x24 | 위쪽 기준 벡터 | GameFrameSetup+0x28, NaN이면 상수 `*0x7105791978` = (0,1,0) |
| +0x30 | 이동 방향(단위) | ctrl vt 0x38, S+0x184/+0x188로 기울임 |
| +0x3c | 이동 방향 크기 계수 | 위 계산의 길이(기본 1.0) |
| +0x44 | dt | `[[*0x71057906f0]+0xe8]+0x24` (런타임 값, 1/60로 추정) |
| +0x60 | 유효 플래그 = 1 | |

(일반 `FrameSetup` `0x7103a8b7a4`는 +0x18을 `세계설정+0x40 × vt0x1f0`로, +0x24를 ctrl vt 0x48로 채우는 점이 다르다. SplPlayer는 Game 버전을 쓴다.)

### 3.4 단계별 동작 [판독]

| 단계 | vtable / 업데이트 | 동작 |
|---|---|---|
| GameFrameSetup | `0x71055746a0` / `0x71012acf60` | §3.3 프레임 정보 작성 |
| MoveStateUpdate | `0x7105747238` / `0x7103a8c2a0` | 현재 상태 객체가 처음이면 slot3(진입) 호출, slot4(갱신)(state, &vel, &frame), 상태 시간 += dt. 상태가 Free가 아니면 `dot(vel, 중력방향)`을 S+0x204(생성자 기본 200)로 상한 → 최대 낙하 속력 |
| ├ GameInAir | `0x7105574390`, slot4 `0x71012aa138` | `+0x1c == 0`이면 기본 InAir(`0x7103a84f58`): `A = 현재속도 + dt·중력`, 모드(+0x14)≠0이면 A를 중력 방향 성분만 남기고 이동 방향×속력의 수평 성분을 더함. **`+0x1c != 0`이면 `vel = 이동속력 × 이동방향`(게임이 넘긴 속도 그대로)**. 진입 직후(+0x1d)이고 +0x1e면 vel.y>0을 0으로 |
| ├ GameOnGround | `0x7105574428`, slot4 `0x7103a85410` | 접지 법선으로 이동 방향을 투영해 `이동계수×이동속력` 만큼 더하고, 접지 거리(+0x38)가 있으면 중력의 법선 성분으로 붙임 |
| AirDumping | `0x71055744a8` / `0x71012aaa38` | `v -= dt·kn[상태]·(v·u)u; v -= dt·kt[상태]·(v − (v·u)u)` (u = ctrl vt 0x200). kn=+0x34[3], kt=+0x28[3] |
| SplJump | `0x7105681c98` / `0x7102c6087c` | 자체 필드만 갱신(+0x28 요청 속력, +0x58 요청 플래그, +0x30 쿨다운 −dt, 공중이면 누적 임펄스 +0x40 → +0x34, y ≥ −1000). vel 인자는 건드리지 않음 |
| GameFollowSurface | `0x71055745f8` / `0x71012aba18` | 발판 속도. 결과 +0x3c..+0x44(유닛/초)를 플레이어 코드가 ×1/60로 읽음(`player_misc1.c` 718행) |
| CliffSlip | `0x7105574590` / `0x71012ab4a8` | 빈 함수 |
| ImpactAndReject | `0x7105574708` / `0x71012adb58` | 데이터 D(=+0x28, 0x68 B): `vel += dt·D.impact(+0x08)` (공중·모드1이면 중력방향 성분 제거), `vel += dt·D.reject(+0x24)`, 위치 보정 `(D+0x4c..)+(D+0x58..)`을 `/dt` 해서 더함. 이후 두 가속도를 D+0x14 비율로 곱하거나(+0x14가 NaN이면 D+0x18 시간에 걸쳐 선형) 감쇠, 크기²<1e-4이면 0 |
| GameApplyVelocity | `0x7105574510` / `0x71012aaef8` | ctrl vt 0x130/0x148로 강체 선/각속도 설정, S+0x1a0(선)·+0x1ac(각)·+0x1b8(선−임펄스몫)·+0x1c4(임펄스몫) 기록 |

AirDumping 계수: 생성(`0x7103a83840` 경로)에서 +0x10~+0x3c를 0으로 초기화하고, 플레이어 초기화 `0x71024f4270`이 `[PC+0xe348]+0x38 = 0`, `+0x2c = 0`(공중 상태 [1]의 kn, kt)을 다시 씁니다. 이 포인터(PC+0xe348)를 계산하는 명령은 main 전체에서 `0x71024f4280`(위 함수)과 `0x7102a38ed8`(다른 클래스) 두 곳뿐입니다(`mov w?, #0xe348` 전수 검색). 따라서 **플레이어에게 AirDumping은 0 계수(효과 없음)** 입니다 **[판독]**. 다른 클래스의 `0x71017301b8` 호출자(`0x710172f504`, `0x7101ca2c9c`)는 플레이어가 아닙니다.

## 4. 중력

### 4.1 중력값 함수 `0x71024c9684` [판독], 상수 [실행(에뮬)]

인자: arg1 = 본체+0xa5f9, arg2 = `[본체+0xa680]`(spl::PlayerInkActionSpJetpack), arg3 = `[본체+0xa7e8]`(spl::PlayerInkActionSpSkewer). 클래스 이름은 `analysis/player/player_components.tsv`의 오프셋 대응.

```
g = 0.008                                        // [0x71058bbc84]
special = 본체+0x65c (특수 상태 번호; "특수 활성" = 본체+0x588/+0x598 또는 +0x678/+0x688 포인터 쌍이 같음)
if 특수 활성 && special == 0x18:                  // player 문서 §6.1에서 SpJetpack 비율을 쓰는 번호와 같음
    n = arg2[+0x188]                              // 프레임 카운터(의미 미확정)
    if n > 0 && [[arg2+0x14a0]+0x108]+0x73c <= 0:  // 주인 플레이어의 수직 속도가 0 이하이면
        return g * (n > 19 ? 0.2 : ((n-20)/-20)*0.8 + 0.2)
    return g
if 특수 활성 && special == 0x1b && arg3[+0x40] ∈ {3,4}:
    return g * 0x71025f1040(arg3)                // 연결 객체의 +0x44 값(연결이 없으면 1.0)
if 특수 활성 && special == 0x1c: return 0
if [본체+0xa818]+0x38 != 0 || [본체+0xa818]+0xb0 != 0: return 0   // 본체+0xa818 = spl::PlayerPeriscope
return g
```
special 0x18에서 n이 1..19이면 배율 = 0.2 + 0.8·(20−n)/20(n=1에서 0.96, n=19에서 0.24), 20 이상은 0.2. 즉 내려오는 동안 중력이 점점 약해진다.

특수 상태 번호 이름 — 정정(이전 [미확정]): 본체+0x65c = 10 + 특수 열거 인덱스이고([camui] 판독, SHARED.md), 0x18 = Jetpack, 0x1b = Skewer, 0x1c = SuperLanding이다. 각 분기가 읽는 컴포넌트(+0xa680 PlayerInkActionSpJetpack, +0xa7e8 PlayerInkActionSpSkewer)와도 맞는다 **[판독+데이터]**. Periscope(+0xa818) +0x38/+0xb0의 게임 의미는 **[미확정]**.

### 4.2 게임 코드의 수직 속도 갱신 `0x71024a7d00` [판독]

호출: 메인 계산 `0x7102475a54`(줄 4925, `0x710247c860`)가 `(본체+0xa5f9, &본체+0xc0, PC, &본체+0x72c, X)`로 호출. 기준 객체: **본체**.

| 본체 오프셋 | 타입 | 의미 | writer | reader |
|---|---|---|---|---|
| +0xc0 | s32 | 공중 프레임 수 (`0x710245f964`의 airFrames와 같은 주소) | 슬롯19 `0x71024abcf0` → `0x710246b574`(+1) / `0x710246b32c`(0), 점프 프레임 메인 계산 `0x710246b32c`(0) | 중력 조건, `0x710245f964` |
| +0x734 | s32 | 점프 시작 뒤 프레임 수(+0x72c 구조체 +8) | `0x71024a7d00` (+1/프레임), `0x71024a8000` 점프 시작(0) | 같은 함수(≥3 조건), 재점프 대기(> 6) |
| +0x750 | vec3 | 3D 점프 속도 X(아래 의사코드의 X, 인자 5). 경사에서 점프하면 +0x73c 대신 여기에 (0, jump, 0) | 메인 계산 점프부, 벽 점프(0) | 같은 함수, `0x710245aed8` |
| +0x73c | f32 | **수직 속도(유닛/프레임, 위가 +)** | 점프 시 초기 속도(메인 계산 줄 5413), `0x71024a7d00` | 이동(`0x710245b2b4`)·점프 판정 여러 곳, 컨트롤러 전달(§5) |
| +0x740 | f32 | 수직 합계 = +0x73c + X.y | `0x71024a7d00` | 미추적 |
| +0x744 | u8 | 위 합계 유효 플래그 | 같은 함수 | |
| +0xd58, +0xd60, +0xde0, +0xdf0, +0xe0c | s32 | 다운 계열 카운터(+0xc0 기준 인덱스 0x326/0x328/0x348/0x34c/0x353). ui 문서가 "+0xd60/+0xde0/+0xdf0/+0xe0c > 0이면 아이콘 Down"으로 읽은 필드와 일치 | | 중력 조건 |

```
g = 0x71024c9684(...)
// X = 3D 점프 속도 본체+0x750(인자 5). X.y > 0.001 이고 현재 이동 상태가 InAir([1])이면
//   본체+0x73c += X.y; X.y = 0          (임펄스를 수직 속도로 옮김)
if !X.flag(+0x30):
    X.xyz *= 0.98                                        // [0x71058bc140]
    if (airFrames < 3 || 다운 카운터 > 0) && 본체+0x734 >= 3:
        X.y = max(0.98·X.y − g, 0)
if 현재 상태가 Free([2])가 아니거나 특수 0x12:
    v = 0.98 · 본체+0x73c                                 // [0x71058bbc74]
    if airFrames >= 3 && 다운 카운터 모두 <= 0:            // 3 = [0x71058bbc80]
        v -= g
    본체+0x73c = v
else:
    본체+0x73c = 0
if v + X.y > 0.001 || airFrames >= 4: 본체+0x740 = v + X.y  else 본체+0x744 = 0
본체+0x734 += 1
```

같은 꼴(`v = 0.98v`, 3프레임째부터 `−g`)이 `0x71024b9464`(다른 이동 동작의 수직 속도)에도 있고, `0x71024c0b38`은 목표 높이 h를 주면 `v=0.98v−g; y+=v`를 v ≤ 0까지 반복해 높이가 맞는 초기 속도를 이분 탐색합니다(점프대 등). 이 역산 루프는 **첫 프레임부터 중력**을 빼므로, 게임이 "수직 속도 모델 = 매 프레임 `v ← 0.98v − g; y += v`"를 전제로 함을 보여 줍니다 **[판독]**.

### 4.3 Phive 쪽 중력 [판독]

- 상태 S(ctrl+0x20) 생성자 `0x7103a862cc`: 기본 중력 G0 = S+0x1dc..+0x1e4 = 세계 설정 `[[*0x71057906f0]+0xe8]+0xb8` → +0x2a4..+0x2ac에서 복사(세계 설정이 없으면 생성자 기본 (0, −9.8, 0)), 방향 S+0x1e8 = normalize(sign(scale)·G0), 배율 S+0x1f4 = 1.0, 실효 중력 S+0x1f8 = 배율·G0, 상한 S+0x204 = 200. 세계 설정의 런타임 값은 확인하지 않았다 **[미확정]**(기본값 −9.8은 [판독]).
- ctrl vt 0x1e8 `0x7103a87898` setGravityScale(s): 부호가 바뀌면 방향 재계산, S+0x1f4 = s, S+0x1f8 = s·G0. vt 0x1e0 get, vt 0x1f0 = &S+0x1f8, vt 0x1f8 setBaseGravity(G0).
- 게임은 매 프레임(메인 계산 줄 4688~4699):
  ```
  scale = (airFrames >= 3 && 다운 카운터 모두 <= 0 && !param_16[2]) ? g·60·60/9.8 : 0
  ctrl.setGravityScale(scale)            // g=0.008 → 2.9387755
  ```
  즉 Phive가 중력을 쓰는 단계에서도 `|G0| = 9.8`, dt = 1/60이면 프레임당 속도 변화가 정확히 g가 되도록 맞춘다 **[판독: 식]**, dt=1/60은 **[추정]**.
- 그러나 SplPlayer에서 공중 상태(GameInAir)는 `0x71024f4270`이 `+0x14 = 2`, `+0x1c = 1`로 바꿔 두므로, 공중 갱신은 `vel = 게임이 넘긴 이동 속도`이고 중력(frame+0x18)을 쓰지 않는다 **[판독]**. 지상 상태(GameOnGround)는 중력 성분을 쓰지만 지상에서는 airFrames < 3이라 scale = 0이다. 따라서 **실제 낙하를 만드는 것은 §4.2의 게임 코드**이다 **[판독]**. (airFrames ≥ 3인데 Phive 상태가 지상인 경우—급경사 미끄러짐 등—에는 Phive 중력이 작용할 수 있으나 확인하지 않음 **[미확정]**. 4차: 세계 기본 중력 런타임 값·dt writer는 이번에도 미해소.)

### 4.4 점프 곡선 [원본 실행(함수 연결)] — 정정

> 정정(2026-10-02 [move]): 이전 표(중력 1프레임째부터 12프레임·0.6327 / 3프레임째부터 14프레임·0.8078, `web/tools/physics_jump.py`)는 (1) 점프 프레임의 첫 이동량이 감쇠 전 0.115라는 것, (2) 이동 속도 y의 별도 보정(`0x710245f964`)이 최종 y에 더해진다는 것, (3) 점프 버튼 유지 가산, (4) 상수 비트(g = 0x3c03126e, 점프 = 0x3deb851e, 둘 다 십진 상수의 최근접 f32보다 1ulp 작음)를 반영하지 않아 틀렸다. `physics_jump.py`는 `F(0.008)`·`F(0.115)`를 써서 비트도 다르다(역산 모델 `0x71024c0b38` 재현 용도로만 남김).

공중 프레임 +0xc0 의 수명(판독): 점프 프레임 메인 계산에서 `0x710246b32c`가 0을 쓰고, 같은 프레임 슬롯19에서 Phive가 공중 상태이므로 `0x710246b574`가 1로 올린다. 메인 계산의 수직 갱신은 그 앞 프레임 값을 읽으므로 점프 뒤 1·2번째 프레임은 감쇠만, 3번째부터 −g. 프레임 순서·근거: [../player/movement_physics.md](../player/movement_physics.md) §3.3, §6.4.

| 입력(평지, 0AP, 스틱 중립) | 최고점 프레임(점프 프레임=1) | 최고 높이(유닛) | y ≤ 0 프레임 |
|---|---|---|---|
| 탭 | 14 | 0.84145 | 30 |
| 5프레임 유지 | 16 | 1.06384 | 34 |
| 10프레임 유지 | 19 | 1.29583 | 38 |
| 계속 유지 | 30 | 1.73148 | 53 |

- 실행: `PY web/tools/move_jump_emu.py --hold N [--json …]` — `0x71024a7d00`(중력 `0x71024c9684` 포함), `0x710246b574`, `0x710245f964`를 unicorn으로 원본 그대로 실행하고 재구현과 비트 비교(4경우 불일치 0). 점프 대입·카운터 리셋·유지 가산·Phive 적분·착지는 판독대로 대체.
- 종단 속도: 수직 속도 −g/(1−0.98) = −0.4, 이동 속도 y −0.0025 → 합 약 −0.4025 유닛/프레임 **[재구현 계산]**.
- Phive GravityScale = 2.93877554(공중 ≥ 3이고 다운 카운터 0일 때). 공중에서는 Phive가 쓰지 않는다(§4.3).
- 역산 모델(`0x71024c0b38`, 점프대 등): 높이 0.628720 → 초기 속도 0.114695(±0.01 이분 탐색) — `physics_jump.py` [재구현 계산]. 이 모델은 첫 프레임부터 −g를 빼므로 실제 점프 곡선과 다르다(목표 높이 맞춤용 근사).
- 다운 계열 카운터(+0xd60/+0xde0/+0xdf0/+0xe0c)는 [life]의 쓰러짐 구조체 T(본체+0xd58)의 T+8/+0x88/+0x98/+0xb4 타이머다 — [../combat/player_life.md](../combat/player_life.md). 0이 아니면 중력·GravityScale이 꺼진다(쓰러짐 연출 중 수직 속도는 감쇠만) **[판독]**.

## 5. 게임 ↔ Phive 속도 전달

### 5.1 게임 → Phive: `0x71024f4f7c(PC, v, flag)` [판독]

메인 계산 끝(줄 6531)에서 `v = param_17[0..2] + param_17[0x12..0x14]`(유닛/프레임)로 호출됩니다.

```
if PC+0x30 != 0:                                   // 워프·리셋 직후 경로(메인 계산이 1로 설정)
    ctrl강체.setLinearVelocity(v·60)               // 0x7103ae2890
else if |v|² >= 1.42e-14:
    vj = (현재 상태가 OnGround([0])이거나 [1]/[2]가 아니면) 본체+0x73c : 0
    m = (v − (0, vj, 0))·60
    if |m|² >= 1.42e-14: ctrl.setMoveVelocity(m)   // vt 0x68 → 방향+속력
    else ctrl.setMoveSpeed(0)
else ctrl.setMoveSpeed(0)
// 이후: [PC+0xe378](= SplResultPlayer)+0x1338 = v + ImpactAndReject 가속합/3600 + 본체+0x4bc.. (게임 속도, 유닛/프레임),
//       보조 강체(+0x48/+0x50/+0x58, ColBullet 계열)에 v·60 설정
// 정정(4차): 이전 판의 "PC+0xe378 표시용 위치"는 틀림. PC+0xe378은 결과 컴포넌트 SplResultPlayer이고 +0x1338은 속도다.
//   접지 판정이 이 값으로 '상승 중 바닥 접촉 무시'를 한다 — character_controller.md §4, §6.2
```

- 공중(InAir)에서는 vj = 0이라 수직 속도까지 포함한 v 전체가 이동 속도가 되고, GameInAir(+0x1c=1)가 그것을 그대로 강체 속도로 씁니다 → 공중 궤적은 게임 속도가 결정 **[판독]**.
- 지상에서는 +0x73c를 뺀 나머지만 넘기고, 점프로 +0x73c > 0.001이 되면 메인 계산(줄 4664~4682)이 이동 상태를 InAir([1])로 강제 전환합니다 **[판독]**.
- 정정(이전 [추정]): `param_17` = 본체+0xe4(최종 속도 구조체)이고, `0x710245aed8`이 `F[0..2] = 이동 속도(+0x114) + 3D 점프(+0x750) + (0, +0x73c, 0) + 보조 항들`로 만든다. 즉 v.y는 +0x73c를 그대로 더한 값이다 **[판독]** — [../player/movement_physics.md](../player/movement_physics.md) §6.7. 넘기는 값은 F[0..2] + 본체+0x12c(F[0x12..0x14], 프레임 시작에 0).

### 5.2 Phive → 게임 [판독]

| 읽는 값 | 위치 | 변환 |
|---|---|---|
| 발판 속도 | `[PC+0xe350]+0x3c..+0x44` | ×0.016666668 (`player_misc1.c` 718행) |
| 충격·밀어냄 가속도 | `[[PC+0xe360]+0x28]+0x08` / `+0x24` | (a₁+a₂)×0.016666668×0.016666668 = 1프레임 속도 변화 (`0x710245b2b4` 1736행, `0x7102475a54` 점프부, `player_slot19.c` 528행) |

이동 함수에서의 쓰임(`0x710245b2b4` 1720~1745행) **[판독]**: 원하는 이동 벡터 d의 방향 n에 대해 `push = max(0, n·(a/3600 + 본체+0x4bc..))`, `|d| ← max(0, |d| − 1.2·push)`(1.2 = `[0x71058bbef8]`). 같은 방향으로 밀리고 있으면 그만큼 입력 속도를 깎는다. 점프부는 `jump −= max(0, 본체+0x4c0 + a.y/3600)`.

## 6. 탄 바디 (슈터 탄 +0x138)

### 6.1 데이터 [데이터]

- `BulletShooterBase.phive__ControllerSetParam`: `$parent` BulletEmpty(`CColEntityNamePathAry: []`), `CharacterControllerName: "BulletSimple"`. `PathCharacterController`·강체 목록 없음. PhiveConfig `CharacterComponentPresetCollection`에는 `BulletSimple` 프리셋이 없다(Default, KbtkTest, FlyerTest, SplPlayer, SplGround, SplFlyer뿐).
- 탄 바디는 액터 `BulletBodyRef` → `BulletBodyControllerEntity` → UnitArray 1개(`BulletBodyParam: BulletSimple`(LayerEntity `SplInkBullet_FriendThrough`, BlockableLayerHitMask `HitAll`), `ShapeParam: BulletShooterBase`(구 GroundOnly/ExceptGround)).
- PhiveConfig `MotionPropertiesCollection`에 `SplBullet`(GravityScale 0, LinearDamping 0, MaxLinearSpeed 1000, MaxAngularSpeed 100)이 있다. 탄 바디가 이것을 쓰는지는 **[미확정]**.

### 6.2 코드 [판독]

- 탄 바인드 `0x7101644650`: 탄+0x108 = 슬롯52(생성 정보), **탄+0x138 = 슬롯67 `0x7101763948`이 만든 0x40 B 래퍼**(vtable `0x710559f3f8`, 35슬롯), 이어서 래퍼 slot30(+0xf0) `0x71016cb660`으로 초기화.
- 래퍼 초기화: 액터 컴포넌트(+0x208 표 인덱스 0x23) → +0x28 = 유닛 목록(래퍼+0x18: +8 개수, +0x10 배열). 각 유닛 `+0x38` = 바디. 바디 +0xf8 셰이프에서 이름 `GroundOnly` → 래퍼+0x20, `ExceptGround` → 래퍼+0x28(복합 셰이프면 래퍼+0x30, 자식 번호 +0x38/+0x3c).

| 래퍼 슬롯(오프셋) | 함수 | 동작 |
|---|---|---|
| 7 (0x38) | `0x71016cb0a0` | **setVelocity**: 모든 유닛 바디에 `+0xc4..+0xcc = v·60`, `+0xdc..+0xe4 = v·60` |
| 9 (0x48) | `0x71016cb100` | 바디 +0xdc × 0.016666668 반환 |
| 10 (0x50) | `0x71016cb174` | 바디 +0xc4 × 0.016666668 반환 |
| 15 (0x78) | `0x71016cb210` | 바디마다 접촉 목록(+0x100)을 훑어 가장 위를 향한 접촉 법선 y를 구하고 전역 임계값(`[0x7105858358]`)과 비교, 프레임 내 캐시(+8 결과, +9 계산함) |
| 18,19 (0x90,0x98) | `0x71016cb3a0`, `0x71016cb3d0` | 현재 유닛(목록+0x28 번호)의 바디 |
| 20,21 (0xa0,0xa8) | `0x71016cb400`, `0x71016cb460` | 바디+0x90 bit1 켜기/끄기, 모션(vt0x38)+0xc = bit1 ? 0 : 바디+0xf4 |
| 22~25 | `0x71016cb4c0`… | 충돌 필터(바디+0x138 → +8) 비트 0..5, 6..11 쓰기/읽기 |
| 26,27 (0xd0,0xd8) | `0x71016cb590`, `0x71016cb5ec` | GroundOnly / ExceptGround 구 반경(+0xe4) 설정(±1.19e-7 넘게 달라질 때만) — 반경식은 [combat](../combat/damage_hit.md) |
| 33,34 (0x108,0x110) | `0x71016cbd04`, `0x71016cbd08` | 빈 함수(탄 갱신 앞뒤 훅) |

- 탄 위치 읽기 `0x710164434c`: 래퍼 vt0x98 바디가 있으면 바디 **+0x94**(위치) 사용, 없으면 강체(vt0x88)의 행렬 이동 성분(+0xe4 또는 모션+0x14).
- 탄 이동 상태머신은 **탄+0x1118의 게임 쪽 사본**만 읽고 쓴다(getVelocity `0x7101762d00`). 바디 ×60/÷60 왕복을 거치지 않으므로 상태머신 결과는 바디 쪽 반올림의 영향을 받지 않는다.

### 6.3 객체 사슬: 컴포넌트 → 유닛 → phive 탄 바디 [판독]

(2026-10-02 3차 해소. 이전 판의 "바디 vtable·적분 함수 미확정"을 아래로 대체합니다. 이전 `physics_memscan.py` 전수 검색이 놓친 이유: 적분 함수는 `ldr x8,[x21,#0x94]!`(사전 인덱스)로 기준을 +0x94로 옮긴 뒤 `ldp s1,s2,[x21,#0x30]`으로 +0xc4를 읽어서 오프셋 0xc4 명령이 없음.)

```
액터.컴포넌트표[0x23] = BulletBodyComponent (vtable 0x710557ada0, 등록 0x710133fc70: 정적 초기화로 팩토리 0x710557acb0 등록)
  초기화 slot5 0x710133ffd8:
    +0x20 = 액터, +0x30 = 유닛 엔티티 E(0x50 B, vtable 0x71055539e8, 초기화 0x71010036a8)
    +0x40 = 접촉 리스너 L(0x58 B, vtable 0x7105553ae0, +8 보조 vtable 0x7105576010, +0x10 보조 0x71055760a0)
    모든 유닛 바디: body+0x110 = L, body+0x178 = L+8
  slot9 0x71013405e0: 유닛+0x90 이면 월드(→+0x120 탄 바디 관리자)에 바디 추가 0x7103adf738, 유닛 공간 격자 위치 = body+0x94 (0x71012daa38)
  slot7 0x710134051c / slot10 0x7101340788: 바디 제거(0x7103b0a148 / 0x7103b0a004)
E (+8 개수, +0x10 유닛 배열): 유닛(0x98 B, vtable 0x7105553a20)마다
    유닛+0x40 = 형상(0x7103a49c44), 유닛+0x38 = 바디 = 0x7103b0ada8(desc) , body+0x180 = 유닛
탄 바디 래퍼(탄+0x138, vtable 0x710559f3f8, §6.2)의 +0x18 = E
```

**phive 탄 바디 클래스** — 생성 `0x7103b0af78`(0x198 B, vtable `0x7105749990`, 기반 `0x7105749938`), 설정 `0x7103b0ada8`. 기준 객체: 바디.

| 오프셋 | 타입 | 의미 | writer | reader |
|---|---|---|---|---|
| +0x08 | ptr | 월드 쪽 핸들(캐스트 첫 인자) | 생성 | 스텝 |
| +0x10 | s32 | 월드 번호(0이면 `[*0x710599dfa8+0xe8]`) | desc+0 | 스텝, 추가·제거 |
| +0x90 | u32 | 플래그. bit1 = 충돌 끔(모션+0xc = 0) | 래퍼 slot20/21 | |
| +0x94 | vec3 | **위치** | desc+0x10, 스텝 | 탄 위치 `0x710164434c`, 리스너 |
| +0xa0..+0xc0 | 3×3 | 회전(진행 방향 행렬) | 리스너 slot6 | 캐스트(형상 방향) |
| +0xc4 | vec3 | **현재 속도(유닛/초)** | 래퍼 setVelocity(v·60), 스텝(충돌 시 0) | 스텝, 래퍼 slot10(÷60) |
| +0xd0 | vec3 | 각속도(모션 종류 3일 때만 사용) | | 스텝 |
| +0xdc | vec3 | **이번 스텝에 쓴 속도**(스텝 시작 시 +0xc4 복사, 충돌로 지워지지 않음) | 스텝, setVelocity | 래퍼 slot9(÷60), 리스너 slot6(방향) |
| +0xf4 | s32 | 충돌 필터 정보 원본 | desc+0x48 | 래퍼 slot21 |
| +0xf8 | ptr | 형상 | desc+0x30 | 캐스트 |
| +0x100 | ptr | 접촉 목록(용량 desc+0x38 = 32) | 생성 `0x7103a62e78`, 스텝 시작에 비움 | 리스너, 래퍼 slot15 |
| +0x108 | s32 | 모션 종류. 탄은 **2**(desc+0x3c, `0x71010036a8`의 `0x200000020`) — 3이 아니므로 각속도 적분 없음 | 생성 | 스텝 |
| +0x110 | ptr | 접촉 리스너 L | `0x710133ffd8` | 스텝 |
| +0x118..+0x128 | 목록 노드 | 관리자 목록(+0x28) 연결 | `0x7103adf738` | 관리자 스텝 |
| +0x138 | ptr | 충돌 필터 객체(+8 비트 0..5 레이어, 6..11 하위 레이어) | `0x7103b0ae68` | 래퍼 slot22~25, 접촉 분배 |
| +0x178 | ptr | 접촉 수신자(=L+8) | `0x710133ffd8` | `0x71012d66cc` |
| +0x180 | ptr | 유닛 | `0x71010036a8` | 리스너 slot6 |
| +0x188 | u8 | bit0이면 리스너가 회전 갱신 안 함 | 생성 0 | 리스너 slot6 |
| +0x18c | f32 | 관통력(기본 **−1.0** = 항상 막힘) | 생성 | 리스너 slot5 |
| +0x190 | ptr | 관통 판정 배율 키(기본 `0x7104a98138`) | 생성 | 리스너 slot5 |

desc(`0x71010036a8`이 스택에 구성): +0x10 위치 = 0, +0x1c 속도 = **0**, +0x30 형상, +0x38 접촉 용량 32, +0x3c 모션 종류 2, +0x40.. 필터(`0x7101004e00`). 즉 **생성 직후 바디 속도는 0**이고 탄 슬롯54의 setVelocity가 처음 속도를 넣는다 **[판독]**.

### 6.4 한 물리 스텝 안의 탄 바디 (관리자 `0x7103adeb4c`/`0x7103adec7c`, 바디 스텝 `0x7103b0a2bc`) [판독]

월드(`*0x710599dfa8 + 0xe8`[번호], vtable `0x7105748188`, 생성 `0x7103ac71c8`)의 스텝 단계 `0x7103ac9a00`이 끝에서 `월드+0x120`(탄 바디 관리자)의 `0x7103adec7c`로 꼬리 호출하고, 관리자는 목록 `+0x28`의 바디마다 `0x7103b0a2bc`를 **한 번씩** 부릅니다(순차 경로; 병렬 경로는 같은 함수를 작업 람다 `0x7103adfa80`으로 실행). 서브스텝은 없습니다.

```
dt  = 월드+0x24                                   // 0.016666668f, 아래
body+0xdc = body+0xc4                             // 이번 스텝 속도 보관
if 모션==3: body+0xe8 = body+0xd0
접촉목록(+0x100) 비움
p0 = body+0x94
p1.x = fadd(fmul(dt, vx), p0.x)  (y, z 같음)      // 0x7103b0a3d0~0x7103b0a3f4, fmadd 아님
ang = 모션==3 ? dt·ω : 0
0x7103c55968(월드, body, 형상, 접촉목록, &p0, &p1, &회전, &ang)   // 쓸어 넘기기(p0, p1 읽기만)
body+0x94 = p1
(모션==3이면 회전 적분 — 탄은 해당 없음)
0x7103a6144c(접촉목록)                            // 정리
minF = FLT_MAX
for c in 접촉목록:
    f = (c.flags(+0x68) & 0x1060) ? c+0x60 : 0     // 쓸어 넘긴 구간에서의 비율 0..1 (처음부터 겹침은 0)
    if minF + 1e-7 < f: c.표시 |= 2 (무시); continue
    if L.vt[0x20](c, body, &p0, &p1): c.표시 |= 2; continue      // 0x7101006410: 특수 구형 물체 안쪽 접촉 무시
    if !L.vt[0x28](c, body, ...): continue                        // 0x7101006718: 막는 접촉인가
    if f < minF (f==0이면 0 < minF):
        body+0x94 = p0 + f·(p1 − p0)            // fsub → fmul → fadd (0x7103b0a90c)
        body+0xc4 = 0
        minF = f
if body.vt[0x40]() : 접촉을 다른 수집기에 보고(0x7103a62948)
L.vt[0x30](body)                                  // 0x71010067e0: 스텝 후 처리
```

- **dt 값**: 월드 생성 호출부 `0x7103db385c`가 desc+0x24(x26 = desc+0x5c−0x38)에 `0x3c888889`(0.016666668)를 쓰고, 생성자 `0x7103ac71c8`가 `월드+0x20 = +0x24 = +0x2c = min(desc+0x24, 0.99899f)`, `+0x28 = +0x30 = 1/dt`로 둡니다 **[판독]**. phive 범위(0x7103a80000~0x7103b40000)의 다른 `str s,[x,#0x24]` 15곳 중 7곳(`0x7103ade2f0`, `0x7103a8d068`, `0x7103a8da6c`, `0x7103a8ab1c`, `0x7103a8907c`, `0x7103ae9230`, `0x7103ab4518`)은 월드가 아닌 객체였고 나머지 8곳과 범위 밖 경로는 확인하지 않았습니다 **[추정: 실행 중 1/60 고정]**. 컨트롤러 프레임 정보 dt(§3.3 +0x44)도 같은 월드+0x24입니다.
- **막는 접촉**(L slot5 `0x7101006718`): 접촉 플래그 +0x68 bit1이 꺼져 있으면 막지 않음(접촉만 기록). bit1이 켜져 있으면 `body+0x18c < 0`(기본 −1)이면 막음. 0 이상이면 상대 바디(+0x70/+0x78) +0x2a4 값과 `body+0x18c × 배율(0x7101a856e8(DamageRate 계열 표, body+0x190, 상대+0x2a8))`을 비교해 관통하면 bit1을 지우고 막지 않음 **[판독]**. 이 관통력(+0x18c)을 쓰는 곳은 찾지 못함 **[미확정]**. 접촉 bit1이 충돌 필터 표(LayerEntityParamTable 값 2 = 충돌, combat 문서)에서 오는지는 **[추정]**.
- **충돌 응답 = 멈춤**: 반사·미끄러짐·관통 보정 없음. 위치는 첫 막는 접촉 시점으로 되돌리고 속도는 0. 게임 쪽 속도 사본(탄+0x1118)은 그대로라 다음 프레임 슬롯54가 다시 setVelocity 합니다(실제로는 아래 콜백이 정지·소멸 처리) **[판독]**.
- **쓸어 넘기기**(`0x7103c55968`): 형상의 p0·p1 AABB를 합쳐 넓은 단계 질의(월드 vt+0x3b8) → 후보마다 좁은 단계 처리기 표 `0x7105756468`(4개: `0x7103c52d30`, `0x7103c5368c`, `0x7103c54140`, `0x7103c54de4`)에서 상대 바디가 움직이는지(선속도 +0x144/+0x2d4, 각속도 +0x138/+0x2c8이 0인지)와 모션 종류로 하나를 고름. 처리기 내부(TOI 계산)는 판독하지 않음 **[미확정]**.

### 6.5 스텝 후 처리 (L slot6 `0x71010067e0`) [판독]

```
if !(body+0x188 & 1):
    d = body+0xdc;  |d|>0 이면 정규화
    if |d| != 0: body+0xa0.. = 0x71012500d4(진행 방향 d로 만든 회전)     // 막혀도 이번 스텝 속도 방향
if body+0x180(유닛): 유닛 공간 격자 위치 갱신(0x71012daa38, 유닛+8 = body+0x94)
작업 J(vtable 0x7105553b78, 바디 포인터)를 접촉 반응 큐에 복사(0x71012e76c0 → 큐 +0x200/+0x230)
```

큐는 `PhysicsContactReactionSequencer(Entity)`(생성 `0x71012e508c`, vtable `0x7105576640`, 기반 생성자 `0x7103c7e4d8`, 비우기 = 슬롯36 `0x71012e55cc`: 우선순위 힙에서 꺼내 작업 slot0 실행)입니다. 이 시퀀서는 `0x71012e7768`이 만들고 월드 리스너 목록(월드+0x1c0)에 등록합니다. 즉 **탄 충돌 콜백은 바디 스텝 안에서 바로 불리지 않고, 접촉 반응 시퀀서가 큐를 비울 때 실행**됩니다 **[판독]**. 시퀀서가 프레임 안에서 언제 도는지(탄 슬롯18·19·21 대비)는 **[미확정]**(§6.7).

### 6.6 접촉 → 탄 콜백 분배 [판독]

```
J.slot0 0x7101006e24: 0x71012d6150(body+0x100 접촉목록, 방문자 vtable 0x7105576030)
  방문자 0x71012d2e4c (접촉쌍마다):
    상대 레이어 1(CustomReceiver)이면 생략, 상대 바디의 사용자 수신자(+0x2b8)가 처리하면 끝
    수신자 = 0x71012d66cc(쌍) = 탄 바디 쪽이면 body+0x178 (= L+8)
    0x71012d2cb8(L+8, 방문자 0x71055760d8):
       액터 = L+0x38(= 컴포넌트+0x20), 행동 객체 = 액터+0x90
       선행 수신자들(+0x68 목록).vt[0xc0] → 행동.vt[0xb0] (= 탄 슬롯22) → 후행 수신자들(+0x78).vt[0xc0]
탄 슬롯22 (ShooterBase 0x71017504f4: 데미지·넉백·히트 이펙트, combat 문서) → 0x7101763310 → 0x7101646910
0x7101646910(탄, 접촉):
    if !슬롯64()(ShooterBase: 슬롯63 = 0): 접촉 목록에 막는 접촉(+0x68 bit1)이 하나도 없으면 return
    상대 바디 = 쌍의 반대쪽(+0x70/+0x78), 레이어 = 상대 필터(+0x180→+8) & 0x3f
    if 레이어 != 3(Ground): 슬롯60
    else: n = 0x71018a5c70(접촉): 첫 막는 접촉의 법선(이 탄 쪽 기준, 0x71012d4f8c 캐시 +0xc/+0x18)
          n.y > T ? 슬롯58 : 슬롯59           // T = [0x7105858358] = 0.64144969 (cos 50.1°)
```

레이어 번호는 PhiveConfig `LayerEntityCollection` 순번(0 NoHit, 1 CustomReceiver, 2 GameCustomReceiver, **3 Ground**, 4 Water, 5 SplPlayer, …) **[데이터]**. 임계값 T는 정적 초기화 `0x71018a5b50`을 unicorn으로 실행해 얻음(`analysis/bulletbody/bss_5858340.json`, 이웃 값 0.0854/−0.2571/−0.5721은 state 문서의 표면 상수와 같음) **[실행(에뮬)]**. 래퍼 slot15 `0x71016cb210`(접지 판정)도 같은 T를 씁니다.

슬롯별 동작(ShooterBase)은 [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md) §3.3에 정리합니다.

### 6.7 프레임 안 순서와 남은 것

| 단계 | 근거 | 수준 |
|---|---|---|
| 탄 슬롯18: 래퍼+9(접지 캐시) 초기화, 래퍼 훅 0x108, prevPos = body+0x94, age++, 슬롯54(setVelocity), 슬롯57(반경), `+0x12a==1`이면 속도 0 | `0x71016460fc` | [판독] |
| 물리 스텝: 바디마다 `0x7103b0a2bc` 1회 | §6.4 | [판독] |
| 접촉 반응 시퀀서: 탄 슬롯22 → 58/59/60 | §6.5~6.6 | [판독], 위치 [미확정] |
| 탄 슬롯21(`0x7101646544`): body+0x94로 표시 위치 보간 0.88, 슬롯56(이동 거리·스플래시), `+0x12a`를 1 줄이고 1→0이면 소멸 요청 | 디컴파일 | [판독] |
| 탄 슬롯19(`0x71016461bc`): 래퍼 훅 0x110, 슬롯55(꼬리·보관 도색), 낙하 소멸 | 디컴파일 | [판독] |

슬롯18이 "물리 전", 슬롯19·21이 "물리 후"라는 것은 슬롯18이 속도를 넣고 슬롯21·56이 바디 위치로 이동 거리를 재는 구조에서 나온 **[추정]**입니다. 슬롯18의 `+0x12a == 1` 검사는 접촉 처리가 슬롯21(감소) 뒤·다음 슬롯18 앞에 있어야 의미가 있으므로 그 순서로 봅니다 **[추정]**. 시퀀서·액터 계산 단계의 실제 순서를 확정하려면 시퀀서 기반 클래스(`0x7103c7e4d8`, 다른 파생 생성자 7곳: `0x7101324220`, `0x71013250d0`, `0x71027bda30`, `0x7102c3d954`, `0x7103146a3c`, `0x7103cbdf6c`, `0x7103db3ed8`)의 실행 목록과 액터 계산 단계의 호출 위치를 추적해야 합니다.

### 6.8 재구현 비교 (`web/tools/bulletbody_integrate.py`) [재구현 계산]

`p += fl(dt·fl(60·v))`(원본 판독식)과 `p += v`(이전 가정)를 슈터 6종 × 발사각 0°/+30°/−20°, 40프레임으로 비교:

| 항목 | 결과 |
|---|---|
| `fl(dt·fl(60·v)) != v`인 비율(무작위 v ∈ [−3,3], 20만 개) | 61% |
| 위치 최대 차이(40프레임) | 2.9e-6 유닛(WeaponShooterNormal 0°), 나머지 ≤ 1.9e-6 |
| 예: WeaponShooterNormal 0°, 40프레임 z | `p+=v` 16.448555 / 바디식 16.448557 |

비트 일치가 필요하면 바디식을 써야 합니다. 상태머신은 탄+0x1118 사본만 쓰므로 이 차이는 이동 거리(+0x1200)·스플래시 생성 지점·도색 위치·충돌 판정에만 들어갑니다. 결과 `analysis/bulletbody/integrate_compare.json`.

## 7. 웹 포팅 구조

| 모듈(웹 권장 이름) | 책임 | 원본 대응 |
|---|---|---|
| `PlayerVertical` | 수직 속도 `vy`(본체+0x73c)·공중 프레임 수·중력값 | `0x71024a7d00`, `0x71024c9684` |
| `CharacterBody` | 캡슐 충돌·접지·이동(Phive 대체). 공중에서는 게임 속도를 그대로 적용 | ctrl + GameInAir(+0x1c=1) |
| `ImpactAccumulator` | 다른 물체에 밀릴 때의 가속도 2개와 감쇠 | ImpactAndReject `0x71012adb58` |
| `BulletBody` | 탄 위치 적분·구 쓸어 넘기기 충돌(바닥 전용/그 외 2개)·멈춤 응답·접촉 큐 | 탄 바디 래퍼 `0x710559f3f8`, phive 탄 바디 `0x7105749990`, 스텝 `0x7103b0a2bc` |
| `BulletContactRouter` | 접촉 → 탄 슬롯22 → 바닥/벽/그 외 분기 | `0x7101646910` (§6.6) |

의사코드(한 프레임, 플레이어 수직 성분만):
```ts
const G = Math.fround(0.008), K = Math.fround(0.98);
function gravity(p: Player): number {              // 0x71024c9684 (특수 상태 분기는 §4.1)
  if (p.special === 0x1c || p.blockGravity) return 0;
  return G;
}
function updateVertical(p: Player) {               // 0x71024a7d00 (Free 상태·임펄스 X 생략)
  const g = gravity(p);
  let v = Math.fround(K * p.vy);
  if (p.airFrames >= 3 && !p.downCounterActive) v = Math.fround(v - g);
  p.vy = v;
}
// 위치: 공중에서는 최종 속도(유닛/프레임)를 그대로 1프레임 적분 (Phive GameInAir +0x1c 모드)
```
원본과 같게 유지할 것: 0.98 곱 → g 빼기 순서, airFrames ≥ 3 조건, f32 반올림. 중력 스케일(2.9387755)은 웹에서 Phive를 쓰지 않으면 필요 없습니다.

탄 바디(웹 권장 이름, 원본 필드는 주석):
```ts
const DT = Math.fround(1 / 60);                     // 월드+0x24 = 0x3c888889
const FLOOR_NY = Math.fround(0.64144969);           // [0x7105858358]
class BulletBody {
  pos: Vec3;            // body+0x94
  velSec = ZERO;        // body+0xc4 (유닛/초)
  stepVelSec = ZERO;    // body+0xdc
  setVelocity(v: Vec3) { this.velSec = this.stepVelSec = v.map(c => Math.fround(c * 60)); }  // 0x71016cb0a0
  step(world: World): Contact[] {                   // 0x7103b0a2bc
    this.stepVelSec = this.velSec;
    const p0 = this.pos;
    const p1 = p0.map((c, i) => Math.fround(Math.fround(DT * this.velSec[i]) + c));
    const contacts = world.sweepSphere(this.shapes, p0, p1);   // 0x7103c55968 (f: 0..1)
    this.pos = p1;
    let minF = 3.4028235e38;
    for (const c of contacts.sort(byF)) {
      if (minF + 1e-7 < c.f) { c.ignored = true; continue; }
      if (!c.blocking) continue;                                // 접촉 +0x68 bit1, 관통력 기본 −1
      if (c.f < minF) {
        this.pos = p0.map((a, i) => Math.fround(a + Math.fround(c.f * Math.fround(p1[i] - a))));
        this.velSec = ZERO; minF = c.f;
      }
    }
    return contacts;                                            // → 접촉 반응 큐(프레임 안 처리 위치는 §6.7)
  }
}
function routeContact(b: ShooterBullet, c: Contact) {          // 슬롯22 끝 → 0x7101646910
  if (!c.anyBlocking) return;
  if (c.otherLayer !== LAYER_GROUND) return b.onHitOther(c);   // 슬롯60
  return c.normalTowardBullet.y > FLOOR_NY ? b.onHitFloor(c)   // 슬롯58
                                           : b.onHitWall(c);   // 슬롯59
}
```

## 8. 검증

| 종류 | 내용 | 결과 |
|---|---|---|
| 원본 실행(에뮬) | 정적 초기화(`player_initemu.py`, 기존)로 얻은 상수: 0.008, 0.98, 3, 4 | `analysis/player/bss_consts_58bb000.txt` |
| 원본 명령 판독 | §3~6의 식 | 디컴파일 + `disasm.py` 대조 |
| 재구현 계산 | `.venv/Scripts/python web/tools/physics_jump.py --json analysis/physics/jump_curve.json` | 역산 모델만 유효(§4.4 정정 참고) |
| 원본 실행(함수 연결) | `web/tools/move_jump_emu.py --hold {0,5,10,60}` — 수직 속도·공중 카운터·공중 보정 원본 3함수를 프레임 순서대로 실행 | §4.4 표, 재구현과 비트 일치 |
| 데이터 확인 | 프리셋·모션 속성·탄 ControllerSet | §2, §6.1 |
| 원본 실행(에뮬) | 정적 초기화 `0x71018a5b50` → 접촉 법선 임계값 0.64144969(`player_initemu.py 0x7105858340 0x7105858370 --all-init`) | `analysis/bulletbody/bss_5858340.json` |
| 원본 명령 판독 | 탄 바디 스텝 `0x7103b0a2bc`의 적분·충돌 보간 명령(`disasm.py`로 fmul/fadd 분리 확인), setVelocity `fmul ×60.0f`, 월드 dt 상수 `0x3c888889` | §6.4 |
| 재구현 계산 | `.venv/Scripts/python web/tools/bulletbody_integrate.py --json analysis/bulletbody/integrate_compare.json` | §6.8 |

스텁·미검증: 플레이어 메인 계산(점프 판정·이동)과 Phive 스텝은 원본으로 실행하지 않았다(수직 속도·중력·공중 카운터·공중 보정 함수만 원본 실행, 나머지는 판독대로 대체). 탄 바디 스텝은 명령 판독뿐이고 원본 실행 비교는 없다. 좁은 단계 TOI 계산(`0x7105756468` 처리기 4종), 접촉 정리 `0x7103a6144c`의 정렬 기준은 판독하지 않았다.

## 9. 미확정 사항과 다음 근거

| 항목 | 상태 | 필요한 근거 |
|---|---|---|
| 본체+0xc0(공중 프레임) 증가·초기화 시점 | **해소 [판독 + 실행(함수 연결)]** | 슬롯19 `0x710246b574`(+1)/`0x710246b32c`(0), 점프 프레임 메인 계산 `0x710246b32c`(0) — §4.4. 남은 것: Phive가 점프 프레임 스텝 중 OnGround로 되돌리지 않는다는 가정 [추정] |
| 최종 속도 v(param_17)의 수직 성분 구성 | **해소 [판독]** | `0x710245aed8` — §5.1 |
| 이동 벡터의 `0.92y − 0.0002`와 +0x73c의 관계 | **해소 [판독]** | `0.92y − 0.0002`는 이동 속도(+0x114) y 보정(`0x710245b2b4` 끝 `0x710245edc0`), 최종 y = 둘의 합 |
| 세계 기본 중력(+0x2a4) 런타임 값, dt(+0x24) | 미확정(−9.8, 1/60 추정) | `-9.8` f32 상수는 main 전체에서 S 생성자 1곳뿐이고 PhiveConfig에도 중력 항목이 없다(2026-10-02 [move] 확인). 영향 범위: 공중 이동은 GameInAir(+0x1c=1)라 G0와 무관, 지상은 scale 0 → **플레이어 궤적에는 공중 ≥ 3인데 Phive 상태가 OnGround인 경우에만 영향**. dt는 게임 속도 ×60을 Phive가 적분하는 데 쓰이므로 1/60이 아니면 프레임당 이동량이 달라진다 — `[[*0x71057906f0]+0xe8]+0x24` writer(세계 스텝) 추적 필요 |
| 특수 상태 0x18/0x1b/0x1c, `+0xa818` 컴포넌트 이름 | **해소 [판독+데이터]** | 0x18 Jetpack, 0x1b Skewer, 0x1c SuperLanding(본체+0x65c = 10 + 특수 열거), +0xa818 = spl::PlayerPeriscope(`player_components.tsv`). Periscope +0x38/+0xb0 의미만 미확정 |
| 탄 바디 적분·충돌 응답 | **해소**(2026-10-02, [판독]) | §6.3~6.4 |
| 탄 접촉 반응 시퀀서의 프레임 내 실행 위치(→ 첫 명중 age) | 추정(물리 후·슬롯21 뒤·다음 슬롯18 앞) | §6.7의 시퀀서 기반 클래스 `0x7103c7e4d8` 실행 목록, 액터 계산 단계 호출 위치 |
| 좁은 단계 TOI(처리기 4종)·접촉 정렬 기준 | 미판독 | `0x7103c52d30`/`0x7103c5368c`/`0x7103c54140`/`0x7103c54de4`, `0x7103a6144c` |
| 관통력 body+0x18c를 쓰는 탄 | 미확정(기본 −1 = 항상 막힘) | `str s?,[x?,#0x18c]` 전수 검색, `0x7101a856e8` 표 |
| 월드 dt를 런타임에 바꾸는 경로 | 추정(1/60 고정) | 월드+0x24 쓰기 나머지 8곳 |
| shapeTag → 재질표·충돌 필터(hknp 코덱·필터 구현) | 미확정 | 질의 문맥 +0x130의 [0] vt+0x40(코덱 decode)·[1] vt+0x40(필터) 구현 클래스. 월드 생성 `0x7103ac71c8` 안의 하위 객체 생성(`0x7103b1b33c`, `0x7103a72c28`, `0x7103ac3960` 등)에서 vtable을 찾을 것 |
| Phive OnGround/InAir 전이 조건·점프 프레임 공중 유지 | **해소 [판독]** (4차) | 상태 vt+0x30 `0x71012aa648`/`0x71012aa108`, SplResultPlayer `0x7102c5a3c8`·`0x7102c5dd20` — [character_controller.md](character_controller.md) §5~6 |
| 플레이어 캡슐·충돌 필터·재질 | **해소 [판독]+[데이터]** (4차) | character_controller.md §3 |
| 액터 계산 단계와 Phive 월드 단계의 프레임 내 순서 | 미확정(월드 단계 이름·함수만 판독) | character_controller.md §9 |
| 컴포넌트 배열이 프리셋 순서로 만들어지는지 | 추정 | 팩토리 호출부(`0x7103a8367c`를 부르는 프리셋 순회) 판독 |
