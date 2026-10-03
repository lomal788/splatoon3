# ManualBindSRT.HideEar 실제 뼈 소비

## 1. 기능 개요

모자 설정의 HideEar는 몸의 Ear_L/Ear_R 뼈에 고정 행렬과 보조벡터를 적용한다 [판독]. 이름을 보고 임의의 메시 가시성 토글로 해석하지 않는다. 실제 consumer1454330 원본 실행 2,048입력의 getter/행렬/setter 호출이 비트 일치했다 [실행].

## 2. 원본 자료

Splatoon3 v0 main. 기존26e4e80/26e613c는 SRT writer/모자 결합으로 재사용했다. 새 `analysis/decomp/r8_graphics/manualbind_consumer.c`, `ear_flag_and_grid.c`, `hairinfo_loader.c`, `char_type_params.c`의 미판독 Ear 이름조회부분. decomp_index/SHARED/FUNCS와 실제prologue/ret를 대조했다. 도구 `web/tools/r8_gfx_dynamic_ear_emu.py`, 결과 `analysis/completion/r8/dynamic_ear_emu.json`.

## 3. 호출 흐름 [판독]

ManualBindSRT reflection26c865c →26e4e80(flags+3B0/+3B1 및SRT+380)→플레이어 사람 갱신243a4ec의243ab58→1454330. holder+64 사람 계산이 켜져 있을 때다. 모자행렬결합은 별도26e613c의 기존259건 proof를 유지하며 재계상하지 않는다.

1454330은 holder+210의 descriptor를 우선하며 descriptor0의+24가4인지 확인한다. 실패하면+1F8을 확인한다. +210이 유효하되 descriptor+8 모자runtime이0이면 +1F8로 다시가지 않고 끝난다. 이 실제 우선순위를 보존한다.

## 4. 필드·writer/reader [판독]

| 기준 객체 | 필드 | 확정 연결 |
|---|---:|---|
| ManualBindSRT | +30/+5B | HideEar enum/설정flag,26c865c명시등록→26e4e80 |
| ManualBindSRT | +34,+40,+4C | Rotation,Scale,Translate,26c865c명시등록 |
| HairInfo row | +18 | IsLong,13c1aa4의문자열조회/BOOL타입0xD0→byte→26e4e80 Auto모드 |
| 모자runtime | +3B0/+3B1 | 왼쪽/오른쪽 귀 적용byte;26e4e80→1454330 |
| holder | +CC/+CE,+D0/+D2 | Ear_L 모델/뼈index, Ear_R 모델/뼈index i16;144f9a0실제이름조회→1454330 |
| global58388E0 | 3×4 | 144f2a0초기화→1454330 SIMD소비 |

2026-10-03 정정: 기존 SRT +30 Rotation/+3C Scale/+48 Translate 표는 HairInfo fallback과ManualBindSRT 두 구조를 혼동했다. 위 ManualBindSRT 명명 reflection의 실제 오프셋으로 정정한다. 기존 수식은 유지한다.

## 5. 상태 규칙 [판독]

26e4e80 switch:0→(0,0),1→(1,1),2→(HairInfo.IsLong,HairInfo.IsLong),3→(0,1),4→(1,0). 범위밖 switch는 flags를 새로쓰지 않는다. 모자설정/머리카락행/리소스가 없으면 flags0과단위SRT. enum의외부텍스트명은 임의명명하지 않는다.

## 6. 행렬·순서 [실행]+[판독]

원본 고정 M의 행별 f32 rawbits:

```
3F1A108D BF47FBA4 3E2A07E1 00000000
3F4C7361 3F16B2AE BE00209C 00000000
80000000 3E54E6CE 3F7A67E2 00000000
```

각 getter의 local3×4 B행마다 아래 SIMD계산을 수행한다.

```
p = f32(M[0,c]*B[r,0])
p = fma32(M[1,c],B[r,1],p)
p = fma32(M[2,c],B[r,2],p)
O[r,c] = f32(p + (c==3 ? B[r,3] : 0))
```

FMUL→FMLA→FMLA→FADD 순서. xyz변환은고정회전,translation은보존한다. setter의 x2는 original4A999F8의 **(0.65,0.8,1.0)**다 [데이터]. 이 보조입력도 보존하며 단위scale라고 부르지 않는다. consumer전체가 이포인터를 두귀에 같은값으로 넘긴다. 실제SDK skeleton계산 전체를 이번2,048건 consumer검증으로 확대하지 않는다.

## 7. 모델·에셋 연결

144f9a0은 같은이름이라고 추정하지 않고 모델 vt40으로 Ear_L/Ear_R을 각각찾아 반환 modelindex/boneindex를 저장한다. consumer는 holder+28 모델component→+40 모델wrapper배열을 통해 해당 모델을 선택한다. vt68 localmatrix getter 뒤vt50 setter를 부른다. HairArrange와Head모자결합은 별도경로다.

## 8. 상호작용

flags는 모자/HairInfo 입력이고 실제적용은 사람 뼈 계산중 일어난다. shader색/LOD선택으로 해석하지 않는다. 몸↔모자 결합과파츠뼈copy의 기존순서와함께 재현해야 한다. `_Hlf` 전체pose합성은 별도미확정이다.

## 9. 웹 반영 필요

impl/render.md/assets.md: ManualBindSRT enum+HairInfo.IsLong→좌우flags, 실제Ear_L/R binding,원본SIMD행렬과보조벡터를 연결한다. 기존SRT오프셋표를두구조로분리한다. 구현/impl은 변경하지 않았다.

## 10. 검증

`python web/tools/r8_gfx_dynamic_ear_emu.py` → ear2048, matrix bitmatch true,두귀flags4조합 및합성무작위3×4행렬 전수일치. 원본matrix초기자144f2a0도실행했다. 스텁은 초기자의 네트워크ErrorResult/MakeIpv4Address(행렬과무관),consumer의 합성localmatrix getter/setter sink뿐이며 귀판단·곱셈 명령은 대체하지 않았다. 모자SRT결합의 이전259+1건은 이번새결과로세지 않는다.

## 11. 미확정·정정

2026-10-03 player_assembly §6.1의switch의미 미확정을 위 실제이름/writer/consumer로해소했다. 외부enum텍스트명,전체클립→SDK skeleton pose→skin/GPU의비트동등성은미확정이다. 보조벡터의SDK내부처리까지 consumer검증으로보장하지않는다. 다음전체pose:39cd350/39be4a0/39bf1b8 및model vt50 구현.
