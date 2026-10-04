# 그래픽 r11 gfx-diff — 광원 영역

2026-10-04. 사격장(Lby_Lobby00) 화면의 광원 경로를 원본·웹 차등 실행으로 검사했습니다. 방법과 규칙은 `analysis/gfx_r11/DIFF_BRIEF.md`를 따랐습니다. 이전 중단 기록(§7)은 그대로 둡니다.

## 1. 결론

| 항목 | 결과 |
|---|---|
| 비교한 짝 | 13개. CPU 10짝, 셰이더 3짝(+재질 담당이 한 재질 셰이더 조명 항 1짝 참조) |
| 일치 | 13/13. CPU는 비트 일치이거나, SDK sinf/cosf와 JS libm 차이(≤2e-7)만 있습니다. 셰이더는 f32 반올림 순서 차이만 있습니다(§3) |
| 갈라진 지점 | 식이나 데이터가 원본과 다른 곳은 찾지 못했습니다. GPU 정밀도 경계는 1곳입니다. Illuminate 1샘플 LOD 항 `fma(a²,nh²,−nh²)+1`이 r 0.05에서 상쇄되어 면 2개에서 상대차 3.4e-3이 납니다. GLSL ES 3.0에는 fma가 없어 고칠 수 없습니다 |
| 웹 코드 변경 | 층 12(잉크 반사) 생산자를 추가했습니다(§4.1, env_prefilter.ts·lighting.ts). 광원 식은 바꾸지 않았습니다 |
| 원본 사진(따뜻함·밝음)과의 차이 | 주광 방향·색·세기는 원본 데이터 그대로 셰이더까지 갑니다(Env[5]=(6.706,8.510,10), Env[23]=월드 방향). 주광 색 자체가 푸른색 (0.67,0.85,1)입니다. 따라서 따뜻한 인상은 주광에서 오지 않습니다. 남은 후보는 §5입니다 |

## 2. 짝 목록과 비교 결과

| # | 원본 | 웹 | 입력 | 결과 |
|---|---|---|---|---|
| 1 | 0x7102b607c4 MainLight Color/Intens → DL+0x128/+0x1a0 | map.ts `parseEnv` → lighting.ts `hLightColor`/`hLightAlpha` | 로비 1 + 무작위 64 (unicorn) | 색·세기 비트 일치, `hLightColor = f32(I·c)` 비트 일치 |
| 2 | 0x7102b60ea0 Lat/Lon → DL+0x1c0 (SDK sinf/cosf) | `lonLatToDir` → `hLightDirection` | 같은 65건 | 로비 비트 일치, 무작위 ≤2e-7(libm) |
| 3 | **0x71035d6500** agl DirectionalLight 뷰별 갱신 | 셰이더 `normalize(−hLightDirection)` | 로비 + 무작위 47(행렬·ViewCoordinate 0/1) | ViewCoordinate 0: `+0x208[view]` = 정규화된 월드 방향 ≤2e-7. 로비 비트 일치 |
| 4 | **0x71036b35c0** Env UBO 512 B 채우기(DL 1 + agl Fog 2, 실제 실행) | lighting.ts uniforms | 로비 + 무작위 16 | Env[5] ↔ hLightColor 비트 일치, [5].w ↔ hLightAlpha, [4].w = I, [23] ↔ 정규화 방향, [10] ↔ hDepthFog 비트 일치, [11].w/[12].x ↔ −S/(E−S)·1/(E−S), [13] ↔ hHeightFog, [14] = (0,−1,0, −S/(E−S)), [15].x ↔ 1/(E−S) |
| 5 | 0x7101033b78 방향광 → SH | `directionalSH` | 기존 128 | 기존 fixture 비트 일치(tests/graphics_native) |
| 6 | 0x7101033dc0 SH 평가 | `evalSH` | 기존 128 | 비트 일치(기존) |
| 7 | 0x71010325d4 SH 포장 | `packReadbackSH` | 기존 128 | 비트 일치(기존, tests/common_lighting) |
| 8 | 0x710102ff04 Illuminate UBO | `illuminateUBO` | 기존 65 | 일치(gfx-light 2차) |
| 9 | 동적광 격자·원뿔(0x7101048fa8 등) | `lightGrid`/`coneCell` | 기존 32시퀀스·256판정 | 일치(기존) |
| 10 | Hoian_Proc `GGXEnvBRDF` 픽셀 셰이더(보완 역번역) | env_prefilter `ggxEnvBRDF`(LUT 생산) | 8점 (NoV,r), 같은 VdC | 최대차 1.2e-7 |
| 11 | `GGXPrefilterEnvMap` MRT1/FILTER2/**ILLUMINATE1** (0x7101037098) | `ILLUMINATE_FRAGMENT` | 6방향, 로비 18광원 UBO, 같은 mock 큐브·하이라이트 | 면 0/3/4는 상대차 ≤1e-6. 면 1/5는 3.4e-3(§3) |
| 12 | `GGXPrefilterEnvMap` MRT1/FILTER2/ILLUMINATE0, 12층 400샘플 (0x7101036a18) | `LAYER_FRAGMENT` `hPrefilter` | 층 0/3/7/11 × 6방향 | 상대차 ≤5.7e-6 |
| 13 | `IrradianceCubeMapAllToSH` W128 (0x710103289c, 이번에 보완 역번역) | `SH_PROJECTION_FRAGMENT` | 표본 id 12개(면 0~5) | 방향 생성·7 MRT 상수·칸 대응 일치. zz 항만 fma 상쇄로 절대차 ≤2e-12 |
| 참고 | p946/917/1714/1689 재질 셰이더의 직접광·SH·반사·동적광 항 | forward.ts | 재질 담당 표본 8개 | 상대차 ≤2e-7([r11 재질 차등](graphics_r11_diff_재질.md)). 같은 일을 다시 하지 않았습니다 |

셰이더 실행 방법: 새 도구 `web/tools/glsl_eval.mjs`(GLSL 부분집합 CPU 해석기, 매 연산 f32 반올림)로 **원본 역번역 GLSL 텍스트와 웹 GLSL 문자열을 그대로** 실행합니다. 텍스처는 두 쪽에 같은 해석 함수를 줍니다. 웹 쪽 GLSL은 `NativeEnvironment` 인스턴스의 실제 셰이더 문자열입니다.

## 3. 정밀도 경계(식 차이 아님)

- Illuminate 1샘플(`cParam0.w = 1`, r = 0.05): `d = 1/max(a²·nh²−nh²+1, 1e-8)`에서 a² = 6.25e-6이고 nh ≈ 1입니다. 그래서 f32 반올림 한 번이 d를 몇 % 바꾸고, LOD가 0.651~0.678로 흔들립니다. 원본도 면마다 0.595/0.651/0.678로 흔들립니다. 원본은 fma 한 번 반올림이고 웹 GLSL ES 3.0에는 fma가 없습니다. 영향은 해당 면의 R·G가 3.4e-3 상대차입니다.
- SH 투영 zz 항 `fma(z², .00012095132, −4.0317e-5)`도 같은 유형이며 절대 2e-12입니다.

## 4. 캡처 큐브 입력(맵 재질 cube 변형) 판독

| 항목 | 결과 | 수준 |
|---|---|---|
| 캡처 패스 assign | 재질 렌더 정보 플래그 0x710365c7a8: renderInfo 키 표 0x7105726e00의 [4] `gsys_cube_map`, [5] `gsys_cube_map_only` 값 "1"이면 +0x78 비트 4/5를 켭니다. 프로그램 검색 0x710365d6bc: 패스별 (assign 색인 +0x1b6+3·pass, 시작 셰이딩모델 +0x1b7)로 `gsys_weight`/`gsys_assign_type`(표 0x710572cf80, [7]=cubemap)/`gsys_index_stream_format`를 넣어 0x7103775b98 → g3d `UpdateVariation` 0x7100896810을 부릅니다. 이 함수는 키가 없으면 program을 0으로 둡니다(`str xzr,[x19,#0x20]`). 그러면 다음 셰이딩모델을 찾고, 끝까지 없으면 null입니다 | [판독] `analysis/decomp/r11_gfx_light/cube_assign*.c` |
| Hoian_UBER 키 표 | `gsys_assign_cubemap` 프로그램은 66개뿐입니다. 사격장 맵 재질 61종(Fld_VSLobby·FldBG_LobbyDV·Screen·Door)은 **cubemap 변형이 없습니다**. assign 외 옵션이 같은 후보는 material/zonly/dynamic 변형뿐입니다. cubemap 변형이 있는 것은 Glass(5408→**5410**, 전체 셰이딩·정적/동적 그림자 포함), mSky(25→27), **Fld_Emission4EnvMap**(20→**22**)입니다 | [데이터] `analysis/gfx_r11/cube/select_cube.py` → `selection.json` |
| Fld_Emission4EnvMap | 로비 배치 `DObj_Fld_Emission4EnvMap` pos (36.21, 8.69, −25.90), scale 10, 상자 24 인덱스. renderInfo `gsys_cube_map 0`·`gsys_cube_map_only 1`이라 **환경 큐브에만** 그립니다. p22 출력은 `emission_intensity(0)·intens_in_envmap·emission_color + albedo_color(1,1,1)` + 안개 → 휘도 (1,1,1)입니다. 팩에는 재질 값 덮어쓰기가 없습니다. 캡처점 기준 입체각은 약 0.047 sr이라 SH DC 기여는 약 0.004입니다(웹 DC 0.37 대비 1%) | [데이터]+[판독] `analysis/gfx_r11/cube/p22.frag` |
| 맵 재질이 큐브에 그려지는가 | **그려집니다.** 패스별 assign 결정 0x710365c92c(0x710365d234~0x710365d2f0)는 23개 패스마다 assign k부터 시작합니다. 셰이딩모델 +0xc0 가용 비트를 보고, 없으면 대체 표 **0x7104ac06b0**를 따라갑니다. 이 표에서 `cubemap(7) → material(0)`, reflection·dilate·xlu_zprepass·user·dynamic → material, zprepass·gbuffer·silhouette·depthshadow → zonly이고, material 다음은 끝(23)입니다. 결과는 +0x1b6/+0x1b7(+3·pass)에 기록됩니다. 따라서 사격장 맵 재질은 캡처 큐브에 **화면용 프로그램(1714/946/917…)**으로 그려집니다. 웹 방식(맵을 forward 재질로 캡처)과 같습니다 | [판독] |
| 캡처 대상 renderInfo | 로비 visual.glb 모델 전체 재질의 원본 `gsys_cube_map`은 1, `gsys_cube_map_only`는 0입니다. 예외는 `SadowMtl00`(static_depth_shadow_only 1, 그림자 담당이 visible=false로 처리)뿐입니다 | [데이터] `analysis/gfx_r11/cube/cube_renderinfo.{py,json}` |
| 큐브 시선 구성(웹 형상 기준) | CapturePos에서 6×24² 방향으로 광선을 쏜 결과입니다. 하늘이 보이는 비율은 0.41%입니다. 나머지는 LobbyFloorConcrete 23%, LobbySign02 13%, BigScreen 12%, mLobbyFloorRubber 10%, MetalPanelBlack 7%, SadowMtl00 6%(원본·웹 모두 안 그림), 천장 8%, Wall02 3%, Glass 1.5%입니다. 하늘이 보태는 몫은 약 0.4%×하늘 휘도(×80) ≈ (0.07,0.08,0.11)로, 웹 DC (0.37,0.44,0.57)의 파랑 쪽 일부입니다 | [웹 실행: CPU 광선] |

웹에 반영하지 않은 것: Emission4EnvMap 상자(기여 1%)는 그리지 않았습니다. Glass는 웹 재질로 그리며 cube 변형 5410은 쓰지 않습니다.

### 4.1 층 12(잉크 반사) 생산자 — 로비 확정

0x710102ce04 → 0x710103921c → 0x7101036a18 → 0x7101036d84(param_4 = 1036A18 param_6 bit0, param_5 = plVar13) 순서로 호출됩니다.
- `plVar13`은 Illuminate 객체가 아니라 **env의 첫 DirectionalLight**입니다. 타입 ID `*0x7105999180`, RTTI 0x710555a088(+0x48 검사)로 찾습니다. 로비에는 defaultday "Main"이 있고 MainLight가 여기에 기록되므로 non-null입니다.
- `param_6 = (capture+1000 == (ambMgr+0x5c8 ^ 1))`입니다. +1000은 리드백 횟수입니다(0x710102c694가 0으로 놓고 SH마다 +1, `(5c8^1) < count`이면 끝). 로비는 +0x5c8 = 0이라 **두 번째 캡처(횟수 1)**에서만 bit0 = 1입니다.
- 따라서 첫 캡처에서는 층 12가 BlackCube(`*(0x7105999230)+0x30`)이고, **최종 층 12는 "illuminate"(1샘플, r = BlitzUBO0[18].x = 0.05, Illuminate UBO는 0x710102f254가 MainLight로 기록)를 그 캡처의 base 큐브에서 그린 결과**입니다 [판독+데이터].
- 웹 반영(env_prefilter.ts·lighting.ts·ink_surface.ts): `NativeEnvironment.inkLayer(renderer, source, pass===1)`가 같은 Illuminate 식을 기존 12층 아틀라스의 **빈 칸**(층 2 행의 오른쪽 절반, `PREFILTER_INK_TILE` x 384·64², 웹 정책)에 면별로 그립니다. 조건이 맞지 않으면 `hPrefilInkAvailable 0`이 되어 0(BlackCube)을 반환합니다. 조회 `hPrefilInkSample(d)`(lod 0)는 `hPrefilAtlas`를 그대로 쓰므로 **sampler가 늘지 않습니다**. 처음에는 별도 samplerCube로 만들었는데, `r11_sampler_budget` 테스트에서 잉크 재질 4종이 17개로 넘쳐 아틀라스 방식으로 바꿨습니다. 잉크 분기는 ink_surface.ts에서만 `hNativeEnvSpecular` 대신 `hNativeInkSpecular`(층 12 × (F0·brdf.x+brdf.y))를 씁니다. forward.ts와 캐릭터 셰이더는 바꾸지 않았습니다.
- 검증: 재질 담당 테스트 `r11_gfx_diff_material` 잉크 분기의 원본(946 실행) 대 웹 색이 상대차 2e-4 이내로 일치합니다. 이 테스트는 웹의 층 0을 기대값으로 고정하고 있었습니다. 원본은 같은 테스트 안에서 층 12를 요청하므로(근거), 기대값을 원본 층 12(아틀라스 칸)로 고쳤습니다. `r11_sampler_budget` 전부 16개 이하입니다.

### 4.2 노란 SH의 남은 후보 [추정] — 3차 조사 결과

- **env 객체 집합(가설 ②): 부정 쪽입니다** [판독, 부분]. 큐브 장면 렌더러는 생성 0x710373e948 → 0x71036d1138로 만들어집니다(패스 = 뷰×12, 면 6 × "Model(CubeMap/Opa+AlphaMask)"/"Model(CubeMap/Xlu)", assign 7). 이 렌더러는 자기 Env UBO 묶음(+0x2a8, 0x71036ae130)을 가집니다. 그 env 포인터(+0x7b8 = 0x2a8+0x510)는 생성 인자 `[sp+0x18] = *(scene+0x38)`인 장면 env이고, 0x71036b35c0가 같은 첫 DirectionalLight("Main", MainLight가 기록)를 읽습니다. 뷰 번호가 DL 뷰 배열 범위를 넘으면 원소 0을 씁니다. 따라서 큐브 Env[5]/[23]은 화면과 같습니다.
- **gsys_shadow_prepass(가설 ①): 확정하지 못했습니다.** 시스템 텍스처 이름표 0x7105726130의 [5]를 쓰는 곳은 샘플러 위치표 생성 0x710366096c뿐입니다. 그리기 때 큐브 뷰에 묶이는 텍스처는 찾지 못했습니다. SPP 관리자의 뷰 기록(0x1448 간격, +0x1040 텍스처·+0x10c8 swizzle)이 큐브 뷰에도 만들어지는지도 확인하지 못했습니다. 기존 판독(common_shadow_r6)상 clear/기본 SPP.x = 1(그림자 없음)이라, 기본값이 묶이면 직접광은 빠지지 않습니다.
- 따라서 "큐브에서 주광 직접항 제외"는 확정할 수 없어 **웹 캡처 경로는 바꾸지 않았습니다**(규칙: 원본 식으로만). 남은 확인 경로: 0x71036d1138 객체의 그리기 vfunc(+0x428 보유자)에서 시스템 텍스처 배열을 채우는 곳, 또는 cubemap_mgr(0x71035bfec8, "cubemap_unit_%d")의 뷰 컨텍스트.

이전 판단(아래)은 기록으로 남깁니다.

### 4.3 4차 추적 — 큐브 뷰 `gsys_shadow_prepass`([5]) 바인딩 [미확정]

| 시도 | 결과 |
|---|---|
| SPP 기록 소비자 탐색 | SPP 관리자는 `scene+0x438`(= env+0x1338 ShadowPrePass)입니다. 뷰별 기록은 0x1448 간격(+0x1d8, 개수 +0x1d0)이고 +0xfe8/+0x1040 텍스처, +0x10c8 swizzle을 둡니다. 기록 색인은 뷰 번호이며, **범위 밖 뷰는 기록 0(화면 뷰)을 씁니다**(0x71036cd2b8, 0x7103725060, 0x7103752be4의 `b.ls` 분기). 이 오프셋을 읽고 쓰는 곳 46곳 중 판독한 것은 생성자와 그림자 그리기(0x7103725344 → 0x710372aca8, 0x7103764c28)뿐이고, 재질 sampler에 묶는 곳은 아니었습니다 |
| SPP 그리기 구동 | 0x7103764c28은 0x7103752be4(장면 그림자 단계, `param_3+8` = 뷰 번호) 한 곳에서만 불립니다. 큐브 렌더러가 이 단계를 거치는지는 확인하지 못했습니다 |
| 재질 시스템 sampler 표 | 0x710366096c가 32개 시스템 슬롯(이름표 0x7105726130, [5] = gsys_shadow_prepass)의 위치를 `{+0x10 유효 비트, +0x14 위치[32]}` 객체로 만들어 셰이딩 assign의 [2]에 둡니다(크기 0x98). 그리기 때 이 표를 읽어 텍스처를 묶는 함수는 찾지 못했습니다 |
| 큐브 렌더러 | 0x71036d1138(생성 0x710373e948, gsys+0x428 보관). 패스 표와 Env UBO까지만 판독했고, 그리기 vfunc는 찾지 못했습니다. cubemap_mgr 0x71035bfec8/0x71035bf7c8(`cubemap_unit_%d`, vtable 0x7105722348)은 agl env CubeMap 유닛으로, SPP 관련 바인딩이 보이지 않았습니다 |
| 간접 단서 | Glass의 cubemap 변형 5410은 SPP를 쓰지 않고 정적·캐스케이드 깊이 그림자를 직접 샘플합니다. 다만 화면용 5408도 같은 방식(반투명)이라 SPP 부재의 근거는 되지 못합니다 |
| 동적(unicorn) | 큐브 그리기 경로는 실행 중 gsys 장면 상태(뷰·렌더 타깃·명령 버퍼)가 있어야 돌릴 수 있습니다. 메모리 덤프가 없어 이번에는 시도하지 않았습니다 |

결론: 큐브 뷰의 [5] 바인딩은 **[미확정]**이고, web 캡처 경로는 바꾸지 않았습니다. SH(−z)·바닥 반사의 역산값 비교도 하지 않았습니다(바꾼 것이 없음). 다음 주소는 아래와 같습니다.
1. 셰이딩 assign [2] 객체(+0x10 유효 비트·+0x14 위치)를 읽는 그리기 시점 바인더
2. 0x710373d384가 gsys+0x428에 둔 큐브 렌더러의 vtable(생성자 0x710373e8xx 주변)과 그리기 슬롯
3. 0x7103752be4를 부르는 장면 그림자 단계 상위(큐브 뷰도 이 단계를 지나는지)
4. 범위 밖 뷰 → SPP 기록 0 대체 규칙이 재질 바인딩에도 쓰이면, 큐브 면은 화면 뷰 SPP를 화면 UV로 샘플합니다(직접광이 무늬처럼 일부 빠짐). 이 가능성은 판독 근거 없이 [추정]입니다


재질 담당이 역산한 원본 SH(−z) ≈ (0.25,0.25,0.11)의 색비 R=G≈2B는 **벽 베이크 빛 색**((0.058,0.058,0.029))과 같습니다. 웹 캡처에서 벽·바닥은 주광 직접항 `alb/π·NoL·(6.7,8.5,10)·shadow`(푸른색)이 베이크 빛보다 큽니다. 원본 큐브 패스에서 주광 직접항이 빠지거나 크게 줄면 원본 색비가 설명됩니다. 확인할 곳은 두 군데입니다.
1. 큐브 뷰에서 시스템 텍스처 `gsys_shadow_prepass`(표 0x7105726130의 [5])에 무엇이 묶이는지. 기본 검정이면 shadow = 0입니다.
2. 큐브 뷰의 Env UBO(0x71036b35c0 view 인자)가 가리키는 env 객체 집합(`gsys_env_obj_set TPS`)에 Main DirectionalLight가 있는지.

둘 다 판독하지 못했으므로 웹 코드는 바꾸지 않았습니다.

## 5. 원본 사진 차이에 대한 판단

- 광원 영역의 식·데이터 경로는 원본과 같습니다. 주광은 푸른색 ×10이고, 바닥의 진한 그림자는 정적 깊이 그림자(그림자 담당, SHARED `[r11 gfx-diff 그림자]`)입니다.
- 벽 베이지는 재질 담당이 "환경 SH 쪽"으로 판정했습니다. SH 투영·포장·평가·Illuminate·12층은 원본과 같고, 맵도 원본처럼 화면용 프로그램으로 큐브에 그려집니다(§4). 남은 차이는 **큐브 패스에서의 조명 입력**입니다(§4.2: 주광 직접항·SPP 바인딩·env 객체 집합) [추정].
- 컬러 그레이딩 커브(R 탄젠트 0.765 > B 0.617 > G 0.510)의 색감 기여는 후처리 담당 범위입니다.

## 6. 테스트·도구

| 파일 | 내용 |
|---|---|
| `web/tools/r11_gfx_diff_light_emu.py` | unicorn: 0x7102b607c4·0x7102b60ea0·0x71035d6500·0x71036b35c0 → `tests/fixtures/r11_gfx_diff_light_native.json` |
| `web/tools/glsl_eval.mjs` | GLSL 부분집합 해석기(원본 역번역·웹 GLSL 공용) |
| `web/tools/r11_gfx_diff_light_shaders.mjs` | 원본 Hoian_Proc 셰이더 3종 실행 → `tests/fixtures/r11_gfx_diff_light_shader_native.json`, 공용 mock |
| `games/splatoon3/tests/r11_gfx_diff_light.test.mjs` | 8건: MainLight 65, DL 뷰 48, Env UBO 17, BRDF 8, Illuminate·12층, SH 투영 12, 층 12 조건, 잉크 층 12 반사식·셰이더 연결 |
| `analysis/gfx_r11/proc_fixed/sh/` | IrradianceCubeMapAllToSH 6변형 보완 역번역 |
| `analysis/gfx_r11/cube/` | cube 변형 선택표, renderInfo 표, p22/p5410 역번역 |
| `analysis/decomp/r11_gfx_light/cube_assign*.c`, `cube_draw.c` | 프로그램 선택·g3d 선택기·0x710103dd08 판독 |

`npm run typecheck` 통과, `npm test` 452/452 통과(`r11_sampler_budget` 포함).

## 7. 이전 중단 기록(2026-10-04 오전)

짝 11개를 목록으로 만들었고, Env[23] 좌표계(0x71035d6500)를 디스어셈블로 판독했으며, p1714 식을 판독으로 대조했습니다. 이 내용은 위 §2~§4로 흡수했습니다.
