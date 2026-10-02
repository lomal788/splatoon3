# 피격 판정 형상·리시버 분배·탄 age 시작값 (combat4)

Splatoon 3 v0 원본에서 **탄이 플레이어·오브젝트에 "닿았다"고 판정되는 형상과, 닿은 뒤 어느 리시버로 데미지가 가는지**를 정리합니다. 데미지 값·배율은 [damage_hit.md](damage_hit.md), HP·아머·리스폰은 [player_life.md](player_life.md)에 있습니다.

- 작업 지침 [../../분석.txt](../../분석.txt). 확정 수준 **[실행] [판독] [데이터] [추정] [미확정]**.
- 상태: **분석 일부 완료(4차, 2026-10-02 중간 마감)**. 웹 구현 없음. 남은 것은 §6.
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

**첫 명중 age [추정]**: [move] 문서의 "슬롯18 → 물리 스텝 → 슬롯19" 순서를 따르고 접촉 반응 시퀀서(탄 슬롯22)가 물리 뒤·다음 슬롯18 앞이면, 이동으로 생긴 첫 접촉은 **age 0**(첫 갱신의 물리 스텝)입니다. 생성 위치가 처음부터 겹친 경우 첫 슬롯18 전에 물리 스텝이 돌면 age −1입니다(감쇠 결과는 같음). 프레임 안 순서는 [phys4]에 요청함(SHARED).

## 2. 플레이어 피격 형상 [데이터] + 결속 [판독 일부]

`extracted/actor/SplPlayer/Phive/`:

| 바디(RigidBody) | 형상 | LayerEntity / 히트 마스크 | 쓰임 |
|---|---|---|---|
| `ColBullet` | 캡슐 A(0, 0.35, 0) B(0, 1.30, 0), r **0.35** (발밑 원점 기준, 높이 0~1.65) | `SplPlayer` / `SplPlayerSensor`(CustomReceiver, GameCustomReceiver, SplInkBullet, SplInkBullet_FriendThrough, SplSubstanceBullet_HitOpposite/_HitBullet, SplRollerBody, SplBlowerInhale, SplBluntWeapon, SplInkTornado, SplGreatBarrier, SplSaberBombGuard, SplItem) | **탄 피격 판정**. Kinematic, 액터 행렬 결속(`BoneBindModePosition All`, 추적 뼈 없음, `WarpMode AfterUpdateWorldMtx`), 리셋 때 월드에 추가 |
| `ColBullet_Chariot` | 구(캡슐 A=B) 중심 (0, 0.4, 0), r 1.15 | `SplPlayerChariotShield` / `SplChariotColBullet` | 스페셜 Chariot(게살 탱크 추정) 중. 리셋 때 추가하지 않음 |
| `ColBullet_CoopZombie` | 구 중심 원점 r 0.8 | `SplObject` / `SplPlayerSensorCoopZombie` | 코옵 좀비 |
| (캐릭터 컨트롤러 `SplPlayer_cct`) | `ColGround` 캡슐 (0,0,0)-(0,0.7,0) r 0.6, `ColOthers` (0,−0.21,0)-(0,0.51,0) r 0.39 | 이동·지형용 | 피격과 무관 |

- `spl:PlayerCollision`(vtable `0x7105633ec0`, 본체+0xa690) 초기화 `0x71024f2e5c`가 +0x48 = `ColBullet`, +0x50 = 표[1] 이름 바디(`ColBullet_CoopZombie`로 추정), +0x58 = `ColBullet_Chariot` 바디를 잡습니다 **[판독]**.
- **인간/오징어/잠복 차이**: 데이터의 피격 캡슐은 하나뿐이고, 형태별로 형상·크기를 바꾸는 코드는 이번에 찾지 못했습니다 **[미확정]**. `0x7103ae4c48(바디, bool)`이 +0x48/+0x50 바디에 리스폰 리셋(1)·리스폰 후 타이머 종료(0)·SuperHook 공격 상태 진입(0, `0x71024b3efc`)에서 불립니다 — 바디 활성/비활성 계열로 보이나 의미 **[미확정]**(`0x7103ae4c48` 디컴파일: `c4_batch1.c`).
- 탄 쪽: `ExceptGround` 구(반경 = `InitRadiusForPlayer`→`EndRadiusForPlayer`, damage_hit §6.2)와 이 캡슐의 접촉. 판정식은 Havok 좁은 단계라 판독하지 않았습니다. 웹은 **선분(쓸어 넘긴 탄 중심 p0→p1)과 캡슐 축 사이 거리 ≤ r_bullet + 0.35** 로 근사합니다 **[추정]**(막는 접촉 중 최소 비율 f에서 정지 — [physics §6.4](../physics/phive_controller.md)).

## 3. 같은 팀 통과 — 필터 그룹 [판독 일부], 표 선택 [미확정]

- 탄 시작 `0x71016455d0`~`0x71016455fc`: 생성정보+0x18 바이트가 참이면 래퍼 슬롯5 `0x71016cafc0`({u32 생성정보+0x10, u8 생성정보+0x14})로 모든 유닛 바디의 필터 객체 F(= 바디 vt+0x38 = 바디+0x138)에 **F+0x14 = 그룹 id, F+8 비트12 = 그룹 사용**을 씁니다 **[판독]**. F+8 비트0~5 = 레이어, 6~11 = 하위 레이어 **[판독]**.
- **표 선택 규칙 [판독]** (보조 조사, `analysis/decomp/combat4/filter_1.c`·`filter_2.c`): 표 변환 `0x7103b16ad8`이 층(레이어) 행마다 마스크 둘을 만듭니다 — mask0 = 값 1 또는 2, mask1 = 값 2. 백엔드(`CollisionFilterBackEnd`, 생성 `0x7103b1ab5c`, 0x310 B, 복사 `0x7103b1ae90`)에 Default/Same/Other × mask0/mask1이 층당 u32로 들어갑니다. 쌍 판정 `0x7103af44e8(A,B)`는 두 바디의 필터 객체 **F+0x30(u16)** 을 봅니다: 하나라도 0 → Default, 둘 다 0이 아니고 같음 → Same, 다름 → Other(`0x7103af4518`/`0x7103af4520`/`0x7103af4610`). 그 표의 A층 행에서 B층 비트를 검사하고, 최종 판정(`0x7103c4dd30` 등 4곳)은 (A,B)·(B,A) 양쪽과 F+0x18(층)·F+0x1c(하위 층) 마스크를 모두 통과해야 충돌입니다.
- 따라서 Same/Other를 가르는 값은 위 F+0x14/비트12가 아니라 **F+0x30**이고, 그 setter는 `0x7103ae53f0(바디, u16)`(대기 버퍼 +0xc0, 적용 `0x7103b084d4`)입니다. 게임 코드에서 누가 ColBullet·탄 바디에 어떤 값(팀 번호 추정)을 넣는지는 **[미확정]** — 다음 단서: `0x7103ae53f0` 호출자. F+0x14/비트12의 용도와 생성정보 +0x10/+0x14/+0x18의 출처도 미확정.
- `0x7103ae4c48(바디, bool)`은 그룹 setter가 아니라 바디+0x88 비트11(0x800)을 켜고 끄는 함수입니다(대기 +0xd0 비트0, 적용 `0x7103b08540`~`0x7103b08564`) **[판독]**, 비트 의미 **[미확정]**.
- **구현에 중요한 관찰 [데이터]+[추정]**: 슈터 데이터는 `FriendThroughFrameForPlayer = 0`을 명시하고(`WeaponShooter*`; 미션·Rival 적 슈터만 4), FTF 0이면 시작에서 레이어 8(`SplInkBullet`)이 됩니다(§4.8 판독). `SplInkBullet × SplPlayer`는 **세 표(Default/Same/Other) 모두 2(충돌)** 이고 위 쌍 판정은 어느 표를 고르든 이 칸을 보므로(F+0x18/+0x1c 마스크가 막지 않는다면) **슈터 탄은 같은 팀 플레이어 캡슐에도 물리적으로 막힙니다** — 리시버 결과는 Through·데미지 0이고 슬롯60이 `+0x12a = 1`(다음 슬롯21에서 소멸)을 겁니다. FriendThrough(9)는 Same 표에서만 0입니다. 그룹·표 선택이 확정되기 전까지 웹은 "슈터 탄은 아군에 막혀 소멸, 데미지 0"으로 두고 **[추정]** 표시를 유지하세요.

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
- 탄의 송신자(이력 모드 vt+0x20 등을 가진 객체)는 탄 바디+0x150입니다. 슈터 탄 GPT `BulletShooterBase`의 `DamageSenderArray = [{Name "Main", RefRigidBody []}]`. 그 송신자 클래스의 모드 값은 **[미확정]**(생성 함수 후보 `0x7101e3d69c`, `analysis/decomp/life/batch1.c`).

## 5. 웹 구현 요약

1. 탄 age: 시작 −1, 갱신마다 +1(이동 전). 슬롯54: age 0이면 속도 그대로, age 1이면 생성 속력으로 재정규화.
2. 플레이어 피격 캡슐: 발밑 기준 y 0.35~1.30, r 0.35, 형태 무관(미확정 표시). 탄 구 반경과 더해 선분-캡슐 거리로 판정, 최소 비율 접촉에서 정지.
3. 리시버는 바디별 목록, 결과 최댓값. 아군 통과는 §3 [추정]대로.

## 5.1 폭발(Blast) 데미지 기본 규칙 [판독, 실행 검증 없음] (보조 조사 중간 결과)

`spl::BulletBlast`(vtable `0x710559b3f8`) 슬롯22 OnHit `0x71016586c4`. 디컴파일 `analysis/decomp/combat4/blast_1~3.c`, 정리본 `analysis/combat4/blast_onhit_clean.c`.

- 파라미터 배치(`spl::BulletBlastParam`): DistanceDamage 배열 +0x30(원소 Damage s32 +0x30, Distance f32 +0x34, 부모 배열 원소가 먼저), PlaneDamage 배열 +0x60, KnockBackParam 포인터 +0x58(Accel +0x30, Bias +0x34, DirectionZeroAccelRate +0x38, Distance +0x3c), DamageLinear +0xe2.
- 중심: 시작 `0x7101653aa0`에서 생성정보+0x30 + DamageOffsetY×up(+0x80) (생성정보+0x99면 오프셋 없음). 판정 구 반경 = max(0.05, S·최대 Distance, CollisionRadiusForPaint) → 바디 vt+0xd8. 레이어 FriendThrough, 마스크 ExceptGround.
- 거리 d = 탄 위치(`0x710164434c`) → 상대 강체 기준점(기준점 정체 [추정]).
- 거리→데미지 `0x710165c6ec`: S = 생성정보+0xa4 × SpecUp(DistanceDamageDistanceRate). lo = S·Dist ≤ d 중 최대, hi = S·Dist ≥ d 중 최소. hi 없음 → 0, lo 없음 → Damage[hi], 같은 Distance → Damage[lo], DamageLinear 거짓 → Damage[hi](계단), 참 → 선형 보간 후 0 방향 절삭. 블래스터(700/0.94, 500/3.3, S=1) 예: d 0→700, 2→610, 3.3→500, 4→0 [재구현 계산].
- PlaneDamage: up축 부호 있는 높이 h로 같은 조회(음수는 크기), 최종 = min(거리, 평면), 범위 밖 0. 그 뒤 info.damage = int(생성정보+0xa0 × 데미지). 0이면 리시버로 보내지 않음. ExtraInfo = 생성정보+0xa8(2→4, 6→6, 9→10, 그 밖→3).
- 넉백 `0x7101e665d0`: t = clamp01(d/(S·KB.Distance)), f = t^(−log2 Bias), 크기 = Accel×(1−f), 방향 중심→대상, 수직 성분 제거.
- **차폐(시야 레이캐스트)는 OnHit 안에서 찾지 못함 [미확정]**. DamageAttackerPriority 의미(읽는 곳 슬롯65 `0x71016581cc`), 생성정보 +0xa0/+0xa4/+0xa8 출처, DamageRateInfo 행 [미확정].

## 5.2 플레이어가 받은 넉백의 효과 [판독 일부] (보조 조사 중간 결과)

- 리스너 `0x71024632ec`: 크기 = |kb|×(1/3600), ×8.0 조건(`0x71024635a0`~`0x710246369c`) = 피해자가 특수 0x1a(Chariot) 사용 중 & 본체+0x268(접지 프레임) > 0 & 상태 ∈ {0x82~0x90, 0xaa~0xac, 0xed, 0xee, 0x10c} & 레퍼리가 `VersusRefereeVLift`(야구라)이고 `0x7103055514` 값 == 본체+0x368(야구라 탑승 [추정]), 그 뒤 0.48로 자름.
- `0x71024c8318`: v×3600을 메시지로 [[본체+8]+0x510]+0x20 vt+0x10에 송신(+0x58 = 모드0이면 1, +0x5c/+0x60 = 1.0, +0x6d = 0). SuperLanding(0x1c)·본체+0xa5f4/+0xa5f8·[본체+0xa6c0]+0x2658이면 보내지 않음.
- 수신(Phive 쪽, 0x9a0 B 객체 vt `0x7105576e50`): `0x71012ad75c`가 ImpactAndReject 데이터 D의 충격 가속 D+0x08 = normalize(기존+새)×max(|새|,|기존|), D+0x18/+0x1c = max(·,1.0). 매 스텝 `0x71012adb58`: vel += dt·D+0x08, 감쇠 f = 1 − dt/D+0x18(1.0초) → **약 60프레임 선형 감소 [추정]**.
- 게임 쪽 이동 `0x710245b2b4`(`0x710245d698`~`0x710245d814`)의 외력 K(본체+0x16c): |K| ≤ 0.002면 0, 아니면 스틱 방향(본체+0xd30, 크기 m 본체+0xd3c)과의 내적 t로 f = 0.9 + (t≥0 ? t·0.04 : −t·(−0.7)), K *= f, 이동 속도 += K. 카운터 본체+0x168 > 0 && K ≠ 0이면 desired를 0x7101252ff0(t = 카운터/25, 방향×0.03)로 보간(입력 억제 [추정]), 카운터는 `0x710245aed8`에서 매 프레임 −1. **K·카운터 writer, 두 경로(Phive 충격 가속 vs K)의 관계, 애니·카메라 효과는 [미확정]** — 다음 단서 `0x710245cca8`, `0x710245cd28`, `0x710246dfac`.

## 6. 미확정과 다음에 볼 곳

| 항목 | 다음 근거 |
|---|---|
| 탄·ColBullet 바디의 F+0x30 값(팀 번호인지) → 아군 충돌 여부 확정 | `0x7103ae53f0` 호출자, 탄 바디(F = 바디+0x138)가 쌍 판정의 +0x180 경로를 타는지, 생성정보 +0x10/+0x14/+0x18 |
| 형태(인간/오징어/잠복)별 피격 형상 변화 | 바디+0x88 비트11(`0x7103ae4c48`)의 의미, PlayerCollision 슬롯(`0x71024f4994`, `0x71024f4a44`, `0x71024f4878`, `0x71024fbb7c` — `c4_batch1.c`에 디컴파일만 해 둠) |
| 프레임 안 순서(첫 명중 age 0/−1) | [phys4] 결과(SHARED 요청) |
| 송신자 클래스별 이력 모드 | 탄 바디+0x150에 들어가는 객체의 vtable(`0x7101e3d69c`가 DamageSenderArray로 만드는 클래스) |
| 히트 이펙트·히트마커 조건 | `0x71016d99f4`/`0x71016d9c60`(combat/batch1·2.c) — 이번에 보지 못함 |
| Blast 차폐·DamageAttackerPriority, 넉백 writer·카메라·애니 효과 | §5.1·§5.2 끝의 단서. 원본 실행 대조 없음 |
