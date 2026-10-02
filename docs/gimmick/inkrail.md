# 잉크레일 (InkRailOnline / spl::InkRail / spl::PlayerInkRail)

대전 스테이지에서 쓰이는 v0 유일의 "탈 것" 기믹입니다. 노즐에 잉크를 맞히면 맞힌 팀의 레일이 펼쳐지고, 같은 팀 플레이어가 레일에 닿으면 레일을 따라 미끄러져 이동합니다. 목차는 [stage_gimmicks.md](stage_gimmicks.md).

표기: **[판독]** 원본 명령/디컴파일 판독, **[데이터]** 데이터 확인, **[추정]**, **[미확정]**, **[재구현]** 파이썬 재구현 계산. 원본 실행 확인(**[실행]**)은 이 문서에 없습니다.
주소는 main NSO 0x7100000000 기준. 디컴파일 원문 `analysis/decomp/gimmick/inkrail_sponge.c`, `gimmick_b2.c`, 주석·체인 접기본 `analysis/gimmick/annot/*.c`.

---

## 1. 사용자에게 보이는 동작

1. 대기(Wait): 레일 노즐만 보입니다. 아무 팀이든 노즐(또는 레일 판정)에 잉크를 맞히면 **처음 맞힌 팀**이 소유 팀 후보가 됩니다.
2. 누적 피해가 `WaitLife`(100 = 10.0 HP 상당) 이상이면 연결(Connect) 상태로 바뀌고, 레일이 노즐에서 **매 프레임 1.0씩** 끝점까지 자랍니다.
3. 연결 상태는 기본 **15초**(`ConnectionSec`) 유지됩니다. 같은 팀 잉크를 맞히면 수명이 늘고, 적 팀 잉크를 맞히면 줄어듭니다(`IsProlongByFriend`, `IsUnemitByEnemy`).
4. 수명이 0이 되면 해제 요청(RequestUnemit) 상태가 되고 0.5초(`RequestUnemitSec`) 뒤 대기로 돌아갑니다.
5. 같은 팀 플레이어가 레일에 닿으면 탑승합니다. 스틱을 레일 방향으로 기울이면 가속하고(최대 0.192/프레임), 점프하거나 레일이 끊기면 이탈합니다. 레일 끝에서는 자동으로 떨어지지 않고 끝점에 머뭅니다(§7.2b, 2026-10-02 3차 정정). 적 팀은 레일에 닿으면 밀려나고, 위에서 노즐에 떨어진 플레이어도 옆으로 밀려납니다.

## 2. 자료 위치

| 항목 | 위치 | 비고 |
|---|---|---|
| 배치 | `extracted/params/Banc/Vss_*.bcett.byml.json` 의 `InkRailOnline` 액터 + `Rails[]` 의 `LiftRail` | `spl__InkRailBancParam.LinkToPoint` = 레일 첫 점 Hash [데이터] |
| 액터 팩 | `romfs/Pack/Actor/InkRailOnline.pack.zs` (해제본 `analysis/gimmick/pack/InkRailOnline/`) | 부모 `InkRail` → `ObjParent` |
| 동작 클래스 | Behavior `ClassName "spl::InkRail"` | vtable `0x710560f318`(46슬롯), getName `0x7102178c30`, 크기 `0x25f8` [판독] |
| 액터 파라미터 | `InkRail.game__GameParameterTable` + `InkRailOnline`(자식) | `spl__InkRailParam`, `spl__RailColliderParam`, `spl__ActionGuideArea`, `spl__MultiModelHelperParam` |
| 플레이어 파라미터 | `Params.pack` `SplPlayer.game__GameParameterTable` 의 `spl__InkRailPlayerParam` | 리플렉션 `analysis/param_reflect/spl__InkRailPlayerParam.json` |
| 피해 배율 | Bootup 팩 `spl__DamageRateInfoConfig` 열 `InkRail` | `analysis/combat/DamageRateInfoConfig.json`([combat] 추출) |
| 네트워크 | `InkRailOnline.game__NetParam`: ActorType MapObject, 상태 `spl::InkRailNetState`, SenderPolicy `SessionMasterOrEvent` | RSDB `MapObjReplicaInfo`에 `InkRailOnline` 행 [데이터] |
| 모델 | `Work/Model/Object/Obj_InkRail_VS/output/Obj_InkRail_VS.fmdb`, 소형 모델 `Obj_InkRailSmall_VS`, `Obj_InkRailSmallBase`, 노즐 `Obj_nozzle_VS`, `Obj_nozzleSmall_VS`, `Obj_InkRailBase_VS` | `spl__MultiModelHelperParam`, `spl__InkRailParam.FmdbPathsSmallModel` [데이터] |
| 관련 클래스 | `spl::InkRailData`(vt `0x710560f6e8`), `spl::InkRailDrawer`(vt `0x710560f818`), `spl::InkRailNetHelper`(vt `0x710560f948`), `spl::PlayerInkRail`(vt `0x710563c988`) | `web/tools/class_info.py` [판독] |

## 3. 진입점과 호출 흐름

```
씬 로드 → Banc Actors: InkRailOnline 생성 (Layer = Cmn 또는 선택 모드)
  spl::InkRail vt8  0x7102178c44  초기화: 상태머신(this+0x2540)에 4개 상태 등록
        Wait          enter 0x7102179524  exec 0x7102179984(빈 함수)
        Connect       enter 0x7102179988  exec 0x710217a25c  exit 0x710217a2f4
        RequestUnemit enter 0x710217a318  exec 0x710217a4a0(=0x710217d810 썽크)
        Invisible     enter 0x710217a4a4  exec 0x710217a4e0  exit 0x710217a4e4
      ├ 피해 수신 콜백 등록(DamageParam "InkRail" 열)
      └ InkRailData 0x710217f758: LinkToPoint로 레일 점 목록·구간 길이 구성
  vt9   0x710217a518  보조 객체(+0x1c0/+0x1040/+0x1a0) 초기화, 피격 콜백 0x710217a668 연결
  vt15  0x710217a8a8  시작: 리셋(0x710217acb8) 후 IsOpen이면 Connect+완전연장, 아니면 Wait(씬 분류 "Scene_Coop" 비트가 켜져 있으면 Invisible, §5.2)
  매 프레임 vt18 0x710217b514  상태 전이·수명 시간 감소
           vt19 0x710217bce8  게이지(미터) 애니
           현재 상태 exec (Connect/RequestUnemit: 0x710217d810 레일 연장·표시)
  접촉     vt22 0x710217c148  플레이어 접촉 → 밀어냄/넉백/탑승 시작(0x710217ca44)
  피격     0x710217a668 수명 가감, 0x710217ea4c 피격 연출·팀 결정
  네트워크 0x71021899dc (InkRailNetHelper) 원격 상태 반영, 0x710217dba8 이벤트(6: Wait, 8: Invisible)
```

vtable 슬롯 의미(8 초기화, 15 시작, 18 프레임 갱신, 22 접촉)는 이 클래스 내부 동작으로 붙인 이름이고, 슬롯 번호의 엔진 공통 의미는 **[추정]**입니다(spl::Lift, spl::Geyser, spl::Sponge도 같은 46슬롯 계열이며 18·19·22번을 덮어씀).

## 4. 데이터

### 4.1 배치 (Yagara) [데이터]

`InkRailOnline` 액터의 `Translate`는 에디터 배치 위치일 뿐, 실제 노즐 위치는 레일 첫 점으로 덮어씁니다(§6.1). 레일은 `Rails[]`의 `LiftRail`(`game__GraphRailWithParentParam`, 점마다 `game__LiftGraphRailNodeParam {}`)이고 점 좌표는 월드 좌표입니다(알파/브라보 쌍이 원점 대칭인 것으로 확인).

| 레이어 | 팀 쪽 | 점(UseBase 적용 후, 첫 점 Y+0.5) | 구간 길이 | 전체 | 연장 프레임 |
|---|---|---|---|---|---|
| Pnt, Var | Alpha 쪽 | (-2.75,12.5,50.25) (0,15.5,43.25) (4.25,16.75,37.75) | 8.0971, 7.0622 | 15.1593 | 16 |
| Pnt, Var | Bravo 쪽 | 원점 대칭 | 동일 | 15.1593 | 16 |
| Vgl | 양쪽 | (-2.75,12.5,50.25) (-0.25,14.25,46) (3.75,14.75,43.75) | 5.2321, 4.6165 | 9.8487 | 10 |
| Vcl | 양쪽 | (5.25,8.75,44.25) (7.75,12.25,36) | 9.3039 | 9.3039 | 10 |
| Vlf, Tcl | — | 없음 | | | |

다른 스테이지: Temple00 Vgl 2개(12.545), Upland03 Vgl·Vlf·Vcl 각 2개(10.008/9.606/8.666), Carousel Cmn 2개(`GeneralRail` 4점, 10.931). 전체는 `analysis/gimmick/<스테이지>_summary.json` [재구현].

### 4.2 spl__InkRailBancParam [판독]

방문 함수 `0x71020703f0`, 생성자 `0x7102070334`, vtable `0x7105604868`.

| 오프셋 | 필드 | 타입 | 기본값 | 설정 플래그 | 소비 |
|---|---|---|---|---|---|
| +0x30 | LinkToPoint | 레일 점 참조(u64 Hash) | — | 0x3a | `0x710217f758` 레일 찾기 |
| +0x38 | IsOpen | bool | false | 0x3c | `0x710217a8a8` 시작 시 바로 Connect |
| +0x39 | UseBase | bool | true | 0x3b | `0x710217f758` 첫 점 Y+0.5, 첫 점 플래그 |

### 4.3 spl__InkRailParam [판독 기본값 + 데이터]

리플렉션 `analysis/gimmick/param_reflect/spl__InkRailParam.json` (방문 `0x7102073c54`, 생성자 `0x7102073944`). 기준 객체 = 파라미터 객체(액터 this+0x2588이 가리킴). 값 조회는 [bullet] 확인 규칙대로 "설정 플래그가 켜진 가장 가까운 `$parent`"의 값입니다.

| 오프셋 | 필드 | 기본값 | InkRail 데이터 | InkRailOnline 데이터 | 소비(reader) |
|---|---|---|---|---|---|
| +0x5c | ConnectionSec | 15.0 | | | `0x710217b514`, `0x710217d54c` |
| +0x60 | CureRate | 1.0 | | | reader 없음 → v0 미사용 **[추정]** (§12 근거) |
| +0x78 | EmitLife | 4000 | | | Connect enter `0x7102179988` |
| +0xf4 | WaitLife | 100 | | | Wait enter `0x7102179524` |
| +0xc4 | RequestUnemitSec | 0.5 | | | `0x710217a318`, `0x710217d54c`, `0x71021899dc` |
| +0xb4 | OppositeKnockback | 1.0 | | | `0x710217c148` |
| +0xb8 | PlayerDropImpact | 10.0 | **1.0** | | `0x710217c148` |
| +0xbc | PlayerDropImpactEnableVelY | 0.1 | | | `0x710217c148` |
| +0xc0 | PlayerDropImpactEnableY | 0.2 | **0.48** | | `0x710217c148` |
| +0x7c | HitSoundLimit | 4 | | | `0x710217ea4c` |
| +0xf8 | IsAllowNeutral | false | | **true** | 초기화 `0x7102178c44` |
| +0xf9 | IsProlongByFriend | false | | **true** | `0x710217a668`, Connect enter |
| +0xfa | IsUnemitByEnemy | false | | **true** | Connect enter, `0x710217acb8` |
| +0xfb | IsUnemitByTime | false | | **true** | `0x710217b514` |
| +0x9c/+0xa0/+0xa4/+0xa8/+0xac/+0xb0 | OffsetEffectBirth/LEnd/LStart/SplashBirth/SplashBirthInhale/SplashBirthLStart | 0.5/0.7/0.45/0.5/-0.47/0.7 | LStart 0.8, LEnd 0.3 | | 이펙트 위치 `0x710217d1f0`, `0x7102187468`~`0x7102187b44` |
| +0x84/+0x88 | MeterAnimLength / MeterAnimToBlinkFrame | 100 / 80 | | | 게이지 `0x710217bce8`, `0x7102185e78` |
| +0x80 | MaxScale | 2.0 | | | 표시 스케일 `0x71021884e8` |
| 그 외 | Nozzle*/SmallModel*/StartPoint*/Scale*/Dynamics* | 표 JSON 참고 | | | 표시 전용(드로어 `0x7102182954` 등) |

`spl__RailColliderParam`(방문 `0x7102c69108`): `RailSphereRadius` 커브 Linear [0.3,0.3,0.3] MaxX 5.0 → 레일 판정 구 반지름 0.3 고정, `QueryLayerHitMaskEntity "SplKeepOutPlayer"` [데이터]. 커브 평가와 구 배치 간격은 **[미확정]**.

### 4.4 spl::InkRail 객체 필드 (기준 = spl::InkRail this) [판독]

| 오프셋 | 의미 | writer | reader |
|---|---|---|---|
| +0x10 | 액터 본체(위치 +0x28c..+0x294, 회전 +0x298..; 팀 +0x668) | 엔진 | 전반 |
| +0x160..+0x18c | 노즐 행렬 사본(위치 xyz + 회전) | `0x710217acb8` | 행렬 기록 |
| +0x24f0 | 시작부터 연결 여부(IsOpen 등) | `0x710217a8a8` | Connect enter |
| +0x24f8 | 수명(현재, int) | Wait/Connect enter, `0x710217b514`, `0x710217a668`, 넷 | `0x710217b514` |
| +0x24fc | 수명 최대(int) | Wait/Connect enter | `0x710217a668` 클램프, 감소량 |
| +0x2500 | 완전 연장 플래그 | `0x710217d810`, `0x710217a8a8` | `0x710217d810` |
| +0x2504 | 현재 연장 길이(f32) | `0x710217d810` | 드로어, 탑승 끝 판정 |
| +0x2508 / +0x250c | 연장 끝이 있는 구간 번호 / 구간 내 비율 | `0x710217d810` | 드로어 |
| +0x2510/+0x2518 | "Rail" 이펙트 핸들 | Connect enter | `0x710217b514`, `0x710217da1c` |
| +0x2520 | 피격음 쿨다운(HitSoundLimit) | `0x710217ea4c` | `0x710217ea4c` |
| +0x2524/+0x2525 | 외부 연결 요청 플래그 | `0x710217dfec` | Wait 갱신 |
| +0x2528 | 시간 감소 누적(f32) | `0x710217b514` | 같음 |
| +0x252c | 해제 마감 프레임(u32) | `0x710217a318`, `0x710217d54c`, 넷 | RequestUnemit 갱신 |
| +0x2530 | 레일 팀(0 Alpha, 1 Bravo, 3/-1 중립) | Wait enter(액터 팀), `0x710217ea4c`(첫 피격 팀), `0x710217b418` | 피격·접촉 |
| +0x2540 | 상태머신(+0x38 현재 상태 id, +0x40 직전 id) | | |
| +0x2548 | InkRailData(점 배열 +0x58 개수 +0x50, 구간 배열 +0x68 개수 +0x60, 구간 길이 = 구간 객체 +0x10) | `0x710217f758` | |
| +0x2550 | InkRailDrawer | | |
| +0x2558 | InkRailNetHelper(vt+0x10 = 권한(마스터) 여부) | | |
| +0x2580 / +0x2588 | InkRailBancParam / InkRailParam | | |
| +0x2310/+0x2318 | 탑승자 목록(중복 탑승 방지) | `0x710217ca44` | `0x710217c900` |

팀 값은 액터 `+0x668`와 같은 체계입니다(0, 1, 3=중립, -1=없음). Alpha=0, Bravo=1 대응은 Wait enter의 `team==0 → 1, ==1 → 0, 그 외 3` 반전 기록(콜라이더 +0x1bc)으로 본 **[추정]**입니다.

## 5. 상태 전이와 수명

시간 단위는 60fps 프레임. "현재 프레임" = `[[0x7105790610]+0x148]`(u32, 음수면 0으로 클램프)이고, 마감 비교에 씁니다 [판독].

```
           피격(아무 팀) life -= dmg ; 처음 맞힌 팀 → team
 ┌────────── Wait ──────────┐
 │ enter: life = max = WaitLife(100), team = 액터 팀(중립)
 │ 갱신: (life<=0 && 권한) 또는 외부요청 → Connect
 └──────────┬───────────────┘
            ▼
 ┌────────── Connect ───────┐  enter: life = max = EmitLife(4000), 연장 0부터
 │ exec: 연장 += 1.0/프레임 (끝 도달 시 완전연장)
 │ 갱신(IsUnemitByTime): acc += max / int(ConnectionSec*60);
 │        acc>=1 → life -= floor(acc), acc -= floor(acc), life>=0
 │ 피격: 같은팀&IsProlongByFriend → life += dmg, 아니면 life -= dmg, [0,max]
 │ life<=0 → RequestUnemit
 └──────────┬───────────────┘
            ▼
 ┌──── RequestUnemit ───────┐  enter(권한): deadline = now + int(RequestUnemitSec*60)
 │ exec: Connect와 같은 연장·표시 함수(0x710217d810)
 │ 갱신: deadline!=0 && now >= deadline → 정리(0x710217da1c) → Wait
 └──────────────────────────┘
 Invisible: 넷 이벤트 8 또는 시작 시 "Scene_Coop" 씬 비트 → 숨김 (§5.2)
```

판독 근거:
- Wait→Connect, Connect 감소, RequestUnemit→Wait: `0x710217b514`. 감소식은 `acc = acc + (float)max / (float)(int)(ConnectionSec*60.0)`, `acc>=1`이면 `k = floor(acc)`(음수 보정 포함), `life = max(life-k, 0)`, `acc -= k` [판독].
- 피격 가감: `0x710217a668`. 인자 `{amount(int), attackerTeam}`. 권한이 없는 쪽(비마스터)은 직접 바꾸지 않고 NetHelper vt+0x30으로 넘김 [판독].
- 팀 결정: `0x710217ea4c`에서 현재 팀이 3 또는 -1이면 공격 팀으로 설정 [판독]. 피해 0은 무시(`*param_2 != 0`).
- 마감 갱신: Connect enter와 Connect exec에서 권한이 있으면 `0x710217d54c`가 `deadline = int(RequestUnemitSec*60 + (now + int(life/max * int(ConnectionSec*60))))`로 계속 덮어씀 → 남은 연결 시간 + 0.5초. 원격 동기화용 값 [판독], 용도 해석은 [추정].

### 5.1 원격(비마스터) 반영 [판독, 범위 제한]

`0x71021899dc`는 넷 상태(수명 int, 마감 프레임 u32, 팀 int, 연결 bool)를 받아 지역 상태를 맞춥니다. 연결=true이고 `deadline - RequestUnemitSec*60 <= now`이면 RequestUnemit, 아니면 Connect로 간주하여 현재 상태·팀이 다르면 정리 후 `0x710217b418(팀)`으로 Connect 진입 또는 RequestUnemit로 전환하고, 마지막에 `life = clamp(수신 수명, 0, max)`, `deadline = 수신값`을 씁니다. 상세 비트 포맷은 [network] 담당 표(`analysis/network/`) 참고 **[미확정 — 이 문서에서 대조 안 함]**.

### 5.2 Invisible 진입 (`0x71058e87a4`) [판독]

`0x71058e87a4`는 "현재 씬이 `Scene_Coop` 분류에 속함" 비트입니다. 유일한 쓰기는 `0x7102b55594`(함수 `0x7102b546e0` 안)이고, 씬 분류 비트표(행 = 현재 씬, 열 = 분류 이름 인덱스)에서 이름 정적 객체 `0x71058e9270`(이름 포인터 → 문자열 `"Scene_Coop"`, 정적 초기화 `0x7102b582d0`)의 열을 읽어 저장합니다. 이웃 전역도 같은 방식입니다(`0x71058e87a0` ← `Scene_MissionLastBoss02` 등). 비트표가 "씬 그룹 소속"이라는 해석은 이름 목록으로 본 **[추정]**입니다.

- 시작(vt15 `0x710217a8a8`): Scene_Coop이면 다음 상태 = 3(Invisible), 아니면 0(Wait).
- 초기화(`0x7102178c44`): Scene_Coop이고 `*0x7105790740 != 0`이면 `0x7100f3de98`에 자신을 등록(연어런 쪽 관리자 [추정]).
- 넷 판정(`0x7102189464`): Scene_Coop이고 [[0x71057908b8]+0x195]==0 등 조건이면 권한 판정 1.
- **v0 대전에서는 이 비트가 꺼져 있으므로 잉크레일은 항상 Wait로 시작**합니다 [판독 + 대전 씬은 Coop 아님]. Invisible에서 벗어나는 경로는 넷 이벤트 6(Wait)입니다(§3).

## 6. 계산

### 6.1 레일 구성과 노즐 위치 [판독]

```
// 0x710217f758 InkRailData::setup
rail = findRailByPoint(BancParam.LinkToPoint)      // 0x7101302ba8
if rail.points < 2: 레일 없음(이후 갱신 대부분 조기 반환)
for i in points: p[i] = rail.point[i].pos           // 점 객체 +0x18..+0x20
if UseBase: p[0].y += 0.5 ; p[0].isBase = true
seg[i].len = f32 sqrt(dx²+dy²+dz²)                  // 직선 구간, 곡선 보간 없음
// 0x710217acb8 reset
nozzle.pos = p[0]; dir = normalize(p[1]-p[0])
nozzle.rot = 현재 회전을 dir에 맞게 회전(0x710124ff50; 각이 0 또는 π면 0x710124fc48)
actor 행렬(+0x2c8..)에 기록 → 배치 Translate는 무시됨
life = max = 100 ; 상태 관련 필드 0
```

### 6.2 레일 연장 (Connect/RequestUnemit exec) [판독]

```
// 0x710217d810
if !fullyExtended:
    total = Σ seg.len
    ext = min(ext + 1.0, total)          // 1.0 = [0x71058a7764], 정적 초기화 0x71021785e0 에서 (−1.0, 1.0) 기록
    if ext >= total: fullyExtended = true
    segIdx = 첫 번째로 누적길이 >= ext 인 구간
    frac = (ext - 누적길이_앞) / seg[segIdx].len
    구간이 바뀌거나 완전연장 시 해당 구간 애니 "Idle"
드로어(+0x2550) 갱신: 구간별 모델 행렬·이펙트(InkInhaleL 등)
```

### 6.3 플레이어 접촉 (vt22 `0x710217c148`) [판독]

```
contact(player):
  if player가 탑승 중이 아님(플레이어+0x108 객체 +0xa668 의 핸들(+0x1b8)이 -1 이거나, 핸들 대상 +0x24 상태가 7~11):
     if player.velY(+0x73c) < PlayerDropImpactEnableVelY (0.1)
        and player.y(+0x14) > rail.actorY(+0x290) + PlayerDropImpactEnableY (0.48):
          n = 접촉 법선의 XZ 정규화(0이면 기본 벡터)
          player에 n * PlayerDropImpact(1.0) 밀어냄 (0x71012d42f4)
  if state == Wait: return
  if player.team != rail.team:
       player에 접촉 법선 * OppositeKnockback(1.0) 밀어냄
       return
  q = 접촉점(법선 방향 보정) → 레일 최근접 위치(0x710217ff60, 아래)
  if state == Connect and team 일치 and player가 탑승 가능(0x71023538f0) and 아직 목록에 없음:
       탑승 시작 0x710217ca44 (탑승자 목록 추가 → PlayerInkRail 바인드)
```

레일 최근접점 `0x710217ff60(InkRailData, &dist, &s, q)` [판독 — `analysis/decomp/stage/inkrail_ride_full.c`]:
```
best = +3.4028235e38(FLT_MAX); bi = 0; bu = 0
for i in 0..구간수-1:                         // 구간 = (p0, p1, len=+0x10), InkRailData +0x68 배열
    d = p1 - p0; t = dot(d, q - p0)
    if t <= 0: u = 0, c = p0
    elif t < |d|²: u = t / |d|², c = p0 + d*u
    else: u = 1, c = p1
    e = |c - q|²
    if e < best: best = e, bi = i, bu = u     // 같으면 앞 구간 유지
s = Σ_{j<bi} seg[j].len + bu * seg[bi].len ; dist = sqrt(best)
```
점은 InkRailData가 만든 점(첫 점 UseBase면 Y+0.5)이고 레일 부모 변환은 쓰지 않습니다(InkRailData는 레일 점 객체 +0x18 원좌표를 복사, `0x710217f758`) [판독].

### 6.3b 탑승 가능 판정 (`0x71023538f0` → `0x710262c480`) [판독]

`0x710217c900`(레일 쪽, 상태 Connect·팀 일치일 때만)이 `0x71023538f0(player, railHandle)`을 부르고, 이것은 플레이어 본체 +0xa668(PlayerInkRail)로 `0x710262c480(PlayerInkRail, rail)`을 호출하는 포장 함수입니다. 참이면 탑승자 목록(+0x2310/+0x2318)에 같은 레일 id(+0x10)가 없을 때 탑승합니다.

```
canBind(pir = PlayerInkRail, rail):                       // 0x710262c480, 기준 body = [pir+0x1a0]+0x108
  if [[0x71057908b8]]+0x180 != 0: return false             // 전역 정지 플래그 [의미 미확정]
  if [[0x7105790d88]+0xc70]+0x18 >= 0 and !0x710129e56c(body+0xa8e0 +0x20): return false   [의미 미확정]
  if pir+0x1b8 핸들이 유효하고 대상 +0x24 상태가 7~11 밖: return false   // 이미 다른 레일에 바인드 중
  if 0x71024c7234(body 컴포넌트 묶음, 0, 0) : return false  // 플레이어 쪽 금지 상태 묶음 (아래 표)
  if body+0xb3c != 0: return false
  st = [body+0xa8c8]+0xc8                                  // 플레이어 상태 번호
  if st ∉ S = {0x82..0x90, 0xaa..0xac, 0xed, 0xee, 0x10c}: return false
       // S는 [player] movement_physics §4.2의 "오징어 속도 경로 상태 집합"과 같은 집합 → 오징어(잠복) 상태에서만 탑승
  if body+0x926c / +0x65c(0x1a·0x1c) 계열 특수 상태, [body+0xa6c0] (PlayerInkActionSpNiceBall)+0x2658 != 0,
     [body+8]+0x7b9 != 0, [body+0xa880] (PlayerDokanWarp)+0x30 != 0: return false
  if [body+0xa810] (PlayerAttractTarget) 핸들 대상 상태가 7~11 밖: return false
  if [body+0xa7c0] (PlayerCoopZombie)+0xeec != 0: return false
  if recentFinish(pir, player) and rail.id(+0x10) == pir+0x1d0(직전 레일 id): return false   // §7.5
  return true
```

컴포넌트 이름은 [player]의 `analysis/player/player_components.tsv` 기준입니다. +0x65c 값 0x1a/0x1c, +0x926c, +0xb3c, +0x7b9의 의미는 **[미확정]**(특수 무기·상태 플래그로 보임).

`0x71024c7234` 내부(2026-10-02 3차 판독, `analysis/decomp/stage/lift_rail_matrix.c`). 인자: p1 = 본체+0xa5f9, T = 본체+0xd58(쓰러짐 구조체, [life] player_life.md §6.8), p3 = 본체+0x9208, DokanWarp, StartLaunch(+0xa6a8), 본체+0x925c, CoopSeq(+0xa830), MissionTicketGateAction(+0xa6c8), MissionSeqPinch(+0xa860), 상태 소유자(+0xa8c8), 0, 0. **참(1) = 탑승 금지**:

| 순서 | 조건 → 1 | 비고 |
|---|---|---|
| 1 | T+8 > 0 | 사망 대기([life] T+8) |
| 2 | (T+0x98 > 0 && T+0xac > 0) 또는 (T+0xb4 > 0 && T+0xc4 > 0), 또는 T+0x88 > 0, T+0xb4 > 0, T+0x98 > 0, T+0 > 0 | [life]의 같은 계열 타이머(다운 등) |
| 3 | T+0x101 ≠ 0, 바이트 T+0x85bc(=본체+0x9314) ≠ 0 | 의미 미확정 |
| 4 | [T+0x9970] (=MissionTicketGateAction)+0x38 == 1 && +0x3c ≤ 124.0 | 미션 전용 |
| 5 | p3+8, p3+10, p3+0xb 바이트 ≠ 0, [p3+0x1628] (CoopSeq)+0x1348 == 0xc | 의미 미확정 |
| 6 | 전역 조건(`[0x7105825fd0]+0x180==0`, `[[0x7105801cc0]+0xc70]+0x18 ≥ 0`, [본체+0xa8e0]+0x2c ≠ 0 이고 +0x48 분기 일치)일 때 본체+0x92e0 또는 +0x92a0 바이트 ≠ 0 | 의미 미확정 |
| 7 | CoopSeq+0x38 > 9 또는 비트 ∉ {0,1,6,9}(마스크 0x243) | 연어런 진행 상태 |
| 8 | (MissionTicketGateAction+0x38 ∉ {0,5}) 또는 (MissionSeqPinch+0x38 ∈ {3,4}) | 미션 전용 |
| 9 | 상태 번호(+0xc8)가 0xef/0xf0이고 [상태+0x18]+0x30(+[0x71058bb8f4] 인덱스) ≤ 95.0, 0xf1, 0xf2이고 같은 값 ≤ 50.0 | 특정 상태의 진행 값(애니 프레임 [추정]) |
| 10 | [p1+0xd7] (=[본체+0xa6d0])+0x38 ≠ 0, 또는 DokanWarp+0xcf ≠ 0, 또는 w = DokanWarp+0x30 ∈ {1,2}, 또는 w ∉ {0} 이면서 (w==3 이고 세부 조건 X 불충족, 또는 +0xc0 == 1, 또는 +0xf4 ≥ 0x1f) | 토관 워프. w==0(대전 기본)이면 +0xcf만 봄 |
| 11 | StartLaunch+0xb4 ≠ 0 이고 r = (+0xc60 ≤ 0 ? 1 : max(+0xa4/+0xc60, 0)) < +0xc64 | 경기 시작 발사 연출 진행 중 [추정 — 컴포넌트 이름] |
| 그 외 | 0(허용) | |

v0 대전에서 실제로 걸릴 수 있는 것은 1·2(쓰러짐·사망)와 11(시작 연출)입니다 **[추정 — 나머지는 미션·연어런·토관 컴포넌트]**. 웹 대전 구현은 "사망/다운 중, 경기 시작 연출 중 탑승 금지"로 충분합니다.

"+0x73c = 수직 속도"는 비교 대상(EnableVelY)으로 본 **[추정]**, 밀어냄 함수 `0x71012d42f4`의 단위(속도/임펄스)는 **[미확정]**. 같은 "핸들 상태 7~11 밖" 검사가 PlayerInkRail 갱신(`0x7102628108`) 첫머리에서 "탑승 진행 중"의 조건으로 쓰입니다 [판독].

## 7. 플레이어 탑승 (spl::PlayerInkRail)

기준 객체 = PlayerInkRail this(`param_4`). 파라미터 객체 = this+0x178(그리고 +0xa0, +0x238; 모두 InkRailPlayerParam) [판독].

### 7.1 spl__InkRailPlayerParam [판독 기본값 + 데이터]

| 오프셋 | 필드 | 기본값 | SplPlayer 데이터 | 플래그 | reader |
|---|---|---|---|---|---|
| +0x38 | AccLerpNBias | 0.25 | | 0x95 | `0x7102628108` |
| +0x3c | BindLerpCnt | 24 | | 0xa4 | 같음 |
| +0x40 | FinishImmAfterFrame | 24 | **30** | 0xa7 | `0x710262c7f0` |
| +0x44 | FinishPlayerVelRateY | 0.05 | **0.3** | 0x9d | `0x7102626adc` |
| +0x48 | KeepPrevLineFStickCancelAngle | 0.0 | | 0x9c | `0x7102628108` |
| +0x4c | PlayerAcc | 0.05 | | 0x96 | 같음 |
| +0x50 | PlayerAirKd | 0.92 | | 0x99 | 같음 |
| +0x54 | PlayerJumpRightSpeed | 0.05 | **0.01** | 0x9b | `0x7102626adc` |
| +0x58 | PlayerJumpSpeed | 0.19 | | 0x9a | `0x7102626adc`, `0x7102628108` |
| +0x5c | PlayerSpeedMax | 0.192 | | 0x97 | `0x7102625ef8` |
| +0x60 | PlayerSpeedMax_LostArmor | 0.1 | | 0x98 | `0x7102625ef8` |
| +0x64 | PlayerVelBufferSize | 5 | | 0x9e | `0x7102628108` |
| +0x68/+0x6c | ScaleFix / ScaleFixSpeedMin | 0.8 / 0.05 | | 0xa2/0xa3 | UseScaleFix(+0x94, false)일 때만 |
| +0x74 | SpeedLimit | 0.3 | | 0xa5 | `0x7102628108` |
| +0x90 | VerticalLineAngle | 15.0 | | 0xa6 | **[미확정]** |
| 기타 | StartPointScaleDistance 2.0, SmallModelScaleDistance 1.4, Sphere* | | ModelDynamicsUnitParam(AirRes 0.9 등) | | 표시 전용 |

`PlayerSpeedMax_LostArmor`는 `0x7102625ef8`에서 "this+0 != 0 이고 플레이어(+0x108)+0x92ec == 0"일 때 쓰입니다. 조건 필드의 의미(아머 상실)는 이름으로 본 **[추정]**.

### 7.1b 탑승 시작 (`0x710262caf4`) [판독]

`0x710217ca44`(레일 쪽 탑승 목록 추가)에서 이어지는 플레이어 쪽 바인드 초기화입니다.

```
(s, segIdx) = 레일 최근접 위치(0x710217ff60, 접촉점)          // 레일 시작부터의 거리
pos 캐시(this+0x108) = 플레이어 위치(플레이어+0x10)
dirFlag(this+0x141) = dot(seg[segIdx].p1 - p0, 플레이어+0x34..0x3c) > 0   // 1이면 "Born", 0이면 "BornBack" 애니
frame(this+0x144) = 0, 링버퍼 비움
v0 = dot(플레이어+0xe4..0xec, railDir)
speed = dirFlag ? clamp(v0, 0, vmax) : clamp(v0, -vmax, 0)           // 진행 방향 성분만, 최대 속도 이하
vel(this+0x120) = railDir * speed
플레이어 속도 관련 필드(+0x73c, +0x750.., +0xe4.. 등) 0으로 초기화
```

플레이어 +0x34 벡터(앞 방향 또는 이동 방향)와 +0xe4 벡터(속도)의 의미는 [player] 문서와 대조 필요 **[추정]**. 진입 직후 BindLerpCnt(24)프레임 동안 위치가 레일로 끌려가므로, 웹에서도 바인드 순간 위치를 순간이동시키지 말 것.

### 7.2 탑승 중 매 프레임 (`0x7102628108`) [판독]

```
speed: f32 (this+0x138, 레일 따라 부호 있는 속도, 단위/프레임)
s:     f32 (this+0x13c, 레일 시작부터 거리)
frame: this+0x144 (탑승 후 프레임, 매 프레임 +1)

stickWorld = 카메라 기준 좌스틱(플레이어 +0x474,+0x478 → 행렬 +0xa878) 를 레일 평면에 투영 (0x7102625d40 계열)
m = |stick|
speed *= PlayerAirKd                                 // 0.92
x = bias(m, AccLerpNBias)                            // §7.4, 0.25 → m²
a = x * dot(stickDir, railDir)                       // railDir = this+0x14c..0x154
(구간 전환 프레임이면 직전 a와 비교해 절댓값 큰 쪽, 직전 부호 유지)
speed += a * PlayerAcc                               // 0.05
(UseScaleFix 경로는 기본 false라 생략)
vmax = PlayerSpeedMax (또는 LostArmor)
speed = clamp(speed, -vmax, vmax)
s += speed
s = clamp(s, 0, 전체 길이)                            // 끝에서 이탈하지 않음 (§7.2b, 3차 정정)

// 위치 보간
t = clamp(frame / BindLerpCnt, 0, 1)                  // 24프레임에 걸쳐 레일로 끌려감
target = railPoint(s)                                 // 구간 선형 보간
corr = (target - pos) * t ; |corr| <= SpeedLimit(0.3) 로 길이 제한
vel  = speed * railDir(s)                             // this+0x120..0x128
pos  = pos + corr (+ vel 은 별도 기록)                 // this+0x108..0x110
속도 링버퍼(this+0x160, 용량 this+0x168, 시작 +0x16c, 개수 +0x170)에 vel 추가,
개수 > PlayerVelBufferSize(5) 이면 가장 오래된 것 제거
```

- 바이어스와 속도 식, 클램프, 보간 t, SpeedLimit, 버퍼는 디컴파일 판독입니다.
- 2026-10-02 3차: 위 `s += speed` 뒤의 "레일 끝 판정 → 이탈"은 **틀렸습니다**(정정). 전체 분석 프로젝트로 다시 받은 디컴파일(`analysis/decomp/stage/inkrail_ride_full.c`)에서 끝 처리는 §7.2b와 같습니다.

### 7.2b 레일 끝·이탈 분기 전체 (`0x7102628108`) [판독 — 2026-10-02 3차]

```
// 매 프레임 (기준 = PlayerInkRail this, body = [this+0x1a0]+0x108, rail = 바인드 핸들의 InkRail)
this+0x1e4 = min(this+0x1e4 + 1, 9999)
if 핸들(this+0x1b8) 무효 or rail 액터 상태 ∈ 7..11: return            // 갱신 안 함
if 원격 조건(넷 관리자 +0x180==0 && … && !0x710129e56c(본체+0xa8e0+0x20)): → [원격 경로] (아래)
if DokanWarp+0x30 != 0:                       → 이탈(속도 = 0x7102626adc)
if 특수 활성 && 본체+0x65c == 0x1c && [본체+0xa7f0]+0x40 != 0:
                                              → 이탈(속도 (0,0,0) = DAT 0x7104a981f4)
if 상태 번호 ∉ S' = {0x82..0x90, 0xaa..0xac, 0xed, 0xee, 0x10c}:
                                              → 이탈(속도 = 0x7102626adc)   // 오징어 상태를 벗어남
if rail 상태 != Connect(1):                   → 이탈(속도 (0, PlayerJumpSpeed, 0))
jumpEdge = 본체+0x72d                         // 점프 버튼 눌림 엣지(아래)
… §7.2 속도 계산 …
speed = clamp(speed, -vmax, vmax)
flip = (dirFlag==0 && speed > 1.1920929e-07) || (dirFlag==1 && speed < -1.1920929e-07)
frame(this+0x144) += 1.0
s' = s + speed
if 연장 길이(rail+0x2504) == 전체 길이 && InkRailData+0x48 != 0: 루프/연결 처리     // v0 에서 실행 안 됨(아래)
s = clamp(s', 0, 전체 길이)                    // 끝에서 이탈하지 않고 멈춤
0x7102626954(s): this+0x13c = s, 구간 번호 this+0x180, 구간 비율 this+0x184 = (s − 앞 누적)/구간 길이
target = 구간 선형 보간 점, t = clamp01(frame / BindLerpCnt)
corr = (target - pos) * t ; |corr| > SpeedLimit 이면 SpeedLimit 길이로
vel(+0x120) = speed * railDir ; (+0x12c) = corr - vel ; pos(+0x108) += corr
if flip: dirFlag ^= 1 ; 애니 "Turn" + xlink "InkRailTurn"(0x710262d84c)
속도 링버퍼 push(용량 PlayerVelBufferSize)
0x710262d19c(0, this, pos, 정규화(this+0xb4)): 플레이어로 바인드 위치·방향 메시지
if jumpEdge: → 이탈(속도 = 0x7102626adc, §7.3)
```

- **레일 끝 자동 이탈 없음**: v0 경로에서 s는 `[0, 전체 길이]`로 클램프만 됩니다. 끝점에서 속도는 vmax 클램프를 유지하고 위치는 끝점으로 수렴합니다 [판독].
- `InkRailData+0x48`(루프/연결 분기 플래그)은 InkRail 코드 영역(0x7102170000~0x7102190000, capstone skipdata 전수)에서 0 기록(`0x710217f70c`, `0x71021807ac`)만 있습니다. 같은 데이터의 `+0x40`(닫힘)도 `0x710217f758`이 0으로 둡니다 → v0에서 루프 분기(턴 판정 `0x7102626f50`, 속도 부호 반전)는 실행되지 않습니다 [판독 — 범위 검색].
- `UseScaleFix`(+0x94, 기본 false) 경로(마지막 구간에서 구간 비율 this+0x184 > 0.5 조건, ScaleFixSpeedMin)는 v0 데이터에서 꺼져 있습니다 [데이터].
- 이탈 시 공통: `0x710262ab60(this, &vel, 1)` — §7.5의 재탑승 래치(+0x1d8, +0x1dc)를 씁니다.
- **점프 엣지 `본체+0x72d`**: `0x710249f494` 안(`0x71024a0968`~`0x71024a09c8`)에서 `+0x72c` = 입력 바이트([본체+0xa164]+0x58, 유지), `+0x72d` = (직전 0 → 현재 1) 엣지 또는 버퍼(+0x747) [판독]. `+0x72c`가 점프 유지라는 의미는 [network] 04 PlayerNetState Jump 필드(본체+0x72c) 기준 **[추정]**.
- **[원격 경로]** (`LAB_7102628200` 이하): 넷으로 받은 위치(this+0x1ec, 플래그 +0x1e8)를 `0x7102180160`으로 레일에 붙인 뒤 최근접점 `0x710217ff60`로 s를 다시 구하고, 속도 = dot(구간 방향, this+0x120)로 재설정합니다. 판정 조건 `0x710129e56c`가 "이 기기 조작" 판정이라는 것은 **[추정]**.
- `pos` 갱신식은 디컴파일상 `pos += (corr - vel) + vel`로 나옵니다(최종 = pos + corr). 이동량 vel이 별도 경로(플레이어 이동 계통)로 더해지는지는 **[미확정]**이고, [player] 문서와 맞춰야 합니다.
- 스틱 → 월드 변환, `railDir`의 부호(진행 방향 플래그 this+0x141)는 큰 틀만 판독 **[부분 판독]**.

### 7.3 이탈 속도 (`0x7102626adc`, 디스어셈블로 확정) [판독]

```
v = 링버퍼에서 가장 최근의 |v|>0 속도 (없으면 this+0x48..0x50)
d = 현재 레일 방향(0x7102625d40 출력 (dx,dy,dz))
side = this+0x84 (좌우 입력, [추정])
out.x = v.x + (-d.z) * side * PlayerJumpRightSpeed
out.y = v.y * FinishPlayerVelRateY + PlayerJumpSpeed
out.z = v.z + ( d.x) * side * PlayerJumpRightSpeed
```

레일이 사라져(상태 ≠ Connect) 강제로 떨어질 때는 `(0, PlayerJumpSpeed, 0)`을 씁니다(`0x7102628108` 안 플래그 0x9a 경로) [판독].

### 7.4 바이어스 곡선 (InkRail 탑승·스펀지 공통) [판독]

```
bias(x, b):
  if |b - 0.5| <= 0.001: return x            // 항등 (정확히 b-0.5 == 0.001 도 항등)
  if |x| < 0.001: return 0
  if b < 0.001: return (|x| >= 0.999) ? 1 : 0   (부호는 원 코드에서 양수만 확인)
  y = exp( ln|x| * ln(b) * -1.442695 )      // = |x|^(-log2 b)
  return sign(x) * y
```

`-1.442695 = -1/ln2`. b=0.25면 지수 2(제곱). exp/ln 호출(`0x7103e9be20`, `0x7103e9c2a0`)은 libm으로 본 **[추정]**.

### 7.5 이탈 직후 재탑승 금지 (`0x710262c7f0`, FinishImmAfterFrame) [판독]

이전 판에서 `0x710262c7f0`을 "레일 끝 이탈 세부"로 적었으나, 판독 결과 **이탈 직후 같은 레일에 다시 붙지 않게 하는 판정**입니다(정정).

```
// 이탈 시(탑승 갱신 0x7102628108 의 종료 경로, 0x710262ab60): pir+0x1d8 = 1(또는 인자), pir+0x1dc = now(GameFrame, 음수면 0)
// 바인드 시작(0x710262caf4): pir+0x1d8 = 0
recentFinish(pir, player):                                 // 0x710262c7f0
  if (now - pir+0x1dc) <= FinishImmAfterFrame(SplPlayer 30) and pir+0x1d8:
      return clamp01(body+0x73c / K) > 0                    // K = [[0x7105795dd8]+0xe8], 부호만 의미
  if [body+0xa880] (PlayerDokanWarp)+0x30 ∈ {1,2}:
      return clamp01(body+0x73c / K) > 0
  return false
canBind: recentFinish && rail.id == pir+0x1d0 이면 금지
```

즉 레일을 떠난 뒤 30프레임 동안 플레이어가 위로 움직이는 중(body+0x73c > 0 [추정: 수직 속도])이면 **같은 레일**에는 다시 탑승하지 않습니다. 다른 레일은 허용됩니다.

정정(2026-10-02 3차): 이전 판의 "완전 연장 상태에서 `s + speed`가 범위 밖이면 종료 경로" 서술은 틀렸습니다. 범위 밖이면 s를 클램프할 뿐이고, 이탈은 §7.2b의 다섯 경로(토관 워프, 특수 0x1c, 오징어 상태 이탈, 레일 비연결, 점프 엣지)뿐입니다 [판독].

## 8. 표현·이펙트·사운드

| 시점 | 연결 | 근거 |
|---|---|---|
| Wait→Connect | ASKey "StartUp", "Activate" (액터 +0x520 재생기, 인자 2) | `0x710217b514` [판독] |
| Wait enter | ASKey "Wait"(드로어) | `0x7102179524` |
| Connect enter | 이펙트 "Rail" 시작(핸들 +0x2510) | `0x7102179988` |
| 피격 | 애니 "DamageShot", 쿨다운 0이면 "HitEnemy" | `0x710217ea4c` |
| 연장 중 | 구간 "Idle", "InkInhaleL" 이펙트 | `0x710217d810` |
| 탑승 | xlink "InkRailJump", "InkRailTurn" (`searchAndEmit`) | PlayerInkRail 함수 |
| 게이지 | 애니 "Gauge", "Gauge_fts", "Gauge_fsp", "GaugeBlink" (MeterAnimLength 100, BlinkFrame 80) | `0x710217bce8` |

ASKey/xlink 이름과 실제 이펙트·사운드 파일 대응은 [effect_sound] 문서 소관입니다.

## 9. 다른 기능과의 상호작용

- **피해 계통**: InkRail은 DamageReceiver(`DamageRateInfoCol "InkRail"`)로 잉크 피해를 받습니다. 배율 표: 대부분 1.0, `RollerCore` 12.0, `Bomb_DirectHit` 0.0 [데이터]. 피해 단위 0.1HP([combat] 확인)라 슈터 1발(예: 36.0 → 360)로 WaitLife 100을 넘깁니다.
- **플레이어 이동**: 탑승 중 플레이어 위치·속도는 PlayerInkRail이 정합니다. 진입 조건은 §6.3b(오징어 상태 집합 S에서만 탑승)로 판독했습니다. 상태 번호의 이름은 [player] 쪽에서도 미확정입니다.
- **네트워크**: 수명·팀·마감은 마스터가 결정하고 넷 상태로 퍼뜨립니다. 웹 서버 권위 모델이면 서버가 마스터 역할.
- **모드 레이어**: Yagara는 Pnt/Var/Vgl/Vcl에만 레일이 있고 Vlf(야구라)에는 없습니다 [데이터].

## 10. 웹 포팅

### 10.1 모듈

| 모듈 | 책임 | 공유 |
|---|---|---|
| `stage/railGraph` | Banc `Rails[]` 파싱, Hash→점, 구간 길이(f32) | 서버·클라 |
| `gimmick/inkRail` | 상태머신·수명·팀·연장 길이 | 서버 권위, 클라 예측 표시 |
| `gimmick/inkRailRider` | 탑승 속도·위치·이탈 | 서버·클라 공통(결정적) |
| `gimmick/inkRailView` | 노즐/레일 모델, 게이지, 이펙트 | 클라 |

### 10.2 상태 객체 (웹 권장 이름 ↔ 원본)

```ts
interface InkRailState {          // 원본 spl::InkRail
  state: 'Wait'|'Connect'|'RequestUnemit'|'Invisible'; // +0x2540[+0x38] 0..3
  team: 0|1|3|-1;                 // +0x2530
  life: number;  lifeMax: number; // +0x24f8 / +0x24fc (int)
  timeAcc: number;                // +0x2528 (f32)
  deadlineFrame: number;          // +0x252c (u32)
  extend: number; fullyExtended: boolean; // +0x2504 / +0x2500
  segIndex: number; segFrac: number;      // +0x2508 / +0x250c
  points: Vec3[]; segLen: number[];       // InkRailData
}
interface InkRailRider {          // 원본 spl::PlayerInkRail
  speed: number; s: number; frame: number; // +0x138 / +0x13c / +0x144
  velRing: Vec3[];                // +0x160.., cap PlayerVelBufferSize
}
```

### 10.3 갱신 순서 (한 프레임)

1. 피격 이벤트 처리(`onInkDamage(amount, team)`): 팀 결정 → 수명 가감.
2. `inkRail.update(now)`: §5 전이 (Wait 판정 → Connect 시간 감소 → RequestUnemit 마감).
3. 상태 exec: Connect/RequestUnemit이면 연장 +1.0.
4. 접촉 처리: 플레이어별 밀어냄·넉백·탑승 시작.
5. 탑승자 갱신(§7.2, §7.2b), 이탈(점프 엣지·레일 비연결·오징어 상태 이탈 등) 시 §7.3 속도로 플레이어 공중 상태 전환. 레일 끝에서는 s만 클램프.

원본에서 피격 콜백과 vt18 갱신의 같은 프레임 내 순서는 **[미확정]**(엔진 호출 순서 미판독). 위 순서는 피격이 먼저라는 가정이며, 결과 차이는 Wait에서 "같은 프레임에 활성되느냐 다음 프레임이냐" 1프레임입니다.

### 10.4 정밀도

- 수명은 int, `timeAcc`는 f32. `Math.fround`로 `acc += fround(max / int(sec*60))` 재현. 4000/900 = 4.444…라 900프레임에 정확히 0 도달(재구현 확인).
- 구간 길이 f32 sqrt. 연장 비교는 f32.

### 10.5 의사코드 (서버 공용)

```js
function inkRailUpdate(r, now, p) {
  switch (r.state) {
  case 0: if ((r.life <= 0 && isAuthority) || r.extReq) enter(r, 1, p); break;
  case 1:
    if (p.IsUnemitByTime && r.life > 0) {
      r.acc = f(r.acc + f(r.lifeMax / Math.trunc(f(p.ConnectionSec * 60))));
      if (r.acc >= 1) { const k = Math.floor(r.acc); r.life = Math.max(r.life - k, 0); r.acc = f(r.acc - k); }
    }
    if (r.life <= 0) enter(r, 2, p, now);
    break;
  case 2: if (r.deadline !== 0 && now >= r.deadline) { cleanup(r); enter(r, 0, p); } break;
  }
  if (r.state === 1 || r.state === 2) extend(r);   // +1.0
}
```

## 11. 검증

| 종류 | 내용 | 결과 |
|---|---|---|
| [재구현] 레일 길이 | `PY web/tools/gimmick_stage.py summary Vss_Yagara` | Pnt 15.1593(16프레임 연장), Vgl 9.8487, Vcl 9.3039 |
| [재구현] 상태 수명 | `gimmick_stage.py inkrail Vss_Yagara`: 10프레임에 팀0이 360 피해 | 10프레임 Connect, 910프레임 RequestUnemit(정확히 900프레임=15초), 940프레임 Wait(30프레임=0.5초) |
| [재구현] 탑승 가속 | `gimmick_stage.py ride --len 13.2`, 스틱 1.0 정방향, 초기 속도 0 | 0.05, 0.096, 0.13832, 0.177254, 이후 0.192 고정. 13.2 이동에 71프레임 |
| [재구현] 이탈 속도 | v=(0.192,0,0), d=(1,0,0), side=1 | (0.192, 0.19, 0.01) |

결과 파일 `analysis/gimmick/sim_results.json`. 모두 판독식을 옮긴 재구현이며 **원본 실행 비교는 없습니다**. 탑승 초기 속도는 §7.1b 식(진행 방향 성분 클램프)인데, 이 시뮬레이션은 0에서 출발시킨 합성 테스트입니다.

검증 기대값(웹 단위 테스트용):
- WaitLife 100, 피해 99 → Wait 유지, 피해 1 추가 → 다음 갱신에 Connect.
- Connect 중 적 피해 360 1발 → life 4000−(경과 감소)−360.
- Connect 중 같은 팀 피해는 lifeMax(4000)를 넘지 않음.

## 12. 미확정과 추가 근거

| 항목 | 상태 | 필요한 것 |
|---|---|---|
| CureRate(+0x60) 사용처 | 미확정→**추정(미사용)** | 플래그 바이트 +0x100 비트4(방문 `0x7102073e58`). main 전체에서 `ldr s,[x,#0x60]` 근처(±40명령) `[x,#0x100]` 접근 11곳을 확인했으나 InkRailParam 판독 코드 아님. InkRail 코드 영역(0x7102170000~0x7102190000)에 +0x60 f32 읽기 1곳(`0x7102176e5c`, 다른 객체). 문자열 참조는 방문 함수 2개뿐. 남은 가능성: 플래그 비트를 다른 방식으로 읽는 범용 조회 |
| 진입 조건 `0x71023538f0` | **해소 [판독]** | §6.3b. `0x71024c7234` 내부도 판독(2026-10-02 3차, 조건표). 남은 것: +0x65c/+0x926c/T+0x101 등 개별 플래그의 게임 의미 |
| 최근접점 `0x710217ff60` 세부 | 미확정→**해소 [판독]** | §6.3 끝(구간별 투영, 동률은 앞 구간, s = 앞 구간 길이 합 + u·len) |
| FinishImmAfterFrame(`0x710262c7f0`) | **해소 [판독]** | §7.5(재탑승 금지) |
| 레일 끝 판정 분기 전체(`0x7102628108`) | 미확정→**해소 [판독]**, 이전 서술 정정 | §7.2b: 끝에서 자동 이탈 없음(클램프), 이탈 다섯 경로, 루프 분기(InkRailData+0x48)는 v0 미사용. 남은 것: 본체+0x72c가 점프 버튼이라는 의미 확인([player]) |
| `RailSphereRadius` 판정 구 배치 간격 | 미확정 | `spl::RailCollider` 판독 |
| Invisible 상태 진입 전역 플래그 `0x71058e87a4` | **해소 [판독]** | §5.2 |
| 같은 프레임 피격/갱신 순서 | 미확정 | 엔진 액터 갱신 순서([player]/[main]) |
| 팀 번호 ↔ Alpha/Bravo | 추정 | 팀 enum 판독 |
