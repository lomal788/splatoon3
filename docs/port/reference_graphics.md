# 첨부 원본 화면 대응 — 그래픽·이펙트 우선 반영 지시 (2026-10-03)

현재 구현이 원본과 크게 다른 원인을 **실제 데이터 전달과 셰이더 소비의 누락**으로 확인했다. 이번에는 분석과 MD만 반영했다. [사진·현재 화면 대조](../graphics/reference_graphics_gap.md), [잉크 표면](../graphics/reference_ink_surface.md), [발사·잠영 이펙트](../effect_sound/reference_shooter_visuals.md), [캐릭터·광원](../graphics/reference_character_lighting.md), [최종색](../graphics/reference_hdr_output.md)에 근거를 기록했다.

| 고정 기준 | 현재 전체 항목 충족 | 이번 변화 |
|---|---:|---|
| 원본 전체 inventory | 556/986 = 56.39% | 전체 질문 승격 0 |
| 원본 그래픽 | 102/204 = 50.00% | 부분 셰이더·소비 근거 추가, 분모·분자 유지 |
| 원본 도색 | 52/100 = 52.00% | 분모·분자 유지 |
| 원본 이펙트·효과음 | 60/140 = 42.86% | 부분 이펙트 계약 추가, 분모·분자 유지 |
| 웹 전체 반영 확인 | 13/62 = 20.97% | 코드 변경 0 |
| 웹 그래픽 GR01~10 | 0/10 = 0.00% (일부 반영 7/10) | 화면 전체 동등성 미완료 |
| 웹 이펙트 FX01~04 | 0/4 = 0.00% (일부 반영 3/4) | 실제 누락 확인, 코드 미반영 |

이 수치는 고정 항목의 전체 질문을 충족한 비율이다. 로드한 모델·재질 수나 화면 유사도 점수가 아니다. 새 검사를 통과한 부분을 전체 GPU 동등성으로 승격하지 않았다.

| 우선순위·기존 항목 | 이번에 확인한 차이 | 반영할 일과 완료 조건 |
|---|---|---|
| **P0 FX03/04: 번들→실행기** | 실제 39개 emitter에서 scale/alpha0/color0 animation key가 fields만 전달하는 과정에서 유실된다. 실행기는 기본 키 1개를 사용한다. | 원본 key/count/frame을 추출→collectEmitters→ParticleBatch까지 보존. 다중 키가 있는 scale 31개·alpha0 33개·color0 18개로 성장·축소·소멸을 연속 검증. |
| **P0 도색+GR03/04/05: 지형 잉크 표면** | collision overlay·roughness .35·단일색·환경맵 없음. native ColPaint·InkBright·경계 normal·두께·반사 분기가 연결되지 않음. | 실제 visual model 속성·atlas를 원본 잉크 셰이딩에 연결. roughness .05 한 값만 바꾸는 것으로 완료하지 않음. |
| **P0 FX02/03: 탄·튀김의 입체감** | 실제 FX GLB 26개의 normal, 15개의 tangent와 color, 2개의 UV1이 실행기 geometry에서 유실됨. unlit 재질·동일 blend/depth/cull을 사용함. | 속성·VAT 및 발사·분열·착탄의 원본 emitter/shader 선택 복구. emitter별 opaque/depth-write/cull·두 색·alpha 계약을 검증. |
| **P0 GR03: 피부·머리·오징어** | native enable_taransmission 철자, cheapSSS/edge/film 소비가 빠짐. _Thc/_re2를 준비해도 셰이더 sampling은 0. | MAi.R·Thc.R·역광·film→SHNormal/diffuse/tau와 실제 팀색·광원 alpha 연결. 4개 material hook과 원본 셰이더 항을 함께 검증. |
| **P0 GR01/FX01: 잠영·표면 파문** | ownInk=1·swimming=true에서도 squid mesh 2개 표시. SplPlayer leaf/emitter 자원 연결 없음. | B7a0·표시 holder의 모델 숨김과 원본 player emitter 13개·ELink leaf 9개의 상태·행렬·수명을 연결. 마른 바닥·잠영·대시·발밑 ripple 구분. |
| **P0 GR07: 최종색** | LUT/Bloom/Vignette가 없고 gamma1은 웹 선택. 원본 8³ LUT는 RGB11/11/10 unsigned floating·4B/texel·level1. | native CC 목록·저장 양자화·sampler·Tone4 뒤 LUT 연결. 노출/Bloom→Tone4→LUT→Vignette→Gamma 순서 보존. |
| **P1 GR02/06/08/09: 애니·그림자·cloth·LOD** | WeaponDetail 빈 값, 재질·가시성 애니와 그림자·cloth·LOD의 일부 계약 미반영. | 원본 AS·뼈·표시·그림자·cloth·LOD 명세 소비. 40프레임 발사 유지의 state 0x59는 확인했으며 최종 Shoot 포즈 검증은 별도. |
| **분석 선행 검사: 셰이더 도구** | Negate를 괄호 없이 출력해 곱셈의 의미가 바뀜. BRDF y는 −roughness, cube layer12는 bias0이며 명시적 mip0이 아님. | 원시 명령·분석 전용 보완 출력으로 식 검사. 표준 CLI는 이번에 수정하지 않았으므로 기존 GLSL을 그대로 기대값으로 삼지 않음. |

바로 지시할 수 있는 작업:

1. **“이펙트 animation key 전달 유실부터 고치고, 원본 속성·VAT·blend/depth/cull 계약까지 발사·탄·착탄 화면에 연결해줘.”**
2. **“바닥·벽 잉크를 실제 ColPaint visual mesh와 원본 잉크 셰이딩으로 연결해줘. normal·두께·InkBright·반사를 함께 반영해줘.”**
3. **“캐릭터·오징어의 cheapSSS·투과·film 소비와 잠영 숨김·파문을 원본 명세대로 연결해줘.”**
4. **“원본 CC LUT·샘플러·저장형식을 확인해 최종 HDR 경로에 반영하고 같은 사격장 조건으로 화면을 비교해줘.”**

첨부 사진의 보라·노랑과 현재 Lby 팀색은 동일 조건이 아니다. stage·camera·teamcolor·frame·paintmask를 맞춘 원본 캡처가 없어 픽셀 동일성은 미확정이다. 확인된 누락 경로부터 연결하고, 임의 색·밝기 배율로 원본값을 대신하지 않는다. 실제 명령·실패·검증 경계는 각 상세 문서 §10과 [completion_run](../completion_run.md)에 기록했다.


## 후속 실제 반영 — 2026-10-03

위 표는 r3 분석 당시 상태다. 후속 지시로 animation key·FX 속성·VAT·렌더 상태와 마우스 시점을 실제 반영했다. [현재 결과](priority_1_4.md): 로더39/39, known shader17/39, VAT2/2, 전체 test226/226·타입 검사·빌드·브라우저 오류0. ColPaint 표면·캐릭터/잠영·HDR/LUT 전체는 이번 범위에 포함하지 않았으며 원본 전체 pixel 동등성은 남는다.

## 6번 공통 경로 후속 반영 — 2026-10-03

[common_render_r5](common_render_r5.md)에 SH7MRT·2shadow·nativecurve8³LUT의 실제연결을 기록했다. 전체252/252·GPUshadow13/13·post36/36·actualLby오류0. 위r3/r4의미반영LUT·single shadow·Three SH항목은이후수정됐다. nativeBloom/DOF/전체cube/활성flag·ColPaint/SSS/잠영은여전히남는다. whole원본/웹고정점수는유지.


## 공통 경로 r6 후속 웹 반영 — 2026-10-03

[현재 구현·검증·잔여](common_render_r6.md). mSky cube27의 채도 .4, 원본 PCF/strict 캐스케이드/SPP·Default fade40~60, DefaultDay old_calc=false Bloom producer와 HDR 소비를 연결했다. 전체266/266·typecheck/build PASS, 실제 Lby4단계·GPU오류0. Sky21/Shadow25/Bloom18 웹 GPU 검사와 원본 writer1,024·Bloom블록/파서775건을 구분한다. native Illuminate/12layer·live sampler/SPP/HDR alpha·DOF·ColPaint·캐릭터/잠영은 남는다. 고정13/62=20.97%, GR0/10·일부7/10 및 원본556/986는 유지한다.


## 바닥·벽 잉크 표면 r7 실제 반영 — 2026-10-03

[현재 구현·검증·다음 지시](ink_surface_r7.md). 띄운 collision overlay를 actual visual triangle draw로 옮기고 packed UV/switch/tangent, InkBright·rim·normal1.8·floor/wall thickness·F0.015/roughness.05와 공통 베이크/SH/그림자/HDR 조명을 연결했다. 원본 leaf writer277/panel256/변환블록128 입력 대조, WebGL 판독slice↔포트431건, 전체285/285·typecheck/build·actualLby4단계 오류0. 전체원본GPU/atlas 동등성은 아니다.

PNT06 차이→일부이며 **고정13/62=20.97%, 일부37/차이9/미확정3**, GR0/10·일부7/10, 원본556/986=56.39% 유지. native atlas/seam·BRDF/cube12/Illuminate·W 후속writer/환경emission·캐릭터SSS/film·잠영숨김/파문이 남는다. 과거 collision overlay/.35 설명은 당시 사실로 보존하며 현재상태는 r7 링크를 따른다.


## 캐릭터 그래픽 r8 실제 반영 — 2026-10-03

[현재 반영·검증·다음 지시](character_graphics_r8.md): body/face cheapSSS·Thc 역광, hair/squid film·2cl 보정 법선, RGBA 강도, B7a0 지연 숨김/복귀, 슈터 Shtr/Shtr를 웹에 연결했다. 전체304/304·typecheck/build, WebGL 판독식512건, actual Lby12단계 오류0. 원본 NVN/전체 프레임 동등성은 아니다.

고정13/62=20.97%(일부37/차이9/미확정3), GR0/10·일부7/10, 원본556/986=56.39%·그래픽102/204=50.00% 유지. 추가 재질3개/live 몸 잉크·type11/18·SPP·cube12/BRDF·벽/상승 공중 producer·잠영 파문은 남는다. 이전 '캐릭터SSS/film/B7a0 전체 미연결' 설명은 당시 기록이고 최신 한정 반영은 r8 링크를 따른다.


## 재질·눈 패턴·총구 그래픽 r9 — 2026-10-03

[현재 반영·검증·다음 지시](graphics_priority_r9.md): 탱크/하네스/병의 native 재질·owner texture, raw type11 눈 채널, [Maya0/rotation0 UV6lane](../graphics/character_texsrt_r9.md), [실제 Muzzle 시각 행렬 및 내적 정정](../effect_sound/muzzle_attachment_r9.md)을 웹과 MD에 반영했다. FMAA 원본1,212/피부 홀더67/SRT313/내적 격리블록2,048, 선택 GLSL↔웹GPU448건은 각각 범위가 다른 검증이며 원본 NVN/전체프레임 일치가 아니다.

고정 원본556/986=56.39%·그래픽102/204=50.00%, port13/62=20.97%(일부37/차이9/원본미확정3)·GR0/10/일부7/10 유지. 신규 부분 근거를 기존 복합 질문 전체 확정으로 승격하지 않았다. 몸CP/skin idx·weighted type11/type18·다른 SRT mode/rotation·cube/BRDF/SPP·잠영 파문/Custom1/VAT·native 최종픽셀은 남는다. 최종 테스트·브라우저·보호 SHA와 실패는 r9 요약의 실행 기록을 따른다.
