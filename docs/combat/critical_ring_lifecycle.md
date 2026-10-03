# 크리티컬 누적 링 생성·리셋 (v0)

## 1. 기능 개요와 사용자에게 보이는 동작

같은 샷이 같은 대상에 여러 번 닿았는지를 플레이어별8칸에 기록한다. 기존 누적식 `16e6260`과3,000회 실행은 재사용한다. 이번 신규 근거는 링을 처음 비우는 시점과 재시작 때 비우는 방식이다 [판독]+[실행]. 고정 inventory `combat/damage_hit.md:L283`의 초기화 질문을 해소한다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 `extracted/exefs/main.reloc.img`. 신규 `analysis/decomp/r8_combat/critical_manager_ctor.c`, `critical_reset.c`, `critical_reset_signal.c`; 기존 `combat/batch1.c`, `paintgpu/pg1.c` 재사용. 실행 도구 `web/tools/r8_combat_critical_lifecycle_emu.py`, 결과 `analysis/completion/r8/combat_critical_lifecycle_emu.json`.

## 3. 진입점과 전체 호출 흐름

```text
Scene 생성27cc960 → 탄 관리자 M(0xBB8) 생성 → 27ce0ac..42c 링 초기값 저장
  → M+320 멤버 thunk(VT5649a28, this=M, function16e48c8)
  → M+340 type key582ecc0
관리자 초기화16e3294 → 0f3de98(dispatcher,[M+2f8]) 구독 등록
SplProcessReset 생산2d53a3c → ResetType 값 [P+78] → 메시지 VT568c5b8
  → 1323ea8 원본 방송(type getter VT+20=2d550c4, key582ecc0)
  → subscriber+28=M+320 → 27d2150 → 16e48c8 → 80개 key=-1
```

이름 `SplProcessReset`은 원본 `2d54e84` 문자열이다. 이 이름의 프로세스가 보내는 신호라는 연결을 확정했으며, 메시지 클래스에 별도 이름을 지어 붙이지 않는다. `16e3294` 등록과 생성자 전체는 판독, 생성자 저장 구간 및 원본 등록·방송·멤버 thunk·리셋은 실행했다.

## 4. 구조체·필드·상수·열거형 표

| 객체/필드 | 원본 값·의미 | 근거 |
|---|---|---|
| M VT | 55a1028 | 27cde5c..68; 기존 싱글턴 등록16e7708 재사용 |
| M+3C0..8BF | 10명×8칸×16B | 기존16e6260, 신규 생성 저장 |
| 칸+0 Q64 | 대상 포인터; 생성0 | 27ce0ac..42c |
| 칸+8 S32 | 샷 키; 생성·리셋−1 | 같은 생성 구간,16e48c8 |
| 칸+C S32 | 데미지; 생성0, 리셋 시 보존 | 같은 저장 및 리셋 구간 |
| M+3B8 Q64 | 리셋에서0 | 16e4adc |
| M+320/+328/+330/+338 | 멤버 thunk VT/this/함수/조정값0 | 27cdff8..27ce044 |
| M+340 | 구독 타입 키582ECC0 | 같은 생성 구간 |
| dispatcher global5801908 | 타입별 방송 관리자 | 기존1323ea8, 신규16e3294 연결 |

## 5. 상태 전이와 전체 수명

관리자를 생성할 때 링 전체를 `{target=0,key=-1,damage=0}`으로 만든다. 탄 관리자 초기화에서 Reset 신호의 구독자를 등록한다. 누적 호출이 슬롯을 채운 뒤 `SplProcessReset` 생산자의 방송을 받으면 키80개만 −1로 바꾸고 M+3B8을0으로 만든다. **리셋은 링 전체 memset이 아니다** [판독]+[실행]. 이후 누적기는 키−1을 빈 칸으로 보므로 오래된 대상·데미지가 남아 있어도 새 유효 샷으로 사용하지 않는다.

## 6. 계산식·조건·상세 의사코드

```text
ctor: for each80 cells: target=0; key=-1; damage=0
ResetCallback:
  # 앞서 다른 탄 피드백 리스트 및 뒤쪽 actorref도 정리한다
  for each80 cells: key=-1
  M[3b8]=0
# 기존 누적기: key==-1 빈 칸 우선, 없으면 u32 최소 key 슬롯 교체
```

신호 생산자는 `ResetType` 값을 메시지+18에 넣는다. 원본 링 콜백은 메시지 인자를 읽지 않는다. 실행에서0/1/2/3/FFFFFFFF/80000000의 값 모두 같은 링 초기화 결과였다. ResetType의 각 이름·메뉴 입력 연결을 이 결과로 확정하지 않는다.

## 7. 원본 데이터 값과 사격장 적용

신규 수치 근거는 코드의 생성·리셋 저장값이다. 싱글턴 포인터 셀5850620(GOT5797F18)은 기존 근거다. 사격장 슈터가 공유하는 탄 관리자 구조에 적용한다. 플레이어/표적 HP 리셋, 표적 복귀 시간, 탄 삭제 전체를 이 링 검증으로 묶어 확정하지 않는다.

## 8. 재현·검증 명령과 결과

```text
PY web/tools/decomp_index.py --no-build 16e48c8 / 27cc960 / 1323ea8
PY web/tools/func_lookup.py 16e499c / 27ce038 / 2d53a60
sh web/tools/full_decomp.sh analysis/decomp/r8_combat/critical_reset.c 0x71016e48c8
sh web/tools/full_decomp.sh analysis/decomp/r8_combat/critical_manager_ctor.c 0x71027cc960 0x71016e4b54
sh web/tools/full_decomp.sh analysis/decomp/r8_combat/critical_reset_signal.c 0x7102d53a3c 0x7101323ea8 0x7100f3de98 0x7100f3e094 0x71027d2150 0x7102d55000 0x71016e3294
PY web/tools/r8_combat_critical_lifecycle_emu.py
```

`PY=.venv/Scripts/python.exe`, Windows shell은 Git `sh.exe`를 명시했다. 중복1323EA8은 도구가 기존pg1.c를 감지해 SKIP했다. 최종 생성80칸1,280B, 리셋512건40,960키, 원본 등록→실제 메시지 생산 구간→방송256건: 불일치0. 원본 코드는 패치하지 않았다. ResetType RTTI의 SDK guard 및 native 노드 mutex SDK init/LockMutex/UnlockMutex는 경계 스텁. dispatcher 상위 lock 객체만 원본 RET를 가리키는 합성 VT로 공급했다. 관리자·dispatcher 주변 메모리는 합성, 피드백 리스트는 비어 있고 actorref12개는 무효 handle이다. 전체 Scene/프로세스 실행은 아니다.

첫 실행 실패: 생성 저장 구간을27ce0ac부터 시작해 앞의 W11=−1 명령을 빠뜨렸다. 시작을27ce054로 확장해 원본 명령이 W11을 생성하도록 고친 뒤 PASS. `func_lookup.py 2d53a60`은 앞 함수2d539b4를 반환하지만 범위가 포함하지 않는다. 실제 SP−80 프롤로그2d53a3c를 판독해 사용했다. xref GOT5798650의28e9704는 실제579F650 읽기인 페이지 추적 오탐이므로 증거에서 제외했다.

## 9. 미확정·실패·다음에 볼 곳

메뉴/로비에서 어떤 입력이 `SplProcessReset` 프로세스를 시작하는지는 이번 범위의 링 초기화 질문과 분리하며 [미확정]이다. 전체 Scene ctor 실행과 유효 actorref/피드백 정리, 실제 스레드 lock은 실행하지 않았다. 링 데이터와 신호 전달의 판독·실행 근거만 확정한다. 기존 needCount>1 무기 종류 질문은 그대로 남긴다.

## 10. 웹 구현 차이와 반영 필요

`impl/combat.md`, `impl/weapon.md`: 관리자 생성 시80칸의 target0/key−1/damage0; Reset 신호 시 key만−1, target/damage 보존을 반영해야 한다. 임의 시간 경과나 매 샷/매 프레임 링 초기화를 추가할 근거는 없다. 구현 파일은 수정하지 않았다.

## 11. 확정 수준·정정 이력

2026-10-03 r8: [판독] 관리자 생성·구독 등록·SplProcessReset 생산자와 callback의 연결; [실행] 생성 저장·native RTTI·native 등록/방송/멤버 thunk/키 리셋. 기존 문서의 “링 초기화 시점 미확정”은 보존한 채 이 근거로 해소한다. 누적 식 자체는 기존 r5 실행을 재사용했으며 신규율에 중복 계산하지 않는다.
