# 피격 판정 형상·리시버 분배·탄 age 시작값 (combat4)

Splatoon 3 v0 원본에서 **탄이 플레이어·오브젝트에 "닿았다"고 판정되는 형상과, 닿은 뒤 어느 리시버로 데미지가 가는지**를 정리합니다. 데미지 값·배율은 [damage_hit.md](damage_hit.md), HP·아머·리스폰은 [player_life.md](player_life.md)에 있습니다.

- 작업 지침 [../../분석.txt](../../분석.txt). 확정 수준 **[실행] [판독] [데이터] [추정] [미확정]**.
- 상태: **분석 일부 완료(4차, 2026-10-02 중간 마감; 5차 2026-10-03 [r5 combat] §2·§3 보강)**. 웹 구현 없음. 남은 것은 §6.
- 도구: `web/tools/combat4_iscan.py`(명령 정규식 전수 검색, 함수별 묶음), `combat4_seqscan.py`(명령 A 뒤 N개 안 명령 B), `combat4_owner.py`(함수 → 소속 vtable·클래스 이름). 디컴파일 `analysis/decomp/combat4/c4_batch1.c`.

## 1. 탄 age는 −1에서 시작한다 [판독: 명령 직접] — 정정

| 근거 | 내용 |
|---|---|
| `0x7101645608` / `0x7101645610` | 시작 보조 `0x7101645590`(슬롯15 `0x710174efc0` → `0x7101762f68` → 첫 `bl`)이 분기 합류점 뒤에서 무조건 `mov w23,#-1; str w23,[x19,#0x134]` |
| `0x7101646128`~`0x7101646160` | 슬롯18: `age < 0`이면 prevPos 저장 생략(`tbnz w8,#31`), 그 뒤 `age += 1` |
| `0x7101764178` | 슬롯54: `age == 0`이면 상태머신은 진행하되 속도 = 입력 속도(생성 속도) 그대로 |
| `0x71017640b4` | 슬롯54: `age == 1`이면 생성 속력으로 재정규화 |

따라서 **첫 갱신이 age 0, 두 번째 갱신이 age 1**입니다. 이전 판(이 문서 영역의 damage_hit §6.1, [bullet] 문서)의 "생성 0, 첫 갱신 age 1"은 틀렸습니다. 생성자(`0x710174e644` 경로)가 0을 쓰지만 시작이 곧바로 −1로 덮습니다. `0x7101644e84`(복원 경로로 보임 [추정])만 외부 값으로 age를 씁니다.

영향: 데미지 감쇠의 age([damage_hit.md §6.1](damage_hit.md)), 반경 보간 `age/ChangeFrame`(§6.2), FriendThroughFrame 해제 `age == FTF`(§4.8)는 모두 이 age를 씁니다. 감쇠 시작(ReduceStartFrame)의 최솟값이 4(Precision)라 **처음 몇 프레임의 데미지는 age −1/0/1/2 어느 쪽이든 ValueMax**이지만, 같은 "비행 프레임 수"에서 age가 이전 가정보다 1 작으므로 감쇠 곡선 전체가 한 프레임 늦게 적용됩니다.

**첫 명중 age — 정정(2026-10-03 [r5 combat]): [추정] → [판독]**. [r5 physics]가 프레임 안 순서를 판독(그래프 간선은 원본 실행)했습니다([physics/phive_controller.md §6.7](../physics/phive_controller.md)): 단계0에서 표적·플레이어·탄의 슬롯18 → Phive Entity 월드 갱신(탄 바디 스텝·접촉 작업 등록), 단계1 그룹0에서 접촉 반응 큐 비우기(탄 슬롯22 = OnHit) → 그 뒤 액터 슬롯19·20·21. 따라서 **이동으로 생긴 첫 접촉의 데미지는 그 프레임 슬롯18이 올린 age, 곧 age 0**입니다(생성 age −1, 생성 바디 속도 0 — [weapon/shooter_bullet.md §3.3](../weapon/shooter_bullet.md), SHARED [r5 camweapon]). 생성 위치가 처음부터 겹친 경우에 그 탄의 첫 슬롯18보다 먼저 Phive가 도는지는 탄이 생성되는 단계에 달려 [미확정]이지만, age −1/0 모두 ReduceStartFrame(최소 4)보다 작아 데미지는 같습니다. 이전 판 기록: [move] 문서의 "슬롯18 → 물리 스텝 → 슬롯19" 순서를 따르고 접촉 반응 시퀀서(탄 슬롯22)가 물리 뒤·다음 슬롯18 앞이면, 이동으로 생긴 첫 접촉은 **age 0**(첫 갱신의 물리 스텝)입니다. 생성 위치가 처음부터 겹친 경우 첫 슬롯18 전에 물리 스텝이 돌면 age −1입니다(감쇠 결과는 같음). 프레임 안 순서는 [phys4]에 요청함(SHARED).

## 2. 플레이어 피격 형상 [데이터] + 결속 [판독 일부]

`extracted/actor/SplPlayer/Phive/`:

| 바디(RigidBody) | 형상 | LayerEntity / 히트 마스크 | 쓰임 |
|---|---|---|---|
| `ColBullet` | 캡슐 A(0, 0.35, 0) B(0, 1.30, 0), r **0.35** (발밑 원점 기준, 높이 0~1.65) | `SplPlayer` / `SplPlayerSensor`(CustomReceiver, GameCustomReceiver, SplInkBullet, SplInkBullet_FriendThrough, SplSubstanceBullet_HitOpposite/_HitBullet, SplRollerBody, SplBlowerInhale, SplBluntWeapon, SplInkTornado, SplGreatBarrier, SplSaberBombGuard, SplItem) | **탄 피격 판정**. Kinematic, 액터 행렬 결속(`BoneBindModePosition All`, 추적 뼈 없음, `WarpMode AfterUpdateWorldMtx`), 리셋 때 월드에 추가 |
| `ColBullet_Chariot` | 구(캡슐 A=B) 중심 (0, 0.4, 0), r 1.15 | `SplPlayerChariotShield` / `SplChariotColBullet` | 스페셜 Chariot(게살 탱크 추정) 중. 리셋 때 추가하지 않음 |
| `ColBullet_CoopZombie` | 구 중심 원점 r 0.8 | `SplObject` / `SplPlayerSensorCoopZombie` | 코옵 좀비 |
| (캐릭터 컨트롤러 `SplPlayer_cct`) | `ColGround` 캡슐 (0,0,0)-(0,0.7,0) r 0.6, `ColOthers` (0,−0.21,0)-(0,0.51,0) r 0.39 | 이동·지형용 | 피격과 무관 |

- `spl:PlayerCollision`(vtable `0x7105633ec0`, 본체+0xa690) 초기화 `0x71024f2e5c`가 +0x48 = `ColBullet`, +0x50 = 표[1] 이름 바디(`ColBullet_CoopZombie`로 추정), +0x58 = `ColBullet_Chariot` 바디를 잡습니다 **[판독]**.
- **인간/오징어/잠복 차이**: 데이터의 피격 캡슐은 하나뿐이고, 형태별로 형상·크기를 바꾸는 코드는 이번에 찾지 못했습니다 **[미확정]**. 2026-10-03 [r5 combat] 추가 판독: `0x71024f4ccc(PC, zombie)`는 ColBullet(+0x48)에 zombie 값, +0x50 바디에 항상 1로 `0x7103ae4c48`을 부른 뒤 팀 그룹을 설정합니다(§3 표). `0x7103ae4c48`의 플레이어 범위 호출은 이 밖에도 27곳입니다 — `spl:PlayerCollision` 슬롯13 `0x71024f4270`(→ `0x71024f4440`, +0x50에 1)·슬롯48 `0x71024fc228`·슬롯73 `0x71024fc7e8`, `spl::PlayerPipeline` 경로 `0x71024f87dc`(+0x48/+0x50/+0x58), 리스폰 리셋 `0x710249cb60` 2곳, `0x71024a2b74`, SuperHook `0x71024b3efc`, `0x71024b48fc`, `0x71024b9edc`, `0x710249a6a8`/`0x710249c0c4`/`0x710249c4bc`, `0x7102523398`, `0x710259b6d4`/`0x710259b748`, `0x71026895c8`/`0x7102689818`(`bl_callers.py 0x7103ae4c48`). 탄 코드에서도 수십 곳이 켜고 끕니다. 이 중 형태(인간/오징어/잠복) 전이와 이어지는 것이 있는지, 비트11의 의미(쌍 판정·좁은 단계에서 읽는 곳)는 [미확정] — 다음 단서: 위 PlayerCollision 슬롯13/48/73의 호출 시점, Phive에서 바디+0x88 비트11(`tbz/tbnz #0xb`)을 읽는 곳. `0x7103ae4c48(바디, bool)`이 +0x48/+0x50 바디에 리스폰 리셋(1)·리스폰 후 타이머 종료(0)·SuperHook 공격 상태 진입(0, `0x71024b3efc`)에서 불립니다 — 바디 활성/비활성 계열로 보이나 의미 **[미확정]**(`0x7103ae4c48` 디컴파일: `c4_batch1.c`).
- 탄 쪽: `ExceptGround` 구(반경 = `InitRadiusForPlayer`→`EndRadiusForPlayer`, damage_hit §6.2)와 이 캡슐의 접촉. 판정식은 Havok 좁은 단계라 판독하지 않았습니다. 웹은 **선분(쓸어 넘긴 탄 중심 p0→p1)과 캡슐 축 사이 거리 ≤ r_bullet + 0.35** 로 근사합니다 **[추정]**(막는 접촉 중 최소 비율 f에서 정지 — [physics §6.4](../physics/phive_controller.md)).

### 2.1 일반 인간·오징어·잠복의 실제 피격 형상 — 2026-10-03 정정 [판독]+[실행]

§2의 “형태별 크기 코드 미발견”과 §6의 후보 함수 표는 당시 기록으로 보존하고 다음 새 검증으로 정정한다. 일반1인연습의 크기 갱신 함수는 **24F5DD8 전체**, 피격 body는 **PC+0x48 ColBullet**다. 상태→B+0x7a4의 t 생산/10프레임 접근은 기존 r6 근거를 재사용한다. PC+0x16c에 저장된 t는 끝점0/1 부근 ±2^-23에서 값이 다르면, 중간값에서는 abs(f32(old−t))>.2f이면 갱신한다. 잠복 여부로 별도 ColBullet 치수를 고르는 분기는 없으며 오징어 상태집합의 t를 함께 쓴다. 지형용 B+0x7a8과 구분한다.

```text
r = f32(.35f + f32(f32(.8f−.35f)*t))
H = f32(1.65f + f32(−1.65f*t))
H <= f32(r+r): A=B=(0,f32(H*.5f),0)
그 밖:        A=(0,r,0), B=(0,f32(H−r),0)
```

인간 t0: A.y=.35/B.y=1.30/r=.35. 오징어 t1: A=B=(0,0,0)/r=.8. 중간 t.6: A=B.y=.3299999833/r=.6200000048. H1.65는 인간 **전체 높이**이며 캡슐 축 길이로 해석하지 않는다. 원본은 중간 구형 전환에서 H를2r로 올려 보정하지 않는다. 이 함수가 갱신하는 두 번째 body는 **PC+0x58 ColBullet_Chariot** 중심이며 PC+0x50 CoopZombie가 아니다. Chariot 실제 동작은 범위 밖이며 일반형 크기 증거와 구분한다.

새 native 소비까지 연결했다: 실제 CapsuleVT5745788+A0=**3A6AEF4**가 gameShape+d8/e4/f0의 A/B/r를 읽고 세 축 차이가 모두 ±2^-23 안이면 **092EFBC sphere**, 아니면 **0930B40 capsule**을 만든다. backend f8의 vt38=**3C2799C**가 새 native 참조 증가→backend+8 교체→이전 참조 감소, 임시 참조 감소 뒤 vt18=**3C27858**가 nativeShape+28에 gameShape owner를 기록한다. 기존 pending 재생성 처리3A66EA4와 frame단계 소비는 재사용이다. 형태 갱신은 bit11을 쓰지 않으며 bool1 쌍거부/bool0 저장 마스크 복원은 §3.1의 별도 native filter 근거다. 일반 형태 크기를 bit11의 enable 변화라고 설명하지 않는다.

**신규 실행:** 전체24F5DD8→실제 Capsule RTTI/A0→실제 native 재생성/교체 콜백의 연속1,014사례에서 **24,417 f32필드 및6,084 종류·정점수·owner필드**가 독립 기대값과 비트 일치, null/자동 매핑/실행 오류0. 앞선 gameShape만 검증한1,014/15,210과 중복 신규 항목으로 계산하지 않는다. 실제 shape 타입·정점·반경까지 검증했으나 synthetic PC/Actor fixture·참조 body 목록이 비어 있어 부착 body의 shape-change notification/broadphase 및 전체 접촉 솔버는 별도 미검증이다. 비일반 특수·아머·debug·Replica 크기 override는 일반1인연습 질문에 합쳐 확정하지 않는다.

명령 `.venv/Scripts/python.exe web/tools/r8_physics_hitshape_native_emu.py` exit0, `physics_hitshape_native_emu.json`. 첫 보조 shape를 PC50으로 본1,009건 독립 기대값 실패와 첫 native owner bind 누락2필드 실패는 각각 `physics_hitshape_wrong_secondary_failure.json`/`physics_hitshape_native_owner_initial_failure.json`에 보존했다. PC58 명령 판독 및 실제 초기 owner callback 실행으로 정정했다. 식과 pending 소비·기존 후보24F4994/4A44/4878/BB7C의 실제 생명주기 역할은 [character_controller.md §3.3.1–3.3.2](../physics/character_controller.md)에 있다.

웹 반영 필요: 화면 모델 크기 대신 ColBullet의 t·.2 히스테리시스·위 r/H/A/B 식과 native sphere 전환 경계를 적용한다. 잠복을 독립 작은 캡슐로 가정하지 않는다. 형상 갱신과 리스폰 쌍 마스크를 분리한다.

## 3. 같은 팀 통과 — 필터 그룹 [판독 일부], 표 선택 [미확정]

- 탄 시작 `0x71016455d0`~`0x71016455fc`: 생성정보+0x18 바이트가 참이면 래퍼 슬롯5 `0x71016cafc0`({u32 생성정보+0x10, u8 생성정보+0x14})로 모든 유닛 바디의 필터 객체 F(= 바디 vt+0x38 = 바디+0x138)에 **F+0x14 = 그룹 id, F+8 비트12 = 그룹 사용**을 씁니다 **[판독]**. F+8 비트0~5 = 레이어, 6~11 = 하위 레이어 **[판독]**.
- **표 선택 규칙 [판독]** (보조 조사, `analysis/decomp/combat4/filter_1.c`·`filter_2.c`): 표 변환 `0x7103b16ad8`이 층(레이어) 행마다 마스크 둘을 만듭니다 — mask0 = 값 1 또는 2, mask1 = 값 2. 백엔드(`CollisionFilterBackEnd`, 생성 `0x7103b1ab5c`, 0x310 B, 복사 `0x7103b1ae90`)에 Default/Same/Other × mask0/mask1이 층당 u32로 들어갑니다. 쌍 판정 `0x7103af44e8(A,B)`는 두 바디의 필터 객체 **F+0x30(u16)** 을 봅니다: 하나라도 0 → Default, 둘 다 0이 아니고 같음 → Same, 다름 → Other(`0x7103af4518`/`0x7103af4520`/`0x7103af4610`). 그 표의 A층 행에서 B층 비트를 검사하고, 최종 판정(`0x7103c4dd30` 등 4곳)은 (A,B)·(B,A) 양쪽과 F+0x18(층)·F+0x1c(하위 층) 마스크를 모두 통과해야 충돌입니다.
- 따라서 Same/Other를 가르는 값은 위 F+0x14/비트12가 아니라 **F+0x30**이고, 그 setter는 `0x7103ae53f0(바디, u16)`(대기 버퍼 +0xc0, 적용 `0x7103b084d4`)입니다. 게임 코드에서 누가 ColBullet·탄 바디에 어떤 값(팀 번호 추정)을 넣는지는 **[미확정]** — 다음 단서: `0x7103ae53f0` 호출자. F+0x14/비트12의 용도와 생성정보 +0x10/+0x14/+0x18의 출처도 미확정.
- **F+0x30 writer 정리 [판독]** (2026-10-03 [r5 combat], `bl_callers.py 0x7103ae53f0` 11곳 전수 + 포인터 참조 0): 게임 쪽 값은 모두 **팀 → 그룹 = (팀 ∈ {−1, 3}) ? 0 : 팀 + 1** 입니다([physics/collision_runtime_completion.md](../physics/collision_runtime_completion.md)의 `0x71012eab48`/`0x71012eac80`/`0x71021f2e70` 매핑과 같음). 이번에 등록 경로를 찾았습니다.

  | 경로 | 대상 바디 | 팀 |
  |---|---|---|
  | 액터 활성화 `0x7100f7400c` → 물리 컴포넌트(액터+0x510) `0x71012e9914` → functor `0x71012eab48`(vt `0x7105576df0`) | 그 액터 물리 컴포넌트의 모든 바디(F+0x30이 이미 0이 아니면 그대로) | `[comp+8]+8`+0x668. 단 comp+8 객체가 형식 `*0x7105793128` IsA일 때만(형식 이름 [미확정]) |
  | `spl:PlayerCollision` `0x71024f4ccc(PC, zombie)` ← 리스폰 리셋 `0x710249cb60`, `0x71024b270c`(코옵 좀비 해제) | 플레이어 액터 물리 컴포넌트의 모든 바디(ColBullet 포함) | zombie = 0이면 액터+0x668, 1이면 **팀 1 고정(그룹 2)** |
  | `spl::SighterTarget` `0x71021ef2cc` → functor `0x71021f2e70`(vt `0x7105615478`) | 표적 바디(+0x1d8 컴포넌트) | (로컬 플레이어 팀 == 1) ? 0 : 1 — 리시버 +0x1bc에도 같은 값 |
  | functor vt `0x7105576e28`(`0x71012eac80`) | `spl::AttractTarget`(`0x710211d234`), `spl::Geyser`(`0x7102157a04`), `spl::MovePainterFixedDirection`(`0x71021c12d8`), `spl::GrindRail`(`0x7102167d94`), `spl::InkRail`(`0x7102178c44`), PlayerCollision | 각자 넘긴 팀 |
  | 조준 예측·탄 질의(바디가 아니라 질의 필터) | `0x710175779c`(§6.7 damage_hit), `0x710164dd5c`(Beacon) 등 탄 코드 `strh [x,#0x30]` 10곳 | 생성정보+0x2c(팀)+1 |
  | Phive 내부 `0x7103a11ad4`, `0x7103aeca74`, `0x7103aefbfc`, `0x7103b35594`, `0x7103b35f38`, `0x7103b36d60`, `0x7103b37b28` | 재초기화 플래그 비트8일 때 | **0으로 리셋** |

  **탄 바디 자체의 F+0x30을 쓰는 곳은 찾지 못했습니다 [미확정]**: 위 11개 호출자에 탄 경로가 없고, 탄 코드 범위(0x7101640000~0x7101780000)·바디 설명자 범위(0x7100f00000~0x7101200000)·Phive 탄 바디 생성 `0x7103b0af78`/설정 `0x7103b0ada8`에서 `strh [x,#0x30]` 바디 필터 쓰기를 찾지 못했습니다. 0이면 Default 표를 고르고 그 표의 `SplInkBullet_FriendThrough × SplPlayer` = 2(충돌)이므로, 아군 통과가 Same 표로 이뤄지려면 탄 바디에도 팀 그룹이 있어야 합니다. 조준 예측 질의는 팀 + 1을 넣으므로 원본 의도는 "탄도 팀 그룹을 가진다"로 보이나 **[추정]** 입니다. 또 탄 바디 래퍼의 레이어 setter(`0x71016cb4c0`, damage_hit §4.8)는 필터 객체를 **내부 바디(vt+0x90)+0x138**에서 찾는데, 쌍 판정 `0x7103af44e8`은 **강체+0x180**을 읽습니다 — 탄 바디가 이 쌍 판정을 그대로 타는지부터 [미확정]입니다. 다음에 볼 곳: Phive 탄 바디(vt `0x7105749990`)의 +0x180 필터 객체 생성(`0x7103b09ee4`, `0x7103a62e78`), 탄 바디 설명자 `0x71010036a8`이 넘기는 필터 정보, 바디 → 질의 복사 함수 `0x71012edb20`/`0x7103afc394`의 역방향(질의 → 바디)이 있는지.
- **정정(2026-10-03 [r6 combat]): 탄 바디 F+0x30 = 팀 + 1 [실행]**. 위 "탄 바디 writer 못 찾음"을 바로잡습니다.
  - writer는 `0x7103ae53f0` 호출자가 아니라 **BulletBodyComponent 슬롯9 `0x71013405e0`**(바디 월드 추가)입니다. 유닛마다 F = 바디.vt+0x38(`0x7103b0b350` = 바디+0x138)을 얻고, **F+0x30 == 0일 때만** F+0x30 = (팀 ∈ {−1, 3}) ? 0 : 팀 + 1 을 씁니다(`0x7101340678`~`0x71013406a4`). 팀 = 액터(컴포넌트+0x20, vt+0x78 = `0x7100f78650` 자기 자신)+0x668.
  - 액터+0x668은 탄 행동 슬롯12 `0x71016444ec`가 생성정보+0x2c(팀)로 씁니다(액터+0x4d0 == 2면 안 씀, `0x71016445ac`). 풀 생성 `0x7100f7f6a4`가 슬롯12(vt+0x60)를 부른 뒤 활성화 요청(`0x7103c7ea60`, 0xef)을 하므로 팀 기록이 바디 월드 추가보다 앞섭니다 [판독].
  - 필터 객체는 `0x7103b0ae68` → `0x7103a5fe40`(0x40 B)가 만들고 +0x30 = 0으로 시작합니다. `0x7103b09ee4`(바디 해제)·`0x7103a62e78`(접촉 목록 생성)은 필터와 무관합니다 [판독]. 풀 재사용 때 F+0x30을 0으로 되돌리는 곳은 phive 탄 바디 범위(0x7103b09000~0x7103b10000)에 없습니다 [판독].
  - **탄↔강체 쌍 판정은 `0x7103af44e8`을 타지 않습니다.** 접촉 필터 `0x7103c55ed8(접촉, 탄 바디, 키, 강체, 키)`가 F_A = 탄 바디+0x138, F_B = 강체+0x180으로 `0x7103c34e14`(같은 Default/Same/Other 선택 + F+0x18/+0x1c 마스크 + 형상 필터 `0x7103c34ce8`, 양방향)를 부르고, 참이면 **접촉+0x68 비트1(막는 접촉)** 을 켭니다. 표는 값 2만 담은 mask1(+0x190/+0x210/+0x290, 백엔드 복사 `0x7103b1ada4`의 `0x7103b1af6c`/`0x7103b1b1c4`)입니다 [판독].
  - **원본 실행** `PY web/tools/r6_combat_filter_emu.py`(결과 `analysis/combat/r6_filter_emu.json`): A 슬롯12 → 슬롯9 연결 600건, B `0x7103c55ed8`(+`0x7103c34e14`, `0x7103c34ce8` 원본) PhiveConfig 실제 표로 4,006건, **불일치 0**. 스텁: IsA 가상 호출 = 1, 행동 vt+0x1a8 = 1, 뮤텍스 PLT 바로 반환, 월드 추가·공간 격자 경로 끔.
  - **결론 [실행 + 데이터]**: 슈터 탄(FTF 0 → 레이어 8 `SplInkBullet`)과 같은 팀 ColBullet은 그룹이 같아 Same 표를 고르고, `SplInkBullet × SplPlayer` Same = 2 → **막는 접촉**. 다른 팀(Other)과 똑같이 막히며, 리시버 결과는 Through·데미지 0입니다. `SplInkBullet_FriendThrough`(9) × 같은 팀은 0 → 통과. 마스크 F+0x18/+0x1c는 팀과 무관해 이 구분을 바꾸지 않습니다. 탄 F+0x18 = BlockableLayerHitMask(`HitAll`, 설명자 `0x7101004e00` 5번째 필드 → desc+0x50) [데이터 + 판독], F+0x1c(BlockableSubLayerHitMask 기본값)는 [미확정].
- `0x7103ae4c48(바디, bool)`은 그룹 setter가 아니라 바디+0x88 비트11(0x800)을 켜고 끄는 함수입니다(대기 +0xd0 비트0, 적용 `0x7103b08540`~`0x7103b08564`) **[판독]**, 비트 의미 **[미확정]**.
- **구현에 중요한 관찰 [데이터]+[추정]**: 슈터 데이터는 `FriendThroughFrameForPlayer = 0`을 명시하고(`WeaponShooter*`; 미션·Rival 적 슈터만 4), FTF 0이면 시작에서 레이어 8(`SplInkBullet`)이 됩니다(§4.8 판독). `SplInkBullet × SplPlayer`는 **세 표(Default/Same/Other) 모두 2(충돌)** 이고 위 쌍 판정은 어느 표를 고르든 이 칸을 보므로(F+0x18/+0x1c 마스크가 막지 않는다면) **슈터 탄은 같은 팀 플레이어 캡슐에도 물리적으로 막힙니다** — 리시버 결과는 Through·데미지 0이고 슬롯60이 `+0x12a = 1`(다음 슬롯21에서 소멸)을 겁니다. FriendThrough(9)는 Same 표에서만 0입니다. 그룹·표 선택이 확정되기 전까지 웹은 "슈터 탄은 아군에 막혀 소멸, 데미지 0"으로 두고 **[추정]** 표시를 유지하세요.

### 3.1 Body bit11의 의미 — 2026-10-03 정정 [판독]+[실행]

§3의 기존 “비트 의미 [미확정]” 기록은 당시 결론으로 보존한다. **새 실제 native 쌍 필터의 판독·실행으로 의미를 해소했다.** `3AE4C48(Body,1)`은 Body+0x88 bit11을 켜서 전체 staging 적용 `3B07B8C`에서 **F+0xc 허용 layer 마스크를0**으로 만든다. `(...,0)`은 bit11을 끄고 Body+0x15c 저장 마스크를 복원한다. Body bit27의 전역 마스크 제한은 별도로 적용된다. 그룹 setter·형상 축소·nativeBody 제거·motion active flag로 해석하지 않는다.

새 native filter VT `5756560`+0x20=`3C56BC4` → **새 `3B19798→3B19308`**은 nativeWorld+0x38의 0xc0 B body에서 +0x98 engine Body를 읽고, 표의 허용값과 양방향 F+0xc layer 비트를 모두 요구한다. 따라서 bool1로 마스크0이 된 몸체는 native body 쌍 목록에서 거부된다. F+8 bits16..19에 따른 sublayer 검사와 F+0x18/+0x1c blockable 마스크는 구분해야 한다. pending+0xd0 bit0/dirty+0xd4 bit19의 적용 대기와 부착된 몸체의 `3C50020` 갱신 판독도 확인했다.

원본 setter→전체 staging **16,384사례/32,768필드**, 실제 native filter **17,571쌍**, 독립 표/마스크 계산과 불일치0, null/자동 매핑/실행 오류0. 원본 CharacterMatterRigidBody VT의 실제 F getter를 사용했다. synthetic engine/native Body·표 fixture, 단일 스레드 mutex no-op과 부착되지 않은 몸체의 갱신 early return을 명시한다. 실제 부착된 broadphase refresh·솔버·인간/오징어/잠복 형상 전체를 이 검증으로 확정하지 않는다. 기존 allow 표29×3과 기존 setter 판독은 재사용이며 **새 소비자·연결 실행**이 r8 근거다.

전체 식·명령·추상 VT null 실패 기록은 [character_controller.md §3.3.2](../physics/character_controller.md), `web/tools/r8_physics_bit11_pair_emu.py`, `analysis/completion/r8/physics_bit11_pair_emu.json`을 따른다. 웹 반영 필요: 리스폰 등에서 bool1을 충돌 enable로 쓰지 말고 native pair 허용 마스크0으로 적용하며, bool0에서 저장 마스크를 복원한다. 형태별 크기 질문은 별도로 남긴다.

## 4. 접촉 → 리시버 분배 규칙 (일반 리시버) [판독]

`0x71012d4adc`(damage_hit §3.3)를 다시 읽은 결과, 리시버 목록은 액터 전체가 아니라 **닿은 바디(강체)마다** 붙어 있습니다.

```
pair = 첫 접촉 쌍; self/other 쪽은 pair+8/+9 바이트와 pair 플래그 비트0, pair+0x69 비트4로 고름
sender = other 바디+0x238                     // 일반 강체
       | (self가 탄 바디형) self 바디+0x150    // 탄 래퍼 슬롯4 0x71016caf20가 모든 유닛 바디 +0x150에 씀
receivers = 상대 강체+0x248[개수 +0x240]  또는 (탄 바디형 상대) +0x160[+0x158]
result0 = 접촉 목록에 막는 접촉(+0x68 비트1)이 있으면 1(Constant) 아니면 0
for R in receivers: copy→ R.vt38(computeResult) → R.vt40(apply); 데미지·결과는 최댓값
수신 대상이 없으면: 막는 접촉 있으면 {0, 결과 1}, 없으면 {0, 0}
```

- 데이터 `spl__DamageParam.DamageReceiverArray[].RefRigidBody`가 리시버 ↔ 바디 대응입니다 **[데이터]**: `SplPlayer` Main(`Default` 열) = `ColBullet`/`Body`/`ColBullet_CoopZombie`, Chariot(`Chariot` 열) = `ColBullet_Chariot`. 비컨 Main(`Wsb_Flag`) = `Body`. 따라서 게살 탱크 중 탱크 구에 맞으면 Chariot 열 배율, 몸 캡슐에 맞으면 Default 열입니다 **[추정: 대응 연결 코드는 미판독]**.
- `RefHitPointHolder`가 리시버와 HP 홀더를 잇는 이름 목록입니다(비컨은 비어 있음 — 이 경우 DamageHelper 리스너가 리시버 이름 → 대상 마스크로 홀더를 고름, player_life §3.6) **[데이터]**, 연결 코드 **[미확정]**.
- **송신자 클래스·이력 모드 [판독]** (2026-10-03 [r6 combat]): 송신자 객체(0x80 B, vtable `0x71055bdfd0`)는 탄의 `spl:DamageHelper`(탄+0x160) 초기화 `0x7101e3d69c`가 DamageSenderArray 항목마다 만들고(`0x7101e400fc`~`0x7101e4012c`: +0x60 핸들 = *[`0x7105797f20`], **+0x68 모드 = 0**, +0x6c/+0x6d = 1/1, +0x70 상한 = 0, +0x74 간격 = 0.0, +0x78 key = −1), 바디+0x150에 이름으로 연결합니다. vt18/20/28/30/38/40/48 = +0x60/+0x68/+0x74/+0x6c/+0x6d/+0x70/+0x78 읽기. 탄 공통 시작 `0x7101645590`이 +0x6c = 생성정보+0x6d, 기본 functor(vt `0x710559ad50`)로 +0x6d = 탄.vt+0x208을 씁니다. **BulletShooterBase는 전용 functor가 없어 모드 0(이력 판정 없음)** 입니다. 클래스별 functor 52개 전수(`PY web/tools/r6_combat_sender_modes.py` → `analysis/combat/r6_sender_modes.json`): 모드 1(간격 = 파라미터 프레임/60) TripleTornado·ShelterCanopy·Shield·BombCurling·RollerBody·SpChariotBody·JetpackJet·MicroLaserBit·SuperLaser·ShockSonarGenerator·연어런 적 다수, 2 BlasterBase·ChargerBase·RollerInk·LineMarker·SpMultiMissile·SuperHook·UltraStamp 등, 3 ShelterShotBase, 4 BlastSpNiceBall, 5 SpInkStormCloud, Blast·SlosherBase는 계산값. 그래서 이 탄은 바디의 DamageHelper(+0x160)를 **송신자 쪽**으로 씁니다(이전 "용도 미확정" 해소). 핸들 *[`0x7105797f20`]의 id는 [미확정].
- 탄의 송신자(이력 모드 vt+0x20 등을 가진 객체)는 탄 바디+0x150입니다. 슈터 탄 GPT `BulletShooterBase`의 `DamageSenderArray = [{Name "Main", RefRigidBody []}]`. 그 송신자 클래스의 모드 값은 **[미확정]**(생성 함수 후보 `0x7101e3d69c`, `analysis/decomp/life/batch1.c`).

## 5. 웹 구현 요약

1. 탄 age: 시작 −1, 갱신마다 +1(이동 전). 슬롯54: age 0이면 속도 그대로, age 1이면 생성 속력으로 재정규화.
2. 플레이어 피격 캡슐: 발밑 기준 y 0.35~1.30, r 0.35, 형태 무관(미확정 표시). 탄 구 반경과 더해 선분-캡슐 거리로 판정, 최소 비율 접촉에서 정지.
3. 리시버는 바디별 목록, 결과 최댓값. 아군 통과는 §3 [추정]대로.

### 4.1 RefHitPointHolder 이름 → 피해 대상 마스크 [판독 + 실행] (2026-10-03 [r8 combat])

기존 §4의 “연결 코드 미확정”을 해소한다. 신규 원본 reflection `1a82330(444B)`은 **DamageReceiverParam+68 = RefHitPointHolder**, +BE 상속/설정 플래그로 등록한다(원본 visitor 인자 기록). `1e3d69c`의 `1e3f9..1e3fd84`는 부모 항목의 +68을 선택한 뒤 이름 배열을 순회하며 DamageHelper+30 개수/+38 배열의 HP 홀더 이름을 대조한다. 첫 일치 인덱스 i에 대해 **mask |= 1u << (i&31)**. 같은 이름을 중복 기재해도 OR, 없는 이름은 추가하지 않고, 홀더 배열의 이름이 중복이면 첫 항목만 고른다. Ref 목록이 비고 홀더가 하나 이상이면 mask=0xffffffff, 홀더가0개면 초기0을 유지한다. 이 마스크는 리시버 이름을 키로 하는 Helper+98 tree의 node+28에 기록된다.

실제 리스너 `1e4476c`는 리시버 이름으로 그 tree를 찾고 마스크가 켜진 각 홀더에 `1a89524`(피해 누적), 결과7=Cure이면 `1a89790`를 호출한다. tree에 이름이 없으면 기본mask1로 첫 홀더를 선택한다. 커스텀 functor Helper+1a0/+1c0 경로는 명시적 대상 마스크를 우선할 수 있다(기존 §3.6 연결). **32 이상 인덱스는 원본 W-register shift의 하위5비트 때문에 마스크가 겹친다.** 더 자연스러운64bit 구현으로 바꾸면 원본과 다르다.

새 `r8_combat_holder_binding_emu.py`: 원본 reflection descriptor3개 확인, **원본 함수 안 `1e3fb00/20..fb5c` 완결 마스크 구간1,300건**(0..40홀더, UTF8/중복/없는 이름, empty), **전체 로컬 리스너72건**(Cure/피해, 0/1/2/7/32/37홀더·마스크) 불일치0. 마스크 구간은 스텁없음. 리스너의 홀더 누적/회복은 호출 대상을 기록하는 경계 스텁, dc=0으로 네트워크 송신 경로 제외. 전체 DamageHelper 생성/넷 이벤트를 실행했다고 확대하지 않는다. 결과 `analysis/completion/r8/combat_holder_binding_emu.json`; 기존 `life/batch1.c`·`network/net_player.c` 재사용, 신규 `r8_combat/receiver_reflect.c` 1함수.

웹 반영 필요: `impl/weapon.md`, `impl/range.md`, `impl/combat.md`에서 리시버별 이름 연결/empty=전체 mask/firstmatch/Cure 대상/32bitshift 순서를 반영해야 한다. 구현 코드는 수정하지 않았다.

### 4.2 RefRigidBody 이름 → 실제 몸체별 리시버 목록 — 2026-10-03 정정 [데이터]+[판독]+[실행]

위 §4의 데이터 대응 추정을 보존하고 정정한다. 원본 `1e3d69c`의 완결 바인딩 구간 및 새 이름 조회·전체 순회·Phive 이름 getter를 실행해 **RefRigidBody 문자열이 실제 body+248 receiver 목록에 연결됨**을 확인했다. 각 receiver의 원본 ctor에서 Name/RateColumn도 확인했다. body별 receiver를 쓰는 기존12D4ADC 소비를 연결하므로 Main의 Default, Chariot의 Chariot 열 대응은 추정이 아니다. 실제 Chariot 특수 행동·다른 무기 실행으로 범위를 확장하지 않고 원본 데이터에 있는 이름 연결을 확인했다. 고정 r7 hitboxL61의 미판독 연결식 질문을 해소한다. 전체 actor load/metadata등록/비로컬 상속 producer는 별도 경계이며 실행했다고 넓히지 않는다.

#### 원본 경로

1. 새 원본 factory `1a82234(244B)`는 `DamageReceiverParam`(0xc8 B, VT55c9438), RefRigidBody 배열 +90(VT5737130), RefHitPointHolder +68을 실제 초기화한다. Ref count는 배열+24=P+b4, parent pointer=배열+10; 판독 `38a94fc(60B)`는 실제 array.vt+80 count와 parent count를 합친다. 값 필드만 만들고 VT를 빼면 count가 틀리는 것이 첫 실패 원인이었다.
2. 기존 reflection `1a82330`의 RefRigidBody 값 +90/flag BD 및 이름 +60을 사용한다. Helper+1f0=DamageParam의 ReceiverArray+30을 순회한다. BD 플래그가 없으면 동일 타입·유효 generation인 부모 값을 탐색한다. 이번 실행은 로컬 BC/BD/BF=1, parent null이며 실제 상속 RTTI/generation 조합은 판독만 했고 실행 범위에서 제외한다.
3. 목록이 비지 않으면 각 UTF-8 문자열에 대해 **새 `12ec7c0(424B)`**로 Helper+1f8 Physics 객체의 몸체를 순회한다. 직접 몸체는 Physics+10 list(+10 count/+18 pointer array), controller는 Physics+18/+20에서 controller+8 group(+10 count/+18, unit stride18의 +8 body)을 읽는다. 추가 Physics+120 dynamic controller 분기는 판독했으나 이번 fixture는 null이다.
4. **새 `12ee210(148B)`**, VT5576f50 slot0는 해당 body.vt0로 이름을 얻고 요청 문자열과 byte 단위 비교한다. 일치하면 output에 body 포인터를 쓰지만 순회를 멈추지 않는다. 따라서 **동명 body가 여러 개이면 순회에서 마지막 일치**를 선택한다.
5. **새 `3ae5a38(104B)`** 실제 Phive body name getter(VT5749048, Character VT57468d8 slot0)은 body+90의 native id 하위24bit, body+88의 mode low2와 bit5를 이용해 Phive global manager+e8 월드의 body metadata 이름 table을 읽는다. metadata+18 이름 포인터의 **bit0을 제거**한다. fixture는 mode0/bit5=0이며 실제 getter 명령을 실행했다. native world의 name metadata 등록/할당 생산자는 공급 경계로 남긴다.
6. Helper+50/+58의 receiver 이름 node를 앞에서부터 비교해 **첫 동일 이름 node+58의 R 포인터**를 선택한다. 해당 body+240 count가 +244 capacity보다 작으면 body+248 pointer array에 R을 추가하고 count를1늘린다. 없는 body 이름은 추가하지 않는다. Ref 목록 중복은 중복 제거 없이 같은 R을 다시 추가한다. 매칭 receiver 이름이 없으면 null R을 추가하는 판독 경로도 있으며 이번 fixture는 각 param 이름의 receiver node를 공급했다.
7. Ref 목록이 비면 **새 `12ec970(424B)`** 전체 순회와 **새 `1e45a64(560B)`**, VT55ea578 slot0가 동일 receiver R을 **모든 body**에 용량 한도까지 추가한다.
8. 기존 `1a860f0` 실제 Receiver 생성자를 이 새 바인딩 시험에 연결했다. Name은 R+d0, DamageRateInfoCol은 R+128에 복사된다. 바인딩된 R 포인터를 몸체별 consumer `12d4adc`가 사용한다는 기존 판독과 이어진다. 새로운 데미지 계산 재실행으로 계상하지 않는다.

#### 실제 데이터와 실행 결과

읽은 원본 데이터:
- `extracted/params/Component/GameParameterTable/SplPlayer.game__GameParameterTable.bgyml.json`의 GameParameters/spl__DamageParam/DamageReceiverArray.
- `extracted/actor/SplPlayer/Phive/ControllerSetParam/SplPlayer.phive__ControllerSetParam.bgyml.json`: Body 직접 몸체1개, Main controller와 ColBullet/Chariot/CoopZombie entity 목록.
- `extracted/actor/SplPlayer/Phive/RigidBodyControllerEntityParam/SplPlayer_ColBullet.phive__RigidBodyControllerEntityParam.bgyml.json`: 유닛3개의 순서/이름.

| 실제 fixture 몸체 | 실제 바인딩 receiver | ctor에서 확인한 rate column |
|---|---|---|
| Body | Main | Default |
| ColBullet | Main | Default |
| ColBullet_Chariot | Chariot | Chariot |
| ColBullet_CoopZombie | Main | Default |

`PY web/tools/r8_camweapon_ref_rigid_binding_emu.py` 최종 결과: 실제 데이터1 + 랜덤1,024 = **1,025건, mismatch0**. 원본 name getter20,433회, iterator5,922회. null virtual calls0/auto pages0/faults0/PLT stubs0. 랜덤에서는 몸체0..7, receiver0..4, 문자열 exact case/UTF-8/동명, Ref empty·중복·unknown, 초기 목록 항목과 capacity0..8, direct/controller 분할을 비교했다. 단순 이름 결합이므로 재구현의 정확 포인터 목록/개수를 대조했다.

**경계**: 원본 Param/Receiver factory/ctor 실행 뒤 이름/ref array 및 Helper receiver-name nodes, Physics body 목록과 native metadata name table은 공급한다. 전체 actor live-load/world name registration을 실행한 것은 아니다. 실제 original callback stub은 사용하지 않았다. flags TargetedByBombRobot 등의 다른 행위는 이번 시험 대상이 아니며 factory 기본 empty 그대로다. Chariot·Coop 실제 게임 동작은 범위 밖이므로 이름 연결 데이터 외 실행하지 않았다. 비컨 기존 데이터 예시를 새 다른 무기 동작으로 확장하지 않았다.

#### 명령과 실패 기록

1. `rg -n 'RefRigidBody|KnockBackHelper|1a82330|1e3d69c|BodyArray|body lookup' analysis/notes/SHARED.md analysis/notes/FUNCS.tsv web/docs/combat web/docs/physics web/docs/player` — 기존 reflection/holder/constructor 근거 확인.
2. `decomp_index.py --no-build 1e3d69c/12ec7c0/12ec970/12ee210/3ae5a38/1a82234/38a94fc`와 `func_lookup.py 71012ec7c0 71012ec970`, 각각 71012ee210/3ae5a38/1a82234/38a94fc — init 기존 decomp 재사용, 새 함수 시작/크기 확인.
3. `sh web/tools/full_decomp.sh analysis/decomp/r8_camweapon/ref_rigid_binder.c 71012ec7c0 71012ec970` — 성공2함수.
4. `sh web/tools/full_decomp.sh analysis/decomp/r8_camweapon/ref_rigid_lookup.c 71012ee210 7103ae5a38` — 성공2함수.
5. `sh web/tools/full_decomp.sh analysis/decomp/r8_camweapon/ref_rigid_factory.c 7101a82234 71038a94fc 7101e45a64` — 성공3함수. 1e45a64 앞부분이 생성자의 destructor라는 다른주소를 혼동하지 않았고 실제 VT55ea578 slot0에서 entry를 확인했다.
6. 초기 실행 — 실패: 수동 Ref array의 VT가0이어서 count getter가 null call→0으로 읽혔고 모든 몸체에 두 receiver가 붙었다. 원본 factory1a82234와 기존1a7cd84로 변경 후 성공1,025 mismatch0/null0.
7. controller 구조 확장 후 재실행 — 성공1,025 mismatch0, 실제 Body 직접1/controller 유닛3.
8. 기존 original1a860f0 Receiver ctor를 연결해 Name/RateColumn까지 확인한 최종 실행 — 성공1,025 mismatch0, null/auto/fault/PLTstub0. 최종 JSON만 현재 정규 결과로 둔다.
9. 읽기 실패: CP949 stdout의 em-dash UnicodeEncodeError는 PYTHONIOENCODING=utf-8로 해결. JSON에 root wrapper가 있다고 읽어 KeyError('root')→실제 GameParameters 루트 수정. 미존재 Component/Physics·PhysicsParam directory rg os2→실제 extracted/actor/SplPlayer paths로 수정. Windows wildcard path rg os123→directory와 -g 사용. 광역 analysis JSON rg는 거대 packed index one-line로 출력이 잘렸으며 이후 고정 원본 파일만 읽었다.

#### 웹 반영 필요/잔여

`impl/weapon.md`, `impl/range.md`, `impl/combat.md`: 리시버를 actor 하나에 붙이는 방식은 몸체별 name→R 배열로 바꿔야 하며, empty=all/unknown skip/duplicate append/last body vs first receiver/capacity 순서를 반영한다. 구현 코드는 바꾸지 않았다.

다음 확인: `1e3d69c` 전체 actor component init→Helper+1f8 Physics producer, native `3ae5a38`의 name metadata allocation/registration producer. 현재 질문의 연결식은 위 구간으로 직접 답했으나 전체 actor load를 실행했다고 표기하지 않는다. 원문에서 Chariot 실제 행동/비컨 행위를 새 범위로 요구한다면 그것은 이번 범위 밖으로 구분하되 분모를 임의로 줄이지 않는다.


## 5.1 폭발(Blast) 데미지 기본 규칙 [판독, 실행 검증 없음] (보조 조사 중간 결과)

`spl::BulletBlast`(vtable `0x710559b3f8`) 슬롯22 OnHit `0x71016586c4`. 디컴파일 `analysis/decomp/combat4/blast_1~3.c`, 정리본 `analysis/combat4/blast_onhit_clean.c`.

- 파라미터 배치(`spl::BulletBlastParam`): DistanceDamage 배열 +0x30(원소 Damage s32 +0x30, Distance f32 +0x34, 부모 배열 원소가 먼저), PlaneDamage 배열 +0x60, KnockBackParam 포인터 +0x58(Accel +0x30, Bias +0x34, DirectionZeroAccelRate +0x38, Distance +0x3c), DamageLinear +0xe2.
- 중심: 시작 `0x7101653aa0`에서 생성정보+0x30 + DamageOffsetY×up(+0x80) (생성정보+0x99면 오프셋 없음). 판정 구 반경 = max(0.05, S·최대 Distance, CollisionRadiusForPaint) → 바디 vt+0xd8. 레이어 FriendThrough, 마스크 ExceptGround.
- 거리 d = 탄 위치(`0x710164434c`) → 상대 강체 기준점(기준점 정체 [추정]).
- 거리→데미지 `0x710165c6ec`: S = 생성정보+0xa4 × SpecUp(DistanceDamageDistanceRate). lo = S·Dist ≤ d 중 최대, hi = S·Dist ≥ d 중 최소. hi 없음 → 0, lo 없음 → Damage[hi], 같은 Distance → Damage[lo], DamageLinear 거짓 → Damage[hi] (계단), 참 → 선형 보간 후 0 방향 절삭. 블래스터(700/0.94, 500/3.3, S=1) 예: d 0→700, 2→610, 3.3→500, 4→0 [재구현 계산].
- PlaneDamage: up축 부호 있는 높이 h로 같은 조회(음수는 크기), 최종 = min(거리, 평면), 범위 밖 0. 그 뒤 info.damage = int(생성정보+0xa0 × 데미지). 0이면 리시버로 보내지 않음. ExtraInfo = 생성정보+0xa8(2→4, 6→6, 9→10, 그 밖→3).
- 넉백 `0x7101e665d0`: t = clamp01(d/(S·KB.Distance)), f = t^(−log2 Bias), 크기 = Accel×(1−f), 방향 중심→대상, 수직 성분 제거.
- **차폐(시야 레이캐스트)는 OnHit 안에서 찾지 못함 [미확정]**. DamageAttackerPriority 의미(읽는 곳 슬롯65 `0x71016581cc`), 생성정보 +0xa0/+0xa4/+0xa8 출처, DamageRateInfo 행 [미확정].

## 5.2 플레이어가 받은 넉백의 효과 [판독 일부] (보조 조사 중간 결과)

- 리스너 `0x71024632ec`: 크기 = |kb|×(1/3600), ×8.0 조건(`0x71024635a0`~`0x710246369c`) = 피해자가 특수 0x1a(Chariot) 사용 중 & 본체+0x268(접지 프레임) > 0 & 상태 ∈ {0x82~0x90, 0xaa~0xac, 0xed, 0xee, 0x10c} & 레퍼리가 `VersusRefereeVLift`(야구라)이고 `0x7103055514` 값 == 본체+0x368(야구라 탑승 [추정]), 그 뒤 0.48로 자름.
- `0x71024c8318`: v×3600을 메시지로 [[본체+8]+0x510]+0x20 vt+0x10에 송신(+0x58 = 모드0이면 1, +0x5c/+0x60 = 1.0, +0x6d = 0). SuperLanding(0x1c)·본체+0xa5f4/+0xa5f8·[본체+0xa6c0]+0x2658이면 보내지 않음.
- 수신(Phive 쪽, 0x9a0 B 객체 vt `0x7105576e50`): `0x71012ad75c`가 ImpactAndReject 데이터 D의 충격 가속 D+0x08 = normalize(기존+새)×max(|새|,|기존|), D+0x18/+0x1c = max(·,1.0). 매 스텝 `0x71012adb58`: vel += dt·D+0x08, 감쇠 f = 1 − dt/D+0x18(1.0초) → **약 60프레임 선형 감소 [추정]**.
- 게임 쪽 이동 `0x710245b2b4`(`0x710245d698`~`0x710245d814`)의 외력 K(본체+0x16c): |K| ≤ 0.002면 0, 아니면 스틱 방향(본체+0xd30, 크기 m 본체+0xd3c)과의 내적 t로 f = 0.9 + (t≥0 ? t·0.04 : −t·(−0.7)), K *= f, 이동 속도 += K. 카운터 본체+0x168 > 0 && K ≠ 0이면 desired를 0x7101252ff0(t = 카운터/25, 방향×0.03)로 보간(입력 억제 [추정]), 카운터는 `0x710245aed8`에서 매 프레임 −1. **K·카운터 writer, 두 경로(Phive 충격 가속 vs K)의 관계, 애니·카메라 효과는 [미확정]** — 다음 단서 `0x710245cca8`, `0x710245cd28`, `0x710246dfac`.

### 5.3 넉백 메시지의 수신·합성·감쇠 [판독 + 실행] (2026-10-03 [r8 combat])

§5.2의 “약 60프레임 선형 감소 [추정]”는 아래 조건부 계산·원본 실행으로 정정합니다. 기존 기록은 비교를 위해 보존합니다. 메시지 저장 `0x71012eb378`과 실제 큐 소비 `0x71012eb680`은 **별개 함수**입니다. 첫 디컴파일에서 `0x71012eb710`을 앞 함수의 내부로 잘못 찾은 것은 `func_lookup.py 12eb680`로 정정했습니다(시작 `0x71012eb680`, 1,052 B).

- 생성 `0x71012a95f0`은 D+0x14에 **NaN(0x7fc00000)** 을 씁니다(`0x71012a9708`의 64비트 저장 상위 절반). D는 ImpactAndReject+0x28이며 D+0은 ApplyVelocity 컴포넌트를 가리킵니다. `0x71012ad2c8`은 이 포인터가 없을 때 `CharacterUpdateApplyVelocity`를 이름·타입으로 찾습니다.
- 큐 소비 `0x71012eb680`은 각 메시지 M의 **M+0x40 vec3, M+0x5c/0x60 f32, M+0x58 u32, M+0x6d byte**를 `0x71012ad75c(D, vec, kind, reject; s0=time, s1=holdTime)`에 전달합니다. `0x71024c8318`의 플레이어 넉백 메시지는 vec = v×3600, 두 시간 = 1.0, reject = 0이므로 D+8 충격 경로입니다.
- 수신: 새 벡터가 모두 0이면 **시간도 갱신하지 않습니다**. reject가 0이면 A=D+8, 1이면 A=D+0x24를 선택합니다. `m=sqrt(max(|A|²,|new|²)); A+=new; |A|>0이면 A*=m/|A|`. 따라서 정확히 반대인 두 벡터가 합쳐져 0이면 0으로 남습니다. D+0x18와 +0x1c는 각각 기존/새 시간의 최대, kind 0~3은 D+0x30+4×kind, 범위 밖은 +0x30 하나를 늘립니다. +0x1c>0이면 +0x20=1.
- 갱신 `0x71012adb58`은 속도에 **감쇠 전** `dt×impact`와 `dt×reject`를 더합니다. 모드가 1이고 하위 이동 상태가 0이면 impact 추가를 생략, 상태 1이면 impact의 up 성분을 제거합니다. D+0x20>0 && +0x18>0에서 입력 속도가 충격의 수평 방향과 반대이면 그 반대 성분을 D+0x20 비율만큼 제거합니다. 위치 보정 `(D+0x4c+D+0x58)/dt`도 속도와 ApplyVelocity+0x40에 더합니다.
- **D+0x14가 NaN**: 남은 시간 T=D+0x18>0이면 두 가속도에 `max(1−dt/T,0)`을 곱하고, T≤0이면 두 벡터를 0으로 합니다. **유한한 D+0x14**: 두 벡터에 그 배율을 곱하고 각각 크기²<1e−4이면 0으로 합니다. 이 경로에는 T로 나누는 선형 감쇠가 없습니다. 이후 +0x18/+0x1c/+0x30~0x3c 시간 여섯 개를 `max(T−dt,0)`으로 감소합니다. 보정 벡터 두 개는 소모 후 0, 합은 +0x40에 저장합니다.
- 새 `r8_combat_impact_emu.py`: 원본 `0x71012ad75c` **1,400건**, `0x71012adb58` **2,264건**, 독립 f32 계산과 벡터·시간·감쇠·보정 필드 비트 대조 **불일치 0**. 합성 주변 객체를 사용했으며 전체 Havok 프레임은 실행하지 않았습니다. 마지막 strength 감소의 런타임 상수 `0x7105826ce0`은 입력 1.0을 공급했으므로 실제 사격장 값의 근거가 아닙니다. 모드별 상향 투영 분기는 판독 수준입니다.

원본 실행에서 T=1.0, dt=f32(1/60), impact=(0,0,280), D+0x14=NaN을 매 스텝 이어 넣으면 60번째 갱신 뒤 T=**2.7939677238464355e−7**, impact.z=**7.816286233719438e−5**가 남고 **61번째**에 둘 다 0이 됩니다. 60/61번째 속도 추가는 각각 0.07777908444404602 / 1.3027143950239406e−6 유닛/초입니다. 60번째에 정수 타이머로 강제 종료하면 원본과 다릅니다. 결과: `analysis/completion/r8/combat_impact_emu.json`.

**남은 경계 [미확정]**: 외력 K(본체+0x16c)의 writer·D와의 관계, 실제 접촉 솔버 이후 이동 합성 전체, 넉백의 애니·카메라 연결. §5.2와 §6의 이 복합 항목들은 이번 리프 실행만으로 전체 확정하지 않습니다. 웹 반영 필요: 충격 합성의 최대 크기·상쇄, 감쇠 전 속도 추가, f32 남은 시간·NaN/유한 분기, 61번째 잔량을 유지해야 합니다(`impl/physics.md`, `impl/combat.md`; 구현 문서는 수정하지 않음).

### 5.3.1 게임 송신부터 원본 큐·컴포넌트 바인딩까지 (2026-10-03 추가)

새 [knockback_pipeline.md](knockback_pipeline.md) §3–10에서 `24c8318→12eb378→12d53f8→12eb680→12ad75c→12adb58` 및 실제Impact생성/바인딩을1,024건 원본실행했다(28,672 f32, 불일치0). **§5.3의 5826CE0=1.0은 합성입력 검증범위이며, 실제 생성기본은 신규12ad660 원본store로30.0**임을정정한다. 60.0/30.0 메시지기본시간과 실제리스너1.0초override도구분한다. 전체솔버/K/연출 composite는계속미확정.

## 6. 미확정과 다음에 볼 곳

| 항목 | 다음 근거 |
|---|---|
| 탄·ColBullet 바디의 F+0x30 값(팀 번호인지) → 아군 충돌 여부 확정 | r5: ColBullet = 액터 팀 + 1 **[판독]**(리스폰 리셋 `0x71024f4ccc`, 코옵 좀비면 2), 호출자 11곳 전수(§3 표). **탄 바디 writer [미확정]** — Phive 탄 바디(vt `0x7105749990`) +0x180 필터 생성 `0x7103b09ee4`/`0x7103a62e78`, 설명자 `0x71010036a8` |
| 형태(인간/오징어/잠복)별 피격 형상 변화 | r5: 데이터 피격 캡슐 1개 [데이터], 바디 활성 비트11 setter의 플레이어 쪽 호출자 27곳 목록화(§2) — 형태와의 관계 [미확정]. 남은 것: PlayerCollision 슬롯13 `0x71024f4270`·48 `0x71024fc228`·73 `0x71024fc7e8`의 호출 시점, 비트11 소비처, 기존 디컴파일 슬롯(`0x71024f4994`, `0x71024f4a44`, `0x71024f4878`, `0x71024fbb7c` — `c4_batch1.c`) |
| 프레임 안 순서(첫 명중 age 0/−1) | r5 해소: 이동 접촉 첫 명중 age 0 [판독] — [r5 physics] 프레임 순서, §1. 생성 겹침 접촉의 age만 [미확정] (데미지 동일) |
| 송신자 클래스별 이력 모드 | 탄 바디+0x150에 들어가는 객체의 vtable(`0x7101e3d69c`가 DamageSenderArray로 만드는 클래스) |
| 히트 이펙트·히트마커 조건 | r5 해소: 히트 이펙트는 결과 ≠ 0일 때만(damage_hit §3.2) [판독], 조준 히트마커 = 궤적 예측 + 리시버 팀별 플래그(damage_hit §6.7) [판독 + 플래그 실행]. 남은 것: 이펙트 이벤트 소비 `0x71027b4704`, 크리티컬 행 선택 |
| Blast 차폐·DamageAttackerPriority, 넉백 writer·카메라·애니 효과 | §5.1·§5.2 끝의 단서. 원본 실행 대조 없음 |

### 6.1 6차 갱신 (2026-10-03 [r6 combat])

| 항목 | 상태 | 근거 / 다음 |
|---|---|---|
| 탄 바디 F+0x30 값 → 아군 충돌 | **[실행] 해소** | §3 정정: 슬롯9 `0x71013405e0`이 팀+1(0일 때만), 쌍 판정 `0x7103c55ed8`→`0x7103c34e14`. 슈터 탄(레이어 8)은 같은 팀에도 막힘. 남은 것: 탄 F+0x1c 기본값, 풀 재사용 때 다른 팀으로 바뀌는 경우(리셋 없음) |
| 송신자 클래스별 이력 모드 | **[판독] 해소** | §4: 슈터 = 모드 0, 클래스별 52개 표. 남은 것: 기본 핸들 *[`0x7105797f20`] id |
| 형태별 피격 형상 | [미확정] | PlayerCollision 슬롯13 `0x71024f4270`(리셋: `0x71024f4440`(…,1), +0x50 바디 비트11 = 1, GameInAir +0x14 = 2), 슬롯48 `0x71024fc228` = `0x7103ae24a4`(바디, 상수 `0x7104a981f4`) 뒤 비트11 = 0, 슬롯73 `0x71024fc7e8` = 해제(free) [판독, `analysis/decomp/r6_combat/c1.c`]. 비트11 소비처 후보 `0x7103af11a4`(`tbnz #0xb`), `0x7103af13c0`, `0x7103af1ee8`, `0x7103af20f0`, `0x7103ae4f74`, `0x7103ae5714` — 미판독 |
| 생성 겹침 첫 명중 age | [미확정] | 6차 미착수. 다음: 풀 생성 `0x7100f7f6a4` → 활성화 이벤트 0xef(`0x7103c7ea60`)가 실행되는 프레임 단계 |

### 6.2 슈터 명중 이펙트·예측 마커 조건 — 2026-10-03 정정 [판독]+[데이터]+[실행]

위 §6의 소비/크리티컬 행 미확정과 고정 r7 L98의 show/predict·단계 수 질문을 [hit_effect_pipeline.md](hit_effect_pipeline.md) §3–10으로 정정한다. 실제 Shooter VT5637898+60=2586AA0/ShotGuideFrameP64와 명중 요청→큐→프레임 소비→S1/E1/S2/E2를 연결했다. 신규876+512 표시/단계,1024+2688 요청/paint,5880 소비/140 큐/5FIFO/16거리 케이스 모두일치. 기존 r5 예측/flag12000과 r6 critical행은 재사용을 명시했다. fullGPU/오디오·유효ActorRef/그룹·지연전체는 별도미확정으로보존한다. 예측마커와실제명중이펙트를합치지않는다.

**2026-10-03 r8 정정:** §6의 형태별피격형상/후보 함수 미확정은 §2.1의 새 원본 전체함수→native shape 연결과 §3.1 native bit11 소비로 해소했다. 실제 부착 body 갱신·솔버의 별도 미확정은 유지한다.
