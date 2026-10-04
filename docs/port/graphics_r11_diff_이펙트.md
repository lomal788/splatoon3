# r11 그래픽 차등 — 이펙트 (2026-10-04)

사격장 이펙트(발사·탄·착탄·조준 표시)를 원본 실행/역번역 셰이더와 web 코드에 **같은 입력**을 넣어 비교하고, 갈라진 지점을 원본대로 고쳤다. 헤드리스 화면 캡처는 하지 않았다(셰이더 46종 WebGL 컴파일 오류 검사만 화면 없이 실행).

## 1. 방법과 도구

| 구분 | 원본 쪽 | web 쪽 | 비교 도구 |
|---|---|---|---|
| GPU 셰이더 | Negate 보완 역번역 `analysis/gfx_r11/fx_fixed/p{1940,1897,1886,1885,1747,1202,1383,1385}.{vert,frag}` (기존 `analysis/vfx/shader/`와 binding 번호만 다름). 사본 `tests/fixtures/r11_fx_glsl/` | `client/fx/particle_shaders.ts` VERT/FRAG | `tests/glsl_eval.mjs`(GLSL→JS 해석기, 원본·web 공용), `tests/r11_fx_shader_harness.mjs` |
| 정적 UBO | `sysEmitterStaticUniformBlock.data[i]` = ResEmitter + 16·i(FIXED 패치 후). `web/tools/r11_gfx_fx_res.py` → `fixtures/r11_fx_res.json`(46 이미터) | 실제 로더 `emitterDefinition(emitters.json)` → `ParticleBatch.uniforms` | 같은 하네스 |
| CPU | unicorn: `r11_gfx_fx_tables.py`(0x7100827d04), `r11_gfx_fx_shape_emu.py`(형상 함수 6종), `r11_gfx_fx_cpu_emu.py`(0x710080e4cc, 0x710081e3e4), `r11_gfx_fx_emit_emu.py`(0x710081b784), `r11_gfx_fx_splash_emu.py`(0x71027b877c) | `shapes.ts`, `particles.ts`(EmitterInstance/spawn/step), `splash.ts` | `tests/r11_gfx_fx_diff.test.mjs` |
| 렌더 상태 | r8 원본 CPU 실행 NVN setter 인자(`analysis/completion/r8/vfx_state_emu.json` 실제 11 이미터) → `fixtures/r11_fx_render_capture.json` | `render_state.ts` | 같은 테스트 |

입력 표본: 실제 Lby 이미터 46개 값(번들 39 + 조준 7), 무작위 이미터 행렬·나이·난수·크기·정점(17 이미터 × 12~24), uv에 따라 바뀌는 텍스처(같은 함수를 양쪽 샘플러에 공급), 실제 VAT 반정밀도 텍셀.

## 2. 짝 목록과 결과

| # | 원본 | web | 결과 |
|---|---|---|---|
| 1 | p1940 정점 (바닥 Splash) | VERT | 위치·C0/A0 일치, **uv 갈라짐**(텍스처 이동 애니 없음) → 고침 |
| 2 | p1897 정점 (Crown, soft) | VERT | 일치, uv 갈라짐 → 고침 |
| 3 | p1886 정점 (벽 Splash, XZ, ZXY) | VERT | **XZ 크기 축 순서·회전 순서** 갈라짐 → 고침 |
| 4 | p1885 정점 (벽 Ripple) | VERT | 회전 순서, **깊이 오프셋 없음**, 근거리 페이드 깊이식 → 고침 |
| 5 | p1747 정점 (머즐 SplashCorn, YZX) | VERT | **회전 순서** → 고침 |
| 6 | p1202 정점 (머즐 Flash) | VERT | **셰이더 애니 정점 변위 없음**(텍스처 A로 법선 방향 변위) → 고침 |
| 7 | p1383 정점 (탄 VAT) | VERT | VAT 위치·법선(A 반정밀 복원) 일치 |
| 8 | p1385 정점 (분열 탄 VAT) | VERT | 일치(근거리 페이드 → 고침 후) |
| 9~16 | 8개 프래그먼트 알파·discard | FRAG | 1383/1385 **알파 테스트 없음**인데 web 은 discard → 고침. 1885 페이드 → 고침. 그 외 일치 |
| 17 | 8개 프래그먼트 알베도(조명 전) | FRAG `base` | 7개 일치(1385 는 알베도 변수 미지정) |
| 18 | 형상 0/1/2/12/13/14 (0x710540fea8 표) | `shapes.ts`(신규) | web 은 점만 → 이식 후 600건 일치(상태 LCG·카운터·순번 포함) |
| 19 | 방향표 0x7100827d04 (DAT_71057d52f8) | `vfx_random_table.ts`(생성) | 512×3 비트 일치 |
| 20 | 이미터 로컬 SRT 0x710080e4cc | `EmitterInstance` | **emitterTrans·회전 난수 미적용** → 고침, 138건 일치 |
| 21 | 입자 생성 0x710081e3e4 첫 입자 | `ParticleBatch.spawn` | **allDirectionVel 항 없음·positionRandom 방향표 아님** → 고침, 184건 일치 |
| 22 | 방출 0x710081b784 프레임 루프 | `EmitterInstance.step` | 8계획 방출 프레임·개수 일치 |
| 23 | 착탄 0x71027b877c 벽 행렬 | `wallMatrix` | 855건 일치(f32 asin/acos 차 ≤1e-4) |
| 24 | 착탄 바닥 이동 행렬·θ·종류 (→0x71018b4f74) | `floorMatrix`/`hitTheta`/`splashKind` | 559건 일치 |
| 25 | 착탄 바닥 속도0 (0x71058237b0) | `identityFloor` | 86건 일치, 종류 = Floor(아래 §3.9) |
| 26 | 렌더 상태 0x710082804c NVN 인자 | `render_state.ts` | 11/11 일치 |
| 27 | 조준 표시 PlayerShotGuide | 없음(CSS 십자선) | **미구현** → 이미터셋 추가·예측·발생 구현 |

비교한 짝 27개: 처음부터 일치 11, 갈라짐 16(모두 원본대로 수정 후 일치, 27번은 신규 구현).

## 3. 갈라진 지점과 고친 것

1. **회전 순서** (p1747 YZX, p1886/1885 ZXY): 원본 M = Rx·Rz·Ry(YZX), Ry·Rx·Rz(ZXY). web 은 Ry·Rz·Rx / Rz·Rx·Ry. 두 축 이상 회전 난수가 있는 이미터(머즐 SplashCorn·Flash, 벽 Splash 등)가 다른 방향으로 그려졌다. `particle_shaders.ts`.
2. **POLYGON_XZ 크기**: 원본은 primitive 축에서 크기·피벗을 곱한 뒤 (x,z,−y) 교환. web 은 교환 뒤 곱해 y/z 크기가 뒤바뀜. 축 교환 자체는 원본과 같음(문서의 "교환 없음"은 정정).
3. **텍스처 이동 애니(_TEX_n_SHIFT_ANIM)**: 원본 정점이 샘플러별 uv 를 (uvScale/div·uv−.5)·(t·scaleAdd+r·scaleRand+scale+scaleRand) − (t·scrollAdd+scroll+scrollRand−2r·scrollRand) + .5 로 만든다(ResEmitter 0x490+0x50·slot). 슬롯별 난수: 0=(r.x,r.y), 1=(r.y,r.z)(flagsZ bit0=0), 2=(r.z,r.x | r.x,r.y)(모드2). web 은 원 uv. 프로그램별 켜진 슬롯은 `FX_UV_SHIFT_SLOTS`. 패턴 애니·회전 애니는 Lby 프로그램에서 꺼져 있음.
4. **근거리 페이드**: 원본은 정점 단계에서 **입자 중심의 시야 깊이**로 clamp((d−near.x)/(near.y−near.x))·dyn[3].x, ≤0 이면 정점 컬. 시작=끝(벽 Splash 4/4)이면 계단. 켜진 프로그램은 1202/1385/1747/1885/1886 뿐(1897·1383 은 근거리 페이드 없음). web 은 조각마다 카메라 거리, 모든 프로그램, 시작=끝이면 끔.
5. **깊이 오프셋(1885 Ripple)**: 시야 z 에 data[15].w(=0.1)를 더한 투영으로 gl_Position.z 만 바꾸고, 근거리 페이드 깊이는 d01' = d01 + off·(d01−1)/w. web 없음(벽과 z 싸움).
6. **1202 셰이더 애니 변위**: pos += key(t/life)·normalize(pos)·(2·T0(uv0).a−1). 키는 0x940 의 8행 전체를 STEP 합 Σk_i·s_i·(1−s_{i+1}) 로 읽어 마지막 실제 키 뒤에는 0(파일의 빈 행 시간 0). web 없음.
7. **rotateRegist 0**: 원본 R(t) = 0(pow(0,t) 를 1로 취급), web 은 1.
8. **알파 테스트**: 1383/1385 는 _ALPHA_COMPARE 없음 → discard 안 함. web 은 alphaThreshold 로 discard(분열 탄 일부가 사라짐).
9. **형상·방향표·allDirectionVel**: 형상 0 방향 = 표[E+0xBA++]·allDirectionVel(WpCmnHit/Splash .21, WpCmnHitInvalid/SplashCorn_Copy1 .26), positionRandom 도 같은 표·같은 카운터. 형상 2(분할 원: Watersplash 3분할, HitMarker juuji 4분할 X자)는 방출 수 × 분할 수(0x710081e070). 시드 E+0xB8 = seed, 카운터 = seed>>16, LCG = seed(0x7100828004), randomSeedType 2 = randomSeed·0xDFDC1C35.
10. **emitterTrans·회전 난수**: 0x710080e4cc 가 초기화 때 LCG 6번(회전 XYZ→이동 XYZ)으로 로컬 RT 를 만든다. web 은 회전만(Drip y .02, Watersplash y −.15 누락).
11. **조준 표시**: PlayerShotGuide `Shooter_Center_<종류>`/`Shooter_HitMarker_<종류>`(WpShtrSite / WpShtrSiteHit / WpShtrFieldHitMarker / WpShtrHitMarker). 종류 = 실제 탄 규칙으로 ShotGuideFrame(8) 단계 흉내 낸 첫 접촉(상대 팀 리시버 2, 지형·같은 팀 1, 없음 0). 종류가 바뀌거나 핸들이 끝나면 다시 발생, 아니면 위치만 갱신(0x710258683c/0x71025498d4). 가운데 = 예측 점, 회전 = 카메라 축 [근사]. `shot_guide.ts`, `index.ts`.

에셋: `web/tools/asset_fx_r11.py`(신규, 조준 이미터셋 7개·`circlering08_fia` 추가, 기존 행·파일 무변경), `asset_fx_port.py`(r11 필드 uvShiftAnim/staticFlags/depthOffset/paramKeys/numParamKeys/shaderAnimInterpolation/shapeRaw 를 모든 행에, 개수 검사 일반화), `asset_fx.py`(ESETS 에 조준 5개 추가). VAT bin 2개 비트 일치 유지, GLB 재생성 0. 변경 전 사본 `analysis/gfx_r11/fx_diff/`.

## 4. 테스트

`tests/r11_gfx_fx_diff.test.mjs` 10개: 정점 스윕(17 이미터), 프래그먼트 알파·알베도 스윕, 형상 600, 방향표, SRT 138·첫 입자 184, 방출 8계획, 렌더 상태 11, 착탄 1500, 에셋 r11 필드 46, 조준 표시(키 대응·예측 종류). `npm run typecheck`, `npm test` 462/462 통과. 셰이더 46종 WebGL(SwiftShader) 컴파일 오류 0(화면 캡처 없음).

## 5. 남은 미확정

- 원본 Custom1(VAT 시간률·알파 remap)·dynamic color(팀색 writer)·FX BRDF/env: 양쪽에 같은 값을 넣어 비교했을 뿐 실제 공급값은 [미확정](web `FX_WEB_DEFAULTS`).
- 정점이 쓰지 않는 varying(1383/1385 in_attr2.w, 1747 in_attr4.w)은 Maxwell 기본 (0,0,0,1) 로 가정(web linkedAlpha=1 과 같음) [미확정].
- 입자 단위 LCG 소비 순서(velRandom·크기·수명·sysRandomAttr): web 은 형상 외 난수를 Math.random 으로 뽑아 두 번째 입자부터 LCG 열이 원본과 달라짐(분포·식은 같음).
- 형상 3~11·15, 텍스처 패턴/회전 애니, 이미터 크기(AE0)의 위치 반영(Lby 전부 1).
- 방출 0x710081b784 의 초기 E+0x58/0x60 writer 미확인: 첫 시작 프레임 방출을 가정하고 정상 상태 간격을 비교.
- 조준 표시: 바이어스(좌우) 각도 공급원·0x710175779c 의 out 두 점 구성·회전 행렬 대상([this+0x108]+0x30)·리시버 무적 모드, 조준 프로그램 914/919/920/921/224/227/231/232 셰이더(웹 fallback). app.ts 의 CSS 십자선은 조정자 판단(이제 이펙트와 겹침).
- 1202 셰이더 애니 STEP 이 빈 키 행(시간 0)을 0으로 읽는 것은 파일값 그대로의 결과다. 런타임이 빈 행을 채우는지는 [미확정].
