# 일반 Convex TOI 지원점·전진·종료 (r9, 2026-10-03)

## 1. 기능 개요와 체감 동작

네 게임 TOI 처리기가 native 질의로 전달하는 형상은 같은 처리를 사용하지 않는다. 일반 convex는 `0949570→aec920`, 캡슐 쌍은 `0948f30→0954550`, 회전 입력은 `0948360→094e6e4→af7b70`로 갈 수 있다. 이 문서는 **일반 convex의 지원점 선택·전진식 [판독]+[실행]**을 기록한다. 전체 일반/회전/메시 TOI는 아직 **[미확정]**이다.

## 2. 원본·버전·자료

Splatoon 3 v0 원본 ARM64. 기존 `analysis/decomp/r8_physics/solver_toi_core.c`의 `aec920`(13,272B), `primitive_toi.c`의 `0949570` 전체와 새 `analysis/decomp/r9_physics/motion_library_bind.c`의 `af107c`(756B)를 원본 명령과 대조했다. 기존 r8 디컴파일을 새 성과로 세지 않는다. 새 실행 `r9_physics_generic_support_emu.py`, `r9_physics_generic_toi_advance_emu.py`, `r9_physics_generic_toi_trace.py`; JSON은 `analysis/completion/r9/physics_generic_*.json`이다.

## 3. 진입점과 전체 호출 흐름

**[판독]** `3c52d30/5368c/54140/54de4→09af088→0947aec`가 query dispatcher를 고른다. `0949570`은 shape export table `57dd738+[type*200]+a8`에서 정점 배열·개수·convex radius를 얻고 scale/offset이 있으면 먼저 적용한다. 원본 두 collector을 전달하는 네 게임 처리기는 generic에서 **aec920의 arg7(initial-distance output)이 nonNULL**이고 시작 t=0이다. arg7=NULL이면서 A가 원점의 한 정점인 경우만 `aefd00→aefdc0`의 빠른 경로를 고른다. 따라서 별도 one-point 시험을 게임 네 처리기의 일반 실행이라고 확대하지 않는다.

## 4. 구조체·필드·상수

native generic 입력 Q: +0 delta(vec4), +10/+20/+30 상대 회전 열, +40 상대 원점, +50 tolerance 두 lane, +58 시작 fraction 두 lane, +60 radius 합 두 lane, **+68 반복 상한**, **+6c flags**. 출력 O: +0/4 fraction, +8/c separation, +10 point4, +20 normal4, +30 valid. 실제 `0949570`은 Query+7c=256을 Q+68에 복사한다. 2026-10-03 초기 Q68=0 탐색은 잘못된 fixture였고 원본 iteration 필드의 의미를 확인해 정정했다(실패 JSON 보존).

`aec920` 상수: 이동제곱 tiny=`1.4210855e-14`, margin=`max(tolerance*.1,2e-5)-radiusSum`의 하한0, 시작 및 선분 방향의 근사식에는 **f32 비트 해석** `(s32(bits(d2))>>1)+0x1fbb4000`, `0x7ef504f3-bits(edgeLengthSquared)`를 쓴다. 숫자→정수 변환식이 아니다. 로컬 support tolerance=1e-5(`3727c5ac`)에서 매 closest 평가 후 f32×1.3, 전진 후1e-5로 리셋한다.

## 5. 상태 전이와 수명

**[판독]** A/B 각 정점에는 XYZ와 `0x3f000000|index`인 네 번째 f32 **비트 태그**가 붙는다. 공간 W 좌표로 해석하면 안 된다. 초기 cache가 NULL이면 A0와 `Rᵀ(B0-origin)-delta*t`로 시작한다. 원본 wrapper는 cache=NULL이다. 두 형상의 feature 개수는 별개이고 분류값은 **B개수 | (A개수<<3)**이다. 2026-10-03 분석 중간 설명의 A/B 순서를 아래 원본 저장 대응으로 정정한다: param1/local158/local270/local_ac=A; param3/local168/local210/local_b0=B. 실행 입력/참조 수치는 이 명명 정정으로 변하지 않는다.

| classifier | A/B feature | 원본 처리 |
|---:|---|---|
| 9 | 1/1 | 점 차이 |
| 10 /17 | 1/2, 2/1 | 선분 투영·endpoint 줄이기; 서로 다른 부호에서 내부 방향 |
| 11 /25 | 1/3, 3/1 | 삼각형 Voronoi signed cross/dot mask; 내부면/edge/point 줄이기 |
| 12 /33 | 1/4, 4/1 | 사면체 signed face 거리 비교→한 면/edge/point로 줄이기 |
| 18 | 2/2 | 선분 쌍 cross, clamped closest parameters, endpoint 줄이기 |
| 19 /26 | 2/3, 3/2 | 삼각형과 선분의 교차/내부면 검사, 두 edge 후보 거리 비교 및 줄이기 |
| 나머지 | 해당 없음 | 원본 near-zero/recovery 분기로 보냄 |

feature 처리 순서·mask와 signed-zero는 원본 `solver_toi_core.c`의 `aecda4~aee4d4` 순서다. 이것을 임의의 단일 Minkowski simplex 개수라고 부르지 않는다. 선분 쌍은 cross² ≥ lenA²*lenB²*`.0025000002` 분기와 이후 `1e-12`, 근사 길이×`1e-5` 내부 guard를 그대로 둔다. 사면체는 signed distance*abs(distance)/normal², 퇴화면의 `0x7f7fffee`, max면/다음면×1.1 비교 및 원본 lookup table로 feature를 줄인다. 각 signed mask와 교환 순서는 C와 ARM64 주소를 함께 읽어야 하며 전체 재구현 비트 일치로 주장하지 않는다.

## 6. 계산식·조건·의사코드

### 6.1 지원점 선택 **[판독]+[실행]**

`af107c` 및 generic inline `aee5a0~aeeadc`는 dot=`F(F(v.x*n.x+v.y*n.y)+v.z*n.z)`를 계산한다. SIMD4lane마다 **새값이 더 큰 경우에만** index를 바꾸므로 같은 lane의 동률은 기존 index를 유지한다. 끝에서 lane0/1, lane2/3 비교는 앞 lane 동률 우선이고, 그 다음 첫 pair 동률 우선이다. **전역 최소 index를 고르는 연산이 아니다.** 8정점에서 최대값이 index1/4에 동시에 있으면 index4를 고른다.

개수 mod4=1은 첫 dot/index0를4lane에 복제하고 정점1부터4씩; mod4=2는 첫2개와 −inf 두 lane으로 시작하고2부터; mod4=3(개수>3)은 첫4개 후3부터4씩; mod4=0은4부터4씩 처리한다. 개수3만 별도 동률 mask 표 `[0,0,1,1,2,2,2,2]`를 사용한다. A는 −N, B는 R*N 방향으로 고르고 B를 A 좌표로 바꾼 뒤 support 개선량을 검사한다. dot/transform를 FMA로 합치지 않는다.

### 6.2 보수적 전진 **[판독]+[실행]**

원본 `aef0bc~aef1c0`, 각 연산은 f32다. 두 lane 시간/거리 계산과 XYZ dot 순서를 보존한다.

```text
gap = separation - radiusSum
if gap.low <= margin.low: return feature-reduction continuation
closing = F(F(delta.x*N.x + delta.y*N.y) + delta.z*N.z)
if closing >= 0: reject/reduction branch
step = -(gap-margin) / closing
nextT = t + step
if nextT.low >= outputMaxFraction: reject/reduction branch
B.feature[j] -= delta * step    // 4개 슬롯, 태그 lane도 원본대로
translationOffset = delta * nextT
iteration += 1
tolerance = 1e-5
if flags.bit1 && feature-count-reduction: continue
if iteration < Q.68: continue
return current-contact-valid
```

한도 소진은 반드시 miss가 아니다. flags.bit0의 distance-preserving branch와 bit1의 feature-count 조건은 원본 rejection `aef19c~aef1c0/aefb40~aefb6c`를 구분한다. zero delta tiny에 따른 초기 miss는 flags.bit0=0 **그리고** arg7=NULL일 때만 적용된다. initial-distance output이 있을 때 정지 질의가 같은 초기 조건으로 실패한다고 가정하지 않는다.

### 6.3 접점 저장과 추가 경계 **[판독]**

`0949570`은 초기 separation≤Query78에서 kind5를 두 번째 collector에 저장한다. main valid에서는 kind2를 첫 collector에 저장하고 fraction/point/normal을 세계로 바꾼다. 세계 point=`R_A(deltaLocal*t+pointLocal-normalLocal*(separation+radiusA))+originA`; normal=`R_A*normalLocal`. 실제 두 collector callback과 게임 staging은 [phive_controller.md](phive_controller.md) §6.12.1의 원본1024회 결과와 연결한다. `aec920`의 near-zero feature recovery와 추가 점/선분 시간 guard는 아직 독립 대조 전이며 §11 경계를 유지한다.

## 7. 화면·애니메이션·이펙트·소리 연결

원본 fraction과 point/normal은 원본 collector→contact128B→BulletGameContactList로 전달된다. 효과/표적 선택은 그 이후 consumer다. 네 번째 vertex 태그를 화면 좌표로 보내면 잘못된 값이 된다.

## 8. 다른 기능과의 상호작용

capsule `0954550`과 generic `aec920`를 구분한다. sphere→quad `094ae10`, native mesh tree→leaf와 회전 support는 별도 경로이며 이 지원점 테스트에 포함하지 않았다. 원본 game/native filter가 NULL인 fixture의 경계를 전체 Lby 레이어 조합으로 확장하지 않는다.

## 9. 웹 포팅 구조와 순서

`impl/physics.md/weapon.md`에 향후 반영: 실제 query dispatcher별 native 계산 선택, 두 collector의 시작 overlap,4lane 동률 순서, f32 전진 및 iteration exhausted valid를 유지한다. 미확정 일반/회전 경로를 단일 그럴듯한 t값으로 채우지 않는다. 이번에는 분석 문서/도구만 수정했다.

## 10. 검증 코드·실행 결과

실제 명령 `python -X utf8 web/tools/decomp_index.py --no-build 0aec920`, `func_lookup.py 0aec920`, 원본 capstone 판독 `aef0a8~aef200/af107c~af1370`, 세 신규 도구 실행. 로그 `analysis/completion/r9/physics_commands.md`.

- 전체 원본 `af107c` 8,193회/32,772 필드 독립 bit 불일치0. finite count1..64, 동률904개, null/auto/fault/PLT0. NaN·음수/0 count는 이 실행 범위가 아니다.
- 원본 advance block 4,097회/10,200 f32·정수 필드 불일치0. within-threshold713, reject2,976, iterate315, budget-valid93, null/auto/fault/PLT0. block 입력은 synthetic이며 kernel 전체 입력 생산까지 증명하지 않는다.
- 전체 `aec920` cube/triangle/oblique8회는 정상 반환과 trace 저장; arg7 있음/없음 모두 관찰. 전체 generic 독립 재구현과 비트 일치라는 주장이 아니다.
- 이전 aligned 참조40건 실패·Q68 fixture 실패·캡슐 거리173건 및 overlap3건 참조 실패는 부모 문서와 JSON에 그대로 남겼다. 실패를 지우거나 성공 표본에 합치지 않았다.

## 11. 미확정과 다음 근거

**[미확정]** `ae7b34` near-zero/overlap recovery, generic 추가 vertex guard와 arbitrary closest-feature whole 독립 대조, `094ae10` sphere/quad 특수 계산 전체, native leaf/codec/filter와 실제 사격장 지형 모든 쌍 연결, 회전 closest `af7b70`. pose interpolation `08a8764`는 [rotation_pose.md](rotation_pose.md)의 새98328+352필드 비트대조로 해소했으며 전체 회전 경로와 구분한다. 다음은 `aec920 aef9b8→ae7b34`, wrapper0949570의 원본 generic geometry 입력, 회전 지원점·보간식, `094ae10`이다. 현재 고정 phive L359/L495/L508은 **조사중**이며 이 부분식 성공만으로 확정 카운트를 올리지 않는다.
