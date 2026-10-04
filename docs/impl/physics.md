# [physics] 플레이어 이동·충돌 구현 기록

2026-10-04 몸체 물리 정정: 캡슐·몸체 원점 분리, native 침투 보정·순차 법선 충격량·carry/finalize·double COM, SplResultPlayer 지지 분류·이동 상태 전이, 양방향 충돌 필터·하위 레이어, 발밑 Disk 모니터 가중 합을 원본 식으로 바꿨다 — §1.5. §1.2 의 body.ts 설명과 §2.1 근사 표는 정정 표시만 달고 보존한다.

2026-10-04 이동 계산 정정: 방향 보간·acos 를 sead 표로, 입력(데드존·+0x480·벽 입력 계수·이력 24칸·15프레임 스틱 고정·리스폰 리셋), 오징어 k, 벽 차기·롤·차지 벽 점프·래치를 원본대로 바꿨다 — §1.4. 아래 §2.2 의 해당 근사 항목은 정정 표시만 달고 보존한다.

2026-10-03 탄·총 통합 정정: player는 mainInput 우선 게이트와 6a8/6ac/6b0 세 회복 카운터를 연결했다. 음수 진행/이전 max 판단을 구현했으나 fastStealth 공급은 swimming 근사, 실제 B7a0/상위 회복 게이트는 미연결이다. collision에 초기 overlapSphere를 추가했으며 player body solver나 camera sweep은 변경하지 않았다. 근거·153개 테스트 결과는 [weapon.md](weapon.md) §4~10. 아래는 이전 구현 기록을 보존한다.

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

### 1.4 이동 계산 원본 반영 (2026-10-04, MOV01·MOV03·MOV05)

근거: movement_physics.md §6.1.1·§6.2.1·§6.3.2·§6.3.3·§6.4.1~6.4.4·§6.8, player_state.md §6.3(P12·P13·H), SHARED `[r5 player]`·`[r6 player]`. 이번에 새로 판독해 쓴 명령 구간은 줄 끝에 주소를 적었다.

| 항목 | 반영 | 원본 근거 |
|---|---|---|
| 방향 보간·acos | `slerpDir` = `camera/native_math.ts` 의 `directionSlerp`(sead 사인 표 0x7104aa5b5c·아탄 표 0x7104aa6b6c, 명령 순서 f32). 플레이어 호출부 8곳은 모두 axis = null 이라 반대 방향 축 분기는 없다. 입력 전방 축·공중 바닥 법선 복귀(contact.ts)·0x710245f964 변위 혼합이 모두 이 함수를 쓴다 | [실행] acos 2015건·slerp 2407건 비트 일치(이번 fixture) |
| 스틱 공급·데드존 | `inputStick`: +0x786 = 직전 +0x785 ? min(+1,100) : 0(`0x71024a0564`), 스틱 = (Emote·+0xaec 잠금이면 0) / 덮어쓰기(+0x80c > 0) / 컨트롤러 원값, +0x47c = clamp01((√(y²+x²)−0.1)/0.9), +0x480 = 내려갈 때만 0.2 추종 | [실행] 200건 비트 일치 |
| 벽 입력 계수 x | `wallInputUpdate` = 0x71024a7100 (N = 본체+0x180, D = 본체+0xd40, C = 카메라 기저 Y `camera.up`). 벽에서 N×D·C·스틱, 바닥에서 +0x484 −1·+0x488 −0.03 | [실행] 300건 비트 일치 |
| 이동 이력 | 24칸 링(`pushHistory`/`historyAt`), 항목 = 수평 방향·속력(바닥이면 \|v\|, 벽이면 v.y + jump3d.y)·잠복·벽. 리스폰에서 유지 | [판독] 입력 함수 기록부(move_input.c 760~830행) |
| 입력 나머지 | `inputPost`: +0xaec max(x,1)−1, +0xad8 = max(x−1, 조건값), +0xab0 래치, n 리셋(상태 ∉ S 또는 마지막 발사 + 90 < 프레임, s32 비교), +0x790 부호 있는 연속 프레임 | [판독]·[실행: n 쓰기 1572건] |
| 리스폰 리셋 | +0x734 = 9999(생성자도 9999), n = 0, +0x774..+0x782·입력 구조체·+0xaec·발사 구조체 0, 이력 유지 (이전 웹 선택 100 정정) | [판독] 0x71023547bc |
| 발사 활성 해제 | `launchPre` = 0x7102477780~0x71024778a4: 적용 프레임이 아니고 접지(+0x268 ≥ 1)·vs ≤ 0.001 이면 L+0x3c/+0x3d = 0, 그 밖에 상태 ∉ 0x82..0x90 이면 L+0x3c = 0. 이어서 +0x80c = max(x,1)−1. 이전에는 L+0x3c 를 리스폰 외에 지우지 않았다 | [판독] 이번 디스어셈블 |
| 15프레임 스틱 고정 | 벽 점프 발사가 L+0x54 = 15, L+0x58/+0x5c = 정규화한 발사 순간 스틱. 입력 전방 축은 +0x80c == 15 인 프레임의 축(c)을 저장해 > 0 동안 쓴다(move_full_main.c 10408행) | [판독] |
| 착지 경직 | 기존 `updateMove` 의 0.06 쪽 min(x/30,1) 보간이 원본 명령(11300~11330행)과 같음을 재확인 | [판독] |
| aimFold | 공중 감쇠 h 접기 = `(+0xad8 ≥ 1 && 상태 ∉ S)`. +0xad8 은 입력 단계 max(x−1, 조건값)·발사 꼬리 max(x, 6) 으로 갱신 | [판독] (조건값 [미확정], 아래) |
| 롤·차지 감쇠 | `launchDamping` = PlayerParam+0x140 을 min(n,10)번 **연속** 곱(f = kd·f). Ghidra 의 4개 묶음 곱 표기는 원본 명령(0x7102459b90~)과 다르다 | [실행] 1020건 비트 일치 |
| MOV03 k | `squidSpeedK`(gear.ts) = 0x710266c6e4: 인자 bit0 → 1, PlayerParam+0xac 의 능력 104 비트 → 0x3f666666, 그 밖 1. +0xac 는 `GearAP.ninja`(징어닌자) 때 bit 4. 기본 장비 1 | [실행] 1088건 비트 일치 |
| 벽 차기 | `tryJump`: !+0x7f4 && N.y < 0.6414 && 눌림 && 최신 9개 중 최신 6개에 (벽 && 잠복) && 0x71024593e8 → 재점프 대기 생략, `launch(…, false)`. 0x71024593e8 은 +0xaec > 0 이면 컨트롤러 원값을 읽음 | [판독] 5330~5372행 |
| 오징어 롤 | !+0x7f4 && N.y ≥ 0.6414 && 눌림 && (ZL·+0x786 ≥ 6 ‖ 우선순위 맨 앞 ZR/R) && 이력의 첫 유효 후보(벽 아님, 속력 ≥ 0.144, \|dir\|² > 2⁻²³) && 최신 6개 잠복 && dot ≤ cosf(60°) = 0x3effffff → 속력 대입·`launch(…, true)`·오징어면 점프 0.1705 | [판독] 5440~5600행, cosf 상수 [실행: SDK] |
| 발사 0x7102459630 | 롤 = normalize(sy·aim + sx·(−aim.z,0,aim.x))·속력·1.0, 벽 = normalize(n.x,0,n.z)·0.192, ×감쇠, 벽이면 a30 = a38 = 0(이전: a2c 벡터 전체 0 → 정정), jump3d = 0, vs = min(0.23 + 0·…, 0.3), 점프 시작(상태 요청 없음). 꼬리 n += 1(s32)·L+0x28 = max(frame,0)·+0xad8 ≥ 6, 오징어면 0x8d 요청 | [판독] move_contact.c 466~830행 |
| 점프 시작 | 0x71024a8000: +0x734 = +0x77c = 0, 상태 요청은 3D 점프·롤·벽 경로가 아닐 때만 | [판독] move_jumpstart.c |
| 차지·래치 | `wallChargeStage` = 0x7102482980~0x7102482fbc(+0x778, onWall, 뗄 때 바깥 → 발사 / 아니면 0x7102458a18, 래치 해제·진행, +0x774 증감) | [판독] 6185~6412행 |
| 0x7102458a18 | `wallLatch`: s = clamp01((+0x774−10)/WallJumpChargeFrm), y = 0.02 + 0.23·s, jump3d.y = max, +0x75c 사본, s ≥ 0.2 → +0x780 = +0x782 = 1, +0x774 = 0, 점프 시작 | [실행] 92건 비트 일치(원본 연결 실행 결과) |
| 유지 가산 | +0x782 차단, `!(L+0x3d && L+0x3f)`, 0x710249bb60 의 own²·x 항은 +0x790 > 0 && x > 0 일 때만 | [판독] 6150~6180행 |
| 상태기계 | P12(+0x7f4 && (want ‖ cur 0x8d) → 0x8d 유지/적용), P13(want && +0x782 && +0x780 && cur 0x87 && !B7a0 → 0x90), H(차지 > 10 → 0x8f), ToHuman 의 SM+0x1f4 조건 +0x782 로 정정 | [판독] state_big_full.c 1492~1560·2370~2422행 |
| 측면 접촉 ③ | contact.ts 가 이미 공중에도 적용한다(코드 변경 없음). 근거 수준만 [추정] → [실행] (`[r6 player]`) | [실행] |

남은 차이·미확정:
- **+0xad8 조건값** [미확정]: 입력 함수 0x71024a0474 의 `max(x−1, w10 ? [x29−0x2c] : 0)` 에서 w10·스택 값이 무기 잉크액션 상태에 달려 있다. 웹은 "이번 프레임 사격 자세면 1" 로 둔다.
- 0x710249bb60 뒷부분(조건부 min(s, 0.3))은 기준 객체 오프셋(+0x9e54 등)이 본체 크기를 넘어 정체 미확정 → 생략.
- 3D 점프 선택(uVar31: 오징어·벽 붙기 한계·N.y < 0.6414)과 일반 점프의 경사 처리·+0x77c 생산식은 기존 근사 그대로.
- +0xa4c(벽 낙하)·+0x781·+0x768 법선 기록·넷 이벤트·FUN_710243c1c4(오징어 발사 효과)·+0xad0/+0xad4/+0xadc 는 쓰지 않는다. +0x745(0.96 감쇠) 1 writer 미확정 그대로.
- 원격(PlayerRemote/PlayerNetState_Jump) 경로, 사이드스텝·Chariot·대시 패널 조건은 모두 거짓으로 둔다. 세션 조건(로컬 조작 플레이어)은 참으로 둔다 [추정].
- 0x71024593e8 의 acosf, 0x710245b2b4 의 powf/logf/expf 는 SDK libm 대신 `Math.*`+f32 (드물게 1ulp, §9.4).
- +0xab0 카메라 리셋(Y 버튼)은 `core/input.ts` 에 버튼이 없어 항상 거짓.
- contact.ts(몸체 담당)의 a2c/a38 식은 아직 x = 오징어 버튼(`squidRequest`) 추정을 쓴다. `p.wallInput`(+0x488)로 바꿔야 원본과 같다(조정 요청 7). → 2026-10-04 반영(§1.5).
- 0x8d/0x8e Somersault 클립 길이는 samples.json 에 없어 기본값.

검증(2026-10-04):
- `tests/player_move_native.test.mjs` 10개 — fixture `tests/fixtures/player_move_native.json`(생성 `web/tools/r7_player_move_fixture.py`: acos·slerp 는 이번에 unicorn 으로 원본 실행, 나머지는 기존 원본 실행 결과 파일 r5_player_input_emu / roll_counter_emu / squid_speed_k / r6 walljump_emu 에서 옮김). 모두 비트 일치.
- `tests/player_wall_launch.test.mjs` 8개 — 롤 gate·벽 차기·15프레임 스틱 고정·차지/래치/해제·n 리셋·+0x786/+0x790 흐름(판독식 대조).
- 기존 테스트 기대값은 바꾸지 않았다. HEAD 의 body/contact/collision 위에 이번 변경만 얹은 격리 사본(`git archive HEAD` 로 만든 임시 사본, 확인 뒤 삭제)에서 전체 322개 중 319개 통과(실패 3개는 사본 밖 상대 경로 fixture 없음: bloom_common·common_shadow_r6·fx_data_port), 플레이어·무기 관련 전부 통과.
- 작업 트리 전체는 391개 중 384개 통과(기록 시점). 실패 7개(player_collision 경사·벽 수영, player_jump 곡선 4, StartPos)는 동시에 진행 중인 몸체 물리 변경(body.ts·contact.ts·collision/*)에서 나며 위 격리 사본에서는 통과한다. → 몸체 반영 뒤 398/398 통과, 기대값 정정 근거는 §1.5 끝.
- 헤드리스(`analysis/r7_player/browser_move.mjs`, 개발 서버 PORT=5197, Lby_Lobby00): 걷기·정지·점프·옆걸음+회전·오징어 수영·롤 시도·오징어 점프 유지·벽 쪽 차지·뒤로 당김·사격 이동·리셋 700프레임, pageerror·console error 0, 상태 숫자 모두 유한. 결과 `analysis/r7_player/browser_move.json`. 잉크 칠한 벽이 없어 실제 벽 발사는 브라우저에서 일어나지 않았다(단위 테스트로만 확인).

### 1.5 몸체 물리 원본 반영 (2026-10-04, PHY01~PHY04·COL02·MOV04)

근거: phive_controller.md §3·§5·§6.7·§6.10.1~6.10.5, character_controller.md §3·§4.1·§5~7, player_state.md §7.3·§8, paint_and_score.md §7(발밑 모니터 [r6 paint]), SHARED `[r6 physics]`·`[r8 physics]`·`[r9 physics]`·`[r6 paint]`, analysis/completion/r8/contact_kernel_support.md·solver_info_support.md·contact_properties_support.md. 기존 §1.2 의 body.ts(쓸어 넘기기+미끄러짐 근사)와 §2.1 표는 이 절로 대체한다(지우지 않고 아래 정정 표시만 단다).

한 프레임 순서(phive_controller §6.7): `index.ts` stepPlayer 안에서 슬롯18(메인 계산) → **Phive Entity 월드**(`body.ts stepBody`: 형상 갱신 → 속도 전달 → 컨트롤러 → native 솔버 → SplResultPlayer) → 접촉 반응 큐(플레이어 몸체 콜백 없음) → 액터 단계1 write-back → 슬롯19(`contactCleanup` 등) 순서로 나눴다.

| 항목 | 반영 (파일) | 원본 근거·수준 |
|---|---|---|
| PHY01 형상 | `body.ts updateShape`: 본체+0x7a4(상태 ∈ 오징어 집합 쪽으로 0.1/프레임), +0x7a8(사람 쪽 ×0.1 감쇠·\|차\| < 0.001 대입, 오징어 쪽 즉시), PC+0x168 0.2 히스테리시스(끝점 ±2⁻²³). ColGround B = A + 0.7·(1−t), r = 0.6, ColOthers len 0.72−0.72t·r 0.39+0.01t·A0 −0.21. 반경 setter min(max(0.6, world+0x21c = 0.01), 2000) | [판독] character_controller §3.2~3.3, 0.2 히스테리시스 꼴은 ColBullet [실행] 과 같은 꼴 |
| PHY01 원점 분리 | 게임 위치 ≠ 몸체 원점. 리셋 0x71024f4440 = 위치 + (0, r, 0), 평상시 write-back 0x71024d26f8 = 원점 − r·up (`writeBackPosition`). native COM(double)·몸체 원점(f32)·잔차를 `BodyState.motion` 에 둔다 | [실행] 1024/1024 ×2 (r6), 이번 fixture 비트 대조 |
| PHY02 침투 보정 | `collision/solver.ts contactBias`(old/carry/depth 분기, cap = dt·C0, k = C8 −0.05, gamma = 288, 임계 −2⁻²³, ARM FMIN/FMAX 부호 0), `effectiveMass`(압축 inverse mass SHLL #16 0x3c24 → 0.010009765625 → 99.90243530273438), `normalRow`(dot ≥ target && λ = 0 이면 건너뜀, delta = max(−λ, (target−dot)·M), 순차 갱신), `normalRowsTwoBody`(같은 manifold 여러 행 순차) | [실행] 원본 블록 비트 대조(아래 §4). 4회 overlap push / 4회 slide 근사는 삭제 |
| PHY02 반복 | `stepMotion`: 한 프레임 normal 8회 사이 carry 7회, finalize 1회(sub8/micro1/tau .6/damp1). 행 target 은 프레임마다 1회 생산, λ 는 프레임 시작 0 | [판독+실행] 원본 MT graph 횟수, 첫 커널 λ 0 관찰 |
| PHY03 속도·적분 | `initialCurrent`(09d4ba8: current = v + subgravity·scale, MotionProperties13 은 GravityScale 0), `carryStep`(0a4b514, cap/√n), `finalizeStep`(0a4b8c8: 저장 속도 = cap(current−baseline), 위치용 속도 = f32(f32(base + f32(delta·tau/damp))·f32(1/sub·damp/tau)), COM64 += double(f32(속도·dt)), cap 은 (1/√n)·cap), `poseFromCom`(09d5b68: 원점 = f32(COM − center), 잔차), `nativeSetLinear`(3c50c7c→09d9e54: 축 차 ≤ 2⁻²³ 이면 안 씀, 상한 20000·×(1−2·2⁻²³), NaN 거부) | [실행] 각 함수 원본 비트 대조 + 원본 MT 첫 프레임 전체 사슬(COM .8074951050803065, 원점 .45749515295028687) 재현 |
| PHY03 컨트롤러 | 0x71024f4f7c: \|v\|² ≥ 1.42e-14 이면 m = (v − (0, OnGround ? vy : 0, 0))·60 → setMoveVelocity(방향·속력). GameInAir(+0x1c = 1): vel = 속력·방향. GameOnGround 0x7103a85410: t = normalize((u × d) × N)·속력 + 중력 법선 성분 N·(N·g)·min(\|S+0x38/(N·g)\|, dt). MoveStateUpdate 낙하 상한 200. SplAlongGnd 0x7102c5fdf0(공중 N·0.05·strength 밀기, 지상 −N 질의 v += Δ·k/dt) | [판독] decomp physics/phive_batch1.c, r8_player/along_ground.c; SplAlongGnd 산술 [실행: 합성 질의] |
| PHY04 결과 | `body.ts resultStep` = SplResultPlayer 슬롯7 pass 0: 등급(d < 0.02 ‖ f > 0 ‖ 종류4 → 0, d ≤ 0.19999999 && 종류2 → 1, 종류5 → 2), PhiveUnridable(bit3) 75° 제외, 분류 `classify` = 0x7102c5dd20 전 분기(몸 앞 접점 버림, InAir 상승 중 바닥 버림, 직전 지지와 0.7071 미만이면 속도 방향 [0x71058f0ba0]=90° 검사, θ ≥ 75° && 수평각 > 50° 버림, θ ≥ 104.9° 천장(129.9°/150°), 계단 0.2(acos((R−0.2)/R)), 40°/30°/cos85°·Result+0x1344 입력 방향 조건), 벽 후보 평균(S+0xb4/+0xc0/+0xf5), 바닥 후보 병합(0.05·0.99, f·d 교체), d×1000 오름차순 → f 내림차순 정렬 후 첫 후보, S+0x34 = 얼굴 법선(0.65 미만·병합이면 S+0x28), UserShapeTag 플래그(+0x1744~+0x174b, +0x16bc/+0x16c8/+0x16c9), S+0xf4 해제, OnGround↔InAir 전이(0x71012aa648/0x71012aa108), Result+0x132c/+0x1320/+0x13f8 | [판독] decomp phys4/p4_world_ctrl.c 1348~3854·p4_resultplayer.c. "첫 허용 normal 채택" 근사 삭제 |
| PHY04 정렬 | 접촉 목록을 `collision/contacts.ts heapSortMode3`(키 f, 1-기반 최대 힙, 불안정)로 정리 → 같은 f 접촉도 힙 순서 | [실행] 3000/3000 (r6) — 캐릭터 목록의 실제 모드는 [미확정], 지시대로 모드 3 |
| PHY04 잉크 판정 | 0x7102c5e6a8 은 레이가 아니라 **접촉점 잉크 판정**이다(이번 디컴파일 analysis/decomp/phy_port/step_ray.c): Result+0x39(오징어) && 팀 유효 → 칠 가능 → 모니터 질의 → own − StepPaint+0x44 > 0 && enemy − +0x5c ≤ 그 값. character_controller §6.2 의 "추가 레이 판정" 표현을 이 근거로 정정한다(2026-10-04) | [판독] |
| COL02 | `collision/filter.ts`: `commonPairFilter`(Default/Same/Other block 표비트 + 양방향 F+0x18/+0x1c, 32비트 shift 하위 5비트), `shapeRowOk`/`combinedPairFilter`(0x7103c5e244: bit28 몸체의 형상 행 lo/hi, 복합 +0xb8/+0xbc), `blockRow`(값 2 → bit), `playerSubLayer`(3/4/5/6/7/12). `collision/world.ts playerTerrainFilter` = 플레이어(L5, S = 하위 레이어, bit28 0) ↔ 지형(L3, bit28 1, 삼각형 행), Default 표 행은 PhiveConfig 데이터 | [실행] 4096/4096·4000/4000 (r6), 이번 fixture 비트 대조 |
| MOV04 | `contact.ts FootMonitors`: 모니터 4개 배열(+0x14 = 1/6, +0x18 = 2), 배치 0x7102c71650(같은 대상 재사용, 없으면 가중치 ≤ 0 칸, id 발급), 슬롯 기록(이미 있는 id 유지, 첫 빈 슬롯), `footWeight` 0x7102c71330, `footDelegate` 0x7102c5ec74. `updateStepPaint` = 0x710268b3b8: k = min(N/15,1), f = c/N·k, N == 0 이면 직전 값 1회 재사용(S+0xa8) 후 0, 샘플 없음(O+8 == 0)이면 아군 −1·적 −0.25. 반경 0.6 상수(GroundPaintMonitorRadius 추정) 삭제 — Disk 1×1 스탬프 | 가중치·델리게이트 [실행] 4000/4000 (r6 paint), 배치·슬롯 [판독] |
| MOV04 카운트 | `paint/paintworld.ts monitorCounts(pos, n)`(읽기 함수 최소 추가): 접점 법선을 향한 차트 위 반경 1 원(쿼드 ±1) 안 팀 스텐실 수·칠 가능 텍셀 수. 웹 PaintWorld 대체 구현이 이 함수를 주지 않으면 `sample(pos, 1)` 비율을 카운트 형식으로 바꿔 쓴다(index.ts) | 원 모양·높이 범위·GPU 1~2 프레임 지연은 근사 |
| 슬롯19 입력 | `contactCleanup` 이 PC 필드를 읽는다: PC+0xd0(OnGround && S+0x20), 측면 접촉 = PC+0xec 벽 평균 법선, 천장 = (본체+0x184 < 0.6414 && ny < −0.572 && KebaInk 벽 없음) ‖ (PC+0xd3 && 오징어 && 최종 vy > 0), 표면 법선 +0x1c8 = PC+0xb8(Result+0x13f8). a38·a2c 의 x = `p.wallInput`(본체+0x488), own²·x 항은 +0x790 > 0 일 때(조정 요청 7 반영) | [판독] player_state §7.3 |

원본과 남은 차이·[미확정]:
- **PHY05 접촉 생성** [미확정, 근사 유지]: native manifold(행)와 몸체 접촉 컬렉션(+0x188)의 실제 생산(TOI 처리기·종류·비율·행 수)을 재현하지 않는다. 행 = 시작 자세 캡슐과 삼각형별 최근접 접촉(분리 ≤ 이번 이동 거리 + `CONTACT_LOOKAHEAD` 0.05, 웹 매개변수), 삼각형당 1행. Result 목록 = 그 manifold 삼각형 ∪ 끝 자세 분리 < 0.02 인 삼각형, 거리는 끝 자세 값, 종류 2·f 0. 기본 도형은 기존 다면체(경도 12) 그대로.
- 침투 보정 flag(nativeManifold+92) = 1: 원본 정적·kinematic fixture 관찰값, producer [미확정]. 예측 항(v·S+0x20)은 flag 0 일 때만이라 쓰지 않는다. 접촉 cache(old/carry)는 삼각형 번호로 이어 간다.
- 몸체 local COM (0, .34999996423721313, 0) 은 ColGround 단독 fixture 의 원본 생산값이다. 복합 형상의 질량 분포와 형상 변경 시 COM 재계산은 [미확정](생성 값 고정).
- GameOnGround 의 지지 법선 N 은 S+0x08/S+0x14 중 위쪽에 가까운 것인데 두 필드 writer 가 [미확정] → 직전 S+0x34. 중력 법선 성분의 S+0x38 은 §6.1 배치대로 보정 법선 y 로 읽었다 [추정: 필드 의미]. S+0xd0 bit4 벽 평면 제한·발판 분기 생략. setMoveVelocity 정규화 산술 순서 [추정]. Phive 중력 = −9.8·GravityScale(g·3600/9.8) 의 곱 순서 [추정].
- SplAlongGnd 질의는 반경 0.1 구 쓸어 넘기기, 접촉 컬렉션 "가장 낮은 반대면 접점" 법선은 단일 적중 법선으로 대신한다. SplJump+0x59 [미확정] → 거짓.
- SplResultPlayer pass 1(Result+0x39 조건의 반경 R+0.35 두 번째 질의, 바닥 법선 상자 평균으로 S+0x28/+0x34 덮어쓰기)·움직이는 상대 취소·R+0x1418 의 본체+0x184 < 0.6414 접점 보정·KebaInk 바닥 외 일부 플래그 소비는 생략. Result+0x27·Result+0x28(본체+0x744)·본체+0x746·SplJump 쿨다운 [미확정] → 거짓/0. Result+0x26 = 1 [추정].
- 모니터 대상 식별(원본 (종류, id, 패널) 0x7102c71e50)은 삼각형 번호, 접촉 잉크 질의 0x7102c71a00 은 미판독이라 배치 규칙으로 근사, 칠 가능 검사 0x71012ed800 은 재질 paintable 로 둔다.
- COL02: 플레이어·지형 몸체 F+0x18/+0x1c 런타임 값(raw 이름 → 숫자 연결 [미확정])은 전부 허용. 하위 레이어 flag(본체+0x7a0 등) [미확정] → Visible(4). 카메라·탄 질의는 기존 경로 그대로(이번 범위 밖).
- 몸체 up 은 (0,1,0) 고정(write-back 의 본체+0x28 회전 열, 벽 위 오징어의 본체 회전 미구현). 본체+0xfa0 [미확정] → 빼기 적용.
- 실제 Lby 에서 이웃 기하(턱·기본 도형 다면체) 옆을 걸을 때 1cm 미만으로 들렸다 내려오는 프레임이 있다(평평한 바닥 관통 없음, 아래 헤드리스).

정정(2026-10-04): 테스트 3개 기대값을 원본 근거로 고쳤다. (1) player_collision 벽·경사 메시 winding 을 바깥쪽으로(원본 얼굴 법선 0x7103c4988c flag1 은 winding 그대로 — player_state §7.3.4; 실제 Lby 메시도 바깥쪽), 60° → 80° "못 오름"(최대 경사 75°, 0x7102c5dd20 θ < 75° 면 바닥), 오징어 "멈추면 머묾" → "스틱을 놓으면 벽 미끄럼으로 내려옴"(x = 본체+0x488 = 0, ④⑤). (2) player_jump 높이는 하네스 스텁(y += F) 대신 F 를 native 사슬에 넣은 값, 착지는 몸체 지지 프레임부터 비교 중단. (3) StartPos 0.01 내려앉기는 2 프레임.

## 2. 원본과 다른 점

### 2.1 캐릭터 컨트롤러 근사 (Phive/hknp 내부 대체)

> 정정(2026-10-04): 아래 표는 이전 근사의 기록이다. 형상·기준점·이동·지지 판정·적분·동일 t 순서는 §1.5 의 원본 식으로 대체했다(기준점 = 원점 − r·up [실행], 적분 = native carry/finalize·double COM [실행], 지지 = SplResultPlayer 분류 [판독], 동일 f = 모드 3 힙 순서 [실행]). 남은 근사는 §1.5 "남은 차이"의 접촉 생성(PHY05)·기본 도형 다면체·동적 상자다.

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

- **방향 보간 0x7101252ff0**: 원본은 sead 사인 표(0x7104aa5b5c)로 계산 → 웹은 `Math.acos/sin` + f32. 입력 전방 축·공중 바닥 법선·0x710245f964 변위 혼합에 쓰여 비트 일치하지 않을 수 있다(평지·정지 카메라에서는 보간 t 가 0/1 이라 영향 없음). → 2026-10-04 정정: sead 표 재구현(§1.4, 원본 실행 비트 일치).
- **입력 오른쪽 벡터**: 원본 0x710245b2b4 는 `N × *(PlayerCamera+0x68)` 로 전방 축을 만든다. +0x68 이 가리키는 벡터를 판독하지 못해 카메라 오른쪽(rigForward 에서 (−fz,0,fx))으로 둠 [추정]: 이 가정에서만 평지 정면 = 카메라 정면, 벽을 보고 밀면 벽 위쪽이 된다. 보간 비율 본체+0xd4c 는 생성자 1.0 [판독], 0 으로 되돌리는 본체+0xab0 writer 는 미판독 → 항상 1.
- **powf/logf/expf**: `Math.pow/log/exp` + f32(기어 쪽은 같은 방식으로 원본 실행과 비트 일치 확인됨).
- **모델 정면**(공중 감쇠의 [본체+8] 행렬 열 +0x2a0/+0x2ac/+0x2b8): 사람 = 조준 수평 방향, 오징어 = 수평 이동 방향 [추정].
- **SM+0xd4 이동 애니 속도값**(0x710246d060 미판독): |이동 속도|로 근사 → 대기/걷기 판정(idle 0.001/0.003)과 착지 임계.
- **애니 진행 프레임**: ASB 대신 클립 길이 표(`sm.ts` CLIP, analysis/graphics/dump/samples.json.gz): ToSquid 6, Sqd_ToSquid 13, Sqd_ToHuman 3, ToHuman 30, Jump00_St 5, Jump00 20, Jump00_Ed 19, Sqd_Jump_St 15, Sqd_Jump 30(반복), Sqd_Jump_Ed 15 등. JumpVarID 무작위 변형(Jump01/02)은 대표 00 으로 [추정].
- **본체+0x488 x**(입력 구조체 +0x14, writer 미확정): 오징어 버튼을 누르는 동안 1 [추정]. 0x710249bb60 `s = min(a38, 1 − own²·x)` 로 아군 잉크 벽에서 미끄럼이 없어지고, 벽 위 a2c 감쇠 0.97−0.01x, cling acc 0.005−0.002x 가 된다. x=0 이면 오징어가 아군 잉크 벽에서 0.1/프레임으로 미끄러져 내려가 원본 동작과 맞지 않는다. → 2026-10-04 정정: x writer = 0x71024a7100(벽 입력 계수, [실행]). move.ts 가 `p.wallInput` 으로 계산하고, contact.ts 의 추정 사용처 교체는 조정 요청 7.
- **발밑 샘플**: `world.paint.sample(pos, 0.6)` 의 `ratio[t]` 를 `c_t/N·min(N/15,1)` 로 본다. 반경 0.6(GroundPaintMonitorRadius [미확정])은 캡슐 반경. 접지 중은 지지 접점, 공중은 발 위치에서 샘플. `paint` 가 없으면 무도색.
- **오징어 벽 붙기 판정**(0x710268c3fc 요약): 오징어이고 벽(법선 y < 0.7071) 접촉점의 아군 비율이 임계(0.65 − 0.3w)를 넘으면 다음 프레임 지면 한계 −0.2571. 토관·나이스볼·점프 중 조건 분기는 생략.
- **벽 점프 트리거**: 원본은 입력 링 버퍼(최근 6프레임, 항목 +0x10/+0x11)와 0x71024593e8 → 웹은 `점프 눌림 && 바닥 법선 y < 0.6414 && 최근 6프레임 안 벽 붙기 && 0x71024593e8(스틱 ≥ 0.4, 벽 반대쪽 60° 안)` [추정: 링 버퍼 의미]. 발사 식(0.192·0.23·0.3, Somersault_MoveVelKd^n)은 판독 그대로, n(본체+0x7dc) writer 미확정 → 0. → 2026-10-04 정정: 이동 이력 24칸·벽 차기/롤/차지 트리거와 n(s32, 상한 10, 90프레임 리셋)을 원본대로(§1.4).
- **0x710245b2b4 의 착지 바닥 투영 ⑥**: `v·N ≤ v·(본체+0x18c)` 분기의 본체+0x18c 정체 미확정 → 항상 단순 투영 `v −= N(v·N)`.
- **측면 접촉 ③**: 접지 중만이 아니라 공중에도 적용(공중에서 벽 쪽 이동 속도가 남지 않게) [추정]. → 2026-10-04: 공중 적용은 [실행]으로 확정(`[r6 player]`).
- 입력 우선순위 목록의 종류↔버튼(오징어 = ZL, 사격 = ZR, 서브 = R) [추정, player_state.md §6.1.1].
- 무기 표 이름: 무기 id `Shooter_Normal_00` → `WeaponShooterNormal`(번들 params 규칙). 없으면 생성자 기본값(Mid, AccType 1, MoveSpeed = 0x71058bbdac 0.072).
- `respawn` 의 `sinceJump = 100`(재점프 대기 없이 바로 점프 가능) — 원본 리셋 값 미확인, 웹 선택. → 2026-10-04 정정: 0x71023547bc 가 9999 를 쓴다(§1.4).

### 2.3 미구현

- 0x710245b2b4 의 특수·코옵·대시 패널·레일·잉크레일·Jetpack·Chariot·SuperLanding·나이스볼·연어런 분기, 넉백 벡터(본체+0x16c 감쇠·더하기는 외부 입력이 없어 0), 레일·발판 외부 속도, ImpactAndReject 충격·밀어냄(0), 벽 쪽 감쇠(본체+0x498/+0x48c), 미끄럼 계수에 따른 상승 억제 블록(0x710249bb60 > 0 && 접지), 경사 cap 비율(본체+0x1d8 필요 — 0.1 고정), 오징어 벽 속도 제한의 본체+0x1d4 벡터 부분.
- 점프: 0x710269e674(특정 상태), 본체+0xc18 카운터 배율, 0.07 상한 조건(bVar31), 바닥 플래그 0.06, 외부 상한 콜백, +0x4c0 감산, 점프 직후 지속 프레임 +0x77c 식(벽 근처 점프에서만 0 아님 — 평지 0).
- 오징어 롤(Somersault, 0x8d/0x8e), 벽 점프 차지(0x8f, 본체+0x774 증가 조건 bVar27 미판독), 0x780/0x782 플래그 writer. → 2026-10-04: 구현(§1.4).
- 슬롯19: A 제한(PC+0x1d0 침투 분류), 벽 낙하 끌어내림(b)(a44/a48), 이륙 관성·모서리 밀기(+0xfc, a74/a78), 안전 지점 기록, 다운 계열 카운터·쓰러짐 연출, Surprise(0x88) 요청.
- 상태기계: 사이드스텝·토관·슈퍼점프·스페셜·0x710244187c 의 무기별 분기(슈터만), 보조(상체) 레이어 SM+0xd0, 지연 요청, 사람 걷기 재생 속도식.

## 3. 미확정·추가 분석 필요

| 항목 | 풀리려면 |
|---|---|
| PlayerCamera+0x68 벡터 정체(입력 전방 축) | 카메라 메인 갱신 0x71024d9ae8 에서 +0x68 쓰기 추적 |
| ~~캡슐 기준점(발 + 0.6)~~ | 해소(2026-10-04 반영): 리셋 +r·up / write-back −r·up [실행] — §1.5 |
| ~~Phive 지지 판정 거리·OnGround↔InAir 전이~~ | 반영(2026-10-04): SplResultPlayer pass 0 분류·전이 [판독] — §1.5. 남은 것: 몸체 접촉 컬렉션 생산(PHY05), pass 1, S+0x08/+0x14 writer |
| 본체+0x488(x), +0x790, +0x78c writer | 입력 함수 0x710249f494 의 구조체 복사 경로 실행 추적 |
| 0x710246d060(SM+0xd4) | 디컴파일·실행 |
| 입력 링 버퍼(본체+0x9dcc..) 항목 의미 | 0x7102475a54 링 버퍼 writer |
| ~~GroundPaintMonitorRadius~~ | 해소: 발밑은 반경이 아니라 Disk 1×1 모니터(paint_and_score §7 [r6 paint]) — §1.5. 남은 것: 모니터 대상 식별 0x7102c71e50, 접촉 잉크 질의 0x7102c71a00, GPU 카운트 지연 프레임 |
| 몸체 local COM·형상 변경 시 COM | 복합 형상(ColGround+ColOthers) 질량 분포 함수 0x7100abf6e0 입력과 형상 재생성 3a66ea4 → 몸체 통지 3a7ffd0 의 COM 처리 |
| 침투 보정 flag(nativeManifold+92) producer | 0a15b70 앞단 manifold 생산(0a218f0 계열)의 +92 writer |
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
| `tests/physics_native_fixture.test.mjs` (2026-10-04) | 원본 실행 하네스를 사례 수만 줄여 다시 돌린 fixture(`web/tools/phy_port_fixture_dump.py` → `tests/fixtures/phy_native.json`, `phy_game.json`)와 비트 대조: solverInfo 64, 침투 target/old/carry 513, 단일 법선 충격량 513, 여러 행 순차 257, carry(상한 포함) 512, finalize(상한·double COM) 512, COM→원점 512, 초기 current 256, stage 선속도 setter 378(NaN·±inf 포함), write-back 256 중 S+0x210 ≥ 1, 접촉 정렬 512, 형상 행+쌍 필터 512, 하위 레이어 512, 발밑 델리게이트 512, 가중치 512, 원본 MT 첫 프레임 전체 사슬 1 | **전부 비트 일치** (16개) |
| `tests/player_body.test.mjs` (2026-10-04) | 몸체 경로 성질: write-back 매 프레임 비트, 평지 서기·걷기 높이 0 고정, 0.15 묻힘 첫 프레임 +0.0075(5%) 후 회복, 0.15 턱 오름·0.5 턱 막힘, 60° 면 Phive 지지 | 통과 |
| 전체 (2026-10-04) | `npm run typecheck` 통과, `npm test` 398/398 통과 | 통과 |
| 실제 에셋 node (2026-10-04) | Lby_Lobby00 1,120 프레임(걷기·옆걸음·오징어·점프·장거리) 평균 0.124 ms/프레임, 최대 7 ms(첫 프레임 포함), 리스폰 없음 | 확인 |
| 헤드리스 (2026-10-04) | playwright-core + Chrome(swiftshader), 개발 서버 PORT=5197: 키 입력 걷기·옆·오징어·점프 + 브라우저 번들 코어 직접 1,800 프레임(걷기·대각·오징어·점프 반복·사격 이동). console error·pageerror 0, NaN 0, 리스폰 0, 접지 중 평평한 바닥 아래로 내려간 최대 7.6e-8, 스텝 최대 9.2 ms. 이웃 기하 옆 1cm 미만 들림은 남음 | 확인 |

원본 실행 대조가 있는 것은 점프 수직 성분(함수 연결)과 기어 수치뿐이다. 수평 이동·cap·가속은 판독식 재구현이며 원본 실행 비교는 없다(0x710245b2b4 는 본체 포인터 수십 개가 필요).

## 5. 조정 요청

1. **DESIGN.md §4 이벤트 표**: `Jump` 에 `wall`(벽 점프 여부), `Land` 에 `air`(착지 전 공중 프레임, 공중 8 이하 착지는 0) 필드 추가.
2. **DESIGN.md §2 shared `player` 설명**: 소유 규칙(§1.3) — `weapon.{shooting,moveSpeed,frame}` 은 weapon 이 쓰고, `ink`·`inkRecoverStop`·`squidLock` 은 weapon/physics 공동(감소·설정은 weapon, 회복·카운트다운은 physics).
3. **[camera]**: shared `camera` 에 PlayerCamera+0x68 이 가리키는 벡터(판독되면)를 `right` 로 내 주면 physics 가 그대로 쓴다(지금은 rigForward 에서 만든 오른쪽).
4. **[weapon]**: 사격 자세를 `player.weapon.shooting` 에, 쓴 프레임을 `player.weapon.frame` 에 매 프레임 써 주면 physics 의 대체 판정(ZR 누름)이 꺼진다. 탄 생성 시 `player.squidLock = max(squidLock, min(param+0x50, [0x71058bdf0c]))`(player_state.md §6.1), `inkRecoverStop` 설정.
5. **[audio]/[render]**: 발밑 법선은 `groundN`, 지지 삼각형 재질은 `groundMaterial`(collision 재질 번호 → `world.collision.materialName()`), 이동 애니 속도값은 `animSpeed`, 변신 카운터는 `transform`, 재생 속도는 `stateRate`.
6. **core/types.ts**(선택): `Layer` 에 철망 같은 "플레이어만 막는 면"과 "플레이어 통과 면"을 구분하는 비트가 필요하면 추가 요청. 지금은 원시 Phive 필터를 `MeshCollisionWorld.material(i).hitMask/subMask` 로 노출하고 플레이어 몸 판정은 그것으로 한다.
7. ~~**[physics 몸체 담당] contact.ts** (2026-10-04)~~ 반영됨(2026-10-04, §1.5 슬롯19 입력): a38·a2c 식의 `const x = p.squidRequest ? 1 : 0` 을 `p.wallInput`(본체+0x488, move.ts 의 0x71024a7100)으로, 0x710249bb60 의 `1 − own²·x` 조건에 `p.squidInkFrames > 0`(본체+0x790)을 더하면 원본 식과 같다. 공중 바닥 법선 복귀의 `p.launch.active` 는 이제 L+0x3c 해제(0x7102477780)를 따른다.
8. **core/input.ts** (2026-10-04): 원본 패드 비트 4(Y, 카메라 리셋 래치 본체+0xab0 → 입력 전방 축 보간 비율 0)에 대응하는 `Btn` 이 없다. 추가되면 `inputPost(…, camResetPressed)` 로 넘긴다. 패드 비트 0/13(A/L, InputSender 종류 3 = 롤 gate +0x57)도 웹 입력에 없다.
9. **core/systems.ts 순서** (2026-10-04, SYS02 제안): 원본 한 프레임은 단계0[표적 슬롯18 → 플레이어 슬롯18 → 탄 슬롯18 → Phive Entity(캐릭터·native·탄 바디)] → 단계1[접촉 반응 큐(탄 슬롯22) → 표적 슬롯19/20/21 → 플레이어 슬롯19/20/21(카메라 메인 갱신 0x71024d9ae8 포함) → 탄 슬롯19/20/21] 이다(phive_controller §6.7). 지금 웹은 camera → player(18·Phive·19 를 한 번에) → weapon 이라 (a) 카메라가 플레이어 물리 **앞**에 돈다, (b) 탄 슬롯18·탄 바디 적분이 플레이어 슬롯19 **뒤**에 온다. 제안: player 시스템을 `stage0`(슬롯18 + Phive)과 `stage1`(슬롯19~21)로 나눠 등록할 수 있게 하고, 순서를 collision → range(18) → player.stage0 → weapon.stage0(탄 18·바디) → weapon 접촉 반응 → range(19~21) → player.stage1 → camera → weapon.stage1 → paint 로 둔다. player 쪽은 `stepPlayer` 안에서 이미 경계(“Phive Entity 월드” 주석)가 나뉘어 있어 함수 분리만 하면 된다.
10. **core/types.ts PaintWorld** (2026-10-04): 발밑 모니터용 `monitorCounts(pos, n): [팀0, 팀1, 팀2, 전체]`(PaintWorldImpl 에 추가)를 인터페이스에 올려 주면 index.ts 의 구조적 검사·`sample` 대체 경로를 없앨 수 있다.
11. **DESIGN.md §2 shared `player`** (2026-10-04): 몸체 상태(native COM·원점·접촉 cache·Result S·모니터)는 shared player 계약을 늘리지 않으려고 `body.ts bodyOf(player)`(WeakMap)로 둔다. 다른 영역이 읽어야 하면 이 함수를 쓰면 된다.

### 조정 처리 (2026-10-04)

- `core/systems.ts` 순서를 collision → range → **player → camera** → weapon → paint로 바꿨다. 원본은 카메라 메인이 플레이어 슬롯19 안, 물리 뒤에 돌고(phive_controller.md §6.7), 플레이어 슬롯18 이동은 직전 프레임 카메라 기저를 쓴다. 테스트 398개 통과, 헤드리스 701프레임 오류 0(`analysis/r7_player/browser_move.mjs`).
- `core/types.ts` `PaintWorld`에 선택 메서드 `monitorCounts`를 추가했다(§5 요청).
- 남은 조정: range·weapon 시스템을 슬롯18 단계와 슬롯19~21 단계로 나누는 전체 재배치(§5 제안), `core/input.ts`에 Y(카메라 리셋 래치 +0xab0)·A/L(롤 gate +0x57) 버튼 추가.
