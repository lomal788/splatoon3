# 실제 지형 draw의 잉크 재질 소비 — 웹 반영 r7

## 1. 기능 개요와 사용자에게 보이는 동작

2026-10-03 · 바닥·벽의 잉크가 기존 지형 재질과 같은 draw에서 색·법선·표면 계수·조명 입력을 바꾸도록 원본 Hoian_UBER 1714/946의 확정된 소비식을 연결한다. 기존 충돌 overlay의 단일 팀 Ink, roughness .35 경로에 빠져 있던 **InkBright 경계, 동률 채널 가산, 이웃 샘플 법선, 바닥/벽 thickness, F0 .015, roughness .05, world-up 쪽 SH 방향**이 대상이다.

이 문서는 원본 판독식의 웹 소비자와 검증을 기록한다. 모델/atlas 공급·실제 씬 통합은 [r7 포트 기록](../port/ink_surface_r7.md)의 구현 결과를 함께 확인한다. **원본 GPU 실행·원본과 같은 전체 픽셀·whole ColPaint raster/atlas 완료를 주장하지 않는다.** 고정 inventory 556/986와 포트 13/62의 복합 행은 이 부분 작업으로 승격하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

| 원본/웹 자료 | 의미 |
|---|---|
| Splatoon 3 v0 `Hoian_UBER.Product.bfsha`, `hoian_uber` 1714/946 | 바닥/벽 대표 잉크 소비자 |
| `analysis/reference_graphics_r3/surface/p1714.fixed.frag/.vert` | 원시 Maxwell NegA에 맞춰 괄호 결함만 보완한 기존 GLSL |
| [reference_ink_surface §6](reference_ink_surface.md#6-계산식조건상세-의사코드) | 원본 near-max/rim/normal/SH/BRDF 부호 근거 재사용 |
| [floor_ink_inputs_r2 §6](floor_ink_inputs_r2.md#6-계산식조건상세-의사코드) | 원본 UV 반전·neighbor 순서와 Z=1/3200, 초기 W=0 연결 실행 재사용 |
| `0x7102c1d6ec`, `0x7102c2036c`, `0x710110f8cc` | 원본 InkUBO 기록·GameFrame 애니·모델 user0 바인딩, 새 디컴파일/실행 없음 |
| `client/render/ink_surface.ts`, `ink_surface_math.ts` | 웹 GPU 소비자/CPU 참조 (`web/games/splatoon3/` 아래) |
| `analysis/port_ink_r7/shader/` | 독립 원본 GLSL 대입문 fixture와 WebGL 비교 |

README/설계/분석.txt와 관련 문서를 읽고 SHARED/FUNCS를 검색했다. `decomp_index.py --no-build 0x7102c1d6ec 0x7102c2036c 0x710110f8cc`는 모두 기존 분석을 가리켰다. 기존 원본 에뮬 결과를 신규 실행 수로 세지 않는다. 신규 원본 Unicorn/Ghidra 실행은0이다.

## 3. 진입점과 전체 호출 흐름

```text
원본: ColPaint → _pu0/1/2 → 1714/946 UV·mask·normal·재질 분기
      → direct/bake/SH/dynamic/occlusion/원본 BRDF·cube array → HDR

웹: 지형 MeshStandardMaterial에 applyHoian → applyForward
    → applyInkSurface(mat,bindings)
      vertex paintUv4/paintSwitch/paintTangent3 소비
      fragment 기존 재질 normal 계산 뒤 hReadInk
      ink일 때 albedo/normal/roughness/metalness/emission 교체
      FORWARD_SURFACE_END에서 world N/F0/SH 방향 교체
      동일 bake/direct/SH/dynamic/shadow/fog/post 경로
```

`applyForward`는 명시적인 `FORWARD_SURFACE_GLSL/END` hook을 제공한다. 없는 hook·비활성 shading 재질을 일반 paint fallback으로 숨기지 않고 오류를 낸다. hNoL은 ink N을 선택한 뒤 계산한다. 도색되지 않은 fragment는 기존 지형 입력을 유지한다.

## 4. 구조체·필드·상수·열거형 표

| 입력/필드 | writer/공급 → reader | 수준·경계 |
|---|---|---|
| `paintUv:vec4`, `paintSwitch:float` | 모델/atlas 공급 → switch<0?zw:xy, 그 뒤 V 반전 | 기존 원본 [판독], 웹 공급 adapter 별도 |
| `paintTangent:vec3` | `_pu2` 대응 object-space → `mat3(modelMatrix)*T` | 기존 원본 vertex [판독]; **T 자체 normalize 없음** |
| vertex N | 원본 ShpMtx의3×3×N, 정규화 → fragment normalize | 기존 [판독]; merged static 지형의 modelMatrix 연결 |
| team `Ink/InkBright[3]` | 원본 팀색 type9/10 → additive weighted sum | 기존 [판독]+[실행]; scene 팀 행 선택은 별도 |
| threshold .30000001192092896 | BlitzUBO0[21].w → gate | 기존 [판독] |
| roughness .05000000074505806 / F0 .014999999664723873 | InkUBOParamDay → direct/dynamic/indirect diffuse | 기존 [데이터]+[판독] |
| normal intensity1.7999999523162842 | [18].y → weighted neighbor gradient | 기존 [데이터]+[판독] |
| thickness .95/.75 + .015625·sin(.03125·f) | 2c2036c → clamp01 → N混合 | 기존 [판독]+[데이터] |
| Mottari1.75 + .0625·sin(.08·f) | 2c2036c → max0 → neighbor UV | 기존 [판독]+[데이터] |
| anisotropy .5 | [19].z → `N→(0,1,0)` SH 방향 | 기존 [판독]+[데이터] |
| rim intensity .625 / blend .875 | [45].y/z → InkBright→Ink 합성 | 기존 [판독]+[데이터] |
| `textureStep:[Z,W]` | **호출자가 실제 atlas 좌표에서 공급** → Mottari를 곱해 sample | 웹 adapter; native Z를 arbitrary texture에 복사하지 않음 |
| `emission:number` | active env의 Ink accessor, 104e6dc → [18].z → albedo×emission | 기존 [판독]; 필수 입력, live 값·initial 정책은 통합 기록 |

원본 Lby init→texel→pack의 `[1/3200,0]`는 `NATIVE_LOBBY_INK_STEP`으로 구분해 보관한다. 웹 atlas 공급이 `[1/pageWidth,0]`를 사용하는 경우 이는 `Mottari/8` world interval을 자기 차트로 옮기는 **명시 adapter**이며 원본 UBO값이라는 뜻이 아니다. 후속 W writer는 미확정이며 W를Z와 같게 채우지 않는다.

## 5. 상태 전이와 전체 수명

`applyInkSurface`는 texture/team/step/emission과 shader hook을 한 번 바인딩한다. 매 fixed GameFrame을 `updateFrame(frame)`으로 받아 thickness/Mottari를 갱신하며 `frame/60`도 원본[20].w 대응으로 보관한다. JS `Math.sin`은 원본 SDK sinf의 모든 입력에서 비트 동등하다고 주장하지 않는다.

negative 선택 UV는 웹에서 이 atlas에 배정되지 않은 triangle을 나타내는 sentinel이며 ink branch를 끈다. 원본 `_pu`가 이런 sentinel을 쓴다고 주장하지 않는다. 정상 UV의 sampler addressing/filter는 texture 공급자가 소유한다. `uvAlreadyFlipped`는 공급자가 이미 원본 V 반전을 적용한 경우만 사용하며 기본값은false다.

`setTexture`는 sampler만 교체한다. `dispose`는 자신이 설치한 hook/cache key만 복구하고 caller 소유 texture/material/geometry를 해제하지 않는다. 세 팀 슬롯, 유한 emission/interval, 적용 순서, attribute 이름을 검사한다.

## 6. 계산식·조건·상세 의사코드

원본 식 상세는 [reference_ink_surface §6](reference_ink_surface.md#6-계산식조건상세-의사코드)를 재사용한다. 이번 GPU 소비자에서 유지한 핵심 순서는 다음과 같다.

```text
uv = switch<0 ? paintUV.zw : paintUV.xy; uv.y=1-uv.y
C=sample(uv); Cv=sample(u,v+Mottari*W); Cu=sample(u+Mottari*Z,v)
M=max(C.b,max(C.r,C.g)); A=clamp(M-threshold)
w=clamp(((C-M)+9.99999975e-5)*100000000)
isInk=min(A*1000,1)>.5
Bright=w.b*Bright2+(w.r*Bright0+w.g*Bright1)
Ink=w.b*Ink2+(w.r*Ink0+w.g*Ink1)
albedo=(Ink-Bright*.625)*clamp(A*.875)+Bright*.625
gu/gv=(weighted C-Cu/Cv)*1.8
Nink=normalize(Nv+Tp*gu+cross(Nv,Tp)*gv)
q=clamp(Nv.y)*(ThicknessFloor-ThicknessWall)+ThicknessWall
N=(Nink-Nmat)*q+Nmat                         // normalize를 추가하지 않음
Nirr=(.5*N.x, .5*(N.y-1)+1, .5*N.z)          // normalize를 추가하지 않음
F0=.015; roughness=.05; metalness=0; emission=albedo*envInk
```

두/세 채널이 동률이면 w=(1,1,0)/(1,1,1)이고 색 합을 나누지 않는다. CPU fixture의 원본 인접 f32 boundary .3005000054836273=false, .3005000352859497=true를 유지한다. 원본은 shader FMA를 포함한다. WebGL 소스의 곱·덧셈/normalize 및 compiler fusion은 NVN Maxwell FMA 결과와 모든 입력에서 비트 일치한다고 주장하지 않는다.

공통 direct/dynamic은 .015 F0와 원본 roughness를 소비한다. 간접 diffuse는 별도 Nirr에서 SH를 평가하고 AO가 기존 공통 경로를 통해 곱해진다. 베이크 UV/샘플과 그림자 입력도 기존 draw에 남는다. **환경 반사의 `getIBLRadiance/EnvironmentBRDF`는 기존 three PMREM/BRDF adapter**다. 원본 음수 roughness BRDF 좌표·층12 implicitLOD+bias0을 대체 완료했다고 주장하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

`hV=normalize(cameraPosition-worldPosition)`가 공통 조명에서 매 draw 갱신된다. 법선 변화가 direct specular와 기존 환경 반사 adapter에 전달되어 정지 상태 시점 회전에서도 반응한다. 바닥 반사는 muzzle/착탄 파티클이 아니므로 VAT/soft-depth/emitter 식을 이번 작업으로 해결했다고 올리지 않는다.

캐릭터/잠영·발사 파티클·효과음은 별도 경로다. 동일한 팀 Ink/InkBright와 공통 lighting을 소비할 수 있지만 해당 캐릭터/FX shader 분기는 이번 재질 hook에 포함되지 않는다.

## 8. 다른 기능과의 상호작용

도색량/팀 소유의 물리 샘플과 표시가 동일 페이지를 소비하도록 통합해야 한다. 시각 모델에 붙이는 adapter의 미배정/거리/소속 실패를 임의 chart로 채우지 않는다. 원본 논리 .3 판정과 visual .3005 주변 f32 gate는 같은 boolean으로 합치지 않는다.

지형 map/albedo/normal/bake 자료는 기존 재질에 남아 있으며 ink가 덮는 부분만 선택한다. 원본 N 혼합 뒤의 normalize 부재는 hN과 SH 방향에 보존했다. three 환경 반사 내부 정규화/BRDF는 남은 adapter 한계다.

## 9. 웹 포팅 구조와 구현 순서

```ts
const bound=applyInkSurface(material,{
  texture:pageTexture, ink:teamInk3, inkBright:teamInkBright3,
  textureStep:adaptedPageStep, emission:explicitEnvInk,
  // geometry: paintUv(vec4), paintSwitch(float), paintTangent(vec3)
});
bound.updateFrame(world.frame);
// geometry/material/atlas는 호출자가 소유하고 해제
bound.dispose();
```

`applyHoian→applyForward→applyInkSurface` 순서를 지킨다. attribute/page마다 sampler binding·cache key를 명확히 유지한다. 미배정 fragment는 기존 지형 분기로 남는다. 이번 source의 소유 범위는 새 재질/수학 모듈·테스트·이 MD이고 atlas, paint system, assets, impl, original은 직접 수정하지 않았다. 통합 파일 변경은 조정자가 별도로 담당한다.

## 10. 검증 코드·실행 결과·기대값

| 실제 수행 | 결과·한계 |
|---|---|
| `decomp_index.py --no-build` 3주소 | 기존 index/분석 확인, 재디컴파일0 |
| `.venv/Scripts/python.exe analysis/port_ink_r7/shader/native_fixture.py` | 원본 corrected1714의 대입문을 직접 파싱/해석한88입력,85ink/3false. [재구현-독립CPU], 원본 실행 아님 |
| `node --test .../ink_surface.test.mjs` | **8/8 PASS**; 88 gate/weight exact, rim/N/Nirr/emission/thickness tolerance2e-6, hook·수명·누락 거부 |
| `npm run typecheck` | exit0 (통합 후 전체검사는 포트 기록 참고) |
| `node analysis/port_ink_r7/shader/gpu_compare.mjs` 첫 실행 | GLSL reserved word `active`로 컴파일 실패1, GL1282, PASS로 세지 않음 |
| 같은 명령, struct field `isInk`로 정정 후 | **431/431 PASS**, 최대 절대차 **5.960464477539063e-8**, console shader error0/GL0 |

GPU 비교는 original corrected GLSL의 `temp_32..temp_74` 대입문 slice와 실제 `INK_SURFACE_GLSL`을 별도 shader로 그려 RGBA32F를 readback한다. 같은88입력에 gate/albedo/N/Nirr/roughness/weights/emission의5출력을 검사하며 inactive에서는 의미 있는 gate/weights만 비교하므로431건이다. 원본 texture roughness/metalness의 inactive 분기는 fixture의 .35/.1로 바꿨고 해당 출력은 비교하지 않았다. native sampler/NVN/Maxwell를 실행한 것이 아니다. 원본 `fma`는 WebGL에서 `a*b+c` 함수로 대응하며 이 경계를 report에 기록한다.

입력은 float3×3 nearest texture와 원본 UBO값으로 통제했다. 원본 normal-map 대입문으로 계산한 Nmat fixture를 포트에 공급해 normal/rim 소비를 독립 비교한다. fixture는 corrected native source의 SHA256을 기록한다. 실제 무압축/압축/linear sampling·지형 geometry·whole atlas mapping 검증을 대신하지 않는다.

실패 기록: 첫 fixture interpreter가 inactive branch를 건너뛰지 못해 temp67 미정의로 실패했고 branch 선택을 고쳤다. 한 번 cwd가web인 상태에서 `.venv` 상대 경로를 써 실행 파일을 못 찾았으며 Cdev 루트에서 재실행했다. 초기 조사에서 존재하지 않는 `web/分析.txt`, `render/shaders.ts`, `render/env.ts`와 잘못된 rg bracket pattern을 사용한 오류는 자료 위치/패턴을 바로잡았다. 성공으로 계상하지 않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 잔여 | 현재 경계·다음 근거 |
|---|---|
| whole native ColPaint/model raster·atlas | root의 실제 지형/webchart 연결은 adapter. 원본 panel/packed UV/_pu binding/GPU stamp submit 전체 연결 필요 |
| W의 whole scene 후속 writer | init→texel→pack의0은 기존 좁은 실행. alias/dirty-frame callback/runtime watch 필요 |
| 원본 BRDF·cube12 실제 리소스/sampler | PMREM/three BRDF adapter 잔류. 원본 GGXEnvBRDF 생성·negative V addressing, cube array12layer/prefilter/binding 필요 |
| 환경 input cube/Illuminate 및 static/projection shadow live | 공통 r6에서 확정된 소비식만 재사용. live draw/descriptor·원본 scene capture 필요 |
| 원본 SDK sinf·Maxwell FMA 전체비트 | JS libm/WebGL 컴파일은 같은 실행환경이 아님. 같은 원본GPU 입력/출력 확보 필요 |
| 캐릭터/잠영/FX shader | 이 지형 재질 범위 밖. 실제 program 선택·raw/UBO/texture·모델 가시성 전환 추적 필요 |
| 원본 동일 Lby 최종 화면 | 사진의 다른 map/color/HDR를 값으로 채택하지 않음. 원본 v0 동일 camera/team/칠량/시각 capture와 대조 필요 |

2026-10-03 정정 기록: [reference_ink_surface §3/9](reference_ink_surface.md#3-진입점과-전체-호출-흐름)의 기존 별도 overlay/단일 Ink/.35 미반영 설명은 분석 당시 사실로 보존한다. 이번 shader 소비자가 해당 식을 공급받아 실제 지형에 통합된 범위는 포트 문서에 날짜와 검증 결과로 후속 기록한다. 전체 native graphics/복합 inventory의 완료로 바꾸지 않는다.
