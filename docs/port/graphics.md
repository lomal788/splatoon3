# 그래픽 반영 요약 — 2026-10-03

Lby_Lobby00 실제 게임에 베이크·원본 하늘·광원·안개·HDR와 캐릭터 재질 계산을 반영했다.
카메라 포팅을 유지하며 UI·물리·총·도색 코어는 바꾸지 않았다.

고정 GR01~10 기준 **반영 확인0/10=0.00% / 일부7/10=70.00% / 차이2/10=20.00% / 원본 미확정1/10=10.00%**.
원래 일부6/차이3에서 GR04를 일부로 이동했다. 넓은 항목 전체가 끝났다고 승격하지 않았다.
전체는 **10/62=16.13%**, 일부38·차이11·미확정3. 원본 분석률은 그대로다.
2026-10-03 후속 탄·총 반영으로 현재 전체는 **13/62=20.97%**, 일부36·차이10·미확정3이다. GR01~10의 위 상태는 유지한다. 잉크/잠영/발사/광원 추가 차이는 [ink_visuals](ink_visuals.md).

| ID | 이번 반영 | 남은 것·다음 지시 |
|---|---|---|
| GR01 일부 | manifest의 선택 파츠·gear 행 하네스, anim/squid 모델 오선택 수정, fres 보강 | 실제 state writer/_Hlf·기어 가림/바인딩 |
| GR02 일부 | 기존 ASB/스켈레탈 유지 | SM+d4·blackboard/typed/event·material/visibility leaf·tex_mtx |
| GR03 일부 | known forward/GGX·calc/resource·UV·팀색f32 | SSS/Thc/필름·calc5/22·원본 ink shading |
| GR04 일부(이번 전이) | 원본 bkdat/재질번호/ST·AO/Shadow·HDR light·전 mip,75mesh | vertex/paint·hemiFix/그림자 입력을 포함한 재질 합성 |
| GR05 일부 | MainLight10·sky/fog·startup SH·spot5·capture2 | 원본 projection/12layer prefilter·capture saturation·actor provider |
| GR06 일부 | 기존 PCF를 새 forward에서 소비 | 원본2 cascade/SPP/fade/ProjShadow |
| GR07 일부 | half-float HDR RT·EV1→2·tone4·HSV f32·Hermit | 전체 LUT·bloom/DOF/vignette·native gamma/CC |
| GR08 차이 | 기존 스켈레탈 머리카락 유지 | native cloth link/damping/constraint/frame source |
| GR09 차이 | 기존 LOD0 유지 | viewZ/radius/bias/hysteresis·다중 LOD 자원 |
| GR10 원본 미확정 | 미확정 경계 보존 | live GPU/팀색 행/captured inputs 근거 |

검증: 원본 SH/Hermit680건·HSV128건 비트 일치, 점광원32×8 시퀀스·cone256결정 일치. 전체143테스트·typecheck·build 통과.
실제 game smoke console/page/404오류0, bake AO75/light75/missing0, sky·spot5·capture2·Exposure2.
원본 NVN 픽셀 동등성은 미검증. 오징어 버튼의 실제 상태 전이를 성공으로 보고하지 않는다.
HDR WebGL pixel18건은 채널당2/255 이내. controlled state/표시·y+2 입력에서 body24/hlf19/squid2mesh와 전경/하늘을 확인했다. 실제 core 전이 검증과 구별한다.

Map 번들73.76MB로 증가했다. HDR atlas/mip 보존 비용이다. 전송 최적화는 HDR 범위·mip를 유지하는 압축부터 검토한다.

다음 지시 예시:

- “GR03과 PNT02~06 연결해. ColPaint/vertex color/ink shading을 베이크·forward와 합쳐.”
- “GR07의 전체 LUT와 후처리 적용해. 곡선8개를 LUT 전체로 취급하지 마.”
- “GR06의 native cascade·SPP·ProjShadow부터 적용해.”
- “GR01~02의 실제 애니 속도/blackboard/재질·가시성 애니 적용해.”
- “GR05의 native projection·12layer prefilter 적용해. actor provider 근거도 확인해.”

[상세 구현·근거·한계](../impl/render.md), [명령과 실패](../../../analysis/port_graphics/commands.md).

## 공통 조명·그림자·최종색 후속 구현 — 2026-10-03

앞선 표는 초기그래픽 반영 기록이다. 현재GR05의Three SH투영은native angular7MRT로,GR06 single shadow는2×1024로,GR07 미연결LUT는원본RGB곡선8³로반영됐다. [현재 결과](common_render_r5.md)를 우선한다. fixedGR0/10/일부7/10와전체13/62는유지. 다음지시는ColPaint·cheapSSS/film·잠영숨김/파문이며nativecube/12layer·SPP/fade·Bloom/DOF/liveflags는그근거를확보해이어간다.


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
