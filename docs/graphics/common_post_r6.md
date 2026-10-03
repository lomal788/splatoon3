# 공통 후처리 r6 — 원본 Bloom 생산 경로와 웹 연결 (2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

시험 사격장의 조명·잉크·캐릭터·총·이펙트가 만든 HDR에서 밝은 부분을 추출하고, 네 해상도로 흐리게 만든 결과를 역순 합성하여 최종 HDR에 더한다. 이번 작업은 이전 [공통 최종색 웹 반영](common_post_web_port.md)의 `bindBloom` 소비 계약에 **실제 mask→reduce→Gaussian H/V→compose 생산 경로**를 연결했다 [웹 구현]+[웹 실행]. 밝은 영역이 원본 기본 임계값·휘도 가중치·필터 계수로 후처리를 거친다.

원본 CPU의 UBO 명령블록 512건·Expand 명령블록 256건·blend 문자열 파서 전체 6건·compose state maker 전체 1건을 새로 실행하여 총 **775건, 불일치 0**을 확인했다 [실행]. 원본 셰이더 식·pass 순서·기본 환경 값은 [판독]+[데이터]다. 원본 NVN GPU를 실행하거나 원본 최종 프레임과 비교한 것은 아니다. 웹 GPU 검증과 원본 실행을 구분하며 `nativeGPUEquivalent=false`를 유지한다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0, `Lby_Lobby00`, 주소 base `0x7100000000`. 새 자료는 `analysis/port_common_r6/post/`에 둔다. `original/`과 키는 읽기 전용이고 웹 에셋·GLB·impl·scripts·package는 수정하지 않았다.

| 근거 | 위치·확정 수준 |
|---|---|
| 원본 CPU render·reduce H/V·compose helper·constructor | `bloom_native.c`: `0x71036ED93C`, `0x71036F1E4C`, `0x71036F2CD8`, `0x71036ECD4C` [판독] |
| 원본 shader container | `analysis/r6_gfx_char/agl_resource/agl_technique_pfx.sharcb`; `shader/`에 mask 256변형, Gaussian/compose 각 2변형, reduce 1변형 [판독]+[데이터] |
| Maxwell 명령 확인 | `gaussian_pixel.ops.json`, `gaussian_vertex.ops.json`, `mask_pixel.ops.json`; 검사한 기본 경로에는 Negate/BRX 없음 [판독] |
| 원본 UBO/Expand/parser/state maker 실행 | `native_blocks.py`·`native_blocks.json` [실행] |
| 원본 DefaultDay Bloom | `analysis/render/env/Default/day/defaultday.baglblm`; 정확한 f32 읽기 `default_bloom.py`·`default_bloom.json` [데이터] |
| 실제 웹 GPU | `browser_bloom.mjs`·`gpu_bloom.json`·`actual_bloom.png` [웹 실행] |
| 초기 생성자 분기 GPU 보고 | `gpu_bloom_ctor_branch.json`; 삭제하지 않고 최종 환경 분기와 분리하여 보존 |

기존 `SHARED.md`·`FUNCS.tsv`·`decomp_index.py`를 먼저 확인했다. 기존 `36EB47C` 파라미터 생성자·`2B699C0` game 설정 적용·`3744058` HDR flag producer·DOF writer/getter의 실행 결과는 재사용하며 이번 신규 775건에 더하지 않는다. 기본 환경 공급→로비 fallback은 [stage_rendering §2·§3.2](stage_rendering.md)의 기존 분석을 재사용한다.

## 3. 진입점과 전체 호출 흐름

```text
native DefaultDay baglblm → Bloom 생성자/파라미터 묶음
  + RenderingDay PostEffect.Bloom 기본/override (2B699C0)
  → Bloom render 36ED93C
     → Enable·view-mask·clipped viewport 검사
     → mask (기본 variant129)
     → 36F1E4C ×4: reduce → Gaussian horizontal → Gaussian vertical
     → 36F2CD8 ×3: level4→3→2→1 역순 compose
     → 최종 STEP3 복사 → game HDRCompose 가산 합성

web HDRCompose.configure(env.json)
  → 누락된 Bloom은 native game 기본값 + DefaultDay agl 기본 분기를 공급
frame → scene 공통 HDR → NativeBloom.render(16 draw)
  → HDR·exp2(EV1) + Bloom → Tone4 → native mode0 8³ LUT → gamma
```

네이티브는 Bloom 객체 `B+0x7D8` Enable과 `B+8` view-mask를 검사한다 [판독]. viewport에서 변환한 폭/높이가 64 미만이면 별도 copy 경로 후 반환한다. 원본 명령 `36EDA0C`의 f32 64, `36EDA40` FCMP, `36EDA48` FCCMP, `36EDA4C` 분기와 decompile `36ED93C`가 근거다. 웹은 하나의 전체 drawing-buffer viewport를 사용하므로 동일 기준을 전체 buffer 폭/높이에 적용한다 [웹 어댑터]. 실제 로비 native view-mask·clipped viewport를 캡처한 것은 아니다.

## 4. 구조체·필드·상수·열거형 표

**기준 객체를 분리한다.** Bloom 본체 `B`; agl param 묶음 `P=B+0x30`; view별 work `D=*(B+0x5C8)+viewIndex*0x858`다. 같은 숫자 오프셋을 서로 다른 객체에 적용하지 않는다.

| 기준·오프셋 | 필드·기본값 | writer → reader / 수준 |
|---|---|---|
| P+18 / B+48 | `threshhold` 4 | `36EB47C`, `2B699C0` → `36ED93C` UBO [판독]+[데이터]+[실행-블록] |
| P+38 / B+68 | `threshold_range` 1 | 동일 → 동일 |
| P+58 / B+88 | `intensity` 1 | 동일 → 동일 |
| P+78 / B+A8 | `finalgather` RGBA全1 | DefaultDay/`2B699C0` → reverse compose [데이터]+[판독] |
| P+A0 / B+D0 | `expand` 1 | DefaultDay → edit_type1 Expand block [데이터]+[실행-블록] |
| P+3E8 / B+418 | `edit_type` 1 | ctor/DefaultDay → Expand branch [데이터]+[판독] |
| P+408 / B+438 | `finalblend` 1 | ctor/DefaultDay → `3744058` → HDR BLOOM1 [기존 판독]+[데이터] |
| P+490 / B+4C0 | `enable_depth_clamp` true | DefaultDay → mask variant129 [데이터]+[판독] |
| P+4B0 / B+4E0 | `enable_luminance_offset` false | DefaultDay → mask 변형 선택 [데이터]+[판독] |
| P+4D0 / B+500 | `enable_clamped_luminance` true | DefaultDay/`2B699C0` → mask ratio clamp [데이터]+[판독] |
| P+4F0 / B+520 | `enable_old_calc` **false** | ctor true→DefaultDay false override → reverse compose [데이터]+[판독] |
| P+510 / B+540 | `quality` 0 | DefaultDay → 품질 분기 [데이터]+[판독]; 실제 target binding 전체 미확정 |
| P+570 / B+5A0 | `clamped_luminance` 5 | ctor/DefaultDay/game → UBO threshold.x [데이터]+[실행-블록] |
| B+5B0,+5B4,+5B8 | 정규화 Y=(.2989116907119751,.5866104364395142,.11447788774967194) | `36ECD4C` literals `3E990AFE/3F162C23/3DEA7371` 정규화 → UBO [판독]+[실행-블록] |
| D+84C | scale 생성자 1 | `36ECD4C` → UBO [판독]; live writer override 미확정 |
| B+7D8 / B+8 | Enable / view-mask | game 적용·scene → render gate [판독]; 실제 프레임 값 미확정 |

Gaussian offset는 ±1.3846, ±3.23077이고 탭 계수는 .31621623, .07027027, .22702703이다 [판독]. 이름으로 추정한 Gaussian sigma를 새로 만들지 않았다.

**NVN blend enum 명명 근거** [판독]+[데이터]+[실행]: `36BC8F0` 원본 문자열 파서는 `zero→0`, `one→1`, `const_color→10`을 반환한다. material 파서 시작 `36BB5A4`의 내부 블록 `36BBEA0`가 쓰는 원본 표 `0x7104AC0A00`에서 index1은 2, index10은 0x61이다. 내부 주소를 함수 시작으로 세지 않는다. `36F351C` 실행 결과 state+28은 `0x61610202`이며, `3588FCC`는 byte28/2A/29/2B를 변환 없이 `nvnBlendStateSetBlendFunc`에 전달한다. `3588FCC`는 `FUNCS.tsv:561`·SHARED paintgpu의 기존 판독을 재사용하여 새 분석으로 세지 않는다. 함수포인터 이름은 원본 loader `83EB80` 기반 `paintgpu_nvnmap.py`의 `57D5BF0`/`57D6110` 근거를 썼다. 외부 enum 이름이나 웹 GPU 성공만으로 NVN 숫자를 확정하지 않았다.

## 5. 상태 전이와 전체 수명

웹 `configure`는 활성 scene 유무, native Enable, depth-scaling/offset 여부 및 UBO finite 여부를 검사한다. 기본 로비 경로의 depth scale/offset은 false다. 미구현 depth 변형을 공급하면 임의 식으로 처리하지 않고 Bloom 생산을 비활성화한다. native clipped viewport 64 gate를 전체 buffer 어댑터에 적용하며 inactive frame은 Bloom binding을 해제한다.

HDR scene을 그린 뒤 해당 프레임 texture로 Bloom을 생산한다. mask 1장·level 4장·scratch 4장의 RGBA16F target은 객체가 소유하고 resize 시 재사용하며, compose마다 source/destination과 다른 scratch target을 쓰고 swap한다. 같은 texture를 동시에 읽고 쓰는 feedback alias를 만들지 않는다. dispose에서 모든 target·material·geometry를 해제한다 [웹 구현].

외부 `bindBloom(texture,mode)` 계약은 configure 또는 `bindBloom(null)`까지 유지되고, 수동 binding 중에는 내부 producer가 덮어쓰지 않는다. null을 주면 다음 frame부터 native 기본 producer가 공급한다. draw 실패에서도 render target·toneMapping·autoClear·default viewport/scissor/scissorTest를 finally로 복구한다. 기존 render target에는 그 target 소유 region을 다시 적용한다. 외부 코드가 GL API로 직접 바꾼 임의의 active viewport 복구까지 확인한 계약은 아니다.

## 6. 계산식·조건·상세 의사코드

원본 CPU UBO 블록은 다음 **f32 순서**다 [실행-512건].

```text
den=f32(scale * ThresholdRange)
inv=(den<=0) ? 0 : f32(1/den)
weight.rgb=f32(inv * normalizedY.rgb)
weight.w=f32(f32(scale * f32(-Threshold)) * inv)
threshold=(f32(inv*ClampedLuminance), 0, Intensity, 10000)
```

기본 scale1/Threshold4/Range1/Clamp5에서는 weight.w=-4, threshold.x=5다. **Clamp5는 RGB를 5로 자르는 값이 아니다.** RGB safety cap은 10000이고, 5/L의 비율을 포화하는 데 사용한다.

```text
h=texture(source,uv)
c=min(h.rgb,10000)
L=fma(c.b,weight.b,fma(c.g,weight.g,c.r*weight.r))
gain=sat(threshold.x/L) * sat(fma(h.a,weight.w,L)) * threshold.z
out=(c.rgb,h.a)*gain
```

mask는 raw HDR **alpha를 임계값 차감에 사용**한다 [판독]. 실제 frame alpha 의미/공급이 달라지면 추출 결과도 달라진다. `BLM_LUMINANCE_CLAMP=0` 원본 변형은 RGB min10000을 유지하고 `sat(threshold.x/L)`만 생략한다. 웹 shader·CPU reference도 이를 구분한다. 기본 DepthClamp1 변형129와 비교변형1은 pixel 512B·vertex 256B bytecode가 각각 완전히 같다 [데이터]; 현재 기본 macro 조합에서는 별도 depth sampler를 추가하지 않는다.

Gaussian은 각 reduce destination 크기의 역수로 offset을 정규화하여 H→V 순서로 소비한다 [판독]. 탭 순서를 보존한다.

```text
a=sample(uv-1.3846*step) * .31621623
a=fma(sample(uv-3.23077*step), .07027027, a)
a=fma(sample(uv), .22702703, a)
a=fma(sample(uv+1.3846*step), .31621623, a)
out=fma(sample(uv+3.23077*step), .07027027, a)
stepH=(1/width,0); stepV=(0,1/height)
```

reduce는 1회 texture sample의 RGBA 전달이다. 원본 STEP2 compose는 source RGB×`cComposeColor.rgb`, alpha0을 출력한다. helper는 source color의 RGB×A를 UBO에 쓰고 destination color의 RGB×A를 `SetBlendColor`에 공급한다. blend ONE/CONST_COLOR에 의해 `src*sourceRGBA.rgb*sourceRGBA.a + dst*destinationRGBA.rgb*destinationRGBA.a`가 된다 [판독]+[실행-state]. 웹은 blend state 대신 두 texture를 다른 target에 읽어 동일 식을 직접 계산한다 [웹 어댑터].

edit_type1 Expand는 [실행-256건]이다. x=f32(Expand); a=f32(3*x); b=f32(a-1); x>=f32(1/3)이면 a=1, 아니면 b=0; inv=f32(1/f32(f32(a+1)+b)); weights=(inv,f32(a*inv),f32(b*inv),f32(0*inv)). 기본1은 (.25,.25,.5,0)이다. 음수·경계값도 임의 clamp로 자연스럽게 바꾸지 않는다.

기본 DefaultDay `enable_old_calc=false`의 역순 compose는 다음과 같다 [판독]+[데이터]. 모든 finalgather RGBA가 1이므로 평탄한 mask 입력을 보존하는 계수 합은 **1**이다.

```text
L3 = L4*0 + L3*.5
L2 = L3*1 + L2*.25
L1 = L2*finalgather.rgb*finalgather.a
   + L1*.25*finalgather.rgb*finalgather.a
```

원본은 4 정렬 후 1/4 mask를 만들고 1/8,1/16,1/32,1/64를 생성한다. 예시 1001×563 → 251×141 mask → 125×70 → 62×35 → 31×17 → 15×8이다. native mip-target 경로도 있으나 웹은 독립 target 경로만 이식했다. native 최종 STEP3 복사(alpha0)는 웹의 최종 HDR shader texture 소비와 합쳤다. 따라서 **웹 producer는 16 draw**이고 이 숫자를 native 전체 draw 수라고 쓰지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

Bloom은 인간/오징어·발사·착탄·잉크 표면·stage·하늘을 모두 그린 공통 HDR를 사용한다. 재질별 색상이나 이펙트 emitter를 새로 조정하지 않았다. alpha가 mask에 영향을 주므로 upstream FX/캐릭터/stage의 render-target alpha 계약은 별도 원본 분석과 대조해야 한다.

`env.json`의 로비 RenderingDay에는 Bloom 블록이 없다. 웹 데이터 어댑터는 원본 game `Bloom` 생성자 기본 Enable=true/Threshold4/Range1/Intensity1/Clamp5/ComposeRGBA1과 agl DefaultDay의 edit_type1/old_calc=false/expand1/finalblend1을 공급한다. **DefaultDay→로비 fallback의 기존 근거를 재사용한 공급**이며 런타임 로비 env construction·active view 값을 실행으로 캡처한 것은 아니다. 에셋을 임의 수정하여 Enable을 만들지 않았다.

## 8. 다른 기능과의 상호작용

mask 입력은 수동 노출 EV1을 곱하기 전 scene HDR다. Native per-view scale은 생성자1 분기를 선택했으며 live writer가 바꾸는지는 미확정이다. 후속 game HDRCompose는 `HDR*2 + Bloom` 뒤 Tone4→CC LUT→조건부 vignette→gamma를 소비한다. LUT·노출·Bloom을 재질마다 중복 곱하지 않는다.

DOF는 별도 pass다. 기존 visitor `119E29C`의 +40 필드는 master `Enable`이 아니라 **IsEnableFarCancel**이었다. [renderparam_runtime §4·§11](renderparam_runtime.md)에 2026-10-03 정정 이유를 남겼다. 기존 writer 1,024건/getter 4,096건은 typed packet의 바이트 결과 증명이며 master enable 증명이 아니다. DefaultDay `DepthOfFieldObj0.enable=false`는 [데이터], 실제 Lby gate와 DOF shader 소비는 [미확정]이므로 임의 blur를 켜지 않았다.

## 9. 웹 포팅 구조와 구현 순서

`client/render/bloom.ts`는 UBO·Expand reference, native 기본 shader, target 수명, 생산 순서 및 상태 복구를 맡는다. `post.ts`는 configure·producer·수동 binding 수명과 최종 HDR 소비를 맡는다. 기존 `post.target/material/size/exposure/gamma` 인터페이스는 유지한다. 다른 담당자의 render/index·lighting·forward 파일은 여기서 수정하지 않았다.

분리해야 할 웹 정책은 RGBA16F transport, Linear min/mag, ClampToEdge, mip생성 없음, 0휘도 finite guard다. native RCP(0)/SAT/NaN 행동을 캡처하지 않아 웹 black-limit를 0으로 처리했으며 원본 GPU 비트 동일성으로 주장하지 않는다. WebGL FMA contraction·half 저장·native format/sampler 차이가 남는다. DOF/vignette/gamma의 미확정 활성값을 이번 Bloom 구현으로 해결된 상태로 승격하지 않는다.

다음 구현 근거는 native sampler/target format·live per-view scale·HDR alpha 공급·original GPU readback이다. 그 뒤 DOF master enable/producer shader를 추적한다. 원본 inventory 분모를 줄이거나 넓은 최종픽셀 질문 전체를 이 부분 결과로 완료 처리하지 않는다.

## 10. 검증 코드·실행 결과·기대값

| 실제 수행 | 결과·경계 |
|---|---|
| parent `full_decomp.sh` Bloom 4함수 포함 batch | exit0, `bloom_native.c`·`bloom_decomp.log` 보존. 같은 batch의 환경맵 2함수는 다른 담당 영역 |
| `decomp_index.py --no-build <주소>`·`func_lookup.py <주소>`·`disasm.py -n ...` | 기존 결과 확인 후 start 검증; raw 판독 근거 보존 |
| Negate/CB1 수정된 기존 shader dump CLI `prog-sharc` | mask256/Gaussian2/compose2/reduce1 추출 exit0 |
| `dotnet build analysis/port_common_r6/post/raw_dump/dump.csproj` + raw dump·Maxwell decoder | raw binary/control 확보; build 경고0·오류0; 기본 Gaussian vertex/pixel·mask 명령에서 Negate/BRX 없음 |
| `python analysis/port_common_r6/post/native_blocks.py` | UBO512+Expand256+native 파서6+state maker1=775, 바이트/반환 불일치0, 산술·call stub 없음. 입구 register/객체는 합성 fixture; NVN upload/draw/view-gate 제외 |
| `python analysis/port_common_r6/post/default_bloom.py` | exact AAMP f32·CRC·source SHA256; DepthClamp129/1 pixel512B·vertex256B 동일 |
| `node --test web/games/splatoon3/tests/bloom_common.test.mjs web/games/splatoon3/tests/post_common.test.mjs` | **20/20 PASS**. native fixture·환경 분기·mask alpha·10000cap·target 해상도·16draw·disable·exception 복구·수동 binding 수명 |
| `npm --prefix web run typecheck` | PASS |
| `node analysis/port_common_r6/post/browser_bloom.mjs` 최종 DefaultDay 분기 | Edge WebGL2/SwiftShader, HDR색6×alpha3=**18/18 PASS**. RGBA16F Bloom 최대오차 .0005807876586914062; 최종색 최대0byte; 128texel Gaussian impulse 최대 .000026304348250336118. console/page/HTTP/GL 오류0 |
| 실제 Lby scene | Bloom 4frame/64draw; sizes160×90/80×45/40×22/20×11/10×5. 공통조명 SH captures2, GL0. SH는 다른 담당자의 웹 cube 입력 경로이며 이 결과로 native capture를 확정하지 않음 |

GPU fixture의 평탄한 18개 입력은 mask/역순 compose/최종 HDR를 검증하며 Gaussian 공간 분포는 별도의 128×1 impulse/bilinear reference로 대조했다. 일반 scene 픽셀과 원본 screenshot의 동일성은 검증 범위 밖이다.

실패·정정도 보존했다. 첫 `spl_data.py cat <baglblm>`는 BYML이 아니어서 ValueError → AAMP 정확 읽기로 전환. 기존 `gfx4_aamp.py`는 표시용 6자리 반올림이 있어 port 값에는 쓰지 않았다. `disasm.py` positional count와 `--func`의 잘못된 heuristic start, wildcard 경로와 존재하지 않는 일부 read 경로 오류는 `func_lookup`·직접 `-n`·정확 경로로 교정했다. native 문자열은 `constant_color`가 아니라 `const_color`여서 xref 표기를 교정했다. 정적 CRC 해독 중 동적 byte가 등장한 ad hoc decoder는 ValueError를 반환했으며 그 실패를 필드 전체 확정으로 세지 않았다. material 내부 주소 `36BBEA0`를 시작으로 넣은 첫 Ghidra batch는 partial decompile로 보존하고, `func_lookup`의 실제 시작 `36BB5A4`로 whole 함수를 다시 요청했다. 원본 표의 raw 판독과 `36BC8F0`/`36F351C` whole 실행은 이 주소 교정과 별개로 유효하다. `git diff --stat`는 C:/dev/splatoon3가 Git root가 아니어서 exit1을 반환했으며 어떠한 git 변경도 하지 않았다.

**2026-10-03 정정:** 처음에는 ctor `enable_old_calc=true`를 적용해 평탄한 Bloom 합이 .75인 웹 branch를 검사했다. exact AAMP CRC `enable_old_calc=0x2745FA65`를 확인하니 DefaultDay는 false였다. 웹을 false로 바꾸고 최종 GPU 보고를 새로 저장했다. 초기 보고는 `gpu_bloom_ctor_branch.json`으로 이름을 바꾸어 보존했다. 이번 최종 값은 ctor만으로 로비 설정을 확정한 결과가 아니다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 이유·시도·다음 근거 |
|---|---|
| native live Enable/view-mask/clipped viewport | render 명령 gate는 읽었지만 실제 로비 register/object snapshot 없음. `36ED93C` 입구·B7D8/B8·viewport 공급 caller runtime 추적 |
| D+84C live scale | ctor1/UBO 식 실행만 확보. depth scale/offset 및 per-view updater writer/runtime 값 추적 |
| native format/sampler/mip 경로 | 독립 target 식·연산은 확보, NVN target format·bound sampler·mip branch 전체 연결/실제 binding 미수집. `36ED93C` target construction·sampler binding→NVN submit 추적 |
| GPU 정밀도·RCP0/SAT/NaN | patched GLSL과 원본 Maxwell 명령은 읽었으나 original GPU readback 없음. 현재 half transport·black finite guard는 웹 정책 |
| 실제 HDR alpha 의미 | mask의 alpha 차감은 확정, upstream scene/FX alpha blend 및 clear alpha 실제 frame값은 미확정. 공통 HDR attachment writer/clear/blend와 pixel capture 대조 |
| native 최종 STEP3 target contract | 식은 RGB copy/alpha0이나 원본 resource alias·resolve/native draw 수 전체 계약 미확정. 후속 HDRCompose texture binding/submit 추적 |
| DOF master enable·GPU 소비 | FarCancel 오명명 정정, DefaultDay disable 데이터와 typed writer/getter만 확보. `35E553C`·secondary VT5729690 render reader·env DOF apply·shader 추적 |
| output gamma/vignette/live CC mode | 기존 후속 미확정 유지. [common_post_web_port §11](common_post_web_port.md)의 writer/runtime/NVN LUT bake 근거 필요 |
| 원본 최종 프레임 동일성 | 웹 GPU 합성 검증만 수행. 동일 Lby 시점·팀색·HDR alpha·장면상태·frame의 원본 HDR/Bloom/최종 readback 비교 필요 |

이번에는 Bloom 기본 수학·pass producer와 실제 웹 GPU 소비를 연결했으며 전체 그래픽·공통 후처리·고정 inventory 전체 완료로 승격하지 않는다.
