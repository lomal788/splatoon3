# 시험 사격장 스플래시슈터 — 검증 기록

## 1. 기능 개요와 이 문서의 역할

작성 2026-10-03, 갱신 2026-10-03([r5 camweapon]). 이 문서는 **검증 기록만** 둡니다. 확정한 내용은 본문으로 옮겼습니다.

| 옮긴 내용 | 본문 위치 |
|---|---|
| 발사 흐름(슬롯 19 → 잉크액션 → 잉크·총구·탄 생성), 사격 게이트(B+0x4d4·B+0xa90·래치), 연사 타이머 초기 phase, PostDelay 소비(0x71024b28b0) | [shooter_bullet.md](shooter_bullet.md) §3.5 |
| 생성 허용 0x71016e3af4(풀 수량 검사 아님), 탄 생성 실패 = 예약 풀 고갈 | [shooter_bullet.md](shooter_bullet.md) §3.5 |
| 총구 위치 0x7102552170·Shooter 항목 없음 → 기본 피치 곡선 | [shooter_bullet.md](shooter_bullet.md) §5.5 |
| 잉크 소비·회복 정지·회복량·108발 | [shooter_bullet.md](shooter_bullet.md) §5.5 |
| 분할 인덱스(I+0x91 → 순열 → S+0x90) | [shooter_bullet.md](shooter_bullet.md) §5.3 |
| 첫 명중 age 0·보관 도색 순서 | [shooter_bullet.md](shooter_bullet.md) §3.3 |
| 꼬리 최대 길이(슬롯 108)·그리기 소비(슬롯 47) | [shooter_bullet.md](shooter_bullet.md) §3.4 |
| PreDelay 값 | [../camera/aim_swerve.md](../camera/aim_swerve.md) §6.4 |

## 2. 분석 대상·자료 위치

v0 main NSO(`extracted/exefs/main.reloc.img`, 기준 0x7100000000). 도구·결과 파일은 §10.

## 3. 진입점과 전체 호출 흐름

본문으로 옮겼습니다: [shooter_bullet.md](shooter_bullet.md) §3.2~§3.5.

## 4. 구조체·필드·상수

본문으로 옮겼습니다: [shooter_bullet.md](shooter_bullet.md) §4.

## 5. 상태 전이와 수명

본문으로 옮겼습니다: [shooter_bullet.md](shooter_bullet.md) §3.3·§3.5.

## 6. 계산식·조건·의사코드

본문으로 옮겼습니다: [shooter_bullet.md](shooter_bullet.md) §3.4·§5.3~§5.5.

## 7. 애니메이션·이펙트·소리·카메라 연결

본문으로 옮겼습니다: [shooter_bullet.md](shooter_bullet.md) §7.

## 8. 다른 기능과의 상호작용

본문으로 옮겼습니다: [shooter_bullet.md](shooter_bullet.md) §8.

## 9. 웹 포팅 구조

본문으로 옮겼습니다: [shooter_bullet.md](shooter_bullet.md) §9, 웹 반영 필요는 SHARED `[r5 camweapon→camera impl]` 줄.

## 10. 검증 코드·실행 결과

### 10.1 원본 실행

| 날짜 | 명령 | 대조 | 결과 | 스텁·검증 범위 |
|---|---|---|---|---|
| 2026-10-02 (weapon 구현) | `PY web/tools/weapon_ink_emu.py` | 원본 잉크 소비 0x7102492120·회복량·연사 타이머 0x7102551530·회복 정지 0x7102353718 대 재구현 | 소비 2012 / 회복량 500 / 연사 타이머 5101 / 정지 500건 불일치 0 | 가짜 본체·오프라인 전역, PLT 0 반환. libm·스케줄러 미검증 |
| 2026-10-02 (weapon 구현) | `PY web/tools/weapon_spawnpos_emu.py` | 총구 0x7102552170 | 17/17 비트 일치 | B+0x58 writer 미연결 |
| 2026-10-02 (weapon 구현) | `PY web/tools/weapon_splash_emu.py` | 슬롯 15·56 → 0x71017540ec 대 `weapon_splash_sim.py` | 불일치 0 | 탄 위치·형식 검사·생성 요청 스텁. 이펙트 모양 아님 |
| 2026-10-03 | `PY web/tools/camera_weapon_completion_emu.py` | 생성 허용 0x71016e3af4 짧은 분기 | 9/9 반환 1 | 외부 호출 없음. 모드 예외가 꺼진 조건만 |
| 2026-10-03 [r5] | `PY web/tools/r5_camweapon_tail_emu.py` | 슬롯 108 0x7101753c00 대 독립 식(§3.4) | **445/445 비트 일치** | 형식 검사 vt[0] → 1, `__cxa_guard_acquire` → 0, 부모 사슬 미실행. 첫 실행은 0/0(MaxLengthFrame 0, age = Delay) 1건 불일치 → asm 0x710175406c `b.ge`·0x7101754078 `b.le`의 NaN 처리(→ Start)를 독립 식에 반영 후 통과 |

결과 파일: `analysis/completion/camera_weapon_original.json`, `analysis/completion/r5/camweapon_tail_emu.json`. 명령·실패 기록 원본은 `analysis/completion/camera_weapon_commands.md`.

### 10.2 판독만 한 것(실행 없음)

- 탄 생성 실패: 0x71025817c8(batch1.c) → 0x71028678b4(disasm 0x7102867f70~0x7102867fb0) → 0x7100f7f39c(`analysis/decomp/r5_camweapon/actor_create.c`).
- 첫 명중 age: [r5 physics] 프레임 그래프 판독([../physics/phive_controller.md](../physics/phive_controller.md) §6.7) + 탄 슬롯 18/54 판독.
- 매치 시드 `+0xd0 → +0xc8` 이동 탐색(실패): `analysis/r5_camweapon/scan_swap.py`, `scan_swap2.py`, `scan_gc8d0.py`, `scan_copy.py`.

함수 테스트 통과를 실제 프레임 사격 전체 검증으로 넓히지 않습니다. 남은 미확정은 [shooter_bullet.md](shooter_bullet.md) §11에 있습니다.

## 11. 미확정 사항

남은 미확정은 [shooter_bullet.md](shooter_bullet.md) §11에 모읍니다. 이 문서에는 새 미확정을 두지 않습니다.
