# range — 시험 사격장 구현 기록

2026-10-03 탄·총 통합 정정: weapon은 raw damage를 넘기고 target receiver에서 rate를 한 번만 적용한다. 물리 contact callback을 DamageInfo와 분리하여 body center·stepVelSec·y=0·BulletImpulsScaler를 휨에 연결했다. 실제 총/표적 fixture에서 damage123 및 HP877·휨 활성 확인. 과거 info.vel 누락/단위 미확정 기록은 이 연결 범위에서 정정한다. 근거·153개 테스트 결과는 [weapon.md](weapon.md) §4~10. 아래는 이전 구현 기록을 보존한다.

담당 폴더: `games/splatoon3/core/range/`, `games/splatoon3/client/range/`. 분석 명세: [../range/shooting_range.md](../range/shooting_range.md)(이하 "명세").
공유 키: `world.shared.get("range")` = `RangeShared`(core/range/index.ts). 이벤트: `Damage`, `Break`.

## 1. 구현한 것

| 항목 | 파일 | 근거(명세 절·원본 주소) |
|---|---|---|
| 배치 읽기: [assets] `placement.json`(actors/rails, 해시 문자열) 또는 원본 Banc(Actors/Rails) | `core/range/placement.ts` | stage_gimmicks §3, docs/impl/assets.md |
| 표적 생성: `SighterTarget`·`_Large`·`_Move` (팁 시험 `_TipsTrial*` 는 기본 제외, `createRangeSystem({ includeTipsTrial: true })` 로 생성 가능) | `core/range/index.ts` | 명세 §1, §11(팁 시험 표적은 시작 시 비활성으로 보임) |
| 파라미터: 맵 번들 `params/SighterTarget*.json`(ParamStore, `$parent` 필드 단위) 우선, 없으면 `data.ts` 의 원본 값(데이터·생성자 판독값) | `core/range/data.ts`, `index.ts` | 명세 §4.1, §4.2 |
| 상태 기계 Wait/DamageShot/Burst/BurstWait/Expand/Flick, enter/exec, 같은 상태 재전이, counter(f32) 규칙 | `core/range/target.ts` | 명세 §5.2, 0x710125a178/0x710125a394 |
| HP 홀더(누적 → 다음 갱신에서 감소, 0 클램프), 리셋 | `target.ts` | player_life §6.1, 0x7101a88e1c |
| 리시버: 같은 팀 Through, 무적 모드(추가 배율 0·결과 4), DamageRate(행=무기, 열 `Default`) `+1e-5`·절삭, 99998 상한 | `target.ts computeResult` | 명세 §6.1, damage_hit §6.4 |
| 표적 리스너: 누계 += dmg, DamageShot 전이 | `target.ts receive` | 0x71021ef25c |
| BurstWait HP 다시 채우기·Expand 전이, Wait 120프레임 초과 → Flick | `target.ts` | 명세 §6.2, 0x71021f1a9c, 0x71021f11f0 |
| 휨 계산기(충격·Kd/Kp 감쇠·단위 클램프·방향각) | `target.ts` | 명세 §6.3, 0x7101e3422c, 0x7101e33ed8, 0x7101e34468 |
| 데미지 숫자 값·위치·isMax·표시 조건(거리 판정은 화면 쪽 카메라 위치) | `target.ts`, `client/range` | 명세 §6.4, 0x71021efc24 |
| 이동 표적 레일(일정·cSpeed 역방향 양수 시간·cSin·점 회전 slerp), 리셋 시 시작 점 위치, 프레임당 0.016666668초 | `core/range/rail.ts` | 명세 §6.5, stage_misc §1.3~§1.5 |
| 표적 팀 = 로컬 플레이어 팀 == 1 ? 0 : 1 | `index.ts teamOf` | 명세 §5.1 |
| 사격 구역 판정(Cube ≤, Cylinder 바닥 원점·높이 2Sy·r² < R²), 무기 허용 래치(공중 프레임 < 4 일 때만 갱신) | `core/range/area.ts` | 명세 §6.6 |
| 시작 위치 목록(StartPos/StartPosTipsTrial 이름·팀·위치·회전) | `index.ts` | 명세 §1 |
| 화면: 맵 번들 `parts/Obj_SighterTarget(.glb)`·`Obj_SighterTargetMove.glb` 스킨 모델(없으면 임시 캡슐), 보간, 데미지 숫자 DOM | `client/range/index.ts` | 명세 §7 |

### 1.1 충돌 등록 (`world.collision.setDynamic`)

| 몸 | id | 모양 | 레이어 | 비고 |
|---|---|---|---|---|
| ColBullet | 표적 Hittable id | 캡슐 (0,0.35,0)–(0,1.3,0) r 0.35 × 스케일 | `Layer.Object` | 탄이 맞는 몸(원본 마스크 SplPlayerSensor ⊃ SplInkBullet) |
| Main | 별도 id(`world.newId()`) | 캡슐 (0,0.39,0)–(0,1.26,0.35) r 0.39 × 스케일 | `Layer.KeepOut` | 플레이어를 막는 몸(원본 마스크 SplPlayerColOthers, 잉크탄 제외) |

Burst·BurstWait 동안 둘 다 `setDynamic(id, null)`. 이동 표적은 매 스텝 갱신, 고정 표적은 켜질 때 한 번.

### 1.2 공유 상태 `range` (`RangeShared`)

`targets[]`: id, kind, model, pos, rot(사원수 x,y,z,w), scale, team, state/stateName, anim/animFrame/animFrames, hp/maxHp, bodiesEnabled, bend{on, angleDeg, weight}, damageInfo{active, value, isMax, pos, distance}. `areas[]`, `inShootingArea`, `canShoot`, `startPositions[]`.

### 1.3 이벤트

| type | 필드 | 원본 대응 |
|---|---|---|
| `Damage` | target, value(최종, 0.1 HP), result(game::DamageResultType: 0 Through, 4 Invincible, 6 Damaged), critical, pos, attacker | 리시버 결과 → HitEffect |
| `Break` | target, pos, user(ELink 사용자: SighterTarget / SighterTargetBig / SighterTarget_TipsTrial) | Burst enter 의 `Break`(0x71021f14a0) |

## 2. 원본과 다른 점

| 항목 | 이유 | 동등성 |
|---|---|---|
| DamageHelper 홀더 갱신을 표적 vt18 바로 앞에 둠 | 원본 순서 [미확정] | 한 프레임 차 가능(명세 §11) |
| 애니 프레임 = 0 에서 시작, 스텝마다 +1(exec 뒤) | 애니 보조 갱신 미판독 | 상태 지속 프레임이 ±1 다를 수 있음 |
| 몸 값 보간(0x71021f0dcc, Expand 중 충돌 크기 변화로 추정)은 안 함 — Expand 동안 충돌은 전체 크기 | 대상 필드 의미 [미확정] | Expand 중엔 어차피 무적(데미지 0) |
| 휨 충격(탄)은 `DamageInfo.vel`(프레임당, 확장 필드)이 있을 때만, 속도 × 60(초당 가정) | 공용 계약에 속도 없음, 원본 단위 [미확정] | 조정 요청 1 |
| 플레이어·폭탄 접촉 휨 충격 없음 | 플레이어 접촉 정보·폭탄 미구현 | |
| 수신 이력 모드·시간 창·ObjectEffect_Up(기어) 없음 | 송신자 쪽 미확정 / 기어 없음 | 슈터 연습에는 영향 없음 [추정] |
| 화면: 원본 스켈레탈 애니 없음 → Burst·BurstWait 숨김, Expand 크기 0→1, 휨은 `leg` 뼈를 각·무게 방향으로 최대 0.35rad 기울임(**표시용 임시 값**), isMax 는 노란색 | 에셋에 클립 없음 | 조정 요청 2 |
| 데미지 숫자는 DOM(`toFixed(1)`) | 레이아웃 Shr_Points_00 미이식 | 형식 "정수.소수"는 메시지 데이터 [데이터], 1자리 [추정] |
| 팁 시험·나무 인형·PaintedArea·기믹 스포너 없음 | 1차 범위 밖 | 명세 §1 |

## 3. 미확정·추가 분석 필요

명세 §11 표 그대로. 구현에 영향이 큰 것: 홀더 갱신 순서, 애니 진행 규칙, 접촉 속도 단위, 사격 구역 래치의 실제 효과(어디서 사격을 막는지).

## 4. 검증

| 테스트 | 내용 |
|---|---|
| `tests/range_target.test.mjs` (8) | 생성·팀·충돌, 피격→DamageShot→Wait(31스텝), Through, 파괴 수명(Burst→BurstWait 122→Expand 45→Wait, 무적 Invincible), Flick(153스텝), 이동 표적, 휨 방향, 에셋 파라미터 표 경로 |
| `tests/range_rail.test.mjs` (6) | 로비 레일 A 실제 값: 구간·주기·sin·역방향·회전·advance·cStop/WaitTime/BreakTime·기본값 |
| `tests/range_area.test.mjs` (4) | 실제 구역 값: Cube 경계, 회전 Cube, Cylinder, 래치 |
| `client/range/dev/shot.mjs` | 개발 서버 + 헤드리스 Chrome: 실제 번들로 17개 표적, 피격 숫자 36.0, 깨짐 108.0, 숨김·복귀 스크린샷(`test/out/range_*.png`). 앱 루프를 멈추고 월드 스텝 + 이 뷰 + 렌더만 직접 구동(다른 뷰 상태와 분리) |

모두 판독식 재구현 + 합성 입력이며 원본 실행 대조가 아닙니다. `npm run typecheck`, `npm test` 통과.

## 5. 조정 요청

1. **공용 계약 `core/types.ts` `DamageInfo`** — 선택 필드 `vel?: Vec3`(탄 속도, 프레임당) 추가 요청. 원본 표적 휨 충격은 접촉 속도(y=0) × BulletImpulsScaler(명세 §6.3). 지금은 `(info as …).vel` 로 읽고 없으면 휨 충격 없음. [weapon] 이 탄 속도를 넣어 주면 됨.
2. **[assets]** `maps/<map>/parts/Obj_SighterTarget.glb`·`Obj_SighterTargetMove.glb` 에 스켈레탈 클립 추가 요청: `DamageShot`(30), `DamageShotBend`(360, 반복 — 프레임=휨각°, 가산), `Brust`(1), `Expand`(45), `Flick`(24) (모두 `romfs/Model/Obj_SighterTarget.bfres.zs` 안). 파편 모델 `Fragment00`, `Fragment01`(같은 bfres), 머티리얼 애니 `Damage`(100) 도 가능하면. 받으면 임시 표시(숨김·크기·기울기)를 클립 재생으로 바꿈.
3. **[assets]** `common/data/param_defaults.json` 에 `spl__SighterTargetParam`(명세 §4.1 표), `spl__BendCalculatorParam`(Kp 0, Kd 0), `game__RailMovableSequentialParam`(stage_misc §1.2 표) 추가 요청. 지금은 `core/range/data.ts` 의 같은 값으로 대신함.
4. **DESIGN.md 이벤트 표** — `Damage` 행에 `result`, `attacker` 필드 추가, 새 행 `Break | range | target, pos, user | ELink "Break"(SighterTarget Burst)` 등록 요청.
5. **[physics] `shared.player`** — 사격 구역 판정에 로컬 플레이어 `pos`(발 위치, 본체+0x10 에 해당)와 `airFrames`(본체+0xc0 공중 프레임)가 필요. 지금은 `shared.get("player")?.pos/.airFrames` 를 읽고 없으면 판정하지 않음. 또는 [physics]/[weapon] 이 `core/range` 의 `insideAnyArea`/`updateShootLatch` 를 직접 써도 됨.
6. **[physics]/[weapon]** — 원본은 로비에서 본체+0x938c(= `range.canShoot`)를 입력·상태 선택 쪽에서 씀(명세 §6.6). 사격 허용 게이트로 쓸지 결정 필요(효과는 [추정]).
7. **[physics]/[weapon] 충돌 레이어 확인** — 표적 ColBullet 을 `Layer.Object`, Main 을 `Layer.KeepOut` 으로 등록함(§1.1). 탄 질의 마스크가 `Object` 를, 플레이어 이동 질의가 `KeepOut` 을 포함해야 함. `Object` 를 플레이어 이동이 막는 레이어로 쓰면 원본(ColBullet 은 플레이어와 충돌 안 함)과 다름.
8. (관찰, [fx] 영역) 헤드리스 실행에서 `client/audio` 의 `AudioSystem.hitEffect → slink("HitEffect")` 가 `new XLinkInstance` 에서 `null.parent` 로 매 프레임 예외 → 앱 rAF 루프가 첫 프레임에서 멈춤(2026-10-02 개발 서버, 사격장 코드와 무관).
