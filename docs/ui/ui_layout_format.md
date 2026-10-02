# UI 레이아웃·리소스 포맷 (Splatoon 3 v0)

[ui_hud.md](ui_hud.md)의 하위 문서입니다. 대전 HUD를 웹에서 재생하는 데 필요한 **파일 포맷, 화면 정의 표, 폰트, 메시지, 아이콘 텍스처**를 정리합니다. 코드 쪽 동작(값 바인딩)은 [ui_hud.md](ui_hud.md), 화면 요소별 정리는 [ui_vs_maintv_elements.md](ui_vs_maintv_elements.md)에 있습니다.

확정 수준 표기는 [README](../README.md)를 따릅니다. 자체 파서·렌더러를 돌려 확인한 결과는 **[실행: 자체 도구]**로 적습니다. 원본 게임을 실행해 확인한 항목은 없습니다.

## 1. 자료 위치

| 항목 | 위치 | 비고 |
|---|---|---|
| 레이아웃 | `extracted/romfs/Layout/<이름>.Nin_NX_NVN.blarc.zs` (348개) | zstd(사전 없음) → SARC |
| 레이아웃 묶음 표 | `extracted/romfs/UI/LayoutArchiveCategory.Product.100.byml.zs` → `analysis/ui/LayoutArchiveCategory.json` | 카테고리 → 레이아웃 이름 목록 |
| 화면 정의 | `RSDB/UIScreen.Product.100.rstbl.byml.zs`(152행), `RSDB/UIScreenInfo.Product.100.rstbl.byml.zs` → `analysis/ui/UIScreen*.json` | |
| 폰트 | `extracted/romfs/Font/Font[_KRko/_CNzh/_TWzh].Nin_NX_NVN.bfarc.zs` | zstd → SARC(FCPX + 암호화 OTF/TTF + FFNT 1개) |
| 메시지 | `extracted/romfs/Mals/<언어>.Product.100.sarc.zs` (14개 언어) | zstd → SARC(MSBT 296개, KRko) |
| 공용 아이콘 | `extracted/romfs/UI/Icon/*.bntx.zs` | 이번 범위에서는 열지 않음 |
| 덤프 | `analysis/ui/layout/<레이아웃>/`(bflyt/bflan JSON, 페인 트리 txt), `analysis/ui/msbt_KRko/`(MSBT JSON 296개), `analysis/ui/tex/`, `analysis/ui/font/`, `analysis/ui/render/` | 대량 변환은 하지 않고 HUD 관련 레이아웃 19개만 덤프 |

| 도구 (`web/tools/`) | 하는 일 |
|---|---|
| `ui_sarc.py list/extract` | SARC 목록·추출. `.zs`면 zstd를 먼저 푼다(mpj 복사본 수정) |
| `ui_lyt.py dump/survey` | BFLYT/BFLAN → JSON, 페인 트리, 섹션 크기 검증(mpj 복사본 + 재질 bit20) |
| `ui_msbt.py <출력폴더> <msbt...>` | MSBT → JSON(라벨→문자열, 제어 태그는 `[그룹:태그:파라미터hex]`) (mpj `msbt.py` 복사본) |
| `ui_font.py list/otf` | 폰트 아카이브 목록, FCPX 구성 폰트, BFOTF/BFTTF 복호화 |
| `ui_render.py` | 레이아웃 정적 렌더 시험(파츠·FLEU·캡처·MeterAction 근사·한국어 문자열) |
| `graphics_bntx.py png` | [graphics] 도구. `timg/__Combined.bntx` → PNG (수정 없이 사용) |

## 2. 레이아웃 아카이브 `.blarc.zs` [데이터]

zstd를 풀면 SARC(리틀엔디언, 해시 키 0x65, 이름 표 있음)입니다. Jamboree의 `.lyt`와 같은 구조입니다.

| 경로 | 내용 |
|---|---|
| `blyt/<레이아웃>.bflyt` | 레이아웃 1개(아카이브 이름과 같음) |
| `anim/<레이아웃>_<애니>.bflan` | 애니메이션. 코드는 `<애니>` 이름으로 찾는다(예: `SuperGaugeTV_00_Gauge.bflan` → `Gauge`) |
| `timg/__Combined.bntx` | 이 레이아웃이 쓰는 텍스처 전부 |
| `bgsh/__ArchiveShader.bnsh`, `.bushvt` | 레이아웃 전용 셰이더(사용자 셰이더 포함) |

**파츠(`prt1`)는 같은 아카이브가 아니라 다른 `.blarc.zs`**를 가리킵니다. 예: `VS_MainTV_00`의 `L_SuperGauge_00` → `SuperGaugeTV_00.Nin_NX_NVN.blarc.zs`. 파츠 텍스처도 그 파츠 아카이브의 `__Combined.bntx`에 있습니다. 어떤 아카이브를 미리 함께 올리는지는 `LayoutArchiveCategory`가 정합니다(§5).

## 3. BFLYT/BFLAN v9.0.0.0 [실행: 자체 도구]

`ui_lyt.py survey`로 348개 bflyt와 2,119개 bflan을 읽었습니다. 모두 버전 9.0.0.0이고, 섹션·재질 크기 검증에서 **347/348개가 일치**합니다.

필드 정의는 mpj 문서 `C:/dev/mpj/web/docs/engine/05_ui_input.md` §3과 같아 여기 반복하지 않습니다. 페인 공통 0x4C 바이트, `pic1/txt1/wnd1/prt1/bnd1`, 재질 flags 비트, `cnt1`, BFLAN `pat1/pai1`, 곡선(계단·에르미트) 규칙이 그대로 맞습니다. Splatoon 3에서 다른 점만 적습니다.

### 3.1 관측 통계

| 섹션 | 수 | 페인 종류 | 수 | 애니 태그 | 수 |
|---|---|---|---|---|---|
| `lyt1` | 348 | `pan1` | 3,247 | `FLPA` | 3,711 |
| `usd1` | 2,452 | `pic1` | 3,498 | `FLVC` | 2,765 |
| `mat1` | 344 | `txt1` | 1,029 | `FLVI` | 2,489 |
| `grp1` | 1,952 | `prt1` | 1,337 | `FLMC` / `FLTS` / `FLTP` | 672 / 633 / 580 |
| `cnt1` | 209 | `wnd1` | 822 | **`FLEU`** | **353** |
| `ctl1` | 1 | `ali1` / `bnd1` / `scr1` | 127 / 53 / 18 | `FLIM` 246, `FLFS` 25, `FLCT`/`FLDS` 5, `FLPS`/`FLAC` 2, `FTBR` 4 | |

`lyt1` 화면 크기는 1920×1080, `drawFromCenter` 1입니다(VS_MainTV_00 확인).

### 3.2 재질 flags bit20 = 사용자 셰이더 블록 [데이터]

Jamboree에 없던 비트입니다. 재질 끝(다른 블록 뒤)에 **0x74 바이트**가 붙습니다.

| 오프셋(블록 기준) | 형식 | 내용 |
|---|---|---|
| +0x00 | char[0x60] | 셰이더 키 이름 (예: `MeterAction`, `Circle01`, `Random00`, `RandomMosaic03`, `FestDisappear_00`, `ColorGap_00`, `Gray02`, `BalloonTail_01`, `Gradation00`) |
| +0x60 | RGBA×5 | 상수색. 대부분 `#ffffffff`, `RandomMosaic03` 일부는 첫 색 `#ffffff05`, `Gray02`는 `#808080ff` |

근거: bit20 재질 26개가 모두 이 크기로 섹션 경계와 맞습니다. 필드 이름과 상수색의 의미는 **[추정]**입니다. 남은 1개(`Msn_MFPage_04`)는 bit19 상세 컴바이너 블록 크기가 달라 생기는 차이이고 HUD와 무관해 보류했습니다 **[미확정]**.

셰이더 키가 붙은 재질의 페인은 `usd1`에 `__CUS_Float_0..2` 같은 사용자 셰이더 인자를 가집니다. 이 인자를 BFLAN `FLEU` 태그가 움직입니다(§3.3). 셰이더 본체는 `bgsh/__ArchiveShader.bnsh`(NVN 바이너리)이고, 같은 폴더에 **원본 GLSL 소스** `bgsh/<키>.glsl`과 `CombinerUserShaderVariation.glsl`(`#if NW_COMBINERUSERSHADER_TYPE == N #include "<키>.glsl"`)이 함께 들어 있습니다 [데이터]. 정정: 이전 판의 "판독하지 않음 [미확정]"을 바꿉니다. 소스가 있는 키(아카이브 수): MeterAction(3: SuperGaugeTV_00, HoldText_00, TimerCircle_00), RandomMosaic03(7), ColorGap_00(6), Random00(3), Circle02·RandomMosaic02·RandomMosaicDisappear00(2), BalloonTail_01·Circle01·FestDisappear_00·Gradation00·Gray00·Gray02(1). 소스는 `nwTextureCoord0`, `nwAlbedoTexture0`, `nwConstantColor0/1`(재질 흑/백), `nwExUserDataFloat_0..2`, `vColor`, `OUTPUT_COLOR`, `CalcAlphaProcess`, `FinalAdjustmentFragmentColor`를 씁니다. MeterAction 해석은 [ui_hud.md §6.5](ui_hud.md), [../graphics/shaders.md §5](../graphics/shaders.md). `.bushvt`는 `DTCB` 블록 3개 + `CBUS`(키 이름 "MeterAction")로 시작합니다(필드 의미 [미확정]).

### 3.3 `FLEU` = 확장 사용자 데이터 애니 [데이터]

애니 대상 종류가 2(user)이고, 키 값은 페인 `usd1`의 float 항목에 들어갑니다. `SuperGaugeTV_00_Gauge.bflan`의 예:

```
pat1: 태그 "Gauge", 그룹 G_Gauge_00 = {P_pict_00, P_pict_02}, 프레임 -100..-25 (길이 75)
pai1: frameSize 75, loop 0
  P_pict_00 (user) FLEU 트랙 0: 에르미트 [(0, 0.75, -0.01), (75, 0.0, -0.01)]
  P_pict_02 (user) FLEU 트랙 0: 같은 키
```

기울기 −0.01 × 75 = −0.75라서 이 곡선은 정확히 직선 `값 = 0.75 × (1 − 프레임/75)`입니다([검증 §10](ui_hud.md)). 트랙이 `usd1`의 어느 항목을 가리키는지(이름 일치인지 인덱스인지)는 확인하지 않았습니다. 관측 데이터에서 움직이는 항목은 `__CUS_Float_0` 하나입니다 **[추정]**.

실행 시 애니 적용 규칙(2026-10-02 [camrest], 근거는 [ui_hud.md §5.3](ui_hud.md) 적용 루프 `0x71038f67f8`) **[판독 + 실행(에뮬)]**: 레이아웃의 AnimTransform 목록을 앞에서부터 Animate하므로 같은 대상(같은 페인·같은 usd1 항목)을 여러 애니가 움직이면 **목록 뒤쪽 애니의 값이 남습니다**. setFrame·재생 명령은 그 애니를 목록 끝으로 옮기고, 정지(speed 0) 애니는 한 번 적용된 뒤 꺼져 목록에서 빠집니다. 웹 변환기(§8)가 만든 애니 데이터를 재생할 때 이 순서 규칙을 같이 구현해야 원본과 같은 화면이 됩니다.

### 3.4 페인 사용자 데이터 키 (HUD에서 관측) [데이터]

코드가 페인의 `usd1` 문자열 키로 기능을 켭니다. 이름은 main 문자열에도 있습니다(`EffectLinkOn`, `TeamColorUse`, `CaptureUseName`, `DynamicCaptureUseName`, `TextScaleOn`, `TracingFraction`).

| 키 | 값 예 | 의미 |
|---|---|---|
| `CaptureOn` / `DynamicCaptureOn` | `"RGBA8"` | 이 페인 하위를 텍스처로 캡처한다. Dynamic은 매 프레임 갱신으로 추정 **[추정]** |
| `MultiFilterFile` | `"blur5"` | 캡처에 걸 필터(`UI/MultiFilter.sarc.zs`로 추정) **[추정]** |
| `CaptureUseName` + `CaptureUseIndex` | `"N_CapSp_00"`, `[1]` | 캡처 텍스처를 재질의 텍스처 슬롯 [인덱스]에 꽂는다 **[추정 — 인덱스=슬롯]** |
| `TeamColorUse`, `TeamColorBlack`, `TeamColorWhite` | `"MyTeam"`, `[1]`, `[1]` | 재질 흑/백 색을 팀 색으로 바꾼다. 팀 색 값은 [graphics]의 TeamColorDataSet **[추정]** |
| `EffectLinkOn` | `"LoopMax"` | 애니와 이펙트 연결 **[추정]** |
| `TextScaleOn` | `[0.6]` | 글자 축소 하한(긴 문자열 맞춤)으로 추정 **[추정]** |
| `TracingFraction`, `TracingWait` | `[1.0]`, `[0.0]` | TraceGauge 인자([ui_hud.md](ui_hud.md) §4.2~§4.3) |
| `LocalizeReplaceOn`, `LocalizeReplaceTarget` | `"T_Extend_00"`, `"JPja\nKRko\nCNzh\nTWzh"` | 해당 언어에서 다른 텍스트 페인으로 교체 **[추정]** |
| `__CUS_Float_0..2` | `[0.0]`, `[1.0]`, `[1.0]` | 사용자 셰이더 인자 |

### 3.5 `cnt1` 컨트롤 (HUD 관련) [데이터]

전 레이아웃의 컨트롤 209개는 `analysis/ui/all_controls.txt`에 있습니다. 컨트롤 이름은 코드 클래스 이름과 짝을 이룹니다.

| 레이아웃 | 컨트롤 | 기능 이름 → 레이아웃 이름 | 코드 클래스 |
|---|---|---|---|
| `SuperGaugeTV_00` | `TraceGauge` | GaugeRatio→`Gauge`, TraceRatio→`Gauge`, TraceColor→(없음), Shortage→(없음) | `SplUISuperGaugeCtrl` (TraceGauge 계열) |
| `CircleTimer_00` | `TraceGauge` | GaugeRatio→`Gauge`, TraceRatio→`Gauge` | |
| `CoopInkGauge_00` | `TraceGauge` | GaugeRatio→`GaugeSize`, TraceRatio→`GaugeSizeTrace` | `SplUICoopInkGauge00Ctrl` 문자열 |
| `HeroGauge`, `MsnGauge_00` | `TraceGauge` | GaugeRatio→`GaugeRatio`, TraceRatio→`TraceRatio`(+Msn은 Shortage→`Shortage`) | |
| `Timer_00` | `SplTimer` | 페인 TimeText→`T_Time_00`; 애니 Valid/State/StateCount→`StateCount_00`/StateLoop→`StateLoop_00` | `SplUITimerCtrl` |
| `PaintNumbers_00` | `SplMultiNumberAnim` | FigureBase→`L_Number_00` | |
| `PaintNumber_00` | `SplNumberAnim` | Number→`Number` | |
| `TGPlayerIcon_00` | `Locater` | (없음) | `SplUITGPlayerIconCtrl` |
| `CmnIconSubSpecial_00` | `SplIcon` | Picture→`P_WpnIcon_00`, TexturePattern→`G_TexturePattern_00` | |

`TraceGauge` 기능 이름 목록 문자열 `"GaugeRatio, TraceRatio, Shortage, GuageStart"`(@0x7104886e63)도 main에 있습니다.

## 4. 텍스처 [실행: 자체 도구]

`timg/__Combined.bntx`는 BNTX 4.1이고 [graphics]의 `graphics_bntx.py png`로 디코드됩니다(SuperGaugeTV_00 17개 성공). 이름 접미는 Jamboree와 같은 관례입니다: `^s` BC4 단일 채널(채널 선택 `111R` → 흰색 RGB, 알파=텍스처), `^w`/`^t`/`^r` 기타. 재질 흑/백 색으로 색을 입힙니다.

특수 게이지 텍스처(알파만, `analysis/ui/tex/supergauge_alpha_strip.png`):

| 텍스처 | 크기 | 모양 |
|---|---|---|
| `GaugeSp_00^s` | 256×256 BC4 | **분절된 원호 270°** — 12시에서 시계 방향으로 9시까지, 왼쪽 위 사분면이 비어 있다 |
| `GaugeSp_01^s` | 256×256 | 같은 호(빛남 레이어) |
| `GaugeSp_02^s` | | 바깥 링 + 분절 호 + 왼쪽 위 원형 돌기(특수 아이콘 자리) |
| `VSSuperGaugeBase_00^s` | | 원판 + 왼쪽 위 돌기, 가장자리 흐림 |
| `InkB_00^s` | | 잉크 튐 모양(아이콘 가리개) |

## 5. 레이아웃 묶음과 화면 정의 [데이터]

### 5.1 `LayoutArchiveCategory`

카테고리 25개. 대전 중 HUD는 `VersusSync`(19개)에 들어 있습니다.

```
VersusSync: AreaAddTime_00, AreaPoint_00, ClamPoint_00, ClamPoint_01, ClamTimer_00, CmnIconSubSpecial_00,
            CmnIconWpnPath_00, CmnNamePlate_00, KeyIconType_00, LiftPoint_00, PaintNumber_00, PaintNumbers_00,
            PauseText_00, SuperGaugeTV_00, TGPlayerIcon_00, Timer_00, VS_MainTV_00, VS_ReadyGo_00, VS_StandbyScene_00
Versus(28): VS_Beaten_00, VS_MapLine_00, VS_ResultMeter_00, ResultMeter_00, VS_ShachihokoCount_00 … (결과·연출)
GameCommon(41): Cmn_NoInk_00, VS_Beat_00, VS_PointFlag_00, Cmn_Pause_00 …
MiniMap(3): VS_MapAnnounce_01 등
```

`VS_MainTV_00`이 참조하는 파츠(`SuperGaugeTV_00`, `Timer_00`, `TGPlayerIcon_00`, `PaintNumbers_00`, `PaintNumber_00`, `PauseText_00` …)가 모두 같은 `VersusSync`에 있습니다. 웹에서는 이 카테고리를 한 번에 미리 올리면 됩니다.

### 5.2 `UIScreen` 행 (대전 HUD)

| 필드 | VS_MainTV_00 | Cmn_NoInk_00 |
|---|---|---|
| Class | `SplUIVSMainTV00Screen` | `SplUICmnNoInk00Screen` |
| BodyLayoutFile | `VS_MainTV_00` | `Cmn_NoInk_00` |
| ArchiveCategory | `VersusSync` | `GameCommon` |
| DrawUnitId | 1 | 0 |
| SortKey | 3000 | 3050 |
| IsEnableControl / IsTouch | false / false | false / false |
| UIScreenInfo InstanceHeapSize | 1,190,472 | 19,840 |

`Class` 문자열은 main의 화면 클래스 이름과 같습니다. 이 문자열을 반환하는 함수가 4슬롯짜리 화면 팩토리 vtable(`SplUIVSMainTV00Screen` → `0x710570f6d8`)의 슬롯 2에 있고, 슬롯 3(`0x71033de790`)이 화면 객체(0x620 B, 메인 vtable `0x710570f290`)를 만듭니다 **[판독]**. `SortKey`·`DrawUnitId`가 그리기 순서와 층을 정하는 것으로 보입니다 **[추정 — 소비 코드 미판독]**.

## 6. 폰트 [실행: 자체 도구]

`Font_KRko.Nin_NX_NVN.bfarc.zs` 구성(16개):

| FCPX | 구성 폰트(앞에서부터) | 기준 크기(+0x1C f32) |
|---|---|---|
| `BlitzMain_S` | `BlitzMain.bfotf`, `AsiaKERIN-M.bfttf` | 40.0 |
| `BlitzMain_L` | 같음 | 100.0 |
| `BlitzBold_S/_L` | `BlitzBold.bfotf`, `AsiaKCUBE-R.bfttf` | |
| `SpAlterna_S/_L` | `SpAlterna-Regular.bfotf` | 40.0(_S) |
| `SpDotGothic_S` | `nintendoP_DotGothic12-M.bfotf` ×2 | |
| `Builtin_S` | `nintendo_udsg-r_std_003.bfttf`(롬에 없음 → 시스템 공유 폰트) **[추정]** | |
| `GambitPic` | `GambitPic.bffnt`(FFNT, 아이콘 글리프) | |

- 구성 항목 2번째(아시아 폰트)에는 f32 1.1이 붙어 있습니다. 한글 글리프를 1.1배로 키우는 배율로 봅니다 **[추정]**.
- 페인 `txt1`의 `fontSize`는 1.12 같은 배율이고 픽셀 크기 = FCPX 기준 크기 × fontSize로 봅니다(예: 타이머 `T_Time_00` = 40 × 1.12 = 44.8px). 렌더 시험에서 자연스러운 크기가 나왔습니다 **[추정 — 렌더 시험으로만 확인]**.
- BFOTF/BFTTF 복호화(mpj `decrypt_bfotf`, 매직별 XOR 키): `BlitzMain.bfotf` → `OTTO`(280,136 B), `AsiaKERIN-M.bfttf` → `00 01 00 00`(1,014,052 B). 웹폰트로 바로 쓸 수 있습니다(`analysis/ui/font/`).
- 기본판 `Font.Nin_NX_NVN.bfarc.zs`에는 아시아 TTF 대신 `FOT-RowdyStd-EB`, `FOT-KurokaneStd-EB`가 있습니다(일본어용).

## 7. 메시지 MSBT [실행: 자체 도구]

`KRko.Product.100.sarc.zs` = MSBT 296개(`CommonMsg/`, `LayoutMsg/`, `LogicMsg/`, `EventFlowMsg/`). UTF-16LE, 전부 파싱 성공 → `analysis/ui/msbt_KRko/`.

**레이아웃 문자열 규칙 [데이터]**: `LayoutMsg/<레이아웃>.msbt`의 라벨이 텍스트 페인 이름입니다. 파츠 안 페인은 `<파츠 페인>-<텍스트 페인>`으로 씁니다. `VS_MainTV_00`:

| 라벨 | 한국어 | 비고 |
|---|---|---|
| `L_SuperGauge_00-T_Max_01` | 풀 충전! | 특수 게이지 가득 참 |
| `L_SuperGauge_00-T_Press_00` | 누르기 | 스틱 누르기 안내 |
| `L_PaintNumbers_00-T_Unit_00` | p | 칠한 포인트 단위 |
| `L_Timer_00-T_Extend_00` | 연장 중! | |
| `T_Balloon_00`, `T_Balloon_01` | 위험해! | 위기(Pinch) 말풍선 |
| `T_BalloonLead_00` | 리드! | |
| `T_Rest_00` | 앞으로 | 영역·탑 남은 카운트 |
| `T_Nice_00` | 나이스 | |
| `L_Info_00-T_Info_00` | 일시 정지 | |
| `000` / `001` / `002` | `+[2:0:00020000]` / 이쪽이야 / 당했어 | 코드가 라벨로 직접 고르는 문구 **[추정]** |

`Cmn_NoInk_00`: `000` 잉크 부족!, `002` 꼬마연어 필요!, `003` 사용 불가, `004` 연어알 부족!

**타이머 형식 [데이터]**: `CommonMsg/UnitName.msbt`

| 라벨 | 값 |
|---|---|
| `VSTimer` | `[2:0:00020000]:[2:0:01020100]` |
| `MinSec_1Digit` | `[2:0:00010000]:[2:0:01020100]` |
| `MsnTimer_MinSec` | `[2:0:00020200]:[2:0:01020100]` |
| `MsnTimer_MinSecCentsec_00` | `[2:0:00020200]:[2:0:01020100].[0:2:3200][2:0:02020100][0:2:6400]` |

`[2:0:…]`은 그룹 2 태그 0(숫자 삽입) 제어 태그이고 첫 바이트가 인자 번호(0=분, 1=초, 2=1/100초)입니다. 나머지 바이트(자릿수·0 채움으로 보임)의 정의 파일(MSBP)이 롬에 없어 의미는 **[추정]**입니다. 초 자리는 모두 `01 02 01 00`이라 "2자리 0 채움"으로 보고, 분 자리 `00 02 00 00`은 0 채움 없음으로 봅니다 → "3:00" **[추정]**.

## 8. 웹 변환 절차

```sh
cd c:/dev/splatoon3; PY=.venv/Scripts/python
# 1) 레이아웃 → JSON (카테고리 VersusSync 19개)
for n in $($PY -c "import json;print(' '.join(json.load(open('analysis/ui/LayoutArchiveCategory.json'))['VersusSync']))"); do
  $PY web/tools/ui_lyt.py dump extracted/romfs/Layout/$n.Nin_NX_NVN.blarc.zs <웹에셋>/layout/$n; done
# 2) 텍스처 → PNG (아카이브마다)
$PY web/tools/ui_sarc.py extract extracted/romfs/Layout/<n>.Nin_NX_NVN.blarc.zs tmp/<n>
$PY web/tools/graphics_bntx.py png <웹에셋>/tex/<n> tmp/<n>/timg/__Combined.bntx
# 3) 폰트 복호화 → woff2 변환은 별도(fonttools)
$PY web/tools/ui_font.py otf extracted/romfs/Font/Font_KRko.Nin_NX_NVN.bfarc.zs scft/BlitzMain.bfotf <웹에셋>/font/BlitzMain.otf
# 4) 메시지 → JSON
$PY web/tools/ui_msbt.py <웹에셋>/msg/KRko <msbt 파일들>
```

- BC4(`^s`)는 PNG 알파 채널로 바꿔 두면 재질 흑/백 보간을 셰이더에서 그대로 할 수 있습니다.
- `ui_lyt.py`의 JSON은 그대로 웹 런타임 입력으로 쓸 수 있게 필드 이름을 정했습니다. 웹 쪽에서 다시 파싱할 필요가 없습니다.
