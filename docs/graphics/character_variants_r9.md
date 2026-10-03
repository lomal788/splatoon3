# 탱크·하네스·슈터 잉크병의 필름 재질 — r9, 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

r8의 실제 플레이어 로딩에서 남았던 taransmission 후보3개를 원본 프로그램까지 추적했다. 같은 `M_Body` 이름을 가진 인간 피부와 탱크를 같은 재질로 다루면 안 된다. **[데이터]+[판독]** 탱크·하네스·슈터 병은 CompPaint/Thc를 읽지 않으며, 이들에 피부·오징어의 필수 texture gate를 걸었던 것은 웹의 과도한 조건이었다. 병은 실제 transmission texture도 사용하지 않는다.

이번 웹 반영은 세 shader variant의 필름·투과량·scattering lobe·F0와 색 계산을 구별하고 필요한 실제 자원만 요청한다. 탱크의 같은 이름 자원 충돌을 발견해 원본 owner별 자원을 준비했다. **일반 재질 branch 지원과 원본 화면 전체 동등성은 별개다.** 초기에는 비항등 TexSRT→Mat producer도 미확정으로 남겼다. **정정(2026-10-03): 뒤이어 원본 Maya/회전0도 callback의 실행 근거가 확보되어 실제 탱크·병의6lane와 해당 runtime endpoint를 연결했다(§6).** 다른 mode/회전, 원본 그림자/환경 BRDF, 재질 애니메이션의 모든 소비까지 해결된 것으로 세지 않는다. 기존 whole inventory의 분모/완료 수를 이 부분 포팅으로 변경하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 Product `Hoian_UBER.Product.bfsha/hoian_uber`와 실제 출하 웹 GLB를 사용했다. 기존 SHARED/FUNCS와 `decomp_index.py --no-build M_Harness M_Bottle Tnk_Simple`, `... tex_mtx TexSrt ModeMaya`를 확인했다. 해당 sampler 변형의 소비 식과 SRT producer 확정 기록은 찾지 못했다. 기존 [shaders.md §3.5–3.7](shaders.md)의 키 선택·팀색·UV 의미를 재사용했고 원본 함수 디컴파일/Unicorn을 반복하지 않았다.

| 실제 owner / 재질 | 정확한 정적 키 후보 | 분석 자료 |
|---|---:|---|
| `characters/Player00/parts/Tnk_Simple.glb / M_Body` | 2419,2423 | [tank_grouped.frag](../../../analysis/port_graphics_r9/variants/tank_grouped.frag), `.vert/.options.txt` |
| 같은 owner / M_Harness | 4526,4530 | [harness_grouped.frag](../../../analysis/port_graphics_r9/variants/harness_grouped.frag), `.vert/.options.txt` |
| `weapons/Shooter_Normal_00/model.glb / M_Bottle` | 320 | [bottle_grouped.frag](../../../analysis/port_graphics_r9/variants/bottle_grouped.frag), `.vert/.options.txt` |

[actual_variants.json](../../../analysis/port_graphics_r9/variants/actual_variants.json)은 GLB FRES 전체, 정규화 옵션과 후보를 보존한다. `<Default Value>`를 BFSHA 기본값으로 채우고 True/False→1/0, renderInfo·assign_type을 합친 정적 키의 **불일치가0인 후보만** 사용했다. 첫 시도의 raw GLB 옵션은 matching0/no program이었다. CLI exit0을 shader 성공으로 기록하지 않았다.

탱크·하네스의 두 후보는 gsys_weight가 다르며 fragment는 첫 header를 제외하고 완전히 같았다([alternate_program_check.json](../../../analysis/port_graphics_r9/variants/alternate_program_check.json)). 동적 weight에 관한 실제 원본 runtime 선택 전체를 이번 fragment 동등성으로 확정하지 않는다. negate 괄호 보완 분석 전용 emitter는 r3의 원시 명령 부호 검사를 재사용했다.

## 3. 진입점과 전체 호출 흐름

```text
실제 GLB의 owner + FRES + geometry + texture resolver
  → applyHoian: UV/재질 색 계산/Trm 또는 상수 T
  → applyForward: 공통 RGB·alpha 광원/SH/shadow/fog
  → applyCharacterMaterial: painted / sfxFilm / constantFilm 선택
  → 실제 필요한 texture handle만 await
  → shader: film → diffuse/SHNormal → tau → direct와 backlight
```

[판독] 원본 tank/harness는 SFX.R, transmission RGB, AO.R 및 재질 색 계산의 resource를 읽는다. bottle은 normal/roughness 외에 Mat 상수·팀색을 읽고 transmission RGB는 상수로 만든다. 세 fragment에는 cTexCompPaint와 cTexResource2/Thc sampling이 없다. slot이 빠졌다는 관측만으로 미사용을 추측한 것이 아니라 fragment 전체 texture 호출과 옵션을 확인했다.

## 4. 구조체·필드·상수·열거형 표

아래 숫자는 실제 원본 FRES 기본값/옵션 [데이터]다. runtime material animation 뒤 값을 뜻하지 않는다.

| 입력 | 탱크 몸 | 하네스 | 잉크병 |
|---|---:|---:|---:|
| transmission_rate | .543 | .543 | .05 |
| scattering_rate | .4 | .4 | .72 |
| film_transmission_rate | .88 | .82 | .62 |
| film_transmission_power | .7 | .5 | 2.6 |
| enable_edge_transmission | 0 | 0 | 0 |
| enable_thickness_map / blitz_paint_type | 0 / 0 | 0 / 0 | 0 / 0 |
| enable_manual_fresnel | 0 | 0 | 0 |
| transmission_mask | 2(SFX.R) | 2(SFX.R) | 3(상수1) |
| enable_transmission_map | 1 | 1 | 0 |
| transmission_multi_color | 0 | 0 | 2(팀색 곱) |
| backlight RGB | white | white | white |
| under_film_color.rgb | (0,0,0) | (0,0,0) | (0,0,0) |
| output alpha | 1 | sat(Opa.R) | 1 |

`edge_transmission_power`는 3.7/3.7/1.5가 데이터에 있어도 이 세 프로그램은 추가 edge angular power를 사용하지 않는다. 필드가 있다는 이유로 소비를 발명하지 않았다. F0는 metalness로 만든 기존 식을 유지한다. film 옵션만 보고 manual_fresnel=1을 적용하면 원본과 다르다.

| resource / writer | native shader reader | 웹 역할 |
|---|---|---|
| Tnk `M_Body_Fxm/_fm0` R | tank306/355/362 | film mask와 tau base, 필수 |
| Harness `M_Harness_Fxm/_fm0` R | harness315/418/425 | 같은 역할, 필수 |
| Trm RGB × backlight | tank352/404–406, harness316/395–397 | 실제 texture 입력 |
| Bottle Mat backlight × team | bottle363–365 | texture 없는 T |
| AO.R | tank403, harness398 | SH/dynamic/env AO |
| roughness.R | tank326, harness370, bottle292 | max(sampleR,.0001), 기존 glTF packed G 입력 대응 |
| Harness Opa.R | harness303–307/562 | <=0 discard 및 최종 alpha |
| Env[5].w / 동적 RGBA.w | 원본 light writer → 각 shader 최종 역광 | RGB와 독립 alpha 소비 |

행 번호는 보완 grouped 산출물 기준이다. sampler material slot, 원본 loc, GLSL binding 번호는 다른 번호 공간이다.

## 5. 상태 전이와 전체 수명

`characterVariantProfile`은 기존 painted4재질과 sfxFilm2, constantFilm1을 구별한다. shader가 실제 읽는 input만 load gate에 넣는다. source가 없는 texture를 만든 후 준비됨으로 표시하지 않는다.

- painted: 원본 2cl/Thc/cheap mask 경로는 r8을 유지한다.
- sfxFilm: 실제 SFX, AO, transmission map과 사용된 calc resource를 요구한다. CP/Thc를 요구하지 않는다.
- constantFilm: CP/Thc/SFX/Trm/resource0를 요구하지 않는다. 실제 병의 resolver 추가 호출은0이다.
- 필수 자원 실패면 `missing` 기록, hCharReady=0으로 기존 forward fallback을 유지한다.
- dispose는 binding hook/cache-key만 복구한다. model/geometry/공유 texture 소유권은 caller다.

`textureReady`, `hookCompiled`, `ordinaryConsumer`, `nativeUvMatrices`는 서로 다른 상태다. 초기 조사에서 탱크·병의 마지막 값은false였다. 뒤이어 원본 Maya/회전0 callback을 연결하여 세 variant 모두true로 정정했다. runtime에 미지원 mode/회전을 공급하면 마지막은false이고 기존 row가 유지되며 미지원 진단은 caller가 기록한다.

## 6. 계산식·조건·상세 의사코드

[판독] N=최종 normal-map 법선, Nv=정점 법선, V=표면→눈, L=표면→빛(−Env[23]). sat=clamp0..1. 세 재질은 cheapSSS mask0이며 k=1이다.

```text
mask = tank/harness ? SFX.R : 1
film = sat(mask * pow(sat(max(N·V,.001)), film_power) * film_rate)
tau = transmission_rate * mask * (1-film)
q = (scattering_rate-1)^2
lobe = q * pow(sat(max(−V·L,.001)), 1/scattering_rate) − .2*q + .200000003
T = tank/harness ? Trm.RGB * backlight : backlight * my_team_color
diffuse = mix(albedo*(1-metalness), underFilm, film)
SHNormal = mix(N,Nv,film) // 뒤에 normalize하지 않음
F0 = mix(.04,albedo,metalness) // manual-fresnel override 없음
direct = sat(N·L) * lightRGB * BRDF(diffuse,F0,roughness) * shadow * sat(1-tau)
back = AoLight * lobe * T * lightAlpha * tau
```

동적광도 같은 lobe/film/tau를 사용하고 거리·spot attenuation 및 해당 RGBA.w를 별도로 곱한다. 세 프로그램은 원본 피부의 `pow(sat(1−NoV*sat(−NoL)),edgePower)`를 사용하지 않는다. 몸·오징어·머리카락 기존 enable_edge_transmission1 경로는 유지했다. CompPaint normalCorrection도 이 세 shader에는 없으므로 상수1이다.

색 계산 [판독]:

```text
tank emission calc22 = sat(EmissionTextureRGB * emission_color * const_value0
                         + Resource1RGB − Resource0RGB)
                         * emission_intensity
  Resource0 = native UV2 + tex_mtx1, Resource1/Emission = UV0
harness calc8 albedo = Resource0RGB * const_color0 + AlbedoRGB
bottle calc1 albedo = mix(albedo_color,my_team_color,sat(team_color_blend))
                       + my_team_color
```

tank의 calc D_channel2는 전체 vec4의 unary negative다. 기존 calcChannel이 이 채널을 지원하지 않았고 type22도 빠져 있었다. A*B+C+D와 음수 D를 연결했다. 이 선택 variant 증거를 전체 color-network enum 완료로 올리지 않는다.

**정정(2026-10-03, 발광 강도 중복):** 출하 Tnk GLB `M_Body`의 `emissiveFactor=(.5,.5,.5)`는 exporter에서 `emission_color×emission_intensity`로 만든 값이다([GltfExport.cs](../../tools/asset_bfres2gltf/GltfExport.cs), 388–391행). Three의 `totalEmissiveRadiance`를 calc22의 A로 쓰고 마지막 원본 intensity=.5를 다시 적용하면 A항에 intensity가 두 번 들어간다. 원본 tank516–518행은 **raw EmissionTexture×emission_color×const_value0**를 clamp 앞에서 사용한 다음 최종 intensity를 한 번만 곱한다. 따라서 type22 경로에 실제 `_e0` raw sampler를 연결하고, 준비 gate에 이 실제 자원을 포함했다. emission texture를 제거하거나 intensity로 나누는 근사는 사용하지 않았다. 기존 다른 emission variant는 이 정정의 범위로 승격하지 않는다.

UV shader 소비 [기존+신규 판독]: `u'=u*row0.x+v*row0.z+row1.x`, `v'=u*row0.y+v*row0.w+row1.y`. `_u2=_u0`인 탱크는 **같은 정점 속성**을 써도 UV2의 tex_mtx1을 따로 적용한다. sampler의 native 옵션 이름 `texcoord_select_res0/res1/trsmap`을 기존 잘못된 resource0/resource1/transmission 이름과 구분해 읽었다. packed Mat입력은 `setHoianTexMatrix`로 shader와 실제 PBR UV에 전달한다.

**정정(2026-10-03, native Maya/회전0 producer):** [실행] 별도 원본 분석에서 `ShaderParamCallbackInstall 088f308 → type30 TexSrt callback 088efb0 → Maya writer 088f3d0`를 찾았다. 원본 Main/SDK numeric symbol·SinCosSampleTable[0]을 실제 데이터로 공급한 전체 callback 실행313건이 웹 sixlane 계산과 f32 비트 일치했다. 원본 writer는24B만 쓰며 그 뒤8B는 쓰지 않는다. 상세 근거는 [character_texsrt_r9.md](character_texsrt_r9.md), [texsrt_native_summary.json](../../../analysis/port_graphics_r9/material_anim/texsrt_native_summary.json), [native fixture](../../games/splatoon3/tests/fixtures/material_texsrt_r9_native.json)에 있다. 이 agent는 실행 산출물과 테스트를 재사용했으며 원본 함수를 중복 실행하지 않았다.

| 실제 기본 SRT | 원본 active sixlane / 웹 소비 |
|---|---|
| Tnk tex_mtx1 Maya, sx=sy=1, tx=0, ty=f32(−.6), rot=0 | `[1,−0,0,1,0,f32(−.6)]` → UV2/Resource0 |
| Bottle tex_mtx0 Maya, sx=1, sy=2, tx=ty=0, rot=0 | `[1,−0,0,2,0,−1]` → normal/roughness 등 실제 UV0 |

`applyHoian`은 이 검증된 mode/rotation만 static 행렬로 공급한다. `setHoianMaterialTexSrt(mat,name,raw):boolean`은 tex_mtx0/1/2의 실제 등록 endpoint를 찾아 같은 원본 sixlane helper를 사용하며 미지원 값은false다. shader는 row0.xyzw+row1.xy만 읽는다(tank vertex162–165, harness206/208, bottle157/164). **row1.zw=0은 미소비 웹 carrier padding**으로 두며 원본 UBO padding/upload 값이라고 주장하지 않는다. nonzero rotation과 다른 mode의 수식은 이 경로로 추정하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

**[데이터] 실제 owner 충돌:** bundle의 이름만으로 `M_Body_MAi`와 `M_Body_Trm`를 찾으면 피부용 256²/64²가 탱크로 공급됐다. 원본 탱크는 각각64²/256²다. 탱크 GLB embedded images에는 두 resource와 FxM이 없으므로 GLB 우선 lookup도 이 충돌을 해결하지 못했다. [resource_manifest.json](../../../analysis/port_graphics_r9/variants/resource_manifest.json)에 PNG 원본 추출 경로, metadata, SHA, 크기, slot/UV/channel을 보존했다.

| owner-scoped 신규 resource | 바이트 | 원본 형식/웹 KTX transfer |
|---|---:|---|
| Tnk_Simple/M_Body_MAi.ktx2 | 1697 | 데이터 texture / linear1 |
| Tnk_Simple/M_Body_Trm.ktx2 | 4142 | BC1_SRGB / sRGB2 |
| Tnk_Simple/M_Body_Fxm.ktx2 | 1801 | BC4_UNORM / linear1 |
| 합계 catalog delta | **7640** | 기존 자원을 덮어쓰지 않고 owner scope로 추가 |

분석 PNG→KTX2 UASTC staging은 원본 BC block/mip bit 복사가 아닌 웹 변환이다. original/GLB는 변경하지 않는다. 실제 owner resolver/catalog 추가는 부모 통합이며, 동일명 피부·오징어·무기 자원을 탱크 자원으로 덮어쓰면 안 된다.

**정정(2026-10-03, staging colorSpace):** 첫 Tnk Trm 변환에 --linear를 잘못 적용했다. 원본 metadata의 BC1_SRGB/srgbtrue와 달라 sRGB carrier로 재변환했다. 최초3855B→최종4142B, 합계7353→7640B로 정정한다. DFD primaries1/transfer2 확인([ktx_colorspace.json](../../../analysis/port_graphics_r9/variants/ktx_colorspace.json)), Three KTX2Loader의 parseColorSpace는 이를 SRGBColorSpace로 받는다. 별도 shader에서 임의 gamma를 또 곱하지 않는다. 기존 Harness/피부/얼굴/머리카락 Trm은 원본 sRGB와 current transfer2가 이미 일치했다([existing_resource_colorspaces.json](../../../analysis/port_graphics_r9/variants/existing_resource_colorspaces.json)).

탱크 Gauge/InkLockGauge/type11 재질 writer는 별도 animation 경로다. 이번 static variant 포팅으로 잉크 잔량/점멸/잠영 상태까지 해결되었다고 보고하지 않는다.

## 8. 다른 기능과의 상호작용

공통 light RGB·alpha는 기존 r8 live uniform을 참조한다. 재질 AO는 SH/dynamic/environment에 적용하며 direct shadow와 섞어 새 값으로 대체하지 않는다. 원본 SPP.x/y, fade, projection의 전체 입력 및 환경 cube/BRDF LUT는 [character_material_r8.md §11](character_material_r8.md)의 미확정/웹 어댑터 경계를 유지한다.

alpha는 탱크·병1, 하네스 shader Opa.R이며 <=0 discard가 있다. 하네스 renderInfo의 mask/alpha-test state와 glTF alphaTest 공급은 별개 GPU state다. film을 opacity로 해석하지 않는다. 현재 packed baseColor alpha의 Opa.R 대응은 에셋의 합성 방식을 재사용하며 최종 fixed alpha 비교·AA까지 원본 화면 동등성으로 승격하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

소스는 [character_material.ts](../../games/splatoon3/client/render/character_material.ts), [character_material_math.ts](../../games/splatoon3/client/render/character_material_math.ts), [hoian.ts](../../games/splatoon3/client/render/hoian.ts)에 반영했다. 공개 binding API와 applyHoian→applyForward→applyCharacterMaterial 순서는 r8 그대로다.

1. 실제 owner-scoped resolver를 공급한다. 탱크의 MAi/Trm/FxM 세 resource만 scope 우선 lookup한다.
2. 정확한 FRES options/geometry를 사용한다. variant별 missing을 검사한다.
3. 기본 Maya/회전0 SRT는 `applyHoian`이 원본 sixlane로 자동 공급한다. runtime typed SRT는 `setHoianMaterialTexSrt(mat,name,raw)`로 같은 endpoint에 전달한다. 그 외 검증된 외부 Mat row에만 `setHoianTexMatrix(u,UVIndex,packed8)`를 사용한다.
4. 부모 runtime material animation evaluator의 typed SRT와 scalar/color 결과는 지원 consumer의 연결 여부를 별도로 기록한다. raw 값을 계산했다는 사실은 화면 소비 증명이 아니다.
5. `stats.variant/nativeUvMatrices/textureReady/hookCompiled/ordinaryConsumer`를 실제 게임 draw에서 확인한다.

## 10. 검증 코드·실행 결과·기대값

| 명령/검사 | 결과 | 검증 범위 |
|---|---|---|
| exact key selection | 세 owner, static mismatch0 | [데이터], 원본 runtime 전체 선택 함수 실행 아님 |
| grouped CLI dump5회 | exit0, primary3+alternate2 | [판독 보조], NVN 실행 아님 |
| `node --test ...character_material.test.mjs ...character_variants.test.mjs` | **12/12 PASS** | 기존4 회귀6+새variant6, 실제 FRES/기본 Maya row/runtime 미지원 검사 |
| `node --test ...material_texsrt.test.mjs` | **2/2 PASS**, native callback313case sixlane f32 비트 일치 | [실행] 원본 출력 fixture 재사용, 이 agent의 원본 중복 실행 없음 |
| `node analysis/port_graphics_r9/variants/gpu_compare.mjs` | **448/448 PASS**(film/tau/lobe/alpha288+발광64+UV96), maxAbs **5.960464477539063e-8**, GL0/errors0 | 선택 original GLSL vs port helper/calc22/실제 hook UV, 동일 WebGL2/SwiftShader |
| controlled full shader draw | 3variant ready/compiled/finite/GL0 | 실제 FRES params, synthetic plane+tangent/gray texture. 게임 원본 픽셀 일치 아님 |
| 기존 r8 `gpu_compare.mjs` | 512/512 PASS, maxAbs1.1920928955078125e-7 | 기존4 소비 회귀 |
| `npm run typecheck` | PASS exit0 | source 타입 연결 |

[GPU report](../../../analysis/port_graphics_r9/variants/gpu_verification.json)은 각448입력과 세 full draw 결과를 보존한다. 원본 식은 `{tank,harness,bottle}_{native_slice,uv_native_slice}.glsl`과 [tank_emission_native_slice.glsl](../../../analysis/port_graphics_r9/variants/tank_emission_native_slice.glsl)로 보존하며 입력 변수/Mat/Env 이름을 fixture에 대응시켰다. 발광 검사는 원본 outer fma의 clamp/강도 operand를 그대로 추출하고 조명 addend만0으로 분리해 비교했다. full shader에는 GLB와 같은 emissiveFactor=.5를 넣고 raw sampler가 별도로 연결됨을 Node hook 검사로 확인했다. UV 검사는 실제 compiled Hoian의 `hUV=...` 문장을 뽑고 실제 native6lane uniform을 사용해 원본 vertex UV 식과 비교했다. fma는 WebGL a*b+c 어댑터이므로 native fused rounding bit 일치나 [실행]으로 세지 않는다. film/tau/lobe CPU helper는 JS 계산/최종 f32 변환이고 native Maya callback의 sixlane 실행 검증은 별개다.

그룹별 최대 오차는 film/tau/lobe/alpha288건 **5.960464477539063e-8**, 발광64건 **0**, UV96건 **0**이다. [verify_docs.py](../../../analysis/port_graphics_r9/variants/verify_docs.py)로 report 숫자, 11절, 실제 상대링크 누락0을 최종 확인했다.

명시적 경계 입력: Tnk mask=.5,NoV=1에서 film=.44, tau=.543*.5*.56=.15204. scattering_rate=.4,V·L=−1이면 lobe=.488이며 Nv/NoL을 바꾸어도 이 세 variant에서는 추가 angular power가 없다. synthetic packed row 테스트는 Mat 소비만 검증하고 Maya SRT producer313case 실행 증거와 구분한다. 명령과 실패는 [commands.md](../../../analysis/port_graphics_r9/variants/commands.md)를 따른다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 상태·이유·시도 | 다음에 볼 곳 |
|---|---|---|
| Tnk tex_mtx1 Maya translationY−.6 | 당초 [미확정], **2026-10-03 정정: [실행]+[판독]** Maya/회전0 callback과 sixlane 원본 fixture로 해결·웹 static/live endpoint 반영. identity adapter에서 nativeUvMatrices=true로 변경 | 원본 Mat upload/padding은 아래 경계를 유지 |
| Bottle tex_mtx0 Maya scaleY2 | 당초 [미확정], **2026-10-03 정정: [실행]+[판독]** 같은 callback과 nativeUV0 sixlane/PBR 소비 반영. Three Texture.matrix로 대체하지 않음 | 같은 upload/padding 경계 |
| 다른 TexSrt mode/nonzero rotation/Mat padding | [미확정] 이번 native 실행 지원 범위는 Maya/회전0의6floats/24B. 다른 mode/rotation을 전달하면false; row1.zw는 웹 미소비0 carrier. 원본 UBO packing/upload 전체 검증은 아님 | 원본 mode table의 나머지 writer, 실제 trig/회전 경계, shader-param block upload/offset |
| runtime type11/패턴·Gauge | [미확정] 기본 파라미터·texture 준비와 AS curve runtime 소비는 다른 작업 | 원본 material binding/apply→typed scalar/color/TexSRT→각 shader consumer |
| fixed alpha/AA | [미확정] shader Opa.R/discard와 renderInfo를 분리 확인했으나 원본 최종 GPU state/AA capture 없음 | 원본 pass state/capture와 웹 actual fixed state 대조 |
| 그림자·환경반사·최종색 | [미확정] 기존 common shadow/PMREM/BRDF 어댑터 | 원본 SPPxy/fade/cube-array/BRDF resource 공급, 기존 공통 문서 경계 유지 |
| asset 변환/실제 픽셀 | [미확정] PNG→UASTC 재압축/웹 mip/필터는 original block 동일이 아님. 원본 동일 camera/pose/frame 기준 capture 없음 | 실제 native texture/mip/sampler와 같은 프레임 pixel 비교 |

이 문서는 불필요한 gate 제거와 새 판독식의 소비를 기록한다. 위 미확정을 임의 기본값으로 채워 세 재질 전체 또는 전체 그래픽 완료로 표시하지 않는다.
