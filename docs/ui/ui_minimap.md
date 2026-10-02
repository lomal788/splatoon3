# UI — 대전 맵(미니맵·슈퍼점프 맵)

2026-10-02 [camui], 같은 날 [camrest] 갱신. 상태: **분석 진행**(카메라·투영·좌표 변환·데이터·화면 구성 판독, 카메라 축 규약 전사·재구현, 맵 열기 입력·커서·슈퍼점프 결정 메시지 판독, 맵 셰이더 역번역. 뷰포트 실제 값·결정 메시지 수신 쪽 미확정, 웹 구현 없음). 상위 문서: [ui_hud.md](ui_hud.md). 확정 수준 표기는 [../README.md](../README.md). 주소는 main NSO를 0x7100000000에 올린 기준입니다.

## 1. 기능 개요

대전 중 X를 누르면 화면 전체에 스테이지를 위에서 비스듬히 내려다본 3D 맵이 뜹니다. 지금까지 칠해진 잉크가 팀 색으로 보이고, 아군 위치·슈퍼점프 착지 지점을 고를 수 있습니다. 이 맵은 2D 텍스처가 아니라 **별도 렌더 레이어(MiniMap)에서 스테이지 모델을 정사영(직교 투영) 카메라로 다시 그린 것**이고, 그 위에 레이아웃(VS_MapAnnounce_00 등)을 겹칩니다 [판독+데이터].

| 화면 요소 | 원본 | 수준 |
|---|---|---|
| 3D 맵 그림 | 렌더 레이어 5 `MiniMap`(레이어 열거 `Paint , PlayerPaintMonitor , PaintMonitor , PreMain , Main , MiniMap , …`), 액터 `SplMiniMap`(`spl::MiniMap`) | [판독]+[데이터] |
| 맵 카메라 | 스테이지별 `game__CameraPoserFixedParam`(Pos·Rot·FovY) → 정사영 | [판독]+[데이터] |
| 플레이어 이름표·착지점 목록 | 레이아웃 `VS_MapAnnounce_00`(화면 `SplUIVSMapAnnounce00Screen`) | [데이터], 갱신 코드 일부 [판독] |
| 관전 자동 시점 안내 | `VS_MapAnnounce_01`(카테고리 MiniMap, `N_AutoWatching_00`, 파츠 `MapIcon_00`·`PauseText_00`) | [데이터] |
| 슈퍼점프 궤적 선 | `VS_MapLine_00`(Rotate·Attention 애니) | [데이터] |
| 맵 아이콘 | `MapIcon_00`(P_VSMapIcon_00/05, Loop/On/Off/Decide 애니) | [데이터] |

## 2. 분석 대상과 자료

| 항목 | 위치 |
|---|---|
| 액터 | `Pack/Actor/SplMiniMap.pack.zs` (Behavior `spl::MiniMap`, Category System) |
| 맵 모델 정보 | `Pack/SingletonParam.pack.zs` → `Gyml/Singleton/spl__gfx__MiniMapModelInfo` |
| 기본 맵 카메라 | `Pack/Bootup.Nin_NX_NVN.pack.zs` → `Gyml/VersusMiniMapDefault.game__CameraPoserFixedParam.bgyml` |
| 스테이지 맵 카메라 | `Pack/Scene/Vss_<스테이지>.pack.zs` → `SceneComponent/VersusCamera/<스테이지>.spl__VersusCameraParam.bgyml`의 `MiniMapCamera` 참조 |
| 액터별 맵 모델 | 각 액터 팩 `Component/MiniMapModel/<이름>.spl__MiniMapModelParam.bgyml` (Fld_*, DObj_*, FieldParent 등) |
| 템플릿 모델 | `Model/MiniMapTemplate.bfres.zs`, 환경 `Env/MiniMap.Nin_NX_NVN.genvb.zs`, 렌더 배율 `Bootup … Gyml/MiniMap.game__gfx__parameter__SpecialEnvParamHolder.bgyml` |
| 레이아웃 덤프 | `analysis/ui/layout/{VS_MapAnnounce_00, VS_MapAnnounce_01, MapIcon_00, VS_MapLine_00}/` (`web/tools/ui_lyt.py dump`) |
| 디컴파일 | `analysis/decomp/ui/camui_ui1.c`(생성 0x7102262994, 초기화 0x7102263214, 화면 0x71033df554·0x71033e0408·0x71033dfd58·0x71033e13b0…), `camui_minimap1.c`(갱신 0x7102264240, 5357줄), `camui_minimap2.c`(보조 12개), `camera/camui_full1.c`(0x7102262578) |
| 재구현 도구 | `web/tools/ui_minimap.py table|selftest|cam` → `analysis/ui/minimap_table.md`, `web/tools/ui_minimap_shader.py` → `analysis/camrest/minimap_shader/` |

## 3. 진입점과 호출 흐름

```
spl::MiniMap (vtable 0x7105619958, 46슬롯; getName 0x7102263200)
 ├ 생성 0x7102262994            기본값: Pos(0,50,0), Rot(15,70,0) (+0xbbc..+0xbd0)
 ├ 슬롯 8  0x7102263214         초기화: 렌더 레이어 5(MiniMap) 핸들, 카메라 파라미터 로드, 정사영·카메라 초기값
 ├ 슬롯 19 0x7102264240         매 프레임 갱신(34 KB): 관전/조작 대상, 카메라 기울임·회전·평활, 착지점 목록,
 │                              VS_MapAnnounce_00/VS_MapLine_00 화면 갱신, xlink 키 MILine·MILandingPoint·decide
 ├ 보조 0x710226cd20            월드 좌표 → 맵 레이아웃 좌표 (§6.3)
 ├ 보조 0x710226ca6c            착지점 후보 필터 (§6.4)
 ├ 보조 0x710226d048/c824/c940  화면 VS_MapAnnounce_00/01 의 컨트롤 호출
 └ 정적 0x7102262578            "맵이 열려 있나"(조작 대상 +0x108 플래그) — PlayerCamera 갱신(0x71024d9ae8 2068행)이 관전 상태에서 확인
화면
 ├ SplUIVSMapAnnounce00Screen  생성 0x71033e0874(0x300 B, vtable 0x710570f708), 초기화 슬롯97 0x71033df554, 갱신 슬롯100 0x71033e0408, 슬롯102 0x71033dfd58
 └ SplUIVSMapAnnounce01Screen  생성 0x71033e18ac(0x288 B, vtable 0x710570fb80), 슬롯97 0x71033e13b0, 슬롯100 0x71033e149c
```

화면 슬롯의 호출 순서는 [ui_hud.md §5.3](ui_hud.md)의 화면 calc 순서와 같습니다(공통 화면 기본 클래스).

## 4. 구조체·필드·상수

### 4.1 `game::CameraPoserFixedParam` (리플렉션: 방문 0x710100d3f0, 생성 0x710100d114) [판독]

| 오프셋 | 필드 | 형 | 기본 | 설정 플래그 |
|---|---|---|---|---|
| +0x38 | Far | f32 | 10000 | +0x60 |
| +0x3c | FovY | f32 | 45 | +0x61 |
| +0x40 | Near | f32 | 0.1 | +0x5f |
| +0x44 | Pos | vec3 | (0,0,0) | +0x5d |
| +0x50 | Rot | vec3(도) | (0,0,0) | +0x5e |
| +0x5c | IsDofEnabled | bool | false | |

### 4.2 `spl::MiniMap` 상태 (기준 = MiniMap 객체) [판독, 의미는 표기]

| 오프셋 | 의미(웹 권장 이름) | writer | reader |
|---|---|---|---|
| +0x108 / +0x109 | 맵 열림(`isOpen`) / 결정 후 닫기 예약(`closeAfterDecide`) | 갱신(X 토글·강제 닫힘, §6.5) / 슈퍼점프 결정 시 1, 열 때 0 | 0x7102262578, 갱신, 레이어 5 +0x88 bit1 |
| +0x190 / +0x194 | 조작 대상 팀 / 대상 번호(플레이어 +8→+0x668 / +0x79c) | 갱신 | 착지점 필터 |
| +0x198 | 관전 등 고정 시점 플래그 [추정] | — | 회전(+π 보정 끔), 기울임 입력 끔 |
| +0x1a0 | 카메라 객체(LookAt: 위치 +0x1d8, 주시점 +0x1e4, 위 +0x1f0, double 사본 +0x200..) | 초기화 | 0x710226cd20 |
| +0x230 | 투영 객체(정사영: near +0x2c8, far +0x2cc, top +0x2d0, bottom +0x2d4, left +0x2d8, right +0x2dc) | 초기화 | 0x710226cd20 |
| +0x2e0 | 렌더 레이어 5 핸들(+0x30..+0x3c 뷰포트 x0,y0,x1,y1, +0x78 카메라, +0x80 투영) | 초기화 | 전역 |
| +0xb48..+0xb68 | 평활된 카메라 기저·위치 | 갱신 | |
| +0xb7c / +0xb80 | 자이로 커서 오프셋 = v1·(−450), v2·360 | 갱신 | 착지점 선택 |
| +0xb84..+0xb94 | 커서: +0xb8c/+0xb90 스틱 누적 위치(레이아웃 px), +0xb94 커서 속도, +0xb84/+0xb88 후보 차이 | 갱신(§6.5) | 착지점 선택 |
| +0xc10 / +0xc14 | 슈퍼점프 시작 후 / 쓰러진 뒤 경과 프레임(각 30에서 멈춤, 그 동안 맵 강제 닫힘) | 갱신 | 갱신 |
| +0xb98 / +0xb9c | 뷰포트 반폭 / 반높이 (레이아웃 px) | 초기화 | 범위 계산 |
| +0xba8 | 맵 카메라 파라미터 리소스 | 초기화 | |
| +0xbb0..+0xbb8 | 카메라 기준 위치 = **(0, −1, 0) 상수**(정정: 앞 판본의 Pos 사본 추정은 틀림) | 생성자 0x7102262994만 | 갱신(§6.2) |
| +0xbbc..+0xbc4 | Pos (생성자 기본 (0, 50, 0)) | 초기화 | 정사영 범위 |
| +0xbc8..+0xbd0 | Rot (도, 생성자 기본 (15, 70, 0)) | 초기화 | 갱신 |
| +0xbd4 / +0xbd8 / +0xbdc | FovY / Near−100 / Far | 초기화 | |
| +0xbe0 | k = 월드 단위/레이아웃 px | 초기화 | |
| +0xbe4 | 팀 반대편이면 맵 180° 회전 허용 [의미 추정] (`VersusMapInfo`가 있고 리소스 +0x3c 플래그가 켜져 있을 때 1, `Lobby_GuideBtn_00` 화면 플래그면 0) | 초기화 | 갱신 |

### 4.3 `spl::gfx::MiniMapModelInfo` [데이터]

`HeightGradation`: MinHeightColor (0.063, 0.063, 0.071, 1), MaxHeightColor (0.976, 0.961, 0.937, 1) — 높이에 따른 바닥 명암. `PaintBrightnessUpAmount` 0.95. `UVScale`: Fence 1.5, NoPaint 2.0, Slope 12.0, Wall 10.0. 렌더 배율 `FrameBufferBase3DRenderScale` 0.65(`IsNoInterpolate`). 소비처(2026-10-02 [camrest]): HeightGradation·PaintBrightnessUpAmount → 재질 uniform `map_min/max_gradation_color`(§6.6) [판독], UVScale 소비처 [미확정].

## 5. 상태와 수명

- 초기화(슬롯 8)에서 카메라 파라미터를 고릅니다: 씬 컴포넌트 `spl__VersusCameraParam`의 `MiniMapCamera`가 있으면 그것, 없으면 `Gyml/VersusMiniMapDefault` [판독: 문자열 0x710495fc2d·형 이름 0x710496816d 사용].
- `spl__VersusMapInfo`가 있으면 리소스 플래그(+0x3c)로 +0xbe4를 정하고, `Lobby_GuideBtn_00` 화면 전역 플래그(0x71058e87ac)면 끕니다 [판독].
- 매 프레임(슬롯 19): 조작/관전 대상 플레이어를 정하고(실패 시 +0x190 = −1), 대상의 PlayerCamera(본체+0xa878)의 `+0x16f4`/`+0x1704` 값을 읽어 기울임 입력으로 씁니다(세이브 IsEnableGyro(+0x4000) && 고정 시점 아님) [판독], 그 두 값의 정체는 [미확정 — 자이로 자세 성분으로 추정].

## 6. 계산식

### 6.1 정사영 범위 (0x7102263214) [판독 + 재구현 계산]

```
t = tan(FovY°)            // sead 사인표 0x7104aa5b5c 의 sin/cos 보간 비. FovY 전체 각(반각 아님) — 표로 45°→1.0, 30°→0.57735 확인
k = Pos.Y · t / halfH     // halfH = 뷰포트 반높이(+0xb9c), halfW = 반폭(+0xb98)
top    = Pos.Z + halfH·k = Pos.Z + Pos.Y·t
bottom = Pos.Z − Pos.Y·t
left   = Pos.X − halfW·k
right  = Pos.X + halfW·k
near = Near − 100 ; far = Far
xlink 전역 속성 MiniMapScale = 0.24 / k
초기 카메라: pos = (중심x, 중심z, 투영.vt+0x20()), at = pos − (0,0,1), up = (0,1,0)   // 갱신에서 덮어씀
```

뷰포트(레이어 5 +0x30..+0x3c)는 실행 시 값이라 정적으로 정하지 못했습니다. 레이어 핸들은 `0x71010f6f34(5)`가 레이어 이름 표(0x71010f7ba8)로 이름을 얻어 레이어 관리자(`0x7103d9ccc0`)에서 **찾기만** 하고, 뷰포트를 쓰는 곳은 이 함수들에 없습니다(agl 레이어 생성 쪽, 미추적) [판독]. 다만 (1) 맵 레이아웃 `VS_MapAnnounce_00` 루트가 1920×1080이고(`RootPane size=(1920,1080)`) (2) §6.3이 `NDC × (x1−x0)/2`를 **그대로 레이아웃 좌표**로 써서 이름표를 놓으며 (3) 커서 범위 ±450/±360도 같은 레이아웃 px이므로, 휴대·거치 모두 아이콘이 맞으려면 뷰포트 폭·높이가 레이아웃 가상 좌표 1920×1080이어야 합니다 [추정 — 강함: 좌표 정합 논리, 코드 확인 아님]. 그 가정으로 만든 표(`ui_minimap.py table`) [재구현 계산]:

| 스테이지 | 카메라 파일 | Pos | Rot(X 기울기, Y 방향) | FovY | 반높이(월드) | 반폭(월드) | MiniMapScale |
|---|---|---|---|---|---|---|---|
| Vss_Carousel | Vss_Carousel_MiniMap | (0, 88, 2) | (25, −45) | 42.5 | 80.64 | 143.35 | 1.6072 |
| Vss_District00 | Vss_District00 | (−2, 91, 5) | (15, 45) | 45 | 91.00 | 161.78 | 1.4242 |
| Vss_Kaisou03 | Vss_Kaisou03_MiniMap | (−6, 91, 5) | (14, 40) | 45 | 91.00 | 161.78 | 1.4242 |
| Vss_Scrap00 | Vss_Scrap00 | (0, 55, 8) | (30, 40) | 55 | 78.55 | 139.64 | 1.6499 |
| Vss_Temple00 | Vss_Temple00 | (0, 80, 5) | (20, 40) | 45 | 80.00 | 142.22 | 1.6200 |
| Vss_Upland03 | Vss_Upland03_MiniMap | (0, 72, 8) | (25, 17) | 45 | 72.00 | 128.00 | 1.8000 |
| Vss_Yagara | Vss_Yagara_MiniMap | (3, 73, 6) | (25, 60) | 45 | 73.00 | 129.78 | 1.7753 |
| Vss_Yunohana | Vss_Yunohana | (0, 75, 3) | (25, 25) | 45 | 75.00 | 133.33 | 1.7280 |
| (기본) | VersusMiniMapDefault | (0, 70, 5) | (25, 30) | 45 | 70.00 | 124.44 | 1.8514 |

- `FovY`는 원근 시야각이 아니라 **정사영 범위를 정하는 값**으로 쓰입니다(이름과 달리) [판독].
- 일부 스테이지는 `_MiniMap` 이름이 아닌 `<스테이지>.game__CameraPoserFixedParam`을 `MiniMapCamera`로 가리킵니다 [데이터].

### 6.2 맵 카메라 방향·기울임·평활 (0x7102264240 698~930행) [판독 + 재구현 계산] (2026-10-02 [camrest] 갱신)

앞 판본의 "회전 순서·축 부호 [미확정]"을 디컴파일 식 전사(`web/tools/ui_minimap.py cam`, 함수 `map_camera`)로 정리했습니다. 기준 위치 `+0xbb0..+0xbb8`은 생성자 0x7102262994가 **(0, −1, 0)**으로 두고(`+0xbb4 = 0xbf800000`) 다른 writer가 없습니다(초기화·갱신 디컴파일 전수 grep) [판독]. 즉 앞 판본의 "기준 = Pos 사본" 추정은 틀렸고, 맵 카메라의 주시점은 월드 원점 아래 1입니다 [정정].

```
g1 = 대상 PlayerCamera+0x16f4, g2 = +0x1704   (세이브 +0x4000 IsEnableGyro && !UI 입력 차단(*0x710582ecb8+0xfa) 일 때만, 아니면 0)
tA = clamp(g2·(−180)·0.07, −70, 70)   tB = clamp(g1·(−180)·(−0.07), −70, 70)          // 도
yaw = Rot.Y·π/180 (+π: +0xbe4 && 대상 팀(+0x190)==1 && !+0x198) ; c = cosf(yaw), s = sinf(yaw)
X = 0 + 12·g1, Y = −1, Z = 0 + 5·g2                                                    // +0xbb0/+0xbb4/+0xbb8 + 기울임 이동
at   = rotY(yaw)·(−X, Y, −Z)  = (−c·X − s·Z, Y, s·X − c·Z)
eye0 = (at.x, Pos.Y + Y, at.z)                                                        // 주시점 바로 위 Pos.Y
eye1 = Rodrigues(eye0, 축 k1 = (−c, 0, s), 각 (tA − Rot.X)°)       // 사인표(0x7104aa5b5c)
eye  = Rodrigues(eye1, 축 k2 = (−s, 0, −c), 각 tB°)
up   = 같은 두 회전을 초기 up(수평 전방)에 적용한 뒤 정규화
```

- **회전은 월드 원점을 지나는 축**으로 eye 위치 벡터 자체를 돌립니다(주시점을 중심으로 도는 것이 아님). 기울임 0이면 |eye| = Pos.Y − 1이고 원점에서 본 eye 고각 = 90° − Rot.X이며, 주시점 (0,−1,0)에서 본 실제 내려다보는 각은 약간 큽니다(기본 Pos.Y 70·Rot.X 25 → 65.35°) [재구현 계산]. 정사영이라 화면에는 시선 방향만 영향을 주므로, 웹은 이 식 그대로 eye/at/up을 만들어 `lookAt` 하면 됩니다.
- 축 규약 [재구현 계산 — 판독 식 전사]: Rot.Y = 0이면 카메라가 **+Z 쪽에서 −Z 쪽을 내려다보고 화면 위 = −Z**, Rot.Y = 90이면 +X 쪽에서 −X 쪽을 봅니다(eye의 방위 atan2(x, z) = Rot.Y). 팀 반전(+π)은 eye·at을 Y축으로 180° 돌린 것과 같습니다. 화면 좌우 = 시선 × up 규약은 레이어 카메라 vt+0x20이 sead LookAtCamera 행렬 갱신이라는 전제의 [추정]입니다.
- 자이로 기울임: g2는 피치(tA를 Rot.X에서 뺌)와 주시점 Z 이동(5·g2), g1은 두 번째 축 회전(tB)과 주시점 X 이동(12·g1)에 들어갑니다(이동은 yaw 회전 전 좌표) [판독].
- 평활(+0xb48 eye, +0xb54 up, +0xb60 at 각각): 맵을 연 프레임(토글 && +0x108)은 즉시 대입, 그 밖에는 `step = max(1, |Δ|·0.5)`만큼만 이동(Δ ≤ step이면 도달) [판독]. 결과는 레이어 카메라(+0x1a0)의 +0x38 eye, +0x44 at, +0x50 up(정규화)과 double 사본(+0x60..+0x88)에 쓰고 vt+0x20(행렬 갱신)을 부릅니다 [판독].
- 검증: `ui_minimap.py selftest` 6항목 추가(총 12 PASS) — |eye| = 69(±0.02, 사인표 보간 오차), 원점 기준 고각 65°, up ⟂ eye, at = (0,−1,0), Rot.Y=0 방향, 팀 반전 [재구현 계산]. 원본 실행·화면 대조는 하지 않았습니다.

### 6.3 월드 → 맵 레이아웃 좌표 (0x710226cd20) [판독]

```ts
function worldToMap(p: Vec3, layer): Vec2 | undefined {
  const V = layer.camera.viewMtx34;          // layer+0x78 객체 +0x8..+0x34 (3×4)
  if (V 에 NaN || 투영 행렬에 NaN) return undefined;
  const v = V · [p, 1];                      // 카메라 공간
  const ndc = layer.projection.project(v);   // layer+0x80 투영, 0x71035899b4 (필요 시 행렬 재계산 vt+0x58/+0x60)
  return { x: ndc.x · (vp.x1 − vp.x0)·0.5,   // 레이아웃 좌표: 화면 중심 원점, 위가 +y (ui2d 규약)
           y: ndc.y · (vp.y1 − vp.y0)·0.5 };
}
```

착지점 선택: 커서(+0xb7c, +0xb80)와 후보 점의 레이아웃 좌표 차이를 +0xb8c/+0xb90에 둡니다(1312·1344·1376·1408행) [판독].

### 6.4 착지점 후보 필터 (0x710226ca6c) [판독-부분]

후보 항목(+0x00 활성, +0x04 종류, +0x08 팀, +0x0c 위치, +0x38 핸들, +0x50 플레이어 번호, +0x54 번호2)이 다음을 모두 만족해야 후보입니다:
핸들 번호 ≠ 직전 선택(+0x188), 팀 == 조작 대상 팀(+0x190), 활성; 플레이어 후보면 그 플레이어 본체가 (특정 모드 플래그일 때) 다운·조작 불가 상태(본체+0x9211, +0xd58>0, +0xf34 ∈ {1,2,4}, PlayerCoopSeq 조건)가 아니고 본체+0x44d가 켜져 있을 것; 종류 1이면 번호2 == 대상 번호(+0x194). 각 조건의 게임 의미(점프 가능 상태 등)는 [추정]입니다.

### 6.5 맵 열기·닫기·커서·슈퍼점프 결정 (0x7102264240 340~700, 930~1010, 2006~2520행) [판독] (2026-10-02 [camrest])

컨트롤러 = `0x7103d55638(관리자 *0x71059a57d0, 관리자+0x110)`(카메라 스틱과 같은 객체). `+0x8` 바이트 = 이번 프레임 눌림(trigger) 비트입니다. 비트 0 = A, 3 = X, 4 = Y로 봅니다 — sead `Controller` PadIdx 규약(A 0, B 1, C/ZL 2, X 3, Y 4)과 안내 문구 "Press A … to Super Jump"·X 맵 열기가 맞습니다 [판독(비트) + 추정(버튼 이름, 강함)].

```
// 강제 닫힘(먼저 검사) — +0x108 = 0
if !(+0xc08 객체 && 그 +0xc >= 2)                         → 닫음                     [+0xc08 의미 미확정]
if !+0x198(관전 아님) && 조작 플레이어 P 있음:
   if PlayerDokanWarp(P+0xa880)+0x30 != 0 : +0xc10 < 30 이면 +0xc10++ 하고 닫음   // 슈퍼점프 시작 후 30프레임 동안 닫힘
   else +0xc10 = 0
   if P+0xd60/+0xde0/+0xdf0/+0xe0c 중 ≥1 (쓰러짐):  +0xc14 < 30 이면 +0xc14++ 하고 닫음
         (30이 되는 프레임 0x710226c824(0), 그 전에는 0x710226c940() — VS_MapAnnounce_01 표시 전환)
   else: (P+0xd58 > 0 && +0xc14 ∈ 1..29 이면 0x710226c824(0)), +0xc14 = 0
// 토글
if trig 비트3(X):  (닫혀 있고 +0x198 이고 컨트롤러+0x114 & 0x24 면 무시) else +0x108 ^= 1, toggled = 1
else if +0x108 && +0x109: 닫음, toggled = 1                                      // 결정 다음 프레임 자동 닫힘
레이어 5 핸들 +0x88 bit1 = +0x108 (켜면 0x22, 끄면 0x20, 렌더러 mutex +0x4c8)       // 3D 맵 그리기 on/off
toggled && 열림 → +0xba0 = 1, +0x109 = 0, 화면 VS_MapAnnounce_00 열기 …
trig 비트4(Y) 또는 열고 닫은 프레임 → 커서·선택 초기화(+0xb84..+0xb94 = 0, +0xb6c/+0xb70 = 자이로 커서, +0x110 = 0, 선택 −1)

// 커서 (열림 && 선택 대상 핸들 +0x180/+0x188 유효 && !UI 입력 차단)
st  = 컨트롤러+0x128/+0x12c (오른쪽 스틱 원시값 — IsReverse 미적용)
spd(+0xb94) = |st| > 0.01 ? |st|·12 : max(spd − max(spd·0.5, 0.01), 0)          // 레이아웃 px/프레임
cur(+0xb8c, +0xb90) += st·spd ; (cur.x + 자이로 x(+0xb7c)) ∈ [−450, 450], (cur.y + 자이로 y(+0xb80)) ∈ [−360, 360] 로 자름

// 슈퍼점프 결정: 열림 && 선택 유효 && !UI 입력 차단 && trig 비트0(A)
P  = 조작 플레이어(0x7101701040)
ok = P && 0x71024bb56c(P+0xa5fb, PlayerDokanWarp, P+0x588, P+0x678, P+0xa678, P+0x925c)   // 점프 가능 판정 [의미 추정]
     (+ 코옵·미션 전역 0x7105863d00+0x3680/+0x3681 이면 P+0x9211/+0xd58/+0xf34/PlayerCoopSeq 조건 추가)
if ok:  메시지(vtable 0x7105624a68, 필드 TargetPosL·TargetBlockId·TargetPlayerIdx·IsUseDir, 리플렉션 0x71023a6040)에
          선택 착지점(+0x110..+0x140, 인덱스 +0x170 하위 10비트 <<11, 종류 비트)을 담아
        0x7101c0e4f8(MiniMap 액터(+0x10)+0x350, …, &조작 플레이어 액터 ID, 메시지)   // 조작 플레이어에게 전달
        +0x109 = 1 (다음 프레임 맵 닫힘), xlink 키 "decide"(0x71048f3cec, ELink+SLink 모드 2)
else:   메시지(vtable 0x7105624b58, 필드 TargetPlayerIdx, 리플렉션 0x71023a6524)를 0x7103e0db84(…)로 보내고
        xlink 키 "push"(0x71048f3cf3)                                             // 점프 불가일 때 [의미 미확정]
```

- 메시지를 받은 플레이어가 슈퍼점프 상태(DokanWarp_St 0xaa …)로 들어가는 처리와 메시지 → PlayerDokanWarp 연결은 [state]/[player] 범위이고 이 문서에서 읽지 않았습니다 [미확정].
- `MILine`·`MILandingPoint` xlink 재생 위치는 이번에도 보지 않았습니다 [미확정].

### 6.6 맵 셰이더 (MiniMapTemplate.bfres → Hoian_UBER) [데이터 + 판독: 역번역] (2026-10-02 [camrest])

`Model/MiniMapTemplate.bfres`에는 모델 2개(`MiniMapTemplate`, `MiniMapTemplateObjPaint`)와 재질 5개(MapGround·MapNet·MapNoPaint·MapSlope·MapWall)가 있고, 모두 `Hoian_UBER`에 `blitz_map_paint=1, blitz_map_height=1, enable_normal_map=0` 옵션입니다(`analysis/camrest/MiniMapTemplate.dump.json`) [데이터]. [graphics] 규칙(shaders.md §3.5)으로 프로그램을 골라 Ryujinx 역번역한 GLSL은 `analysis/camrest/minimap_shader/`(`web/tools/ui_minimap_shader.py`) [실행: 자체 도구]:

| 모델 / 재질 | 프로그램 | 옵션 차이 |
|---|---|---|
| MiniMapTemplate MapGround·MapSlope (`blitz_paint_type 1`) | 387 | 일치 |
| MapNoPaint | 381 | 일치 |
| MapWall (`enable_shading 0`, 거칠기 맵) | 358 | 일치 |
| MapNet (`enable_opacity_tex`) | 4081 | 일치 |
| ObjPaint MapGround·MapSlope (`blitz_paint_type 5`) | 381 근사 | 키 표에 5 조합 없음 [미확정] |

MapGround(387) 프래그먼트 핵심 [판독: 역번역 GLSL]:

```glsl
vec3 g = texture(cBlitzWallPaintGrid /*gsys_user3*/, vec2(uvP.x, 1.0 - uvP.y)).rgb;   // uvP = in_attr5.xy (in_attr6.w<0 이면 .zw)
float m = max(g.r, max(g.g, g.b));
bool painted = clamp(m - BlitzUBO0[21].w, 0, 1) * 1000.0 > 0.5;                          // 칠 임계(UBO)
vec3 oneHot = clamp((g - m + 1e-4) * 1e8, 0, 1);                                          // 최대 채널 = 팀
vec3 team = oneHot.r*UBO0[3].rgb + oneHot.g*UBO0[10].rgb + oneHot.b*UBO0[62].rgb;         // 채널별 팀색
float h = clamp((height /*in_attr1.w*/ - Mat.map_min_height) / (Mat.map_max_height - Mat.map_min_height), 0, 1);
vec3 grad = mix(Mat.map_min_gradation_color.rgb, Mat.map_max_gradation_color.rgb, h);     // 높이 명암
if (painted) { hsv = rgb2hsv(team); hsv.v = min(hsv.v + Mat.map_max_gradation_color.w, 1.0);
               c = hsv2rgb(hsv) * grad; c = mix(team*UBO0[45].y, c, clamp(UBO0[45].z,0,1)); // 이어서 UBO0[47].xy 로 HSV 명도 한 번 더
               emission = c * UBO0[18].z; }
else          c = texture(cTexAlbedo, uv0).rgb * grad;                                       // 칠 안 된 바닥 = 알베도 × 높이 명암
// 이후 일반 조명(Env 라이트·그림자 프리패스·안개)
```

- CPU 쪽 uniform 설정 `0x7102b78608`(호출 0x7102b717fc) [판독, `analysis/decomp/camrest/minimap_gfx.c`]: `map_min_height`/`map_max_height` = 관리자 객체 +0xdc/+0xe0(writer 미확인), `map_min_gradation_color` = `HeightGradation.MinHeightColor`(+0x40, rgba), `map_max_gradation_color` = (`HeightGradation.MaxHeightColor`(+0x30).rgb, **`PaintBrightnessUpAmount`**(본체 +0x40) = 0.95) — 리플렉션 0x7102ba02bc(+0x30 Max, +0x40 Min), 0x7102ba14e8(PaintBrightnessUpAmount, 플래그 +0x46) [판독]. 즉 칠한 곳은 팀색 명도를 +0.95(상한 1) 올린 뒤 높이 명암을 곱합니다.
- 칠 텍스처는 `cBlitzWallPaintGrid`(gsys_user3) — 도색 그리드의 RGB 채널별 팀 점유로 보입니다 [추정]. 채널↔팀 대응과 UBO0[3]/[10]/[62]·[21].w·[45]·[47]·[18] 값은 [paint]/[graphics] 범위로 [미확정].
- `UVScale`(Fence 1.5, NoPaint 2.0, Slope 12, Wall 10)을 쓰는 곳은 확인하지 않았습니다 [미확정].

## 7. 화면·애니·이펙트 연결

- `VS_MapAnnounce_00`: `N_Map_00/N_Rival_00`에 `L_Name_00..07`(파츠 PlayerShortCut_00, 위치 (−675,0)/(0,450)/(675,0)/(−747,−450) 등 4개 표시·4개 숨김), `W_Base_00/01` 상대팀 목록(`L_Rival_00..03`, PlayerShortCut_01), `N_Show_00` 안내 문구("Press A while holding + to Super Jump!"), `N_Result_00/N_Home_00` 시작 지점 행(P_Direction_01 화살표, T_Home_00), `N_Effect_00..02` [데이터]. 갱신 함수 0x710226d048(i, a, b)이 i번째(0~7) 이름표 컨트롤(화면+0x268+i·8)의 `0x7103172d9c`를 부릅니다 [판독].
- `VS_MapLine_00`: 슈퍼점프 선(`N_RotateRoot_00/N_Rotate_00`, `P_Line_00`, Attention 강조, `P_Arrow_00`), 애니 In/Out/Loop/Rotate/Attention/Key [데이터]. 갱신 함수에서 화면 이름으로 찾아 씁니다(5198행) [판독-부분].
- `VS_MapAnnounce_01`: 관전 자동 시점 키 안내. 0x710226c824(b)/0x710226c940이 화면 mutex를 잡고 `0x71033e106c`(표시/숨김) 또는 화면 vt+0x2b8을 부릅니다 [판독].
- xlink 키(갱신 함수 안 문자열): `MILine`, `MILandingPoint`, `decide`(SplMiniMap ELink/SLink 사용자) [데이터: 키 이름], 재생 조건 [미확정]. 사운드 팩 `Sound/Resource/SplMiniMap.bars.zs` [데이터].

## 8. 다른 기능과의 상호작용

| 상대 | 연결 | 수준 |
|---|---|---|
| 플레이어 카메라 | 관전 상태(본체+0x1054)에서 맵이 열려 있으면(0x7102262578) 카메라 쪽 분기 변경 — [../camera/player_camera.md](../camera/player_camera.md) | [판독-부분] |
| 조작 설정 | 세이브 +0x4000(IsEnableGyro)이면 자이로 기울임·커서 사용 | [판독] |
| 도색 | 맵에 보이는 잉크는 도색 텍스처를 맵 모델에 입혀 그린 것으로 보임(렌더 패스 순서 Paint → … → MiniMap) — [../paint/paint_and_score.md](../paint/paint_and_score.md) | [추정] |
| 슈퍼점프 | A 결정 → 메시지(TargetPosL·TargetBlockId·TargetPlayerIdx·IsUseDir)를 조작 플레이어 액터 큐로 전송, 다음 프레임 맵 닫힘, 점프 시작 후 30프레임 강제 닫힘(§6.5). 받는 쪽 처리 | 보내는 쪽 [판독], 받는 쪽 [미확정] |
| 조작 설정(반전) | 맵 커서는 컨트롤러 오른쪽 스틱 **원시값**을 읽어 IsReverseUD/LR이 적용되지 않음(카메라는 적용, [../camera/player_camera.md](../camera/player_camera.md) §6.4) | [판독] |
| 쓰러짐 | 본체+0xd60/+0xde0/+0xdf0/+0xe0c 중 하나라도 ≥1이면 30프레임 동안 맵 강제 닫힘 | [판독] |
| 팀 색 | 맵 위 잉크·아이콘 색은 팀 색 세트 — [../graphics/team_color.md](../graphics/team_color.md) | [추정] |

## 9. 웹 포팅

| 모듈(웹 권장 이름) | 책임 |
|---|---|
| `MiniMapCameraData` | 스테이지 `MiniMapCamera`(없으면 기본값) 로드 — `ui_minimap.py table`과 같은 규칙 |
| `MiniMapProjection` | §6.1 정사영 범위, `MiniMapScale` |
| `MiniMapCamera` | §6.2 eye/at/up 식(원점 축 회전, 주시점 (0,−1,0))·팀 180°·기울임·평활 — `ui_minimap.py cam`과 같은 값 |
| `MiniMapRenderer` | 스테이지 모델(+`MiniMapModel` 컴포넌트 모델)을 정사영으로 오프스크린 렌더. 셰이더는 §6.6 역번역 식(칠 그리드 최대 채널 → 팀색, 명도 +0.95, 높이 명암 곱, 미칠 = 알베도×명암) — UBO 값·UVScale 소비는 [미확정] |
| `MiniMapOverlay` | `VS_MapAnnounce_00/01`, `MapIcon_00`, `VS_MapLine_00` 레이아웃([ui_layout_format.md](ui_layout_format.md) 파서·렌더러 재사용), 아이콘 위치 = §6.3 |
| `SuperJumpPicker` | §6.4 후보 필터, §6.5 커서(스틱×12 px/프레임, ±450/±360)·A 결정 메시지·Y 초기화, X 토글 |

구현 순서: 데이터 로드 → 정사영 + 정적 카메라(Rot 그대로)로 맵 렌더 → worldToMap로 아이콘 배치 → 팀 180° → 기울임·평활 → 착지점 선택. 웹에서는 뷰포트를 캔버스 크기로 두고 `k`를 그에 맞춰 다시 계산하면 원본과 같은 월드 범위가 됩니다(범위는 Pos.Y·tan(FovY)로 뷰포트와 무관, 뷰포트는 px 배율에만 관여).

## 10. 검증

| 종류 | 내용 | 결과 |
|---|---|---|
| [데이터 + 원본 표 계산] | sead 사인표로 만든 tan: 22.5°/30°/45°/60° | 0.414214 / 0.577350 / 1.000000 / 1.732052 (math.tan과 1e-6 이내) |
| [재구현 계산] | `ui_minimap.py selftest` — 기본 카메라 반높이 70, 반폭 70·960/540, MiniMapScale, near −99.9 | 6 PASS |
| [재구현 계산] | `ui_minimap.py selftest` 추가 6항목(2026-10-02 [camrest]) — §6.2 eye/up/at 전사식: \|eye\|=69, 원점 고각 65°, up⟂eye, at=(0,−1,0), Rot.Y=0 방향(+Z에서 −Z, 화면 위 −Z), 팀 반전 | 총 12 PASS |
| [실행: 자체 도구] | `ui_minimap_shader.py` — MiniMapTemplate 재질 10개(모델 2) 프로그램 선택·역번역 | 8개 옵션 완전 일치(387/381/358/4081), ObjPaint Ground·Slope 2개는 `blitz_paint_type 5` 조합 없음 |
| [데이터] | Vss_* 8개 스테이지 카메라 표(§6.1) | 추출 |

검증 안 함: 원본 실행 화면 대조, 뷰포트 실제 크기, §6.2 식의 원본 실행(전사 재구현만), §6.5 입력 흐름 실행, 렌더 결과(셰이더 UBO 값 없음).

## 11. 미확정과 필요한 근거

| 항목 | 필요한 근거 |
|---|---|
| 뷰포트(레이어 5 +0x30..+0x3c) 실제 크기 — 1920×1080 레이아웃 가상 좌표로 [추정 — 강함](§6.1) | `0x71010f6f34`는 이름 찾기뿐. agl 레이어 생성·뷰포트 설정 함수(레이어 관리자 0x7103d9ccc0 쪽), 실행 값 |
| ~~§6.2 회전 순서·부호~~ 해소(전사식 재구현, §6.2). 남은 것: PlayerCamera +0x16f4/+0x1704 정체, 원본 실행 대조 | PlayerCamera 해당 필드 writer, 갱신 함수 에뮬 |
| ~~맵 잉크·높이 그라데이션 셰이더~~ 해소(§6.6 역번역). 남은 것: UBO0 팀색·임계 값, `map_min/max_height` writer(관리자 +0xdc/+0xe0), `blitz_paint_type 5` 프로그램, UVScale 소비 | [paint]/[graphics] UBO 채우는 코드, 0x7102b70fa0 관리자 |
| ~~맵 열기(X 버튼) 입력과 +0x108 writer~~ 해소(§6.5: trigger 비트 3 토글, 강제 닫힘 조건). 남은 것: 비트↔버튼 이름은 sead PadIdx 규약 [추정 — 강함], +0xc08 조건 의미 | sead 컨트롤러 버튼 매핑 함수 |
| 슈퍼점프 실행 연결 — 보내는 쪽 해소(§6.5). 남은 것: 메시지(vtable 0x7105624a68) 수신 → PlayerDokanWarp 시작, 'push' 경로 의미, xlink MILine/MILandingPoint 재생 조건 | 메시지 처리 함수(조작 플레이어 액터 +0x350 큐 소비), 갱신 함수 4500~5300행 |
| `VS_MapAnnounce_00` 이름표 컨트롤 `0x7103172d9c` 동작 | 해당 함수 디컴파일 |
