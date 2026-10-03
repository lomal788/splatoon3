# Phive 물리 계층 — 캐릭터 컨트롤러·중력·탄 바디

플레이어 이동과 슈터 탄이 게임 코드에서 계산한 속도를 Phive(Havok hknp 기반 물리 래퍼)로 넘기는 경로, Phive 캐릭터 컨트롤러가 한 스텝 안에서 속도를 만드는 순서, 중력이 실제로 어디서 더해지는지를 정리합니다. 작업 지침은 [../../분석.txt](../../분석.txt), 공용 사실은 [../README.md](../README.md)·[../02_code_and_params.md](../02_code_and_params.md).

이 문서를 쓰는 문서:
- [../player/movement_physics.md](../player/movement_physics.md) — 플레이어 목표 속도·가속·점프(§6.4~6.6, §11이 이 문서로 연결)
- [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md) — 슈터 탄 이동(§3.2, §11)

확정 수준: **[실행]** 원본 실행 / **[판독]** 원본 코드 판독 / **[데이터]** 데이터 / **[추정]** / **[미확정]**. 이 문서의 원본 실행 검증은 (1) 정적 초기화 에뮬로 얻은 상수, (2) 점프 곡선 함수 연결 실행([../player/movement_physics.md](../player/movement_physics.md)), (3) 프레임 작업 그래프 구성 함수 실행(§6.7, 5차)입니다. 탄 바디 스텝과 Havok 솔버는 원본으로 실행하지 않았습니다.

상태: 분석 진행 중. 4차: 플레이어 몸체·캡슐·접지 판정·상태 전이는 [character_controller.md](character_controller.md). 5차(2026-10-03): **프레임 안 실행 순서(액터 슬롯 18/19/20/21/22 ↔ Phive 월드 단계 ↔ 접촉 큐 소비)를 판독하고 그래프 구성 함수를 원본 실행으로 확인**(§6.7), 컴포넌트 배열 순서(§3.3)와 월드 생성 dt(§6.4)를 판독으로 확정. 웹 구현 없음.

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
| 프레임 안 실행 순서 (5차) | 작업 그래프 = 단계 4개 × 그룹 8개 장벽 사슬. 액터 그룹 = `ActorSystemSetting.CalcPriority`(Before 2, Default 3, After 4, Late 5). 한 프레임: 단계0[표적 슬롯18(그룹2) → 플레이어 슬롯18(3) → 탄 슬롯18(4) → Phive Entity 월드 갱신(그룹6: 캐릭터 컨트롤러·Havok 스텝·탄 바디 스텝·접촉 작업 등록)] → 단계1[접촉 반응 큐 비우기(그룹0: 탄 슬롯22→58/59/60) → 표적 슬롯19·20·21(2) → 플레이어 슬롯19·20·21(3, 카메라 메인 갱신 포함) → 탄 슬롯19·20·21(4)] → 단계2[Phive Sensor 월드(그룹0)] → 단계3. 같은 그룹 안 액터끼리는 순서 없음(병렬) — §6.7 | 구조 [판독], 그래프 간선 [실행], 액터 그룹 값 [데이터] |

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
| 5차 디컴파일·도구 | `analysis/decomp/r5_physics/`(order1: 물리 시퀀서·작업, mgr*: 관리자·그래프 구성, actor*/actorjob: 액터 단계 작업, behav1, cseq*: 접촉 반응 시퀀서, seqcreate/calcprio*: 생성·CalcPriority, group: 비교 그룹 공급자, bphsh), `web/tools/r5_physics_frameorder_emu.py`(그래프 원본 실행), `web/tools/r5_physics_chainscan.py`·`r5_physics_compslot.py`(필드→vtable 슬롯 호출 사슬 스캔), 결과 `analysis/completion/r5_physics_frameorder_emu.json` |

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
배열은 프리셋 `UpdateComponents` 데이터 순서 그대로 만들어진다 **[판독]**. 근거:
- PhiveConfig 파서(`0x7103b11dc8` 부근)가 BYML 배열 `UpdateComponents`의 원소 i(문자열)를 프리셋 항목 `+0x10` 배열의 i번 칸에 차례로 넣고 개수를 `+8`에 둔다(`0x7103b12270`~`0x7103b122b4`).
- 컨트롤러 생성 `0x7103a0b318`이 그 항목의 `+8` 개수만큼 `+0x10` 배열을 앞에서부터 돌며(`0x7103a0c7c4` 루프) 팩토리 `0x7103a8367c`로 컴포넌트를 만들고, 만든 순서대로 노드 배열(`+0x38`, 개수 `+0x30`)의 끝에 붙인다(`0x7103a0c818`~`0x7103a0c828`). 이름을 모르는 컴포넌트(팩토리가 0 반환)는 건너뛴다.

정정(2026-10-03): 이전 기록은 "프리셋 순서로 만들어진다고 봄 [추정: 팩토리 0x7103a8367c가 이름별로 만드는 것까지만 판독]"이었다. 파서와 생성 루프를 판독해 [판독]으로 올린다. 남은 가정: `0x7103a0b318`이 읽는 항목 `[x19+0x2d0]+idx·크기`가 위 파서가 채운 프리셋 표와 같은 객체라는 점은 오프셋(`+8`/`+0x10`) 일치로 본 것이다. SplPlayer 프리셋 순서는 §1 표.

프레임 정보(GameFrameSetup `0x71012acf60`이 채움, 기준: 위 `frame` 지역 구조체):

| 오프셋 | 값 | 출처 |
|---|---|---|
| +0x00 | 현재 강체 선속도(유닛/초) | ctrl vt 0x128 |
| +0x0c | 각속도 | ctrl vt 0x150 |
| +0x18 | 중력 가속도 벡터(유닛/초²) | ctrl vt 0x1f0 = S+0x1f8 |
| +0x24 | 위쪽 기준 벡터 | GameFrameSetup+0x28, NaN이면 상수 `*0x7105791978` = (0,1,0) |
| +0x30 | 이동 방향(단위) | ctrl vt 0x38, S+0x184/+0x188로 기울임 |
| +0x3c | 이동 방향 크기 계수 | 위 계산의 길이(기본 1.0) |
| +0x44 | dt | `[[*0x71057906f0]+0xe8]+0x24` (월드 생성 시 1/60 [판독], 이후 변경 경로 [미확정] — §6.4) |
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

특수 상태 번호 이름 — 정정(이전 [미확정]): 본체+0x65c = 10 + 특수 열거 인덱스이고([camui] 판독, SHARED.md), 0x18 = Jetpack, 0x1b = Skewer, 0x1c = SuperLanding이다. 각 분기가 읽는 컴포넌트(+0xa680 PlayerInkActionSpJetpack, +0xa7e8 PlayerInkActionSpSkewer)와도 맞는다 **[판독+데이터]**. Periscope(+0xa818) +0x38/+0xb0의 게임 의미는 8차 새 원본 producer로 **해소 [판독]+[실행]**(§4.1.1).

### 4.1.1 Periscope 상태·중력 차단 요청 (2026-10-03 r8 신규) **[판독]+[실행]**

기준 `P=[본체+0xa818]`는 PlayerPeriscope(vtable563e030)이며 **P+0x38=s32 game 상태**, **P+0xb0=u8 아직 소비하지 않은 시작 요청**이다. 기존 “Periscope+38/+b0 의미 미확정”을 다음 새 원본 근거로 정정한다. 잠망경 카메라의 움직임과 리소스 전체 재생은 별도 범위다.

| P+0x38 | 원본 상태명 | enter/exec/exit(실제로 등록된 주소) |
|---|---|---|
| 0 | Off | 266f780 / 266f914 / 없음 |
| 1 | Extend | 266f918 / 266f9b0 / 없음 |
| 2 | View | 266fcbc / 266fd4c / 266fd8c |
| 3 | Shrink | 266fe1c / 266feb4 / 26701e0 |

상태명·콜백은 신규 init `0x710266f18c`가 그대로 등록하며 원본 실행으로 위 네 문자열을 확인했다. `0x710267027c`가 초기 필드와 상태를 리셋한다. 중력 판정의 `P+38!=0 || P+b0!=0`은 **Extend/View/Shrink 중이거나, Off에서 시작 요청이 이미 들어온 상태**다. Viewer 상태2만 중력을0으로 하는 것이 아니다. HP 빠른 회복의 별도 조건 `P+38==2`는 정확히 **View**다(중력 predicate와 구분).

시작 producer: 원본 접촉 listener `0x71021d2c68`은 플레이어 접촉·태그 조건과 `0x710266ed40(P)` eligibility를 검사하고, 메시지 **0x08536a00** 및 잠망경 actor handle/파라미터를 만든다. 수신자는 P vt 슬롯16=`0x7102427830(P,Msg)`다. Msg+4가 이 ID이고 Msg+0x10 payload가 nonnull이며 payload vt+0x40 형 검사에 성공하면, payload+b0 핸들을 P+78에 복사하고 **P+b0=1**, payload+c8/cc/d0/d4 네 u32를 **P+a0/a4/a8/ac**에 복사하며1을 반환한다. 잘못된 ID/null payload/타입 거부는0이며 래치를 쓰지 않는다. `Obj_Periscope_Raise` 소리 요청도 접촉 listener에 있다; 원본명 연결만 판독했으며 소리 실행은 하지 않았다.

새 update `0x71026703b4`의 순서:

1. DokanWarp 상태가0이 아니고 현재 잠망경 상태가0이 아니면 먼저 Off0 전이.
2. Off0에서 b0가1이면 **b0=0**으로 소비하고 Extend1로 전이한다. 다른 상태에서 b0를 소비하는 분기는 없다.
3. Extend1은 이동 오징어 상태집합 S를 벗어나면 Shrink3. S를 유지하고 `P+3c * f32(1/60) >= config+94`이면 View2.
4. View2는 S를 벗어나면 Shrink3.
5. Shrink3는 `P+3c * f32(1/60) >= config+a4`이면 Off0.
6. 원본 game 상태 기계 `125a178` 전이 및 `125a394` update. 여기서 P3c는 부동소수 tick counter이며 설정의 시간은 초다. 이 함수가 읽는 조건을 “접지”로 바꾸지 않는다.

보통 사격장 이동은 Off0/b0=0으로 위 중력0 우회가 없다. eligibility `266ed40`은 S, 현재 Off0, 요청 없음, 점프/착지/토관/공격 카운터 등이 없는 조건에서만 시작을 허용한다. 요청→Extend/View→Shrink→Off가 끝나면 중력 predicate가 풀린다. 모드 guard와 스틱 입력 유예도 원문에 남겨 두며 임의로 더 자연스럽게 바꾸지 않는다.

검증 `web/tools/r8_physics_periscope_emu.py` → `analysis/completion/r8/physics_periscope_emu.json`: **상태800건 + 요청 수신240건, 정수 필드/래치/반환 불일치0**. 실제 init/state-name 등록 및 gameSM 전이/카운터 업데이트를 실행했다. actor/RTTI payload/config/time는 합성, actor·카메라·이펙트·자원 enter/exec/exit 콜백은 주소별 no-op이다(결과 JSON 목록). null0/PLT0/자동 페이지0. 따라서 **중력 predicate의 상태·요청 의미를 해소**했지만 잠망경 카메라·오브젝트 전체 동작을 검증했다고 쓰지 않는다. 신규 원문은 `analysis/decomp/r8_player/periscope.c`, `periscope_states.c`, `periscope_request.c`이다.

### 4.2 게임 코드의 수직 속도 갱신 `0x71024a7d00` [판독]

호출: 메인 계산 `0x7102475a54`(줄 4925, `0x710247c860`)가 `(본체+0xa5f9, &본체+0xc0, PC, &본체+0x72c, X)`로 호출. 기준 객체: **본체**.

| 본체 오프셋 | 타입 | 의미 | writer | reader |
|---|---|---|---|---|
| +0xc0 | s32 | 공중 프레임 수 (`0x710245f964`의 airFrames와 같은 주소) | 슬롯19 `0x71024abcf0` → `0x710246b574`(+1) / `0x710246b32c`(0), 점프 프레임 메인 계산 `0x710246b32c`(0) | 중력 조건, `0x710245f964` |
| +0x734 | s32 | 점프 시작 뒤 프레임 수(+0x72c 구조체 +8) | `0x71024a7d00` (+1/프레임), `0x71024a8000` 점프 시작(0) | 같은 함수(≥3 조건), 재점프 대기(> 6) |
| +0x750 | vec3 | 3D 점프 속도 X(아래 의사코드의 X, 인자 5). 경사에서 점프하면 +0x73c 대신 여기에 (0, jump, 0) | 메인 계산 점프부, 벽 점프(0) | 같은 함수, `0x710245aed8` |
| +0x73c | f32 | **수직 속도(유닛/프레임, 위가 +)** | 점프 시 초기 속도(메인 계산 줄 5413), `0x71024a7d00` | 이동(`0x710245b2b4`)·점프 판정 여러 곳, 컨트롤러 전달(§5) |
| +0x740 | f32 | 수직 합계 = +0x73c + X.y | `0x71024a7d00` | 5차 [판독]: 슬롯19 큰 함수 `0x7102483134` 의 `0x710248e158`(본체+0x274 가 참이고 +0x740 < 0 이면 −(+0x740) 을 씀), `0x710268c828` 의 `0x710268cc6c`/`0x710268cd30`(−(+0x740) 을 다른 객체 +0xe8/+0x464 값과 비교). main 0x7102400000~0x7102700000 범위 `ldr s,[x,#0x740]` 전수 3곳. 의미(착지 때 낙하 속력) [추정] |
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

- 상태 S(ctrl+0x20) 생성자 `0x7103a862cc`: 기본 중력 G0 = S+0x1dc..+0x1e4 = 세계 설정 `[[*0x71057906f0]+0xe8]+0xb8` → +0x2a4..+0x2ac에서 복사(세계 설정이 없으면 생성자 기본 (0, −9.8, 0)), 방향 S+0x1e8 = normalize(sign(scale)·G0), 배율 S+0x1f4 = 1.0, 실효 중력 S+0x1f8 = 배율·G0, 상한 S+0x204 = 200. 세계 설정의 런타임 값은 확인하지 않았다 **[미확정]**(기본값 −9.8은 [판독]). 5차: 물리 시스템 기본 월드 설명자의 desc+0x28..+0x30 = (0, −9.8, 0)이다 [판독] (§6.4). 상태 S 가 읽는 `[월드+0xb8]+0x2a4` 가 이 설명자 값에서 복사되는지는 찾지 못했다 **[미확정]**(월드+0xb8 은 필터 표 공급자(+0x28 = 레이어 표)로도 쓰이는 설정 객체).
- ctrl vt 0x1e8 `0x7103a87898` setGravityScale(s): 부호가 바뀌면 방향 재계산, S+0x1f4 = s, S+0x1f8 = s·G0. vt 0x1e0 get, vt 0x1f0 = &S+0x1f8, vt 0x1f8 setBaseGravity(G0).
- 게임은 매 프레임(메인 계산 줄 4688~4699):
  ```
  scale = (airFrames >= 3 && 다운 카운터 모두 <= 0 && !param_16[2]) ? g·60·60/9.8 : 0
  ctrl.setGravityScale(scale)            // g=0.008 → 2.9387755
  ```
  즉 Phive가 중력을 쓰는 단계에서도 `|G0| = 9.8`, dt = 1/60이면 프레임당 속도 변화가 정확히 g가 되도록 맞춘다 **[판독: 식]**. dt는 월드 생성 시 1/60으로 정해진다 **[판독]**(§6.4, 5차). 실행 중 dt를 바꾸는 경로가 없는지는 **[미확정]**이다. `|G0| = 9.8`의 런타임 값도 **[미확정]**이다(아래).
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
L.vt[0x30] (body)                                  // 0x71010067e0: 스텝 후 처리
```

- **dt 값**: 월드 생성 호출부 `0x7103db385c`가 desc+0x24(x26 = desc+0x5c−0x38)에 `0x3c888889`(0.016666668)를 쓰고, 생성자 `0x7103ac71c8`가 `월드+0x20 = +0x24 = +0x2c = min(desc+0x24, 0.99899f)`, `+0x28 = +0x30 = 1/dt`로 둡니다 **[판독]**. phive 범위(0x7103a80000~0x7103b40000)의 다른 `str s,[x,#0x24]` 15곳 중 7곳(`0x7103ade2f0`, `0x7103a8d068`, `0x7103a8da6c`, `0x7103a8ab1c`, `0x7103a8907c`, `0x7103ae9230`, `0x7103ab4518`)은 월드가 아닌 객체였고 나머지 8곳과 범위 밖 경로는 확인하지 않았습니다. 컨트롤러 프레임 정보 dt(§3.3 +0x44)도 같은 월드+0x24입니다.
- **5차 보강(2026-10-03) [판독]**: 월드 설명자는 물리 시스템 초기화 `0x7103db346c`(물리 시스템 vtable 슬롯 `0x7105763af0`)가 스택에 만든 기본 설명자(desc = sp+0xb8) 또는 초기화 인자 `[x1+0x28]`이 주는 덮어쓰기 블록(+0x38)이다. `0x7103db37d0`의 `csel x26, x21, x11`이 두 경우 모두 desc+0x24를 가리키게 하므로 **dt 0x3c888889 는 덮어쓰기 블록 유무와 관계없이 생성 시점에 기록된다**. 기본 설명자의 다른 값: desc+0x28..+0x30 = (0, −9.8, 0)(`0x7103db34cc`의 0xc11ccccd), desc+0x7c/+0x80 = 0.05/0.05(`0x7103db3578`의 `stur x11,[x22,#0xb4]`) → 생성자가 월드+0x218/+0x21c에 복사(`0x7103ac72a8` → `0x7103ac73d0`). 5차에서 남은 8곳도 분류했다: `0x7103ac7320`은 생성자 자신(dt 기록), `0x7103afa914`는 스택, `0x7103afd39c`(구조체 +4..+0x28 채우기), `0x7103b0542c`/`0x7103b056dc`(행렬 곱 결과), `0x7103b0c588`(보간 결과), `0x7103b33e70`/`0x7103b34228`(행렬 열 ×0.995 감쇠)은 월드 객체가 아니다 **[판독]**. 즉 phive 범위(0x7103a80000~0x7103b40000) 안에서 월드+0x24 를 쓰는 곳은 생성자뿐이다. 범위 밖 경로와 덮어쓰기 블록 공급자는 **[미확정]**이므로 "실행 중 1/60 고정"은 아직 **[추정]**이다.
- **정정(2026-10-03, 조정)**: 덮어쓰기 블록 공급자는 [r5 camweapon]이 찾았다. 게임 모듈 설정 팩토리 `0x710344af54` case 0xf가 설정 +0xb4 = 0.05, +0xb8 = 0.01을 쓰고, 모듈 생성 `0x7103dad17c`가 이 설정을 초기화 인자 +0x28로 넘긴다. desc = 설정+0x38이므로 desc+0x7c/+0x80 = 0.05/0.01이고, **실행 중 월드+0x218 = 0.05, 월드+0x21c = 0.01**이다 [실행] (`web/tools/r5_camweapon_boom_emu.py`, 사슬 실행 + 경계 12/12 비트 일치) + [판독]. 위의 "월드+0x21c = 0.05"는 덮어쓰기가 없을 때의 기본 설명자 값이다. ColGround 최종 반경 max(0.6, 0.01) = 0.6, 붐 구 반경 max(0.01, 0.3) = 0.3이라 결과 반경은 바뀌지 않는다. dt는 덮어쓰기 블록에서도 desc+0x24에 1/60이 기록된다(위 판독).
- **막는 접촉**(L slot5 `0x7101006718`): 접촉 플래그 +0x68 bit1이 꺼져 있으면 막지 않음(접촉만 기록). bit1이 켜져 있으면 `body+0x18c < 0`(기본 −1)이면 막음. 0 이상이면 상대 바디(+0x70/+0x78) +0x2a4 값과 `body+0x18c × 배율(0x7101a856e8(DamageRate 계열 표, body+0x190, 상대+0x2a8))`을 비교해 관통하면 bit1을 지우고 막지 않음 **[판독]**. 이 관통력(+0x18c)을 쓰는 곳은 찾지 못함 **[미확정]**. 접촉 bit1은 기존 r6 combat의 `0x7103c55ed8→0x7103c34e14`가 그룹별 block 표·양쪽 몸체 마스크·형상 행을 검사해 켠다 **[실행]**. 값2만 block 배열로 만드는 원본 BYML 변환은 7차 [실행] — [character_controller.md](character_controller.md) §3.5.1. 7차 실제 사격장 bphsh 행 부착+탄 block 결과는 [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §3.4.1~2. 기존 [추정]은 이 근거로 정정(2026-10-03).
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

큐는 `PhysicsContactReactionSequencer(Entity)`(생성 `0x71012e508c`, vtable `0x7105576640`, 기반 생성자 `0x7103c7e4d8`, 비우기 = 슬롯36 `0x71012e55cc`: 우선순위 힙에서 꺼내 작업 slot0 실행)입니다. 이 시퀀서는 `0x71012e7768`이 만들고 월드 리스너 목록(월드+0x1c0)에 등록합니다. 즉 **탄 충돌 콜백은 바디 스텝 안에서 바로 불리지 않고, 접촉 반응 시퀀서가 큐를 비울 때 실행**됩니다 **[판독]**. 이 시퀀서의 작업 노드는 **단계1 그룹0**에 있어 같은 프레임의 Phive Entity 월드 갱신(단계0 그룹6) 뒤, 모든 액터의 슬롯19·20·21(단계1 그룹2~5) 앞에서 큐를 비운다 **[판독]+[실행: 그래프 간선]**(§6.7, 5차). 정정(2026-10-03): 이전 기록은 "프레임 안 실행 시점 [미확정]"이었다.

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

### 6.7 프레임 안 실행 순서 (5차, 2026-10-03) [판독]+[실행: 그래프 간선]+[데이터: 그룹 값]

#### 6.7.1 실행 틀: 시퀀서·단계·그룹 [판독]

게임의 프레임 작업은 "시퀀서" 객체 단위로 돈다. 액터도 시퀀서다. 공통 기반 생성자는 `0x7103c7e4d8`이고, 엔진 액터(`0x7103cbdf6c`, vtable `0x710575acd0`)와 게임 액터(vtable `0x7105540368`)가 이를 상속한다. 기반 vtable `0x71057597e0`의 슬롯 2·6·13·15·22가 게임 액터 vtable과 같다.

| 기준 객체 / 필드 | 의미 | writer | reader |
|---|---|---|---|
| 시퀀서+0x20 (u32) | **그룹 번호**(0..7). 생성 설명자 +8 | 기반 생성자 `0x7103c7e4d8` | 노드 생성 `0x7103cc2934` |
| 시퀀서+0x30 + p·0x40 + k·8 | 단계 p(0..3)의 노드 칸 k(0..7) | 노드 생성 함수(시퀀서 vt 슬롯12 / 34) | 목록 연결 `0x7103c88e74`, `0x7103c7f810` |
| 노드(0x40 B)+0x20 / +0x21 | 현재 그룹 / 요청 그룹(다르면 다시 연결) | 노드 생성 | `0x7103c88e74` |
| 노드+0x22 | 1이면 목록 뒤, 0이면 앞에 붙임(액터는 `IsCalcNodePushBack`) | `0x7103cc2934` | `0x7103c88e74` |
| 노드+0x28 → 작업(+0x10 u16 그래프 id, +0x12 주기, +0x13 위상) | 실제로 도는 작업 객체 | 노드 생성 | `0x7103c85fbc` |
| 관리자 `0x71059a37c8` +0xa8 + p·0x40 + g·8 | 장벽 작업 B[p][g] | | `0x7103c85fbc` |
| 관리자+0x2f0 + p·0xc0 + g·0x18 | 목록 L[p][g] (머리·꼬리·개수) | `0x7103c88e74` | `0x7103c85fbc` |

프레임 그래프 구성 `0x7103c85fbc`(매 프레임):

```
for p in 0..3:                      // 켜진 단계만(param_3 비트)
  for g in 0..7: node(B[p][g]); edge(B[p][g-1] → B[p][g])          // g = 0 이면 앞 단계의 B[p'][7] → B[p][0]
edge(B[마지막][7] → END)
for p in 0..3, g in 0..7:
  for 작업 J in L[p][g]:
    if J.주기 == 0: 건너뜀; if J.주기 > 1 && (프레임번호 − J.위상) % J.주기 != 0: 건너뜀
    node(J); edge(B[p][g] → J); edge(J → (g < 7 ? B[p][g+1] : 다음 단계 B[p+1][0] 또는 END))
```
같은 (p, g) 안 작업끼리는 간선이 없다 → **순서가 정해져 있지 않고 병렬로 돈다**. 작업자 수가 2 이상인 묶음 분기(관리자+0x1b0+p·0x40+g·8 의 +0x28)와 시퀀서 간 의존 목록(관리자+0x320, 등록 `0x7103c89b3c`)은 같은 그룹 안의 묶음·순서만 바꾼다(판독, 실행 미확인).

#### 6.7.2 각 작업이 하는 일 [판독]

| 작업(노드 위치) | 실행 경로 | 결과 |
|---|---|---|
| 액터 단계0 (액터+0x230, 그룹 = CalcPriority) | 작업 `0x7103cc9268` → 액터 vt+0x188 `0x7100f746b4` → (상태 +0x4d0 == 1 이면 vt+0x2d8 후 상태 2) → 상태 2면 vt+0x2d0 `0x7100f76a78` → 끝에서 **행동 슬롯18 디스패처** `0x7100ffdaa4`(앞 수신자 vt+0xa0 → 행동 vt+0x90 → 뒤 수신자) | 슬롯18 |
| 액터 단계1 (액터+0x238) | 작업 `0x7103cc95e0` → 액터 vt+0x190 `0x7100f7493c` → 상태 2면 vt+0x2e0 `0x7100f76f78`(1이면 vt+0x2e8) → 물리 결과 반영 뒤 **행동 슬롯19** `0x7100ffdb6c` → **슬롯20** `0x7100f72e74` → … `0x7100f73368` → **슬롯21**(인라인, 앞뒤 수신자 vt+0xb8) | 슬롯19 → 20 → 21 (분기 `0x7100f77730`→`0x7100f7785c`→`0x7100f778e4`→`0x7100f7773c` 확인) |
| Phive Entity 월드(단계0 그룹6) | 물리 시퀀서(`0x7103db3998`가 두 개 생성, vt `0x7105763da8`) 노드 구성 `0x7103db48a4`: 노드 바이트 0x10606(그룹6, 단계0 배열) → 작업 `0x7103db4efc` → `0x7103acaee0(mode 0)`이 Pre1→Pre2(캐릭터 컨트롤러 `0x7103a80560`)→Pre3(Havok 작업 등록)→Post1→Post2(탄 바디 스텝)→Post3(리스너 접촉 작업 등록) 하위 그래프를 붙인다 | 두 번째 물리 시퀀서(+0x208 = 1) 노드는 +0x15 = 1(외부 의존)로 만들어지고, Post3 끝 `0x7103ad3064(…, +0x42c, +0x428)`이 그 노드의 의존 수를 줄여 풀어 준다 → 단계0 그룹7 장벽은 Post3 이 끝난 뒤에 통과 |
| Phive Sensor 월드(단계2 그룹0) | 같은 노드 구성의 0x10000(그룹0, 단계2 배열) → 작업 `0x7103db5218` → `0x7103acaee0(mode 1)` | Sensor 리스너 vt+0x20/+0x28 |
| 접촉 반응(Entity) (단계1 그룹0) | 설명자 `0x71012e4d88`(이름 표 `0x7105576620` 0번, 단계 `DAT_7104998720[0]` = 1, 그룹 0, 우선 0) → 노드 생성 `0x7100ffb584` → 작업 `0x7100ffb96c` → 시퀀서 vt+0x120 = 큐 비우기 `0x71012e55cc` | 탄 슬롯22 → 58/59/60(§6.6) |
| 접촉 반응(Sensor) (단계2 그룹0) | 같은 설명자 1번(단계 2, 우선 0x21=기본) | |

월드 생성 `0x7103acaee0`이 등록하는 하위 단계(기존 판독, 2026-10-03 [collision completion]):

| 작업 | 원본 주소 | 내용 |
|---|---|---|
| Pre1 | `0x7103aca1b4` | Pre2 를 후속으로 연결; 갱신 플래그 0 이면 Post2 쪽 우회 |
| Pre2 | `0x7103aca5d8` | Pre3 연결; 월드+0x50 bit4 일 때 캐릭터 갱신 `0x7103a80560`(순차 또는 작업 묶음) |
| Pre3 | `0x7103aca94c` | mode0 리스너 vt+0x10, mode1 vt+0x20; Havok 작업 등록 `0x7103c48298`(그 안 `0x7103c48740`)에 Pre3/Post1 노드 전달 |
| Post1 | `0x7103ac971c` | Post2 연결; 작업 버퍼 처리 `0x7103adc5f8` |
| Post2 | `0x7103ac9a00` | Post3 연결; 탄 바디 관리자 스텝(§6.4) |
| Post3 | `0x7103ac9ee4` | mode0 리스너 vt+0x18 = `0x71012e47f0`, mode1 vt+0x28 = `0x71012e4abc`(flags bit0 일 때 시퀀서 +0x208/+0x214/+0x230 작업 힙에 접촉 반응 작업 등록) → 끝에서 `0x7103ad3064` 로 합류 노드 해제 |

`0x7103c48298`은 `0x71009ce484` → 이벤트 처리 → `0x71009cee34`의 두 단계로 월드를 진행시키는 함수다. hknp 의 collide/solve 단계로 보는 것은 **[추정]**이다.

#### 6.7.3 액터 그룹 = CalcPriority [판독]+[데이터]

- 액터 생성 `0x7103cd6afc`가 시퀀서 생성 `0x7103c87d38`에 넘기는 설정 구조체 +8 = 액터 정보+0x110(`0x7103cd6afc` 안 `local_120 = *(정보+0x110)`, 복사 `0x7103c81748`, 팩토리 호출 `0x7103c87d38`이 설정 구조체 = 설명자+0x18 을 넘김). 기반 생성자가 이것을 시퀀서+0x20(그룹)에 둔다.
- 액터 정보+0x110 = `ActorSystemSetting.CalcPriority`(부모 사슬을 따라 설정된 값, `0x7103cd59fc`→`0x7103cd5a00`). 같은 정보+0x114 bit7 = `IsCalcNodePushBack`.
- 문자열 → 값 `0x7103dec4e8`: **Before 2, Default 3, After 4, Late 5**(열거 문자열 `"Before, Default, After, Late"`, `0x7103dec698`). 필드 기본값은 `0x7104af4a74` = 2.
- 데이터(`Bootup.Nin_NX_NVN.pack.zs`, 액터 팩): SplPlayer = `Default`(3); 탄 `BulletParent` → `SplBullet` = `After`(4); `SighterTarget` → `ObjParent` → `SplObj` = `Before`(2); `SplStaticMap`/`SplLift`/`SplMapPart`/`SplLockerObj` = `Before`(2); `SplPlayerCustomPart` = `Default`(3).

#### 6.7.4 사격장 한 프레임 (결론)

```
단계0 그룹2  표적(SighterTarget 등 Before) 슬롯18
단계0 그룹3  플레이어 슬롯18 (메인 계산 0x7102475a54 → setMoveVelocity 0x71024f4f7c)
단계0 그룹4  탄 슬롯18 (age++, setVelocity)                       ← 같은 그룹 탄끼리는 순서 없음
단계0 그룹6  Phive Entity: Pre1 → Pre2(캐릭터 컨트롤러) → Pre3 → Havok 스텝 → Post1 → Post2(탄 바디 스텝·쓸어 넘기기)
             → Post3(리스너가 접촉 반응 작업을 큐에 넣음) → 합류 해제
단계1 그룹0  접촉 반응(Entity) 큐 비우기 → 탄 슬롯22 → 슬롯58/59/60
단계1 그룹2  표적 슬롯19 → 20 → 21
단계1 그룹3  플레이어 슬롯19(0x7102353d24 → 0x7102483134: Phive 결과 읽기 0x71024abcf0, 카메라 메인 갱신 0x71024d9ae8) → 20 → 21
단계1 그룹4  탄 슬롯19 → 20 → 21
단계2 그룹0  Phive Sensor 월드 + 접촉 반응(Sensor)
단계3        PostUpdateMatrix 계열(이번에 액터 노드 생성자를 찾지 못함)
```

결과로 바뀌는 해석:
- **탄 첫 명중 age**: 접촉 콜백(슬롯22)은 그 접촉을 만든 물리 스텝과 같은 프레임, 그 프레임 슬롯18 뒤·슬롯19/21 앞에서 실행된다. 따라서 데미지 시점 age = 같은 프레임 슬롯18이 올린 값이다. 탄이 처음 움직이는 프레임이면 age 0(−1에서 시작). 탄이 생성된 프레임에 슬롯18이 도는지(생성 시점이 그래프 구성 뒤인지)는 이번 범위 밖이다 **[미확정]**.
- 정정(2026-10-03): 이전 판은 "슬롯18이 물리 전, 슬롯19·21이 물리 후"를 구조에서 본 **[추정]**으로, "접촉 처리가 슬롯21 뒤·다음 슬롯18 앞"을 **[추정]**으로 두었다. 앞의 것은 맞고 [판독]으로 올린다. 뒤의 것은 틀렸다: 접촉 처리는 **같은 프레임 슬롯19·21 앞**이다. 이전 판 표는 탄 슬롯21을 슬롯19 앞에 적었으나, 액터 디스패치 순서는 슬롯19 → 20 → 21이다.
- 같은 그룹(예: 탄 여러 개, 플레이어 여러 명) 안의 순서는 원본에서도 정해져 있지 않다. 웹은 결정적 순서를 쓰되 그룹 간 순서(표적 → 플레이어 → 탄)는 지킨다.

#### 6.7.5 원본 실행 확인 (`web/tools/r5_physics_frameorder_emu.py`)

| 대상 | 결과 | 스텁 |
|---|---|---|
| `0x7103dec4e8` CalcPriority | 10/10 일치(4개 이름 + 틀린 6개) | 열거 문자열 표(`0x7103dec698` 정적 초기화 결과)를 미리 채움 |
| `0x7103c88e74` 목록 연결 | 13/13 노드가 L[p][g]에 연결, 개수 일치 | 시퀀서 vt+0x10 = 1 |
| `0x7103c85fbc` 그래프 간선 | 사격장 구성 58/58 간선 정확 일치, 무작위 배치 500/500 정확 일치 | 그래프 노드 추가 `0x710351c678` → 순번 id, LockMutex/UnlockMutex |
| 도달 관계(원본 간선으로 계산) | 표적 P0 → 플레이어 P0 → 탄 P0 → 물리 Entity → 접촉(Entity) → 표적 P1 → 플레이어 P1 → 탄 P1 → 물리 Sensor 모두 참, 같은 그룹 쌍 3개는 서로 도달 없음 | |

결과 `analysis/completion/r5_physics_frameorder_emu.json`. 검증하지 않은 범위: 작업자 ≥ 2 묶음 분기, 시퀀서 간 의존 목록, 외부 작업 목록(param_4 bit0), 동적 하위 그래프 `0x7103acaee0`·합류 해제 `0x7103ad3064`의 실행, 실제 작업자 스레드 실행. 액터 그룹 값은 데이터와 판독으로만 확인했다.

### 6.8 재구현 비교 (`web/tools/bulletbody_integrate.py`) [재구현 계산]

`p += fl(dt·fl(60·v))`(원본 판독식)과 `p += v`(이전 가정)를 슈터 6종 × 발사각 0°/+30°/−20°, 40프레임으로 비교:

| 항목 | 결과 |
|---|---|
| `fl(dt·fl(60·v)) != v`인 비율(무작위 v ∈ [−3,3], 20만 개) | 61% |
| 위치 최대 차이(40프레임) | 2.9e-6 유닛(WeaponShooterNormal 0°), 나머지 ≤ 1.9e-6 |
| 예: WeaponShooterNormal 0°, 40프레임 z | `p+=v` 16.448555 / 바디식 16.448557 |

비트 일치가 필요하면 바디식을 써야 합니다. 상태머신은 탄+0x1118 사본만 쓰므로 이 차이는 이동 거리(+0x1200)·스플래시 생성 지점·도색 위치·충돌 판정에만 들어갑니다. 결과 `analysis/bulletbody/integrate_compare.json`.

### 6.9 지형 접촉의 실제 재질 reader·코덱 (8차, 2026-10-03) [실행]+[판독]

`3c5606c`가 shapeA/B의 `12ac5e0` 16 B 재질 결과를 접촉+38/+48로 복사하고 `3c55ed8`로 block bit을 결정한다. `12acb38`는 실제 mesh leaf `0997078` tag&0x1fff를 I+18 count와 비교한 뒤 I+20+index*16을 반환한다. 월드 bootstrap `3c4579c`의 `WorldShapeTagCodec` vt5755ee8+40은 RET; Entity CollisionFilterBackEnd vt5756560+40=3c570c4이다. 새 실제 원본 mesh key→leaf→재질 실행11505건/leaf5530건/정점49770 f32필드 불일치0. **§9/§11의 재질 reader·코덱 클래스 미확정은 새 원본 근거로 해소**한다. 이전 r6/r7 block 계산은 재사용이고 신규확정수로 세지 않는다. 구조·명령·스텁·경계는 [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §3.4.3.

### 6.10 native 쓸어 넘기기·solver 진입 추적 (2026-10-03 r8, 부분) **[판독]/[미확정]**

기존 `3c52d30/3c5368c/3c54140/3c54de4` 네 처리기와 `09af088` 이후를 새로 읽었다. **leaf 함수 표 D(전역57dd738)**와 **Havok 질의 디스패처 Q(world+0x510)**는 별개다. D+type*0x200+0xa8은 정점/반경, +0xc0은 leaf를 공급한다. Q는 `0x7100947508(Q,0)`에서 생성되고 `0x710093fe88`로 쌍 처리기를 등록한다. 새 원본 생성자를 실행해 type0/1/2/4/8의 **25쌍 함수 포인터가 판독값과 일치**했다(null/PLT/자동 페이지 없음, `r8_physics_query_dispatch_emu.py`). 이 실행은 기하 접촉 계산을 실행한 것이 아니다.

`0x7100947aec`는 질의 filter vt+0x40(종류2, flip을 반전한bit, 두 info)를 먼저 확인한다. 각속도 입력 query+0x90..0x9c가0이 아니고 양쪽 shape+0x1a bit0이면 rotating cast `0x7100948360`; 그 외 `Q+0x1eb0 + typeA*0xf8 + typeB*8` 함수로 간다. 메시 상대(타입8)는 기존 topTree `0936ee8`; 반대로 메시→convex는 `0945350`이다. Convex 일반은 `0949570`, 타입1/2 일부쌍은 `0948f30`, 타입1→타입4는 `094ae10`이다. shape type 이름을 포인터 표 번호만으로 임의 명명하지 않는다.

일반 `0949570`은 D+0xa8에서 각 shape의 정점·개수·반경을 받고 info+0x30 scale 조건에 따라 정점을 변환한다. radiusA에는 query+0x74를 더하고, 둘의 반경 합 및 query+0x70 한계·context+0x18 허용값을 native cast에 준다. 첫 접촉 collector가 없고 A정점 수<2·원점0 조건이면 `0x7100aefd00→0x7100aefdc0`; 그 외 **`0x7100aec920`**이다. 초기 겹침 결과가 유효하고 separation<=query+0x78이면 초기 collector vt+0x28에 type5, sweep 결과가 유효하면 hit collector에 type2를 전달한다. 네 상위 처리기의 collector 복사는 `3c5621c/3c56588/3c5677c/3c5698c`로 갈라진다.

solver의 기존 `09cee34`는 `09cec84`를 부르는 래퍼이며 **실제 위치 적분 식 자체가 아니다**. 새 `09cec84` 판독: World+0x4a8 simulation의 vt+0x18을 World+0x920 task queue와 함께 호출하며 simulation+0x18==1인 경우에만 세 번째 작업 인자를 유지한다. `09bff14` 월드 생성자는 desc+0x70==1이면 MultithreadedSimulation(`0a68954`), 아니면 SingleThreadedSimulation(vt5462510, vt+0x18=`0a8ee28`)을 단다. Single 경로는 task 입력→`09ce984`→`0a84230`→`0a4ac10`→`0a71b90` 등으로 이어진다. **실제 적용되는 simulation 모드와 위치 적분/침투해소 커널 전체는 아직 미확정**이다.

SolverInfo는 World+0x530이며 새 기본 생성자 `0a4517c`가 +0x70 substep4/+0x78 microstep1을 쓴다. 실제 월드는 `0a4536c(dt,solveDt,Info,gravity,desc10c,desc110)`로 덮어쓴다. 이 함수는 subdt=`dt/n`, invsubdt=`n/dt`, gravitySub=gravity*subdt, gravityTick=gravity*dt를 저장하며 cap84가 큰 sentinel보다 작으면 `cap84 *= (newN*oldDt)/(oldN*newDt)`로 재조정한다. **기본 생성자의4/1을 사격장 실제 반복 수라고 주장하지 않는다.** desc writer와 실제 task solver 소비를 이어서 확인해야 한다.

새 디컴파일: `analysis/decomp/r8_physics/native_dispatch.c`, `query_solver_init.c`, `primitive_toi.c`, `solver_toi_core.c`. 아직 `0aec920`의 support/GJK·conservative cast와 `0aefdc0`의 핵심 계산, task solver의 최종 position/penetration writer를 완독·재구현 대조하지 못했다. 따라서 TOI 전체와 solver 질문의 **상태는 조사중**, 확정 수 증가0. 다음은 위 native kernel 및 `0a4ac10/0a71b90`이다. 원본 실제 ColGround↔지형→solver→actor→B10을 한 번에 실행하지 않았다.

### 6.10.1 게임 기본 반복 설정과 native motion 저장 (2026-10-03 r8 추가, 부분) **[판독]+[실행: 월드 생성]**

새 판독 `solver_integrate.c`/`solver_motion.c`/`native_motion_body.c`/`native_library_init.c`로 다음 경로를 확보했다. 기존 게임 factory `0x710344af54`의 재분석을 신규 성과로 세지 않으며, 이번에 처음 읽은 native 소비·최종 설정 연결을 기록한다.

- native Cinfo 생성자 `0x7100a454cc`는 `D+0x10c=4`(substep), `D+0x110=1`(microstep), `D+0x70=1`(다중 작업 simulation)을 둔다. **게임 factory의 마지막 override는 Cfg+0x94=8**이다. `0x7103c4579c`가 Cfg+0x38 설명자의 +0x5c/+0x60/+0x64를 각각 D+0x10c/+0x104/+0x108로 전달하므로, 이 기본 gamefactory 경로는 **substep8/microstep1/tau0.6000000238418579/damp1**이다. 런타임 설명자 교체 여부 전체를 아직 확인하지 않았고 native 기본4를 실제 게임 반복 수로 채택하면 안 된다.
- 원본 `0x7100923a60→0x71008f28c0`로 Havok 초기화를 실행한 뒤 `0x71009bff14` nativeWorld 생성이 끝까지 반환했다. 생성된 S=World+0x530의 +0x70/+0x78/+0/+8은 8/1/0.6000000238418579/1, World+0x4a8의 simulation VT는 `0x71054614c8`이며 slot+0x18은 **0x7100a6a078**이다. 테스트는 gamefactory 설정 세 필드를 original bootstrap 대응대로 전달한 합성 설명자이며 실제 게임 월드 캡처가 아니다.
- 처음 월드 생성 실행은 Havok 할당 콜백 미초기화로 `intr 0x3d4ccccd00000201`에 멈췄다. 엔진 초기화 추가 후에는 ELF TLS의 TPIDR_EL0가 0이라 새 스레드 상태를 반복 생성하여 `0x71008af31c/0x71008af2d0` count limit에 걸렸다. 단일 스레드 ELF TLS 메모리와 nn TLS 값을 제공한 마지막 시도는 fault0/자동 매핑0으로 반환했다. SDK 락·시간·할당 외부 경계와 optional null callback은 JSON에 명시했다. 이 성공을 접촉 솔버 실행 성공으로 확대하지 않는다.
- `0x7100a4ac10`는 **단일 작업 simulation**의 Jacobian 루프다. World+0x5a0 substep마다 World+0x5a8 microstep과 유한 cap(World+0x5b4) 분기를 돌며 세 solver stream을 처리하고, 반복 사이 `0x7100a4b514`(StStepMotions), 끝 `0x7100a4b8c8`(StFinalizeMotions)를 부른다. 게임 기본의 다중 작업 경로 `0x7100a6a078`가 만드는 작업·solver 순서는 계속 판독 중이다.
- 새 `0x7100a4b8c8` 위치 저장은 native **hknpMotion stride0x80, COM +0x10/+0x18/+0x20의 double**에 축별 `double(f32(dt * effectiveLinearVelocity))`를 더한다(PC `0x7100a4c12c..0x7100a4c170`). 속도/감쇠·가속 cap·modifier·쿼터니언 갱신이 이 저장보다 먼저 있다. 이어 연결된 nativeBody(stride0xc0)마다 `0x71009d5b68`이 COM·회전·body COM offset으로 body transform과 AABB를 갱신한다. **Phive staging +0x44와 native motion 필드를 같은 객체로 간주하지 않는다.** staging→native 선속도와 native body→게임 body+d8 전체 연결, 접촉 침투 bias 및 Jacobian 전체 수식은 아직 미확정이다.

근거: `web/tools/r8_physics_world_solver_probe.py`, `analysis/completion/r8/physics_world_solver_probe.json`(이전 실패 보존). 원본 월드 생성 반환과 설정 필드 확인을 [실행]으로 기록하며, 재구현한 접촉·위치와 비트 대조한 시험은 아니다. L15/L77/L191 및 TOI 행은 조사중 유지한다.

### 6.10.2 원본 native 강체 생성·접촉 스텝 실행 (8차, 2026-10-03)

**[판독]+[실행 관찰; 독립 재구현 비트 대조 전]**. 원본 라이브러리 초기화와 native body 등록을 끝까지 실행했다. 지난 §6.10.1의 optional null 콜백은 접촉 완결 근거가 아니었다. 이번에는 게임 초기화 `3c07898`의 첫 호출과 같은 **`09153d8(57e5398)`**를 실행하여 `SimdTreeBroadPhase`의 feature descriptor가 factory `0adbb30`을 전역 `57dd918+8`에 등록하게 했다. `09313b0(57dd738)`의 shape dispatcher 초기화와 ELF TLS `TPIDR_EL0`도 필요하다. 외부 nn OS TLS·락·시계·메모리 할당은 실행기의 단일 스레드 모형이다.

| 원본 단계 | 함수·저장 | 확인한 경계 |
|---|---|---|
| 캡슐 | `0930b40`(sret x8) | human A(0,0,0), B(0,.7,0), r .6; 지형 대신 static capsule A(−10,−.1,0), B(10,−.1,0), r .1 |
| native body | `09e64f8` BodyCinfo → `09c78f0` CreateBody → **`09c6a70` AddBodies** | motion type 0 static/1 kinematic/2 dynamic; body id low24와 generation 고비트. `09c8310`은 RemoveBodies, `09c969c`은 DestroyBodies이므로 등록 함수가 아니다 |
| 질량·회전 | `0abf6e0` shape mass distribution → `09db37c` → `09d7338` | dynamic mass100, inertia XYZ0. `09d7338`의 mass는 **s0 실수 인자**이다. Ghidra의 첫 정수 인자 표기를 그대로 실행하면 질량을 잘못 전달한다 |
| material | `0a507cc` → `0a4f76c` → Cinfo+c | probe에서 material+1a/+1c/+1e를 0으로 설정. native 재질 필드의 원본 descriptor 이름 및 Phive preset 변환은 이번 실행에서 대조하지 않았다 |
| 원본 충돌 작업 | `09ce484` → mode1 `0a68c4c` task graph | `TI.dt=1/60`, **TI+4=0**, workerCount1. 기존 게임 `3c48298`는 세계 속도배율1일 때 scaledDt에 0을 넣는다 |
| 작업 소비 | native task interface vt+18 | 원본 그래프 간선의 위상순서로 단일 스레드 실행. 첫 collide 25노드, 원본 `09d275c` graph reset 뒤 solve 7노드. 실제 동시 스케줄러는 모형이며 물리 callback은 원본 |
| 접촉·위치 | `09cee34` → mode1 `0a6a078` → **`0a181fc`** → **`0a4b8c8` → `09d5b68`** | 원본 4-lane contact kernel·COM 적분·몸체 transform/AABB 생성이 모두 실행됨. 이 시험에서는 `0a29f20` 재생성 경로 진입0 |

`r8_physics_contact_mt_probe.py`의 10프레임 모두 반환, **null 호출0/자동 메모리 매핑0/메모리 fault0**. contact kernel80회(8회/프레임), COM 적분10회, body transform10회이다. human native body 원점 y는 .45에서 첫 프레임 **.45749515295028687**, 10번째 **.5101864337921143**; native 저장 속도 y는 첫 **.003538846969604492**, 10번째 **.0022319555282592773**이다. fixture native 세계 중력은 WorldCinfo 기본 −9.81이며, 실제 Phive 플레이어의 매 프레임 속도 지정·native gravity 분리는 아직 연결하지 않았다. **이 수치를 사격장 상수로 사용하지 않는다.**

같은 capsule·mass·material 입력의 진단 Single mode0 실행 `physics_contact_probe.json`과 mode1 실행은 10×(위치3 f32+COM3 f64+속도3 f32) **90필드의 비트가 동일**하다. 이것은 두 원본 경로 간 교차 대조이며 독립 재구현과의 비트 일치가 아니다. 접촉 없이 body 하나를 만든 `physics_body_probe.json`도 반환했다. native hknpMotion stride는 **0x80**, COM은 +10/+18/+20의 double, native linear/angular velocity는 +60/+70이다. Phive staging pool stride **0xd8** 및 staging+44와 혼동하지 않는다.

실패도 보존: feature 미등록에서는 broad phase callback이 null이었다(`physics_body_no_broadphase_probe.json`); workerCount0에서는 simulationContext blockstream 생산이 빠졌다(`physics_body_zero_threads_probe.json`); collide 완료 노드를 solve에서 다시 실행한 첫 MT 실행은 해제된 task pointer를 읽었다(`physics_contact_mt_replayed_probe.json`). graph를 남겨 둔 뒤 TI+4=dt를 사용했던 별도 시험은 `physics_contact_mt_retained_graph_probe.json`에 보존했다. 이후 실제 게임의 TI+4=0 및 collide/solve 사이 원본 graph reset을 적용했다. 마지막 두 시행의 값을 정상 프레임 결과로 혼합하지 않는다.

**[미확정]** 실제 Phive staging velocity→native motion setter, nativeBody transform→Phive body+d8 write-back, `SplPlayer` motion property mapping, 접촉 Jacobian의 침투 bias·impulse 식의 독립 비트 대조, 실제 사격장 지형 메시/경사/계단·오징어 형태의 전체 스텝. next: `3b07b8c→3c50c7c`, `0a181fc/0a29f20`, `0a4b8c8`, nativeWorld vt motion/pose getters. 이 실행 성공으로 기존 mixed whole 질문을 확정으로 승격하지 않는다.

### 6.10.3 게임 속도 전달과 native 스텝 뒤 Phive 되쓰기 (8차 추가, 2026-10-03)

**[실행]+[판독]** 새 `0x7103c50c7c`는 staged linear/angular 변경 플래그에 따라 nativeWorld의 `+0x190=0x71009d9674`(둘), `+0x198=0x71009d9e54`(linear), `+0x1a0=0x71009da1a0`(angular)를 호출한다. game Body+0x90 backend+8의 원본 handle로 native Body를 선택한다. Native motion+0x60..68의 linear setter는 축 차이가 모두 `2^-23` 이하이면 쓰지 않는다. 이 허용 오차는 앞단 게임 setter의 `0.0001`과 별개다. 새 `r8_physics_native_velocity_emu.py`는 원본 body 생성·AddBodies 후 이 bridge와 setter를 실행하여 1,044사례/3,132 f32필드가 독립 계산과 **비트 일치**, null/자동 매핑/실행 오류 0이었다.

Native 속력 제한은 `n=f32(f32(f32(x*x)+f32(y*y))+f32(z*z))`가 `f32(cap*cap)` 이하이면 입력을 그대로 저장한다. 이를 넘으면 `inv=f32(1/f32(sqrt(n)))`, `k=f32(f32(cap*inv)*0.9999997615814209f)`를 먼저 만들고 각 축 `f32(v*k)`를 저장한다. cap=100은 검증 fixture의 motion+0x6c 값이며 사격장 전체 cap의 근거로 쓰지 않는다. NaN 길이는 새 값 저장을 거부하지만 ±무한대 길이는 inv=0을 만들고 무한대 축에 원본 ARM 기본 NaN `0x7fc00000`을 저장한다. 첫 독립 모델의 NaN 부호 불일치 1건은 `physics_native_velocity_nan_sign_failure.json`에 보존했고 원본 명령의 canonical NaN 처리로 모델만 정정했다.

**[실행: 원본 producer 연결]+[판독]** 새 `0x7103ae6410`는 nativeBody+0x54 bit3(active)로 game Body+0x88 bit15를 갱신한다. 이전 또는 현재 active이면 Body+0xd8의 48 B 행렬을 +0x108의 이전 행렬로 복사하고 nativeWorld+0x180=`0x71009d1de0`에서 nativeBody 행렬을 얻는다. `0x71008a8cec`의 quaternion 변환 뒤 회전 9개를 Body+0xd8..+0x100에 쓰고 nativeBody+0x30/+0x34/+0x38의 위치를 Body+0xe4/+0xf4/+0x104에 쓴다. Body bit22가 꺼져 있으면 +0x1d0=`0x71009d9b84`의 linear 속도를 Body+0x138..+0x140으로, +0x1d8=`0x71009d9c5c`의 world angular 속도를 +0x144..+0x14c로 되쓴다. bit25는 bit26으로 넘긴 뒤 지운다.

`r8_physics_native_writeback_emu.py`는 §6.10.2의 원본 MT contact 스텝 10프레임 후 **이 producer와 실제 native getter를 이어 실행**했다. identity 회전·angular0 fixture에서 현/이전 행렬24개, linear/angular6개 ×10 = 300 f32필드가 저장 대응과 비트 일치했고 contact kernel80/COM10/native pose10을 실제 실행했으며 null/자동 매핑/실행 오류는 0이었다. 출력 `physics_native_writeback_emu.json`. 접촉 보정 수식의 독립 재구현 대조나 임의 회전·잠복/계단 상태를 검증한 결과는 아니다.

정정(2026-10-03): 아래 §8의 과거 “Phive 스텝 원본 미실행”은 위 제한된 원본 native contact/되쓰기 실행으로 보강한다. 실제 플레이어 슬롯18→staging→충돌/침투 보정 수식→형태 변경→슬롯19의 **전체 실행·식 검증**은 여전히 미확정이다. 기존 r6/range Main body→actor 저장 사슬은 재사용하며 이번 신규 수로 세지 않는다.

8차 적분 저장 구간 추가(2026-10-03) **[실행: 명령 구간]+[판독]**: 실제 finalizer0a4b8c8의 **0a4c12c..0a4c188**는 먼저 SIMD 입력 실효속도와 dt를 **f32로 곱한 뒤**, 그 곱만 f64로 올려 nativeMotion+10/+18/+20의 double COM에 더한다. 그 후 COM을f32로 줄여 stack+f0에 위치cache를 저장한다. 즉 `COM64_new=COM64_old+double(f32(v_effective32*dt32))`이며 double v×dt가 아니다. 여기의 SIMD 실효속도가 nativeMotion+60의 최종 저장 선속도와 같다는 주장은 하지 않는다(침투 보정/solver 누적값의 합성은 후속 normal/bias 분석 필요). 새 `r8_physics_com_integrate_emu.py`는 이 저장 구간 2,048사례(큰/작은double원점,여러dt)의 **6,144 f64+6,144 f32필드**가 독립 계산과 비트 일치, null/자동 매핑/오류0. 출력 `physics_com_integrate_emu.json`. 전체 contact·finalizer 입구까지 실행한 시험은 §6.10.2/3의 별도 원본fixture다.

8차 native 키네마틱 상대 접촉 추가 **[실행: 원본 전체 probe]/[미확정: 독립 전체 식]**: `r8_physics_contact_kinematic_probe.py`는 §6.10.2의 바닥 nativeBody를kind0 static에서kind1 keyframed로 바꿔 캡슐형 dynamic 몸체와 원본MT 스텝10프레임을 실행했다. kernel80/COM10/pose20, null/자동 매핑/오류0. 기존 static용 singlebody normal PC0a1a4d8/0a1a98c는0회이므로 이 결과는 다른 원본 두-body 경로다. 양쪽 무회전/무마찰 fixture이며 실제사격장 Main의 모든계층·형상·배치 실행이 아니다. 독립 normal/bias 계산 비교 전 whole 질문은 조사중 유지. 같은 첫kernel 시점의 BSS/heap/stack/regs는 `physics_kinematic_kernel_*`에 보존했다.

### 6.10.4 침투 보정·법선 충격량·반복 수 (8차, 2026-10-03) **[판독]+[실행]**

§6.10~6.10.3의 과거 "침투 bias·impulse 식 미확정"은 이 절의 새 판독/실행으로 **보통 플레이어의 무회전·지형/표적 접촉(마찰·반발0) 해소 식에 한해 정정**한다. 탄의 TOI 질의, 임의 회전/마찰 강체, 실제 Lby_Lobby00 메시 전체를 재생했다는 뜻은 아니다. 고정 목록의 `character_controller.md:L191` 질문(침투 보정 속도·반복 수)을 해소하며, TOI가 섞인 `phive_controller.md:L359/L495/L508`과 몸체 속성 전체 바인딩 `character_controller.md:L15`는 조사중이다.

원본 사슬은 nativeWorld solverInfo(+530)의 초기화 **0a452fc→0a4536c**, 접촉 cache 생산 **0a218f0→0a21ae4**, Jacobian/target 생산 **0a15b70**, normal kernel **0a181fc**, carry **0a4b514**, finalize **0a4b8c8**이다. 0a77438 실제 MT 작업은 09d4ba8로 초기 속도/zero carry를 만들고 substep/microstep 카운터를 소비하며 마지막에 finalize를 호출한다. 게임 world desc의 **sub8/micro1/tau.6/damp1**은 §6.10.1 판독을 재사용한다. 실제 원본 MT graph는 한 프레임 normal kernel8회, 그 사이 carry7회, 마지막 finalize1회였고 10프레임에도 이 횟수를 유지했다. single 진단 경로 0a4ac10의 동일 8단계 루프도 판독했다. 반복 수를 "기본 constructor4"로 대입하거나 8회 각각에 전체 dt를 곱하지 않는다.

수학 필드의 기준 객체를 구분한다. 아래 `S=solverInfo`, `C=접촉 cache`, `J=Jacobian행`; **S+C0와 C+C0는 다른 값**이다. root의 신규 전체 원본 실행(1,024사례/16,384 f32필드, `solver_info_emu.json`)에 따라 `S+B0=tau/damp`, `S+C0=damp/tau`, `S+74=f32(1/sub)`, `S+D0=f32(f32(tau/damp)*f32(f32(1/dt)*sub))`다. 실제 dt=f32(1/60),sub8이면 D0=288이다. cache writer0a21ae4는 quality+2c bit7이0이면 `C+C0=1`, `C+C8=-.05`를 두 lane에 저장하며 bit7이1이면 둘을0으로 쓴다(root 신규 1,024사례/4,096필드). enum 이름만으로 모든 게임 cache의 값이1/-.05라고 단정하지 않는다.

원본0a15b70은 native contact+30의 현재 depth와 cache의 old/carry를 읽어 J+1c의 target velocity를 쓴다. 실제 정적 접촉 store PC0a16e20, kinematic 두-body 접촉 store PC0a17544에서 target=`2.1600022315979004`였고, effectiveMass store는 각각0a16d10/0a165e8였다. nativeManifold+92의 분기 byte를 읽는 PC0a15d94(W9), dual의0a165ec..165f4에서초기byte를mask로보존하는명령과 실제 Jacobian 분기/행 반복을 판독했으며, 고수준 플래그 이름을 임의로 붙이지 않는다. 세부 register/store와 실제 trace는 `analysis/completion/r8/contact_kernel_support.md` §4~7.2, `contact_bias_producer.json`/`contact_dual_bias_producer.json`에 보존했다.

`F`를 명령마다 반올림하는 f32로 두면 보정 식은 다음과 같다. `old`/`carry`는 원본 cache 입력, `d`는 depth, `v`는 원본 상대 속도의 투영, `flag`는 해당 원본 분기 입력, `pred=S+20`, `k=C+C8`, `c=C+C0`, `gamma=S+D0`이다. 임계값은 **−2^-23**이고 실제 원본 old/carry 생산·변경은 위 주소의 store에 연결된다.

```text
p = carry if flag!=0 else F(carry + F(v*pred))
cap = F(dt*c)
if old >= -2^-23 and d > F(p-cap):
    outOld=old; outCarry=d; target=F(d*F(-gamma))
else:
    t=max(+0,min(F(d*k),cap))
    b=t if flag!=0 else min(F(old*k),cap)
    diff=F(d-old)
    p=F(min(p,+0)-diff)
    select=p if p>F(cap+F(2*b)) else +0
    nextOld=F(F(old+b)-select)
    nextCarry=F(F(diff-b)+select)
    outOld=min(max(nextOld,F(d-b)),-2^-23)
    outCarry=nextCarry
    target=F(nextCarry*F(-gamma))
```

signed zero와 min/max 순서도 보존했다. actual `old0/carry0/d=-.1500000358/flag1`은 old=`-.14250002801418304`, carry=`-.007500007748603821`, target=`2.1600022315979004`다. 깊이에 하나의 "밀어내기 상수"를 곱하는 식과 다르다. single bias4,097사례/24,582필드와 dual bias4,097사례/24,582필드 독립 bit 일치(early 각1,069/1,055)다.

압축 inverse mass는 원본 **SHLL halfword #16**으로 f32 상위16비트를 복원한다. FP16 변환이 아니다. native mass100 fixture의 압축값0x3c24는 **.010009765625**로 복원되고 유효 질량은 **99.90243530273438**이다. `invMass=.01`로 바꾸지 않는다. single/dual 질량 블록 각각1,024사례/2,048필드가 독립식과 bit 일치했다.

마찰0/관성0에서는 normal N과 linear L의 `dot=F(F(F(Lx*Nx)+F(Ly*Ny))+F(Lz*Nz))`; `dot>=target && oldLambda==0`이면 skip. 그 외 `delta=max(F(-oldLambda),F(F(target-dot)*effectiveMass))`, `lambda'=F(oldLambda+delta)`, `L'=F(L+F(N*F(delta*invMass)))`다. 두-body는 `(LA-LB)·N`을 사용하고 A에는 더하고 B에는 뺀다. kinematic의 inverse mass0 때문에 지정 속도는 그대로이며 dynamic player만 반응한다. 일반 회전 항까지의 명령 식은 support §7/7.1에 기록했지만 그 사용을 ordinary player 데이터로 확대하지 않는다. single normal4,097/40,970필드, dual4,097/77,843필드 bit 일치다.

같은 manifold의 여러 행은 **앞 행이 수정한 속도로 다음 행**을 계산한다. 0a18d78..d88은 header+4 count, row stride0x20, lambda stride4를 소비한다. 실제 원본 kinematic 수직 캡슐 벽에서 **2행**을 생산했고 전체0a181fc의 실제 LR 반환 후 속도/scratch/lambda20필드가 독립 순차식과 일치했다. 추가 explicit2~4행 fixture를 합쳐1,025사례/3,074행/21,524필드 bit 일치. 3/4행의 native manifold 생산은 시험하지 않았다. SIMD 명령을 사용한다는 이유로 독립적인 "4개 접촉 병렬 처리"를 가정했던 후보는 근거가 없어 철회한다. 두 번째 실제 lambda의 작은 값`2.3818596673663706e-05`도0으로 없애지 않는다.

### 6.10.5 최초 속도·carry·COM와 몸체 원점의 전체 연결 (8차, 2026-10-03) **[판독]+[실행]**

§6.10.3의 원본 game stage→native setter와 native→Phive 되쓰기 증거를 재사용하며, 이 절의 신규는 그 사이 native 수식/속도 저장/COM→body origin이다. `State+68` current와 `State+90` baseline은 0x20 B packed 기록이다. angular xyz는+0/+4/+8, linear z는+c, linear x/y는+10/+14다. baseline+18/+1c/+1e는 motionID/속성ID/압축 각속도 상한이며 xyz 벡터로 읽지 않는다.

새0a77438의 초기 단계는 **09d4ba8**을 호출한다. nativeMotion+60의 linear velocity에 `F(S+90의subgravity * MotionProperties+8의scale)`을 축별 f32로 더해 current를 만들고 baseline의 수학적 linear/angular 6성분을0으로 한다. 압축 inverse mass가0이면 그 중력 항을0으로 한다. modifier mask가 활성화되면 원본 vt+A0 callback을 거치는 별도 분기가 있고, 독립 시험은 modifier 없는 synthetic fixture다. 전체09d4ba8의1,024사례/12,288 f32필드 bit 일치(null/자동매핑/fault/PLT0). fixture world gravity−9.81과 실제 Phive 기본−9.8 및 게임이 적용하는 중력/공중 모드를 혼동하지 않는다(실제 게임 값은 §4의 기존 근거 재사용).

각 normal 단계 뒤(마지막 제외) **0a4b514**는 physical delta=`F(current-baseline)`를 선속도 상한에 맞춘 다음 `nextBase=F(base+F(delta*(S+B0)))`, `nextCurrent=F(F(delta+nextBase)+subgravity*propertyScale)`를 쓴다. 새 whole 함수 독립대조: 상한 미도달1,024사례/6,144필드, 상한100/200와 큰 속도를 포함한2,048사례/12,288필드 모두 bit 일치. 원본 cap 경로의 길이²는 `F(F(x²+y²)+z²)`, scale=`F(cap/F(sqrt(length²)))`이다. 양수 상한·finite 입력/관성0·damping0·보통 collider 경계이며 일반 회전/NaN 전체를 이 결과로 확정하지 않는다.

마지막 **0a4b8c8**은 `delta=F(current-baseline)`를 상한에 맞추고 **최종 nativeMotion+60 physicalVelocity**를 쓴다. damping0이면 그 저장값은 clip된 delta다. 위치에 쓰는 실효 속도는 별도로 아래 순서다.

```text
factor = F((S+74 invSub)*(S+C0 damp/tau))
COMVelocity = F(F(baseline + F(physicalDelta*(S+B0 tau/damp)))*factor)
COM64_new = COM64_old + double(F(COMVelocity*dt32))
```

finalize cap은 prestep과 계산 순서가 다르다. `scale=F(F(1/F(sqrt(length²)))*cap)`이며 `cap/sqrt`로 합치지 않는다. whole finalizer 독립1,024사례의3,072 f32 velocity+3,072 f64 COM, cap100/200/과속2,048사례의6,144 f32+6,144 f64가 전부 bit 일치(null/자동매핑/fault/PLT0). identity quaternion/angular0 fixture에서 **원본 함수 전체**를 실제 LR까지 실행하고 해당 출력 필드의 독립 식을 대조했다. 일반 회전적분/강체 modifier의 모든 callback까지 대조한 것은 아니다.

실제 MT 첫 프레임: 첫 normal 뒤 current.y=`2.1600024700164795`; seven carry 뒤 baseline.y=`2.156463384628296`; final current.y=`2.1600022315979004`; physical delta.y=`.003538846969604492`; 위치용 COMVelocity.y=`.449705570936203`다. 이 실효 속도로 dt만큼 적분하므로 native COM.y=`.8074951050803065`, body origin.y=`.45749515295028687`가 된다. 침투 bias 속도를 다음 프레임 이동 속도로 그대로 보존하면 원본과 달라진다. **이 수치는 synthetic capsule 접촉의 결과이며 사격장 조정 상수가 아니다.**

다음 **09d5b68**은 nativeMotion의 double COM에서 회전한 local COM offset을 빼 body origin을 만든다. 원본 nativeBody의+c/+1c/+2c가 local COM offset, +30/+34/+38은 f32 origin, +40/+44/+48은 `F(origin64-double(origin32))`의 잔차다. identity/no-angular 새 whole 함수1,024사례/6,144 f32 origin·잔차 필드가 독립 계산과 bit 일치했다. fixture의 local center.y는 원본 생산값`.34999996423721313`이며 보기에 예쁜`.35`로 치환하지 않는다. 이 함수의 실제 shape AABB callback은 원본을 계속 실행했다. 일반 quaternion 회전 식은 native_motion_body.c 판독 경계이며 이 시험은 identity만 대조했다.

이후 §6.10.3의 **3ae6410→09d1de0→gameBody+d8/previous108/linear138** 및 기존게임 **0f76f78→3a13a24/3a102f0→Player functor24d26f8(반경·up 빼기)→Actor+28c→슬롯19 2483134→Player+10** 연결로 위치와 속도가 돌아온다. 원본 새 수식 체인으로 고정 `character_controller.md:L77`의 "Havok 위치 적분+접촉 해소 내부"를 해소한다. 사격장 실제 메시 전체/복합 몸체·shape의 native 접촉 생성, 게임 SplPlayer motion 속성의 최종 runtime ID/모든 modifier 바인딩은 `L15` 및 별도 TOI 복합질문에 남기며, 계산 함수의 식이 해소된 것을 scene 전체 검증으로 확대하지 않는다.

검증 파일: `physics_initial_velocity_emu.json`, `physics_prestep_capture_probe.json`, `physics_prestep_emu.json`, `physics_prestep_cap_emu.json`, `physics_finalize_capture_probe.json`, `physics_finalizer_emu.json`, `physics_finalizer_cap_emu.json`, `physics_pose_capture_probe.json`, `physics_pose_emu.json`; 원본 snapshot은 `physics_{prestep,finalize,pose}_{fixture.json,heap.bin,stack.bin,bss.bin}`. 각 snapshot에서 실제 LR/주소/입력 register를 보존한다. 상세 commands는 `analysis/completion/r8/physics_commands.md`.

정정 이력(2026-10-03): initial cap 모델의 prestep 합산 순서 오류168사례, finalize의 잘못된 MotionProperties 포인터1,359사례, 그 수정 뒤 `cap/sqrt`와 `(1/sqrt)*cap` 차이536사례를 실패 JSON에 보존했다. 실제 ARM `FADDP→FADD`, 실제 function x0 context+30 pointer, `FDIV1/sqrt→FMUL cap`을 확인해 최종 대조0bad를 얻었다. 원본이 틀렸다고 해석하거나 실패 결과를 성공 건수에 더하지 않는다. char motion bind3ae62cc와3c4f0b8의 새 판독은 resource 쌍 등록/별도 body 생성일 뿐 최종 runtime motion ID를 확정하지 못했으므로 L15는 유지한다.

### 6.11 point 특수 TOI의 원본 전체 실행 (9차, 2026-10-03) **[판독]+[실행: 제한 경로]**

새 함수 `0x7100aefd00`은 두 vertex 배열·개수와 질의 설명자를 `0x7100aefdc0`에 전달한다. 성공(+0x30 != 0)이면 접점 +0x10..+0x1f를 0으로 지우고, 법선 +0x20을 설명자 +0x10/+0x20/+0x30의 회전 열로 바꾼다. 원본 `0x7100aefd80`~`0x7100aefd90`의 연산은 `FMUL` 3번 뒤 `FADD` 2번이며 FMA가 아니다. `0x7100949570`의 vertex 하나가 원점이고 회전 추가 인자가 없는 특수 분기가 이 함수를 사용한다. 일반 형상·각운동은 다른 `0x7100aec920` 경로다.

설명자 Q의 확인된 입력은 Q+0 delta(vec4), +0x10/0x20/0x30 회전, +0x40 원점(vec4), +0x50 허용값 2개, +0x58 초기 fraction 2개, +0x60 합산 convex radius 2개, +0x68 반복 상한, +0x6c flags(byte bit3 포함)이다. 출력 O는 +0/4 fraction, +8/c separation, +0x10 point(vec4), +0x20 normal(vec4), +0x30 valid. 원본은 delta 제곱합이 `1.4210855e-14`보다 작으면 실패한다. 진행 축과 delta의 내적이 양수이면 실패하며, 최대 fraction 직전의 `2^-23 / |delta|` 여유를 포함한 경계를 사용한다. bit3의 시작 겹침 법선 교체 분기는 `0x7100af0884`~`0x7100af08c0`이다. 이는 원본 입력 주소 판독이며 모든 flag의 고수준 이름 확정은 아니다.

`r9_physics_point_toi_emu.py`는 양쪽 배열을 원점 vertex 하나씩, identity 회전, 초기 fraction 0으로 둔 원본 **aefd00→aefdc0 전체**를 2,048건 실행했다. 축·방향·반지름·거리·속도를 바꾸었고, 1,212 hit/836 miss, 24,576 f32 저장 필드와 전체 출력 131,072바이트가 독립 계산과 비트 일치했다. 유한 축 방향에서 기대 fraction은 `f32(f32(D-r)/speed)`이고, 접근 여부 및 최대 fraction의 위 여유 경계를 먼저 검사한다. PLT/자동 매핑/null/fault 모두 0. `physics_point_toi_emu.json`에 결과를 저장했다.

**실패를 보존했다.** 처음 독립 계산이 다른 법선 축에 +0을 넣어 음수 축 hit 599건에서만 불일치했다. 원본의 normal 회전 `FMUL/FADD`는 -0을 보존한다. `physics_point_toi_signedzero_reference_failure.json`의 차이는 normal의 부호 바이트(+0x23/+0x27/+0x2b/+0x2f)에만 있으며 fraction/valid는 이미 일치했다. 독립 기대값에 동일 signed zero 연산을 적용한 후 0건이 되었다. 원본 결과를 바꾼 것이 아니다.

**범위:** 이 실행은 one-vertex/identity/유한 축 방향 특수 경로이다. 일반 simplex 2~4점, 초기 겹침의 fallback, 회전·복합 형상, engine 4처리기의 실제 수집기·재질/접점 생성까지를 이 결과로 확정하지 않는다. 고정 질문 L359/L495/L508은 조사중을 유지한다.

### 6.12 일반 TOI와 engine 처리기 진입 보강 (9차, 2026-10-03) **[판독]+[실행: 제한 경로]**

**입력 정정 이력:** §6.11 초안의 Q+0x68 flags 표기는 틀렸다. 일반 `0949570→aec920`의 Q+0x68은 반복 상한이고 Q+0x6c가 flags다. game 처리기 `3c52f84`의 상수 `0x10000000000`을 query+0x78에 저장하면 query+0x7c=256이며 `0949570`이 이를 native Q+0x68에 복사한다. point 특수 하네스가 Q+0x68=0이어도 통과한 사실은 일반 경로의 반복 상한을 0으로 두는 근거가 아니다. 일반 하네스의 최초 0회 fixture 결과는 `physics_generic_toi_iteration_fixture_failure.json`에 보존했다.

원본 전체 `aec920`의 point/triangle/cube, identity 및 유한 이동 탐색은 함수 반환/null/자동매핑/fault/PLT 0을 확인했다(`physics_generic_toi_probe.json`). 다만 이는 독립 계산 비트 대조가 아니다. 후속 100건 축방향 독립 참조는 **40건 불일치**했다(`physics_generic_toi_aligned_emu.json`). 39건은 diagonal line/triangle/skew quad를 축 extent만으로 계산한 잘못된 참조이고, cube 1건은 단일 나눗셈과 원본 보수적 반복 계산의 1 ULP 차이다. 원본의 일반 GJK 수식·연산 순서를 확인하기 전에는 실패를 성공으로 바꾸지 않는다.

`r9_physics_engine_toi_probe.py`는 원본 game Capsule backend `3c243dc→3c27858`, native shape getter와 `09c78f0` native body를 준비하고 네 game 처리기 `3c52d30/5368c/54140/54de4` **전체**를 실행했다. 모두 `09af088→0947aec→0948f30`의 capsule/capsule 질의와 원본 `3c563dc` 접점 변환까지 도달하고 정상 반환, null/자동매핑/fault 0이었다. 이 형상쌍은 generic `aec920`을 사용하지 않는다. 입력 p0=(2,0,0), p1=(-2,0,0), 두 radius=.6에서 native fraction=.19999998807907104, normal=(1,0,0); 역질의 `54140`은 native normal=(-1,0,0)을 사용한다. 기록 `physics_engine_toi_probe.json`은 실제 query와 native point 128바이트도 보존한다.

**실행 경계:** World와 몸체·회전·좌표는 명시 fixture다. 원본 World query math 및 primitive math를 대체하지 않았지만 WB+0x110 filter/WB+0xd0 codec을 null로 두고 lock/unlock은 원본 RET를 쓴다. 이 최초 probe는 수집된 접촉을 저장할 staging manager 용량이 0이라 game 접촉 목록 저장을 검증하지 않았다. 누락된 game body VT 때문에 native 접촉 후 `3c55f64` null 호출이 발생했던 최초 실패는 `physics_engine_toi_missing_body_vt_failure.json`에 보존했다. 실제 VT5749048을 넣은 결과가 위 성공이며, 실패의 null 호출을 무시하지 않았다. 현재 움직이지 않는 hitbody/identity 입력만으로 상대 운동·회전·모든 generic simplex를 해소하지 않으므로 L359/L495/L508 조사중 유지.

#### 6.12.1 네 처리기의 상대 운동·접촉 저장 (9차) **[판독]+[실행: 축 방향 캡슐]**

입력 묶음 A=[Bullet, ContactList, CastShape, HitBody, p0, p1, Rcast, angular]은 8개 포인터다. 처리기 표 `5756468`은 (52d30,0),(5368c,0),(54140,0),(54de4,0)의 16 B 멤버함수 항목이다. `3c55968`의 모드 3은 항상 54de4다. 그 외, hitBody의 선속도가 0이 아니면 해당 mode를 선택하며 unsigned mode≥4는0으로 돌아간다. 선속도가0이고 각속도가0이 아니면 양수 mode를1로 낮춘 값을 선택한다. 둘 다0이고 음수 mode가 아니면0을 선택한다. 원본의 부호검사/범위초과 fallback은 그대로 보존한다. typed body RTTI5576220이고 bit6/7이0이면 선속도+2d4/각속도+2c8, 그 외 +144/+138을 읽는다. 이는 정적/운동/회전의 기하 종류 4개를 뜻하는 표가 아니라 **질의 상대 운동 구성의 네 변형**이다.

Pcur=HitBody+d8, Pprev=+108. 회전은 행렬을 `12da6dc`로 quaternion으로 바꿔 norm>0일 때 reciprocal sqrt로 정규화한다. 질의0(52d30)은 현재 pose의 역회전에서 p0−tcur와 (p1−tcur)−(p0−tcur)를 만든다. 질의1(5368c)은 이전 pose를 기준으로 p1에 ΔCOM를 더한다. ΔCOM=COMprev−COMcur; bit6=1이면0, 그 외 원본 backend vt28=`3c4fe24`에서 localCOM를 받아 각각 이전·현재 pose로 변환한다. 질의3(54de4)도 이전 pose/ΔCOM를 쓰며 A[7]의 각운동을 추가한다. 질의2(54140)는 두 형상의 역할을 뒤집어, hitBody의 이전 원점에서 현재원점+(p0−p1)로 이동시키는 역질의를 만든다. bit6=0이면 inverse(qprev)*qcur에서 θ=2acos(clamp(abs(w),0,1))와 정규화된 xyz 축을 만들고 θ>1.1920929e-6일 때 θ·axis를 각운동으로 전달한다. 위 inverse는 norm²≤FLT_EPS이면 conjugate, 아니면 conjugate/norm²다.

**[실행]** `r9_physics_engine_toi_relative_emu.py`는 네 처리기 전체와 native capsule closest/advance 및 원본 후처리/목록 함수를 1,024건 실행했다. X/Z축, 방향, 이전/현재 위치를 바꾸며 원본 query origin/delta 2,048필드와 fraction·game 보간 위치 4,096 f32필드가 독립 계산과 비트 일치했다. 전체 1,024 hit, 오류/null/자동매핑/fault 0. native closest callback은 실제 `0954550`, 원본 수집기/포인터 목록은 `3c563dc→3c5621c/56588/5677c/5698c→3a60c74`다. 새 후처리 4함수는 `engine_post.c`, 성공 JSON은 `physics_engine_toi_relative_emu.json`이다.

캡슐의 이 축 제한에서 `d2=f32(o*o)`, `inv=f32(1/sqrtf(d2))`, `N=f32(o*inv)`, `sep=f32(f32(d2*inv)-f32(rA+rB))`, `closing=f32(N*delta)`, `t=sep<=.001 ? 0 : f32(0-f32(sep/closing))`다. `0954774..47f0` 원본은 sqrt를 거리로 직접 쓰지 않고 **d2*inv**를 쓴다. 최초 단순 abs(o)·unitNormal 참조의 173건 차이는 `physics_engine_toi_relative_reference_failure.json`에 보존했다. 그 정정 뒤 초기 겹침 3건은 음수 t를 기대하여 실패했고 `physics_engine_toi_initial_overlap_reference_failure.json`에 보존했다. 원본은 initial-distance contact 및 TOI contact 두 개를 fraction0으로 저장한다. 해당 원본 분기를 반영한 최종 대조가 0건이다.

staging 원천은 `[EngineWorld+10]+8`(worldtype0), 처리기 local meta+20이다. staging+24를 원자적 증가시키고 유효 구간(+20/+28)과 count+10/array+18을 적용하여 128 B 접점을 복사한다. 저장된 접점+24(world bullet center)=p0+f*(p1−p0), 순서는 FSUB→FMUL→FADD이며 FMA가 아니다. 5368c/54de4는 접점+0에서 f·ΔCOM를 빼며, 54140은 보간 중심+(nativepoint−p0), normal을 FNEG한다. ContactList+98/+9c 카운터를 증가시킨 뒤 같은 접점 포인터를 16 B 목록 항목에 저장한다. 첫 static fixture 4건도 `physics_engine_toi_stage_probe.json`에 별도 보존했다.

**경계:** 전체 함수는 실행했지만 입력은 identity/zero localCOM/XZ 유한 축 방향 캡슐이다. game body flag는 동적 입력 소비를 검사하도록 설정했고 native 등록 몸체 자체는 static fixture다. 실제 게임 동적 바인딩·지형 전체·필터/코덱과 일반 simplex의 독립 수식 증거로 확대하지 않는다. 단계별 원본 수식 확인 결과를 whole L359/L495/L508의 일부 근거로만 더한다.

#### 6.12.2 각운동 내부 실제 진입 (9차) **[판독: 사슬]+[원본 실행 관찰: 독립 비트 대조 전]**

`r9_physics_engine_rotation_toi_probe.py`는 vertical capsule의 pure Y 회전 θ=0/.1/1/π2를 넣고 전체54140/54de4를 8건 실행했다. θ>0 6건에서 `0948360→094e6e4→af7b70`(3~4회) 및 `0929530`, 이후 실제 game staging/list까지 도달했다. 모두 정상 반환/null/자동매핑/fault0, native math callback 대체0. 회전 core3함수 새 디컴파일은 `rotation_toi_core.c`, 입력 Q·출력은 `physics_engine_rotation_toi_probe.json`에 보존했다. 기하가 회전 불변이어도 원본 fraction은 .19999997317790985~.20000001788139343로 달랐다. 이를 .2로 바꾸거나 아직 독립 수식 대조 없이 [실행] 확정으로 세지 않는다. 이전 one-vertex proof와 일반 회전 proof를 혼합하지 않는다.

### 6.12.3 회전 시간식 새 지원 [판독]+[실행: 부분]

2026-10-03 [rotation_toi_advance.md](rotation_toi_advance.md) §§3~6·10: 원본 whole54140/54de4 384회/core384회, 실제 advance700/refine806=3,012 f32필드 독립 bit 불일치0. 두 원본 block 각8,192회의32,768f32필드도0bad이며 NaN/FMINNM 경계를 포함한다. query130=1/131=0,최소진행1/256 writer/consumer를 판독했다. OS/TLS/할당 경계를 포함한 실제원본 support·quat를 계산스텁으로 대체하지 않았다. generic support/closest, 보간·추가vertexguard 전체는 별도 미확정이라 fixed3행 상태를 올리지 않는다.

### 6.12.4 일반 지원점·전진식 새 지원 [판독]+[실행: 부분]

2026-10-03 [generic_toi.md](generic_toi.md) §§3~6·10: original `af107c`8193회/32772필드 비트0bad(동률904),`aec920` interior aef0bc~aef1c0 4097회/10200 f32·정수필드0bad. 동률은4lane간우선순위이며global첫index가아니다. 전진limit끝은현재contactvalid경로가있다. 원본classifier는 **B featurecount | (A featurecount<<3)** 로 중간명명을 정정했다. 두collector가있는게임genericwrapper는arg7!=NULL로시작t0이며,別one-pointdirect실행을그경로전체의증거로확대하지 않는다. 실제fullgeneric8회 trace는관찰만이고 independentfullmath증거가아니다. `ae7b34` recovery·sphere/quad `094ae10`·회전support/pose를 이어 확인한다.

### 6.12.5 회전 자세 callback 연결 (9차, 2026-10-03) **[판독]+[실행]**

새 [rotation_pose.md](rotation_pose.md) §3~11: 원본 quaternion interpolation `08a8764`·48 B matrix writer `08a5ed0` 및 SIMD trig `08a69e0/08a6770`을 4097사례/**98328필드** 독립 f32 비트0bad로 확정했다. 게임 회전 처리기 `3c54140/3c54de4` whole8회→실제quat16/matrix24 callback의 input→return **352필드**도 비트0bad이며 정상 반환/nullauto0. theta0/.1/1/π/2 수직capsule·filterNULL fixture의 경계를 유지한다. 회전 support/EPA 전체와 실제 Lby 지형 모든 쌍은 미확정이며 pose 성공만으로 L359/L495/L508을 확정 승격하지 않는다.

### 6.12.6 겹침·퇴화 복구 원본 근거 (9차, 2026-10-03) **[판독]+[실행: 부분식]**

새 [penetration_recovery.md](penetration_recovery.md) §2~11:ae7b34→ae9b14→seed/support/f64facet/horizon/barycentric 전 본문을 새 판독했다. 전체 ae926c plane4097/65552필드, 전체 ae9590 barycentric4097/32776필드 독립비트0bad. 실제generic10whole의plane32+barycentric14=46callback/624필드도input→return0bad,nullauto0이다. 첫barycentric898참조오류를 원본 합 순서로 정정하고 failureJSON보존. 전체EPA/GJK topology의 독립 비트 검증과 부분식·source판독·wholetrace 수준을 구분한다. 최신사용자지시로TOI확대중단, L359/L495/L508조사중유지.

### 6.12.7 일반 closest 및 sphere→quad 부분 검증 마무리 (9차, 2026-10-03)

[원본 closest 지원 문서](../../../analysis/completion/r9/physics_gjk_support.md) §6.1~4/10~11: A1/B2·A2/B1, A1/B3·A3/B1, A1/B4·A4/B1, A2/B2의 원본 signedmask/정점순서/reduction/normal 블록 **32768사례/724904필드 비트0bad**. 각 synthetic 진입·nearzero 중단·처음 참조 피연산자 정정의 경계를 문서대로 유지한다. A2/B3·A3/B2와 회전 closest 대응은 아직 미확정이다.

새 [sphere_quad_toi.md](sphere_quad_toi.md) §3~11: 원본 전체 `094ae10` **5120회/25150필드** 독립f32 비트0bad. 수직2048/13808, scaled oblique3072/11342, A/B radiusoverride·extra radius 포함. SDK mathstub/nullauto0; first199 signed-zero/earlycap 참조오류 보존. 임의 일반/퇴화/initial 전체에 대한 확정으로 확대하지 않는다. 사용자 최신지시로 TOI 신규 확대를 마무리하고 FillUp에 집중한다. 고정 L359/L495/L508은 부분 근거를 저장하며 조사중 유지한다.

## 7. 웹 포팅 구조

| 모듈(웹 권장 이름) | 책임 | 원본 대응 |
|---|---|---|
| `PlayerVertical` | 수직 속도 `vy`(본체+0x73c)·공중 프레임 수·중력값 | `0x71024a7d00`, `0x71024c9684` |
| `CharacterBody` | 캡슐 충돌·접지·이동(Phive 대체). 공중에서는 게임 속도를 그대로 적용 | ctrl + GameInAir(+0x1c=1) |
| `ImpactAccumulator` | 다른 물체에 밀릴 때의 가속도 2개와 감쇠 | ImpactAndReject `0x71012adb58` |
| `BulletBody` | 탄 위치 적분·구 쓸어 넘기기 충돌(바닥 전용/그 외 2개)·멈춤 응답·접촉 큐 | 탄 바디 래퍼 `0x710559f3f8`, phive 탄 바디 `0x7105749990`, 스텝 `0x7103b0a2bc` |
| `BulletContactRouter` | 접촉 → 탄 슬롯22 → 바닥/벽/그 외 분기 | `0x7101646910` (§6.6) |
| `FrameScheduler` | 한 프레임 순서: 단계0[그룹2 → 3 → 4 액터 슬롯18 → Phive Entity] → 단계1[접촉 큐 비우기 → 그룹2 → 3 → 4 액터 슬롯19·20·21] → 단계2[Sensor]. 그룹 = CalcPriority(Before 2, Default 3, After 4, Late 5) | `0x7103c85fbc`, §6.7 |

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
| 원본 실행 | `.venv/Scripts/python web/tools/r5_physics_frameorder_emu.py` — CalcPriority 10/10, 목록 연결 13/13, 그래프 간선 사격장 58/58·무작위 500/500 정확 일치(5차) | §6.7.5, `analysis/completion/r5_physics_frameorder_emu.json` |

스텁·미검증: 플레이어 메인 계산(점프 판정·이동)과 Phive 스텝은 원본으로 실행하지 않았다(수직 속도·중력·공중 카운터·공중 보정 함수만 원본 실행, 나머지는 판독대로 대체). 탄 바디 스텝은 명령 판독뿐이고 원본 실행 비교는 없다. 좁은 단계 TOI 계산(`0x7105756468` 처리기 4종), 접촉 정리 `0x7103a6144c`의 정렬 기준은 판독하지 않았다. 프레임 그래프 실행(5차)은 그래프 노드 추가·뮤텍스·시퀀서 사용 여부 함수를 스텁으로 두고 간선 구성만 원본 실행했다. 작업자 스레드가 그래프를 실제로 소비하는 순서는 간선에서 계산한 도달 관계로만 확인했다.

## 9. 미확정 사항과 다음 근거

| 항목 | 상태 | 필요한 근거 |
|---|---|---|
| 본체+0xc0(공중 프레임) 증가·초기화 시점 | **해소 [판독 + 실행(함수 연결)]** | 슬롯19 `0x710246b574`(+1)/`0x710246b32c`(0), 점프 프레임 메인 계산 `0x710246b32c`(0) — §4.4. 이전에 남았던 "Phive 가 점프 프레임 스텝 중 OnGround 로 되돌리지 않는다" [추정]은 4차 접지 판정(상승 중 바닥 접촉 무시 `0x7102c5dd20`, character_controller.md §6.2)과 5차 프레임 순서(슬롯18 → Phive → 슬롯19, §6.7)로 [판독]이 되었다(2026-10-03) |
| 최종 속도 v(param_17)의 수직 성분 구성 | **해소 [판독]** | `0x710245aed8` — §5.1 |
| 이동 벡터의 `0.92y − 0.0002`와 +0x73c의 관계 | **해소 [판독]** | `0.92y − 0.0002`는 이동 속도(+0x114) y 보정(`0x710245b2b4` 끝 `0x710245edc0`), 최종 y = 둘의 합 |
| 세계 기본 중력(+0x2a4) 런타임 값, dt(+0x24) | dt: 생성 시 1/60 **해소 [판독]**(5차, §6.4: 덮어쓰기 블록 유무와 무관하게 `0x7103db385c`가 기록). 기본 월드 설명자 중력 (0, −9.8, 0) [판독]. 남은 것: 실행 중 dt 변경 경로, 상태 S가 읽는 `[월드+0xb8]+0x2a4`가 설명자 중력에서 오는지 [미확정] | `-9.8` f32 상수는 main 전체에서 S 생성자 1곳뿐이고 PhiveConfig에도 중력 항목이 없다(2026-10-02 [move] 확인). 영향 범위: 공중 이동은 GameInAir(+0x1c=1)라 G0와 무관, 지상은 scale 0 → **플레이어 궤적에는 공중 ≥ 3인데 Phive 상태가 OnGround인 경우에만 영향**. dt는 게임 속도 ×60을 Phive가 적분하는 데 쓰이므로 1/60이 아니면 프레임당 이동량이 달라진다 — `[[*0x71057906f0]+0xe8]+0x24` writer(세계 스텝) 추적 필요 |
| 특수 상태 0x18/0x1b/0x1c, `+0xa818` 컴포넌트 이름 | **해소 [판독+데이터]** | 0x18 Jetpack, 0x1b Skewer, 0x1c SuperLanding(본체+0x65c = 10 + 특수 열거), +0xa818 = spl::PlayerPeriscope(`player_components.tsv`). Periscope +0x38/+0xb0은 8차 §4.1.1에서 해소 |
| 탄 바디 적분·충돌 응답 | **해소**(2026-10-02, [판독]) | §6.3~6.4 |
| 탄 접촉 반응 시퀀서의 프레임 내 실행 위치(→ 첫 명중 age) | **해소 [판독]+[실행: 그래프 간선]**(5차): 단계1 그룹0 = 물리 직후·모든 액터 슬롯19/21 앞(이전 [추정] "슬롯21 뒤·다음 슬롯18 앞"은 정정) | §6.7. 남은 것: 탄 생성 프레임에 슬롯18이 도는지 [미확정] — 생성 시점(사격 처리)과 그래프 구성 `0x7103c85fbc` 호출 위치 |
| 좁은 단계 TOI(처리기 4종)·접촉 정렬 기준 | 미판독 | `0x7103c52d30`/`0x7103c5368c`/`0x7103c54140`/`0x7103c54de4`, `0x7103a6144c` |
| 관통력 body+0x18c를 쓰는 탄 | 미확정(기본 −1 = 항상 막힘) | 5차 시도: `physics_memscan.py 0x18c --kind strs` 전체 40곳 이상·phive 범위 6곳(`0x7103a7e718`, `0x7103a87d2c`, `0x7103a8aab4`, `0x7103a8abfc`, `0x7103a920d4`, `0x7103aea4ac`)을 봤으나 탄 바디 setter 로 확인된 것 없음(`0x71016c33f8`은 다른 객체의 파라미터 정수→실수). 다음: phive 탄 바디 vtable `0x7105749990` 의 setter 슬롯, `0x7101a856e8` 표 |
| 월드 dt를 런타임에 바꾸는 경로 | 생성 시 1/60 [판독], phive 범위 쓰기 15곳 전수 분류 → 생성자만 월드+0x24 기록 [판독], 범위 밖 변경 [미확정] | 범위 밖에서 월드 포인터(`[*0x710599dfa8+0xe8]`)로 +0x20/+0x24 를 쓰는 코드, 물리 시스템 초기화 인자 +0x28 덮어쓰기 블록 공급자 |
| shapeTag → 재질표·충돌 필터(hknp 코덱·필터 구현) | 행 선택 한 단계 [실행] (character_controller.md §3.5), 배열 부착 writer [미확정] | 질의 문맥 +0x130의 [0] vt+0x40(코덱 decode)·[1] vt+0x40(필터) 구현 클래스. 월드 생성 `0x7103ac71c8` 안의 하위 객체 생성(`0x7103b1b33c`, `0x7103a72c28`, `0x7103ac3960` 등)에서 vtable을 찾을 것. 5차 시도: bphsh 경로 생성 `0x7103a221cc`(".%s.bphsh")까지 찾음, 헤더 오프셋(+0xc/+0x10/+0x14…) 기반 포인터 저장 스캔은 phive 범위에서 해당 없음. 다음: `0x7103a221cc` 가 만드는 자원 객체의 로드 완료 콜백, 형상+0x28 에 정보 객체를 쓰는 `str x,[x,#0x28]` |
| Phive OnGround/InAir 전이 조건·점프 프레임 공중 유지 | **해소 [판독]** (4차) | 상태 vt+0x30 `0x71012aa648`/`0x71012aa108`, SplResultPlayer `0x7102c5a3c8`·`0x7102c5dd20` — [character_controller.md](character_controller.md) §5~6 |
| 플레이어 캡슐·충돌 필터·재질 | **해소 [판독]+[데이터]** (4차) | character_controller.md §3 |
| 액터 계산 단계와 Phive 월드 단계의 프레임 내 순서 | **해소 [판독]+[실행]**(5차) | §6.7. 남은 것: 단계2·3 액터 노드(액터+0x240/+0x248) 생성자, 작업자 ≥ 2 묶음 분기 실행 |
| 컴포넌트 배열이 프리셋 순서로 만들어지는지 | **해소 [판독]**(5차) | §3.3: 파서 `0x7103b12270` 순차 채움, 생성 루프 `0x7103a0c7c4` 순차 추가 |

### 6차 갱신 (2026-10-03, r6 physics) — 위 표·본문에 대한 정정과 보강

| 항목 | 6차 결과 | 수준 |
|---|---|---|
| 세계 기본 중력 런타임 값(§4.3) | 게임 모듈 설정(`0x710344af54` case 0xf) desc+0x28..+0x30 = (0, −9.8, 0) → 하위 월드 생성 `0x7103ac6a20`의 `0x7103ac6bf0`~`0x7103ac6c2c`가 하위 월드+0x298 과 **+0x2a4..+0x2ac** 에 복사(월드+0xb8 = Entity 하위 월드) → 상태 S 생성자 꼬리 `0x7103a86794`~가 G0 = (0, −9.8, 0), 방향 (0,−1,0), 실효 = 배율·G0(배율 2.9387755 → −28.8). `web/tools/r6_physics_gravity_emu.py` 4/4 비트 일치. 생성 뒤 하위 월드+0x2a4 writer: 0x7103a00000~0x7103e00000 `add #0x2a4`·`str #0x2a4` 검색에서 생성 1곳뿐 | [실행]+[판독] |
| 월드 dt 런타임 변경(§6.4) | main 전체에서 `[*0x710599dfa8]+0xe8` 로드 뒤 같은 레지스터로 +0x20/+0x24 쓰기 0건, 월드 vtable `0x7105748188` 슬롯 함수의 x0+0x20..+0x30 쓰기 0건, phive 범위는 생성자뿐(5차) → 실행 중 dt = 1/60 고정 | [판독, 패턴 전수 검색 — memcpy 류 간접 쓰기는 제외] |
| 탄 바디가 SplBullet 모션 속성을 쓰는지(§6.1) | 탄 바디 스텝 `0x7103b0a2bc` 식에 중력·감쇠·속력 상한 항이 없으므로 슈터 탄 이동에 영향 없음 | [판독] |
| 관통력 body+0x18c writer(§6.4) | `spl::BulletChargerBase`(vtable `0x710559ecc8`) 슬롯54 `0x71016c30d4`: 차지 비율 < 1 이면 −1, 아니면 (float)매개변수[+0x30], body+0x190 = `0x7101a88920` 키. 슈터는 쓰지 않음 → −1(항상 막힘). 상대 강체 +0x2a4 기본값 −1.0(강체 생성 `0x7103af593c`의 `0x7103af5bb8`) | [판독] |
| 막는 접촉 비트 +0x68 bit1 출처 | `0x7103c39158`~`0x7103c39190`: 상대 F+0x18/+0x1c 에 질의 레이어/하위 레이어가 있고 형상 행 검사 `0x7103c34b7c` 통과 시 켬(character_controller.md §3.5). 탄 쓸어 넘기기에서 이 코드까지의 호출 사슬은 [미확정] | [판독] |
| 접촉 정리 `0x7103a6144c` 정렬 기준 | 목록+0xc0 모드: 탄 바디 목록은 3(생성 `0x7103b0b230`). 모드 3 = 키 f = (+0x68 & 0x1060) ? +0x60 : 0 오름차순 **힙 정렬(불안정)**, 16 B 항목의 플래그 바이트도 함께 이동. 모드 1·2 = 몸체 원점 기준 접점 거리² (+0x64 == 5 우선) [판독]. `web/tools/r6_physics_contactsort_emu.py` 3000/3000 일치(같은 키 포함 2313건). 같은 f 접촉은 이 힙 순서가 슬롯58/59 법선 선택을 정한다 | [실행] |
| 좁은 단계 처리기 4종(§6.4) | 모두 Havok 형상 캐스트 질의를 구성(질의 +0x?? = 0.001f `0x3a83126f`, 조기 종료 `0x7f7fffee`, 필터 = 월드+0x110, 코덱 = 월드+0xd0, 수집기 vtable `0x71057552a8`) 후 `0x71009af088` 실행. 0.001 의 의미 [추정: 허용 오차]. TOI 내부 [미확정] | [판독, 부분] |
| Havok 솔버 | `0x71009ce484` = "TtBuildCollideTasks"(충돌), `0x71009cee34` = 다음 단계. 캐릭터 몸체가 이 스텝을 탄다 [판독]. 내부 [미확정] | 다음: `0x71009cec84` |
| 단계2·3 액터 노드 | `0x7103cc2934`는 +0x230/+0x238 만 만들고 +0x240/+0x248 은 있으면 쓰기만 함. 0x7103c70000~0x7103d00000 에 실제 값 writer 없음 | [미확정] |
| Periscope +0x38/+0xb0 | 6차 미착수 | [미확정] |

## 10. 검증 코드·실행 결과·기대값 (7차 보강)

새 실행은 `r7_physics_table_emu.py`(원본 BYML 표174값), `r7_physics_mask_emu.py`(강체·캐릭터 mask writer 1024사례/5120필드), `r7_physics_mesh_emu.py`(4개 원본 bphsh 부착24필드·접촉 bit1 476사례)이며 모두 불일치0. 원본 함수·스텁·기대값의 상세는 [character_controller.md](character_controller.md) §10 및 [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §10. 기록 `analysis/completion/r7/physics_commands.md`.

정정(2026-10-03): §9의 6차 "막는 접촉 비트 출처 0x7103c39158, 탄 호출 사슬 미확정"은 일반 질의와 탄을 혼동한 기록이다. 실제 탄 경로 `0x7103c55ed8→0x7103c34e14`는 이미 r6 combat에서 확정되었으므로 여기서는 **기존 근거 재사용**으로 정정한다. 7차 신규는 bphsh 정보 writer `0x7103a715b4`와 실제 행 연결 실행이다. §8의 접촉 정렬 미판독 문장 또한 이전 상태이고 §9의 r6 3000건 실행 정정을 따른다.

## 11. 미확정 사항과 추가 분석에 필요한 근거 (7차 보강)

| 항목 | 이번 시도·결론 | 다음에 볼 곳 |
|---|---|---|
| shapeTag → 재질표·코덱 | 배열 부착 writer 미확정은 `0x7103a715b4` [실행]으로 해소. 16 B 재질 reader·쿼리 +0x130 코덱 구현 클래스는 남음. 3b1b33c/3a72c28 명령을 보았으나 코덱 객체로 확인하지 못함 | collision_mesh.md §11, 월드+0xd0 writer·vt+0x40 |
| 좁은 단계 TOI·용접·솔버 | 필터 실행만으로 TOI·침투 보정·용접 동작을 확정하지 않음. 기존 r6 판독 범위 유지 | `0x7105756468` 처리기, `0x71009af088`, `0x71009cec84` |
| 플레이어-표적 실체 충돌 | 데이터 셀 값2→block 배열과 desc→F는 확정. 이름→최종 마스크·전체 솔버 남음 | character_controller.md §11 |
| 나머지 기존 질문 | r6에서 끝난 중력·dt·접촉 정렬·슈터 관통력 기본값·프레임 순서를 다시 신규 성과로 세지 않음. 미해소 단계2/3 노드·작업자 분기·Periscope는 이전 상태 | §9 r6 갱신 표 |

8차 §10 보강(2026-10-03): `web/tools/r8_physics_material_leaf_emu.py`와 `analysis/completion/r8/physics_material_leaf_emu.json` 신규 원본 실행, PLT 미구현0; wrapper getter만 합성. `r8/physics_commands.md`에 성공·실패 명령 기록.

8차 §11 정정: 위 코덱·재질 reader의 과거 미확정 행은 collision_mesh.md §3.4.3의 신규 근거로 해소. 실제 침투 해소·TOI·leaf flags0x20의 용접 소비는 남음; `09af088/09cec84`와 leaf flags reader를 계속 추적한다.

8차 §11 추가(2026-10-03): §6.10에 실제 TOI 디스패처와 solver simulation 진입을 좁혔다. 원본 constructor 포인터25쌍 일치는 전체 TOI 검증이 아니므로 TOI/침투해소/위치 적분은 미확정 유지. 다음0aec920/0aefdc0 및0a4ac10/0a71b90.

8차 §11 Periscope 정정(2026-10-03): 과거 §4.1/§9/6차 표의 P38/Pb0 의미 미확정은 새 §4.1.1 producer·원본1040건 실행으로 해소. 잠망경 카메라/효과 전체는 합성 callback시험 범위밖이며 별도 camera 문서의 상태를 바꾸지 않는다. 웹은 기본 Off0/pending0을 유지하고 pending이 전달되면 Extend/View/Shrink 전체동안 원본대로 중력0 predicate를 보존해야 한다. 코드 변경 없음.

8차 §11 정정(2026-10-03, native 식 해소): §6.10.4/5에서 원본 initial→8normal/7carry→finalize→COM→bodyorigin→Phive 되쓰기를 연결하여 보통 무회전 플레이어의 위치 적분·침투 보정·반복 수 식은 [판독]+[실행]으로 해소했다. 과거 “전체 솔버 미확정” 문장은 현 단계와 위 신규 범위를 구분해 읽는다. TOI 0aec920/0aefdc0·사격장 메시 전체 접촉 생성·runtime motion ID/모든 modifier 바인딩은 미확정이며 C0 quality 바인딩과09d5b68 일반 회전 경로도 다음 근거다. 완성된 식만으로 이 복합질문들의 전체 상태를 승격하지 않는다. 웹 필요: contact normal PGS순서/bit복원·8/1·carry/final physical속도와COM속도 구분·f32곱뒤double적분·native원점잔차를 반영. 코드 변경 없음.

8차 원점 반환 주소 정정(2026-10-03): §6.10.5 초안에서3a83d98을Player+10 writer사슬로명명한것은잘못이다. 기존r6 character_controller§4의실제Actor물리callback/24d26f8와2483134복사주소를다시대조하여위정확한사슬로정정했다. 수학시험출력/확정수는이주소정정에영향없다.

9차 §10 추가(2026-10-03): `web/tools/r9_physics_point_toi_probe.py` 최초 실제 전체 호출은 fraction .375/normal(1,0,0,0)/valid1. `r9_physics_point_toi_emu.py`의 2,048건 대조와 signed-zero 실패 파일은 위 §6.11 참조. 최초 JSON 직렬화는 numpy.bool_ TypeError로 실패하여 bool 변환 뒤 저장했다. 재구현이 signed zero를 버렸던 599건도 삭제하지 않고 실패 JSON에 남겼다.

9차 §11 추가(2026-10-03): 특수 point TOI 경로만 새로 비트 대조했다. 일반 `0x7100aec920` 및 `0x7100aefdc0`의 simplex/fallback·engine `3c52d30/3c5368c/3c54140/3c54de4` 전체 접점 생성은 남음. 다음은 `3c55968`의 4종 선택과 설명자 생산을 원본으로 묶고, native query의 회전/다점 결과를 독립 대조하는 것이다. character_controller §4.2의 live MotionProperties13은 새로 해소되어 이전 'runtime motion ID 미확정' 중 캐릭터 특수13 질문은 정정한다.

9차 §10 보강(2026-10-03): 일반 query 반복 상한 fixture 오류·독립 geometry 참조 불일치·engine body VT 누락 실패는 §6.12에 기록했다. 신규 engine 접촉 저장 함수 3c5621c/56588/5677c/5698c는 기존 notes/index에 없어 lookup·실제 prologue 확인 후 engine_post.c에 새 디컴파일했다. 앞 두 함수는 Ghidra가 tail-called 3a60c74를 inline하여 표시하므로 본문 식은 ARM 명령과 대조한다.

9차 §11 보강: 네 game 처리기의 입력 구성/relative translation/staging/list는 §6.12.1에서 새로 판독·실행했다. 일반 simplex와 native rotation advance 전체 식은 아직 남아 있다. 각운동은 §6.12.2로 원본 내부 진입까지 좁혔으며 다음 094e6e4/af7b70와 aec920의 support/closest-feature/보수적 반복 수식이다.
