# 사격장 충돌 보완 분석 — 검증 기록

분석일: **2026-10-03**(충돌 보완), 같은 날 5차(r5 physics)에서 본문 문서로 합침. 대상은 Splatoon 3(v0)의 1인 시험 사격장 `Lby_Lobby00`이다. 웹 코드는 변경하지 않았다.

이 문서는 **검증 기록만** 남긴다. 확정 내용은 아래 본문 절로 옮겼다. 같은 설명을 두 곳에 두지 않는다.

## 1. 확정 내용이 옮겨 간 곳

| 내용 | 수준 | 본문 위치 |
|---|---|---|
| 공통 쌍 필터 결합식(양방향 표비트·레이어·하위 레이어 마스크 6개 AND) | [실행] | [character_controller.md](character_controller.md) §3.5 |
| shapeTag 행 선택 한 단계 `0x7103ad6a70` | [실행] | [character_controller.md](character_controller.md) §3.5, [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §3.4 |
| 비교 그룹 F+0x30 공급자(`0x71012eab48`/`0x71012eac80`/`0x71021f2e70`)와 쓰는 곳 | [판독] | [character_controller.md](character_controller.md) §3.5 |
| 리셋 몸체 원점 `0x71024f4440`, 반경 setter `0x7103a6a878`, 월드+0x21c 기본값 | [실행]+[판독] | [character_controller.md](character_controller.md) §4 |
| Phive 월드 6단계(Pre1~3/Post1~3)와 Post3 접촉 작업 등록 | [판독] | [phive_controller.md](phive_controller.md) §6.7.2 |
| 프레임 안 실행 순서(액터 슬롯 ↔ 물리 ↔ 접촉 큐) | [판독]+[실행] | [phive_controller.md](phive_controller.md) §6.7 |

이전 판의 결론 중 바뀐 것:
- 정정(2026-10-03, 5차): "소형 함수 `0x71012eac80`·`0x71021f2e70`도 같은 매핑"은 매핑만 같고, **현재 그룹이 0 일 때만 쓰는 조건은 일반 함수 `0x71012eab48`에만 있다**. 소형 두 함수는 조건 없이 쓴다(명령 `0x71012eac80`~`0x71012eacac`, `0x71021f2e70`~`0x71021f2e88`).
- 정정(2026-10-03, 5차): "등록된 접촉 작업이 액터 슬롯19·21·22 대비 언제 실행되는지 [미확정]"은 해소되었다. 접촉 반응(Entity) 시퀀서는 단계1 그룹0 이라 물리 직후·모든 액터 슬롯19/21 앞에서 큐를 비운다.
- 정정(2026-10-03, 5차): "world+0x21c 런타임 writer 미확인"은 월드 생성자 복사(설명자+0x80)와 기본 설명자 값 0.05 까지 판독되었다. 덮어쓰기 블록 공급자는 남았다.

## 2. 자료

| 자료 | 위치 |
|---|---|
| 실행 이미지 | `extracted/exefs/main.reloc.img`, main 기준 `0x7100000000` |
| 필터 판독 | `analysis/decomp/combat4/filter_1.c`, `filter_2.c`, `analysis/decomp/completion/collision_filter_followup.c`, `collision_shape_filter.c`, `collision_shape_tag.c` |
| 플레이어 리셋 | `analysis/decomp/completion/collision_player_reset.c` |
| 월드 단계 | `analysis/decomp/phys4/p4_world_ctrl.c`, `p4_phases.c`, `p4_seq.c` |
| 5차 판독 | `analysis/decomp/r5_physics/*.c`(order1, behav1, actor1~4, actorjob, mgr1~7, cseq*, seqcreate, calcprio*, group, bphsh) |
| 원본 실행 도구 | `web/tools/collision_filter_completion_emu.py`, `collision_origin_completion_emu.py`, `r5_physics_frameorder_emu.py` |

## 10. 실행 검증·명령·결과

| 명령 | 원본 실행 결과 | 한계(스텁·합성) |
|---|---|---|
| `.venv/Scripts/python web/tools/collision_filter_completion_emu.py` | 쌍 필터 `0x7103af44e8`+`0x7103c4dd30` 4096/4096 정수 일치, 불일치 0 | 합성 표/마스크, 표 객체 vt+0x8 형 조회만 스텁(1 반환), 월드 bit3 = 0 |
| 같은 명령(두 번째 결과) | shapeTag 행 선택 `0x7103ad6a70` 1024/1024 정수 일치, 불일치 0 | 잎 결과 tag 는 디스패치 스텁이 공급, 행 배열은 합성 |
| `.venv/Scripts/python web/tools/collision_origin_completion_emu.py` | 리셋 원점 `0x71024f4440` 1024/1024 f32 비트 일치, 불일치 0 | 부수 함수·상태 동기화 스텁, 반경은 명시 입력 |
| `.venv/Scripts/python web/tools/r5_physics_frameorder_emu.py` (5차) | CalcPriority `0x7103dec4e8` 10/10, 목록 연결 `0x7103c88e74` 13/13, 그래프 구성 `0x7103c85fbc` 사격장 58/58 간선·무작위 500/500 정확 일치 | 그래프 노드 추가 `0x710351c678`(순번 id)·뮤텍스·시퀀서 vt+0x10(=1)·CalcPriority 정적 표 스텁. 작업자 ≥ 2 묶음 분기·시퀀서 간 의존·동적 물리 하위 그래프 미실행 |

결과 파일: `analysis/completion/collision_filter_emu.json`, `collision_shape_tag_emu.json`, `collision_origin_emu.json`, `r5_physics_frameorder_emu.json`. 디컴파일 명령·조회 실패 기록은 `analysis/completion/collision_commands.md`에 있다. 원본 게임 전체를 실행한 검증은 아니다.

## 11. 남은 질문

남은 질문과 다음 주소는 본문 문서의 미확정 표에 한 곳으로 모았다: [phive_controller.md](phive_controller.md) §9, [character_controller.md](character_controller.md) §9, [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md) §7.

## 10.1 6차(r6) 원본 실행 기록

| 명령 | 결과 | 스텁 |
|---|---|---|
| `.venv/Scripts/python web/tools/r6_physics_writeback_emu.py` | 평상시 write-back 1024/1024 비트 일치 | PLT TLS·guard, 캡슐 IsA |
| `.venv/Scripts/python web/tools/r6_physics_shapefilter_emu.py` | 형상 행 결합 4096/4096 | 형상 vt, Havok 잎 디스패치, 표 형 조회 |
| `.venv/Scripts/python web/tools/r6_physics_contactsort_emu.py` | 접촉 정렬 모드3 3000/3000 | 없음 |
| `.venv/Scripts/python web/tools/r6_physics_sublayer_emu.py` | 하위 레이어 선택 4000/4000 | 몸체 순회·setSubLayer 기록 |
| `.venv/Scripts/python web/tools/r6_physics_gravity_emu.py` | 중력 사슬 4/4 | 팩토리 malloc/memset/PLT |
