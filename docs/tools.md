# 분석 도구 사용법

모든 명령은 `c:/dev/splatoon3`에서 Git Bash로 실행합니다. 파이썬은 `.venv/Scripts/python`(이하 `PY`)입니다. 파일 경로는 Windows 형식(`C:/dev/...`)으로 넘기세요. `/c/dev/...`는 Windows 파이썬이 열지 못합니다. 출력에 일본어 등이 섞이면 `PYTHONIOENCODING=utf-8`을 앞에 붙입니다.

주소는 main NSO를 0x7100000000에 올렸을 때의 가상 주소입니다. main에는 **게임 함수 이름이 없습니다**.

## 데이터

| 명령 | 용도 |
|---|---|
| `PY web/tools/spl_data.py ls <x.pack.zs>` | SARC 팩 안 파일 목록 |
| `PY web/tools/spl_data.py cat <파일> [팩 안 경로]` | BYML(.bgyml/.byml/.zs) → JSON 출력 |
| `PY web/tools/spl_data.py unpack <x.pack.zs> <출력폴더> --json` | 팩 전체 해제 + JSON 사본 |

- RomFS: `extracted/romfs/` (목록 `extracted/romfs_list.txt`)
- 액터 팩: `extracted/romfs/Pack/Actor/<이름>.pack.zs`, 씬: `Pack/Scene/`
- 파라미터 표: `extracted/params/Component/GameParameterTable/*.json` (이미 해제됨)
- RSDB 표: `extracted/romfs/RSDB/*.rstbl.byml.zs`
- `Work/A/B.type.gyml` 참조 → 팩 안 `A/B.type.bgyml`

## 코드 찾기

| 명령 | 용도 |
|---|---|
| `PY web/tools/xref.py str <문자열...>` | 문자열 위치와 그걸 참조하는 명령 주소(ADRP+ADD/LDR) |
| `PY web/tools/xref.py addr <주소...>` | 주소를 참조하는 명령 주소 |
| `PY web/tools/disasm.py <주소> -n 40` / `--func` / `--end <주소>` | 디스어셈블(문자열·상수 주석). `--func`는 함수 시작으로 되돌아가 ret까지 |
| `PY web/tools/class_info.py <spl::클래스명...> [--diff]` | 클래스 이름 → vtable·슬롯 수·생성 함수, vtable 비교 |
| `PY web/tools/param_reflect.py <필드명...>` | 파라미터 구조체 필드 오프셋·타입·기본값 |
| `analysis/param_reflect/<$type>.json` | 154개 파라미터 타입의 판독 결과(이미 생성됨) |
| `extracted/main_strings.txt` | main rodata 문자열 덤프(grep용) |

경로 잡는 요령:
1. 데이터 이름(파라미터 필드명, `$type`, `ClassName`, 열거형 값)을 `xref.py str`로 찾는다.
2. 참조 주소에서 `disasm.py --func`로 함수 시작을 찾는다.
3. 클래스는 `class_info.py`로 vtable을 얻고, 슬롯 함수를 즉석 디컴파일한다.
4. 열거형은 `spl::<이름>` 문자열 바로 다음 줄(`main_strings.txt`)에 `값0 , 값1 , ...`로 있다.

## 전체 분석 프로젝트 디컴파일 (우선 사용)

main 전체 Ghidra 분석이 끝났습니다(8,547초, 함수 144,170개, `analysis/functions/main.nso.tsv`).

```sh
sh web/tools/full_decomp.sh C:/dev/splatoon3/analysis/decomp/<영역>/<이름>.c <주소...>
PY web/tools/func_lookup.py <주소...>     # 주소가 속한 함수 시작·크기 (전체 분석 기준, 가장 정확)
```

- 호출당 약 30초, 3개까지 동시(`ghidra_proj/spl3_main` + 사본 `f1`, `f2`). 이미 색인된 주소는 건너뜁니다.
- 함수 경계가 즉석 디컴파일보다 정확합니다. 예: 즉석 디컴파일은 Brake 스텝 `0x71017658cc`에 `0x71017683fc`(별도 함수로 꼬리 분기)를 합쳐 보여 줍니다.
- 즉석 디컴파일로 이미 색인된 함수를 전체 분석 기준으로 다시 받으려면 `state_redecomp.sh`를 쓰세요(`full_decomp.sh`는 색인된 주소를 건너뜀).
- 함수 시작을 모를 때는 `func_lookup.py`를 쓰세요(`network_fstart.py`, `disasm.py --func`보다 우선).

## 즉석 디컴파일

```sh
sh web/tools/quick_decomp.sh C:/dev/splatoon3/analysis/decomp/<영역>/<이름>.c 0x7101234560 0x7101234abc ...
```

- 이미 디컴파일된 주소(`analysis/decomp/INDEX.tsv`)는 자동으로 건너뛰고 어느 파일에 있는지 알려 줍니다. 끝나면 색인을 갱신합니다.
- 조회: `PY web/tools/decomp_index.py <주소|이름 일부>` — 디컴파일 파일 위치와 `analysis/notes/FUNCS.tsv`에 등록된 함수 의미를 함께 보여 줍니다.
- 병렬 작업 규칙(선점·공유·추가 전용)은 `analysis/notes/SHARED.md`를 따릅니다.
- 인자는 **함수 시작 주소**여야 합니다(`network_fstart.py`로 확인, 작은 함수는 `disasm.py --func`도 됨).
- 호출 한 번에 프로젝트 로딩으로 약 2분이 걸립니다. 주소를 모아서 한 번에 넘기세요(100개 이상도 됨).
- 동시 실행은 4개까지(`ghidra_proj/q0~q3`), 그 이상은 빈 슬롯을 기다립니다.
- 분석 없는 raw 이미지라 호출 대상은 `func_0x...`, 전역은 `DAT_`/`uRam...`로 나옵니다. 데이터 포인터 값은 재배치가 적용된 상태입니다.
- 전체 분석 프로젝트는 `full_decomp.sh`로만 여세요(잠금 슬롯 관리).

## 공용 보조 도구 (영역 분석 중 추가, 표준을 정함)

같은 일을 하는 도구가 영역마다 따로 생겼습니다. 새 작업에서는 아래 **표준**을 쓰고, 영역 도구는 그 영역 문서가 참조하므로 지우지 않고 둡니다.

| 용도 | 표준 | 같은 일을 하는 영역 도구 | 비고 |
|---|---|---|---|
| BL/B 직접 호출자 | `bl_callers.py <주소...>` | `combat_callers.py`, `paint_blrefs.py`, `ui_blcallers.py`, `graphics_blcallers.py`, `effect_blcallers.py` | `xref.py addr`는 ADRP 참조만 찾으므로 직접 호출은 이것으로 |
| 함수 시작 추정 | `network_fstart.py` | `paint_funcstart.py`, `gimmick_funcs.py`, `camera_funcs.py`, `ui_funcs_in_range.py` | `disasm.py --func`는 큰 함수(분기가 멀리 떨어진 함수)에서 틀릴 수 있음. BL 대상·데이터 포인터 기준 추정이 더 안전 |
| 외부(PLT) 함수 이름 | `player_imports.py [정규식]` | `paint_imports.py` | atanf, sqrtf, logf, expf 등 |
| 파라미터 필드 리더 찾기 | `camera_fieldreaders.py` | `combat_param_reader_scan.py`, `paint_fieldscan.py` | "설정됨 플래그 ldrb + 값 ldr" 근접 패턴 |
| f32 상수 위치 | `paint_findconst.py` | `network_constscan.py` | movz/movk, 리터럴 |
| vtable 슬롯 출력 | `player_vt.py` | `combat_vtname.py`(이름 반환 함수) | `class_info.py`는 클래스명 → vtable |
| 포인터 역참조 | `effect_ptrscan.py` | | 데이터 영역에서 특정 주소를 담은 위치 |
| 디컴파일 정리 | `decomp_clean.py <파일> [주소...]` | `gimmick_annot.py`, `player_annot.py` | 상속 조회 반복문 접기. `player_annot.py`는 bss 상수 값을 주석으로 붙임 |
| 큰 함수 디컴파일 | `player_bigdecomp.sh` | | `quick_decomp.sh`의 180초 제한에 걸리는 함수용 |
| 원본 함수 실행(에뮬) | `network_uc.py`(하네스), `player_initemu.py`(정적 초기화) | `network_emu.py`, `player_gear_emu.py` | `.venv`에 unicorn 설치됨. 스텁으로 바꾼 함수는 각 문서에 명시 |

`.venv` 패키지: cryptography, zstandard, lz4, capstone, numpy, pillow, texture2ddecoder, unicorn.

## 영역별 도구

| 영역 | 도구 | 문서 |
|---|---|---|
| 물리 | `physics_memscan.py`(오프셋별 ldr/str 전수 검색), `physics_jump.py`(수직 속도 재구현) | [physics/phive_controller.md](physics/phive_controller.md) |
| 탄 | `bullet_shooter_sim.py`(속도 상태머신·초기 속도), `bulletbody_integrate.py`(바디 적분 f32 재구현, pos+=vel과 비교), `bulletbody_immscan.py` | [weapon/shooter_bullet.md](weapon/shooter_bullet.md) |
| 플레이어 | `player_gear.py`, `player_move.py`, `player_scan.py`, `move_jump_emu.py`(점프 곡선 원본 함수 연결 실행), `state_table.py`(상태 표 286행), `state_asb.py`(ASB 파서), `state_verify.py` | [player/movement_physics.md](player/movement_physics.md), [player/player_state.md](player/player_state.md) |
| 데미지·생명 | `combat_damage.py`, `combat_layers.py`, `life_hp.py`, `life_emu.py`(HP 홀더 원본 실행), `respawn_emu.py`(리스폰 타이머 원본 실행) | [combat/damage_hit.md](combat/damage_hit.md) |
| 도색·점수 | `paint_shape.py`, `paint_score.py`, `gauge_emu.py`·`gauge_sim.py`(게이지), `paintgpu_record_emu.py`·`paintgpu_renderstate_emu.py`(원본 실행), `paintgpu_frame_sim.py`(한 프레임 패스 재구현) | [paint/paint_and_score.md](paint/paint_and_score.md) |
| 카메라·손맛 | `camera_swerve.py`, `camera_rig.py`, `camera_shake.py`, `camera_rumble_map.py`, `camera_ldscan.py` | [camera/camera_feel.md](camera/camera_feel.md) |
| 셰이더 | `shader_paint_overpaint.py`(도색 스탬프 재구현), `shader_meteraction.py`(UI 게이지), `shader_ryujinx/`(ShaderLibrary + Ryujinx 역번역) | [graphics/shaders.md](graphics/shaders.md) |
| 그래픽 | `graphics_bntx_fmtscan.py`, `render_aamp.py`(env AAMP), `render_ubo_layout.py`, `render_asnode_vt.py`, `render_storescan.py`, `render_bytescan.py`, `graphics_verify/teamcolor_ink_test.mjs`, `graphics_convert.py`, `graphics_bntx.py`(0x12 = R16_G16로 정정, 0x15 FLOAT은 `effect_bntx_float.py`), `graphics_bfres2gltf/`, `graphics_verify/` | [graphics/model_character.md](graphics/model_character.md) |
| 이펙트·사운드 | `effect_xlink.py`, `effect_xlink_eval.py`, `effect_xlink_summary.py`, `effect_usernames.py`, `effect_esetb.py`, `effect_vfxb46.py`, `effect_vfxb.py`, `effect_bntx_float.py`(R16G16B16A16 FLOAT), `vfx_emitter46.py`(이미터 필드·파티클 시뮬), `vfx_resfield_scan.py`, `sound_constscan.py`, `sound_bars.py`, `sound_alto.py`(AROC 롤오프) | [effect_sound/effect_sound.md](effect_sound/effect_sound.md) |
| 기믹 | `gimmick_stage.py`, `gimmick_phive.py`, `gimmick_lift.py`(이동 발판 일정·회전), `gimmick_reflect_fix.py`(커브 필드 뒤 오프셋 꼬임 정정), `collision_tag0.py`·`collision_mesh.py`(Havok TAG0 / hknpMeshShape → glb), `collision_scan.py`, `collision_interior.py`(용접 비트필드) | [gimmick/stage_gimmicks.md](gimmick/stage_gimmicks.md) |
| 네트워크 | `network_typereg.py`, `network_typetable.py`, `network_bitlayout.py`, `network_verify.py`, `network_hashuse.py`, `network_netparam_scan.py`, `network_bitpack.py`, `network_clock.py` | [network/network.md](network/network.md) |
| UI | `ui_sarc.py`, `ui_lyt.py`, `ui_msbt.py`, `ui_font.py`, `ui_render.py`, `ui_animcmd_emu.py`(애니 명령 원본 실행), `ui_animorder_emu.py`(애니 적용 순서 원본 실행), `ui_minimap_shader.py`, `camera_stick_emu.py`(스틱 반전 원본 실행), `ui_minimap.py`, `ui_vcall_scan.py`, `gauge_*.py` | [ui/ui_hud.md](ui/ui_hud.md) |

## 알려진 함정

- capstone으로 넓은 구간을 한 번에 `disasm()`하면 첫 데이터 워드에서 조용히 멈춥니다. `md.skipdata = True`를 켜거나 명령 단위로 디코드하세요(`disasm.py`는 명령 단위라 영향 없음).
- 리플렉션 도구는 커브 필드 뒤에서 오프셋이 뒤바뀝니다(커브는 "값 → 이름 → 플래그" 순서). `gimmick_reflect_fix.py`로 바로잡습니다.
- 오프셋 스캔은 사전 인덱스 주소(`ldr x, [x, #0x94]!`) 뒤 상대 오프셋으로 읽는 경우를 놓칩니다(탄 바디 +0xc4가 이렇게 읽힘). `bulletbody_immscan.py` 참고.
- `Model/Obj_Sponge.bfres.zs`처럼 2바이트짜리 자리표시 파일이 있습니다. 변환 실패를 데이터 오류로 오해하지 마세요.

## 지켜야 할 것

- `c:/dev/splatoon3/original/`은 읽기 전용입니다.
- 작업 파일은 전부 `c:/dev/splatoon3` 안에 둡니다. 문서는 `web/docs/`, 새 파이썬 도구는 `web/tools/`, 디컴파일 결과는 `analysis/decomp/<영역>/`.
- 키 값은 문서·출력에 옮기지 않습니다.

## r8 연결 검증 도구 (2026-10-03)

도구는 저장된 실제 명령과 fixture·스텁·경계를 해당 문서 §10 또는 `analysis/completion/r8/*_commands.md`에서 확인한 뒤 실행한다. 아래 성공은 표의 함수 범위를 뜻하며 원본 전체 게임 실행을 뜻하지 않는다. 신규 물리 world/contact 탐색 도구는 진행 중으로 별도 기록하고 전체 솔버 확정으로 간주하지 않는다.

| 영역 | web/tools 도구 | 원본 실행 범위·문서 |
|---|---|---|
| 피격 | `r8_combat_knockback_chain_emu.py` | 게임 메시지→실제 큐·컴포넌트→f32 충격 합성 — [combat/knockback_pipeline.md](combat/knockback_pipeline.md) |
| 피격 | `r8_combat_critical_lifecycle_emu.py` | 원본 생성·등록·reset 방송/수신 — [combat/critical_ring_lifecycle.md](combat/critical_ring_lifecycle.md) |
| 피격 | `r8_camweapon_zero_hp_event_emu.py` | 대상 HP0의 원본 Helper init·listener와 송신 진입 경계 — [combat/player_life.md](combat/player_life.md) |
| 피격 | `r8_camweapon_ref_rigid_binding_emu.py` | 실제 body name getter·순회→receiver 목록 바인딩 — [combat/hitbox.md](combat/hitbox.md) |
| 명중 이펙트 | `r8_hiteffect_consume_emu.py` | 반응 enum·큐/FIFO·원본 소비자·S1/E1/S2/E2·컬링 — [combat/hit_effect_pipeline.md](combat/hit_effect_pipeline.md) |
| 이펙트 | `r8_fx_identity_emu.py` | 실제 init_array 등록·정적 초기화→속도0 회전 소비 — [effect_sound/floor_fixed_rotation.md](effect_sound/floor_fixed_rotation.md) |
| 충돌 필터 | `r8_physics_bit11_pair_emu.py` | bit11 setter→전체 staging→실제 native pair filter — [physics/character_controller.md](physics/character_controller.md) |
| 형태별 피격 형상 | `r8_physics_hitshape_emu.py` | 24f5dd8 전체 함수 일반 조건·히스테리시스·f32 shape 기록 — [physics/character_controller.md](physics/character_controller.md) |

추가 함정: `func_lookup.py`와 `decomp_index.py`의 최근 선행 함수는 Ghidra 미정의 구간에서 실제 함수 경계를 뜻하지 않을 수 있다. 반환 크기·명령 prologue를 확인한다. HitEffect enum getter는 인자별 문자열 함수가 아니라 전체 문자열 pointer 배열을 반환한다. 큐의 빈 sentinel은 null이 아니라 head 주소이며, ActorRef 무효값은 실제 필드의 −1이다. 원본 signed/unsigned·NaN 결과와 f32 계산 순서를 문서의 재현식대로 유지한다.


### r8 최종 체인 검증 추가 (2026-10-03)

| 도구 | 확인 범위 | 근거 |
|---|---|---|
| `r8_physics_hitshape_native_emu.py` | game ColBullet/Chariot 기록→sphere/capsule 선택→원본 native shape 교체·owner bind. 실제 부착 몸체 broadphase 전체는 제외 | [combat/hitbox.md §2.1](combat/hitbox.md) |
| `r8_physics_initial_velocity_emu.py`, `r8_physics_prestep_cap_emu.py`, `r8_physics_finalizer_cap_emu.py`, `r8_physics_pose_emu.py` | 초기속도→carry→최종 physical/COM 속도→double 적분→native 원점·잔차. 무회전/관성0·감쇠0 경계의 whole 원본 함수와 독립 식 대조 | [physics/phive_controller.md §6.10.4~5](physics/phive_controller.md) |
| `r8_camweapon_contact_*_emu.py`, `r8_combat_solver_info_emu.py`, `r8_combat_contact_quality_emu.py` | 접촉 bias·유효질량·single/dual normal 순차행, 계수 생산과 quality cache 입력. 정확한 파일별 명령은 contact_kernel_commands.md/physics_commands.md | [physics/phive_controller.md §6.10.4](physics/phive_controller.md) |
| `r8_graphics_weapon_category_sources_emu.py` | 실제4 AS 입력 공급 caller·Shtr/Shtr 및 빈 이름. holder는 fixture, sink 뒤 전체 포즈는 제외 | [graphics/animation_weapon_blackboard.md](graphics/animation_weapon_blackboard.md) |
| `r8_graphics_teamcolor_rsdb_emu.py` | 실제 RSDB36행 typed loader/lookup1296검사, metadata/hash/classname, Gyml15 사본196 제공 값 bit 비교. 상위 파일 로드는 판독 | [graphics/teamcolor_rsdb_source.md](graphics/teamcolor_rsdb_source.md) |

최종 정정: native 압축 inverse mass의 SHLL 상위16비트 복원을 IEEE FP16으로 읽지 않는다. prestep의 `cap/sqrt`와 finalizer의 `(1/sqrt)*cap`, f32 곱을 double로 올리는 COM 순서를 합치지 않는다. TeamColor `14097d0`은 로더가 아닌 classname leaf14097cc의 중간 주소다. 기존 함수/기존 근거는 새 실행 건수나 새 확정 행으로 중복 계상하지 않는다.

| 추가 도구 | 검증 범위 | 본문 |
|---|---|---|
| `r8_camweapon_as_request_first_tick_emu.py` | 요청 whole1,025 + 첫 틱 whole1,025 + 래퍼 복사 블록1,025; 9,225 f32 비트 일치. metadata·출력 capacity0·연속2틱 실패 경계 유지 | [graphics/as_request_first_tick.md](graphics/as_request_first_tick.md) |
| `r8_gfx_projected_shadow_creation_emu.py` | 그림자 생성 블록64사례·126객체 및 Scene 등록. 실제 도구 이름과 단계별 명령은 shadow 지원 문서 확인 | [graphics/projected_shadow_runtime.md](graphics/projected_shadow_runtime.md) |

## Shader 역번역의 c1 분기표 함정 (2026-10-03 추가)

기존 `shader_dump/Program.cs`는 inline c1 값을 GLSL 생성 **뒤** 치환했지만 IGpuAccessor.ConstantBuffer1Read를 구현하지 않았다. Ryujinx Decoder가 BRX 간접 분기표를 읽을 때 기본0을 받아 CCLUT color_correction_map의 switch 분기가 누락됐다. 315행 역번역이원본전체수식이라고판정하면실패다.

표준 도구는 이제 ControlShader.GetConstants(byteCode)를 Acc에 전달하고 ConstantBuffer1Read(offset)로 실제 u32를 공급한다. 빌드된표준CLI로다시덤프하면map pixel1694행이며독립보완CLI와SHA256동일. 근거 [graphics/ink_lighting_r2.md](graphics/ink_lighting_r2.md), 자료 analysis/visual_gap_r2/light/cclut_map_canonical. 기존 산출물을 무조건완전한GLSL로믿지말고 BRX가있는셰이더는보완도구로검사한다. 세FX프로그램1202/1885/1385의vert/frag6파일은재검사출력이같았다.

raw 명령·stage header검사는 `dotnet analysis/visual_gap_r2/fx/build/bin/Release/net7.0/shader_raw_audit.dll <bfsha> <model> <program> <outprefix>`와 `... ops <outprefix.vert.bin>`를사용한다. shader raw/역번역은[판독]이며원본GPU[실행]으로표기하지않는다.

## 카메라 r10 원본 검증 도구 (2026-10-03)

실행 위치는 `C:/dev/splatoon3`이며 `python -X utf8`을 사용한다. ELink/zstandard를 읽는 도구는 `.venv/Scripts/python.exe -X utf8`을 사용한다. 도구의 원본 실행 구간과 합성 입력·capture 경계를 해당 문서 §10에서 먼저 읽는다.

| 도구 (`web/tools/`) | 원본 검증 범위 | 근거 |
|---|---|---|
| `r10_camera_input_emu.py` | 스냅/bias/yaw/pitch 네 구간·SDK libm, 12,288 독립 비트 대조 | [입력 응답](camera/r10_input_response.md) |
| `r10_camera_input_chain_probe.py` | raw stick→실제 blocked predicate→yaw/pitch 연결 관측16건 | [입력 응답](camera/r10_input_response.md) |
| `r10_camera_module_emu.py` | 실제 poser callbacks→whole Module/view/projection, 모든 device posture 식·aspect/valid | [모듈·투영](camera/r10_module_projection.md) |
| `r10_camera_start_dispatch_emu.py` | 실제 component VT→Behavior slot15, startup 전후 순서/래치 | [모듈·투영](camera/r10_module_projection.md) |
| `r10_camera_state_emu.py`, `r10_camera_state_water_emu.py` | affine 생산자·whole blocked predicate·Water 높이/타이머/법선 | [상태 생산자](camera/r10_state_producers.md) |
| `r10_camera_shake_data.py`, `r10_camera_shake_emu.py`, `r10_camera_shake_focused_emu.py` | 원본 ELink·쉐이크 수명·admission·실제 Subjective 값 공급 | [쉐이크·슈터](camera/r10_shake_shooter.md) |
| `r10_camera_boom_tag0_probe.py`, `r10_camera_boom_mesh_query.py`, `r10_camera_boom_mesh_verify.py` | 출하TAG0→native Entity/world mesh query8면·40float | [지형 붐](camera/r10_boom_stage_fade.md) |
| `r10_camera_boom_fade_emu.py` | 시간·type1/type2·cache, 22,288; material-null cache는 upload 실행 아님 | [물체 Fade](camera/r10_boom_stage_fade.md) |

추가 함정: SDK libm hook을 기존 Python hook 뒤에서 다시 실행하면 삼각함수가 중복 적용된다. single PLT bridge를 사용한다. `user+B8` property index와 `user+80`의 현재값, FadeType index와 enum value, Entity query wrapper와 body-pair backend를 구분한다. Ghidra가 제거한 조건이라도 raw FMIN/FCMP는 실제 원본과 대조한다. BSS0·포인터 참조 없음·유한 fixture의 비트 일치는 live 상태값이나 모든 동적 writer의 부재 증명이 아니다.

## Negate 괄호 출력 함정 — 2026-10-03

bundled Ryujinx InstGen.Negate의 `zero - expr`는 Special/unary precedence 때문에 곱 안에서 괄호 없이 출력된다. 원시 p1714 `eyeX*(-invLen)`이 GLSL `eyeX*0-invLen`로 바뀐다. 원본 이상 동작이 아닌 분석도구 오류다. [표면 raw·paired 보완 CLI](graphics/reference_ink_surface.md), [캐릭터](graphics/reference_character_lighting.md), [FX](effect_sound/reference_shooter_visuals.md). 표준 CLI/번들DLL은 이번에 바꾸지 않았다. 분석 전용 source copy에서 반환식 전체 괄호 한 곳을 보완한 CLI를 analysis/reference_graphics_r3/surface/dump에 저장했다. 분석용 새source adapter의 인터페이스 차이도 commands.md에 기록했다. CB1 분기표 보완과 별개이므로 legacy GLSL SHA동일/생성성공을 수식 동등성 증명으로 삼지 않는다.

- `r10_camera_posture_timer_scan.py`: direct ad0 u32 store·ADD alias 후보 검색. 같은offset은 타입 근거가 아니며 passed-pointer/register-offset 누락 가능.
- `r10_camera_posture_timer_emu.py`: writer2048·countdown3072·main drain512 원본 정수대조. getter이후 n4/active 술어/진입조건 공급과 실제wholeframe 미검증을 구분한다.

- `r10_camera_state_classifier_data.py`/`r10_camera_state_classifier_emu.py`: 원본19타입 getName/VT/RTTI/literalMOV→store 및 unknown0 대조100·null/same-primary skip10. typeguard-ready byte24개는 합성 초기화후 입력이다.
- `r10_camera_posture_active_emu.py`: active 술어→countdown4096 대조.245aa00/Jetpack/weapon predicate 선행반환 입력과 ARM NaN분기를 명시한다.
- `r10_camera_posture_main_floor_emu.py`: main drain→stack3cd/3ce/3cf×4 하한1024 대조. stack 생산자는 미확정이며 감소만의 앞512건을 최종값으로 확대하지 않는다.

- `r10_camera_shake_posture_emu.py`/`r10_camera_shake_ubo_emu.py`/`r10_camera_shake_viewport_emu.py`/`r10_camera_shake_sdk_nvn_emu.py`: bridge696/UBO97/viewport·base/derived present152/SDK97, 합계1042. 실제SDK RAM 재배치 후 strcmp/math/packet 명령 실행. UBO allocation/copy·API capture와 합성 boot profile 경계를 따로 기록한다. API fallback 검사와 explicit swizzle packet은 실제 Lby GPU 초기값의 증명이 아니다.
- `func_lookup.py`는 떨어진 함수 body 크기 때문에 앞 함수 시작을 반환할 수 있다.117230c/35036b4는 실제 prologue/RET로 경계를 재검증했다. `r10_render_projection.md` §10의 실패·정정 참고.

- `r10_camera_state_demo_emu.py`: parameter defaults2/parser128/selectedwhole receiver408/emptyqueuewholetick384=922 대조,actualIsA282calls/스텁0. 메시지/owner/global 입력과readyguard3은합성경계. Time<0의FCMP/FCSEL MI와NaNraw비트,component 초기값과message 기본값을구분한다. 피치 reader에는wholeblocked를그대로이식하지않는다.

- `r10_camera_boom_actor_source.py`/`r10_camera_boom_banc_source.py`/`r10_camera_boom_source_contract.py`: actualRSDB membership889·Banc originaldefault/parser/matrix15f32·Default registry/factory와entrybitnormal128/384f32 대조. 원본SDK sinf/cosf와호스트hook을중복적용하지않는다.
- `r10_camera_boom_mesh_query.py --actor-source`와`r10_camera_boom_mesh_verify.py --actor-source`: 실제helper/config/비마스크/태그/Banc→actualTAG0 최근접16/128f32. create-info→body matrix·runtimeholder·worldbootstrap adapter와미연결slot68 dispatcher를명시한다. 이표본을임의경사/모서리/전체Scene 독립검증이라고확대하지않는다.

- `r10_camera_posture_grind_gate_emu.py`: original24a0038..00f4/actualPlayerGrindRailVT의 선행bool4096건 독립참조식 대조,스텁0. active하네스의옛key `weapon`은GrindRail합성결과이며Weapon인터페이스가아니다. func_lookup가2531020/25310d0을선행2530fe0으로돌려도실제leaf RET/VT슬롯으로시작을확인한다.

- `analysis/camera_100_r10/boom/next_record.py`: 종료후속기록28/28PASS(원문/포인터/고정4행SHA/5열TSV/11절). native실행검사가아니다. 짧은offset을bl_callers.py에넣어0건이면함수부재로해석하지말고0x710...fullVA로조회한다.

- `r10_camera_shake_next_frame_emu.py`: wholeframework3501dbc32+target35a83f432=64/0bad. clock96/SetRenderTargets32/colorTransition78/depthTransition16은공급/capture 경계다. SDK_stubs빈사전만보고wholeGPU/NVNhelper를실행했다고해석하지않는다.

- `r10_camera_state_next_vehicle_emu.py`: selectedwhole receiver192+queue/FSM→Controlledcallback직전96=288/0bad. 실제SDKmemset offset581ba8을mainPLT/GOT에RAM으로연결,새함수반환스텁0. invalid/emptyref만실행했으므로validref retain/thread·실제scene도달을증명하지않는다.
