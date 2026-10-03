# 공통 최종색 웹 반영 — ColorCorrection 8³ LUT (2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

시험 사격장 바닥·인간/오징어·총·탄·이펙트가 만든 HDR를 한 후처리로 소비한다. 이전 웹은 노출×2→Tone4→출력 gamma1만 연결했다. 이번에는 **Tone4 뒤에 로비 ColorGrading의 HSV→8점 RGB 곡선→Gamma1로 만든 8³ LUT**를 연결했다 [웹 구현]. 재질마다 채도 배율을 넣지 않는다.

원본 CPU packet/곡선 표본은 기존 [실행]+[판독]+[데이터] 근거를 재사용한다. CPU LUT 생산과 웹 GPU 소비는 [재구현]+[웹 실행]이며, 원본 GPU bake/readback과 픽셀 동일성을 확인한 것은 아니다. 별도 공통 조명·그림자 작업의 구현을 이 문서의 LUT 검증으로 승격하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 `Lby_Lobby00`. 근거는 [ink_lighting_r2 §3~§6](ink_lighting_r2.md), [reference_hdr_output §4~§6](reference_hdr_output.md), [stage_rendering §2.2.1·§3](stage_rendering.md), [renderparam_runtime §4~§5](renderparam_runtime.md)다. 기존 `SHARED.md`·`FUNCS.tsv`와 함수 색인에 등록된 결과를 재사용했고 새 원본 함수를 디컴파일하거나 실행한 것으로 세지 않는다.

기존 원본 실행 결과 `analysis/visual_gap_r2/light/cpu_packet.json`을 테스트 fixture `tests/fixtures/post_native_port.json`으로 필요한 부분만 옮겼다. 원본 파일·키·웹 에셋·GLB·impl 문서는 바꾸지 않았다. 임시 결과는 `analysis/port_common_r5/post/`다.

## 3. 진입점과 전체 호출 흐름

```text
기존 native: 35DB354 mode0 → 115567C 로비 공급 → 35DC218 packet
              → shader41 GPU LUT bake [이번 원본GPU 실행 없음]
웹: RenderView.load → HDRCompose.configure(env.json)
     → colorCorrectionPacket → colorCorrectionLUT → Data3DTexture(8×8×8)
프레임: HDRCompose.render → 공통 RGBA16F HDR target
        → 노출(+공급된 Bloom) → Tone4 → LUT → 조건부 비네트 → gamma
해제/재설정: 이전 LUT dispose → 새 LUT 또는 비활성 → 리소스 dispose
```

기존 `post.target`, `material.uniforms.hdr/exposure/gammaMode`, `size`, `exposure`, `gamma` 필드는 보존했다. 전체 게임 core·이동·탄 로직은 바꾸지 않는다.

## 4. 구조체·필드·상수·열거형 표

| 원본/웹 계약 | 공급→소비 | 현재 상태 |
|---|---|---|
| native header `(0,0),(6,1),(1,10)`, count3 | 기본 mode0→packet 재구현 | 기존 [실행-CPU]·웹 native fixture 대조 |
| param0 `(Hue0,S1,V1.0625,0)` | 로비/default 값→HSV | 기존 [데이터]+[실행] |
| param1..8 RGB, param9 끝 RGB 복사 | Hermit2D reader→8점 선형 보간 | 기존 [실행]; RGB 24값 비트 일치 |
| param10 `(1,1,1,1)` | native 기본 Gamma→CC 마지막 연산 | 기존 [실행]; 출력 gamma와 별개 |
| N8, scale .875/bias .0625, level1 | allocator→LUT 소비 | 기존 [판독]+[실행-명령블록] |
| RGB11/11/10 unsigned float bit폭 | format table→LUT 저장 양자화 | bit폭 [데이터]; rounding은 아래 웹 정책 |
| `ccPacket/ccLUT`, `ccEnabled/colorLUT/ccCoeff` | configure→actual HDR shader | [웹 구현]+[웹 실행] |
| `bloomMode/vignetteMode` | 명시적 texture/uniform 공급→조건부 합성 | 실제 로비 초기값0; 미확정 값을 만들어 켜지 않음 |

`ccPacket.params[*].w`의 곡선 A는 RGB LUT에서 사용하지 않는다. A 표본 전체를 원본 비트 동일 계약으로 보고하지 않는다.

## 5. 상태 전이와 전체 수명

ColorGrading.Enable=true이고 R/G/B가 유효한 증가 X의 Hermit2D일 때만 LUT를 만든다. 데이터가 없거나 형식이 다른 경우 비활성으로 두고 `stats.ccReason`에 이유를 남긴다. 새 configure는 이전 GPU texture를 해제하고 CC 상태와 선택적 Bloom/비네트 공급을 초기화한다.

프레임마다 HDR를 만든 뒤 동일 최종색 shader를 한 번 그린다. scene 그리기 또는 compose 그리기가 실패해도 `finally`에서 이전 render target과 toneMapping을 복구한다. renderer의 기존 출력 설정에 별도 three toneMapping/color-conversion chunk를 추가하지 않아 수동 출력 gamma가 중복 적용되지 않는다.

## 6. 계산식·조건·상세 의사코드

```text
CPU packet = [HSV0/S1/V1.0625, native Hermit2D RGB 8samples, 마지막 복사, Gamma1]
for X,Y=0..7: R=X*f32(1/7), G=Y*f32(1/7), B=0
  for Z=0..7:
    c=HSVminChannel(R,G,B) → sampleCurveRGB(clamp(c)*7) → exp2(log2(abs(c))/Gamma)
    texel=quantizeRGB11_11_10(c)
    B=f32(B+f32(1/7))
final: HDR*exp2(EV1) → native Tone4
       → texture3D(LUT, c*.875+.0625) → optional vignette → output gamma
```

HSV는 min-channel tie 순서, delta<1e−5 gate, `fract(f32(fma(Hue/360,h)+1000))`를 유지한다. 따라서 Hue0/S1에서도 HSV를 단순 RGB×Value로 바꾸지 않는다. 예를 들어 순수 파랑의 f32 hue wrap에는 작은 R 잔여가 생기며 이번 웹 LUT에서도 지우지 않았다. CC Gamma1의 exp2/log2 연산을 identity라는 이유로 목록에서 제거하지 않았다.

**명시적 웹 정책** `CC_WEB_POLICY`: RGB11/G11/B10의 exponent5·mantissa6/6/5를 CPU nearest-even으로 양자화하고, 값이 정확히 표현되는 RGBA16F로 전송한다. min/mag Linear, ClampToEdge, mip생성 없음(level0)이다. 이는 native sampler numeric min5/mag1/wrap7의 기호 의미와 live override가 해소됐다는 주장이 아니다. native 채널 packed byte 순서를 확보했다는 주장도 하지 않는다. GPU FMA/특수함수 반올림·NVN 저장 반올림은 미확정이다.

비네트 소비식은 [stage_rendering §3.1](stage_rendering.md)의 ellipse/square, .8716/.5625 및 range 계수를 연결했다. `setVignette`에 명시적 검증 값이 공급될 때만 켜진다. 로비 live 값이 없어 0을 유지한다. Bloom은 공급된 texture가 있을 때 원본 가산/휘도 가중 합성식을 소비하는 `bindBloom` 계약만 제공한다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

인간/오징어 전환, 발사·착탄, 바닥 도색, 하늘·베이크·동적광이 기존 scene에 만든 HDR는 같은 LUT를 거친다. LUT를 개별 material/teamColor에 곱하지 않는다. 기존 `env.json`을 읽으므로 새로운 색 에셋이나 스크린샷에서 추출한 보라/노랑 상수는 추가하지 않았다.

## 8. 다른 기능과의 상호작용

노출 EV1→2배와 Tone4는 유지하고 ColorGrading.Value1.0625는 LUT **내부 첫 HSV 연산**에서 처리한다. 팀색 Ink/InkBright 공급, 바닥 반사·normal, 캐릭터 SSS, FX색·alpha는 upstream 계약이므로 LUT만으로 해당 미확정을 해결했다고 하지 않는다.

Bloom은 로비 RenderingDay에 블록이 없어 native 생성자 기본 Enable=true/Threshold4/Range1/Intensity1/Clamp5를 `stats.nativeBloom`에 기록했다. **알려진 활성 입력이 있다는 사실과 실제 mask/reduce/gaussian/compose GPU 식이 구현됐다는 사실은 다르다.** DOF는 로비 Level.5/Start484/End900/FarCancel20이지만 native shader와 live Enable이 미확정이라 임의 blur를 추가하지 않았다.

## 9. 웹 포팅 구조와 구현 순서

구현 파일은 `client/render/post_math.ts`와 `post.ts`다. post_math는 native-executed Hermit2D를 재사용하고 기본 CPU packet·HSV·8³ 격자·양자화·검증용 linear sampler reference를 맡는다. post.ts는 데이터 texture 소유권·shader 합성·렌더 상태 복구를 맡는다. 공통 render/index·lighting·forward는 별도 담당 작업이며 수정하지 않았다.

다음 순서는 native NVN sampler live 의미/rounding 확보→nativeGPU LUT readback 대조, 그 뒤 Bloom/DOF의 원본 shader 복원과 실제 enable/pass-order 연결이다. 임의 광원/채도/blur로 남은 차이를 채우지 않는다.

## 10. 검증 코드·실행 결과·기대값

| 실제 명령 | 결과/경계 |
|---|---|
| `node --test web/games/splatoon3/tests/post_common.test.mjs` | 11/11 PASS. native CPU fixture 재사용·24 RGBbits·헤더/HSV/Gamma/count, 512texel quant/half transport, linear center/edge, configure/release, draw 실패 상태복구 |
| `npm run typecheck` | PASS |
| `node analysis/port_common_r5/post/browser_gpu.mjs` 최종 | exit0. actual post WebGL2 knownHDR readback36/36, 최대0byte 오차. CC off/on×gamma0/1/2×HDR색6, alpha.75 보존. console/page/HTTP 오류0·GL0 |
| 첫 post.ts delete/add patch | apply_patch 중복 대상 오류, 파일 변경 없음. Update File patch로 정상 적용 |
| 첫 테스트 | 10/11; 순수 파랑 R=0 기대가 native f32 hue 잔여를 지워 실패. 근거 식과 실제값 확인 후 작은 R 잔여 보존 검사로 정정 |
| GPU fixture 초기2회 | MSAA clear 뒤 resolve누락→모두0, 이어renderer clear의premultipliedAlpha .75→RGB축소로실패. empty render resolve 및rawGL knownHDR RGB/alpha공급으로교정. production post.render 소비식은바꾸지않음 |
| 세번째 GPU 전체scene | post36readback 최대0B, 각gl0. 동시공통shadow MeshStandardMaterial 주입의plain i가threeunroll뒤남아shader컴파일실패;부모에게보고. post통과와scene전체통과를분리 |
| 최종 실제scene/SH 캡처 | 부모가shadow 주입을UNROLLED_LOOP_INDEX로교정한후전체scene오류0. actuallighting captures2·projectiondraws2·7 RGBA32F attachments·98304 samples, raw28값finite/음수SH보존. 이것은웹큐브입력이고원본NVN 캡처확정은아님 |

기존 원본 CPU 실행을 이번 신규 native 실행으로 합산하지 않는다. 테스트 통과를 전체 framebuffer 원본 동일성으로 확대하지 않는다. commands·실패·GPU fixture는 `analysis/port_common_r5/post/`에 둔다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 남은 이유/다음 근거 |
|---|---|
| native LUT texel·저장 반올림 | NVN shader41·actual UBO·RGB11/11/10 original GPU bake/readback 필요 |
| native sampler live 의미 | 3591834 numeric min/mag/wrap 의미와 CC bound sampler·override/submit 추적 필요. 웹 Linear/Clamp 선택과 구분 |
| actual mode/reload/active variant | 이번은 기본 mode0. 35DE4A8/35DF17C 런타임 변경·scene 연결 필요 |
| gamma live bit | scene+523c/+5239 writer/runtime 값 미수집. gamma1은 기존 웹 선택 유지 |
| 비네트 live 값 | HDR 문맥+300의 enable/shape·param/color/start/range producer와 실제 로비값 필요 |
| Bloom/DOF 생산 | 로비 데이터/생성자·typed writer만 확보. native GPU mask/reduce/gaussian/compose/DOF와 활성/pass 순서 필요 |
| 원본 최종 픽셀 | 동일 Lby·시점·팀색·mask·frame의 native/웹 HDR·최종 frame 대조 필요 |

원본 inventory 분모와 넓은 그래픽 질문 상태를 이 부분 이식으로 바꾸지 않는다.

2026-10-03 r6 후속: 위 Bloom 소비 계약에 원본 mask·reduce·Gaussian H/V·reverse compose producer를 연결했다. DefaultDay `enable_old_calc=false`·DepthClamp1 기본 분기와 신규 원본 실행 775건, 웹 GPU 18개 HDR/alpha·128texel impulse 검증은 [common_post_r6](common_post_r6.md)에 정리했다. 위의 r5 "Bloom 생산 미연결" 설명은 당시 상태로 보존한다. DOF visitor +40은 master Enable이 아니라 FarCancel이며 [renderparam_runtime §11](renderparam_runtime.md)에 정정했다. native GPU 동일성·live gates·sampler/format·DOF master enable 미확정은 계속 남는다.
