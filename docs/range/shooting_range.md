# 시험 사격장: 표적·사격 구역·시작 위치 (range)

Splatoon 3 v0 대전 로비(`LobbyVersus` 씬, 배치 `Banc/Lby_Lobby00`)의 시험 사격장을 원본 코드·데이터로 정리합니다. 중심은 표적 `spl::SighterTarget`(일반·대형·이동)이고, 사격 구역(`LobbyShootingArea`), 시작 위치, 팁 시험(TipsTrial) 계열·나무 인형·PaintedArea는 1차 범위 밖이라 무엇인지와 확인한 만큼만 적었습니다.

- 작업 지침: [../../분석.txt](../../분석.txt). 확정 수준: **[실행]** 원본 실행, **[판독]** 원본 명령/디컴파일 판독, **[데이터]** 데이터 확인, **[재구현]** 재구현 계산, **[추정]**, **[미확정]**.
- 상태: 표적 동작은 **분석 완료(일부 미확정 §11)**, 웹 구현은 [../impl/range.md](../impl/range.md). "분석 완료" ≠ "구현 완료" ≠ "동작 검증 완료"입니다.
- 원본 실행(2026-10-03, 5차): 휨 계산기·캡슐 보간·애니 진행·영역 판정·데미지 숫자 형식 5종을 unicorn으로 실행해 독립 재구현과 비트 대조했습니다(§10, `web/tools/r5_range_emu.py`). 상태 함수 전체와 액터·물리 연결은 실행하지 않았습니다.
- 정정(2026-10-03): 이전 판의 "원본 실행 대조는 없습니다"는 위 5종에 한해 더 이상 맞지 않습니다. 이유: 5차 원본 실행 추가.
- 6차(2026-10-03): 팁 시험 진행(로직 AINB `Lby_Lobby00_5bad` 해독, 시퀀스 노드·도우미 상태 기계·판정 객체, 태그 `ActorAttr_ForTipsTrial`/`NotForTipsTrial`)을 §6.7에 새로 정리했습니다. 표적 잉크 색이 빠지는 연출(LossOfColor)의 실제 경로(§6.2.1), `[액터+0x348]+0x3b`의 뜻(§6.7.5), 재피격 때 `ダメージ` 재방출(§7.1, 원본 실행 28/28)을 확정했습니다.
- 연결 문서: 데미지 단위·배율·리시버 [../combat/damage_hit.md](../combat/damage_hit.md), HP 홀더 [../combat/player_life.md](../combat/player_life.md) §4.1·§6.1, 레일 이동 [../gimmick/stage_misc.md](../gimmick/stage_misc.md) §1.2~§1.5, Banc 형식 [../gimmick/stage_gimmicks.md](../gimmick/stage_gimmicks.md) §3, xlink 규칙 [../effect_sound/xlink_format.md](../effect_sound/xlink_format.md) §4.4, UI 애니 명령 [../ui/ui_hud.md](../ui/ui_hud.md) §5.3.

---

## 1. 기능 개요와 사용자에게 보이는 동작

| 대상 | 개수(Banc) | 보이는 동작 | 확정 수준 |
|---|---|---|---|
| `SighterTarget` | 12 | 맞으면 흔들리고(DamageShot) 휜다(DamageShotBend). 머리 위에 받은 데미지 누계가 `36.0` 형식으로 뜬다. HP 1000(=100.0)을 다 깎으면 터지고(Brust) 사라졌다가 약 2초 뒤 다시 솟는다(Expand). 120프레임 넘게 안 맞으면 털어내며(Flick) HP·누계가 처음으로 돌아간다. 프레임 수는 §5.3 | [판독]+[실행] |
| `SighterTarget_Large` | 2 | 같은 동작, HP 5000, 크기 1.3배, ELink 사용자 `SighterTargetBig` | [데이터]+[판독] |
| `SighterTarget_Move` | 3 | 같은 동작 + 레일(LiftRail)을 따라 왕복. 속도 7/4/5(초당 단위), sin 가감속, 끝에서 바로 되돌아옴 | [판독]+[데이터] |
| `SighterTarget_TipsTrial`(18), `_TipsTrialMove`(2) | 20 | 팁 시험(로비 연습 과제) 전용 표적. 깨지면 다시 솟지 않음(Burst에 머묾) [판독]. 초기화에서 `[액터+0x348]+0x3b = 0`(배치 기록의 "자동 깨우기 허용" 끔, §6.7.5)을 씀 [판독]. 태그 `ActorAttr_ForTipsTrial`이라 팁 시험 Restore에서 종료 요청을 받음 [판독]+[데이터]. 시험의 Playground가 시작될 때 로직 AINB의 `Logic_Activate`로 켜짐(§6.7.2) [데이터]. 장면 시작 때 실제로 꺼져 있는지(로직 액터 기본 상태)는 [미확정] | [판독]+[데이터]+[미확정] |
| `LobbyShootingArea`(3, Cube) / `_Cylinder`(1) | 4 | 로컬 플레이어가 이 안에 있는지 매 프레임 판정 → 플레이어 본체 플래그. 로비 플래그가 켜져 있고 구역 밖이면 입력 종류 4개 중 오징어(종류 0)를 뺀 3개를 끈다(§6.6) | [판독]+[데이터]+[실행] |
| `StartPos`(10) | | Alpha 시작 1개, 결과 화면 `ResultPlayer0~7`, 리플레이 복귀 `FromReplay` | [데이터] |
| `StartPosTipsTrial`(17) | | 팁 시험 시작 위치(`Aim`, `Front10m`~`Front30m`, `MoveTarget`, `Charger`, `IkaFlip`, `IkaNet`, `GyroCamera`, `WoodenFigure`, `SpSuperHock`, `Restore`) | [데이터] |
| `WoodenFigure` | 1 | 상호작용(가이드 `WoodenFigureOn`, 반경 3)으로 켜는 나무 인형. 슈터·스플래시봄을 들고 쏘고 던짐(애니 `PowerOn`, `Shooting_Shooter`, `Hold_Bomb`, `Throw_Bomb`). HP 9999 | [데이터]+[판독-부분] |
| `PaintedArea_Cube`(8) / `_Cylinder`(19) | 27 | 초기화 때 영역을 팀 잉크(배치 팀 Alpha)로 칠하는 로케이터. 27개 모두 로직 AINB의 `SplLogicActor`로 묶여 해당 Playground의 Setup 펄스(`Logic_Activate`)를 받음(§6.7.2) | [판독-부분]+[데이터] |
| `SpawnerForShieldGimmick_TipsTrial`(2, Bravo) / `SpawnerForBeaconGimmick_TipsTrial`(1) | | 팁 시험용 스플래시실드·비컨 기믹 스포너. AINB `Spawn` 입력 ← `MoveTargetShield`·`SuperJump` Setup(§6.7.2), 태그 `ActorAttr_ForTipsTrial` | [데이터] |

거리 단위 확인: `StartPosTipsTrial "Front10m"`(15.5, 0, 12.75)과 팁 시험 표적(15.5, 0, 22.75)의 거리가 10.0 → 게임 1단위 = 1 m로 이름 붙어 있음 [데이터].

## 2. 분석 대상 원본·버전·자료 위치

| 항목 | 위치 |
|---|---|
| 씬 | `romfs/Pack/Scene/LobbyVersus.pack.zs` → `Banc/Lby_Lobby00.bcett.byml`(해제본 `analysis/range/pack_LobbyVersus/`), 로직 `Logic/Lby_Lobby00_5bad.logic.root.ainb`(AiGroups가 WoodenFigure·PaintedArea·TipsTrial 표적을 참조) |
| 사격장 액터 발췌 | `analysis/range/banc_range_dump.txt` |
| 액터 팩 | `romfs/Pack/Actor/SighterTarget*.pack.zs` 등 → `analysis/range/actor/<이름>/` (`--json` 사본) |
| RSDB | `ActorInfo`(→ `analysis/range/ActorInfo.json`), `LocatorInfo`(→ `analysis/range/LocatorInfo.json`: 영역 ShapeType·Scale) |
| 모델 | `romfs/Model/Obj_SighterTarget.bfres.zs` → 덤프 `analysis/range/Obj_SighterTarget_dump.json`(모델 4: Fragment00/01, Obj_SighterTarget, Obj_SighterTargetMove; 스켈레탈 애니 5, 머티리얼 애니 1) |
| 데미지 숫자 레이아웃 | `Layout/Shr_Points_00.Nin_NX_NVN.blarc.zs`(덤프 `analysis/r5_range/Shr_Points_00/`), 메시지 `analysis/ui/msbt_KRko/LayoutMsg/Shr_Points_00.json` |
| xlink | SLink·ELink 사용자 `SighterTarget`(`analysis/effect_sound/slink2_users.json`, `elink2_users.json`) |
| 디컴파일 | `analysis/decomp/range/`: `sighter_vt.c`(+`_annot.c`, vtable 전 슬롯), `sighter_helpers.c`(상태 기계·휨·애니 보조), `rail_helper.c`, `area_inside.c`, `painted_area.c`, `wooden_figure.c`, `points_ui.c`, `burst_notice.c`. 5차 추가 `analysis/decomp/r5_range/`: `anim_play.c`(애니 재생·레일 강체·+0x3b 사용처), `anim_init.c`, `xlink_action.c`(모델 애니→xlink), `locator_shape.c`(LocatorInfo 행), `shoot_gate.c`(입력 게이트) |
| 원본 실행 | `web/tools/r5_range_emu.py` → `analysis/completion/r5/range_emu.json`, 6차 `web/tools/r6_range_xlink_emu.py` → `analysis/r6_range/xlink_regress_emu.json` |
| 6차 자료 | AINB 해독기 `web/tools/r6_range_ainb.py`(버전 0x404, 인자 = .ainb 경로·출력 JSON) → `analysis/r6_range/lby_lobby00_5bad_ainb.json`·`ainb_dump.txt`(로직 147노드), `spllobbyversus_ainb.json`·`spllobbyversus_dump.txt`(Bootup 팩 `UniqueSequenceSPL/SplLobbyVersus.root.ainb`). 팁 시험 파라미터 53종 `analysis/r6_range/tipstrial/all_tipstrial_params.json`(Bootup 팩 `Gyml/TipsTrial/*.spl__TipsTrialParam.bgyml`). 태그 표 `analysis/r6_range/tag_rstbl.json`(RSDB `Tag.Product.100.rstbl`). 디컴파일 `analysis/decomp/r6_range/`: `batch1.c`(로직 노드·HP 홀더 파라미터·생성 정보 복사·RigidBodyController 파라미터), `tips_seq.c`(Setup/Restore 노드·도우미·판정), `tips_helper.c`(도우미 calc `0x7102e1c72c`, 함수 목록에 없던 14 KB 함수), `complement.c`(모델 칠 보완 재질 쓰기), `rbc.c` |

## 3. 진입점과 전체 호출 흐름

### 3.1 클래스와 vtable [판독]

`Behavior.ClassName "spl::SighterTarget"` → vtable `0x7105615188`(59 슬롯), getName `0x71021ee658`, 크기 `0x1e0`(슬롯 4), 생성 `0x71021ee4dc`. 슬롯 의미는 InkRail·Sponge와 같은 액터 규약(vt8 초기화, vt15 리셋, vt18 프레임, vt22 접촉)입니다.

| 슬롯 | 주소 | 내용 |
|---|---|---|
| 7 | `0x71021ee66c` | 상태 기계(+0x128) 6개 등록: `cWait`, `cDamageShot`, `cBurst`, `cBurstWait`, `cExpand`, `cFlick`. 상태 i의 enter = vt[47+2i], exec = vt[48+2i](멤버 포인터 vtable 오프셋 0x178+0x10·i) |
| 8 | `0x71021eec40` | 초기화: 강체 `Main`→+0x108, `ColBullet`→+0x110, 각 몸 캡슐의 A.y(형상 +0xdc)를 +0x118/+0x11c에 저장, 애니 보조(+0x170) 생성. `IsTipsTrial`이면 `[액터+0x348]+0x3b = 0` |
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
1. if !(R+0x1cc) || R+0x1c4 != 0:                // 무적 모드(추가 배율 0)가 아니면
       if H.hp(+0x4c) < 1 && state != Burst: changeState(Burst)
2. 상태 기계 exec(dt = *[0x71059a7430 계열 프레임 배수])  0x710125a394
3. 애니 보조 갱신(+0x170: 0x71012664cc, 재질 채널 0x7101262c18 ×2)     // §5.2.1
4. 휨 계산기 갱신 0x7101e33ed8(+0x180)
   if DamageShotBend 가산 애니 핸들 유효: +0x188+0x40 = 휨각(0x7101e34468) × 57.295776 (도 = 애니 프레임),
                                        +0x188+0x48 = min(|휨 벡터|, 1) (가중치)
5. 레일(+0x1a8 +0x38 레일 있음):  now = [0x710580e758]+0x148 프레임 카운터
       dt = (float)(now − +0x178) × 0.016666668;  +0x178 = now
       RailMovableSequential vt+0x30(dt, out=+0x84 자세)  → Main 강체 목표 위치(0x7103ae41b8 → 속도, 0x7103ae2890 setLinearVelocity)
```

#### 3.2.1 Behavior·컴포넌트 단계와 HP 홀더 갱신 순서 [판독] (2026-10-03)

정정(2026-10-03): 이전 판은 "DamageHelper의 프레임 갱신(슬롯 23 `0x7101e43218` → HP 홀더 `0x7101a8905c`)이 이 vt18보다 먼저인지 나중인지는 확인하지 않았습니다 [미확정]"이었습니다. 아래 판독으로 **vt18·vt19 뒤**로 확정합니다.

- Behavior(표적 객체)는 단계 5개(k = 0..4)의 컴포넌트 목록을 가집니다. 목록 구성 `0x7100ffc20c`: 컴포넌트마다 vt19(+0x98)가 단계 마스크, vt31(+0xf8)이 0이면 앞 목록, 1이면 뒤 목록. 단계 k의 목록은 Behavior+0x48+0x20·k(앞: 개수 +0, 배열 +8 / 뒤: 개수 +0x10, 배열 +0x18).
- 단계 0 `0x7100ffdaa4`(SplActor `0x7100f76a78`의 끝 `0x7100f76f40`에서 호출): 앞 컴포넌트 vt20 → **Behavior vt18** → 뒤 컴포넌트 vt20.
- 단계 2 `0x7100ffdb6c`(SplActor `0x7100f76f78`의 `0x7100f77884`): 앞 vt21 → **Behavior vt19** → 뒤 vt21.
- 단계 4(`0x7100f76f78` 안 `0x7100f77b20`~`0x7100f77b7c`): 앞 컴포넌트 vt23 → Behavior vt21 → 뒤 컴포넌트 vt23.
- `spl:DamageHelper`(vtable `0x71055ea2e8`)는 vt19 = `0x7101e43fc0`(마스크 **0x11** = 단계 0·4), vt31 = `0x7101e43fc8`(1 = 뒤). 단계 0의 vt20 `0x7101e421a4`는 수신 큐(AttackEvent) 처리, 단계 4의 vt23 `0x7101e43218`이 **HP 홀더 갱신**입니다.
- 따라서 한 프레임 안 표적 순서는 `vt18(HP<1 검사·상태 exec·애니·휨·레일) → … → vt19(데미지 숫자) → … → HP 홀더 갱신(대기 데미지 반영)`입니다. 탄 접촉으로 쌓인 데미지가 HP에 반영되는 것은 그 프레임 단계 4이고, Burst 전이는 **다음 프레임의 vt18**입니다.
- 남은 것: 탄 접촉 반응 시퀀서가 프레임 안 어디서 도는지(단계 4 앞인지 뒤인지)는 물리 영역의 [미확정]입니다([../physics/phive_controller.md](../physics/phive_controller.md) §6.7). 그 위치에 따라 마지막 명중 → Burst가 1프레임 또는 2프레임 뒤가 됩니다.

### 3.3 피격 [판독]

```
탄 OnHit → 0x71012d4adc(contact, info) → 표적 리시버(열 "Default")
   0x7101a86ec0 결과·배율 (damage_hit.md §6.4)
   0x7101a87e24 apply → 리스너:
       DamageHelper 0x7101e4476c: 결과 Cure면 회복, 아니면 HP 홀더 누적 0x7101a89524 (단계 4 홀더 갱신에서 HP 감소)
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
| `spl__BendCalculatorParam`(방문 `0x7101dd4858`, 기본 0/0) | Kd 0.9(+0x30, 플래그 +0x39), Kp 0.05(+0x34, 플래그 +0x38). 갱신 `0x7101e33ed8`이 +0x30을 감쇠, +0x34를 복원 계수로 씀 [실행] |
| `spl__DamageParam.HitPointHolderArray[Main]` | MaxHitPoint 1000(Large 5000, WoodenFigure 9999), SlipCure 0, IsRefComplementPaintToModel true, PaintBias 0.5 |
| `spl__DamageParam.DamageReceiverArray[Main]` | DamageRateInfoCol `Default`, Flag TargetedByBombRobot·TargetedByMultiMissile, HistMax 64 |
| 휨 종류 계수표 `0x7104a9d010` | [0.005 탄, 0.01 플레이어, 0.015 폭탄] (이미지 값 [데이터]) |
| 이동 표적 `game__RailMovableSequentialParam` | #1 MoveSpeed 7, #2 4, #3 5; 모두 cSin·cContinue·cSpeed; WaitTime·MoveTime 미지정(기본) |
| `game__LiftGraphRailNodeParam` 생성자 `0x71012fabdc` | BreakTime(+0x30) 0, Rotation(+0x34) 0 → 로비 레일 점은 Rotation Y −90°만 있음 |

### 4.3 충돌 형상 [데이터]

| 몸 | 캡슐(로컬, 스케일 1) | 레이어 / 마스크 | 의미 |
|---|---|---|---|
| `Main` | A (0, 1.26, 0.35), B (0, 0.39, 0), r 0.39. 키네마틱. 컨트롤러 `IsTrackingActor false`, 뼈 묶음(BoneBindMode All) | SplPlayer / `SplPlayerColOthers` = CustomReceiver·GameCustomReceiver·SplPlayer·ChariotShield·InkShield·InkFilm·SplObject·MissionEnemy·CoopEnemy·Item·WallaObj | 플레이어·물체를 막음. 잉크탄은 안 맞음 |
| `ColBullet` | A (0, 1.3, 0), B (0, 0.35, 0), r 0.35. 컨트롤러 `IsTrackingActor true`(액터 추적) | SplPlayer / `SplPlayerSensor` = …·SplInkBullet·SplInkBullet_FriendThrough·SubstanceBullet_HitOpposite/HitBullet·RollerBody·BlowerInhale·BluntWeapon·InkTornado·GreatBarrier·SaberBombGuard·Item | 탄이 맞는 몸 |

마스크 비트는 `common/data/phive_config.json`(LayerEntityCollection 순번)으로 풀었습니다.

**실행 중 캡슐 A [실행]+[판독] (2026-10-03)**: Phive 캡슐 형상은 A = +0xd8..+0xe0, B = +0xe4..+0xec, 반경 +0xf0입니다([../physics/character_controller.md](../physics/character_controller.md) §3.1, 데이터 CenterA가 +0xd8). 표적의 `0x71021f0dcc(t)`는 두 몸 모두 **A = (0, B.y + t′·(A0.y − B.y), 0)**, t′ = (t < 0) ? 0 : min(t, 1)로 다시 씁니다(A0.y = vt8이 저장한 +0x118/+0x11c). 첫 Wait enter(리셋 직후)에서 t = 1이 쓰이므로 **Main의 A.z 0.35는 게임 중에 0이 됩니다**(Main A = (0, 1.26, 0)). 데이터 표의 A.z는 실행 중 값이 아닙니다.

### 4.4 `spl::SighterTarget` 객체 필드 (기준: 표적 객체) [판독]

| 오프셋 | 의미 | writer | reader |
|---|---|---|---|
| +0x108 / +0x110 | 강체 Main / ColBullet | vt8 | 여러 곳 |
| +0x118 / +0x11c | 각 몸 캡슐 A.y 초기값(형상 +0xdc) | vt8 | 0x71021f0dcc |
| +0x120 | 받은 데미지 누계(0.1 HP) | 리스너 +=, 리셋·Flick enter·BurstWait 끝 = 0 | vt19 |
| +0x128 | 상태 기계: +0x130 현재, +0x134 프레임 카운터(f32), +0x138 이전, +0x13c 이전 카운터, +0x140 다음(초기 0), +0x149 이번 exec 중 전이 | 0x710125a178 | |
| +0x170 | 애니 보조(§5.2.1) | vt8 | 상태 함수, vt18 |
| +0x178 | 마지막 레일 갱신 프레임 | 생성자·vt15·vt18 | vt18 |
| +0x180 … +0x1b8 | 컴포넌트(§3.1 슬롯 36) | | |
| +0x1c8 | SighterTargetParam | vt37 | |

### 4.5 열거형·이름 [판독]+[데이터]

| 항목 | 값 |
|---|---|
| 상태(등록 순서 = 번호) | 0 Wait, 1 DamageShot, 2 Burst, 3 BurstWait, 4 Expand, 5 Flick |
| 상태 → 스켈레탈 애니 | Wait "", DamageShot "DamageShot", Burst **"Brust"**(원본 철자), BurstWait "", Expand "Expand", Flick "Flick". 빈 이름 ""은 검색에 실패해 **이전 애니·프레임을 그대로 둡니다**(§5.2.1) |
| 애니 프레임 수(bfres) | Brust 1, DamageShot 30, DamageShotBend 360(반복), Expand 45, Flick 24; 머티리얼 애니 Damage 100 |
| `spl::TipsTrialJudgeType` | BreakOneSighterTarget, BreakAllSighterTarget, UseSubWeapon3Times, UseSpecialWeapon3Times, UseTeamSignal3Times |
| 로케이터 영역 모양 | **1 Cone, 2 Cube, 3 Cylinder, 4 Plane, 5 Sphere, 6 ConeShift, 7 Hemisphere** [판독]. `0x71013ca4d4`(LocatorInfo 행 읽기)가 `ShapeType` 문자열을 열거 문자열 `"Cone , Cube , Cylinder , Plane , Sphere , ConeShift , Hemisphere"`(`0x71013cc804`)의 순번과 비교해 **순번+1**을 행+0x10에 넣고, `0x710124a364` → `0x71012490e8`이 영역+0x20 = 행+0x10, 영역+0x24 = 행+0xc(Scale), 영역+0x18 = 로케이터 액터로 둡니다 |
| LocatorInfo | LobbyShootingArea Cube·Scale 1·ControlledPlayer, _Cylinder Cylinder, PaintedArea_Cube/Cylinder, StartPos·StartPosTipsTrial Cone [데이터] |
| 접촉 태그(vt22) | bss 태그 객체 → 이름(`0x7102b582d0` 정적 초기화): `0x71058e88b0` Actor_Player, `0x71058e88d0` Actor_Bullet, `0x71058e8a70` Actor_BulletRollerBody, `0x71058e8b30` Actor_BulletShelterCanopy, `0x71058e8a90` Actor_BulletBomb, `0x71058e8b70` Actor_BulletBlast [판독] |
| 데미지 숫자 애니 슬롯 | 열거 문자열 `"In, Above, Out"` → 핸들 0 In, 1 Above, 2 Out [판독]+[데이터] |

정정(2026-10-03): 이전 판은 영역 모양 번호를 "판정 함수의 case 번호 = 순번+1로 보면 코드와 맞음 [추정]"으로 두었습니다. 위 행 읽기 판독으로 [판독]으로 올립니다. Plane(4)은 판정 함수 `0x71012496e8`에 case가 없어 항상 거짓입니다 [실행].

## 5. 상태 전이와 전체 수명

### 5.1 리셋 (vt15 `0x71021ef388`) [판독]

```
+0x120 = 0;  애니 보조 리셋(0x710125efc8: 슬롯 id −1, tick 0); 몸 활성 플래그 정리
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
| 0 Wait `0x71021f10d8` / `0x71021f11f0` | R+0x1cc(추가 배율) 끔, 몸 둘 다 켬, 캡슐 보간 t = 1, 애니 "" | `hp ≥ max`면 끝. `counter ≤ NoDamageRefreshFrame(120)`이면 끝. 아니면 → Flick |
| 1 DamageShot `0x71021f13a4` / `0x71021f1464` | 애니 "DamageShot" | 애니 끝 → Wait |
| 2 Burst `0x71021f14a0` / `0x71021f1864` | 애니 "Brust", 몸 둘 다 끔, 리시버 무적 모드(R+0x1c4 = 0.0, +0x1c8 = 4 Invincible, +0x1cc = 1), 가산 애니 정지, xlink 키 `Break`(ELink·SLink 둘 다, `0x7103e1e37c` 모드 2), 캡슐 보간 t = 0, SensorMarkable·PoisonEffectable 처리, 전역 메시지 큐(`0x710582b7c0`)에 깨짐 메시지(vtable `0x7105615390`) 추가 | `!IsTipsTrial && 애니 끝` → BurstWait (팁 시험 표적은 Burst 유지) |
| 3 BurstWait `0x71021f19dc` / `0x71021f1a9c` | 애니 "" | HP 다시 채움(§6.2), `counter > BurstWaitDispFrame(120)`이면 홀더 리셋·누계 0 → Expand |
| 4 Expand `0x71021f1ff8` / `0x71021f2308` | 애니 "Expand", 몸 둘 다 켬, 가산 애니 재설정(가중치 0), 팀 표시 플래그 | 애니 진행 중이면 캡슐 보간 t = 현재 프레임/끝 프레임, 끝나면 → Wait |
| 5 Flick `0x71021f2384` / `0x71021f24b8` | 애니 "Flick", 홀더 리셋(hp = max), 누계 0, 리시버 무적 모드 | 애니 끝 → Wait |

- 무적 모드는 Burst·Flick enter에서 켜고 **Wait enter에서만** 끕니다. 즉 Burst → BurstWait → Expand → Wait 동안, Flick → Wait 동안 데미지는 0(결과 Invincible)입니다. Expand 동안 몸은 켜져 있어 탄이 맞고 휨 충격도 받습니다.
- Expand 동안 두 몸의 캡슐은 B 쪽에서 위로 자랍니다(§4.3, t = 0 → 44/45). 이전 판의 "몸 값 +0xdc 보간의 의미 [미확정]"은 §4.3으로 해소했습니다(정정 2026-10-03: 대상은 강체가 아니라 캡슐 형상 A 정점).
- 상태 기계(`0x710125a178` 전이, `0x710125a394` exec, 공용 game 상태 기계) [판독]: 전이는 현재 상태 exit(이 클래스는 없음) → cur = 새 상태, counter = 0, 전이 플래그 = 1 → 새 상태 enter. exec는 전이 플래그 = 0 → 현재 exec → 그 exec 안에서 전이가 없었으면 counter += dt. 같은 상태로의 전이도 enter를 다시 부릅니다(DamageShot 재시작).
- 애니 끝 판정 `0x710126006c`: 스켈레탈 채널 현재 프레임 ≥ 프레임 수(FSKA FrameCount), 루프 비트(리소스 +4 bit2)면 끝나지 않음. 재질 채널은 id가 있을 때만 함께 봄 [실행].

#### 5.2.1 애니 보조(+0x170) 진행 규칙 [실행]+[판독] (2026-10-03)

정정(2026-10-03): 이전 판은 "프레임 진행 속도(1프레임당 1)는 [추정]", §11에서 "1프레임 1, 0부터 [추정]"이었습니다. 원본 실행으로 확정했고, **재생 직후 첫 갱신은 프레임을 올리지 않는다**는 규칙이 추가됩니다.

- 생성(vt8): 슬롯 2개(블렌드용), +0x2c = 0(슬롯 0만 진행), +0x90 = 1.0(기본 재생 속도), +0x80 = 0(이름별 속도 표 없음; 표적 코드에서 쓰는 곳 없음) [판독].
- 재생 `0x710125f27c(name)` → `0x7101266974`: 이름을 모델 애니 목록에서 찾으면 새 슬롯을 앞에 넣고 **frame = 0, rate = 1, 블렌드 t = 0·속도 1, tick(+0x18) = 0**. 이어서 재질 채널 2개(+0x30, +0x58)에서 같은 이름을 찾고(표적 bfres에는 같은 이름의 재질 애니가 없음), `0x710125fa40`이 rate = +0x90(= 1.0)으로 둡니다. 이름을 찾지 못하면(빈 이름 "") 슬롯을 바꾸지 않습니다 [실행]+[판독].
- 갱신 `0x71012664cc`: **tick > 0일 때만** frame += rate, 루프 비트가 없으면 [0, 프레임 수]로 자릅니다. 그 뒤 블렌드 가중치 (1 − cos(π·t))/2(t += 블렌드 속도 1 → 첫 갱신에 1, 즉시 전환), tick += 1 [실행].
- 끝 판정은 frame ≥ 프레임 수 [실행].
- 결과: 재생한 같은 vt18 안에서 갱신이 한 번 돌아도 frame은 0에 머물고, 다음 갱신부터 1씩 오릅니다. 원본 실행 결과 끝 판정이 처음 참이 되는 갱신 횟수는 Brust 2, DamageShot 31, Expand 46, Flick 25(rate 1), rate 0.5면 3/61/91/49입니다.

### 5.3 수명 요약 (데이터 기본값, 1프레임 = 1/60초, 상태 기계 dt = 1 가정)

정정(2026-10-03): 이전 판의 "웹 재구현 기준 프레임 수(31스텝째 Wait, 153스텝째 Flick, BurstWait 122스텝, Expand 45스텝)"는 §5.2.1의 첫 갱신 규칙을 빠뜨린 값입니다. 원본 규칙으로 다시 센 값은 아래입니다 [판독+실행 규칙의 조합 = 재구현]. 상태 기계 dt가 1인지는 [추정]입니다(§11).

```
피격(리스너, vt18 밖) ── DamageShot 재생(frame 0, tick 0)
  vt18 #1: exec(frame 0) · 갱신(진행 없음)
  vt18 #k(k≥2): exec가 보는 frame = k−2  → #32 에서 frame 30 ≥ 30 → Wait  (피격 뒤 32번째 vt18)
Wait 진입(#32) → Wait exec 가 보는 counter = j−1 (진입 뒤 j번째 vt18) → counter > 120 이면 Flick: j = 122
  → 마지막 피격 뒤 154번째 vt18 에 Flick 진입
Flick 진입 vt18(F0) → F0+25 에서 Wait (Flick 25프레임)
HP<1(단계 4 홀더 갱신 뒤) → 다음 vt18(B0) 처음에 Burst 진입, 같은 exec 에서 frame 0
  B0+2 에서 BurstWait 진입 (Burst 2프레임)
BurstWait 진입(W0) → W0+j 에서 counter = j−1 → counter > 120 이면 Expand: W0+122
  HP: counter 0~60 은 0, 61~120 은 0→max 선형(§6.2)
Expand 진입(E0) → E0+k(k=1..45) 캡슐 t = (k−1)/45 → E0+46 에서 Wait (Expand 46프레임)
```

웹 현재 값과의 차이(웹 반영 필요): DamageShot→Wait +1(31→32), 무피격 Flick +1(153→154), Flick 길이 25, Burst 2, Expand 46, HP 반영과 Burst 검사 순서(§3.2.1).

## 6. 계산식·조건·상세 의사코드

### 6.1 데미지 [판독 — 공용 리시버, damage_hit.md §6.4]

```
dmg = info.value (0.1 HP)
if R.team ∉ {−1, 3} && R.team == 공격 팀:  결과 Through, 0
결과 = Damaged(6)
if R+0x1cc: dmg = fcvtzs((R+0x1c4 + 1e-5) × dmg);  결과 = R+0x1c8 (≠8이면)
dmg = fcvtzs((DamageRate(행=무기, 열="Default") + 1e-5) × dmg)
if dmg == 0: 결과 = (R+0x1cc && R+0x1c8 != 6) ? R+0x1c8 : Through
dmg > 99999 → 99998
```

표적 열은 `Default`라 슈터(`Shooter___Default`)는 1.0 → 스플래시슈터 360(36.0) 3발로 1000을 넘어 깨집니다 [재구현]. 표적 HP 1000은 플레이어와 같습니다. 수신 이력 모드(송신자 vt+0x20)는 탄 쪽 값이라 [미확정] (combat 영역, [../combat/hitbox.md](../combat/hitbox.md) §4), 표적은 vt9에서 시간 창(R+0x1fc)을 끕니다 [판독].

### 6.2 BurstWait의 HP 다시 채우기 `0x71021f1a9c` [판독]

```
i = (int)(counter − LossOfColorWaitFrame)                // f32 빼기 후 절삭
t = (i < 0) ? 0 : min( (float)i / (float)max(BurstWaitDispFrame − LossOfColorWaitFrame, 1 (2 미만이면 1)), 1 )
v = (uint)(t × (float)H.max)
H.hp = (v ≥ lo) ? min(v, H.max) : lo,     lo = (H.flags & 1) ? −H.max : 0
if (float)BurstWaitDispFrame < counter:  0x7101a88e1c(H) (hp = max), +0x120 = 0, → Expand
```

정정(2026-10-03, 6차): 이전 판은 "HP를 0에서 max로 올리는 것은 … 잉크 색이 빠지는 연출로 보입니다 **[추정]**"이었습니다. 아래 §6.2.1 판독으로 **[판독]+[데이터]**로 올립니다. 이전 판이 다음 단서로 적은 `0x7101a8439c`·`0x7101e2ab94`는 파라미터 방문 함수(이름·오프셋 등록)일 뿐 값을 쓰는 곳이 아니었습니다. `0x7101a8439c`는 HitPointHolder 파라미터 방문 `0x7101a84204` 안, `0x7101e2ab94`는 다른 구조체(PaintMagnification +0x34, PaintBias +0x30)의 방문 `0x7101e2aacc`입니다.

#### 6.2.1 모델 칠 보완(LossOfColor의 실제 경로) [판독]+[데이터] (2026-10-03)

기준 객체: `HitPointHolderArray` 파라미터 항목(방문 `0x7101a84204`). Name +0x30, RefComplementPaintModelKey +0x38(문자열), MaxHitPoint +0x40, PaintBias +0x44, PaintMagnification +0x48, SlipCure +0x4c, IsRefComplementPaintToModel +0x50(bool). 기본값은 MaxHitPoint 0, SlipCure 0, IsRef… **true**, PaintMagnification **1.0**, PaintBias **0.5**입니다(이미지 `0x7104a9badc`~`0x7104a9baec`) [데이터]. 표적 데이터는 IsRef… true, PaintBias 0.5만 적혀 있어 Magnification은 기본 1.0입니다.

1. 생성: DamageHelper 초기화 `0x7101e3d69c`가 항목마다 홀더 +0x124 = SlipCure를 넣고, IsRef…가 참이면 칠 보완 대상을 만듭니다. 키 문자열이 비어 있으면 액터 모델(`param_1[0x42]` vt+200)을 쓰고, 객체(vtable = `[0x7105799450]+0x10`, +8/+0xc/+0x10 = 채널 0/1/2 마지막 값, 처음 NaN, +0x18 = 모델)를 이름(Name)으로 찾을 수 있게 등록합니다 [판독].
2. 매 프레임: DamageHelper 슬롯23 `0x7101e43218`이 **HP 홀더 갱신(`0x7101a8905c`) 직후** 칠 보완 대상마다 아래를 계산합니다 [판독].

```
t = (max != 0) ? 1 − hp/max : 1                   // H+0x48 max, +0x4c hp, f32 나눗셈
if Mag(+0x48) > 0:
    b = clamp(Bias(+0x44) / Mag, 0, 1)
    if −0.001 ≤ b − 0.5 ≤ 0.001:  f = t                         // 표적: b = 0.5 → 선형
    elif |t| < 0.001:              f = 0
    elif b < 0.001:                f = (|t| ≥ 0.999) ? 1 : 0
    else:                          f = sign(t) · expf(logf(|t|) · (logf(b) · −1.442695))   // 0x7101e438f8~0x7101e43924
    v = Mag · f
else: v = 0
ch = H+0x13c                                        // 마지막 적용 피격의 팀(lastHit 팀, 홀더 갱신이 +0x54에서 복사)
채널 ch(0..2)는 v로, 나머지 채널은 0으로: 이전 값과 0.01보다 크게 다르거나 0이 되는 순간에만 vt+0x10(v, 객체, 채널) 호출
ch == −1이면 세 채널 모두 0
```

3. vt+0x10 = `0x71010ff640` → 모델 인스턴스마다 `0x7101103270(v, 모델, 채널)` → 재질마다 `0x710110513c`: 셰이더 아카이브가 `Hoian_UBER`인 재질에만, 채널별 재질 파라미터 `thr_comp_paint_intens_alpha`/`_bravo`/`_charlie`(표 `0x7105560440`)에 v를 쓰고, 재질 옵션 `comp_paint_type`이 `'2'`이면 세 값 중 최대인 팀을 `two_comp_paint_team`에, 최대값을 `two_color_complement_paint_intensity`(`0x7105560470`)에 씁니다 [판독]. 표적 `M_Body`는 `Hoian_UBER`이고 이 파라미터들을 가집니다(기본 0) [데이터]. `M_Body`의 `comp_paint_type` 옵션 값은 bfres 덤프에 없어(셰이더 아카이브 기본값) [미확정]입니다.

결과(표적, Mag 1·Bias 0.5): **표적 몸의 보완 칠 세기 = 1 − hp/max, 색 = 마지막으로 맞힌 팀의 잉크**입니다. 맞을수록 몸이 상대 잉크색으로 칠해지고, BurstWait의 HP 0 → max 선형 복귀(카운터 61~120) 동안 세기가 1 → 0으로 빠집니다. Flick(hp = max)에서는 한 프레임에 0이 됩니다. 이것이 파라미터 이름 LossOfColorWaitFrame(60)의 "색 빠짐"입니다 [판독]. 화면에 어떻게 그려지는지(셰이더 식)는 그래픽 영역입니다. 웹 반영: 표적 재질에 "공격 팀 색 × (1 − hp/max)" 보완 칠 세기를 넘겨야 합니다.

머티리얼 애니 `Damage`(100프레임)는 `M_Body`의 바로 이 파라미터 `two_color_complement_paint_intensity`를 움직이는 커브 1개입니다 [데이터]. 실행 중에는 위 경로가 같은 파라미터를 직접 씁니다. 이 애니를 재생하는 코드는 표적·DamageHelper 범위에서 찾지 못했습니다 [미확정] (§11).

### 6.3 휨 계산기 (spl::BendCalculator) [실행]

원본 실행(§10): 충격 `0x7101e3422c` 9,440회, 갱신 `0x7101e33ed8`과 방향각 `0x7101e34468` 8,030스텝, atan2Idx `0x7101252998` 3,015건이 아래 식(f32, 명령 순서 그대로)과 비트 일치합니다. 회전이 있는 축·임의 Kd/Kp·종류 0~3·스케일 여러 값을 넣었습니다.

충격 `0x7101e3422c(scale, B, 접촉 위치 c, 충격 벡터 J, 종류 k)`: 기준 B = 계산기, B+0x30 액터 위치 P, B+0x3c/+0x48/+0x54 액터 X/Y/Z 축(이전 갱신에서 복사; 액터 행렬 +0x298 3×4의 열).

```
if k ≥ 3: return
d = c − P
a = dot(d, X) × −10;  e = dot(d, Z) × −10;  L = sqrt((a·a + 0) + e·e)
n = L > 0 ? (a/L, 0×(1/L), e/L) : (a, 0, e)
s = 계수표[k] × ( ((dot(J,X)·10)·0.016666668)·n.x + ((dot(J,Y)·10)·0.016666668)·n.y + ((dot(J,Z)·10)·0.016666668)·n.z );  s = min(s, 1)
r = min(scale, 0.4)/0.4;  g = |r| ≥ 0.001 ? sign(r)·expf(logf(|r|)×2.321928) : 0
B+0x60 += (n.x·s)·g, (n.y·s)·g, (n.z·s)·g
```

표적 vt22는 scale 자리에 **상수 1.0**을 넘깁니다(`0x71021f0a5c fmov s0, #1.0`) → g = 1. `Scale` 파라미터(대형 1.3)는 휨 크기에 들어가지 않습니다 [판독].

갱신 `0x7101e33ed8`(매 프레임):

```
P, X, Y, Z ← 액터
v(+0x78) = Kd × (v + imp(+0x60))
v = v − p_old(+0x6c) × Kp
p = v + p_old;  if |p|² > 1: p = p × (1/sqrt(|p|²))
imp = 0
```

방향각 `0x7101e34468`: w = X·p.x + Y·p.y + Z·p.z(성분별 (X·p0 + Y·p1) + Z·p2),
a = ((Z.y·w.z − w.y·Z.z)·Y.x + (w.x·Z.z − w.z·Z.x)·Y.y) + (w.y·Z.x − w.x·Z.y)·Y.z,
b = ((Z.y·w.y + w.x·Z.x) + w.z·Z.z) − ((Z.x·Y.x + Z.y·Y.y) + Z.z·Y.z)·((w.x·Y.x + w.y·Y.y) + w.z·Y.z),
각 = atan2Idx(a, b)(u32, 표 `0x7104aa6b6c` 128구간 선형 보간) × 1.4629181e-09 → (−π, π]로 접은 뒤 음수면 +2π. 로컬로는 atan2(p.x, p.z) — 0 = 앞(+Z), 90° = +X. 이 각(도)이 반복 애니 `DamageShotBend`(360프레임)의 프레임, |p|(1로 자름)가 가중치입니다.

- atan2Idx(y = s0, x = s1)는 sead 방식 정수 각도입니다: 팔분면마다 t = 작은 쪽/큰 쪽, i = trunc(t·128), 결과 = 표[i].idx + (u32)(표[i].slope × (t·128 − i))를 0, 0x40000000, 0x80000000, 0xC0000000에 더하거나 뺌. x = y = 0이면 0, 무한대는 고정 값 [실행]. 웹은 `Math.atan2`가 아니라 이 표 방식을 써야 비트가 맞습니다.

접촉 종류와 충격 벡터(vt22 `0x71021f0348`, 접촉 태그 6종 `0x71012d3e10`) [판독]. 정정(2026-10-03): 이전 판은 "태그 ↔ 대상 대응은 계수 이름으로 정함"이었습니다. 태그 이름을 정적 초기화에서 읽어 확정합니다(§4.5).

| 접촉 태그 | 위치 c | 충격 J | 종류 |
|---|---|---|---|
| Actor_BulletRollerBody, Actor_BulletShelterCanopy | — | 무시(먼저 검사) | |
| Actor_Player | 접촉점(+법선×깊이) | −법선 × (접촉점+0x60) × PlayerImpulsScaler | 1 |
| Actor_BulletBlast이고 접촉점+0x30 > 0 | — | 무시 | |
| Actor_BulletBomb | 접촉점 | 접촉 vt+0x18 속도 × BombImpulsScaler | 2 |
| Actor_Bullet | 상대 몸 위치(탄 바디 +0x94 또는 강체 이동 성분) | 접촉 vt+0x18 속도의 **y를 0**으로 × BulletImpulsScaler | 0 |

**접촉 vt+0x18 속도 단위 [판독] (2026-10-03, 이전 [미확정])**: 표적 vt22가 받는 접촉 객체는 방문자 `0x71012d2e4c`가 스택에 만든 객체(vtable `0x71055760d8`, +0x10 = 접촉쌍)이고 vt+0x18 = `0x71012d4a48`입니다. 이 함수는 접촉쌍의 **상대 몸**을 골라, 접촉점 플래그(+0x69 bit4)가 켜져 있으면(상대 = 탄 바디) `0x71012ece20`, 아니면(상대 = 강체) `0x71012eccd0`으로 갑니다. 둘 다 속도 공급자(+0x148 / +0x260)가 없으면 각각 **탄 바디 +0xdc(이번 스텝에 쓴 속도)**, **강체 +0x138(선속도)**를 그대로 돌려줍니다. 둘 다 **유닛/초**입니다(탄 바디 setVelocity가 v·60을 씀, 강체는 setLinearVelocity `0x7103ae2890` 유닛/초 — [../physics/phive_controller.md](../physics/phive_controller.md) §6.3, §3). 공급자가 있으면 접촉점을 몸 로컬로 바꿔 공급자 vt+0x10에 묻고 다시 월드로 돌립니다. 탄 바디 생성자 `0x7103b0af78`이 `0x7103b0b1a4 stp xzr, xzr, [x22, #0x140]`으로 +0x140·+0x148을 0으로 두고, 탄 바디 클래스 함수 범위(0x7103b0a000~0x7103b0c000)에는 +0x148을 쓰는 명령이 없습니다 [판독]. 따라서 슈터 탄에서는 J = 1.66 × 60 × (v_x, 0, v_z)(v = 프레임당 탄 속도)입니다. 웹의 "속도 × 60" 가정과 같습니다. 이 범위 밖 phive 코드의 +0x148 쓰기(예: `0x7103ada484`)가 탄 바디에 닿는지는 확인하지 않았습니다.

플레이어 접촉의 접촉점+0x60은 탄 바디 접촉 목록에서는 쓸어 넘기기 비율 f입니다([../physics/phive_controller.md](../physics/phive_controller.md) §6.4). 플레이어(캐릭터 강체) 접촉에서도 같은 구조인지는 [미확정]입니다. 6차 확인(2026-10-03): 쓸어 넘기기 `0x7103c55968`의 BL 호출자는 탄 바디 스텝 `0x7103b0a454` 하나뿐이고, `0x7103c40000`~`0x7103c60000`에서 +0x60에 f32를 쓰는 곳은 `0x7103c59234`(`0x7103c58e4c` 안, 다른 구조체로 보임) 하나였습니다. 캐릭터 강체 ↔ 키네마틱 강체 접촉의 접촉점 작성자는 찾지 못했습니다 [미확정]. 물리 영역에 넘겼습니다(SHARED `[r6 range→physics]`).

### 6.4 데미지 숫자 (vt19 `0x71021efc24`, 표시 `0x71021f0c90` → `0x710338cf0c`, 텍스트 `0x710338d2d0`) [판독]+[실행]

```
if !IsAlwaysDrawDamageInfo && H.max ≤ H.hp:
    Shr_Points_00의 이 액터 슬롯을 닫음(핸들 2 Out: 명령 1, a −1, b 1.0 → 처음부터 재생; 닫는 중 표시)
elif 카메라 모듈(*0x710580c3b0+0xe8) 활성(+0x140):
    거리 = |카메라 위치(+0x144) − 액터 위치(+0x28c)|
    if 거리 ≤ DrawDamageInfoDistance(40):
        표시(값 v = (f32)누계 / 10.0f (scvtf → fdiv), 위치 = 액터 위치 + 액터 Y축 × DamageInfoOffsetY(2.6),
             액터 id, isMax = H.max ≤ 누계)
```

텍스트 갱신 `0x710338d2d0`(레이아웃 calc) [실행, 4,872건 비트 일치]:

```
for 활성 슬롯:
    if v != 이전 값(+0x378):
        i = floor(v)            // fcvtzs 후 (v<0 && 정수 아님)이면 −1
        d = floor((v − i) × 10) // 같은 방식
        T_Num_00 ← 메시지 "000" = "[2:0:00030000].[2:0:01010000]" 에 인자 (i, d)
        이전 값 = v
for 활성 슬롯: if 슬롯 age(+0x3c) ≥ 2 && 닫는 중 아님: Out 재생, 닫는 중 표시
```

- 소수는 **한 자리, 반올림이 아니라 버림**입니다. f32라 누계 13 → v = 1.29999995 → "1.2"처럼 소수 자리가 하나 작게 나오는 경우가 있습니다(누계 0~99,999 중 39,995개). 10의 배수(스플래시슈터 360 등)는 "36.0"으로 맞습니다 [실행]. 정정(2026-10-03): 이전 판의 "소수 자릿수(1자리)는 [추정]"을 [실행]으로 올리고, 웹의 `toFixed(1)`(반올림)과 다름을 적습니다.
- 숫자 태그 인자 바이트(`03`, `01`)가 자릿수·0 채움인지는 UI 영역의 [추정]입니다([../ui/ui_layout_format.md](../ui/ui_layout_format.md) §7). 텍스트 상자 기본 문자열은 `０００.０`입니다 [데이터].
- 레이아웃 `Shr_Points_00`은 슬롯 최대 16개(액터 id로 슬롯 재사용) [판독]. 슬롯마다 애니 핸들 3개 In/Above/Out(§4.5) [판독]+[데이터]:
  - 새 슬롯: In 명령 1(처음부터, 속도 1) → `N_All_00` 알파 0 → 255(8프레임).
  - isMax가 바뀔 때 Above: 참이면 명령 1(재생), 거짓이면 명령 6(첫 프레임 정지). Above = `T_Num_00` 크기 1 → 2 → 1(8프레임, 4프레임에 2배)과 글자색 (255, 255, 255) → (255, 33, 13)(8프레임), 반복 없음 → **누계가 최대 HP 이상이면 숫자가 한 번 커졌다 돌아오고 주황빛 빨강으로 남습니다** [데이터]+[판독]. 정정(2026-10-03): 이전 판의 "isMax 모양 [미확정]"을 해소했습니다.
  - Out: `N_All_00` 알파 255 → 0(8프레임). 닫는 중이던 슬롯을 다시 쓰면 Out 명령 10(끔).
  - 슬롯 age(+0x3c)는 레이아웃 기반 calc `0x71032031d0`이 활성 슬롯마다 1씩 올립니다 [판독]. 다시 0으로 돌리는 곳(표시 함수 vt+0x438 추정)은 [미확정]입니다. 즉 거리 40 밖으로 나가 표시 요청이 끊기면 몇 프레임 뒤 Out으로 사라지는 것으로 보입니다 [추정].
- 명령 번호의 뜻은 [../ui/ui_hud.md](../ui/ui_hud.md) §5.3 표(원본 실행 13건)를 따릅니다.

### 6.5 이동 표적 레일 [판독]

`spl::RailMovableSequentialHelper`(vtable `0x71055edbf8`): 초기화 vt7 `0x7101e7f4ac`가 `ToRailPoint`(Banc `spl__RailMovableSequentialHelperBancParam`)로 레일 점을 찾고(`0x7101302ba8`), `game::RailMovableSequential`(0x18f8 B, vtable `0x7105577e98`, 어댑터 vtable `0x7105587318` — 이동 발판과 **같은 객체**)을 만들어 일정 `0x7101305238`을 짓습니다. 리셋 vt13 `0x7101e7f86c` = 시작 점 자세 복사 + 시간 0(vt5 `0x71013046c4`). 표적 vt18이 객체 vt6 `0x71013046d4`로 `t += dt`(역재생 플래그 +0x18f4면 −dt) → 시간 평가 `0x71013043d8`(stage_misc §1.3).

**보강(정정 제안)**: 이동 시간 `0x7101305b40`의 cSpeed는 어댑터 vt+0x70 `0x710147b6dc(a, b, rev)`를 **rev 플래그와 함께** 부릅니다. 이 함수는 rev이면 `d[b]−d[a]`의 부호를 뒤집으므로 역방향 이동 시간도 양수입니다. 이동 함수 `0x7101304cec`의 거리 계산은 플래그 0(부호 있는 길이)을 씁니다. `web/tools/gimmick_lift.py`의 `seg_len`은 두 곳 모두 플래그 0이라 cSpeed 왕복에서 역방향 구간이 빠집니다(Carousel은 cTime이라 영향 없음).

로비 레일과 결과 [데이터]+[재구현]:

| 표적 | 레일(점 Y −90°) | 속도 | 한 구간 | 주기 |
|---|---|---|---|---|
| Move #1 (15066127630233066301) | (40,0,18) → (40,0,3) | 7 | 15/7 = 2.142857초 | 4.285714초 |
| Move #2 (1759095691775920200) | (40,6,3) → (40,6,18) | 4 | 3.75초 | 7.5초 |
| Move #3 (10119736514646560643) | (33.5,0,3) → (33.5,0,18) | 5 | 3.0초 | 6.0초 |

위치 = 레일 위치(배치 Translate의 Y 2/7/0.5는 리셋에서 레일 점으로 덮임), 회전 = 점 회전 Ry(−90°)(배치 Rotate와 같음).

**Main 강체로 넘기는 방식 [판독] (2026-10-03)**: `0x7103ae41b8(강체, out, 목표 위치)`는 목표가 NaN이면 경고만 하고, 아니면 `out = (목표 − (현재 위치 + dt·(ω × (현재 위치 − 질량 중심)))) × (1/dt)`(dt = 월드+0x24, 1/dt = 월드+0x28)를 계산하고, `0x7103ae2890`이 이 값을 선속도(유닛/초)로 씁니다. 즉 키네마틱 Main 몸은 한 물리 스텝에 레일 위치로 옮겨지고, 회전은 이 경로로 넘기지 않습니다. 액터 행렬이 Main 몸을 따라가는 경로(컨트롤러 Main `IsTrackingActor false`, `WarpMode AfterUpdateWorldMtx`)는 여전히 [미확정]입니다.

6차 진척(2026-10-03) [판독]: RigidBodyController 파라미터 방문 `0x7103b9e32c`/`0x7103b89c4c` 기준 오프셋은 TrackingBoneName +0x40, TrackingEntityAlias +0x48, BoneBindModePosition +0x50, BoneBindModeRotation +0x54, **WarpMode +0x58**(열거 `AfterUpdateWorldMtx, BeforeUpdateWorldMtx, None`), IsTrackingEntity +0x5e, **IsTrackingActor +0x69**, **UseNextMainRigidBodyMatrix +0x6a**입니다. 실행용 기록은 `0x7103ae9f2c`가 몸마다 0x18 B 칸(소유 객체 +0x28 배열)에 만듭니다: 칸+0xc = BoneBindModeRotation, 칸+0x10 = WarpMode, 칸 바이트0 bit1 = IsTrackingActor(참일 때 OR 2), bit6 = UseNextMainRigidBodyMatrix(`& 0xbf | v<<6`). 이 칸을 읽어 액터 행렬을 몸에서 되돌려 쓰는 함수는 찾지 못했습니다 [미확정]. 다음 단서: 칸 +0x10(WarpMode)·바이트0 bit1을 읽는 곳, 물리 영역 `[r6 physics]`의 슬롯19 write-back 동적 추적(`0x7100f76f78`).

### 6.6 사격 구역 [판독]+[데이터]+[실행]

안쪽 판정 `0x71012496e8(영역, 점)`(영역+0x20 모양, +0x24 배율 s, 로케이터 액터 +0x40 위치 T, +0x4c 3×3 m[0..8], +0x70 스케일 S). 원본 실행 7모양 × 1,500건 = 10,500건이 아래 식과 비트 일치합니다 [실행].

```
d = p − T;  l_c = m[c]·d.x + m[3+c]·d.y + m[6+c]·d.z            // 열 c 와의 내적
Cone(1):       0 ≤ l_y < 2·s·Sy 이고 sqrt(l_x² + l_z²)/(2·s·Sy − l_y) < (s·Sx)/(2·s·Sy)
Cube(2):       |l_x| ≤ s·Sx·0.5 && |l_y| ≤ s·Sy·0.5 && |l_z| ≤ s·Sz·0.5
Cylinder(3):   0 ≤ l_y < 2·s·Sy && l_x² + l_z² < (s·Sx)²          // 바닥이 원점
Plane(4):      항상 거짓
Sphere(5):     |T − p|² ≤ (Sx·s)²
ConeShift(6):  −2·s·Sy ≤ l_y < 0 이고 sqrt(l_x² + l_z²)/(−l_y) < (s·Sx)/(2·s·Sy)
Hemisphere(7): |d|² ≤ (Sx·s)² && l_y ≥ 0
```

플레이어 쪽(`0x7102483134` 안 `0x7102484ff8`~`0x7102489e6c`, 로비 분기): 이름 `"LobbyShootingArea"` 영역 목록을 먼저, 없으면 `"LobbyShootingArea_Cylinder"` 목록을 돌며 본체+0x10 위치로 판정 → **본체+0x938d = 안쪽 여부**. 그리고 `본체+0xc0(공중 프레임) < 4`(상수 `0x71058bbc20`)일 때만 **본체+0x938c = 안쪽 여부**(공중에서는 이전 값 유지).

**효과 [판독] (2026-10-03, 이전 [추정])**: 입력 송신 `0x7102630e6c`가 입력 판정 `0x710246b8c8`에 `본체+0x938c` 주소를 넘기고, 그 안 `0x710246c290`~`0x710246c2b0`에서

```
if [0x71058e87ac] != 0 && 본체+0x938d == 0:      // 전역 플래그(로비 경로에서 쓰임, 이름 [미확정]), 공중 래치 없는 값
    출력 21 = 0; 출력 22 = 0; 출력 25 = 0
```

를 합니다. 이 세 출력은 InputSender 우선순위 목록의 입력 종류 1·2·3(+0x54 / +0x56 / +0x57 쪽, 누름 비트 5 / 14 / 0·13)의 "허용" 값이고, 종류 0(오징어, +0x55, 누름 비트 2)은 건드리지 않습니다([../player/player_state.md](../player/player_state.md) §6.1.1). 즉 **로비 플래그가 켜져 있으면 구역 밖에서는 오징어 입력만 남고 나머지 세 버튼 입력이 버려집니다**. 판정에는 공중 래치가 없는 +0x938d를 씁니다. 버튼 이름(종류 1 = 메인 사격 등)은 player 영역의 [추정]입니다.

+0x938c(공중 래치 값)를 읽는 곳: 정지 상태 선택(`0x710244187c` — WaitHold_Sp 조건 `B+0xbe4 ≥ 1 && !Demo+0x37 && B+0x938c`), 입력 송신, 원격 표시(`life/batch1.c` 11190행 조건), UI(`0x71031eaac8` 스페셜 표시), 미니맵 `0x7102264240`.

**로케이터 회전 저장 순서 [실행]+[판독] (2026-10-03, 6차)**: `0x7100f827c4`는 생성 정보의 플래그 바이트(+0x90) bit0이면 위치(+0..+8 → 액터 +0x40), bit1이면 9개 f32(+0xc..+0x2c → 액터 +0x4c..+0x6c, 순서 그대로), bit2이면 스케일(+0x30.. → +0x70)을 복사합니다 [판독]. `0x7103d03658`은 Rotate 읽기가 아니라 형식 키(`&0x710599eea8`)를 돌려주는 작은 함수였습니다 [판독]. Banc `Rotate` → 생성 정보는 [r6 assets]가 `0x7103d03f4c`를 원본 실행해 확정했습니다: **R = Rz·Ry·Rx(라디안, x = Rotate[0]), 3×3 행 우선 저장, 스케일은 곱하지 않고 따로 복사**(로비 부모 행렬 = 단위, 4257/4257 비트 일치, [../gimmick/stage_misc.md](../gimmick/stage_misc.md) §5.1). 판정의 l_c = m[c]·d.x + m[3+c]·d.y + m[6+c]·d.z에 m[3r+c] = R[r][c]를 넣으면 l = Rᵀ(p − T)입니다. 따라서 아래 이전 판의 [추정] l = Rᵀ(p − T)를 확정합니다(정정 2026-10-03: 이유 = 작성자 원본 실행 + 판정 열 내적 판독). 웹 `range_area`의 현재 식이 이와 같으면 그대로 둡니다.

과거 기록: 로케이터 행렬 저장 순서는 확인하지 않았습니다. 판정은 열 내적(= 행 우선 저장이면 Rᵀ(p − T), 로컬 좌표)을 씁니다. 로케이터 액터 +0x4c는 생성 정보 +0xc..+0x2c를 그대로 복사한 값(`0x7100f827c4`, `0x7100f82874`~`0x7100f828d0`)이고, 생성 정보의 3×3이 Banc `Rotate`(오일러, `0x7103d03658`이 읽음)에서 어떻게 만들어지는지는 [미확정]입니다 **[추정: l = Rᵀ(p − T)]**(회전된 영역은 Y 0.778 rad 상자 1개).

### 6.7 팁 시험(TipsTrial) 진행 [판독]+[데이터] (2026-10-03, 6차)

이전 판은 "팁 시험 진행(AINB)·WoodenFigure 공격 상세·PaintedArea 칠 요청 형식은 범위 밖"이었습니다. 진행 흐름은 아래처럼 확정했고, WoodenFigure 공격과 PaintedArea 칠 형식은 남았습니다(§11).

#### 6.7.1 데이터: 팁 시험 53종 `spl__TipsTrialParam` [데이터]+[판독]

Bootup 팩 `Gyml/TipsTrial/<이름>.spl__TipsTrialParam.bgyml` 53개(전체 덤프 `analysis/r6_range/tipstrial/all_tipstrial_params.json`). 파라미터 클래스(방문 `0x7102df12cc`, 생성자 `0x7102df0ff4`, 0x78 B):

| 오프셋 | 이름 | 기본값 | 뜻(판독) |
|---|---|---|---|
| +0x38 | HintText | "" | 안내 문구 |
| +0x40 | LocatorName | "" | 시작 위치: `StartPosTipsTrial` 로케이터 이름(§6.7.3 `0x7102e20a28`) |
| +0x48 | Playground | "" | 로직 AINB의 `SplLogicJudgeTipsPlayground.Name`과 맞춰 보는 이름(§6.7.2) |
| +0x50 | WeaponName | "" | 시험 무기 |
| +0x58 | Judge | **1 = BreakAllSighterTarget** | 열거 `BreakOneSighterTarget(0), BreakAllSighterTarget(1), UseSubWeapon3Times(2), UseSpecialWeapon3Times(3), UseTeamSignal3Times(4)`(열거 문자열 `0x710492b114`, 열거 객체 vtable `0x7105691848`의 슬롯6이 `0x7102df342c`로 이 문자열을 씀) |
| +0x5c | JudgeDelay | 0.0 | 판정 성공 뒤 대기(초, ×60 프레임) |
| +0x60 | SpecialState | 0 | `AlwaysFull` 등 |
| +0x64 | VariableN | **3** | 횟수형 판정의 목표 횟수 |
| +0x30 | ControlLimit(구조체) | | `CanUseShot/Squid/Bomb/Jump/LStick/Minimap/RStickPress/TeamSignal` = Always/None/InSpecial… |

Judge가 없는 파일은 기본 BreakAll입니다(예: `Aim`, `Blaster`, `Charger`). 명시된 값은 UseSubWeapon3Times 9종, UseSpecialWeapon3Times 4종(VariableN 1), UseTeamSignal3Times 1종(`Signal`), BreakAllSighterTarget 1종(`SpUltraShot`)입니다. Playground 이름은 25종이고, 로직 AINB의 JudgeTipsPlayground 노드 25개의 Name과 집합이 정확히 같습니다(예: `Aim`·`BombQuick`·`SubWeapon`·`SpecialWeapon` → `Front_10-20_Cen`).

#### 6.7.2 로직 AINB `Lby_Lobby00_5bad` [데이터] + 노드 코드 [판독]

`Logic/Lby_Lobby00_5bad.logic.root.ainb`(AIB 0x404, 카테고리 `Logic`, 147노드)를 `web/tools/r6_range_ainb.py`로 해독했습니다(그래프 `analysis/r6_range/ainb_dump.txt`). Banc `AiGroups[0].References`가 InstanceName → 배치 Hash를 잇습니다.

| 노드 클래스 | 개수 | 입출력 | 코드 |
|---|---:|---|---|
| `SplLogicJudgeTipsPlayground` | 25 | 즉시값 `Name`, 출력 펄스 `Restore`, `Setup` | vtable `0x7105679510`, 등록 이름 `LogicSplLogicJudgeTipsPlayground`(`0x7102bb8df8`). 슬롯24 `0x7102bb917c`가 Name·Setup·Restore를 묶고, 슬롯37 `0x7102bb902c`가 메시지 버스(`*0x7105801908`)에 형식 키 `0x71058ebfd8`로 수신자를 등록. 수신 `0x7102bb9054(노드, msg)`: `msg+0x20`(문자열) == Name이면 `msg+0x18`(bool)이 참 → Setup 펄스 = 1, 거짓 → Restore 펄스 = 1 [판독] |
| `SplLogicActor` | 47 | 즉시값 `InstanceName`, 입력 `Logic_Activate`·`Logic_Sleep`, 출력 `Logic_IsActive`·`Logic_OnSleep` | vtable `0x710553cd00`(생성 `0x7100f40f88`), 슬롯24 `0x7100f40678`이 `Logic_Activate`를 묶음 |
| `GameFlowPulseOr` | 19 | 다중 입력 `MultiInput` → `Output` | |
| `GameFlowDevLogNotice` | 48 | `Category`/`Message`(개발 로그) | 동작 없음(로그) |
| `SplLogicBhvSpawnerForShieldGimmick` / `…BeaconGimmick` | 2 / 1 | 입력 `Spawn` | |
| `SplLogicBhvWoodenFigure` | 1 | 입력 `IsAutomationMain`(bool), `Logic_Activate`(연결 없음) | |
| `GameFlowPulseToBool` / `GameFlowBoolToPulse` | 1 / 1 | | |
| `SplLogicBhvAreaSwitch` | 1 | `IsOneTime` true, `LocatorAreaSwitch_addc`, 출력 `IsInside` | |
| `SplLogicLobbyToPlaza` | 1 | 입력 `Pulse` | 등록 이름 `LogicSplLogicLobbyToPlaza` |

그래프 요점 [데이터]:
- 모든 `SplLogicActor.Logic_Sleep` 입력과 모든 JudgeTipsPlayground의 `Restore` 출력은 **연결이 없습니다**. 즉 이 AINB는 Setup 때 켜기만 하고 끄는 일은 하지 않습니다(끄기는 §6.7.4 Restore 코드).
- Playground별 Setup이 켜는 것(PulseOr로 묶임): 예) `Front_10-20` → PaintedArea 원기둥 5개(f2d5·8822·8ca0·5e68·1ef5)·`SighterTarget_TipsTrial_adb6`; `MoveTargetShield` → 이동 표적 2개(034e·9bea)·`SpawnerForShieldGimmick` 2개; `SuperJump` → `SpawnerForBeaconGimmick_af2b`·Jump 표적; `WoodenFigure` → PaintedArea `a52a`와 `GameFlowPulseToBool` → `SplLogicBhvWoodenFigure.IsAutomationMain`; `IkaFlip`·`SquidSurge`·`IkaNet`·`GyroCamera`·`SpSuperHock`·`Charger` 등은 각자 PaintedArea·표적 묶음. 전체 대응은 덤프 파일에 있습니다.
- `LocatorAreaSwitch_addc.IsInside` → BoolToPulse → `SplLogicLobbyToPlaza`(로비 → 광장 이동, 사격장과 무관).

#### 6.7.3 시퀀스와 도우미 상태 기계 [판독]+[데이터]

대전 로비 시퀀스(Bootup 팩 `UniqueSequenceSPL/SplLobbyVersus.root.ainb`, 덤프 `analysis/r6_range/spllobbyversus_dump.txt`)의 상태 `TipsTrial`(노드 34, 순차 노드):

```
SplUIStartFader(30, 검정 페이드) → 동시{ SplPlayerDemoFadeIn(1), SplTipsTrialSetup, GameSoundStopDucking("CmnSubSeq") }
→ SplUIEndFader(30) → SplTipsTrialProgress → SplUIStartFader(30) → SplTipsTrialRestore → SplUIEndFader(30)
→ GameSeqWaitFrameChangeState(0, "Progress")
```

시퀀스 노드 코드(등록 문자열 `UniqueSequenceSPLSplTipsTrial*`) [판독]:
- Setup 계산 `0x7102e25218`: 시퀀스 값 `TipsTrialPath`(문자열)를 받아 도우미의 `0x7102e1c604`로 넘김 → 도우미 상태 = 1, 경로의 `spl__TipsTrialParam` 리소스를 비동기로 잡고 상태 = 2.
- Restore 계산 `0x7102e2460c`: 도우미 상태 = 8, 진행 객체 vt+0x20(Restore 메시지), `0x7102e1fff8`(복구) 호출.
- 도우미(`TipsTrialHelper`) calc `0x7102e1c72c`(함수 목록에 없던 14 KB, 상태 = 도우미+0x38):

| 상태 | 처리 |
|---|---|
| 2 | 진행 객체(+0x70, vtable `0x7105693148`, +8 = Playground 이름) 생성; 판정 객체(+0x78) = `0x7102e21878(Judge, VariableN)`; `0x7102e20a28(LocatorName)`로 `StartPosTipsTrial` 중 이름이 같은 로케이터의 위치·회전을 찾아 도우미 +0x3c..+0x68에 둠(플레이어 이동); WeaponName·SpecialState 적용; 그리고 **태그 `ActorAttr_NotForTipsTrial` 배치 기록마다 기록+0x3b = 0, 액터에 종료 요청 `0x7100f721b8(액터, 2)`** → 상태 3 |
| 3 | 준비(`0x71030e5ac0`, `0x7102647b34`)되면 진행 객체 vt+0x10 = `0x7102e22b10`: 메시지(vtable `0x7105693188`, 형식 키 `0x71058ebfd8`, +0x18 = **1**, +0x20 = Playground)를 `0x7101323ea8`로 **즉시 방송** → §6.7.2 노드의 Setup 펄스 → 상태 4 |
| 4 → 5 | 한 프레임 대기 |
| 5 | 진행 객체 vt+0x18(`0x7102e22b5c`: 카운터 > 0, 호출마다 +1)이 참이고 준비면 판정 객체 vt+0x10(시작) → 상태 6 |
| 6 | 판정 객체 vt+0x18(성공?)이 한 번 참이 되면 +0x80 래치. 래치 뒤 매 프레임 +0x84 += 1, `JudgeDelay × 60 ≤ (float)+0x84`이면 상태 7(성공) |
| 8 | 진행 객체 vt+0x28(`0x7102e22bbc`)이 참이고 준비면 진행·판정 객체 해제, 상태 0 |

#### 6.7.4 판정 객체와 깨짐 메시지 소비처 [판독]

`0x7102e21878(type, N)`이 판정 객체(0x68 B)를 만들고 메시지 버스 `*0x7105801908`에 수신자를 등록합니다(`0x7100f3de98`).

| Judge | vtable | 수신 형식 키 | 수신 처리 | 시작(vt+0x10) | 성공(vt+0x18) |
|---|---|---|---|---|---|
| 0 BreakOne | `0x7105692f40` | `0x71058a9d10` | `0x7102e21db0`: +8 += 1 | 없음 | `0x7102e21e9c`: +8 > 0 |
| 1 BreakAll | `0x7105692fa8` | `0x71058a9d10` | `0x7102e21f54`: +8 += 1 | `0x7102e2203c`: +0xc = 지금 살아 있는 액터 중 형식 검사(`0x710553e680`)를 통과하고 태그 `ActorAttr_ForTipsTrial`인 것의 수. +8은 건드리지 않음(생성 때 0, 생성 뒤 깨짐부터 셈) | `0x7102e22388`: +8 ≥ +0xc |
| 2 UseSub | `0x7105693010` | `0x71058c0e68` | +8 += 1 | | `0x7102e22524`: +8 ≥ +0xc(= VariableN) |
| 3 UseSp | `0x7105693078` | `0x71058be3a8` | | | 같은 꼴 |
| 4 UseTeamSignal | `0x71056930e0` | `0x71058c1060` | | | 같은 꼴 |

- **깨짐 메시지 소비처 [판독]**: 표적 Burst enter가 큐(`0x710582b7c0`)에 넣는 메시지(vtable `0x7105615390`)의 형식 키 함수(vt+0x20 = `0x71021f2bc0`)는 `&0x71058a9d10`을 돌려줍니다. 이 키로 등록하는 수신자는 위 BreakOne/BreakAll 판정 객체입니다. 즉 **표적이 깨질 때마다 판정 카운터가 1 오릅니다**. 메시지는 표적 종류를 가리지 않지만, 시험 중에는 일반 표적(`NotForTipsTrial`)이 상태 2에서 종료되므로 사실상 팁 시험 표적만 셉니다. 큐 `0x710582b7c0`의 항목(+0xd8 목록)이 버스로 배달되는 함수는 찾지 못했습니다(형식 키 일치까지만 판독).
- BreakAll의 목표 수는 시작 순간 살아 있는 `ForTipsTrial` 액터 수입니다. 태그 표(RSDB `Tag.Product.100.rstbl`, 비트 = 태그번호 + 177 × 행) [데이터]: `ActorAttr_ForTipsTrial` = SighterTarget_TipsTrial, SighterTarget_TipsTrialMove, SpawnerForBeaconGimmick_TipsTrial, SpawnerForShieldGimmick_TipsTrial; `ActorAttr_NotForTipsTrial` = SighterTarget, SighterTarget_Large, SighterTarget_Move. 형식 검사 `0x710553e680`이 어느 클래스를 고르는지(스포너 포함 여부)는 [미확정]입니다.

복구 `0x7102e1fff8`(Restore) [판독]: `0x7102e20a28("Restore")`로 Restore 로케이터를 찾아 위치를 두고, 배치 기록을 모두 돌며 `NotForTipsTrial` → 기록+0x3b = **1**, 액터에 상태 요청 `0x7103c7ea60(액터, 0xef)`이 받아지면 액터+0x5cc = 5; `ForTipsTrial` → 기록+0x3b = **0**, 종료 요청 `0x7100f721b8(액터, 2)`. 진행 객체 vt+0x20(`0x7102e22b74`)은 같은 형식의 메시지를 +0x18 = **0**으로 방송해 Playground 노드의 Restore 펄스를 내지만, AINB에서 Restore는 연결이 없습니다.

#### 6.7.5 `[액터+0x348]+0x3b`의 뜻 [판독] (2026-10-03)

정정(2026-10-03): 이전 판은 "[미확정] — 기본 0xff의 3상태 플래그로 보임"이었습니다.

- 액터+0x348은 **배치(생성) 기록**(0x110 B, 기록 목록 `0x71059a3ea0`에서 0x110 간격)입니다. 근거: 판정 시작 `0x7102e2203c`가 `[액터+0x348]+0x80 → +0x128`(태그 행 번호)을 읽고, 복구 `0x7102e1fff8`이 기록 목록의 각 기록 `+0x80 → +0x128`로 같은 태그를 검사한 뒤 같은 기록의 +0x3b를 씁니다.
- +0x3b = **기록 단위 "자동으로 깨워도 됨" 플래그**: 처음 0xff면 액터 초기화 `0x7101468138`(`0x7101467e68` 안)가 `!(기록+0xa8 bit27)`로 채웁니다. 거리·화면 기준으로 액터를 재우고 깨우는 `0x71027ae0d8`은 상태 3 또는 6인 액터를 깨울 때 **+0x3b가 0이면 깨우지 않습니다**(`0x71027ae454`). 팁 시험 상태 2와 복구가 태그별로 0/1을 씁니다(§6.7.3·§6.7.4).
- `SighterTarget_TipsTrial`의 vt8이 0을 쓰는 것은 "이 표적이 잠들거나 종료돼도 거리 관리자가 다시 깨우지 않게" 하는 것입니다. 상태 번호 3·6의 이름은 [미확정]입니다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

| 항목 | 내용 |
|---|---|
| 모델 | `Obj_SighterTarget`(일반·대형·팁), `Obj_SighterTargetMove`(이동), 파편 `Fragment00/01`(같은 bfres). 뼈: root, leg, burst, body, ear_L0/L1, Z_ear_L, ear_R0/R1, Z_ear_R [데이터] |
| 스켈레탈 애니 | §4.5, 진행 규칙 §5.2.1. BurstWait·Wait의 ""는 직전 애니의 마지막 프레임을 유지합니다(Brust 끝 자세로 숨은 채 BurstWait, Expand·Flick·DamageShot 끝 자세로 Wait) [판독]. `Brust`(1프레임)는 burst·body·ear 뼈 크기가 1e-9(사실상 숨김)인 자세입니다 [데이터] |
| 깨짐 연출 | Burst enter의 xlink 키 `Break`(ELink·SLink 둘 다). ELink `SighterTarget`의 `Break` = Blend 컨테이너 [`SandBagBreak`, `SighterTargetFragment`] 크기 0.8(대형 `SighterTargetBig`은 크기 지정 없음 = 1.0) [데이터]. SLink `Break` = `Obj_SighterTarget_Burst_00`(음량 0.9~1.0, 피치 0.95~1.05, DistCoef 15) [데이터] |
| 가산 애니 | `game::AnimationAddable`(+0x188) = "DamageShotBend"(프레임 = 휨각°, 가중치 = 휨 벡터 길이(1로 자름)) + "DamageShot" [판독] |
| 머티리얼 애니 | `Damage`(100프레임) = `M_Body`의 `two_color_complement_paint_intensity` 커브 1개 [데이터]. 표적 코드에는 이 이름을 쓰는 곳이 없고, 애니 보조의 재질 채널은 상태 애니와 같은 이름만 찾으므로 표적 상태가 직접 틀지 않습니다 [판독]. 같은 파라미터는 DamageHelper 칠 보완 경로가 매 프레임 직접 씁니다(§6.2.1) [판독]. 이 애니를 재생하는 곳은 **[미확정]** |
| 효과음 `ダメージ` 등 | SLink `SighterTarget` 액션 슬롯 `Skl[0]`의 액션 `DamageShot` → `ダメージ`(Random2: `Obj_SighterTarget_Damage_00~03`, 피치 1.0~1.3), `Expand` → `復活する`(`Obj_SighterTarget_Expand_00`), `Flick` → `回復する`(`Obj_SighterTarget_Flick_00`). 트리거 start 0, end 0x7FFFFFFF, flag 0 [데이터]. 방출 코드: 게임 코드가 키를 직접 내지 않고, 모델 애니 → xlink 동기 `0x7101346470`이 스켈레탈 채널 i의 **애니 인덱스가 바뀔 때만** `0x710389b61c`(ELink +0x30·SLink +0x38의 TriggerCtrlMgr, 애니 이름, (int)프레임, 슬롯 i)로 액션을 바꾸고, 같으면 액션 프레임만 고칩니다 [판독] |
| 재피격 소리 | DamageShot 중이나 그 뒤 Wait(애니 유지) 중에 다시 맞으면 채널 애니 인덱스가 그대로라 액션이 바뀌지 않고 액션 프레임만 0으로 돌아갑니다 [판독]. 이때 **`ダメージ`는 다시 나고, 아직 울리던 이전 소리는 끄기 표시(+8 \|= 0x90)를 받습니다** [실행] (§7.1). Flick·Expand 뒤 첫 피격은 액션이 바뀌어 `ダメージ`가 납니다 [판독] |
| 기타 이펙트 | ELink `MarkingEnd/Icon/Point/Line`(포인트 센서), `Deviling`(독), `TorpedoTarget`, `TargetMarker`, 팁 시험 표적은 상시 `試してみよう的アイコン`(`IconSighterTarget`, MiniMap3D) [데이터]. 피격 이펙트·소리 공용분은 HitEffect(damage_hit §6.6) |
| UI | `Shr_Points_00`(§6.4) |
| 카메라 | 데미지 숫자 거리 기준 = 카메라 모듈 위치 |

### 7.1 재피격 때 `ダメージ` 재방출 [실행]+[판독] (2026-10-03, 6차)

정정(2026-10-03): 이전 판은 "재방출 여부 [미확정] (effect_sound 영역에 넘김)"이었습니다.

xlink2 액션 트리거 매 프레임 calc `0x7103895f64`(기준: 트리거 제어 ctrl, +0x24 = 이번 액션 프레임, +0x28 = 직전 프레임, +0x30 = 액션, +0x10 = 트리거 상태 표 0x28 B 간격)를 판독하고 원본 실행으로 확인했습니다.

```
regress = cur < prev;  if regress: prev = −1
for 트리거 i (액션의 시작~끝 인덱스):
    종류 = flag bit2 ? 1 : bit3 ? 2 : bit4 ? 3 : 0
    loop = 리소스 접근자 vt+0x10 결과 +0x10이 있으면 그 사용자 리소스 +0x80 표[에셋 번호] 바이트+2 bit1, 없으면 0
    if 종류 != 0 && !loop: 건너뜀            // 시작·종료·직전 액션형은 매 프레임 calc에서 loop일 때만
    start = (종류 == 3) ? 0 : 트리거+0x10   (종류 3은 상태+0x26 == 0이면 건너뜀)
    if regress && !(flag bit0) && 상태+0x24(발생함): 살아 있는 핸들이면 이벤트+8 |= 0x90, 핸들 비움
    if !loop:  if prev < start <= cur < end(+0x18) && !(bit0 && 발생함): 방출 0x7103899c68, 발생함 = 1
    else:      if start <= cur < end && 핸들 없음/만료 && !(bit0 && 발생함): 방출, 발생함 = 1
    if prev < end <= cur: 살아 있는 핸들이면 이벤트+8 |= 0x90, 핸들 비움
ctrl+0x28 = cur
```

`ダメージ` 트리거(시작 0, 끝 0x7FFFFFFF, flag 0)는 종류 0이라 loop 비트와 관계없이 처리됩니다. 재피격 때 액션 프레임이 k(≥1) → 0으로 가면 regress → prev = −1 → `−1 < 0 ≤ 0 < 끝`이 성립해 **다시 방출**합니다. 이전 이벤트가 살아 있으면 먼저 0x90 표시로 끕니다. loop 비트가 1이어도 끈 직후 핸들이 비어 다시 방출하므로 결과가 같습니다 [실행].

- 예외: xlink가 본 직전 프레임이 이미 0이면(직전 피격 뒤 프레임이 아직 오르지 않음, §5.2.1 첫 갱신 규칙) 역행이 아니라 다시 나지 않습니다 [실행: 0 → 0 시나리오].
- 주의: 에셋 loop 비트가 1이면 역행이 없어도 이벤트가 끝난 뒤 `start ≤ cur < 끝` 동안 계속 다시 방출합니다(끝 0x7FFFFFFF이므로 액션이 유지되는 내내). `ダメージ`(Random2 4종)의 이 비트 값은 런타임 표(사용자 리소스 +0x80)를 만드는 곳을 찾지 못해 [미확정]입니다.
- 원본 실행: `web/tools/r6_range_xlink_emu.py` — 재피격(prev 5/10/30/31 × loop 0/1 × 이전 이벤트 살아 있음/없음 16건), 첫 재생, 0 → 0, 정상 진행, 이벤트 끝난 뒤, bit0 넘겨받기형, 접근자 없음, 구간 트리거 2건, 모두 28건이 위 재구현과 방출 호출 인자·끄기 표시·핸들·발생함·직전 프레임까지 일치(28/28). 스텁: 방출 `0x7103899c68`(ret, 인자 기록), 리소스 접근자 vt+0x10(합성 객체), 이벤트 끄기의 전역 객체 호출(핸들 +0x28 = 0으로 미실행). 입력 구조체는 함수가 읽는 오프셋만 합성했습니다. 실제 액션 프레임이 calc에 들어오는 순서(애니 → `0x7101346470` → calc)는 [판독]이며 연결 실행은 하지 않았습니다.

## 8. 다른 기능과의 상호작용

| 상대 | 내용 |
|---|---|
| 탄·데미지 | 리시버 열 `Default`. 팀 = 로컬 플레이어 반대 팀 → 자기 잉크로 맞힘. 같은 팀이면 Through |
| HP 홀더 | DamageHelper 공용 홀더(player_life §6.1). 홀더 갱신(단계 4)은 vt18·vt19 뒤라 깨짐 검사는 다음 프레임 vt18(§3.2.1) |
| 충돌 | ColBullet만 탄과 충돌, Main은 플레이어를 막음. Burst~BurstWait 동안 둘 다 꺼짐. Expand 동안 캡슐이 자람(§4.3) |
| 레일 | 이동 발판과 같은 RailMovableSequential, Main 몸은 속도로 이동(§6.5) |
| 입력 | 사격 구역 밖이면 로비에서 입력 종류 1~3 차단(§6.6) |
| 팁 시험 | `IsTipsTrial` 표적은 깨진 채 남고, 깨짐 메시지(형식 키 `0x71058a9d10`)를 팁 시험 판정 객체 BreakOne/BreakAll이 받아 카운터를 올립니다 [판독] (§6.7.4). 진행은 시퀀스 `SplTipsTrialSetup/Progress/Restore` → 도우미 `0x7102e1c72c` → Playground 메시지 → 로직 AINB `Lby_Lobby00_5bad`의 Setup 펄스(§6.7) |
| 조준 보조·센서 | ShotTarget 로케이터(0,1,0), SensorMarkable(+0x198 +0x30 = 상태 > 1), 폭탄 로봇·멀티미사일 대상 플래그 |

## 9. 웹 포팅 구조와 구현 순서

### 9.1 모듈 (웹 권장 이름 — 원본 이름 아님)

| 모듈 | 책임 | 원본 대응 |
|---|---|---|
| `core/range/target.ts` `SighterTarget` | 상태 기계·HP 홀더·리시버 일부·휨·표시값·애니 보조 진행 | vt15/18/19/22, 상태 함수, 0x7101a86ec0 일부, 0x71012664cc |
| `core/range/rail.ts` `RailPath`/`RailMover` | 레일 일정·평가 | 0x7101305238, 0x71013043d8, 0x7101304cec, 어댑터 |
| `core/range/area.ts` | 사격 구역 판정·입력 허용 래치 | 0x71012496e8, 0x7102484ff8~, 0x710246b8c8 |
| `core/range/index.ts` | 배치 → 생성, Hittable·충돌 등록, 공유 상태 | |
| `client/range/index.ts` | 모델·데미지 숫자 | Shr_Points_00, 0x710338d2d0 |
| `core/range/tipsTrial.ts`(웹 권장 이름, 미구현) | 팁 시험: TipsTrialParam 로드 → 시작 위치·무기 → 일반 표적 끄기 → Playground Setup(AINB 표로 켤 액터 목록) → 판정 카운터 → JudgeDelay → Restore | §6.7 |
| 표적 재질 보완 칠 | 마지막 공격 팀 채널 세기 = 1 − hp/max(Mag 1·Bias 0.5) | §6.2.1 |

### 9.2 상태 객체 대응

| 원본 | 웹 |
|---|---|
| +0x130 / +0x134 | `state` / `counter` |
| +0x120 | `accum` |
| H+0x48 / +0x4c / +0x50 | `holder.max` / `hp` / `pending` |
| R+0x1bc / +0x1cc / +0x1c4 / +0x1c8 | `recv.team` / `extraOn` / `extraRate` / `extraResult` |
| BendCalculator +0x60/+0x6c/+0x78 | `bendImp` / `bendPos` / `bendVel` |
| 애니 보조 슬롯 +4/+8, +0x18 | `animFrame` / `animRate` / `animTick` |

### 9.3 순서·정밀도

1. 표적 한 프레임: vt18(Burst 검사 → exec → 애니 보조 갱신 → 휨 → 레일) → vt19 표시값 → HP 홀더 갱신(대기 데미지 반영). 피격은 탄 처리 중 즉시(리스너가 바로 DamageShot 전이).
2. 애니 보조: 재생 시 frame 0·tick 0, 갱신은 tick > 0일 때만 frame += 1(§5.2.1).
3. f32 연산, 배율 `+1e-5`, `fcvtzs`(0 방향 절삭), 99998 상한, BurstWait의 `(int)` 절삭과 `(uint)` 변환은 그대로.
4. 같은 상태 전이도 enter 재실행(애니 재시작).
5. 휨 각은 atan2Idx 표 방식, 휨 충격 scale 인자는 1.0 고정.
6. 데미지 숫자: v = f32(누계)/10, 정수부 floor, 소수 floor((v − i)×10).

## 10. 검증 코드·실행 결과·기대값

| 검사 | 종류 | 결과 |
|---|---|---|
| `web/tools/r5_range_emu.py` A 휨 | [실행] 원본 `0x7101e3422c`·`0x7101e33ed8`·`0x7101e34468`(+`0x7101252998`) 연결 실행 vs 독립 재구현 | 400시행, 충격 9,440회, 갱신·각 8,030스텝, atan2Idx 3,015건 전부 비트 일치. 스텁: PLT sqrtf·logf·expf(ucrtbase)·guard |
| 같은 도구 B 캡슐 | [실행] 원본 `0x71021f0dcc` | 1,210쓰기 비트 일치. 실제 값: t=1 → Main A (0, 1.26, 0), t=0 → (0, 0.39, 0). 스텁: dynamic cast(1), 형상 +0x14 bit5 = 1로 dirty 큐 경로 미실행 |
| 같은 도구 C 애니 | [실행] 원본 재생 `0x710125f27c`(→`0x7101266974`, `0x710125fa40`) → 갱신 `0x71012664cc` → 끝 `0x710126006c` 연속 | 4애니 × rate 2가지 전부 일치(§5.2.1). 스텁: 이름 검색 `0x71036c29ec`(고정 인덱스), 모델 바인드 `0x71036731d0`(채널 id 기록), 프레임 평가 콜백(ret), cosf. 재질 채널은 모델 없음으로 생략 |
| 같은 도구 D 영역 | [실행] 원본 `0x71012496e8` 7모양 | 10,500건 비트 일치(회전 포함, 경계 근처 포함) |
| 같은 도구 E 숫자 | [실행] 원본 `0x710338d2d0` | 4,872건 인자 (i, d)·이전 값 갱신 일치, 같은 값이면 다시 쓰지 않음 1건. 스텁: 레이아웃 기반 calc `0x71032031d0`(ret), 텍스트 설정 `0x71013621d0`(인자 캡처), 슬롯 age 0 |
| `web/tools/r6_range_xlink_emu.py` | [실행] 원본 xlink 트리거 calc `0x7103895f64` vs 재구현(§7.1) | 28/28 일치(재피격 16건 포함). 스텁: 방출 `0x7103899c68`, 리소스 접근자 vt+0x10, 이벤트 끄기 전역 호출 경로 미실행. 결과 `analysis/r6_range/xlink_regress_emu.json` |
| `web/tools/r6_range_ainb.py` | [데이터] AINB 0x404 해독(로직·시퀀스) | 로직 147노드: JudgeTipsPlayground 25개의 Name 집합 = TipsTrialParam 53개의 Playground 집합(25종) 정확히 일치. 입력 연결이 가리키는 출력은 Setup·PulseOr.Output·Bool·Pulse·IsInside뿐(Restore·Logic_Sleep 미연결) |
| `tests/range_target.test.mjs` | [재구현] 합성 시나리오 | 피격 360 → DamageShot, 31스텝째 Wait, HP 640, 표시 36.0; 3발 → Burst → BurstWait 122스텝 → Expand 45스텝 → Wait; 무피격 → 153스텝째 Flick 등. §5.3에 따라 원본과 1스텝씩 다른 값이 있음(웹 반영 필요) |
| `tests/range_rail.test.mjs` | [재구현] 로비 레일 실제 값 | 구간 15/7초, 주기 2배, sin 중간점 10.5, 역방향 cSpeed, Ry(−90°) 축, cStop·WaitTime·BreakTime |
| `tests/range_area.test.mjs` | [재구현] 배치 실제 값 | Cube 경계(≤), 회전 Cube, Cylinder 바닥·높이·반지름(엄격 <), 래치(공중 4프레임) |
| `client/range/dev/shot.mjs` | 헤드리스 화면(웹) | 17개 표적 표시, 피격 시 "36.0", 깨짐 시 "108.0"(노란색, isMax), BurstWait 숨김, Expand 크기 복귀 — `test/out/range_*.png` |

검증하지 않은 범위: 상태 함수·vt18·vt22 전체(액터·컴포넌트 객체 그래프), 접촉 시퀀서 위치, 액터가 Main 몸을 따라가는 경로, xlink 액션 프레임 공급(애니 → `0x7101346470` → calc) 연결 실행, 팁 시험 도우미 상태 기계·판정 객체(판독만), 칠 보완 계산(판독만), 레이아웃 텍스트 렌더(태그 해석). 함수 단위 실행 일치를 전체 동작 검증으로 넓히지 않습니다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 상태 | 다음 단서 |
|---|---|---|
| ~~DamageHelper 홀더 갱신과 표적 vt18의 순서~~ | **해소 [판독]** §3.2.1: 홀더 갱신은 단계 4(vt18·vt19 뒤) | — |
| 탄 접촉 시퀀서의 프레임 안 위치(마지막 명중 → Burst 1프레임/2프레임) | [미확정] | 물리 영역 §6.7: Post3 큐 소비 위치, `0x71012e55cc` |
| ~~애니 프레임 진행 속도·첫 프레임~~ | **해소 [실행]** §5.2.1 | — |
| 상태 기계 dt(`0x7103d987c0(*0x71059a7430)`)가 60fps에서 1.0인지 | [추정] | `0x7103d987c0` 반환 값 writer |
| ~~몸 값 +0xdc 보간(`0x71021f0dcc`)의 의미~~ | **해소 [실행]** §4.3: 캡슐 A 정점, t는 [0,1] 클램프 | — |
| ~~접촉 속도 단위(vt+0x18)~~ | **해소 [판독]** §6.3: 유닛/초(탄 바디 +0xdc, 강체 +0x138), 탄 바디 +0x148 공급자는 생성 때 0 | 클래스 밖 +0x148 쓰기(`0x7103ada484` 등)의 대상 클래스 |
| ~~접촉 태그 6종의 정확한 이름~~ | **해소 [판독]** §4.5 | — |
| 이동 표적 액터 행렬 | [판독-부분] Main 몸 속도 경로(§6.5), RigidBodyController 파라미터 오프셋·실행 칸(+0x10 WarpMode, 바이트0 bit1 IsTrackingActor) [판독]. 액터가 몸을 따라가는 경로 [미확정] | 칸(`0x7103ae9f2c`가 만드는 0x18 B 배열)의 +0x10·bit1 reader, 물리 `[r6 physics]` 슬롯19 write-back 추적 |
| ~~사격 구역 래치의 효과~~ | **해소 [판독]** §6.6: 로비 플래그 && +0x938d == 0 → 입력 종류 1~3 차단. 버튼 이름은 player 영역 [추정] | 전역 `0x71058e87ac` 이름(writer) |
| ~~로케이터 회전 저장 순서~~ | **해소 [실행]+[판독]** §6.6: R = Rz·Ry·Rx 행 우선([r6 assets] 원본 실행) + 열 내적 판정 → l = Rᵀ(p − T) | — |
| ~~영역 모양 번호 = 문자열 순번+1~~ | **해소 [판독]** §4.5 | — |
| ~~`[액터+0x348]+0x3b`(팁 시험 표적이 0으로 씀)~~ | **해소 [판독]** §6.7.5: 액터+0x348 = 배치 기록, +0x3b = 자동 깨우기 허용(0이면 `0x71027ae0d8`이 깨우지 않음), 팁 시험 Setup/Restore가 태그별로 씀 | 액터 상태 번호 3·6의 이름 |
| ~~데미지 숫자 소수 자릿수·isMax 모양~~ | **해소 [실행]+[데이터]** §6.4 | 태그 인자 바이트 뜻은 UI 영역 [추정] |
| 데미지 숫자 슬롯 age를 0으로 돌리는 곳 | [미확정] | 레이아웃 vt+0x438(표시 위치 설정) |
| ~~LossOfColor(잉크 색 빠짐)의 경로~~ | **해소 [판독]+[데이터]** §6.2.1: DamageHelper 칠 보완 = Mag·bias(1 − hp/max, Bias/Mag) → 재질 `thr_comp_paint_intens_*`·`two_color_complement_paint_intensity` | 셰이더 식은 그래픽 영역. `M_Body`의 `comp_paint_type` 옵션 값(셰이더 아카이브 기본값) |
| 머티리얼 애니 `Damage`를 재생하는 곳 | [미확정] — 같은 파라미터를 칠 보완 경로가 직접 씀 [판독]. 표적·DamageHelper 범위에 `Damage` 문자열 참조 없음 | `Damage` 문자열 참조 42곳 중 재질 애니 재생(모델 애니 보조 재질 채널) 호출자 |
| ~~재피격 때 `ダメージ` 재방출 여부~~ | **해소 [실행]** §7.1: 액션 프레임 역행이면 이전 이벤트를 끄고 다시 방출. 직전 프레임이 0이면 안 남 | `ダメージ` 에셋의 loop 비트(사용자 리소스 +0x80 표 작성자) — effect_sound 영역 |
| 플레이어 접촉 충격(접촉점+0x60) | [판독-부분] 탄 바디 접촉에서는 쓸어 넘기기 비율 f. 쓸어 넘기기는 탄 바디 전용(BL 호출자 1곳) | 캐릭터 강체 ↔ 키네마틱 강체 접촉점 작성자(물리 영역에 넘김) |
| 수신 이력 모드(탄 송신자)·ObjectEffect_Up | [미확정] (combat 영역 `[r6 combat]` 선점, 결과 대기) | 송신자 생성 `0x7101e3d69c` |
| 팁 시험 진행 | **[판독]+[데이터]** §6.7: 시퀀스 → 도우미 → Playground 메시지 → 로직 AINB Setup 펄스, 판정 객체 5종, 태그별 Setup/Restore | 깨짐 메시지 큐 `0x710582b7c0` → 버스 배달 함수, 판정 형식 검사 `0x710553e680`의 클래스, 성공(상태 7) 뒤 연출 |
| 로직 액터(`SplLogicActor`)의 `Logic_Activate`가 하는 일, 장면 시작 때 팁 시험 표적·PaintedArea가 꺼져 있는지 | [미확정] | 노드 vtable `0x710553cd00` 기반 `0x7103cb83d4`(묶기)·`0x7103cb7bf8`, 펄스 처리 calc |
| WoodenFigure 공격 상세(`IsAutomationMain` 효과)·PaintedArea 칠 요청 형식·스포너 `Spawn` | [미확정] | `wooden_figure.c`, `0x7101f07b5c` → `0x7102bc46f8`(PaintedArea 칠 형식은 `[r6 paint]` 선점) |
