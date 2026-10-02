# 플레이어 캐릭터 컨트롤러 — 형상·충돌 필터·접지 판정·이동 상태 전이

Phive 캐릭터 컨트롤러가 플레이어 캡슐을 어떻게 만들고, 물리 스텝 뒤 어떤 접촉을 "바닥"으로 인정해 OnGround/InAir를 바꾸는지 정리합니다. 속도 전달·중력·컴포넌트 순서는 [phive_controller.md](phive_controller.md), 게임 쪽 접촉 정리(벽·착지·천장)는 [../player/player_state.md](../player/player_state.md) §7.3입니다. 작업 지침: [../../분석.txt](../../분석.txt).

확정 수준: **[실행]** / **[판독]** / **[데이터]** / **[추정]** / **[미확정]**. 근거는 명령 판독과 데이터가 중심이다. 원본 실행으로 확인한 것은 bss 상수(정적 초기화 에뮬), 공통 쌍 필터(4096건)·shapeTag 행 선택(1024건)·리셋 몸체 원점(1024건)이다(§3.5, §4; 실행 기록은 [collision_runtime_completion.md](collision_runtime_completion.md) §10). Havok 솔버와 접지 판정 함수는 원본으로 실행하지 않았다.

상태: 4차(phys4) 1차 작성, 2026-10-03 충돌 보완·5차(r5) 반영(§3.5 필터·그룹, §4 몸체 원점·프레임 순서). 6차(r6, 2026-10-03): 평상시 Phive → 본체+0x10 write-back 원본 실행(§4.1), 형상 필터 행 결합식 원본 실행(§3.5), 하위 레이어 전환 원본 실행(§3.6), 오징어 비율 t 출처(§3.3), 공중 강제 S+0xf4 의 두 항·Free 상태(§5) 판독. 웹 구현 없음. 디컴파일 `analysis/decomp/phys4/`(p4_world_ctrl.c, p4_support.c, p4_resultplayer.c, p4_pcupdate.c, p4_shape.c, p4_body.c, p4_phases.c, p4_seq.c).

---

## 1. 요약

| 질문 | 결론 | 수준 |
|---|---|---|
| 몸체 종류 | hknp **동적 강체**(질량 100, 관성 텐서 배율 0 = 회전 안 함, MotionProperty SplPlayer: 최대 선속도 100 유닛/초, 감쇠 0). 게임이 매 프레임 속도를 넣고(GameApplyVelocity → setLinearVelocity `0x7103ae2890`가 월드 모션 +0x44에 기록), **위치 적분·접촉 해소는 Havok 솔버**가 한다 | 데이터·속도 경로 [판독], 솔버 내부 [미확정] |
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

### 3.4 충돌 필터 데이터 [데이터]
| 형상 | 재질 프리셋 | LayerHitMaskEntity → 맞는 레이어 | 기타 |
|---|---|---|---|
| ColGround | SplPlayerColGround | GroundOnly(26) → CustomReceiver, Ground, Water | |
| ColOthers | SplPlayerColOthers | SplPlayerColOthers → CustomReceiver, GameCustomReceiver, SplPlayer, SplPlayerChariotShield, SplInkShield, SplInkFilm, SplObject, MissionEnemy, SplCoopEnemy, SplItem, SplWallaObj | UserShapeTagMask GameUnridable, ActivateWallaObj |
| 강체 | LayerEntity SplPlayer(5), SubLayer Unspecified(데이터 값). 실행 중 매 프레임 3/4/5/6/7/12 로 바뀐다 — §3.6 [실행] | BlockableSubLayerHitMask SplPlayerCharaCtrl(오징어 하위 레이어 4·5·6, SuperHookCheck, VehicleSpectacle 제외) | |

지형 삼각형의 필터는 shapeTag별 u64(=LayerHitMask | SubLayerHitMask<<32, [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §3.4). 예: `SplKeepOutPlayer`(플레이어만 막는 벽), `SplPlayerThrough`(플레이어 통과), `SplInkThrough`+`SquidThrough`(철망: 잉크·오징어 통과). 기존 결론: 두 필터의 결합식과 콜백 클래스가 미확정이었다. **2026-10-03 정정 [실행]**: 공통 강체 쌍은 Default/Same/Other 표비트와 양쪽 Layer/SubLayer 마스크 6개를 AND한다(`0x7103c4dd30`, 4096/4096 exact match). **[미확정]** shapeTag별 override 결합 방식·배열 attach·코덱 클래스는 남았다. 결합식·그룹·행 선택은 §3.5, 실행 기록은 [collision_runtime_completion.md](collision_runtime_completion.md) §10.

### 3.5 충돌 필터 결합·비교 그룹·shapeTag 행 (2026-10-03 보완 + 5차)

기준 객체: `A`/`B` = 강체, `F = *(body+0x180)` = 그 강체의 필터 객체. shapeTag 필터 표는 별도 형상 객체에 붙는다.

| 기준/필드 | 타입·의미 | writer | reader |
|---|---|---|---|
| F+0x08 bits0..5 | 레이어 번호(공통 표 행·열) | 생성 `0x7103a5fe40`(desc[0] & 0x3f; 강체 `0x7103af6088`·캐릭터 몸체 `0x7103a85a8c`·탄 `0x7103b0ae68`이 부름) [판독, 6차]. 실행 중 변경 = 대기 setter `0x7103af3834`(대기 버퍼 +0x8c, 플래그 bit12) → 월드 명령 처리 `0x7103b07b8c`. 탄은 래퍼 slot22~25 | `0x7103af44e8`, `0x7103c4dd30` |
| F+0x08 bits6..11 | 하위 레이어 번호 | 생성 `0x7103a5fe40`(desc[1], `bfi #6,#6`). 실행 중 변경 = 대기 setter `0x7103af394c`(+0x90, bit13) → `0x7103b07b8c` [판독, 6차]. 플레이어 값 규칙은 §3.6 [실행] | `0x7103c4dd30` |
| F+0x08 bit28 | 형상(shapeTag) 필터 행 사용 | 대기 setter `0x7103af43a4`(+0xc4, bit24) → `0x7103b07b8c` 의 `bfi #28,#1`(`0x7103b086a8`). 물리 구성요소 초기화 `0x71012e9914`가 functor `0x7105576db8`(slot0 `0x71012ea8c4`)로 몸체 집합을 돌며 **레이어 3(Ground) 몸체에 1** — 단 액터 태그 `Actor_MapParts_KeepOut` 또는 `Actor_Lift_KeepOut`이 있으면 건너뜀 [판독, 6차] | `0x7103c34b7c`, `0x7103c5e244` |
| F+0x0c | u32 | `0x7103a5fe40`: `[[*0x710599dfa8]+0x18]+0x48]+8` [판독] | |
| F+0x18 | u32 상대 레이어 허용 마스크 | 생성 `0x7103a5fe40`이 **공통 표 Default 행(표+0x190 + L·4)으로 초기화** [판독, 6차]. 데이터 마스크(EnableLayerHitMask 등)로 덮어쓰는 writer [미확정] | `0x7103c4dd30` |
| F+0x1c | u32 상대 하위 레이어 허용 마스크 | 로더 [미확정] | `0x7103c4dd30` |
| F+0x30 | u16 비교 그룹(0 = Default 표) | setter `0x7103ae53f0`(대기 버퍼 +0xc0, +0xd4 bit19) | `0x7103af44e8` |

**공통 쌍 필터 [실행]** (`0x7103c4dd30` → `0x7103af44e8`(A,B) → A 마스크 → `0x7103af44e8`(B,A) → B 마스크, 월드+0x18 bit3 = 0 일 때; 원본 4096/4096 정수 일치):
```text
L(x) = F(x)+8 & 63;  S(x) = (F(x)+8 >> 6) & 63
T = (그룹A == 0 || 그룹B == 0) ? Default(표+0x190) : (그룹A == 그룹B ? Same(+0x210) : Other(+0x290))
표비트(A,B) = (T[L(A)] >> (L(B)&31)) & 1
마스크(A,B) = ((F(A)+0x18 >> (L(B)&31)) & 1) & ((F(A)+0x1c >> (S(B)&31)) & 1)
허용 = 표비트(A,B) & 마스크(A,B) & 표비트(B,A) & 마스크(B,A)
```
32비트 가변 shift 는 하위 5비트만 쓴다. 실행 범위는 레이어 0..28, 하위 레이어 0..26이다. 표비트가 참이라는 것은 쌍 허용이며 막음/통과 종류까지 정하지 않는다. 월드+0x18 bit3 = 1 이면 월드+0x440 콜백과 이름 표 `0x71034a3a1c`(`Character`, body+0x88 & 0x1c == 4) 제외가 추가된다 [판독, 실행 안 함]. 좁은 단계 `0x7103c51de0`도 같은 6개 검사를 하고, 이어 형상별 검사 `0x7103b02470`을 한다. 형상별 필터 `0x7103c34b7c`는 상대 F+0x08 bit28 이 켜졌을 때 `0x7103ad658c`로 형상 필터 행을 얻는다(일반 `0x7103ad6a70`, 복합 type15 `0x7103ad677c`) [판독].

**shapeTag 행 선택 한 단계 [실행]** (`0x7103ad6a70`; 원본 1024/1024 일치, 잎 결과 태그는 스텁 공급): 형상 type 7..10, 키 ≠ −1, 정보 = 형상+0x28, 내부 메시 = 정보+0x28 이면 Havok 디스패치(내부 메시 type, slot+0xc0)로 잎 결과를 얻고, 결과+0xbf8 의 u16 에서 `index = tag & 0x1fff`; `index < (i32)정보+8` 이면 `정보+0x10` 의 8 B 행을 low/high u32 로 내보내고 1 반환, 아니면 출력하지 않고 0. 정보 객체를 만드는 writer(bphsh 필터 표 부착)는 **[미확정]**(phive_controller.md §9). 6차 보강 [데이터]: hknp 형상 +0x28 은 TAG0 형식 표의 `hknpShape::userData`(hkUint64)이다. 즉 정보 객체는 Phive 가 userData 에 단 포인터다.

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
- 질의(쓸어 넘기기) 쪽 [판독, 호출 사슬 미확인]: `0x7103c39158`~`0x7103c39190`이 상대 몸체 F+0x18 에 질의 레이어, F+0x1c 에 질의 하위 레이어가 있고 `0x7103c34b7c(L, S, key, 몸체)`가 1 이면 **접촉 +0x68 |= 2(막는 접촉 비트)**를 켠다. 탄 바디 스텝이 읽는 "막는 접촉" 비트가 여기서 온다(phive_controller.md §6.4). 이 코드가 탄 쓸어 넘기기 수집기(`0x7103c55968` → 처리기 → 수집기 vtable `0x71057552a8`)에서 불리는 사슬은 확인하지 않았다.
- 매니폴드 수정자가 Phive 월드에 등록되는 경로와, 좁은 단계 `0x7103c51de0`(공통 6검사 → `0x7103b02470`)과의 역할 분담은 [미확정].

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

**플레이어 몸 ↔ 표적(SighterTarget) [데이터]** (5차, `Pack/Actor/SighterTarget.pack.zs`): 표적 본체 강체 `Main` = LayerEntity **SplPlayer**, MotionType **Kinematic**, EnableLayerHitMask `SplPlayerColOthers`, 형상 캡슐 A(0, 1.26, 0.35)–B(0, 0.39, 0) r 0.39, 재질 프리셋 `SplPlayerColOthers`(플레이어 ColOthers 와 같은 프리셋). 피격용 `ColBullet` = SplPlayer 레이어, EnableLayerHitMask `SplPlayerSensor`, 캡슐 A(0, 1.3, 0)–B(0, 0.35, 0) r 0.35, 재질 프리셋 `SplPlayerColBullet`(플레이어 피격 캡슐과 같은 치수, [../combat/hitbox.md](../combat/hitbox.md)). PhiveConfig 레이어 표 값 SplPlayer×SplPlayer 는 Default/Same/Other 모두 **2**이고, 양쪽 마스크(SplPlayerColOthers)가 SplPlayer 비트를 포함한다. 비교 그룹은 플레이어 팀+1 ≠ 표적 팀+1 → Other 표. 따라서 **데이터상 플레이어 ColOthers 와 표적 본체는 다른 팀 플레이어끼리와 같은 조건으로 충돌 후보가 된다**. 표 값 2 가 솔버에서 "막음"인지(값 → 런타임 표비트 변환)와 형상별 마스크가 강체 F+0x18 로 가는 대응은 **[미확정]** — 웹에서 표적이 플레이어를 막게 할지는 이 가정을 표시하고 정할 것.

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
| Havok 솔버 접촉 해소 | 미확정. 캐릭터 몸체가 월드 스텝을 탄다는 것만 [판독](§4.1) | `0x71009cee34` 내부 |
| 용접 비트 | 미확정(6차 미착수) | `0x7105756468` 처리기 |
