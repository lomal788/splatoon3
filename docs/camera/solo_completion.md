# 시험 사격장 카메라·조준 — 검증 기록

## 1. 기능 개요와 이 문서의 역할

작성 2026-10-03, 갱신 2026-10-03([r5 camweapon]). 이 문서는 **검증 기록만** 둡니다. 확정한 내용은 본문으로 옮겼습니다.

| 옮긴 내용 | 본문 위치 |
|---|---|
| 생성 경로(팩토리 0x71024d5c6c → 구 형상), +0x60/+0x68 포인터 | [player_camera.md](player_camera.md) §3, §4.2 |
| 카메라 기저 갱신식·소비처(이동 입력 축 N×X, 발사 축 −Z)·주소 정정 | [player_camera.md](player_camera.md) §6.7 |
| 오징어 FOV 가중치 +0x1550 정정·오징어 블록 곡선 | [player_camera.md](player_camera.md) §4.1, §6.2 |
| 붐 구 반경 식·런타임 값 0.3·필터 객체 | [player_camera.md](player_camera.md) §6.8 |
| 사람 FOV 목표 본체+0x6dc = 55 | [player_camera.md](player_camera.md) §4.2, §6.2 |
| yaw 축 스케일 s·블렌드 w, 피치 α | [player_camera.md](player_camera.md) §6.4, §6.5 |
| 슈터 조준 피치 곡선(Shooter 항목 없음 → 기본 −70/5/75도) | [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md) §5.5 |

## 2. 분석 대상·자료 위치

v0 main NSO(`extracted/exefs/main.reloc.img`, 기준 0x7100000000). 도구·결과 파일은 §10.

## 3. 진입점과 전체 호출 흐름

본문으로 옮겼습니다: [player_camera.md](player_camera.md) §3.

## 4. 구조체·필드·상수

본문으로 옮겼습니다: [player_camera.md](player_camera.md) §4.2.

## 5. 상태 전이와 수명

본문으로 옮겼습니다: [player_camera.md](player_camera.md) §5·§6.7.

## 6. 계산식·조건·의사코드

본문으로 옮겼습니다: [player_camera.md](player_camera.md) §6.2·§6.4·§6.5·§6.7·§6.8.

## 7. 애니메이션·이펙트·소리·카메라 연결

본문으로 옮겼습니다: [shake_rumble.md](shake_rumble.md) §3.2b.

## 8. 다른 기능과의 상호작용

본문으로 옮겼습니다: [player_camera.md](player_camera.md) §8.

## 9. 웹 포팅 구조

본문으로 옮겼습니다: [player_camera.md](player_camera.md) §9, 웹 반영 필요는 [../impl/camera.md](../impl/camera.md) 담당이 SHARED `[r5 camweapon→camera impl]` 줄로 확인.

## 10. 검증 코드·실행 결과

### 10.1 원본 실행

| 날짜 | 명령 | 대조 | 결과 | 스텁·검증 범위 |
|---|---|---|---|---|
| 2026-10-03 | `PY web/tools/camera_weapon_completion_emu.py` | 원본 기저 명령 구간 0x71024df4e8..0x71024df6d4 + 0x71012507e0 대 독립 f32 재구현 | **260/260 9성분 비트 일치** | 스텁 없음. 정상 256·기본 1·수직 ±2·0길이 1. NaN/Inf 제외 |
| 2026-10-03 | 같은 명령, 카메라 팩토리 | 설정 없음/.05/.3/.6 → descriptor 반경, +0x68 포인터 | **4/4 비트 일치**(.3/.3/.3/.6) | malloc 0x710083d2f0, 질의 0x7103a62e78/0x7103a72e1c, TLS 0x7103e9aa00 스텁. 구 solver·필터 미실행 |
| 2026-10-03 | 같은 명령, 생성 허용 함수 0x71016e3af4 | local·음수 speed·관리자 null 짧은 분기 | **9/9 반환 1** | 외부 호출 없음. 모드 ActorParam 예외 분기·원격 컬링 제외 |
| 2026-10-03 [r5] | `PY web/tools/r5_camweapon_boom_emu.py` | 팩토리 0x710344af54(case 0xf) → 월드 생성자 복사 구간 0x7103ac728c..0x7103ac73ec → 카메라 팩토리. 경계 12건은 독립 식 `min(fmaxnm(c,0.3),2000)` | 설정 +0xb8 = 0x3c23d70a, 월드+0x21c = 0x3c23d70a, 반경 **0x3e99999a**, 경계 **12/12 비트 일치** | malloc·memset·PLT(0 반환)·0x7103585094·질의 할당·형상 래퍼 스텁. 모듈 생성 도우미 0x7103dad17c·Phive init 0x7103db346c는 판독만 |

| 2026-10-03 [r5] | `PY web/tools/r5_camweapon_libm_emu.py` | SDK sdk.img logf/expf로 계산한 bias 식 대 웹 Math 근사 | 흔들림 29,971건 중 97건(각 94건), 스틱·피치·자이로 40,000건 중 95건 다름, 최대 14ulp | 스텁 없음([r5 player] `r5_player_libm_emu.Sdk` 재사용). main PLT ↔ SDK 심볼 연결은 이름 기준 |
| 2026-10-03 [r5] | `PY web/tools/r5_camweapon_bnvib_emu.py` | SDK ParseVibrationFile/RetrieveVibrationValue 대 독립 디코더 | 헤더 115/115, 샘플 30,240/30,240 비트 일치 | 스텁 없음(리프 함수). VibrationPlayer 재생은 판독만 |
결과 파일: `analysis/completion/camera_weapon_original.json`, `analysis/completion/r5/camweapon_boom_emu.json`, `analysis/completion/r5/camweapon_libm_emu.json`, `analysis/completion/r5/camweapon_bnvib_emu.json`. 이전 실패 기록: 처음 카메라 팩토리 실행은 `UC_ERR_WRITE_UNMAPPED`로 실패했습니다. malloc이 PLT가 아니라 `0x710083d2f0`에 있어 후킹되지 않은 것이 원인이었고, 그 할당만 스텁한 뒤 통과했습니다. 명령·실패 기록 원본은 `analysis/completion/camera_weapon_commands.md`.

정정(2026-10-03 [r5]): 이전 판 카메라 팩토리 하네스의 기대식은 `0.3 if c ≤ 0.3 else c`였습니다. 원본은 2000 상한과 NaN → 0.3(fmaxnm)이 있어, 그 하네스의 4건은 맞았지만 식은 불완전했습니다. 새 하네스의 독립 식이 이를 포함합니다.

### 10.2 판독만 한 것(실행 없음)

- yaw 축 스케일·블렌드: asm 발췌 `analysis/r5_camweapon/input_24e0178.asm`(0x71024e0178부터 3000명령).
- 사람 FOV writer: 0x7102354cd8~0x7102354ce0, 저장 스캔 `web/tools/r5_camweapon_storescan.py 0x7102300000 0x7102700000 0x6dc`.
- 붐 필터 객체: 0x71024d5ec8~0x71024d5f10, 캐스트 `analysis/decomp/r5_camweapon/boom_cast.c`.

`[실행]` 숫자는 함수·구간별 검증 건수이며 전체 사격장 동등성 비율이 아닙니다. 남은 미확정은 [player_camera.md](player_camera.md) §11에 있습니다.

## 11. 미확정 사항

남은 미확정은 [player_camera.md](player_camera.md) §11에 모읍니다. 이 문서에는 새 미확정을 두지 않습니다.
