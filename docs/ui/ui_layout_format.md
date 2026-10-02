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

`lyt1` 화면 크기는 1920×1080, `drawFromCenter` 1입니다(VS_MainTV_00 확인). 2026-10-03 [r5 ui] 전수: 348개 중 **333개 1920×1080**, 14개 1280×720(`CmnIcon*`, `Btn*`, `Bonus_01`, `Tuto_GuideMsg_00` 등 파츠·아이콘), 1개 350×135(`Lobby_CapScreen_00`), drawFromCenter는 전부 1 [데이터]. 사격장 화면(`Lobby_GuideBtn_00`, `Cmn_NoInk_00`, `Shr_Points_00`, `Shr_InkReset_00` 등)은 모두 1920×1080입니다. 이 가상 화면을 실제 출력 해상도로 바꾸는 투영 코드는 읽지 않았습니다 [미확정]. 2026-10-03 [r6 ui] [판독, 부분]: drawFromCenter 바이트는 레이아웃 객체에 복사되지 않습니다. 레이아웃 사각형은 항상 중심 원점(±w/2, ±h/2)입니다. 화소 변환 소비처 두 곳(캡처 크기, 가위 페인)이 렌더 타깃 크기 / 레이아웃 크기 배율을 씁니다. 근거와 남은 것은 [ui_hud.md §1.1](ui_hud.md)에 있습니다.

### 3.2 재질 flags bit20 = 사용자 셰이더 블록 [데이터]

Jamboree에 없던 비트입니다. 재질 끝(다른 블록 뒤)에 **0x74 바이트**가 붙습니다.

| 오프셋(블록 기준) | 형식 | 내용 |
|---|---|---|
| +0x00 | char[0x60] | 셰이더 키 이름 (예: `MeterAction`, `Circle01`, `Random00`, `RandomMosaic03`, `FestDisappear_00`, `ColorGap_00`, `Gray02`, `BalloonTail_01`, `Gradation00`) |
| +0x60 | RGBA×5 | 상수색. 대부분 `#ffffffff`, `RandomMosaic03` 일부는 첫 색 `#ffffff05`, `Gray02`는 `#808080ff` |

근거: bit20 재질 26개가 모두 이 크기로 섹션 경계와 맞습니다. 필드 이름과 상수색의 의미는 **[추정]**입니다. 남은 1개(`Msn_MFPage_04`)는 bit19 상세 컴바이너 블록 크기가 달라 생기는 차이이고 HUD와 무관해 보류했습니다 **[미확정]** — 히어로 모드 레이아웃이라 사격장 범위 밖(2026-10-03).

셰이더 키가 붙은 재질의 페인은 `usd1`에 `__CUS_Float_0..2` 같은 사용자 셰이더 인자를 가집니다. 이 인자를 BFLAN `FLEU` 태그가 움직입니다(§3.3). 셰이더 본체는 `bgsh/__ArchiveShader.bnsh`(NVN 바이너리)이고, 같은 폴더에 **원본 GLSL 소스** `bgsh/<키>.glsl`과 `CombinerUserShaderVariation.glsl`(`#if NW_COMBINERUSERSHADER_TYPE == N #include "<키>.glsl"`)이 함께 들어 있습니다 [데이터]. 정정: 이전 판의 "판독하지 않음 [미확정]"을 바꿉니다. 소스가 있는 키(아카이브 수): MeterAction(3: SuperGaugeTV_00, HoldText_00, TimerCircle_00), RandomMosaic03(7), ColorGap_00(6), Random00(3), Circle02·RandomMosaic02·RandomMosaicDisappear00(2), BalloonTail_01·Circle01·FestDisappear_00·Gradation00·Gray00·Gray02(1). 소스는 `nwTextureCoord0`, `nwAlbedoTexture0`, `nwConstantColor0/1`(재질 흑/백), `nwExUserDataFloat_0..2`, `vColor`, `OUTPUT_COLOR`, `CalcAlphaProcess`, `FinalAdjustmentFragmentColor`를 씁니다. MeterAction 해석은 [ui_hud.md §6.5](ui_hud.md), [../graphics/shaders.md §5](../graphics/shaders.md). `.bushvt`는 `DTCB` 블록 3개 + `CBUS`(키 이름 "MeterAction")로 시작합니다(필드 의미 [미확정]).

### 3.3 `FLEU` = 확장 사용자 데이터 애니 [데이터]

애니 대상 종류가 2(user)이고, 키 값은 페인 `usd1`의 float 항목에 들어갑니다. `SuperGaugeTV_00_Gauge.bflan`의 예:

```
pat1: 태그 "Gauge", 그룹 G_Gauge_00 = {P_pict_00, P_pict_02}, 프레임 -100..-25 (길이 75)
pai1: frameSize 75, loop 0
  P_pict_00 (user) FLEU 트랙 0: 에르미트 [(0, 0.75, -0.01), (75, 0.0, -0.01)]
  P_pict_02 (user) FLEU 트랙 0: 같은 키
```

기울기 −0.01 × 75 = −0.75라서 이 곡선은 정확히 직선 `값 = 0.75 × (1 − 프레임/75)`입니다([검증 §10](ui_hud.md)).

**대상 항목 = 이름** [데이터] (2026-10-03 [r5 ui], 이전 판 "이름인지 인덱스인지 미확인 [추정]" 대체): user(target 2) 엔트리는 `이름[28], 태그 수 u8, target u8, pad u16, 태그 오프셋 u32[n]` 뒤에 **사용자 데이터 이름 오프셋 u32[n]**(엔트리 기준 → `u32 4` + 문자열)을 더 가집니다. `SuperGaugeTV_00_Gauge`의 `P_pict_00` 엔트리: 태그 오프셋 0x28, 이름 오프셋 0x5c → `__CUS_Float_0`. 전 레이아웃 bflan을 `web/tools/r5_ui_fleu_names.py`로 훑으면 user 태그 353개(전부 FLEU)가 모두 이름을 가집니다: `__CUS_Float_0` 121, `__CUS_Float_1` 64, `__CUS_Float_2` 46, `__CUS_Vec2_0` 36, `__CUS_Vec2_1` 32, `__CUS_Vec2_2` 36, `__CUS_Vec2_3` 18. 트랙의 index 바이트가 Vec2의 x/y 성분인지는 확인하지 않았습니다 [추정]. 이 값이 상수 버퍼로 가는 위치는 이름 비교 `0x7100867134`로 확정입니다([ui_hud.md §6.5](ui_hud.md)) [판독]. 애니 바인딩 코드가 이 이름으로 usd1 항목을 찾는 부분은 읽지 않았습니다(데이터에 인덱스가 없어 이름 외 대응 수단이 없음). `ui_lyt.py`의 `t += 4` 처리는 이 이름 오프셋 표를 건너뛰는 근사라 이름은 출력하지 않습니다.

실행 시 애니 적용 규칙(2026-10-02 [camrest], 근거는 [ui_hud.md §5.3](ui_hud.md) 적용 루프 `0x71038f67f8`) **[판독 + 실행(에뮬)]**: 레이아웃의 AnimTransform 목록을 앞에서부터 Animate하므로 같은 대상(같은 페인·같은 usd1 항목)을 여러 애니가 움직이면 **목록 뒤쪽 애니의 값이 남습니다**. setFrame·재생 명령은 그 애니를 목록 끝으로 옮기고, 정지(speed 0) 애니는 한 번 적용된 뒤 꺼져 목록에서 빠집니다. 웹 변환기(§8)가 만든 애니 데이터를 재생할 때 이 순서 규칙을 같이 구현해야 원본과 같은 화면이 됩니다.

### 3.4 페인 사용자 데이터 키 (HUD에서 관측) [데이터]

코드가 페인의 `usd1` 문자열 키로 기능을 켭니다. 이름은 main 문자열에도 있습니다(`EffectLinkOn`, `TeamColorUse`, `CaptureUseName`, `DynamicCaptureUseName`, `TextScaleOn`, `TracingFraction`).

| 키 | 값 예 | 의미 |
|---|---|---|
| `CaptureOn` / `DynamicCaptureOn` | `"RGBA8"` | 이 페인 하위를 텍스처로 캡처한다. 값은 텍스처 포맷 [판독]: `CaptureOn` 설정 `0x71038dea90`이 `RGBA8`/`BC3`/`BC1`/`RGB565`… 문자열을 비교해 포맷을 고르고, `DynamicCaptureOn` 설정 `0x71038e0a2c`는 `R10G10B10A2`면 플래그 4를 켭니다. 같이 읽는 키: `CaptureWorkFormat`, `CaptureOutputAlpha`(255면 플래그 8), `CaptureApplyScale`(0x80), `CapturePersProjection`(도 → 라디안, 0x100), `CaptureAdjustSize`(없거나 0이 아니면 0x10), `CaptureScale`. Dynamic = 매 프레임 갱신이라는 해석은 **[추정]**(갱신 코드 미판독). **확정(2026-10-03 [r6 ui]) [판독]**: 두 키는 다른 페인 클래스를 만듭니다(페인 생성 `0x71038dc97c`: `CaptureOn` → vtable `0x7105739ae0`, `DynamicCaptureOn` → `0x7105739bf0`). 그리기 슬롯 22에서 **정적** `0x71038df608`은 캡처 필요(+0xd4 ≠ 0) 또는 플래그 0x200(+0xd3 bit1)일 때만, 그리고 페인 표시(+0x58 bit0)·알파(+0x59) ≠ 0일 때 캡처합니다. 캡처 뒤에는 플래그 |= 1, +0xd4 = 플래그 bit6(`CaptureOn` 설정은 0x40을 켜지 않으므로 0)으로 바꿔 **한 번만** 캡처합니다. 다시 캡처하려면 코드가 +0xd4 = 1을 씁니다(예: SuperGauge 갱신의 아이콘 캡처 다시, [ui_hud.md §5.2](ui_hud.md)). **동적** `0x71038e0d70`은 필요 플래그 검사 없이 표시·알파 ≠ 0·페인 크기 ≠ 0이면 **그릴 때마다** 캡처합니다 |
| `MultiFilterFile` | `"blur5"` | 캡처에 걸 필터 [판독+데이터]: `0x71038fe320`이 `"%s.baglmf"`를 리소스 접근자로 읽고(같은 이름은 재사용), 필터 객체 +0x7c8 = 5. `blur5.baglmf`(AAMP)는 `UI/MultiFilter.sarc.zs`에 있습니다(그 밖 `msgwin_blur`, `reduce2`, `GuideKey_00` 등 7개). 필터 파라미터 의미는 미판독 |
| `CaptureUseName` + `CaptureUseIndex` | `"N_CapSp_00"`, `[1]` | 캡처 텍스처를 재질의 텍스처 슬롯 [인덱스]에 꽂는다 **[판독]** (2026-10-03): `0x71038fdc40`이 이름으로 캡처 페인을 찾아, 이 페인의 재질마다 `Index < 텍스처 수(재질+0x14 & 3)`이면 텍스처 맵[Index](+0x18 배열, 0x10 B씩)의 +8에 캡처 텍스처(캡처 객체+0xf0)를 넣습니다 |
| `TeamColorUse`, `TeamColorBlack`, `TeamColorWhite` | `"MyTeam"`, `[1]`, `[1]` | 재질 흑/백 색을 팀 색으로 바꾼다. 팀 색 값은 [graphics]의 TeamColorDataSet **[추정]**. 2026-10-03: `0x7103436a70`이 `TeamColorUse` 값 문자열을 이름 표(`0x710343b4c8`)와 비교해 순번을 고르는 것까지 확인 [판독-부분], 색 적용은 미판독. **2026-10-03 [r6 ui] 뒷부분 [판독]** — 아래 표 |
| `EffectLinkOn` | `"LoopMax"` | 애니와 이펙트 연결 **[추정]**. 읽는 코드 `0x71038f7bc8`(개수), `0x7103901da0`(등록), `0x7103902290`(값 파싱) [판독: 위치만]. **2026-10-03 [r6 ui] [판독]+[데이터]**: 값 = 콤마로 나눈 애니 이름 목록(`-` = 없음). 애니마다 키 `"<파츠 경로>/<애니 이름>"`(예 `L_SuperGauge_00/LoopMax`)를 만들어 그 AnimTransform과 짝짓습니다. 이 키가 ELink 사용자의 액션 슬롯 이름이고, 이펙트는 `UIGaugeMax`/`LayoutGaugeMax`, Bone = 페인 경로입니다([ui_hud.md §7](ui_hud.md)). 액션을 켜는 시점은 [미확정] |
| `TextScaleOn` | `[0.6]` | 글자 축소 하한(긴 문자열 맞춤)으로 추정 **[추정]**. 값을 꺼내는 함수 `0x71038eaf68`은 텍스트 박스 vtable 3개(`0x710573a0b8`, `0x710573ad10`, `0x710573afe8`)의 가상 함수이고, 그 슬롯을 부르는 쪽은 아직 못 찾음. **2026-10-03 [r6 ui] [판독, 부분]** — 아래 의사코드 |
| `TracingFraction`, `TracingWait` | `[1.0]`, `[0.0]` | TraceGauge 인자([ui_hud.md](ui_hud.md) §4.2~§4.3) |
| `LocalizeReplaceOn`, `LocalizeReplaceTarget` | `"T_Extend_00"`, `"JPja\nKRko\nCNzh\nTWzh"` | 해당 언어에서 다른 텍스트 페인으로 교체 **[판독]** (2026-10-03): 페인 생성 `0x71038dc97c`가 현재 언어 코드(표 `0x7104aa6fa6` 또는 설정 `*0x7105997788`)를 줄바꿈 목록과 비교해, 들어 있으면 `LocalizeReplaceOn` 이름의 페인을 대신 만들고 원래 페인 재질의 +0x28 포인터를 옮깁니다 |
| `__CUS_Float_0..2` | `[0.0]`, `[1.0]`, `[1.0]` | 사용자 셰이더 인자 |

**`TeamColorUse` 색 적용 `0x7103436a70` [판독]** (2026-10-03 [r6 ui])
- 값 → 팀 종류:
  - 문자열이면 열거 `MyTeam, RivalTeam, Neutral, FestTeamA, FestTeamB, FestNeutral, None, TricolorA, TricolorB, TricolorC, FestTeamC`(0..10, 문자열 표 `0x710343b4c8`)와 비교합니다.
  - 정수 배열(`[0]` 등, usd 형식 1)이면 그 수를 그대로 씁니다. 6(None)이면 아무것도 하지 않습니다.
  - 사격장 레이아웃에서는 `MyTeam`(`Lobby_GuideBtn_00` 2곳, `SuperGaugeTV_00`, `CmnIconSubSpecial_00`, `Shr_InkReset_00`, `Cmn_PlayGuide_00`)과 `[0]`(`Cmn_NoInk_00` 3곳)만 씁니다 [데이터].
- `MyTeam`(0): 팀 = 호출 인자(param_3)입니다. −1이면 전역 `(*0x7105791088)+0xf4`(내 팀)를 씁니다. 다른 종류는 RivalTeam = (팀 == 0), Neutral = 2, TricolorA/B는 인자에 따라 0/1, TricolorC = 2, Fest 계열은 별도 경로입니다.
- 색 세트 = 팀 색 관리자 `(*0x7105793648)+0x560 + 팀×0xF0`(팀 > 3이면 세트 0)를 0xF0 B 그대로 복사한 것입니다. [graphics] [team_color.md §3](../graphics/team_color.md)의 세트와 같은 표이고, 14색 + 원본입니다.
- 키 `TeamColorBlack, TeamColorWhite, TeamColorVtxT, TeamColorVtxB, TeamColorVtxL, TeamColorVtxR, TeamColorShadowBlack, TeamColorShadowWhite`(이름 표 `0x710343b280`, 대상 번호 0..7)마다:
  - 값 v가 정수이고 1 ≤ v ≤ 7이면 세트의 색 v를 고릅니다(team_color.md §4 이름: 1 Pale, 2 Bright, 3 Dark, 4 HueBright, 5 HueBrightHalf, 6 HueDark, 7 HueDarkHalf). 그 밖이면 색 0(Original)입니다.
  - 고른 색을 `0x7103435f70(페인, 대상, 색)`에 넘깁니다.
- `0x7103435f70`:
  - 키 `TeamColorOffset`(f32×3)이 있으면 `0x7101188334`로 색을 한 번 더 보정합니다.
  - 각 채널을 [0, 1]로 자른 뒤 `×255 + 0.5`를 정수로 바꿉니다(음수면 0.5).
  - 대상 0(Black)은 재질(vt+0x58) 흑색의 알파 바이트를 유지한 채 RGB만 바꿉니다. 나머지 대상의 기록 위치는 그 함수의 switch 분기입니다.
- 남은 것: 대상 1~7의 정확한 기록 칸, `TeamColorOffset` 보정식(`0x7101188334`).

**`TextScaleOn` 맞춤 축소 [판독, 부분]** (2026-10-03 [r6 ui]): 값 읽기 `0x71038eaf68`은 게임 텍스트 박스 vtable(`0x7105739f28`, `0x710573ab80`, `0x710573ae58`)의 슬롯 50(+0x190)입니다. 이를 부르는 슬롯 49 `0x71038eae80`은 다음과 같습니다.

```
if 글자 수(+0x112) == 0 || 폰트 없음(0x71008725e0) → 끝
minScale = 0; if !slot50(&minScale) → 끝                 // TextScaleOn 없으면 아무것도 안 함
if 인자 == 0 && 저장값(+0x158) > 0: 글자 크기 = (저장값, +0xfc) 로 되돌림(0x71008725e8)
w = slot45(+0x168)()                                      // 현재 글자열 폭
if w <= 페인 폭(+0x50) → 끝
if 저장값 == 0: 저장값 = 글자 크기.x(+0xf8)
s = (+0x108 객체).vt+0x80(this, w, minScale)              // 배율 계산 [미확정]
글자 크기 = (s × 원래 크기.x, 크기.y 그대로)                 // 가로만 줄임
```

- 버퍼 크기 추정 `0x71038ea4c0`도 슬롯 50을 부릅니다. 최소 글자 폭을 `크기.x × 0.4 × minScale`(TextScaleOn이 없으면 `× 0.4`)로 잡습니다.
- 남은 것: +0x108 객체(ui2d TextBox의 복사 생성자가 그대로 복사하는 포인터)의 vt+0x80이 w·minScale로 배율을 어떻게 정하는지([추정]: max(페인 폭/w, minScale)). 다음에 볼 곳: 텍스트 박스 생성 시 +0x108 writer.

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

**씬별 적재 목록 [데이터]** (2026-10-03 [r5 ui]): 어떤 카테고리를 올리는지는 씬의 Sequence 컴포넌트(`Pack/Bootup.Nin_NX_NVN.pack.zs` 안 `SceneComponent/Sequence/<이름>.game__SequenceComponentParam.bgyml`)의 `LoadSyncCategories`/`LoadAsyncCategories`가 정합니다. 카테고리 이름은 열거형 `game::LayoutArchiveCategory`(`Test, Boot, GameCommon, VersusSync, Versus, LobbySync, Lobby, …`)입니다.

| 씬(Sequence) | LoadSync | LoadAsync |
|---|---|---|
| `LobbyVersus`(사격장 `Lby_Lobby00`) | XMenu, Customize, GameCommon, LobbySync, News, Narration, StageSelect | Lobby, TalkWin, FestRegion, Takeover, MiniMap, Manual |
| `ShootingRange`(씬 팩에서 쓰는 곳 없음) | XMenu, Customize, GameCommon | — |

사격장(`LobbyVersus`)은 `VersusSync`를 올리지 않으므로 `VS_MainTV_00`이 없고, 게이지는 `LobbySync`의 `Lobby_GuideBtn_00` 안 `SuperGaugeTV_00`에 나옵니다([ui_hud.md §1.1](ui_hud.md)). 웹 사격장은 `GameCommon` + `LobbySync` + `Lobby` 중 쓰는 레이아웃만 변환하면 됩니다.

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

사격장 화면(2026-10-03 [r5 ui]) [데이터]:

| 필드 | Lobby_GuideBtn_00 | Shr_Points_00 | Shr_InkReset_00 | Cmn_GuideActionPoint_00 |
|---|---|---|---|---|
| Class | `SplUILobbyGuideBtn00Screen` | `SplUIShrPoints00Screen` | `SplUIShrInkReset00Screen` | `SplUICmnGuideActionPoint00Screen` |
| ArchiveCategory | `LobbySync` | `GameCommon` | `Lobby` | `GameCommon` |
| DrawUnitId | 0 | 1 | 3 | 1 |
| SortKey | 3000 | 1000 | 10000 | 3000 |
| 화면 vtable(팩토리 → 화면) | `0x71056e7a80` → `0x71056e7638` | `0x7105703728` → `0x71057031f8` | `0x71057031c8` → `0x7105702d80` | `0x71056df078` |

`Cmn_NoInk_00`은 팩토리 `0x71056e0410` → 화면 vtable `0x71056dffc8`입니다. 화면은 UI 관리자(`*0x710599b7a0`)의 화면 목록에서 이름 인덱스(`0x7100f7694c`)로 찾고, 기본 화면 vtable(`0x710557d558`)의 +0x2b0 열기·+0x2b8 닫기·+0x2d0 열림·+0x2d8 닫힘·+0x2e8 닫는 중을 씁니다([ui_hud.md §5.5](ui_hud.md)) [판독].

`Class` 문자열은 main의 화면 클래스 이름과 같습니다. 이 문자열을 반환하는 함수가 4슬롯짜리 화면 팩토리 vtable(`SplUIVSMainTV00Screen` → `0x710570f6d8`)의 슬롯 2에 있고, 슬롯 3(`0x71033de790`)이 화면 객체(0x620 B, 메인 vtable `0x710570f290`)를 만듭니다 **[판독]**. `SortKey`·`DrawUnitId`가 그리기 순서와 층을 정하는 것으로 보입니다 **[추정 — 소비 코드 미판독]**. 2026-10-03 [r6 ui] [판독, 부분]: UIScreen 행 로더 `0x7103e946dc`가 `DrawUnitId` → 행+0x28(s32), `HeapInitialSize` → +0x2c(음수는 0), `SortKey` → +0x30에 넣습니다. 행 → 문자열 출력 `0x7103e926a0`도 같은 오프셋을 씁니다. 행 +0x28/+0x30을 읽어 정렬·층을 고르는 소비 코드는 아직 못 찾았습니다(오프셋이 흔해 정적 스캔으로 가려내지 못함). 다음에 볼 곳: 화면 생성 시 UIScreen 행 포인터를 저장하는 칸과 그 reader. 별개로 `0x7103e12cb0`은 다른 표에서 `DrawUnitId`를 u8로 +0x30에 읽습니다.

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

- 사격장 화면이 쓰는 폰트는 **`BlitzMain_S`, `BlitzBold_L` 두 개뿐**입니다(`Lobby_GuideBtn_00`·`SuperGaugeTV_00`·`HoldText_00`·`Cmn_NoInk_00` = BlitzMain_S, `Shr_Points_00` = BlitzBold_L, `PauseText_00` = 둘 다, `PlayerStatus_00`·`Shr_InkReset_00` = 없음) [데이터] (2026-10-03). `Builtin_S`는 사격장 범위 밖입니다.
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
| `000` / `001` / `002` | `+[2:0:00020000]` / 이쪽이야 / 당했어 | 코드가 라벨로 직접 고르는 문구 **[추정]**. 대전 화면 전용이라 사격장 범위 밖(2026-10-03) |

`Cmn_NoInk_00`: `000` 잉크 부족!, `002` 꼬마연어 필요!, `003` 사용 불가, `004` 연어알 부족!. 이 레이아웃은 라벨이 페인 이름이 아니고, 화면 갱신 `0x7103277148`이 kind에 따라 페인(`T_NoInk_00`/`_01`)과 라벨을 골라 넣습니다(kind 0 → `T_NoInk_00` ← `000`) [판독+실행] — [ui_hud.md §5.5](ui_hud.md). `Lobby_GuideBtn_00`도 코드가 `T_Signal_00` ← `000`/`001`, `<L_GuideBtn_02>-T_Info_00` ← `010`을 넣습니다 [판독].

**타이머 형식 [데이터]**: `CommonMsg/UnitName.msbt`

| 라벨 | 값 |
|---|---|
| `VSTimer` | `[2:0:00020000]:[2:0:01020100]` |
| `MinSec_1Digit` | `[2:0:00010000]:[2:0:01020100]` |
| `MsnTimer_MinSec` | `[2:0:00020200]:[2:0:01020100]` |
| `MsnTimer_MinSecCentsec_00` | `[2:0:00020200]:[2:0:01020100].[0:2:3200][2:0:02020100][0:2:6400]` |

`[2:0:…]`은 그룹 2 태그 0(숫자 삽입) 제어 태그이고 첫 바이트가 인자 번호(0=분, 1=초, 2=1/100초)입니다. 나머지 바이트(자릿수·0 채움으로 보임)의 정의 파일(MSBP)이 롬에 없어 의미는 **[추정]**입니다. 초 자리는 모두 `01 02 01 00`이라 "2자리 0 채움"으로 보고, 분 자리 `00 02 00 00`은 0 채움 없음으로 봅니다 → "3:00" **[추정]**.

**확정(2026-10-03 [r6 ui]) [판독]+[실행]** — 위 [추정]을 대체합니다. 정정: 앞 판에서 다음에 볼 곳으로 적은 `0x7101362370`은 태그 처리가 아니라 "메시지 파일·라벨로 찾기 → `0x7101361930`으로 텍스트 설정" 함수입니다.

- 처리 경로: 게임 TagProcessor(`nn::font::TagProcessorBase<char16_t>` 파생, RTTI 없음, vtable `0x710557cce0`)의 슬롯 22 `0x7101360478`이 그룹(+2) 3이면 문자열 복사, 2이면 `0x7101360544`로 갑니다.
- 태그 구조: `u16 0x0E, u16 그룹, u16 종류, u16 인자 크기, 인자 바이트…`.
- 종류 0(정수):
  - p0 = 인자 번호. 16 미만이면 인자 표+8+4·p0의 s32를 씁니다.
  - p1 = 자릿수 → `max(p1, 1)`.
  - p2 = 채움 방식.
  - 숫자 문자열은 `0x71013616b0(버퍼, 값, 자릿수, 채움, 0)`이 만듭니다.
  - p3 == 0이면 ASCII 0x21..0x7e를 전각(−0x120 → U+FF01..)으로, 공백을 U+3000으로 바꿉니다.
- 원본 실행 `web/tools/r6_ui_msbt_num_emu.py`(`0x7101360544` 전체, libc PLT만 파이썬 대체) 결과(`analysis/r6_ui/msbt_num_emu.json`):

| 태그(p0 p1 p2 p3) | 0 | 3 | 36 | 120 | 1234 | −5 |
|---|---|---|---|---|---|---|
| `00 03 00 00` (Shr_Points_00 정수부) | ０ | ３ | ３６ | １２０ | １２３４ | －５ |
| `01 01 00 00` (Shr_Points_00 소수부) | ０ | ３ | ３６ | １２０ | １２３４ | －５ |
| `00 02 00 00` (VSTimer 분) | ０ | ３ | ３６ | １２０ | １２３４ | －５ |
| `01 02 01 00` (VSTimer 초) | ００ | ０３ | ３６ | １２０ | １２３４ | －５ |
| `00 02 02 00` (MsnTimer 분) | 　０ | 　３ | ３６ | １２０ | １２３４ | －５ |
| `00 03 01 00` (비교) | ０００ | ００３ | ０３６ | １２０ | １２３４ | －０５ |
| `00 03 02 00` (비교) | 　　０ | 　　３ | 　３６ | １２０ | １２３４ | 　－５ |

- 뜻: **p1 = 최소 자릿수**(부호 포함, 넘치면 자르지 않음), **p2 = 채움**(0 없음, 1 '0', 2 공백 U+3000). 채움이 0이면 p1은 효과가 없습니다. 숫자는 **전각**(U+FF10..)으로 나옵니다.
- 시험한 p3 = 1에서도 결과가 전각이었습니다. 숫자가 이미 전각으로 만들어지기 때문으로 보이며, p3의 효과는 이 시험 범위에서 관측되지 않았습니다.
- 결과 문자열:
  - 대전 타이머 `VSTimer` = 분(채움 없음) + `:`(메시지의 ASCII) + 초(2자리 0 채움) → "３:００".
  - 사격장 데미지 숫자 `Shr_Points_00` "000" = 정수부(채움 없음) + `.`(ASCII 0x2e) + 소수부 → 예 "３６.０". 텍스트 상자 기본 문자열 `０００.０`과 같은 문자 종류입니다.
- 웹: 숫자를 전각 문자로 만들거나 폰트에서 같은 글리프로 매핑해야 원본 글리프 폭이 나옵니다. 데미지 숫자는 소수부를 버림한 정수 두 개를 넣습니다([range §6.4](../range/shooting_range.md)).

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

## 9. 미확정과 필요한 근거 (2026-10-03 [r5 ui] 정리)

| 항목 | 지금 수준 | 다음에 볼 곳 |
|---|---|---|
| ~~FLEU 트랙의 usd1 대상(이름/인덱스)~~ | 해소: 애니 엔트리에 대상 이름이 있음 [데이터], 상수 버퍼 위치는 이름 비교 [판독] — §3.3 | 애니 바인딩 코드(이름 검색) 판독은 남음 |
| ~~`CaptureUseIndex` = 텍스처 슬롯~~ | 해소 [판독] — §3.4 | |
| ~~`MultiFilterFile` 출처~~ | 해소 [판독+데이터] — §3.4 | `.baglmf`(AAMP) 파라미터 의미 |
| ~~`LocalizeReplace*` 의미~~ | 해소 [판독] — §3.4 | |
| ~~`DynamicCaptureOn` = 매 프레임 갱신~~ | 해소(2026-10-03 [r6 ui]) [판독]: 동적 페인 그리기 `0x71038e0d70`은 그릴 때마다 캡처, 정적 `0x71038df608`은 한 번(+0xd4 요청 시 다시) — §3.4 | |
| `TeamColorUse` 색 적용 | 이름 → 순번까지 [판독-부분]. 2026-10-03 [r6 ui]: 팀 → 색 세트(관리자+0x560+팀×0xF0) → 키별 색 번호(1..7, 그 밖 0) → `0x7103435f70` [판독] — §3.4 | 대상 1~7 기록 칸, `TeamColorOffset` 보정 `0x7101188334` |
| `EffectLinkOn` | 2026-10-03 [r6 ui]: 키 `<파츠 경로>/<애니>` 생성과 ELink 이펙트 이름 [판독]+[데이터] — §3.4 | 키를 ELink 액션으로 켜는 시점(쌍 표 소비처) |
| `TextScaleOn` | 2026-10-03 [r6 ui]: 호출 슬롯 49 `0x71038eae80` 판독(넘치면 가로 글자 크기만 축소) [판독, 부분] — §3.4 | 배율 함수 (+0x108).vt+0x80 |
| `SortKey`·`DrawUnitId` 소비 | [추정]. 2026-10-03 [r6 ui]: 행 오프셋(+0x28 DrawUnitId, +0x30 SortKey, 로더 `0x7103e946dc`) [판독] | UIScreen 행을 읽는 화면 생성·정렬 코드 |
| 폰트 `fontSize`·아시아 폰트 1.1배 | [추정] — 사격장 `T_Num_00`은 BlitzBold_L, fontSize 0.42, 박스 154.5×67.2 | ui2d 글리프 배율 계산(FCPX +0x1C 기준 크기 사용처) |
| `Builtin_S` 시스템 폰트 | [추정], 사격장 화면에서 안 씀 [데이터] → 범위 밖 | 시스템 공유 폰트 로더 |
| ~~MSBT 숫자 태그 파라미터~~ | 해소(2026-10-03 [r6 ui]) [실행]: p0 인자, p1 최소 자릿수, p2 채움(0/‘0’/공백), 전각 숫자 — §7 | p3 효과 |
| `Msn_MFPage_04` bit19 블록 | [미확정], 사격장 범위 밖 | — |
| 1920×1080 가상 화면 → 출력 해상도 | 레이아웃 크기 [데이터], 변환 코드 미판독. 2026-10-03 [r6 ui]: 중심 원점 사각형·RT/레이아웃 배율 소비처 2곳 [판독, 부분] — §3.1 | 본 그리기 투영 행렬 설정, 그리기 정보 +0x1a0 writer |
