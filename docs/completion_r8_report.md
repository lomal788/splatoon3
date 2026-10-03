# r8 종료 검증 — 사격장 핵심 요소 확정률 증가

2026-10-03 (Asia/Seoul). **요청한 10영역 증가 목표를 모두 충족했다.** 전체 원본 확정은 529/986 (53.65%)이며 전체 100% 분석은 아직 미달이다. 이 보고는 MD 분석 반영 완료이고 웹 구현 완료나 원본 전체 게임 실행 검증을 뜻하지 않는다.

## 1. 기능 개요와 사용자에게 보이는 동작

Splatoon 3 v0 Lby_Lobby00 1인 연습의 물리·카메라·그래픽·피격을 우선하고 이동·스플래시슈터 탄·표적·이펙트·바닥 도색·효과음을 함께 추적했다. 입력→수식/상태→최종 소비자 중 이번에 새로 연결한 경로를 본문 MD에 반영했다. 분모 축소·질문 분할·부분 결과의 복합 전체 승격 없이 r7 고정 항목에 새 원본 근거를 추가했다.

## 2. 분석 대상 원본·버전·자료 위치

작업 폴더 `C:\dev\splatoon3`, 원본 `original/` 읽기 전용. 분석 입력은 v0 추출 `extracted/exefs/main.reloc.img`, `extracted/romfs`, 기존 디컴파일/SHARED/FUNCS다. 신규 함수마다 기존 노트·함수표·decomp_index를 확인하고 실제 함수 경계를 판독했다. 모든 임시·도구·산출물은 같은 작업 폴더 안에 저장했다.

기준은 r7 종료 `analysis/completion/r8/inventory_before.json`(1,119 기록, 범위 내986) 및 `targets.json`이다. 해당 두 파일을 새로 수집/축소하지 않았고 안정ID를 보존했다. 반복 출처의 질문은 r7에 있던 단위대로 남겼다. effect/sound 공통31항목은 고정 분류상 양쪽 목표에 대응하며 전체986에는 한 번만 포함한다.

## 3. 진입점과 전체 호출 흐름

핵심 새 연결은 [물리](physics/phive_controller.md) §6.10.4~5의 initial→접촉target/normal→8normal/7carry→finalize→double COM→몸체 원점→Phive/Actor/Player 위치, [피격 형상](combat/hitbox.md) §2.1의 형태율→game capsule→native sphere/capsule→owner bind, [명중 피드백](combat/hit_effect_pipeline.md)의 판정→큐/FIFO→컬링→이펙트/소리 소비다. 그래픽은 [LOD](graphics/lod_runtime.md)의 실제 모델→단계→MeshLOD→draw 인자, [팀색](graphics/teamcolor_rsdb_source.md)의 RSDB file→typed loader→행 lookup, [AS 무기 이름](graphics/animation_weapon_blackboard.md)의 실제 caller→두 이름 공급을 연결했다. 단계별 판독/실행 경계는 해당 문서를 따른다.

## 4. 구조체·필드·상수·열거형 및 고정 집계

| 영역 | r7 확정/고정 분모 | 현재 확정/고정 분모 | 현재율 | 신규 확정 | 증가 %p | 요청 최소 %p | 상태 |
|---|---:|---:|---:|---:|---:|---:|---|
| 물리 | 39/56 | 51/56 | 91.07% | 12 | +21.43 | +20 | 충족 |
| 카메라 | 44/106 | 67/106 | 63.21% | 23 | +21.70 | +20 | 충족 |
| 그래픽 | 56/204 | 97/204 | 47.55% | 41 | +20.10 | +20 | 충족 |
| 피격 | 35/118 | 59/118 | 50.00% | 24 | +20.34 | +20 | 충족 |
| 이동 | 52/133 | 66/133 | 49.62% | 14 | +10.53 | +10 | 충족 |
| 탄 | 27/50 | 32/50 | 64.00% | 5 | +10.00 | +10 | 충족 |
| 표적 | 29/39 | 33/39 | 84.62% | 4 | +10.26 | +10 | 충족 |
| 이펙트 | 24/85 | 33/85 | 38.82% | 9 | +10.59 | +10 | 충족 |
| 도색 | 42/100 | 52/100 | 52.00% | 10 | +10.00 | +10 | 충족 |
| 효과음 | 20/86 | 30/86 | 34.88% | 10 | +11.63 | +10 | 충족 |

전체 신규 해소 **147개**, 반영 manifest 160개다. 조사중/부분과 확정 불가는 신규 확정에 포함하지 않았다. 현재 상태 수는 기존 해소 표기 49, 미확정 315, 조사중 79, 확정 529, 확정 불가 14이다. 출처별 안정ID와 근거는 [전체 목록](analysis_completion.md), [r8 감사표](completion_r8.md)에 보존했다. 비율은 고정 질문 기록의 원본 근거 확정률이다.

## 5. 상태 전이와 전체 수명

탄 소멸은 요청 즉시 free라는 설명을 정정하고 manager의 비활성 lifecycle/작업·컴포넌트 종료로 기록했다. 무적 bit11은 실제 engine filter-mask 0/복원을 확인했으며 shape 제거로 해석하지 않는다. xlink action 변경·Always·Switch 종료/취소·release 조건과 원본 순서를 기록했다. [AS 첫 tick](graphics/as_request_first_tick.md)과 [그림자 생성/소비](graphics/projected_shadow_runtime.md)의 지원은 검증한 경계만 반영하고 전체 포즈·live 입력 질문은 유지한다.

## 6. 계산식·조건·상세 의사코드

원본 함수의 식·필드·writer/reader·입출력 표는 개별 MD에 있다. 핵심 정밀도 정정은 다음과 같다.

- native 압축 inverse mass는 SHLL 상위16비트 f32 복원이다. mass100 fixture 0x3c24→0.010009765625이며 IEEE FP16이 아니다.
- 물리 carry cap의 `cap/sqrt`와 finalize의 `(1/sqrt)*cap`, 최종 physical velocity와 위치용 COM velocity를 구분한다. COM은 `COM64+=double(f32(vEffective32*dt32))`.
- ColBullet H는 전체 높이다. 일반 h=1.65와r=.35이면 캡슐 endpoint y=.35/1.30이며 오징어 끝점은 sphere 분기로 이어진다. 모양/연결을 임의로 더 자연스럽게 바꾸지 않는다.
- TeamColor14097d0는 로더가 아닌 실제classname leaf14097cc의 중간 주소다. Gyml15사본의 제공196원소는 RSDB와동일이며 기존24/GreenPurple색차이 원문을 날짜·정정 이유와 함께 보존했다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

| 영역 | 신규 확정한 핵심과 수준 | 근거 |
|---|---|---|
| 물리 | 접촉 침투target/normal 순차행·반복·carry/최종속도·COM/몸체 원점 [판독]+[실행];mesh/material/filter native 연결 | [phive_controller](physics/phive_controller.md), [character_controller](physics/character_controller.md) |
| 카메라 | 입력11B/sixaxis producer·활성포저·감도21단계·특수리그/쉐이크·진동 전달 [판독]+[실행] | [player_camera](camera/player_camera.md), [shake_rumble](camera/shake_rumble.md) |
| 그래픽 | AS 이벤트/진행률/무기 두이름·실제LOD/mesh/draw·roughness/transmission/thickness·RSDB 팀색 [판독]+[실행]+[데이터] | [LOD](graphics/lod_runtime.md), [팀색](graphics/teamcolor_rsdb_source.md), [AS](graphics/anim_state_machine.md) |
| 피격 | 배율 원본 행/enum·충격 합성·형태별 native형상·무적bit11·명중반응 소비 [판독]+[실행]+[데이터] | [damage_hit](combat/damage_hit.md), [hitbox](combat/hitbox.md), [hit_effect_pipeline](combat/hit_effect_pipeline.md) |
| 이동 | 입력edge·AP 누적/reset·추가이동벡터·착지spring·상태 조건/실제face법선 소비 [판독]+[실행] | [movement_physics](player/movement_physics.md), [player_state](player/player_state.md) |
| 탄 | 팀producer·WallDrop 표/helper생성소유권·소멸lifecycle [판독]+[실행] | [shooter_bullet](weapon/shooter_bullet.md) |
| 표적 | Main body선택→이동→Actor현재위치·native contactImpulse receiver [판독]+[실행] | [shooting_range](range/shooting_range.md) |
| 이펙트 | render follow/인자·중력소비·FIXED 단위회전·xlink trigger/switch/count [판독]+[실행]+[데이터] | [effect_resources](effect_sound/effect_resources.md), [floor_fixed_rotation](effect_sound/floor_fixed_rotation.md) |
| 도색 | texture runtime로더·실제vertex/panel/seam·패턴recognizer·그룹/root·공유edge 연결 [판독]+[실행] | [colpaint_atlas](paint/colpaint_atlas.md), [model_panel_mapping](paint/model_panel_mapping.md), [panel_connections](paint/panel_connections.md) |
| 효과음 | pitch합성순서·global unit/공간값·xlink 종료/강제재생 전달 [판독]+[실행] | [sound_resources](effect_sound/sound_resources.md), [sound_parameter_composition](effect_sound/sound_parameter_composition.md), [sound_global_unit](effect_sound/sound_global_unit.md) |

## 8. 다른 기능과의 상호작용

충돌/피격/카메라/효과 소비가 같은 프레임에 연결되는 순서를 문서에 남겼다. actor 속도와 물리 엔진 되쓰기, native body와 Phive staging, 게임 위치와 시각 spring, RSDB의 Work/Gyml 행 키와 실제Gyml파일을 구분했다. 원본 코드로 실행한 synthetic/nativefixture를 실제 사격장 전체/최종 GPU 픽셀 검증으로 확대하지 않았다. 혼합 질문의 남은 부분은 고정ID 조사중 상태에 유지한다.

## 9. 웹 포팅 구조와 구현 순서

이번 작업의 결과는 분석 MD다. 웹 반영은 후속 구현에서 아래 순서와 원본 식을 대조해야 한다.

| 우선 | 필요한 반영 | impl 대응 |
|---|---|---|
| 1 | 입력/감도·활성포저·착지spring·이동벡터·native 접촉/COM 정밀도 | physics.md, camera.md |
| 2 | 탄 소유/lifecycle·팀·native 피격형상/무적필터·명중큐·표적physics 되쓰기 | weapon.md, range.md, assets.md |
| 3 | 도색 실제패널/연결/seam·texture 이름배열·GPU 남은부분 경계 | paint.md, assets.md |
| 4 | 실제LOD 모델/mesh 인자·AS state 전달·팀색RSDB·재질 calc/광원 확정부분 | render.md, assets.md |
| 5 | xlink gate/cancel/release·이펙트follow/단위회전·sound합성/공간단위 | fx.md, assets.md |

항목별 정확한 변경은 analysis_completion.md의 “웹 반영 필요” 열에 기록했다. **web/games·web/scripts·web/docs/impl·web/package.json·original 변경 없음, commit/push 없음.** 보호 대상592개 파일 SHA256의 변경/추가0을 검증했다.

## 10. 검증 코드·실행 결과·기대값

실제 명령은 `analysis/completion/r8/*_commands.md`에 성공·실패 모두 보존했다. 아래는 이번 최종 연결의 대표 실행 결과다. 각 하네스의 fixture/SDK/함수 경계는 원본 근거 MD를 따른다.

| 실제 명령 | 결과 |
|---|---|
| `PY web/tools/r8_physics_initial_velocity_emu.py` | whole09d4ba8 1024/12288f32 불일치0 |
| `PY web/tools/r8_physics_prestep_cap_emu.py` | whole0a4b514 2048/12288f32 불일치0 |
| `PY web/tools/r8_physics_finalizer_cap_emu.py` | whole0a4b8c8 2048/6144f32+6144f64 불일치0 |
| `PY web/tools/r8_physics_pose_emu.py` | whole09d5b68 1024/6144f32 불일치0 |
| `PY web/tools/r8_physics_hitshape_native_emu.py` | 1014case/24417f32+6084type/ownerfield 불일치0, native형상owner연결 |
| `PY web/tools/r8_graphics_weapon_category_sources_emu.py` | 실제4source각256=1024 이름비트일치/null0;holderfixture/sink전중단 명시 |
| `PY web/tools/r8_graphics_teamcolor_rsdb_emu.py` | wholetypedloader/namequery36행1296check 불일치0/null0;Gyml15file196 제공원소비트동일 |
| `PY analysis/completion/r8/merge_progress.py` | 고정ID/분모/목표/보호file검사 통과, all_targets_met=true |

`PY`는 작업 폴더의 `.venv/Scripts/python.exe`다. 신규 원본 디컴파일은 Git sh의 `web/tools/full_decomp.sh <analysis/decomp/...c> <실제시작주소...>`로 성공했고 decomp_index에 연결했다. Windows rg glob/없는파일/함수경계 검색 실패, native 초기화/TLS/하네스 인자 실패, cap 계산 순서 및 TeamColor 검사기오프셋 실패도 로그/실패JSON에 보존했다. 없는고정ID 승격은 감사assert에서 거부하여 집계하지 않았다. Cdev는 Git 저장소가 아니어서 status/diff검사 실패를 기록했으며 commit/push를 실행하지 않았다.

물리/접촉 independent f32/f64 대조, 그래픽/도색원본 bytes·branch비교, 명중/음성큐 수명 검증은 합성재구현만 성공한 것을 확정으로 세지 않는다. 원본 whole 함수 실행이라도 fixture로 제공한 입력·검사한 출력·명시적스텁을 넘는 효과는 주장하지 않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

증가 목표는 충족했고 아래 핵심 복합은 미확정으로 남겼다. 원본에서 불가능하다고 일괄 단정하지 않으며 시도/막힌 입력·다음reader/writer를 기록했다.

| 남은 범위 | 아직 확정 못한 이유·다음 근거 |
|---|---|
| 실제 지형/모션속성/TOI | native kernel 식은 해소했으나 실제 SplPlayer runtimeID/모든modifier 및Lby 전체접촉생산 입력까지 연결되지 않음. 0aec920/0aefdc0, quality/motion속성 writer, 실제mesh/계단/경사 사슬 |
| 전체 캐릭터 포즈 | AS request/leaf·진행률/이벤트 부분은 확인했으나 SDK 스켈레탈/재질/가시성 sampler의 전체합성과 정규화 미연결. firsttick연속2tick pool입력 실패도 보존 |
| live 광원/GPU/LUT | Shadow typedapply/생성/소비 일부해소. liveconfig19E0·frame matrix530/factor4E8·ColorGrading115567c 전체operations/LUT 연결이 남아 L342묶음 조사중 |
| 이펙트 전체color/alpha | BDC/BDD/BE0..BE7 전체consumer와 C3d..f/실제combineroption 대응이 남음. 일부필드실행을 전체combiner 확정으로 올리지 않음 |
| 상위 피해 애니·수명/안전복귀 | Damage_Shield 후보·B9228 writer/reader 및 playerState 슬롯19·B78c 다음 입력이 남음. 상세next는고정목록 유지 |

[core_experience_priority.md](core_experience_priority.md)의 새 r8 연결/잔여를 우선하고, [analysis_completion.md](analysis_completion.md)에서 미완료를 따라 다음 원본 분석을 이어갈 수 있다. 분석 가능한 새 경로가 생기면 기존근거 중복을 확인한 뒤 계속 추적한다.
