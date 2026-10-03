# 6번 공통 조명·그림자·최종색 반영 — 2026-10-03

**실제 웹에 반영하고 검사했다.** 주광10·베이크75mesh·spot5·원본 sky/fog의 기존 연결을 유지하면서, 환경광 투영·동적 그림자·색 보정 LUT를 보완했다. [환경광 상세](../graphics/common_lighting_web_port.md), [그림자 상세](../graphics/common_shadow_web_port.md), [최종색 상세](../graphics/common_post_web_port.md).

| 고정 기준 | 반영 확인 | 이번 상태 |
|---|---:|---|
| 웹 전체62 | **13/62 = 20.97%** | 분자/분모 유지. 부분 이식을 broad 질문 전체완료로 올리지 않음 |
| 웹 그래픽 GR01~10 | **0/10 = 0.00%**, 일부7/10 | GR04/05/06/07의 근거·실제 연결 갱신, 넓은 범위의 잔여 유지 |
| 원본 전체 inventory | **556/986 = 56.39%** | 원본 신규 판독·packer 실행을 부분 근거로 추가, 전체 질문 승격0 |

이번 변경 수나 단위 검사 수를 원본 완성률로 계산하지 않았다.

| 항목 | 실제 달라진 것 | 원본 근거/검증 | 남은 것 |
|---|---|---|---|
| 공통 간접광 GR05 | Three 입체각 가중 투영→native sin 각도 샘플·7MRT 가산·원본 SH 포장. 256² cube near4/far1024, 두 번째 capture 유지 | shader128 [판독], 새103289c width 선택 [판독]. CPU원본128회/3584bit 일치 [실행]. 실제98304point×7attachment×2 | 웹 cube 내용·Illuminate·saturation·mip live·GPU 누적 동등성·native12layer/BRDF |
| 공통 그림자 GR04/06 | 고정 ±6 single map→2×1024² depth target. stage/player forward에 AO/bake+dynamic+projection **가산 occlusion** 연결. paint overlay도 동일 depth supply 소비 | Common1024/2/.3/5/.5 [실행]+[판독]+[데이터] 재사용. 웹 near/far caster/alpha/projection fixture13/13, 실제caster24(23skinned), 두 RT 모두 기록 | cascade split/fitting/4tapPCF/NVN bias는 명시한 웹 정책. native SPP/fade·actor cast flag producer는 미확정. range 표적 shadow flag는 미연결 |
| ProjShadow GR06 | 로비 Density0은 추가 occlusion0. 원본 count/enabled·두clamp×f32·3행 입력 consumer 제공 | 기존 원본 [판독]+[실행] 재사용, default/discard/R채널 GPU검사 | nonzero frame matrix/factor producer가 없어 자동 생성하지 않음 |
| 최종색 GR07 | 노출2→Tone4 뒤 **원본 RGB8점 곡선/HSV/Value1.0625로 8³ LUT** 연결→조건부 비네트→선택gamma. 모든 HDR 재질에 같은 pass | CPUpacket/곡선 [실행]+[판독]+[데이터] 재사용. 실제 post WebGL 36/36, 최대0byte | unsigned RGB11/11/10 nearest-even·Linear/Clamp는 웹 정책. native rounding/sampler·active gamma/vignette·Bloom/DOF 생산 미확정 |
| 실제 프레임 | shadow→FXsceneDepth→HDRCompose 순서, environment readback 중 main draw 보류, 상태·resource 복구 | idle/firing/impact/fade4단계 모두 GPU/콘솔/HTTP0 | native 전체 draw scheduling 동일성은 미확정 |

최종 screenshot은 `analysis/port_common_r5/lobby_after.png`에서 확인했다. 바닥의 칠은 현재 overlay/PBR 근사가 남아 있고, 캐릭터 SSS·잠영 숨김/파문도 이번 공통 패스로 전체 해결되지 않았다. 첨부 대전 사진과 Lby는 stage/팀색/카메라가 달라 이 화면을 원본 픽셀 동일성으로 판정하지 않는다.

| 실제 수행한 검증 | 결과 |
|---|---|
| `python web/tools/common_sh_port_emu.py` | 원본 함수128회, 스텁0,3584bit 불일치0 |
| `npm run typecheck` | 최종 exit0. 최초 MAX_DRAW_BUFFERS 타입 오류는 WebGL2 context로 명시해 수정 |
| `npm test` | **252/252 PASS**, failure0 |
| `npm run build` | exit0. 사전 absolute dist 경로 확인 후 기존 빌드 실행 |
| `node analysis/port_common_r5/browser_verify.mjs` | 실제Lby4phase/pass순서·7MRTSH·2shadow·8³LUT, GL/페이지/콘솔/HTTP 오류0 |
| `node analysis/port_common_r5/shadow/browser_gpu.mjs` | GPU13/13, 실제RT1024²×2, write950/107pixel, nativeNVN 검증 아님 |
| `node analysis/port_common_r5/post/browser_gpu.mjs` | GPU36/36, CC off/on×gamma0/1/2×6HDR, 최대0byte |

명령·실패·보호검사는 `analysis/port_common_r5/commands.md`, `final_verification.json`에 있다. 초기 shadow 주입의 `i`가 Three unroll 뒤 남아 GPU컴파일 실패한 것을 `UNROLLED_LOOP_INDEX`로 고쳤다. post fixture의 MSAA resolve/premultiplied clear 실패2회도 성공으로 숨기지 않고 보존했다.

수정은 `client/render/{index,map,lighting,forward,post}.ts`, 새 `shadows.ts/sh_projection.ts/post_math.ts`, 해당 테스트·재현 도구·문서다. **impl/scripts/package/웹 에셋/original 변경0, commit/push0**이다.

다음으로 체감 차이가 큰 것은 **ColPaint visual mesh/잉크 normal·두께·InkBright·반사**와 **캐릭터 cheapSSS·film·잠영 숨김/파문**이다. 공통 경로의 다음 분석은 native cube/Illuminate/12layer·SPP/fade·Bloom/DOF/active flags를 실제 입력부터 이어서 연결하는 작업이다.
