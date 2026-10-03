# AS 요청 → 첫 tick·프레임 보고 원본 실행 — r8

## 1. 기능 개요와 보이는 동작

[실행] 기본 SkeletalAnimation(kind3) 잎의 커맨드를 요청하면 즉시 `cur=0`, 보고되는 슬롯 프레임도0이다. 이어 같은 프레임 후반 AS 틱을 실행하면 `dt=1`, 슬롯rate1일 때 `cur=1`이며 슬롯/래퍼 보고값도1이다. 요청 자체가 한 번 전진시킨 뒤 틱에서 다시 전진하는 동작이 아니다.

고정 질문 `graphics/anim_state_machine.md:L276`의 확정된 하위 연결이다. 복합 질문의 상태는 조사중으로 유지한다. [anim_state_machine.md §4.2](anim_state_machine.md)의 기존 판독을 보강한다. 기존 end=FSKA FrameCount와 상태 판정은 틱 전 cur이라는 판독을 재사용하며 새 성과로 다시 세지 않는다. 출력 포즈 합성 전체와 상태기계 전체를 실행했다고 확대하지 않는다.

## 2. 원본·버전·기분석 확인

Splatoon3(v0), 읽기 전용 원본의 추출 실행 이미지 `extracted/exefs/main.reloc.img`. 실행 BASE=`0x7100000000`. SHARED.md224 및 FUNCS.tsv454/455의 기존 프레임식과 `decomp_index.py --no-build`를 확인했다. 기존 `state/state_aux.c`399e340, `render/r4_asnode.c`399f848/39d3608, `render/r4_asnode2.c`39bc994/39bcdbc/399ec94 및 `r6_gfx_char/batch1.c`39cd350을 재사용했다.

새 디컴파일은 `analysis/decomp/r8_camweapon/as_first_tick.c`, `as_first_traversal.c`, `as_request_metadata.c`, `as_report_binding.c`다. 함수 시작은 func_lookup.py로 확인했다. 기존 실행 근거를 재실행 건수로 계상하지 않는다.

## 3. 진입과 전체 연결

[실행] 아래 함수의 전체 원본 바이트를 이어 실행했다. 커맨드/클립 메타데이터 공급 경계는 §10에 별도로 명시한다.

```text
399e340 AS 커맨드 요청
  → 3994f08/399f604 슬롯 커맨드·전환 입력
  → 39cd5d0/39c06d4 →39bbb5c
  → 원본 leafVT5743410+A8=39d3608
  → 39bc994: cur0,prev−1,end=FrameCount
  → 39bcdbc(x4=1): 전진 함수를 부르지 않음
  → 399ec94→3997558→39cd350→39d3dcc: slot104=0
399f848 AS 첫 틱
  → 399ec94→3996d84
  → 39ccc4c→leafVT+B0=39d3b10
  → 39bcdbc(x4=0)→39ab2c4: 전진
  → 39cd350→39d3dcc→slot104
24507a8 내부 원본 복사 블록2450c94..2450d6c
  → wrapper30=slot104
```

복사 블록은 X19=wrapper,X21=slot0,X24=descriptor stride48,X27=slot count1을 명시한 구간 실행이다. 24507a8 전체 렌더/기타 모델 작업까지 실행한 결과가 아니다.

## 4. 객체·필드와 writer/reader

| 기준 객체 | 필드 | 내용 | 원본 writer → reader |
|---|---|---|---|
| leaf node | VT+A8/B0/C8 | 진입/틱/보고 | VT5743410 →39d3608/39d3b10/39d3dcc |
| leaf instance | +92 byte | 재생 entry 번호 | 39d3608 →39d3b10/39d3dcc |
| AS slot | +170/+178 | entry 개수/64B 표 | fixture 입력 →39d3608 |
| entry | +4/+8 f32 | cur/prev | 39bc994 초기화,39ab2c4 전진 →39d3dcc |
| entry | +c/+14/+20/+28 | rate/end/loopStart/endOverride | 39bc994 →39ab2c4 |
| AS slot | +d4 f32 | 슬롯 재생률 | 입력 fixture →39bcdbc |
| AS slot | +104 f32 | 보고된 cur | 3997558/3996d84 →2450cc4 |
| wrapper | +30 f32 | 게임이 읽는 슬롯0 cur | 2450d68 원본 store →기존 상태 판정 |

같은 숫자 오프셋을 다른 객체와 혼동하지 않는다. entryRate1·loopStart0·endOverride−1은 이번 기본 잎의 원본 생성 결과이며 다른 FrameController 부착 상태에 확대하지 않는다.

## 5. 요청·틱 수명

[실행] 각 case는 깨끗한 동일 입력 fixture에서 요청→첫 틱을 수행한다. 요청의 leaf enter 인자 x4=1이고 trace에39ab2c4 호출이 없다. 첫 틱의 x4=0이며39ab2c4가 한 번 호출되고, 이후39d3dcc가 바뀐cur를 보고한다. 요청 직후 prev−1, 첫 틱 뒤 prev0이다.

연속 여러 틱은 별도로 시도했지만 두 번째 틱(실패 JSON의 0기준 tick=1)에서 slot+f4 pool count가1이 된 뒤 slot+168 pool pointer가 입력 fixture에 없어서3997080에서 멈췄다. 따라서 이번1025건은 첫 틱 결과이며 연속8틱 성공으로 기록하지 않는다(§11).

## 6. 독립 계산과 정밀도

[실행] 독립 Python 식은 원본 바이트/출력값을 참조하지 않고 명령 순서대로 f32 반올림한다. 첫 틱 cur0,entryRate1의 기본 입력에서는 다음과 같다.

```text
step=f32(f32(dt*slotRate)*entryRate)
x=f32(cur+step)
y=f32(x*10000)
r=nearest_integer_ties_away_from_zero(y)   # 원본 FRINTA
next=f32(f32(r)/10000)
if next>=end:
  if nonloop: next=end
  else if end>loopStart:
    len=f32(end-loopStart)
    if next>=f32(len+len): len=f32(len*trunc(f32(next/len)))
    next=round4(f32(next-len))
  else: next=end
prev=cur
```

원본은 별개 FMUL/FADD 명령이며 임의 FMA로 합치지 않는다. 양수 finite dt/slotRate 입력, 반복/비반복, 큰 첫 전진에 따른 clamp/wrap 경계를 포함했다. NaN/Inf·역재생·부착 FrameController 일반 경계는 이번 시험에 포함하지 않았다.

## 7. 에셋·화면 연결

기본 사례의 이름은 `ToSquid`, FrameCount6,비반복,dt1,slotRate1이다. 기존 문서의 사람 ToSquid 데이터6을 입력 메타데이터로 재사용한다. 이번 실제 BFRES/ASB 로더 전체를 새로 실행한 것은 아니다. 1024 추가 사례의 FrameCount1~120·loop 여부는 합성 메타데이터 입력이며 실제 모든 클립 열거라고 주장하지 않는다.

[실행] 기본 사례는 요청0→첫 틱1→slot104=1→wrapper30=1의 모든 f32 비트가 일치한다. 이것으로 모델이 실제 화면에 출력한 포즈를 검증했다는 주장은 하지 않는다.

## 8. 다른 기능과 순서

기존 원본 상태기계는 틱 전에 wrapper30을 읽어cur+3>end로 전환 판정한다. 이 연결 판독은 기존 근거이며 이번 새 연결 실행은 요청/첫 틱/보고 경로를 보강한다. 상태기계 본체 전체·모델 skinning·렌더 출력·소리는 본 시험 밖이다. dt 기본값1과 actor시간배율 공급은 별도 [anim_state_machine.md §4.2](anim_state_machine.md)의 SM 기본값 실행 정정을 참조한다.

## 9. 웹 반영 필요

분석만 수행했으며 웹 코드/impl 문서는 변경하지 않았다. 웹 요청 함수는 entry cur0을 초기화·보고하고, 같은 프레임 후반 AS 틱에서 한 번 전진한 값을 래퍼에 복사해야 한다. 상태 판정은 틱 전 프레임 값을 읽는 기존 원본 순서를 유지한다. dt×slotRate×entryRate 및 round4는 f32 순서와 ties-away를 보존한다. 이 순서 정정이 필요한 impl은 그래픽 담당의 표/원문 연결에서 기록한다.

## 10. 실행 검증·명령·실패

최종 `PY web/tools/r8_camweapon_as_request_first_tick_emu.py` 성공: **1025 요청 whole +1025 첫 틱 whole +1025 원본 wrapper 복사 블록, 9225 f32필드, bit mismatch0, null/fault/자동페이지0**. 요청/틱은 모든case에서 지정 반환PC까지 도달했고 trace에서 enter/tick의 인자·전진/보고 호출을 확인했다. 기본1025중1 +합성1024다.

경계: resource command→leaf 및 command index, transition metadata 없음, FSKA animIndex/FrameCount/loop/name 반환, 출력 binder capacity0/clear, debugoff, memcpy와 C++ guard acquire/release 런타임. 이 경계 호출은 JSON에 이름과 횟수가 남는다. 원본 요청·entry·advance·traversal·report 함수를 스텁하지 않았다. 출력capacity0 때문에 포즈 생성/바인딩 전체는 검증되지 않는다. guard 런타임 뒤 RTTI initializer는 원본 실행했다.

실제 명령/오류는 `analysis/completion/r8/as_first_tick_commands.md`, 성공JSON `analysis/completion/r8/as_request_first_tick_emu.json`, 연속 틱 실패JSON `analysis/completion/r8/as_request_first_tick_failure.json`에 저장했다. 초기 fixture 누락 원본 PC는399f63c(empty transition table),399ecc4(event pool),39b989c(frame buffer),39972ac(blend state),399a4dc(output binder)였다. 각 원본 read에 맞는 빈 입력객체를 연결했다. 정적 초기화의 PLT guard를 명시한 뒤 첫 틱은 정상 반환했다. 오류가 있었던 실행의 exit0 요약을 성공으로 세지 않는다.

## 11. 미확정·다음 근거

2026-10-03 정정: 기존 '요청 프레임 첫 틱은 경로 판독만(실행 검증 없음)'은 **기본 kind3/noattachment 커맨드의 요청→첫 틱→보고 연결에 대해 [실행]**으로 보강됐다. FrameCount와 틱 전 상태 판정 기존 결론은 뒤집지 않았다.

남음: 연속 두 번째 이후 AS 전체 수명은 slot+168 인스턴스 pool producer와399574c/3997020..7178을 연결한 입력 fixture가 더 필요하다. 실제 복합 ASB FrameController/InitialFrame/전환 metadata 요청, 모델 포즈 최종 합성, wrapper24507a8 전체 실행은 별개 미검증 경계다. 다음원본 주소는399574c(인스턴스 방문),3996d84의 pool 처리3997020..7178, 기존 slot constructor 및39c101c(인스턴스 reset)다. 이 한계를 미확정 전체 포즈·수명 질문을 완료하는 근거로 사용하지 않는다.
