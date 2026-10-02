# [physics] 플레이어 이동·충돌 구현 기록

담당 폴더: `games/splatoon3/core/collision/`, `games/splatoon3/core/player/`. 목표: 시험 사격장(대전 로비 `Lby_Lobby00`) 1인 연습에서 원본과 같은 이동.
근거 문서: `docs/player/movement_physics.md`, `player_state.md`, `gear_skills.md`, `docs/physics/phive_controller.md`, `docs/gimmick/collision_mesh.md`, `docs/combat/player_life.md`(리스폰만), `docs/paint/paint_and_score.md`(발밑 잉크).

확정 수준 표기는 분석 문서와 같다: [판독] [데이터] [실행(에뮬)] [추정] [미확정]. "근사"는 원본 엔진 내부라 같은 의미를 다른 방법으로 낸 곳.

---

## 1. 구현한 것

### 1.1 충돌 세계 `core/collision/`

| 파일 | 내용 |
|---|---|
| `geom.ts` | 점·선분-삼각형 최근접점, 레이-삼각형(Möller–Trumbore), 면 법선. f64 계산 |
| `mesh.ts` | `TriMesh`: 삼각형 BVH(잎 4, 중심값 분할), `raycast`, `sweepSegment`(선분+반경 = 구/캡슐을 보수적 전진으로 쓸어 넘김), `overlapSegment`(겹침 깊이·법선) |
| `filter.ts` | Phive 레이어 히트 마스크 이름→값([데이터] PhiveConfig), 원시 필터 → 웹 `Layer` 비트 |
| `world.ts` | `MeshCollisionWorld implements CollisionWorld`(raycast / sweepSphere / setDynamic / materialName), 플레이어 몸 질의(`sweepBody`, `overlapBody`, `bodyFilter`), 데이터 읽기 `loadCollision`, 기본 도형 다면체화, 대체 평면 |
| `index.ts` | `createCollisionSystem` — init 에서 `world.collision` 설정. 에셋이 없거나 읽기 실패면 y=0 평면(±500)과 `console.warn` |

**충돌 데이터** (`world.data.collision = { meta: collision.json, bin }`, 에셋 담당 형식에 맞춤):
- `meta.layout.{positions(f32x3, count=정점 수), indices(u32, count=인덱스 수), triMaterial(u16, count=삼각형 수)}` 의 `offset` 으로 `bin` 을 자른다(`byteLength` 가 있으면 우선).
- `meta.materials[i]`: `name`, `layer`(문자열), `paintable`, `flags.{userShapeTags[], layerHitMask, subLayerHitMask, filterRaw}`. 원시 필터(hitMask/subMask)가 있으면 플레이어 막힘 판정은 원시 필터로 한다(아래 1.2).
- `meta.primitives[]`(삼각형이 아닌 Capsule/Sphere/Cylinder, 로비 의자·캡슐 기계 13개): 경도 12·반구 4 분할 다면체로 메시에 붙인다(근사, §2).
- 재질 → 웹 `Layer` 비트: `layer` 가 `Ground/Object/Player/Water/KeepOut` 이면 그대로, 그 밖(`InkThrough`, `PlayerThrough`, `KeepOutBullet` …)은 원시 필터로 판정 — 잉크탄(레이어 8)을 막으면 `Ground`, 플레이어(레이어 5)만 막으면 `KeepOut`, 이름이 물이면 `Water`. 그래서 철망(`SplInkThrough`)은 `KeepOut`(탄 통과), `SplKeepOutBullet` 은 `Ground`(탄만 막음), `SplPlayerThrough` 는 `Ground` 이지만 플레이어는 통과.

**동적 충돌체**(`setDynamic`): 구·캡슐은 해석적 레이/쓸어 넘기기, 상자(yaw 회전)는 국소 좌표 slab(구 반경만큼 각 축을 늘린 근사). `Hit.actor` = 등록 id, 지형은 −1. 플레이어 몸은 동적 충돌체와 충돌하지 않는다(표적이 플레이어를 막는지 [미확정]).

### 1.2 플레이어 `core/player/`

| 파일 | 원본 | 내용 |
|---|---|---|
| `consts.ts` | bss 0x71058bbb60~0x71058bc260 | 상수를 **원본 비트**로(`fb(0x3c03126e)` 등). 디컴파일 십진 리터럴은 `Math.fround` |
| `gear.ts` | 0x710265df40/0x710265fd48/0x7102665ee4 | AP→p, Low/Mid/High 보간, b(x,s) 곡선, `PlayerParam`(+0xb0..+0x140) — 기본 0AP |
| `states.ts` | 상태 표 0x7105630270 | 286개 [이름, 모델, 블렌드, 플래그], 집합 S/Q |
| `state.ts` | 본체 필드 | shared `player` 객체 `PlayerState`(필드마다 본체 오프셋 주석) |
| `vertical.ts` | 0x71024a7d00, 메인 계산 점프부, 0x7102482df8, 0x7102459630, 0x710245aed8, 0x71024593e8 | 수직 속도·3D 점프, 점프 판정·대입(적 잉크 보간), 버튼 유지 가산, 벽 점프 발사, 최종 속도 합성 |
| `move.ts` | 0x710245b2b4 일반 경로, 0x710245f964, 0x7101252ff0 | 입력 전방 축(N×카메라 오른쪽), 이동 방향·m=|dir|⁴, 목표 속도(인간/오징어/적 잉크/사격 MoveSpeed/벽 점프 차지/오징어 벽 0.096), cap 갱신(0.3/0.1/0.003), 공중 상한 보간(0.04, 90/180프레임), 착지 경직, 가속량 전 분기(지상·잠복/점프·넉백·사격), 상승 보정, 공중 감쇠(f40·f33), 바닥 법선 성분 제거·공중 수평 클램프, 위쪽 가속 제한, v.y ≤ 0.168, 공중/접지 보정 |
| `body.ts` | Phive SplPlayer 캐릭터 컨트롤러 | 캡슐 쓸어 넘기기+미끄러짐 근사(§2.1) |
| `contact.ts` | 슬롯19 0x71024abcf0, 0x710246b32c, 0x710246b574, 0x710268b3b8 | 공중/접지 카운터, 착지 감속(공중 > 8), 접지 중 침투·수직 속도(오징어 벽 −0.04 하한·0.95~0.85), 측면 접촉, 천장(타이머 30), 경사·벽 미끄럼 a38/a2c, 바닥 평면 투영, 발밑 잉크 평활·분류 |
| `sm.ts` | 0x710243e7d0, 0x7102442354 일부, 0x7102447bfc/0x710244128c | 인간↔오징어 판정·전환 단계(end < cur+3), 변신 카운터 SM+0xf0, 점프·낙하·착지 상태, 지상 걷기(사분면)·대기, 상태 요청의 모델 검사 |
| `spawn.ts` | (데이터) | `placement.json` StartPos 선택 |
| `index.ts` | 프레임 흐름 | `createPlayerSystem`, 입력(InputSender 우선순위→본체+0x784), 카메라 읽기, 리스폰, 이벤트, 잉크 회복 |

**프레임 순서**(movement_physics.md §3.3·§9.3): 입력 → 수직 갱신 → 점프 판정(→ 점프 시작: +0x734=0, 0x710246b32c(1), 상태 요청, `Jump`) → 유지 가산 → +0x738 → 입력 방향 → 이동(0x710245b2b4 → 0x710245f964) → 발사 프레임 대체 → 최종 속도 합성 → vy > 0.001 이면 공중 강제 → **캐릭터 몸**(지상: F−(0,vy,0) 을 지면 평면으로, 공중: F 그대로) → 슬롯19 접촉 정리 → 발밑 잉크 → 오징어 벽 붙기 → 상태기계 → 잉크 회복 → 낙하 판정.

**시작 위치**: `Lby_Lobby00` StartPos 10개 중 9개는 이름 있는 것(`ResultPlayer0..7` 결과 화면, `FromReplay`)이고 이름 없는 1개가 TeamCmp Alpha(−0.149, 0.01, −11.959, yaw −0.382)다. `StartPosTipsTrial` 은 팁 체험 전용 이름(Restore/Aim/Front10m…). 그래서 이름 없는 내 팀 StartPos 를 고른다 [데이터 판단 + 추정: 로비 입장 위치]. 이 점은 `LobbyShootingArea`(중심 −8.17, 6.82, −8.41, 20×34) 안이다. 정면 = (sin yaw, 0, cos yaw)(카메라 담당과 같은 규약).

**리스폰**(`Btn.Reset`, 물 아래로 내려감, `PlayerDead` 태그 접촉, 맵 아래 10 유닛): 0x710249cb60 cRespawn 요약 — 위치·방향, 속도·카운터 0, 상태 WaitHold(0x56), 잉크 1.0, `respawns++`(카메라가 이 값 변화로 리셋). 쓰러짐 타이머·연출·무적은 미구현.

**잉크 탱크**: `ink`(본체+0x698, 생성 1.0), `inkRecoverStop`. 회복은 InkRecoveryUp 0AP 생성자 기본값 `InkRecoverFrm_Std_Low 600`(사람), `InkRecoverFrm_Stealth_Low 180`(잠복) 프레임에 0→1 선형 [판독: 기본값 / 추정: 적용식·조건].

**이벤트**(DESIGN.md §4): `Jump`(owner, pos, wall: 벽 점프 여부), `Land`(owner, pos, air: 착지 전 공중 프레임 — 공중 8 초과일 때만 0이 아님), `ToSquid`(0x82 요청), `ToHuman`(0x91), `Swim`(오징어·접지·발밑 아군·움직임 시작 프레임, xlink 의미 [추정]).

### 1.3 player 상태 필드와 소유 (shared `"player"`, 타입 `PlayerState`)

- physics 만 쓰는 필드: 위치·속도·상태 번호·카운터·법선 전부. 다른 영역이 읽는 주요 필드: `pos`, `prevPos`(보간), `facing`, `vel`, `final`, `vy`, `jump3d`, `state`/`stateName()`/`stateFrame`/`stateRate`/`animSpeed`, `squid`, `squidModel`, `transform`(SM+0xf0, ≥61 이면 `_Hlf`), `onGround`, `airFrames`, `airRatio`, `floorN`, `surfN`, `groundN`, `groundMaterial`, `wallCling`, `swimming`, `step.{cls,own,enemyMove}`, `team`, `id`, `respawns`, `spawnPos`, `spawnYaw`.
- **weapon 소유**(physics 는 읽기만): `weapon.shooting`(이번 프레임 사격 자세, 원본 본체+0x4ec/+0x524 > 0 또는 잉크액션 vt[0x28] 참), `weapon.moveSpeed`(WeaponShooterParam.MoveSpeed; 0 이면 physics 가 무기 표에서 읽은 값), `weapon.frame`(마지막으로 쓴 `world.frame`; −1 이면 physics 가 `ZR 누름 && 사람 && 오징어 요청 없음`으로 대신 판정).
- **공동**: `ink` — weapon 이 소비(감소), physics 가 회복(증가). `inkRecoverStop` — weapon 이 설정(InkRecoverStop 20 등), physics 가 매 프레임 1 감소. `squidLock`(본체+0xac4, 사격 직후 오징어 불가) — weapon 이 `max(현재, 값)`으로 설정, physics 가 매 프레임 `max(x,1)−1`.
- 시스템 순서상 weapon 은 player 뒤라 physics 는 weapon 의 **직전 프레임** 값을 읽는다(원본은 같은 프레임 입력 단계 값 — §3).

## 2. 원본과 다른 점

### 2.1 캐릭터 컨트롤러 근사 (Phive/hknp 내부 대체)

| 항목 | 원본 | 웹 | 이유 |
|---|---|---|---|
| 형상 | ShapeParam `SplPlayer_cct` ColGround 캡슐 (0,0,0)-(0,0.7,0) r 0.6 [데이터] | 같은 캡슐, 기준점 = 발 + (0, 0.6, 0) | 기준점 [추정]: ColGround/ColOthers 아래 끝이 모두 −0.6, ColBullet 아래 끝이 0, 모서리 미끄럼 a7c = 법선y − max(dy,0)/R 이 평지에서 dy=0 이 되려면 발=접점 |
| 이동 | 강체 + 접촉 해석, GameOnGround/GameInAir 상태 전이 | 겹침 해소(최대 4회) → 쓸어 넘기기 + 접촉면 미끄러짐(최대 4회). 지면 모드는 변위 방향을 지면 평면으로 투영하고 크기 유지, 지면이 아닌 면(n.y < 한계)은 수직 벽처럼 다룸 | 엔진 미판독 |
| 지지 판정 | PC+0xd0 = Phive 상태 OnGround && S+0x20 | 지면 모드: 직전 바닥 법선 반대로 `수평 이동량×1.196(tan50.1°)+0.02` 쓸어 넘겨 n.y ≥ 한계면 지지(경사 한계까지 따라 내려감). 공중 모드: 0.001 + 이동 중 접촉. 이동 중 막아 선 "지면으로 볼 수 있는 다른 면"(경사 시작, 오징어가 붙을 벽)이 있으면 그 면 법선으로 탐색 | 지지 거리·전이 조건 미판독 |
| 공중 강제 | vy > 0.001 이면 InAir, 같은 프레임 Phive 가 OnGround 로 되돌리지 않는다 [추정] | 같은 가정 | |
| 적분 | 게임 속도 ×60 → 강체 → dt(1/60) 적분 | `pos += F`(f32) | ×60/÷60 왕복의 ulp 차이 무시(phive_controller.md §6.8 과 같은 종류) |
| 충돌 거리 | TOI 정밀 | 보수적 전진, 간격 ≤ 1e-4 에서 정지(착지 높이 오차 ≤ 1e-4) | |
| 동일 t 의 접촉 | — | 간격이 더 작은 삼각형 우선(이웃 삼각형 모서리의 기울어진 법선 방지) | |
| 기본 도형 | hknp 캡슐/구/원통 | 다면체(경도 12): 반경의 최대 3.4% 안쪽 | 메시 하나로 질의 통일 |
| 동적 상자 쓸어 넘기기 | — | 각 축을 반경만큼 늘린 상자(모서리에서 실제보다 큼) | |

### 2.2 이식 차이·근사

- **방향 보간 0x7101252ff0**: 원본은 sead 사인 표(0x7104aa5b5c)로 계산 → 웹은 `Math.acos/sin` + f32. 입력 전방 축·공중 바닥 법선·0x710245f964 변위 혼합에 쓰여 비트 일치하지 않을 수 있다(평지·정지 카메라에서는 보간 t 가 0/1 이라 영향 없음).
- **입력 오른쪽 벡터**: 원본 0x710245b2b4 는 `N × *(PlayerCamera+0x68)` 로 전방 축을 만든다. +0x68 이 가리키는 벡터를 판독하지 못해 카메라 오른쪽(rigForward 에서 (−fz,0,fx))으로 둠 [추정]: 이 가정에서만 평지 정면 = 카메라 정면, 벽을 보고 밀면 벽 위쪽이 된다. 보간 비율 본체+0xd4c 는 생성자 1.0 [판독], 0 으로 되돌리는 본체+0xab0 writer 는 미판독 → 항상 1.
- **powf/logf/expf**: `Math.pow/log/exp` + f32(기어 쪽은 같은 방식으로 원본 실행과 비트 일치 확인됨).
- **모델 정면**(공중 감쇠의 [본체+8] 행렬 열 +0x2a0/+0x2ac/+0x2b8): 사람 = 조준 수평 방향, 오징어 = 수평 이동 방향 [추정].
- **SM+0xd4 이동 애니 속도값**(0x710246d060 미판독): |이동 속도|로 근사 → 대기/걷기 판정(idle 0.001/0.003)과 착지 임계.
- **애니 진행 프레임**: ASB 대신 클립 길이 표(`sm.ts` CLIP, analysis/graphics/dump/samples.json.gz): ToSquid 6, Sqd_ToSquid 13, Sqd_ToHuman 3, ToHuman 30, Jump00_St 5, Jump00 20, Jump00_Ed 19, Sqd_Jump_St 15, Sqd_Jump 30(반복), Sqd_Jump_Ed 15 등. JumpVarID 무작위 변형(Jump01/02)은 대표 00 으로 [추정].
- **본체+0x488 x**(입력 구조체 +0x14, writer 미확정): 오징어 버튼을 누르는 동안 1 [추정]. 0x710249bb60 `s = min(a38, 1 − own²·x)` 로 아군 잉크 벽에서 미끄럼이 없어지고, 벽 위 a2c 감쇠 0.97−0.01x, cling acc 0.005−0.002x 가 된다. x=0 이면 오징어가 아군 잉크 벽에서 0.1/프레임으로 미끄러져 내려가 원본 동작과 맞지 않는다.
- **발밑 샘플**: `world.paint.sample(pos, 0.6)` 의 `ratio[t]` 를 `c_t/N·min(N/15,1)` 로 본다. 반경 0.6(GroundPaintMonitorRadius [미확정])은 캡슐 반경. 접지 중은 지지 접점, 공중은 발 위치에서 샘플. `paint` 가 없으면 무도색.
- **오징어 벽 붙기 판정**(0x710268c3fc 요약): 오징어이고 벽(법선 y < 0.7071) 접촉점의 아군 비율이 임계(0.65 − 0.3w)를 넘으면 다음 프레임 지면 한계 −0.2571. 토관·나이스볼·점프 중 조건 분기는 생략.
- **벽 점프 트리거**: 원본은 입력 링 버퍼(최근 6프레임, 항목 +0x10/+0x11)와 0x71024593e8 → 웹은 `점프 눌림 && 바닥 법선 y < 0.6414 && 최근 6프레임 안 벽 붙기 && 0x71024593e8(스틱 ≥ 0.4, 벽 반대쪽 60° 안)` [추정: 링 버퍼 의미]. 발사 식(0.192·0.23·0.3, Somersault_MoveVelKd^n)은 판독 그대로, n(본체+0x7dc) writer 미확정 → 0.
- **0x710245b2b4 의 착지 바닥 투영 ⑥**: `v·N ≤ v·(본체+0x18c)` 분기의 본체+0x18c 정체 미확정 → 항상 단순 투영 `v −= N(v·N)`.
- **측면 접촉 ③**: 접지 중만이 아니라 공중에도 적용(공중에서 벽 쪽 이동 속도가 남지 않게) [추정].
- 입력 우선순위 목록의 종류↔버튼(오징어 = ZL, 사격 = ZR, 서브 = R) [추정, player_state.md §6.1.1].
- 무기 표 이름: 무기 id `Shooter_Normal_00` → `WeaponShooterNormal`(번들 params 규칙). 없으면 생성자 기본값(Mid, AccType 1, MoveSpeed = 0x71058bbdac 0.072).
- `respawn` 의 `sinceJump = 100`(재점프 대기 없이 바로 점프 가능) — 원본 리셋 값 미확인, 웹 선택.

### 2.3 미구현

- 0x710245b2b4 의 특수·코옵·대시 패널·레일·잉크레일·Jetpack·Chariot·SuperLanding·나이스볼·연어런 분기, 넉백 벡터(본체+0x16c 감쇠·더하기는 외부 입력이 없어 0), 레일·발판 외부 속도, ImpactAndReject 충격·밀어냄(0), 벽 쪽 감쇠(본체+0x498/+0x48c), 미끄럼 계수에 따른 상승 억제 블록(0x710249bb60 > 0 && 접지), 경사 cap 비율(본체+0x1d8 필요 — 0.1 고정), 오징어 벽 속도 제한의 본체+0x1d4 벡터 부분.
- 점프: 0x710269e674(특정 상태), 본체+0xc18 카운터 배율, 0.07 상한 조건(bVar31), 바닥 플래그 0.06, 외부 상한 콜백, +0x4c0 감산, 점프 직후 지속 프레임 +0x77c 식(벽 근처 점프에서만 0 아님 — 평지 0).
- 오징어 롤(Somersault, 0x8d/0x8e), 벽 점프 차지(0x8f, 본체+0x774 증가 조건 bVar27 미판독), 0x780/0x782 플래그 writer.
- 슬롯19: A 제한(PC+0x1d0 침투 분류), 벽 낙하 끌어내림(b)(a44/a48), 이륙 관성·모서리 밀기(+0xfc, a74/a78), 안전 지점 기록, 다운 계열 카운터·쓰러짐 연출, Surprise(0x88) 요청.
- 상태기계: 사이드스텝·토관·슈퍼점프·스페셜·0x710244187c 의 무기별 분기(슈터만), 보조(상체) 레이어 SM+0xd0, 지연 요청, 사람 걷기 재생 속도식.

## 3. 미확정·추가 분석 필요

| 항목 | 풀리려면 |
|---|---|
| PlayerCamera+0x68 벡터 정체(입력 전방 축) | 카메라 메인 갱신 0x71024d9ae8 에서 +0x68 쓰기 추적 |
| 캡슐 기준점(발 + 0.6) | PlayerCollision 이 강체 위치를 쓰는 함수(리셋 0x710249cb60 → PC) 판독 |
| Phive 지지 판정 거리·OnGround↔InAir 전이 | ctrl 상태 S+0x20/+0x38, GameOnGround slot4 0x7103a85410 의 접지 거리 |
| 본체+0x488(x), +0x790, +0x78c writer | 입력 함수 0x710249f494 의 구조체 복사 경로 실행 추적 |
| 0x710246d060(SM+0xd4) | 디컴파일·실행 |
| 입력 링 버퍼(본체+0x9dcc..) 항목 의미 | 0x7102475a54 링 버퍼 writer |
| GroundPaintMonitorRadius | paint 영역(모니터 목록에 넣는 함수) |
| 시스템 순서(weapon 사격 플래그를 player 가 같은 프레임에 보는지) | 원본 입력 단계(0x710249f494)의 +0x4ec/+0x524 writer |
| 플레이어가 동적 충돌체(표적)에 막히는지 | 표적 액터 Phive 레이어(range 영역) |
| 잉크 회복 적용식·조건 | InkRecoveryUp 소비 함수 |

## 4. 검증

| 테스트 | 내용 | 결과 |
|---|---|---|
| `tests/player_jump.test.mjs` | 점프 곡선 hold 0/5/10/60 을 원본 함수 연결 실행 결과(`analysis/move/jump_emu_hold*.json` → `player_fixture_jump.json`)와 프레임마다 vy·이동 y·높이·공중 프레임 비교 | **비트 일치**(30/34/38/53 프레임, 착지 프레임 전까지). 최고점 탭 0.84145(14f), 유지 1.73148(30f) |
| `tests/player_move.test.mjs` | 기어 AP 14종 × (인간 3, 오징어 3, 사격 배율, 적잉크 점프·이동·사격 이동)를 `player_gear.py`(원본 실행과 731값 일치) 출력(`player_fixture_gear.json`)과 비교 | **비트 일치** |
| 〃 | cap 정지 중 비율 0.1, 정상 속도 0.096(Mid 0AP), 가속 0.01/프레임·감속 0.008, 사격 중 0.072(WalkShoot 0x60), 오징어 무도색 0.072 / 아군 0.192 / 적 0.012, 0x82→0x84→0x87, 0x91→0x92→0x56, 리셋, StartPos 선택 | 통과(판독식 대조) |
| `tests/player_collision.test.mjs` | collision.json/bin 읽기, 레이·구 쓸어 넘기기·레이어(철망 KeepOut, 물 Water)·동적 구, 사람/오징어 철망 필터, 벽 막힘·미끄러짐, 30° 경사 오름/60° 막힘, 턱 낙하·착지(Land), 물 리스폰, 대체 평면, 오징어 벽 수영(붙기·머묾·꼭대기 넘기) | 통과 |
| 실제 에셋 | `Lby_Lobby00` collision(8825 삼각형 + 기본 도형) — 시작 위치 착지, 사방 이동, 점프, 오징어 대각 이동, 리셋. 프레임당 0.05~0.12 ms | 확인(node) |
| 브라우저 | `npm run dev` + playwright 헤드리스: 실제 에셋 충돌(fallback 아님), 시작 위치, 점프 상태 0x9b, 콘솔 오류 없음 | 확인 |

원본 실행 대조가 있는 것은 점프 수직 성분(함수 연결)과 기어 수치뿐이다. 수평 이동·cap·가속은 판독식 재구현이며 원본 실행 비교는 없다(0x710245b2b4 는 본체 포인터 수십 개가 필요).

## 5. 조정 요청

1. **DESIGN.md §4 이벤트 표**: `Jump` 에 `wall`(벽 점프 여부), `Land` 에 `air`(착지 전 공중 프레임, 공중 8 이하 착지는 0) 필드 추가.
2. **DESIGN.md §2 shared `player` 설명**: 소유 규칙(§1.3) — `weapon.{shooting,moveSpeed,frame}` 은 weapon 이 쓰고, `ink`·`inkRecoverStop`·`squidLock` 은 weapon/physics 공동(감소·설정은 weapon, 회복·카운트다운은 physics).
3. **[camera]**: shared `camera` 에 PlayerCamera+0x68 이 가리키는 벡터(판독되면)를 `right` 로 내 주면 physics 가 그대로 쓴다(지금은 rigForward 에서 만든 오른쪽).
4. **[weapon]**: 사격 자세를 `player.weapon.shooting` 에, 쓴 프레임을 `player.weapon.frame` 에 매 프레임 써 주면 physics 의 대체 판정(ZR 누름)이 꺼진다. 탄 생성 시 `player.squidLock = max(squidLock, min(param+0x50, [0x71058bdf0c]))`(player_state.md §6.1), `inkRecoverStop` 설정.
5. **[audio]/[render]**: 발밑 법선은 `groundN`, 지지 삼각형 재질은 `groundMaterial`(collision 재질 번호 → `world.collision.materialName()`), 이동 애니 속도값은 `animSpeed`, 변신 카운터는 `transform`, 재생 속도는 `stateRate`.
6. **core/types.ts**(선택): `Layer` 에 철망 같은 "플레이어만 막는 면"과 "플레이어 통과 면"을 구분하는 비트가 필요하면 추가 요청. 지금은 원시 Phive 필터를 `MeshCollisionWorld.material(i).hitMask/subMask` 로 노출하고 플레이어 몸 판정은 그것으로 한다.
