# 플레이어 캐릭터 컨트롤러 — 형상·충돌 필터·접지 판정·이동 상태 전이

Phive 캐릭터 컨트롤러가 플레이어 캡슐을 어떻게 만들고, 물리 스텝 뒤 어떤 접촉을 "바닥"으로 인정해 OnGround/InAir를 바꾸는지 정리합니다. 속도 전달·중력·컴포넌트 순서는 [phive_controller.md](phive_controller.md), 게임 쪽 접촉 정리(벽·착지·천장)는 [../player/player_state.md](../player/player_state.md) §7.3입니다. 작업 지침: [../../분석.txt](../../분석.txt).

확정 수준: **[실행]** / **[판독]** / **[데이터]** / **[추정]** / **[미확정]**. 근거는 명령 판독과 데이터가 중심이다. 원본 실행으로 확인한 것은 bss 상수(정적 초기화 에뮬), 공통 쌍 필터(4096건)·shapeTag 행 선택(1024건)·리셋 몸체 원점(1024건)이다(§3.5, §4; 실행 기록은 [collision_runtime_completion.md](collision_runtime_completion.md) §10). Havok 솔버와 접지 판정 함수는 원본으로 실행하지 않았다.

상태: 4차(phys4) 1차 작성, 2026-10-03 충돌 보완·5차(r5) 반영(§3.5 필터·그룹, §4 몸체 원점·프레임 순서). 6차(r6, 2026-10-03): 평상시 Phive → 본체+0x10 write-back 원본 실행(§4.1), 형상 필터 행 결합식 원본 실행(§3.5), 하위 레이어 전환 원본 실행(§3.6), 오징어 비율 t 출처(§3.3), 공중 강제 S+0xf4 의 두 항·Free 상태(§5) 판독. 웹 구현 없음. 디컴파일 `analysis/decomp/phys4/`(p4_world_ctrl.c, p4_support.c, p4_resultplayer.c, p4_pcupdate.c, p4_shape.c, p4_body.c, p4_phases.c, p4_seq.c).

---

## 1. 요약

| 질문 | 결론 | 수준 |
|---|---|---|
| 몸체 종류 | hknp **동적 강체**, 질량100·관성 배율0. 캐릭터 생성은 데이터명 SplPlayer 대신 **특수 MotionProperties13**을 선택: 최대 선속도20000·각속도10000, 선/각 감쇠0·중력 배율0·TimeScale1(§4.2). 게임 최종 속도를 staging+44에 넣고 **위치 적분·접촉 해소는 native 솔버**가 한다(§4.1). | [데이터]+[판독]+[실행], 9차 정정 |
| 접촉 재질 | 플레이어 재질 `Character`는 지형 재질 전부와 **마찰 0, 반발 0**(예외: Shield·ThrowingWeapon 0.4/0.1, PlayerMammal 0.55/0.2, Torpedo 0.4/0.1) → 지형에서는 법선 방향 속도만 지워지는 미끄러운 접촉 | [데이터] |
| 캡슐 | 복합 형상 2개. **ColGround**(지형용) 사람 A(0,0,0)–B(0,0.7,0) r 0.6, **ColOthers**(사람·물체용) A(0,−0.21,0)–B(0,0.51,0) r 0.39. 둘 다 바닥 = 원점 −0.6. 오징어 비율 t에 따라 매 프레임 다시 만든다(§3) | [데이터]+[판독] |
| 충돌 상대 | ColGround = LayerHitMask `GroundOnly`(CustomReceiver·Ground·Water만). ColOthers = `SplPlayerColOthers`(플레이어·물체·적·아이템 등, 지형 없음) + UserShapeTag 마스크 GameUnridable·ActivateWallaObj | [데이터] |
| 바닥 판정 주체 | 결과 컴포넌트 **SplResultPlayer**(`[PC+0xe378]`, 0x1750 B, vtable `0x7105681b08`, 생성 `0x7102c598bc`) 슬롯7 `0x7102c5a3c8`가 Havok 스텝 뒤 접촉 목록에서 지지 여부 S+0x20을 정한다 | [판독] |
| 상태 전이 | OnGround → InAir: `S+0x20 != 1 ‖ S+0xf4`(`0x71012aa648`). InAir → OnGround: `S+0x20 == 1 && !S+0xf4`(`0x71012aa108`). 판정은 Result 끝(`0x7103a88248` 패턴, 현재 상태 vt+0x30) | [판독] |
| 점프 프레임 공중 유지 | **해소**: InAir 상태에서 바닥 쪽 접촉(n.y ≥ 0.6414)은 `n·v > 0.001`(v = Result+0x1338 = 게임 최종 속도, 위로 뜨는 중)이면 버린다(`0x7102c5dd20`). 점프 프레임에는 게임이 InAir로 강제하고 v.y ≥ 0.115라 지지가 생기지 않는다 → 같은 프레임 슬롯19는 공중 | [판독] |
| 최대 경사 | CharacterControllerParam `MaxSlopeAngle` 기본 **75°**(데이터에서 덮어쓰지 않음) → S+0x190 = 1.3089969 rad, S+0x194 = cos 75°. `EnableMaxSlopeAngleContact`(S+0x198)은 메인 계산이 매 프레임 **사람 상태일 때만 1**, 오징어 이동 상태면 0 | [판독]+[데이터] |
| 오징어 벽 접지 | 오징어(S+0x198=0)는 최대 경사 거부가 꺼지고, 지지 법선 하한이 `−0.2571`(104.9°, [0x71058f0b7c])까지 내려간다 → 아군 잉크 벽에서 Phive가 지지(S+0x20=1)를 줄 수 있는 구조 | [판독], 실제 벽에서의 결과 [미확정 — 실행 없음] |
| 접촉의 재질 정보 | 접촉 +0x38(A쪽)/+0x48(B쪽) 16 B = bphsh 재질표 행 (u32 재질 번호, u32, **u64 UserShapeTag 마스크**). Result가 태그 비트로 PlayerDead·Fence·Ice·KebaInk·PlayerUnsafe·Sponge·SquidGuard/Slide 플래그를 만든다(§6.4) | [판독]+[데이터: 비트 이름 대조] |

## 2. 자료 위치

| 항목 | 위치 |
|---|---|
| 데이터 | `extracted/actor/SplPlayer/Phive/{ShapeParam,CharacterMatterRigidBodyParam,CharacterControllerParam,ControllerSetParam}/*.json`, `analysis/player/PhiveConfig.json`(MaterialPresetCollection 28~30, LayerHitMask/SubLayerHitMask, MaterialParamTableSets, UserShapeTagMaskCollection) |
| 파라미터 | CharacterControllerParam 방문 `0x7103b7daec`, 생성자 `0x7103b7d8fc`(vtable `0x710574d498`): +0x90 GravityScale 1.0, **+0x94 MaxSlopeAngle 75.0**, +0x98 EnableMaxSlopeAngleContact true, +0x9b IsEnableBuoyancyForce, +0x9c IsEnableFloatVelocity |
| 디컴파일 | `analysis/decomp/phys4/*.c` (위) |
| 상수 | `player_initemu.py 0x71058f0b60 0x71058f0ba0 --all-init`(작성자 `0x7102c59750`): 0x71058f0b70/74 = 0.64144969, 0x78 = 0.0854, **0x7c = −0.25713277**, 0x80 = −0.5721, 0x90/94/98 = −0.1/−0.3/−0.2, 0x9c = 0x101(두 바이트 플래그 1,1) |

## 3. 형상 (기준 객체: PlayerCollision = 본체+0xa690, 이하 PC)

### 3.1 Phive 캡슐 객체 레이아웃 [판독]
A = +0xd8..+0xe0, B = +0xe4..+0xec, 반경 = +0xf0(설정 `0x7103a6a878`). 근거: `0x71024f2e5c`가 B−A로 축·길이를 구하고, `0x71024fc35c`가 B만 다시 쓰고 반경을 `0x7103a6a878`로 넣는다. 형상 종류 1 = 캡슐(`0x7103a81b24`).

### 3.2 초기화 `0x71024f2e5c` [판독]
복합 형상 `PC+0x38`의 자식 번호 `PC+0x40`(ColGround), `PC+0x44`(ColOthers)를 이름으로 찾고:
- PC+0x138 = ColGround 축(B−A 정규화) = (0,1,0), **PC+0x144 = 길이 0.7**
- PC+0x148 = ColOthers 축 = (0,1,0), PC+0x154 = ColOthers A = (0,−0.21,0)

### 3.3 매 프레임 갱신 `0x71024f5dd8(f1, t, PC, flag)` [판독]
호출: 메인 계산 `0x710247eb5c`. t = PC+0x168(다음 식의 비율; 0 = 사람 형상, 1 = 오징어 형상 — 값의 출처 변수는 [추정: 변신 진행률]).

**6차 보강 — t 의 출처 [판독]** (`move_full_main.c` 7085~7164행, 메인 계산 `0x7102475a54`): 이 함수의 인자는 `(f1 = 본체+0x7a4, f2 = 본체+0x7a8, PC, flag)`이고, PC+0x160 = f1, PC+0x164 = f2 를 기록한다. ColGround/ColOthers 의 t(PC+0x168)는 f2(본체+0x7a8)를 0.2 히스테리시스로 받은 값이고, 피격 캡슐은 f1(본체+0x7a4)을 PC+0x16c 로 같은 방식으로 받는다.
```
target = (상태 번호 ∈ [0x82, 0x90] ∪ [0xaa, 0xac] ∪ {0xed, 0xee, 0x10c}) ? 1 : 0     // [본체+0xa8c8]+0xc8
본체+0x7a4 = target 쪽으로 프레임당 최대 0.1 이동                                     // 사람↔오징어 10프레임
if 새 +0x7a4 <= 이전 +0x7a8:  +0x7a8 += (+0x7a4 − +0x7a8)·0.1;  |차| < 0.001 이면 +0x7a8 = +0x7a4   // 사람 쪽으로는 지수 감쇠
else:                          +0x7a8 = +0x7a4                                                  // 오징어 쪽으로는 즉시
```
정정(2026-10-03, 6차): "값의 출처 변수 [추정: 변신 진행률]"을 위 판독으로 대체한다. 상태 번호의 이름은 상태 표([../player/player_state.md](../player/player_state.md))를 따른다.

다시 만드는 조건: t가 0·1이 아닌데 이전 값과 0.2 넘게 다르거나, 0·1이면 이전과 다를 때, 또는 특수 플래그(PC+0x1c9)·특수 길이/반경이 바뀔 때. 즉 **0.2 단위 히스테리시스**로만 형상을 바꾼다.

```
// ColGround (콜백 vt 0x71056340b0 → 0x71024fc35c)
len = 0x71024b7a3c(): 기본 PC+0x144(=0.7); 특수 0x12면 lerp(0.7, f(), k), 0x1a면 0, 0xf면 0.7·[+0xa798]+0x3a60
r   = 0x71024b7b3c(): 기본 0.6; 특수 0x1a면 1.0; SuperLanding(0x1c) 단계 4면 0.6·[0x71058bbf6c]
B = A + len·axis·(1 − t);  반경 r                 → 사람: 캡슐 0~0.7, 오징어: 원점 구 r 0.6
// ColOthers (vt 0x71056340e8 → 0x71024fc514)
len1 = 0.72 − 0.72t,  r1 = 0.39 + 0.01t           (특수 0x1a면 ColGround 값)
s = −t·r1;  A = A0 + axis·s + (0,0,|(PC+0x1a8, PC+0x1b0)|·k);  B = A + axis·len1   (A0 = PC+0x154)
Result+0x16b8 = r(ColGround 반경);  r이 커졌으면 0x71024c8afc로 바닥 법선 방향 밀어내기
```
같은 함수가 탄 피격용 캡슐(PC+0x48 바디, r 0.35→0.8, 길이 1.65→0)도 t로 보간한다(세부 [판독-부분]).

### 3.3.1 일반 인간/오징어/잠복의 탄 피격 형상 (8차 추가, 2026-10-03) **[실행]+[판독]**

기존 §3.3 끝의 “피격 캡슐 r0.35→0.8, 길이1.65→0, 세부 부분 판독”을 다음 **새 전체 함수 실행**으로 보강한다. 일반 사격장(특수/아머/디버그/Replica 크기 override 없음)에서 피격 body는 **PC+0x48 ColBullet**이고, cached t=PC+0x16c는 B+0x7a4를 원본 0.2 히스테리시스로 받은 값이다. 입력 t가0 또는1 부근 `±2^-23`이면 cached값과 다를 때, 중간값이면 `abs(f32(old-t))>0.2f`일 때만 갱신한다. 상태→B7a4의10프레임 접근과 B7a8의 별도 지형 형상 접근은 기존 r6 §3.3 근거를 재사용한다. 잠복 여부로 별도 ColBullet 치수를 선택하는 분기는 없으며, 오징어 이동 상태집합의 t를 함께 사용한다.

```text
r = f32(0.35f + f32(f32(0.8f-0.35f)*t))
H = f32(1.65f + f32(-1.65f*t))     // 전체 높이용 값. 캡슐 축 길이가 아님
if H <= f32(r+r): A=B=(0, f32(H*0.5f), 0)
else:            A=(0,r,0); B=(0,f32(H-r),0)
```

따라서 인간 t0: A=(0,.35,0),B=(0,1.30,0),r.35. 오징어 t1: A=B=(0,0,0),r.8. 중간값의 sphere 전환에서도 원본 H를 clamp해 올려서 보정하지 않는다. t.6이면 A=B=(0,.3299999833,0),r.6200000048이다. **H1.65는 축 길이가 아니라 인간의 총 높이**이며 기존 “길이1.65” 표현을 정정한다(2026-10-03). 겉보기 캐릭터 크기로 반경을 축소하면 원본과 다르다.

같은 갱신이 **PC+0x58 ColBullet_Chariot**의 중심도 A=B=(0, `f32(.9f+f32(t*.100000024f))`, `f32(.4f-f32(t*.4f))`)로 바꾼다. 반경1.15는 유지된다. 이 body는 일반1인연습에서 활성 스페셜로 사용하지 않으며 데이터·원본 body 생명주기 조건을 따로 따른다. PC+0x50은 CoopZombie body로서 이 보간 대상이 아니다.

새 `r8_physics_hitshape_emu.py`는 **24f5dd8 함수 전체**(일반 조건 fixture, 지형 cached t0)를 실행해 입력끝점/중간값/히스테리시스/랜덤 연속1,014사례에서 ColBullet7·Chariot7·cached t1의 **15,210 f32필드가 독립 식과 비트 일치**, null/자동 매핑/실행 오류0이었다. 결과 `physics_hitshape_emu.json`. 타입 질의만 합성 Capsule RTTI true, 외부 mutex 단일 스레드 no-op; 실제 shape pending 재생성은 shape+0x14 bit5 fixture로 제외했다. 반경 저장은 원본3a6a878을 실행(월드 최소.05 fixture). 첫 보조 shape를PC50으로 착각한 독립 기대값1,009불일치는 `physics_hitshape_wrong_secondary_failure.json`에 보존했고 PC58 명령 판독으로 fixture/기대값을 정정했다. ColBullet는 이 첫 실패에서도 불일치0이었다.

형태 갱신 함수는 bit11을 변경하지 않는다. 피격 shape 크기와 bool1=pair거부/bool0=mask복원은 §3.3.2의 별도 경로다. combat/hitbox의 후보24f4994(8controller 완료 AND),24f4a44(완료controller해제),24f4878(침투/커스텀flagreset),24fbb7c(destructor)는 기존 decomp 재사용으로 확인한 생명주기 함수이며 이 크기 갱신 함수와 혼동하지 않는다. 원본 pending shape가 native capsule로 재생성되는 전체 소비는 실제 접촉 솔버 질문의 남은 범위다.

8차 원본 native 재생성 연결 보강(2026-10-03) **[실행]+[판독]**: 실제 Capsule vtable `0x7105745788`의 +0xa0는 **새 `0x7103a6aef4`**. 기존 재생성 처리 `3a66ea4`가 pending flags를 이 슬롯으로 넘기면 A=gameShape+d8/B=e4/R=f0을 읽는다. 세 축 A−B가 모두 ±2^-23 안이면 원본 **092efbc sphere**, 아니면 **0930b40 capsule**을 생성한다. 새 shape가0이면 실패 반환, 유효하면 backend=`gameShape+f8`의 vt+38=**새3c2799c**가 새 native ptr refcount를 올린 후 backend+8에 교체하고 이전 ptr refcount를 내린다. 이어 임시 생성 refcount를 내리고 backend vt+18=**새3c27858**가 nativeShape+28에 gameShape owner를 기록한다. `3a66ea4`는 dirtyflags를0으로 지운 뒤 gameShape의 참조 body 목록을 돌며 기존3a7ffd0으로 형상 변경을 알린다. pending shape의 소비 `3ac83b4/3aca1b4→3a66ea4` 호출은 기존 frame단계 근거 재사용이다.

새 `r8_physics_hitshape_native_emu.py`는 앞의 원본 전체24f5dd8을 **실제 Capsule VT의 RTTI/A0 및 실제 backend 재생성/교체 콜백**과 연결했다. 초기 backend도 새 원본3c243dc로 만들었다. 연속1,014사례에서 game15,210+native정점/반경9,207 = **24,417 f32필드**가 독립 기대값과 비트 일치, native종류(1 sphere/2 capsule)·정점수·owner포인터 **6,084필드** 일치; null/자동 매핑/실행 오류0. 결과 `physics_hitshape_native_emu.json`. 이제 Capsule RTTI·native 재생성/shape math 콜백은 스텁하지 않는다. 참조body 목록은 비어 있는 fixture이므로 실제 부착 body의 shape-change notification/broadphase 갱신 및 전체 접촉 솔버는 별도 미검증이다. 첫 native 초기 fixture가 owner bind를 빠뜨려2필드 불일치였던 기록은 `physics_hitshape_native_owner_initial_failure.json`에 보존하고 실제3c27858 초기 binding을 실행해 정정했다. 원본식 변경 없음.

### 3.4 충돌 필터 데이터 [데이터]
| 형상 | 재질 프리셋 | LayerHitMaskEntity → 맞는 레이어 | 기타 |
|---|---|---|---|
| ColGround | SplPlayerColGround | GroundOnly(26) → CustomReceiver, Ground, Water | |
| ColOthers | SplPlayerColOthers | SplPlayerColOthers → CustomReceiver, GameCustomReceiver, SplPlayer, SplPlayerChariotShield, SplInkShield, SplInkFilm, SplObject, MissionEnemy, SplCoopEnemy, SplItem, SplWallaObj | UserShapeTagMask GameUnridable, ActivateWallaObj |
| 강체 | LayerEntity SplPlayer(5), SubLayer Unspecified(데이터 값). 실행 중 매 프레임 3/4/5/6/7/12 로 바뀐다 — §3.6 [실행] | BlockableSubLayerHitMask SplPlayerCharaCtrl(오징어 하위 레이어 4·5·6, SuperHookCheck, VehicleSpectacle 제외) | |

지형 삼각형의 필터는 shapeTag별 u64(=LayerHitMask | SubLayerHitMask<<32, [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §3.4). 예: `SplKeepOutPlayer`(플레이어만 막는 벽), `SplPlayerThrough`(플레이어 통과), `SplInkThrough`+`SquidThrough`(철망: 잉크·오징어 통과). 기존 결론: 두 필터의 결합식과 콜백 클래스가 미확정이었다. **2026-10-03 정정 [실행]**: 공통 강체 쌍은 Default/Same/Other 표비트와 양쪽 Layer/SubLayer 마스크 6개를 AND한다(`0x7103c4dd30`, 4096/4096 exact match). **정정(2026-10-03, r7)**: override 결합은 r6 [실행], 배열 attach는 r7 §3.5.2 [실행]으로 해소. 코덱 클래스·16 B 재질 reader는 7차 당시 [미확정]으로 남았다. **8차 정정(2026-10-03): 신규 `3c4579c` 코덱 생성자와 `12ac5e0/12acb38/0997078` 실행으로 해소**([../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §3.4.3). 결합식·그룹·행 선택은 §3.5, 실행 기록은 [collision_runtime_completion.md](collision_runtime_completion.md) §10.

### 3.5 충돌 필터 결합·비교 그룹·shapeTag 행 (2026-10-03 보완 + 5차)

기준 객체: `A`/`B` = 강체, `F = *(body+0x180)` = 그 강체의 필터 객체. shapeTag 필터 표는 별도 형상 객체에 붙는다.

| 기준/필드 | 타입·의미 | writer | reader |
|---|---|---|---|
| F+0x08 bits0..5 | 레이어 번호(공통 표 행·열) | 생성 `0x7103a5fe40`(desc[0] & 0x3f; 강체 `0x7103af6088`·캐릭터 몸체 `0x7103a85a8c`·탄 `0x7103b0ae68`이 부름) [판독, 6차]. 실행 중 변경 = 대기 setter `0x7103af3834`(대기 버퍼 +0x8c, 플래그 bit12) → 월드 명령 처리 `0x7103b07b8c`. 탄은 래퍼 slot22~25 | `0x7103af44e8`, `0x7103c4dd30` |
| F+0x08 bits6..11 | 하위 레이어 번호 | 생성 `0x7103a5fe40`(desc[1], `bfi #6,#6`). 실행 중 변경 = 대기 setter `0x7103af394c`(+0x90, bit13) → `0x7103b07b8c` [판독, 6차]. 플레이어 값 규칙은 §3.6 [실행] | `0x7103c4dd30` |
| F+0x08 bit28 | 형상(shapeTag) 필터 행 사용 | 대기 setter `0x7103af43a4`(+0xc4, bit24) → `0x7103b07b8c` 의 `bfi #28,#1`(`0x7103b086a8`). 물리 구성요소 초기화 `0x71012e9914`가 functor `0x7105576db8`(slot0 `0x71012ea8c4`)로 몸체 집합을 돌며 **레이어 3(Ground) 몸체에 1** — 단 액터 태그 `Actor_MapParts_KeepOut` 또는 `Actor_Lift_KeepOut`이 있으면 건너뜀 [판독, 6차] | `0x7103c34b7c`, `0x7103c5e244` |
| F+0x0c | u32 | `0x7103a5fe40`: `[[*0x710599dfa8]+0x18]+0x48]+8` [판독] | |
| F+0x10 | 별도 u32 마스크 | 강체 `0x7103af6088`·캐릭터 `0x7103a85a8c`: desc+0xc0 → F+0x10 [실행, 7차] | BYML 이름과의 대응은 §3.5.1 [미확정] |
| F+0x18 | u32 막는 상대 레이어 마스크 | factory `0x7103a5fe40`의 Default block 행 초기화 뒤, 강체 `0x7103af6088`·캐릭터 `0x7103a85a8c`가 desc+0xc4로 덮어씀 [실행, 7차] | `0x7103c4dd30`, `0x7103c34e14` |
| F+0x1c | u32 막는 상대 하위 레이어 마스크 | 강체 `0x7103af6088`·캐릭터 `0x7103a85a8c`: desc+0xc8 → F+0x1c [실행, 7차] | `0x7103c4dd30`, `0x7103c34e14` |
| F+0x30 | u16 비교 그룹(0 = Default 표) | setter `0x7103ae53f0`(대기 버퍼 +0xc0, +0xd4 bit19) | `0x7103af44e8` |

**공통 쌍 필터 [실행]** (`0x7103c4dd30` → `0x7103af44e8`(A,B) → A 마스크 → `0x7103af44e8`(B,A) → B 마스크, 월드+0x18 bit3 = 0 일 때; 원본 4096/4096 정수 일치):
```text
L(x) = F(x)+8 & 63;  S(x) = (F(x)+8 >> 6) & 63
T = (그룹A == 0 || 그룹B == 0) ? Default(표+0x190) : (그룹A == 그룹B ? Same(+0x210) : Other(+0x290))
표비트(A,B) = (T[L(A)] >> (L(B)&31)) & 1
마스크(A,B) = ((F(A)+0x18 >> (L(B)&31)) & 1) & ((F(A)+0x1c >> (S(B)&31)) & 1)
허용 = 표비트(A,B) & 마스크(A,B) & 표비트(B,A) & 마스크(B,A)
```
32비트 가변 shift 는 하위 5비트만 쓴다. 실행 범위는 레이어 0..28, 하위 레이어 0..26이다. 이 표는 값2만 포함하는 **block 배열**이다(7차 §3.5.1). 표비트 외에 양쪽 마스크·형상 행을 검사한 결과가 막는 접촉을 정한다. 월드+0x18 bit3 = 1 이면 월드+0x440 콜백과 이름 표 `0x71034a3a1c`(`Character`, body+0x88 & 0x1c == 4) 제외가 추가된다 [판독, 실행 안 함]. 좁은 단계 `0x7103c51de0`도 같은 6개 검사를 하고, 이어 형상별 검사 `0x7103b02470`을 한다. 형상별 필터 `0x7103c34b7c`는 상대 F+0x08 bit28 이 켜졌을 때 `0x7103ad658c`로 형상 필터 행을 얻는다(일반 `0x7103ad6a70`, 복합 type15 `0x7103ad677c`) [판독].

**shapeTag 행 선택 한 단계 [실행]** (`0x7103ad6a70`; 원본 1024/1024 일치, 잎 결과 태그는 스텁 공급): 형상 type 7..10, 키 ≠ −1, 정보 = 형상+0x28, 내부 메시 = 정보+0x28 이면 Havok 디스패치(내부 메시 type, slot+0xc0)로 잎 결과를 얻고, 결과+0xbf8 의 u16 에서 `index = tag & 0x1fff`; `index < (i32)정보+8` 이면 `정보+0x10` 의 8 B 행을 low/high u32 로 내보내고 1 반환, 아니면 출력하지 않고 0. 정보 객체 writer `0x7103a715b4`는 **[실행]+[판독]**(7차 §3.5.2); 실제 Havok 잎 태그는 8차 `0997078` 원본 실행으로 해소, 월드 코덱은 `WorldShapeTagCodec` vt5755ee8+40=RET **[판독]**(collision_mesh.md §3.4.3). 6차 보강 [데이터]: hknp 형상 +0x28 은 TAG0 형식 표의 `hknpShape::userData`(hkUint64)이다. 즉 정보 객체는 Phive 가 userData 에 단 포인터다.

**형상 필터 행과 공통 쌍 필터의 결합 (6차, 2026-10-03) [실행]+[판독]**

`0x7103c5e244(A, B, keyA, keyB)` — 접촉 매니폴드 수집기 `TtCollectManifoldModifier`(`0x7103c5df04`, `0x7103c5e33c`, 매니폴드 +0xa0/+0xa4 의 형상 키)가 부른다. 같은 꼴이 접촉 수정자 `0x7103c5cda0`(vtable 슬롯, 실패 시 매니폴드 +0x2c |= 0x20)와 `0x7103c584f0`(실패 시 `0x71009b1000`로 접촉 끔)에 인라인돼 있다.
```text
shapeOK(X, keyX, 상대 O) = (F(X)+8 bit28 == 0) ? 1 :                                 // 0x7103c34b7c(L(O), S(O), keyX, X)
      (형상 X+0x28 이 복합(IsA 0x7105553a08) ? (lo, hi) = (형상+0xb8, 형상+0xbc)
       : 행 찾음(0x7103ad658c → 0x7103ad6a70) ? (lo, hi) = 행 : (0xffffffff, 0xffffffff))
      → ((lo >> L(O)) & 1) && ((hi >> S(O)) & 1)
결합(A, B) = ((F(A) bit28 || F(B) bit28) ? shapeOK(B, keyB, A) && shapeOK(A, keyA, B) : 1)
             && 공통 쌍 필터(A, B)                                            // 위 [실행] 식, 인라인 af44e8·마스크 양방향
```
원본 실행 `web/tools/r6_physics_shapefilter_emu.py`: `0x7103c5e244`·`0x7103c34b7c`·`0x7103ad658c`·`0x7103ad6a70`·`0x7103af44e8`를 그대로 실행해 재구현과 **4096/4096 일치**(형상 검사 적용 3458건, 형상 행으로 거부 847건). 스텁: 형상 vt IsA·형식·하위 형상 반환, Havok 잎 디스패치(키별 합성 태그), 공통 표 형 조회, PLT. 결과 `analysis/completion/r6/physics_shapefilter_emu.json`.
- 의미: 지형처럼 bit28 이 켜진 몸체는 **삼각형마다 그 행의 low(Layer)·high(SubLayer) 마스크에 상대 몸체의 레이어·하위 레이어 비트가 있어야** 접촉이 살아남는다. 예: `SplKeepOutPlayer` 행(low 0x62)은 플레이어(레이어 5) 접촉을 통과시키고(막힘), `SplPlayerThrough` 행(low 0x1fffff9e, bit5 = 0)은 플레이어 접촉을 끈다(통과) [실행: 식]+[데이터: 행].
- 질의(쓸어 넘기기) 쪽 [판독, 호출 사슬 미확인]: `0x7103c39158`~`0x7103c39190`이 상대 몸체 F+0x18 에 질의 레이어, F+0x1c 에 질의 하위 레이어가 있고 `0x7103c34b7c(L, S, key, 몸체)`가 1 이면 **접촉 +0x68 |= 2(막는 접촉 비트)**를 켠다. **정정(2026-10-03, 7차): 일반 질의 코드의 이 비트를 탄 출처로 단정했던 문장은 철회한다.** 실제 탄 경로는 기존 r6 combat의 `0x7103c55ed8→0x7103c34e14` [실행]이며 §3.5.2에서 근거를 연결한다.
- 매니폴드 수정자가 Phive 월드에 등록되는 경로와, 좁은 단계 `0x7103c51de0`(공통 6검사 → `0x7103b02470`)과의 역할 분담은 [미확정].

### 3.5.1 원본 BYML 표 변환·몸체 마스크 writer (7차, 2026-10-03) [실행]+[판독]

원본 `PhiveConfig.byml.zs`의 Default/Same/Other 레이어 표(각 29×29)를 `0x7103b16ad8`에 입력하고 `0x7103b1ae90`의 backend 복사까지 실행했다. 셀 `v`는 **allow bit = (v==1 || v==2), block bit = (v==2)**로 서로 다른 u32 배열을 만든다. 표 객체의 allow count/pointer는 +0/+8, block count/pointer는 +0x10/+0x18이다. backend의 allow 배열은 +0x10/+0x90/+0x110, block 배열은 **+0x190/+0x210/+0x290**이다. 따라서 위 공통 검사에서 읽는 표는 값2만 포함하는 block 배열이다. 값1이 접촉/센서의 전체 수명에서 어떻게 소비되는지는 이 실행 범위를 벗어난다.

| 기준 객체 | writer | 필드 전달 | reader·수준 |
|---|---|---|---|
| 강체 생성 desc `D` → F | `0x7103af6088`(내부 factory `0x7103a5fe40`) | D+0x88/0x8c → F+8 layer/sub; D+0xbc → F+0xc; **D+0xc0 → F+0x10, D+0xc4 → F+0x18, D+0xc8 → F+0x1c** | 공통·탄 block 검사 F+0x18/+0x1c; 원본 실행 |
| 캐릭터 몸체 desc `D` → F | `0x7103a85a8c`(같은 factory) | 위와 같은 5필드 | 원본 실행 |
| 강체의 해석된 파라미터 `Q` → D | `0x7103b2ad14` | Q+0x74 → D+0xc4, Q+0x48 → D+0xc8; Q+0x85/0x86 상속 분기 | [판독], raw BYML 객체와 Q는 다름 |
| 캐릭터의 해석된 파라미터 `Q = [[input+0x28]+8]+0x158` → D | `0x7103a25d04` | Q+0x78 → D+0xc4, Q+0x74 → D+0xc8, Q+0x64 → D+0x88 | [판독] |

실행 `r7_physics_table_emu.py`: 원본 BYML reader·표 parser·backend copier의 **87행×2 = 174 u32 배열 값 전부 일치**, PLT 스텁 없음. `r7_physics_mask_emu.py`: 강체512+캐릭터512 = **1024사례/5120필드 일치**, 무작위 u32 마스크와 layer0..28/sub0..26, PLT 스텁 없음. 마스크 이름 문자열을 해석된 Q 필드로 바꾸는 로더는 실행하지 않았다.

정정(2026-10-03, 7차): 이전 F+0x18 writer를 "EnableLayerHitMask 등으로 덮어쓰기 미확정"이라 기록했다. 실제 생성 writer의 전달 오프셋은 위 C4/C8이고, block 검사에서 쓰는 필드와 C0→F+0x10은 별개다. **BYML 이름→숫자 Q 필드까지 연결하지 않은 상태에서 Enable/Blockable 이름을 같은 필드로 간주하지 않는다.** 이전 "표비트가 쌍 허용이며 막음/통과 종류를 정하지 않는다"는 설명은 block 배열의 원본 변환으로 정정한다; 실제 접촉 bit1에는 몸체 마스크와 형상 행도 필요하다.

### 3.5.2 원본 bphsh 정보 부착과 슈터 접촉 (7차 보강)

writer `0x7103a715b4`: bphsh P+0x20(재질 바이트)>>4 와 P+0x24(필터 바이트)>>3 중 작은 N을 사용하고, hknpShape H.userData(+0x28)에 I=O+0x48을 단다. I+8=N, I+0x10=필터 행, I+0x18=N, I+0x20=재질 행, I+0x28=H. 4개 원본 형상 24필드 실행과 사격장 행을 포함한 476사례 탄 block 검증은 [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §3.4.1~2. **정보 writer는 해소**, 16 B 재질 행 reader·실제 Havok 잎 태그 코덱은 7차 당시 미확정이었다. 8차 새근거 §3.5.3으로 정정한다.

탄의 막음 bit1 경로 `0x7103c55ed8→0x7103c34e14→0x7103c34ce8`는 기존 r6 combat 확정 근거([../combat/hitbox.md](../combat/hitbox.md) §3)를 재사용한다. 이번 실제 bphsh 행 연결은 신규지만 공통 탄 경로를 신규 확정 수로 중복 계산하지 않는다. 이전 질의 후보 `0x7103c39158`은 일반 질의 접촉 생성(`0x7103c38b08`)이며 실제 탄 경로 주소로는 정정한다(2026-10-03).

### 3.5.3 실제 query filter·codec·재질 reader (8차, 2026-10-03) [실행]+[판독]

신규 하위 월드 bootstrap `3ac6a20→3c4579c`: 하위 월드+d0 = WorldShapeTagCodec(vt5755ee8), +110 = CollisionFilterBackEnd(Entity vt5756560). queryctx+130의 코덱 decode vt40은 `3c49f00` RET이고, 필터 vt40은 `3c570c4` query dispatcher다. 형상 행 reader는 `3c57d04→3ad6a70`; query 레이어·하위레이어와 해당 low/high를 검사한다. 공통 몸체 쌍은 기존 r6 Default/Same/Other block + 양방향 마스크 + shape override AND 규칙이다.

16 B material reader는 `12ac5e0→12acb38`; 원본 Havok leaf `0997078`의 tag&0x1fff로 I+18 count/I+20 pointer 행을 선택한다. 실제 원본 사격장 3개+교차검증 mesh의 재질 pointer/바이트11505건, leaf5530건, 정점49770 f32필드 불일치0. **기존 미확정 “결합 클래스·코덱·재질 reader”를 해소**하며 침투 보정 솔버·전체 query를 검증한 것으로 확대하지 않는다. 상세 구조·경계·스텁·원본주소는 [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §3.4.3.

### 3.6 플레이어 몸체 하위 레이어 전환 (6차) [실행]+[판독]

`0x71024f5dd8` 안 `0x71024f5fc4`~`0x71024f60f8`이 매 프레임 `[PC+0xe3b0]+0x18` 몸체 집합의 모든 몸체에 setSubLayer(v)(functor `0x7105634078` slot0 `0x71024fc2d0` → `0x7103af394c`)를 걸고, PC+0x58 몸체에는 8(SplPlayerChariotShield)을 건다.
```text
sp = 특수 번호(본체+0x588 쌍이 같으면 +0x658, 다르면 +0x65c; 쌍 없음 0)
v = 액터(본체+8)+0x7b9 ? 12(Enemy) : 7(SplPlayerChariot)
if sp != 0x1a && 액터+0x7b9 == 0:
    if f1(본체+0x7a4) < 1.1920929e-07 || [본체+0xa7c0](PlayerCoopZombie)+0xeec: v = 3 (SplPlayerHuman)
    elif ([본체+0xa880](PlayerDokanWarp)+0x30 − 1) < 2 (부호 없음):          v = 6 (SplPlayerSquid_NoThroughFence)
    else: v = flag ? 5 (SplPlayerSquid_Invisible) : 4 (SplPlayerSquid_Visible)
```
원본 실행 `web/tools/r6_physics_sublayer_emu.py` 4000/4000 일치(스텁: 몸체 집합 순회·setSubLayer 인자 기록). 하위 레이어 번호 이름은 PhiveConfig `SubLayerEntityCollection` 순번 [데이터]. setSubLayer 는 대기 버퍼를 거쳐 다음 월드 명령 처리 `0x7103b07b8c`에서 F+8 bits6..11 에 들어간다 [판독]. flag 출처(본체+0x7a0·+0x789·액터 컴포넌트 상태, `move_full_main.c` 7131~7163행)와 액터+0x7b9 의미는 [미확정].

**비교 그룹(F+0x30) 공급자 [판독]** — 공급자 객체 slot0 이 몸체마다 setter `0x7103ae53f0`을 부른다. 몸체 집합 순회 = `0x71012ec7c0`/`0x71012ec970`.

| 공급자(vtable) | 팀 출처 | 조건 | 그룹 | 쓰는 곳 |
|---|---|---|---|---|
| `0x71012eab48` (`0x7105576df0`) | 액터 = *(공급자+8), 팀 = 액터+0x668 | **현재 그룹이 0 일 때만** | 팀 ∈ {−1, 3} → 0, 그 밖 → 팀+1 | 물리 구성요소 초기화 `0x71012e9914`(호출 `0x7100f745ec`, `0x71013450ac`; 액터 형 검사 통과 시) |
| `0x71012eac80` (`0x7105576e28`) | 팀 = **(공급자+8) | 조건 없음 | 같은 대응 | 플레이어 `0x71024f4ccc`(PlayerCollision): 인자 0 이면 팀 = [[[PC+0xe3a8]+0x108]+8]+0x668, 인자 1 이면 팀 1 고정. 호출: `0x71024b270c`(인자 0), 리스폰 `0x710249cb60`의 `0x710249d7d4`(리스폰 방식 w27 == 5 일 때 인자 1). 대상 = [액터+0x510]+0x18 몸체 집합 |
| `0x71021f2e70` (`0x7105615478`) | 팀 = *(u32*)(공급자+8) | 조건 없음 | 같은 대응 | SighterTarget(`0x71021ef708`~`0x71021ef720`): 팀 = (로컬 플레이어 팀 == 1) ? 0 : 1 → 그룹 1 또는 2, 대상 = [표적+0x1d8] |

정정(2026-10-03, 5차): 보완 문서는 "소형 `0x71012eac80`·`0x71021f2e70`도 같은 매핑"이라고 적었다. 매핑은 같지만 **현재 그룹 0 조건이 없다**(명령 `0x71012eac80`~`0x71012eacac`, `0x71021f2e70`~`0x71021f2e88`). 결과: 플레이어 몸체와 표적 몸체는 서로 다른 0 아닌 그룹 → **Other 표**, 같은 팀 플레이어끼리 → Same 표. 탄은 일반 공급자 경로(현재 그룹 0 일 때만 탄 액터 팀+1)를 탄다고 판독되나, 탄 액터가 형 검사를 통과하는지와 런타임 팀 값은 **[미확정]**.

**플레이어 몸 ↔ 표적(SighterTarget) [데이터]** (5차, `Pack/Actor/SighterTarget.pack.zs`): 표적 본체 강체 `Main` = LayerEntity **SplPlayer**, MotionType **Kinematic**, EnableLayerHitMask `SplPlayerColOthers`, 형상 캡슐 A(0, 1.26, 0.35)–B(0, 0.39, 0) r 0.39, 재질 프리셋 `SplPlayerColOthers`(플레이어 ColOthers 와 같은 프리셋). 피격용 `ColBullet` = SplPlayer 레이어, EnableLayerHitMask `SplPlayerSensor`, 캡슐 A(0, 1.3, 0)–B(0, 0.35, 0) r 0.35, 재질 프리셋 `SplPlayerColBullet`(플레이어 피격 캡슐과 같은 치수, [../combat/hitbox.md](../combat/hitbox.md)). PhiveConfig 레이어 표 값 SplPlayer×SplPlayer 는 Default/Same/Other 모두 **2**이고, 양쪽 마스크(SplPlayerColOthers)가 SplPlayer 비트를 포함한다. 비교 그룹은 플레이어 팀+1 ≠ 표적 팀+1 → Other 표. 따라서 **데이터상 플레이어 ColOthers 와 표적 본체는 다른 팀 플레이어끼리와 같은 조건으로 충돌 후보가 된다**. 7차에서 **표 값2 → backend block 배열은 [실행]**, desc C4/C8 → F+0x18/+0x1c writer도 [실행]으로 해소했다(§3.5.1). 그러나 raw BYML의 Enable/Blockable 이름을 해석된 Q 숫자 필드로 넣는 경로·표적 최종 F 마스크·실제 동적 접촉 솔버는 **[미확정]**이다. 표적을 웹에서 플레이어 벽으로 만들지 여부를 현재 근거만으로 완전 확정하지 않는다. 기존 미확정의 해소 부분과 남은 부분을 구분한 정정(2026-10-03)이다.

### 3.3.2 Body bit11의 실제 native 쌍 거부 의미 (8차, 2026-10-03) **[판독]+[실행]**

새 native Entity filter의 실제 vtable `0x7105756560` 슬롯+0x20는 `0x7103c56bc4`이다. nativeWorld+0x38 배열의 0xc0 B nativeBody에서 +0x98 engine Body를 가져와 **새 `0x7103b19798→0x7103b19308`**을 실행하고 거부된 8 B bodyID 쌍을 목록에서 제거한다. `3b19308`은 기존 pair-group 배제 검사 뒤 F+8 layer와 F+0x30 group으로 table allow row(+0x10 Default/+0x90 Same/+0x110 Other)를 선택한다. 반드시 **table.allow[A.layer][B.layer] AND F_A+0xc의 B.layer 비트 AND F_B+0xc의 A.layer 비트**를 통과해야 한다. F+8 bits16..19가 어느 쪽에서1이면 sublayer 검사를 생략하고, 아니면 F_A+0x10의 B.sub 비트와 F_B+0x10의 A.sub 비트도 모두 필요하다. F+0x18/+0x1c의 blockable 마스크와 다른 검사다.

기존 `0x7103ae4c48(Body, bool)`과 `0x7103b07b8c` 판독을 이 **새 소비자에 연결**하면 bool=1은 body+0x88 bit11을 켜고, staging 적용에서 **F+0xc를0**으로 만들어 native body pair를 거부한다. bool=0은 bit11을 끄고 저장된 Body+0x15c의 허용 마스크를 F+0xc로 복원한다(Body bit27의 전역 마스크 제한은 별도로 적용). 따라서 이 bool은 충돌 허용을 **끄는 방향**이며 nativeBody 제거·shape 반경 축소·motion active flag가 아니다. setter는 pending+0xd0 bit0와 dirty+0xd4 bit19에 대기시킨 뒤 적용한다. 부착된 몸체의 mask 변경은 `0x7103c50020`(새 판독)이 주변 body를 깨우고 nativeWorld vt+0x398 갱신을 요청한다. 부착되지 않은 fixture에서는 이 갱신이 early return하므로 실제 broadphase 갱신 효과를 실행 검증했다고 확대하지 않는다.

`r8_physics_bit11_pair_emu.py`: 원본 setter→전체 staging apply **16,384사례/32,768 state필드**, 실제 nativeFilter `3c56bc4→3b19798→3b19308` **17,571 body 쌍**이 독립 table/mask 계산과 일치, null/자동 매핑/실행 오류0. 원본 r7 PhiveConfig allow row29×3은 기존 확정 데이터를 재사용했고 새 소비자와 새 연결 실행만 이번 근거다. 외부 mutex는 단일 스레드 no-op; synthetic nativeBody engine-pointer와 game Body/Stage/F fixture, 구체적인 원본 CharacterMatterRigidBody VT57468d8의 실제 F getter를 사용했다. 첫 fixture에서 추상 MatterBody VT5749048의 null slots90/98을 선택한 실패는 `physics_bit11_wrong_abstract_vt_failure.json`에 보존하고 구체 VT로 정정했다.

리스폰 reset에서 PlayerCollision+0x48/+0x50을 bool1로 부른다는 기존 근거는 이 native pair 거부를 뜻하고 타이머0에서 bool0은 저장 마스크 복원이다. HP invincible T0 검사 자체는 combat/player_life의 별도 원본 근거를 따른다. **인간/오징어/잠복의 shape·크기·receiver 사용 전환 전체는 이 비트 하나로 해소하지 않는다.**

## 4. 몸체와 한 물리 스텝 [판독]

```
[단계0 그룹3] 게임 슬롯18 메인 계산 → 0x71024f4f7c: ctrl.setMoveVelocity(v·60)  (+ Result+0x1338 = v + 충격 a/3600 + 본체+0x4bc..)
[단계0 그룹6] 월드 갱신 "PreImpl Phase2" (작업 0x7103aca5d8 / 동기 0x7103ac83b4, 월드+0x50 bit4):
   캐릭터마다 0x7103a80560 → 업데이트 컴포넌트 11개(phive_controller.md §3.4) → GameApplyVelocity가 강체 선속도 설정
Havok 스텝(솔버): 위치 적분 + 접촉 해소           ← 내부 [미확정], 재질상 마찰·반발 0
결과 컴포넌트(SplResultPlayer 슬롯7 0x7102c5a3c8): 접촉 목록 → 지지·벽·천장 정보(S) → 이동 상태 전이
[단계1 그룹3] 게임 슬롯19 0x71024abcf0 → 0x71024f7410: S → PC 필드(§7)
```
- 단계·그룹 순서는 **[판독]+[실행: 그래프 간선]**(5차): 플레이어 CalcPriority = Default(그룹3), Phive Entity 월드 = 단계0 그룹6, 슬롯19 = 단계1 그룹3 — [phive_controller.md](phive_controller.md) §6.7. 정정(2026-10-03): 이 블록의 "슬롯18 → 물리 → 슬롯19" 순서는 이전에 구조로 본 것이었고 이제 원본 근거가 있다. 같은 Default 그룹의 다른 액터(다른 플레이어)와의 순서는 정해져 있지 않다.
- 기준점: 컨트롤러 몸체 행렬은 ctrl+0x18 강체 +0xd8(3×4, 이동 성분 +0xe4/+0xf4/+0x104; getPosition = ctrl vt 슬롯26 `0x7103a87114`). 캡슐 바닥은 몸체 원점 −0.6. 기존 결론은 게임 위치↔몸체 원점 오프셋을 **[미확정: 발+0.6 추정]**으로 두었다. **2026-10-03 정정 [실행]**: 리셋 `0x71024f4440`이 몸체 transform 위치를 `(game.x+0, game.y+ColGroundRadius, game.z+0)`로 전달한다(1024/1024 f32 bit match). 일반 요청 반경은 0.6f(`0x71024b7b3c`, 비트 `0x3f19999a`) [판독+데이터]이고 `0x71024fc35c` → setter `0x7103a6a878`이 `r = min(max(요청, 월드+0x21c), 2000)`, NaN/무한이면 1 로 capsule+0xf0 에 쓴다(월드가 없으면 하한 0.05) [판독]. **5차 보강 [판독]**: 월드+0x21c 는 월드 생성자 `0x7103ac71c8`이 설명자+0x80 에서 복사하고(`0x7103ac72a8` ldur x23,[desc,#0x7c] → `0x7103ac73d0` str x23,[world,#0x218]), 물리 시스템 초기화 `0x7103db346c`의 기본 설명자에서 그 값은 0.05(`0x3d4ccccd`, `0x7103db3578`)다. 따라서 기본 설명자를 쓰면 최종 ColGround 반경 = 0.6, 몸체 원점 = 게임 위치 + (0, 0.6f, 0). 초기화 인자 +0x28 덮어쓰기 블록이 실제로 쓰이는지는 **[미확정]**. 피격 바디에는 반경을 더하기 전 transform을 전달한다. 리셋 식(`0x71024f4440` → ctrl vt+0xb8 `0x7103a870c8` → 강체 transform setter `0x7103ae1da8`)은 원본 1024/1024 f32 비트 일치 [실행]. **[미확정]** 평상시 Phive→게임 위치 write-back 전체 검증은 남았다 — 실행 기록 [collision_runtime_completion.md](collision_runtime_completion.md) §10.
- **4.1 평상시 write-back (6차, 2026-10-03) [실행]+[판독]**: 액터 단계1 `0x7100f76f78`(vt+0x2e0)가 물리 구성요소(컴포넌트[10])+0x18 몸체 집합 → `0x7103a13a24` → 주 몸체 `0x7103a102f0(집합,0)` = 캐릭터 몸체(ctrl+0x18, 생성 `0x7103a80a60`, vtable `0x71057468d8`)의 행렬 M(S+0x210 < 1 이면 보간 행렬 S+0x244, 아니면 몸체+0xd8)을 얻고, 액터+0x4e0 functor 를 부른다. 플레이어는 PlayerBehavior 슬롯8 `0x7102456e90`이 functor vtable `0x71056337c0`(slot0 `0x71024d26f8`, this = 본체)을 설치하며, 이것이 **M 회전 = 본체 회전, 본체+0xfa0 == 0 이면 M 이동 −= r·up**(r = ColGround 캡슐+0xf0, up = 본체+0x28/+0x2c/+0x30, fmul 뒤 fsub)으로 바꾼다. 결과가 액터+0x28c..+0x2b8 이고, 슬롯19 `0x7102483134` 첫머리(`0x7102483278`~`0x71024832d8`)가 본체+0x40 = 이전 본체+0x10, **본체+0x10 = 액터+0x28c**, 본체+0x1c.. = 액터 회전(전치)로 복사한다. 따라서 게임 위치 = 몸체 원점 − 0.6·up(발) — 리셋 식(+r)의 역이다. 원본 실행 `web/tools/r6_physics_writeback_emu.py` 1024/1024 비트 일치(`0x7100f76f78`→`0x7100f77730`, `0x7103a13a24`, `0x7103a102f0`, IsA `0x7103a820c4`, `0x71024d26f8`, 슬롯19 구간; 스텁: PLT TLS·guard, 캡슐 IsA). 정정(2026-10-03): 웹 impl 의 "기준점 = 발 + 0.6 [추정]"은 이 [실행]으로 확정된다. 미검증: 몸체 집합 주 칸 0 = 캐릭터 몸체는 판독(`0x7103a08814`~`0x7103a08870`), 본체+0xfa0 의 의미 [미확정].
- 몸체가 솔버를 타는지 [판독]: 캐릭터 몸체는 `0x7103a80a60`이 `0x7103a85a8c`로 모션을 만들어 월드에 넣는 hknp 몸체이고, 컨트롤러는 속도만 넣는다. 위치는 월드 스텝(`0x71009ce484` "TtBuildCollideTasks" → `0x71009cee34`)이 바꾼다. 솔버 내부(반복 수·침투 보정)는 [미확정].
- 서브스텝: 컨트롤러 업데이트는 월드 스텝마다 1회(`0x7103a80560` 호출 2곳 모두 반복 없음). 월드 dt = 1/60(phive_controller.md §6.4) **[판독, 런타임 고정은 추정]**.

### 4.1 native 위치 적분·침투 보정의 원본 식 (8차, 2026-10-03) **[판독]+[실행]**

§4의 과거 "Havok 솔버 위치 적분·접촉 해소 내부 [미확정]"은 [phive_controller.md](phive_controller.md) §6.10.4~5의 새 원본식·whole함수 실행으로 정정한다. 원본 09d4ba8가 native velocity/subgravity에서 packed current와0 baseline을 만들고, 0a15b70→0a181fc가 접촉마다 침투 target/유효질량/순차 normal impulse를 생산·소비한다. 실제 원본 MT에서8normal/7carry(0a4b514)/1finalize(0a4b8c8)다. static한body·kinematic두body·실제두행kernel 및explicit2~4행 순차식까지 독립 bit 일치이며, 인간·오징어의 무회전/지형·표적 마찰0/반발0 데이터는 기존 근거를 재사용한다.

최종 저장 속도는 clipped(current−baseline)이지만 위치용 속도는 `F(F(baseline+F(delta*tau/damp))*F(invSub*damp/tau))`다. native COM double은 `COM+=double(F(COMVelocity*dt))`로 갱신한 뒤09d5b68에서 local COM offset을 빼 f32 몸체 원점(+30)과잔차(+40)를 만든다. 이후3ae6410의 game body pose 되쓰기와 기존0f76f78→3a13a24/3a102f0→24d26f8→Actor+28c→2483134→본체+10 경로로 돌아온다. cap100/200 포함wholeprestep2,048/12,288f32,wholefinalizer2,048/6,144f32+6,144f64,wholebodyorigin1,024/6,144f32 독립 일치. 식·명령/입력 writer·실패 로그는 위 절에 모두 기록했다.

고정 목록 L77(위치 적분+접촉 해소 식)과 L191(침투 보정 속도+반복 수)은 해소한다. L15의 실제 game SplPlayer motion runtime ID/최종 modifier 바인딩, 전체 Lby_Lobby00 메시·경사·계단/오징어 모양의 native 접촉 생성 및 TOI 전체 재생은 미확정 유지한다. 이번 synthetic 캡슐fixture 수치를 사격장 상수로 대입하지 않는다. initial native world gravity−9.81 fixture는 실제 Phive−9.8·게임 자체중력과 구분하며 모션속성 custom callback 없는 수학시험이다.

### 4.2 실제 캐릭터 MotionProperties 선택과 native 동적 실행 (9차, 2026-10-03) **[판독]+[실행]**

**정정 이력:** §1의 이전 “MotionProperty SplPlayer, 최대 선속도100”은 원본 BYML의 데이터 행만 읽은 결론이었다. `CharacterMatterRigidBodyParam`의 MotionProperty 문자열은 SplPlayer이며 PhiveConfig 데이터 행의 최대값100도 맞지만, **캐릭터 native 생성 경로가 그 행을 사용하지 않는다.** 9차 원본 생성자/등록자 판독과 실행으로 실제 특수13 선택을 확인해 §1을 정정한다. r8 solver 시험에서 명시했던 cap100/200은 합성 fixture 한계로 보존한다. r8의 독립 solver 수식은 재사용하며 이번에 새로 확인한 것은 실제 게임 캐릭터의 속성 선택·등록·동적 소비 연결이다.

생성 수명: World의 MotionProperties 관리자 `0x7103ada00c`가 16개의 wrapper(각0x98B)를 만들며 +170=count16/+178=pointer array를 소유한다. `0x7103ade180(P,index,manager,heap)`는 0..12에서 PhiveConfig의 MotionPropertiesCollection 행을 읽고, **13/14/15는 원본 literal**을 사용한다. 캐릭터 생성의 기존 `3a80a60→3a85a8c`는 **3c4e8c4의 첫 인자 kind1**을 전달한다. 원본 `3c4eb7c..3c4ebd4`는 World+0xc8의 관리자에서 `index=(kind==1 ? 13 : desc+84)`를 선택해 P+40 backend의 +8 native u16 ID를 **BodyCinfo+88**에 저장한다. 범위 밖 index는 pointer array 첫 행으로 fallback하며 World 번호가0이 아니면 기본 World0을 선택한다. 여기서 Root+0xc8과 World+0xc8을 혼동하지 않는다.

| wrapper P | 의미 | 특수13 | native MotionProperties Cinfo |
|---|---|---:|---|
| +8 / 대체+20 | LinearDamping | 0 | +18 |
| +c / 대체+24 | AngularDamping | 0 | +1c |
| +10 / 대체+28 | MaxLinearSpeed | 20000 | +10 |
| +14 / 대체+2c | MaxAngularSpeed | 10000 | +14 |
| +18 / 대체+30 | GravityScale | 0 | +8 |
| +1c / 대체+34 | TimeScale | 1 | +c(1일 때 native 기본 유지) |
| +38 | 대체 필드 선택 bit0/1/2/3/4/5 | 생성 시0 | 등록 `3c5291c` |
| +3c / +40 / +48 / +90 | index / backend / owner / world index | 13 / 실제 backend / 관리자 / 0 | backend+8가 native ID |

특수15는13과 같은 값이고 특수14만 선/각 감쇠10000이다. 숫자13/14/15에 데이터에 없는 원본 클래스 이름을 붙이지 않는다. Native 등록은 **새 `3c5291c→0a67a38`**이고 wrapper/backend ID 자체를 상수로 가정하지 않는다. Native World 생성 기본 library 용량16에는 이미 builtin5행이 있다. 게임 bootstrap의 기존 **3c4579c**는 World+8b0 library에 **새0a67414(bodyManager+48 count+16)**를 호출해 등록 용량을 확장한다. fixture에서 이 원본 확장을 실제 실행한 용량32의 등록 순서상 특수13 native ID가17이었으며 **17은 게임 상수가 아니다**.

새 전체 생성/등록 시험 `r9_physics_motion_property_emu.py`: 실제 PhiveConfig13행을 새로 판독한 원본 parser row(32B) 레이아웃으로 입력했다. **원본3ade180 전체16사례/192 f32필드**, 실제 native library의 GravityScale/TimeScale/최대속도/감쇠 **96 f32필드**가 독립 기대값과 비트 일치한다. 원본 native library·등록·속성 산술은 스텁하지 않았다. 별도의 원본 binder 명령 블록 **320사례**(kind4종,world4종,선언index20종)에서 native ID 저장이 독립 정수 선택식과 전부 일치했다. 전체3c4e8c4 생성 시험과 이 부분 블록 시험은 아래에서 구분한다.

새 `r9_physics_actual13_dynamic_emu.py`는 **원본 전체3c4e8c4**를 실행했다. 실제 Capsule VT5745788의 getter3a6acbc→실제 backend3c243dc/3c27858→native09c78f0→massdistribution/질량100/관성 배율0 적용→AddBodies→원본 MT collide/solve로 연결했다. 두 캐릭터의 원본 BodyCinfo+88이 특수13의 실제 등록 ID17을 저장했다. 합성 캡슐 바닥 접촉 body와 멀리 떨어진 자유 body를 함께10프레임 실행하여 normal kernel80회, finalize12회, body-origin20회가 정상 반환했다. 이것은 native 접촉 경로의 **실행 관찰**이며 새 독립 접촉식 대조로 세지 않는다(r8 §4.1의 독립식 근거 재사용).

자유 body 입력 선속도(300,0,0)는 **100으로 잘리지 않고300을 유지**했고, native GravityScale0으로 Y속도도0을 유지했다. 각 프레임 COM은 `doubleCOM.x += double(f32(300f * f32(1/60)))`, Y/Z 유지라는 독립식과10프레임의 COM3f64+속도3f32, **총60필드 비트 일치**였다. raw L15의 “동적몸체/게임속도전달/native적분·접촉 계산”은 r8의 원본식과 이 새 live-property 동적 연결로 해소한다. 전체 사격장 지형·TOI·모든 특수 modifier를 이 질문의 해소로 확정하지 않는다.

실행 경계: 실제 게임 스레드/씬은 실행하지 않았다. Root/World/관리자와 기하 위치·외부 WB mutex는 fixture(단일스레드 원본 RET 콜백)이며, optional desc+a0 modifier를false로 둔 시험이다. 형상 getter/native 생성·속성 등록·질량 계산·solver 산술·contact kernel은 원본이다. 널 호출/자동 매핑/실행 오류0; nnOS mutex/TLS/tick·메모리 할당은 호스트 환경 처리다. optional modifier의 실제 game binding과 전체 사격장 mesh/경사/계단/TOI는 §11의 미확정 경계로 유지한다.

## 5. 이동 상태 전이 [판독]

결과 컴포넌트 끝(기본 ApplyResult `0x7103a88248`, SplResultPlayer `0x7102c5a3c8` 2472행 근처 같은 패턴):
```
next = 상태[M+0x40].vt[0x30] (&S+0x20)
if next != M+0x40: M+0x44 = 이전; 이전.vt[0x28] (퇴장); M+0x40 = next; (InAir→OnGround면 M+0x48 = 1)
GameOnGround.vt[0x30] 0x71012aa648: return (S+0x20 == 0) | S+0xf4      // 1 = InAir
GameInAir.vt[0x30]    0x71012aa108: return (S+0x20 == 1 && S+0xf4 == 0) ? 0 : 1
```
- **S+0xf4 (공중 강제)** = Result 시작에서 `Result+0x1358 > 0 ‖ [0x71024f4104(PC)]+0x30 > 0 ‖ (특수 0x1c SuperLanding && [본체+0xa7f0]+0x40 == 3) ‖ 본체+0x746`. 본체+0x746은 점프 발사 계열(`0x7102641ec4`, `0x71024a8000` 직후)이 쓴다. Result+0x1358·`0x71024f4104` 대상의 writer는 [미확정].
- 게임 쪽 강제: 메인 계산이 수직 속도 > 0.001이면 현재 상태가 InAir가 아닐 때 퇴장 호출 후 M+0x40 = 1, [PC+0xe350]+0x4d = 1(`move_full_main.c` 4938~4957행). 다른 곳(카메라·생명·기믹·게이지 코드)도 M+0x40을 직접 바꾼다(`gauge_batch1.c`, `life/batch1.c` 등 — 각 영역 문서).
- 6차 보강 [판독]: Result+0x1358 = 본체+0x73c(게임 수직 속도) — 메인 계산 `0x710247e944`가 매 프레임 기록(인자 x6 = 본체+0x72c 의 +0x10). `0x71024f4104(PC)`는 컴포넌트 목록에서 "CharacterUpdateJump"(SplJump)를 찾고 그 +0x30 = SplJump 쿨다운. 즉 공중 강제 = 수직 속도 > 0 ‖ SplJump 쿨다운 > 0 ‖ SuperLanding 단계 3 ‖ 본체+0x746. 같은 곳에서 Result+0x28 = 본체+0x744 && 본체+0x73c > 0.001.
- Free([2])로의 전이는 외부 강제(VehicleSpectacle 등)만 확인. 6차 [판독]: Free 상태(팩토리 `0x7103a8367c` 이름 표 `0x7105746ab8` 2번 → 생성 `0x7103a848ac`, vtable `0x7105746b48`, +8 = 2)의 vt+0x30 `0x7103a84cf4`는 **항상 2** → Free 는 스스로 OnGround/InAir 로 바뀌지 않는다. 갱신 vt+0x20 = `0x7103a849b8`(내부 식 미판독).

## 6. 접지 판정 SplResultPlayer `0x7102c5a3c8` [판독-부분]

2,500줄 함수입니다. 아래는 웹 재현에 필요한 판정 규칙만 뽑은 것입니다(전체 분기 중 탈것·특수 경로 일부 생략).

### 6.1 출력 (기준 객체 S = ctrl+0x20)
| S 오프셋 | 의미 |
|---|---|
| +0x20 | 지지 상태(1 = 지지). 시작에 0 |
| +0x24 | 지지면 속성값(접촉 상대 바디 +0x190, 캐시) |
| +0x28..+0x30 | 지지 법선(가중 평균). 법선 y < −0.2571이면 기본값 유지 |
| +0x34..+0x3c | 지지 법선(얼굴 법선 `0x7103c4988c`로 보정: 평균과 0.65 미만으로 다르면 얼굴 법선) |
| +0x40..+0x48 | 지지 접점 |
| +0x58 | 지지 접촉 거리 − Result+0x1c |
| +0x8c..+0x94 | 스텝 뒤 강체 속도(유닛/초) |
| +0x98..+0xa4 | 지지 접촉의 재질표 행(재질 번호, u64 UserShapeTag) |
| +0xb4 / +0xc0 | 측면(벽) 접촉 평균 법선 / 평균 접점, +0xf5 = 있음, +0xf0 bit2 |
| +0xcc | 지지 상대 레이어(필터 & 0x3f) |
| +0xf4 | 공중 강제(§5) |
| +0xf7 | 지지 상대 바디 종류 == 2 |

### 6.2 후보 접촉
1. 막는 접촉(+0x68 bit1)이고 상대 레이어 == **3(Ground)** 인 것만.
2. 거리 d(+0x30)·비율 f(+0x60)·종류(+0x64)로 등급: `d < 0.02 ‖ f > 0 ‖ 종류 4 → 0`, `d ≤ 0.2 && 종류 2 → 1`, `종류 5 → 2`, 그 밖 버림.
3. UserShapeTag bit3(PhiveUnridable)이면 얼굴 법선과 중력 사이 각이 S+0x190(75°)보다 작을 때 버림.
4. 분류 `0x7102c5dd20(Result, pass, …)` → 0 버림 / 1 바닥 후보 / 2 벽 후보(pass 1에서는 반대). 주요 조건:
   - 접점이 몸체 중심 기준 법선 앞쪽이면 버림.
   - **InAir이고 n.y ≥ 0.6414이면 `n·v > 0.001`일 때 버림**(v = Result+0x1338, 점프 상승 중).
   - OnGround이고 이전 지지 법선(Result+0x132c)과 0.7071 미만으로 다르면, `n·v > 0.001`이고 v 방향과 [0x71058f0ba0]° 안이면 버림.
   - 법선–중력 각 θ(atan2) ≥ S+0x190이고 수평 각 ≥ 50°(0.87266 rad)면 버림.
   - θ ≥ 104.9°(1.83085 rad): 천장 쪽. Result+0x28면 150° 미만 버림, 아니면 129.9°(2.26718 rad) 미만이고 SquidGuard 태그가 없으면 버림, 나머지 벽.
   - 접점 높이 `(p − 중심)·(−g) ≤ 0.2 − R`(R = Result+0x16b8 = ColGround 반경 0.6) → **계단 오르기 높이 0.2**. 이 안쪽 접촉은 바닥 쪽으로 분류(추가 레이 `0x7102c5e6a8` 판정, 각도 acos((R−0.2)/R)).
   - θ < S+0x190(75°)면 바닥. 그 밖 경사 조건: 이전 지지 법선 y < 0.6414이면 40°(0.6981) 이하 바닥, 30°(0.5236) 초과 벽, n.y < cos 85°(0.0872)이면 벽.
5. 같은 바디·0.05 이내·법선 내적 > 0.99인 후보는 합친다(더 작은 f, 같으면 더 작은 d).
6. 바닥 후보를 d(×1000 비교) → f 순으로 정렬, 최선 등급 이하 후보를 |n·g| 가중으로 법선 평균.
7. 상대 바디가 움직이면(`(v_self − v_point)·n > 5`이고 `v_point·g < −5`) 지지 취소.
8. 통과하면 S+0x20 = 1, 법선·접점·재질 기록.

### 6.3 기본 ApplyResult `0x7103a887fc`(다른 캐릭터) [판독]
플레이어는 쓰지 않습니다. 접점 높이 h = (p − (pos + up·body+0x358))·up를 body+0x354와 비교해 바닥/위쪽 목록으로 나누고, 평균 법선·up ≥ S+0x194(cos 75°)면 지지. body+0x354/+0x358/+0x35c는 형상에서 계산(`0x7103a80a60`): 가장 낮은 캡슐의 반경 / min(0, 캡슐 바닥) / 최대 반경 → SplPlayer_cct 값이면 0.39 / −0.6 / 0.6 **[판독식, 값은 재구현 계산]**.

### 6.4 UserShapeTag 플래그 (기준 객체: SplResultPlayer) [판독]+[데이터]
| 태그 비트(이름) | 결과 |
|---|---|
| 3 PhiveUnridable | 경사 75° 미만 면을 지지 후보에서 제외(기본 ApplyResult는 지지 0) |
| 19 SquidGuard / 20 Slide | 지지 법선 y ∈ [0.6414, 1)이면 +0x16bc = 법선, +0x16c8 = 1 → PC+0xc4/+0xd2 |
| 21 PlayerDead | +0x1744 |
| 25 Fence | +0x1745 |
| 26 Ice | +0x1746 |
| 30 KebaInk | 바닥: +0x1747(+0x172c 접점, +0x1738 법선), 벽: +0x1748 |
| 22 PlayerUnsafe | +0x1749 |
| 31 Sponge | +0x174a(→ +0x174b) |

player_state.md §7.3의 `[PC+0xe378]+0x1748 == 0`(천장 조건)은 "KebaInk 벽 접촉 없음"입니다.

## 7. PC로 옮기는 값 `0x71024f7410` (슬롯19 첫머리) [판독]

| PC | 값 |
|---|---|
| +0xd0 / +0xd1 | 현재 상태 OnGround && S+0x20==1 / 직전 값 |
| +0xec | S+0xf5(측면 접촉 있음) |
| +0x108 | +0xd0 && S+0x38 ≥ [0x71058bc7a0] |
| +0x109 | S+0x20 == 1 |
| +0xa0 / +0xac | 지지 접점 S+0x40 / 지지 법선 S+0x34 (+0xd0일 때) |
| +0xd4 / +0xe0 | 벽 접점 S+0xc0 / 벽 법선 S+0xb4 (+0xec일 때) |
| +0xb8 | Result+0x13f8(지지 중) 또는 +0x1404(상승 중 등) |
| +0xc4 / +0xd2 / +0xd3 | Result+0x16bc / +0x16c8 / +0x16c9 |
| +0xd088 | 탐색 구 중심 = 본체+0x10 + 0.6·up |

## 8. 웹 포팅

| 모듈(웹 권장 이름) | 원본 |
|---|---|
| `PlayerShape` — t로 ColGround/ColOthers 캡슐 갱신(0.2 히스테리시스) | `0x71024f5dd8` |
| `CharacterBody` — 속도 v·60을 받아 1/60초 이동, 지형과 **마찰 0 미끄럼 접촉**(침투 해소 + 법선 속도 제거) | Havok 솔버(대체 구현) |
| `SupportDetector` — §6.2 규칙으로 S 생성 | `0x7102c5a3c8`, `0x7102c5dd20` |
| `MoveStateMachine` — §5 전이 | `0x71012aa648`, `0x71012aa108` |

```ts
const MAX_SLOPE = Math.fround(75 * Math.PI / 180), STEP = 0.2, FLOOR_NY = Math.fround(0.64144969);
function nextMoveState(cur: 0|1|2, s: Support): 0|1|2 {      // 0 OnGround, 1 InAir
  if (cur === 0) return (s.supported && !s.forceAir) ? 0 : 1;
  if (cur === 1) return (s.supported && !s.forceAir) ? 0 : 1;
  return cur;                                                // Free: 외부 강제만
}
function ignoreFloorWhileRising(cur: number, n: Vec3, v: Vec3) {  // 점프 프레임 공중 유지
  return cur === 1 && n.y >= FLOOR_NY && dot(n, v) > 0.001;
}
```
동등성: Havok 솔버를 그대로 재현할 수 없으므로 웹은 "스윕 + 미끄럼(마찰 0)"으로 대체하고, 지지 판정·상태 전이·계단 높이 0.2·경사 75°/50.1°/104.9° 상수는 원본 값을 쓴다. 비트 일치는 기대하지 말고 착지 프레임·경사 경계에서 원본 영상과 대조할 것.

## 9. 미확정과 다음에 볼 곳

| 항목 | 상태 | 다음 근거 |
|---|---|---|
| Havok 솔버의 접촉 해소(침투 보정 속도, 반복 수) | 미확정 | hknp 솔버는 라이브러리 코드. 웹은 대체 구현 |
| 게임 위치(본체+0x10) ↔ 몸체 원점 오프셋 | 리셋 식 해소 [실행]: 월드 Y + 최종 반경, 1024/1024 비트 일치. 최종 반경 = max(0.6, 월드+0x21c), 실행 중 월드+0x21c = 0.01(게임 모듈 설정이 덮어씀, [실행] phive_controller.md 정정 참고. 기본 설명자 값은 0.05) → 0.6 [판독] (5차) | 평상시 write-back(Phive 결과 → 본체+0x10) writer: GameFrameSetup/SplResultPlayer 위치 전달, ctrl vt 슬롯26 `0x7103a87114` 를 부르는 본체+0x10 writer. 5차 단서 [판독-부분]: 액터 단계1 vt+0x2e0 `0x7100f76f78` 앞부분이 추적 강체 transform 을 `0x71012ecf60`/`0x7103a13a24`/vt+0xd8 로 읽어 액터 행렬(액터+0x28c.., `param_1[0xa3..0xae]`)에 쓴 뒤 행동 슬롯19 를 부른다 — 플레이어 본체+0x10 과의 관계·반경 오프셋 적용 여부는 미판독. 물리 시스템 초기화 인자 +0x28 덮어쓰기 블록 공급자 |
| 프레임 내 접촉 반응 시퀀서 실행 시점·액터 종류 간 순서 | **해소 [판독]+[실행: 그래프 간선]**(5차) | [phive_controller.md](phive_controller.md) §6.7. 정정(2026-10-03): 이전 기록 "미확정(월드 단계 이름·함수만 판독)"을 대체. 남은 것: 단계2·3 액터 노드 생성자, 작업자 ≥ 2 묶음 분기 실행 |
| 충돌 필터 결합식·shapeTag 디코드 클래스(질의 문맥 +0x130 vt+0x40) | 공통 결합식 [실행], 행 선택 한 단계 [실행], 비교 그룹 공급자 3종 [판독] (§3.5). 형상별 필터 행이 공통 결과와 어떻게 결합되는지·정보 객체 writer·코덱 클래스 [미확정] | `0x7103c34b7c` 이후 `0x7103b02470` 의 행 사용 식, 형상+0x28 정보 객체 writer(bphsh 로더 `0x7103a221cc` 이후) |
| 용접 비트(interiorPrimitiveBitField) | 미확정(5차에서도 접촉 생성 쪽 미판독) | 좁은 단계 처리기 표 `0x7105756468`, 메시 접촉 생성의 섹션 +0x18 읽기(캐스트 경로 `0x71009372cc`/`0x7100936ee8`에는 없음) |
| Free 상태 vt+0x30, Result+0x1358 writer, `0x71024f4104` 대상 | 미확정 | 이동 상태 열거 "OnGround, InAir, Free"는 문자열만 확인. Free 상태 클래스 vtable 은 팩토리 `0x7103a8367c` 의 이름 표에서 찾을 것 |
| 오징어 하위 레이어 전환(SplPlayerSquid_* 런타임 설정) | 미확정 | 5차 시도: PlayerCollision 범위(0x71024f0000~0x7102500000)가 부르는 강체 함수는 `0x7103ae4c48`(bit11)·`0x7103ae1da8`·`0x7103ae2890`·`0x7103ae24a4`·`0x7103ae442c`·`0x7103ae2af8`·`0x7103ae0fe0`·`0x7103ae0f08` 뿐이며 필터 +8 bits 6..11 쓰기는 없음. 다음: 메인 계산 `0x7102475a54` 의 필터 객체 직접 쓰기, 탄 래퍼 slot22~25 와 같은 꼴의 setter |

**6차 갱신(2026-10-03)** — 위 표의 상태 변경(지우지 않고 덧붙임):

| 항목 | 6차 상태 | 다음 근거 |
|---|---|---|
| 게임 위치(본체+0x10) ↔ 몸체 원점 | **해소 [실행]+[판독]**: 평상시 본체+0x10 = 몸체 원점 − r·up(§4.1, 1024/1024) | 본체+0xfa0 의미 |
| 충돌 필터 결합식 | 형상 행 결합 **해소 [실행]** 4096/4096(§3.5). bit28 setter·F 생성 writer [판독] | 정보 객체(userData) writer, 코덱 클래스, 수정자 등록 경로 |
| 오징어 하위 레이어 전환 | **해소 [실행]** 4000/4000(§3.6) | flag·액터+0x7b9 의미 |
| Free vt+0x30, Result+0x1358, `0x71024f4104` | **해소 [판독]**(§5) | Free 갱신식 `0x7103a849b8` |
| t 출처 | **해소 [판독]**(§3.3) | |
| Havok 솔버 접촉 해소 | 미확정. 캐릭터 몸체가 월드 스텝을 탄다는 것만 [판독] (§4.1) | `0x71009cee34` 내부 |
| 용접 비트 | 미확정(6차 미착수) | `0x7105756468` 처리기 |

## 10. 검증 코드·실행 결과·기대값 (7차)

| 실행 도구 | 원본 실행 범위 | 결과 | 스텁·미검증 |
|---|---|---|---|
| `web/tools/r7_physics_table_emu.py` | 3b16ad8, 3b1ae90, 원본 BYML reader | 174/174 u32, 불일치0 | 할당·문자열 intern(동일 문자열), PLT 없음. mask 이름 로더·전체 센서 수명 미검증 |
| `web/tools/r7_physics_mask_emu.py` | 3a5fe40, 3af6088, 3a85a8c | 1024/1024 사례, 5120/5120필드 | 할당·형상 구성 인터페이스·표 타입·backend 강체 생성 반환, PLT 없음. 이름→Q 숫자·표적 솔버 미검증 |
| `web/tools/r7_physics_mesh_emu.py` | 실제 원본 bphsh 행 부착 + 기존 탄 block 경로 | 24/24필드, 476/476 접촉 bit1 | 상세 스텁·기대값은 collision_mesh.md §10. 실제 기하/TOI 미검증 |

결과: `analysis/completion/r7/physics_{table,mask,mesh}_emu.json`, 디컴파일 `analysis/decomp/r7_physics/{filter_begin,filter_load,mesh_attach,bullet_mesh_filter}.c`. 실제 명령 및 실패는 `analysis/completion/r7/physics_commands.md`. 함수 입력·출력 검증을 표적과 플레이어의 전체 동작 검증으로 확대하지 않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거 (7차)

| 항목 | 해소와 남은 범위 | 다음 근거 |
|---|---|---|
| 표적이 플레이어를 실제로 막는지 | 값2 block 변환과 D→F writer는 해소. raw 파라미터 마스크 이름→Q 숫자·Main 최종 F·전체 솔버는 미확정. `param_reflect.py` Blockable 검색 결과는 탄 parameter visitor여서 캐릭터/표적의 증거로 쓰지 않음 | `0x7103b2ad14`가 읽는 Q+0x74/+0x48 writer, `0x7103a25d04` Q+0x78/+0x74 writer; raw class creator `0x7103bb5c5c`(RigidBodyEntityParam)·`0x7103b7fbac`(CharacterMatterRigidBodyParam)의 방문/해석 경로 |
| shapeTag 코덱·재질 행 reader | userData writer와 filter 행 결합은 해소. shapeTag로 16 B 재질을 복사하는 reader·코덱 클래스 미확정 | collision_mesh.md §11 |
| 솔버·용접 | 6차 상태 유지. 7차 실행은 필터와 배열 부착만 | Havok `0x71009cec84`/`0x71009cee34`, 처리기 `0x7105756468` |
| 기존 나머지 미확정 | §9의 r6 상태·다음 주소 유지. 원본 벽 지지 전체 실행, Free 갱신식·flag 이름을 이번 실행으로 해소하지 않음 | 기존 해당 절 |

정정 이력: 5차 F+0x18/+0x1c writer 미확정과 "EnableLayerHitMask 등" 추정은 §3.5.1로 구체화했다. 6차 userData writer 미확정은 §3.5.2로 해소했고, 일반 질의 3c39158을 탄 막음 출처로 적었던 내용은 기존 r6 combat의 실제 경로로 바로잡았다. 수정일 2026-10-03. §9의 이전 표는 당시 조사 기록으로 보존한다.

다음 물리 최우선은 **실제 사격장 접지·경사·계단의 한 프레임 완전 경로**다. 기존에 확정한 필터·dt·중력·write-back을 다시 실행해 완료 수를 늘리는 작업으로 대체하지 않는다.

```text
Player 슬롯18 속도 → 캐릭터 갱신 0x7103a80560
 → 실제 지형/플레이어 캡슐의 Havok 충돌 0x71009ce484, 스텝 0x71009cee34(내부 아직 미확정)
 → 원본 접촉 목록(거리·TOI·접점·법선·재질·block bit1)
 → SplResultPlayer 0x7102c5a3c8
 → 바닥/벽 분류 0x7102c5dd20, 계단 추가 질의 0x7102c5e6a8
 → S+0x20/법선/접점 + OnGround/InAir 전이
 → 슬롯19 0x71024f7410의 지지 값 + 0x7102483134의 실제 위치
```

**[미확정]**: 이 연결에서 실제 지형 캡슐 접촉을 만드는 좁은 단계·침투 해소와, 2,500줄 SplResultPlayer의 범위 내 모든 분기 실행은 아직 없다. 이번 태그 공급 스텁으로는 착지 프레임·계단 실제 이동량·경사 미끄러짐을 증명할 수 없다. 다음 입력은 Lby_Lobby00/Fld_VSLobby의 실제 지형과 원본 ColGround/ColOthers, 평지 착지·0.2 계단 경계·75° 경사 경계·오징어 벽 접지다. 기대값은 원본 완전 경로에서 S/상태/위치의 비트를 기록해 재구현과 대조해야 하며, 임의 접촉을 주는 합성 함수 테스트가 성공해도 이 항목을 완료로 올리지 않는다. 먼저 `0x71009cec84`/`0x71009cee34`의 접촉 출력 연결과 `0x7102c5e6a8`의 실제 질의 문맥을 판독한다. 지원/경사 식의 기존 [판독]과 위 완전 경로 [미확정]은 구분한다.

8차 §10 보강(2026-10-03): `web/tools/r8_physics_material_leaf_emu.py`와 `analysis/completion/r8/physics_material_leaf_emu.json` 신규 원본 실행, PLT 미구현0; wrapper getter만 합성. `r8/physics_commands.md`에 성공·실패 명령 기록.

8차 §11 정정: 위 코덱·재질 reader의 과거 미확정 행은 collision_mesh.md §3.4.3의 신규 근거로 해소. 실제 침투 해소·TOI·leaf flags0x20의 용접 소비는 남음; `09af088/09cec84`와 leaf flags reader를 계속 추적한다.

2026-10-03 8차 추가 정정(§11): 기존 “용접 비트(interiorPrimitiveBitField)” 명명은 원본IS_INTERIOR_TRIANGLE=0x20로 정정. 파일primitivebit→실제leaf.flags0x20→narrowphase a5b798/a5d6f4의ALLOW_INTERIOR_TRIANGLE_COLLISIONS pairflag0x8 유지/해제→b230e4 또는 일반generator 분기를 확인했다. 원본gate20,000건불일치0 [데이터]+[판독]+[실행]; [collision_mesh.md §3.3.1](../gimmick/collision_mesh.md). 전체용접modifier/솔버를 이 gate 실행으로 확정하지 않는다.

8차 §11 보강(2026-10-03): 보통 무회전 플레이어의 solver 위치 적분·침투 보정·반복 수 미확정(L77/L191)은 §4.1/phive§6.10.4~5로 해소. native 접촉 입력에서 결과 pose/velocity가 Phive로 돌아오는 수식 경계가 확정됐으며, geometry의 모든 접촉 생성/TOI 및runtime motion ID/전체modifier 연결은 별도 L15/TOI질문으로 남긴다. 웹 구현은 침투 target을상수depth비례로치환하지않고 current/baseline및실효COM속도를분리해야한다.

8차 원점 되쓰기 주소 정정(2026-10-03): §4.1초안의3a83d98→본체10표현은기존r6 Actor/functor주소대조로철회했으며본문의실제0f76f78/24d26f8/2483134사슬을따른다.

9차 §10 추가(2026-10-03): 새 `web/tools/r9_physics_motion_property_emu.py`, `r9_physics_actual13_dynamic_emu.py`; 결과 `analysis/completion/r9/physics_motion_property_emu.json` 및 `physics_actual13_dynamic_emu.json`. 생성192+native96 f32/binder320 ID/자유동적60필드 불일치0, contact10프레임 정상 관찰. 원본 새 디컴파일은 `analysis/decomp/r9_physics/motion_{config,library_bind,property_ctor,native_register,library_native,library_grow}.c`. 명령 성공·실패는 `analysis/completion/r9/physics_commands.md`.

9차 §11 정정: L15의 native motion ID/선택 속성은 §4.2로 해소했다. 앞선8차의 cap100/200은 fixture였고 actualCharacter용 특수13 cap20000/중력0/감쇠0와 구분한다. Native ID17을 상수로 넣지 않는다. 실제 전체 Lby_Lobby00 지형·TOI4handler의 좁은 질의식, optional body modifier3c51de0 actual binding/내용과 모든접지분기 실행은 여전히 미확정이다. 다음 주소: 3c52d30/5368c/54140/54de4→0947aec→0aec920/0aefdc0, Bodydesc+a0 생산자3a80a60/3a82a88/3a0b318.
