# 그래픽 r11 — 사격장(Lby_Lobby00) 광원·색 공간 감사

2026-10-04. 대상은 `client/render/{post,post_math,bloom,lighting,sky,sh_projection,bake,shadows,map,dynamic_lights}.ts`입니다. 캐릭터 재질·애니메이션은 r11 gfx-char 담당이 같은 시기에 고쳤습니다(SHARED `[r11 gfx-char]`). 확정 수준 표기는 [README](../README.md)를 따릅니다.

## 1. 결론

| 항목 | 결론 | 수준 |
|---|---|---|
| 원인 1: 하늘 텍스처 | `Sky_Daytime00.mSky_Alb`는 원본 **BC6H_UFLOAT**(선형 HDR)입니다. 번들은 이 선형값을 8비트로 담은 뒤 KTX2 sRGB(emissive 슬롯)로 태그했습니다. 그래서 three가 sRGB→선형 변환을 한 번 더 했습니다. 하늘이 R 3.3배·G 3.2배·B 2.2배 어둡고 파랑으로 치우쳤습니다. 하늘은 환경 큐브 캡처(×80)·SH·환경맵의 입력입니다. **수정: `sky.ts`에서 NoColorSpace** | [데이터]+[웹 실행] |
| 원인 2: 발광 마스크 | `*_Emm`은 원본 **BC4_UNORM**(선형)입니다. 그런데 GLTFLoader가 emissive 슬롯을 sRGB로 강제했고, KTX2 태그도 sRGB였습니다. 그 결과 x^2.2로 어두워졌습니다(맵 13장, 예: Celling_Emm 0.29배). **수정: `map.ts`에서 gfx-char의 `applyNativeTextureColorSpace`(model.ts) 사용** | [데이터]+[웹 실행] |
| 감마 변형 | 장면+0x523c bit4 = SystemTask+0x464 bit0 = **SystemTask+0x422(sRGB 표시 버퍼 플래그)**. 0이면 UNORM 표시 버퍼(형식 0x1d)이고 **GAMMA 1(pow 1/2.2)**입니다. 생성자 기본값은 0입니다. 웹 캔버스는 UNORM이므로 GAMMA 1을 유지합니다. 로비에서 +0x422를 쓰는 writer는 찾지 못했습니다 | [판독], 로비 실제값 [미확정] |
| 그 밖의 경로 | 알베도/Emi/Trm sRGB, Rgh/Mtl/Nrm 선형, 베이크 RGBA16F, HDR 선형 half, 노출 2.0→Bloom 가산→Tone4→8³ LUT→pow(1/2.2)는 원본 식과 같습니다. 이중 변환은 없습니다 | [판독]+[데이터] |
| 효과 | 캡처 SH DC: cAr.w 0.128→0.312, cAg.w 0.149→0.367, cAb.w 0.227→0.481입니다. 위쪽 조도 R/B 비는 0.53→0.64입니다. 스테이지 화소 평균은 +9~11 레벨입니다(아래 §6) | [웹 실행] |

임의의 밝기·채도·감마 배율은 넣지 않았습니다. 원본 텍스처 값은 바꾸지 않았고, 저장된 값을 원본 형식대로 해석하도록만 고쳤습니다.

## 2. 색 공간 감사표

| 단계 | 원본 | 웹(수정 후) | 판정 |
|---|---|---|---|
| `_Alb`, `_Emi`, `_Trm`, mSun | BC1_SRGB, HW sRGB 디코드 | KTX2 tf=2 → SRGBColorSpace(BPTC_SRGB) | 일치 |
| `_Rgh`, `_Mtl` (`.mr` 합본) | BC4_UNORM | KTX2 tf=1 → LinearSRGB | 일치 |
| `_Nrm` | BC5_SNORM | KTX2 tf=1(UASTC) → Linear | 일치 |
| `_Opa` | BC4_UNORM | 알베도 KTX2의 **A 채널**(sRGB는 RGB에만 적용) | 일치 |
| `_Emm` | BC4_UNORM | 이전: GLTFLoader 강제 sRGB. **수정: NoColorSpace** | **고침** |
| `_Tcl`(오징어) | BC4_UNORM | gfx-char 고침(model.ts resolver) | 고침(타 담당) |
| mSky_Alb | BC6H_UFLOAT | 1차: 8비트 선형 NoColorSpace. **2차: 원본 BC6H 블록을 GPU가 디코드**(BPTC 없으면 8비트로 대체) | **고침** |
| 베이크 AO/그림자 | BC5_UNORM (R=AO, G=그림자) | 8비트 디코드 → RGBA16F, NoColorSpace | 일치 |
| 베이크 빛 | BC6H_UFLOAT, 셰이더 `rgb·a·32` (comp RGB1 → a=1) | bcdec float → RGBA16F, `hBL.rgb*hBL.a*32.` | 일치 |
| 주광·안개·스폿 색 | RenderingDay/genv 값을 그대로 씀(0x71036b35c0 `I·Diffuse` 감마 없음) | `color·intensity` 그대로 | 일치 |
| 팀색 | raw → pow 2.2 (0x71011743a0) | `buildTeamSet` 같은 식 | 일치 |
| 셰이딩·안개 | 선형, 셰이더 감마 없음 | forward.ts/hoian.ts에 pow/sRGB 변환 없음 | 일치 |
| 큐브 캡처 | RGBA16F 256² + Illuminate 되복사 | HalfFloat cube, LinearSRGB, NoToneMapping, Illuminate 패스(§9) | 일치(입력 재질 변형 제외) |
| HDR 타깃 | 선형 RGBA16F | HalfFloat MSAA4, LinearSRGB, NoToneMapping | 일치 |
| Bloom | 노출 전 HDR → mask/reduce/gauss/compose, 가산 | bloom.ts, NoColorSpace | 일치 |
| 노출 | `White2D.w × exp2(1.0)` = 2.0 | `exposure=2` | 일치 |
| 톤매핑 | Tone4 | 같은 식 | 일치 |
| LUT | 8³ RGB11/11/10, `c·.875+.0625` | CPU LUT, half 3D 텍스처, NoColorSpace | 일치(NVN 반올림·sampler 미확정) |
| 비네트 | 활성·값 미확정 | 비활성 | [미확정] |
| 감마 | GAMMA 1 (UNORM 표시) | `pow(c,1/2.2)` | 일치(§3) |
| 캔버스 | UNORM 표시 버퍼 | ShaderMaterial, colorspace_fragment 없음 → 추가 변환 없음 | 일치 |

검증 도구: `analysis/gfx_r11/probe/ktx_vs_native.py`(번들의 모든 KTX2 DFD transfer를 원본 BNTX 형식과 대조), `sky_colorspace_check.py`, `emm_colorspace_check.py`.

## 3. 감마 변형 판독

```text
0x71036c8c24(scene, flags):  scene+0x5238 |= 0x38;  scene+0x523c = flags     // +0x523c 의 유일한 writer
0x71037a5994 호출부: flags = (ST+0x458 bit4) | (ST+0x458 bit7)<<1 | (ST+0x458 bit5)<<2 | cond<<3
                          | (ST+0x464 bit0)<<4 | (ST+0xd0)->+0x338<<5 | ((ST+0xd0)->+8 bit4)<<6
                          | (ST+0x45c bit10)<<7 | ((ST+0xd0)->+8 bit6)<<8          // ST = gsys::SystemTask
0x71037a2348(ST ctor): ST+0x45c..+0x46b = 0
0x71037a46bc: ST+0x464 = (ST+0x464 & ~3) | ST+0x422 | ST+0x423<<1
              displayFormat = ST+0x423 ? 0x1a : (ST+0x422 ? 0x22 : 0x1d) → *(0x7105999378)+0x1d0
0x71036c99b8 step5: gamma = linear_lighting ? (523c bit4 ? 5239 bit4 : 1) : 5239 bit4
0x71036c8874: 복사 감마 = (출력 형식 == 0x1d) && linear_lighting && !(523c bit4)
```

- override 비트는 표시 버퍼 형식을 고르는 플래그와 같은 값입니다. 0이면 UNORM(0x1d)이므로 셰이더에서 감마를 걸고(GAMMA 1), 1이면 sRGB(0x22)이므로 GAMMA = +0x5239 bit4입니다. +0x5238 워드는 0x71036c8c24·0x71036c971c가 bit0~5만 쓰므로 bit12는 0입니다. 즉 이 경우 GAMMA 0이고 하드웨어가 sRGB 인코딩을 합니다. 어느 쪽이든 표시 인코딩은 한 번입니다.
- 0x1d/0x22/0x1a를 각각 R8G8B8A8_UNORM/SRGB/10비트로 보는 이름 대응은 [추정]입니다. 0x71036c8874가 0x1d일 때만 감마를 거는 것과는 맞습니다.
- ST+0x422 writer는 전체 텍스트에서 `strb/strh/str w` 스캔(#0x422/#0x423/#0x420)으로 찾지 못했습니다. 생성자에도 없습니다. 생성 인자 복사 경로 같은 다른 경로가 남아 있어 로비 실제값은 [미확정]입니다. sRGB 표시라면 원본은 piecewise sRGB 곡선이고 웹은 pow(1/2.2)입니다. 어두운 영역에서 차이가 납니다(선형 0.002 → 0.026 대 0.059).
- 디컴파일: `analysis/decomp/r11_gfx_light/{gamma_flags,systask_scene_flags,final_output,final_output2}.c`, 스캔: `analysis/gfx_r11/probe/{scan_523x,st464,st422b}.py`.

## 4. 광원·그림자 연결 확인

| 항목 | 원본 | 웹 | 상태 |
|---|---|---|---|
| MainLight | Color (0.6706,0.8510,1.0), Intens 10, Lat 34.5/Lon −3 → Env[5]=(6.706,8.510,10), L=(0.0431,−0.5664,−0.8230) | `hLightColor`/`hLightDirection` 같은 값(실측) | 연결됨 |
| 하늘 SH | 실행 중 큐브 캡처 2회 투영(0x710102ce04), skyUp은 로비 Ink/InkBright와 무관([r6]) | 캡처 2회 + 7MRT 투영 + 원본 CPU 포장. 이번에 하늘 입력 색을 고침 | 연결됨(Illuminate·재질 큐브 변형 없음) |
| 환경맵 | 12층 GGX prefilter(+Illuminate) | 2차에서 원본 식으로 연결(§9, 저장은 웹 아틀라스) | 연결됨 |
| 베이크 | `(rgb·a·32)`, AO/그림자 `[36]/[37]`(0x7102b67bc4: [36].x=−ShOff·ShScale, [36].y=ShScale) | 같은 식. 실내 G≈0이면 occBake 상한 1.875·(1−0.71875)=0.527이고 주광 47%가 남는 것은 원본 식입니다 | 연결됨 |
| 동적 그림자 | 캐스케이드 2, 1024², polygon offset 0.3/scale 5.0, PCF 0.5 texel | `NATIVE_SHADOW_SETTINGS` 같은 값, 맵은 `gsys_dynamic_depth_shadow 0`이라 caster 아님 | 연결됨(정적 깊이 그림자 2048 미구현) |
| 동적광 | 스폿 rig `Color·Intensity` | `dynamic_lights.ts` 같은 값 | 연결됨 |

## 5. 최종색

노출 2.0 → `HDR·2 + Bloom`(가산) → Tone4 → 8³ LUT(HSV Value1.0625→8점 곡선, Gamma1) → (비네트 비활성) → pow(1/2.2). 기존 GPU 검증(post 36/36)의 식은 바꾸지 않았고, 감마 근거 문자열만 갱신했습니다(`post.ts` stats).

## 6. 수정 전후 화면

같은 시작 위치에서 같은 입력 순서(`analysis/gfx_r11/shot.mjs`)로 찍었습니다. swiftshader, 960×540입니다. 수정 후 화면에는 gfx-char의 같은 시기 변경(팀색 행·피부·텍스처 소유권)도 들어 있습니다. 잉크·캐릭터 색 차이는 그쪽 변경입니다.

| | 앞 | 뒤 |
|---|---|---|
| 수정 전 | ![before front](../../../analysis/gfx_r11/stage_before_front.png) | ![before back](../../../analysis/gfx_r11/stage_before_back.png) |
| 수정 후 | ![after front](../../../analysis/gfx_r11/stage_after_front.png) | ![after back](../../../analysis/gfx_r11/stage_after_back.png) |

스테이지 영역(왼쪽 디버그 글·가운데 안내·캐릭터 제외) 평균 RGB: 앞 (79,77,77)→(88,86,87), 뒤 (125,129,137)→(136,140,148). 브라우저 콘솔 오류 0입니다.

## 7. 검증

| 실행 | 결과 |
|---|---|
| `npm run typecheck` | 통과 |
| `npm test` | 400/400 통과. 새 `tests/graphics_r11_light.test.mjs` 2건: 원본 BC6H 256텍셀(고정 `fixtures/sky_bc6h_bytes.json`)과 웹 샘플값의 최대 오차 ≤1.25/255(이전 sRGB 경로 평균 오차 >0.05), 맵 `_Emm` NoColorSpace·`_Alb/_Emi` sRGB 유지 |
| `sky_colorspace_check.py` | 전체 4096×1024: 선형 읽기 평균 오차 0.002(clamp 후 최대 0.0044), 이전 sRGB 디코드 0.114/0.170/0.252 |
| `emm_colorspace_check.py` | 이전 sRGB 디코드 배율(0이 아닌 텍셀): Celling 0.29, Fluorescentlight 0.58, Capsule02 0.29, M_Eye 0.078 |
| 브라우저 probe(`probe/tex.js`) | 텍스처 colorSpace·SH·주광 값 수집, 콘솔 오류 0 |

## 8. 남은 미확정

| 항목 | 이유·다음 근거 |
|---|---|
| SystemTask+0x422 실제값(로비 표시 버퍼 sRGB 여부) | 직접 store 없음. 생성 인자 구조체 복사나 vtable setter 경로를 추적해야 함. sRGB라면 웹은 pow 대신 piecewise sRGB 인코딩이어야 함 |
| 맵 재질 큐브 변형 | 캡처 때 맵은 웹 forward 재질로 그림(원본 cube 변형 재질 미판독) |
| 정적 깊이 그림자(2048) | `gsys_static_depth_shadow 1` 맵 caster 경로 미구현 |
| 비네트 활성·값, LUT NVN 반올림/sampler | 기존 미확정 유지 |
| 파츠 glb(Obj_SighterTarget 등) `M_Body_Emm` | 원본 형식 메타가 작업 폴더에 없어 대조 못 함 |

## 9. 2차(같은 날) — Illuminate·12층 반사·하늘 HDR

### 9.1 원본 판독·실행 결과

| 항목 | 결론 | 근거·수준 |
|---|---|---|
| Illuminate 흐름 | 0x710102ce04가 base 큐브(256², RGBA16F)를 그린 뒤 0x7101037098을 호출합니다. 0x7101037098은 base를 GGXPrefilterEnvMap(MRT1/FILTER2/ILLUMINATE1)으로 임시 텍스처에 그리고 **base로 되복사**합니다. 그 base로 SH 투영(0x710103289c)과 12층 prefilter(0x710103921c→0x7101036a18)를 합니다 | `r6_gfx_stage/c1_envmap.c` 되복사 루프 [판독] |
| Illuminate 입력 | 샘플 1(`cParam0.w`)입니다. roughness override는 `*(SceneCommonUBOHolder 0x7105818e38)+0xb98` = BlitzUBO0[18].x(잉크 거칠기 0.05)입니다. 하이라이트 roughness는 0.05+0.11(C34)입니다 | blitzubo0_layout 멤버 0x8b0=[18] [판독] |
| UBO | `cLightParam=(LightTexScale, .11, 개수)`, `cLightColor`=MainLight DiffuseColor RGBA(강도 미곱), `cLightInfo[i]=(normalize(cos lat·R(lonFromMain)·mainDir.xz, −sin lat), Intensity×BaseIntensity)` | **0x710102ff04 unicorn 원본 실행 65건**(Lby 1 + 무작위 64). 외부는 SDK sinf/cosf/sqrtf 원본, 스텁은 Lock/UnlockMutex뿐입니다. 웹 port와 param/color는 비트 일치, 방향 성분 절대차 ≤1e-6(JS libm 차이) [실행] |
| 배율·기본값 | holder+0xEC0 = RoughnessOffset(typed +0x60, 이 경로에서 소비 없음), **+0xEC4 = BaseIntensity**(+0x58, 기본 1.0), +0xEC8 = LightTexScale(+0x5c, 기본 1.0)입니다. LightArray 원소 기본값은 Intensity 1000 / Latitude 40 / Longitude 0(ctor 0x71011abd34)이고, 20개를 넘으면 복사하지 않습니다(0x7101030288) | param_reflect·디컴파일 [판독] |
| Lby 광원 | 18개: 6000(67.5°/315°), 3000(80°/180°), 1000×16(40°, 270/315/90/90/270, 나머지 11개는 0°). 원본 RenderingDay JSON과 같습니다 | [데이터] |
| 층12(잉크) | 0x7101036d84 flag0은 기본 텍스처 `*(0x7105999230+0x30)`을 층12로 복사합니다. 잉크 전용이라 이번 범위 밖입니다 | [판독] |
| 12층 | Illuminate 타입이면 샘플 400(0x7101036a18 `param_8==1`)입니다. 층 roughness는 `t+(sin((t−.92)·2π)−.4817533)·.13`(t=l/11, r0≈0, r11≈1)이고 FILTER_TYPE 2(입력이 큐브)입니다 | [판독] |
| BRDF | Hoian_Proc `GGXEnvBRDF`: 1024샘플, `x=Σ G(1−Fc)/1024`, `y=Σ G·Fc/1024`, 입력 (NoV, roughness) | 보완 CLI 역번역 `analysis/gfx_r11/proc_fixed/` [판독] |
| hemiFix | p1714 보완본 `clamp(1.16 − N.y·(1−dot(Nink,−L))·(1−clamp(−7·(inkMax−.3))))`, 상한 1. 비도색(inkMax≤0.157)은 **1.0**이라 일반 스테이지 면에는 영향이 없습니다 | [판독] → 웹 변경 없음 |
| 비네트 | ctx `*0x7105811f48`+0x300 객체(vtable 0x71055627e0)의 생성자에서 +8=0입니다. 켜는 writer 0x710115d94c(+8=1, 파라미터 +9..+0x34)는 vtable 0x7105564a90 슬롯14(0x710115ce08)가 꼬리호출합니다. 끄는 곳은 0x710115b640, 0x7102b90124입니다. 로비에서 이 슬롯이 언제 불리는지 미확정이라 비활성을 유지합니다 | [판독], 활성 [미확정] |

보완 역번역 명령: `web/tools/shader_ryujinx/dotnet/dotnet.exe analysis/reference_graphics_r3/surface/dump/bin/Release/net10.0/dump.dll prog-sharc extracted/shader/Sample.Nin_NX_NVN.release/Hoian_Proc.sharcb <GGXPrefilterEnvMap|GGXEnvBRDF> analysis/gfx_r11/proc_fixed`. 기존 `analysis/r5_gfx_stage/proc/`는 Negate 괄호 결함이 있는 표준 dump이므로 이식에 쓰지 않았습니다.

### 9.2 웹 반영

| 파일 | 내용 |
|---|---|
| `client/render/env_prefilter.ts`(신규) | `illuminateUBO`(0x710102ff04 f32 port), Illuminate 큐브 패스(base 1샘플 prefilter + 18광원 하이라이트, 보완 GLSL 식 그대로), 12층 GGX prefilter(400샘플, PDF 기반 lod, 98304), `GGXEnvBRDF` CPU port → 64² LUT, 머티리얼 조회 `hNativeEnvSpecular` |
| `client/render/lighting.ts` | 캡처마다 base → Illuminate → 그 큐브로 SH·12층·PMREM(비원본 재질용) |
| `client/render/forward.ts` | Hoian forward의 `indirectSpecular`를 원본 식으로 교체: 층 `roundEven(5.5−5.5cos πr)`, `prefil(R)·(F0·brdf.x+brdf.y)·(1−occAO)` |
| `client/render/sky.ts`, `map.ts` | mSky_Alb 원본 BC6H 블록을 `RGB_BPTC_UNSIGNED` 압축 텍스처로 GPU 디코드(`EXT_texture_compression_bptc` 있을 때). sampler는 원본 repeat/linear+point mip. 하이라이트 텍스처 로드 |
| 에셋 | `maps/Lby_Lobby00/sky/mSky_Alb.bc6h.{bin,json}`(5,592,464 B, 13밉 원본 블록 비트 그대로), `env/IlluminateEnvMap.rgba8.{bin,json}`(64² BC1_SRGB 7밉 디코드, 21,844 B). catalog `map/Lby_Lobby00` bytes 73,755,489 → 79,371,949 |

재생성 명령: `.venv/Scripts/python web/tools/asset_r11_env.py`(원본 romfs 읽기 전용 → 번들 4파일 + catalog 갱신). 원본 블록 검증: 내보낸 bin을 bcdec로 디코드한 값이 `decode_bc6h_float`와 mip0/3/12 모두 최대차 0입니다.

웹 정책(원본 아님): 12층을 768×512 2D 아틀라스(층 타일 128/128/64/64/32/32/16/16/8/8/8/8, 면 수동 선택, lod0)에 담습니다. 원본은 cube array 13층이고 implicit LOD입니다. BRDF LUT 해상도 64와 `(NoV, −r)`·repeat 좌표를 `r` 행으로 저장한 것, cVanDerCorputMap 내용을 base-2 radical inverse로 둔 것([추정]: 이름과 Hammersley 패턴 근거)도 웹 정책입니다. Illuminate 결과 큐브의 밉은 웹이 다시 생성합니다.

### 9.3 검증

| 실행 | 결과 |
|---|---|
| `npm run typecheck` / `npm test` | 통과 / **422/422**(신규: Illuminate 원본 65건 대조, Lby 18광원·기본값, 층 roughness 끝점·층 선택, BRDF 범위·VdC, 아틀라스 면 왕복) |
| 브라우저 GPU probe(`analysis/gfx_r11/probe/env.js` → `env1.json`) | `illuminate: 18 lights connected`, prefilter 2회, sky `bc6h`, BPTC 지원. 하이라이트 증분(GPU lit−base)과 CPU 식(같은 UBO·하이라이트 텍스처 bilinear): 정점 방향 −L0/−L1/−L7에서 상대차 1.5/4.3/2.0%(half 저장·텍셀 보간), 그 밖의 방향 <1e-3 |
| SH DC | cAr.w .312→.368, cAg.w .367→.441, cAb.w .481→.567(+18%, Illuminate 반영) |
| 콘솔 오류 | 0 |

### 9.4 화면(마지막 한 번 촬영)

| | 앞 | 뒤 |
|---|---|---|
| 2차 후 | ![stage2 front](../../../analysis/gfx_r11/stage2_after_front.png) | ![stage2 back](../../../analysis/gfx_r11/stage2_after_back.png) |

스테이지 영역 평균 RGB(1차 전 → 1차 후 → 2차 후): 앞 (79,77,77) → (88,86,87) → (89,88,88), 뒤 (125,129,137) → (136,140,148) → (135,139,147). 2차 변경은 반사(하이라이트·층·BRDF)와 SH +18%라서 이 시점의 평균 밝기 변화는 작습니다. 원본 동일 위치 화면이 없어서 "회색·평평함"이 원본과 얼마나 다른지 수치로 확정하지 못했습니다. 바닥 알베도가 선형 0.01~0.03이고, 베이크 그림자 G≈0이면 주광의 47%가 남는다는 점(§4)은 원본 데이터와 식 그대로입니다.

### 9.5 남은 미확정(2차 갱신)

| 항목 | 이유·다음 근거 |
|---|---|
| SystemTask+0x422(sRGB 표시) | 생성 함수 0x7103da0258·생성자·prepare에서 +0x420..+0x423을 쓰는 곳을 찾지 못했습니다. 영(0) 초기화라면 GAMMA 1이 맞습니다 |
| 비네트 활성 | vtable 0x7105564a90 소유 클래스와 슬롯14 호출 조건 필요 |
| LUT 반올림·sampler | NVN R11G11B10 쓰기 반올림·sampler 미확인. 영향은 노드당 6비트 가수 이하 |
| 12층 저장 형식 | cube array 13층의 층별 mip·implicit LOD 규칙(1035C4C `FUN_710103d774` 인자 의미) 미확정 → 웹 아틀라스 |
| cVanDerCorputMap 내용·GGXEnvBRDF 해상도 | 텍스처 생성자 미발견 |
| 캡처 시 맵 재질 cube 변형 | 원본 cube pass 재질 변형 미판독 |
