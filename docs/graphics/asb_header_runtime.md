# ASB 이벤트 개수와 뼈 이름 마스크 그룹 — r9

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행]+[데이터] 사람 ASB의 header+14는 이벤트 그룹 개수5, 오징어는1이다. +18의2/0은 애니 슬롯 개수가 아니라 **이름으로 뼈를 선택하는 마스크 그룹 개수**다. 사람의 상체/루트 애니 적용을 분리할 수 있는 자료이며, 이 문서는 최종 포즈 합성까지 확정하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0. `extracted/exefs/main.reloc.img`, `extracted/romfs/Pack/Actor/SplPlayer.pack.zs`의 `AS/SplPlayer.root.asb`, `AS/SplPlayerSquid.root.asb`. 신규 C는 `analysis/decomp/r9_graphics/as_header_load.c`, `as_header_consumers.c`. 기존39B17F8 로더 판독은 재사용한다.

## 3. 진입점과 전체 호출 흐름

[판독] 신규3DE0F6C는 버전410 검사→0x18 wrapper(VT5741748)→0x80 resource(VT57419B0)→기존39B17F8 생성 후 wrapper VT1C0=신규39AFDFC로 header14를 읽는다. 0보다 크면 VT200=신규39B01BC가 ASB 파일 이름을 반환하고 `AnimationEvent/AsNode/%s.baev`를37B2B28로 요청한다. 이벤트 키 실제 발화는 기존 [asb_event_runtime.md](asb_event_runtime.md)의 근거를 따른다.

[판독] 신규39AE15C는 ASB+18와 요청 group index를 비교하고 resource+30(header34의 오프셋)에서 `(12+8*n)` 크기의 그룹들을 차례로 건너뛴다. 이름별 마스크 객체를 모델 바인더 VT+C0에서 얻고 신규39AE544로 그룹 항목을 적용한다. 이는 AS 슬롯0/1 생성 코드가 아니다.

## 4. 구조체·필드·상수·열거형 표

| 기준 객체 | 필드 | writer / reader와 의미 |
|---|---|---|
| ASB 헤더 | +14 u32 | 이벤트 그룹 개수.39AFDFC 및39B17F8의 그룹 초기화 루프 reader |
| ASB 헤더 | +18 u32 | 이름 마스크 그룹 개수.39AE15C 요청 index 상한 reader |
| ASB 헤더 | +34 u32 | 이름 마스크 그룹 시작 offset.39B17F8→resource30 writer |
| 마스크 그룹 | +0 s16 | 항목 수n; 다음 그룹=현재+12+8*n |
| 마스크 그룹 항목 | +0 u32,+4 s16,+6 s16 | 문자열 풀 기준 뼈 이름 offset, 값, bool로 변환되는 마지막 필드.39AE544 reader→마스크 API VT10 |
| 적용 객체 | +18 pointer,+20 pointer | 마스크 객체, resource wrapper |
| 적용 객체 | +30/+31/+34 byte | 인자4 bit0/인자3 bit0 및 `obj33 && !arg4` 상태.39AE544 writer |

API 마지막 bool의 원래 이름/자식 상속 의미는 여기서 이름을 붙이지 않는다. 실제 SDK 마스크 구현 판독 전에는 raw bool로 보존한다.

## 5. 상태 전이와 전체 수명

[판독]+[실행] 마스크가 있으면 VT8 reset→그룹 순서대로 모든 이름을 VT10에 추가→상태30/31/34 갱신. obj33=0 및 arg4=0이면 VT30 finalize를 호출한다. 마스크 포인터가 null이면 반환한다. 39AE15C에서 요청 그룹이 header18 이상이면 생성·적용을 건너뛴다. 원본 마스크 할당/SDK 해제 전체는 이번 실행 범위에 포함하지 않는다.

## 6. 계산식·조건·상세 의사코드

```text
p = resource.groupTable
repeat groupIndex: p += 12 + 8*s16(p)
mask.reset()
for i in 0..s16(p)-1:
    name = ASB.stringPool + u32(p+12+i*8)
    mask.add(name, s16(p+16+i*8), s16(p+18+i*8)!=0)
obj30 = arg4 & 1; obj31 = arg3 & 1
obj34 = (obj33 != 0) & (arg4 ^ 1)
if obj33==0 and (arg4&1)==0: mask.finalize(obj+8)
```

[판독] 실제 함수는 음수 문자열 offset에 대해 전역 공유 문자열 목록을 사용한다. 실행 표본은 실제 원본 두 ASB와 양수 offset이며 음수 경로를 검증하지 않았다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

[데이터]+[실행] 사람 두 그룹(offset AF64/AF88)은 모두 세 항목 `nw4f_root`, `Spine_1`, `Root_Model`, 값1/bool1이다. 오징어 header18=0이라 이 표가 없다. 이벤트 개수 사람5/오징어1은 원본 getter 출력과 동일하다. ASB SHA256는 실행 JSON에 저장했다. 표의 값1을 임의로 최종 포즈 가중1이라고 확대하지 않는다.

## 8. 다른 기능과의 상호작용

AS 슬롯 수와 그룹 수를 같은 값으로 두면 오징어의 슬롯 자체를 없애는 오독이 된다. 슬롯 커맨드 요청과 이름 마스크 선택은 다른 입력이다. 그룹 적용 뒤 SDK의 실제 스켈레탈/재질/가시성 샘플러 합성은 [미확정]이다.

## 9. 웹 포팅 구조와 구현 순서

`impl/render.md`, `impl/assets.md` 반영 필요: ASB header18을 보조 슬롯 수로 사용하지 않고 가변 길이 이름 마스크 그룹으로 별도 저장한다. `(name,value,bool)` 순서를 보존하고 최종 포즈 적용은 SDK 소비 식이 밝혀질 때 연결한다. 코드/impl 문서는 수정하지 않았다.

## 10. 검증 코드·실행 결과·기대값

`.venv/Scripts/python.exe web/tools/r9_gfx_as_header_emu.py` 성공. 신규 원본39AFDFC 실제 ASB2건, 신규39AE544 전체1,024 합성 그룹+실제 사람 그룹2건=1,026건, 호출 순서·이름·값·bool·상태 모두 mismatch0. PLT 미처리0. 마스크 API VT8/10/30만 명시 fixture callbacks이며 원본39AE544 본체는 LR까지 실행했다.39AE15C allocation 및3DE0F6C 파일 서비스는 [판독]이며 실행하지 않았다.

사람 그룹2개와 각각3항목, 오징어0개를 실제 원본 팩에서 다시 읽었다. 실제 파서/파일해시/콜백 경계는 `analysis/completion/r9/graphics_as_header_emu.json`에 있다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

2026-10-03 정정: 종전 [anim_state_machine.md §2.1](anim_state_machine.md)의 '+18 보조 슬롯(레이어) 수' 추정을 이름 마스크 그룹 개수로 정정한다. +14 이벤트 수는 getter·BAEV 요청과 연결하여 확정한다. 기존 문구는 날짜별 정정으로 보존한다.

실제 SDK 마스크 add/finalize의 자식 상속·스켈레탈 샘플러 가중 소비는 [미확정]. 다음은39AE15C가 얻는 모델 바인더 VT+C0의 실제 클래스 및 그 마스크 VT10/30이다. header2C 등의 다른 섹션은 +14 해소만으로 전체 확정하지 않는다. 이번 raw+2C/stride96 검사에서 실제 파일의 별도 그룹 크기와 일치하지 않는 것이 드러났으므로39AFE0C를 이벤트 테이블 전체 loader로 해석하지 않았다.
