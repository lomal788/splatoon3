# 실제 캐릭터 네 재질의 피부 산란·역광·필름 소비 — r8, 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

피부가 빛을 받는 경계에서 완전히 검어지는 차이, 몸과 얼굴의 가장자리 역광이 없는 차이, 머리카락·오징어가 불투명 플라스틱처럼 보이는 차이를 대상으로 한다. [판독] 원본은 MAi.R 마스크에 wrapped lighting을 섞고, Thc.R로 역광을 줄이며, 오징어·머리카락의 필름량으로 바탕색·환경광 법선·투과량을 함께 바꾼다. 이것은 재질 opacity나 임의의 보조광으로 대체할 계산이 아니다.

**이번 웹 반영:** 실제 출하 GLB의 body/face/squid/hair 네 재질에 원본 일반 재질 분기의 cheap SSS, edge transmission, film, CompPaint 기반 보정 법선과 직접광 감쇠를 연결했다. [웹 GPU 대조] 원본 보완 GLSL의 선택된 식과 포팅 함수를 동일 WebGL GPU에서 512건 대조해 최대 절대 오차 `1.1920928955078125e-7`을 확인했다. 원본 NVN GPU 실행, 전체 원본 화면 동등성 또는 그래픽 전체 확정으로 올리지 않는다. 전체 질문 inventory의 분모·완료 수를 이 부분 결과로 바꾸지 않는다.

기존 원본 근거는 [reference_character_lighting.md](reference_character_lighting.md)를 재사용한다. 이 문서는 **실제 웹 소비와 그 경계**를 기록한다.

## 2. 분석 대상 원본·버전·자료 위치

| 대상 | 자료 | 수준 |
|---|---|---|
| Splatoon 3 v0 원본 | `extracted/shader/Hoian_UBER.Product.bfsha`, Hoian_UBER | [데이터], 원본 읽기 전용 |
| 인간 몸 | [body5549_grouped.frag](../../../analysis/reference_graphics_r3/character/body5549_grouped.frag), `.vert` | 기존 [판독] 재사용 |
| 인간 얼굴 | [face1115_grouped.frag](../../../analysis/port_character_r8/material/face1115_grouped.frag), `.vert`, `.options.txt` | 이번 동일 보완 emitter 재출력 후 [판독] |
| 오징어 | [squid3358_grouped.frag](../../../analysis/reference_graphics_r3/character/squid3358_grouped.frag) | 기존 [판독] 재사용 |
| 머리카락 | [hair2855_grouped.frag](../../../analysis/reference_graphics_r3/character/hair2855_grouped.frag) | 기존 [판독] 재사용 |
| 실제 웹 네 재질 | [actual_materials.json](../../../analysis/port_character_r8/material/actual_materials.json), [fixture](../../games/splatoon3/tests/fixtures/character_material_native.json) | 실제 GLB JSON에서 추출한 [웹 데이터]. 원본 FRES 대조는 기존 문서 재사용 |
| 새 웹 소비자 | [character_material.ts](../../games/splatoon3/client/render/character_material.ts), [character_material_math.ts](../../games/splatoon3/client/render/character_material_math.ts) | 웹 구현 |
| 재질 색 계산 | [hoian.ts](../../games/splatoon3/client/render/hoian.ts) | 선택된 원본 type/source 소비 추가 |
| 실행 기록 | [commands.md](../../../analysis/port_character_r8/material/commands.md), [gpu_verification.json](../../../analysis/port_character_r8/material/gpu_verification.json) | 성공·실패 모두 보존 |

번역기의 negate 괄호 결함과 원시 FMUL 부호 대조는 기존 문서 §2를 따른다. 이번 얼굴도 같은 분석 전용 보완 emitter로 출력했다. legacy GLSL과 SHA가 같다는 이유로 잘못된 식을 재사용하지 않았다. 보완 GLSL 실행 역시 원본 NVN 명령 전체 실행과 구분한다.

신규 추적 전에 SHARED.md/FUNCS.tsv 및 `decomp_index.py --no-build 0x7101134c40 0x71036b35c0 0x7102c1d6ec`를 확인했다. 해당 원본 함수 분석은 이미 존재하여 다시 디컴파일·Unicorn 실행하지 않았다. 신규 파일에 임의 함수 주소나 기존 함수의 신규 [실행] 성과를 기입하지 않았다.

## 3. 진입점과 전체 호출 흐름

[판독] 원본 경로는 `MainLight RGBA×Intensity → Env[5]`, 재질 옵션·파라미터·sampler, CompPaint/normal branch, ordinary/ink branch, wrapped direct/edge/film, 주광·BlitzUBO2 동적광·SH·환경반사·그림자, 안개·최종색 순서다. `0x71036b35c0`의 RGBA writer와 UBO writer는 기존 판독을 재사용한다.

웹의 동일 draw 재질 후크 순서:

```text
actual FresMaterial + actual geometry/texture resolver
  applyHoian: 원본 material calc, UV, Trm/backlight, under-film, team colors
  applyForward: 공통 SH/동적광/그림자/안개와 안정된 shader anchor
  applyCharacterMaterial: 네 선택 재질의 ordinary 소비자
  await binding.ready: 실제 필수 texture handle 확인
  onBeforeCompile: MAi/Thc/2cl/AO sample → surface 수정 → lighting 소비
  매 draw: 현재 light RGB·alpha, 동적광 RGBA, 시선/법선 소비
```

`applyCharacterMaterial`은 `nativeForward`를 요구한다. HOIAN material, forward surface, forward lighting의 정확한 marker가 없으면 compile 단계에서 throw한다. 부분 문자열이 우연히 비슷하다는 이유로 다른 조명 위치에 삽입하지 않는다. 원본 Scene/Actor/NVN frame 순서를 이 후크 순서로 확정하지 않는다.

## 4. 구조체·필드·상수·열거형 표

다음은 기존 원본 FRES [데이터]와 이번 실제 네 GLB 기본값 재검사다. 재질 애니메이션 뒤 런타임 값이라는 의미는 아니다.

| 필드 | 몸·얼굴 | 오징어 | 머리카락 | reader |
|---|---:|---:|---:|---|
| `enable_taransmission` | True | True | True | 소비자 선택, 원본 철자 유지 |
| `enable_cheap_sss` | True | False | False | MAi.R wrapped mask |
| `enable_transfilm` | False | True | True | film 소비 |
| `transmission_rate` | .3 | .5 | .4 | tau |
| `scattering_rate` | .2 | 1 | 1 | edge angular lobe |
| `scatter_distance` | .2 | 0 | 0 | wrap 분모/분자 |
| `scattering_color.rgb` | (.78,.46,.44) | (1,1,1) | (1,1,1) | 주광·동적광 wrapped RGB |
| `edge_transmission_power` | 1.2 | 1 | 1 | edge power |
| `film_transmission_rate` | 0 | .9 | 1 | film |
| `film_transmission_power` | 3.2 | .7 | 2.5 | film |
| `manual_fresnel` | 1 | .1 | .1 | film 재질의 F0 |
| `manual_fresnel_color` | white | white | white | F0 색 |
| `comp_paint_texcoord_offset` | .02 | .005 | .005 | UV 양쪽 두 sample |
| `comp_paint_norm_intens` | 1 | 1 | 1 | tangent 기울기 |
| `two_color_complement_paint_intensity` | 0 | 0 | 0 | static ordinary gate |
| `two_comp_paint_team` | 0 | 0 | 0 | static 2cl 채널 가중치 |

| 입력 | writer/자료 → shader reader → 웹 공급 |
|---|---|
| MAi.R | actual `_fm0` → body510/643–647 → `hCharMaskTex`, cheap mask |
| Thc.R | actual `_re2` → body511/799 → `hCK=1−R` |
| Trm.RGB | actual `_t0` × backlight/const/team calc → body512–514 → `hCalcTransmission.rgb` |
| under-film | resource0 + hue complement → material under_film_color → `hCalcUnderFilm.rgb` |
| CompPaint | actual `_cp0`/2cl → body425–450, face398–421 → `hCNc`, signed paint |
| AO.R | actual `_ao0` → body583, face506 → `hCAO` |
| 주광 RGB·A | 원본 MainLight/Env writer → `Env[5].rgb/.w` → `hLightColor`, live `hLightAlpha` uniform |
| 동적광 RGB·A | `BlitzUBO2` → body717–779 → `hDynColor[index].rgb/.w` |
| 지오메트리 tangent | 원본 vertex basis → 2cl 변형 normal → 실제 `tangent` attribute 필요 |

`enable_transmission`은 별개 원본 옵션이다. 이를 `enable_taransmission`과 병합하지 않는다. 수정된 경고는 새 캐릭터 소비자가 부착된 경우에만 taransmission 미소비 경고를 억제하며, 별개 옵션의 미소비 경고는 유지한다.

**정정(2026-10-03, 얼굴 AO):** 이전 r3 sampler 요약이 `_ao0`를 빠뜨렸으나 실제 body.glb M_Face의 FRES에는 `M_Face_Ao/_ao0`가 있다. 이번 얼굴1115 출력도 `cTexAO`의 R sample을 확인한다. 따라서 “얼굴 AO 리소스 없음”을 원본 결론으로 사용하면 안 된다. 코드가 실제 AO handle을 얻지 못하면 `missing`에 기록하고 ordinary 소비자 활성화를 막는다. 중성 AO를 넣어 해결로 표시하지 않는다.

## 5. 상태 전이와 전체 수명

1. 실제 재질 옵션·필드를 읽는다. 필수 파라미터가 없으면 에러이고, 실제 tangent가 없으면 진단 후 소비자를 붙이지 않는다.
2. 실제 `_re2`, `_cp0`, cheap `_fm0`, 해당 `_ao0`를 비동기 요청한다. `applyHoian`이 소비하는 `_t0`, `_re0`의 실제 handle도 준비 완료 조건에 포함한다. 가짜 회색 texture로 실제 게임 준비를 선언하지 않는다.
3. 준비 전 `hCharReady=0`이므로 기존 forward 경로를 유지한다. 모든 필수 handle이 있고 static CPIntensity가0이면 `hCharReady=1`, 재컴파일한다.
4. CPIntensity가0이 아니면 `runtime CompPaint ink branch needs native ink uniform supply`를 기록한다. 몸 잉크의 원본 분기가 연결되지 않은 상태에서 ordinary SSS를 더하지 않는다.
5. draw마다 현재 시선·법선·live RGBA light를 소비한다. film/tau는 픽셀별 조명량이고 재질 opacity나 인간↔오징어 전환 상태를 변경하지 않는다.
6. `dispose()`는 이 binding이 소유하는 hook/cache-key/진단만 복구한다. 재질·geometry·공유 texture의 소유권은 호출자에게 있다.

body/face AO는 필수다. hair 선택 프로그램에 AO sampler가 없는 경우는 shader 자체의 상수 경로이며, 누락된 피부 AO를 같은 경우로 다루지 않는다. UV selector0 이외의 필요한 sample은 이 모듈에서 미지원 진단한다.

원본 type11 material leaf, 피부·얼굴 패턴, 몸 잉크 런타임 writer, night emission writer 및 animation 수명은 이번 static 재질 공급으로 확정되지 않는다.

## 6. 계산식·조건·상세 의사코드

이 절의 식은 [판독] 선택된 원본 body5549/face1115/squid3358/hair2855 일반 분기다. 웹 권장명 N은 최종 normal-map 법선, Nv는 원본 vertex 법선, Nc는 **별도의 CompPaint 보정 법선**이다. V는 표면→눈, L은 표면→빛이며 원본 Env[23]의 반대 방향이다. `sat(x)=clamp(x,0,1)`.

```text
m = cheapSSS ? MAi.R : 0
k = 1 − Thc.R
n = sat(N·L)
wrap = sat(N·L + scatter_distance) / (1 + scatter_distance)
directRGB = (sat(n + scattering_color) * wrap * lightRGB − n*lightRGB)*m
            + n*lightRGB
q = (scattering_rate − 1)^2
edge = pow(sat(1 − (N·V)*sat(−N·L)), edge_power)
       * (q*pow(sat(max(−V·L,.001)),1/scattering_rate) − .2*q + .200000003)
       * k
film = sat(pow(sat(max(N·V,.001)),film_power)*film_rate*filmMask) * k
tau = transmission_rate * (filmEnabled ? 1−film : m)
backlightRGB = AoLight * edge * transmissionRGB * lightAlpha * tau
```

원본 film clamp 뒤에 k를 곱한다. 선택된 오징어/머리카락 일반 분기의 filmMask는1이다. film이 픽셀 alpha에 들어가는 것으로 해석하지 않는다. 주광·동적광의 backlight는 RGB가 아니라 **각 광원의 RGBA.w**를 소비한다. light RGB를0으로 바꾸고 alpha를 유지하면 backlight를 독립적으로 남길 수 있다.

```text
grad = cp(uv + (offset,offset)) − cp(uv − (offset,offset))
Nc = normalize(normalize(Nv) + tangent * grad * comp_paint_norm_intens)
team = 1 − two_comp_paint_team
c = min(cp(uv) + CPIntensity − 1, .3) + threshold
signed = max(c*(1−abs(team)), c*max(team,0), c*max(−team,0)) − threshold
b = N.y * (1 − Nc·L)
normalCorrection = sat(b*sat(signed*−7) − b + 1.16)
```

threshold는 기존 잉크 UBO21.w의 `.30000001192092896` 정적 공급을 재사용한다. 실제 static CPIntensity0과 cp∈[0,1]에서는 max channel≤threshold이므로 ordinary 분기가 유지된다. **cp의 기울기·signed 값은 여전히 살아 있으며**, 따라서 CPIntensity0이라고 `Nc=Nv`, signed0으로 놓으면 틀린다. shader 원본의 두 법선을 혼동하지 않고 실제2cl를 sample한다. runtime CPIntensity 및 ink UBO의 live 공급은 별도 미확정이다.

film 소비 순서:

```text
SH normal = mix(N, normalize(Nv), film)  // 원본대로 뒤에 다시 normalize하지 않음
diffuse = mix(existing albedo, underFilmRGB, film)
F0 = filmEnabled ? manual_fresnel * manual_fresnel_color.rgb : existing F0
direct BRDF *= sat(1−tau) * normalCorrection
backlight 별도 가산
```

selected under-film type5는 `(A+B)*C`이며, `A=resource0`, `B=my_team_color_hue_complement`, `C=under_film_color`다. 웹에서 기존 generic `mix`로 type5를 대체하거나 C를 버리던 결손을 수정했다. source5는 under-film, source58은 hue complement, selected source3은 기존 emission material calc를 연결한다. 모든 Hoian source enum을 새로 확정한 것은 아니다. 오징어의 emission texture×팀색 경로를 재사용하지만 night-emission live writer 전체는 미반영이다.

동적광은 기존 packed grid의 첫4index와 `index>=30` 종료를 유지한다. attenuation은 원본 거리 `exp2(power*log2(sat(1−invRadius*d)))`, spot이면 방향 감쇠를 추가한다. directRGB에 attenuation·BRDF·`1−tau`를 곱하고 backlight는 별도 `AoLight*edge*attenuation*RGBA.w*T*tau`다. 점광 거리0을 원본과 달리 자연스럽게 만드는 보정은 이 선택 소비자에 추가하지 않았다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

실제 body/face는 `assets/characters/Player00/body.glb`, 오징어는 `Player00/squid.glb`, 머리카락은 `parts/Har_SQD000_F.glb`의 FRES와 texture 슬롯을 사용한다. 원본/에셋/GLB를 수정하지 않았다. actual data fixture는 추출한 웹 GLB JSON 복사이며 게임 런타임용 대체 texture가 아니다.

카메라 변화는 V와 film/edge를 픽셀별로 바꾸므로 같은 캐릭터도 시선 각도에서 반사가 달라진다. 변신 모델 표시, 잠영 중 숨김, 그림자 caster 표시, `_Hlf` 교체와 cloth는 기존 별도 상태머신 문서를 따른다. 이번 material hook이 그 상태머신의 일치까지 증명하지 않는다. 발사 FX와 지형 잉크 material은 각각의 별도 consumer를 사용한다.

## 8. 다른 기능과의 상호작용

- 공통 조명이 RGB와 alpha를 독립 공급한다. hLightAlpha는 scalar 값을 복사하지 않고 `LightingState.uniforms.hLightAlpha` 동일 uniform 객체를 참조하므로 설정 변경 뒤 역광도 갱신된다.
- 공통 SH 평가에 film으로 바뀐 normal을 전달한다. shader별 재질 AO는 SH·동적광·환경반사에 적용하며, material AO를 직접광 shadow와 혼합하지 않는다.
- 직접광 shadow/projection과 AoLight는 현재 공통 shadow 어댑터를 소비한다. 원본 SPP.x/y 별도 화면-space 입력과 in_attr4.w/fade는 아직 동일 공급을 확보하지 못했다(§11).
- PMREM 및 Three 환경 BRDF는 현재 웹 어댑터다. F0/film 소비를 추가했다고 원본 prefilter cube/roundEven level/BRDF LUT가 일치한 것으로 올리지 않는다.
- 새 캐릭터 consumer는 shader source의 정확한 marker 뒤에 붙는다. marker 없으면 실패하므로 새 forward 수식 변경 시 조용히 낡은 치환을 성공 처리하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

| 모듈 | 책임 |
|---|---|
| `hoian.ts` | 선택된 color calc/source, Trm/backlight, hue complement/under-film, 안정된 material marker |
| `character_material_math.ts` | 좁은 CPU 검증용 재구현; native 실행이 아님 |
| `character_material.ts` | 실제 texture/UV/tangent 준비, native ordinary GLSL consumer, 통계·수명 |
| 공통 forward/lighting/dynamic_lights | SH·직접광/동적광 RGBA·shadow/fog 공급, 부모 작업 |
| model/player | 실제 모델별 hook 순서·await·dispose, 부모 통합 작업 |

```ts
applyHoian(mat, fres, team, tex, skipped, geometry);
applyForward(mat, fres, lighting, null);
const binding = applyCharacterMaterial(mat, fres, tex, skipped, geometry,
  lighting.uniforms.hLightAlpha);
if (binding) await binding.ready;
// 실제 준비·shader 사용을 별도로 확인
// binding.stats.textureReady / hookCompiled / ordinaryConsumer / missing
// scene 해제 때 binding.dispose(), 공유 resource는 원 소유자가 해제
```

`ready`가 resolve되었다는 사실만으로 성공 판단하지 말고 stats를 검사한다. stats에는 실제 `mat.name` 식별자도 보존한다. runtime material animation 공급 시 CPIntensity0 이외의 값을 임의로 넘겨 ordinary consumer를 활성화해서는 안 된다. 원본 ink branch suppression과 필요한 live UBO를 먼저 연결해야 한다.

실제 Lby 로딩에서 taransmission 후보가7개 발견되며 이 중 selected body/face/hair/squid4와 추가 후보3을 구분한다. 부모의 [두 번째 통합 검사](../../../analysis/port_character_r8/browser_failed_second.json)는 추가3개에 `_re2`/`_cp0` 누락, `M_Body_Fxm unavailable`, 일부 `_t0`/`_re0` 누락을 기록한다. 이3개는 textureReady=false/ordinaryConsumer=false로 기존 forward fallback을 유지한다. 일괄 “7개 원본 재질 완료”로 보고하지 않는다. 같은 검사에서 squid의 hookCompiled=0은 기본 pad로 Shift를 지워 모델을 표시하지 못한 harness 결손이므로 실제 잠영/변신 동등성의 증거로 사용하지 않는다. selected4의 실제 게임 draw 검사는 부모의 수정 harness 결과로 별도 판정한다.

## 10. 검증 코드·실행 결과·기대값

| 검증 | 결과 | 경계 |
|---|---|---|
| `node --test web/games/splatoon3/tests/character_material.test.mjs` | 6/6 PASS | 실제 FRES 네 재질 CPU hook + 독립 sanity 입력, 원본 함수 실행 아님 |
| `node analysis/port_character_r8/material/gpu_compare.mjs` | 512/512 PASS, 최대abs `1.1920928955078125e-7`, GL error0, shader/page error0 | 보완 original GLSL selected식와 웹 helper를 같은 WebGL2/SwiftShader에서 대조 |
| 실제 네 재질 shader compile/draw fixture | body/face/squid/hair 모두 textureReady=true, hookCompiled=1, finite pixel=true, GL error0 | actual FRES params를 사용하되 synthetic plane+tangent+1×1 gray texture. 실제 게임 모델/PNG 픽셀 일치 검사가 아님 |
| `npm run typecheck` (`C:\dev\splatoon3\web`) | 기존 exit0. 최신 병렬 실행은 `core/player/index.ts:315`의 `SphereQueryFilter.subMask` 누락으로 exit1, 부모 수정 확인 요청 | 캐릭터 모듈 밖 공용 물리 수정의 타입 연결 실패도 보존. 최종 whole 검사 결과는 부모 기록을 참조 |
| 얼굴1115 보완 dump | exit0, .vert/.frag/.options 생성 | 기존 emitter/원본 바이너리 재출력, 원본 GPU 실행 아님 |

512건은 실제 네 재질 파라미터×64 합성 방향/마스크/Thc×2 출력이다. mode0은 wrapped direct RGB, mode1은 edge/film/normalCorrection. original statement는 [native_functions.glsl](../../../analysis/port_character_r8/material/native_functions.glsl)에 보존했고 원본 UBO/Mat 입력 이름만 fixture uniform으로 대응시켰다. WebGL에는 해당 원본 fma를 `a*b+c`로 실행했으므로 원본 NVN fused rounding bit 일치로 표시하지 않는다. CPU helper도 JS 계산/최종 f32 변환이며 원본 f32 명령의 bit 동등성 증명이 아니다.

명시적 sanity: 몸의 N·L=0, MAi.R=1, white light에서 directRGB≈(.13,.0766667,.0733333). edge 입력 N·V=0,N·L=0,V·L=+1,Thc=0,Trm/색 예시에서 backlight≈(.01626480,.000957312,.000689472). 처음 test fixture에서 V·L을−1로 넣어 기대값과 실패했으며, 기존 원본 예시의 +1로 정정했다. 원본 방향 부호나 구현을 기대값에 맞춰 뒤집지 않았다.

초기 GPU 두 시도는 GL_INVALID_OPERATION(1282)으로 실패했다. 정수 light-grid와 기본 float shadow sampler가 같은 texture unit을 공유한 fixture 구성 결손이었다. `LightingState.configure`만으로 해결되지 않았고, 실제 `NativeShadowState` uniforms/texture를 함께 공급한 뒤 통과했다. [첫 실패](../../../analysis/port_character_r8/material/gpu_first_failure.json), [둘째 실패](../../../analysis/port_character_r8/material/gpu_second_failure.json)를 삭제하지 않았다. 실패를 원본 shader 문제로 처리하지 않는다.

2026-10-03 부모 통합 후속: 공용 query 필수필드를 정정하고 최종 전체 **304/304·typecheck/build exit0**를 확인했다. 실제 Lby12단계에서 body/face/hair/squid 네 재질의 texture ready/compile/consumer, 미지원 후보3개의 진단, shader/page/HTTP/GL 오류0을 확인했다. [통합 결과](../port/character_graphics_r8.md)와 `analysis/port_character_r8/typecheck.log`가 최종 상태다. 위 exit1과 controlled draw 경계는 당시 실패/검증 기록으로 보존한다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 현재 상태·이유 | 다음 근거/웹 반영 |
|---|---|---|
| 몸 잉크 runtime CompPaint 분기 | [미확정] 현재 actual static CPIntensity0 ordinary만 활성. type11 material animation/ink UBO live 공급 미연결 | 재질 AS writer→Mat CPIntensity/paint uniforms→ink branch. 0이 아닌 경우 consumer 비활성 진단 유지 |
| 추가 taransmission 후보3재질 | [미확정] selected4 외에 `_re2`/`_cp0` 등의 실제 리소스가 없는 variant. 현재 정확한 variant consumer로 구현하지 않았음 | 해당 FRES shader option/program 별도 판독, 실제 resource 경로 확인. 준비 상태를 통과시키기 위해 가짜 texture를 추가하지 않음 |
| 원본 SPP.x/y·fade 입력 | [미확정] shader body temp132=(1−SPP.y)*clamp(in_attr4.w+UBO36.z), AoLight=sat(1−temp132*UBO36.w). direct shadow에는 max(1−SPP.x,1−SPP.y)*같은 fade+projection. 현재 common hDynamicShadow(max채널·cascade/filter 어댑터), hAOMain을 소비 | SPP pass·in_attr4.w/UBO36 writer와 실제 화면-space resource, 별도 y/fade hook 필요. 현재 식의 입력 전체 동일로 승격하지 않음 |
| 원본 env cube·BRDF LUT·LOD 선택 | [미확정] 현재 PMREM/Three EnvironmentBRDF 어댑터. 원본 roundEven/cos 기반 level·array layer·LUT 리소스 공급 차이 | cPrefilEnvMapArray/cEnvBRDFMap 실제 데이터/UBO를 끝까지 연결 |
| source3/색 계산 enum 전체 | [미확정] 선택된 squid emission와 type5 under-film만 소비. 전체 source/type 네트워크 완료로 세지 않음 | 다른 선택 variant의 원본 명령/UBO 매핑, 현재 네 재질 범위 유지 |
| night emission 및 재질 leaf | [미확정] 기본 emission 소비와 live night/type11 적용은 별개 | 실제 AnimationState leaf/material writer, emission_intensity/night writer |
| 실제게임 화면 픽셀 동등성 | [미확정] WebGL 수식 fixture와 실제4재질 shader draw는 확보. 원본 Lby_Lobby00 동일 pose/light/camera/frame reference가 없음 | 원본 동일 프레임 capture+uniform/texture dump와 실제 웹 게임 frame pixel 대조 |
| precision/native GPU | [미확정] 원본 GPU fused FMA/texture filtering/NVN 전체 실행을 하지 않음 | 실제 native capture 또는 엄밀한 instruction-level GPU 기준. 이번 오차 허용 웹 대조를 [실행]으로 세지 않음 |

원본·에셋·impl·package·scripts는 변경하지 않았다. 웹 소스 수정은 사용자가 요청한 그래픽 반영 범위의 새 캐릭터 consumer와 선택 color calc이며, 공통 조명·실제 PlayerView 통합은 별도 부모 작업 결과와 함께 확인해야 한다.
