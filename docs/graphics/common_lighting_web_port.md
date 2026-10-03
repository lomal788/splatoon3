# 공통 환경광 SH 웹 반영 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

사격장 벽·바닥·플레이어·총의 간접광을 같은 SH 계수로 공급한다. 기존 웹의 `LightProbeGenerator`는 선형 큐브 면 텍셀에 입체각 가중치를 주었다. 원본 `IrradianceCubeMapAllToSH`는 **sin으로 만든 각도 방향을 같은 가중으로 투영하고 7개 RGBA 출력에 가산**한다 [판독]. 이번 웹은 이 투영식을 WebGL2에 연결했다. 입력 큐브의 전체 원본 내용과 NVN GPU 비트 동일성은 [미확정]이다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 / `Lby_Lobby00`. [stage_rendering §5.6~5.6.1](stage_rendering.md), [dynamic_lighting](dynamic_lighting.md), `analysis/notes/SHARED.md`·`FUNCS.tsv`·`decomp_index.py`의 기존 결과를 먼저 확인했다. 기존 함수 `0x71010325d4`와 `0x7101034608`의 명령 분석을 다시 한 것으로 세지 않는다. 포팅 fixture를 위해 원본 실행만 128회 추가했다.

새 판독은 색인에 없던 **0x710103289c**의 투영 변형 선택이다. `analysis/decomp/port_common_r5/sh_projection_reader.c`에 보존했다. 셰이더 근거는 `analysis/r5_gfx_stage/proc/IrradianceCubeMapAllToSH__CUBE_MAP_WIDTH_INT-128.{vertex,pixel}.glsl`이다. 원본·키·GLB·에셋은 변경하지 않았다.

## 3. 진입점과 전체 호출 흐름

```text
RenderView.load → MapView.load → LightingState.configure
  → 기존 원본 startup directional SH·MainLight·bake·spot rig 공급
  → LightingState.capture (일반 프레임 draw 잠시 보류)
    → CapturePos, 256²×6 RGBA16F, CubeCamera near4/far1024
    → sky capture exposure80 + 웹 stage 렌더
    → CubeSHProjection: 98304 points → 1² RGBA32F attachment7 가산
    → attachment별 readback → packReadbackSH → hSH 7vec4
    → 웹 PMREM → scene.environment
    → 위 캡처 두 번, 두 번째 SH 유지
  → ordinary frame 재개, stage/player/knownFX는 같은 hSH 참조
```

원본 near4/far1024·256²·두 번째 SH 선택은 기존 [판독]이다. native IlluminateEnvMap draw·큐브 재질 변형·prefilter12layer는 이 웹 흐름으로 전체 재현되지 않았다.

## 4. 구조체·필드·상수·열거형 표

| 원본 writer/reader | 웹 대응 | 값/수준 |
|---|---|---|
| `103289c`, 입력 texture의 `+0x30` ushort | projectionWidth | 입력 너비를 `>>1`; 256이면128 branch [판독] |
| `103289c`, 입력 texture-view `+0xaa` byte → UBO | sourceMip | 원본 필드 판독. live 값은 미확정; 웹 mip1을 명시적 정책으로 사용 |
| `103289c`, mipCount `+0x39` | point count | width를 `min(mipCount-1,1)`만큼 shift해 `6*W²`; 이번 웹은 6*128²=98304 |
| pixel program width128 | 균일 투영 가중 | C0=3.606069e-5, C1=6.24589666e-5, C2=.000139662312, C20=(.00012095132,-4.03171071e-5), C22=6.9831156e-5 [판독] |
| `10325d4`, 7 readback texel | hSH 28float | K0=.28175688/K1=.32534343/K2=.07875311/K3=.27280876/K4=.23625931/K5=.13640438 [실행] |
| `10325d4` output23 | hSH[5].w | **texel5.w*K3**. texel6.w로 바꾸지 않음 [실행] |
| output27 | hSH[6].w | 1 [실행] |

위 오프셋은 함수에 전달된 texture/view 객체 기준이다. gsys scene/env manager 오프셋과 혼용하지 않는다. 낮은 너비 분기의 디컴파일 `0xf` 비교는 이번128 branch 확인에서 해석하지 않았으며 임의16으로 정정하지 않았다.

## 5. 상태 전이와 전체 수명

초기 SH는 기존 원본 startup 식이다. 첫 큐브/SH를 얻은 뒤 두 번째 큐브가 첫 SH와 웹 PMREM를 소비한다. 마지막 hSH를 유지하고 매 프레임 재캡처하지 않는다. 캡처 중 main 프레임 draw를 보류하여 비동기 readback과 shadow/post가 renderer 상태를 덮어쓰지 않는다.

캡처의 finally는 hidden actor·sky exposure·target·viewport/scissor·tone/autoClear를 복구한다. 투영 실패 시 오류를 남기고 가장 최근 유효 SH를 유지한다. 첫 캡처 전 실패라면 startup 값이다. 해제 때 projection target7·geometry/material·cube/PMREM를 dispose한다.

## 6. 계산식·조건·상세 의사코드

width128의 선형 sample id에서 `j=id&16383`, `face=id/16384`다. `a=sin(((floor(j/128)+.5)*.703125-45)*.0174532924)*1.41419995`, `b=sin((((j&127)+.5)*.703125-45)*.0174532924)*1.41419995` [판독]. 면0~5는 각각 `(-1,a,b)/(1,a,b)/(b,-1,a)/(b,1,a)/(b,a,1)/(b,a,-1)`이고 normalize한다.

큐브 `textureLod(direction/maxAbs(direction),sourceMip)`의 RGB에 0·1·2차 SH 항을 곱한다. `sh_projection.ts`의 7 output은 원본의 raw texel 순서다. 모든 point는 한 texel에 그려지고 7 attachment는 `ONE+ONE` 가산한다. 원본은 instanceID, 웹은 동일한 sample id를 vertexID로 공급한다.

CPU packing은 f32 곱·뺄셈의 순서를 보존한다. 원본 reader는 float/half exponent0을 signed0으로 만든다. 원본 fixture는 해당 변환을 거친 입력이며 packer만의 검증이다. GPU sin/FMA·블렌드 누적 순서·readback 형식은 브라우저 드라이버와 NVN 사이의 비트 동등성을 주장하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

MapView와 PlayerView의 Hoian forward, 이미 연결된 knownFX shader는 같은 `LightingState.uniforms.hSH` 객체를 참조한다. 새 팀색 행이나 캐릭터 SSS·잉크 normal을 임의로 추가하지 않는다. 큐브에는 캡처용 하늘 노출80, 일반 화면에는4를 사용한다. 큐브 카메라와 플레이 카메라의 near/far는 별개다.

## 8. 다른 기능과의 상호작용

동적 그림자·FX scene depth·HDR 최종색 패스는 캡처 종료 후 일반 프레임에서 실행한다. 원본 bake·격자광원·높이/깊이 fog를 유지했다. `scene.environment`의 웹 PMREM/Three BRDF는 기존 경계이며 native12layer specular를 이 SH 변경으로 해결했다고 하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

`sh_projection.ts`는 native angular projection/CPU packing/target 소유, `lighting.ts`는 startup·cube2회·공유 uniform, `render/index.ts`는 main draw 보류/재개를 맡는다. GPU에 `EXT_color_buffer_float`, `EXT_float_blend`, draw buffers7 이상을 요구한다. 지원하지 않으면 오류를 기록하고 유효 SH를 유지하며 임의의 다른 투영식으로 성공 처리하지 않는다.

## 10. 검증 코드·실행 결과·기대값

| 실제 실행 | 결과/경계 |
|---|---|
| `python web/tools/common_sh_port_emu.py` | 원본 packer128회, helper도 실제 실행, 스텁0, f32 3584bit 전부 일치. fixture=`tests/fixtures/common_sh_native.json` |
| `node --test games/splatoon3/tests/common_lighting.test.mjs` | 3/3: 원본 packer fixture·paint hook 보존·native forward shadow 중복 방지 |
| `node analysis/port_common_r5/browser_verify.mjs` | 실제 Lby cube2회/projection2회, attachment7·98304sample, SH 유한값, console/page/HTTP/GL 오류0 |
| 독립 constant-cube GPU fixture | RGB(.25,1,2)→6축 평가, 등방 입력 대비 최대 절대차 .004759193. 웹 float 가산 누적 결과이며 원본GPU 비트 검사 아님 |
| `npm test`, typecheck/build | 전체252/252, 타입/빌드 PASS. 통합 결과 [common_render_r5](../port/common_render_r5.md) |

`sh_projection_reader.c`는 `sh full_decomp.sh`가 PATH상 sh 없음으로 실패한 뒤, 같은 QuickDecomp를 기존 Ghidra 프로젝트 readOnly로 직접 호출해 얻었다. 최초 JAVA user.home 디렉터리 부재 실패도 `analysis/port_common_r5/commands.md`에 보존했다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 남은 것 | 이유/다음 위치 |
|---|---|
| native live cMipLevel | texture view+0xaa의 실제 producer/frame 필요; 웹 mip1과 구분 |
| native cube 내용·SaturationInEnvMap .4 | 큐브 재질 변형/원본 live frame, EnvMapIlluminator `1037098`의 활성 자원·행렬 필요 |
| original GPU SH | native 7MRT 원시 texel 및 같은 입력·누적/frame readback 필요 |
| specular environment | native12layer GGXPrefilterEnvMap·BRDF(-roughness)·layer12 bias0의 실제 생산/선택 연결 필요 |
| framebuffer 전체 동일성 | 동일 Lby/시점/팀색/칠mask/frame의 original capture 필요 |

원본 고정 inventory와 GR05/GR10 전체 상태는 유지한다. 원본 투영식을 옮긴 것과 입력·결과 전체 확정은 다르다.


### 2026-10-03 r6 정정·후속

위 §11의 SaturationInEnvMap .4 미연결은 [common_lighting_r6](common_lighting_r6.md)의 cube27 완전키 판독·웹 연결로 해소했다. 화면용25와 캡처용27을 구분하며 웹21 RGB32F검사·최대차.0000159153를 기록한다. 최종 native cube/Illuminate/mSun/mip/12layer/BRDF와 originalGPU전체는 여전히 미확정이다. 과거 결론을 삭제하지 않는다.
