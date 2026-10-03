# AS 값 태그의 타입·참조 분기 — 2026-10-03 r9

## 1. 기능 개요

AS 값의 상위 네 비트만 보고 문자열/bool/int/float를 정하면 안 된다. **호출한 typed reader가 타입을 정하고 태그 비트는 상수/override/참조 종류를 정한다.** 기존 “8은 string/bool, A는 int, D/E는 float”는 실제 파일에서 자주 보이는 값에 붙인 추정이었다.

## 2. 자료와 선행 분석

SHARED/FUNCS/decomp_index의 bool r5와 float/string r8 근거를 먼저 확인했다. r5 IntSelector 39CDA20은 상수120건만 실행됐고 블랙보드 경로는 not_executed였다. 이번은 이 미검증 경로와 주소키 override를 추가했다. 새 디컴파일 analysis/decomp/r9_graphics/as_tag_read.c; func_lookup 39CDA20=576B, 실제 prologue 일치. 같은 파일3998414는 슬롯 이름 검색 보조이며 태그 근거에 쓰지 않았다.

## 3. 공통 첫 분기 [판독]

slot=`[u32 tag][value]`다. bit31=0이면 value를 typed 상수로 읽는다. bit31=1이고 bit24=1이면 instance+60 연결 목록에서 **value칸의 주소**와 row+18이 같은 항목을 찾아 row+30을 typed 값으로 읽는다. 즉 이 경로는 low16 이름 조회가 아니다. 찾지 못했을 때 int/float=0, string은 컨텍스트 유무에 따라 `<Invalid>` 또는 빈 문자열이다. bool 함수는 같은 주소 검색과 오류 표시를 가지며 반환은 0/1이다. 기존 `0x80000000|i`만으로 모든 참조를 표현할 수 없다.

## 4. typed lookup 슬롯 [판독]

| reader | resource/identifier API | value API | 반환 해석 |
|---|---|---|---|
| string 3997A74 | ctx20 vt118, low16 | ctx28 vt130 | 반환 주소의 u64 문자열 포인터 |
| int 39CDA20 | ctx20 vt120, low16 | ctx28 vt138 | u32 비트를 정수 비교값으로 사용 |
| float 3997DE0 | ctx20 vt128 | ctx28 vt140 | f32 |
| bool 39982BC | ctx20 vt130, low16 | ctx28 vt148 | u8 !=0 |
| vec3 component(float reader) | ctx20 vt138 | ctx28 vt150 | tag bit26..27=1/2/3 → X/Y/Z |

위 API 선택은 nibble의 타입 분기가 아니라 각 원본 reader가 고정한다. 새 int 실행은 bit24가 0인 8..F 모두 vt120/138을 쓴다는 반례를 확인했다. float lookup의 low16 전달은 디컴파일의 누락 인자 표기만으로 일반화하지 않고 해당 원본 명령/기존 판독을 따른다.

## 5. float/string의 추가 태그 [판독: 기존 근거 재사용]

float은 공통 override 뒤 `(tag>>30)<3`이면 직접 참조, 상위2bit가3이면 **float 파라미터 표** low16×20으로 간다. 표 내부 tag를 다시 읽으며 scale/offset/min/max/속도 제한을 적용한다. 따라서 일반float참조의 상위 nibble도8..B일 수 있고 D/E는 float이라는 보편 타입 이름이 아니다. 직접참조 bit25=1은 내장 값(0=ctx1DC,1=난수,2=ctx1E0,4=ctx1E4)을 읽는다. string은 bit25=1/low16=3이면 ctx1E8 문자열, 그 밖 내장은 빈 문자열이다. 원본 실제 파일의 D/E 사용 사실과 reader 분기 정의를 구분한다. 캐시·속도 제한식의 새 증거는 r8 asb_float_parameter.md에 이미 있어 재계상하지 않는다.

## 6. 새 정수 selector·변화 플래그 [판독]+[실행]

39CDA20은 읽은 값과 앞 n−1 case를 순서대로 비교하고 첫 일치를 반환한다. 없으면 마지막(n−1), n<2이면 즉시 n−1이다. typed getter가 돌려준 변화byte를 instance+B4와 비교해 outChanged에 기록하고 instance+B4를 갱신한다. override 경로에서는 local changebyte0을 사용한다. case 값도 상수/typed lookup/주소 override를 같은 규칙으로 읽는다. 이번 case 입력은 상수이며 case 자체의 typed/override lookup은 판독만이다.

## 7. 새 원본 실행 검증 [실행]

`PY web/tools/r9_gfx_as_inttag_emu.py` 결과: 39CDA20 전체 LR까지1,536건. typed lookup512, override hit512, override miss512; 상위 nibble8..F 각각192건, output/호출순서/변화 플래그 불일치0, unknown PLT0. 블랙보드 identifier/value API(ctx20 vt120,ctx28 vt138)는 명시적 fixture로 공급했고, 주소 연결 목록 순회와 선택식은 원본이다. 기존 r5 상수120건을 다시 실행하거나 새 성과로 세지 않았다.

## 8. 미확정과 다음 근거

이 문서의 질문은 태그 타입·참조 정의다. 실제 typed blackboard producer와 전체ASB 갱신/포즈는 미실행이며 별도 미확정이다. case typed/override와 오류 출력 부작용도 이번 실행 밖이다. 다음: wrapper의 실제 vt118..138 메모리 lookup 및 value manager producer. upstream 값을 fixture로 공급한 실행을 실게임 값 공급 검증으로 확대하지 않는다.

## 9. 웹 반영 필요

impl/render.md·assets.md에서 nibble→타입 분기를 사용하면 typed reader 및 bit31/24/25/26..27/30 규칙으로 교체해야 한다. 값칸 주소를 키로 하는 override를 low16 블랙보드 조회로 바꾸면 안 된다. 코드와 impl은 변경하지 않았다.

## 10. 명령과 결과

기존 notes/index 확인→func_lookup/disasm→`sh web/tools/full_decomp.sh analysis/decomp/r9_graphics/as_tag_read.c 0x71039cda20 0x7103998414` 성공→에뮬레이터1536건 성공. 초기 disasm.py에 개수를 위치 인자로 넣은 명령은 usage error였고 `-n`으로 수정했다. 다음 reader 후보3998474/3998398은 함수 중간이라 사용하지 않았다.

## 11. 정정 이력

2026-10-03: anim_state_machine §2.4/§2.7의 nibble 종류 대응을 이 원본 reader 분기로 정정한다. 기존 문장은 지우지 않고 이력으로 남긴다. 새 정수 블랙보드·주소 override 실행이 이전 r5 상수 테스트의 구멍을 채웠으며, 다른 reader의 기존 판독/실행 건수는 새 결과로 재계상하지 않았다.
