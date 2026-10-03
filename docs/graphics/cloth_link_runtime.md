# 머리카락 Standard/Bend 링크의 저장 강성과 보정 (r9)

## 1. 기능 개요

2026-10-03. 고정 질문 `graphics/hair_cloth.md:L45`의 저장 강성 해석을 신규 원본 소비자와 실제 TAG0 값으로 정정했다 [판독]+[실행]+[데이터]. Standard/Bend 소비자는 저장 coefficient에 각각 endpoint invMass를 곱하고 invMass 합으로 다시 나누지 않는다. SQD000의 저장 coefficient는 이 소비자에서 effective k=1과 동등하다. “Havok이 저장할 때 나누었다”는 오프라인 작성 경위의 단정은 제거하고 **원본 런타임에서 확인한 의미**로 답한다.

## 2. 원본과 자료

v0 main.reloc.img, `.bphcl` `analysis/render/bphcl/Har_SQD000_F.bphcl`. 신규 `analysis/decomp/r9_graphics/cloth_standard_constraint.c`, `cloth_bend_constraint.c`, `cloth_constraint_stiffness_dispatch.c`. 도구 `web/tools/r9_gfx_cloth_standard_emu.py`; 결과 `analysis/completion/r9/graphics_cloth_standard_emu.json`. 기존 `cloth_summary` 출력은 소수6자리 요약이므로 본 검증에서는 `tree(open_bphcl(...),14)`의 raw f32를 읽었다.

## 3. 전체 호출 경로

`DC8C88/DC8FF4`는 `D0422C`로 입력 강성 scalar를 선택한 뒤 constraint vt38을 호출한다. 실제 RTTI 이름 `28hclStandardLinkConstraintSet` 주소4A92C48의 typeinfo55141E8은 vtable55141A8에 연결되고, +38=`D47BD0`다. Bend는 `24hclBendLinkConstraintSet`4A92B4C→typeinfo5513EA8→vtable5513E68+38=`D1C354`다 [판독].

func_lookup는 각각 앞의 wrapper D47B94/D1C318로 표시했다. 실제 진입은 D47BD0/D1C354의 `FCMP S0,0; B.LS return` 뒤 SP prologue로 확인했다. 호출자가 이 주소를 직접 등록하며 중간 명령을 임의 시작으로 쓰지 않았다.

## 4. 객체와 원본 데이터

constraint X0+28은 링크 배열, +30은 개수다. X1은 hclSimClothInstance, +20은 현재 위치, +18은 data이며 data+40의 입자 stride10, +4가 invMass다.

| 링크 | stride | 필드 |
|---|---|---|
| Standard | 0C | +0 A u16, +2 B u16, +4 restLength f32, +8 stored coefficient |
| Bend | 14 | +0 A, +2 B, +4 bendMinLength, +8 stretchMaxLength, +C bend coefficient, +10 stretch coefficient |

실제 SQD000 Hair_R/L/Rear Standard30개 모두 `F(stored * F(invMassA+invMassB))` bits=`3F800000`이다. Bend Hair_R/L12개 각각 bend/stretch 두 coefficient도 같은 bits1이다 [데이터]+[재구현 계산]. 원본 coefficient bits는 `3F36DB6E`(약.714286), `3EB6DB6E`(약.357143), Rear1은 `3F800000`; invMass1.4 bits는 `3FB33333`다. 반올림한 .714286/.357143를 테스트 입력으로 다시 만들지 않았다.

## 5. 수명과 분기

유한 입력 scalar≤0이면 두 소비자는 링크를 수정하지 않는다. scalar>0이면 배열 순서로 위치를 제자리 갱신하여 다음 링크가 갱신된 위치를 읽는다. endpoint가 같거나 invMass가0인 일반 최종 모델은 별도 입력 상황이다. 본 테스트는 유효 endpoint0/1과 실제 원본 링크의 coefficient/역질량을 사용했다. 입자 위치는 합성 fixture이며 실제 전체 머리카락 포즈를 재생한 것은 아니다.

## 6. 정확한 식과 상수

F는 각 연산 후 f32 반올림이다. 두 소비자는 `d=B-A`, `s=F(F(dx²+dy²)+dz²)`를 만들고, ARM `FRSQRTE` 초기 추정→`FRSQRTS(s,F(r*r))` 한 번→`F(r*refine)`를 사용한다. s≤0이면 invLength0이다. 길이는 `F(s*invLength)`이고 vec4 전체 보정의 normal은 `F(d*invLength)`다. libc sqrt/normalize로 치환하면 비트가 달라질 수 있다.

Standard:

```
q = F(F(F(length-restLength) * stored) * scalar)
correction = F(normal * q)
A += F(correction * invMassA)
B -= F(correction * invMassB)
```

Bend:

```
stretch = F(max(0,F(length-stretchMaxLength)) * stretchStored)
bend = F(max(0,F(bendMinLength-length)) * bendStored)
q = F(F(stretch-bend) * scalar)
correction = F(normal * q)
A += F(correction * invMassA)
B -= F(correction * invMassB)
```

따라서 저장값을 또 `(invMassA+invMassB)`로 나누면 원본보다 보정이 약해진다. effectiveK의 수치 관계는 원본 runtime consumer로 확정했으며, 원본에 없는 오프라인 작성기의 알고리즘을 추정하여 붙이지 않는다. 입력 scalar의 상태별 보정은 D0401C/D0422C의 별도 dispatcher로 전달된다. stored coefficient 자체의 의미와 구분한다.

## 7. 캐릭터 연결

SQD000 Default 상태의 원본 constraint 순서는 LocalRange→Transition→Standard→Bend→Bend→Stretch다. 본 신규 Standard/Bend 호출은 그 consumer를 연결한 것이며, 같은 링크 수와 동일 순서로 원본 전체 상태를 실행한 것은 아니다. 각 링크간 제자리 갱신 순서는 원본 loop로 판독했다.

## 8. 다른 기능과의 상호작용

컬링 dt·substep 감쇠 적분은 [cloth_frame_runtime.md](cloth_frame_runtime.md), [cloth_damping_runtime.md](cloth_damping_runtime.md)에 분리했다. Standard/Bend는 그 위치 버퍼를 수정하고 다음 제약/충돌 소비자에게 넘긴다. 최종 MeshBone/애니 보간이 남으므로 최종 머리카락 모션 전체와 동등하다고 쓰지 않는다.

## 9. 웹 반영 필요

`impl/render.md`, `impl/assets.md`: stored stiffness의 runtime 재나눔을 추가하지 않고, endpoint invMass 가중·배열의 제자리 갱신·Bend 두 방향 coefficient와 경계 식을 반영해야 한다. 원본과 비트 동등성이 필요하면 ARM estimate+한번 refinement의 f32 순서도 보존한다. 웹 코드와 impl은 수정하지 않았다.

## 10. 실행 검증

`PY web/tools/r9_gfx_cloth_standard_emu.py` 성공. native D47BD0 전체1054(실제 링크30의 coefficient + 합성1024), native D1C354 전체2060(실제 Bend12 + 합성2048), f32bits mismatch0, LR종료. 입력 scalar0/음수/.25/1/2, invMass0/양수, 길이0/최솟값 미만/범위 안/최댓값 이상을 포함했다. 두 함수의 위치 vec4 전체8개 lane을 독립 계산과 비교했다.

Callable/PLT/math stub 없음. 합성객체의 profiler context는null이다. 독립 inverse sqrt estimate의 최초 정규화 구간이 잘못되어 case14 실패했다(원본seed3E840000, 재구현3E838000). 진단 hook으로 원인을 찾고 입력 구간을 정정했으며, 최종 도구에서는 진단 hook을 제거했다. 최종 비교는 원본 중간값을 참조하지 않는다.

## 11. 남은 근거와 다음

L45의 runtime coefficient 해석은 전체 해소다. offline exporter 작성 경위는 원본 배포물에 도구가 없어 확정할 수 없으며 런타임 의미를 대체하지 않는다. L79 복합 질문은 감쇠와 Bend 부분을 해소했지만 LocalRange가 남아 전체 확정으로 계수하지 않는다. final pose/landscape/capsule은 별도 미확정이다.
