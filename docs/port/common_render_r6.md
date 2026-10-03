# 공통 조명·그림자·최종색 r6 실제 반영 — 2026-10-03

6번 후속 구현을 웹에 반영했다. **하늘 환경광 캡처의 채도, 그림자 PCF·거리 페이드, Bloom 생산과 최종 HDR 소비**를 원본 근거로 보완했다. [r5 기록](common_render_r5.md)은 당시 결과로 보존한다. 자세한 원본 근거는 [조명](../graphics/common_lighting_r6.md), [그림자](../graphics/common_shadow_r6.md), [Bloom·최종색](../graphics/common_post_r6.md)을 따른다.

| 고정 기준 | 현재 값 | 처리 |
|---|---:|---|
| 웹 전체 | **13/62 = 20.97%** | 좁은 구현 결과로 넓은 항목 전체를 완료 처리하지 않음 |
| 웹 그래픽 GR01~10 | **0/10 = 0.00%**, 일부 7/10 | GR04~07의 설명·근거 갱신, 상태 유지 |
| 원본 inventory | **556/986 = 56.39%** | 부분 원본 근거 추가, 분모 축소·전체 질문 승격 없음 |

위 점수는 고정 질문의 완료율이며 화면 품질이나 구현량 점수가 아니다.

| 항목 | 실제 반영 | 원본 근거·검증 | 남은 것 |
|---|---|---|---|
| 하늘·환경광 GR05 | 화면용 mSky25와 캡처용 cube27 분리. 캡처에 원본 휘도·채도 .400000006 적용 후 화면 노출4·채도1 복구 | shader25/27 완전 키 일치 [판독], SkySphere [데이터]. 웹 RGB32F 21건, 최대차 .0000159153 | 다른 cube 재질·mSun 선택·Illuminate·native12layer/BRDF·live mip·원본 GPU 누적 |
| 그림자 GR04/06 | 원본 기본 1비교 및 선택 가능한 4/9/16비교 커널, strict >20 캐스케이드 경계, PCF offset·SPP 소비식, **Default 거리 페이드40~60** 연결 | writer 전체1,024건/8float bit 일치·스텁0 [실행], selector 명령블록24건 [실행], raw shader12변형 [판독], Default CRC30 [데이터]. 웹 GPU25/25 | native projection·compare sampler/border·static SPP·실제 자원 선택·caster/표적 정책 |
| Bloom·최종색 GR07 | 노출 전 HDR에서 mask→4단계 reduce/H/V→역합성을 생산. **HDR×2+Bloom** 뒤 Tone4→기존8³LUT→선택 gamma. DefaultDay old_calc=false 적용 | UBO블록512·Expand블록256·전체 문자열파서6·state maker1: 총775건 불일치0 [실행]. 합성 enum ONE2/CONST_COLOR61 [판독]. DefaultDay [데이터] | live view/Enable·scale·HDR alpha·native sampler/format/mip·DOF master enable·gamma/vignette·최종 원본 GPU |
| 프레임·자원 | 그림자→FXsceneDepth→HDRCompose→Bloom, producer16draw. 수동 Bloom binding 수명 및 viewport/scissor/target 예외 복구 | 실제 Lby 대기·발사·착탄·잔상4단계, 매 단계 shadow2draw/Bloom16draw·활성·GL0 | native 전체 submit/frame 동일성 |

**생성자와 설정 자료의 차이를 정정했다.** ShadowPrePass 생성자는 farFade=false/100~1000이지만 Default 자료는 true/40~60이다. Bloom 생성자의 old_calc=true 분기를 먼저 검사했으나 DefaultDay는 false여서 소스를 바꾸고 GPU를 다시 검사했다. 초기 결과는 별도 파일로 보존했다. DOF 방문자의 +40도 master Enable이 아닌 IsEnableFarCancel이므로 그 값으로 blur를 켜지 않았다. Default 자료를 공급한 것과 런타임 Lby 자원 선택을 실행으로 확인한 것은 구분한다.

| 실제 수행한 명령 | 결과 |
|---|---|
| `npm test` | **266/266 PASS**, 실패0 |
| `npm run typecheck`, `npm run build` | 각각 exit0 |
| `node analysis/port_common_r6/browser_verify.mjs` | 실제 Lby4단계 순서·Default fade·Bloom 분기·sky 복구 확인, 페이지/콘솔/HTTP/셰이더/GL 오류0 |
| `node analysis/port_common_r6/sky_gpu.mjs` | 21/21 PASS, RGB32F 최대차 .0000159152656352 |
| `node analysis/port_common_r6/shadow/browser_gpu.mjs` | 25/25 PASS, 실제 caster24/SkinnedMesh23, depth1024²×2에 near966/far108pixel 기록 |
| `node analysis/port_common_r6/post/browser_bloom.mjs` | 18/18 PASS, RGBA16F Bloom 최대차 .0005807876587, 최종색0byte. 별도128texel Gaussian impulse 최대차 .0000263043483 |
| 원본 Unicorn 및 Ghidra·shader/AAMP 추출 | 입력·스텁·실패·범위는 각 상세 문서 §10 및 [실제 명령](../../../analysis/port_common_r6/commands.md), [shadow 명령](../../../analysis/port_common_r6/shadow/commands.md), [post 명령](../../../analysis/port_common_r6/post/commands.md) 참조 |

266은 웹 단위 검사 수이고, 775는 명시한 원본 블록/전체 함수 실행 표본 수다. 원본 GPU 실행 수나 전체 질문 확정 수로 합산하지 않는다. GPU readback의 성능 경고도 오류와 구분하여 JSON에 보존했다.

이번 소스는 `render/lighting.ts`, `sky.ts`, `shadows.ts`, `post.ts` 수정과 `bloom.ts` 추가, 검사2파일 추가다. **impl/scripts/package/웹 에셋은 SHA256 불변, original은 키 제외 파일 목록·크기·mtime 불변**을 별도로 확인한다. 원본 내용 전체 SHA 검사라는 뜻은 아니다. 삭제·이동·commit/push는 수행하지 않았다. 최종 근거는 `analysis/port_common_r6/final_verification.json`에 있다.

최종 화면 `analysis/port_common_r6/lobby_after.png`를 확인했다. **원본과 동일한 그래픽으로 완료된 상태는 아니다.** 다음 체감 우선 작업은 **ColPaint visual mesh·잉크 normal/두께/InkBright/반사**와 **캐릭터 cheapSSS/film·잠영 숨김/파문**이다. 공통 경로에서는 native Illuminate/12layer/BRDF와 live sampler·SPP·HDR alpha를 이어서 연결해야 한다. 다음 지시는 [상세 점검표](implementation_status.md)의 기존 ID를 사용하면 된다.
