# 시험 사격장 이동 보완 분석 — 검증 기록

작성·정정: 2026-10-03 (Asia/Seoul). Splatoon 3 v0, `Lby_Lobby00` 1인 연습. 이 문서는 이동 전체 완료 선언이 아니다.

2026-10-03 5차 정리: 이 문서에 있던 확정 내용(식·필드·조건)은 본문 문서로 옮겼다. 이 문서에는 **검증 기록**(명령, 건수, 스텁, 실패와 재실행)만 남긴다. 옮긴 곳은 §3 표에 있다. 옮기기 전 판의 결론은 본문에 "정정(2026-10-03)" 표기와 함께 그대로 보존했다.

## 1. 기능 개요와 사용자에게 보이는 동작

이 문서가 검증한 동작은 다음과 같다. 사용자에게 보이는 의미는 각 본문 절에 있다.

- 오징어 목표 속도의 특수 능력 104(징어닌자) 0.9 배율
- 이동 애니메이션 속도값 SM+0xd4(대기/걷기 판정 입력)
- 롤·벽 점프 연속 발사 횟수 n과 감쇠 반복곱
- 5차: 방향 보간 표 계산, 스틱 데드존, 벽 입력 계수 x, SDK 수학 함수 차이

## 2. 분석 대상 원본·버전·자료 위치

원본 이미지: `extracted/exefs/main.reloc.img`(base `0x7100000000`), SDK 모듈 `extracted/exefs/sdk.img`. 기존 디컴파일 `analysis/decomp/player/playerparam_gear.c`, `analysis/decomp/state/state_select.c`, `state_big.c`, `state_big_full.c`, `analysis/decomp/move/*.c`, `analysis/decomp/physplayer/lerp_dir.c`를 재사용했다. 상수 출처: `analysis/player/bss_consts_58bb000.json`(정적 초기화 에뮬), 원본 정적 초기화 `0x710265c230`, `0x7102455db0`.

명령 사본: `analysis/completion/squid_speed_k.asm`, `sm_move_speed.asm`. 실행 결과: `analysis/completion/` 아래 JSON(§10).

## 3. 진입점과 전체 호출 흐름 — 옮긴 곳

| 이전 절 | 내용 | 옮긴 곳 |
|---|---|---|
| §3, §6.1 | `0x710266c6e4` k 식 | [movement_physics.md](movement_physics.md) §6.1.1 |
| §3~§6.2, §7, §8 | `0x710246d060` SM+0xd4 식·필드·우회 조건 | [player_state.md](player_state.md) §6.1.3 |
| §6.3 | 연속 발사 횟수 n·감쇠·90프레임 리셋 | [movement_physics.md](movement_physics.md) §6.8.1 |
| §6.4 | 이동 이력 버퍼 필드·롤 소비 | [movement_physics.md](movement_physics.md) §6.4.2, §6.4.3 |
| §9 | 웹 반영 필요 | 각 본문 절, [../impl/physics.md](../impl/physics.md)는 고치지 않음 |

## 4. 구조체·필드·상수·열거형 표

본문으로 옮겼다(§3 표). 검증에 쓴 합성 상태의 필드만 §10에 적는다.

## 5. 상태 전이와 전체 수명

본문으로 옮겼다. 검증은 모두 함수·명령 구간 단독 실행이며 상태 수명 전체를 실행하지 않았다.

## 6. 계산식·조건·상세 의사코드

본문으로 옮겼다(§3 표).

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

SM+0xd4는 대기·이동 상태 선택의 속도 입력이다([player_state.md](player_state.md) §6.3). 이 함수 자체는 ASB 커맨드·xlink·카메라를 호출하지 않는다. 스칼라만 맞았다고 애니메이션 재생 속도·전환 전체가 확정된 것으로 보지 않는다.

## 8. 다른 기능과의 상호작용

본문으로 옮겼다. 실행한 함수들은 Phive 프레임과 다른 액터를 거치지 않았다.

## 9. 웹 포팅 구조와 구현 순서

웹 반영 필요 목록은 각 본문 절과 `analysis/completion/r5/player.json`의 `web` 칸에 있다. 이 문서 작업으로 웹 코드를 고치지 않았다.

## 10. 검증 코드·실행 결과·기대값

### 10.1 1차 보완(2026-10-03)

```powershell
.venv/Scripts/python.exe web/tools/decomp_index.py --no-build 0x710266c6e4 0x710246d060
.venv/Scripts/python.exe web/tools/func_lookup.py 0x710266c6e4 0x710246d060
.venv/Scripts/python.exe web/tools/solo_move_emu.py
.venv/Scripts/python.exe web/tools/solo_roll_counter_emu.py
```

| 대상 | 방법 | 결과 | 스텁·제외 |
|---|---|---|---|
| `0x710266c6e4`(340 B) k | 원본 단독 실행 vs numpy f32 재구현. bit0 인자 0/1/2/3, 특수 비트 반대 조건, 열거 순서와 첫 슬롯 fallback 포함 | **1088건 비트 일치**, 불일치 0 | 열거 표 생성·실제 장비 AP 집계는 합성 상태 |
| `0x710246d060`(1436 B) SM+0xd4 | 원본 단독 실행 vs 재구현. 난수 2000건 + 기초 4건, N/M 축·경사, 투영 허용/우회, 빠른 경로, 외부 벡터/캐시, 추가 컴포넌트 속력 | 반환값과 r(B+0x178) 갱신 **2004건 모두 비트 일치** | 실제 액터/컨트롤러 대신 메모리 구조 합성. NaN sqrtf fallback·비슈터 차지 경로 미비교 |
| 감쇠 반복곱 `0x7102459b44~0x7102459bb8` | 명령 구간 실행 | **1020건 비트 일치** | 구간 실행 |
| n·마지막 프레임 쓰기 `0x7102459eec~0x7102459f04` | 명령 구간 실행 | **1572건 정수 비트 일치** | 구간 실행 |

결과 파일: `analysis/completion/squid_speed_k.json`, `sm_move_speed.json`, `roll_counter_emu.json`.

실패와 재실행: 롤 검증 최초 실행은 S8 선행 초기값을 주지 않아 음수 n에서 0을 얻는 AssertionError로 실패했다. 원본 선행 `factor = 1`을 합성 입력에 제공한 뒤 재실행해 통과했다. 수정은 검증 하네스 입력에만 적용했다.

### 10.2 5차(2026-10-03, [r5 player])

```sh
PY=.venv/Scripts/python
$PY web/tools/r5_player_lerpdir_emu.py     # acos 0x7101252780, 방향 보간 0x7101252ff0
$PY web/tools/r5_player_input_emu.py       # 스틱 데드존 구간, 벽 입력 계수 0x71024a7100
$PY web/tools/r5_player_libm_emu.py        # SDK powf/logf/expf/cosf, b 곡선, 기어 표
$PY web/tools/r5_player_storescan.py 0x782 --lo 0x7102400000 --hi 0x7102700000   # 오프셋 store 전수 검색(보조)
```

| 대상 | 방법 | 결과 | 스텁·제외 |
|---|---|---|---|
| acos `0x7101252780` | 원본 단독 실행 vs 이미지의 아탄 표(0x7104aa6b6c)로 짠 명령 순서 재구현. 경계값 15개 + 난수 20000개 | **20015건 비트 일치** | 없음(순수 함수) |
| 방향 보간 `0x7101252ff0` | 원본 단독 실행 vs 사인·아탄 표 재구현. 임의 크기·단위 벡터, 거의 평행·거의 반대(축 있음/없음), 영벡터, t 경계 | **13707건 비트 일치**. 같은 입력의 libm acos/sin + f32 근사는 12404건 불일치(최대 절대 차 0.00366) | 없음. sqrtf PLT는 NaN 입력에서만 호출되며 미도달 |
| 스틱 기록·데드존 `0x71024a0850~0x71024a0940` | 명령 구간 실행(x28 = 합성 본체, s3/s2 = 스틱) vs 재구현 | **3009건 비트 일치**(+0x474/+0x478/+0x47c/+0x480) | 구간 앞의 스틱 공급 분기와 구간 뒤 `0x71024a7100` 호출은 이 항목에서 실행하지 않음. DZ > 1 분기는 상수 0.1에서 도달 불가 |
| 벽 입력 계수 `0x71024a7100`(696 B) | 원본 단독 실행 vs 재구현. 바닥·벽(N.y −0.3..0.64)·임의 법선, 임의 D·C, 스틱 0 포함 | **6000건(벽 4167건) 비트 일치**(+0x10, +0x14) | 없음(순수 함수) |
| SDK 수학 함수 | `sdk.img` 동적 심볼(powf 0x5a1f40, logf 0x5a1800, expf 0x59e2e8, cosf 0x59d410) 단독 실행 vs 배정밀 libm → f32 | powf 10/20007, logf 157/20007, expf 16/20004, cosf 59/5001, b 곡선 46/20000, 기어 표 1/1740 불일치(모두 최대 1ulp) | main PLT ↔ SDK 심볼 연결은 이름 기준. 함수 안에서 외부 호출 없음 |

결과 파일: `analysis/completion/r5_player_lerpdir_emu.json`, `r5_player_input_emu.json`, `r5_player_libm_emu.json`.

정적 판독 보조: `r5_player_storescan.py`는 `[Rn, #imm]` 형식 store가 오프셋을 덮는지만 본다. 기준 레지스터가 본체인지는 판독하지 않으므로 "쓰기 없음" 결론은 본체 기준·즉치 오프셋 형식에 한정된다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 시도와 남은 이유 | 다음에 볼 곳 |
|---|---|---|
| SM+0xd4 입력 벡터·캐시의 실제 로비 writer 수명 | 계산 자체는 확정. 모든 producer/프레임 수명을 연결하지 못함 | `0x7102475a54`, `0x71024abcf0`, [character_controller.md](../physics/character_controller.md) |
| 메인 계산·입력 함수 전체 실행 | 롤 gate·벽 차기·차지 분기는 판독만. 함수 전체 실행은 본체 포인터 수십 개와 컨트롤러 객체가 필요 | `0x7102475a54`, `0x710249f494` 메모리 쓰기 훅 동적 추적 |
| 이동 전체 100% | 남은 항목은 [movement_physics.md](movement_physics.md) §11, [player_state.md](player_state.md) §12 | [전체 목록](../analysis_completion.md) |
