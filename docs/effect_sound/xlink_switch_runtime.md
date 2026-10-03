# XLink Switch 갱신·취소 조건 — r8 (2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행] 감시 값으로 선택한 자식이 달라질 때 기존 효과·소리에 취소를 요청하고 해제한 뒤 새 자식을 시작한다. 매 프레임 무조건 선택을 다시 하는 것은 아니다. 이 문서는 기존 `xlink_format.md` §4.2의 남은 **Switch calc 조건**을 확정한다. 음성 믹서의 페이드 시간·파형은 별도 미확정이다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 `extracted/exefs/main.reloc.img`. 기존 `analysis/decomp/effect_sound/xlink_core.c`를 재사용하고, 새 취소 전달 함수는 `analysis/decomp/r8_fx/xlink_cancel.c`에 저장했다. 도구 `web/tools/r8_fx_switch_emu.py`, 결과 `analysis/completion/r8/fx_switch_emu.json`.

## 3. 진입점과 전체 호출 흐름

[판독] Switch VT `0x7105736890`: +0x20 start=`0x7103897e1c`, +0x28 calc=`0x71038976d4`, +0x30 cancel=`0x710388e748`, +0x18 release=`0x710388e6b4`. calc는 기존 selector `0x71038978bc`와 allocator `0x710388e468`를 호출한다. 자식이 바뀌면 **old.vt30 → old.vt18 → 새 생성 → new.vt20** 순서다.

## 4. 구조체·필드·상수·열거형 표

| 기준 객체 | 필드 | 타입·소비 |
|---|---|---|
| Switch C | +8 | CallTable 포인터 |
| C | +0x10 | Event E 포인터 |
| C | +0x18 | 현재 자식 포인터 |
| C | +0x28 | s32 남은 duration; calc 감소, cancel은 0 |
| E | +8 | flags: bit4이면 감시 재선택 전체 생략, bit3이면 재선택 생략 |
| Resource 각 asset-entry | +2 bit1 | 1일 때만 calc 재선택 가능 |
| 자식 | +8 | 자식 CallTable: 새 선택과 포인터 비교 |
| 자식 | +0x20 | cancel 전달 시 다음 형제 포인터 |

flags의 다른 비트와 이름은 이 실행으로 의미를 확대하지 않는다. resource 접근 실패 때도 재선택을 생략한다.

## 5. 상태 전이와 전체 수명

[실행] 재선택은 **E.flags.bit4=0 AND resource 존재 AND asset.bit1=1 AND E.flags.bit3=0**일 때 수행한다. 선택과 현재 자식 CallTable이 같으면 취소·재생성하지 않는다. 새 선택이 null이어도 기존 자식과 다르면 기존 자식을 취소·해제하고 빈 상태가 된다. 생성 실패면 빈 상태, 생성 성공·start 실패면 새 객체를 즉시 release한다.

자식 calc(vt28)의 완료 bit0가 0이면 부모는 0을 반환한다. 완료면 release하고 자식 포인터를 비운다. duration>0만 1 감소하며 0이 아니면 부모 start(vt20)로 다시 시작한다. duration 0·1은 재시작하지 않고, -1은 감소 없이 재시작한다.

## 6. 계산식·조건·상세 의사코드

```text
watch = !(E.flags & 16) && resource && (asset.flags & 2) && !(E.flags & 8)
if watch:
    next = select(C)
    if child && child.callTable != next:
        child.cancel(); child.release(); child = null
    if !child && next:
        x = create(E,next,1.0f)
        if x:
            if x.start() & 1: child=x
            else: x.release()
if child:
    if !(child.calc() & 1): return 0
    child.release(); child=null
    if duration>0: duration--
    if duration!=0 && (C.start() & 1):
        return (!watch) & child.calc()
return !watch
```

[판독]+[실행] **watch가 가능한 동안 자식이 없어도 부모 반환은 0**이다. 결과를 단순히 `child==null`로 끝 판정하면 원본과 다르다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

ELink/SLink 공통 컨테이너 코드다. 속성 감시 Switch는 값이 바뀌면 즉시 새 자식이 되는 것이 아니라 위 비트·리소스 조건과 해당 calc 실행 시점을 따른다. selector의 기존 첫 참·첫 무조건 선택 규칙은 `xlink_format.md` §4.2를 따른다. 음성 믹서와 이미터 내부 페이드 곡선은 이 문서에서 확정하지 않는다.

## 8. 다른 기능과의 상호작용

[판독]+[실행] 공통 cancel `0x710388e748(C)`는 C+0x18에서 자식 +0x20 체인을 순서대로 따라 각 vt30을 호출한 뒤 C.duration=0을 쓴다. **현재 자식 포인터를 지우지 않는다.** release는 호출자가 따로 수행한다. cancel 직후 포인터가 남아 있다고 재생 중으로 해석하면 안 된다.

## 9. 웹 포팅 구조와 구현 순서

권장 이름은 위 의사코드의 C/child/duration/watch이며 원본 심벌 이름이 아니다. 컨테이너 calc의 bit gate와 반환값, cancel→release 순서, watch 동안 자식 없는 상태를 유지할 필요가 있다. `impl/fx.md` 구현을 수정하지 않았고 `analysis_completion.md`의 웹 반영 열에만 요구를 기록한다.

## 10. 검증 코드·실행 결과·기대값

실제 명령:

```powershell
& 'C:\Program Files\Git\bin\sh.exe' web/tools/full_decomp.sh C:/dev/splatoon3/analysis/decomp/r8_fx/xlink_cancel.c 0x710388e748 0x710388e788 0x710388e7d8 0x71038acd68
.venv/Scripts/python.exe web/tools/r8_fx_switch_emu.py
```

[실행] Switch **10,240 입력 조합**, cancel 전달 **7개 체인(0..6자식)**, 호출 순서·현재 포인터·duration·return 불일치 **0**. 합성 구조체이며 selector, resource accessor, allocator, child lifecycle, parent restart는 반환을 제어하고 인자를 기록하는 경계 스텁이다. **원본 Switch calc와 cancel 순회 명령 자체를 실행했다.** 전체 선택기·믹서·게임 프레임 실행으로 확대하지 않는다.

조사 중 주소 `0x71038acde0`의 시작은 `0x71038acd68`이었다. 새 디컴파일 결과는 타입 판정 함수로, duration 변환 후보가 아니므로 근거로 채택하지 않았다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 이유·다음 근거 |
|---|---|
| 실제 stop fade 길이·파형 | vt30 이후 ELink 이미터/SLink voice backend의 stop 전달과 시간 필드; 이 Switch 조건 질문과 별개 |
| asset bit1의 원본 명칭 | 숫자 조건은 확정했으나 loop라는 이름은 불확실; loader와 leaf 반복 소비를 추가 추적 |
| 프레임 전체 calc 순서 | 액터/큐 processor 연결 별도 추적; 이 문서는 1회 calc 입력에 대한 동작만 확정 |
