# 플레이어 캐릭터 컨트롤러 — 형상·충돌 필터·접지 판정·이동 상태 전이

Phive 캐릭터 컨트롤러가 플레이어 캡슐을 어떻게 만들고, 물리 스텝 뒤 어떤 접촉을 "바닥"으로 인정해 OnGround/InAir를 바꾸는지 정리합니다. 속도 전달·중력·컴포넌트 순서는 [phive_controller.md](phive_controller.md), 게임 쪽 접촉 정리(벽·착지·천장)는 [../player/player_state.md](../player/player_state.md) §7.3입니다. 작업 지침: [../../분석.txt](../../분석.txt).

확정 수준: **[실행]** / **[판독]** / **[데이터]** / **[추정]** / **[미확정]**. 이 문서는 **명령 판독과 데이터만** 근거로 합니다. 원본 실행으로 확인한 것은 bss 상수(정적 초기화 에뮬)뿐입니다.

상태: 4차(phys4) 1차 작성. 웹 구현 없음. 디컴파일 `analysis/decomp/phys4/`(p4_world_ctrl.c, p4_support.c, p4_resultplayer.c, p4_pcupdate.c, p4_shape.c, p4_body.c, p4_phases.c, p4_seq.c).

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
| 강체 | LayerEntity SplPlayer(5), SubLayer Unspecified(실행 중 변경 [추정]) | BlockableSubLayerHitMask SplPlayerCharaCtrl(오징어 하위 레이어 4·5·6, SuperHookCheck, VehicleSpectacle 제외) | |

지형 삼각형의 필터는 shapeTag별 u64(=LayerHitMask | SubLayerHitMask<<32, [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §3.4). 예: `SplKeepOutPlayer`(플레이어만 막는 벽), `SplPlayerThrough`(플레이어 통과), `SplInkThrough`+`SquidThrough`(철망: 잉크·오징어 통과). 두 필터를 엔진이 결합하는 식(양쪽 마스크 AND인지, LayerEntityParamTableSet 팀 표가 끼는지)은 **[미확정]** — 필터 콜백 클래스 미발견(§9).

## 4. 몸체와 한 물리 스텝 [판독]

```
게임 슬롯18 메인 계산 → 0x71024f4f7c: ctrl.setMoveVelocity(v·60)  (+ Result+0x1338 = v + 충격 a/3600 + 본체+0x4bc..)
월드 갱신 "PreImpl Phase2" (작업 0x7103aca5d8 / 동기 0x7103ac83b4, 월드+0x50 bit4):
   캐릭터마다 0x7103a80560 → 업데이트 컴포넌트 11개(phive_controller.md §3.4) → GameApplyVelocity가 강체 선속도 설정
Havok 스텝(솔버): 위치 적분 + 접촉 해소           ← 내부 [미확정], 재질상 마찰·반발 0
결과 컴포넌트(SplResultPlayer 슬롯7 0x7102c5a3c8): 접촉 목록 → 지지·벽·천장 정보(S) → 이동 상태 전이
게임 슬롯19 0x71024abcf0 → 0x71024f7410: S → PC 필드(§7)
```
- 기준점: 컨트롤러 몸체 행렬은 ctrl+0x18 강체 +0xd8(3×4, 이동 성분 +0xe4/+0xf4/+0x104; getPosition = ctrl vt 슬롯26 `0x7103a87114`). 캡슐 바닥은 몸체 원점 −0.6. 게임 위치(본체+0x10)와 몸체 원점 사이 오프셋은 **[미확정]** — 근거: `0x71024f7410`이 탐색 구를 `본체+0x10 + 0.6·up`에 두는 점(본체+0x10이 발밑일 가능성), 반대 근거 없음. 웹은 "몸체 원점 = 발밑 + 0.6"을 가정하고 대조 테스트로 확인할 것.
- 서브스텝: 컨트롤러 업데이트는 월드 스텝마다 1회(`0x7103a80560` 호출 2곳 모두 반복 없음). 월드 dt = 1/60(phive_controller.md §6.4) **[판독, 런타임 고정은 추정]**.

## 5. 이동 상태 전이 [판독]

결과 컴포넌트 끝(기본 ApplyResult `0x7103a88248`, SplResultPlayer `0x7102c5a3c8` 2472행 근처 같은 패턴):
```
next = 상태[M+0x40].vt[0x30](&S+0x20)
if next != M+0x40: M+0x44 = 이전; 이전.vt[0x28](퇴장); M+0x40 = next; (InAir→OnGround면 M+0x48 = 1)
GameOnGround.vt[0x30] 0x71012aa648: return (S+0x20 == 0) | S+0xf4      // 1 = InAir
GameInAir.vt[0x30]    0x71012aa108: return (S+0x20 == 1 && S+0xf4 == 0) ? 0 : 1
```
- **S+0xf4 (공중 강제)** = Result 시작에서 `Result+0x1358 > 0 ‖ [0x71024f4104(PC)]+0x30 > 0 ‖ (특수 0x1c SuperLanding && [본체+0xa7f0]+0x40 == 3) ‖ 본체+0x746`. 본체+0x746은 점프 발사 계열(`0x7102641ec4`, `0x71024a8000` 직후)이 쓴다. Result+0x1358·`0x71024f4104` 대상의 writer는 [미확정].
- 게임 쪽 강제: 메인 계산이 수직 속도 > 0.001이면 현재 상태가 InAir가 아닐 때 퇴장 호출 후 M+0x40 = 1, [PC+0xe350]+0x4d = 1(`move_full_main.c` 4938~4957행). 다른 곳(카메라·생명·기믹·게이지 코드)도 M+0x40을 직접 바꾼다(`gauge_batch1.c`, `life/batch1.c` 등 — 각 영역 문서).
- Free([2])로의 전이는 외부 강제(VehicleSpectacle 등)만 확인, Free의 vt+0x30은 미판독 **[미확정]**.

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
| 게임 위치(본체+0x10) ↔ 몸체 원점 오프셋 | 미확정(0.6 위로 추정) | 본체+0x10 writer(슬롯19 또는 엔진 액터 동기), ctrl vt 슬롯27 setPosition 호출부 |
| 프레임 내 접촉 반응 시퀀서 실행 시점·액터 종류 간 순서 | 미확정 | 월드 단계 이름 "[Phive] updateWorldPre/PostImplCalledFromExternalPhase1~3"(`0x7103acaee0`가 작업 6개 등록: Pre1 `0x7103aca1b4`, Pre2 `0x7103aca5d8`(캐릭터 컨트롤러), Pre3 `0x7103aca94c`(월드 리스너 vt+0x10 호출), Post1 `0x7103ac971c`, Post2 `0x7103ac9a00`(탄 바디), Post3 `0x7103ac9ee4`). 작업 그래프를 만드는 호출부 `0x7103db4efc`/`0x7103db5218`, 시퀀서 생성 `0x71012e4d88`(0·1 두 개), 월드 리스너(`0x71012e4acc`, vtable `0x71055765e0`)의 슬롯 판독이 다음 단계(디컴파일 `p4_seq.c`에 있음, 미독) |
| 충돌 필터 결합식·shapeTag 디코드 클래스(질의 문맥 +0x130 vt+0x40) | 미확정 | 접촉 +0x38/+0x48에 재질표 행이 들어오는 것은 판독. 디코드 쓰는 쪽은 좁은 단계 처리기 |
| 용접 비트(interiorPrimitiveBitField) | 미확정(이번에 보지 못함) | 접촉 생성 쪽 |
| Free 상태 vt+0x30, Result+0x1358 writer, `0x71024f4104` 대상 | 미확정 | |
| 오징어 하위 레이어 전환(SplPlayerSquid_* 런타임 설정) | 미확정 | 강체 필터 +8 비트 6..11 쓰기 |
