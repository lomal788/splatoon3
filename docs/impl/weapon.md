# 스플래시슈터 탄·총 반영 기록 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

현재 사격장에서 입력 우선순위·6프레임 연사·탄과 분열 탄 생성 수명·잉크 소비/회복·표적 HP/휨을 연결했다. 사용자 지시로 코드를 반영했으며 전체 원본 물리/렌더 동등성 완료를 뜻하지 않는다. 이전 구현 기록은 이 문서 뒤에 보존한다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 / Lby_Lobby00 / 1인 / Shooter_Normal_00. 기존 [shooter_bullet](../weapon/shooter_bullet.md) §3.3.5~3.3.6·§3.5.1·§5.3~5.5, [aim_swerve](../camera/aim_swerve.md), [damage_hit](../combat/damage_hit.md) §6.4, [shooting_range](../range/shooting_range.md) §6.3 및 SHARED/FUNCS/decomp_index의 r5~r8 근거를 재사용했다. **새 원본 분석으로 중복 계상하지 않는다.**

## 3. 진입점과 전체 호출 흐름

player.readInput→mainInput(B4d0)→weapon 사격 게이트. 프레임 시작 활성 탄/방울 목록을 복사→기존 탄 pre→body physics→접촉→플레이어 사격(slot19 group3)→기존 탄 post19/21(group4)→방울 post→정리. 중간에 생성한 메인/분열 탄·벽 방울은 생성 프레임 갱신에 들어가지 않는다. 전체 actor scheduler의 이식은 SYS02에 남는다.

## 4. 구조체·필드·상수·열거형 표

| 원본 | 웹 producer/consumer | 이번 반영과 범위 |
|---|---|---|
| B4d0 / InputSender+54 | player.readInput / weapon/input.ts→actors.ts | raw Fire&&!Squid 대신 우선 입력·잠금·경계 게이트·s32 카운터 |
| Babc/Bab4 | shooter.tick | max(s32,1)-1, 사격 판단 이전 감소. Badc의 전체 writer는 미확정 |
| B698 | weapon consume / player recover | 기존 소비 허용 오차 유지 |
| B6a8/6ac/6b0 | stopInk/lackInk / recoverInk | 인간20·부족30·오징어 정지 독립 카운터, 음수 진행 |
| B6b4/6b8/6bc | stopInk/consumedInk / recoverInk | 소비 hold·잠영 frames/blend, 소비 시 후자 둘 초기화 |
| G match seed | runtime.matchSeeds / swerve | fresh Lobby (1,0,0,0), 가중합13. 원천 객체 부재 fallback10과 구분 |
| BulletShooter 예약32 | runtime.fire | 소비/RNG 후 빈 슬롯 없으면 생성/Fire 없음. 분열/방울 풀은 미연결 |
| DamageInfo.value | weapon→range receiver | raw 데미지 전달, 배율은 receiver에서 한 번 |
| BulletContactInfo | weapon physics contact→range | body center와 stepVelSec 전달, y=0·BulletImpulsScaler 적용 |

## 5. 상태 전이와 전체 수명

탄 age=-1 생성→다음 프레임 pre에서0→이동/접촉→post. age0 명중 시 첫 데미지360. 바닥 보관 도색은 같은 프레임 post19에서 실행하며, 벽 탄은 원본 hold4를 유지한다. 사격 시 인간 정지20 설정, 잉크 부족은 별도 정지30 설정. 회복 여부는 감소 **이전** 세 카운터 max<1로 결정한다.

2026-10-03 정정: 이전 기록의 사격을 모든 post 뒤에 두는 순서, 새 탄 첫 갱신 미확정, 기본 seed10, 회복 카운터 하나, 벽 방울 레이2개, 송신자 선배율 및 휨 vel 누락은 최신 원본 근거와 실제 코드로 교체했다. 이전 결론은 아래 보존 기록으로만 읽는다.

## 6. 계산식·조건·상세 의사코드

- input 게이트: 0x710249f494의 24a0ce0..24a0ec8 블록. 차단 시 frames=0/래치 해제; 허용 시 native main priority에 따라 s32 증가 또는0.
- countdown: 249fcb0..249fdc0의 max(s32,1)-1.
- recovery: previousMax=max(human,noInk,squid); 세 값을 s32로1씩 감소; previousMax≥1이면 회복 없음. 기본률 f32(1/f32(600)) / fast-stealth f32(1/f32(180)), gap과 min한 후 f32 가산.
- consumer state는 native 0x82..0x90/0xaa..0xac/0xed/0xee/0x10c. B7a0가 없으면 swimming으로 fast-stealth를 근사하므로 전체 회복 경로 완료가 아니다.
- 지형/대상 초기 sphere overlap을 이동 sweep보다 먼저 확인하여 t=0 접촉을 처리한다. WallDrop radius=.2 sphere overlap으로 벽/바닥을 판정하며 칠 불가 재질을 먼저 거른다. 실제 Havok 후보 순서/TOI 전체는 근사로 남는다.
- receiver 배율 예: raw360·rate.344 →123을 한 번만 기록, target HP1000→877. damage 수신과 물리 휨 접촉은 분리하여 Through 접촉도 별도 callback을 받는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

카메라 shared 기저/이전 프레임 조준 축을 유지한다. Fire/BulletSpawn/BulletHit/NoInk 기존 이벤트를 유지하며 BulletHit.age를 추가했다. 이번 총 포트로 ball VAT·분열 탄 전용 emitter·바닥 ink shading이 구현된 것은 아니다. 해당 시각 차이는 후속 [잉크 그래픽 분석](../port/ink_visuals.md)에서 다룬다.

## 8. 다른 기능과의 상호작용

core/types에 optional overlapSphere/BulletContactInfo/onBulletContact 계약을 추가했다. 기존 camera sweep이나 플레이어 body solver는 변경하지 않았다. range는 raw receiver와 물리 휨을 분리했다. 레거시 단위 vel 입력은 기존 테스트 호환 경로이며 실제 gun은 stepVelSec를 쓴다.

## 9. 웹 포팅 구조와 구현 순서

신규 core/weapon/input.ts·ink.ts → player 공급 → shooter/runtime 수명 → collision.overlapSphere → range 수신/접촉 순으로 반영했다. 고정 포트 ID BUL01·HIT01·TGT03를 반영 확인으로 이동했다. BUL03/04/06은 남은 producer/query가 있으므로 일부 반영을 유지한다. 상세 요약은 [port/weapon](../port/weapon.md).

## 10. 검증 코드·실행 결과·기대값

| 실제 명령/검사 | 결과 | 한계 |
|---|---|---|
| PY web/tools/weapon_port_fixture.py | 원본 함수 1,926건: input768/countdown262/consume384/rate128/stop128/timer256 | normal gate 경계 bool/InputSender 주입, offline/no gear40/no partial6d8, PLT ret0. whole frame 아님 |
| npm --prefix web test | 153/153 통과, 신규 native fixture 비트 일치 | 기존 재구현 fixture도 포함 |
| npm --prefix web run typecheck | 통과 | — |
| npm --prefix web run build | 통과 | — |
| node analysis/port_weapon/smoke.mjs | 실제 Lby 30발, 간격 모두6, Floor 명중·team paint4140 texels, 부족 타이머30/회복 경계, main 우선 입력, finite 값 | 수동 고정60Hz·Edge SwiftShader, 원본 화면 실행 아님 |
| console/page error·HTTP≥400 | 0 / 0 | GPU 화질 동등성은 별도 |

첫 실행의 native rate ABI 인자 오류로 UC_ERR_READ_UNMAPPED 발생→기존 weapon_ink_emu ABI(X1=pp,X4=B+a5d8)를 재사용하여 해결. decomp_index 기본 rebuild는 INDEX 쓰기 PermissionError→--no-build 성공. 초기 테스트의 z=2.2/정규화 길이 기대는 native sead 보간과 fresh Lobby seed로 바뀐 방향을 잘못 가정했으므로 body의 각 축 f32 적분식으로 검증했다. 카운터 하나 기대/없는 snapshot.bendWeight도 실제 계약으로 정정했다. 실패를 native 성공으로 세지 않았다.

보고 자료: analysis/port_weapon/before.json·weapon fixture·smoke.json·smoke.png. smoke의 inkAfter31 필드 저장에는 이전 잔량을 쓰는 보고 오류가 있어 그 값은 근거에서 제외한다. 회복 경계 자체의 assertion은 실제 31번째 값으로 통과했다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

- B7a0 지연 writer·회복 상위 게이트 연결: player_state §6.1.4. swimming 근사와 gear 조건 때문에 BUL06은 일부.
- 발사원점 B58·a90/4d4·일부 reset/Badc·GameFrame 시작값: shooter_bullet §3.5~5.5. fresh Lobby seed만 확정이며 매치 후 계승은 별도.
- native typed contact filter·두 형상 바디 TOI/후보 순서·천장/paint flag: PHY05/COL04/BUL04.
- Splash/WallDrop 예약 admission·실제 manager budget의 연결: 메인32만 적용.
- graphics ball VAT/color·floor shader·squid hide/thickness·최종 GPU: 시각 분석/포팅 항목으로 남는다.

---

# 이전 구현 기록 보존 — 2026-10-03 위 §5·§10 정정 우선

# [weapon] 메인 무기(스플래시슈터)·탄 구현 기록

담당 폴더: `games/splatoon3/core/weapon/`, 테스트 `games/splatoon3/tests/weapon_*.test.mjs`(+ 기대값 `weapon_fixture_*.json`).
근거 문서: [weapon/shooter_bullet.md](../weapon/shooter_bullet.md), [camera/aim_swerve.md](../camera/aim_swerve.md), [physics/phive_controller.md](../physics/phive_controller.md) §6, [combat/damage_hit.md](../combat/damage_hit.md), [paint/paint_shape.md](../paint/paint_shape.md), [effect_sound/effect_sound.md](../effect_sound/effect_sound.md) §3.2, [network/05_events_combat.md](../network/05_events_combat.md) §3.
이번 작업에서 새로 판독·에뮬한 것(아래 표의 "추가 분석")은 `analysis/notes/SHARED.md` 의 `[weapon impl]` 줄과 도구 `web/tools/weapon_*.py`, 디컴파일 `analysis/decomp/weapon/*.c` 에 있다.

상태(2026-10-02): 시험 사격장 1인 연습에서 사격 → 탄(직진·브레이크·자유낙하) → 스플래시 → 바닥 도색·벽 낙하 방울·표적 데미지까지 동작한다. 개발 서버 헤드리스 실행(실제 맵·플레이어·카메라·도색 시스템)에서 오류 없이 발사·착탄·도색(p 증가)을 확인했다.

## 1. 구현한 것

### 1.1 파일

| 파일 | 내용 | 원본 근거 |
|---|---|---|
| `params.ts` | 파라미터 형(MoveParam·CollisionParam·DamageParam·PaintParam·SplashPaint/Spawn·WeaponShooterParam·AdditionParam·TailLength·WallDrop 3종)과 생성자 기본값, `readParam`(ParamStore 결과에 기본값 보충), 무기 → 표 이름 | `analysis/param_reflect/*.json` 팩토리 기본값 [판독] |
| `move.ts` | 상태 머신 GoStraight/Brake/Free, 단계 전이, age 1 재정규화(len² = z² + (x²+y²)) | 0x71017657f4, Brake 본체 0x71017683fc(asm 연산 순서 대조), 0x71017659a4, 0x71017697f8, 0x7101763a10 |
| `body.ts` | 탄 바디: setVelocity(v·60), 스텝 `p1 = fl(dt·v60) + p0`(dt 0x3c888889), 막힘 `p0 + f·(p1−p0)`·속도 0, 충돌 끔 | 0x71016cb0a0, 0x7103b0a2bc, 0x7103b0a90c (physics §6.4) |
| `bullet.ts` | 탄 한 발(ShooterBase·SplashShooter 공용): 생성정보, age −1 시작, 슬롯18(prevPos → age++ → 슬롯54 → 슬롯57 → +0x12a), 정지 프레임, 꼬리(0.6/0.88 보간, DelayShotFrame 부터 꼬리 상태머신) | 0x7101645590(age = −1, vel = dir·(speed+info+0x68)), 0x71016460fc, 0x7101750d6c, 0x71017510c0 앞부분, 0x7101764ef8 / 0x71017ffb64 |
| `swerve.ts` | sead 시드(프레임 + 매치 시드 a..d), bias 곡선(logf/expf), 사인표 조회(fcvtzs·상위 8비트·하위 24비트 보간), 월드 Y축 로드리게스 회전(asm 순서), 흔들림·점프 bias, 연사 타이머·대기 | 0x7102583008 asm 0x71025839a8~0x7102583c64, 0x7102580f98, 0x7102551530, 0x710258295c |
| `sincos_table.ts` | sead 사인표 256×(sin, dsin, cos, dcos) f32 비트 | main 0x7104aa5b5c(*0x7105794810) [데이터] |
| `spawn.ts` | 발사 위치(ShotDirParam 베지어·총구 오프셋), 조준 기준 축 a, 초기 속도(플레이어 속도 가산), dir·speed 정규화, 분할 순열 표 | 0x7102552170·0x7102552710(추가 분석, 원본 에뮬 17/17), 0x71024df4e8, 0x71026beed0(asm), 0x71025823b0, 0x7104a9b0a1 |
| `shooter.ts` | 사격 처리(타이머 → 잉크 → 흔들림 → 생성), 입력 게이트(누른 프레임·사람 프레임·탭 래치·PreDelay), 잉크 소비·부족 규칙, InkAction(FireImpact/FireOn/FireOff) | 0x7102583008, 0x7102483134 0x7102485dc0~(추가 분석), 0x7102580780, 0x7102492120, 0x7102353718, 0x71025856c8, 0x71024b28b0, 0x7102864104/0x710286540c |
| `splash.ts` | 스플래시 일정(slot15), 이동 거리·최고 높이·생성 루프(slot56), 스플래시 하나 생성(위치 보간·전용 시드·기준 축·난수 X→Y→Z) | 0x710174efc0, 0x71017512bc→0x7101751304, 0x71017540ec, 0x71012500d4, 0x710174fe94 (추가 분석, 원본 에뮬 불일치 0) |
| `wall_drop.ts` | 벽 낙하 방울: 양자화·난수, 초기 속도, 3단계 미끄럼, 낙하(중력 0.008/0.015), 벽 도색(Shock/Fall·WallDrip 패턴·알파·쿨다운), 바닥 도색(무작위 회전), 솎아내기 링 | 0x7101648824, 0x7101646b10, 0x71018b0bd4, 0x71018ad66c, 0x71018ad26c, 0x71018ada10, 0x71018ae5e8, 0x71018ae054, 슬롯55/56 (추가 분석) |
| `damage.ts` | 데미지 감쇠, 충돌 반경, DamageRateInfo 조회(`damage_rate_info` 표), 배율 `fcvtzs((rate+1e-5)·dmg)`·상한 99998, 넉백 벡터 | 0x71017506d0, 0x71018a6b68/0x71018a6fe4, 0x7101a856e8, 0x7101a86ec0, 0x7101e66c4c |
| `paint_shape.ts` | 슈터 반폭(거리 보간·두 점 정렬)·깊이 비율(각도·BreakFree·[1,5])·수평 방향, 스플래시 반폭·깊이 | 0x7101751c08(asm 5.0 클램프 확인), 0x7101811b44 |
| `actors.ts` | shared `player`·`camera` 읽기(필드 이름은 §5) | — |
| `runtime.ts` | 한 프레임 조립(§1.2), 접촉 분배(슬롯22 → 58/59/60), 도색 요청, 벽 낙하 생성·접촉, 사격·잉크 포트, 정리·shared `bullets`·이벤트 | 슬롯22 0x71017504f4 → 0x7101646910, 슬롯58 0x7101764de4, 슬롯59 0x7101764ff8, 슬롯60 0x7101765794, 슬롯19 0x71016461bc, 슬롯21 0x7101646544 |
| `index.ts` | `createWeaponSystem` | — |

### 1.2 한 프레임 (weapon 시스템 step)

1. 탄마다 슬롯18: `age ≥ 0` 이면 prevPos 저장 → age++ → 슬롯54(정지 프레임이면 속도 0·감소, 0 이 되면 소멸 / age 0 은 상태머신만 진행하고 생성 속도 유지 / age 1 은 생성 속력으로 재정규화) → 꼬리 → 슬롯57 반경 → `+0x12a == 1` 이면 속도 0. 벽 낙하는 슬롯54(미끄럼·낙하).
2. 물리: 탄 바디 스텝(위 식). 충돌은 `world.collision.sweepSphere` 로 지형 구(Field 반경, Ground|Water)와 대상 구(Player 반경, Object)를 따로 질의해 작은 비율을 고름. 벽 낙하는 `pos += v`.
3. 접촉: 슬롯22(데미지 → `hittables.get(actor).onDamage`, `BulletHit` 이벤트) → 분배: Ground 가 아니면 슬롯60(+0x12a = 1), Ground 이고 법선 y > 0.64144969 면 슬롯58(도색 보관 + hold 0 + +0x12a = 1), 아니면 슬롯59(hold 4·벽 낙하 자식·충돌 끔·표시 위치 = 접촉점; 스플래시는 hold 0 → +0x12a = 1). 벽 낙하는 바닥·벽 접촉 콜백(도색).
4. 슬롯19: 꼬리 점 이동, 보관 도색 실행(`ShooterDeferred`), 낙하 소멸(발사 y − y ≥ DeactivateFallHeight). 슬롯21: y < −10 소멸, 슬롯56(이동 거리·최고 높이·스플래시 생성 — 슈터만), `+0x12a` 1→0 이면 소멸. 벽 낙하 슬롯55/56.
5. 사격(플레이어 0): 입력 게이트 → 0x7102583008 → 새 탄(다음 프레임부터 갱신) → `Fire`·`BulletSpawn`, InkAction 이벤트, 잉크·회복 정지·오징어 잠금 쓰기.
6. 소멸 처리(`BulletDie`), shared `bullets` 갱신, debug `weapon.*`.

순서 근거: 액터 계산 SplActor 0x7100f76a78(슬롯18) → 0x7100f76f78(슬롯19 묶음 → 슬롯21) [판독], 물리가 그 사이 [추정], 접촉 시퀀서가 18 과 19 사이(벽 낙하 +0x3d0 쓰기·읽기 순서) [추정 강함].

### 1.3 이벤트 (DESIGN.md §4)

| type | 필드 | 시점 |
|---|---|---|
| `Fire` | owner, team, pos, dir, vel, weapon, bullet | 탄 생성 성공(SLink "Fire", VariableShotRepeatStartFrame 0) |
| `FireImpact` / `FireOn` / `FireOff` | owner, weapon | InkAction 이 바뀐 프레임만(쏜 프레임 FireImpact, 다음 누름 프레임 FireOn, 뗀 프레임 FireOff) |
| `BulletSpawn` | id, kind("Shooter"/"Splash"/"WallDrop"), owner, team, pos, vel, parent? | 생성 |
| `BulletDie` | id, kind, pos | 소멸 처리 |
| `BulletHit` | id, kind, owner, team, pos(접촉점), normal, surface("Floor"/"Wall"/"Object"/"Water"), paintable, vel, row, target?, damage | 탄 접촉(벽 낙하 제외) |
| `NoInk` (신규) | owner | 잉크 부족 표시 요청(0x7100feb5c4(0) 호출 지점) |

### 1.4 shared `bullets` (`BulletView[]`, 표시용 읽기 전용)

`{ id, kind, owner, team, pos, prevPos, vel, radius, age, tail(슈터 꼬리 끝 +0x11d4, 시작 전 null), stuck(벽 정지 중) }`. 벽에 멈춘 탄의 pos 는 접촉점(원본 컴포넌트 0x38 로 액터 위치를 접촉점으로 옮김).

### 1.5 도색 요청 (`world.paint.request`)

| kind | 언제 | 값 |
|---|---|---|
| `ShooterDeferred` | 슈터 바닥 접촉 프레임의 슬롯19(보관 → 실행) | pos/normal = 접촉, dir = 속도 수평 정규화, widthHalf·depthScale(§0x7101751c08), seed = 접촉 시점 슬롯105 = min(GameFrame, 0x1745d1) |
| `Splash` | 스플래시 바닥 접촉(즉시) | widthHalf(최근접 여부)·depthScale(낙하 높이), dir = normalize(생성정보 +0x94, 0, +0x98) |
| `WallDrop` | 벽 낙하 벽 접촉(쿨다운 통과)·바닥 접촉 | widthHalf = 지름/2, depthScale 1, dir = (0,1,0)(벽) / (sin, 0, cos)(바닥), seed = min(+0x74+age+1, 0x1745d1), 추가 필드 `seedDirect`(= age + +0x74, 원본 C+0x18 = 1·C+0x1c), `inkTexType`(0 / WallDrip 0x1b+pat / 0x20+pat), `alpha`(0..255), `surface`("wall"/"ground") |

복제 탄이 없으므로 모든 요청이 로컬(+0x6d = 1). 칠 불가 재질(`collision.material(i).paintable === false`)이면 도색·벽 낙하를 만들지 않는다.

## 2. 원본과 다른 점

| 항목 | 웹 | 이유 |
|---|---|---|
| 충돌 판정 | hknp 쓸어 넘기기(구 2개 한 바디) 대신 CollisionWorld.sweepSphere 를 구마다 따로 부르고 가장 이른 접촉 하나만 처리. 정지한 탄(이동 0)은 질의하지 않음(원본은 f = 0 재접촉 가능) | 웹 충돌 계약. 좁은 단계 TOI(0x7105756468 처리기) 미판독 |
| 자기 플레이어 | 대상 질의에서 발사자 actor 를 뺌 | 원본 필터(같은 플레이어 무시) 미확인. 1인 연습이라 다른 플레이어 없음 |
| 벽 낙하 접촉 | 0.2 구 겹침 대신 아래·벽 법선 반대 방향 레이(길이 0.2) 2개 | CollisionWorld 에 겹침 질의 없음(조정 요청 4) |
| 벽 낙하 위치 적분 | `pos += v` | 일반 강체 적분 f32 순서 미판독 [추정] |
| 수신 처리 | 같은 팀이면 데미지 없음, 그 밖은 DamageRateInfo 배율·상한만 적용해 `DamageInfo.value` 로 넘김. 이력 모드·시간 창·ObjectEffect_Up·크리티컬 누적 링 없음(critical 항상 false) | 슈터 송신자 이력 모드 미확정, 크리티컬 needCount(+0x92)·shotKey(+0x94)는 TripleShot 무기만 씀 |
| 넉백 | 0x7101e66c4c 식으로 계산해 `info.knockback` 추가 필드로만 넘김 | DamageInfo 에 필드 없음(조정 요청 2) |
| 잉크 소비 계수 | 기어 0(MainInkSave 1.0), 꼬마슈터·코옵 계수 없음, partial 규칙(B+0x6d8) 없음 | 연습장 1인 |
| 사격 게이트 필드 | B+0x4d4·a90·+0x530/+0x531·+0xabc/+0xadc·+0xab4 를 무기 쪽에 둠. a90 은 `player.squid` 로 대신(오징어 상태 집합), abc/adc/ab4 감소는 매 프레임 1 [추정] | physics 쪽에 없음(조정 요청 1) |
| 게이트 입력 B+0x4d0 | `Fire && !Squid` 버튼 | 로컬 writer 미발견 [추정] |
| 발사 위치 기준점 | `player.pos` 를 본체+0x58 로 씀 | +0x58 writer·+0x10 과의 관계 [미확정] |
| logf/expf | f64 계산 후 f32 반올림 | 원본 libm 비트 미확인(1ulp 차 가능) |
| InkAction 보류 | FireOn 최소 유지(vt+0x148) 0, behavior+0x40 = 사격 입력 | 값 미확인 |
| 새 탄 첫 갱신 | 생성한 다음 프레임 | 액터 생성 시점 [미확정] |
| 매치 시드 a..d | 기본 (1,2,3,4)·+0x120 = 10(원천 객체 없음 경로), `tables.match_seed {a,b,c,d}` 가 있으면 13a+59b+71c+97d | 연습장에서 어느 경로인지 [미확정] |
| 스플래시가 만드는 벽 낙하 | BulletSplashShooter 표의 WallDropMoveParam·WallDropCollisionPaintParam 사용 | 슬롯61 이 어느 표 핸들을 읽는지는 [추정](표에 값이 있음 [데이터]) |
| 탄 풀 | ActorReservation(슈터 32·스플래시 32·벽 낙하 16)·생성 판정 0x71016e3af4 없음(항상 생성) | 0x71016e3af4 미판독 |
| GameFrame | `world.frame` | 연습장 GameFrame 시작값 미확인 |

## 3. 미확정·추가 분석 필요

| 항목 | 보면 풀리는 것 |
|---|---|
| 접촉 시퀀서의 정확한 위치(첫 명중 age, +0x12a == 1 검사의 의미) | 시퀀서 기반 0x7103c7e4d8 실행 목록과 물리 스텝 호출 위치 |
| 본체+0x58 writer | 플레이어 위치 갱신(슬롯19 Phive 뒤) |
| a90(사람 프레임) 증감 정확한 상태 집합·B+0x4d0 로컬 writer | 0x71024a2c98, 입력 함수 |
| 서브·스페셜 입력이 block 에 더하는 조건 | 0x7102486560~ |
| 벽 낙하 flag `0x71012ed800`·재질 bit25(천장·바닥 칠 생략) | 해당 함수, PhiveConfig 재질 플래그 |
| 생성 판정 0x71016e3af4(풀·예산) | 함수 판독 |
| 꼬리 MaxLength 계열 사용처 | 그리기 경로 |
| [0x71058e8784](낙하 소멸 예외 영역 LocatorBulletCheckFallIgnoreArea) 런타임 값 | 맵 데이터 |
| 연습장 매치 시드·GameFrame 시작값 | 로비 대전 설정 객체(G+0xc8) 생성 경로 |

## 4. 검증

`npm test`(전체 통과), `npm run typecheck`(오류 0). 기대값은 모두 재구현 도구 출력이고, 그 도구 중 원본 실행과 대조한 것은 표에 적었다.

| 테스트 | 대조 대상 | 결과 |
|---|---|---|
| `weapon_move.test.mjs` 상태머신·바디 적분 age 0~29(발사각 0°/+30°/−20°) | `bullet_shooter_sim.py`(age −1 정정판) 속도 + `bulletbody_integrate.body_step` 위치, 비트 | 일치(90행 × 속도·위치 비트) |
| 같은 파일 §10 표 대표값 | 문서 표(갱신 회차 기준) | 일치 |
| `weapon_swerve.test.mjs` bias 곡선 54점·사인표 8점·연사 흔들림 방향(수평 조준 / 임의 조준+점프) | `camera_swerve.py`(같은 시드식·사인표) 비트 | 일치 |
| 같은 파일 연사 타이머 | aim_swerve.md §10(RepeatFrame 6, 대기 후 0프레임째) | 일치 |
| `weapon_spawn.test.mjs` 초기 속도 4경우 + 2경우 | `bullet_shooter_sim.initial_velocity` 비트 | 일치 |
| 같은 파일 발사 위치 17경우 | `weapon_spawnpos_emu.py` **원본 unicorn 실행**과 비트 일치한 표 | 일치 |
| 같은 파일 분할 순열 표 N=2..15 | main 0x7104a9b0a1 덤프 | 일치 |
| `weapon_splash.test.mjs` 일정(idx 0~7)·생성 위치·방향·속력·도색 방향(y < −10 까지) | `weapon_splash_sim.py`(**원본 에뮬 `weapon_splash_emu.py` 와 불일치 0**) 비트 | 일치 |
| `weapon_walldrop.test.mjs` 양자화·60프레임 위치·속도·가속·쿨다운·벽 도색 프레임/크기/패턴/알파·바닥 회전 | `weapon_walldrop_sim.py`(판독식 재구현) 비트 | 일치 |
| `weapon_damage.test.mjs` 감쇠(age 0~7 → 360, 8 → 354, 9 → 348, 38 → 185, 39+ → 180)·합성 경계·반경·배율(0.344×843 → 290) | `combat_damage.py selftest`/`weapon` | 일치 |
| `weapon_ink.test.mjs` 소비량 0x3c16bb99·회복량 0x3ada740e·108발 잔량 0.006400978·리셋 phase 0x3f555555/rem 0x3f800001·1/7/13 프레임 발사 | `weapon_ink_emu.py`(**원본 실행** 일치 표) | 일치 |
| `weapon_runtime.test.mjs` 사격 게이트(리스폰 후 8프레임째, 6 간격, 탭 래치, 오징어 해제 후 9프레임), age 0 첫 갱신, 표적 데미지, 바닥 보관 도색, 벽 4프레임 정지·벽 낙하 Shock 칠, 잉크 108발·NoInk·회복 정지 20/30·오징어 잠금 4 | 위 판독식(가짜 충돌 세계) | 통과 |
| 헤드리스 실행(개발 서버, 실제 맵·player·camera·paint) | 120프레임 사격 | 오류 없음, Fire 6간격·스플래시·바닥 명중·Paint, paint p 11 |

데미지 경계의 age 는 탄 +0x134(첫 갱신 0)이다. 수평 발사 탄이 첫 갱신에서 바로 맞으면 age 0 → 360.

## 5. 조정 요청

1. **[physics] shared `player`** — 지금 읽고 쓰는 필드: 읽기 `id`, `team`, `pos`(본체+0x58 로 씀), `final`(본체+0xe4, 탄 초기 속도 가산), `squid`, `airFrames`, `respawns`(바뀌면 무기 리셋), 이번 프레임 `Jump` 이벤트(점프 흔들림 vt40). 쓰기 `ink`(소비), `inkRecoverStop`(= max(·, 20) 발사 틱마다, 부족 중 ZR 이면 max(·, 30)), `squidLock`(본체+0xac4 = max(·, min(PostDelay 4, 6)) 트리거 경로마다, 발사 시 max(·, 4)), `weapon.shooting/moveSpeed/frame`.
   - 원본은 회복 정지 카운터가 셋(+0x6a8 사람, +0x6b0 오징어, +0x6ac 부족)이고 회복은 셋의 max < 1 일 때, 카운터는 음수까지 내려간다. 잠복 회복 1/180·사람 Std 1/600, 0x7102492120 성공 시 B+0x6b8/+0x6bc(잠복 상태) = 0 — SHARED `[weapon impl]` 잉크 줄. physics 회복 구현에 반영 부탁.
   - 사격 게이트 필드(B+0x4d4, a90, +0x530/+0x531, +0xabc, +0xadc, +0xab4)는 본체 필드라 physics 가 갖는 것이 원본 구조와 맞다. 옮기면 무기는 읽기만 하겠다.
2. **[조정] `core/types.ts DamageInfo`** 에 `knockback?: Vec3`(0x7101e66c4c, 수신 쪽이 ×1/3600·|v| ≤ 0.48) 추가 제안. 지금은 무기가 추가 필드 `knockback`, `age`, `raw`(배율 전), `bullet` 를 같이 넘긴다. `value` 는 배율 적용 후 값.
3. **[조정] `core/types.ts PaintRequest`** 에 선택 필드 `inkTexType?`, `alpha?`(0..255), `seedDirect?` 추가 제안(벽 낙하 WallDrip 패턴·알파·직접 시드). **[paint]** `kind: "WallDrop"` 요청의 `surface: "wall"` 은 `inkTexType`(0 = Shot00 첫 칠, 0x1b+pat WallDrip00, 0x20+pat WallDrip01)·`alpha` 를 써 주기 바람. 슈터 바닥 도색은 무기가 보관 → 슬롯19 실행을 이미 하므로 `ShooterDeferred` 로 보낸다(같은 프레임).
4. **[조정] `CollisionWorld`** 에 구 겹침 질의(`overlapSphere(center, r, mask): Hit[]`) 추가 제안 — 벽 낙하 접촉(원본 CollectGroundOnly)과 슬롯59 재질의에 필요. 지금은 레이 2개로 대신함.
5. **[조정] DESIGN.md §4** 이벤트 표: `NoInk {owner}` 추가, `BulletSpawn`/`BulletHit` 필드(위 1.3) 갱신, kind 에 "WallDrop" 추가.
6. **[assets]** `weapon_spec.json` 의 `bulletSetting` 이 `$missing` — RSDB `BulletSettingInfo`(BulletShooterBase·BulletSplashShooter 행: DeactivateFallHeight·DeactivateFrame·WallDropPositionStoreNum·WallDropThinOutDistance)를 넣어 주면 무기 쪽 상수 표(`runtime.ts BULLET_SETTING`, 데이터 값 그대로)를 대체하겠다. 매치 시드가 정해지면 `data/match_seed.json {a,b,c,d}`.
7. **[camera]** 읽는 필드: `aimDir`, `rigForward`, `pitchNorm`, `pos`, `target`(축 a). 원본은 축 a 를 PlayerCamera+0x3c 기저(직전 갱신값)에서 읽으므로 카메라가 "수직에 가까우면 갱신 안 함" 결과 벡터를 따로 내주면 그걸 쓰겠다.
8. **[조정] 시스템 순서**: 원본은 플레이어 슬롯19(0x7102483134) 안에서 잉크액션 발사(0x7102486a40 → 0x7102583008)가 돌고, 탄 액터 계산과의 순서는 [미확정]. 지금(player → weapon)을 유지.
