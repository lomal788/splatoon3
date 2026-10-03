# 잉크·발사·오징어 잠영·광원 반영 지시 요약 — 2026-10-03

탄·총 로직 반영 뒤 현재 화면/소스와 원본을 추가 대조했다. **초기 후속 작업은 분석과 MD 반영**이었다. 초기 차이표는 당시 기록으로 보존하고, r7의 실제 지형 잉크 반영은 아래 후속 기록을 우선한다. 자세한 11절 원본 근거·명령·미확정은 [graphics/ink_visual_path](../graphics/ink_visual_path.md).

전체 소스 반영률은 고정62개 **13/62=20.97%**. 이 문서가 추적하는 기존16개 ID의 반영 확인은 **0/16=0.00%**, 일부13·차이2·원본 미확정1이다. 새 질문으로 분모를 늘리거나 부분 결과에 점수를 주지 않았다. 그래픽 작업이 전혀 없다는 뜻이 아니라, 각 고정 항목의 남은 조건이 닫히지 않았다는 뜻이다.

| 착수 순서 | ID·상태 | 실제로 다른 것 | 반영해야 할 결과 | 근거/검증 |
|---|---|---|---|---|
| **1. 바닥 잉크 재질·표면** P0 | PNT02 차이, PNT06/03/05 일부 | r7에서 실제 visual draw·packed UV/tangent·InkBright/normal/rim/thickness/.05/.015·공통 조명은 연결. custom chart/atlas·native seam/BRDF/live 입력 차이가 남음 | 원본 ColPaint panel/basis/atlas→두 panel seam·시각 모델 UV를 연결하고 native 환경반사·W/emission 공급 확인 | [현재 반영·실제 검증·잔여](ink_surface_r7.md), [좌표](../graphics/ink_visual_geometry_r7.md), [shader](../graphics/ink_surface_web_r7.md). 부분 결과를 whole atlas/GPU 완료로 세지 않음 |
| **2. 오징어 변신·잠영 표시** P0 | GR01/02·MOV04 일부 | 모델 전환은 하지만 자기 잉크 swimming=true에서도 squid 메시2개가 보임. B7a0 지연 hide/ASB 재질·가시성 공급 없음 | 248c6fc의 B794/B798 지연→B7a0→243e2dc→holder 표시. state/클립 tick/끝·Hlf·NaN reset·재질 leaf를 연결 | 원본 표시 entry64/64, 웹 ownInk=1/state85/swimmingtrue에도 displayS/2meshes. 즉시 squid&&swimming 숨김으로 대체하지 말 것 |
| **3. 실제 탄·분열 탄 표현** P0 | FX03/04 일부, GR03 일부 | Splash도 WpShtrBullet1Emit 사용, VAT 없고 texture.R mask/단색. 원본 normal·환경/동적광·색/alpha 조합 없음 | slot0 main1383 vs slot800 WpCmnBulletSplash1Emit/ball_Copy1 p1385 분리. primitive row+VAT RGBA16F→두 열/compact normal→shader 조명/색, OneEmitter admission/follow | p1385 신규판독, bulletcmn64×8 half512개 복원. local normal 순서(x,극성분,다른수평축) 정정 적용. varying2.w/시간 k 공급 미확정은 값 추정 금지 |
| **4. 총구·착탄 피드백** P0 | FX01 일부/FX02 차이 | shared muzzle 없으면 탄 위치/방향으로 emitter 부착. 일반 emitter SRT/형상과 shader combiner 누락 | Weapon_R→weapon Root→Muzzle bone matrix, 뼈 −X축 XZ·카메라축 dot. 실제 emitter SRT/방출·InkAction 이벤트 인계 및 p1747/1886 색/alpha | player_assembly §6/effect_sound §3.2/effect_resources §2.2.3~5. FireImpact↔FireOn마다 플래시 재시작 금지, 탄6f와 emitter5/7f 구분 |
| **5. 잉크가 받는 광원·반사·최종색** P0 | GR05/06/07 일부, GR10 원본 미확정 | map 주광/베이크/HDR은 반영했지만 paint는 일반 PBR, FX는 unlit. 원본 cube/SSS/film/shadow/LUT 합성은 일부만 있음 | 공통 native shader light/Env/Blitz UBO·SH/동적광 소비, native environment layer·2cascade/ProjShadow, HDR+Bloom→tone4→CC LUT | 주광10·베이크75·spot5·HDR ×2 유지. **항상 주광4가 원인이라는 주장은 틀림**: paint 정상 parseEnv도10,4는 fallback. 최종 GPU/행선택 미확정은 보존 |

새로 확인한 원본 근거는 **p1385/v5583 shader 소비식 [판독]**, **bulletcmn VAT 64×8 [데이터]**, **B7a0 표시 entry64/64 [실행-부분]**이다. shader의 fragment varying2.w가 vertex dump에 export되지 않아 최종 alpha는 미확정으로 남겼다. 기존 p1383/floor/light 분석을 새로 분석한 것으로 계상하지 않았다. 원본 분석 고정986의 분자/분모는 그대로다.

실제 웹 재현: `analysis/visual_gap/visual_smoke.json`, human/firing/own_ink_squid PNG. 정상 Shift trigger로 변신했고 자기 잉크 stamp fixture를 발밑에 주었다. ownInk ratio1/state0x85/swimmingtrue/stealth59·blend1인데 렌더 displayS·2메시. paint.page0는 MeshStandardMaterial/roughness.35/envMap없음. native 실기와 픽셀 비교한 것은 아니다. console/page/HTTP 오류0. 최초90s render 대기 timeout은 기록했고 180s 재시도는 성공했다.

바로 내릴 지시:

- **“바닥 잉크 PNT02/06부터 원본 ColPaint UV와 ink shader로 반영해줘.”**
- **“오징어 자기 잉크 잠영의 B7a0 지연·표시·재질 애니를 연결해줘.”**
- **“분열 탄 전용 p1385와 메인 p1383 VAT, 총구/착탄 combiner를 반영해줘.”**
- **“잉크/캐릭터 native 환경반사·그림자·SSS/film·후처리를 남은 근거대로 반영해줘.”**

마지막 지시의 whole GPU/LUT/실제 team row 부분은 원본 근거가 확보된 범위부터 진행하고 미확정을 추정으로 덮지 않는다.

### 시각 후속 r2 근거 — 2026-10-03

[원본 상세](../graphics/ink_visual_path.md#추가-분석-r2--2026-10-03). 이번 작업은 분석만 수행했다. 전체 반영률 **13/62=20.97%**, 이 시각 범위 **0/16=0.00%**를 유지한다. 남은 조건이 있는 기존 항목을 부분 결과로 완료 처리하지 않았다.

| 우선순위·기존 ID | 새로 구현 가능한 원본 계약 | 남은 완료 조건 |
|---|---|---|
| P0 PNT02/06·GR04 | Lby texel Z=1/3200, 초기 W=0 보존. near-max `clamp((c−max+1e−4)*1e8)` 가중합과 V 반전 뒤 neighbor. 원본 init→staging 28건 일치 | W의 전체 writer·ColPaint atlas·실제 모델 UV/GPU. W=Z로 채울 근거 없음 |
| P0 GR01/02·MOV04 | hidden0/delay0/age9999 초기화. 후보→B794/B798 지연→B7a0→표시→holder 순서. off 캐시 NaN과 setter0 구분. ordinary 후보 10,800건·연결272프레임 일치 | 실제 StepPaint/Phive 공급·전체 player 프레임·ASB 전체 재질 leaf·GPU·잠영 파문 |
| P0 FX02/03/04 | Flash1202의 두 텍스처 A 곱·ANIM A0·fade·.5 discard. Ripple1885의 `(T0A*vA−A0)*ANIM A1`·fade. C0/scale 키와 sampler를 각각 사용 | p1385 v2.w/Flash v4.w의 linked/default 값·Custom1 VAT k/alpha remap·실제 팀색 공급 |
| P0 GR05/07/10 | 로비 Value1.0625→RGB8점 곡선→Gamma 순서. 8³ LUT 좌표 scale=.875/bias=.0625. CPU packet 및 좌표 블록 각각128건 일치 | 원본 GPU bake/픽셀·sampler/filter·실제 variant·cubemap·그림자 전체 |

바닥·잠영·색 보정 CPU의 [실행] 입력/스텁/호출 경계는 각 상세 문서 §10에 기록했다. Flash/Ripple과 LUT 셰이더는 [판독]+[데이터]이며 GPU 실행 결과가 아니다.


## 바닥·벽 잉크 표면 r7 실제 반영 — 2026-10-03

[현재 구현·검증·다음 지시](ink_surface_r7.md). 띄운 collision overlay를 actual visual triangle draw로 옮기고 packed UV/switch/tangent, InkBright·rim·normal1.8·floor/wall thickness·F0.015/roughness.05와 공통 베이크/SH/그림자/HDR 조명을 연결했다. 원본 leaf writer277/panel256/변환블록128 입력 대조, WebGL 판독slice↔포트431건, 전체285/285·typecheck/build·actualLby4단계 오류0. 전체원본GPU/atlas 동등성은 아니다.

PNT06 차이→일부이며 **고정13/62=20.97%, 일부37/차이9/미확정3**, GR0/10·일부7/10, 원본556/986=56.39% 유지. native atlas/seam·BRDF/cube12/Illuminate·W 후속writer/환경emission·캐릭터SSS/film·잠영숨김/파문이 남는다. 과거 collision overlay/.35 설명은 당시 사실로 보존하며 현재상태는 r7 링크를 따른다.


## 캐릭터 그래픽 r8 실제 반영 — 2026-10-03

[현재 반영·검증·다음 지시](character_graphics_r8.md): body/face cheapSSS·Thc 역광, hair/squid film·2cl 보정 법선, RGBA 강도, B7a0 지연 숨김/복귀, 슈터 Shtr/Shtr를 웹에 연결했다. 전체304/304·typecheck/build, WebGL 판독식512건, actual Lby12단계 오류0. 원본 NVN/전체 프레임 동등성은 아니다.

고정13/62=20.97%(일부37/차이9/미확정3), GR0/10·일부7/10, 원본556/986=56.39%·그래픽102/204=50.00% 유지. 추가 재질3개/live 몸 잉크·type11/18·SPP·cube12/BRDF·벽/상승 공중 producer·잠영 파문은 남는다. 이전 '캐릭터SSS/film/B7a0 전체 미연결' 설명은 당시 기록이고 최신 한정 반영은 r8 링크를 따른다.


## 재질·눈 패턴·총구 그래픽 r9 — 2026-10-03

[현재 반영·검증·다음 지시](graphics_priority_r9.md): 탱크/하네스/병의 native 재질·owner texture, raw type11 눈 채널, [Maya0/rotation0 UV6lane](../graphics/character_texsrt_r9.md), [실제 Muzzle 시각 행렬 및 내적 정정](../effect_sound/muzzle_attachment_r9.md)을 웹과 MD에 반영했다. FMAA 원본1,212/피부 홀더67/SRT313/내적 격리블록2,048, 선택 GLSL↔웹GPU448건은 각각 범위가 다른 검증이며 원본 NVN/전체프레임 일치가 아니다. 초기 표의 탱크/눈 UV와 shared muzzle 누락은 r9 한정 범위에서 후속 반영했다. 머즐 부착과 내적의 선택 뼈를 동일한 원본 근거로 보지 않는다.

고정 원본556/986=56.39%·그래픽102/204=50.00%, port13/62=20.97%(일부37/차이9/원본미확정3)·GR0/10/일부7/10 유지. 신규 부분 근거를 기존 복합 질문 전체 확정으로 승격하지 않았다. 몸CP/skin idx·weighted type11/type18·다른 SRT mode/rotation·cube/BRDF/SPP·잠영 파문/Custom1/VAT·native 최종픽셀은 남는다. 최종 테스트·브라우저·보호 SHA와 실패는 r9 요약의 실행 기록을 따른다.
