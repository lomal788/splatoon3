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
