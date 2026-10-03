# 사격장 잉크·발사·변신·광원 시각 경로 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

사용자가 지적한 “잉크/총 쏘기/바닥 잉크/오징어 잠영/광원이 원본과 다름”을 현재 코드와 원본으로 분리 추적한다. 탄·총 로직 포트 종료 뒤 수행한 **추가 분석**이다. 이 후속 분석에서 client/core/에셋을 변경하지 않았다. 구현 지시용 요약은 [port/ink_visuals](../port/ink_visuals.md).

핵심: 바닥은 collision overlay 일반 PBR이고 native ColPaint ink 분기가 연결되지 않았다. 탄 파티클은 VAT/조명/두 색 조합을 생략하고 분열 탄까지 같은 main emitter를 사용한다. 오징어 모델 선택은 있지만 **B7a0 숨김 producer/consumer가 렌더에 없다**. 이미 반영한 주광10·베이크75·HDR만으로 이 경로들이 원본과 같아지지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

v0 Lby_Lobby00 1인 Shooter_Normal_00. 신규: `analysis/visual_gap/p1385.vert/.frag/.options.txt`(program1385, variation5583), `p1385_evidence.json`, `display_gate.json`. 입력 shader는 기존 추출 `analysis/assets_work/r6/static.vfxb`의 GRSN: offset54706176/64676952B, SHA256 기록은 `grsn_extract.json`. original/키는 읽기 전용 유지.

먼저 SHARED/FUNCS와 `decomp_index.py --no-build ball_Copy1/0x710243e2dc`를 확인했다. p1383 VAT·OneEmitter 슬롯/분열 emitter 값·B7a0 writer·map ink식·광원 값은 **기존 분석 재사용**이며 새 발견으로 세지 않는다. p1385 소비 셰이더 판독과 display entry 실행을 보완했다.

## 3. 진입점과 전체 호출 흐름

| 화면 | 원본 경로 | 현재 웹 경로 |
|---|---|---|
| 바닥 잉크 | ColPaint panel/atlas→모델 속성 _pu0/1/2→shader1714/946 ink branch→native forward/HDR | paint request→독자 charts RGBA8→collision overlay→MeshStandardMaterial→HDR |
| 메인 탄 | BulletShooterBase vt106 1753bb4→OneEmitter slot0→WpShtrBullet1Emit/ball→p1383 | BulletSpawn→같은 이름 batch→프리미티브/구·공통 GLSL |
| 분열 탄 | BulletSplashShooter vt106 17ffc60→slot800→WpCmnBulletSplash1Emit/ball_Copy1→p1385 | Splash도 WpShtrBullet1Emit→공통 GLSL |
| 머즐 | InkAction→ELink 무한 emitter/인계→Muzzle bone matrix/dot→p1747 등 | 이벤트/ELink→shared muzzle 없으면 마지막 탄 위치/방향 근사 |
| 변신/잠영 | 248c6fc B7a0→243e2dc SM 표시→14595b0 holder→모델/재질·ASB | p.state/formCounter→animator.disp→player.draw, B7a0/숨김 입력 없음 |
| 광원 | MainLight/베이크/SH/spot/cubemap·shader 재질 소비→HDRCompose | map known forward 일부→HDRCompose; paint/fx 별도 재질 |

## 4. 구조체·필드·상수·열거형 표

| 입력·writer/reader | 확정 값/계약 | 수준 |
|---|---|---|
| B7a0 byte / 248c6fc→243e2dc | 지연된 ordinary ally squid 및 특수 후보 OR, 켜지면 body/hlf/squid/rail 모두0 | 기존 [판독], 표시 진입 블록 신규 [실행-부분] |
| SMf0 / 표시 reader | humanOn && f0≥61 && type!=Rival이면 Hlf, 그 외 body | [판독]+신규 [실행-부분] |
| p1385 sampler2 / VAT | bulletcmn_vsp, H64×W8 RGBA16F; row=trunc(sysTexCoordAttr.z) | [데이터]+[판독] |
| p1385 UBO Custom1[12].x | VAT 시간률 k; 런타임 producer 값은 미확정 | [판독-소비자]/[미확정-공급자] |
| p1385 emitter C0/alpha0 | C0=static[104].rgb×dyn[0].rgb×static[103].x, A0=static[112].x×dyn[0].w | [판독] |
| p1385 fragment final A | clamp(fma(clamp(v0.w*v2.w)*v1.x,Custom1[11].x,Custom1[11].y)) | [판독-식], v2.w 연결/최종값 미확정 |
| Map InkUBO Day | roughness .05/Fresnel .015/normal1.8/aniso.5/rim.625/blend.875 | 기존 [데이터]+[판독] |
| 현재 paint material | roughness .35/metal0/LIFT.02/threshold.3/동률 첫 채널 우선 | 웹 정적 판독, 원본 값 아님 |
| 현재 주광·베이크 | MainLight10·native bake75, 실제 env parse 사용 | 기존 포트 검증, GPU 전체 동등성 아님 |

## 5. 상태 전이와 전체 수명

변신 state82→84→85/87과 f0/클립 끝/블렌드는 기존 [player_state](../player/player_state.md) §6 및 [player_assembly](player_assembly.md) §5.4에 따른다. **모델이 오징어로 바뀌는 것과 자기 잉크에서 모델을 숨기는 것은 별도 조건**이다. B7a0는 평지 자기 잉크에도 쓰며 벽 전용 bool이 아니다. 지연 counter B794/B798를 보존해야 한다. 임의로 `squid&&swimming`인 프레임마다 즉시 숨기면 원본 지연을 잃는다.

머즐은 FireImpact/FireOn trigger 인계로 이벤트 하나가 유지된다. SplashCorn 시작2 이후5프레임 간격/Flash7프레임 간격은 기존 [effect_sound](../effect_sound/effect_sound.md) §3.2/[effect_resources](../effect_sound/effect_resources.md) §2.2.6의 원본 데이터다. 탄 6프레임마다 플래시를 강제 재시작하는 구현은 원본 근거가 아니다.

분열 ball_Copy1도 life120 CPU/follow ALL이다. p1385에서 birth>now 또는 age≥trunc(life)이면 draw를 비활성화한다. scale 키3개와 VAT 시간은 다른 소비자이며 한 가지 lifetime 비율로 통합하지 않는다.

## 6. 계산식·조건·상세 의사코드

### 6.1 분열 탄 VAT — 신규 [판독]+[데이터]

p1385.vert315~330:

```text
W=textureSize(sampler2).x; t=now-birth; k=Custom1[12].x
q=clamp(min(fma(1/(W+1e-5),t*k,1e-5),.99999),0,1)
f=W*fract(q); x0=trunc(f); x1=(x0<trunc(W-1))?x0+1:x0
row=trunc(sysTexCoordAttr.z); w=fract(f)
P=fma(P1-P0,w,P0)
```

q를 먼저 .99999로 제한하므로 VAT는 끝에서 멈춘다. 무조건 반복 fract(t/life)로 바꾸지 않는다. A 두 샘플은 half 비트를 복원하고 compact normal을 각각 풀어 보간한다. 압축 j/phi/극 성분 식은 [effect_resources §2.1.1](../effect_sound/effect_resources.md#211-탄-ball-vat-적용식-프로그램-1383-판독)과 같다.

**좌표 순서 보완/정정(2026-10-03):** 기존 §2.1.1의 복호화 수식은 구면 좌표 표기 `(sinθcosφ,sinθsinφ,z)`를 썼지만 **실제 회전 입력은 `(sinθcosφ,z,sinθsinφ)`**이다. p1385 temp137/138/139(517~546), p1383 temp135/129/136(508~530)이 이를 확정한다. 극 성분 z를 로컬 Y에 넣는다. 이미터 추가 법선 항도 원본의 VAT P.xyz를 그대로 더한다. 기존 문장을 삭제하지 않고 소비 좌표 정정을 남겼다. 임의 normalize/acos 교체 금지.

p1385.vert497/502/508: C0=static104.rgb×dynamic0.rgb×colorScale(static103.x). position/normal은 별개로 회전·동적 행렬을 거쳐 fragment in_attr4/3으로 전달된다. shader normal 기반 주광/SH/dynamic grid와 environment array **layer6** texture 소비가 존재한다(fragment377). 웹 공통 particle FRAG는 texture.R mask와 단색 alpha만 사용하므로 이 조명 경로가 없다.

p1385.frag513의 최종 alpha식은 표 §4대로다. **vertex dump에 location2 export가 없는데 fragment는 in_attr2.w를 읽는다.** GLSL 출력/옵션/geometry 출력 존재 여부를 확인했으며 이 CLI에서는 geom이 생성되지 않았다. 따라서 emitter alpha1=3 데이터만으로 그 varying을3이라고 대입하거나 최종 투명도를 확정하지 않는다. 실제 Maxwell export/default·파이프라인 연결을 다음 근거로 둔다.

### 6.2 바닥 잉크 표시 — 기존 근거 연결

[stage_rendering §7](stage_rendering.md#7-맵-위-잉크-판독-셰이더-1714): native UV 후보 선택/반전, 최대 채널 근처 1e-4 동률 mask, 표시 비교는 단순 `max≥.3` 대신 `min(clamp(max-.3)*1000,1)>.5`. InkBright*.625→Ink를 clamp((max-.3)*.875)로 보간하고 거칠기.05·neighbor 차분 법선×1.8·층12 반사·thickness(바닥.95/벽.75)를 소비한다.

현재 source는 최대 채널 한 색만 선택, roughness.35이며 위 branch 전체가 없다. ColPaint UV/basis 공급을 연결한 뒤 같은 모델 재질에서 합성해야 한다. **색/roughness 숫자만 바꾸는 것은 전체 반영이 아니다.** [22].w나 최종 cube/LUT 등 미확정 값은 임의로 채우지 않는다.

### 6.3 숨김 gate — 신규 원본 실행(진입 블록)

243e2dc 진입부터 ordinary/invalid-rail branch 끝 e460/e464/e488 전까지 실행한다. rail handle의 index=-1을 공급, B7a0/human/squid/f0/modelType을 바꾼다. B7a0!=0→SMf4/f5/f6/f8=0. 꺼져 있으면 body/hlf/squid flag를 원본식대로 만든다. 64/64 일치, PLT/미매핑0. **B7a0 producer·이후 counter/NaN reset/holder·전체 actor frame은 실행하지 않았다.**

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

- ball_Copy1의 native CSDP/CADP·primitive vertex row·bulletcmn VAT·전용 emitter를 보존한다. VAT texture를 일반 R opacity 텍스처로 사용하는 것은 원본과 다르다.
- Muzzle bone 행렬은 캐릭터 Weapon_R→무기 Root→Muzzle chain을 소비한다. 탄 생성원점과 머즐 시각 부착점을 같은 값이라고 가정하지 않는다.
- 몸/얼굴 _Thc.R→1-R·backlight/source4·film/SSS 및 squid 재질/가시성 leaf는 [calc_thickness_runtime](calc_thickness_runtime.md)/[anim_state_machine](anim_state_machine.md) 근거를 사용한다. 스켈레탈 clip만 재생해서 완료 처리하지 않는다.
- 잠영 상태/애니 clip 이름과 ELink follow/수명은 실제 원본 producer를 함께 연결해야 한다. 파문 이름/크기/밝기를 시각 추측으로 추가하지 않는다.

## 8. 다른 기능과의 상호작용

발밑 sample MOV04/PNT05는 이동·B7a0·회복·잠영 효과 입력이다. 현재 inkFastStealth가 없으면 swimming 근사로 회복하지만 render PlayerSnap에는 그 숨김 bool 자체가 없다. 물리/칠 판정/화면을 각자 다른 값으로 계산하지 않도록 공용 계약을 먼저 연결한다.

현재 paint의 **정상 env 경로는 parseEnv를 공유하여 주광10**을 사용한다. source의 DAY_LIGHT4는 읽기 실패 fallback이다. “항상 주광4라서 잉크가 다름”으로 단정하지 않는다. 큰 차이는 바닥 material/normal/조명 합성의 미반영이다. 기존 주광/베이크/HDR 포트는 유지해야 한다.

## 9. 웹 포팅 구조와 구현 순서

P0: (1) PNT02/06 모델 ColPaint+ink branch (2) GR01/02 B7a0 delayed producer→display·ASB 재질/가시성 (3) FX03 분열 전용 슬롯+VAT/조명/색·alpha (4) FX02/01 Muzzle bone·emitter SRT/인계 (5) GR05/06/07 cube/shadow/LUT/bloom. 병렬 구현 시 같은 team/UV/frame/hidden provider를 공유한다. 상세 지시 단위는 [port/ink_visuals](../port/ink_visuals.md).

## 10. 검증 코드·실행 결과·기대값

| 실제 명령 | 결과 | 확정 경계 |
|---|---|---|
| shader_dump prog-bfsha … --index1385 | vert/frag/options 생성 exit0 | Maxwell shader 역번역 [판독], 원본 GPU 실행 아님 |
| PY web/tools/ink_visual_audit.py | display64/64, PLT0/fault0 | native 진입 블록 [실행-부분] |
| 같은 도구 bulletcmn_vsp | H64×W8/512half 복원 일치, bad0 | 실제 데이터+재구현; GPU 비트 결과 아님 |
| 기존 SHARED/FUNCS/decomp_index | 슬롯·B7a0·ground/light 기존 분석 확인 | 중복 원본 분석률 증가 없음 |
| visual_smoke.mjs 초기 실행 | render.post 90s timeout | 화면 검증으로 사용하지 않음, 재시도/실패 상태 보존 |
| visual_smoke.mjs 재시도(180s) | human/firing/own ink squid 3단계 성공; console/page/HTTP0 | 실제 웹, 자기 잉크 stamp 합성 입력; 원본 GPU 아님 |

브라우저 own_ink_squid: state0x85/ownInk ratio1/swimming=true, stealth59/blend1인데 displayS·visible meshes2다. paint.page0는 MeshStandardMaterial/roughness.35/metal0/envMap없음이다. human/firing은 body24개, 실제 Fire/BulletSpawn 이벤트 확인. 자료 visual_smoke.json/3PNG. 실패/재시도 명령은 `analysis/visual_gap/commands.md`. GPU 최종 픽셀/원본 실기 비교는 수행하지 않았다. 현재 core/client 변경이 없으므로 gun 종료 시153/153/typecheck/build 결과를 유지하며 분석 도구 실행만 추가했다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 남은 원본 질문 | 시도/막힌 곳 | 다음 근거 |
|---|---|---|
| p1385 fragment v2.w·최종alpha | vert/frag/options/geom 존재 확인; export 누락 | Maxwell output 명령·linked attr/default fill·renderer submit |
| Custom1[12].x k/추가법선[14].y | shader 소비자 확보; emitter 일반 의미 불명 | custom shader UBO writer/OneEmitter instance 입력 |
| floor neighbor UV [22].w/whole native atlas·raster | 기존 일부 실행/모델 binding 재사용 | paint UBO writer·실제 ColPaint scene 자료/GPU |
| Lby 최종 cubemap/SH/LUT/variant | 기존 capture/CPU/셰이더근거, 원본 GPU 입력 미확보 | stage capture submit·PMREM 대신 native prefilter·CC shader |
| B7a0 whole player/표시·잠영 효과 원본 frame | entry block64, writer 기존판독; whole 실제 입력 미실행 | 2483134→248c6fc→249648c→holder/ELink 실제 연결 |

원본 inventory의 혼합 질문은 전부 닫힌 경우만 확정으로 바꾼다. 이번 부분 실행/새 shader 판독으로 넓은 GPU/render 질문을 전체 확정으로 승격하지 않는다.

### 추가 분석 r2 — 2026-10-03

앞선 시각 분석 이후 새 근거는 [바닥 UBO 입력](floor_ink_inputs_r2.md), [잠영 지연·모델 표시](squid_ink_visibility_r2.md), [Flash/Ripple shader 입력](../effect_sound/fx_shader_inputs_r2.md), [잉크·캐릭터 색 보정 공급](ink_lighting_r2.md)에 분리했다. 기존 p1385/표시entry64건을 신규 실행으로 중복 계산하지 않는다.

- 바닥: 원본 init→texel→whole vec4 staging pack28/28. Z의 두 store는 모두 Z이며 W 초기0을 보존한다. 기존 BigWorld 비교 판독을 연결하면 **Lby S400/Z1⁄3200**. W 전체 후속 writer/atlas/GPU는 미확정이다.
- 셰이더 보완: near-max 팀 선택은 boolean만이 아니라 `clamp((channel−max+9.99999975e−5)*1e8,0,1)`의 좁은 ramp다. V 반전 **뒤** neighbor를 더한다. 기존 §6.2의 boolean 요약만으로 구현하지 않는다.
- FX: p1202 Flash는 두 텍스처A 곱과raw alpha≤.5 discard; p1885 Ripple은alpha0빼기·ANIM alpha1곱, C1가산없음. p1385 v2.w와Flash v4.w는 원시Maxwell에서도store없음을 확인했으나실제default/linked값은미확정이다.
- 잠영: ordinary 후보 생산 블록 **10,800건**, 초기512·법선4,096·지연8,192·whole 표시2,048·holder4,096건, 수동 연결272프레임 모두 일치했다. off 바인더 캐시 NaN과 실제 재질 setter0은 서로 다르다. 실제 StepPaint/Phive 공급·전체 player 프레임·GPU·파문은 남아 있다.
- 색 보정: 원본 CPU 공급 계약 **128/128** 및 LUT 좌표 블록 **128/128** 일치. 기본 로비는 **HSV Value1.0625→RGB8점 표본 보간→Gamma**, N8 좌표 scale=.875/bias=.0625다. A표본·실제 GPU LUT와 최종 sampler/variant는 이 실행에 포함하지 않았다.
- 분석 도구: c1 inline constants를Decoder BRX target read에공급하도록standard shader_dump를보완했다. 기존 CCLUT switch가누락됐던원인을기록했고canonical/독립보완본출력이같다. 세FXshader6stage출력은보완전후동일했다. shader판독을GPU실행으로승격하지않는다.

나머지 실행 수·경계·실패·정정은 각11절 문서와 `analysis/visual_gap_r2/*/commands.md`에 둔다. 원본고정986·포트고정62의전체질문이닫히지않은행은상태를유지한다.


## 재질·눈 패턴·총구 그래픽 r9 — 2026-10-03

[현재 반영·검증·다음 지시](../port/graphics_priority_r9.md): 탱크/하네스/병의 native 재질·owner texture, raw type11 눈 채널, [Maya0/rotation0 UV6lane](character_texsrt_r9.md), [실제 Muzzle 시각 행렬 및 내적 정정](../effect_sound/muzzle_attachment_r9.md)을 웹과 MD에 반영했다. FMAA 원본1,212/피부 홀더67/SRT313/내적 격리블록2,048, 선택 GLSL↔웹GPU448건은 각각 범위가 다른 검증이며 원본 NVN/전체프레임 일치가 아니다. 초기 표의 탱크/눈 UV와 shared muzzle 누락은 r9 한정 범위에서 후속 반영했다. 머즐 부착과 내적의 선택 뼈를 동일한 원본 근거로 보지 않는다.

고정 원본556/986=56.39%·그래픽102/204=50.00%, port13/62=20.97%(일부37/차이9/원본미확정3)·GR0/10/일부7/10 유지. 신규 부분 근거를 기존 복합 질문 전체 확정으로 승격하지 않았다. 몸CP/skin idx·weighted type11/type18·다른 SRT mode/rotation·cube/BRDF/SPP·잠영 파문/Custom1/VAT·native 최종픽셀은 남는다. 최종 테스트·브라우저·보호 SHA와 실패는 r9 요약의 실행 기록을 따른다.
