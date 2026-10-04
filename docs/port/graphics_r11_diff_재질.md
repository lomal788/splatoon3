# 그래픽 r11 차등 — 재질·베이크 (사격장 Lby_Lobby00)

2026-10-04. 방법은 `analysis/gfx_r11/DIFF_BRIEF.md`를 따랐습니다. 원본 셰이더와 web 셰이더를 같은 입력으로 수치 실행해 비교했고, 헤드리스 화면 캡처는 하지 않았습니다. 코드 변경은 없습니다(테스트·fixture만 추가). 확정 수준 표기는 [README](../README.md)를 따릅니다.

## 1. 결론

| 항목 | 결론 | 수준 |
|---|---|---|
| 맵 재질 셰이더 | 원본 Hoian_UBER 946/917/1714/1689와 web `forward.ts`(+three 표면)가 같은 입력에서 같은 색을 냅니다. 사격장 표본 8개의 상대차는 ≤2e-7입니다 | [실행] |
| 베이크 | 디코드(BC5·BC6H), `rgb·a·32`(a=1), 라이트맵 UV(`_u1·st.xy+st.zw`), 알베도와의 곱 순서가 원본과 같습니다 | [실행]+[데이터] |
| 텍스처 | 알베도·Rgh·Nrm의 KTX2 결과가 원본 BC 디코드와 같습니다. 차이는 ETC1S 손실 수준입니다 | [데이터] |
| 잉크 분기 | 식은 같습니다. **환경 반사 층만 다릅니다.** 원본은 cube array 층 12를 고정으로 쓰고, web은 거칠기로 고른 층 0을 씁니다. 층 12 생산자의 로비 분기가 미확정이라 고치지 않았습니다 | [판독]+[실행], 생산자 [미확정] |
| 벽 베이지 | 재질·베이크 쪽 원인이 아닙니다. 원본 화면을 역산하면 환경 SH가 web보다 노랗고, 바닥의 환경 반사는 web이 3~4배 밝고 파랗습니다. 캡처 큐브(광원 담당) 문제로 넘겼습니다 | [추정: 후처리 역산] |

## 2. 원본 ↔ web 짝 목록

| # | 원본 | web | 비교 | 결과 |
|---|---|---|---|---|
| 1 | Hoian_UBER p946 (Wall02, mLobbyFloorRubber) 보완 재역번역 `analysis/gfx_r11/diff/prog/p946.frag` | `forward.ts` applyForward가 만든 GLSL + three 표면 | glsl_eval 실행, 표본 4개(벽 2·바닥 2, 동적 스폿 1 포함) | 일치 |
| 2 | p917 (TrussYellow) | 같음 | 표본 2개(아래면·윗면) | 일치 |
| 3 | p1714 (mLobbyWoodBox, 금속 맵) | 같음 + `.mr` B 채널 metalness | 표본 1개 | 일치 |
| 4 | p1689 (mLobbyMetalPanelBlack) | 같음 | 표본 1개 | 일치 |
| 5 | p946 잉크 분기(temp_50) | `ink_surface.ts` hReadInk + FORWARD_SURFACE_END 치환 | 표본 3개, 환경 층 무관 입력 | 식 일치, 층만 다름(12 vs 0) |
| 6 | 베이크 AO/그림자 BC5 (comp R,G,0,1) | `bake.ts` RGBA16F, `[36]/[37]` 식 | 실제 지점 텍셀 | 일치 |
| 7 | 베이크 빛 BC6H_UFLOAT (comp R,G,B,1) | RGBA16F `hBL.rgb*hBL.a*32` | bcdec vs texture2ddecoder 독립 디코드, web 에셋 비트 | 일치(평균차 0.001) |
| 8 | 원본 bfres `_u1` | visual.glb TEXCOORD_1 (meshopt·양자화 해제) | 범위·지점 | 일치, 뒤집힘 없음 |
| 9 | bkdat MaterialElements | `BakeBindings.resolve` 조건 | Fld_VSLobby 47재질×2 | 전부 해석 |
| 10 | 알베도 BC1_SRGB / Rgh BC4 / Nrm BC5 | glb KTX2 (ETC1S/UASTC, node basis 트랜스코드) | 평균값·픽셀차 | 일치(ETC1S 오차) |

같은 입력: 원본 BC 디코드 텍셀, 실제 사격장 지점의 베이크 텍셀(아래 표), 주광 (6.706,8.51,10)·방향 (0.0431,−0.5664,−0.8230), 카메라 (11.0,3.69,−2.67), web 캡처 SH(`probe/env1.json`), 안개 값. 그림자 프리패스는 1, 투영 그림자는 0으로 두었습니다(그림자 담당 범위). 환경 BRDF LUT와 prefilter 내용은 두 쪽에 같은 해석 함수를 넣었습니다. LUT·prefilter 내용 자체의 동등성은 광원 담당 범위입니다. BRDF는 원본 `(NoV, −r)` repeat 좌표와 web `r` 행 저장 정책이 같은 값을 가리킨다고 두었습니다.

## 3. 실제 사격장 지점의 베이크 표본

`analysis/gfx_r11/diff/bake_at.mjs`(glb 삼각형에서 최근접점의 uv1) → `bake_sample.py`(bindings의 st로 아틀라스 이중선형).

| 재질 | 지점 | AO | G(그림자) | 빛×32 | R/B |
|---|---|---|---|---|---|
| Wall02 먼 벽 | (25,3,43) | 0.668 | 0 | (0.058,0.058,0.029) | 1.99 |
| Wall02 먼 벽 | (20,6,43) | 0.721 | 0 | (0.074,0.074,0.049) | 1.52 |
| Wall02 왼쪽 벽 | (42.4,3,30) | 0.721 | 0 | (0.015,0.015,0.013) | 1.20 |
| 바닥 | (24,0,12) | 0.909 | 0 | (0.714,0.588,0.419) | 1.70 |
| 바닥 | (30,0,30) | 0.898 | 0 | (0.127,0.120,0.102) | 1.25 |
| mLobbyWoodBox | (16.4,2,29) | 0.656 | 0.091 | (0.127,0.119,0.073) | 1.73 |

사격장 바닥·벽의 G는 0입니다. 그래서 occBake는 0.527로 일정하고 주광은 47%만 남습니다. 트러스·고보 그림자 무늬는 베이크가 아니라 정적 깊이 그림자에서 옵니다([그림자 담당](graphics_r11_diff_그림자.md)).

## 4. 벽 베이지 원인 분석

후처리는 원본과 같다고 확인되었습니다(SHARED `[r11 gfx-diff 후처리]`). 그래서 web `post_math`의 노출 2·Tone4·8³ LUT·pow(1/2.2)를 역으로 풀어 원본 화면 영역의 HDR 값을 추정했습니다(`analysis/gfx_r11/diff/invert_post.mts`).

| 영역 | 원본 HDR | web HDR |
|---|---|---|
| 먼 벽 | (0.054,0.054,0.026) | (0.046,0.051,0.045) |
| 왼쪽 벽 | (0.048,0.048,0.041) | (0.049,0.053,0.046) |
| 바닥 밝은 곳 | (0.158,0.176,0.187) | (0.208,0.240,0.291) |
| 바닥 그림자 | (0.068,0.075,0.078) | (0.122,0.139,0.165) |

- 원본 먼 벽의 색조(R=G≈2B)는 이 벽 베이크 빛의 색조와 같습니다. 먼 벽은 −z를 향해 주광을 받지 않으므로 색은 `알베도×(1−F0)×(bake+SH)×(1−occAO)`가 거의 전부입니다.
- 이 식을 역산하면 원본 SH(−z) ≈ (0.25,0.25,0.11)입니다. web 캡처 SH(−z)는 (0.19,0.22,0.20)입니다. 같은 식에 web SH를 넣으면 web 화면 값 (0.044,0.050,0.041)이 재현됩니다.
- 바닥은 알베도가 선형 0.011이라 환경 반사가 대부분입니다. web 환경 반사는 ≈(0.18,0.21,0.26)입니다. 원본 그림자 영역(직접광 0)에서 역산한 환경 반사 상한은 ≈(0.05,0.057,0.059)입니다.
- 따라서 남은 차이는 캡처 큐브(prefilter·SH)의 입력입니다. 재질 셰이더나 베이크 쪽이 아닙니다. 광원 담당의 "맵 재질 cube 변형" 조사로 넘겼습니다.
- 이 역산은 원본 스크린샷이 같은 버전·같은 후처리라는 가정에 기댑니다. 원본 사진의 바닥 배치가 web과 일부 다릅니다(오른쪽 경사대, 노란 레인 선). 그래서 수치는 [추정]입니다.

## 5. 잉크 환경 반사 층 12

원본 잉크 분기는 `texture(cPrefilEnvMapArray, vec4(R, 12), 0.0)`입니다. 층 12의 생산자는 0x7101036d84입니다(`analysis/decomp/port_common_r6/draw_native.c`).

```text
0x710102d3xx (c1_envmap): FUN_710103921c(..., param_5 = (+1000 == cube+0x5c8^1), param_6 = plVar13 /*param_3+0x4bd0 표의 Illuminate 객체, IsA 0x7105814c50*/)
0x710103921c → 0x7101036a18(..., param_6&1, param_7=plVar13) → 층 0..11 → 0x7101036d84(..., bit0, plVar13)
0x7101036d84:
  bit0==0                : 층12 ← *(*0x7105999230 + 0x30) = BlackCube
  bit0==1 && plVar13==0  : 층12 ← (cube+0x370 bit0 ? Zero2D(+0x58) : cube+0x378)
  plVar13 != 0           : "illuminate" 텍스처를 GGX prefilter 함수(0x71010351e8/35c4c/35fa0)로 그림.
                           roughness override = *(0x7105818e38)+0xb98 = BlitzUBO0[18].x(잉크 .05) → 층12
```

agl 기본 텍스처 표는 0x7103610520이 만들고, 이름은 0x7105723f20에 있습니다(+8+i·8: i=5 BlackCube, i=7 White2D, i=10 Zero2D). 로비에서 plVar13이 있는지 확정되지 않았습니다. 그래서 web의 층 0 사용은 [미확정] 차이로 남깁니다. 생산자가 확정되면 `ink_surface.ts`가 층 12를 소비하도록 고칩니다.

## 6. 그 밖의 관찰(범위 경계)

- `Gobo1__SadowMtl00`은 `gsys_static_depth_shadow_only 1`입니다. 원본은 색 패스에 그리지 않습니다. web `map.ts`는 그리지만, 로비 캡처점에서 레이 400개 중 5%만 닿고 모두 뒷면이라 컬링됩니다. 그래서 화면 영향은 작습니다. 정적 깊이 그림자를 구현할 때 "색 패스 제외·정적 캐스터 포함"으로 처리해야 합니다(그림자 담당과 조율).
- `Fld_VSLobbyScreen` 사이니지 세 셰이프(Long/Fes/Matching)는 같은 자리에 있습니다. 뼈 기본 가시성은 Long·Matching이 켜져 있고, FVIS `Commercial` base는 [T,F,F]입니다. 로비가 어떤 가시성 애니를 쓰는지 [미확정]이라 손대지 않았습니다.
- 실 GPU(d3d11) 헤드리스에서 캐릭터 M_Body/M_Face/M_TeamColor가 MAX_TEXTURE_IMAGE_UNITS(16)를 넘어 링크에 실패했습니다(swiftshader는 32라 통과). 캐릭터 재질은 이번에 차등 실행하지 않았습니다. gfx-char 확인 대상으로 남깁니다.
- 원본 `clamp(viewZ + BlitzUBO0[36].z, 0, 1)`(동적·정적 그림자 거리 인자)의 [36].z writer는 미확정입니다. web은 1로 둡니다(그림자 담당 범위).

## 7. 검증

| 실행 | 결과 |
|---|---|
| `tests/r11_gfx_diff_material.test.mjs` | 3건 통과: ① 4프로그램×8표본 원본=web ② 베이크 빛 차분 일치·색조 보존 ③ 잉크 분기 3표본 일치, 원본 층 12/web 층 0 기록 |
| `npm run typecheck` / `npm test` | 통과 / 429/429 |
| `analysis/gfx_r11/diff/mat_diff.py` | python f32 실행기(`glsl2py.py`)로 같은 결과(상대차 ≤2e-7) |
| `cmp_tex.py`, `bc6_check.py`, `ktx_decode.cjs` | 텍스처·베이크 디코드 짝 일치 |

재역번역 명령: `web/tools/shader_ryujinx/dotnet/dotnet.exe analysis/reference_graphics_r3/surface/dump/bin/Release/net10.0/dump.dll prog-bfsha extracted/shader/Hoian_UBER.Product.bfsha hoian_uber - analysis/gfx_r11/diff/prog/p<N> --index <N>`.

## 8. 남은 미확정

| 항목 | 이유·다음 근거 |
|---|---|
| 잉크 층 12 내용 | 0x7101036d84 분기 입력(plVar13, bit0)의 로비 값. 광원 담당 큐브 조사와 함께 |
| 환경 SH·prefilter 색·밝기 | 캡처 큐브 입력(맵 재질 cube 변형)과 Illuminate. 광원 담당 |
| 사이니지 가시성 애니 | DObj_VSLobbyScreen 액터의 FVIS 선택 로직 미판독 |
| 캐릭터 재질 차등 실행 | 이번 회차에 하지 않음. d3d11 텍스처 유닛 16 초과 링크 실패 별도 |

## 9. 사격장 표적(SighterTarget) 색 — 2026-10-04 추가

### 9.1 결론

| 항목 | 결론 | 수준 |
|---|---|---|
| 갈라진 첫 지점 | web `client/range/index.ts`가 parts glb를 GLTFLoader 기본 `MeshStandardMaterial`로 그렸습니다. Hoian 재질 경로를 타지 않아 팀색 혼합이 없었고, `M_Body_Alb`(평균 sRGB 0.34, 어두운 회색)만 보였습니다 | [실행] |
| 원본 식 | 표적 M_Body = Hoian_UBER **3443**(옵션 불일치 0, 후보 2). 비도색 분기 `alb' = mix(Alb, Mat.my_team_color, clamp(Subst(_su0 Tcl).x + team_color_blend_alpha))`, 거칠기 `max(_r0.x,1e-4)`, 금속 `_m0.x`, 발광 `Emm·emission_color`(intensity 0) | [판독] |
| 팀 | 액터 팀 = 로컬 플레이어의 상대 팀(0x71021ef388, 문서 range §5.1). 팀 세트 = 로비 VersusRegular 행(부팅 1회) | [판독] |
| 데이터 누락 | `M_Body_Tcl`(BC1_SRGB 512², 평균 0.894, 92%가 >0.5 → 몸 대부분이 팀색)과 `M_Body_2cl`이 parts glb에 없었습니다(PBR 슬롯 밖이라 gltfpack이 버림) | [데이터] |
| 색 공간 | 표적 `M_Body_Rgh`·`_Emm`·`_Tcl`은 **BC1_SRGB**입니다(맵·캐릭터는 BC4). `.mr` 합본 G에는 sRGB 부호화 값(평균 0.47)이 들어 있고, 원본 셰이더는 HW sRGB 디코드 값(평균 0.19)을 받습니다. 전체 텍스처 메타 98장 중 sRGB Rgh는 이 하나뿐입니다 | [데이터] |
| 재질 애니 | `Damage`(100f)는 `two_color_complement_paint_intensity`만 움직입니다. 실행 중에는 LossOfColor가 1−hp/max를 같은 파라미터에 씁니다. 정지(hp=max) 상태는 0이라 회색의 원인이 아닙니다 | [데이터]+[판독] |

### 9.2 고친 것

- `web/tools/asset_r11_target_tex.py`(신규): 원본 bfres 내장 BNTX에서 `M_Body_Tcl`을 sRGB KTX2로 `maps/Lby_Lobby00/tex/Obj_SighterTarget/`에 넣고, 원본 텍스처 형식 표 `native_formats.json`을 씁니다. catalog bytes 79,389,098 → 79,415,954입니다.
- `client/render/part_material.ts`(신규): 파츠 재질에 applyHoian(팀 세트 = 액터 팀) → applyForward(맵 LightingState) → `_r0`가 `*_SRGB`면 `.mr` G를 정확한 sRGB EOTF로 해석 → shareMaterialSamplers 순서로 적용합니다. 텍스처 해석은 소유 폴더 우선, colorSpace는 KTX2/glTF 선언 그대로입니다(nativeLinear 이름 규칙은 BC4 전제라 쓰지 않음).
- `client/range/index.ts`: 맵 env가 로드되면 표적 팀(`range.targets[0].team`)으로 파츠 재질을 한 번 만들고, 이미 붙은 표적 몸을 다시 복제합니다.

### 9.3 검증

- 테스트 `r11_gfx_diff_material.test.mjs`: ④ 원본 3443을 계측(재질 값 출력만 추가)해 표본 3개에서 web 경로의 알베도(팀색 혼합)·거칠기(sRGB)·금속이 일치(<1e-6). ⑤ SighterTarget/Move 파츠 재질 16 텍스처 유닛 이내, sRGB 거칠기 훅이 `texelRoughness` 선언 뒤.
- typecheck 통과, `npm test` 464/464.
- 브라우저 probe: range 재질 4개 모두 nativeForward, M_Body 2개 sRGB 거칠기, 공유 샘플러 `.mr` 1개.
- 최종 캡처 1회 `analysis/gfx_r11/ref/target_after.png`: 표적 영역 (82,81,92) → (129,67,66). 색이 팀색을 따릅니다. 이번 세션의 무작위 행에서는 상대 팀색이 붉은 계열이었습니다. 원본 사진은 TurquoisePink 행의 Alpha 청록(0.09,0.83,0.74)과 맞습니다(잉크 분홍 = 플레이어 Bravo, 표적 = Alpha). 웹은 플레이어 팀을 URL로 바꿀 수 없어 같은 행·같은 팀으로 찍지 못했습니다. `?teamSeed`로는 행만 고정됩니다.

### 9.4 남은 것

| 항목 | 이유 |
|---|---|
| 보완 칠(LossOfColor·Damage) 2cl 분기 | 3443 `temp_52` 분기(2cl 마스크·마지막 공격 팀 채널·잉크 rim·거칠기 [18].w·`comp_paint_norm_intens`)는 미구현입니다. core RangeTargetView에 마지막 공격 팀이 없고 `M_Body_2cl`(BC4)도 아직 번들에 없습니다 |
| 투과·엣지광 | 3443은 enable_taransmission/edge_transmission/edge_light입니다. character_material 프로파일(painted=thickness 필요)에 맞지 않아 소비하지 않습니다 |
| Fragment 재질 | 4691 선택 시 normal_map·comp_paint_type 옵션 불일치 2~3건이 있어 원본 프로그램을 확정하지 못했습니다 |
