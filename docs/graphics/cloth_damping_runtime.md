# 머리카락 천의 감쇠 계수와 적분 (r9)

## 1. 기능 개요

2026-10-03. 고정 r7 질문 `graphics/hair_cloth.md:L63`의 `globalDampingPerSecond` 해석을 신규 원본 함수로 확정했다 [판독]+[실행]. 원본은 기본 중력/감쇠 또는 override 정보를 선택한 뒤 `(1-damping)^effectiveDt`를 Havok 자체 f32 log/exp 다항식으로 계산한다. 이는 Bend·LocalRange·충돌 전체 해소를 뜻하지 않는다.

## 2. 원본과 자료

v0 main.reloc.img. 신규 `analysis/decomp/r9_graphics/cloth_simulate_op.c`, `cloth_simulate_execute.c`, `cloth_damping_coefficient.c`, `cloth_integrate_damping.c`, `cloth_sim_instance.c`. 실행 `web/tools/r9_gfx_cloth_damping_emu.py`; 결과 `analysis/completion/r9/graphics_cloth_damping_emu.json`. 기존 `.bphcl` 값은 `hair_cloth.md §3.1/3.3`을 재사용했다.

## 3. 전체 호출 경로

world `CD3EAC` → 상태 operator vt28 → `hclSimulateOperator` vtable55134D8+28=`DC32EC` → 실제 시작 `DC32F0`. 초기 준비 vt20=`DC42A0`가 감쇠를 계산한다. 각 substep의 적분은 `DC32F0→EE41F0`이고, 그 뒤 `DC8C88/DC8FF4`에서 제약/충돌을 처리한다 [판독]. 최종 뼈까지 실행한 것은 아니다.

## 4. 데이터와 객체

| 객체 | 필드 | 의미와 근거 |
|---|---|---|
| hclSimClothInstance I | +18 data pointer | CFEE50 생성자 |
| data | +20 gravity vec4, +30 damping f32 | TAG0 OverridableSimulationInfo metadata + native D00038 |
| I | +260 override pointer | D00038가 우선 사용; 없으면 data+20 |
| I | +20 current particles, +30 previous particles, +28 count | EE41F0 |
| I | +50 cached effectiveDt, +54 coefficient | DC42A0/override setter CFFC88/reset CFFEF0 |
| I | +140 instance kind, +144 time scale | DC42A0에서 kind1이면 scale1, 나머지 +144 |
| operator | +50 config, config+28 substeps | DC42A0; 상태 override substeps가 있으면 우선 |
| data | +40 particles | mass+0, invMass+4, stride10; EE41F0 |

`.bphcl`의 감쇠 0.001은 파일별 데이터 확정이며 새 실행은 이 데이터 의미를 소비자까지 연결한 근거다. 테스트의 객체는 합성 유효 구조체다.

## 5. 수명과 분기

CFEE50는 cached dt=0, coefficient=1로 만든다. DC42A0는 새 effectiveDt가 cached dt와 같으면 coefficient를 다시 계산하지 않는다. 달라지면 +50을 갱신하고 감쇠를 다시 계산한다. dt가 바뀌는 기존 상태는 이전 위치/속도 조정 경로를 가진다 [판독]; 본 실행은 fresh cached dt=0으로 이 조정의 독립 검증을 범위에서 뺐다.

CFFC88은 gravity/damping override를 저장하며 cached dt가 0이 아니면 같은 계수 분기를 갱신한다. CFFEF0는 override를 해제하고 기본 data 값으로 돌아가 같은 계수를 갱신한다 [판독]. setter 전체는 본 harness에서 실행하지 않았다.

## 6. 정확한 식과 상수

초기 준비의 effectiveDt는 `f32(inputDt / f32(scale * substeps))`. scale은 instance kind1이면1, 그렇지 않으면 I144이며 substeps는 상태 override 또는 config28이다 [판독]+[실행]. 본래 외부 frameInfo의 최초 writer는 `cloth_frame_runtime.md §11`에 별도 미확정으로 남긴다.

계수 c:

- damping≥1: c=0.
- damping=0: c=1.
- 그 외: c=`8A63E0(f32(1-damping), effectiveDt)`.

이 helper는 log(base)→exponent 곱→exp의 별도 f32 FMUL/FADD/FSUB/FDIV 다항식이다. 일반 libc `powf`로 비트 일치를 가정하지 않는다. 전체 식과 원본 상수 비트는 도구의 독립 `pow_native_math`에 보존했다. log 계수 `3E049000,3E1163FE,3E4CD0BB,3EAAAAA8`; ln2 분할 `3EB17218,B082E308`; exp 계수 `3AB52000,3C09383F,3D2AAD87,3E2AAA19,3EFFFFFA`; log2e `3FB8AA3B`, 범위 `42B170A4/C2AEA8F6`를 사용한다. 음수 damping 또는 dt도 임의 clamp하지 않는다. damping=.001, effectiveDt=f32(1/60)의 c bits는 `3F7FFEE8`이다 [실행].

EE41F0의 각 vec4 lane은 다음 순서다. F는 각 연산 후 f32 반올림이고, 합성 힘0에서 검증했다.

```
dt2 = F(dt * dt)
accel = F(F(force + F(gravity * mass)) * invMass)
delta = F(c * F(current - previous))
new = F(F(current + delta) + F(dt2 * accel))
previous = old current
```

질량과 역질량을 중력에서 미리 약분하지 않는다. 실제 입자의 mass/invMass는 f32라 반올림 경로가 달라질 수 있다. 고정 입자의 이전 위치 일치는 상위 스킨/보간 경로에 의존하며 이 함수가 감쇠항을 invMass0으로 별도 제거하지 않는다.

## 7. 캐릭터 연결

Har_SQD000의 hcl 데이터와 operator 이름/순서는 기존 §3에 있다. native Simulate operator에서 머리/척추 collidable의 변환 갱신 `D01B38`을 적분 앞에 호출한다. 그 세부 변환/충돌을 실행하지 않았으므로 capsule 및 지형 접촉 전체는 미확정이다.

## 8. 다른 기능과의 상호작용

CullFrame은 외부 incomingDt를 period 배율로 바꾸고, instance row48은 월드에 들어가기 전에 추가 배율을 곱한다. hcl operator는 이후 time scale/substeps로 effectiveDt를 나눈다. 각 계층의 scale을 하나로 임의 약분하지 않는다. 감쇠는 substep마다 이 effectiveDt에 맞춘 계수를 사용한다.

## 9. 웹 반영 필요

`impl/render.md`, `impl/assets.md`: 기존 감쇠의 추정 표기를 원본 consumer 근거로 갱신하고, coefficient의 경계 분기·native f32 polynomial·중력 mass/invMass의 곱셈 순서를 반영해야 한다. dt의 최초 공급자, 제약/충돌/최종 포즈는 별도 미확정으로 유지한다. 웹 코드는 수정하지 않았다.

## 10. 실행 검증

`PY web/tools/r9_gfx_cloth_damping_emu.py` 성공. 원본8A63E0 helper 4096건, DC42A0 계수+EE41F0 적분 1024건, f32bits mismatch0, LR종료. helper는 독립 log/exp 식, 적분은 독립 vec4 식으로 대조했다. substeps1~4, kind1/2, scale.5/1/2, dt 양수/음수, damping0/.001/.5/1/1.2/음수, 입자1~9(벡터4개 묶음과 잔여1~3)를 포함했다.

SDK math stub 없음. 명시적 fixture는 scratch allocation/free, force count0/profiler null의 합성객체, nn::util ReferSymbol no-op이다. 최초 검사에서 ReferSymbol 맹글링을 EPKc로 허용하여 assertion 실패했고 실제 EPKv로 정정했다. 계산 비트 대조는 그 전에도 통과했다. 상태 override 및 최종 제약/충돌은 제외했다.

## 11. 남은 근거와 다음

L63 감쇠 식 질문은 전체 해소다. `hair_cloth.md:L79`의 감쇠+Bend+LocalRange 복합 질문은 감쇠 부분만 해소하며 **whole 확정으로 계수하지 않는다**. 다음은 constraint vt38의 Standard/Bend/LocalRange 연산, frameInfo 최초 writer, capsule transform 및 뼈 보간이다.
