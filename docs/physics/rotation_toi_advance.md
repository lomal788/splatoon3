# 회전 TOI 시간 전진·경계 보정 (r9, 2026-10-03)

## 1. 기능 개요와 체감 동작

회전하는 충돌 상대를 질의할 때 원본은 한 번의 직선 교차식으로 끝내지 않는다. **[판독]+[실행: 부분 식]** `094e6e4`는 현재 거리로 시간 전진량을 구하고, 접촉을 지나친 구간은 제한된 경계 보정으로 다시 좁힌다. 이 문서는 그 시간 계산과 분기를 확정한다. 일반 support/closest-feature, quaternion 보간 및 회전 TOI 전체는 **[미확정]**으로 남긴다.

## 2. 원본·버전·자료

Splatoon 3 v0, 원본 ARM64 image, `Lby_Lobby00` 1인 연습 범위. image SHA256 `39a8c94826d84b6106f112f2db16f7b2e2743bc6afd72054534a7708a9848a41`.

- 원본 함수 `0x710094e6e4` (3,920 B), 호출자 `0x7100948360`.
- 기존 새 디컴파일 `analysis/decomp/r9_physics/rotation_toi_core.c`를 재사용하고 원본 명령과 대조했다.
- 새 도구 `web/tools/r9_physics_rotation_advance_emu.py`; 결과 `analysis/completion/r9/physics_rotation_advance_emu.json`.
- 이전 단계 [phive_controller.md](phive_controller.md) §6.12.1~2의 상대 운동·staging과 구분한다.

## 3. 진입점과 전체 호출 흐름

**[판독]** `3c54140/3c54de4 → native 질의 → 0947aec → 0948360 → 094e6e4 → af7b70`의 회전 경로다. `af7b70`은 각 후보 pose에서 새 거리/법선을 생산한다. 이후 기존 원본 수집기와 게임 접촉 저장이 실행된다.

이번 새 실행은 게임 처리기 전체에서 해당 경로를 384회 통과하고 각 `ea28/ea6c`, `f170/f1e4` 경계를 관찰했다. 그 경계에서 들어온 거리·법선은 원본 생산값이며 별도 재구현으로 대체하지 않았다. 전체 수명·초기 overlap·목록 저장은 부모 §6.12.1을 참조한다.

## 4. 구조체·필드·상수

`Q`는 **094e6e4의 x1 입력 구조체**다. 게임 query 원본 또는 body와 같은 주소 체계로 혼동하지 않는다. `0948360`의 stack+0xd0에 구성된다. 아래 이름은 웹 권장 설명명이고 원본 클래스 필드명은 미확인이다.

| Q offset | 타입·용도 | writer / reader |
|---|---|---|
| +0/+8 | shape A/B 포인터 | 09486b8 / e740 |
| +10 | f32 보수적 운동 경계의 벡터 배율 | 09486bc~c0에서 query+9c / e808~868 |
| +20/+30 | 시작/종료 위치 vec4 | 09487cc~dc / ea80~eb14 |
| +50/+60 | 시작/종료 회전 표현 | 09487c8,88ac / 08a8764 호출 |
| +e0/+f0 | 선형/각운동 관련 vec4 | 09486d0/86d4 / e9ac~f4e0 |
| +110 | f32 시간 상한 capT | 09486d8/86e4, collector+10 / e73c |
| +114 | f32 보간 시간 배율 | 09486dc~e0, 기본1 / ea5c·f1c0 |
| +118 | f32 목표 거리 | 0948708, 기본0 / e72c·e9f8~ea24 |
| +11c | f32 전진식 거리 오프셋 | 09486f0~871c, −max(query+70,min(0929530 반환,query+88)) / e738·ea28 |
| +120/+124 | f32 비접근 접점 이후 목표 추가량 | 094870c, 기본0/0 / f4ec~514 |
| +128 | f32 거리 오차 허용량 | 0948720, query+70 / f12c·f2d0 |
| +12c | f32 최소 전진량 | 0948724~873c, 1/f32(query+7c 정수) / ea48·f1b4 |
| +130 | u8 최종 법선 상대 속도 검사 우회 | 0948700/8740, 기본1 / f474~478 |
| +131 | u8 추가 support guard 비활성 조건(값1) | 09486ac의 strh0 뒤 +130만1 / e7ac·e908 |

실제 fixture의 core 입력은 capT=1, 보간배율1, 목표거리0, +11c=−0.1982421875, +128=`0x3a83126f`(f32 .001), +12c=.00390625(1/256), flag130=1/131=0이었다. +10=.6999999284744263이다. 이를 게임 전체 기본 상수나 각도 단위로 확대하지 않는다.

## 5. 상태 전이와 수명

**[판독]** 결과 R(x3)의 byte0은 먼저0이다. 시간은 두 f32 lane으로0에서 출발한다. 간격은 `context+160`의 두 거리에서 shapeA/B+20 반지름 합을 뺀 값이다.

1. 남은 시간 동안 거리 목표에 닿을 수 없는 부등식이면 R.byte0=0으로 종료한다. R+4=시간 상한, R+8=현재 거리도 저장한다.
2. 시간 전진→pose 보간→`af7b70` 거리 갱신을 반복한다. 새 거리의 **low lane**이 목표보다 작아지면 경계 보정으로 넘어간다.
3. 거리 오차가 이미 허용량 이하면 보정을 생략한다. 크면 최대10회 보정한다.
4. 최종 접점/법선을 R+10/+20에 저장한다. Q+130≠0이면 R.byte0=1로 종료한다.
5. Q+130=0에서는 §6의 법선 상대 속도가 음수일 때만 hit. 그 외 목표/전진 오프셋을 갱신하고 다시 반복한다. 이 루프를 임의 종료 조건으로 바꾸지 않는다.

메모리 해제·TLS arena 반환 경로도 원본을 실행했다. allocator 정책은 기존 fixture 경계다.

## 6. 계산식·조건·의사코드

### 6.1 시간 전진 **[판독]+[실행: 식 비트 일치]**

`094e9ac~ea24`에서 현재 world 방향 n과 두 lane 시간 t에 대해 아래 bound를 생산한다. f32 연산별 반올림, `FSQRT`, lane별 연산을 유지한다.

```text
linear = dot3(n, Q.e0)                  // FMUL 각 성분, FADDP(x,y), FADD(z)
angular = length3(cross(Q.f0 * Q.10, n))
remaining = capT - t
bound = remaining * (angular - linear)
if gap.low - target.low >= bound.low:   // FCMGE의 mask를 반전한 low bit 검사
    return miss(capT, gap.low)
step = max((remaining * (gap - Q.11c)) / bound, Q.12c)
tNext = min(t + step, capT)
poseTime = tNext * Q.114
```

§10의 실행 대조는 `ea28~ea6c`의 **step→tNext→poseTime 블록**이다. 앞의 cross/dot bound 생산식은 이번에는 **[판독]**이며 숫자 독립 대조까지 했다고 쓰지 않는다. 부등식은 equal에서도 miss다. NaN에서 비교 mask=0이므로 `gap>=bound`가 참이라고 가정하지 않는다.

### 6.2 경계 보정 **[판독]+[실행: 식 비트 일치]**

이전 non-crossing endpoint `(tLo,gLo)`와 새 crossing endpoint `(tHi,gHi)`를 보존한다. entry에서 `abs(gap.low−target)>tolerance`일 때만 보정한다. 한 회의 원본 `f170~f1e4`는 다음과 같다.

```text
r = (target - gLo) / (gHi - gLo)
r = FMAX(FMINNM(r, f32(.9)), f32(.1))
tCandidate = FMAX(tLo + (tHi - tLo) * r, Q.12c)
poseTime = tCandidate * Q.114
```

상수는 .9=`0x3f666666`, .1=`0x3dcccccd`이다. 첫 상한 제한은 **FMINNM**이므로 NaN이면 숫자 .9를 선택한다. 이를 일반 NaN 전파 min으로 바꾸면 다르다. 곱과 합을 FMA로 합치지 않는다.

새 gap의 `abs(gap.low−target)<tolerance`이면 종료한다. 같은 허용량에서 진입은 `>`이고 내부 종료는 `<`이므로 equality도 원본대로 구분한다. non-crossing이면 lower endpoint를 갱신한다. crossing이면 upper endpoint를 갱신하고 tCandidate.low가 최소 진행량과 같은 경우에도 종료한다. 최대10회, 최종 선택 endpoint와 현재 평가 endpoint가 다른 경우 pose를 한 번 더 계산한다. 거리 판정은 low lane, 수치 갱신은 두 lane이다.

### 6.3 추가 support guard와 최종 방향 검사 **[판독]**

Q+131=1일 때 추가 guard를 끈다. 그 외 angular/linear의 비교 및 t<capT 조건에서 shape별 table slot+58/+60으로 vertex count/배열을 얻는다. 이 정점별 시간 하한 보정은 `eb50~f124`이고, 이 문서의 독립 실행 식 범위에 포함하지 않는다.

Q+130=0의 최종 검사는 `normalWorld · (Q.e0 + cross(Q.f0, contactPoint−lerp(Q.20,Q.30,t*Q.114)))`다. `f4e4`의 `FCMP` 뒤 `B.MI`이면 hit, 그 외 `target=min(target,gap+Q.120)`, `advanceOffset=min(advanceOffset,gap+Q.124)` 후 재진입한다. 원본 +130이1인 현재 fixture는 이 분기를 실행 증거로 검증하지 않았다.

## 7. 화면·애니메이션·이펙트·소리 연결

시간 fraction과 접점/법선이 게임 후처리/저장으로 전달된다. 착탄과 피격 표현에는 그 결과가 쓰인다. 이번 함수는 이펙트·음원 선택을 직접 결정하지 않는다. 부모 §6.12.1에서 저장하는 native point와 bullet center를 구분한다.

## 8. 다른 기능과의 상호작용

native 질의의 일반 support 계산, query 필터, shape codec, collector와 연결된다. 실제 fixture의 filter/codec은NULL이며 수학 함수는 원본이다. 게임 body는 회전 입력을 소비하는 flag/VT를 갖고, native 생성 body는 static이며 broadphase 등록을 수행하지 않은 직접 후보 질의다. 전체 사격장 메시·동적 다중 접촉으로 확대하지 않는다.

## 9. 웹 포팅 구조와 순서

`impl/physics.md`에 향후 반영할 사항: 회전 TOI가 필요할 때 시간 전진식과 10회 경계 보정, f32 순서, .1/.9 제한, FMINNM 의미, flag130/131 조건을 별도로 유지한다. 결과를 기하적으로 그럴듯한 .2 등으로 스냅하지 않는다. generic support/pose 보간이 미확정인 상태에서 임의 공식을 채우지 않는다. 이번 작업은 문서만 기록했고 impl/웹 코드는 변경하지 않았다.

## 10. 검증 코드·실행 결과

실제 명령:

```text
.venv/Scripts/python.exe web/tools/decomp_index.py 0x710094e6e4 --no-build
.venv/Scripts/python.exe web/tools/func_lookup.py 0x710094e6e4
.venv/Scripts/python.exe web/tools/disasm.py 0x710094e6e4 -n 980
.venv/Scripts/python.exe web/tools/r9_physics_rotation_advance_emu.py
```

**[실행: 식]** 전체54140/54de4 384회 정상 반환, core384/접촉목록1개씩. pureY회전과 x시작/종료·y/z 위치를 바꿨다. 실제 advance700/refine806회=1,506회, 두 lane **3,012 f32필드** 독립 식 비트 불일치0.

추가 원본 블록의 입력을 명시한 분리 실행은 advance8,192+refine8,192회, **32,768 f32필드** 불일치0. 두 endpoint가 서로 다른 lane, 0 분모/NaN 및 무한대도 포함했다. 이는 함수 전체 검증이 아닌 **원본 block 범위의 실행**이다. native support/quat를 재구현하거나 스텁하지 않았다.

전체 fixture의 null call/자동 mapping/fault0. 수학 callback 대체0. OS mutex·tick·coremask/time/clock/allocator Free 경계는 JSON `runtime.plt`에 전부 기록했다. 분리 블록은 PLT/null/auto/fault0. 기존 최초 rotation8건의 ULP 차이는 그대로 보존하고 이번 실행이 고정 .2를 기대하지 않는다.

## 11. 미확정과 다음 근거

**[미확정]** generic support/closest-feature `af7b70/aec920`, quaternion 보간 `08a8764`, 추가 vertex guard 전체 `eb50~f124`, 최종 non-approaching 분기의 독립 실행, 실제 Lby 전체 메시·codec/filter 조합. 이 문서는 시간 식 부분만 해소했으며 고정 inventory **phive_controller:L359/L495/L508**을 전체 확정으로 승격하지 않는다. 다음에는 일반 support와 회전 pose를 독립 대조하여 현재 whole 실행에서 생산된 거리/법선의 근거를 완성해야 한다.
