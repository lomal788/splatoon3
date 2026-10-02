# 사격장 이펙트·사운드 검증 기록

작성: 2026-10-03. 갱신: 2026-10-03(5차).

이 문서는 **검증 기록만** 둡니다. 확정한 식과 규칙은 5차에 본문 문서의 해당 절로 옮겼습니다. 옮긴 내용은 지우지 않았고 §6 표의 위치에 그대로 있습니다. 절 구성은 [../../분석.txt](../../분석.txt) 11절 형식을 따르되, 1~9절은 본문으로 연결만 합니다. 웹 코드는 수정하지 않았습니다.

## 1. 기능 개요와 사용자에게 보이는 동작

사격장 1인 연습에서 들리는 발사·착탄·피격 소리와 보이는 탄·스플래시 이펙트입니다. 개요는 [effect_sound.md](effect_sound.md) §1에 있습니다.

## 2. 분석 대상 원본·버전·자료 위치

v0 `extracted/exefs/main.reloc.img`. 디컴파일은 `analysis/decomp/vfx/`, `analysis/decomp/fx/`, `analysis/decomp/r5_fx/`(5차), 셰이더 역번역은 `analysis/vfx/shader/p1383·p1886·p1897·p1940·p1747.*`, 이미터 데이터는 `analysis/vfx/emitters_v46_fields.json`입니다.

## 3. 진입점과 전체 호출 흐름

[effect_sound.md](effect_sound.md) §3, [sound_resources.md](sound_resources.md) §4.1(리스너)·§4.2(감쇠)·§4.3(그룹 제한기), [effect_resources.md](effect_resources.md) §2.2(이미터)·§3(탄 파티클)을 봅니다.

## 4. 구조체·필드·상수 표

ResEmitter D3C~D3F·D40~D5C·680/700/780/800, VAT 텍셀, 보이스 +8/C4/CC/210 표는 [effect_resources.md](effect_resources.md) §2.2.3·§2.2.5.1·§2.1.1과 [sound_resources.md](sound_resources.md) §4.3.1로 옮겼습니다.

## 5. 상태 전이와 전체 수명

FIXED 패치 시점(리소스 설정 중)은 [effect_resources.md](effect_resources.md) §2.2.5.1, 제한기 억제·재개(레벨 비트, 핸들 상태 3→4)는 [sound_resources.md](sound_resources.md) §4.3.2에 있습니다.

## 6. 계산식·조건·상세 의사코드 (옮긴 위치)

| 이전 위치 | 내용 | 지금 위치 |
|---|---|---|
| §6.1 | FIXED color0/1·alpha0/1 정적 블록 패치(`0x71008190fc`) | [effect_resources.md](effect_resources.md) §2.2.5.1 |
| §6.2 | 탄 ball VAT 시간 clamp·A 채널 compact normal 복호화(프로그램 1383) | [effect_resources.md](effect_resources.md) §2.1.1 |
| §6.3 | 프로그램 1940/1897/1383 색·알파 조합 | [effect_resources.md](effect_resources.md) §2.2.5.1 (5차에 1886/1747 추가) |
| §6.4 | Alto 제한기 비교 키·guard | [sound_resources.md](sound_resources.md) §4.3.1 (5차에 정렬 뒤 생존 §4.3.2 추가) |
| (5차 신규) | 리스너 위치·지향성 거리 배율 | [sound_resources.md](sound_resources.md) §4.1.2·§4.1.3 |
| (5차 신규) | 형상 함수 점프표·0번·1번 식 | [effect_resources.md](effect_resources.md) §2.2.4.1 |
| (5차 신규) | S1/S2 기준 플레이어, AggregateNum·지연 목록, 컬링 n | [effect_sound.md](effect_sound.md) §3.2·§3.5 |

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

표본 11이미터가 모두 volumeType 0이라는 기록([데이터])과 슬롯별 탄 클래스는 [effect_resources.md](effect_resources.md) §2.2.4.1·§3으로 옮겼습니다. 애니 → xlink 액션 이름 규칙은 [xlink_format.md](xlink_format.md) §4.4입니다.

## 8. 다른 기능과의 상호작용

고정 키 덮어쓰기를 적용한 값이 셰이더에 들어가야 합니다. VAT A를 투명도로 쓰면 법선과 조명이 달라집니다. 일반 sound priority 정렬과 음원 거리 우선순위(AUDC)는 필드 이름이 비슷하다는 것만으로 같다고 보지 않습니다.

## 9. 웹 포팅 구조와 구현 순서

웹 반영 필요 목록은 SHARED.md `>> [r5 fx→impl/fx]` 줄과 `analysis/completion/r5/fx.json`의 `web` 칸에 있습니다. GPU sin/log2/exp2 비트 일치는 검증하지 않았으므로 셰이더 [판독]을 원본 GPU 실행 완료로 표기하지 않습니다.

## 10. 검증 코드·실행 결과·기대값

### 10.1 원본 실행(unicorn)

| 실행 | 명령 | 대상 함수 | 건수·결과 | 스텁·미실행 범위 | 결과 파일 |
|---|---|---|---|---|---|
| 제한기 비교 3함수(1차) | `PY web/tools/completion_limiter_compare_emu.py` | `0x7103848c88`, `0x7103848e34`, `0x7103849000` | 각 768건, 합계 **2,304/2,304 정수 비트 일치**, null 6건 일치. guard 8조합·비트 선택 0..4·상태 6/7·순서 0/7fffffff/80000000/ffffffff 포함 | 스텁 없음. factor는 보이스 +0x210 → +0x18에서 공급. +0x180 vt+0x38 분기·정렬·정지 호출자·런타임 필드 writer는 실행 안 함 | `analysis/completion/fx_limiter_compare_emu.json` |
| 리스너 TargetOffset(5차) | `PY web/tools/r5_fx_listener_emu.py` | `0x710390d0cc`(컨트롤러 vt+0x40), `0x710383b534`(리스너 갱신), `0x7100fa6fd4`(역행렬) | vt+0x40 출력 **512/512 비트 일치**(외부 타깃 포인터 경로 포함). 리스너·카메라 월드 위치 512/512 허용오차 일치(최대 4.1e−5) | 스텁 없음. 카메라·타깃 공급(vt+0x38 `0x710390cfc4`의 isKindOf·호출자)은 실행 안 함. 역행렬 경로는 비트 비교 대상 아님 | `analysis/completion/r5/fx_listener_emu.json` |
| 리스너 지향성 거리 배율(5차) | `PY web/tools/r5_fx_listener_dir_emu.py` | `0x710384922c`, `0x71038612b0` | **2,048/2,048 비트 일치**(대전 값·무작위 값; 안쪽 988·바깥 197·중간 863) | `atan2f` PLT `0x7103e9c1e0`를 파이썬 f32 atan2로 대체. 지향 행렬 공급(`0x7103147020`)·호출 조건(`0x7103863ab4`)은 판독만 | `analysis/completion/r5/fx_listener_dir_emu.json` |
| 제한기 적용(정렬 뒤 생존, 5차) | `PY web/tools/r5_fx_limiter_core_emu.py` | `0x71038473e8` + 종류 1 정렬 `0x7103847950` + 비교 `0x7103848c88` + 억제 `0x710383cffc`/`0x710383d940` | **600/600경우** 정렬 순서·비트·핸들 상태·호출 순서 일치(생존 1,593, 정지 795, 일시정지 247, 플래그 건너뜀 279) | `nn::os::Lock/UnlockMutex` PLT no-op, `0x71037dfde4`·`0x71037e019c`·`0x710383da0c`·`0x71037dca78`·`0x7103862298` 호출 기록만. 종류 2~4 정렬·타이머(+0xE) 분기 실행 안 함 | `analysis/completion/r5/fx_limiter_core_emu.json` |

재구현은 각 하네스 안에 원본과 독립으로 짠 식이며, 원본 함수 출력과 비교했습니다. 함수 단독 실행이므로 게임 전체 프레임 순서·호출 시점은 검증 범위가 아닙니다.

### 10.2 데이터 대조·판독

- `PY web/tools/completion_vat_normal_check.py`: 실제 bulletshtr_vsp 83×6의 A half **498/498 비트 복원** [데이터 대조/재구현]. 방향 길이² 오차 최대 4.0762e−5. 원본 GPU 실행이 아니며 sin/cos/log2/exp2/FMA 비트 일치를 주장하지 않습니다. 결과 `analysis/completion/fx_vat_normal_check.json`.
- 원본 `0x71008190fc` FIXED 패치는 디컴파일과 디스어셈블의 분기·store를 판독했습니다. 전체 리소스 초기화 함수는 실행하지 않았습니다.
- 5차 판독(실행 아님): S1/S2 기준 플레이어(`0x71016d9c60`), AggregateNum·지연 목록(`0x71027b7938`, `0x71027b84e0`), 컬링 n(`0x7101645590`/`0x7101645f84`), 분열 탄 슬롯(`0x71017ffc60`), 형상 함수 0·1번, 프로그램 1886/1747 색·알파, 패닝 입력(`0x71038644fc`), xlink compare 분기 재확인(`0x7103897bf8`~`0x7103897d74`). 근거는 본문 각 절.
- 명령·실패 기록: `analysis/completion/graphics_fx_commands.md`(1차). 5차 탐색 스크립트는 `analysis/r5_fx/`(scan_off.py, scan_seq.py, scan_listener.py), 결과 파일 생성은 `analysis/r5_fx/make_fx_json.py`.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 시도·남은 이유 | 다음에 볼 곳 | 본문 |
|---|---|---|---|
| DistCoef → 확장+4 | 인라인 getter·팝카운트 마스크·문자열 xref 전수 스캔 모두 실패 → [미확정] | SLink 에셋 실행 0x7103888030~0x71038888f4 나머지, 확장 기본값 표 0x7105911d18 사용처 | sound_resources §4.2.6 |
| 리스너 주시점 공급원 | 컨트롤러 vt+0x38 호출자 미발견(BL·간접 호출 패턴 전수) | 0x7103147020 주변, 0x7103909570 호출자 | sound_resources §4.1.2 |
| 필터 컷오프·패닝 이득·FarFx 버스 | 감쇠 슬롯 8/9는 읽었으나 출력 +0x10·스피커 배분 소비자 없음 | aal 보이스 적용, SpeakerBalanceUnifier, InteriorParam 소비자 | sound_resources §4.4·§4.5 |
| 보이스 +8 writer | 카운터·프레임 수 패턴 스캔 실패 | 그룹 대기 목록(+0x1C0)에 넣는 재생 시작 경로 | sound_resources §4.3.2 |
| 팀색 dynamic writer | 셰이더 dynamic color reader만 판독 | ELink ForceTeam, OneEmitter 팀 슬롯 → NnVfx2EmitterDynamicParam[0]/[1] 기록 | effect_resources §2.2.5.1 |
| 형상 2~15번 식, POLYGON_XZ 쿼드 | 함수 주소·필드만 확인, 셰이더는 축 교환 없음 | 0x710081fcac~0x7100821f34, nn::vfx 쿼드 버퍼 생성 | effect_resources §2.2.4.1·§2.2.3 |
| Combiner/Render/TexAnim 전체 바이트 | 5개 프로그램 소비식과 FIXED 로더만 해소 | 0x71008190fc 나머지 분기, 프로그램 키 생성자, 1885/1202 | effect_resources §2.2.5.1 |

위 표의 항목은 조사 중인 [미확정]입니다. 미조사·스텁·런타임 writer 미발견을 확정 불가로 세지 않습니다(DistCoef도 탐색 실패라 [미확정]으로 둡니다. 정정(2026-10-03): 이전에는 확정 불가로 셌으나, 원본에 정보가 없다는 증명이 아니라 다음에 볼 주소가 남은 탐색 실패이므로 미확정으로 바꿨습니다).
