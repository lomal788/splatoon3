# 시험 사격장: 표적·사격 구역·시작 위치 (range)

Splatoon 3 v0 대전 로비(`LobbyVersus` 씬, 배치 `Banc/Lby_Lobby00`)의 시험 사격장을 원본 코드·데이터로 정리합니다. 중심은 표적 `spl::SighterTarget`(일반·대형·이동)이고, 사격 구역(`LobbyShootingArea`), 시작 위치, 팁 시험(TipsTrial) 계열·나무 인형·PaintedArea 는 1차 범위 밖이라 무엇인지와 확인한 만큼만 적었습니다.

- 작업 지침: [../../분석.txt](../../분석.txt). 확정 수준: **[실행]** 원본 실행, **[판독]** 원본 명령/디컴파일 판독, **[데이터]** 데이터 확인, **[재구현]** 재구현 계산, **[추정]**, **[미확정]**.
- 상태: 표적 동작은 **분석 완료(일부 미확정 §11)**, 웹 구현은 [../impl/range.md](../impl/range.md). 원본 실행 대조는 없습니다("분석 완료" ≠ "구현 완료" ≠ "동작 검증 완료").
- 연결 문서: 데미지 단위·배율·리시버 [../combat/damage_hit.md](../combat/damage_hit.md), HP 홀더 [../combat/player_life.md](../combat/player_life.md) §4.1·§6.1, 레일 이동 [../gimmick/stage_misc.md](../gimmick/stage_misc.md) §1.2~§1.5, Banc 형식 [../gimmick/stage_gimmicks.md](../gimmick/stage_gimmicks.md) §3.

---

## 1. 기능 개요와 사용자에게 보이는 동작

| 대상 | 개수(Banc) | 보이는 동작 | 확정 수준 |
|---|---|---|---|
| `SighterTarget` | 12 | 맞으면 흔들리고(DamageShot 30프레임) 휜다(DamageShotBend). 머리 위에 받은 데미지 누계가 `36.0` 형식으로 뜬다. HP 1000(=100.0)을 다 깎으면 터지고(Brust) 사라졌다가 2초 뒤 다시 솟는다(Expand 45프레임). 120프레임 넘게 안 맞으면 털어내며(Flick 24프레임) HP·누계가 처음으로 | [판독] |
| `SighterTarget_Large` | 2 | 같은 동작, HP 5000, 크기 1.3배, ELink 사용자 `SighterTargetBig` | [데이터]+[판독] |
| `SighterTarget_Move` | 3 | 같은 동작 + 레일(LiftRail)을 따라 왕복. 속도 7/4/5(초당 단위), sin 가감속, 끝에서 바로 되돌아옴 | [판독]+[데이터] |
| `SighterTarget_TipsTrial`(18), `_TipsTrialMove`(2) | 20 | 팁 시험(로비 연습 과제) 전용 표적. 깨지면 다시 솟지 않음(Burst 에 머묾). 시작 시 비활성으로 보임 | [판독]+[추정] |
| `LobbyShootingArea`(3, Cube) / `_Cylinder`(1) | 4 | 로컬 플레이어가 이 안에 있는지 매 프레임 판정 → 플레이어 본체 플래그(무기 사용 관련) | [판독]+[데이터], 효과는 [추정] |
| `StartPos`(10) | | Alpha 시작 1개, 결과 화면 `ResultPlayer0~7`, 리플레이 복귀 `FromReplay` | [데이터] |
| `StartPosTipsTrial`(17) | | 팁 시험 시작 위치(`Aim`, `Front10m`~`Front30m`, `MoveTarget`, `Charger`, `IkaFlip`, `IkaNet`, `GyroCamera`, `WoodenFigure`, `SpSuperHock`, `Restore`) | [데이터] |
| `WoodenFigure` | 1 | 상호작용(가이드 `WoodenFigureOn`, 반경 3)으로 켜는 나무 인형. 슈터·스플래시봄을 들고 쏘고 던짐(애니 `PowerOn`, `Shooting_Shooter`, `Hold_Bomb`, `Throw_Bomb`). HP 9999 | [데이터]+[판독-부분] |
| `PaintedArea_Cube`(8) / `_Cylinder`(19) | 27 | 초기화 때 영역을 팀 잉크(배치 팀 Alpha)로 칠하는 로케이터 | [판독-부분] |
| `SpawnerForShieldGimmick_TipsTrial`(2, Bravo) / `SpawnerForBeaconGimmick_TipsTrial`(1) | | 팁 시험용 스플래시실드·비컨 기믹 스포너 | [데이터] |

거리 단위 확인: `StartPosTipsTrial "Front10m"`(15.5, 0, 12.75)과 팁 시험 표적(15.5, 0, 22.75)의 거리가 10.0 → 게임 1단위 = 1 m 로 이름 붙어 있음 [데이터].

## 2. 분석 대상 원본·버전·자료 위치

| 항목 | 위치 |
|---|---|
| 씬 | `romfs/Pack/Scene/LobbyVersus.pack.zs` → `Banc/Lby_Lobby00.bcett.byml`(해제본 `analysis/range/pack_LobbyVersus/`), 로직 `Logic/Lby_Lobby00_5bad.logic.root.ainb`(AiGroups 가 WoodenFigure·PaintedArea·TipsTrial 표적을 참조) |
| 사격장 액터 발췌 | `analysis/range/banc_range_dump.txt` |
| 액터 팩 | `romfs/Pack/Actor/SighterTarget*.pack.zs` 등 → `analysis/range/actor/<이름>/` (`--json` 사본) |
| RSDB | `ActorInfo`(→ `analysis/range/ActorInfo.json`), `LocatorInfo`(→ `analysis/range/LocatorInfo.json`: 영역 ShapeType·Scale) |
| 모델 | `romfs/Model/Obj_SighterTarget.bfres.zs` → 덤프 `analysis/range/Obj_SighterTarget_dump.json`(모델 4: Fragment00/01, Obj_SighterTarget, Obj_SighterTargetMove; 스켈레탈 애니 5, 머티리얼 애니 1) |
| 데미지 숫자 레이아웃 | `Layout/Shr_Points_00.Nin_NX_NVN.blarc.zs`, 메시지 `analysis/ui/msbt_KRko/LayoutMsg/Shr_Points_00.json` |
| 디컴파일 | `analysis/decomp/range/`: `sighter_vt.c`(+`_annot.c`, vtable 전 슬롯), `sighter_helpers.c`(상태 기계·휨·애니 보조), `rail_helper.c`, `area_inside.c`, `painted_area.c`, `wooden_figure.c`, `points_ui.c`, `burst_notice.c` |

## 3. 진입점과 전체 호출 흐름

### 3.1 클래스와 vtable [판독]

`Behavior.ClassName "spl::SighterTarget"` → vtable `0x7105615188`(59 슬롯), getName `0x71021ee658`, 크기 `0x1e0`(슬롯4), 생성 `0x71021ee4dc`. 슬롯 의미는 InkRail·Sponge 와 같은 액터 규약(vt8 초기화, vt15 리셋, vt18 프레임, vt22 접촉)입니다.

| 슬롯 | 주소 | 내용 |
|---|---|---|
| 7 | `0x71021ee66c` | 상태 기계(+0x128) 6개 등록: `cWait`, `cDamageShot`, `cBurst`, `cBurstWait`, `cExpand`, `cFlick`. 상태 i 의 enter = vt[47+2i], exec = vt[48+2i](멤버 포인터 vtable 오프셋 0x178+0x10·i) |
| 8 | `0x71021eec40` | 초기화: 강체 `Main`→+0x108, `ColBullet`→+0x110, 각 몸 값(+0xdc)을 +0x118/+0x11c 에 저장, 애니 보조(+0x170) 생성. `IsTipsTrial` 이면 `[액터+0x348]+0x3b = 0` |
| 9 | `0x71021ef144` | 리시버(DamageHelper 두 번째 목록 첫 항목)에 리스너 `0x71021ef25c` 등록, 리시버+0x1fc(시간 창 사용) = 0 |
| 11 | `0x71021ef2cc` | 해제 |
| 15 | `0x71021ef388` | 리셋(§5.1) |
| 18 | `0x71021ef9f8` | 프레임 갱신(§3.2) |
| 19 | `0x71021efc24` | 데미지 숫자 표시(§6.4) |
| 22 | `0x71021f0348` | 물리 접촉 → 휨 충격(§6.3) |
| 28 | `0x71021f0a94` | `Scale` 파라미터 → 액터 스케일(+0x2bc..+0x2c4), 바뀌면 컴포넌트마다 vt+0x50 통지 |
| 36 | `0x71020caea0` | 컴포넌트 생성: `spl::BendCalculator`(+0x180), `game::AnimationAddable`(+0x188), `spl:DamageHelper`(+0x190), `spl::SensorMarkable`(+0x198), `spl::PoisonEffectable`(+0x1a0), `spl::RailMovableSequentialHelper`(+0x1a8), `spl::BombTorpedoTargetHelper`(+0x1b0), `spl::MultiMissileTargetEffectable`(+0x1b8) |
| 37 | `0x71020cb5b8` | `spl__SighterTargetParam` 바인딩(+0x1c8), Banc 파라미터(+0x1d0), 컴포넌트(+0x1d8) |
| 47~58 | `0x71021f10d8` … `0x71021f24b8` | 상태 enter/exec(§5) |

### 3.2 매 프레임 (vt18 `0x71021ef9f8`) [판독]

```
R = DamageHelper 두 번째 목록[0]+0x58 (DamageReceiver),  H = 첫 목록[0]+0x58 (HP 홀더)
1. if !(R+0x1cc) || R+0x1c4 != 0:                // 무적 모드(추가배율 0)가 아니면
       if H.hp(+0x4c) < 1 && state != Burst: changeState(Burst)
2. 상태 기계 exec(dt = *[0x71059a7430 계열 프레임 배수])  0x710125a394
3. 애니 보조 갱신(+0x170: 0x71012664cc, 0x7101262c18 ×2)
4. 휨 계산기 갱신 0x7101e33ed8(+0x180)
   if DamageShotBend 가산 애니 핸들 유효: +0x188+0x40 = 휨각(0x7101e34468) × 57.295776 (도 = 애니 프레임),
                                        +0x188+0x48 = min(|휨 벡터|, 1) (가중치)
5. 레일(+0x1a8 +0x38 레일 있음):  now = [0x710580e758]+0x148 프레임 카운터
       dt = (float)(now − +0x178) × 0.016666668;  +0x178 = now
       RailMovableSequential vt+0x30(dt, out=+0x84 자세)  → Main 강체 목표 자세(0x7103ae41b8, 0x7103ae2890)
```

DamageHelper 의 프레임 갱신(슬롯23 `0x7101e43218` → HP 홀더 `0x7101a8905c`)이 이 vt18 보다 먼저인지 나중인지는 확인하지 않았습니다 **[미확정]**(§11).

### 3.3 피격 [판독]

```
탄 OnHit → 0x71012d4adc(contact, info) → 표적 리시버(열 "Default")
   0x7101a86ec0 결과·배율 (damage_hit.md §6.4)
   0x7101a87e24 apply → 리스너:
       DamageHelper 0x7101e4476c: 결과 Cure 면 회복, 아니면 HP 홀더 누적 0x7101a89524 (다음 홀더 갱신에서 HP 감소)
       표적 0x71021ef25c:
           if !(R+0x1cc && R+0x1c4 == 0) && dmg >= 1:  +0x120 += dmg;  changeState(DamageShot)
물리 접촉 콜백 → vt22 0x71021f0348 → 휨 충격 (데미지와 별개, 몸이 켜져 있을 때만 접촉이 생김)
```

## 4. 구조체·필드·상수·열거형

### 4.1 `spl__SighterTargetParam` (방문 `0x71020cba38`, 팩토리 `0x71020cb944`, vtable `0x7105608218`) [판독]+[데이터]

기준 객체 = 파라미터 객체. 플래그 바이트 = +0x56 + 순번.

| 오프셋 | 플래그 | 이름 | 타입 | 기본값 | 데이터(SighterTarget) | reader |
|---|---|---|---|---|---|---|
| +0x50 | +0x56 | Scale | f32 | 1.0 | 1.0 (Large 1.3) | 0x71021ef388, 0x71021f0a94 |
| +0x38 | +0x57 | BurstWaitDispFrame | s32 | 120 | — | 0x71021f1a9c |
| +0x48 | +0x58 | NoDamageRefreshFrame | s32 | 120 | — | 0x71021f11f0 |
| +0x44 | +0x59 | LossOfColorWaitFrame | s32 | 60 | — | 0x71021f1a9c |
| +0x34 | +0x5a | BulletImpulsScaler | f32 | 0.06 | 1.66 | 0x71021f0348 |
| +0x30 | +0x5b | BombImpulsScaler | f32 | 1.0 | 0.1 | 0x71021f0348 |
| +0x4c | +0x5c | PlayerImpulsScaler | f32 | 0.03 | 0.005 | 0x71021f0348 |
| +0x3c | +0x5d | DamageInfoOffsetY | f32 | 2.6 | — | 0x71021efc24 |
| +0x40 | +0x5e | DrawDamageInfoDistance | f32 | 40.0 | — | 0x71021efc24 |
| +0x54 | +0x5f | IsAlwaysDrawDamageInfo | bool | false | — | 0x71021efc24 |
| +0x55 | +0x60 | IsTipsTrial | bool | false | (TipsTrial 계열 true) | 0x71021eec40, 0x71021f1864 |

### 4.2 기타 파라미터 [데이터]+[판독]

| 표 | 값 |
|---|---|
| `spl__BendCalculatorParam`(방문 `0x7101dd4858`, 기본 0/0) | Kd 0.9(+0x30), Kp 0.05(+0x34) |
| `spl__DamageParam.HitPointHolderArray[Main]` | MaxHitPoint 1000(Large 5000, WoodenFigure 9999), SlipCure 0, IsRefComplementPaintToModel true, PaintBias 0.5 |
| `spl__DamageParam.DamageReceiverArray[Main]` | DamageRateInfoCol `Default`, Flag TargetedByBombRobot·TargetedByMultiMissile, HistMax 64 |
| 휨 종류 계수표 `0x7104a9d010` | [0.005 탄, 0.01 플레이어, 0.015 폭탄] |
| 이동 표적 `game__RailMovableSequentialParam` | #1 MoveSpeed 7, #2 4, #3 5; 모두 cSin·cContinue·cSpeed; WaitTime·MoveTime 미지정(기본) |
| `game__LiftGraphRailNodeParam` 생성자 `0x71012fabdc` | BreakTime(+0x30) 0, Rotation(+0x34) 0 → 로비 레일 점은 Rotation Y −90°만 있음 |

### 4.3 충돌 형상 [데이터]

| 몸 | 캡슐(로컬, 스케일 1) | 레이어 / 마스크 | 의미 |
|---|---|---|---|
| `Main` | A (0, 1.26, 0.35), B (0, 0.39, 0), r 0.39. 키네마틱, 뼈에 묶임(BoneBindMode All) | SplPlayer / `SplPlayerColOthers` = CustomReceiver·GameCustomReceiver·SplPlayer·ChariotShield·InkShield·InkFilm·SplObject·MissionEnemy·CoopEnemy·Item·WallaObj | 플레이어·물체를 막음. 잉크탄은 안 맞음 |
| `ColBullet` | A (0, 1.3, 0), B (0, 0.35, 0), r 0.35. 액터 추적(IsTrackingActor) | SplPlayer / `SplPlayerSensor` = …·SplInkBullet·SplInkBullet_FriendThrough·SubstanceBullet_HitOpposite/HitBullet·RollerBody·BlowerInhale·BluntWeapon·InkTornado·GreatBarrier·SaberBombGuard·Item | 탄이 맞는 몸 |

마스크 비트는 `common/data/phive_config.json`(LayerEntityCollection 순번)으로 풀었습니다.

### 4.4 `spl::SighterTarget` 객체 필드 (기준: 표적 객체) [판독]

| 오프셋 | 의미 | writer | reader |
|---|---|---|---|
| +0x108 / +0x110 | 강체 Main / ColBullet | vt8 | 여러 곳 |
| +0x118 / +0x11c | 각 몸의 +0xdc 초기값 | vt8 | 0x71021f0dcc |
| +0x120 | 받은 데미지 누계(0.1 HP) | 리스너 += , 리셋·Flick enter·BurstWait 끝 = 0 | vt19 |
| +0x128 | 상태 기계: +0x130 현재, +0x134 프레임 카운터(f32), +0x138 이전, +0x13c 이전 카운터, +0x140 다음(초기 0), +0x149 이번 exec 중 전이 | 0x710125a178 | |
| +0x170 | 애니 보조(스켈레탈+머티리얼 채널) | vt8 | 상태 함수 |
| +0x178 | 마지막 레일 갱신 프레임 | 생성자·vt15·vt18 | vt18 |
| +0x180 … +0x1b8 | 컴포넌트(§3.1 슬롯36) | | |
| +0x1c8 | SighterTargetParam | vt37 | |

### 4.5 열거형·이름 [판독]+[데이터]

| 항목 | 값 |
|---|---|
| 상태(등록 순서 = 번호) | 0 Wait, 1 DamageShot, 2 Burst, 3 BurstWait, 4 Expand, 5 Flick |
| 상태 → 스켈레탈 애니 | Wait "", DamageShot "DamageShot", Burst **"Brust"**(원본 철자), BurstWait "", Expand "Expand", Flick "Flick" |
| 애니 프레임 수(bfres) | Brust 1, DamageShot 30, DamageShotBend 360(반복), Expand 45, Flick 24; 머티리얼 애니 Damage 100 |
| `spl::TipsTrialJudgeType` | BreakOneSighterTarget, BreakAllSighterTarget, UseSubWeapon3Times, UseSpecialWeapon3Times, UseTeamSignal3Times |
| 로케이터 영역 모양 문자열 | `Cone , Cube , Cylinder , Plane , Sphere , ConeShift , Hemisphere` — 판정 함수의 case 번호 = 순번+1 로 보면 Cube=2, Cylinder=3, Sphere=5 가 코드와 맞음 [추정] |
| LocatorInfo | LobbyShootingArea Cube·Scale 1·ControlledPlayer, _Cylinder Cylinder, PaintedArea_Cube/Cylinder, StartPos·StartPosTipsTrial Cone [데이터] |

## 5. 상태 전이와 전체 수명

### 5.1 리셋 (vt15 `0x71021ef388`) [판독]

```
+0x120 = 0;  애니 보조 리셋; 몸 활성 플래그 정리
Scale → 액터 스케일(바뀌면 컴포넌트 통지)
가산 애니 설정 ("DamageShotBend", "DamageShot")
team = (로컬 플레이어 인덱스 없음) ? 1 : (플레이어+0x160 != 1)      // 로컬 팀 1 → 0, 그 밖 → 1
R+0x1bc = team;  액터 팀도 team (0x71012ec970, 0x71011024d0)       // 표적은 항상 로컬 플레이어의 상대 팀
+0x178 = now
ShotTarget 로케이터(로컬 (0,1,0)) → ColBullet 몸 로컬 좌표(+0x298) (조준 보조용)
레일이 있으면 액터 위치 = 레일 시작 점(ToRailPoint) 위치, 액터 vt+0x1f8
상태: prev = cur, cur = next(+0x140 = 0 → Wait), counter = 0, Wait enter
```

### 5.2 상태 함수 [판독]

| 상태 | enter | exec |
|---|---|---|
| 0 Wait `0x71021f10d8` / `0x71021f11f0` | R+0x1cc(추가 배율) 끔, 몸 둘 다 켬, 몸 값 보간 t=1, 애니 "" | `hp ≥ max` 면 끝. `counter ≤ NoDamageRefreshFrame(120)` 이면 끝. 아니면 → Flick |
| 1 DamageShot `0x71021f13a4` / `0x71021f1464` | 애니 "DamageShot" | 애니 끝 → Wait |
| 2 Burst `0x71021f14a0` / `0x71021f1864` | 애니 "Brust", 몸 둘 다 끔, 리시버 무적 모드(R+0x1c4 = 0.0, +0x1c8 = 4 Invincible, +0x1cc = 1), 가산 애니 정지, 이펙트 `Break`(컴포넌트 13 `0x7103e1e37c`), 몸 값 t=0, SensorMarkable·PoisonEffectable 처리, 전역 메시지 큐(`0x710582b7c0`)에 깨짐 메시지(vtable `0x7105615390`) 추가 | `!IsTipsTrial && 애니 끝` → BurstWait (팁 시험 표적은 Burst 유지) |
| 3 BurstWait `0x71021f19dc` / `0x71021f1a9c` | 애니 "" | HP 다시 채움(§6.2), `counter > BurstWaitDispFrame(120)` 이면 홀더 리셋·누계 0 → Expand |
| 4 Expand `0x71021f1ff8` / `0x71021f2308` | 애니 "Expand", 몸 둘 다 켬, 가산 애니 재설정(가중치 0), 팀 표시 플래그 | 애니 진행 중이면 몸 값 보간 t = 현재 프레임/끝 프레임, 끝나면 → Wait |
| 5 Flick `0x71021f2384` / `0x71021f24b8` | 애니 "Flick", 홀더 리셋(hp = max), 누계 0, 리시버 무적 모드 | 애니 끝 → Wait |

- 무적 모드는 Burst·Flick enter 에서 켜고 **Wait enter 에서만** 끕니다. 즉 Burst → BurstWait → Expand → Wait 동안, Flick → Wait 동안 데미지는 0(결과 Invincible)입니다. Expand 동안 몸은 켜져 있어 탄이 맞고 휨 충격도 받습니다.
- 상태 기계(`0x710125a178` 전이, `0x710125a394` exec, 공용 game 상태 기계) [판독]: 전이는 현재 상태 exit(이 클래스는 없음) → cur = 새 상태, counter = 0, 전이 플래그 = 1 → 새 상태 enter. exec 는 전이 플래그 = 0 → 현재 exec → 그 exec 안에서 전이가 없었으면 counter += dt. 같은 상태로의 전이도 enter 를 다시 부릅니다(DamageShot 재시작).
- 애니 끝 판정 `0x710126006c`: 스켈레탈 채널(그리고 머티리얼 채널이 있으면 그것도) 현재 프레임 ≥ 프레임 수(FSKA FrameCount) [판독]. 프레임 진행 속도(1프레임당 1)는 **[추정]**.

### 5.3 수명 요약 (데이터 기본값, 1프레임 = 1/60초) [재구현]

```
맞음(dmg≥1) ── DamageShot(30) ──▶ Wait ──(무피격 counter>120)──▶ Flick(24) ─▶ Wait(HP·누계 초기화)
     │HP<1(다음 홀더 갱신 뒤)
     ▼
Burst(Brust 1) ─▶ BurstWait(counter 0~60 HP 0, 60~120 HP 0→max 선형, counter 121 에서) ─▶ Expand(45) ─▶ Wait
```

웹 재구현 기준 프레임 수(시험 `range_target.test.mjs`): 피격 뒤 31스텝째 Wait, 마지막 피격부터 153스텝째 Flick, BurstWait 122스텝, Expand 45스텝.

## 6. 계산식·조건·상세 의사코드

### 6.1 데미지 [판독 — 공용 리시버, damage_hit.md §6.4]

```
dmg = info.value (0.1 HP)
if R.team ∉ {−1, 3} && R.team == 공격 팀:  결과 Through, 0
결과 = Damaged(6)
if R+0x1cc: dmg = fcvtzs((R+0x1c4 + 1e-5) × dmg);  결과 = R+0x1c8 (≠8 이면)
dmg = fcvtzs((DamageRate(행=무기, 열="Default") + 1e-5) × dmg)
if dmg == 0: 결과 = (R+0x1cc && R+0x1c8 != 6) ? R+0x1c8 : Through
dmg > 99999 → 99998
```

표적 열은 `Default` 라 슈터(`Shooter___Default`)는 1.0 → 스플래시슈터 360(36.0) 3발로 1000 을 넘어 깨집니다 [재구현]. 표적 HP 1000 은 플레이어와 같습니다.

### 6.2 BurstWait 의 HP 다시 채우기 `0x71021f1a9c` [판독]

```
i = (int)(counter − LossOfColorWaitFrame)                // f32 빼기 후 절삭
t = (i < 0) ? 0 : min( (float)i / (float)max(BurstWaitDispFrame − LossOfColorWaitFrame, 1 (2 미만이면 1)), 1 )
v = (uint)(t × (float)H.max)
H.hp = (v ≥ lo) ? min(v, H.max) : lo,     lo = (H.flags & 1) ? −H.max : 0
if (float)BurstWaitDispFrame < counter:  0x7101a88e1c(H) (hp = max), +0x120 = 0, → Expand
```

HP 를 0 에서 max 로 올리는 것은 HP 홀더의 "모델 칠 보완"(`IsRefComplementPaintToModel`)과 맞물려 잉크 색이 빠지는 연출(파라미터 이름 LossOfColor)로 보입니다 **[추정]**.

### 6.3 휨 계산기 (spl::BendCalculator) [판독]

충격 `0x7101e3422c(scale, B, 접촉 위치 c, 충격 벡터 J, 종류 k)`: 기준 B = 계산기, B+0x30 액터 위치 P, B+0x3c/+0x48/+0x54 액터 X/Y/Z 축(이전 갱신에서 복사).

```
if k ≥ 3: return
d = c − P
a = dot(d, X) × −10;  e = dot(d, Z) × −10;  n = (a, 0, e) 정규화(길이 0 이면 그대로·n.y = 0)
s = 계수표[k] × ( dot(J,X)·10·0.016666668·n.x + dot(J,Y)·10·0.016666668·n.y + dot(J,Z)·10·0.016666668·n.z );  s = min(s, 1)
g = |min(scale,0.4)/0.4|^2.321928 (부호 보존, |..| < 0.001 이면 0)        // scale 1.0 → 1
B+0x60 += n × s × g
```

갱신 `0x7101e33ed8`(매 프레임):

```
P, X, Y, Z ← 액터
v(+0x78) = (v + imp(+0x60)) × Kd
v = v − p(+0x6c) × Kp
p = p + v;  if |p|² > 1: p = p / |p|
imp = 0
```

방향각 `0x7101e34468`: w = X·p.x + Y·p.y + Z·p.z, 각 = atan2(Y·(Z×w), w·Z − (Y·Z)(w·Y)) 을 [0, 2π) 로(정수 각 `0x7101252998` × 2π/2³²). 로컬로는 atan2(p.x, p.z) — 0 = 앞(+Z), 90° = +X. 이 각(도)이 반복 애니 `DamageShotBend`(360프레임)의 프레임, |p| 가 가중치입니다.

접촉 종류와 충격 벡터(vt22 `0x71021f0348`, 접촉 태그 6종 `0x71012d3e10` 으로 판별) [판독, 태그 ↔ 대상 대응은 계수 이름으로 정함]:

| 접촉 | 위치 | 충격 J | 종류 |
|---|---|---|---|
| 태그 `0x71058e88b0`(플레이어) | 접촉점(+법선×깊이) | −법선 × (접촉+0x60) × PlayerImpulsScaler | 1 |
| 태그 `0x71058e8a90`(폭탄) | 접촉점 | 접촉 vt+0x18 속도 × BombImpulsScaler | 2 |
| 태그 `0x71058e88d0`(탄) | 상대 몸 위치 | 접촉 vt+0x18 속도의 **y 를 0** 으로 × BulletImpulsScaler | 0 |
| 태그 `0x71058e8a70` / `0x71058e8b30` | — | 무시 | |
| 태그 `0x71058e8b70` 이고 접촉+0x30 > 0 | — | 무시 | |

접촉 vt+0x18 이 주는 속도의 단위(초당인지 프레임당인지)는 확인하지 않았습니다 **[미확정]**. Havok 속도라면 초당이고, 슈터 탄(프레임당 약 2)에서 충격 크기는 약 0.17 입니다(웹은 이 가정 — impl 문서).

### 6.4 데미지 숫자 (vt19 `0x71021efc24`, 표시 `0x71021f0c90` → `0x710338cf0c`) [판독]

```
if !IsAlwaysDrawDamageInfo && H.max ≤ H.hp:
    Shr_Points_00 의 이 액터 슬롯을 닫음(슬롯 값 {1, −1.0, 1.0} 설정)
elif 카메라 모듈(*0x710580c3b0+0xe8) 활성(+0x140):
    거리 = |카메라 위치(+0x144) − 액터 위치(+0x28c)|
    if 거리 ≤ DrawDamageInfoDistance(40):
        표시(값 = (float)누계 / 10.0, 위치 = 액터 위치 + 액터 Y축 × DamageInfoOffsetY(2.6),
             액터 id, isMax = H.max ≤ 누계)
```

- 레이아웃 `Shr_Points_00` 은 슬롯 최대 16개(액터 id 로 슬롯 재사용) [판독].
- 메시지 `000` = `[2:0:00030000].[2:0:01010000]` — 숫자 태그 두 개를 점으로 이은 "정수.소수" 형식 [데이터]. 소수 자릿수(1자리)는 **[추정]**.
- isMax 는 슬롯의 레이아웃 애니 값(6/1, 0/−1, 0/1)을 바꿉니다. 어떤 모양인지는 레이아웃 애니를 보지 않았습니다 **[미확정]**.

### 6.5 이동 표적 레일 [판독]

`spl::RailMovableSequentialHelper`(vtable `0x71055edbf8`): 초기화 vt7 `0x7101e7f4ac` 가 `ToRailPoint`(Banc `spl__RailMovableSequentialHelperBancParam`)로 레일 점을 찾고(`0x7101302ba8`), `game::RailMovableSequential`(0x18f8 B, vtable `0x7105577e98`, 어댑터 vtable `0x7105587318` — 이동 발판과 **같은 객체**)을 만들어 일정 `0x7101305238` 을 짓습니다. 리셋 vt13 `0x7101e7f86c` = 시작 점 자세 복사 + 시간 0(vt5 `0x71013046c4`). 표적 vt18 이 객체 vt6 `0x71013046d4` 로 `t += dt`(역재생 플래그 +0x18f4 면 −dt) → 시간 평가 `0x71013043d8`(stage_misc §1.3).

**보강(정정 제안)**: 이동 시간 `0x7101305b40` 의 cSpeed 는 어댑터 vt+0x70 `0x710147b6dc(a, b, rev)` 를 **rev 플래그와 함께** 부릅니다. 이 함수는 rev 이면 `d[b]−d[a]` 의 부호를 뒤집으므로 역방향 이동 시간도 양수입니다. 이동 함수 `0x7101304cec` 의 거리 계산은 플래그 0(부호 있는 길이)을 씁니다. `web/tools/gimmick_lift.py` 의 `seg_len` 은 두 곳 모두 플래그 0 이라 cSpeed 왕복에서 역방향 구간이 빠집니다(Carousel 은 cTime 이라 영향 없음).

로비 레일과 결과 [데이터]+[재구현]:

| 표적 | 레일(점 Y −90°) | 속도 | 한 구간 | 주기 |
|---|---|---|---|---|
| Move #1 (15066127630233066301) | (40,0,18) → (40,0,3) | 7 | 15/7 = 2.142857초 | 4.285714초 |
| Move #2 (1759095691775920200) | (40,6,3) → (40,6,18) | 4 | 3.75초 | 7.5초 |
| Move #3 (10119736514646560643) | (33.5,0,3) → (33.5,0,18) | 5 | 3.0초 | 6.0초 |

위치 = 레일 위치(배치 Translate 의 Y 2/7/0.5 는 리셋에서 레일 점으로 덮임), 회전 = 점 회전 Ry(−90°)(배치 Rotate 와 같음). 매 프레임 결과를 Main 강체 목표 자세로 넘기고 액터가 그 강체를 따라가는 것으로 보입니다 **[추정 — 액터 행렬 갱신 경로 미판독]**.

### 6.6 사격 구역 [판독]+[데이터]

안쪽 판정 `0x71012496e8(영역, 점)`(영역+0x20 모양, +0x24 배율, 로케이터 +0x40 위치, +0x4c 3×3, +0x70 스케일):

```
d = p − T;  l_i = dot(d, (m[+0x4c+4i], m[+0x58+4i], m[+0x64+4i]))     // 축별 로컬 좌표
Cube(2):     |l_x| ≤ s·Sx·0.5 && |l_y| ≤ s·Sy·0.5 && |l_z| ≤ s·Sz·0.5
Cylinder(3): 0 ≤ l_y < 2·s·Sy && l_x² + l_z² < (s·Sx)²                // 바닥이 원점
Sphere(5):   |d|² ≤ (s·Sx)²
```

플레이어 쪽(`0x7102483134` 안 `0x7102484ff8`~`0x7102489e6c`, 로비 분기): 이름 `"LobbyShootingArea"` 영역 목록을 먼저, 없으면 `"LobbyShootingArea_Cylinder"` 목록을 돌며 본체+0x10 위치로 판정 → **본체+0x938d = 안쪽 여부**. 그리고 `본체+0xc0(공중 프레임) < 4`(상수 `0x71058bbc20`)일 때만 **본체+0x938c = 안쪽 여부**(공중에서는 이전 값 유지).

+0x938c/+0x938d 를 읽는 곳: 정지 상태 선택(`0x710244187c` — WaitHold_Sp 조건), 입력 처리 `0x710249f494` → `0x71024c7d5c`(로비 `0x71058e87ac` 이면 +0x938d 를 조건으로 씀), 입력 송신 `0x7102630e6c`, UI(`0x71031eaac8` 스페셜 표시), 미니맵 `0x7102264240` 등. 이름·소비처로 보아 **로비에서 무기(사격) 허용 여부**로 보입니다 **[추정 — 사격 입력을 막는 정확한 지점은 미판독]**.

로케이터 행렬 저장 순서는 확인하지 않았습니다. 코드가 로컬 좌표를 구한다고 보고 l = Rᵀ(p − T) 로 둡니다 **[추정]**(회전된 영역은 Y 0.778rad 상자 1개).

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

| 항목 | 내용 |
|---|---|
| 모델 | `Obj_SighterTarget`(일반·대형·팁), `Obj_SighterTargetMove`(이동), 파편 `Fragment00/01`(같은 bfres). 뼈: root, leg, burst, body, ear_L0/L1, Z_ear_L, ear_R0/R1, Z_ear_R [데이터] |
| 스켈레탈 애니 | §4.5. Burst 시 파편 연출은 `Brust`(1프레임)와 이펙트로 보임 [추정] |
| 가산 애니 | `game::AnimationAddable`(+0x188) = "DamageShotBend"(프레임 = 휨각°, 가중치 = |휨|) + "DamageShot" [판독] |
| 머티리얼 애니 | `Damage`(100프레임). 구동 경로 미확인 **[미확정]** — HP 홀더 칠 보완(IsRefComplementPaintToModel, PaintBias 0.5)과 관련 추정 |
| 이펙트/소리 | ELink/SLink 사용자 `SighterTarget`(대형 ELink `SighterTargetBig`, 팁 `SighterTarget_TipsTrial`). Burst enter 가 `Break` 를 보냄. 피격 이펙트·소리는 공용 HitEffect(damage_hit §6.6) |
| UI | `Shr_Points_00`(§6.4) |
| 카메라 | 데미지 숫자 거리 기준 = 카메라 모듈 위치 |

## 8. 다른 기능과의 상호작용

| 상대 | 내용 |
|---|---|
| 탄·데미지 | 리시버 열 `Default`. 팀 = 로컬 플레이어 반대 팀 → 자기 잉크로 맞힘. 같은 팀이면 Through |
| HP 홀더 | DamageHelper 공용 홀더(player_life §6.1). 홀더 갱신 전에는 HP 가 그대로라 깨짐은 다음 홀더 갱신 뒤 |
| 충돌 | ColBullet 만 탄과 충돌, Main 은 플레이어를 막음. Burst~BurstWait 동안 둘 다 꺼짐 |
| 레일 | 이동 발판과 같은 RailMovableSequential |
| 팁 시험 | `IsTipsTrial` 표적은 깨진 채 남고, 깨짐 메시지가 전역 큐로 감 → `BreakOneSighterTarget`/`BreakAllSighterTarget` 판정에 쓰이는 것으로 보임 [추정]. 진행은 AINB `Lby_Lobby00_5bad`·`SplTipsTrialSetup/Progress/Restore` 시퀀스 |
| 조준 보조·센서 | ShotTarget 로케이터(0,1,0), SensorMarkable(+0x198 +0x30 = 상태>1), 폭탄 로봇·멀티미사일 대상 플래그 |

## 9. 웹 포팅 구조와 구현 순서

### 9.1 모듈 (웹 권장 이름 — 원본 이름 아님)

| 모듈 | 책임 | 원본 대응 |
|---|---|---|
| `core/range/target.ts` `SighterTarget` | 상태 기계·HP 홀더·리시버 일부·휨·표시값 | vt15/18/19/22, 상태 함수, 0x7101a86ec0 일부 |
| `core/range/rail.ts` `RailPath`/`RailMover` | 레일 일정·평가 | 0x7101305238, 0x71013043d8, 0x7101304cec, 어댑터 |
| `core/range/area.ts` | 사격 구역 판정·무기 허용 래치 | 0x71012496e8, 0x7102484ff8~ |
| `core/range/index.ts` | 배치 → 생성, Hittable·충돌 등록, 공유 상태 | |
| `client/range/index.ts` | 모델·데미지 숫자 | Shr_Points_00 |

### 9.2 상태 객체 대응

| 원본 | 웹 |
|---|---|
| +0x130 / +0x134 | `state` / `counter` |
| +0x120 | `accum` |
| H+0x48 / +0x4c / +0x50 | `holder.max` / `hp` / `pending` |
| R+0x1bc / +0x1cc / +0x1c4 / +0x1c8 | `recv.team` / `extraOn` / `extraRate` / `extraResult` |
| BendCalculator +0x60/+0x6c/+0x78 | `bendImp` / `bendPos` / `bendVel` |

### 9.3 순서·정밀도

1. (DamageHelper) 홀더 갱신 → 2. vt18(Burst 검사 → exec → 애니 → 휨 → 레일) → 3. vt19 표시값. 피격은 탄 처리 중 즉시(리스너가 바로 DamageShot 전이).
2. f32 연산, 배율 `+1e-5`, `fcvtzs`(0 방향 절삭), 99998 상한, BurstWait 의 `(int)` 절삭과 `(uint)` 변환은 그대로.
3. 같은 상태 전이도 enter 재실행(애니 재시작).

## 10. 검증 코드·실행 결과·기대값

| 검사 | 종류 | 결과 |
|---|---|---|
| `tests/range_target.test.mjs` | [재구현] 합성 시나리오 | 피격 360 → DamageShot, 31스텝째 Wait, HP 640, 표시 36.0; 3발 → Burst(Break 이벤트, 충돌 해제) → BurstWait 122스텝(counter 61 에서 HP 16) → Expand 45스텝 → Wait; 무피격 → 153스텝째 Flick; 같은 팀 Through; 무적 중 Invincible·0; 대형 HP 5000·스케일 1.3; 이동 표적 64프레임 뒤 z ∈ (10, 11) |
| `tests/range_rail.test.mjs` | [재구현] 로비 레일 실제 값 | 구간 15/7초, 주기 2배, sin 중간점 10.5, 역방향 cSpeed, Ry(−90°) 축, cStop·WaitTime·BreakTime |
| `tests/range_area.test.mjs` | [재구현] 배치 실제 값 | Cube 경계(≤), 회전 Cube, Cylinder 바닥·높이·반지름(엄격 <), 래치(공중 4프레임) |
| `client/range/dev/shot.mjs` | 헤드리스 화면(웹) | 17개 표적 표시, 피격 시 "36.0", 깨짐 시 "108.0"(노란색, isMax), BurstWait 숨김, Expand 크기 복귀 — `test/out/range_*.png` |

원본 실행 대조(unicorn)는 하지 않았습니다. 상태 함수는 액터·컴포넌트 객체 그래프가 깊어 단독 실행 하네스가 크기 때문입니다. 재구현은 판독식 옮김 + 합성 입력이며 "동작 검증 완료"가 아닙니다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 상태 | 다음 단서 |
|---|---|---|
| DamageHelper 홀더 갱신과 표적 vt18 의 순서 | [미확정] | 액터 컴포넌트 갱신 순서(컴포넌트 calc 호출부) — 깨짐이 같은 프레임인지 다음 프레임인지 1프레임 차 |
| 애니 프레임 진행 속도·첫 프레임 | [추정: 1프레임 1, 0부터] | `0x71012664cc`(애니 보조 갱신) 판독 |
| 몸 값 +0xdc 보간(`0x71021f0dcc`)의 의미 | [미확정] | 강체 객체 +0xd8/+0xdc/+0xe0/+0xe8 필드 — 크기(스케일)로 보이나 미확인. Expand 동안 충돌 크기가 자라는지 |
| 접촉 속도 단위(vt+0x18) | [미확정] | 접촉 객체 vtable(+0x18) 판독 |
| 접촉 태그 6종의 정확한 이름 | [추정 — 계수 이름으로 대응] | 태그 객체(bss `0x71058e88b0` 등) 초기화의 이름 문자열 |
| 이동 표적 액터 행렬 | [추정 — 액터가 Main 강체를 따라감] | `0x7103ae41b8`/`0x7103ae2890` 판독 |
| 사격 구역 래치의 효과(사격 금지 지점) | [추정] | `0x71024c7d5c` 반환값 소비처, `0x7102630e6c` 의 +0x938c 사용 |
| 로케이터 회전 저장 순서 | [추정] | 로케이터 영역 생성(영역 관리자 `0x7105802a28`) |
| 영역 모양 번호 = 문자열 순번+1 | [추정] | `0x71013cca0c`(열거 정보) 근처 등록 코드 |
| `[액터+0x348]+0x3b`(팁 시험 표적이 0 으로 씀) | [미확정 — 기본 0xff 의 3상태 플래그로 보임] | 읽는 곳 `0x7101468138`, `0x71027ae454`, `0x7102d55f00` |
| 데미지 숫자 소수 자릿수·isMax 모양 | [추정]/[미확정] | Shr_Points_00 레이아웃(텍스트 박스 형식, 애니) |
| 머티리얼 애니 `Damage` 구동 | [미확정] | HP 홀더 칠 보완 경로 |
| 팁 시험 진행(AINB)·WoodenFigure 공격 상세·PaintedArea 칠 요청 형식 | 범위 밖 | `Lby_Lobby00_5bad.logic.root.ainb`, `wooden_figure.c`, `0x7101f07b5c` → `0x7102bc46f8` |
| 플레이어 접촉 충격(접촉+0x60) | [판독-부분] | 접촉 객체 필드 |
