# UI·HUD — 대전 HUD(VS_MainTV_00)와 특수 게이지 값 바인딩

2026-10-02, 갱신 2026-10-03([r5 ui] 사격장 화면). 상태: **분석 진행**(특수 게이지 경로는 데이터→화면→게임 값까지 판독, 웹 구현 없음). 게임 값 쪽(게이지 비율 writer·넷 %)은 [gauge] 담당이 원본 명령 구간을 unicorn으로 실행해 확인했습니다([../paint/special_gauge.md](../paint/special_gauge.md) §10). 화면 쪽 원본 실행은 애니 핸들 명령(§5.3), 표시 min 규칙(§6.4), 잉크 부족 화면(§5.5)입니다.

사격장(대전 로비 `Lby_Lobby00` 1인 연습)에서 실제로 보이는 HUD는 **§1.1**에 따로 정리했습니다. 대전 화면 `VS_MainTV_00`은 사격장 씬에서 적재되지 않습니다.

하위 문서:
- [ui_layout_format.md](ui_layout_format.md) — blarc/BFLYT/BFLAN v9 차이점, 사용자 셰이더·FLEU, UIScreen·LayoutArchiveCategory, 폰트·MSBT, 변환 절차
- [ui_vs_maintv_elements.md](ui_vs_maintv_elements.md) — VS_MainTV_00 배치, 화면 애니 50개, 타이머·칠 포인트·팀 아이콘·우세 표시
- [ui_minimap.md](ui_minimap.md) — 대전 맵(X 맵·슈퍼점프 맵): 맵 카메라·정사영·월드→맵 좌표·착지점 후보·VS_MapAnnounce_00/01·VS_MapLine_00 ([camui])

확정 수준: **[실행]** 원본 실행(이 문서에는 §5.3 애니 핸들 명령·적용 순서 에뮬, §5.5 잉크 부족 화면 에뮬), **[판독]** 원본 명령/디컴파일 판독, **[데이터]** 데이터 확인, **[추정]**, **[미확정]**. 자체 도구로 돌린 결과는 **[실행: 자체 도구]**, 판독을 옮긴 계산은 **[재구현]**으로 따로 적습니다. 주소는 main NSO를 0x7100000000에 올린 기준입니다.

---

## 1. 기능 개요

대전 중 화면 위쪽의 HUD 한 장이 `VS_MainTV_00` 레이아웃(화면 클래스 `SplUIVSMainTV00Screen`)입니다. 보이는 요소는 다음과 같습니다.

| 요소 | 위치 | 게임 값 | 이 문서 |
|---|---|---|---|
| 남은 시간 "3:00" | 위 가운데 | 타이머 프레임 → 초 | [elements §4](ui_vs_maintv_elements.md) |
| 팀 아이콘 4+4 (생존/×/이탈, 특수 준비 링) | 위 가운데 양쪽 | 플레이어별 상태·특수 비율 | [elements §6](ui_vs_maintv_elements.md) |
| 우세 기울기·"리드!"·"위험해!" | 아이콘 묶음 | 팀 칠 비율 차이 단계 | [elements §7](ui_vs_maintv_elements.md) |
| **특수 게이지**(원형 270° 호, 가득 차면 "풀 충전!"·누르기 안내) | 오른쪽 위 | 관전 대상 플레이어의 특수 비율 | **§3~§6 (끝까지 추적한 화면 요소)** |
| 칠한 포인트 "1234p" | 게이지 왼쪽 | 플레이어 도색 텍셀 ÷ 211.2 | [elements §5](ui_vs_maintv_elements.md) |
| 시그널/나이스 | 왼쪽 아래 | 십자키 | 이번 범위 밖 |

잉크 탱크는 2D HUD가 아니라 등에 멘 3D 모델로 보이고, 잉크가 모자랄 때 뜨는 "잉크 부족!"은 별도 화면 `Cmn_NoInk_00`입니다(§5.5) **[데이터]+[판독]**.

정정(2026-10-03 [r5 ui]): 이전 판은 탱크 모델을 `spl::InkBar`로 보았습니다 **[추정]**. 데이터를 보면 플레이어 탱크는 액터 `PlayerTank`(`Pack/Actor/PlayerTank.pack.zs`: Behavior `spl::PlayerCustomTank`, 모델 `Work/Model/Weapon/Tnk_Simple`, AS `PlayerTank.root.asb`)입니다. `spl::InkBar`는 `ObjParent`를 상속한 스테이지 오브젝트(`InkBar.pack.zs`: 모델 `Obj_InkBar_Octa`, DamageHelperParam·Physics)라 탱크가 아닙니다 **[데이터]**. 2D 잉크 게이지 페인은 `CoopInkGauge_00`, `Coop_MainTV_00`(`L_InkGauge_00`), `MsnGauge_00`에만 있어(전 348개 bflyt 검색) 대전·사격장에는 2D 잉크 게이지가 없습니다 **[데이터]**.

### 1.1 사격장(`Lby_Lobby00`) 화면에 보이는 HUD [데이터 + 판독] (2026-10-03 [r5 ui])

사격장은 `LobbyVersus` 씬(`Pack/Scene/LobbyVersus.pack.zs`, StartupMap `Lby_Lobby00`)입니다. 씬의 Sequence `LobbyVersus.game__SequenceComponentParam`(`Pack/Bootup.Nin_NX_NVN.pack.zs`)이 레이아웃 묶음을 정합니다 **[데이터]**.

| 구분 | 레이아웃 묶음(`LayoutArchiveCategory`) |
|---|---|
| LoadSyncCategories | `XMenu`, `Customize`, `GameCommon`, `LobbySync`, `News`, `Narration`, `StageSelect` |
| LoadAsyncCategories | `Lobby`, `TalkWin`, `FestRegion`, `Takeover`, `MiniMap`, `Manual` |

`VersusSync`(`VS_MainTV_00`, `Timer_00`, `TGPlayerIcon_00` 등)는 목록에 없으므로 **사격장에는 대전 HUD(타이머·팀 아이콘·칠 포인트·우세 표시)가 없습니다** [데이터]. 사격장 1인 연습 화면에 나오는 HUD는 다음과 같습니다.

| 요소 | 레이아웃(묶음) / 출처 | 게임 값·조건 | 상태 |
|---|---|---|---|
| 특수 게이지 + 안내 버튼 + 플레이어 상태 | `Lobby_GuideBtn_00`(LobbySync, `SplUILobbyGuideBtn00Screen`, SortKey 3000). 파츠 `L_SuperGauge_00` = `SuperGaugeTV_00`(위치 (816.75, 418.77), 대전 (825, 423)), `L_PlayerStatus_00` = `PlayerStatus_00`, `L_GuideBtn_00~02` = `PauseText_00`, `N_Signal_00` | 게이지는 대전과 같은 디스패처 `0x710342eb10`가 화면+0x278에 씀(§3, §5.4) | [판독]+[데이터] |
| 잉크 부족 "잉크 부족!" | `Cmn_NoInk_00`(GameCommon, SortKey 3050) | 슈터 발사 시 잉크 검사 실패(§5.5) | [실행]+[판독] |
| 잉크 잔량 | 2D 없음. 3D 탱크 `PlayerTank` | 잔량 → 표시 식은 [gfx_char] 영역 | 표시 식 [미확정] |
| 조준점·히트마커 | 레이아웃이 아니라 **이펙트**: ELink 사용자 `PlayerShotGuide`(`spl::PlayerShotGuideXLink`, vtable `0x710563e670`). 슈터: `Shooter_Center_NoHit` → `WpShtrSite`, `Shooter_Center_HitEffective`·`HitConstant` → `WpShtrSiteHit`, `Shooter_HitMarker_HitEffective` → `WpShtrHitMarker`, `Shooter_HitMarker_HitConstant` → `WpShtrFieldHitMarker`, `Shooter_Bias{Left,Right}_*` → `WpShtrHitMarkerSide`/`WpShtrSiteSide`(`analysis/effect_sound/elink2_users.json`) | 상태 이름 표 `0x710267e51c` = `NoHit, HitConstant, HitEffective, HitBombDead, HitKebaInkCore, ChargeKeep`, 방출 `0x7102677578`(슈터 호출 `0x710258683c`). 상태 결정·위치·발생/종료 조건은 [r5 combat] 진행 중 | 연결 [데이터], 조건 [미확정] |
| 표적 데미지 숫자 | `Shr_Points_00`(GameCommon, SortKey 1000, `T_Num_00` BlitzBold_L) | [range](../range/shooting_range.md) §6.4 | 로직은 [range] |
| 잉크 리셋 연출 | `Shr_InkReset_00`(Lobby, SortKey 10000, DrawUnit 3, 1920×1920 `P_Collor_00`) | 시퀀스 노드 `SplLobbyInkReset` | 호출 조건 [미확정] |
| 행동 안내 "A" 표시 | `Cmn_GuideActionPoint_00`(GameCommon) | NPC·물건 근처(호출 `0x710247a5f8` 등) | 이번 범위 밖 |

- 범위 화면의 `lyt1` 크기는 모두 **1920×1080, drawFromCenter 1**입니다. 전 348개 bflyt 중 333개가 1920×1080, 14개(아이콘 파츠)가 1280×720, `Lobby_CapScreen_00` 하나가 350×135입니다 [데이터]. 레이아웃 좌표는 1920×1080 가상 화면의 중심 원점 기준(drawFromCenter)이고 Y 위쪽은 nn::ui2d 관례로 본 것입니다 [추정]. 실제 출력 해상도(도킹 1920×1080 / 휴대 1280×720)로 바꾸는 투영 코드는 읽지 않았습니다 [미확정].
  - 2026-10-03 [r6 ui] 보강 [판독, 부분]:
    - `Layout::Build`(`0x7100857748`)가 `lyt1`+0xc/+0x10을 레이아웃+0x28/+0x2c(폭·높이 f32)에, `lyt1`+0x1c(레이아웃 이름)의 주소를 +0x30에 넣습니다. `lyt1`+8(drawFromCenter 바이트)은 레이아웃 객체에 복사하지 않습니다.
    - 레이아웃 사각형 함수 `0x7100859058`은 drawFromCenter와 관계없이 항상 `left = −w/2, top = h/2, right = w/2, bottom = −h/2`(중심 원점, Y 위쪽)를 돌려줍니다.
    - 레이아웃 단위를 화소로 바꾸는 곳이 두 군데 있습니다. 두 곳 모두 그리기 정보(+0xc0 = Layout, +0x1a0 = 현재 렌더 타깃)에서 **배율 = 렌더 타깃 크기 / 레이아웃 크기**를 축마다 따로 씁니다.
      - 캡처 크기 `0x71038e8728`: 화소 폭 = (|전역 배율×페인 폭| + 여백) × RT 폭(+0x38 u16) / 레이아웃 폭(+0x28), 높이도 같은 방식.
      - 가위(Scissor) 페인 그리기 `0x71038e9e10`: 배율 = RT(+8, +0xc) / 레이아웃(+0x28, +0x2c). 그리기 정보 +0x1a0+0x28 플래그가 켜져 있으면 1.0.
    - 그러므로 1920×1080 가상 화면 전체가 렌더 타깃 전체에 축별 균등 배율로 놓인다고 읽힙니다 [판독: 위 두 소비처].
    - 본 그리기 투영 행렬을 만드는 함수는 아직 찾지 못했습니다. `nn::ui2d::DrawInfo` vtable `0x710541a010`은 저장하는 곳이 없습니다. 코드·데이터에 f32/u32 1920·1080 상수 쌍도 없습니다.
    - UI 렌더 타깃의 실제 크기(도킹/휴대별)는 런타임 값이라 [미확정]입니다. 다음에 볼 곳: 그리기 정보 +0x1a0 writer.
- 사격장 `Lobby_GuideBtn_00`의 갱신(`0x71032ba75c`)은 관전 대상 본체의 +0xd60/+0xde0/+0xdf0/+0xe0c(쓰러짐 계열, >0)으로 시그널 문구(`T_Signal_00` = `000`/`001`)를 바꾸고, +0xbf0>0(스페셜 사용 중) 등이면 안내 버튼을 숨깁니다 [판독]. 필드 writer는 [life] 영역입니다.

## 2. 분석 대상과 자료

| 항목 | 위치 |
|---|---|
| 원본 | `original/Splatoon 3 [0100C2500FC20000][v0].xci` (읽기 전용), 추출물 `extracted/` |
| 레이아웃 | `extracted/romfs/Layout/{VS_MainTV_00, SuperGaugeTV_00, Timer_00, TGPlayerIcon_00, PaintNumbers_00, PaintNumber_00, Cmn_NoInk_00 …}.Nin_NX_NVN.blarc.zs` |
| 덤프 | `analysis/ui/layout/<이름>/` (19개), `analysis/ui/msbt_KRko/`, `analysis/ui/tex/`, `analysis/ui/font/`, `analysis/ui/render/` |
| 디컴파일 | `analysis/decomp/ui/hud_batch1.c`(화면·게이지·타이머·아이콘·TraceGauge 47개), `hud_batch2.c`(HUD 관리자·디스패처 11개), `hud_batch3.c`(타이머 표시·NoInk 8개) |
| 재구현 검증 | `analysis/ui/hud_sim.py` → `analysis/ui/hud_sim_out.txt` |
| 사격장 화면(2026-10-03) | 씬 해제 `analysis/r5_ui/scene_LobbyVersus/`, Bootup 해제 `analysis/r5_ui/bootup/`, 레이아웃 덤프 `analysis/r5_ui/layout/{Lobby_GuideBtn_00, Shr_Points_00, Shr_InkReset_00, Cmn_GuideActionPoint_00, Cmn_GuideBtn_00, Cmn_PlayGuide_00, Cmn_Pause_00, HoldText_00, CmnIconSubSpecial_00}/` |
| 디컴파일(2026-10-03) | `analysis/decomp/r5_ui/screens1.c`(화면 찾기·NoInk 요청), `range_screens.c`(NoInk 갱신·기본 화면 상태 질의·Lobby_GuideBtn_00 init/reset/갱신), `usd_keys.c`(사용자 데이터 키), `ui2d_cbuf.c`(재질 상수 버퍼), `frameflag.c`(dt 플래그), `shotguide.c`(PlayerShotGuideXLink) |
| 원본 실행(2026-10-03) | `web/tools/r5_ui_noink_emu.py` → `analysis/r5_ui/noink_emu.json`, `web/tools/r5_ui_fleu_names.py`(데이터 전수) |
| 보조 스캔 | `analysis/ui/scan_*.py`(필드 저장 위치 전역 스캔), `web/tools/ui_blcallers.py`, `web/tools/ui_funcs_in_range.py` |
| 6차(2026-10-03 [r6 ui]) | 디컴파일 `analysis/decomp/r6_ui/batch1.c`(프레임워크 그리기·calc, 씬 시작, 메시지 찾기), `batch2.c`(게임 TagProcessor 글자 배치, 캡처 크기). 도구 `web/tools/r6_ui_lib.py`(공용: vtable 칸·BL 검색·unicorn·libc PLT 대체), `r6_ui_fps30_emu.py`, `r6_ui_msbt_num_emu.py`, `r6_ui_rectscan.py`, `r6_ui_constscan.py`. 데이터 `analysis/r6_ui/{Tag.json, SceneInfo.json, decide_xref.txt, fps30_emu.json, msbt_num_emu.json}` |

## 3. 진입점과 전체 호출 흐름

```
[매 프레임, 게임 쪽]
 HUD 관리자 갱신 0x710275c1ac                                   (spl::Spectator 슬롯 21 [판독], 2026-10-03)
   ├─ 관전 대상 인덱스 i = 관리자+0x27c (음수면 대상 없음)
   ├─ 플레이어 목록 관리자+0x110[i] → 항목+8 → +0x80 → +0x208 컴포넌트 배열[0 또는 24] → +0x20 = 플레이어 객체 P
   │     (sead RTTI 검사 0x710164b2d8, 전역 형 0x71058bc2e0)
   ├─ D = P+0x108 (플레이어 본체: vtable 0x7105632a60, 0xac80 B, 생성 0x710245717c. 클래스 이름은 바이너리에 없음 — §4.1)
   ├─ 게이지 화면이 열려 있는가: 존재 플래그 순서대로 첫 화면 하나만 본다 [판독]
   │     0x71058e877c(VS_MainTV_00) → 0x710342e8e0 / 아니면 0x71058e87ac(Lobby_GuideBtn_00) → 0x7102dd2474
   │     / 아니면 0x71058e87a4(Coop_MainTV_00) → 0x7102d2f794 / 아니면 0x71058e8784(Msn_MainTV_00) → 0x710342e9f8
   │     (각 함수 = 이름으로 화면 찾기 + 화면 vt+0x2d0 "열림"). 열려 있지 않으면 아래 게이지·칠 포인트 갱신을 건너뜀
   ├─ ratio = D+0xbe4 (f32)                                       ← 특수 게이지 비율 0~1
   ├─ key   = (int)D+0xbe8 + i*1000                                  ← D+0xbe8 = 필요 p(SpecialPoint, f32)
   ├─ showFullText = (ratio >= 1.0) && (관리자+0x3d8 == key)       ← 지난 프레임과 같은 대상·같은 카운터
   ├─ 0x710342eb10(showFullText, ratio)          ──────────────┐
   ├─ 0x710275f124( (s32)((f32)D+0xbd4 / 211.2f) )   칠 포인트   │
   └─ 관리자+0x3d8 = key                                         │
                                                                 ▼
 setSuperGaugeRatio 0x710342eb10                                 
   ├─ 활성 화면 고르기: VS_MainTV_00(전역 0x71058e877c) → Lobby_GuideBtn_00(0x71058e87ac) → Coop_MainTV_00(0x71058e87a4) → Msn_MainTV_00(0x71058e8784)
   ├─ 화면 = UI 관리자(전역 0x710599b7a0)의 화면 목록에서 이름 인덱스(0x7100f7694c)로 찾기 + 형 검사 + (관리자+0xc8 == 0)
   ├─ 게이지 G = 화면+0x3e0 (VS) / +0x278 (Lobby) / +0x2d0 (Coop) / +0x320 (Msn)
   ├─ v = ratio < 0 ? 0 : min(ratio, 1) × 75.0
   ├─ if 0 ≤ v ≤ G.frameCount(GaugeRatio): G+0x48 = v
   └─ G+0x1a8 = showFullText
                                                                 ▼
[매 프레임, UI 쪽]  (호출 순서 §5.3)
 SplUISuperGaugeCtrl 갱신 0x710317426c (vtable 슬롯 13)   — G+0x48 ≥ 75 / G+0x4c ≥ 75 변화로 Max·LoopMax·InText·OutText 애니
 TraceGaugeControl 갱신 0x71038d6748 (슬롯 4 → b)         — 값 G+0x4c ← G+0x48, 추적값 G+0x50 이동, 애니 프레임 쓰기
   └─ 0x71038d69bc: GaugeRatio.frame = N(1 − ·/N),  TraceRatio.frame = …   (N = 75)
 Layout 애니 적용(ui2d)                                    — Gauge 애니 FLEU → P_pict_00/02 의 __CUS_Float_0 = 0.75 × (1 − frame/75)
 그리기                                                    — 재질 사용자 셰이더 "MeterAction"(GaugeSp_00 270° 호)이 __CUS_Float_0 만큼 호를 드러냄
```

| 함수 | 주소 | 근거 수준 |
|---|---|---|
| HUD 관리자 갱신 | `0x710275c1ac` (안쪽 `0x710275d758~0x710275dd9c`) = `spl::Spectator`(vtable `0x7105646650`, 46슬롯, getName `0x7102759f08`) 슬롯 21 | [판독] (클래스: 2026-10-03, vtable 역추적) |
| 화면 활성 확인(VS/Lobby/Coop/Msn) | `0x710342e8e0`, `0x7102dd2474`, `0x7102d2f794`, `0x710342e9f8` | [판독] |
| 사격장 게이지 화면 init | `Lobby_GuideBtn_00` 슬롯 97 `0x71032ba20c`(§5.4) | [판독] |
| setSuperGaugeRatio | `0x710342eb10` | [판독] |
| 칠 포인트 표시 | `0x710275f124` | [판독] |
| SuperGaugeCtrl 갱신 / 초기화 | `0x710317426c` / `0x7103173c9c` | [판독] |
| TraceGaugeControl 초기화 / 갱신 / 프레임 적용 | `0x71038d64bc` / `0x71038d6748` / `0x71038d69bc` | [판독] |
| AnimTransform 생성(이름) | `0x71038db1d8` | [판독] |
| 화면 생성 / 초기화 / 리셋 / 갱신 | `0x71033de790` / `0x71033d93a0` / `0x71033d9f84` / `0x71033dbacc` | [판독] |

같은 0x710342eb10 경로를 쓰는 UI 시험 코드 블록이 `0x7100fe8750` 근처에 있습니다. 카운터(+0x2c)를 11400·720으로 나머지 연산해 0~240을 만들고 `min(x/240, 1) × 75`를 게이지에, `x/60×5`를 칠 포인트에 넣습니다. 게임 경로가 아니라 데모·디버그로 봅니다 **[추정]**.

정정(2026-10-03 [r6 ui]): 위 [추정]을 **[판독]+[데이터]**로 확정합니다. 이 블록은 개발용 UI 점검 시퀀스 `GameSeqUICheckGuide`의 것입니다.
- 정적 초기화 `0x7100fdf7c0`이 팩토리 표(`0x7105802d18` 목록)에 이름 `UniqueSequenceGameSeqUICheckGuide`와 생성 함수 `0x7100fdf994`를 등록합니다. 생성 함수가 0xaa8 B 객체를 만들고 vtable `0x7105551d60`을 넣습니다.
- vtable 슬롯 36 `0x7100fdfae4`는 현재 점검 대상 레이아웃 이름(+0xa98)을 `Cmn_Pause_00`, `Cmn_NoInk_00` … `VS_MainTV_00`과 하나씩 비교해 레이아웃별 점검 블록으로 갑니다. `0x7100fe0524`/`0x7100fe053c`가 `VS_MainTV_00` 일치 시 `0x7100fe8750`으로 분기합니다.
- 제품 씬 표 `RSDB/SceneInfo`의 SequenceName은 `Boot, Coop, DayChange, DevPortal, LobbyCoop, LobbyLocal, LobbyVersus, Mission, PlayerMake, Plaza, Shop, StaffRoll, TestMatchScene, Versus, World`뿐이고 `UICheckGuide`를 쓰는 행이 없습니다 [데이터].
- 따라서 사격장·대전 경로에서는 실행되지 않습니다. 개발 포털에서 여는 경로가 있는지는 범위 밖입니다.

## 4. 구조체·필드·상수

### 4.1 플레이어 정보 블록 D (= 플레이어 객체 P + 0x108이 가리키는 플레이어 본체)

D는 [player] 문서의 "플레이어 본체"(PlayerBehavior+0x108, vtable `0x7105632a60`, 0xac80 B)와 같은 객체입니다. 근거: 아이콘 갱신이 읽는 D+0xa650(→+0x37), D+0xa7c0(→+0xeec)이 본체 컴포넌트 표의 `spl::PlayerDemo`(+0xa650), `spl::PlayerCoopZombie`(+0xa7c0)와 맞고, 게이지 블록 writer가 본체 함수들(`0x7102483134` 등)입니다 **[판독]** (2026-10-02 [gauge], 이전 "클래스 미확인"). 본체 클래스의 이름은 **확정 불가**입니다(2026-10-03 [r5 ui]): vtable `0x7105632a60`은 슬롯 4개(`0x7102470418`, `0x71024705e4` 소멸자 계열, `0x710234b580` init, `0x710234f3ec`)뿐이고 getName 슬롯이 없습니다. 바로 뒤(+0x20~)는 함수가 아니라 액터 이름 문자열 표(`PlayerCoopFloat`, `PlayerRobe`, `PlayerBag`, `PlayerSpawner` …)입니다. main에는 게임 RTTI가 없으므로 이름을 담은 데이터가 없습니다. 웹 이름은 `PlayerBody`(권장)로 둡니다.

D+0xbd4..+0xc03은 스페셜 게이지 구조체 G입니다. 함수들이 `D+0xbd4` 포인터를 받아 G 기준 오프셋(+0x10 등)으로 쓰기 때문에, 이전의 "`str [x,#0xbe4]` 77곳" 스캔으로는 writer가 잡히지 않았습니다. 전체 표: [special_gauge.md §4.1](../paint/special_gauge.md).

| 오프셋 | 형식 | 의미(웹 권장 이름) | reader | writer |
|---|---|---|---|---|
| +0xbe4 (G+0x10) | f32 | `specialRatio` 0~1 | HUD 관리자, 아이콘 `0x71031eaac8`, 넷 송신 | 로컬: `0x7102483134`(매 프레임, 게이지 텍셀/필요 텍셀 또는 스페셜 중 남은/전체) / 원격: `0x7102475a54`(넷 % 복원) / 리셋·사망·스페셜 종료 **[판독]+[실행(에뮬 구간)]** |
| +0xbe8 (G+0x14) | f32 | `specialPoint` 필요 p(무기 SpecialPoint, 기본 200) | HUD 관리자(풀충전 키), 비율 계산 | `0x71024901c4`(무기 장착), 생성자 **[판독]** |
| +0xbd4 (G+0x00) | u32 | `paintTexels` 칠한 텍셀 | HUD 관리자, 결과 집계 | `0x7102483134`(매 프레임 += 칠 카운터 +4) **[판독]** |
| +0xbf0 (G+0x1c) | s32 | `specialFramesLeft` 스페셜 남은 프레임(>0 = 사용 중) | HUD 관리자(리플레이 경로), 아이콘(간접) | `0x7102483134`(매 프레임 −1), 스페셜 시작(미추적) |
| +0xd60, +0xde0, +0xdf0, +0xe0c | s32 | 하나라도 ≥1이면 아이콘 Down. 이 넷 또는 +0xd58이 >0이면 게이지 가산도 멈춤. 사격장 `Lobby_GuideBtn_00`은 이 값으로 시그널 문구 `000`/`001`을 바꿈(§1.1) | 아이콘, 게이지 가산(`0x7102485420`), `Lobby_GuideBtn_00` 갱신 `0x71032ba75c` | [미확정] ([life] 담당) |
| +0xe58, +0xe59 | u8 | +0xe59 = 이탈(Absent). 대전 팀 아이콘 전용(사격장 화면에 팀 아이콘 없음) | 아이콘 | [미확정], 사격장 범위 밖 |

정정(2026-10-02 [gauge]): 이전 판의 "+0xbe8 = `specialSerial`(풀충전 문구 판정용 카운터 추정)"은 틀렸습니다. +0xbe8은 필요 p이며, 키 `(int)필요p + 관전대상×1000`은 사실상 "같은 관전 대상인가"만 가릅니다(무기를 바꾸지 않는 한 필요 p는 그대로). +0xbf0도 "의미 미확정 s32"에서 스페셜 남은 프레임으로 바꿉니다: 리플레이 목록에 `+0xbf0 < 1`일 때만 `(int)(비율×100)`을 넣는 것은 "스페셜 사용 중이 아니면 %"라는 뜻입니다.

### 4.2 특수 게이지 컨트롤 G (`SplUISuperGaugeCtrl`, 0x1B0 B)

TraceGauge 공통 필드(+0x18~+0x74)는 다음 표, 게이지 전용 필드(+0x138~+0x1a8)는 [elements §3.3](ui_vs_maintv_elements.md).

| 오프셋 | 형식 | 원본 이름 | 웹 권장 이름 | 기본값(생성 @0x71031f04cc) | init(0x71038d64bc) 뒤 | writer / reader |
|---|---|---|---|---|---|---|
| +0x18 | char* | | `ownerName` | | 컨트롤 소속 이름 문자열 **[판독]** (2026-10-03 [r6 ui], 이전 `nameSource` [추정] 대체): 레이아웃 루트 페인(Layout+0x18)에 부모(페인+0x18)가 있으면 그 루트 페인의 이름(페인+0xb0, 파츠면 `L_SuperGauge_00` 같은 파츠 페인 이름), 없으면 Layout+0x30(레이아웃 이름 = `lyt1`+0x1c, `Layout::Build` `0x7100857b68`) | init |
| +0x20 | ptr | | `layout` | | `nn::ui2d::Layout*` **[판독]** (2026-10-03 [r6 ui], 이전 [추정] 대체): 컨트롤 생성기 `0x71038ce9d0`(인자 x1 = ControlSrc, x2 = Layout)가 TraceGauge 객체(0x78 B, 기본값 저장 후)를 init `0x71038d64bc`(x1 = ControlSrc, x2 = Layout)에 그대로 넘김. init이 +0x20 = x2를 맨 먼저 씀 | init |
| +0x28 | ptr | 기능 `GaugeRatio` | `animGauge` | | AnimTransform(`Gauge`) | init / 갱신 |
| +0x30 | ptr | 기능 `TraceRatio` | `animTrace` | | AnimTransform(`Gauge`) **새 인스턴스** | init / 갱신 |
| +0x38 | ptr | 기능 `TraceColor` | `animTraceColor` | 0 | 없음(이름 빈칸) | |
| +0x40 | ptr | 기능 `Shortage` | `animShortage` | 0 | 없음 | |
| +0x48 | f32 | | `target` | 100.0 | **75.0**(프레임 수) | 디스패처·리셋 / 갱신 |
| +0x4c | f32 | | `value` | 100.0 | 75.0 | 갱신 |
| +0x50 | f32 | | `trace` | 100.0 | 75.0 | 갱신 |
| +0x54 | f32 | `TracingSpeed` | `traceSpeed` | **2.0** | 사용자데이터 있으면 덮어씀 | init / 갱신 |
| +0x58 | f32 | `TracingFraction` | `traceFraction` | 0.0 | | |
| +0x5c | f32 | | `shortageLevel1` | 20.0 | | 갱신(Shortage) |
| +0x60 | f32 | | `shortageLevel2` | 0.0 | | 갱신(Shortage) |
| +0x64 | f32 | | `traceWaitLeft` | 0 | | 갱신 |
| +0x68 | f32 | `TracingWait` | `traceWait` | 0 | | |
| +0x6c, +0x70 | f32 | `TracingOnValueChange`[0..1] | `jumpFraction`, `jumpMin` | 0, 0 | | |
| +0x74 | u8 | | `traceEnabled` | 1 | | 갱신 |

`SuperGaugeTV_00`에는 레이아웃·컨트롤 수준 `Tracing*` 사용자 데이터가 없어 기본값이 그대로 쓰입니다(`P_Infinity_00` 페인의 `TracingFraction/Wait`는 페인 단위라 이 init이 읽는 위치가 아닙니다) **[데이터 + 추정: init이 읽는 대상(+0x18 레이아웃 사용자데이터, 이어서 컨트롤 cnt1 인자)]**.

### 4.3 TraceGaugeControl (0x71038d64bc / 0x71038d6748)

init이 하는 일 **[판독]**:
1. cnt1 기능 이름 `GaugeRatio`, `TraceRatio`로 레이아웃 애니 이름을 얻어 `0x71038db1d8(layout, 이름, 1)`로 **각각 새 AnimTransform(0x68 B)**을 만든다. 두 기능이 같은 `Gauge`를 가리켜도 인스턴스는 2개다.
2. 두 애니의 플래그 `anim+0x54 &= ~0x20`.
3. `target = value = trace = GaugeRatio 프레임 수`(u16→f32, SuperGauge = 75).
4. `TraceColor`, `Shortage` 이름이 비어 있지 않으면 같은 방식으로 만든다(SuperGauge는 없음).
5. `TracingSpeed`·`TracingFraction`·`TracingWait`·`TracingOnValueChange`(값 1~2개)를 레이아웃 사용자데이터(`0x710086ab98`)에서 먼저, 없으면 컨트롤 인자(`0x7100855a90`)에서 찾는다.

### 4.4 상수

| 값 | 쓰임 | 근거 |
|---|---|---|
| 75.0 | 비율 → 게이지 값 배율, 가득 참 판정 | 디스패처 `fmul … #75.0`, SuperGauge 갱신 `75.0 <= …` [판독]; `Gauge` 애니 프레임 수 75 [데이터] |
| 0.75 | Gauge 애니 frame 0의 `__CUS_Float_0` (= 270°/360°) | bflan 키 [데이터], 텍스처 호 270° [데이터] |
| 2.0 | TracingSpeed 기본(값 단위/프레임) | 생성자 상수 `0x4000000042c80000` @0x71031f04f0 [판독] |
| 211.2 | 텍셀 → p | `0x43533333` @0x710275dd94 [판독], [paint]와 일치 |
| 10800.0 | 대전 타이머 리셋(프레임) | `0x4628c000` @화면 리셋 [판독] |
| 60, 1 | 타이머 fps(+0x14c), 올림(+0x148) | SplUITimerCtrl 생성자 `0x710314cc9c` [판독] |
| 1000 | 풀충전 판정 키의 대상 인덱스 배수 | `madd w21, w9, #1000, w11` @0x710275d818 [판독] |

## 5. 상태 전이와 수명

### 5.1 화면 수명

| 단계 | 함수 | 하는 일 |
|---|---|---|
| 생성 | `0x71033de790` (팩토리 vtable 슬롯 3) | 0x620 B 할당, vtable `0x710570f290`, 내부 리스트·상태 초기화 |
| 초기화 | `0x71033d93a0` (슬롯 97) | 애니 핸들 50개, 컨트롤 포인터(+0x3e0 게이지, +0x3e8 칠 포인트, +0x450 타이머 + 형식 1, +0x458 일시정지 문구) |
| 리셋/진입 | `0x71033d9f84` (슬롯 98) | 게이지 `+0x48 = 0`(빈 게이지), `+0x1a8 = 0`; 칠 포인트 0; 타이머 `+0x140 = 10800.0`; 우세 `+0x4c8 = +0x4cc = 2`; Watch·TerritoryGauge·Lead 애니 정지 |
| 갱신 | `0x71033dbacc` (슬롯 100), `0x71033db1b8`(102) | 우세·리드 애니, 규칙별 카운터 |
| 해제 | `0x71033de674` 등 | — |

리셋 직후 게이지는 `target = 0`, `value·trace = 75`입니다. 첫 갱신에서 `value = 0`이 되고, 추적값은 2.0/프레임으로 75 → 0까지 38프레임 걸려 내려갑니다. 화면에 보이는 값은 §6.4 규칙에 따라 0부터 바로 0으로 보입니다 **[재구현]**.

### 5.2 가득 참 연출 (0x710317426c)

`target != value`인 프레임(= 디스패처가 값을 바꾼 직후, TraceGauge 갱신이 value를 따라가기 전)에만 판정합니다.

```
if target != value:
    if target >= 75:                                   // 이번에 가득 참
        Max: 코드1(처음부터, 속도1)      LoopMax: 코드3(현재 프레임부터 재생)   LoopGauge: 코드3
        if suppressMaxTextOnce(+0x1a0) == 0:
            if layout+0xf0 != 0 && 레이아웃 페인 조상 전부 표시(+0x58 bit0) && showFullText(+0x1a8):
                InText: 코드1                          // "풀 충전!" 들어오기
        else: suppressMaxTextOnce = 0
    if value >= 75:                                    // 가득에서 내려감(특수 사용 등)
        Max: 코드6(처음 프레임 정지)      LoopMax: 코드5(그 자리 정지)       LoopGauge: 코드5
        if InText 재생 중(프레임≠0 또는 코드≠0):  InText: 코드10,  OutText: 코드1
if InText AnimTransform 플래그(+0x54 bit0, 재생 끝으로 추정) 켜짐:  OutText: 코드1
아이콘 파츠(+0x180)+0x152 != 0 이면: 캡처 다시(+0x190 → +0xd4 = 1);
    아이콘 파츠+0x158 == 0x14 이고 iconSwapped(+0x1a1)==0 → OutMax 코드1 속도+1, +0x1a1=1
    아니고 +0x1a1 != 0 → OutMax 코드1 속도−1, +0x1a1=0
+0x188 파츠도 같은 방식으로 캡처 다시(+0x198)
iconPart(+0x180)+0x150=1, +0x154=2;  (+0x188)+0x150=1, +0x154=1;  showFullText(+0x1a8) = 0
```

`showFullText`는 HUD 관리자가 **"지난 프레임과 같은 관전 대상이고 +0xbe8도 같을 때"만** 1로 줍니다. 그래서 관전 대상을 이미 가득 찬 다른 플레이어로 바꾼 프레임에는 Max 애니는 나오지만 "풀 충전!" 문구는 나오지 않습니다 **[판독 + 의미 추정]**. 다만 위 코드에서 InText 조건이 `+0x1a8`을 그대로 읽는 것은 "이번 프레임 값"이고, 매 갱신 끝에서 0으로 지웁니다.

### 5.3 프레임 안 순서·dt·애니 핸들 명령 [판독] (2026-10-02 [camui] 갱신, 앞 판본의 [추정]을 대체)

#### 화면 1개의 calc (화면 기본 vtable 0x710557d558 슬롯 17 = 0x710136608c → 0x71038f5cd0)

| 순서 | 호출 | 하는 일 |
|---|---|---|
| 1 | 화면 슬롯 39 (Spl 화면 0x7103205e2c → 기본 0x7101366134) | 모듈 링(화면+0x1b0, 개수 +0x1c0)의 보조 인터페이스 +0x90 → +0x48(= **컨트롤 슬롯 13**, SuperGauge `0x710317426c` 가득 참 판정) → **화면 슬롯 100**(VS 화면 갱신 `0x71033dbacc`) → +0x50 → +0x58 |
| 2 | 하위 레이아웃 목록(화면+0x100) | 각각 `0x71038f89dc`, 활성이면 vt+0x20 |
| 3 | 화면 슬롯 40, 25 | — |
| 4 | 화면 슬롯 65 (`0x7101366304`) | `dt = 화면 슬롯 41()`; 컨트롤 목록(화면+0x38, 노드 = 컨트롤+8)의 **컨트롤 슬롯 4(dt)** = TraceGauge 갱신 `0x71038d6748`(SuperGauge의 슬롯 4 = `0x710135a960` → b `0x71038d6748`); 이어서 모듈 링 +0x60 |
| 5 | 화면 슬롯 69, 71 | — |
| 6 | 화면 슬롯 73 (`0x71013663fc`) | 애니 핸들 목록(화면+0x178)의 명령 처리 `0x71013686f8` → `0x71038f67f8` → 화면 vt+0x3a8 |

- 모듈 링(+0x1b0)은 `0x7101365b98`이 화면 컨트롤 목록을 돌며 형 검사에 맞는 객체의 **보조 인터페이스 포인터**(컨트롤+0x28/+0x78/+0x80/+0x90)를 넣은 것입니다. SuperGauge(TraceGauge 계열)는 +0x78 보조 vtable(0x71056bd970)을 넣고, 보조 +0x48은 썽크 `0x710135b7b0`(`ldr x8,[x0,#-0x78]!; ldr x1,[x8,#0x68]; br x1`)로 주 vtable 슬롯 13에 갑니다 [판독].
- 따라서 **같은 프레임에서 슬롯 13(가득 참 판정, `target != value`) → 슬롯 4(`value = target`, 추적값 이동)** 순서가 원본 코드로 확인됩니다. 디스패처(HUD 관리자, 게임 쪽)가 이 calc보다 먼저 도는지는 두 시스템의 상위 순서를 보지 않아 [추정]으로 남깁니다.
- 상위 순서 추적(2026-10-03 [r6 ui]) [판독, 부분]:
  - 프레임워크(vtable `0x71055552c8`) 프레임 함수 `0x7103502d10`의 호출 순서는 vt+0xe8(슬롯 29 → `0x7103502e18`, NVN 명령 버퍼로 그리기) → vt+0xf0(슬롯 30 = `0x7101026dd0`) → vt+0x70입니다.
  - 슬롯 30 `0x7101026dd0`은 UI 레이어 dt 64칸을 먼저 채우고(`0x710138475c`) `0x71035031ec`를 부릅니다. 이 함수는 UI 전용이 아니라 프레임워크 calc 전체입니다. 작업 관리자(+0x38: `0x7103509238`, `0x7103509538`) 다음에 메서드 트리 루트(+0x40 → +0x48)를 `0x7103505738`로 재귀 실행합니다(노드 +0x50 대리자, 자식 +0x28, 형제 +0x30, +0x7c 일시정지 비트).
  - 그러므로 액터 단계(`spl::Spectator` 슬롯 21 포함)와 UI 화면 calc는 모두 이 메서드 트리 안에서 자식 연결 순서대로 돕니다. 그 연결은 실행 중에 만들어지므로 둘의 앞뒤는 여전히 [미확정]입니다.
  - 정정: 앞의 "UI 갱신 `0x71035031ec`"라는 이름은 "프레임워크 calc(메서드 트리)"로 고칩니다.
  - 다음에 볼 곳: 액터 시스템 calc 노드와 UI 레이어 calc 노드를 메서드 트리에 붙이는 호출(노드 +0x28/+0x30을 쓰는 attach 함수).
- 애니 명령(슬롯 13이 핸들에 써 둔 Max·LoopMax·InText 등)은 같은 프레임 6단계에서 AnimTransform에 반영됩니다.

#### dt

```
dt(screen) = *( *(screen+0x20) + 0x408 )            // 화면 슬롯 41 = 0x71038f77d0
UI 레이어 관리자(*0x7105999e38)의 +0x32c..+0x428 (64칸)을 0x710138475c 가 한 값으로 채움
그 값 = 0x7101026dd0(프레임워크, vtable 0x71055552c8 슬롯 30):
  n = this+0x2cc(이전 값) ; this+0x2cc = 1 ; this+0x2c8 = n
  f = (*(*0x7105791c30)+0x222) & 1 ? 2.0 : 1.0
  dt = (n ≥ 2) ? f·n : f      → UI 갱신 0x71035031ec 실행 → n ≥ 2 였으면 dt = f 로 되돌림
```

- 대전처럼 60fps로 매 프레임 도는 경우 n = 1, 플래그 비트가 0이면 **dt = 1.0** [판독]. 플래그 비트(전역 `*0x7105791c30`+0x222 bit0)가 켜지면 2.0인데, 이 플래그를 30fps 동작 모드(광장 등)로 보는 것은 [추정]입니다. n ≥ 2(프레임 누락 수로 추정)일 때 배수가 됩니다 [판독: 식] / [추정: n 의미].
- 플래그 추적(2026-10-03 [r5 ui]) [판독]: `*0x7105791c30`(GOT) = `0x710580e5e8`이 가리키는 프레임워크 객체입니다. `gsys::SystemTask::preCalc_`(`0x71037a288c`)가 SystemTask+0x458 bit0을 프레임워크+0x222 bit0에 복사합니다(bit0이 이미 켜져 있으면 유지). SystemTask 생성자(`0x71037a26e4`)의 +0x458 기본값은 `0x4000f2`라 **bit0 = 0 → dt = 1.0**입니다. bit0이 켜지면 프레임 끝 `0x7103502d10`이 bit1을 매 프레임 뒤집고, bit0·bit1이 모두 켜진 프레임에는 시간 측정을 건너뜁니다(격프레임 동작). SystemTask+0x458 bit0을 켜는 setter는 찾지 못했습니다(전역 `str32 #0x458` 스캔 0x71037xxxxx 구간 3건은 생성자·crc 초기화). 그래서 "이 플래그 = 30fps 모드"는 여전히 [추정]이고, 사격장이 이 플래그를 켜는 근거는 없습니다 [미확정]. 다음에 볼 곳: SystemTask+0x458 비트 setter(`orr`/`bfi` 후 `str [x, #0x458]`), 씬 전환 시 프레임레이트 설정 호출.
- **플래그 setter 확정(2026-10-03 [r6 ui]) [판독]+[데이터]+[실행]** — 위 두 항목의 [추정]·[미확정]을 대체합니다.
  - 씬 객체(vtable `0x7105579058`)의 슬롯 4 `0x710131f254`가 `Work/Scene/<씬>.engine__scene__SceneParam.gyml` 행에 태그 `SceneAttr_Fps30` 비트가 있는지 확인합니다(행 찾기 `0x71038c425c`, 태그 이름 → 열 `0x71038c4a00`, 비트 = 표+0x70[(행×표+0x60 + 열) >> 3] >> (… & 7) & 1). 결과를 씬+0x354에 씁니다(`0x710131f794`).
  - 씬 시작 슬롯 6 `0x710131fa04`의 `0x710131fac4`: `(씬+0x354 | 2) == 3`이면 `*(0x7105999df8)+0x458 |= 1`.
  - 씬 종료(`0x7101320390`, 상태 +0x220 = 5)의 `0x71013207f0`: 같은 조건이면 `&= ~1`, 이어서 +0x354 = 0.
  - `*0x7105999df8`은 SystemTask 인스턴스입니다. SystemTask 생성 경로(`0x7103d9e604` → 생성자 `0x71037a2348`, 문자열 "gsys::SystemTask")가 생성 콜백으로 `0x71037a2258`(비어 있으면 인스턴스 저장)을 넘깁니다(`0x7103d9f350`).
  - 데이터(`RSDB/Tag.Product.100.rstbl.byml.zs`, 태그 177개·경로 4373행, `analysis/r6_ui/Tag.json`): `SceneAttr_Fps30`(열 127)이 켜진 씬은 **`Plaza`(광장) 하나**입니다. 사격장 `LobbyVersus`는 꺼져 있습니다(켜진 태그: `SceneAttr_Customize`, `SceneAttr_ExtraRumbleConstant`, `SceneAttr_News`, `Scene_AroundPlaza`, `Scene_AutoProfile`, `Scene_Lobby`, `Scene_PlazaRc`). 같은 디코드로 `SceneAttr_NoMiniMap`·`SceneAttr_NoPaint` = Plaza·Shop이 나와 해석을 교차 확인했습니다.
  - 결론: 광장에서만 dt 배수 2.0과 격프레임 동작이 켜지고, **사격장 UI dt는 1.0**입니다(프레임 누락이 없을 때).
  - 원본 실행 `web/tools/r6_ui_fps30_emu.py`: 씬+0x354 = 0/1/2/3 × n 열(모두 1, `[1,2,1,3,1,1]`) 8시나리오에서 씬 시작 구간 → 6프레임(preCalc_ 구간 `0x71037a2a30..0x71037a2b24` → UI 프레임 `0x7101026dd0` 전체 → 프레임 끝 `0x7103502d10` 전체) → 씬 종료 구간을 원본으로 돌렸습니다. SystemTask+0x458, 프레임워크+0x222, `0x710138475c`에 넘긴 dt가 독립 재구현과 **8/8 일치**했습니다. 예: Fps30이면 dt 2.0, n = 2면 4.0 다음 2.0, 비트 1은 매 프레임 토글. 결과 `analysis/r6_ui/fps30_emu.json`.
  - 스텁: 프레임워크 vt+0(형 검사 → 1), vt+0xe8/+0xf0/+0x70/+0x110/+0x118, `0x710138475c`(dt 기록), `0x71035031ec`, `0x7103509808`, `0x7103e9a3d0`(시각). 태그 표 찾기(`0x71038c425c`/`0x71038c4a00`)는 실행하지 않고 데이터 디코드로 대신했습니다.
- TraceGauge 추적 속도 2.0은 "값 단위/dt" 이므로 60fps 대전에서는 2.0/프레임 그대로입니다.

#### 애니 핸들 명령 코드 (`0x71013686f8`, 점프 표 `0x7104a9972a`) [판독 + 실행(에뮬)]

핸들(생성 `0x7101363ef4`, 화면+0x178 목록, 노드 = 핸들+0x20): `+0x00 vtable 0x710557dd60`, `+0x08 AnimTransform*`, `+0x10 명령 s32`, `+0x14 f32 a`, `+0x18 f32 b`. 처리 후 명령은 0으로 지웁니다. AnimTransform(0x68 B, vtable 0x710573b610) 필드: `+0x20 frame`, `+0x24 enable u8`, `+0x50 speed`, `+0x54 플래그 u16(하위 4비트 상태, bit5 이벤트 알림)`, `+0x56 루프`.

| 명령 | 처리 | AnimTransform 동작 (함수) | 웹 권장 이름 |
|---|---|---|---|
| 0 | 없음 | — | `none` |
| 1 | vt+0xc0(speed=b) → vt+0xb8 | **처음부터 재생**: b ≥ 0이면 frame=0, b < 0이면 frame=프레임 수(역재생 시작), speed=b, 루프=데이터 플래그, enable (`0x71038f3120`→`0x71038f2efc`) | `playFromStart(b)` |
| 2, 3 | frame=a(비트 그대로), vt+0xc8(loop=데이터, speed=b) | **지정 프레임에서 재생**: speed=b, enable (`0x71038f3160`) | `playFrom(a, b)` |
| 4, 5 | vt+0xd0(a) | **프레임 a에서 정지**: speed=0, frame=a, enable (`0x71038f32e4`) | `setFrame(a)` |
| 6 | vt+0xe0 | **첫 프레임 정지**: speed=0, frame=0 (`0x71038f3410`) | `stopAtStart()` |
| 7 | vt+0xe8 | **끝 프레임 정지**: speed=0, frame=프레임 수 (`0x71038f3468`) | `stopAtEnd()` |
| 8 | frame=a | 프레임만 씀(정지·enable 변화 없음) | `writeFrame(a)` |
| 9 | vt+0x20(true) | enable (`0x71038f34d0`) | `enable()` |
| 10 | enable=0(`0x7100851c88`), speed=0 | 끔 | `disable()` |
| 11 | 10과 같음 + 레이아웃 애니 목록에서 뺌 | 끄고 분리 | `detach()` |
| ≥12 | 없음 | — | |

- 핸들 보조 함수: `0x7101368848(b)` = 명령 1, a=−1, b; `0x710136885c` = 명령 7, a=프레임 수, b=0; `0x71013688a4` = 명령 6; `0x71013688b4(f)` = 0 ≤ f ≤ 프레임 수이고 바뀔 때만 명령 4(a=f) [판독].
- 앞 판본(§5.2)이 "코드1(처음부터, 속도1)", "코드3(현재 프레임부터 재생)", "코드5(그 자리 정지)", "코드6(처음 프레임 정지)"로 쓴 해석은 위 표와 맞습니다. 코드3의 a는 SuperGauge 갱신이 넣은 현재 프레임(직전 명령이 8이면 그 a)이라 "현재 프레임부터 재생"이 됩니다. 코드10은 "끔"입니다 [판독].
- **enable(vt+0x20, 1)은 AnimTransform을 레이아웃 애니 목록(레이아웃+0x70)의 끝으로 옮깁니다**(`0x71038f34d0`, 노드 +0x40) [판독]. setFrame·재생 함수가 모두 enable을 부르므로 같은 프레임에서 **나중에 명령한 AnimTransform이 목록 끝**이 됩니다.
- **적용 루프 `0x71038f67f8`(화면 슬롯 73 0x71013663fc가 핸들 명령 처리 직후 화면 자신을 넘겨 호출)** — 2026-10-02 [camrest] [판독 + 실행(에뮬)]:

```
dt = 화면.vt+0x148()
for node in 화면+0x70 목록(앞→뒤, 노드 = AnimTransform+0x40, 다음 = 노드+8):
    at.vt+0x28()                      // Animate = 0x7100852b2c: enable(+0x24)이고 바인딩 수(+0x38)>0 이면
                                      //   바인딩(+0x30, 0x10 B씩)마다 종류(+0x1d)에 따라 vt+0x98/+0xa0/+0xa8/+0xb0 로 대상에 값 기록
    if at.speed(+0x50) != 0 && at.enable: at.vt+0x18(dt)   // UpdateFrame 0x71038f3560: frame += speed·dt, 끝 처리
    else if !(at.flags(+0x54) & 2):
        at.enable = 0 ; (at+0x58 객체).vt+0xc0(at) ; speed = 0 ; flags &= 0xfff0
        if 옛 flags & 1 : flags |= 2 (목록에 남김)   else 목록에서 뺌(노드 자기 연결)
    else: 목록에서 뺌, flags &= 0xfff0
```

  - 즉 **목록 순서대로 적용하고, 같은 대상은 나중에 적용된 값이 남습니다.** setFrame(정지)된 AnimTransform은 **한 번 적용된 뒤 꺼지고 목록에서 빠집니다**. 다음 setFrame이 다시 enable해 목록 끝에 넣습니다. 그래서 값이 그대로인 프레임(TraceGauge가 프레임을 쓰지 않는 프레임)에는 아무것도 다시 쓰지 않고 마지막 값이 재질에 남습니다 [판독].
  - TraceGauge 프레임 적용(`0x71038d69bc`)은 모든 분기에서 GaugeRatio(+0x28)를 먼저, TraceRatio(+0x30)를 나중에 setFrame하므로 매번 **TraceRatio가 마지막에 적용**됩니다 → §6.4 `표시 = min(value, trace)` **확정** [실행(에뮬)].
  - 검증 `web/tools/ui_animorder_emu.py`: 원본 `0x71038d6748`(TraceGauge 갱신)→`0x71038d69bc`→`0x71038f32e4`(setFrame)→`0x71038f34d0`(enable·목록 이동)→`0x71038f67f8`(적용 루프)를 unicorn으로 연결 실행. 스텁은 AnimTransform vt+0x28(Animate: 호출 순서와 그때 frame 기록)·vt+0x18(UpdateFrame)·레이아웃 vt+0x60/+0xc0/+0x148(dt=1). 감소 75→30(4프레임)·증가 30→75(24프레임), 초기 목록 순서 A,B / B,A 두 경우 모두 **28프레임 × 2 = 56 PASS**(표시 = 마지막 Animate의 frame을 값으로 환산 = min(value, trace)). 값·추적값이 같아진 뒤에는 목록이 비어 Animate 호출이 없음도 확인 [실행(에뮬)]. Animate 내부의 재질 쓰기(vt+0x98..)는 판독이고 실행하지 않았습니다.
- 검증: `web/tools/ui_animcmd_emu.py` — 원본 `0x71013686f8`을 unicorn으로 명령 0~12에 대해 실행, AnimTransform 가상 호출을 스텁으로 기록. 명령→슬롯(1→0xc0, 2·3→0xc8(x1=루프 1), 4·5→0xd0(s0=a), 6→0xe0, 7→0xe8, 9→0x20(1)), 8은 frame=a, 10·11은 enable·speed 0, 처리 후 명령 0 — **13항목 PASS** [실행(에뮬)]. AnimTransform 각 슬롯 내부는 스텁이므로 위 표의 "동작" 열은 디컴파일 판독입니다.

### 5.4 사격장 게이지 화면 `Lobby_GuideBtn_00` [판독] (2026-10-03 [r5 ui])

화면 클래스 `SplUILobbyGuideBtn00Screen`(팩토리 vtable `0x71056e7a80`, 화면 vtable `0x71056e7638`). 대전 화면과 달리 게이지 초기화가 리셋(슬롯 98)이 아니라 **init(슬롯 97)**에 있습니다.

| 단계 | 함수 | 하는 일 |
|---|---|---|
| init(슬롯 97) | `0x71032ba20c` | 애니 핸들 5개(`Change, Signal, Nice, Chat, ToMatch` 순서, +0x250~+0x270). +0x278 = `L_SuperGauge_00` 컨트롤(`SplUISuperGaugeCtrl`), **target(+0x48) = 0, showFullText(+0x1a8) = 0**. +0x280 = `L_GuideBtn_00`(파츠 컨트롤의 애니 핸들 +0x150에 setFrame 6), +0x290 = `L_GuideBtn_01`(setFrame 4), +0x288 = `L_GuideBtn_02`(vt+0x158(8)). +0x298 = `L_PlayerStatus_00` 컨트롤, +0x2a0 = 페인 `N_Signal_00` |
| 리셋(슬롯 98) | `0x71032ba500` | 씬 이름이 `LobbyLocal`이면 +0x2a8 = 1. `Change`(+0x250)·`ToMatch`(+0x270) 핸들 명령 6(첫 프레임 정지), `L_GuideBtn_02` 문구 `<파츠>-T_Info_00` = 라벨 `010`, `T_Signal_00` = `000` |
| 갱신(슬롯 100) | `0x71032ba75c` | 관전 대상 본체 상태로 안내 버튼 표시·숨김(+0xbf0>0 = 스페셜 사용 중이면 숨김), 시그널 문구 `000`/`001` 전환, 미니게임 방(`IsInMiniGameRoom`)·특수 모드(`*0x710580e340`+0x143d0) 분기 |

- 게이지 값은 HUD 관리자(`spl::Spectator` 슬롯 21)가 `Lobby_GuideBtn_00`이 열려 있을 때만 `0x710342eb10`으로 +0x278 컨트롤에 씁니다(§3). 그 뒤 동작(가득 참 판정·TraceGauge·표시 min 규칙)은 대전과 같은 `SplUISuperGaugeCtrl`·`SuperGaugeTV_00` 파츠라 §5.2~§6.5를 그대로 따릅니다 [판독].
- 따라서 사격장 입장 직후 init 상태는 target 0, value·trace 75(TraceGauge init)이고, 첫 TraceGauge 갱신에서 value = 0 → 표시 = min(value, trace) = 0입니다(§6.4) [재구현: 판독식].

### 5.5 잉크 부족 화면 `Cmn_NoInk_00` [판독 + 실행(에뮬)] (2026-10-03 [r5 ui])

화면 클래스 `SplUICmnNoInk00Screen`(팩토리 vtable `0x71056e0410`, 화면 vtable `0x71056dffc8`, 객체 0x278 B). 진입점은 `0x7100feb5c4(kind)`(이름으로 화면을 찾아 `0x7103276e2c` 호출)입니다. 슈터에서는 발사 처리 `0x71025856c8`이 잉크 검사(`0x7102492120`) 실패이고 본체+0x1058 == 0일 때 kind 0으로 부릅니다([elements §8](ui_vs_maintv_elements.md), [paintgpu] 판독). 잉크가 모자란 상태로 계속 쏘면 매 발사 시도마다 요청이 들어옵니다.

필드(기준: NoInk 화면 객체) — 생성자 `0x7103277694`가 +0x260~+0x26f = 0, +0x270 = 1:

| 오프셋 | 형식 | 웹 권장 이름 | 의미 |
|---|---|---|---|
| +0x250 | ptr | `animFrameIn` | 핸들 `FrameIn`(48f) — 이름 표 `"FrameIn, Type"`(`0x71032777d8`) |
| +0x258 | ptr | `animType` | 핸들 `Type`(3f): 페인 표시 전환 |
| +0x260 | s32 | `flashLeft` | 열림 처리 남은 프레임(열기 시 32, FrameIn 재생 시 48) |
| +0x264 | s32 | `holdLeft` | 요청 유지(요청마다 2) |
| +0x268 | s32 | `showLeft` | 최소 표시 프레임(새 표시면 40) |
| +0x26c | s32 | `kind` | 종류 |
| +0x270 | u8 | `textDirty` | 문구 다시 쓰기 |

```ts
// 요청 0x7103276e2c
function request(s: NoInk, kind: number) {
  if (s.kind !== kind) {
    s.kind = kind; s.textDirty = true;
    const f = {0: 0, 3: 2, 4: 3, 5: 4}[kind] ?? 1;          // Type 프레임
    const h = s.animType;                                   // 핸들 a/b 는 앞 명령 값이 남아 있음
    const n = h.anim.frameCount;                            // 0x7100851c78 (Type = 3)
    const same = h.a === f && h.b === 0 && h.anim.inList;   // 이미 그 프레임으로 적용 대기 중
    const tooShort = kind === 0 ? false : n < f || n === 0;
    if (!same && !tooShort) h.cmd(4, f, 0);                 // setFrame(f)
  }
  if (!isOpen(s) || s.holdLeft === 0) s.showLeft = 40;
  s.holdLeft = 2;
  if (isClosed(s) || isClosing(s)) { s.flashLeft = 32; open(s); }          // vt+0x2b0
  else if (s.flashLeft === 0) { s.animFrameIn.cmd(1, -1, 1.0); s.flashLeft = s.animFrameIn.anim.frameCount; } // 48
}
// 갱신(화면 슬롯 100) 0x7103277148
function update(s: NoInk) {
  if (s.textDirty) { setText(TEXT[s.kind]); s.textDirty = false; }
  if (isOpen(s)) {
    if (s.flashLeft > 0) s.flashLeft--;
    if (s.showLeft > 0) s.showLeft--;
    if (s.holdLeft > 0) s.holdLeft--;
    if (s.showLeft < 1 && s.holdLeft < 1) close(s);                       // vt+0x2b8
  }
}
// isOpen = (+0x16e == 2 && (s8)+0x16d >= 0) 0x7101363e48
// isClosed = (+0x16e == 0 && (s8)+0x16d < 1) 0x7101363e6c
// isClosing = (+0x16e == 3 || ((s8)+0x16d < 0 && +0x16e in {1,2})) 0x7101363ec4
```

| kind | 텍스트 페인 ← LayoutMsg/Cmn_NoInk_00 라벨 (한국어) | Type 프레임 → 보이는 아이콘 |
|---|---|---|
| 0 (슈터 잉크 부족) | `T_NoInk_00` ← `000` "잉크 부족!" | 0 → `T_NoInk_00`, `N_Icon_00` |
| 1 | `T_NoInk_01` ← `001`(KRko에 라벨 없음) | 1 → `T_NoInk_01`, `N_Icon_01` |
| 2, 6 이상 | `T_NoInk_01` ← `003` "사용 불가" | 1 |
| 3 | `T_NoInk_00` ← `002` "꼬마연어 필요!" | 2 → `N_Icon_02` |
| 4 | `T_NoInk_00` ← `004` "연어알 부족!" | 3 → `N_Icon_03` |
| 5 | `T_NoInk_00` ← `004` | 4 요청이지만 Type 길이 3이라 생략(이전 프레임 유지) |

- 생성자가 `textDirty = 1`, `kind = 0`이라 첫 갱신에 `000`이 들어가고, 첫 kind 0 요청은 kind가 같아 Type 명령을 내지 않습니다(Type 애니 데이터 초기 프레임 0 그대로) [판독+실행].
- 보이는 시간: 열림(+0x16e = 2) 프레임만 줄어듭니다. 한 번만 요청하면 **열린 뒤 40프레임**, 계속 요청하면 **마지막 요청 뒤 2프레임과 40프레임 카운트가 모두 끝난 프레임**에 닫기를 요청합니다. 요청 간격이 3프레임이면 holdLeft가 0이 된 뒤 다음 요청에서 showLeft = 40으로 다시 채워집니다 [실행].
- 원본 실행 `web/tools/r5_ui_noink_emu.py`: 6개 시나리오(단발, 매 프레임 유지 60f, 3프레임 간격 20회, 열린 상태 FrameIn 재생, kind 0~6 전환 × Type 애니 목록 안/밖, 닫는 중 재요청) **317/317 프레임**에서 원본 `0x7103276e2c`/`0x7103277148`과 재구현의 필드·핸들 명령·이벤트가 일치 [실행]. 스텁: 열기 vt+0x2b0·닫기 vt+0x2b8(호출만 기록), 텍스트 설정 `0x71013621d0`(인자 기록). 상태 질의 세 함수와 `0x7100851c78`은 원본 그대로 실행했습니다. 화면 상태 바이트(+0x16d/+0x16e)의 실제 전이(In/Out 애니 길이)는 UI 프레임워크 몫이라 시나리오가 넣었고 검증하지 않았습니다.
- 화면 배치: `N_All_00`(0, −185) 안 180×67 창, 문구 `T_NoInk_00`(20, −4) — 화면 중앙 아래쪽 [데이터]. 애니 `In` 8f, `Out` 5f, `Loop` 1000f(반복), `FrameIn` 48f, `Type` 3f [데이터].

## 6. 계산식·의사코드

### 6.1 디스패처 (0x710342eb10) [판독]

```ts
function setSuperGaugeRatio(showFullText: boolean, ratio: number /* f32 */) {
  const g = activeScreenGauge();            // VS: screen.superGauge (+0x3e0)
  if (!g) return;                           // 화면 없음 / 형 불일치 / UI관리자+0xc8 != 0
  let v = ratio < 0 ? 0 : Math.min(ratio, 1) * 75;       // f32 (fmin, fmul, fcsel mi)
  if (v >= 0 && v <= g.animGauge.frameCount) g.target = v;  // 범위 밖이면 target 유지
  g.showFullText = showFullText;            // +0x1a8, 범위 밖이어도 씀
}
```

NaN이면 `fcmp` 결과가 비교 실패라 target을 쓰지 않습니다(원본 분기 그대로).

### 6.2 TraceGauge 갱신 (0x71038d6748) [판독]

```ts
function traceGaugeUpdate(g: TraceGauge, dt: number) {
  const v = g.target; let cur = g.value; let jump = 0; let changed = false;
  if (v !== cur) {
    if (cur <= v) changed = true;                                 // 증가
    else if (g.jumpFraction === 0) changed = false;               // 감소, 점프 없음
    else { const j = (cur - v) * g.jumpFraction; jump = Math.max(g.jumpMin, j); changed = true; }
    if (cur < v && g.jumpFraction !== 0) { const j = (v - cur) * g.jumpFraction; jump = -Math.max(g.jumpMin, j); }
    if (g.animShortage) {                                         // SuperGauge 에는 없음
      const s = v <= g.shortageLevel2 ? 2 : v <= g.shortageLevel1 ? 1 : 0;
      if (s !== g.animShortage.frame) g.animShortage.setFrame(s);
    }
    if (g.trace === cur) g.traceWaitLeft = g.traceWait;
    g.value = cur = v;
    if (!changed || cur === g.trace) return applyFrames(g);       // 감소(점프 없음)는 이번 프레임 추적값 이동 없음
  } else {
    if (cur === g.trace) return;                                  // 아무것도 안 함(프레임도 안 씀)
  }
  // 추적값 이동
  if (!g.traceEnabled) return changed ? applyFrames(g) : undefined;
  if (g.traceWaitLeft > 0) {
    const w = g.traceWaitLeft - dt;
    g.traceWaitLeft = (w > 0 && w <= g.traceWaitLeft) ? w : 0;
    return changed ? applyFrames(g) : undefined;
  }
  const sp = Math.max(g.traceSpeed, Math.abs(g.trace - cur) * g.traceFraction);
  let tr = g.trace;
  if (cur < tr) { const t = tr - sp * dt; tr = (t <= cur || tr < t) ? cur : t; }
  else if (cur > tr) { const t = tr + sp * dt; tr = (cur <= t || t < tr) ? cur : t; }
  g.trace = tr;
  if (jump < 0 && cur + jump < tr) g.trace = cur + jump;
  else if (jump > 0 && tr < cur + jump) g.trace = Math.min(cur + jump, g.animGauge.frameCount);
  applyFrames(g);
}

function applyFrames(g: TraceGauge) {           // 0x71038d69bc
  const N = g.animGauge.frameCount;            // 75
  const fv = N * (1 - g.value / N), ft = N * (1 - g.trace / N);
  if (g.value < g.trace)      { g.animGauge.setFrame(ft); g.animTrace.setFrame(fv); g.animTraceColor?.setFrame(0); }
  else if (g.value === g.trace){ g.animGauge.setFrame(fv); g.animTrace.setFrame(fv); g.animTraceColor?.setFrame(1); }
  else                        { g.animGauge.setFrame(fv); g.animTrace.setFrame(ft); g.animTraceColor?.setFrame(1); }
}
```

- `dt`는 갱신 함수의 s0 인자이고, 화면 슬롯 65가 화면 슬롯 41로 얻은 값을 넘깁니다. 대전(60fps, 프레임 누락 없음)에서 **1.0** [판독] — §5.3.
- `setFrame`은 AnimTransform vtable +0xd0입니다.

### 6.3 Gauge 애니 → 셰이더 인자 [데이터]

`__CUS_Float_0(frame) = 0.75 × (1 − frame/75)`. `frame = 75 × (1 − x/75)`이므로 결국 **`__CUS_Float_0 = 0.75 × (x / 75) = 0.01 × x`** (x = value 또는 trace, 0~75). 비율로 쓰면 `0.75 × ratio`입니다.

### 6.4 두 AnimTransform이 같은 페인을 움직일 때 [판독 + 실행(에뮬)] (2026-10-02 [camrest] 확정, 앞 판본 [추정])

`GaugeRatio`와 `TraceRatio`가 모두 `Gauge`라서 두 AnimTransform이 같은 `__CUS_Float_0`를 씁니다. 적용 루프 `0x71038f67f8`이 레이아웃 목록 순서대로 Animate하고, 프레임 적용 `0x71038d69bc`가 매번 GaugeRatio → TraceRatio 순으로 setFrame(→ 목록 끝 이동)하므로 **TraceRatio가 항상 마지막에 적용되어 이깁니다**(§5.3 끝, 원본 연결 에뮬 56 PASS). 생성 순서(앞 판본 근거)와는 무관합니다(초기 순서를 뒤집어도 같음). 화면 값:

| 상황 | 화면 비율 |
|---|---|
| 게이지 증가(value > trace) | **trace** — 2.0/프레임(= 2.67%/프레임)으로 따라 올라감, 0→가득 37.5프레임 |
| 게이지 감소(value < trace) | **value** — 즉시 떨어짐 |
| 같음 | value |

즉 `표시 비율 = min(value, trace) / 75`입니다(증가는 2.0/프레임으로 서서히, 감소는 즉시) **[실행(에뮬): 원본 함수 연결 실행]**. 남은 전제: 두 바인딩이 같은 재질 값을 쓴다는 것은 bflan 데이터([데이터])이고, Animate의 재질 쓰기 내부와 화면 출력은 실행하지 않았습니다.

### 6.5 MeterAction 셰이더 [판독: 원본 GLSL 소스]

정정: 이전 판에서는 셰이더 바이너리를 못 읽어 시작각·방향을 설정값으로 남겼으나, 레이아웃 아카이브 `bgsh/MeterAction.glsl`에 **노드 편집기가 생성한 원본 GLSL 소스**가 들어 있었습니다(SuperGaugeTV_00·HoldText_00·TimerCircle_00 세 곳, 같은 파일 md5 bfe8a690…). 컴파일본 `__ArchiveShader.bnsh` 역번역도 같은 상수·구조입니다. 전체 식과 검증은 [../graphics/shaders.md §5](../graphics/shaders.md).

- **시작각·방향**: 12시에서 **시계 방향**으로 채웁니다. `t = 1 − (atan(p.x, p.y) + π)/(2π)`, `p = uv·2 − 1`(v가 작은 쪽이 화면 위), `t < F0` 부분이 보임. 보이는 끝 각도 = `360° × (1.005·F0 − 0.0025)`, 경계 0.005(1.8°)는 smoothstep으로 부드럽게.
- **`__CUS_Float_1`** = 링 두께 비율(안쪽 반지름 `F2·(1−F1)`, 1이면 중심까지), **`__CUS_Float_2`** = 바깥 반지름(UV 단위, 중심 0.5 기준). 둘 다 1.0이면 반지름 마스크가 없음 — HUD는 둘 다 1.0이라 호 모양은 텍스처(`GaugeSp_00`)가 정합니다.
- 색: `mix(재질 흑색, 재질 백색, vec4(tex.rgb, arc·tex.a·outer·inner)) × 정점색`, 이후 ui2d 알파 처리.
- 가득일 때 F0 = 0.75 → 0..270.45°로 텍스처 호(12시→9시) 전체와 일치.

```glsl
// 웹 구현(원본 식 그대로)
uniform float cus0, cus1, cus2;                  // __CUS_Float_0..2
vec2  p   = vUv * 2.0 - 1.0;                     // vUv: 페인 UV, v 아래로 증가(ui2d 기본 LT(0,0)…RB(1,1))
float t   = 1.0 - (atan(p.x, p.y) + 3.14159265) / 6.2831853;
float e0  = mix(-0.005, 1.0, cus0);
float arc = 1.0 - smoothstep(e0, e0 + 0.005, t);
float d   = distance(vUv, vec2(0.5));
float outer = smoothstep(cus2 + 0.005, cus2, d);
float rin   = cus2 - mix(0.0, cus2, cus1);
float inner = smoothstep(rin, rin + 0.005, d);
vec4  c = mix(matBlack, matWhite, vec4(tex.rgb, arc * tex.a * outer * inner)) * vtxColor;
```

`__CUS_Float_N` ↔ 소스의 `nwExUserDataFloat_N` 대응은 **확정**입니다 [판독] (2026-10-03 [r5 ui], 이전 판 [추정] 대체):
- ui2d 재질 그리기 준비 `0x7100866c98`이 재질 픽셀 상수 버퍼(GPU 버퍼 + 재질+0x34)를 0x220 B 지운 뒤, `0x7100867134`가 페인 사용자 데이터를 **이름 비교(strcmp)**로 읽어 `__CUS_Float_0..3` → 버퍼 +0x120/+0x124/+0x128/+0x12c, `__CUS_Vec2_N` → +0x130+0x10·N, `__CUS_Vec3_N` → +0x170+0x10·N, `__CUS_Rgba_N` → +0x1b0+0x10·N(정수/255)에 씁니다.
- 컴파일된 셰이더(`analysis/shader/layout_SuperGaugeTV_00/var009.frag.glsl`, 역번역)는 `uConstantBufferForPixelShader.data[18].x/.y/.z`(바이트 0x120/0x124/0x128)를 F0/F1/F2로 읽습니다. 예: `fma(data[18].x, 1.005, -0.005)` = `mix(-0.005, 1.0, F0)`.
- 두 오프셋이 같으므로 `nwExUserDataFloat_N` = `__CUS_Float_N`입니다. 남은 가정: `var009`가 MeterAction 재질이 실제로 고르는 변형이라는 것(셰이더 키 `MeterAction`, 변형 표는 `CombinerUserShaderVariation.glsl` TYPE 1).

기존 근사 렌더(`analysis/ui/render/supergauge_frames_0_37.5_75.png`, "각도/360 ≤ 인자")는 12시·시계 방향이라 방향은 맞았고, 경계의 1.005배·smoothstep 차이만 있습니다. 재구현 렌더 `analysis/shader/meteraction_gauge.png`.

## 7. 애니·이펙트·에셋 연결

| 상태 | 애니(SuperGaugeTV_00) | 보이는 것 |
|---|---|---|
| 상시 | Gauge(프레임 = 값) | 주황 호(P_pict_02, #ff5d00) + 빛번짐(P_CapUse_01 = N_Cap_00 캡처, blur5, 가산 블렌드 추정) |
| 가득 참 진입 | Max(8f, 알파 0→255), LoopMax(120f 반복, 무지개 정점색), LoopGauge(2000f 반복, 번개 무늬 회전) | 안쪽 무늬·아이콘 빛남, 스틱 누르기 그림(N_MaxAll_00, Loop 애니로 흔들림) |
| 가득 + 같은 대상 | InText(120f) | "풀 충전!" 왼쪽에서 들어옴 |
| 가득에서 내려감 | Max 정지, LoopMax/LoopGauge 일시정지, OutText(16f) | 문구 사라짐 |
| 특수 발동 | Decide(6f, 배율 1→0.5, 알파 →0) | 재생 주체 **[미확정]** → 2026-10-03 [r6 ui]: **원본에서 재생하는 경로 없음** [판독]+[데이터] (아래) |
| 등장 | Appear(8f) | |

- Decide 재생 주체(2026-10-03 [r6 ui]) [판독]+[데이터]:
  - 애니 핸들은 콤마 이름 목록 문자열로 만들어집니다. `SplUISuperGaugeCtrl`의 목록은 `LoopGauge, Max, LoopMax, InText, OutText, Coop, Item, Mission, OutMax`입니다. 이 목록에도, `Lobby_GuideBtn_00`(`Change, Signal, Nice, Chat, ToMatch`)·`VS_MainTV_00`(파츠 애니는 `L_파츠$애니` 형식) 목록에도 `Decide`나 `L_SuperGauge_00$Decide`가 없습니다.
  - main 전체에서 `Decide\0`로 끝나는 문자열 9곳(꼬리 병합 포함)을 ADRP 참조와 데이터 포인터로 전수 검색했습니다. 참조는 `0x7104911ec8` 한 곳뿐이고, 사용처 4곳(`0x71038cae08`·`0x71038cf484`·`0x71038d1004` = 버튼 컨트롤 vtable 슬롯 41, `0x71038d7cd0` = Select/TouchSelect/…/Cancel 목록)은 모두 nn::ui2d 버튼 컨트롤(NormalButton 등)의 기능 애니 이름입니다. 앞 판의 `0x71038d7c3c`는 함수 경계 오인입니다. `SuperGaugeTV_00`에는 버튼 컨트롤이 없습니다(§3.5 cnt1 = TraceGauge).
  - romfs에서 `SuperGauge`를 담은 파일은 ELink2·SLink2·Mals·LayoutArchiveCategory뿐이고, 그 안에 Decide 키는 없습니다.
  - 결론: `SuperGaugeTV_00_Decide.bflan`은 데이터에만 있고 제품 코드가 재생하지 않습니다. 웹에서는 재생하지 않습니다.
  - 한계: AINB 등 다른 데이터가 이름을 실행 중에 조립하는 경로는 `SuperGauge` 문자열 0건으로 배제했습니다.

- `N_SuperGauge_00`의 `EffectLinkOn: LoopMax`는 LoopMax 애니와 이펙트를 묶는 표시로 보입니다. 어떤 이펙트인지는 [effect_sound] 영역입니다 **[미확정]**. 2026-10-03 [r5 ui]: 이 키를 읽는 코드는 `0x71038f7bc8`(개수 세기), `0x7103901da0`(페인·애니 목록 항목 0x60 B 등록), `0x7103902290`(값 문자열 파싱) 셋입니다 [판독: 위치만]. 값 문자열과 애니 이름의 결합, 이펙트 이름 결정은 아직 읽지 않았습니다. 다음에 볼 곳: `0x7103902290` 파싱 뒤 호출, ELink 사용자 이름.
  - 2026-10-03 [r6 ui] 확정 [판독]+[데이터]:
    - 등록 `0x7103901da0`: 레이아웃을 재귀로 돌며 `EffectLinkOn`이 있는 페인마다 0x60 B 항목 {페인, 레이아웃, 경로}를 만듭니다. 경로는 파츠 깊이 n에 따라 `"%s/%s"`(상위 파츠 루트 페인 이름들 + 페인 이름)이고, 여기서는 `L_SuperGauge_00/N_SuperGauge_00`입니다.
    - 파싱 `0x7103902290`: 값을 콤마로 나눕니다(`"-"`는 없음). 이름마다 레이아웃 애니 목록에서 애니 이름이 같은 AnimTransform을 찾아 {AnimTransform, 키} 쌍(0x18 B)을 만듭니다. 키는 항목 경로에서 페인 이름 부분을 애니 이름으로 바꾼 문자열입니다 → **`L_SuperGauge_00/LoopMax`**.
    - ELink 데이터(`analysis/effect_sound/elink2_users.json`): 액션 슬롯 이름이 바로 이 키인 사용자가 둘 있습니다.
      - `#b85f0970`: 에셋 `UIGaugeMax`
      - `#baad4149`: 에셋 `LayoutGaugeMax`, EffectGroup `Main2D`. 같은 사용자의 `L_SuperGauge_00/SendNice`는 `LayoutGaugeSendNice`
      - 공통: Bone `L_SuperGauge_00/N_SuperGauge_00`, Scale 5.0, ForceTeam = 로컬 속성 Team(곡선 (−1,−1)~(3,3)), BitFlag 14
    - 어느 사용자가 어느 화면(VS/Lobby)인지는 사용자 이름 해시 역산을 못 해 [미확정]입니다.
    - 키를 ELink 액션으로 켜는 시점(LoopMax 재생 중인지)은 소비 함수를 읽지 않아 [미확정]입니다. 다음에 볼 곳: 0x18 B 쌍 표(파싱 결과, 소유 객체 +8)를 읽는 함수.
- 캡처 구조: `N_CapSp_00`(특수 무기 아이콘 파츠 `CmnIconSubSpecial_00`)을 정적 캡처 → 원판 아이콘(`P_BaseIconSp_00`)과 잉크 모양 합성(`P_CapUse_00/02`, 텍스처 슬롯 1)에 씁니다. `N_Cap_00`(흰 게이지)은 매 프레임 캡처 → 흐림 → 빛번짐 2장.
- 소리: SuperGauge 컨트롤 코드에서 소리 호출은 보지 못했습니다. 가득 참 소리는 플레이어 쪽에서 날 가능성이 큽니다 **[미확정]**.
  - 정정(2026-10-03 [r6 ui]) [판독]+[데이터]: 가득 참 소리는 플레이어가 아니라 **UI 애니 재생 이벤트**에서 납니다.
    - AnimTransform "처음부터 재생"(`0x71038f2efc`, 명령 1의 vt+0xb8)과 지정 프레임 재생(`0x71038f328c`)은 플래그 +0x54 bit5(이벤트 알림)가 켜져 있으면 (+0x58 레이아웃 래퍼)+0x88의 vt+0x298(화면 기본 `0x71038f8564`)을 접미 `"_play"`와 함께 부릅니다.
    - 이 함수는 `"anim_"` + `0x71038fff40`(파츠 경로를 `"-"`로 이은 애니 이름) + `"_play"` 키를 만들어 화면의 xlink(화면+0x160 vt+0xf0, `searchAndEmit`)로 보냅니다. TraceGauge init은 Gauge 애니 둘의 bit5를 지우므로 게이지 애니는 이벤트를 내지 않습니다.
    - SLink 데이터(`analysis/effect_sound/slink2_users.json`): 키 **`anim_L_SuperGauge_00-InText_play` → 에셋 `Pl_SpecialGaugeFull_00`**(GroupName `UI_PauseOn`, Priority 0.9, Pan 0.7, SpeakerBalanceType 1, BitFlag 11). 사용자 다섯 개에 같은 값으로 들어 있습니다.
      - 사격장 화면 사용자: `#12b3e87d`. 같은 사용자에 `anim_L_GuideBtn_00-Decide_play` 등 `Lobby_GuideBtn_00` 파츠 키가 있어 그렇게 판단했습니다 [데이터 대조].
      - 대전 사용자: `#731b5f69`(`OverTime` 함께 있음).
    - 결론: "풀 충전!" 문구(InText, §5.2: 같은 관전 대상일 때만)가 재생되는 프레임에 소리가 납니다. 관전 대상을 바꾼 프레임처럼 InText가 생략되면 소리도 나지 않습니다 [판독: 키 경로].
    - 웹: 소리를 게이지 비율이 아니라 InText 재생 명령에 묶습니다.

## 8. 다른 기능과의 상호작용

| 상대 | 연결 | 상태 |
|---|---|---|
| [gauge] 특수 포인트 → 비율 | `D+0xbe4` = 게이지 텍셀 / (int)(SpecialPoint×211.2), 가산 = 스페셜용 칠 텍셀 × 배율(+0xe8) + 역경 강화 + 규칙 가산 — [special_gauge.md](../paint/special_gauge.md) | [판독]+[실행(에뮬 구간)] |
| [paint] 칠 포인트 | `D+0xbd4 / 211.2` — 결과 집계와 같은 식 | [판독] 일치 |
| [paint] 우세 단계 | `VersusRefereePaint` → 화면+0x4c8 | [판독] ([elements §7](ui_vs_maintv_elements.md)) |
| 관전(관전 대상 전환) | HUD 관리자+0x27c 변경 → 같은 프레임 `showFullText = false` → 문구 생략 | [판독] |
| 모드 | 같은 디스패처가 Lobby(+0x278)·Coop(+0x2d0)·Msn(+0x320) 화면 게이지에도 씀 | [판독] |
| 일시정지 | `L_Info_00`(PauseText_00) 표시. 연결 코드 미판독 | [미확정]. 사격장에서는 대전 화면이 없고, 메뉴(`SplMainMenu` 인터럽트, `XMenu`)는 분석 범위 밖 |
| 잉크(사격장) | 슈터 잉크 검사 실패 → `Cmn_NoInk_00` kind 0 (§5.5). 잔량 표시는 3D 탱크 `PlayerTank` | 화면 [실행]+[판독], 탱크 표시 [미확정] |
| 네트워크 | 다른 플레이어의 `D+0xbe4`는 PlayerNetState+0x7c(7비트 %, 가득=100, 그 외 최대 99)에서 `min(p/100, 0.99)`(100이면 1.0)로 복원, 조건부 0.3 지수평활. 그래서 관전 중 다른 플레이어 게이지는 1% 단위로 움직이고 99%에서 멈췄다가 100%에서 가득이 됨 | [판독]+[실행(에뮬 구간)] |

## 9. 웹 포팅 구조와 구현 순서

### 9.1 모듈

| 모듈(웹 권장 이름) | 책임 | 원본 대응 |
|---|---|---|
| `LayoutAssets` | VersusSync 카테고리 레이아웃 JSON·텍스처 PNG·폰트·MSBT 로드 | LayoutArchiveCategory, blarc |
| `LayoutInstance` | 페인 트리, 행렬(부모 원점 + T·Rz·S), 알파 전파, 파츠 인스턴스(별도 레이아웃) | nn::ui2d::Layout |
| `AnimTransform` | 애니 1개 인스턴스: 프레임, 곡선 평가(에르미트·계단), 대상 쓰기(FLPA/FLVC/FLVI/FLMC/FLTS/FLTP/**FLEU**) | `0x71038db1d8`가 만드는 0x68 B 객체 |
| `AnimHandle` | 명령 코드 0~11 → AnimTransform 재생 제어(§5.3 표), 화면 calc 마지막(슬롯 73)에 일괄 처리 | 핸들 +0x10/+0x14/+0x18, `0x71013686f8` |
| `TraceGauge` / `SuperGaugeCtrl` | §6.2, §5.2 | `0x71038d6748`, `0x710317426c` |
| `TimerCtrl`, `MultiNumberAnim`, `PlayerIconCtrl` | [elements §4~§6](ui_vs_maintv_elements.md) | |
| `VsMainTvScreen` | 컨트롤 묶음, 리셋, 우세·리드 | `SplUIVSMainTV00Screen` |
| `HudBinder` | 매 프레임 게임 상태 → 화면 (특수 비율·칠 포인트·타이머·아이콘 상태) | HUD 관리자 `0x710275c1ac`, 디스패처 |
| `UiRenderer` (WebGL) | 재질(흑/백 보간 × 텍스처 × 정점색 × 알파), 블렌드, **캡처(렌더 타깃)**, 사용자 셰이더(MeterAction). 사용자 셰이더 인자는 usd1 이름 `__CUS_Float_N` → 유니폼 `nwExUserDataFloat_N`(§6.5) | ui2d 그리기, `0x7100867134` |
| `LobbyGuideScreen` (사격장) | `Lobby_GuideBtn_00` 레이아웃 + `SuperGaugeCtrl`(+0x278). init에서 target 0 | `SplUILobbyGuideBtn00Screen`, §5.4 |
| `NoInkScreen` (사격장) | §5.5 요청·갱신, 텍스트 kind 표, 열기/닫기 상태 | `SplUICmnNoInk00Screen` |

Canvas2D/DOM보다 WebGL을 권합니다. 사용자 셰이더, 가산 블렌드, 캡처+흐림을 원본과 같은 순서로 재현해야 하기 때문입니다.

### 9.2 상태 객체

```ts
interface PlayerHudInfo {          // 원본 D (플레이어 정보 블록)
  specialRatio: number;            // +0xbe4 f32
  specialPoint: number;            // +0xbe8 f32 필요 p (정수로 잘라 키에 씀)
  paintTexels: number;             // +0xbd4 u32
  downCounters: [number, number, number, number]; // +0xd60,+0xde0,+0xdf0,+0xe0c
  absent: boolean;                 // +0xe59
}
interface HudBinderState { watchedIndex: number /* +0x27c */; lastFullKey: number /* +0x3d8 */ }
interface TraceGauge { target: number; value: number; trace: number; traceSpeed: number; traceFraction: number;
  shortageLevel1: number; shortageLevel2: number; traceWaitLeft: number; traceWait: number;
  jumpFraction: number; jumpMin: number; traceEnabled: boolean;
  animGauge: AnimTransform; animTrace: AnimTransform; animTraceColor?: AnimTransform; animShortage?: AnimTransform }
interface SuperGaugeCtrl extends TraceGauge { showFullText: boolean; suppressMaxTextOnce: boolean; iconSwapped: boolean;
  anim: Record<'loopGauge'|'max'|'loopMax'|'inText'|'outText'|'coop'|'item'|'mission'|'outMax', AnimHandle> }
```

### 9.3 매 프레임 순서

```ts
function frame(game: GameState) {
  hudBinder.update(game);      // §3: setSuperGaugeRatio, setPaintPoints, (타이머 값), 아이콘 입력
  // 화면 calc (§5.3): 슬롯39 → 슬롯65 → 슬롯73
  superGauge.update();         // 슬롯13(모듈 링 +0x48): 가득 참 판정 (target != value 일 때), 핸들에 명령만 기록
  vsMainTv.update();           // 화면 슬롯100: 우세·리드 애니 (0x71033dbacc) — 원본은 컨트롤 슬롯13 다음
  traceGaugeUpdate(superGauge, dt /* 대전 1.0 */);   // 슬롯4(컨트롤 목록)
  timer.update(); icons.forEach(i => i.update()); paintNumbers.update();
  animHandles.forEach(h => h.flush());   // 슬롯73: 명령 → AnimTransform, enable 시 레이아웃 목록 끝으로 이동
  layout.animate();            // 0x71038f67f8: 목록 순서대로 Animate(같은 대상은 나중 것이 이김) → 재생 중이면 UpdateFrame(dt), 정지면 끄고 목록에서 뺌
  renderer.draw(layout);       // 캡처 패스 → 본 패스
}

function hudBinderUpdate(s: HudBinderState, players: PlayerHudInfo[]) {
  const i = s.watchedIndex;
  if (i < 0) { setSuperGaugeRatio(false, 0); setPaintPoints(0); s.lastFullKey = 0; return; }
  const d = players[i];
  const key = Math.trunc(d.specialPoint) + i * 1000;            // fcvtzu 후 madd
  const full = d.specialRatio >= 1.0 ? (s.lastFullKey === key) : false;
  setSuperGaugeRatio(full, d.specialRatio);
  setPaintPoints(Math.trunc(Math.fround(Math.fround(d.paintTexels) / Math.fround(211.2))));
  s.lastFullKey = key;
}
```

### 9.4 원본과 똑같이 지킬 것

- 비율은 `min(r,1)×75`로 **f32** 계산, 음수는 0, 범위 밖이면 target을 바꾸지 않음.
- `value`는 디스패처가 아니라 **TraceGauge 갱신에서** 바뀐다. 가득 참 판정은 그 전에 한다.
- 감소 + 점프 없음 프레임에는 추적값을 움직이지 않는다(다음 프레임부터 움직임).
- 값과 추적값이 같고 변화가 없으면 애니 프레임을 다시 쓰지 않는다(다른 애니가 같은 대상을 덮어썼다면 그 값이 남음).
- 칠 포인트는 `(f32)u32 / 211.2f` 후 0 방향 절삭.
- 같은 `Gauge` 애니를 두 인스턴스로 만들고, setFrame/재생 때 목록 끝으로 옮기며, 목록 순서대로 적용한다. 정지(speed 0)된 인스턴스는 한 번 적용 후 끄고 목록에서 뺀다(§5.3 적용 루프). 결과적으로 TraceRatio가 이긴다(§6.4 확정).

### 9.5 구현 순서

1. 변환: VersusSync 19개 레이아웃 JSON·PNG, BlitzMain/AsiaKERIN 폰트, KRko MSBT ([format §8](ui_layout_format.md)).
2. `LayoutInstance` + 정적 렌더(파츠 포함) → `analysis/ui/render/vs_maintv_ko_sample.png`와 배치 비교.
3. `AnimTransform`(FLEU 포함) → `SuperGaugeTV_00_Gauge` 프레임 0/37.5/75 확인.
4. 캡처·블렌드·MeterAction 셰이더.
5. `TraceGauge`·`SuperGaugeCtrl` → `hud_sim_out.txt`와 같은 프레임 값.
6. 타이머·칠 포인트·아이콘·우세.
7. `HudBinder`를 게임 상태([paint]·[player] 결과)에 연결.

## 10. 검증

| 종류 | 내용 | 결과 |
|---|---|---|
| [실행: 자체 도구] 파서 | `ui_lyt.py survey` 348 bflyt / 2,119 bflan | 버전 전부 9.0.0.0, 크기 검증 347/348 일치(나머지 1건은 HUD 무관 재질 bit19) |
| [실행: 자체 도구] MSBT | KRko 296개 | 전부 파싱 |
| [실행: 자체 도구] 폰트 | BlitzMain.bfotf, AsiaKERIN-M.bfttf 복호화 | `OTTO`, `00010000` 헤더 |
| [데이터] Gauge 곡선 | 프레임 0/18.75/37.5/56.25/75 → 0.75/0.5625/0.375/0.1875/0 | 직선식과 일치 |
| [재구현] 디스패처 | r = −0.5/0/0.3/0.999/1/1.7 → 0/0/22.5/74.925/75/75 | |
| [재구현] 상승 0→1 (리셋 후 40프레임 정착) | 1프레임에 trace 2.0, 10프레임 20.0, 20프레임 40.0, 38프레임 75.0(가득) | 표시 = min(value, trace) 가정 |
| [재구현] 감소 1→0.4 | value 즉시 30.0, trace 75→73→…(2.0/프레임), 23프레임에 31.0 | |
| [재구현] 칠 포인트 | 211→0p, 212→1p, 2112→10p, 211200→1000p | |
| [실행(에뮬 구간)] 게이지 값 원천 | `web/tools/gauge_emu.py`: 비율(G+0x10)·넷 %·가산 구간을 원본 명령으로 실행 | 재구현과 전부 일치([special_gauge.md §10](../paint/special_gauge.md)) |
| [재구현] 타이머 | 10800f→"3:00", 10799f→"3:00"(올림) / 179s(내림), 59.5f→0:01 | 대전 타이머는 올림(생성자 +0x148=1, fps 60 [판독]) → "3:00"이 1프레임 뒤에도 유지, 마지막 1프레임까지 "0:01" |
| [재구현] 아이콘 상태 | 빈 슬롯 →(2,F), 게이지 1.0·준비 →(0,T), 사망 카운터>0 →(1,F) | |
| [실행: 자체 도구] 렌더 | `vs_maintv_ko_sample.png`, `supergauge_frames_0_37.5_75.png` | 배치·한국어·게이지 채움 해석 확인 (원본 화면 대조 아님) |

| [실행(에뮬)] 애니 핸들 명령 | `web/tools/ui_animcmd_emu.py` 원본 `0x71013686f8` 명령 0~12 | 13 PASS (§5.3) |
| [실행(에뮬)] 표시 min/max | `web/tools/ui_animorder_emu.py` 원본 TraceGauge 갱신→setFrame→enable→적용 루프 연결, 감소·증가 28프레임 × 초기 순서 2가지 | 56 PASS, 표시 = min(value, trace) (§5.3, §6.4) |
| [실행(에뮬)] 잉크 부족 화면 | `web/tools/r5_ui_noink_emu.py` 원본 `0x7103276e2c`(요청)·`0x7103277148`(갱신)과 상태 질의 `0x7101363e48/6c/ec4`를 프레임마다 실행, 독립 재구현과 필드 5개·핸들 명령 2개·이벤트(열기/닫기/텍스트) 비교 | 6시나리오 **317/317 프레임 일치** → `analysis/r5_ui/noink_emu.json` (§5.5) |
| [데이터] 사격장 레이아웃 묶음 | Bootup 팩 `LobbyVersus.game__SequenceComponentParam` | VersusSync 없음, LobbySync·GameCommon·Lobby 적재 (§1.1) |
| [데이터] FLEU 대상 이름 | `web/tools/r5_ui_fleu_names.py` 전 레이아웃 bflan | user 태그 353개 모두 이름 있음(§6.5, [format §3.3](ui_layout_format.md)) |
| [실행(에뮬)] dt 배수 플래그 사슬 (2026-10-03 [r6 ui]) | `web/tools/r6_ui_fps30_emu.py`: 씬 시작/종료 구간 + preCalc_ 구간 + UI 프레임 `0x7101026dd0` + 프레임 끝 `0x7103502d10`, 씬+0x354 4가지 × n 열 2가지 × 6프레임 | **8/8 일치**(§5.3) → `analysis/r6_ui/fps30_emu.json` |
| [데이터] SceneAttr_Fps30 씬 | `RSDB/Tag` 비트 표 디코드(`analysis/r6_ui/Tag.json`) | Plaza만 켜짐, LobbyVersus 꺼짐(§5.3) |
| [실행(에뮬)] MSBT 숫자 태그 (2026-10-03 [r6 ui]) | `web/tools/r6_ui_msbt_num_emu.py`: 원본 `0x7101360544`(그룹 2 종류 0)을 태그 10가지 × 값 9개로 실행 | 결과 표 [format §7](ui_layout_format.md) → `analysis/r6_ui/msbt_num_emu.json` |

스텁·미검증 범위: Animate(vt+0x28)·UpdateFrame(vt+0x18) 내부(에뮬에서 스텁; 적용 루프·setFrame·enable은 원본 실행), 캡처·블러·블렌드 결과, 사용자 셰이더(상수 버퍼 위치는 §6.5에서 판독으로 확정, 셰이더 실행 결과는 미검증), 30fps 모드 dt, 팀 색, 잉크 부족 화면의 열기/닫기 내부와 화면 상태 바이트 전이(§5.5 스텁).
- 2026-10-03 [r6 ui] 갱신:
  - "30fps 모드 dt"는 플래그 사슬을 원본으로 실행해 검증 범위에 들어왔습니다. 다만 태그 표 찾기는 데이터 디코드로 대신했습니다.
  - dt 사슬 에뮬 스텁: 프레임워크 가상 호출 6개, `0x710138475c`, `0x71035031ec`, `0x7103509808`, `0x7103e9a3d0`.
  - MSBT 에뮬 스텁: libc PLT(memcpy 등)를 파이썬 구현으로 바꿨습니다.
  - 팀 색은 적용 경로만 판독했습니다([format §3.4](ui_layout_format.md)). 실제 색 값은 [graphics] 세트를 따릅니다. 재구현 시험은 **함수 단위 합성 테스트**이고 화면 전체 동작 검증이 아닙니다. 다시 실행: `.venv/Scripts/python analysis/ui/hud_sim.py`.

## 11. 미확정과 필요한 근거

| 항목 | 이유 | 필요한 근거 |
|---|---|---|
| ~~`D+0xbe4` 특수 비율을 쓰는 코드~~ | 해소(2026-10-02 [gauge]): 로컬 `0x7102483134`, 원격 `0x7102475a54` — §4.1 | 남은 것: 스페셜 시작 시 G+0x1c/+0x20 writer |
| ~~`D`(플레이어 +0x108) 클래스 이름~~ | **확정 불가**(2026-10-03 [r5 ui]): vtable `0x7105632a60`은 4슬롯이고 getName 슬롯이 없으며 뒤는 액터 이름 표, main에 게임 RTTI 없음(§4.1) | 바이너리에 이름이 없음. 웹 이름 `PlayerBody` |
| ~~TraceRatio·GaugeRatio 적용 순서(표시가 min인지 max인지)~~ | 해소(2026-10-02 [camrest]): 적용 루프 0x71038f67f8 판독 + 원본 연결 에뮬 56 PASS → min(§6.4) | 남은 것: Animate 재질 쓰기 내부 실행, 원본 화면 대조 |
| ~~MeterAction 시작각·방향·`__CUS_Float_1/2`~~ | 해소: 원본 GLSL 소스(§6.5) | ~~`nwExUserDataFloat_N` ↔ usd1 이름 대응~~ 해소(2026-10-03): `0x7100867134` 이름→상수 버퍼 +0x120+4N, 셰이더 data[18] [판독] |
| ~~`dt` 값, 컨트롤 갱신 호출 순서(슬롯 13 vs 4)~~ | 해소(2026-10-02 [camui]): 슬롯 13 → 슬롯 4 같은 프레임, dt = 1.0(60fps) — §5.3 | ~~dt 배수 플래그 setter~~ 해소(2026-10-03 [r6 ui]): 씬 태그 `SceneAttr_Fps30`(Plaza만) → 씬 시작 `0x710131fac4`가 SystemTask+0x458 bit0 설정, 종료 `0x71013207f0`가 해제. 사격장 dt = 1.0 [판독]+[데이터]+[실행 8/8]. 남은 것: 게임 갱신(`spl::Spectator` 슬롯 21)과 UI calc의 상위 순서 [미확정]. 둘 다 프레임워크 calc `0x71035031ec`의 메서드 트리(`0x7103505738`) 안이라 노드 연결 순서가 결정함 — 다음: 액터 시스템·UI 레이어 calc 노드 attach 호출 |
| ~~애니 핸들 명령 코드 의미~~ | 해소: §5.3 표 + 원본 에뮬 13 PASS | ~~ui2d 적용 루프 `0x71038f67f8` 이후~~ 해소(§5.3) |
| ~~타이머 `+0x140` 갱신 주체, fps·올림~~ | 해소: 생성자 `0x710314cc9c`가 올림=1·fps=60, 공급 `0x7103096214`가 매 프레임 max(종료프레임−GameFrame, 0) — [elements §4](ui_vs_maintv_elements.md) | 종료프레임(규칙 객체 +0x50) writer |
| ~~MSBT 숫자 태그 파라미터 의미~~ | 해소(2026-10-03 [r6 ui]) [실행]: 처리 함수는 `0x7101362370`(메시지 찾기)이 아니라 게임 TagProcessor(vtable `0x710557cce0`) 슬롯 22 `0x7101360478` → 그룹 2 `0x7101360544`. p0 = 인자 번호, p1 = 자릿수, p2 = 채움(0 없음/1 '0'/2 공백), 숫자는 전각 — [format §7](ui_layout_format.md) | p3의 효과(이번 시험에서 차이 없음) |
| ~~"위험해!"(Pinch) 조건~~ | 해소: TerritoryGauge_00/03 애니가 Pinch 페인 알파를 움직임(우세 단계 0/4 = 차 15.01% 이상) — [elements §7](ui_vs_maintv_elements.md) | |
| ~~Decide 애니 재생 주체~~ | 해소(2026-10-03 [r6 ui]) [판독]+[데이터]: 재생하는 원본 경로 없음. 참조 4곳은 nn::ui2d 버튼 컨트롤 기능 애니(슬롯 41 `0x71038cae08`/`0x71038cf484`/`0x71038d1004`, `0x71038d7cd0`; 앞 판의 `0x71038d7c3c`는 경계 오인), SuperGauge·화면 핸들 목록에 Decide 없음, romfs에도 없음 — §7 | 웹: 재생하지 않음 |
| ~~가득 참 소리~~ | 해소(2026-10-03 [r6 ui]) [판독]+[데이터]: InText 재생 이벤트 키 `anim_L_SuperGauge_00-InText_play` → SLink `Pl_SpecialGaugeFull_00` — §7 | |
| `EffectLinkOn: LoopMax` 이펙트 | 이펙트 확정(2026-10-03 [r6 ui]): 키 `L_SuperGauge_00/LoopMax` → ELink `UIGaugeMax`/`LayoutGaugeMax`(Main2D), Bone `L_SuperGauge_00/N_SuperGauge_00`, Scale 5 — §7 | 키를 액션으로 켜는 시점, 사용자 ↔ 화면 대응 |
| ~~잉크 부족 화면 조건~~ | 사격장(슈터) 해소(2026-10-03): 요청 = 슈터 잉크 검사 실패 && 본체+0x1058 == 0 → kind 0([paintgpu] 판독), 화면 요청·갱신·표시 시간·문구 = §5.5 [실행] | `0x71024eb9b8`(GoldenIkura·소지물 던지기 경로)는 연어런·가치 매치용이라 사격장 범위 밖 |
| 사격장 잉크 잔량 표시 | 2D 게이지 없음 [데이터]. 3D 탱크 `PlayerTank`(`spl::PlayerCustomTank`) 잔량 → 표시 식 미추적 | [gfx_char]/[player]: `PlayerTank.root.asb`, `spl::PlayerCustomTank` 갱신 |
| 사격장 조준점·히트마커 조건 | 이펙트(`PlayerShotGuide` ELink)로 연결 확정 [데이터], 상태 결정·위치는 [r5 combat] 진행 | `0x7102677578`, `0x7102678304`, 상태 이름 표 `0x710267e51c` |
| 레이아웃 → 실제 화면 투영 | 레이아웃 1920×1080 가상 화면 [데이터], 출력 해상도 변환 코드 미판독. 2026-10-03 [r6 ui] [판독, 부분]: 레이아웃 사각형은 항상 중심 원점(`0x7100859058`), 캡처(`0x71038e8728`)·가위(`0x71038e9e10`)가 화소 배율 = RT 크기 / 레이아웃 크기 — §1.1 | 본 그리기 투영 행렬 설정 함수, 그리기 정보 +0x1a0(RT) writer |
| ~~`0x7100fe8750` 시험 블록~~ | 해소(2026-10-03 [r6 ui]) [판독]+[데이터]: 개발용 시퀀스 `GameSeqUICheckGuide`(vtable `0x7105551d60` 슬롯 36)의 `VS_MainTV_00` 점검 분기. 제품 씬 표에 이 시퀀스 없음 — §3 | |
| `Shr_InkReset_00` 호출 조건 | 시퀀스 노드 `SplLobbyInkReset`, 문자열 참조 `0x7102d9cc6c` 3곳 | `0x7102d9cc6c` 호출자 |
| 미니맵 | 분석 진행(2026-10-02 [camrest]: 축 규약·열기 입력·슈퍼점프 결정 메시지·맵 셰이더 추가): [ui_minimap.md](ui_minimap.md) | 그 문서 §11 |
| 결과 화면 칠 % | 값(PaintPermille)·미터 애니 프레임 해소([special_gauge.md §6.8~6.9](../paint/special_gauge.md)). 문자열 형식은 [paintgpu]가 해소([elements §8](ui_vs_maintv_elements.md)) | 대전 결과 화면이라 사격장 범위 밖 |
