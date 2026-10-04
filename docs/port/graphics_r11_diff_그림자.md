# r11 그래픽 차등 — 그림자 (2026-10-04)

사격장(Lby_Lobby00) 바닥에 원본처럼 천장 노란 트러스·구조물의 진한 그림자가 생기지 않던 원인을 원본·web 차등으로 찾고 고쳤다. 방법은 [DIFF_BRIEF](../../../analysis/gfx_r11/DIFF_BRIEF.md)를 따랐다. 헤드리스 화면 캡처는 하지 않았다.

## 1. 결론

**갈라진 지점 = 정적 깊이 그림자 경로 전체가 web에 없었다.** 트러스 그림자는 동적 캐스케이드(2단·1024²)가 아니라 **정적 깊이 그림자(2048² VSM)** 에서 나온다. 원본 TrussYellow의 renderInfo는 `gsys_static_depth_shadow=1`, `gsys_dynamic_depth_shadow=0`이다. 반면 web은 다음 상태였다.

- 맵 메시가 어느 그림자에도 캐스터로 등록되지 않았다.
- visual.glb renderInfo에서 `gsys_*depth_shadow` 키가 빠져 있었다(asset_model.RI_KEEP).
- `hShadowPrePass`의 정적 슬롯이 상수 1이었다.

이 경로를 원본 식대로 구현해 SPP 정적 슬롯에 연결했다. 그 과정에서 Hoian의 `clamp(viewZ+BlitzUBO0[36].z)` 인자도 원본 값으로 연결했다. 두 값은 ShadowPrePass `is_farDepthTestDist`와 Default 60이다.

## 2. 먼저 확인한 네 가지

| 질문 | 원본 | web(수정 전) | web(수정 후) |
|---|---|---|---|
| 트러스가 캐스터인가 | 정적 캐스터다(동적 아님). Fld_VSLobby 50재질 중 48이 정적 캐스터이고, 제외되는 것은 LobbySign02·Water00이다. `SadowMtl00`(Gobo1)은 static_only다. FldBG_LobbyDV 8재질은 0이다. 동적 캐스터는 SignageMatching00 하나뿐이다 [데이터: romfs bfres renderInfo] | 캐스터 아님 | 13모델 86재질 표를 공급했다. 정적 캐스터 메시는 68개이고 158메시 전부 해석된다 |
| web에서 캐스터로 들어가나 | 0x710374f950이 +0x10 bit4 모델의 셰이프 구를 수집한다 | castShadow·정적 패스 없음 | `applyNativeDepthShadowFlags`로 등록한다. static_only는 색 패스에서 제외하고 캐스터로만 쓴다 |
| 캐스케이드/범위가 트러스를 덮나 | 정적 맵 한 장으로 정적 캐스터 구 합 AABB 전체를 맞춘다 | 정적 맵 없음 | 원본 맞춤 함수 그대로(비트 일치) |
| 농도 식이 같나 | SPP.x=동적, SPP.y=정적(뷰 swizzle 3,5,4,2). Hoian은 `max(1−x,1−y)·clamp(viewZ+[36].z)`로 계산하고, 여기에 베이크·AO·투영을 더한다 | 동적 쪽 식은 같고 정적 채널=1, [36].z 인자 없음 | 정적 채널과 [36].z=60을 연결했다. 합성 순서는 그대로다(재질 담당 실행 대조로 일치 확인) |

## 3. 짝 목록과 비교 결과

| # | 원본 | web | 비교 방법 | 결과 |
|---|---|---|---|---|
| 1 | 정적 맞춤 0x7103754fe8 + sead LookAtCamera 0x710358857c + OrthoProjection 0x7103589f84 | `nativeStaticShadowFit` | unicorn 원본 실행 49건(로비 광원 방향 포함) vs node | view/proj/ortho/tex **f32 비트 일치** 49/49 (`web/tools/r11_gfx_static_shadow_emu.py`, fixture `r11_static_shadow_fit_native.json`) |
| 2 | NVN 텍스처 행렬(−0.5·P1+0.5·P3) | `webStaticShadowMatrix` | v_gl = 1−v_nvn, AABB 안 표본 | 같은 텍셀(오차 ≤1e-5), three Ortho 행렬과 일치 |
| 3 | 정적 AABB 0x710374f950(구 중심±반경 f32) | `nativeStaticShadowBounds` | 판독식 | 일치 |
| 4 | 정적 페이드 3764908 frame+1424/+1428 | `nativeStaticShadowFarFade` | r6 unicorn 877건 output[6],[7] | **비트 일치** 877/877 |
| 5 | prepass v216 SPP.w(Chebyshev, FFMA 2개, 분산 하한 없음) | `nativeStaticShadowVisibility` / GLSL `hStaticShadowVisibility` | v216 식 직역 vs CPU 4000표본, GLSL 분기형 | CPU 비트 일치. GLSL형은 ≤1e-5 차이(d==m1·분산0의 0/0은 FMNMX 규칙상 1) |
| 6 | static_depth_shadow 프로그램(d, d², 0, 1) | 복사 셰이더 | 원본 역번역 대조 | 같은 식 |
| 7 | vsm PASS1/PASS2(7탭 ±1.3846/3.2308/5.0769, 924/1287/286/13 ×0.000245700008) | 블러 셰이더 | 원본 역번역 상수 대조 | 같은 탭·가중치 |
| 8 | 블러 반복 obj+0xb98 | `blurIterations:3` | 생성자 0x710375418c 판독(x19=x0+0x98, `stur x9,[x19+0xafc]`: +0xb94=1.0f, **+0xb98=3**), 전 텍스트 #0xb98·#0x1380 store 스캔에서 다른 writer 없음 | 3 [판독] |
| 9 | Hoian `clamp(in_attr3.w+[36].z)`, in_attr3.w=Context[2]·P(=−깊이) | `hDynamicShadow` 안 `clamp(hShadowFarDepthTest−depth)` | p946 역번역 문자열·[36].z writer 0x7101110750 | [36].z = env+0x1338(ShadowPrePass, +0x468 is_enable·+0x488 resolutionMode 읽는 0x71036ca5a4로 확인)+0x7c8 = `is_farDepthTestDist`(ctor 1000, Default **60**) |
| 10 | 캐스터 renderInfo | data/depth_shadow.json | romfs 8 bfres dump | 표 그대로 |
| 11 | 동적 2단·1024²·바이어스 .3/5·PCF .5·커널·strict 20·fade 40..60·투영 Density0 | 기존 shadows.ts | r6 실행 fixture 재사용(재실행 안 함) | 일치(기존 테스트 유지) |
| 12 | 광원 방향 = DirectionalLight +0x208[view] = Direction 월드 정규화 | env.direction 정규화 | 광원 담당 0x71035d6500 판독 재사용 | 같음 |

결과: 비교한 짝 12개 중 일치 12개다. 수정 전 갈라진 짝은 1·3~10(정적 경로 없음)과 9([36].z 없음)였고, 모두 고친 뒤 일치시켰다.

## 4. 고친 것

- `client/render/shadows.ts`
  - 원본 대조 헬퍼: `NATIVE_STATIC_SHADOW_SETTINGS`(gsys `static_sdw_width` 2048, mip 1, Depth_32, R32_G32_float — CRC로 이름 복원), `NATIVE_VSM_BLUR`, `nativeStaticShadowBounds/Fit/FarFade/Visibility`, `webStaticShadowMatrix`.
  - `NativeStaticShadow` 클래스: 원본 맞춤 행렬을 광원 카메라에 그대로 넣고 D32F 깊이를 그린다. 이어서 (d,d²) RG32F 복사, vsm 블러 3×2 핑퐁을 거친다. 정적 맵은 한 번만 그린다(`is_useUpdatableStaticDepthShadow` false).
  - `applyNativeDepthShadowFlags`: 모델+재질로 정적·static_only·동적 플래그를 단다.
  - GLSL `hStaticShadowVisibility`를 추가했다. `hShadowPrePass`는 (동적, 정적)을 반환하고, `hDynamicShadow`에는 farDepthTest 인자가 들어간다. `NATIVE_SHADOW_PREPASS_*`에 static fade·farDepthTestDist를 추가했다.
- `client/render/map.ts`(최소 수정): data/depth_shadow.json으로 플래그를 단다. 병합 때 정적 플래그, 셰이프 구(월드), castShadow를 넘긴다.
- forward.ts는 수정하지 않았다(`hDynamicShadow` 계약 유지).
- 에셋: `assets/maps/Lby_Lobby00/data/depth_shadow.json`(`web/tools/asset_r11_static_shadow.py`, catalog 갱신). 이후 재빌드를 위해 `asset_model.RI_KEEP`에 `gsys_static/dynamic_depth_shadow.*`를 추가했다.
- 테스트: `tests/graphics_r11_diff_shadow.test.mjs` 11건.

## 5. 남은 미확정

- **vsm `cInvTexSize` 공급값**: PASS1과 PASS2 바이너리는 같다. 그리기 헬퍼 0x71035f73d8은 (w,h,1/w,1/h) 16바이트를 프로그램 위치표[1]에 올린다. web은 역번역 식대로 (1/2048, 1/2048) 대각 탭을 두 패스 모두에 쓴다. 가로/세로 분리 여부는 [미확정]이다.
- 블러 프로그램 식별: 0x7103754a88의 목록 +0x60[14]/[12]을 shdw `vsm`으로 보았는데, 아카이브 목록 기준 오프셋은 [추정]이다. 함께 쓰인 +0x28[1]은 static_depth_shadow binary 1과 맞는다.
- 정적 맵·블러 sampler 필터: web은 `OES_texture_float_linear`가 있으면 선형, 없으면 nearest를 쓴다. 원본 sampler 콜백 0x7103756c0c/c50의 필터 필드 1/2 의미는 [미확정]이다.
- 정적 깊이 패스의 polygon offset·cull: 원본 렌더 상태를 모른다. web은 offset 없이 재질 면 설정을 따른다.
- 셰이프 구: 원본은 셰이프별 구(bfres radius)를 쓴다. web은 병합 전 월드 지오메트리의 three 구(박스 중심·최대 거리)를 쓴다. 맵 해상도에만 영향이 있다.
- 동적 캐스터 SignageMatching00: renderInfo대로 등록했다. 사이니지 3종 가시성은 재질 담당 [미확정]이다.
- 텍스처 유닛: 맵·캐릭터 forward 셰이더에 sampler가 1개(`hStaticShadowMap`) 늘었다. 16 한도 근처인 캐릭터 셰이더는 확인이 필요하다(gfx-char).
- 투영 그림자 프레임·native compare sampler·live 리소스 선택은 r6 상태 그대로다.

## 6. 도구·근거

- `web/tools/r11_gfx_static_shadow_emu.py`(unicorn), `web/tools/asset_r11_static_shadow.py`(캐스터 표)
- `analysis/gfx_r11/probe/shadow/`: scan_b98.py(store 스캔), scan_1338.py(env+0x1338 소비자), disasm_at.py, vsm/(vsm 6변형 역번역), sharc/(agl 아카이브 목록)
- 판독: analysis/decomp/r11_gfx_ref/static_shadow_*.c, analysis/port_common_r6/shadow/prepass/v216.pixel.glsl, analysis/gfx_r11/ref/sds/v0.pixel.glsl, analysis/gfx4/programs/Fld_VSLobby__LobbyFloorConcrete.frag
- 검증: `npm run typecheck` 통과, `npm test` 446/446

## 7. 화면 미반영 원인 추적 (2026-10-04, 실 GPU 런타임 판독)

조정자의 최종 화면(final_after)에서 트러스 그림자가 보이지 않았다(바닥 대비 1.24). `ref/shoot.mjs`(d3d11)로 같은 시점을 열고 렌더 타깃을 readPixels로 수치 확인했다(`analysis/gfx_r11/probe/shadow/rt/probe*.js`).

| 점검 | 결과 |
|---|---|
| 정적 패스 실행 | captures 1, casters 65, blurPasses 6, 선형 필터, available 1 |
| 맞춤 범위 | ortho ±172×±233×±230. 바닥·트러스 모두 맵 안에 있다 |
| 맵 값·바인딩·SPP.y | 맵 텍셀 30%가 1 미만이다. 바닥 표본은 d≈0.45, m1≈0.27로 판정 0이 나온다. uniform·텍스처·페이드·farDepthTest 60 모두 정상이다 |
| 바닥을 가리는 캐스터 | 바닥 표본 4개 모두 광원 방향으로 95단위 위, 즉 **Gobo1__SadowMtl00**(static_only)에서 막힌다 |

**원인**: Gobo1은 x −84..96, y −116..82, z −88..87의 외향 법선 상자다. 열린 곳은 윗변 z 72..87 / 앞벽 상단 y 62..82 띠뿐이다(102삼각형, probe7 판독). 로비 주광(lat 34.5, lon −3)에서는 이 띠로 들어온 빛이 바닥 z −47.6..−2.7, 즉 카메라 뒤쪽에만 닿는다. 그래서 보이는 바닥 전체가 정적 그림자가 됐다. 런타임 연결은 정상이었고, 데이터대로 그린 결과가 원본 화면과 달랐던 것이다.

**원본과 대조한 근거** [추정, 코드 근거 미확보]
- 베이크 G(0_bktex0)를 바닥 월드 위치로 펼치면(probe17), 빛 받는 칸은 z −35..−6의 띠뿐이다. 베이크는 같은 고보와 로비 태양 방향으로 구워졌다는 뜻이다(이 고보는 bake_cast_shadow).
- 원본 화면의 바닥 밝은 곳 휘도 0.367은 정적 그림자가 없던 web(0.414)과 같은 수준이다. 직사광이 보이는 바닥에 닿는다는 뜻이다.
- 고보를 빼고 그린 정적 맵의 바닥 판정(probe18 L3)을 원본 사진에 겹치면, 트러스가 만든 둥근 덩어리 그림자 배치가 원본과 겹친다(ov_L3.png). 컬 반전·컬 없음·기본 env 방향(−0.3,−0.7,−0.6)·AABB에서만 제외 같은 다른 후보는 모두 원본 무늬를 만들지 못했다(hyp*.png, ov_BC.png).
- 결론: 원본 런타임 정적 맵에는 static_only 고보가 들어가지 않는 것으로 보고 `applyNativeDepthShadowFlags`에서 static_only를 정적 캐스터에서 뺐다. 색 패스에서도 계속 숨긴다. 원본 코드에서 이렇게 고르는 지점(셰이프 패스 선택)은 [미확정]이다.

**재측정**(final_after_shadow.png, 1회): 바닥 밝은 곳/그림자 대비가 1.24에서 **1.65**로 올랐다(원본 2.7, 수정 전 1.64). 트러스 그림자 무늬가 바닥·경사대에 나타난다. 남은 차이는 다음과 같다.
- 그림자 농도: 그림자 영역 휘도 0.243(원본 0.136).
- 대각 번짐: vsm `cInvTexSize`를 (1/2048, 1/2048) 대각으로 두 패스 모두 쓴 결과, 무늬가 한 대각 방향으로 늘어진다. 원본 블러 방향·공급(0x71035f73d8의 (w,h,1/w,1/h) 업로드, 렌더 상태 콜백 0x7103756c0c/c50의 +0x1c 하위 비트 1/2)은 [미확정]이다. 원본 무늬는 등방에 가깝다.

테스트: typecheck 통과, npm test 464/464.

## 8. 중단 (2026-10-04, 조정자 지시)

현재 코드는 typecheck 통과, npm test 464/464 상태다. 다음에 볼 곳은 세 가지다.
1. static_only 셰이프를 정적 패스에서 빼는 원본 코드 지점: 재질 플래그 bit3(0x71036bb5a4가 +0x10에 기록)의 소비자, 그리고 view 9 셰이프 제출 경로.
2. vsm 블러 방향: 0x71035f73d8의 (w,h,1/w,1/h) 업로드가 어느 uniform 위치로 가는지, 렌더 상태 콜백 0x7103756c0c/c50의 +0x1c 하위 비트(1/2)가 패스별 방향·쓰기 마스크 중 무엇인지.
3. 그림자 농도 차이(그림자 휘도 0.243 vs 원본 0.136): 블러가 정해진 뒤 VSM 빛 번짐 정도를 다시 대조한다.
