# 액션 변경·종료·상시 트리거 — r8 (2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행] 연사·피격 연출은 같은 액션의 프레임만 바꾸는 경우와 액션 이름을 바꾸는 경우를 구분한다. flag bit3 종료 트리거는 **매 프레임 calc가 아니라 새 액션으로 교체하는 함수의 이전 액션 정리 루프**에서 방출한다. 상시 트리거는 실제 유저 재활성화 요청과 loop 에셋·살아 있는 핸들 조건을 사용한다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0, `extracted/exefs/main.reloc.img`. 기존 `analysis/decomp/vfx/snd_xlink_b1.c`, `vfx_b1.c`, `render/r4_vis1.c`와 `r5_range/xlink_action.c`는 재사용. 신규 `analysis/decomp/r8_fx/always_trigger.c`의 실제 함수는 **0x710389c130(428B)**다. 세 실행 결과는 `analysis/completion/r8/xlink_action_calc_emu.json`, `xlink_change_emu.json`, `xlink_always_emu.json`이다.

## 3. 진입점과 전체 호출 흐름

[판독] 애니→XLink `1346470`은 재생 인덱스 변경 때 이름/프레임을 `389b61c`에 넘기고 같으면 슬롯 프레임만 갱신한다(기존 r5 근거). `38964b8`은 액션 CRC가 같으면 재시작하지 않는다. 다르면 `3896874`가 신규 액션 트리거 초기화→시작 방출/이전 핸들 이전→이전 액션 종료·정리→현재 프레임/액션 기록을 수행한다. 다음 `3895f64`는 프레임 구간과 역행을 처리한다. 상시 컨트롤러는 `389c130`; 실제 force-byte writer는 유저 요청 함수 `389d410`이다. 주소의 접두사는 `0x710`이다.

## 4. 구조체·필드·상수·열거형 표

[판독]+[실행] 액션 state stride 0x28: +10 이벤트 핸들, +18 세대, +24 발생함, +25 이전 완료, +26 직전 이름 조건 일치. trigger stride 0x28: +8 CallTable, +10 start 또는 직전 이름 문자열, +18 end, +1c u16 flag, +20 property overwrite. 분류 우선순위는 **bit2 시작 > bit3 종료 > bit4 직전 이름 > 일반 구간**이다. bit0은 같은 CallTable의 이미 발생한 이벤트를 넘겨받으며, bit1은 이 액션 분류에서 읽지 않는다. 액션 ctrl+24 현재 프레임, +28 직전 프레임, +30 현재 액션, +38 관찰 필요 값이다.

상시 trigger는 stride 0x18, +8 CallTable/+10 overwrite. resource+60 표, resource8+28 signed count, resource+B0 유효. Always ctrl+18은 재활성화 강제 평가 바이트다. state의 핸들+20과 state+18 세대가 일치해야 살아 있다고 본다.

## 5. 상태 전이와 전체 수명

[판독]+[실행] 신규 액션은 state+24/+25/+26을 지운다. 일반 비 loop 에셋은 `start == startFrame`일 때 시작 방출한다. loop 에셋은 `start <= startFrame < end`이면 시작 방출한다. bit4는 원본 CRC32 명령으로 직전 액션 이름을 비교한다. 같은 에셋을 넘겨받을 때 이전 state+24가 참이면 이전 +25와 새 +24를 켜며 새 방출을 하지 않는다. 살아 있는 세대가 맞으면 핸들을 옮기고 원래 핸들·세대를 0으로 만든다. property overwrite의 실제 재바인딩은 별도 함수다.

이전 액션 중 +25가 꺼진 트리거는 유효 핸들의 flag+8에 0x90을 OR하고 핸들·세대를 지운다. 그 뒤 `(flag & 0x0c) == 8`이며 `bit0=0 또는 발생함=0`이면 **이전 액션의 종료 트리거**를 방출하고 발생함=1로 둔다. bit2/3 동시 설정은 종료 종류로 보지 않는다. 함수 끝의 ctrl+24/+28은 둘 다 새 시작 프레임, +30은 새 액션이다.

매 프레임 `3895f64`의 새 전수 조합 대조는 low flag 0..31·에셋 loop·발생/생존/직전이름 상태·property resource·구간 경계를 포함한다. 프레임 역행은 prev=−1, bit0=0의 발생한 살아 있는 이벤트를 취소하며 일반 트리거를 다시 평가한다. 기존 r6의 DamageShot 28건은 다시 실행하거나 신규로 세지 않았다.

## 6. 계산식·순서·경계조건

[판독]+[실행] 상시 calc: 유효 resource가 없으면 즉시 return하여 ctrl+18을 보존한다. 유효 resource이고 count>0이면 순회한다. ctrl+18=1은 모든 상시 트리거를 고려한다. 0이면 accessor의 UserParam이 존재하고 해당 에셋 bit1(loop)이 켜져야 고려한다. 고려된 트리거의 핸들이 없거나 세대가 다를 때 `3899c68(ctrl,2,index,overwrite,CallTable)`을 호출한다. 유효 resource 처리 끝에는 count=0이어도 ctrl+18을 0으로 만든다.

[판독]+[실행] 실제 유저 `389d410(user,request)`는 `(request XOR ((user+f8 & 2)>>1)) & 1`이 0일 때만 상태 변경한다. request=1 경로는 선택된 resource+60의 Always ctrl+18=1과 user+f8 bit1=0을 기록한다. request=0은 `389d258` 정리 호출 후 user+f8 bit1=1로 기록한다. 따라서 user+f8 bit1을 일반적인 '현재 활성=1'로 읽으면 반대가 된다.

## 7. 원본 데이터와 실행 입력

실행 입력은 함수가 실제 읽는 필드만 합성했다. 원본 코드·원본 이미지 table을 실행한다. 이름 CRC 테스트는 빈 문자열의 CRC=0과 비일치1, start=3/end=8의 앞/안/끝, 0/1/3개 상시 트리거, 소유자 index 0/1/범위 밖, 살아 있는 핸들/낡은 세대/없는 핸들을 사용했다. 전체 인게임 부팅·백엔드 파형 재생 대조로 확대하지 않는다.

## 8. 웹 반영 필요

`impl/fx.md`, `impl/assets.md`: bit 우선순위·액션 종료 루프·동일 CallTable 이전·세대 비교·동일 액션 frame 역행을 적용해야 한다. 유저 inactive bit와 Always force를 구분하고 상시 트리거의 강제/loop 평가를 연결해야 한다. 해당 impl과 웹 코드는 수정하지 않았다.

## 9. 확정 수준과 범위

[실행] 원본 calc 9,216건, 원본 action change 40,960건, 원본 Always calc 768건, 실제 force writer 16건 모두 기대 기록/상태와 일치. [판독] 종료 방출 위치·순서·frame writer는 기존 원문과 새 전체 분기를 연결했다. **이벤트 재바인딩 내부, property overwrite 문자열 적용 내부, NVN/오디오 백엔드 실제 수명·mix/fade는 별도 미확정**이다. 합성 입력에서 이벤트+28=0을 사용하여 백엔드 cleanup을 실행하지 않았다.

## 10. 실제 명령·결과·실패

SHARED/FUNCS 검색, `decomp_index.py --no-build 389c130/3896874`, `func_lookup.py 389c130/389d410`, 기존 decomp 판독. `full_decomp.sh analysis/decomp/r8_fx/always_trigger.c 0x710389c130 0x710389c218`은 성공했지만 **389c218은 함수 중간 주소였다. 해당 가짜 분리 결과는 근거로 쓰지 않는다**. `r8_xlink_action_calc_emu.py` 9216/0, `r8_xlink_change_emu.py` 40960/0, `r8_xlink_always_emu.py` 768+16/0. prefix 재사용 첫 시도 `__file__` 누락은 수정했다. 스텁은 emit(인자 기록), accessor(합성 UserParam), 재바인딩(호출 기록), 비활성 cleanup(호출 기록)이며 원본 내부 계산을 대체하지 않았다.

## 11. 미확정과 다음에 볼 곳

이 문서의 트리거 flag·발생 규칙은 확정했다. 실제 재바인딩 `3890444`, 이름 property `accessor vt+20/+28`, event+28 백엔드 정리, 실제 파형/입자 종료 시각은 독립 질문으로 남는다. 상시 ctrl 생성·배포 전체를 이번 실행이 검증했다고 주장하지 않는다.
