# r11 gfx-diff 후처리 — 원본·web 차등 비교 (2026-10-04)

담당 파일은 `client/render/{post,post_math,bloom,fx_depth}.ts`입니다. 방법은 `analysis/gfx_r11/DIFF_BRIEF.md`를 따랐습니다. 원본 셰이더는 역번역 GLSL을 f32 파이썬으로 실행했고, CPU 함수는 unicorn으로 실행했습니다. web은 node에서 같은 입력으로 계산했습니다. 화면 캡처는 하지 않았습니다.

## 1. 결론

- HDRCompose(노출 2.0 → 블룸 가산 → Tone4 → 8³ LUT → 감마 1)와 LUT 굽기, 블룸 mask 식은 원본과 web이 같은 값을 냅니다. 원본 사진과 web의 톤 차이(원본은 대비가 크고 따뜻하며 web은 평평하고 차가움)는 이 단계들에서 생기지 않습니다.
- 갈라진 곳은 한 군데입니다. 블룸 객체의 clamped_luminance 칸(+0x5a0)입니다. 원본 적용 함수 0x7102b699c0은 이 칸에 `lerp(old.ClampedLuminance, new.Intensity, t)`를 씁니다. 같은 함수가 다른 칸에는 같은 필드끼리 보간하는 것과 달리, 여기서는 Intensity(+0x60)를 읽습니다. 전환이 끝날 때 마지막 호출은 t=1이므로(environment_transition.md §6) 로비 값은 Intensity 1.0입니다. web은 5를 쓰고 있었습니다. 그래서 휘도 4를 넘는 밝은 화소의 블룸이 원본보다 최대 5배 강했습니다. 이것을 고쳤습니다.

## 2. 짝 목록과 비교 결과

| # | 원본 | web | 입력 | 결과 |
|---|---|---|---|---|
| 1 | `Hoian_ProcHDRCompose` 변형#201(BLOOM1·CC1·TONE4·GAMMA1·VIG0) 픽셀·정점. Negate·CB1을 보완한 CLI로 324변형 전부 다시 역번역했습니다(`analysis/gfx_r11/proc_fixed/hdrcompose/`) | post.ts 셰이더 식, `tone4()` | HDR 90표본: 회색 21단계(0~64), 잉크색 8종×8배율(0.02~8), alpha 0/0.5. 블룸 입력, 노출 2.0 | Tone4 최대차 1.6e-7, LUT 좌표 1.2e-7, 최종 8.6e-7. **일치** |
| 2 | agl `color_correction_map`(binary 41, 1988행 보완 역번역 `proc_fixed/cclut/`)을 원본 CPU 패킷(0x71035dc218 실행 836 B)으로 실행 | post_math.ts `colorCorrectionLUT`/`ccPixel` | 8×8 화소 × MRT 8 slice | 512텍셀×RGB **1536/1536 f32 비트 일치** |
| 3 | LUT 저장 형식. agl 0x1A는 NVN 63 = R11G11B10F입니다(FUNCS 0x71035b1c84, ROM 0x4ABF510) | `encodeUnsignedFloat` 최근접 짝수 반올림 | 같은 텍셀 | python 인코더와 비트 일치. GPU 쓰기 반올림 방식은 [미확정]이며, 차이는 6비트 가수 1ulp 이하입니다 |
| 4 | `bloom_mask` 변형#129(r6 보완 덤프) | bloom.ts `bloomMask`·셰이더 | 같은 90표본, clamp 5와 1 | 상대오차 2e-7 이내 **일치** |
| 5 | `bloom_gaussian` DIR0/1, `bloom_compose` STEP2 | bloom.ts 셰이더 | 식 판독 | 탭 순서·계수·오프셋(±1.3846/±3.23077), `src·cComposeColor`·alpha 0 모두 같습니다 [판독] |
| 6 | Bloom 적용 0x7102b699c0 (unicorn, 259건: 기본·t=0/.5/1·무작위) | `bloomGameApply` (신규) | t, new/old 파라미터 | 수정 전에는 +0x5a0이 불일치했습니다. 수정 후 Threshold/Range/Intensity/+0x5a0 **259/259 비트 일치** |
| 7 | edit_type(B+0x418) 분기(0x71036ed93c) | bloom.ts Expand 가중치 | 판독 | 0이면 Layer8x8/16x16/32x32Color를 쓰고, 1이면 Expand를 씁니다. 게임 적용은 +0x418을 쓰지 않으므로 DefaultDay 1 → Expand입니다. RenderingDay 층 색은 로비에서 쓰이지 않습니다. web도 같습니다 |
| 8 | 변형 선택 0x710112215c, 플래그 0x7103744058 | post.ts 고정(BLOOM1·CC1·TONE4·GAMMA1·VIG0) | r5 원본 실행 2000건씩(재사용) | 일치. GAMMA는 SystemTask+0x422, VIG는 비네트 +8에 달려 있고 둘 다 [미확정](gfx-light 기록) |
| 9 | DOF | 없음 | 데이터 | DefaultDay DepthOfFieldObj0.enable=false, RenderingDay DOFGaussian Start 484/End 900. 켜져 있어도 484 m 밖만 흐려지므로 사격장에서는 하늘에만 영향이 갑니다. master enable은 [미확정] |
| 10 | (원본 맵 셰이더 p1714 출력 alpha) | hoian `diffuseColor.a`, sky alpha 1 | 판독 | 원본도 `output_color[0].w = 1.0`입니다. 블룸 mask의 alpha 임계 차감 입력이 같습니다 |

fx_depth.ts는 FX soft particle에 깊이를 공급하는 일만 하고 색을 바꾸지 않습니다. 비교할 후처리 식이 없습니다.

## 3. 갈라진 지점의 근거

명령(0x7102b6a394, 0x7102b6a49c~4b0):

```
ldr s9, [x27, #0x30]      ; x27 = old(x2) 쪽 상속 결과 → ClampedLuminance
... x27 = new(x0) 쪽 상속 결과, 플래그 +0xa3(Intensity 것)
ldr s0, [x27, #0x60]      ; Intensity
fsub s0, s0, s9 ; fmul s0, s0, s8(t) ; fadd s0, s9, s0
str s0, [x26, #0x5a0]     ; 블룸 객체 clamped_luminance → UBO threshold.x
```

실행: `web/tools/r11_post_bloom_apply_emu.py`(vtable+0x98 getter만 합성, 설정 플래그를 모두 켜서 상속 탐색 경로는 실행하지 않음) → `analysis/gfx_r11/diff/post/bloom_apply_native.json`. t=1일 때 5→1, t=0일 때 5, t=0.5일 때 3입니다.

로비에서 이 적용이 실행된다는 전제는 web이 MainLight Intensity 10 등 RenderingDay 값을 쓰는 전제와 같습니다(stage_rendering §4).

## 4. 고친 것

- `bloom.ts`: `bloomGameApply(next, prev = next, t = 1)`를 추가했습니다. 원본 f32 순서로 Threshold/ThresholdRange/Intensity를 보간하고, ClampedLuminance는 `lerp(old.ClampedLuminance, new.Intensity, t)`로 만듭니다. `NativeBloom.configure`는 `bloomPacket(bloomGameApply(setting))`을 씁니다. `bloomPacket` 자체(agl 객체 → UBO, 기본값 5)는 원본 UBO 실행 fixture와 계속 맞으므로 바꾸지 않았습니다.
- 로비 블룸 UBO는 threshold.x 5 → 1로 바뀝니다. 나머지(weight, intensity 1, cap 10000)는 그대로입니다.

## 5. 테스트

- `tests/r11_gfx_diff_post.test.mjs` + `tests/fixtures/r11_post_native.json`(원본 GLSL 실행 출력·LUT 텍셀·mask·적용 259건): 4개 테스트.
- `npm run typecheck` PASS, `npm test` **428/428 PASS**. 기존 기대값은 바꾸지 않았습니다.
- 재현: `python analysis/gfx_r11/diff/post/cclut_bake.py` → `post_fixture.py`, `.venv/Scripts/python.exe web/tools/r11_post_bloom_apply_emu.py`. 러너는 `analysis/gfx_r11/diff/post/glsl_run.py`입니다(공용 `glsl2py.py`에 else-if·local_memory·uintBitsToFloat를 더함).

## 6. 남은 미확정

| 항목 | 영향 |
|---|---|
| LUT sampler 객체(선형 가정)·R11G11B10F GPU 쓰기 반올림 | 선형이 아니면 8³ LUT가 계단처럼 보일 것이라 선형일 가능성이 높습니다. 반올림 차이는 1ulp 이하입니다 |
| GAMMA(SystemTask+0x422)·비네트 활성 | gfx-light 기록대로 남아 있습니다. GAMMA 0이면서 sRGB 표시 버퍼여도 결과는 같습니다 |
| 블룸 live view-mask, 64 미만 viewport, STEP3 복사 대상 크기 | 기존 r6 미확정 |
| DOF master enable | 사격장에서는 하늘(484 m 밖)만 영향 |
| 로비에서 0x7102b699c0이 실제로 불리는지(전환 요청 경로) | web의 RenderingDay 적용 전제와 같습니다 |

원본 사진과의 대비·색온도 차이는 후처리 앞단(재질·광원·그림자·하늘 입력)에서 찾아야 합니다. 후처리는 같은 HDR 입력에 원본과 같은 출력을 냅니다.
