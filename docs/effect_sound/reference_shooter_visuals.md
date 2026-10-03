# 사격·발밑·잠영 이펙트의 원본 화면 계약 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

첨부 화면에서 비교할 공통 요소는 잉크 방울의 입체감, 번쩍임과 튀는 액체의 형태, 발밑 파문, 잠영 전환이다. 스플래시슈터/Lby_Lobby00에 해당하는 원본 자료와 현재 웹의 실제 자료 공급 경로를 대조했다. 사진의 다른 무기·특수 상태 효과를 슈터의 기본 이펙트로 추가하지 않는다. 사진만으로 특정 emitter·광량·팀색을 확정하지 않는다.

**현재 FX가 원본과 다른 큰 이유는 수치 미조정 이전의 입력 유실과 렌더 경로 단일화다.** [웹 실행] 실제 번들 39개에서 스케일·alpha0·color0 키를 담은 상위 구조는 있지만, 로더는 키가 없는 `fields`만 전달한다. 모든 39개가 기본 키 `[1,1,1,0]`, 개수1로 생성된다. 원본 발사·탄·착탄 셰이더의 기존 근거는 재사용하며, 이번에는 플레이어 13이미터·9개 ELink leaf와 6프로그램의 선택된 alpha/표면/렌더 계약을 추가했다 [데이터]+[판독]. 웹 코드는 변경하지 않았다.

## 2. 분석 대상 원본·버전·자료 위치

원본 Splatoon 3 v0. `analysis/assets_work/r6/static.vfxb`, `analysis/visual_gap/static_grsn.bfsha`, `extracted/romfs/ELink2/elink2.Product.100.belnk.zs`를 읽었다. `original/`와 키는 취급하지 않았다. 이번 자료는 `analysis/reference_graphics_r3/fx/`에 둔다.

| 자료 | 범위·수준 |
|---|---|
| `player_emitter_exact.json` | 원본 ResEmitter 13개, 프로그램·텍스처 ID·렌더16B·PColor·애니 키를 직접 읽음 [데이터] |
| `player_elink_exact.json` | 원본 ELink의 9leaf·부모 switch/grid·trigger·곡선. 기존 파서의 소수6자리 표시를 이번 격리 실행에서 제거하여 f32값 보존 [데이터] |
| `shader_contracts.json`, `p*_fixed.*`, `.bin/.control/.ops.tsv` | 6program/12stage, raw Maxwell와 보완 역번역. GPU 실행0 [판독] |
| `web_batch_execution.json` | 실제 로더 함수·ParticleBatch·actual GLB CPU 실행39개 [웹 실행] |
| `shooter_render_reused.json` | r8의 원본11이미터 setter 기록 재사용. 신규 원본 실행0 |

SHARED.md/FUNCS.tsv와 `decomp_index.py --no-build`로 `08190fc/082804c/081a6f0/08157b0/081e3e4/PlayerInkDash`를 확인했다. FIXED 패치·VAT1383/1385·Flash1202·Ripple1885·OneEmitter 원본 실행은 다시 계상하지 않았다. shader 프로그램 번호는 ARM 함수 주소가 아니다.

## 3. 진입점과 전체 호출 흐름

| 경로 | 원본 → 현재 웹 | 확정 경계 |
|---|---|---|
| 발사/탄/착탄 | 기존 ELink/OneEmitter → VFXB → shader → emitter별 render → scene/HDR | 기존 [effect_resources](effect_resources.md), [fx_shader_inputs_r2](fx_shader_inputs_r2.md) 재사용 |
| 번들 애니 키 | JSON `emitterSets[*].scale/color` → `audio/data.ts:collectEmitters` → `d.emitters.set(key,f)` → `fx/index.ts:batch` → `new ParticleBatch(def)` | 실제 함수 추출·실제 constructor CPU 연결 [웹 실행] |
| 바닥 파문/잠영 | SplPlayer ELink action/property/grid → 이름별 emitter set → 프로그램2076/2090/2085/1630/1787/153 | 데이터 분기·선택된 shader 소비 [데이터]+[판독]. 상위 게임 writer와 GPU draw 미실행 |
| render 설정 | 기존 `0x71008182f4` → `0x710082804c` → NVN setters | r8 판독/CPU setter capture 재사용. 새 13개는 실제 BD8..BE7 바이트만 대조 |

현재 `client/audio/data.ts`는 assets의 상위 `scale.keys`/`color.alpha0.keys`/`color.color0.keys`를 `fields`에 합치지 않는다. `fx/particles.ts`는 `fields.scaleKeys` 등만 읽고 없는 경우1키로 대체한다. fallback에 있던 키도 같은 이름의 번들 `fields`가 도착하면 사라진다. 이는 자료가 최종 도착한 경로의 확정이며 브라우저 최초 로딩 시점과 네트워크 실패 상태를 재현한 것은 아니다.

## 4. 구조체·필드·상수·열거형 표

### 4.1 실제 웹 공급 유실 [웹 실행]

| 원본/JSON 의미 | 실제 consumer가 요구하는 이름 | 번들39개 결과 |
|---|---|---|
| 크기 애니 키/개수 | `scaleKeys/numScaleKeys` | 전부 없음 → `[1,1,1,0]`/1. 상위 다중 키31개 |
| alpha0 애니 키/개수 | `alpha0Keys/numAlpha0Keys` | 전부 없음 → `[1,1,1,0]`/1. 상위 다중 키33개 |
| color0 애니 키/개수 | `color0Keys/numColor0Keys` | 전부 없음 → 기본 키/1. 상위 다중 키18개 |
| 정점 표면 입력 | `normal/tangent/color/uv1` | actual GLB26개 모두 normal 유실, tangent15·color15·uv1 2개 유실 |
| 파티클 fragment | emitter별 shader와 sampler 채널 | 모든 emitter `uMap` 하나/R mask, unlit 출력, `.004` discard |

정점 유실은 `ParticleBatch`가 primitive에서 `position`과 `uv`만 새 geometry에 복사하기 때문이다. 아래 shader2090처럼 원본 primitive vertex alpha를 사용하는 경로에 색 속성을1로 가정해 채우지 않는다. 웹의 shader가 해당 속성을 안 읽는 것과 원본이 안 읽는 것은 다른 사실이다.

### 4.2 새 원본 플레이어 emitter [데이터]

숫자 calc/follow는 기존 판독된 `0=CPU,1=GPU_TIME`, `0=ALL,1=NONE,2=POS`. life/start는 프레임, interval은 파일값이다. 마지막 열은 `blendEnable/depthTest/depthWrite/blendMode/cullByte` 순서이며 NVN enum 명칭을 임의로 붙이지 않는다.

| emitter | shader/variation | calc/follow | life/start/interval | 실제 render |
|---|---|---|---|---|
| PlayerInkDash/Ripple | 2076/3612 | 0/1 | 6/1/0 | 1/1/0/0/1 |
| PlayerInkDash/splash | 580 | 1/1 | 20/4/1 | 0/1/1/0/0 |
| PlayerInkDashLine/Line | 153/3558 | 1/1 | 10/10/4 | 1/0/1/1/0 |
| PlayerInkTrack/Splash | 1040 | 0/1 | 20/3/1 | 1/1/0/0/0 |
| PlayerMetmDive/cover | 1787/3834 | 1/0 | 4/0/9 | 0/1/1/0/0 |
| PlayerMetmDive/splash | 364 (기존 POS 표본) | 1/2 | 20/3/1 | 0/1/1/0/1 |
| PlayerMetmDiveFr/crown | 2085/3840 | 0/0 | 21/0/4 | 1/1/0/0/1 |
| PlayerMetmDiveFr/splash | 548 | 1/1 | 16/3/4 | 0/1/1/0/0 |
| PlayerMetmDiveFr/Figure | 1630/3846 | 0/0 | 30/0/4 | 1/1/0/0/1 |
| PlayerMetmDiveFr/splash2 | 542 | 1/1 | 18/26/4 | 0/1/1/0/0 |
| PlayerMetmDiveSlopeFr/crown | 2085/3840 | 0/0 | 21/0/4 | 1/1/0/0/1 |
| PlayerMetmDiveSlopeFr/splash | 548 | 1/1 | 16/3/4 | 0/1/1/0/0 |
| PlayerMoveRippleInk/Ripple | 2090/3897 | 0/1 | 15/0/9 | 1/1/0/0/0 |

13개 모두 depth comparison byte3이다. 시작+duration이1이라고 “1프레임 뒤 모두 꺼짐”으로 해석하지 않는다. Dash/Track/Line은 `hasEmitEnd=0`이고 각각 별도 life와 방출 지속 상태를 갖는다. 나머지는 `hasEmitEnd=1`, duration1이다. 프로그램580/1040/548/542 전체 식은 이번 신규 판독 범위에 포함하지 않았다.

## 5. 상태 전이와 전체 수명

[데이터] ELink의 선택과 액체 표면은 단순한 `squid=true` 한 분기로 합쳐지지 않는다.

| 시작·조건 | 선택된 원본 |
|---|---|
| `SklAnim_Human/ToSquid`, ground!=OnFriend | PlayerMetmDive(cover+splash), trigger raw는 exact JSON |
| `SklAnim_Squid/Sqd_ToSquid`, grid GndPaintTeamType=OnFriend & GrindRailType=None, FieldAngleType=Plane | PlayerMetmDiveFr. Alpha는 PlayerAlpha의 (0,0)→(1,1) 곡선 |
| 위 동일 grid, FieldAngleType=Slope | PlayerMetmDiveSlopeFr. 같은 Alpha 곡선 |
| `SklAnim_Squid/Sqd_Walk`, SubjectiveType=Focused, MoveVelXZ>`0.15000000596046448` | PlayerInkDashLine |
| `State/Squid_Move`, GndPaintTeamType=OnNeutral, FieldAngleType!=Cliff | PlayerInkTrack |
| 직접 키 MoveSmokeL/MoveSmokeR, ShoesDirtyRt<`-0.27000001072883606` | PlayerMoveRippleInk. leaf의 OnNeutral 이름만으로 일반 잉크 걷기 전체라고 해석하지 않음 |
| 직접 키 InkDash, SubjectiveType=Focused 또는 기본 child | PlayerInkDash, Matrix2, PositionZ=-.5, MoveVelXZ에 따른 EmissionScale/Interval 곡선 |

마지막 두 직접 키의 실제 게임 호출자·ShoesDirtyRt writer는 [미확정]이다. 이름과 데이터 조건은 확정했지만 시각 전환 타이밍 전체를 확정하지 않는다. 상세 부모 트리·Grid는 `player_elink_exact.json`이다. Fr의 splash2 start26과 Figure life30은 서로 다른 emitter의 데이터이며 인간/오징어 표시 전환 임계값을 이 값으로 대신하지 않는다.

## 6. 계산식·조건·상세 의사코드

### 6.1 현재 웹 애니 키 유실 [웹 실행]

```text
loadedEmitter = emitter.fields              // 실제 collectEmitters
loadedEmitter.scaleKeys == absent
loadedEmitter.numScaleKeys == absent
ParticleBatch.uScaleK[0] = (1,1,1,0)
ParticleBatch.uScaleN = 1
// alpha0, color0도 같은 데이터 전달 결함
```

이 상태에서 native 키를 더 분석해 JSON 상위에 쌓아도 화면 크기·수축·밝기는 반영되지 않는다. 먼저 최종 `def`까지 정확한 키·개수·FIXED 패치 결과가 전달돼야 한다. Web shader의 “FIXED color0이면 vec3(1)”도 원본 PColor를 보편적으로 대체하지 못한다(6.5의 Line 색 값).

### 6.2 대시 파문2076 [판독]+[데이터]

새 원본 fragment는 **두 텍스처 A와 primitive alpha**, alpha0 빼기, FIXED alpha1, 깊이 기반 soft particle을 모두 소비한다. `T0=pattern02_fi`, `T1=pattern01_nrm`; normal XY는 별도 법선 입력이다.

```text
A0 = animate(Res700, t) * dynamic[0].w
A1 = 100 * dynamic[1].w             // D3F=FIXED. 파일 alpha1 키30→1을 쓰지 않음
C0 = (1,1,1) * dynamic[0].rgb * Res670
invScene = 1 / fma(sceneDepth, View30.w, -View30.y)
invParticle = 1 / fma(projectedParticleZ, View30.w, -View30.y)
S = clamp(fma(invScene,-View30.z,(-invParticle)*(-View30.z))/Res8B4,0,1)
rawA = S * clamp(fma(T1.a*T0.a,primitiveA,-A0)*A1,0,1) * dynamic[3].x
if rawA <= 0: discard
mappedA = fma(rawA,Custom1[11].x,Custom1[11].y)
Aout = clamp(mappedA,0,1)
RGB = 법선·주광·SH·동적광·환경 layer6·안개 소비
```

원본 soft distance `Res8B4=0.33000001311302185`, colorScale `Res670=1.7000000476837158`. 위 식은 선택된 GPU 명령 판독이며 GPU 비트 실행이 아니다. `projectedParticleZ`는 shader in_attr3.z/in_attr3.w이고 screen UV도 in_attr3를 사용한다. dynamic/Custom 공급값은 남아 있어 최종 alpha·화면색을1/팀색으로 확정하지 않는다.

**2026-10-03 도구 주의:** 표준 역번역 출력의 `0.0 - x * 0.0 - y`는 Negate 반환식에 괄호가 없어 부호 의미가 달라질 수 있다. 이번 raw Maxwell와 analysis 전용 보완 CLI를 함께 읽었으며 의도한 원본 식을 잘못된 GLSL 문자열 계산으로 검증하지 않았다. 표준 도구·웹 shader를 변경하지 않았다. 자세한 보완 도구는 §10.

### 6.3 발밑 파문2090 [판독]+[데이터]

```text
rawA = clamp(fma(T0.a,primitiveA,-A0)*A1,0,1) * dynamic[3].x
if rawA <= 0: discard
Aout = clamp(fma(rawA,Custom1[11].x,Custom1[11].y),0,1)
RGBpre = primitiveRGB * C0
RGBout = 법선·광원·반사·안개 소비
```

T0=`splash04_fi`. A0=0@0→.1083649993@.5099999905→1@1, A1=5@0→5@.7200000286→0@1(정확한 f32는 JSON). **A1은 ANIM이며 D5C=5를 고정으로 적용하면 틀린다.** vertex의 sysVertexColor0Attr.xyzw를 out_attr4에 실제 export한다. billboard byte2는 프로그램 옵션 Y_BILLBOARD로 대응했다. 보완 fragment는 sampler1 normal XY도 읽지만 ResEmitter sampler1에는 GTNT와 맞는 ID가 없다. 실제 SDK 기본/linked sampler1 값은 미확정이며 normal 텍스처 이름을 발명하지 않는다.

### 6.4 아군 잉크 잠영2085/1630·마른 바닥 변신1787 [판독]+[데이터]

crown2085는 `clamp(fma(T0.a,primitiveA,-A0)*A1,0,1)*fade`, A1 FIXED3과 pattern01_fi/pattern01_nrm을 쓴다. Figure1630은 **일반 texture0가 없고** `soft * clamp((primitiveA-A0)*A1,0,1)*fade`다. soft distance=.5, A1 FIXED3. depth와 primitive alpha 없이 임의 단색 원으로 대체할 계약이 아니다.

cover1787은 ResEmitter sampler1=`pattern01_nrm`만 연결되며 최종 alpha 입력은 `clamp(T1.a*primitiveA*A0,0,1)*fade`, 그 뒤 Custom1[11] remap/clamp다. A0 FIXED1이며 파일의 4개 alpha0 키(.8015/10/10/.9127)를 그대로 애니하면 틀린다. render는 blend off/depth write on, draw path12다. 동일 fragment에는 custom sampler1/2 기반 차폐 계수와 환경·광원 경로가 있다. 각각의 공급 UBO/텍스처는 아직 완전 연결하지 못했다.

### 6.5 오징어 대시선153 [판독]+[데이터]

```text
RGBout = fma(T0.rgb,C0,C1)
rawA = clamp(T0.a*A0,0,1) * dynamic[3].x
if rawA <= 0: discard
Aout = clamp(rawA,0,1)
```

T0=`glow00_fi`. PColor C0=(.2564103007,.3888888955,.3910256028), C1=(.1666667014,.3012819886,.4743590057), 각각 FIXED이며 dynamic0/1와 colorScale을 곱하는 vertex 공급을 보존한다. shader 옵션은 `VEL_LOOK_POLYGON`(billboard byte6), TEXTURE_ADD, draw path9. 이 line은 depth test0, write1, blend mode1이다. 현재 웹의 bill6은 emitter 축 일반 polygon 분기로 들어가며 기본 alpha blend/depth test를 쓰므로 같은 렌더 계약이 아니다. 전체 속도 정렬 기저의 특수 경계·GPU 궤적은 미확정이다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

발사 Flash/SplashCorn, 탄 main/splash VAT, 바닥 Crown/Splash, 벽 Ripple/Splash는 별도 원본 shader/primitive이다. 기존 [ink_visual_path](../graphics/ink_visual_path.md)·[fx_shader_inputs_r2](fx_shader_inputs_r2.md)와 연결한다. 이 문서의 플레이어 효과는 같은 SplPlayer 애니/state/xlink 입력에 이어져야 한다. `squid=true`에 루프 이펙트 하나를 수동 발동하는 방식으로 전부 치환할 수 없다.

현재 shipped shooter 번들에 Player* emitter set은0개, fallback ELink 사용자에는 WeaponShooterNormal/HitEffect만 있다. `SplPlayer`가 다른 경로에서 공급되는지까지 “없음”으로 일반화하지 않고, 이 두 실제 자산 경로에 없음을 확인했다. `onPlayer`는 SplPlayer가 없으면 missing 기록 후 return한다. 직렬화된 native sampler 번호를 map 하나의 “첫 사용 가능한 텍스처”로 축약하면 Flash의 gradation02 R을 고르는 등의 불일치가 생긴다.

원본 G3NT ID·인덱스는 새 JSON에 보존했다. 이 자료만으로 G3NT index=BFRES model index라는 기존 변환 추정을 해소하지 않았다. 모델 이름·정점색을 확정하려면 실제 SDK resource primitive resolver를 더 추적해야 한다.

## 8. 다른 기능과의 상호작용

팀색은 기존 원본 dynamic[0]/[1] 공급자 미확정을 유지한다. 주광·SH·environment·안개·alpha remap·HDRCompose를 모두 생략한 unlit RGB는 총 쏘는 물리식을 이식한 것만으로 같아지지 않는다. 현재 batch의 색 공간 변환까지 포함한 fragment는 emitter별 원본 조명/컴포지션 경로를 구현하지 않는다.

원본 r8 11이미터 중7개는 blend off+depth write on,8개는 cull byte nonzero다. 웹은11개 모두 transparent=true/depthWrite=false/DoubleSide로 생성된다. 이는 기존 원본 CPU setter 근거 재사용과 신규 웹 실행의 대조다. 새 GPU 실행11건으로 다시 계상하지 않는다. 또한 모든 FX가 한 transparent 패스에서 정렬되는 구조와 원본 draw path0/1/9/12/13의 구체 render scheduling은 별도 질문이며 번호 이름만으로 패스 순서를 발명하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

이번에는 MD만 반영했다. 아래는 후속 구현 지시 단위다.

| 우선 | 바꿔야 하는 실제 계약 | 완료 판정 |
|---|---|---|
| P0 | `collectEmitters`의 상위 애니 키/개수를 최종 def에 정확히 공급. FIXED는 원본 PColor 패치 적용 | 번들 도착 뒤 scale/A0/C0 count와 키·타입이 원본과 일치, fallback→번들 전환 때 키 유실0 |
| P0 | effect geometry의 normal/tangent/color/UV1과 native sampler 슬롯/채널을 보존 | 실제 GLB 입력 속성 보존, primitive alpha와 sampler A/R의 구별 |
| P0 | main1383/splash1385 VAT + Flash1202/SplashCorn1747 + 착탄1897/1940/1885/1886 각각 원본 shader 계약 | 원본 시각 자료와 동일 카메라/팀/상태/시각의 비교. alpha1·linked 입력 미확정 임의 대입 금지 |
| P0 | emitter별 blend/depth test/write/cull와 render path 유지 | 11개 기존·13개 신규 원본 descriptor 비교. setter 일치와 GPU pixel 일치를 분리 |
| P1 | SplPlayer ELink·Player* emitter/resource를 원본 action/state/prop→grid 조건으로 공급 | ToSquid/OnFriend Plane/Slope/dry→DiveFr/DiveSlopeFr/Dive 분리, alpha/soft depth와 delayed splash 유지 |
| P1 | Dash2076·Line153·Track1040·MoveRipple2090를 각 원본 조건으로 연결 | 원본 producer가 확보된 키부터 연결, ShoesDirtyRt·MoveVelXZ·PlayerAlpha 단위·writer 미확정 보존 |

현재 FX 관련 구현 파일은 `client/audio/data.ts`, `client/fx/particles.ts`, `client/fx/index.ts`, effect bundle 변환/로더다. impl 문서는 질문 목록으로 읽었으며 수정하지 않았다. [port/ink_visuals](../port/ink_visuals.md)의 FX02~04에 위 P0 계약을 먼저 반영해야 한다. 부분 shader 판독으로 해당 복합 inventory 전체를 완료 승격하지 않았다.

## 10. 검증 코드·실행 결과·기대값

실제 명령·실패는 `analysis/reference_graphics_r3/fx/commands.md`.

- [웹 실행] `node analysis/reference_graphics_r3/fx/web_batch_probe.mjs`: actual collectEmitters exact function을 타입만 제거하여 호출하고 actual ParticleBatch를 생성했다. actual compressed GLB는 web의 같은 MeshoptDecoder로 파싱. **39/39 PASS, fail0**, 키 기본화39, GLB26 모두 표면속성 유실. fake GPU/renderer는 없고 GPU·브라우저는 실행하지 않았다. fixture는 실제 자산 전달/constructor 수준이며 생존 파티클의 최종 pixel 테스트가 아니다.
- [데이터] `audit_data.py`: original ELink9leaf exact f32 및 ResEmitter13개. 고정 키 덮어쓰기는 기존08190fc 판독 재사용. 새 원본 CPU/Unicorn 실행0.
- [판독] 표준 `shader_dump.dll`의 6program/12stage와 raw audit12stage를 생성했다. BRX12stage 전부0. 부호·음수 식은 analysis 전용 `surface/dump/bin/Release/net10.0/dump.dll` 보완 역번역으로 다시 확인했고 `shader_contracts.json`에 보존했다. 서로 다른 Ryujinx 버전 출력의 SHA가 다르므로 단순 SHA 비교를 원본 식 차이로 주장하지 않는다. GPU 실행0.
- 재사용: r8 render832+actual11, native FIXED 패치, VAT498/512 등 이전 건수는 재실행하거나 이번 신규 실행으로 합산하지 않았다.

실패도 보존했다. 최초 `client/fx/inkfx.ts` 읽기는 존재하지 않아 실패→실제 particles/index를 찾았다. 첫 data audit는 list와 eset 문자열의 변수 es 충돌로 AttributeError→emitter_rows로 고침. Node GLTF는 MeshoptDecoder 미설정으로 실패→원래 web 로더와 같은 decoder를 설정해 성공했다. 일부 검색의 존재하지 않는 effect/경로·PowerShell wildcard 전달은 실패했으며 올바른 effects/shooter 경로와 파일 목록으로 좁혔다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 남은 질문 | 시도·막힌 이유 | 다음 원본/검증 |
|---|---|---|
| 사진과 실기/웹의 최종 pixel 동일성 | 사진은 다른 장면·무기·팀/후처리 조건이 섞임. 현재 actual web CPU/원본 명령·데이터만 확인 | 같은 Lby_Lobby00/슈터/포즈/팀/카메라/프레임의 원본 실기+웹 GPU capture |
| dynamic0/1 팀색·alpha·Custom1[11] remap | shader reader/Res PColor까지 확보, runtime producer 미연결 | ELink ForceTeam→EmitterSet 동적색 writer, callback+50/draw submit |
| 2090 sampler1 실제 texture/default | corrected shader reader 존재, native Res slot1은 GTNT ID와 불일치 | 원본 primitive/material sampler binding·callback 기본 resource |
| G3NT→실제 BFRES primitive name | native ID/index 데이터만; 기존 index 동등성은 추정 | SDK resource primitive resolver·vertex buffer binding |
| InkDash/MoveSmokeL/R 호출과 ShoesDirtyRt writer | ELink direct leaf/조건은 읽었으나 actor 호출자는 이번 미추적 | SplPlayer ELink direct search 호출·PlayerFoot/Model paint dirty property writer |
| calc CPU emitter의 전체 frame update, billboard6 기저 | 옵션/입력 소비·생존키/렌더 바이트 확보. 전체 CPU simulation·GPU 운동 실행 미완 | nn::vfx CPU update/birth + p153 정점 운동기저 전 경계 |
| draw path0/1/9/12/13의 실제 schedule 및 renderer targets | 파일/옵션값은 확정, 최종 scene renderer 분배 미연결 | VFX renderer draw submit와 frame pass graph |

키 전달 오류나 render descriptor 차이를 분석했다고 원본 그래픽 전체가 동일하다고 처리하지 않는다. 신규 inventory 전체 승격0, 신규 원본 CPU 실행0이며 위 미확정은 그대로 남긴다.

