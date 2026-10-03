# ASB InitialFrame 방식 3 — 난수 시작 프레임

## 1. 기능 개요와 화면 동작

사람 ASB의 Shop_Wait 잎에 붙는 종류 19 노드 263은 방식 3을 쓴다. 진입 때 시작 프레임을 구간 안에서 난수로 고른다 [실행]+[판독]. 다른 InitialFrame 방식 및 최종 포즈 합성은 이 문서의 확정 범위 밖이다.

## 2. 원본·자료 위치

Splatoon 3 v0, `extracted/exefs/main.reloc.img`. 함수 0x71039c9fcc는 `analysis/decomp/render/r4_asnode2.c`에 이미 있었으므로 새 디컴파일을 하지 않았다. 원본 반환 레지스터 s0를 직접 읽었다. ASB 데이터는 `analysis/assets_work/asb/SplPlayer.json`의 노드 263이다.

## 3. 진입점과 호출 흐름 [판독]

애니 잎 진입 0x71039bc994 → 부착된 종류 19 → 0x71039c9fcc. 입력 s0/s1/s2는 시작/끝/기준 길이이고, 일반 잎 초기화 호출에서는 0/FrameCount/FrameCount다. 함수 x0는 InitialFrame 객체, x1는 문맥, x4는 애니 엔트리다. 객체+0x18이 노드 본문 포인터다.

## 4. 구조체·상수·writer와 reader [판독]

| 기준 객체 | 필드 | reader/동작 |
|---|---|---|
| 노드 본문 | +0 u32 | 39c9fcc 방식 번호 |
| 본문 | +0x1C 태그, +0x20 bool 값 | 39982bc 값 슬롯. 슬롯+0xCC bit3이 없고 true이면 방식 3 강제 |
| 본문 | +0x24 태그, +0x28 bool 값 | 39982bc. true이면 문맥의 기존 난수, false이면 전역 난수 전진 |
| 문맥 | +8 | AS 슬롯 포인터 |
| 문맥 | +0x28 u32 | 39bf1b8이 기록하는 기존 난수, 고정 경로 reader 39c9fcc |
| 애니 엔트리 | +0 u32 | 39c9fcc가 bit7(0x80)을 OR |
| 전역 0x7105997950 | Random 포인터 | false 경로에서 xorshift128 네 단어를 전진 |

## 5. 초기화·유지·종료

방식 3은 진입 때 엔트리 bit7을 세우고 프레임을 반환한다. 고정 경로는 문맥 난수를 소비하며 전역 Random 상태를 바꾸지 않는다. 비고정 경로는 전역 네 단어를 한 번 전진한다 [실행]. Shop_Wait 노드 263의 두 bool 상수는 모두 false다 [데이터]. 따라서 그 데이터로는 비고정 경로다. 이후 프레임 전진은 기존 [anim_state_machine.md](anim_state_machine.md) §4.1을 따른다.

## 6. 원본 계산식 [실행]+[판독]

```text
if fixed: word = context.random
else:
    t = x ^ (x << 11)                   # u32
    word = t ^ (t >> 8) ^ w ^ (w >> 19)
    (x,y,z,w) = (y,z,w,word)
u = f32(bitcastFloat(0x3F800000 | (word >> 9)) - 1)
frame = f32(start + f32(f32(end - start) * u))
entry.flags |= 0x80
```

u는 상위 23비트로 만드는 [0,1) 값이다. 끝보다 시작이 큰 입력도 따로 정렬하지 않는다 [실행]. 분리된 fsub/fmul/fadd이며 이 경로에는 FMA가 없다 [판독]. 호출 잎 39bc994는 반환값을 `frinta(f32(frame*10000))/10000`으로 소수 네 자리에서 반올림하고 현재 프레임(+4)에 넣는다. 직전(+8)은 같은 방식으로 반올림된 현재 frame−1을 반올림한다 [판독].

## 7. 애니메이션·에셋 연결

사람 노드 262/287/288(Shop_Wait_Rllr/Nrml/Strn)에 InitialFrame 263이 부착된다 [데이터]. 이벤트 부착은 [asb_event_runtime.md](asb_event_runtime.md)를 참조한다. 방식 3 자체는 효과·소리 action을 호출하지 않는다.

## 8. 다른 기능과 상호작용

문맥의 기존 난수와 전역 난수는 서로 다른 경로다. 고정 여부를 무시하고 항상 새 난수를 만들면 다른 노드의 난수 순서도 달라진다. 시작 프레임 이후 이벤트는 직전·현재 구간으로 조회된다.

## 9. 웹 포팅 명세

권장 함수 `initialFrame3(start,end,context,globalRandom)`에 위 bool 선택과 f32 순서를 보존한다. 원본 문맥+0x28과 전역 Random을 구분한다. 전체 ASB 파서는 값 슬롯의 태그가 상수 주소의 4바이트 앞에 있다는 기존 규칙을 따른다. 웹 코드는 변경하지 않았다.

## 10. 원본 실행 검증

`web/tools/r8_gfx_initial3_emu.py` → `analysis/completion/r8/graphics_initial3_emu.json`: 원본 39c9fcc 전체 및 bool getter 39982bc 실행, **1536/1536** 반환 f32 비트·네 난수 단어·엔트리 플래그 일치. 유한 임의 시작/끝, 역전 구간, 고정/비고정 경로를 검사했다. 함수 스텁은 없다. 전체 ASB/GPU 포즈와 방식 1/2/4/5/6/7을 실행 검증한 것은 아니다.

## 11. 정정·미확정·다음 근거

2026-10-03 r8 정정: 종전 '방식 3 무작위 시작 [추정]'을 원본 실행·명령으로 확정했다. 기존 C는 char* 반환형으로 잘못 복원되어 FP 결과 계산을 누락했다. 판독은 s0 반환 명령과 독립 f32 식으로 보완했다. 최초 하네스는 bool 태그/값 위치가 4바이트 어긋나 assert 실패했고, 39982bc의 `ldur [value-4]`를 확인해 수정한 뒤 전수 일치했다. FloatBlend 동기화·Sequence·전체 포즈 합성은 별도 [미확정]이며 39c890c/39ce888/39cd350이 다음 근거다.

2026-10-03 r8 추가 정정: 초판의 호출자 `fcvtzs`/절삭 설명은 디컴파일 `(int)` 표기를 따른 오류였다. 실제 39bcacc/39bcae0은 `frinta`(최근접, 정확한 반은 0에서 멀어지는 방향)다. 방식3 함수 반환값 1536건 검증은 이 호출자 반올림 이전 값이므로 검증 결과는 그대로 유효하다.
