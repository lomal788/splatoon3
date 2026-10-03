# 공통 그림자 — native PCF·캐스케이드·거리 페이드, 2026-10-03 r6

## 1. 기능 개요와 사용자에게 보이는 동작

플레이어·무기의 현재 pose에서 만든 깊이 그림자를 직접광에 공급한다. r5의 고정 4점 커널·1.5 이하 제외·20 이상 두 번째 캐스케이드 선택을 새 원본 근거에 맞춰 정정했다. 원본 PCF 변형은 **1/4/9/16회 비교 texture 호출**이며, 다점 커널의 폭은 투영 깊이와 `pcfWidth`에도 비례한다 [판독]. 캐스케이드 경계 비교는 엄격한 `>`이므로 깊이20은 첫 캐스케이드에 남는다 [판독].

웹은 원본 `Default/default.baglshpp`의 `is_PcfShaderType=0 / is_PcfSampleNum=0 / pcfWidth=5`를 공급해 한 번 비교한다 [데이터]. 같은 리소스의 far fade는 **true·40..60**으로, 생성자 기본 false·100..1000과 다르다. 생성자 기본값을 웹에 공급하던 r6 중간 결과를 리소스 데이터로 정정했다(2026-10-03). 로비 실제 런타임 리소스 선택·추가 override 경로와 원본 GPU sampler의 내부 필터·border, light camera-fit, 화면 SPP RT 전체는 [미확정]이다. 이번 결과를 원본 화면의 픽셀 동일성으로 승격하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0, `Lby_Lobby00` 1인 연습 범위다. 원본은 읽기만 했다.

- 기존 생성자: `analysis/decomp/r8_graphics/render_shadow_manager.c`, `0x7103762450`.
- 기존 cascade 설정 writer: `analysis/decomp/r8_graphics/projected_shadow_creation.c`, `0x710374C50C`.
- 새 CPU writer: `analysis/port_common_r6/common_producers.c`, `0x7103750740`; `draw_native.c`, `0x7103764908 / 3764C28 / 37631D0`.
- caller 원본 명령: `analysis/port_common_r6/shadow/caller_374f510.asm.txt`, `0x710374F510`.
- 원본 shader: `analysis/r6_gfx_char/agl_resource/agl_technique_shdw.sharcb`, `shadow_pre_pass`, 총576 매크로 조합 중12개 pixel/vertex 변형을 이번에 덤프했다. 전체576개를 실행·판독한 것이 아니다.
- 새 근거·실행: `analysis/port_common_r6/shadow/native_probe.json`, `raw_audit.json`, `prepass/v*.pixel.{glsl,bin,control,meta.json,ops.txt}`.
- 원본 Default 리소스: `analysis/render/env/Default/default.baglshpp`; 정확한 offset·CRC·f32 bits·SHA256은 `analysis/port_common_r6/shadow/default_shadow.json`. `Default/day/defaultday.bgsdw`도 대조했으나 ShadowPrePass parameter object는 없다.

분석 전 `SHARED.md`, `FUNCS.tsv`, `decomp_index.py`, `func_lookup.py`로 재사용 여부를 확인했다. 374C50C/3762450/0FA6FD4는 기존 decomp를 재사용했다. 3751A78은 새 함수 시작이 아니라 **3750740의 내부 주소**다. 379B200 전체 decomp는 reduced-color RT producer였고, cascade 경계 consumer로 추천한 기존 주소 연결은 맞지 않았다.

## 3. 진입점과 전체 호출 흐름

1. `3762450`이 `aglshpp / ShadowPrePass` 객체를 초기화한다. CRC32 이름30개 parameter와 ShadowPrePass 객체 이름을 복원했다 [실행, base/allocator helper2 BL sink 명시].
2. `374C50C`는 gsys 설정의 cascade near 값을 manager의 `boundary[0..count-1]`에 쓰고 `boundary[count]=far`로 쓴다 [판독, 기존 근거 재사용].
3. `3750740`은 shader length `i`에 **`boundary[i+1] - optionalOffset`**을 쓴다. 길이 배열과 camera projection near를 혼동하지 않는다 [판독].
4. `374F510` caller는 RenderContext `+0x18`이 가리키는 camera frame의 `+140/+144`를 near/far 인자로 읽어 `3764908`에 전달한다 [판독]. 해당 far는 cascade config의60을 직접 읽는 코드가 아니다.
5. `3764908`은 매트릭스·카메라 파라미터·pcfWidth·두 far fade 파라미터를 frame `+1418..1428`에 기록한다 [실행].
6. `3764C28`은 count·filter selector·static/depth-to-normal/SSAO/NLD 조건을 조합해 shader를 선택하고 frame 값들을 Common UBO로 옮긴다 [판독]. 이번에 실행한 것은 selector 일부 명령 블록이며 전체 GPU draw는 실행하지 않았다.
7. native prepass pixel shader는 view 위치를 복원하고 cascade를 선택해 비교 texture를 읽는다. `SPP.y=visibility+farFade`이며 결과를1로 제한하지 않는다 [판독].
8. Hoian_UBER는 `max(1-SPP.x,1-SPP.y)`로 동적 occlusion을 소비한다. 별도 `clamp(viewZ+BlitzUBO0[36].z,0,1)` 인자도 있으며 이 producer의 live 값은 아직 미확정이다 [기존 판독 재사용].

## 4. 구조체·필드·상수·열거형 표

| 기준 객체·필드 | 원본 의미/기본값 | writer → reader | 수준 |
|---|---|---|---|
| ShadowPrePass `+468` | `is_enable=true` | 3762450 → 3764908/3764C28 | [실행] |
| `+508` | `pcfWidth=5.0` | 3762450 → 3764908 `frame+1418` → Common `+2F0 cShadowBias` | [실행]+[판독] |
| `+5C8` | `is_useFarFade=false` | 3762450 → 3764908 | [실행] |
| `+5E8/+608` | 생성자 `dynamicShadowFarFadeStart/End=100/1000` | 3762450 → 3764908(enabled 분기만) | [실행] |
| `+628/+648` | static start/end=100/1000 | 3762450 → 3764908 | [실행] |
| `+7E8/+808` | `is_PcfShaderType / is_PcfSampleNum=0/0` | 3762450 → 3764C28 `3768940..895C` | [실행] |
| frame `+141C/+1420` | dynamic fade start/multiplier | 3764908 → 3764C28 → Common `+2F4/+2F8` | [실행]+[판독] |
| frame `+1424/+1428` | static fade start/multiplier | 3764908 → Common `+2FC/+300` | [실행]+[판독] |
| depth manager `+318` | boundary array pointer, `[1.5,20,60]` for Common/count2 | 374C50C → 3750740 reads `[i+1]` | [판독]+[데이터 재사용] |
| Common `+250 vec2` | `cInvDepthShadowTexSize=pcfOffset/width,height` | 3750740 frame producer → prepass pixel | [판독] |
| Common `+270 vec4` | `cDepthShadowLength=[20,60,...]` for count2, optional offset0 | 3750740 → pixel strict comparison | [판독] |
| Common `+2E4/+2E8` | cNear / cFarMinusNear | 3764908 → prepass position reconstruction | [실행]+[판독] |
| SPP `.y` | dynamic visibility + clamped far fade | prepass shader → forward .xy max consumer | [판독] |

Default `.baglshpp`의 30개 parameter CRC가 생성자에서 복원한 이름과 전부 일치했다 [데이터]. 차이는 다음과 같다. 여기의 AAMP offset은 파일 내 데이터 offset이며 객체 필드 offset과 구분한다.

| 리소스 parameter | ctor 기본값 | Default 값 / AAMP offset | 수준 |
|---|---|---|---|
| `is_useFarFade` | false | true / `0x13C` | [실행]+[데이터] |
| dynamic/static fade start/end | 100/1000 | 40/60 / `0x148 / 0x14C` | [실행]+[데이터] |
| `is_useStaticDepthShadow / is_useDecalAo / is_useFarDepthTest` | false | true / `0x13C` | [실행]+[데이터] |
| `is_farDepthTestDist` | 1000 | 60 / `0x14C` | [실행]+[데이터] |
| `is_PcfShaderType / is_PcfSampleNum / pcfWidth` | 0/0/5 | 0/0/5 / `0x140 / 0x140 / 0x144` | [실행]+[데이터] |

정적 깊이·decalAO·farDepthTest 플래그가 true인 데이터는 확인했지만 해당 전체 RT 경로를 이번 웹 구현에서 완성한 것은 아니다.

`depth_shadow_pcf_offset=.5`와 `pcfWidth=5`는 **서로 다른 객체의 값**이다. `.5/1024`만 사용해 고정 커널을 만드는 식은 원본의 다점 커널과 다르다. 생성자 기본값을 로비의 live override로 취급하지 않는다.

## 5. 상태 전이와 전체 수명

native `is_enable=0`이면 CPU writer/draw가 조기 반환한다. frame index가 count 범위를 벗어나면 index0 frame으로 되돌아간다 [실행]. `is_useFarFade=0`은 shader far fade 기여를 완전히 삭제하는 상태가 아니다. CPU가 `start=cameraFar, mul=1`을 공급한다 [실행].

웹 depth target·현재 pose proxy·실패 시 stale texture 방지는 [common_shadow_web_port.md §5](common_shadow_web_port.md)의 수명을 유지했다. `configure(raw)`는 웹에서 사용 중인 Default 환경 리소스의 far fade true·40..60을 공급하고, `capture`는 원본 writer 식대로 매 프레임 fade 값을 갱신한다. false 설정을 명시하면 camera.far·mul1 분기도 보존된다. `configurePrePass`는 확인된 native settings를 공급할 확장점이며 ctor 기본값·리소스 값·live selection의 구분을 보존한다. 원본에서 division-by-zero가 가능한 start=end 설정은 웹 공급 API에서 거절한다. 이 검증 거절은 웹 입력 보호이며 원본의 추가 clamp로 기술하지 않는다.

## 6. 계산식·조건·상세 의사코드

### cascade consumer [판독]

```text
length[i] = boundary[i+1] - (optionalOffsetEnabled ? offset : 0)
positiveViewDepth = -viewZ
CASCADE_TYPE1: layer = int(depth > length[0]) + int(depth > length[1])
Common/count2/offset0: length[0]=20, length[1]=60
depth=20 → layer0; depth>20 → layer1; depth>60 → layer2
```

CASCADE_TYPE0은 단일 행렬/layer0, type1은 두 경계, type2는 세 경계를 가진다. CPU count2→type1, count3 이상→type2다 [판독]. type1 shader에는 layer2 선택도 있으므로 **native array의 layer/border 동작을 별도로 확정해야 한다**. 웹은 마지막 cascade 밖의 visibility1을 명시적 adapter 정책으로 남겼다. 1.5는 first cascade camera-fit near 설정이며 receiver shader의 lower cutoff가 아니다.

### PCF selector·sampling [실행 블록]+[판독]

```text
SHADER_TYPE = (is_PcfShaderType==1 && unsigned(is_PcfSampleNum)<3)
              ? is_PcfSampleNum+1 : 0
q = shadowMatrix * reconstructedViewPosition
uv=q.xy/q.w; ref=clamp(q.z/q.w,0,1)
offset = ref * cShadowBias * cInvDepthShadowTexSize
kernel0: compare(uv,ref)                         // 1 call
kernel1: average grid x/y ∈ {−.5,+.5}          // 4 calls, weight .25
kernel2: average grid x/y ∈ {−1,0,+1}          // 9 calls, weight f32 .11111111
kernel3: average grid x/y ∈ {−1.5,−.5,+.5,+1.5}// 16 calls, weight .0625
```

원시 SASS의 comparison texture 명령은 `Tex`, `Dc=True`, `Dim=Array2d`이며 12개 선정 변형에서 1/4/9/16 call 수를 교차 확인했다. 이는 texture-call 수다. NVN sampler가 한 call 내부에서 선형 비교 필터를 몇 texel로 수행하는지는 이 숫자만으로 알 수 없다.

### fade writer·SPP consumer [실행]+[판독]

```text
if useFarFade:
    start=f32(dynamicStart)
    multiplier=f32(1 / f32(f32(dynamicEnd)-f32(dynamicStart)))
else:
    start=f32(cameraFar)
    multiplier=1
SPP.y = kernelVisibility + clamp((depth-start)*multiplier,0,1)
dynamicOcclusion = max(1-SPP.x,1-SPP.y)
```

SPP.y의 마지막 가산에는 clamp가 없다. visibility1+fade.5는 SPP.y1.5다. clear/default SPP.x1을 소비하면 occlusion0이므로 음의 occlusion으로 직접광을 밝게 하지 않는다. 웹 `hShadowPrePass`는 raw .xy를 반환하고 `hDynamicShadow`가 같은 max 소비를 수행한다. 별도 BlitzUBO0[36].z near fade 값은 미확정이어서 새 임의값으로 채우지 않았다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

깊이 proxy의 skeleton·morph·alpha/displacement 계약은 r5를 유지했다. 변경한 shader/CPU 소비는 그래픽 전용이다. 음향·탄·도색·물리 데이터를 수정하지 않았다. native shader asset 자체도 변경하지 않았다.

원본 프리패스는 linear depth와 view ray에서 view 위치를 복원한다. 웹은 동일한 receiver의 world 위치를 이미 가진 forward shader에 light matrix를 바로 적용하는 adapter를 사용한다. screen-space SPP RT의 해상도·depth-to-normal·static shadow/SSAO/reduced blur를 새로 구현한 것은 아니다.

## 8. 다른 기능과의 상호작용

AO·베이크·dynamic·projected 그림자는 직접광 occlusion에 합성한다. SH·환경광 전체에 그림자곱을 적용하지 않는다. stage/player shader와 generic receiveShadow shader는 같은 shadow uniforms를 공유한다. `hDynamicShadow` 계약이 visibility이므로 기존 forward 연결은 유지된다.

로비 ProjShadow Density0은 기존 원본 dual-clamp·texture gate 계약을 유지한다. 전체 렌더 순서·현재 target 복원·FX scene-depth와 post 연결은 [../port/common_render_r5.md](../port/common_render_r5.md)의 통합 구조를 따른다.

## 9. 웹 포팅 구조와 구현 순서

`games/splatoon3/client/render/shadows.ts`에 `NATIVE_SHADOW_PREPASS_DEFAULTS`, 별도 `NATIVE_SHADOW_PREPASS_DEFAULT_ENV`, `nativeShadowShaderType`, `nativeShadowFarFade`, `configurePrePass`, `hShadowPrePass`를 추가했다. Default 리소스의0 selector는 단일 비교이고 `configurePrePass`에서 확인된 selector를 공급하면 4/9/16 커널이 동작한다. offset에 ref depth·pcfWidth를 곱한다.

캐스케이드 선택은 `depth<=20`에서 첫 map이며 1.5 미만을 잘라내지 않는다. projection ref depth는 clamp0..1한다. 설정을 받은 `capture`는 CPU writer 계약대로 Default fade `[40,f32(1/20)]`를 만든다. 아직 원본 array 밖 texture·border 정책과 NVN sampler 내부 비교는 웹 nearest adapter임을 `WEB_SHADOW_POLICY`에 남겼다.

웹 원본-like screen SPP RT는 다음 단계다. 추가 producer가 확인되면 native view matrix·length/fade·sampler 상태·ray/depth RT를 함께 공급해야 한다. 부분 PCF 확인을 전체 renderer 확정으로 올리지 않는다.

## 10. 검증 코드·실행 결과·기대값

`native_probe.py`가 **whole 3764908 1,024건 / output8float bit PASS 1,024·FAIL0**을 확인했다. enabled877건은 호출되는 순수 원본3×4 matrix inverse `0FA6FD4`도 실행했으며 producer에는 stub이 없다. disabled147건은 원본 조기 반환을 실행했다. enabled/disabled·frame index fallback·far fade on/off·pcf bias 및 정적/동적 fade를 비교했다. ShadowPrePass ctor는 base helper2 BL을 명시적으로 skip하며 CRC·기본값 기록만 [실행] 범위다. 전체 원본 생성 시스템·GPU 검증이 아니다.

selector `3768940..895C`는 synthetic data/register를 공급한 **원본 명령 블록24건 PASS**이다. `raw_audit.py`는 선정12 pixel 변형의 comparison opcode 수 **12/12 PASS**를 확인했다. 역번역은 기존 Negate/CB1 수정 translator를 재사용했고 원시 bytecode는 변경하지 않았다.

Node `common_shadow.test.mjs + common_shadow_r6.test.mjs` **17/17 PASS**. 신규 JS fade helper는 enabled877건의 original output start/mul와 f32 bits가 일치했다. Default 리소스 fixture를 추가해 ctor false 값·리소스 true 값의 구분 및 capture의 `[40,f32(1/20)]` 공급을 검증했다. typecheck exit0. 초기 기존 테스트1개가 WEB_SHADOW_POLICY comment 삭제 때문에 실패했다(11/12); 남은 adapter 정책 comment를 실제 GLSL에 유지한 뒤16/16 통과했고, Default fixture 추가 뒤17/17 재실행 통과했다.

Edge SwiftShader WebGL2의 **최종 synthetic GPU25/25 PASS**. 실제 웹24casters/23SkinnedMesh를 두1024² depth target에 그려 near966/far108개의 depth-color pixel 기록을 확인했다. 기본 kernel0/bias5 및 **Default fade `[40,0.05000000074505806]`** 공급이 일치했고 shader failure·GL/page/HTTP 오류는 모두0이다. warnings2는 검사 ReadPixels GPU stall 성능 메시지다. alpha discard·stale texture·projection gate·strict20 경계·near cutoff 제거·projectedZ clamp·rawSPP.y>1 보존·1/4/9/16 커널 readback을 검증했다. 결과는 `analysis/port_common_r6/shadow/gpu_verification.json`, 화면은 `actual_shadow.png`이다.

처음 ctor 기본 falsefade 상태에서 검증한 GPU25건도 통과했지만 이때 fade[2000,1]은 Default 리소스 값이 아니었다. `gpu_ctor_verification.json`에 당시 결과를 보존하고 Default 리소스 공급 뒤 재실행한 결과만 최종 상태로 쓴다. 중간 재실행의 RAF callback 준비 조건15초 timeout도 `commands.md`에 기록했으며 불필요한 pending callback 대기 조건을 제거한 harness로 재실행 통과했다. 이 결과는 웹 GPU 검증이고 NVN GPU 실행이 아니다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 이유·시도·다음에 볼 곳 |
|---|---|
| 로비 live gsys/ShadowPrePass resource 선택 | ctor 기본값·Default AAMP override·draw selector를 각각 확인했으나 Scene+1C0/config resource-selection producer 및 추가 live override 선택 미확정. `gsys.bgmsconf` 전체 dump와 Default/default.baglshpp CRC 대조를 수행함 |
| native sampler filter·compare·border와 array layer2 | 37631D0 sampler bytes247..24B 및 white border 설정은 읽었으나 NVN API enum 소비가 미확정. 1033F0C/35B7A30/3596xxx sampler writer와 depth array376B398 |
| light camera-fit/projection·bias NVN 대응 | 두 web orthographic fit와 WebGL polygonOffset5/.3은 adapter. native cascade per-frame matrix producer `374F640 / 374F950 / 376A848` |
| full screen SPP RT/pass order·SSAO/static/reduced blur | 3764C28 decomp와 default 변형은 확인했으나 전체 frame draw 및 active variation capture는 미실행 |
| BlitzUBO0[36].z near fade | 기존1110750는 active env+1338→+7C8 값 소비, live값·원본 camera frame 대응 미확정. 별도 far fade와 혼동하지 않음 |
| 원본 화면 픽셀 동일성 | 같은 원본 NVN frame/camera/light/pose 캡처와 웹 대응 비교 미수행 |

고정 inventory 분모·전체 항목 확정 개수를 변경하지 않았다. kernel·CPU 계약 확정과 전체 renderer 완료는 별도 상태다.
