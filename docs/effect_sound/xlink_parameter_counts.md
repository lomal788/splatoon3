# XLink 리소스 파라미터 수와 공통 로더 (v0)

## 1. 기능 개요와 사용자에게 보이는 동작

사격장 사격·이동·피격의 ELink/SLink 에셋을 읽기 위한 공통 파일 형식이다. `numResParam`은 **에셋 레코드에 저장된 u32 ResParam 값의 수**이며 트리거 덮어쓰기 값은 포함하지 않는다 [데이터]. 재생 개수·동시 음성 수·사용자 수가 아니다. 이 문서는 고정 inventory `xlink_format.md:L69`의 수 불일치 질문을 해소한다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 main과 `extracted/romfs/ELink2/elink2.Product.100.belnk.zs`(0x22), `SLink2/slink2.Product.100.bslnk.zs`(0x1F). 새 디컴파일은 `analysis/decomp/r8_fx/xlink_rom_loader.c`, `xlink_common_loader.c`. 해제 원본의 SHA256과 필드 전수 집계는 `analysis/completion/r8/xlink_count_emu.json`에 저장한다. 기존 ParamDefine 로더 `0x71038922f0`는 r6 결과를 재사용하며 신규 확정 수에 다시 넣지 않는다.

## 3. 진입점과 전체 호출 흐름

`0x7103899460`은 XLNK 네 바이트 및 버전을 검사하고 ParamDefine 로더 `38922f0` 뒤 **공통 로더 `0x71038945a8`**을 호출한다 [판독]. `38945a8`은 헤더 수와 공통 표 포인터를 저장한 뒤 선택적 debug dump, 문자열 포인터 relocation, 사용자 블록 relocation, 시스템 전역 속성 연결을 처리한다. 이번 실행 검증은 `38945a8..389473c` 메타데이터 초기화까지만 수행한다. 후반 전체 실행으로 확대하지 않는다.

## 4. 구조체·필드·상수·열거형 표

H는 XLNK 파일 시작, C는 runtime common resource, P는 ParamDefine runtime이다 [판독].

| 원본 필드 | 저장 위치 | 의미/원본 근거 |
|---|---|---|
| H+0C u32 | C+00 u32 | numResParam; 원본 debug 문자열도 같은 이름 |
| H+10 u32 | C+04 u32 | 에셋 레코드 수 numResAssetParam |
| H+14 u32 | C+08 u32 | 덮어쓰기 레코드 수 |
| H+48 u32 | C+98 u32 | 사용자 수 |
| H+18 u64 | C+30 pointer | 덮어쓰기 표: H+pos |
| H+20 u64 | C+38 pointer | 속성 이름 표: H+pos |
| P+40 u32 | C+28 계산에 사용 | ParamDefineTable 바이트 크기 |

`3894650/54`는 H+0C→C+00만 복사한다. C+28 에셋 표 시작 계산(`389469c..46b4`)에는 사용자 수와 ParamDefine 바이트 크기를 사용하고 numResParam은 사용하지 않는다. C와 H가 같은 구조체인 것처럼 오프셋을 혼용하지 않는다.

## 5. 상태 전이와 전체 수명

로드 전 C를 초기화한다. 파일 내 offset은 이 시점에 포인터로 만들고 후반에서 이름과 사용자 참조를 연결한다. numResParam은 초기 복사된 메타데이터이며 갱신 중 음성/이미터 카운터가 아니다 [판독]. 이번 근거는 해제·재로드 전체 수명을 추가 확정하지 않는다.

## 6. 계산식·조건·상세 의사코드

```text
pdt = align8(0x60 + 4*numUser) + 8*numUser
assetStart = pdt + ParamDefineTable.size
p = assetStart; assetValues = 0
repeat numResAssetParam:
    k = popcount(u64 mask[p])
    assetValues += k
    p += 8 + 4*k
assert p == triggerOverwriteParamTablePos
assert assetValues == numResParam
p = triggerOverwriteParamTablePos; overwriteValues = 0
repeat numResTriggerOverwriteParam:
    k = popcount(u32 mask[p])
    overwriteValues += k
    p += 4 + 4*k
assert p == localPropertyNameRefTablePos
```

위 equality는 **실제 v0 원본 두 파일 전수 [데이터]**다. 원본 빌드 도구의 모든 버전을 대상으로 한 일반 명세로 확대하지 않는다. 로더의 C+28=`align8(H+60+4*numUser)+8*numUser+P+40`는 [판독]+[실행: 초기화 블록]이다.

| 원본 | 에셋 레코드 | 에셋 값 = numResParam | 덮어쓰기 레코드 | 덮어쓰기 값 | 두 종류 합 |
|---|---:|---:|---:|---:|---:|
| ELink | 2,822 | 16,893 | 60 | 108 | 17,001 |
| SLink | 14,591 | 138,491 | 41 | 47 | 138,538 |

2026-10-03 정정: 기존 “에셋+덮어쓰기 합과 달라 의미 미상”은 **별도 표인 덮어쓰기 값을 더했던 비교 범위 오류**였다. header 자체의 오류/숨은 파라미터로 해석하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

같은 공통 로더가 ELink와 SLink에 적용된다. 에셋의 개별 값은 해당 ParamDefine 타입과 참조 방식으로 해석한다. 이 수는 CPU/GPU 입자 수나 오디오 그룹 제한으로 사용하지 않는다. 사용자의 실제 액션 규칙은 [xlink_trigger_runtime.md](xlink_trigger_runtime.md)를 따른다.

## 8. 다른 기능과의 상호작용

트리거 덮어쓰기 표는 독립 헤더 위치와 레코드 수를 갖는다. userParam의 경우 SLink 8개, ELink 0개도 에셋 값 수에 합산하지 않는다 [데이터]. `ActionTrigger+1E` 공통 flags 의미는 별도 미확정으로 유지한다. composite inventory L430은 numResParam만 해결됐으므로 전체 확정으로 승격하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

`impl/fx.md`, `impl/assets.md`의 원본 비교 시 parser의 검증 카운터를 `assetValues`와 `overwriteValues`로 구분해야 한다. numResParam은 앞의 값과 대조한다. 재생 로직·입자 수·음성 수를 이 헤더 값으로 정하지 않는다. 이번 작업에서 웹 소스와 impl 문서는 수정하지 않았다.

## 10. 검증 코드·실행 결과·기대값

명령: `.venv/Scripts/python.exe web/tools/r8_xlink_count_emu.py`. 원본 두 파일 전수 mask 집계와 원본 메타데이터 블록 8건, **불일치 0·스텁 0**. 각각 numResParam을 원본/0/1/FFFFFFFF로 공급해 C+00만 변하고 C+04..9F는 모두 비트 동일함을 확인했다. 변형은 emulation memory만이며 original 파일은 변경하지 않았다. 원본 두 파일의 실제 에셋/덮어쓰기 끝 위치도 일치한다.

사전 SHARED/FUNCS 조회 및 `decomp_index.py --no-build 0x71038945a8`, `func_lookup.py` 확인 후 신규 3899460/38945a8을 full_decomp 했다. default decomp_index는 INDEX 쓰기 권한으로 실패했고 --no-build 읽기로 재확인했다. `web/docs/분석.txt`, `web/tools/xlink_parse.py` 경로 조회 실패는 실제 `web/분석.txt`, `effect_xlink.py`로 정정했다. XLNK 정수 상수 검색에 결과가 없었던 것은 로더가 바이트별 magic을 검사하기 때문이며 로더 부재 근거로 쓰지 않았다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

원본 리소스 생산 도구의 내부 정의는 확보하지 않았다. v0 두 파일의 count 의미와 소비 위치는 확정했고, 다른 버전의 일반화는 하지 않는다. 공통 로더 후반 전체 실행·ActionTrigger+1E 모든 flags·믹서/렌더러 전체 동작은 별도 질문으로 남긴다. 다음 근거는 `38945a8` 후반과 action 생성/갱신의 flags 소비자다.
