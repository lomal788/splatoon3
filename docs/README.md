# Splatoon 3 (v0) 분석 문서 목차

원본을 분석해 웹으로 포팅하기 위한 명세입니다. 작업 지침은 [../분석.txt](../분석.txt).

## 프로젝트 정보

| 항목 | 값 |
|---|---|
| 게임 | Splatoon 3, TitleID `0100C2500FC20000`, v0 (XCI) |
| 원본 | `c:/dev/splatoon3/original/` — **읽기 전용** |
| 추출물 | `c:/dev/splatoon3/extracted/` (재생성 가능) |
| 분석 산출물 | `c:/dev/splatoon3/analysis/` |
| 분석 도구 | `c:/dev/splatoon3/web/tools/` (+ Ghidra는 `c:/dev/mpj/tools/ghidra_12.1.2_PUBLIC` 그대로 사용) |
| 웹 프로젝트 | `c:/dev/splatoon3/web/games/splatoon3/` (시험 사격장 구현 중, 기록은 [impl/](impl/)) |

## 공용 문서

7차(2026-10-03) 최신 상태는 [analysis_completion.md](analysis_completion.md), 추가 근거는 [completion_r7.md](completion_r7.md). 아래 기능 표는 이전 회차 요약도 포함하므로 본문의 날짜별 정정과 최신 감사 목록을 우선한다.

- [analysis_completion.md](analysis_completion.md) — Lby_Lobby00 1인 연습 출처별 미확정/추정 감사 목록·정확한 처리율
- [completion_run.md](completion_run.md) — 이번 인수 분석의 명령·성공/실패·보호 파일 검증
- [core_experience_priority.md](core_experience_priority.md) — 사용자 지정 핵심 체감 다섯 경로·최우선 잔여 연결
- [completion_r7.md](completion_r7.md) — 사격 입력·도색 정점·색 보정·카메라·물리 추가 실행과 웹 반영 사항
- [completion_summary.md](completion_summary.md) — 이번 회차 종료 보고·영역별 집계·확정/미확정·웹 반영 필요
- [camera/solo_completion.md](camera/solo_completion.md) — 카메라 기저·붐 구체·FOV 정정
- [weapon/solo_shooter.md](weapon/solo_shooter.md) — 첫 발·잉크·탄 생성 허용 원본 근거
- [physics/collision_runtime_completion.md](physics/collision_runtime_completion.md) — 양방향 필터·몸체 원점·월드 단계
- [graphics/ink_visual_path.md](graphics/ink_visual_path.md) — 실제 잉크/발사/잠영/광원 시각 차이·p1385 신규판독·숨김 reader64건 실행 ([구현 지시 요약](port/ink_visuals.md))
- [graphics/solo_graphics_audit.md](graphics/solo_graphics_audit.md) — 모자 행렬 원본 실행 및 HairArrange 후보 정정
- [effect_sound/solo_fx_audit.md](effect_sound/solo_fx_audit.md) — FIXED4채널·VAT 법선·음성 제한기 비교
- [player/solo_completion.md](player/solo_completion.md) — 오징어속도 k1088건, 이동애니속도2004건 원본 비트 대조


- [00_extraction_pipeline.md](00_extraction_pipeline.md) — XCI→NCA→ExeFS/RomFS 추출, 해시 검증, 재현 명령
- [01_package_and_assets.md](01_package_and_assets.md) — RomFS 구성, zstd/SARC/BYML, 액터→컴포넌트→파라미터 연결
- [02_code_and_params.md](02_code_and_params.md) — main NSO(심볼 없음), 파라미터 리플렉션으로 필드·기본값 판독, 클래스명→vtable
- [tools.md](tools.md) — 분석 도구 사용법 (즉석 디컴파일 포함)

## 기능 문서

| 영역 | 문서 | 상태 |
|---|---|---|
| 슈터 탄 계산 | [weapon/shooter_bullet.md](weapon/shooter_bullet.md) | 이동 상태머신·스텝식·프레임 순서·난수·발사 속력·초기 속도·스플래시 생성·바디 적분·충돌 콜백(바닥 58/벽 59/대상 60) 판독, 재구현 계산. 탄 age −1 시작(정정), 첫 명중 age 0 [추정] |
| 플레이어 물리·이동 | [player/movement_physics.md](player/movement_physics.md) ([gear_skills](player/gear_skills.md), [player_state](player/player_state.md)) | 기어→속도(원본 실행 731건), 목표 속도·상한·입력 곡선, 점프 곡선 확정(탭 최고 0.841/14f, 원본 함수 연결 실행 비트 일치), 최종 속도 합성식, 가속 식 전체, 벽 타기·벽 점프·오징어 롤, 상태 286개·전이 우선순위 판독. 세계 중력 런타임 값·일부 플래그 의미 미확정 |
| Phive 물리 계층 | [physics/phive_controller.md](physics/phive_controller.md), [physics/character_controller.md](physics/character_controller.md) | 플레이어 중력 0.008 유닛/프레임²·v=0.98v−g·종단 −0.4(게임 코드가 적용, Phive 중력·감쇠는 0), 컨트롤러 단계 순서, 탄 바디 적분(서브스텝 없음, p += dt·(v×60), dt 1/60)·충돌 응답(최소 f 접촉점에서 정지)·충돌 콜백 분배(바닥/벽/플레이어) 판독. 플레이어 몸체(동적 강체·마찰 0)·캡슐(오징어 비율 t)·접지 판정(계단 0.2·경사 75°)·OnGround/InAir 전이·shapeTag 의미 판독(4차). 프레임 내 액터↔Phive 순서·필터 결합식 미확정 |
| 피격·데미지·타격 판정 | [combat/damage_hit.md](combat/damage_hit.md), [combat/player_life.md](combat/player_life.md), [combat/hitbox.md](combat/hitbox.md) | 탄 데미지 감쇠·반경·크리티컬·넉백·배율표·수신 이력 6모드 판독. HP·회복·적 잉크 데미지·사망·리스폰 흐름(타이머·Revival·리스폰 무적·지점 선택)·StartArmor·무적 판정 판독, HP 홀더·리스폰 타이머 원본 실행 일치. 플레이어 피격 캡슐·Same/Other 레이어 선택·아머 원인 이름·리스폰 착지 단계·Blast 규칙 판독(4차). 히트마커 조건·형태별 형상 미확정 |
| 잉크 도색·점수 | [paint/paint_and_score.md](paint/paint_and_score.md), [paint/paint_shape.md](paint/paint_shape.md), [paint/special_gauge.md](paint/special_gauge.md), [paint/colpaint_atlas.md](paint/colpaint_atlas.md), [paint/turf_result.md](paint/turf_result.md) | 도색 모양·지연 도색·요청 큐→송신→렌더 패스 전체 경로·모드 0~17(패스 역할+팀)·스탬프 회전·패턴 변형(원본 실행 600건)·텍스처 size(1단위당 8텍셀)·집계 규칙·p 환산·PaintPermille·스페셜 게이지(원본 실행) 판독. 지형 아틀라스(42방향 투영·8텍셀/단위·기요틴 패킹, 원본 실행 일치)·나와바리 승패(무승부 없음) 판독(4차). 패널 연결·패턴 인식·게이지 일부 writer 미확정 |
| 카메라·손맛(조작감) | [camera/camera_feel.md](camera/camera_feel.md) ([aim_swerve](camera/aim_swerve.md), [player_camera](camera/player_camera.md), [shake_rumble](camera/shake_rumble.md)) | 조준 흔들림·연사 타이머·카메라 리그·감도·스틱·추종·쉐이크 판독, 대체 리그 7종 발동 조건·자이로 경로·리셋·쉐이크 적용 위치·블래스터·Diffusion 판독. 반전 설정(원본 실행 4건 일치)·벽 회피 거리 반영·슈퍼점프 카메라 판독, Diffusion의 두 필드는 결과에 영향 없음. 질의 형상·사망 메시지 수신 측 미확정 |
| 그래픽·모델·캐릭터 | [graphics/model_character.md](graphics/model_character.md) ([formats](graphics/formats_bfres_bntx.md), [team_color](graphics/team_color.md), [player_assembly](graphics/player_assembly.md), [anim_state_machine](graphics/anim_state_machine.md), [shaders](graphics/shaders.md), [stage_rendering](graphics/stage_rendering.md), [hair_cloth](graphics/hair_cloth.md)) | FRES v10·BNTX 변환, 팀 컬러(Ink/InkBright = 주 방향광+하늘 SH 기반) 판독, BlitzUBO0 레이아웃(원본 실행)·몸 잉크 색식, 셰이더 슬롯·옵션·혼합식, 인간/오징어/_Hlf(변신 과도기) 표시 선택, ASB 노드·끝 프레임·전환 블렌드·블랙보드, 신발 미러·모자 바인드 판독. 스테이지 렌더링(주광 직접 기록·렌더러 구성·맵 재질 프로그램 식·베이크 형식·잉크 표시 식·동적 광원 격자) 판독(4차). 머리카락 천 상수(Har_SQD000) 해독. Env UBO 칸 대응·톤매핑·LOD 소비 코드·HairArrange 적용식 미확정 |
| 이펙트·효과음 | [effect_sound/effect_sound.md](effect_sound/effect_sound.md) ([xlink](effect_sound/xlink_format.md), [sound](effect_sound/sound_resources.md), [effect](effect_sound/effect_resources.md)) | xlink 실행 규칙·트리거 비트·보류 액션 판독, VFXB v46 이미터 주요 필드·GPU 위치식(셰이더 역번역)·슈터 이펙트 웹 재현값 표, Alto 롤오프·AUDC·AADR 판독, 무기 그룹 동시 발음 제한 없음 확인. 이미터 형상별 식·DistCoef 확장값·필터 컷오프 미확정 |
| 스테이지 기믹 | [gimmick/stage_gimmicks.md](gimmick/stage_gimmicks.md) ([inkrail](gimmick/inkrail.md), [sponge](gimmick/sponge.md), [misc](gimmick/stage_misc.md), [collision_mesh](gimmick/collision_mesh.md)) | 배치 레이어=모드, 잉크레일·탑승·스펀지 판독+재구현, 충돌 메시(hknpMeshShape) 디코드 1485개 전수·Yagara glb 출력, 이동 발판 일정·회전(Bravo=레일 Y축 180°)·좌표계 판독, 잉크레일 이탈 경로 5종(끝 자동 이탈 없음), 스펀지 중심·SafePos, 사망 이유 열거형, 간헐천 법칙. 점프대 속도·파이프라인·그라인드 레일 미확정 |
| 시험 사격장 | [range/shooting_range.md](range/shooting_range.md) | 표적 SighterTarget 상태 6개·HP(1000/대형 5000)·파괴·복귀·회복·휨·데미지 숫자, 이동 표적 레일, 사격 구역 판정 판독. 팁 시험·인형·PaintedArea 일부 판독 |
| 네트워크 | [network/network.md](network/network.md) (01~06 하위 문서) | P2P 메시·15Hz 상태·비트 직렬화(LSB 우선)·PlayerNetState 필드 출처·의미 다수(HP·아머·공중 프레임 등)·GameFrame 동기·시계=pia GetClock(ms)·시드 로비→설정 복사·Rule 값 표·pia 신뢰 전송(창 128, 재전송 33ms+1.4×RTT)·다음 호스트 선택, 원본 실행 다수. 일부 필드·로비→게임 객체 복사 지점 미확정 |
| UI | [ui/ui_hud.md](ui/ui_hud.md) ([layout format](ui/ui_layout_format.md), [VS_MainTV 요소](ui/ui_vs_maintv_elements.md), [minimap](ui/ui_minimap.md)) | 대전 HUD 특수 게이지 추적, 레이아웃 v9·폰트·MSBT 파서 전수 실행, 칠 포인트·타이머·Pinch·결과 % 판독, 갱신 루프 순서·dt·애니 명령(원본 실행 13건 일치), 미니맵 정사영·축 규약·맵 열기 입력·맵 셰이더(역번역) 판독, 게이지 표시 = min(value, trace) 확정(원본 실행 56건). 뷰포트 실제 크기 미확정 |

## 확정 수준 표기

- **[실행]** 원본 실행 확인
- **[판독]** 원본 코드/명령 판독 확인
- **[데이터]** 데이터 확인
- **[추정]** 추정
- **[미확정]** 미확정

"분석 완료", "웹 구현 완료", "동작 검증 완료"는 서로 다른 상태입니다. 웹 구현 상태는 [impl/](impl/)에 영역별로 있습니다.

## r8 원본 분석 갱신 (2026-10-03)

[analysis_completion.md](analysis_completion.md)의 안정 ID와 [completion_r8.md](completion_r8.md)의 **r7 종료 고정 분모**로 진행률을 집계한다. 아래 기능 표의 과거 상태는 당시 기록이며, 최신 해소·잔여·실행 경계는 각 본문의 날짜별 정정과 r8 표를 따른다. 전체 목표는 아직 분석 중이다. 부분 검증을 복합 질문의 전체 확정으로 승격하지 않는다.

| 신규 문서 | 원본 근거 범위 |
|---|---|
| [combat/knockback_pipeline.md](combat/knockback_pipeline.md) | 게임 넉백 메시지→원본 큐·행동 슬롯18·충격 컴포넌트 연결 |
| [combat/critical_ring_lifecycle.md](combat/critical_ring_lifecycle.md) | 크리티컬 누적 링의 생성·reset 등록·방송 경로 |
| [combat/hit_effect_pipeline.md](combat/hit_effect_pipeline.md) | 슈터 명중 요청→64개 FIFO→반응 셀·XLink 속성·거리 컬링 순서 |
| [effect_sound/xlink_parameter_counts.md](effect_sound/xlink_parameter_counts.md) | XLink 속성 개수와 실제 인덱스 의미 |
| [effect_sound/floor_fixed_rotation.md](effect_sound/floor_fixed_rotation.md) | 속도0 착탄의 원본 init 배열→단위 회전→코드 emitter 소비 |
| [graphics/light_rig_runtime.md](graphics/light_rig_runtime.md) | 스테이지 Spot/Point Rig의 뼈 prefix·행렬·광원 값 전달 |

카메라·탄·표적은 해당 기존 문서의 r8 절, 충돌 필터/피격 형상은 [character_controller.md](physics/character_controller.md) §3.3.1–3.3.2와 [hitbox.md](combat/hitbox.md), HP 대상0은 [player_life.md](combat/player_life.md) §3.6.1, 도색은 기존 paint 문서의 r8 절에서 확인한다. 구현 변경 필요 사항은 completion_r8 표에 기록하며 이번 작업에서는 웹 코드·impl을 변경하지 않는다.

- [graphics/lod_runtime.md](graphics/lod_runtime.md) — r8 거리/화면 LOD 선택·히스테리시스·정적 패킷 전달. 전체 Player 모델 이름 override·GPU3단 전환은 별도 미확정.

- [graphics/animation_weapon_blackboard.md](graphics/animation_weapon_blackboard.md) — 슈터 Category/Detail의 네 caller·empty 공급·원본 버퍼 절삭. 전체 포즈 합성은 별도 미확정.


## r8 최소 증가 목표 검증 완료 (2026-10-03)

r7 종료 고정 inventory에서 신규147개를 원본 근거로 해소하여 확정529/986이다. 물리·카메라·그래픽·피격 각각+20%p 이상, 이동·탄·표적·이펙트·도색·효과음 각각+10%p 이상을 충족했다. 정확한 고정 분모·현재율·원본 근거·웹 반영 필요는 [completion_r8.md](completion_r8.md), [완료 보고](completion_r8_report.md), [전체 감사 목록](analysis_completion.md)에서 확인한다. 전체 100% 확정은 아직 미달이다.

새 마지막 근거: [물리 접촉/COM/몸체 되쓰기](physics/phive_controller.md) §6.10.4~5, [형태별 native 피격 형상](combat/hitbox.md) §2.1, [LOD 실제 모델/mesh/draw](graphics/lod_runtime.md), [무기 AS 두 이름 공급](graphics/animation_weapon_blackboard.md), [RSDB 팀색 공급 및 기존 데이터 설명 정정](graphics/teamcolor_rsdb_source.md). 실제 메시 전체·TOI·runtime 속성 바인딩·그림자 live 입력·GPU/LUT·전체 포즈 복합 질문은 유지한다.

- [graphics/as_request_first_tick.md](graphics/as_request_first_tick.md) — 기본 AS 요청→첫 틱→래퍼 보고 1,025건 원본 실행. 연속 두 번째 틱과 전체 포즈는 조사중 유지.
- [graphics/projected_shadow_runtime.md](graphics/projected_shadow_runtime.md) — 그림자 객체 생성·Scene 등록·밀도 uniform 소비. live 입력 및 L342 전체는 조사중 유지.

## 9차 최종 기록 — FillUp 집중 분석 후 마무리 (2026-10-03)

최신 지시에 따라 신규 분석을 종료하고 지금까지의 결과를 저장했다. 고정 r7 inventory·분모를 유지한 최신 수치는 [completion_r9.md](completion_r9.md), 이번 결과/실패/미확정/웹 반영 필요는 [completion_r9_report.md](completion_r9_report.md), 모든 안정ID 상태는 [analysis_completion.md](analysis_completion.md)에서 확인한다. 아래 과거 표는 당시 기록이며 이 최신 문서의 날짜 정정을 우선한다. 물리·카메라100% 등 이전 전체 목표를 달성한 것으로 표시하지 않는다.

- FillUp 원본 프리셋 등록: [fillup_preset_runtime.md](physics/fillup_preset_runtime.md)
- FillUp 실제 접촉·대체 탐색: [fillup_contact_runtime.md](physics/fillup_contact_runtime.md), [fillup_fallback.md](physics/fillup_fallback.md)
- FillUp 원본 저작 형상·배치: [fillup_authored_data.md](gimmick/fillup_authored_data.md)
- FillUp 액터/리소스 공급과 형상 프리셋 소비: [fillup_dynamic_sources.md](physics/fillup_dynamic_sources.md)
- 물리 회전/침투/구–사각형 TOI 부분 검증: [rotation_pose.md](physics/rotation_pose.md), [penetration_recovery.md](physics/penetration_recovery.md), [sphere_quad_toi.md](physics/sphere_quad_toi.md)
- 카메라 원본 붐/충돌 감쇠/상태/리셋: [r9_boom_query.md](camera/r9_boom_query.md), [r9_collision_spring.md](camera/r9_collision_spring.md), [r9_state_sources.md](camera/r9_state_sources.md), [r9_reset_contexts.md](camera/r9_reset_contexts.md)
- 그래픽 원본 ASB/typed tag/cloth: [asb_header_runtime.md](graphics/asb_header_runtime.md), [asb_typed_tags.md](graphics/asb_typed_tags.md), [cloth_damping_runtime.md](graphics/cloth_damping_runtime.md), [cloth_link_runtime.md](graphics/cloth_link_runtime.md)
- 이펙트/효과음 원본 생성·제한·필터: [one_emitter_runtime.md](effect_sound/one_emitter_runtime.md), [sound_limiter_runtime.md](effect_sound/sound_limiter_runtime.md), [sound_runtime_filters.md](effect_sound/sound_runtime_filters.md)

### 잉크·발사·잠영·광원 추가 근거 r2 (2026-10-03)

- [바닥 texel/neighbor 입력](graphics/floor_ink_inputs_r2.md) — init→texel→staging28건,wholeW/atlas는미확정.
- [잠영 지연·표시 holder](graphics/squid_ink_visibility_r2.md) — B7a0 지연과표시/재질reset의실행경계.
- [Flash/Ripple·raw VAT 입력](effect_sound/fx_shader_inputs_r2.md) — 새1202/1885조합식과Maxwellexport누락.
- [색 보정/LUT 공급](graphics/ink_lighting_r2.md) — c1분기표누락보완·실제로비CPU연산순서.

구현요약 [port/ink_visuals.md](port/ink_visuals.md). 이번은분석+MD+분석도구보완이며게임코드반영은없다. 넓은GPU/프레임질문을부분실행으로승격하지않았다.

### 정지 상태 마우스 시점 분석 (2026-10-03)
- [시점 급변·피치 후행 재현](camera/mouse_view_jumps.md), [입력 수명](camera/mouse_input_lifecycle.md), [원본 자동 제어 경계](camera/mouse_original_controls.md).
- 구현 지시 요약: [port/mouse_camera.md](port/mouse_camera.md). 분석만 수행했으며 현재 코드 수정은 없다.

### 첨부 원본 화면의 그래픽·이펙트 차이 분석 — 2026-10-03

[사진/현재 웹/전체 경로](graphics/reference_graphics_gap.md), [잉크 표면](graphics/reference_ink_surface.md), [발사·탄·발밑·잠영 FX](effect_sound/reference_shooter_visuals.md), [캐릭터 산란·필름](graphics/reference_character_lighting.md), [HDR/LUT 저장·sampler](graphics/reference_hdr_output.md). 구현 지시용 [port/reference_graphics](port/reference_graphics.md). 웹 코드 변경0/고정 inventory·포트 항목 승격0이며 원본 GPU·동일 Lby 픽셀 비교는 미확정이다.


## 마우스·슈터이펙트 후속 웹 반영 — 2026-10-03

[마우스 실제 반영](camera/mouse_web_port.md), [슈터FX소비자](effect_sound/shooter_web_port.md), [실제 구현·검증 요약](port/priority_1_4.md). 원본분석승격과웹구현검증을구분한다.

## 공통 조명·그림자·최종색 웹 반영 — 2026-10-03

- [port/common_render_r5.md](port/common_render_r5.md) — 6번 실제반영·고정분모·명령/실패·전체252테스트/GPU검증·잔여
- [graphics/common_lighting_web_port.md](graphics/common_lighting_web_port.md) — native sin 각도7MRTSH·CPU원본128회/3584bit·웹큐브근사경계
- [graphics/common_shadow_web_port.md](graphics/common_shadow_web_port.md) — 2×1024depth·가산occlusion·Density0·13GPUfixture·caster/표적정책미확정
- [graphics/common_post_web_port.md](graphics/common_post_web_port.md) — native곡선8³LUT·36WebGLreadback·Bloom/DOF/liveflags잔여

이번 사용자 지시는 웹 구현이므로 렌더source를 수정했다. impl/scripts/package/original·에셋은 그대로이며 원본전체556/986와포트13/62는 유지한다.


## 공통 조명·그림자·Bloom 후속 반영 r6 — 2026-10-03

- [구현·검증·다음 지시](port/common_render_r6.md)
- [하늘 cube27·Illuminate 잔여](graphics/common_lighting_r6.md)
- [PCF/SPP·Default fade40~60](graphics/common_shadow_r6.md)
- [Bloom 원본 생산·DefaultDay·DOF 정정](graphics/common_post_r6.md)

전체266/266·typecheck/build 및 실제 사격장4단계 오류0. narrow 원본 근거와 웹 검증을 구분하고 whole 상태/분모는 유지한다.


### 2026-10-03 잉크 표면 r7 웹 반영·검증

[실제 포트 요약](port/ink_surface_r7.md), [시각 모델 좌표/geometry](graphics/ink_visual_geometry_r7.md), [원본 판독식 소비 shader](graphics/ink_surface_web_r7.md). collision overlay를 actual visual draw로 옮기고 InkBright/rim/normal/thickness/F0/roughness·베이크/SH/그림자/HDR를 연결했다. 원본 writer277/panel256/transform명령블록128입력 재검증·WebGLslice↔실제포트431건·전체285테스트·타입/빌드·actualLby4단계 오류0를 구분한다.

고정 원본986/확정556=56.39%, 그래픽102/204=50.00%, 도색52/100=52.00% 유지. web PNT06 차이→일부, 고정13/62=20.97%, 일부37/차이9/원본미확정3. native wholeatlas/seam·live W/emission·BRDF/cube/최종NVN은 미확정이며 adapter/부분결과를 전체확정으로 올리지 않는다. 실패와 실제명령은 analysis/port_ink_r7/commands.md 및각상세§10에 보존한다.


## 캐릭터 그래픽 r8 실제 웹 반영 — 2026-10-03

[구현 요약](port/character_graphics_r8.md), [재질 11절](graphics/character_material_r8.md), [잠영 표시 11절](graphics/character_display_r8.md). 실제4재질 cheapSSS/film/RGBA, B7a0 지연 표시, Shtr/Shtr 공급. 전체304/304·typecheck/build·actual Lby12단계 오류0. 원본 GPU/전체 producer 미확정 유지, 고정 inventory556/986·port13/62 유지.


## 재질·눈 패턴·총구 그래픽 r9 — 2026-10-03

[현재 반영·검증·다음 지시](port/graphics_priority_r9.md): 탱크/하네스/병의 native 재질·owner texture, raw type11 눈 채널, [Maya0/rotation0 UV6lane](graphics/character_texsrt_r9.md), [실제 Muzzle 시각 행렬 및 내적 정정](effect_sound/muzzle_attachment_r9.md)을 웹과 MD에 반영했다. FMAA 원본1,212/피부 홀더67/SRT313/내적 격리블록2,048, 선택 GLSL↔웹GPU448건은 각각 범위가 다른 검증이며 원본 NVN/전체프레임 일치가 아니다.

고정 원본556/986=56.39%·그래픽102/204=50.00%, port13/62=20.97%(일부37/차이9/원본미확정3)·GR0/10/일부7/10 유지. 신규 부분 근거를 기존 복합 질문 전체 확정으로 승격하지 않았다. 몸CP/skin idx·weighted type11/type18·다른 SRT mode/rotation·cube/BRDF/SPP·잠영 파문/Custom1/VAT·native 최종픽셀은 남는다. 최종 테스트·브라우저·보호 SHA와 실패는 r9 요약의 실행 기록을 따른다.


## 카메라 100% 목표 원본 분석 r10 — 2026-10-03

카메라 고정106행의 현재 검토 결과·신규 근거/기존 정정 구분·잔여 추적은 [camera/analysis_100.md](camera/analysis_100.md)와 [analysis_completion.md](analysis_completion.md)를 따른다. 이 작업은 원본 분석·MD 반영이며 웹 코드·에셋·impl 변경은 없다. 100% 목표는 아직 미달이다.

- [스틱 입력·yaw/pitch 응답](camera/r10_input_response.md): 새12,288 native 구간·SDK libm 대조, 비트 불일치0.
- [Module·시작·투영 연결](camera/r10_module_projection.md): whole Module·device 식·valid 래치와 viewport 갱신 시점; liveposture 미확정.
- [상태 생산자·WaterFall](camera/r10_state_producers.md): affine·whole blocked predicate·contact 높이/타이머→normal 보정.
- [쉐이크·슈터·Focused](camera/r10_shake_shooter.md): 원본 수명·gain 묶음·일반 발사/명중 admission·실제 Subjective 값 공급.
- [실제 사격장 메시 붐·Fade](camera/r10_boom_stage_fade.md): 출하TAG0→native Entity/query8면·40float 일치, 별도 Fade helper supplier/material 관계와22,288 부분 실행. authored필터/wholeframe/GPU 잔여 유지.

- [카메라 사격 자세 타이머 보강](camera/r10_posture_timer.md): 원본5632건, Bad0 writer/공중 감소/메인 drain; 모든 상태와 전체프레임 미확정 유지.

- [카메라 렌더·UBO·출력 후속](camera/r10_render_projection.md): 논리 Projection 소비·Context34멤버/2336B·compiled submit/present·SDK1042/0bad. 최종Lby GPU/window는 미확정.

**2026-10-03 r10 actual-source와 자세 타이머 최종 후속:** 상태검증6071,자세timer10752,렌더1042는각범위의원본구간불일치0이다. 지형source는최종16/128f32·RSDB889·Banc15f32·normal128/384f32·rawmask353/2118u32. 지형의slot68 dispatcher/초기posewriter 및최종GPU/window가남으며,고정카메라현재수치는 [analysis_100.md](camera/analysis_100.md)의직접집계를따른다.

## 카메라 r10 사용자 지정 종료 시점 — 2026-10-03

추가 분석을 멈추고 모든 담당 결과를 MD에 반영했다. 현재 고정 카메라 **93/106=87.74%**, 시작78/106 대비 **+15행/+14.15%p**다. 신규 원본 근거 해소13행과 기존 해소 정정2행을 구분한다. 전체는 **571/986=57.91%**이며 **카메라100%는 미달**이다. [최종 집계·근거·잔여13행](camera/analysis_100.md), [전체 감사 목록](analysis_completion.md).

- [상태/탑승 상황 §6.11](camera/r10_state_producers.md): VehicleSpectacle cockpit→typedref/queue/FSM→C1918,새288/0bad;Pipeline/Dokan 기존근거와합쳐고정11/22의상황의미를해소. 전체Lby도달·배송·유효ref수명은별도미검증.
- [지형 붐 §3.1.5](camera/r10_boom_stage_fade.md): 실제Actor→component.vt68 dispatcher와manager조건 판독;Banc→Actor최초pose→native초기적용의마지막동일성은잔여. 새native0,고정4/23/32/38미승격.
- [타이머 §6.2](camera/r10_posture_timer.md): 선행가상대상은PlayerGrindRail,옛Weapon명칭정정. 새4096/0bad,누계14848는부분구간이며전체frame미확정.
- [렌더 §3.4/3.5](camera/r10_render_projection.md): normalframework/worker·origin1/window image·actualHDRtriangle 공급,새64/0bad. 같은frameHDRtarget/window와GPU초기swizzle 미확정;누계1106는CPU계약.

앞6071/10752/1042와slot68dispatcher잔여는후속이전검토시점이다. 이번최종값은상태6359/타이머14848/렌더1106이며서로다른구간을전체scene검증으로합산하지않는다. 웹코드·에셋·impl/original변경및commit/push는없다. 실제명령·실패·검증경계는각문서§10/11과analysis/camera_100_r10/commands.md에보존했다.

## 카메라 웹 r10 반영 — 2026-10-04

[카메라 웹 적용 기록](port/camera_r10.md): 원본 f32 입력/피치·logical투영/aspect래치·blocked/WaterFall/B7a0 소비·쉐이크owner/serial/종료순서를반영했다. 전체359/359·typecheck/build통과. 원본확정93/106·전체571/986은변경없으며실제공급자/GPU경계를유지한다.
