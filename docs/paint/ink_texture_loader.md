# InkTexInfo 로더 — 임시 파라미터와 런타임 행 연결

## 1. 기능 개요

슈터 도색의 변형 텍스처와 높이 범위는 InkTexInfo 파라미터에서 런타임 행으로 복사된다. PatternNum은 텍스처 개수이자 변형 나눗수이며 배열의 n번째는 명시적으로 이름 `_n`에 연결된다 [판독].

## 2. 분석 대상

Splatoon 3 v0. 원본 C `analysis/decomp/r8_graphics/gp_core.c` 13c3f54, `asb_sequence_ink.c` 2c2362c. 기존 소비자·자료는 [paint_and_score.md §3.5.3](paint_and_score.md)이다.

## 3. 호출 흐름 [판독]

도색 전역 초기화 2c4ff64 → 2c2362c(globalInfo, heap) → `Model/InkTexture.bfres` 로드 및 50개 InkTexType 이름으로 `Work/Gyml/<이름>.spl__paint__InkTexInfo.gyml` 조회 → 텍스처 찾아 0xF8B 객체 배열 → 런타임 행. 파서는 13c3f54다. 이전에 적은 13c3fd0은 함수 안 레이블이므로 함수 시작 주소를 정정한다.

## 4. 임시 구조와 런타임 구조 [판독]

런타임 행은 globalInfo+0x40+i*0xD0이다. 아래 R 오프셋은 **행 기준**이다.

| 원본 키 | 임시 T | 런타임 R | 값 전달 |
|---|---|---|---|
| PatternNum | +20 | +0 / +10 | 0이면 1로 바꾼 수를 배열 개수·나눗수 두 칸에 씀 |
| AnimationFrame | +10 | +14 | 원값 |
| AnimationStep | +14 | +18 | 양수는 1로 제한, 0은 0 |
| HeightRangeType | +1C | +B8 | enum 원값 |
| StaticHeightRangeMax | +24 | +BC | f32 비트 그대로 |
| StaticHeightRangeMin | +28 | +C0 | f32 비트 그대로 |
| HeightRangeRate | +18 | +C4 | f32 비트 그대로 |
| DisableSlopeScale | +2C | +C8 | byte 원값 |
| TextureName | +8 pointer | 행 이름 문자열 | 빈 문자열이면 InkTexType 이름 사용 |

## 5. 상태 수명

초기화 때 각 행의 텍스처 객체들을 만들고 globalInfo+38에 BFRES 리소스를 저장한다. 파라미터 행을 찾지 못하면 텍스처 1개로 `White` 이름을 조회하며 런타임 PatternNum도 1로 둔다 [판독]. 기존 값 유지 여부를 임의로 0으로 초기화하면 안 된다.

## 6. 텍스처 배열 순서 [판독]

```text
N = PatternNum != 0 ? PatternNum : 1
name = TextureName이 비어 있지 않으면 그것, 아니면 InkTexType 이름
if N == 1: texture[0] = BFRES.textures.find(name)
else: for n in 0..N-1: texture[n] = BFRES.textures.find(format("%s_%d", name, n))
```

BFRES 내부 저장 순서나 이름 사전 정렬이 배열 순서를 정하는 것이 아니다. Shot00의 N=12이므로 런타임 [0..11]은 Shot00_0..Shot00_11이다. 찾지 못한 texture 객체를 자동으로 다른 변형으로 바꾸는 분기는 없으며 소비자의 범위 밖 인덱스는 [0]으로 바뀐다(기존 소비자 판독).

## 7. 에셋 연결

`Model/InkTexture.bfres`의 이름 조회 3597068→1180400→361f908으로 agl::TextureData를 만든다. gyml TextureName이 기본 InkTexType 이름을 대체할 수 있다. 텍스처 이름과 변형 인덱스를 빌드 변환 시 유지한다.

## 8. 다른 기능과의 상호작용

N→D 변환의 `Random(seed).getU32() % PatternNum`은 이 배열에서 변형을 고른다. AF/AS는 반복 요청 소비자의 입력이다. 로더가 AS 양수를 1로 제한하므로 **데이터의 AS=3을 그대로 런타임 3으로 넣으면 원본과 다르다** [판독]. 실제 렌더 단계 내 순서는 여기서 확정하지 않는다.

## 9. 웹 포팅 구조

권장 `InkTextureRegistry` 초기화는 이름→배열 구축과 위 표의 원본 복사를 수행한다. 계산·소비자는 런타임 표를 사용하고 gyml 임시 구조를 직접 사용하지 않는다. 도색 요청 시드·정밀도는 기존 명세를 따른다. 코드 수정은 이번 분석 범위에 포함하지 않는다.

## 10. 검증과 실제 명령

`full_decomp.sh analysis/decomp/r8_graphics/asb_sequence_ink.c ... 2c2362c` → 7함수 디컴파일, INDEX 5433. 13c3f54의 문자열 키와 필드 저장, 2c2362c의 소스/목적 오프셋·`%s_%d` 분기를 함께 판독했다. 이 로더는 원본 실행하지 않았다. 합성 N→D 600회·r6 포맷 검증은 기존 근거이며 새 로더 실행 증거로 쓰지 않는다.

## 11. 미확정과 정정

2026-10-03 r8: 기존 `PatternNum/높이 max,min,rate` 이름 추정 및 텍스처 배열 이름 순서 추정을 원본 writer로 정정했다. AnimationStep은 데이터 값과 런타임 값이 다름을 명시했다. BFRES 파라미터 전체 메모리 연결 실행·GPU 프레임 내 단계 연결은 [미확정]; 다음은 실제 객체 구성 후 2c2362c 연결 실행과 ModuleSystem 3daae40/3dac8b4다.
