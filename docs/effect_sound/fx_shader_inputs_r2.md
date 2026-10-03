# 발사 Flash·착탄 Ripple·VAT shader 입력 보완 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

총구 번쩍임(Flash), 벽에 맞은 잉크 고리(Ripple), 분열 탄의 투명도 입력을 추가 분석했다. 기존 1747 SplashCorn/1886 Splash와 다르게 **Flash는 두 텍스처 A를 곱하고 .5 이하를 discard**, Ripple은 **alpha0을 빼고 애니 alpha1을 곱한다**. 같은 R 마스크·단색 파티클로 합치면 원본과 다르다. 웹 코드/impl/에셋은 변경하지 않았다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0, Lby_Lobby00, Shooter_Normal_00. 기존 `analysis/assets_work/r6/static.vfxb`와 `analysis/visual_gap/static_grsn.bfsha`를 읽었다. 새 자료 `analysis/visual_gap_r2/fx/p1202_fixed.*`, `p1885_fixed.*`, `p1385.*.bin/.control/.ops.tsv`, `audit.json`, `emitter_fields.json`, `emitter_assets.json`, `attrs_raw.json`. 원본 키는 취급하지 않았다.

SHARED/FUNCS 및 `decomp_index.py --no-build CustomShader/EffectShader/0x710084c968/0x710137f144/0x7100817b28`로 중복 확인했다. 1202/1885는 effect_resources §2.2.5.1에 미판독으로 남아 있었다. 1385 VAT 식·SDK OneEmitter·CSDP 등록은 기존 근거를 재사용한다. shader program 번호1202는 ARM 주소0x7100001202가 아니므로 주소 색인 조회만으로 shader 중복 여부를 판정하지 않는다.

## 3. 진입점과 전체 호출 흐름

| 경로 | 원본 데이터→소비자 | 이번 범위 |
|---|---|---|
| 총구 Flash | WpShtrMzfNml/Flash R+C4C=1202→variation5772의 vertex/fragment | 데이터·색/alpha·discard 판독 |
| 벽 Ripple | CmnWallSplash1Emit/Ripple R+C4C=1885→variation258 | 같은 범위 |
| 분열 ball_Copy1 | WpCmnBulletSplash1Emit→program1385/v5583 | 원시 Ast/Ipa export 누락 확인, VAT 재분석 아님 |
| custom shader 입력 | E+548 callback+50 또는 SDK080c620 기본 CSDP 바인딩 | 공급자 탐색 경계. callback 주소·실제 Custom1 값은 남음 |

variation 번호는 각 `.raw.json`/`.options.txt`의 원본 값을 우선한다. 아래 §10에서 자동 대조한다.

## 4. 구조체·필드·상수·열거형 표

| 항목 | 값·원본 계약 | 수준 |
|---|---|---|
| Flash A discard threshold | R+8A8=.5; 최종 remap 전 a<=.5이면 discard | [데이터]+[판독] |
| Ripple A discard threshold | R+8A8=0; remap 전 a<=0 discard | [데이터]+[판독] |
| Flash near fade | R890/894=(3,6), dyn[3].x 곱 | [데이터]+[판독-소비] |
| Ripple near fade | (3,4), dyn[3].x 곱 | [데이터]+[판독-소비] |
| Flash C0/A0 type | ANIM/ANIM: 키2/2 | [데이터] |
| Flash A1 | FIXED→PColor D5C=3; 파일 키10→3이 덮어써짐. 이 fragment의 alpha 계산은 A1을 읽지 않음 | 기존 패치 [판독] 재사용+현재 데이터/소비 판독 |
| Ripple A1 | ANIM: 2@.2→0@1; PColor3을 넣으면 틀림 | [데이터]+[판독] |
| p1385 location2.w | attribute byte172(0xAC): fragment Ipa PC0778에서 읽음, 원시 vertex Ast 전체에 해당 store 없음 | [판독-원시 명령] |
| p1202 location4.w | byte204(0xCC): fragment reader, vertex는192/196/200(xyz)=1만 export | [판독-원시 명령] |

## 5. 상태 전이와 전체 수명

Flash life5/GPU_TIME/NONE, start2·interval6+1=7f 무한 방출은 기존 데이터다. Flash의 밝기 C0은 모든 축 3.2@.15→2@.61, A0=1.5@.24→1@.58, scale=.583@0→.869@.14→.967@.31이다. 숫자는 원본 f32의 짧은 표시이며 정확한 비트/값은 audit.json에 둔다.

Ripple life8/GPU_TIME/NONE은 기존 데이터. 신규 연결: C0=2@.1→1@.5, A0=0@0→.3@.21→1@1, A1=2@.2→0@1. scale=(.3,3.6,.3)@0→(.9,1.2,.9)@.61→(.9,.2,.9)@1. 일반 Splash의 alpha1 FIXED3과 Ripple의 ANIM을 구분한다. 곡선·근접 fade·emitter dyn[3].x·최종 alpha remap은 별도 단계다.

## 6. 계산식·조건·상세 의사코드

### 6.1 Flash1202 [판독]

fragment287~302/475~485/515/625:

```text
T2A = texture(sysTextureSampler2, v2.xy).a
T1A = texture(sysTextureSampler1, v1.zw).a
rawA = clamp(T2A*T1A*v4.w*A0,0,1)*fade
if rawA <= .5: discard
RGBpre = v4.rgb*C0*mix(Custom1[3].rgb*Custom1[3].w,
                     Custom1[2].rgb,clamp(Custom1[4].z*.7,0,1))
Aout = clamp(fma(rawA,Custom1[11].x,Custom1[11].y),0,1)
```

T1.xy는 normal 텍스처 입력이며 RGBpre를 텍스처 R mask로 치환하지 않는다. v4.xyz=1은 원본 vertex export로 확인했다. **v4.w는 export되지 않아 runtime linked/default 값을 확정하지 않았다**. A1=3을 곱하지 않는다. 최종 RGB는 normal/SH/주광/동적광/environment/안개를 추가로 소비하므로 RGBpre를 화면색으로 쓰면 원본과 다르다.

### 6.2 Ripple1885 [판독]

fragment280~325/480/말미:

```text
rawA = clamp(fma(T0.a,v4.w,-A0)*A1,0,1)*fade
if rawA <= 0: discard
mappedA = fma(rawA,Custom1[11].x,Custom1[11].y)
if mappedA <= 0:
    RGBout=(1,0,0)   // 원본의 이 분기; 알파0을 이유로 식을 삭제하지 않음
else:
    RGBpre=v4.rgb*C0*동일 Custom1[2]/[3] 보간계수
    RGBout=normal·광원·반사·안개 소비 결과
Aout=clamp(mappedA,0,1)
```

v4는 이 shader에서는 **sysVertexColor0Attr**에서 export되며 .w도 명시적으로 쓴다(vert948~973). C1 가산이 없으므로 벽 Splash1886의 `(T0.rgb*C0+C1)*vRGB`와 다르다. `mappedA<=0` 분기의 붉은 RGB는 원본 그대로 기록하며 보기 좋게 바꾸지 않는다.

### 6.3 export 누락과 역번역 완전성 [판독]

새 shader_raw_audit는 BNSH bytecode/control을 복사하고 실제 바이트의 Maxwell 명령을 디코딩한다. shader header48+80B 이후32B마다 scheduling word를 제외했다. 전체 코드 길이는 원본 control+1784의 bytecode_len을 사용한다. p1385 vertex의 모든 Ast는32bit·고정 immediate 주소, 172를 쓰는 명령이 없다. p1202도204를 쓰는 명령이 없다. 즉 단순 GLSL 출력 정리로 그 store가 사라진 것으로 채울 수 없다. 하드웨어의 linked/default 공급을 확보하기 전 alpha를1/3으로 대입하지 않는다.

색 보정 조사에서 standard shader_dump의 IGpuAccessor가 c1 상수를 번역 후 GLSL에만 치환하고, **Decoder의 BRX target read에는 기본0**을 공급하는 문제가 발견됐다. 실제 inline 상수의 `ConstantBuffer1Read`를 web/tools/shader_dump에 연결했다. 1202/1885/1385의 vert+frag **6파일은 기존과 보완 출력 SHA256 전부 동일**다. 이3개 표본의 결과가 같다고 전체 shader dump가 완전하다고 주장하지 않는다. CCLUT 분기는 실제로 복원됐다([ink_lighting_r2](../graphics/ink_lighting_r2.md)).

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

| emitter | sampler 슬롯→실제 텍스처 |
|---|---|
| Flash | 1 splash04_nrm, 2 splash04_fi; 함께 직렬화된 0 gradation02_fi는 이 fragment가 읽지 않음 |
| Ripple | 0 pattern01_fi, 1 pattern01_nrm |

primitive 이름이 빈 문자열로 나오는 데이터는 없다고 단정하지 않았다. muzzle 부착/ELink 인계는 기존 원본 경로를 연결해야 한다. 원본 emitter start/interval과 탄6f를 같은 수명으로 묶지 않는다.

## 8. 다른 기능과의 상호작용

원본 팀색의 dyn[0]/[1] runtime writer와 Custom1 공급자가 확보되기 전 현재 웹 teamcolor를 대응값이라고 승격하지 않는다. shader의 colorScale·ANIM·FIXED 패치·vertex color·near fade·discard·alpha remap·postprocess는 서로 다른 입력이다. gun 탄 생성/연사 원본 포트가 있어도 이 부분이 자동 반영되지 않는다.

## 9. 웹 포팅 구조와 구현 순서

FX02/03/04: main/splash VAT 분리 이후 Flash1202와 SplashCorn1747, 벽 Ripple1885와 Splash1886을 각각 원본 shader/asset로 연결한다. 두 텍스처 A의 곱, 빼기 alpha0·곱하기 ANIM alpha1, `.5` discard와 C0 키를 명시적으로 분리한다. 소스 구현은 이번에 수정하지 않았다. linked/default와 Custom1 값은 미확정으로 유지하며, 공급자를 확보하기 전 해당 전체 항목을 반영 완료로 처리하지 않는다. 구현 요약은 [port/ink_visuals](../port/ink_visuals.md).

## 10. 검증 코드·실행 결과·기대값

실제 명령·실패는 `analysis/visual_gap_r2/fx/commands.md`. 새 `web/tools/fx_shader_gap_audit.py`는 실제 v46 값을 읽고 raw Ast/Ipa 및 old/fixed GLSL hash를 검사한다. 3프로그램/6 stage 출력 동일, p1385 export172없음/p1202 export204없음 확인. **GPU를 실행한 테스트가 아니며 native sin/FMA 픽셀 비트 일치를 주장하지 않는다.**

ShaderParam 문자열 후보084c968은 func_lookup으로084c78c를 찾고 full_decomp했다. 원본 함수의 ReferSymbol `NintendoWare_Font`와 PerCharacterParamBlock을 확인하여 **폰트 후보로 제외**했다. 이 결과로 VAT 시간률을 확정하지 않았다. CSDP100B/CADP4B 원시 자료도 추출했으나 UBO1 offset과 연결하지 못했으므로 공식 필드 이름을 붙이지 않았다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 남은 질문 | 시도·막힌 이유 | 다음 원본 |
|---|---|---|
| p1385 v2.w / Flash v4.w 실제 입력 | raw Ast/Ipa와 보완역번역까지 확인, compiler export 없음 | NVN varying/default 설정·linked attribute state·draw submit |
| VAT Custom1[12].x·alpha remap[11].xy | 소비식/실제 CSDP/CADP·SDK resource/callback 경로 확보; 잘못된 Font ShaderParam 후보 제외 | E+548 callback+50 등록 producer, SDK080ca78의 callback table 인자, draw080f0bc 주변 |
| 실제 팀 dyn[0]/[1] | 기존 OneEmitter matrix큐와 shader reader 재사용; runtime color source 연결 없음 | ELink ForceTeam32/OneEmitter team slot→EmitterSet dyn color writer |
| 전체 GPU 출력·primitive/default | 원시 export와 shader 데이터만 확보 | NVN draw command+원본 GPU 실행 |

색 조합 inventory는 위 공급자가 함께 남아 있는 혼합 질문이므로 조사중을 유지한다. shader 두개 판독만으로 전체 combiner를 확정 승격하지 않았다.

