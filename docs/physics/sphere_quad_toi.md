# 구–사각형 TOI 원본 실행 (r9, 2026-10-03)

## 1. 기능 개요와 체감 동작

**[판독]+[실행: 유한 rectangle sweep]** `094ae10`은 shape query table의 구/점(type1)→사각형(type4) 처리기다. 면, 네 모서리, 네 꼭짓점의 후보에서 가장 이른 접촉을 선택한다. 넓은 면의 충돌만 계산하면 실제 모서리·꼭짓점 접촉 시간과 법선을 재현할 수 없다. 이번 실행은 전체 원본 함수의 제한된 입력군 대조이며, 물리 복합 질문 전체의 확정으로 확대하지 않는다.

## 2. 원본·범위·자료

Splatoon3 v0 Lby_Lobby00 1인 연습 분석. `0x710094ae10` 3,968B. 기존 `analysis/decomp/r8_physics/primitive_toi.c`의 원문을 SHARED/FUNCS/decomp_index/func_lookup로 확인하고 재사용했다. query dispatch·mesh leaf 생성은 기존 [phive_controller.md](phive_controller.md) §6.10 근거다.

신규 도구 `r9_physics_sphere_quad_probe.py`, `r9_physics_sphere_quad_emu.py`, `r9_physics_sphere_quad_oblique_emu.py`. 결과는 `analysis/completion/r9/physics_sphere_quad_{probe,emu,oblique_emu}.json`. 최초 독립 참조 실패는 `physics_sphere_quad_first_failure.json`에 보존했다.

## 3. 진입점과 호출 흐름

**[판독]** `094ae10(Ctx,Q,IA,ShapeB,TagB,IB,RelativeTransform,reserved,TOICollector,InitialCollector)`.

A shape는 Q+38, B shape는 인자3이다. 원본 sphere constructor `092efbc`로 생성한 A를 쓰고, B의 type4/네 정점은 명시한 fixture 입력이다. 전체 함수가 계산한 128B 접촉을 collector의 virtual+28에서 기록한다. 이 출력 소비 경계만 capture하며 형상·query·TOI·법선 계산은 원본 명령으로 실행했다.

## 4. 필드·상수·자료형

| 필드 | 원본 소비 |
|---|---|
| Q+38 | shapeA |
| Q+50 vec4 | 상대 이동 delta |
| Q+74 f32 | 추가 반지름 |
| Q+78 f32 | 초기 접촉 허용 거리 |
| Ctx+18 f32 | 0이면 초기 접촉 검사를 허용 |
| IA/IB+20 pointer | 월드 pose |
| IA/IB+30 byte | 반지름 override 선택 |
| IA/IB+38 f32 | override 반지름 |
| IA/IB+40 vec4 | 정점 scale |
| shape+20 f32 | 기본 반지름 |
| shape+40 signed relative pointer | 구 중심 또는 사각형 정점 |
| TOICollector+10/+14 | four-lane 시간 상한 입력 |
| 접촉+0/+10/+20/+78 | 월드 접점/월드 법선/분율 또는 초기 signed distance/종류 |

원본 상수: 면 외적 재계산 기준 `f32(1e-8)`; 작은 법선 성분 한계 `0x2c800000=2^-38`; 작은 비영 법선 확대 `0x5f800000=2^64`; 후속 모서리 법선 보정의 외적 기준 `f32(1.6e-11)`. 같은 최소값의 lane 선택은 원본 `4a81220` bitmap table을 따른다.

## 5. 상태 전이·순서

구 중심은 shape의 중심을 IA scale로 곱하고 상대 transform에 넣는다. 중심XYZ가 모두0이면 transform+30을 직접 사용한다. 네 B 정점은 IB scale을 곱한다. 반지름 합은 **f32(f32(radiusA+radiusB)+Q.extraRadius)** 순서다.

면 후보의 예상 시간은 수집 상한과 먼저 비교한다. 초기 거리가 `radius+Q78`보다 크고 면 후보 시간이 상한 이상이면 다른 edge/vertex 후보를 보기 전에 반환한다. 따라서 후속 quadratic의 반올림만으로 상한보다 조금 작은 값을 만들어 접촉을 추가하면 원본과 다르다.

원본은 초기 collector에 종류5를 전달한 뒤 조건에 따라 TOI collector에 종류2·분율0을 전달한다. 동일 입력도 InitialCollector 유무에 따라 기록 수가 다르다.

## 6. 계산식·상세 흐름

**[판독]+[실행: rectangle 유한 입력군]** 아래 dot/cross와 각 사칙 연산은 원본 f32 순서로 반올림한다. fused multiply-add로 치환하지 않는다.

```text
r = f32(f32(rA+rB)+extraR)
e_i = v_(i+1)-v_i
m_i = origin-v_i
N = normalize(cross(v1-v0, v2-v0))
sep = dot(origin-v0,N)
faceClosing = dot(delta,N) with sign xor when sep<0
faceT = (r-abs(sep))/faceClosing if closing<0 and r-abs(sep)<=0
```

각 vertex의 quadratic:

```text
invV2 = delta²==0 ? 0 : f32(1/dot(delta,delta))
b = f32(dot(delta,m_i)*invV2)
residual = m_i-delta*b
D2 = dot(residual,residual)
if D2 < r² and sqrt(f32((r²-D2)*invV2)) <= -b:
    vertexT = f32((-b)-sqrt(f32((r²-D2)*invV2)))
```

각 edge는 원본 projection으로 `mPerp=m_i-e_i*(dot(m_i,e_i)/e_i²)`, `deltaPerp=delta-e_i*(dot(delta,e_i)/e_i²)`를 만들고 같은 quadratic을 계산한다. edge 위 좌표 `dot(m_i,e_i)+dot(delta,e_i)*edgeT`가 **0 이상·e_i² 이하**여야 한다. 0길이 분모의 역수는 mask로0이 된다. 면 후보에는 원본 half-space와 인접 edge mask가 적용된다. 일반 사각형의 그 mask를 rectangle 경계 검사만으로 대체한 근거는 아니다.

최소 후보의 유형 우선순위는 같은 값이면 vertex→edge→face이며, 같은 유형 내 lane은 원본 bitmap table을 따른다. vertex 법선은 centerAtT−vertex의 정규화, edge 법선은 **cross(cross(edge,centerAtT−edgeStart),edge)**의 정규화다. 원본의 작은 벡터 확대/영벡터 fallback을 생략하지 않는다. 뒤쪽 면 법선에는 vec4 전체 sign xor가 적용되어 **(-0,-1,-0,-0)**이 남는다.

```text
centerAtT = origin + delta*t
pointLocal = centerAtT-(candidateDistance-rB)*normalLocal
pointWorld = IB.pose * pointLocal
normalWorld = IB.pose.rotation * normalLocal
```

일반 sweep의 candidateDistance는 r 합이다. 초기 접촉에서는 실제 최소 거리이며 종류5의 scalar는 `distance-r`다. 정규화 후 법선이 네 정점 중 하나에 음의 support distance를 만들면 원본은 네 edge의 대체 법선을 검토한다. 유효 외적 기준1.6e-11과 support 최소값 비교를 거친 뒤, 원래 면 법선이 더 유효하면 마지막에 이를 선택한다. 이 보정 전체의 독립 수치 대조는 이번 입력군에 포함되지 않는다.

## 7. 표시·카메라·효과음 연결

이 함수가 기록하는 분율·접점·법선은 후속 query collector와 게임 측 접촉 순서에 사용된다. 히트마커·도색·효과음을 직접 발생시키는 함수는 아니다. shape tag와 body 정보는 접촉 metadata로 전달된다.

## 8. 상호작용·실행 경계

원본 라이브러리 초기화와 sphere 생성은 실행했다. 사각형 정점·scale·반지름·collector 상한은 명시한 입력이다. 월드 pose는 별도 identity를 쓰며 상대 transform의 translation과 중복하지 않는다.

PLT 경계는 OS mutex/tick/core-mask, time/clock, allocator Free다. query 수학 함수는 stub으로 대체하지 않았다. 모든 신규 최종 실행의 null/auto-page/fault는0이다. 실제 Lby 지형 mesh 전체와 활성 filter를 이 단독 fixture로 검증했다고 기록하지 않는다.

## 9. 웹 반영 사항

향후 `impl/physics.md`/`impl/weapon.md`: 면·edge·vertex 후보, plane 초기 거절의 cap equality, f32 연산 순서, 초기 종류5와 TOI 종류2 구분, sign xor의 음수0, B 반지름을 뺀 접점 식을 고려해야 한다. 해당 impl·웹 코드는 이번에 수정하지 않았다.

## 10. 실제 실행·실패

```text
.venv/Scripts/python.exe web/tools/decomp_index.py 0x710094ae10 --no-build
.venv/Scripts/python.exe web/tools/func_lookup.py 0x710094ae10
.venv/Scripts/python.exe web/tools/disasm.py 0x710094b408 -n 190
.venv/Scripts/python.exe web/tools/disasm.py 0x710094b70c -n 120
.venv/Scripts/python.exe web/tools/disasm.py 0x710094b9c8 -n 116
.venv/Scripts/python.exe web/tools/r9_physics_sphere_quad_probe.py
.venv/Scripts/python.exe web/tools/r9_physics_sphere_quad_emu.py
.venv/Scripts/python.exe web/tools/r9_physics_sphere_quad_oblique_emu.py
```

probe:14회 전체 함수 정상 반환. 면/edge/꼭짓점/miss/away/겹침/뒤쪽면 × 초기 collector 유무. 면 분율.375, edge .3999999761581421, 꼭짓점 .43385618925094604. 겹침에서는 초기 collector가 있으면 signed distance−.19999998807907104/종류5 뒤 분율0/종류2 두 기록이다.

**[실행]** 수직 sweep2,048사례/13,808개 필드, scaled rectangle·oblique sweep·A/B radius override·추가 반지름3,072사례/11,342개 필드가 독립 f32 비트 일치했다. 합계5,120사례/25,150필드, 불일치0. 명중 유형은 각각 face413/edge394/vertex369 및 face551/edge257/vertex19다.

첫 probe는 PhysicsUC에 없는 w16 호출로 AttributeError(exit1), u16 직접 기록으로 수정했다. 초기 탐색 fixture는 IB world pose와 상대 transform을 같은 버퍼로 써 접점 translation이 두 번 적용됐으며 별도 버퍼로 수정했다. 독립 참조 첫2,048회는199불일치(exit1)였다. 뒤쪽 법선의 음수0과 **면 초기 cap 거절이 후속 quadratic보다 앞서는 순서**를 원본 명령에 맞춰 정정해0불일치(exit0)다. 최초 실패 JSON을 보존했다. oblique3,072회는 첫 독립 대조부터0불일치(exit0)다.

## 11. 미확정·다음 원본

**[미확정]** 일반 비평면·퇴화 quad의 모든 인접 edge mask·f64 외적 재계산, 법선 support 보정 전체의 독립 수치 대조, 실제 mesh leaf→collector 전체 경로는 이번 완료 범위가 아니다. 다음 근거는 `094b658` f64 cross, `094b2d0..394` 후보 mask, `094bb98..bd8c` 대체 법선 순회, mesh leaf `09372cc` producer다. 물리 고정 복합 질문 L359/L495/L508의 전체 확정으로 이 제한 입력군만 승격하지 않는다.
