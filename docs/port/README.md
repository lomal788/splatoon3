# 사격장 원본 분석 → 현재 웹 반영 현황

2026-10-03 · Splatoon 3 v0 / Lby_Lobby00 / 1인 / 스플래시슈터.
현재 실제 소스와 r9까지의 분석을 대조한 **구현 지시용 요약**이다. 최초 문서는 정적 소스 대조로 작성했고, 2026-10-03 사용자 지시로 카메라 코드를 반영한 뒤 고정 점검표를 갱신했다.

먼저 **충돌 계약·물리 접촉, 카메라, 칠/도색 표시, 스테이지/캐릭터 그래픽, 탄/피격 연결**을 반영해야 한다. UI·메뉴·부가기능은 이번 목록에서 제외한다. 분석률이 높아져도 이 실제 소스 연결이 해결되지 않으면 핵심 체감 구현은 완료로 보지 않는다.

## 현재 반영률

**13/62 = 20.97%**. 일부 반영 37개, 차이/미반영 9개, 원본 미확정 3개.

우선 작업은 **P0 31개 / P1 14개 / P2 1개**이며, 반영 유지13개·원본 보류3개를 별도로 표시했다.

[상세 점검표](implementation_status.md)의 고정 항목을 분모로 삼고 **반영 확인만 1, 나머지는 0**으로 센다. 부분 점수·난이도 가중치·미확정 제외 없음. 많은 계산/에셋 경로가 이미 존재하지만 해당 항목 안에 남은 차이가 있으면 일부 반영이다.

**구현량이나 체감 품질의 퍼센트가 아니다.** 해당 항목에 명시한 범위의 정적 소스 반영률이다. 최초 작성 때에는 정적 대조만 수행했다. 이번 카메라 반영은 원본 함수 fixture 1,031건 비트 비교와 웹 전체 테스트·빌드·브라우저 실행을 확인했다. 다른 영역의 반영 확인 행이나 카메라 전체를 원본과 동등하다고 검증한 것은 아니다. 원본 분석률은 별도 [analysis_completion.md](../analysis_completion.md)와 [r9 보고](../completion_r9_report.md)를 따른다.

| 영역 | 반영 확인 | 일부 | 차이/미반영 | 원본 미확정 | 고정 항목 | 소스 반영률 |
|---|---:|---:|---:|---:|---:|---:|
| 물리 | 0 | 2 | 2 | 1 | 5 | 0/5 = 0.00% |
| 충돌 | 1 | 2 | 1 | 0 | 4 | 1/4 = 25.00% |
| 이동 | 1 | 3 | 1 | 0 | 5 | 1/5 = 20.00% |
| 카메라 | 2 | 5 | 0 | 0 | 7 | 2/7 = 28.57% |
| 탄·총 | 3 | 3 | 0 | 0 | 6 | 3/6 = 50.00% |
| 피격·판정 | 1 | 3 | 0 | 0 | 4 | 1/4 = 25.00% |
| 표적 | 2 | 2 | 0 | 0 | 4 | 2/4 = 50.00% |
| 도색 | 1 | 4 | 1 | 0 | 6 | 1/6 = 16.67% |
| 그래픽 | 0 | 7 | 2 | 1 | 10 | 0/10 = 0.00% |
| 이펙트 | 0 | 3 | 1 | 0 | 4 | 0/4 = 0.00% |
| 효과음 | 1 | 3 | 1 | 0 | 5 | 1/5 = 20.00% |
| 공통 | 1 | 0 | 0 | 1 | 2 | 1/2 = 50.00% |
| **전체** | 13 | 37 | 9 | 3 | **62** | **13/62 = 20.97%** |

## 우선 반영할 작업 묶음

번호는 착수 순서·의존 관계다. P0는 모두 핵심 체감에 필요하다. 작은 연결 수정은 선행 작업과 병행 가능하다. ID로 범위를 지정하면 된다.

| 묶음 | 우선 | 요청 ID | 현재 차이 → 적용할 결과 | 선행·검증 |
|---|---|---|---|---|
| A. 공통 충돌 계약 | P0 / 1 | COL02~04, PHY01·04 | layer/subLayer 양방향 허용·query point/t/normal·Main 동적 capsule을 공통 경로에 연결. 플레이어가 표적 Main을 통과하는 원인 제거 | native helper 출력 및 지형/표적 fixture 대조. B/C/D/F가 같은 계약 사용 |
| B. 카메라 | P0 / 2 | CAM03~05 | 이번에 리그·기저/법선·반경.3·두 질의·복귀/축소·spring 소비·출력 게이트와 ELink 쉐이크를 반영했다. 다음은 실제 D/B210/formHeight/상태 공급과 native 지형 LP/태그/표 질의 연결 | A와 physics 계약 공유. [현재 카메라 구현/검증](../impl/camera.md), 원본 fixture 1,031건 일치. whole 원본 frame 동등성은 미검증 |
| C. 물리·이동·잉크 위 체감 | P0 / 3 | PHY02~04, MOV01·04~05, BUL06 | 4회 push/slide 근사에서 원본 접촉 target·normal impulse·8/7/1과 COM 적분으로 전환. 발밑 잉크 재사용·벽 상태·3회복 카운터 연결 | A. 자유 이동→바닥→벽/모서리→경사·착지→표적 접촉. PT05와 동일한 sample 사용 |
| D. 칠 모양·지형·도색 표시 | P0 / 4 | PNT02~06 | r7에서 띄운 overlay를 실제 visual draw·packed UV/tangent·원본 ink material/조명으로 연결했다. 다음은 native panel/basis/atlas·두 panel seam·target 좌표 seed·raw paint flag | A. 원본 stamp 재사용. [잉크 표면 현재 검증](ink_surface_r7.md). custom chart는 adapter이며 floor/wall/모서리/덧칠·발밑 분류를 계속 대조 |
| E. 화면·캐릭터 | P0 / 5 | GR01~07 | 베이크75mesh/원본 하늘·MainLight·fog·spot5·HDR/known forward를 반영했다. 다음은 SSS/film·ColPaint·native 환경/그림자·LUT·애니 공급 ([graphics 요약](graphics.md)) | D와 잉크 shading 공유. 밝기 .25만 삭제하거나 PBR 재질만 교체해서 완료 판정하지 않음. GR10 별도 |
| F. 총·피격·표적 반응 | P0 / 6 | BUL01·03~04, HIT01·03, TGT03 | 탄 생성 경계·fresh Lobby RNG·우선 입력·세 잉크 카운터·벽 방울 sphere·배율/휨 연결을 반영. 다음은 실제 원점·상태 producer·native query ([탄·총 요약](weapon.md)) | A/B. 근거리·감쇠거리·연속 명중·비1 배율·표적 휨. vel 연결은 작은 독립 수정 가능 |
| G. 탄/착탄 시각 피드백 | P0 / 7 | FX02~03 | 점으로 통일한 volumeType을 형상별 식/난수 순서로 대체. color0/1·alpha0/1 조합과 ball VAT 적용 | F/GR03. 실제 슈터 emitter의 팀색/시간/프레임 계약 확인 |
| H. 나머지 인게임 수명·소리 | P1 | CAM06~07, MOV03, HIT02·04, TGT02·04, FX01·04, GR08, SND02~05 | reset/ELink 쉐이크·표적 파괴/레일·cloth·listener/거리/필터/그룹 수명 보완 | actual T 공급·전체 DSP 등 미확정은 유지 |
| I. 성능·추가 원본 추적 | P2 / 보류 | GR09, PHY05, GR10, SYS02 | LOD는 기본 화면 정합 뒤. 실제 Lby whole query·최종 GPU 선택·전체 actor 순서는 원본 근거 추가 필요 | 미확정 전체 경로를 근사나 임의 값으로 닫지 않음 |

## 이미 존재하는 구현

원본 표 기반 mode0 리그·최종 기저·법선 slerp·두 붐 질의 계산, 보통 점프/수직 감쇠, 슈터 damage/radius·잉크 소비, weapon→paint.request/지연 도색, 원본 R8 스탬프 52개/InkTexInfo 50행은 있다. 표적 배치/두 capsule·6상태/HP 복귀식·BendCalculator와 캐릭터/파츠/_Hlf 조립·ASB 재생 기반, 원본 변환 사운드 자산도 있다.

60Hz fixed step과 EventTap의 복수 step 이벤트 보존/FX·audio drain 경로도 있다. 기존 impl의 설명만 보고 “탄→paint 연결 없음”, “스탬프 전부 근사”, “마지막 queue만 읽어 이벤트 유실”로 되돌리지 않는다.

다만 **함수가 존재하는 것과 실제 caller 연결은 별개**다. 표적 휨은 탄 패킷에 vel이 없어 호출되지 않고, Main은 등록돼 있어도 player sweep이 소비하지 않는다.

## 구현 때 유지할 경계

- **FillUp은 후순위 참고.** r9의 확인된 Lby source closure 53 root/338 방문에서 FillUp 0건이다. [충돌 문서 §3.4.4~3.4.7](../gimmick/collision_mesh.md)과 [프리셋 런타임](../physics/fillup_preset_runtime.md)을 따르고 임의 장벽을 생성하지 않는다. runtime 전체 확정이라는 뜻은 아니다.
- **스플래시슈터에 headshot 배율을 만들지 않는다.** ordinary/critical HitEffect 모두 Shooter 행이라는 사실과 critical ring 수명을 구분한다.
- **미확정 값을 분석 완료값으로 바꾸지 않는다.** listener T·활성 GPU/LUT/팀색 행·whole TOI/프레임 순서는 미확정을 유지한다.
- UI/잉크 게이지/데미지 숫자/메뉴/네트워크/다른 무기·서브·스페셜은 후속 목록이다. 이번은 인게임 상태와 그 시각·청각 피드백에 집중한다.

## 바로 내릴 수 있는 지시 예시

- “A와 B의 남은 연결 적용해. CAM03의 native LP/태그/표와 CAM04~05의 실제 physics 공급자를 연결해.”
- “F에서 HIT01/TGT03부터 적용해. 비1 배율과 표적 휨을 검증해.”
- “D와 E 병렬 적용해. ColPaint UV·재질 경계를 공유하고 GR10은 미확정으로 남겨.”
- “C 적용해. native solver fixture 수치를 게임 상수로 쓰지 말고 식·저장 순서를 옮겨.”

구현 후 기존 ID/분모와 실제 수정 파일·검증 기록을 유지하며 상태를 갱신한다. 새 항목은 새 ID로 추가하고 질문 쪼개기·부분 결과의 전체 승격으로 비율을 올리지 않는다.

## 카메라 반영 기록 — 2026-10-03

카메라 고정 7항목 중 CAM02를 추가 반영 확인으로 바꿨다. **1/7 → 2/7, +14.29%p**다.
CAM07은 producer를 연결했으므로 차이/미반영 → 일부 반영이다. 나머지 고정 분모와 타 영역 상태는 유지했다.

기저·법선·리그·붐 복귀/전진·spring/위치 게이트의 원본 **1,031개 표본 전부 비트 일치**.
실제 Lby 브라우저에서 조준·이동/점프·사격·오징어 버튼·리셋 입력을 전달했고 페이지 오류0, 카메라 유한값을 확인했다.
오징어 입력 단계는 현행 플레이어 상태에 따라 사람 상태에 남았으므로 실제 오징어 전환 성공으로 계산하지 않았다.
오징어 리그/가중치는 별도 원본 및 코어 테스트로 검증했다.

[남은 카메라 연결과 실제 명령/실패](../impl/camera.md#9-남은-차이다음-지시).

## 그래픽 반영 기록 — 2026-10-03

GR04를 미반영→일부로 갱신했다. 그래픽 일부6/10→7/10(60%→70%). **전체 반영 확인0/10**은 broad 행의 남은 원본 차이 때문에 유지한다. 전체 점검표10/62=16.13%, 일부38/차이11/미확정3이다. 원본 분석률을 높인 작업이 아니다.
베이크75mesh AO/light/missing0·spot5·sky·capture2·HDR/EV2와 native SH/Hermit/HSV/광원 fixture 대조를 확인했다. 다음 지시용 [graphics.md](graphics.md)에 반영 내용·남은 차이·검증을 정리했다.

## 탄·총 반영 기록 — 2026-10-03

[탄·총 요약](weapon.md), [구현 기록](../impl/weapon.md). native fixture1,926건·전체153테스트·typecheck/build 통과, 실제 Lby 6프레임 연사/도색/잉크 부족·회복·오류0 확인. 고정62개 중13개 반영 확인이며 총/피격 전체 완료가 아니다. 후속 잉크/발사/오징어/광원 시각 차이는 [잉크 그래픽 분석](ink_visuals.md)에서 추적한다.

## 잉크·발사·잠영·광원 추가 분석 — 2026-10-03

[ink_visuals.md](ink_visuals.md)에 실제 차이·우선 반영 순서·지시 예시를 정리했다. 원본 p1385 신규판독/데이터512·표시gate64 원본실행, 웹 자기 잉크에서 squid2메시 표시를 재현했다. 후속 시각 코드는 변경하지 않았고 고정 전체13/62 및 넓은 항목 상태는 유지한다.

## 정지 마우스 시점 수정 지시 — 2026-10-03
[mouse_camera.md](mouse_camera.md)에 정지 조준의 큰 delta/최단 quaternion 보간·pitch 후행을 우선순위로 정리했다. 이번 작업은 분석이며 고정62개와 카메라7개의 구현 반영률은 그대로다.

## 첨부 원본 화면의 그래픽 반영 지시 — 2026-10-03

[reference_graphics.md](reference_graphics.md)에 키 유실·표면/캐릭터shader·잠영FX·LUT 경로의 구체 차이와 다음 구현 지시를 정리했다. 전체13/62와그래픽0/10·FX0/4의고정완료점수유지. 이번은분석만이다.


## 우선순위1·4 웹 반영 — 2026-10-03

[현재 구현·검증 결과](priority_1_4.md). 마우스와 FX 로더·에셋·소비자를 실제 반영했다. 원본키39개, known shader17개, VAT2개를 브라우저까지 검증했고 전체 테스트226/226·타입 검사·빌드가 통과했다. 원본 GPU 전체 동등성과 고정분모의 전체완료수는 별도다.

## 6번 공통 조명·그림자·최종색 실제 반영 — 2026-10-03

[현재 반영·검증·다음 지시](common_render_r5.md). native 각도 SH7MRT·2×1024 그림자·원본곡선8³LUT를 실제 연결했다. 전체252/252·타입/빌드 PASS, actualLby/GL/HTTP오류0. 고정13/62(20.97%)와GR0/10/일부7/10은broad잔여때문유지. native cube/12layer·SPP/fade·Bloom/DOF/liveflags와 ColPaint/캐릭터/잠영은 별도잔여다.


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

## 카메라 r10 후속 적용 — 2026-10-04

[현재 적용·검증·다음 공급자](camera_r10.md): 입력·피치 f32/투영/상태/쉐이크를 반영했다. 테스트359/359·typecheck/build PASS. 고정카메라2/7(28.57%)은실제공급자·전체query/event경계때문에유지한다.
