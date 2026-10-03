# 원본 화면 기준 잉크 표면·반사 차이 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

첨부 화면에서 두드러지는 잉크의 젖은 광택, 밝은 칠 경계, 시점에 따라 바뀌는 반사, 바닥/벽의 표면 변화를 Lby_Lobby00 v0 원본 근거와 현재 웹 소스에 연결했다. **현재 바닥 잉크는 원본 잉크 재질 분기가 없는 별도 충돌 메시 오버레이**다. 이전 그래픽 포트의 지형 주광·베이크·일부 조명 반영과 잉크 재질 반영은 서로 다른 상태다.

이번 신규 [판독]은 원시 Maxwell의 부호 연산, BRDF 좌표 부호, 잉크 SH 방향과 셰이더 역번역 도구 결함을 확정한다. 기존 UV/팀색/표면 상수·원본 에뮬 결과는 재사용한다. **원본 GPU 실행·전체 픽셀 동등성·고정 inventory의 복합 행 완료는 주장하지 않는다.** 이번에는 MD와 분석 산출물만 추가했다.

첨부 이미지는 시각 목표를 설명하는 자료다. 사진의 RGB·노출·다른 스테이지의 조명을 Lby의 원본 값으로 채택하지 않았다. 원본과 같은 화면을 내려면 색만 진하게 하거나 광원 세기만 바꾸는 것으로 끝내지 말고 아래 경로를 함께 반영해야 한다.

## 2. 분석 대상 원본·버전·자료 위치

| 자료 | 위치·의미 |
|---|---|
| v0 원본 지형 셰이더 | `extracted/shader/Hoian_UBER.Product.bfsha`, model `hoian_uber` |
| 바닥 대표 | program **1714**, variation **761**, LobbyFloorConcrete/RampRubber/mLobbyWoodBox |
| 벽/고무 대표 | program **946**, variation **765**, Wall02/mLobbyFloorRubber |
| 기존 프로그램 연결 | `analysis/gfx4/programs/index.tsv`, 원본 재질의 정적 옵션 불일치0 |
| 이번 raw/역번역 | `analysis/reference_graphics_r3/surface/p1714.*`, `p946.*` |
| 비교 가능한 보완본 | `p*.fixed.vert/.frag`와 **동일 source** `p*.same_source_unpatched.vert/.frag` |
| 신규 검증 | `surface_audit.py`, `surface_evidence.json`, `p*.patch.diff`, `commands.md` |
| 현재 웹 | `client/paint/index.ts`, `client/render/forward.ts`, `lighting.ts`, `core/paint/surface.ts` (모두 `web/games/splatoon3/` 아래) |

먼저 README→분석.txt→docs README→tools를 읽고 SHARED/FUNCS를 확인했다. `decomp_index.py --no-build 0x7102c1d6ec 0x7102c2036c 0x710110f8cc`는 모두 기존 분석을 가리켰다. 다시 디컴파일하거나 기존 실행 건수를 신규 건수로 세지 않았다. [ink_visual_path](ink_visual_path.md), [floor_ink_inputs_r2](floor_ink_inputs_r2.md), [stage_rendering](stage_rendering.md), [model_panel_mapping](../paint/model_panel_mapping.md)을 재사용한다.

## 3. 진입점과 전체 호출 흐름

```text
원본: 도색 요청/원본 stamp → ColPaint panel·atlas
      → 모델 runtime _pu0(vec4 UV 후보), _pu1(switch), _pu2(paint tangent)
      → Hoian_UBER 1714/946 한 지형 draw 안에서 지형/잉크 재질 선택
      → 주광+SH+베이크+동적광+원본 cube array+BRDF+그림자
      → 원본 HDR/색 보정

현재: core/paint/surface.ts 독자 차트 → RGBA8 페이지
      → client/paint/index.ts 별도 충돌 삼각형을 법선 방향0.02 띄움
      → MeshStandardMaterial(.35)에서 단일 팀 Ink만 대입
      → three 기본 재질 조명 → 공통 후처리
```

[판독] UBO 공급은 기존 `110f8cc`(모델 user0 바인딩), `2c1d6ec`(상수), `2c2036c`(프레임 표면 애니)를 사용한다. 현재 map의 `applyForward()`는 지형 재질에 주광·베이크·SH·동적광을 연결했지만 별도 paint 재질에 호출되지 않는다. `forward.ts`를 추가했으므로 모든 잉크가 같은 원본 조명을 받는다는 결론은 성립하지 않는다.

## 4. 구조체·필드·상수·writer/reader 표

| 입력 | writer → reader / 값 | 수준 |
|---|---|---|
| 모델 `_pu0/1/2` | 기존 ColPaint 생성·모델 바인딩 → vertex paintUV/switch/tangent | 기존 [판독]+[실행-명시된 부분], 실제 전체 scene/GPU 미확정 |
| BlitzUBO0[21].w | `2c4ff64` 초기0.3 / GlobalWind 접근자 → frag 최대량에서 뺌 | 기존 [판독] |
| [3]/[4], [10]/[11], [62]/[63] | `1185c7c` → 팀0/1/2 Ink/InkBright | 기존 [판독] |
| [18].x/.y/.z | `2c1d6ec`·환경 접근자 → roughness **.05**, normal intensity **1.8**, emission | 기존 [판독]+[데이터], emission live 값 별도 |
| [19].x/.z | `2c1d6ec` → Fresnel **.015**, irradiance anisotropy **.5** | 기존 [판독]+[데이터] |
| [20].x/.y/.z | `2c2036c` → 바닥 thickness **.95**, 벽 **.75**, Mottari **1.75**의 사인 애니 | 기존 [판독]+[데이터] |
| [22].z/.w | init→texel→pack → UV neighbor interval | 기존 r2 원본28건 재사용, Lby Z=1/3200, 해당 연결의 W=0; 전체W writer 미확정 |
| [45].y/.z | `2c1d6ec` → InkRimIntensity **.625** / InkRimBlendCoef **.875** | 기존 [판독]+[데이터] |
| Env[25..31] | 기존 SH UBO 공급 → **N을 world-up 쪽으로 섞은 별도 방향**에서 SH 평가 | 소비식 신규 [판독] |
| cEnvBRDFMap 좌표 | fragment raw07f8/0928 → **(max(dot(N,V),1e-8), −roughness)** | 신규 [판독], sampler addressing 미확정 |
| cPrefilEnvMapArray | fragment raw0b28 layer12 /0b38 array-cube → 잉크 반사 | 기존 판독을 raw로 보강, prefilter 입력/GPU 미확정 |

표의 값은 Day 원본 데이터다. 사진을 보고 새 거칠기/밝기/법선 세기를 만들지 않는다.

## 5. 상태 전이와 전체 수명

한 번 칠한 면의 논리 소유, 화면의 잉크 재질 분기, 반사/조명은 서로 다른 계산이다. 도색 shader의 0.3 소유 판정이 지형 shader의 최종 표시 분기와 동일하다고 합치지 않는다.

[판독] 1714/946은 같은 지형 draw에서 ink branch가 거짓이면 원래 지형 albedo·normal·roughness·metalness를 사용한다. 참이면 해당 값을 잉크 값으로 바꾸고 이후 조명 계산으로 이어진다. 원본 최종 알파는1이다. 얇은 잉크 overlay의 알파를 임의로 낮춰 경계를 맞추는 경로가 아니다.

thickness와 Mottari는 GameFrame 정수 f마다 갱신된다. 기존 사인식 `(base+A*sin(period*f))`의 period는 라디안/프레임이다. 별도 UV 파형·noise·시간 단위를 추가하지 않는다. 지형 material normal은 잉크로 완전히 덮이지 않고 thickness에 따라 일부 남는다.

## 6. 계산식·조건·상세 의사코드

### 6.1 UV·잉크 분기·팀색 (기존 재사용, 경계 검증 보강)

```text
uv = switch<0 ? paintUV.zw : paintUV.xy
uv.y = 1-uv.y
c = sample(paintGrid,uv).rgb
Cv = sample(paintGrid,(u, fma(Mottari,W,v))).rgb
Cu = sample(paintGrid,(fma(Mottari,Z,u),v)).rgb
m=max(c); d=m-threshold; a=clamp(d,0,1)
w_i=clamp((c_i-m+9.99999975e-5)*1e8,0,1)
isInk=min(a*1000,1)>.5
```

원본 w는 단일 팀 index가 아니다. **동률 채널은 모두 가산하며 가중치 합으로 나누지 않는다.** 정확히 `(R,G,B)=(.5,.5,0)`이면 w=(1,1,0), 세 채널 동률이면(1,1,1)이다. 현재 웹은 R→G→B 우선순위의 하나만 선택한다.

[재구현-CPU] threshold0.3의 f32 입력에서 m=`0x3e99db23`(0.3005000054836273)는 false, 바로 다음 `0x3e99db24`(0.3005000352859497)는 true다. “m≥.3”나 실수식 “m>.3005”를 그대로 비교하면 원본 연산 순서와 같다는 근거가 없다. 이 결과는 식의 CPU 계산이며 실제 GPU bilinear sample의 비트 검증이 아니다.

```text
bright=Σ(w_i*InkBright_i); ink=Σ(w_i*Ink_i)
t=clamp(a*RimBlendCoef,0,1)
albedo=fma(ink-bright*RimIntensity,t,bright*RimIntensity)
```

현재 paint는 `Ink(9)`만 사용하고 InkBright/rim branch가 없다. 칠 경계의 밝은 색과 중심색은 단일 diffuseColor 대입으로 재현되지 않는다.

### 6.2 잉크 법선과 SH 평가 방향 — 신규 정밀화 [판독]

```text
gv=Σ(w_i*(c_i-Cv_i))*InkNormalIntensity
gu=Σ(w_i*(c_i-Cu_i))*InkNormalIntensity
Nink=normalize(Nv+Tp*gu+cross(Nv,Tp)*gv)
q=fma(clamp(Nv.y,0,1),ThicknessFloor-ThicknessWall,ThicknessWall)
N=fma(Nink-Nmat,q,Nmat)          // 이후 normalize를 추가하지 않음
Nirr=(aIrr*N.x, fma(N.y-1,aIrr,1), aIrr*N.z)
indirectSH=max(SH9(Nirr),0)      // Nirr도 다시 정규화하지 않음
```

**2026-10-03 정정:** [stage_rendering §7](stage_rendering.md#7-맵-위-잉크-판독-셰이더-1714)의 “비등방 Nv 혼합”은 축을 충분히 밝히지 않은 요약이다. 실제 방향은 **vertex normal Nv와의 혼합이 아니라 최종 N과 월드 위쪽(0,1,0)의 혼합**이다. p1714 원시0b78/0b80은 X/Z에 [19].z를 곱하며0b98은 Y−1에 같은 값을 곱해1에 더한다. 보완 GLSL `temp_118/119/120→temp_136/137/138`이 SH 입력으로 이어진다. 벽에서도 world-up을 사용한다.

`Nmat`와 `Nink`를 각각 정규화한 뒤 q로 섞지만 혼합 뒤 정규화는 없다. 원본의 이 동작을 “더 자연스럽게” 정리하지 않는다. 합성 평면 fixture에서 최종 N 길이0.99497265, 벽0.98000520였고 SH 방향도 비단위였다. 이 수치는 [재구현] 예시이며 원본 GPU 실행값은 아니다.

### 6.3 역번역 괄호 결함과 원시 부호 — 신규 [판독-도구/원본]

p1714 eye-vector 경로의 원시 Maxwell:

| stage byte offset | word | 원본 명령 의미 |
|---|---|---|
| 08a8 | 5080000000570204 | R4=rsqrt(R2), R2=eye.xyz 제곱합 |
| 08b8 | 5c69100000470f0f | R15=**−R15*R4**, NegA=true |
| 08c0 | 5c69100000470e0e | R14=**−R14*R4**, NegA=true |
| 08c8 | 5c69100000470d0d | R13=**−R13*R4**, NegA=true |

기존 표준 dump는 `temp_80 = temp_74 * 0.0 - temp_79` 등으로 출력했다. GLSL 우선순위대로 읽으면 `−inverseLength`가 세 축 모두에 들어가며 원본 `−eyeComponent*inverseLength`와 다르다. **게임 원본의 이상한 동작이 아니라 역번역 출력 결함**이다.

로컬 Ryujinx `InstGen.Negate()`가 `0.0 - expr`를 괄호 없이 반환하고, `NeedsParenthesis()`는 Special인 Negate를 함수처럼 취급해 부모 Multiply에서 괄호를 생략한다. analysis 전용 source copy에서 반환식만 `(0.0 - expr)`로 보완했다. 같은 source/같은 adapter의 unpatched와 patched를 따로 빌드해 p1714/946을 대조했다. 보완본은 `temp_89 = temp_83 * (0.0 - temp_88)` 등이며 원시 NegA 명령과 일치한다. 단순 눈짐작 치환은 사용하지 않았다.

**정정 적용 범위:** 기존 GLSL의 `x*0.0-y`·`fma(...,x*0.0-y)`와 유사 표현을 그대로 이식하지 않는다. 괄호 문제는 V·반사·주광·안개·동적광을 오염시킬 수 있다. 모든 이전 shader를 이번에 다시 검증했다고 주장하지 않는다. 이 문서의 보완본은1714/946만 검사했다. 표준 tool/source/build는 변경하지 않았다.

### 6.4 BRDF·반사·그림자 합성 — 신규 부호 정정, 나머지 기존 재사용

```text
V = normalize(cameraPosition-worldPosition)  // 위 raw negmul을 보존
NoV=max(dot(N,V),1e-8)
brdf=sample(cEnvBRDFMap,(NoV,-roughness)).xy
R=reflect(-V,N)                            // N은 §6.2의 혼합값
E=sampleCubeArray(R/maxabs(R),layer=12,bias=0)
envSpec=E*fma(brdf.x,InkFresnel,brdf.y)
```

**2026-10-03 정정:** [stage_rendering §5.4](stage_rendering.md#54-프래그먼트--조명-합성-판독)의 `(NoV,rgh)`는 shader의 좌표 부호를 빠뜨렸다. 원시07f8은 NegA/NegB로 R25=−roughness−0을 만들고0928 Texs의 두 번째 좌표로 사용한다. 기존·보완 GLSL 모두 음수 좌표가 남는다. sampler address와 원본 BRDF texture의 배열 방향이 미확정이므로 `−r`를 임의로 `r`나 `1−r`로 바꾸지 않는다.

**2026-10-03 추가 정정 [판독]:** 기존 문서의 층12 “명시 lod0” 설명도 수정한다. p1714 raw0b38은 `Tex/Dim=ArrayCube/Lod=Lb`이고 R26=0을 공급한다. 로컬 `InstEmitTexture.cs:287–291`은 Lb를 **LodBias**로 분류한다. 보완 GLSL의 `texture(...,0.0)`는 implicit LOD에 **bias0**을 더하는 호출이며 `textureLod(...,0)`가 아니다. 배열 층12 확정은 유지하고 mip0 고정이라는 결론은 철회한다. 원본 sampler/mipmap 상태 없이 minFilter를 임의로 고정하지 않는다.

[판독-재사용] 주광 diffuse는1/π, spec은1/(4π)·원본 roughness GGX/가시성/exp2 프레넬을 사용한다. 베이크 빛은 간접 diffuse 및 직접광 입력 두 곳에 들어간다. 원본 shadow는 AO·베이크 shadow·화면 shadow-prepass·projection shadow 합성이다. 잉크에서도 이 경로를 보존한다. indirect에 ambient occlusion을 곱하고 direct에 합성 shadow를 곱하며 ink emission은 그 뒤 가산한다. details는 [stage_rendering §5](stage_rendering.md#5-맵-재질-셰이더-hoian_uber) 원시·보완식과 함께 확인한다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

바닥 표면의 normal은 발사 파티클/착탄 튀김과 별개의 지형 재질 계산이다. 입자가 추가되어도 바닥 반사·빛 번짐이 자동으로 원본과 같아지지 않는다. 발사/착탄/잠영 이펙트와 캐릭터는 다른 담당 문서의 원본 VAT·shape·soft-depth·가시성/ASB 근거를 함께 반영한다.

이 표면 경로에는 원본 `_pu` 기저, 잉크 grid, 팀 Ink/InkBright, 베이크2장, Env SH, BRDF map, 층12를 포함한 cube array, shadow-prepass가 필요하다. three PMREM 환경맵이나 분석용 텍스처를 원본 리소스와 같다고 명명하지 않는다. 카메라 시점이 바뀔 때 V와 반사 방향이 갱신되어야 한다.

## 8. 다른 기능과의 상호작용

물리/발밑 판정은 도색량·팀 소유를 읽는다. 화면이 다른 overlay UV로 칠되면 플레이어가 느끼는 자기 잉크 위치와 보이는 경계가 어긋날 수 있다. 같은 ColPaint 입력을 논리 샘플과 모델 shader가 소비해야 한다. 기존 panel mapping 근거는 재사용하고 whole scene 연결은 남긴다.

현재 env 정상 로드에서는 paint도 `parseEnv()`로 주광10에 따라 팀색을 계산한다. DAY_LIGHT4는 읽기 실패 fallback이다. 이번 차이를 “항상 광원4여서 발생”으로 단정하지 않는다. 계산된 팀색 입력과 실제 잉크 fragment 조명 누락을 구분한다.

## 9. 웹 포팅 구조와 구현 순서

| 우선 | 구체 지시 | 현재 코드/기존 port |
|---|---|---|
| P0-1 | 모델 material에 native ColPaint UV/switch/tangent와 atlas 연결, 같은 draw의 지형/잉크 분기 구현 | `client/paint/index.ts:57–76`, `core/paint/surface.ts`; PNT02/PNT06 |
| P0-2 | narrow weights·f32 분기·InkBright/rim·neighbor normal·thickness·애니 전체 소비 | `client/paint/index.ts:114–130`; PNT06 |
| P0-3 | 잉크 F0=.015/roughness=.05·world-up SH·원본 direct/indirect/bake/shadow 합성 연결 | `client/render/forward.ts:73–91`; GR05/06, PNT06 |
| P0-4 | 원본 BRDF texture/sampler와 cube12 prefilter 연결; PMREM 대체 경계 해소 | `lighting.ts:73–94`, `forward.ts:88–90`; GR05/07 |
| 검증 | 정지+시점 회전, 바닥/벽/경사, 두 팀 경계/동률, 칠 전후 동일면을 원본 동일 입력으로 비교 | GPU 입력·동일 Lby capture 필요 |

숫자만 `.35→.05`로 바꾸는 작업을 잉크 그래픽 전체 반영으로 종료하지 않는다. `_pu` 공급부터 최종 조명까지 연결한 결과를 별도로 검증한다. 구현 시 표준 dump의 무괄호 Negate를 그대로 사용하지 않는다. 이번 MD는 분석/구현 지시 명세이고 현재 코드 반영 완료 상태를 바꾸지 않는다.

## 10. 검증 코드·실행 결과·기대값

| 실제 수행 | 결과 | 확정 경계 |
|---|---|---|
| 표준 `shader_raw_audit ... hoian_uber 1714/946` | vertex/fragment raw/control/header2프로그램 생성 | 원본 데이터/명령 [데이터]+[판독] |
| 분석 decoder | fragment 원시 명령 **666+660**개 기록, p1714 NegA3개 확인 | 명령 판독, 원본 GPU 실행0 |
| analysis patched library/dump 빌드 | 반환 괄호1곳 보완, 같은 source unpatched 빌드도 성공; 최종 warning/error0 | 분석 도구 실행 |
| 동일 source paired 덤프 | 2프로그램×2stage, 보완 전후 fragment 각각79행 변경 | source AST 출력 비교; 전체 shader 동등성 실행 아님 |
| `surface_audit.py` | **24/24 검사**, fail0; 1,024 eye fixture/3,072 f32 성분에서 잘못된 식 반례 | [재구현-CPU]+정적/raw 검사 |
| 경계/동률/법선 fixture | f32 경계8점, 팀색4점, 법선2점 기록 | [재구현], GPU 실행 아님 |

보완 CLI는 `web/tools/shader_ryujinx/dotnet/dotnet.exe analysis/reference_graphics_r3/surface/dump/bin/Release/net10.0/dump.dll prog-bfsha <bfsha> <model> - <analysis prefix> --index N`. 신형 source의 IGpuAccessor에 binding/array-length 메서드7개를 analysis adapter로 제공한다. c1 inline constants는 decode 전에 공급한다. buffer/sampler binding은 변환 이름을 위한 분석 fixture이며 GPU pipeline을 실행하지 않는다.

실패도 [commands.md](../../../analysis/reference_graphics_r3/surface/commands.md)에 남겼다. 처음 raw CLI의 model `0`은 named dictionary라 KeyNotFoundException, `hoian_uber`로 해결. 초기 build의 상대 참조/신형 interface/decoder 검색경로 오류를 보존하고 마지막 성공 command로 수정했다. 신규 Unicorn 사례는0이고 기존 원본28건 등은 재실행하지 않았다.

## 11. 미확정 사항과 다음 근거

| 미확정 | 시도·경계 | 다음에 볼 곳 |
|---|---|---|
| 원본 cEnvBRDFMap texture·sampler address/filter 연결 | raw 음수 좌표 및 `GGXEnvBRDF` 이름은 확보; 실시간 handle/sampler 미확보 | 렌더 리소스 `GGXEnvBRDF` 생성→sampler 기록/바인딩, 원본 GPU capture |
| 원본 cube array 층12 실제 픽셀/prefilter | shader 소비 확정, 현재 PMREM 대체 | GGXPrefilterEnvMap 생성·IlluminateEnvMap·원본 cube writer 및 submit |
| whole ColPaint model atlas/raster·[22].w 후속 writer | 기존 typed UV/panel/28건 재사용; actual whole scene/GPU 제외 | model_panel_mapping의 미해소, `2be8aec`/UBO 후속 writer |
| 원본 shadow-prepass·projection live 입력 | 원본 식/값은 기존 판독, PCF/다른 frame으로 대조 불가 | native shadow scene submit·cascade/light frame |
| 원본 동일 Lby 최종 픽셀 | 첨부는 동일 Lby/동일 시점/동일 입력 capture라는 근거가 없음 | 원본 v0 Lby 동일 camera/team/칠 map/capture + 웹 동일 입력 |
| 다른 이전 shader의 Negate 피해 범위 | 이번에는1714/946의 원시·paired 보완본을 검사 | 캐릭터/FX/후처리 각 실제 program raw·paired dump |

고정 inventory/port 분모와 복합 행 상태는 유지한다. GPU·실제 scene 입력이 없다는 이유를 남기며 사진에서 보이는 값을 임의로 확정값으로 채우지 않는다.


### 2026-10-03 잉크 surface r7 포팅 후속·정정

[현재 실제 구현·검증·잔여](../port/ink_surface_r7.md), [좌표/geometry](ink_visual_geometry_r7.md), [원본 판독식 소비](ink_surface_web_r7.md). 이전 별도 collision overlay/.35/단일색 미반영은 당시 상태다. 현재는 actual visual triangle에 원본 packed writer 값과 밝은 경계·법선·두께·F0.015/.05·공통 조명을 연결했다. 베이크 UV1은 paint UV로 바꾸지 않았고 clone의 shader hook/USE_UV1 defines를 유지한다.

원본 panel/atlas 전체는 customchart adapter, 환경반사는 PMREM/Three BRDF이다. native Z1/3200과 웹 페이지 폭 역수를 구별하고 초기 W0/emission0을 live 원본값으로 확정하지 않는다. 실제게임/GPU 검증은 포트 링크의 명령/실패를 따른다. fixed986/556 및 web13/62 유지, PNT06만 차이→일부.
