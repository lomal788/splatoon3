# 공통 그림자 웹 반영 — 2026-10-03 r5

## 1. 기능 개요와 사용자에게 보이는 동작

플레이어 등 동적 캐스터의 그림자를 카메라가 보는 두 구간에서 생성해, 베이크 AO·그림자와 함께 **직접광 감쇠**에 공급한다. 기존 단일 `1024² / ±6 / bias −0.0005` 그림자에서 두 개의 `1024²` 깊이 텍스처로 전환하는 소비 모듈이다. 이 문서는 구현 및 웹 검증 기록이다. 원본 GPU 화면과 동일하다는 판정은 아니다.

원본 설정 값은 [실행]+[데이터]+[판독] 근거를 재사용했다. 캐스케이드 구간 해석, 카메라 적합 방식, PCF 커널과 API 바이어스 대응은 `WEB_SHADOW_POLICY`라는 **웹 어댑터 정책**에 따로 둔다. 원본 미확정을 이 구현만으로 확정하지 않는다.

## 2. 원본·버전·자료 위치

Splatoon 3 v0, `Lby_Lobby00` 1인 연습이다. 원본 자료와 기존 분석은 [stage_rendering.md §3.0·§5.4·§11.2](stage_rendering.md), [projected_shadow_runtime.md §3~§6](projected_shadow_runtime.md)이다. 동적 설정 이름·오프셋은 `analysis/r6_gfx_stage/gsys_cfg_params.tsv`에 있다.

새 원본 분석이나 디컴파일을 수행하지 않았다. `SHARED.md`의 r6 그림자 설정·r8 ProjShadow 기록과 `FUNCS.tsv`의 `1152ED8 / 37AB8E0 / 3756CC8 / 374C50C`를 재사용했다. `decomp_index.py 0x7103751a78`은 “디컴파일 없음”을 반환했다. 이번 웹 반영은 기존 명세 범위이며 그 주소를 신규 원본 실행 증거로 세지 않는다.

## 3. 진입점과 전체 호출 흐름

구현은 `games/splatoon3/client/render/shadows.ts`의 `NativeShadowState`이다.

1. 생성 시 두 깊이 RT와 두 orthographic camera, 기본 흰 투영 그림자 텍스처를 만든다.
2. `configure(env.json)`은 로비 `Shadow.ProjShadow.Density`를 읽는다. 0이면 투영 그림자 기여는 정확히 0이다. 0이 아니거나 없으면 미확정 frame producer를 만들지 않는다.
3. `capture(renderer, scene, viewCamera, MainLight.direction)`이 visible `castShadow` Mesh를 선택하고, 전용 proxy scene에서 현재 pose를 깊이로 그린다.
4. 두 패스가 모두 성공한 경우만 `hShadowAvailable=1`이다. 정상/실패 모두 주 renderer의 target·viewport·scissor·clear color·tone mapping·auto clear·shadow auto-update를 복원한다.
5. 포워드 재질에서 `hDynamicShadow`의 visibility와 `hProjectionOcclusion`을 직접광 합성에 사용한다.
6. 폐기 시 소유한 RT·depth material·흰 텍스처만 해제한다. 원본 source mesh·geometry·재질·skeleton은 해제하지 않는다.

실제 map/forward/renderScene 연결과 통합 브라우저 결과는 [../port/common_render_r5.md](../port/common_render_r5.md)에 기록한다.

## 4. 필드·상수·원본 대응

| 웹 필드 | 값/계약 | 수준과 원본 writer/reader |
|---|---|---|
| `NATIVE_SHADOW_SETTINGS.cascades` | 2 | [데이터], gsys Common |
| `width / height` | 1024 / 1024 | [실행]+[데이터], `3705FEC` 이름 복원 |
| `nearValues / far` | 1.5,20,250,16 / 60 | [데이터], 경계 해석 자체는 미확정 |
| `polygonOffset / polygonScale` | .3 / 5 | [판독]+[데이터], `36C971C` 렌더 상태 복사 |
| `pcfOffset` | .5 텍셀 | [판독]+[데이터], `3751A78`가 폭·높이로 나눔 |
| `hShadowTexel` | (.5/1024,.5/1024) | 위 설정의 웹 전달 |
| `hShadowMatrix0/1` | world→light clip→[0,1] | 웹 camera-fit producer, 원본 producer 동등성 미확정 |
| `hShadowSplits` | (1.5,20,60) | `WEB_SHADOW_POLICY`, 원본 near/far 해석 미확정 |
| `hProjShadowRows[3]` | 실제 producer에서 제공한 3×vec4 | [판독]+[실행], 원본 `37AB8E0`의 target530..55F→uniform110..130 |
| `hProjShadowDensity` | clamp(factor)×clamp(Density), f32 | [판독]+[실행], `37AB8E0` target4E8/5AC→uniform1A0 |
| `hProjShadowAvailable` | count>0 && enabled | [판독]+[실행], texture slot14 gate |

2048·`Depth_32`·`R32_G32_float`는 정적 그림자 설정이다. 이번 두 동적 RT의 해상도로 오인하지 않는다.

## 5. 상태 전이와 수명

깊이 값의 초기/실패/캐스터 없음 상태는 unavailable이다. 두 패스 성공 뒤 available로 바뀐다. 다음 capture 시작에 먼저 unavailable로 돌아가므로 첫 캐스케이드만 새로 그린 뒤 두 번째가 실패해도 이전 프레임 texture를 유효한 새 그림자로 읽지 않는다.

caster가 hidden·castShadow=false·다른 camera layer가 되거나 scene에서 제거되면 proxy를 제거한다. 다시 나타나면 현재 geometry·matrix·material·morph·skeleton을 다시 연결한다. 모든 조정은 시각 전용이며 물리·플레이어 상태를 변경하지 않는다.

## 6. 계산식과 조건

### 원본 ProjShadow 필드 적용 [판독]+[실행 재사용]

`blendProjectedShadow(A,B,t)`는 Density→Rotate→Scale→Trans→ScrollAnim→RotateAnim 순서로 원본 FSUB/FMUL/FADD 결합을 전사한다.

```text
mix(A,B,t) = f32(f32(B) + f32(f32(f32(A)-f32(B)) * f32(t)))
```

t와 결과를 제한하지 않는다. 렌더 density는 이후 별도 단계에서 `f32(clamp01(factor) * clamp01(Density))`이다. 아직 로비 frame producer가 없으므로 Scale/Rotate 등의 필드로 임의 투영행렬을 만들어 연결하지 않는다.

### 동적 깊이 패스 [웹 어댑터]

view projection inverse로 두 camera depth 구간의 각 8개 corner를 world 좌표에 만든다. 주광 방향에 수직인 XY orthographic bounds는 receiver 구간을 포함한다. Z 범위에는 receiver와 현재 동적 caster의 pose bounds를 모두 넣는다. near/far .01 padding은 WebGL 카메라 slab의 퇴화를 방지하는 정책이다.

깊이는 unsigned-int depth texture, nearest로 읽는다. polygon bias는 WebGL `polygonOffset(factor=5,units=.3)`로 적용한다. 이는 확정된 설정 값을 웹 API에 옮긴 정책이며 NVN rasterizer와의 동등성은 미검증이다. 기존 receiver `bias −.0005`는 넣지 않는다.

선택은 positive view depth `1.5 ≤ z < 20`에서 near, `20 ≤ z ≤ 60`에서 far이며 범위 밖은 visibility1이다. 이는 near/far 설정의 웹 해석이다. 두 경계의 실제 native 사용 코드는 아직 판독되지 않았다.

PCF는 ±.5 texel의 네 점 nearest depth 비교를 같은 가중으로 평균한다. 원본 커널의 샘플 수·가중은 미확정이다. 이 네 점 방식을 원본 커널로 기술하지 않는다.

### 그림자 합성 [판독, 실제 texture는 웹 어댑터]

`hDynamicShadow`는 밝음=1인 visibility를 반환한다. `hProjectionOcclusion`은 `Density*(1−projectedTexture.R)`을 반환한다. 베이크 포함 원본 구조는 다음과 같다.

```text
shadow = clamp01(1 - (AO*AOMainLightOcclude + dynOcclusion + projOcclusion + bakedOcclusion))
```

원본 `cGSysShadowPrePass.xy`를 screen-space로 재현한 것은 아니다. 두 cascade 결과를 dynOcclusion 공급으로 쓰는 웹 adapter이다. 원본 viewZ+[36].z fade producer도 미확정으로 남긴다.

## 7. 모델·애니메이션·에셋 연결

proxy는 현재 source geometry를 공유한다. SkinnedMesh는 실제 skeleton과 bind matrix를 사용하며 morph influences 배열도 공유한다. 현재 pose의 정확한 vertex bounds를 사용해 bind-pose의 오래된 bounds로 그림자를 자르지 않는다.

MeshDepthMaterial은 alpha map·map·alpha test·opacity·side/shadowSide·clipping·displacement를 복사한다. shader feature가 변경되면 material을 다시 컴파일한다. source material 자체에는 polygon offset을 쓰지 않는다. 별도 원본 RT/texture 에셋을 추가하거나 GLB를 재변환하지 않았다.

특수 customDepthMaterial과 원본 GPU만의 vertex deformation는 이 adapter에서 자동 전사하지 않는다. 해당 producer가 필요한 모델이 추가되면 별도 계약이 필요하다.

## 8. 다른 기능과의 상호작용

정적 베이크 맵 receiver는 기본적으로 동적 caster에 넣지 않는다. 실제 `castShadow`를 가진 actor만 대상으로 한다. 현재 character/weapon 비anim GLB24재질에는 `gsys_dynamic_depth_shadow` 필드가 없으므로 기존 actor caster 선택을 native flag 판독으로 승격하지 않는다. 히트·탄·물리·도색 결과에는 쓰지 않으며 화면용 직접광 감쇠만 공급한다.

환경 큐브 캡처 중 shadow source의 visibility/material을 바꾸지 않는다. 본 화면 렌더 직전에 capture하여, 이펙트 scene-depth와 HDRCompose가 같은 현재 pose 결과를 보게 한다. 세부 native 패스 실행 순서는 미확정이므로 웹 순서를 원본 순서 증명으로 다루지 않는다.

## 9. 웹 구조와 연결 순서

`MapView`가 `NativeShadowState`를 소유하고 로드 시 raw env를 configure한다. 주 `DirectionalLight`는 광색·세기·방향 역할을 유지하며 castShadow를 끈다. renderScene에서 `shadow.capture → FX sceneDepth → HDRCompose`를 호출한다. stage/player의 원본 포워드 식과 기존 receiveShadow를 가진 paint/placeholder에 공통 uniforms·`SHADOW_GLSL`을 연결한다. 현재 range 표적은 receiveShadow/castShadow를 설정하지 않아 이번 caster/receiver 검사에 포함하지 않았다. 표적 GLB에도 원본 depth-shadow flag가 없어 임의로 원본 정책으로 승격하지 않았다.

`bindProjectedFrame`은 실제 matrix/factor producer가 확보됐을 때만 호출하는 확장점이다. 현재 Density0 로비는 별도 projector를 만들 이유가 없다. nonzero 씬으로 범위를 넓힐 때는 기존 unresolved 상태를 먼저 해결해야 한다.

## 10. 검증 코드와 실행 결과

`games/splatoon3/tests/common_shadow.test.mjs`의 **12/12** 웹 계약 테스트가 통과했다. 확인 범위는 다음과 같다.

- 두 1024² target/half-texel과 정적 그림자 설정의 구분.
- ProjShadow의 두 독립 clamp·f32 product 및 unclamped field extrapolation.
- Density0 exact skip, nonzero Density만으로 producer를 invent하지 않는 조건.
- count/enabled texture gate와 제공된 3개 행렬 row 보존.
- off-center view projection을 포함한 receiver corner 위치.
- 두 depth 패스와 16개 receiver corner의 light-clip 포함.
- 두 번째 패스 실패 시 stale availability 방지와 renderer 상태 복원.
- visible caster 선택, static baked receiver 제외, hidden→복귀.
- alpha/displacement/side/world transform 보존, source 재질 변경 없음.
- 실제 THREE.SkinnedMesh의 skeleton/bind/morph 배열 보존.

명령 `node --test games/splatoon3/tests/common_shadow.test.mjs`은 exit0이었다. `npm run typecheck`도 모듈 추가 직후 exit0이었다. 기존 원본 projected-shadow 실행 3,072건·creation 64건/126레코드는 **재사용 근거**이며 이번 실행 횟수로 합산하지 않는다. 이 Node 테스트는 WebGL GPU 실행이 아니다.

root 연결 뒤 `node analysis/port_common_r5/shadow/browser_gpu.mjs`을 Edge SwiftShader WebGL2에서 실행했다. 실제 웹 caster24개(23 SkinnedMesh)를 두 1024² RT에 그려 near950/far107개의 depth-color pixel 기록을 확인했고 GL 오류·shader failure·page error·HTTP failure는 각각0이었다. 별도 합성 장면에서 near/far 밝음255/그림자0·범위외255·hidden caster stale 무효화·alpha opaque0/discard255·projected R/alpha 구분·밀도 두clamp 결과64·count0/default·enabled false/default 등 **13/13 GPU readback**이 기대 byte와 일치했다. warnings2는 검사 ReadPixels의 GPU stall 성능 메시지다. 결과는 `analysis/port_common_r5/shadow/gpu_verification.json`, 화면은 `actual_shadow.png`이다. 첫10-case 실행도 통과했으며3개 projection gate case를 추가한 뒤 재실행했다.

이 검사는 현재 웹 깊이 패스·셰이더 공급을 실행한 것이다. 원본 NVN GPU·원본 실제 frame matrix/factor producer를 실행한 것은 아니다. 최종 post/SH/카메라 통합 결과는 [../port/common_render_r5.md](../port/common_render_r5.md)를 따른다.

## 11. 미확정과 추가 근거

| 남은 항목 | 원인·다음에 볼 곳 |
|---|---|
| 로비 live gsys Common 선택 | 설정 적용 포인터 producer·Scene+1C0 런타임 공급 |
| near/far 경계·캐스케이드 선택·fade | `374C50C`, `379B200`, 그림자 프리패스 shader; 현재 정책을 native로 승격하지 않음 |
| PCF sample 수·가중과 NVN/WebGL polygon bias 대응 | native depth-shadow raster/receiver shader와 실제 GPU 비교 |
| 원본 screen-space shadow .xy의 생성·패스 순서 | gsys/agl shadow prepass RT producer와 shader |
| nonzero projector frame matrix/factor | target530..55F / target4E8 writer; `projected_shadow_runtime.md`의 다음 위치 |
| actor caster 등록 및 표적 원본 shadow 정책 | character/weapon renderInfo에는 해당 flag가 없음; actor runtime shadow registration writer |
| 원본 픽셀 동일성과 시각 증감 | native GPU frame과 같은 camera/pose/light의 대응 캡처 |

분석 inventory의 확정 개수·분모를 바꾸지 않았다. 웹 적용 완료와 native renderer 완료는 별도 상태다.

### 2026-10-03 r6 정정 — 기존 r5 정책의 변경

위 §6의 경계·4점 PCF 문장은 r5 당시 웹 adapter 및 당시 미확정 상태를 보존한 기록이다. 이후 `3750740`의 length upload와 `shadow_pre_pass` 원시 shader, `3764908/3764C28` 원본 실행·판독으로 **receiver 1.5 cutoff가 없고 depth20은 첫 cascade이며, kernel selector0/1/2/3은1/4/9/16 비교 texture 호출**임을 확인했다. 다점 offset은 `clamp(projectedZ,0,1) * pcfWidth * (pcfOffset/textureSize)`다. 기존 고정±.5 texel4점 정책을 이 식과 엄격한 경계 비교로 교체했다. 원본 sampler 내부 filter·border는 별도 미확정이다.

far fade writer는 설정 false이면 cameraFar·mul1을 공급하지만, **원본 Default/default.baglshpp는 true·start40/end60**이다 [데이터]. ctor false·100/1000을 live 리소스 값으로 취급하지 않고 웹 configure에서 Default 리소스 override를 공급한다. SPP.y에는 visibility와 clamped fade를 더하며 마지막 clamp가 없다. forward는 `max(1-SPP.x,1-SPP.y)`를 소비한다 [판독].

새 11절 근거·검증 및 남은 분석은 [common_shadow_r6.md](common_shadow_r6.md)를 따른다. r5의 실제 GPU13건은 재사용 기록이고 r6 신규 원본 writer1,024건·selector24건·12개 shader raw audit·Node17개 및 후속 웹 GPU 검증과 합산하지 않는다. §11의 경계/PCF sample 수는 이 새 근거로 정정됐으며 full SPP RT·live resource 선택·actor registration·픽셀 동일성은 계속 미확정이다.
