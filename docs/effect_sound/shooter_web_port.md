# 슈터 발사·탄·착탄 이펙트 웹 반영 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

사용자가 우선순위 4를 실제 웹에 반영하도록 요청했다. 발사·메인 탄·분열 탄·바닥/벽 착탄을 같은 unlit R-mask shader로 처리하던 경로를, 확인된 프로그램별 색/alpha 소비와 VAT·프리미티브 표면 속성·이미터 렌더 설정으로 분리했다. 원본 GPU 픽셀 동등성은 주장하지 않는다.

소비자 `client/fx/`와 공급자 `client/audio/data.ts`, `assets/effects/shooter/emitters.json`을 모두 실제 반영했다. 최초 자동 승인 거부 후 사용자 명시 승인으로 적용했다. 원본 입력 계약이 부족한 shader는 기존 웹 fallback을 유지한다. 현재 상태는 [우선순위1·4](../port/priority_1_4.md)를 따른다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0, Lby_Lobby00, Shooter_Normal_00. 원본 분석 재사용: [effect_resources](effect_resources.md) §2.1.1/2.1.2/2.2.5.1, [fx_shader_inputs_r2](fx_shader_inputs_r2.md) §6, [reference_shooter_visuals](reference_shooter_visuals.md), [emitter_render_follow](emitter_render_follow.md). original과 키를 변경하거나 출력하지 않았다.

새 웹 작업/임시는 `analysis/port_priority_r4/fx_render/`. 실제 원본 데이터 fixture39개와 유한 VAT half 표본16개는 `tests/fixtures/fx_native_port.json`에 보존한다. fixture의 CPU normal 기대값은 [재구현]이며 원본 GPU 실행 결과가 아니다. 기존 원본 CPU 832조합·11개 emitter·VAT498/512 검증은 신규 실행으로 다시 계상하지 않는다.

## 3. 진입점과 전체 호출 흐름

```text
core events → FxSystem → emitter definition + sampler slots + primitive
→ ParticleBatch → particle-state RGBA32F texture
→ known program vertex (VAT/independent keys/normal) + fragment (two colors/alpha)
→ per-emitter WebGL render descriptor → scene HDR
```

`FxSystem`은 `ClientContext.fxLighting/fxDepth`의 실제 공유 uniform 객체를 받는다. scene-depth prepass와 HDR 출력은 조정자가 관리하는 `client/render/` 경로다. 해당 prepass의 정확한 원본 draw schedule은 [미확정]; 웹의 depth 공급 방식과 원본의 soft 식을 구분한다.

## 4. 구조체·필드·상수·열거형 표

| 새 consumer | 입력 | 근거·경계 |
|---|---|---|
| `particles.ts` | scale/C0/A0/C1/A1 키·개수·type와 각각의 loop/phase | native FIXED 패치 결과를 최종 def에서 소비. 실제 공급 완료·44/44 검증 |
| `render_state.ts` | `nativeRender` 또는 `render` | BD8/BD9/BDA/BDB/BDE/BDF 판독·원본 CPU setter 재사용. Boolean와 numeric 필드 모두 소비 |
| `particle_shaders.ts` | sampler0/1/2, primitive normal/tangent/color/uv1 | RGBA component selectors가 적용된 texture의 A를 읽음; R로 대체하지 않음 |
| VAT | sampler2, 원본 packed UV의 z = glTF uv1.x | 원본 `082c0a0`에서 _u0/_u1 f32x2를 vec4로 합침. 데이터 담당자의 `native_vat_binding.json`, `vat_geometry_verification.json` 2/2 [판독]+[데이터] |
| 웹 bridge | VAT rate=1, linked alpha=1, remap=(1,0), roughness=.25/Fresnel=.04 | `FX_WEB_DEFAULTS`에 명명. native producer/material 값으로 확정한 값이 아님 |

**Cull adapter 재확인:** 기존 r8 원본 CPU capture에서 Res+BDF=1→NVN CullFace2, 2→1, FrontFace는1이다. 공개된 [NintendoSDK NVN header 원문 재구성](https://code.botw.link/uking/uking/lib/NintendoSDK/include/nvn/nvn.h.html)의 enum 이름은 CullFace2=BACK/1=FRONT, FrontFace1=CCW다. 따라서 Res1→three FrontSide(뒤를 cull), Res2→BackSide(앞을 cull)가 맞다. 게임의 숫자 전달은 원본 근거, API 숫자의 이름은 외부 SDK header 보조 근거로 구분한다. `cull_adapter_check.json`에 재사용11개 원본 setter 값을 보존했다. 새 원본 실행 건수0.

모든 원래 primitive attribute는 instanced geometry에 유지한다. 표면 속성과 기존 instance13개를 직접 attribute로 수신하면 WebGL 최소16 위치를 넘으므로 instance 상태13 vec4를 texture로 옮기고 `aSlot` 하나로 읽는다. GPU attribute 제한을 해결하기 위한 웹 이식 구조이며 원본 버퍼 배치의 재현은 아니다.

## 5. 상태 전이와 전체 수명

기존 InkAction/ELink FireImpact→FireOn 인계는 유지한다. 발사마다 머즐 이벤트를 무조건 재시작하지 않는다. `BulletSpawn(kind=Shooter)`는 WpShtrBullet1Emit/1383, `kind=Splash`는 WpCmnBulletSplash1Emit/1385로 분리한다 [판독, 기존 slot800 근거].

follow ALL은 현재 행렬 전체, POS는 원본 `08157b0`에 따라 현재 원점만 갱신하며 birth 축을 유지한다. NONE은 birth 행렬을 유지한다. 일반 CPU full trajectory는 [미확정]. fractional emit rate는 debt에 쌓아 정수 방출 수를 만들고, rate0/소수에서도 무조건1개를 생성하던 동작을 제거했다.

## 6. 계산식·조건·상세 의사코드

| program | alpha consumer (remap 전) | RGB 전단계 |
|---|---|---|
| 1383/1385 | clamp(A0 × linkedAlpha) × fade | C0 |
| 1202 Flash | clamp(T1.a × T2.a × linkedAlpha × A0) × fade, .5 이하 discard | C0 |
| 1747 SplashCorn | clamp(T0.a × linkedAlpha × A0) × fade | T0.rgb × C0 + C1 |
| 1940 Floor Splash | clamp(T0.a × primitiveA × A0) × dynamicFade | (T0.rgb × C0 + C1) × primitiveRGB |
| 1897 Crown | soft × clamp((T0.a × primitiveA − A0) × A1) × fade | C0 × primitiveRGB |
| 1885 Ripple | clamp((T0.a × primitiveA − A0) × A1) × fade | C0 × primitiveRGB; mappedA<=0 원본 red 분기 유지 |
| 1886 Wall Splash | clamp((T0.a × primitiveA − A0) × A1) × fade | (T0.rgb × C0 + C1) × primitiveRGB |

C0/C1에 각 키·현재 웹 팀색 bridge·colorScale을 적용한다. 근접 fade, threshold discard, alpha remap은 별도 단계다. 실제 Custom1/linkedAlpha 공급값은 미확정이며 웹 기본값으로 원본 전체 계약을 승격하지 않는다.

VAT는 `q=clamp(min(t*rate/(W+.00001)+.00001,.99999),0,1)`, `f=W*fract(q)`, 인접 두 열을 보간한다. 마지막 열에서 멈춘다. A half는 opacity가 아니라 compact normal이며 원본 다항식·sin/cos와 local `(sinθcosφ,polar,sinθsinφ)` 순서를 사용한다. 원본 VAT P.xyz에 E4 항을 더하는 소비 순서도 보존한다. GLSL `packHalf2x16`은 유한 half sample의 비트를 복원하기 위한 웹 adapter다; native log2/exp2/FMA와 GPU 비트 동등성은 미검증이다.

각 C0/A0/C1/A1/scale은 별도의 loop period/phase로 시간을 만든다. key mode1은 left HOLD, mode0은 선형 보간이며 파일 키 경계를 유지한다. mode2/255의 undefined output behavior와 RANDOM color 전체는 미확정.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

- 실제 emitterSamplers의 슬롯을 유지하여 Flash1/2, VAT2, normal1을 분리한다. 배열의 첫 텍스처를 보편적인 opacity라고 처리하지 않는다.
- BRTI→PNG `apply_comp`→KTX 경로에서 splash06/09_fia는 [R,R,R,G], pattern/flash fi는 [R,R,R,R], normal은 [R,G,0,1] selector를 이미 반영한다 [데이터/변환 판독]. shader A 소비가 맞다.
- 총구 Muzzle bone 공급·팀색 Original의 실제 native dynamic writer·Custom1 callback은 남는다.
- 소리 로직과 물리·총 로직을 이번 FX consumer 변경으로 원본 전체 확정 처리하지 않는다.

실제 공급 상세:

- `effects/shooter/emitters.json`의39개 emitter: scale·color0/1·alpha0/1 키를 원본 f32 전체 정밀도로 보존한다. 표시용 소수6자리 `round`를 사용하지 않는다. raw key와 최종 소비 key를 구분하여 `serializedKeys`에 원문을 남기고, FIXED인 채널의 키0만 원본 `08190fc`의 PColor 패치로 교체한다. ANIM은 그대로 둔다. 파일의 `numKeys=0`도 삭제하거나1로 바꾸지 않는다.
- `nativeRender`는 원본BD8..BE7 16B와 확정된 blendEnable/depthTest/depthWrite/depthCompare/blendMode/cullMode만 해석한다. 미사용 바이트 전체 의미는 미확정이다. nearFade(R890/894), alphaThreshold(R8A8), softDistance(R8B4), VAT normal offset(RE4), keyInterpolation(RC38..3C)을 보존한다.
- `client/audio/data.ts`는 nested 키·종류·개수를 최종 emitter def로 연결한다. sampler slot은 `emitterSamplers`로 명시 보존하며 배열 순서로 실제 슬롯을 추측하지 않는다. `textureInfo`에 원본 BRTI channel selector와 변환 여부를 남긴다. BC4 `fi`는RGB/A가R, BC5 `fia`는RGB가R/A가G인 자료가 있어 모든효과를 R mask로 합치면 안 된다. PNG/KTX는 기존 `graphics_bntx.to_png→apply_comp`에서 selector를 적용했다.
- 기존 VAT `bulletshtr_vsp.bin`(6×83·3984B), `bulletcmn_vsp.bin`(8×64·4096B)을 무손실 half 원값으로 실제 로딩한다. `RGBAFormat/HalfFloatType`, flipY=false, NoColorSpace, nearest, mip 생성 없음으로 공급한다. VAT selector는 identity이고 rawhalf에 재배치하지 않는다. 원본 shader의 texelFetch 입력을 보존하는 전송 경계이며 native sampler 전체 의미를 확정한 것은 아니다.
- **VAT row 연결 정정:** 최초 조사에서 `_u0.z`가 유실됐다고 가정했으나 원본 `082c0a0`은 인접한 `_u0.xy/_u1.xy`를 matching f32x2→f32x4로 결합한다. 따라서 `sysTexCoordAttr.z=_u1.x`, 현재GLB의 `uv1.x`가 원본 row다. 기존 두 GLB의188정점·238삼각형 row값/삼각형 topology가 원본과 정확 일치하며 **GLB 재출력과 VATbin 변경은 하지 않았다.** 파티클 geometry가 UV1을 소비해야 한다. 정점번호로 row를 대신하지 않는다.
- 좁은 재현도구 `web/tools/asset_fx_port.py`는 emitter JSON과 catalog의 effect/shooter bytes만 갱신한다. 전체asset_build·폴더청소·다른번들 재출력은 하지 않는다. 효과번들41파일·677638B, emitters.json413072B. 일반asset_build의 기존asset_fx.py가 이 보강을 재설정할 수 있으므로 이후 이 도구를 다시 실행한다.


## 8. 다른 기능과의 상호작용

확인된 FX 프로그램의 법선이 이제 주광·SH·동적광·안개를 소비한다. 현재 stage LightingState의 실제 uniform을 공유하며, FX-specific Custom1 조명/BRDF 계수와 environment array layer6 공급은 아직 없다. 현재 GGX·roughness·Fresnel은 명시된 **웹 lighting bridge**다. 원본 사진과의 밝기 차이를 이 숫자로 임의 튜닝해 확정했다고 기록하지 않는다.

Crown soft alpha는 scene/particle depth 차이를 원본 Res8B4 거리로 나눈다. 웹 perspective depth 선형화와 opaque prepass가 공급 경계이며, 실제 native NnVfx2ViewParam 계수/target schedule은 별도 확인 대상이다.

## 9. 웹 포팅 구조와 구현 순서

반영한 파일: `client/fx/particles.ts`, `particle_shaders.ts`, `shader_contract.ts`, `render_state.ts`, `index.ts`. 테스트는 `tests/fx_render_port.test.mjs`, fixture는 `tests/fixtures/fx_native_port.json`.

소비자와 39개 키/nativeRender/sampler/VAT 공급을 실제 연결했다. 실제 공개 로더44/44 및 브라우저 전체 이미터39개 검사까지 통과했다. known 계약 입력이 부족하면 `contractInputsReady=false`, `knownShaderContract=false`로 fallback을 보존한다. 로딩 중에는 FX view의 owner 생성과 spawn을 미뤄 임시 geometry/재질이 영구 캐시에 남지 않게 한다. ready는 실패 후에도 true가 되므로 기존 fallback은 로드 실패 후 사용할 수 있다. 이 대기 정책은 웹 이식 경계이며 원본 시작 순서 확정이 아니다.

## 10. 검증 코드·실행 결과·기대값

`node --test web/games/splatoon3/tests/fx_render_port.test.mjs`: **11/11 PASS**. 같은 입력에 8program 서로 다른 alpha를 독립 기대값으로 대조, 원본39개 descriptor/4channel 키 actual constructor, actual VAT half16 CPU golden, 마지막 열 정지/독립 loop/HOLD, primitive attribute와 row 필수 조건, POS/kill/state texture, fractional 방출, incomplete loader gate를 검사했다. GPU 원본 실행은0.

`node analysis/port_priority_r4/fx_render/actual_geometry.mjs`: 원본 fixture39개와 실제 압축 GLB26개를 actual ParticleBatch에 공급하여39/39 PASS. normal26·tangent15·color15·uv1 2개 모두 보존. 실제 VAT half2개와 원본 packed uv1.x로 VAT2/2 활성. 확인된 8종 program에 해당하는 emitter17개는 known 계약, 나머지22개는 기존 fallback. **이 geometry 검사는 native fixture를 공급한 소비자 검사다. 이후 실제 bundled loader/GPU 검사는 아래 최종 통합 결과에서 별도로 확인했다.**

`npm run typecheck`, `npm test`, `npm run build`: 최종 통과, **226/226**. `tests/fx_loading.test.mjs`3/3은 느린 공급에서 legacy 재질 캐시를 생성하지 않고 새 원본키 도착 후 known 계약을 사용하며, 실패 후 fallback은 계속 허용하는지 확인한다. 첫 view fixture에는 EventQueue가 없어2/3 실패했고 실제 clear/list 경계를 공급한 뒤3/3 통과했다.

`node analysis/port_priority_r4/browser_verify.mjs`: 실제 Edge/SwiftShader, 공개 로더→FxSystem→ParticleBatch→GPU. 전체39개 중 known17·fallback22, VAT2/2 활성, missing0, 페이지/HTTP/GLSL/GPU 오류0. 발사40·착탄80·소멸45프레임 검사와 화면 저장을 마쳤다. fx update가 경고로 삼킨 오류도 최종 검사가 거부한다. 모든 ESet을 한 위치에 생성한 화면은 정상 플레이나 원본 pixel 비교가 아니라 전체 소비자 컴파일 검사다.

자료 공급은 `tests/fx_data_port.test.mjs`44/44이며 원본 f32 키/count/type/FIXED/render/interpolation, 슬롯·selector, raw half VAT2개, 역순 bundle iteration을 실제 비동기 공개 fxData에서 검사했다. `web/tools/asset_fx_port.py --output analysis/port_priority_r4/fx_data/rebuild`의 JSON 전체 bytes/SHA256 및 catalog 전체값이 실제 에셋과 같았다. effects41파일677638B, emitter JSON413072B. `asset_build`의 기존 exporter가 키 정밀도와 metadata를 덮어쓸 수 있어 이후 좁은 보강 도구를 다시 실행한다. GLB2·VATbin2는 기존 SHA256 유지다.

첫 test는 VAT mid blend 수동 decimal 기대값의 오기 때문에8/9였다(.000076249904687 대신 정확한 double 계산 .00007625000468758358). 계산식/기대값 출처를 확인해 수정한 뒤9/9, legacy gate 추가 뒤10/10, cull 방향 보조 대조 추가 뒤11/11으로 통과했다. 읽기 중 존재하지 않는 native_shader.ts/effect_shape_math.md/테스트 파일과 PowerShell glob literal 경로로 실패한 검색은 `analysis/port_priority_r4/fx_render/commands.md`에 기록했다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 남은 항목 | 이유·다음 근거 |
|---|---|
| Custom1 VAT rate/alpha remap와 dynamic0/1 | shader reader는 확정, runtime producer 연결 없음. ELink ForceTeam→EmitterSet writer, callback+50/draw submit |
| GPU linked/default alpha | 1385/1202/1747 varying export 없음. NVN varying state·linked attribute/default |
| 원본 FX BRDF/environment layer6/전체 pixel | actual scene lighting bridge는 연결했으나 native coefficient/환경 texture 공급 미확정. 원본 draw capture와 동일 조건 Lby 화면 |
| volume2 세 emitter·point direction table | 원본36개 volume0, WaterSplash 및 HitMarker 3개 volume2. volume2 식/512방향표 actual 생성 미확정; native shape reader/table writer |
| CPU full update/billboard0/2/5/geometry resolver/texture scroll | 이전 웹 근사 경계 유지; 해당 원본 전체 소비자·NVN primitive binding |

자료 또는 부분 shader 구현이 생겼다고 inventory의 복합 질문을 반영 완료로 승격하지 않는다.


## 재질·눈 패턴·총구 그래픽 r9 — 2026-10-03

[현재 반영·검증·다음 지시](../port/graphics_priority_r9.md): 탱크/하네스/병의 native 재질·owner texture, raw type11 눈 채널, [Maya0/rotation0 UV6lane](../graphics/character_texsrt_r9.md), [실제 Muzzle 시각 행렬 및 내적 정정](muzzle_attachment_r9.md)을 웹과 MD에 반영했다. FMAA 원본1,212/피부 홀더67/SRT313/내적 격리블록2,048, 선택 GLSL↔웹GPU448건은 각각 범위가 다른 검증이며 원본 NVN/전체프레임 일치가 아니다. 이전 shared Muzzle 미공급 설명은 당시 기록이다. 현재 시각 부착은 실제 뼈를 따르며 내적의 실제 선택 뼈와 native frame 평가 순서는 미확정이다.

고정 원본556/986=56.39%·그래픽102/204=50.00%, port13/62=20.97%(일부37/차이9/원본미확정3)·GR0/10/일부7/10 유지. 신규 부분 근거를 기존 복합 질문 전체 확정으로 승격하지 않았다. 몸CP/skin idx·weighted type11/type18·다른 SRT mode/rotation·cube/BRDF/SPP·잠영 파문/Custom1/VAT·native 최종픽셀은 남는다. 최종 테스트·브라우저·보호 SHA와 실패는 r9 요약의 실행 기록을 따른다.
