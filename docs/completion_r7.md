# Lby_Lobby00 1인 연습 — 7차 추가 분석

2026-10-03. 사용자가 추가한 5·6차 문서를 먼저 읽고 남은 미확정을 병렬 분석했다. 웹 구현은 변경하지 않았다.

## 1. 기능과 영역별 집계

**사용자 최우선: 카메라·물리·사격·바닥 도색·그래픽.** [핵심 체감 경로](core_experience_priority.md)의 끝까지 원본 근거가 이어지는 것을 먼저 해결한다. 아래 처리율이 올라가도 이 다섯 경로가 미확정이면 전체 해결로 평가하지 않는다.

**확정 382/986 = 38.74%**, 6차 370/986에서 **12개 출처 기록 추가 확정**. 이번 갱신은 31개 기록이다. 중복 출처를 보존한 목록 처리율이며 게임 전체 파악도를 뜻하지 않는다. 부분 해소는 확정으로 세지 않았다.

| 영역 | 항목 수 | 확정 | 이번 증가 | 확정률 |
|---|---:|---:|---:|---:|
| 카메라·조준 | 106 | 44 | +3 | 41.51% |
| 이동 | 133 | 52 | +2 | 39.10% |
| 물리·충돌 | 56 | 39 | +1 | 69.64% |
| 탄·무기 | 50 | 27 | +1 | 54.00% |
| 도색 | 100 | 42 | +0 | 42.00% |
| 그래픽 | 204 | 56 | +1 | 27.45% |
| 피격·판정 | 118 | 35 | +0 | 29.66% |
| HUD | 40 | 22 | +0 | 55.00% |
| 표적·사격장 | 39 | 29 | +0 | 74.36% |
| 이펙트·효과음 | 140 | 36 | +4 | 25.71% |

## 2. 원본과 자료 위치

Splatoon 3 v0의 기존 main/SDK 이미지, PhiveConfig BYML, 로비 bphsh, static.vfxb를 읽었다. original은 읽기 전용이다. SHARED/FUNCS·디컴파일 색인을 먼저 확인했다. 6차 공통 탄 필터 호출 사슬은 기존 근거로 재사용했다.

기준 목록은 `analysis/completion/r7/inventory_before.json`, 신규 근거는 같은 폴더의 `*_updates.json`, 전후 상태는 `merge_audit.json`이다. 안정 ID의 L번호는 최초 수집 위치이며 현재 본문은 절 번호로 찾는다. 전체 목록은 [analysis_completion.md](analysis_completion.md).

## 3. 진입점과 호출 흐름

- 이동: 2442354 후반→2450510 rate, 244a260→244ab70/244b030/244b190 보조 요청, 2447bfc 전이 게이트. [player_state §6.3.1~3](player/player_state.md).
- 카메라: 24dd4d8 전진 계수·24dde2c 붐 산술, 1017434→원본 LookAt→3589d74 논리 투영. [player_camera §6.7/6.8.1](camera/player_camera.md).
- 충돌: 3b16ad8/3b1ae90 표 변환, 3a715b4 shape userData 부착. [물리 보완](physics/collision_runtime_completion.md).
- 효과: 080e4cc SRT, 081e3e4 점 방출, 081c0b8 GPU_TIME 갱신. [effect_resources §2.2.3/2.2.5](effect_sound/effect_resources.md).

주소는 main의 0x710 접두부를 생략했다. 전체 주소·writer/reader는 각 본문과 JSON에 보존했다.

## 4. 구조체·상수 신규 확정

- [실행]+[판독] SM+e4 기본값 1.25, SM+e0 이동 블렌드와 AS 슬롯 rate는 별도. 앞/뒤와 옆 방향은 다른 재생 속도 상수를 쓴다.
- [실행]+[판독] bVar9 = B+7a0!=0 및 C+13c<비트0x3f24360c. 전진 계수 중간 상한 2.5, 감소 rate lower 상한 0.35. FOV는 수직 전체각.
- [실행]+[데이터] PhiveConfig 값1/2는 허용 표, 값2만 막음 표로 변환. 원본 bphsh 행의 userData 부착 위치·개수와 설명자 mask writer 확인.
- [실행]+[판독] 효과 CF8 지정 방향 배율, D60 기본 탄생 크기, E+50 이번 dt, E+4c 누적 나이.

- [실행]+[판독] 사격 입력 B+4d0 로컬 writer와 연속 카운터, ab4/abc 등 포화 감소를 확인했다. [shooter_bullet §3.5.1](weapon/shooter_bullet.md).
- [실행]+[판독] ColPaint 패널→시각 정점 UV/switch/tangent 포장 구간을 확인했다. [colpaint_atlas](paint/colpaint_atlas.md). 전체 지형 매칭·GPU 출력은 남았다.
- [실행]+[판독]+[데이터] 색 보정 Hermit2D는 (X,Y,구간 정규 접선)이며 접선에 X폭을 곱하지 않는다. [stage_rendering §2.2.1](graphics/stage_rendering.md). 전체 LUT/GPU 처리는 남았다.

## 5. 상태 전이와 수명

걷기 가속→유지→감속→재시작을 1440스텝 연속 대조했다. 보조 WaitShoot/NG/WalkHold와 벽 상태 E2/E3 예외를 구분했다. Jump_St 문턱은 애니메이션 프레임·rate 식이며 고정 게임 6프레임이 아니다. 효과는 초기 SRT 난수, 탄생 크기, dt 저장·누적을 분리했다.

## 6. 계산식과 정정

상태별 f32 식·게이트·붐 pre/limited 순서·효과 난수 소비를 본문에 전사했다. 원본의 별도 곱셈/덧셈 또는 FMA를 보존했고 임의 clamp를 넣지 않았다.

2026-10-03 정정: 카메라 디컴파일에 빠진 fmin 상한을 명령으로 보완했다. 효과 0826cb0는 일반 CPU 적분기가 아닌 흔들림 변위 소비자다. 물리 3c39158은 일반 질의 경로이며 탄 경로로 취급하지 않는다. 기존 기록은 날짜·이유와 함께 보존했다.

## 7. 화면과 에셋 연결

[애니메이션 블랙보드](graphics/anim_state_machine.md)에 슈터 MoveSpeedRt 잔여 분기를 연결했다. 논리 투영은 확인했지만 최종 device posture·활성 포저 연결은 남았다. 로비 KeepOut 태그1·2·25·33은 탄 막음0, PlayerThrough 태그23은1이다. 효과 SRT는 원본 11개 표본도 대조했다.

## 8. 상호작용과 실행 한계

원본 명령에 합성 객체·질의 결과를 공급한 함수/구간 실행이다. 보조 상태의 clip 종료·잉크 충분·사격 대기, Jump의 종료/최종 적용을 스텁으로 대체했다. 물리는 TAG0 loader/leaf shapeTag 경계와 Havok TOI를 제외했다. 카메라 SDK 수학은 원본 SDK에 연결했고 투영256건은 identity pose 고정이다. 효과 GPU_TIME은 빈 이미터다. 게임 전체 동작이나 실제 GPU 전체 수명 검증으로 확대하지 않았다.

## 9. 웹 반영 필요 — 구현 변경 없음

| 구현 기록 | 필요한 변경 |
|---|---|
| [impl/render.md](impl/render.md) | 요청 게이트·우선순위 적용→상태별 slot rate/MoveSpeedRt 분리→블랙보드 공급→ASB 전진 |
| [impl/camera.md](impl/camera.md) | bVar9·이동량 항, 14ec 상한2.5, 감소 lower 상한0.35, 붐 순서, 수직FOV·f32 reciprocal 순서 |
| [impl/physics.md](impl/physics.md), [impl/assets.md](impl/assets.md), [impl/weapon.md](impl/weapon.md) | 허용/막음 두 표, 설명자 mask writer, shape userData 필터 행 연결. 탄 판정으로 플레이어 막힘을 단정하지 않음 |
| [impl/weapon.md](impl/weapon.md) | B4d0을 입력 우선순위·차단·래치를 거친 연속카운터로 보존, ab4/abc 포화 감소 |
| [impl/paint.md](impl/paint.md), [impl/assets.md](impl/assets.md), [impl/render.md](impl/render.md) | ColPaint 시각 정점 UV/switch/tangent 정수 포장과 Hermit2D 정규 접선·f32 순서 반영 |
| [impl/fx.md](impl/fx.md) | SRT RzRyRx·난수 순서, 방향 배율·탄생 크기, dt/나이 분리; 100% 초과 난수를 임의 clamp하지 않음 |

## 10. 실제 검증과 명령

| web/tools 실행 도구 | 원본 실행 결과 |
|---|---|
| r7_player_walk_emu.py | 독립5515 + 연속1440, 비트 불일치0 |
| r7_player_upper_emu.py | 선택6640 + NG6640, 불일치0 |
| r7_player_jumpgate_emu.py | 1152 요청 허용/거부 일치 |
| r7_weapon_input_emu.py | 입력1680·감소1030사례(11330필드) 불일치0 |
| r7_graphics_hermit2d_emu.py | 2127/2127(로비 RGB36 포함), 스텁없음 |
| r7_paint_display_emu.py | writer4096/4096·패널→표시버퍼1200/1200 |
| r7_camweapon_emu.py | 붐640·gate640·전진계수480·투영256, 불일치0 |
| r7_physics_table_emu.py | 87행 두 배열·u32 174값 일치 |
| r7_physics_mask_emu.py | 1024사례·5120필드 일치 |
| r7_physics_mesh_emu.py | 4 bphsh 부착24필드·68행×7=476 사례 일치 |
| r7_fx_transform_emu.py | SRT413/413(원본11 포함) |
| r7_fx_particle_emu.py | 지정방향402/402, 탄생크기402/402 |
| r7_fx_timestep_emu.py | dt/나이306/306 |

담당자가 실제 실행했다. 조정자는 결과 JSON·원본 실행 코드·문서·경계를 검수했으며 통과한 담당 도구를 모두 중복 재실행하지 않았다. PY는 `.venv/Scripts/python.exe`, SH는 `C:/Program Files/Git/bin/sh.exe`다. 실패·수정·검증 제외 범위도 기록했다.

- [이동 명령 로그](../../analysis/completion/r7/player_commands.md)
- [카메라 명령 로그](../../analysis/completion/r7/camweapon_commands.md)
- [물리 명령 로그](../../analysis/completion/r7/physics_commands.md)
- [효과 명령 로그](../../analysis/completion/r7/fx_commands.md)
- [사격 입력 명령 로그](../../analysis/completion/r7/weapon_commands.md)
- [도색 표시 명령 로그](../../analysis/completion/r7/paint_commands.md)
- [그래픽 명령 로그](../../analysis/completion/r7/graphics_commands.md)
- [병합/검수 로그](../../analysis/completion/r7/root_commands.md)

이번 시작 기준 보호 파일592개(웹 코드/scripts/impl/package.json) 변경·추가0. 원본 쓰기, commit/push, 삭제/이동 없음. `git status --short`는 .git이 없어 실패했으므로 Git clean 여부는 주장하지 않는다.

재병합 명령: `.venv/Scripts/python.exe analysis/completion/r7/merge_and_report.py`. r7 시작 스냅샷에 r7 결과만 적용한다. 과거 r5_merge.py 재실행은 r7 결과를 덮으므로 사용하지 않는다.

최종 문서 검수: 로컬 링크3327개 확인·깨진 링크0, 새 보고/목록 표 오류0, Python 구문16파일 성공, 보고 도구 누락0. 기능 문서11개 NUL없음. 결과는 `analysis/completion/r7/validation.json`에 보존했다.

## 11. 남은 미확정과 다음 근거

| 항목 | 남은 경로·이유 |
|---|---|
| 최종 화면 좌우 | 5997898→모듈+2ac device posture writer, 활성 포저 vt+30→C+88 연결 |
| 카메라 필터·상태 | W+d0 writer·world vt+3f8 호출, B+7a0/B+ad0 생산자 의미; 자이로 G writer는 신규 미착수 |
| 충돌 전체 | Havok 실제 leaf shapeTag 코덱·TOI, 표적 최종 numeric mask 연결 |
| 바닥 도색 전체 | 실제 모델→패널 매칭·삼각형 경계 후처리·GPU 출력, 검증한 정점 구간만으로 전체 완료 아님 |
| 렌더링 전체 | Hermit2D 이후 전체 LUT·다른 색보정 연산·GPU 적용, 캐릭터/환경/광원 잔여 연결 |
| 효과 전체 | 부모 합성·월드 방향·확산각·상속·전체 field 파형·상위dt·나머지 형상 |
| 애니 전체 | 전체 물리 프레임→ASB 재생 연결 실행, 남은 블랙보드 질문 |
| 이번 미착수 | 피격·표적·HUD·나머지 도색/그래픽/효과음은 5·6차 상태 유지 |

후속 조사 경로가 있는 항목은 확정 불가로 단정하지 않고 미확정/조사중으로 유지했다. 임의 값으로 채우지 않았다. 전체 100% 완료가 아니다.
