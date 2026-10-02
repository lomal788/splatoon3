# VS_MainTV_00 화면 요소 (대전 HUD)

[ui_hud.md](ui_hud.md)의 하위 문서입니다. 대전 중 상단 HUD 화면 `VS_MainTV_00`(코드 클래스 `SplUIVSMainTV00Screen`)의 페인 구성, 애니 슬롯, 파츠별 컨트롤 동작을 정리합니다. 포맷은 [ui_layout_format.md](ui_layout_format.md), 값 바인딩 전체 흐름은 [ui_hud.md](ui_hud.md) §3~§6에 있습니다.

주소는 main NSO를 0x7100000000에 올린 기준입니다. 오프셋 앞에는 기준 객체를 적습니다: **화면**(SplUIVSMainTV00Screen, 0x620 B), **게이지**(SplUISuperGaugeCtrl), **타이머**(SplUITimerCtrl), **아이콘**(SplUITGPlayerIconCtrl), **애니핸들**(아래 §2.1).

## 1. 화면 배치 [데이터 + 실행: 자체 도구]

레이아웃 1920×1080, 원점 화면 중앙, y 위가 +. 아래 화면 좌표는 `ui_render.py`의 변환식(부모 원점 + translate·rotate·scale 누적)으로 계산한 정적 배치값(애니 적용 전)입니다.

| 페인 | 종류 | 화면 좌표(px, 좌상단 원점) | 내용 |
|---|---|---|---|
| `N_TerritoryGauge_00` | pan1 | (960, 96) | 상단 중앙 묶음, 배율 1.1 |
| `W_Base_00` | wnd1 950×80 | (960, 92.7) | 팀 아이콘 바탕 |
| `L_Player_00..03` | prt1 → `TGPlayerIcon_00` | x 568.9 / 656.8 / 745.9 / 833.8, y 70.9 | 우리 팀 4명 (00이 가장 바깥) |
| `L_Opposite_00..03` | prt1 → `TGPlayerIcon_00` | x 1351.1 / 1263.2 / 1174.1 / 1086.2, y 70.9 | 상대 팀 4명 |
| `L_Timer_00` | prt1 → `Timer_00` | (960, 75) | 남은 시간, 배율 0.9 |
| `N_PlayerPinch_00` / `N_OppositePinch_00` | pan1 | (498, 63) / (1422, 63) | "위험해!" 말풍선 |
| `N_Lead_00` | pan1 | (454, 63) | "리드!" 말풍선 |
| `L_SuperGauge_00` | prt1 → `SuperGaugeTV_00` | (1776.8, 121.2) | 특수 게이지(오른쪽 위), 배율 0.99 |
| `L_PaintNumbers_00` | prt1 → `PaintNumbers_00` | (1636.2, 96.5) | 칠한 포인트 "0000p" |
| `N_Signal_00` | pan1 | (100.5, 975) | 왼쪽 아래 시그널/나이스(십자키) |
| `L_Info_00` | prt1 → `PauseText_00` (숨김) | (1883, 997) | "일시 정지" |
| `N_Var_00`, `N_Vlf_00`, `N_Tri_00` | pan1 (숨김) | — | 규칙별(영역·탑·삼색 등) 카운터. 이번 범위 밖 |
| `P_Logo_00` | pic1 (숨김) | — | 로고 |

렌더 결과: `analysis/ui/render/vs_maintv_ko_sample.png`(게이지 절반, 타이머 2:47, 아이콘 Watch 숨김).

## 2. 화면 애니 슬롯

### 2.1 애니 핸들 [판독]

UI 컨트롤과 화면은 애니를 이름으로 찾아 **애니 핸들** 배열에 둡니다. 핸들 구조(기준: 핸들 객체):

| 오프셋 | 형식 | 내용 |
|---|---|---|
| +0x08 | ptr | AnimTransform (`0x71038db1d8`가 만든 0x68 B 객체). `+0x18 → +8` u16 = 프레임 수(`0x7100851c78`) |
| +0x10 | s32 | 명령 코드 |
| +0x14 | f32 | 프레임 인자(−1 = 처음부터) |
| +0x18 | f32 | 속도 |

관측한 명령 코드와 쓰임(의미는 호출 맥락으로 붙인 **[추정]**):

| 코드 | +0x14 / +0x18 | 쓰인 곳 | 추정 의미 |
|---|---|---|---|
| 1 | −1 / 1.0 | 아이콘 Normal/Down/Absent 전환, 게이지 Max | 처음부터 정방향 재생 |
| 1 | −1 / −1.0 | TerritoryGauge 역방향 | 끝에서 역재생 |
| 3 | 현재 프레임 / 1.0 | 게이지 LoopMax·LoopGauge | 현재 위치에서 재생 계속 |
| 4 | 목표 프레임 / 0 | 아이콘 Special(0/1), 숫자 자릿수 | 프레임 고정 |
| 5 | 현재 프레임 / 0 | 게이지 LoopMax·LoopGauge 해제 | 그 자리 정지 |
| 6 | 0 / 0 | 리셋·정지 | 처음 프레임에 정지 |
| 7 | 프레임 수 / 0 | 리셋·TerritoryGauge | 마지막 프레임에 정지 |
| 10 | 0 / 0 | 리셋·상태 해제 | 정지·비활성 |

명령을 실제로 처리하는 함수(핸들 → AnimTransform 프레임)는 판독하지 않았습니다 **[미확정]**.

### 2.2 화면 애니 50개 [판독 + 데이터]

화면 초기화 `0x71033d93a0`(vtable 슬롯 97)이 쉼표 목록 문자열(@0x7104961eb5)을 잘라 50개 핸들을 **화면 +0x250 + i×8**에 둡니다. `이름__그룹`은 그룹 하나만, `파츠$애니`는 파츠 페인의 애니를 뜻합니다 **[추정 — 표기 규칙]**. 전체 표: `analysis/ui/vs_maintv_anim_slots.txt`.

| i | 화면 오프셋 | 애니 | 프레임 | 리셋(`0x71033d9f84`) |
|---|---|---|---|---|
| 0 | +0x250 | Signal | 110–121 | |
| 1 | +0x258 | Nice | 110–121 | |
| 2 | +0x260 | VsRule | 700–705 | |
| 3 | +0x268 | Watch | 100–101 | 코드 6 |
| 4–7 | +0x270..+0x288 | TerritoryGauge_00..03 | −20..−10 / −10..0 / 0..10 / 10..20 | 00: 10, **01: 7(끝 프레임)**, 02·03: 10 |
| 8–12 | +0x290..+0x2b0 | LoopAreaAdvantage_00/01, AreaDisadvantage_00/01, TypeAreaPoint | | |
| 13–27 | +0x2b8..+0x328 | LiftMark, InLiftBest, PosLiftBest, PosLift, PosLiftPoint_00..07 | | |
| 28 | +0x330 | WalkThrough | 760–761 | |
| 29–32 | +0x338..+0x350 | PosHokoPoint, HokoPointBreak (그룹별) | | |
| 33 | +0x358 | PlayerLead | 100–105 | 코드 6 |
| 34 | +0x360 | OppositeLead | 110–115 | 코드 10 |
| 35–36 | +0x368, +0x370 | `L_AreaAddTime_00$Count`, `_01$Count` | | |
| 37–42 | +0x378..+0x3a0 | LoopTriAdvantage_00 / TriDisadvantage_00 (그룹별) | | |
| 43 | +0x3a8 | GaugeOnOff | 0–1 | |
| 44–45 | +0x3b0, +0x3b8 | TriGauge_00/01 | 0–100 | |
| 46–49 | +0x3c0..+0x3d8 | TriTreasureFirst/Second (그룹별) | | |

목록에 없는 레이아웃 애니 `In`(−100..−92, `G_All_00`: 타이머·게이지·팀 묶음), `Out`(1000..1008), `Loop`(100..400 반복), `Logo`, `PlayerLead` 외 연출은 화면 기본 클래스가 이름으로 재생하는 것으로 보입니다 **[추정]**.

### 2.3 화면이 들고 있는 컨트롤 [판독]

| 화면 오프셋 | 대상 | 찾는 방법 (`0x71033d93a0`) |
|---|---|---|
| +0x3e0 | 특수 게이지 컨트롤(`SplUISuperGaugeCtrl`) | `0x710325e198(화면, "L_SuperGauge_00")` — 화면의 컨트롤 목록(+0x38 리스트)에서 이름·타입 일치 |
| +0x3e8 | PaintNumbers 컨트롤(SplMultiNumberAnim) | `"L_PaintNumbers_00"` |
| (여러 오프셋) | 규칙별 파츠(AreaAddTime/AreaPoint/PosLiftPoint) | 서식 `"L_AreaAddTime_%02d"`, `"L_AreaPoint_%02d"`, `"L_PosLiftPoint_%02d"`로 찾음. 오프셋 표는 생략 |
| +0x450 | 타이머 컨트롤(`SplUITimerCtrl`) | `"L_Timer_00"`. 찾은 직후 **타이머+0x150(형식) = 1(`VSTimer`)**을 쓴다 |
| +0x458 | `L_Info_00` 파츠(일시 정지 문구) | `0x71032165d8`, 이어서 vtable +0x158 호출(인자 0x400) |

## 3. 특수 게이지 `SuperGaugeTV_00`

### 3.1 페인 구성 [데이터]

```
RootPane
  N_CapSp_00  [CaptureOn RGBA8]           ← L_SubSpeIcon_01 (CmnIconSubSpecial_00: 특수 무기 아이콘) 캡처
  N_CapSub_00 [CaptureOn RGBA8]           ← L_SubSpeIcon_00 캡처
  N_SuperGauge_00 [EffectLinkOn LoopMax]
    P_SuperGauge_00 (숨김) 270²  VSSuperGaugeBase_00 + Dot_00
    N_Super_00 / P_IconBase_00 96²
    N_Appear_00
      N_Cap_00 [DynamicCaptureOn RGBA8, MultiFilterFile blur5]
        P_pict_00 128²  GaugeSp_00, 흑 #00000000 백 #ffffffff, 사용자 셰이더 MeterAction   ← 게이지(흰색, 캡처 전용)
      P_Base_00 128² Circle128_02 (백 #0f0f0f)          ← 원판 바탕
      P_BaseIconSp_00 128² [CaptureUse N_CapSp_00 #0]   ← 특수 아이콘
      P_BaseGauge_00 256² GaugeSp_00 (흑 #0a0a0a 백 #070707) ← 빈 게이지 눈금(어두운 색)
        P_pict_02 256² GaugeSp_00, 흑 #ff5d0000 백 #ff5d00ff, MeterAction  ← 채워진 게이지(주황)
        P_CapUse_01 256² [DynamicCaptureUse N_Cap_00 #0] 블렌드 op1 src4 dst1  ← 게이지 빛번짐(가산 추정)
      P_CapUse_02 / P_CapUse_00 128² [CaptureUse N_CapSp_00 #1]  ← 아이콘 + 잉크 모양 합성
      N_Max_02 / P_CapUse_03 256² [DynamicCaptureUse N_Cap_00 #0]
    N_Max_01: P_GaugeRInside_00/01 (가득 찼을 때 안쪽 번개 무늬), P_IconSpMax_00
    N_Coop_00 (숨김, 연어런용)
  N_MaxAll_00 → N_Max_00: 스틱 누르기 그림(P_LStickBottom_01, P_RStickTop_01), P_GaugeArrow_00[TeamColorUse MyTeam], T_Press_00 "누르기"
  N_Text_00: T_Max_00/T_Max_01 "풀 충전!" (오른쪽 정렬)
  N_Mis_00, N_Oct_00 (히어로/옥타 모드)
```

주황 `#ff5d00`은 재질에 박힌 색입니다. 게임에서 팀 색으로 바뀌는지는 이 재질에 `TeamColorUse`가 없어 **아니라고 봅니다** **[추정]**. 팀 색을 쓰는 페인은 `P_GaugeArrow_00` 하나입니다.

### 3.2 애니 [데이터]

| 애니 | 프레임 | 반복 | 대상 | 내용 |
|---|---|---|---|---|
| **Gauge** | 75 | × | P_pict_00, P_pict_02 | FLEU `__CUS_Float_0` 0.75 → 0 (직선) |
| Appear | 8 | × | N_Appear_00 | 알파 0(7f) → 255(8f) |
| Max | 8 | × | N_Max_00/01, N_Max_02 | 알파 0→255, N_Max_02 숨김 |
| LoopMax | 120 | ○ | P_GaugeRInside_00/01, P_IconSpMax_00 | 무지개 정점색 순환, 아이콘 밝기 |
| LoopGauge | 2000 | ○ | P_GaugeRInside_00 (재질) | 무늬 텍스처 회전 0 → −360°, 배율 맥동 |
| Loop | 120 | ○ | 화살표·스틱 그림, P_CapUse_01/03 | 누르기 안내 흔들림, 빛번짐 알파 255↔15 |
| InText | 120 | × | N_Text_00, T_Max_01 | "풀 충전!" 들어오기(x −133.5 → −49.5, 알파 0→255) |
| OutText | 16 | × | N_Text_00 | 알파 255→0 |
| OutMax | 5 | × | N_MaxAll_00 | 알파 255→0 후 숨김 |
| Decide | 6 | × | N_Max_00/01 | 배율 1→0.5, 알파 255→0 (특수 발동) |
| Coop / Item / Mission / Oct | 1~2 | × | 표시 전환 | 모드별 |

### 3.3 컨트롤 필드 (기준: 게이지 = `SplUISuperGaugeCtrl`, 0x1B0 B) [판독]

생성: 컨트롤 팩토리 `0x71031eefb0` 안 `SuperGaugeTV_00` 분기(@0x71031f04cc), 기본 vtable(GOT 0x71057a4410 → 0x710557c390). TraceGauge 필드(+0x18~+0x74)는 [ui_hud.md](ui_hud.md) §4.2를 봅니다.

| 오프셋 | 형식 | 이름(웹 권장) | 초기값 | writer | reader |
|---|---|---|---|---|---|
| +0x138..+0x178 | 핸들×9 | `anim.loopGauge, max, loopMax, inText, outText, coop, item, mission, outMax` | — | init `0x7103173c9c`(목록 문자열 @0x710497375e) | update `0x710317426c` |
| +0x180 / +0x188 | ptr | `iconPart1`, `iconPart0` | — | init (`L_SubSpeIcon_01/_00`) | update, `0x71031741b0` |
| +0x190 / +0x198 | ptr | `capSp`, `capSub` (캡처 페인) | — | init (`N_CapSp_00`, `N_CapSub_00`) | update(+0xd4=1 다시 캡처 요청 추정) |
| +0x1a0 | u8 | `suppressMaxTextOnce` | 0 | `0x71031741b0` | update(0이 아니면 이번만 InText 생략하고 0으로) |
| +0x1a1 | u8 | `iconSwapped` | 0 | update | update (아이콘 파츠 +0x158 == 0x14일 때 OutMax 재생 전환) |
| +0x1a4 | s32 | — | 0 | `0x71031741b0` | |
| +0x1a8 | u8 | `showFullText` | 0 | 디스패처 `0x710342eb10`, 리셋 0 | update(가득 참 때 InText 재생 조건) |

갱신 `0x710317426c`(vtable 슬롯 13)의 동작은 [ui_hud.md §5.2](ui_hud.md)에 있습니다.

## 4. 타이머 `Timer_00` (기준: 타이머 = `SplUITimerCtrl`) [판독]

레이아웃: `N_Time_00` 안 `P_BaseTime_00`(154×84 바탕) + `T_Time_00`(BlitzMain_S, 크기 배율 1.12, 기본 문자열 '８:１０'), 숨김 `N_Extend_00`("연장 중!"). 애니: In, Out, Valid, State, StateCount_00/01, StateLoop_00/01/02, GaugeExtend.

| 오프셋 | 형식 | 이름 | 값 | 근거 |
|---|---|---|---|---|
| +0x140 | f32 | `timeFrames` | 생성자 NaN(0xffff0000), 리셋 때 **10800.0** (= 180초 × 60), 대전 중 매 프레임 남은 프레임(아래) | 생성자 `0x710314cc9c`, 화면 리셋 `0x71033d9f84`, 공급 `0x7103096214` |
| +0x144 | s32 | `shownSeconds` | 마지막으로 그린 초(바뀔 때만 문자열 갱신), 생성자 0xbf800000 | `0x710314cf80` |
| +0x148 | u8 | `roundUp` | 1이면 올림. **생성자가 1**, 다른 writer 없음 → 대전 타이머는 올림 | 생성자 `0x710314cc9c` **[판독]** |
| +0x14c | s32 | `framesPerSecond` | **60**(생성자가 64비트 쓰기로 +0x14c=60, +0x150=0) | 생성자 `0x710314cc9c` **[판독]** (2026-10-02 [gauge], 이전 [추정]) |
| +0x150 | s32 | `format` | 0 정수 3자리, 1 `VSTimer`, 2 `MsnTimer_MinSec`, 3 `MsnTimer_MinSecCentsec_00`, 4 `MinSec_1Digit`. **VS_MainTV는 1** | `0x710314cf80` switch, writer 화면 init `0x71033d93a0` |
| +0x154, +0x158, +0x15c, +0x164 | | 리셋 때 2, 0xe10(3600), 0, 1 | 의미 **[미확정]** |
| +0x178 / +0x180 | char* / s32 | 텍스트 페인 이름 버퍼 | `T_Time_00` | |

표시 계산(`0x710314cf80` case 1·2·4):

```
if roundUp:  sec = time <= 0 ? 0 : (int(time) + fps - 1) / fps     // 정수 나눗셈
else:        sec = max(int(time) / fps, 0)
if sec != shownSeconds:
    텍스트 = MSBT CommonMsg/UnitName[형식 라벨]에 (sec / 60, sec % 60) 삽입
    shownSeconds = sec
```

case 3은 1/100초까지: `cs = floor(((time − sec×fps) / fps) × 100)`(음수 보정 포함). 대전 화면은 init에서 형식 1(`VSTimer`)을 직접 씁니다 **[판독]**.

**타이머 공급** (2026-10-02 [gauge], 이전 "줄이는 쪽 미확정") `0x7103096214` **[판독]**:

```
obj = this+0x38 (규칙 타이머 객체; 없으면 화면 타이머 0, +0x431 = 0)
left = obj+0x50 == INT_MIN ? 0x7ffff : max(obj+0x50 − max(GameFrame(*0x710580e758 +0x148), 0), 0)   // 프레임
VS_MainTV_00 화면이 있고 UI 관리자 상태(+0x4c8 & 0xff)가 2·4가 아니면:
    타이머+0x431 = obj.vt[0xa8]()                         // 연장 표시 여부로 추정
    타이머+0x140 = (float)max((int)(float)left, 0)
    +0x431 이면 타이머+0x138 핸들(GaugeExtend 추정)을 코드 4, 프레임 = clamp01(1 − obj.vt[0xb0]()) × 길이
left > 0 이고 left < 600(10초): Cmn_CountDownFinish_00 화면에 (left/60 + 1) 전달 (0x710327121c), 3이 되는 순간 0x71027b06b0(…, 7)
left/60 + 1 == 60(남은 59초대 진입): Cmn_InterimAnnounce_00 재생(vt+0x2b0), 0x71027b06b0(…, 6) — 한 번만(this+0x28 기억)
```

- 표시 = `ceil(left/60)`초(올림). 예: 남은 10800프레임 → 3:00, 10799 → 3:00, 1 → 0:01, 0 → 0:00 **[재구현]**.
- 시작 값: `0x71030b63dc`가 규칙 변수 `InGameFrm`에 경기 설정(…+0x6548)+0xa0 × 60을 넣고 타이머에 같은 값을 씁니다 **[판독]**. 종료 프레임(obj+0x50)의 writer는 **[미확정]**.
- `0x71027b06b0`의 인자 6/7은 BGM·사운드 단계로 추정 **[추정]**.

## 5. 칠한 포인트 `PaintNumbers_00` [판독 + 데이터]

- `PaintNumbers_00` = `L_Number_00..03`(각 `PaintNumber_00` 파츠, 오른쪽 자리부터 x 0, −37.5, −75, −112.5) + `T_Unit_00` "p".
- `PaintNumber_00`(컨트롤 `SplNumberAnim`) = 숫자 띠 텍스처 한 장. 애니 `Number`(30프레임): 재질 FLTS로 V 오프셋을 3프레임마다 0.1씩(숫자 하나) 옮기고, 그 사이 FLPA y 0→3→0으로 살짝 튄다.
- 값 설정 `0x710275f124(n)`(기준: 화면+0x3e8 컨트롤 `C`):
  ```
  C+0x140 = n
  if 화면+0x61c != 0:                      // 숫자 애니 사용
      C+0x158 = double(n × int(자릿수0 애니 프레임 수 / 10))
      for i in 0..자릿수-1:
          d = (n / 10^i) % 10
          f = (프레임수_i / 10) × d   (0..프레임수로 감쌈)  → 자릿수 i 애니를 코드 4(고정)로 f에
          if i < C+0x13c(최소 자릿수) or n >= 10^i: 표시(비트 i 켬, 코드 6)
          else: 숨김(코드 7, 끝 프레임)
      C+0x144 = C+0x148 = n
  ```
- 입력 n = `(s32)((f32)u32 플레이어정보+0xbd4 / 211.2f)`(HUD 관리자 `0x710275c1ac`). 211.2 = 64(8×8 텍셀) × 3.3(평)로 [paint]가 같은 상수를 결과 집계에서 확인했습니다([paint/paint_and_score.md](../paint/paint_and_score.md)).

## 6. 팀 아이콘 `TGPlayerIcon_00` ×8 (기준: 아이콘 = `SplUITGPlayerIconCtrl`) [판독 + 데이터]

### 6.1 레이아웃·애니

페인: `P_PlayerIconSh_00`(그림자), `N_PlayerIcon_00/P_PlayerIcon_00`(오징어 얼굴), `P_PlayerIcon_03`(이탈), `P_PlayerIcon_01`, `N_Special_00`(특수 준비 링 2장), `L_WpnPath_00`(무기 아이콘 파츠), `N_Death_00`(× 표시 막대 2개), `N_Ikura_00`, `L_Key_00`, `N_Attention_00`, `N_Watch_00`(관전용 킬·특수 수 "88").

| 애니(핸들 오프셋) | 프레임 | 내용 |
|---|---|---|
| Normal (+0xe8) | 0 | 얼굴·그림자·무기 표시, 이탈·×표 숨김 |
| Special (+0xf0) | 50–51 | `N_Special_00` 표시(프레임 1) / 숨김(0) |
| GoldIkuraGet (+0xf8) | 150–158 | 연어런 |
| Down (+0x100) | 180–193 | × 막대가 양쪽에서 날아와 교차(위치·배율 키) |
| Absent (+0x108) | 202 | 얼굴 숨김, `P_PlayerIcon_03` 표시, 무기 숨김 |
| Attention (+0x110) | 210–214 | |
| OctaType (+0x118) | 300–301 | 문어 텍스처로 바꾸기(FLTP) |
| Watch (+0x120) | 400–401 | `N_Watch_00` 표시(0) / 숨김(1). 리셋 `0x71031eb1a8`이 코드 7(끝 프레임)로 숨김 |
| Asari (+0x128) | 0–8 | 아사리 |
| (Pinch) | 100 | 아이콘 파츠의 Pinch 애니. 목록에 없음 — 다른 곳에서 재생 **[미확정]**. 화면 상단 "위험해!" 말풍선(`N_PlayerPinch_00`)과는 별개이며 말풍선은 §7 참고 |

### 6.2 상태 선택 `0x71031eaac8` (vtable 슬롯 14)

입력 `D` = 이 아이콘 슬롯 플레이어의 정보 블록(플레이어 목록 항목 → … → +0x20 객체 → +0x108, HUD 관리자와 같은 경로).

```
if 슬롯 무효 또는 플레이어 객체 없음:  state = 2 (Absent), special = false
elif D+0xd60 < 1 && D+0xde0 < 1 && D+0xdf0 < 1 && D+0xe0c < 1 && D+0xe58 == 0:
    absent = D+0xe59 != 0
    other  = (D+0xa7c0 → +0xeec) != 0
    if !absent && !other:
        state = 0 (Normal)
        special = D+0xbe4 >= 1.0 && (D+0xa650 → +0x37) == 0 && D+0x938c != 0
    else: state = absent ? 2 : 1, special = false
else:  state = (D+0xe59 != 0) ? 2 : 1 (Down), special = false
if 연어런 관리자(전역 0x71057985e0) 있음: special 대신 GoldIkuraGet 처리
state 바뀌면: 새 상태 애니 = 코드 1(처음부터 재생), 나머지 둘 = 코드 10
special 바뀌면: Special 애니를 코드 4로 프레임 1.0/0.0 고정
```

필드 의미: +0xbe4 = 특수 게이지 비율([ui_hud.md](ui_hud.md) §3), +0xd60/+0xde0/+0xdf0/+0xe0c = 0보다 크면 Down이 되는 카운터(사망·리스폰 대기 등으로 추정), +0xe59 = 이탈 **[추정 — reader만 확인, writer 미확인]**.

## 7. 우세·리드 표시 [판독, 화면 의미는 추정]

[paint]가 확인한 심판 객체 `VersusRefereePaint`(슬롯 19 `0x7103042394`)가 두 팀 칠 비율 차이를 0~4 단계로 나눠 화면 `+0x4c8`에 넣습니다(diff ≥ 1501 → 0, ≥ 1001 → 1, −1000~1000 → 2, −1500~−1001 → 3, < −1500 → 4). 화면 갱신 `0x71033dbacc`:

```
s = 화면+0x4c8, prev = 화면+0x4cc
idx = (내 팀 플래그 *(…+0xf4) != 0) ? s : 4 − s        // 팀 시점 뒤집기
if 화면+0x240 == −1:
    if 새 idx > 이전 idx:  핸들[idx+3] = 코드 1, 속도 +1  (TerritoryGauge_xx 정방향)
    elif 새 idx < 이전 idx: 핸들[idx+4] = 코드 1, 속도 −1 (역방향)
    else:                   핸들[idx+3] = 코드 7 (끝 프레임)
리드 상태 화면+0x4d0 이 바뀌면 (특정 모드에서): 0 → PlayerLead 재생, 1 → OppositeLead 재생, 그 외 → PlayerLead 코드 6
화면+0x4cc = s, +0x4d4 = +0x4d0
```

`TerritoryGauge_00..03`은 팀 아이콘 8개의 위치·배율을 −20~20 구간 프레임으로 옮깁니다(우세한 쪽 아이콘이 커지거나 밀림). 리셋값 `+0x4c8 = +0x4cc = 2`(동률).

팀 시점 뒤집기의 플래그 `*(*0x7105791bd0 + 0xf4)`는 같은 함수의 `+0x4e9` 분기에서 `< 2`일 때 팀 인덱스로 쓰입니다 **[판독]**. 이를 내 팀 번호(0 Alpha, 1 Bravo)로 보면 idx = Alpha면 `4 − s`, Bravo면 `s`, 즉 **idx = "내 팀이 얼마나 앞서는가"(0 = 크게 뒤짐, 4 = 크게 앞섬)** 입니다 **[추정 — 플래그 의미]**. 아래 Pinch 결과도 이 해석과 맞습니다(내 팀이 뒤질 때 우리 쪽에 "위험해!"). `TerritoryGauge_k`는 단계 k ↔ k+1 전환 애니입니다.

**"위험해!"(Pinch) 말풍선** — 코드가 아니라 TerritoryGauge 애니 데이터가 켭니다 **[데이터 + 판독]** (2026-10-02 [gauge], 이전 [미확정]):

| 애니 | 페인 | 키(애니 로컬 프레임: 알파) | 결과 |
|---|---|---|---|
| TerritoryGauge_00 (단계 0↔1) | `N_PlayerPinch_00` | 0: 255 → 5: 0 | idx 0(내 팀이 15.01% 이상 뒤짐)이면 우리 쪽 "위험해!" 보임, 1로 오르면 0~5프레임에 사라짐 |
| TerritoryGauge_03 (단계 3↔4) | `N_OppositePinch_00` | 5: 0 → 10: 255 | idx 4(내 팀이 15.01% 이상 앞섬)이면 상대 쪽 "위험해!" |
| 01, 02 | 둘 다 | 알파 0 고정 | 나머지 단계에서는 숨김 |

- 기준 차이: 심판 만분율 차 ≥ 1501(= 칠 가능 전체 면적의 15.01%p) **[판독]**, [paint_and_score.md §4.3](../paint/paint_and_score.md).
- `N_LeadAll_00` x는 단계마다 15씩 이동(30 → −30) **[데이터]**.
- 같은 페인을 다른 애니가 덮어쓰지 않는지(예: In/Out)는 확인하지 않았습니다 **[미확정]**.

## 8. 함께 쓰는 다른 화면

| 화면 | 근거 | 상태 |
|---|---|---|
| `Cmn_NoInk_00`(`SplUICmnNoInk00Screen`, GameCommon, SortKey 3050) | 레이아웃: `N_Window_01`(180×67 창) + `N_Icon_00..03` + `T_NoInk_00/01`, 애니 In/Out/Loop/FrameIn/Type. MSBT `000` "잉크 부족!" | 2026-10-02 [paintgpu] 갱신 — **진입점이 둘 [판독]**: ① `0x7100feb5c4(종류)` → 화면 `0x7103276e2c`(종류를 +0x26c에, +0x270 = 1; 종류 0·3·4별 애니 분기). 직접 호출 20여 곳(슈터 잉크 액션 `0x71025856c8`, 0x710254d018, 0x710255341c, 0x7102572a24, 0x7102578c34, 0x71025afe10, 0x71025b2928, 0x710268e1d0/0x7102690990, 0x7102491e54, 0x710249f494, 0x71024bcc00 등). ② `0x71024f023c`(+0x264/+0x268 = 0 → vt+0x2c8; 그 동작이 표시인지 닫기인지 **[미확정]**), 호출자는 `0x71024eb9b8` 하나. "잉크 부족!"(`000`)은 종류 0으로 추정 **[추정 — 라벨 번호와 종류 값 대응]**; `002` 꼬마연어 필요!·`003` 사용 불가·`004` 연어알 부족!은 연어런 계열.<br>**슈터 메인 무기 [판독]**: 발사 처리 `0x7102583008` → `0x71025856c8`: `ok = 0x7102492120(소비량, 본체+0x698(잉크량), 본체+0xa8d0, 0, 1)`; ok면 끝. 아니면(부족) 본체+0x1058 == 0일 때 `0x7100feb5c4(0)`, 그리고 `본체+0x6ac = max(요청+0x60, 30)`(재표시 억제·탱크 점멸 타이머로 추정).<br>**`0x71024eb9b8` 경로 [판독]**: 입력 바이트 `[0] != 0 && [2] == 0`(던지기 시도로 추정)이고, (a) 특수 모드 플래그(`*0x710580e340`+0x143d0) 꺼짐: 규칙 심판이 클래스 B(vtable 0x71056a98e0, 타입 ID 0x7105896408)이고 `0x71024ecbd8` 참(표 `*0x7105851928`+0x57f8+번호×0x118 의 +0x54 > 0 또는 +0x50 > 0, 소지물 수로 추정) → ②, 거짓 → `0x7100feb5c4(1)`; (b) 플래그 켜짐: `0x71024ecbd8`(표 `*0x7105852068`+번호×0x238+0x270 > 0) 참이고 본체+0xa460~+0xa463 중 하나가 0이 아니거나 `0x71024ecd2c`(잉크 충분 검사 0x7102492120) 참 → ②, 아니면 `0x7100feb5c4(0)`. 함수가 `GoldenIkura` 액터를 다루므로 연어런·가치 매치 소지물 던지기 경로로 보며, 클래스 B가 어떤 규칙인지·각 값의 의미는 **[미확정]** |
| 잉크 탱크 | `spl::InkBar`, `spl__InkBarParam`, `spl::InkBarBaseModelDisplayType` 문자열 → 대전 잉크 탱크는 **2D 레이아웃이 아니라 등의 3D 모델**로 보임 | [graphics]/[player] 영역 **[추정]** |
| `VS_ReadyGo_00`(SortKey 5000, DrawUnit 3), `Cmn_CountDownFinish_00` | 시작·종료 연출 | 이번 범위 밖 |
| `VS_ResultMeter_00`(Versus, SortKey 4000) | 승패 무늬 + `L_Meter_00`(ResultMeter_00 파츠, 컨트롤 `Locater`), MSBT "우리 팀"/"상대 팀"/"WIN!"/"LOSE…" | 값: 나와바리는 팀 {PaintPoint, PaintPermille}, 가치 매치는 100 − 남은 카운트. 화면 `0x71033ec210`, 컨트롤 `SplUIResultMeter00Ctrl` `0x71031a2ccc`(동률 +1, 미터 분할 프레임 = 내p/합×10, 카운트업) **[판독]** — [special_gauge.md §6.8~6.9](../paint/special_gauge.md). **% 문자열(해소, [paintgpu]) [판독]+[데이터]**: `0x71031a3188`이 `T_PlayerPercent_00`/`T_OppositePercent_00`에 `CommonMsg/UnitName:PaintPercent` = `[2:0:00020000].[2:0:01010100]%`(인자 ‰/10, ‰%10 → "52.3%"), `T_PlayerNumUnit_00`/`T_OppositeNumUnit_00`에 `PaintPoint` = `[2:0:00040000]p` |
| 미니맵 `VS_MapAnnounce_01`(MiniMap), `MapIcon_00`, `VS_MapLine_00` | | 미분석 |
