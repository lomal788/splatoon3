# 머리카락 천 물리 — `Phive/Cloth/Har_*.bphcl`

[목차](model_character.md) · 결합 쪽은 [player_assembly.md §6.1](player_assembly.md)

## 1. 개요

머리카락 고유 뼈(`Hair_1..4_L/R`, `Nape_1` 등)는 Havok Cloth(hcl)가 움직인다. 액터 `Har_*` 팩 54개 중 46개에 `Phive/Cloth/<이름>.bphcl` 이 있고 `_F`/`_M` 이 같은 파일을 쓴다 [데이터]. 이 문서는 파일 형식과 시뮬 상수를 정리한다. 게임 코드 쪽(스텝 dt, 컬링 `ClothCullingParam.CullFrame 4` 적용, 머리·척추 캡슐 갱신 순서)은 판독하지 않았다 [미확정].

## 2. 형식 [데이터 + 도구 실행]

- 파일 = `"Phive\0"` 헤더(u32 @0x0C = TAG0 시작, 샘플 0x30) + Havok TAG0, SDKV `20210100`. 루트 `hkRootLevelContainer` → NamedVariant 3개: `Cloth Container`(`hclClothContainer`), `Resource Data`(`hkMemoryResourceContainer`), `Animation Container`(`hkaAnimationContainer`, 천 스켈레톤).
- 섹션: `SDKV, DATA, TYPE{TPTR, TST1, TNA1, FST1, TBDY, THSH, TPAD}, INDX{ITEM, PTCH}` — 충돌 메시(.bphsh)와 같다.
- **기존 `collision_tag0.py` 실패 원인**: TBDY 멤버 레코드 `(이름, flags, 오프셋, 타입)` 중 flags 에 **0x80 비트**가 있는 멤버는 flags 다음에 packed 정수 하나가 더 있다(이 파일에서는 `hclCollidable::userData`, `hkPackedVector3::values`, 둘 다 flags 0xa0, 추가값 3). 이 값을 읽지 않으면 그 뒤 TBDY 가 어긋나 FST1 인덱스가 범위를 벗어난다(IndexError). 추가값의 의미는 [미확정] — 원소 수는 아니다(userData 는 u64 하나, values 는 이미 `T[N]<hkInt16,4>`).
- 새 도구 `web/tools/gfx4p_bphcl.py`(collision_tag0.TagFile 상속, `_types` 만 수정): `types`(274개 타입·멤버 표), `items`, `tree [깊이]`(객체 트리, 다형 포인터에 `$type`), `cloth --json`(시뮬 상수 요약). 결과 샘플 `analysis/gfx4/player/Har_SQD000_cloth.json`(49 KB).
- 검증: `hclCapsuleShape.capLenSqrdInv` 91.131 = 1/|end−start|² (start 0.1376, end 0.2423 → 길이 0.1048) 로 값이 맞게 읽힘을 확인 [재구현 계산].

## 3. 구조 (Har_SQD000) [데이터]

| 항목 | 값 |
|---|---|
| 충돌체 | `Collidable_Head_Root_1` 캡슐 r 0.247623 (축 0.1376→0.2423), `Collidable_Spine_3` 캡슐 r 0.198245 (−0.1768→0.1768). 둘 다 enabled, pinchDetection 끔 |
| 천 데이터 | `Cloth_Hair_R`, `Cloth_Hair_L`(같은 상수), `Cloth_Rear` |
| 연산자(순서 = 상태 `Default` 의 operators [0,1,2,3]) | 0 Skin(`hclObjectSpaceSkinPOperator`, Rear 는 `hclBoneSpaceSkinPOperator`) → 1 `MoveFixedParticles` → 2 `Simulate` → 3 `MeshBone`(`hclSimpleMeshBoneDeformOperator`, 입자 → 뼈). 상태 `AnimToSimCurrent`[0,4]·`AnimToSimPrev`[0,5] 는 `VertexGather*`(hclCopyVertices) |
| 상태 전이·액션 | 없음 |

### 3.1 시뮬 상수 — `Cloth_Hair_R`/`_L`

| 항목 | 값 |
|---|---|
| 입자 | 9개: 0~6 움직임, **7·8 고정**(`fixedParticles`, mass 0·invMass 0 — 스킨된 위치로 이동) |
| 질량 | 움직이는 입자 0.714286 (= totalMass 5.0 / 7), invMass 1.4 |
| 반경·마찰 | 0.05 (maxParticleRadius 0.05), friction 0.5 |
| 중력 | (0, −9.81, 0) — 단위 m/s² [추정: 모델 단위 m] |
| 감쇠 | `globalDampingPerSecond` 0.001 |
| 솔버 | `subSteps` 1, `numberOfSolveIterations` 1, `adaptConstraintStiffness` false, `useAllInstanceCollidables` true |
| 제약 실행 순서 | `constraintExecution` [2, 3, 0, 4, 4, 1] = LocalRange → Transition → Standard → **Bend 두 번** → Stretch |
| Standard Links (id 0) | 14개. stiffness 0.714286(고정 입자 7/8 이 낀 링크) / 0.357143(둘 다 움직이는 입자) |
| Stretch Link (id 1) | 7개, 모두 고정 입자(7 또는 8) → 움직이는 입자, stiffness 1.0, restLength 0.134~0.973 |
| Local Range (id 2) | 7개(입자 i ↔ 참조 정점 i), `shapeRadius` 0.05/0.2/0.05/0.2/0.7/0.7/1.0, stiffness 0.8, normal 거리 무제한(±3.4e38), shapeType 0 |
| Transition (id 3) | 입자 9개, delay 0, toSimMaxDistance 1.0, 기간 1.0 |
| Bend Links (id 4) | 6개, bendMinLength/stretchMaxLength(예 0.157/0.196), bend·stretch stiffness 0.714286/0.357143 |
| 지형 충돌 | landscapeCollisionEnabled true, collisionTolerance 0.2, stuck 검출 끔 |
| 움직임 전달 | transferMotionEnabled false |

- 링크 stiffness 0.714286 = 1/(1.4+0), 0.357143 = 1/(1.4+1.4) — Havok 이 저장 시 `k / (w_A + w_B)` 로 미리 나눈 값으로 보면 원래 k = 1.0 [추정: 수치 일치, Havok 런타임 코드는 SDK 내부라 미판독].

### 3.2 `Cloth_Rear`

입자 3개(0·1 고정), 중력 **0**, 감쇠 0.001, Standard 2개(stiffness 1.0), Stretch 1개(1.0), LocalRange 1개(shapeRadius 0, stiffness 0.5), Volume Constraint 1개 [데이터].

### 3.3 전체 Har 팩

`PY web/tools/gfx4p_bphcl.py cloth --json` 를 팩마다 돌려 비교하는 일괄 표는 만들지 않았다(시간 제한). 다른 머리 모양의 상수 차이는 [미확정].

## 4. 웹 근사안 [추정 — 원본 동등성 미보장]

Havok 런타임(적분·제약 해법)은 SDK 내부라 판독하지 않았다. 위 상수를 그대로 쓰는 위치 기반 동역학(PBD/Verlet) 근사:

```
// 매 스텝 dt (원본 스텝 dt 는 [미확정]; 60fps 게임이므로 1/60 을 기본값으로)
고정 입자(7,8) = 스킨된 뼈 위치(Skin 연산자 결과)
for 움직이는 입자 i:
  v = (x - xPrev) * (1 - damping)^(dt)          // globalDampingPerSecond 0.001 해석은 [추정]
  xPrev = x; x += v + gravity * dt*dt
for c in [LocalRange, Transition, Standard, Bend, Bend, Stretch]:   // constraintExecution 순서, 반복 1회
  Standard: d = xB - xA; e = |d| - rest; xA += wA*k*e*d/|d|; xB -= wB*k*e*d/|d|   // k = 저장 stiffness(이미 /(wA+wB))
  Stretch : |xB - xA| > rest 이면 B 만 rest 거리로 당김(×stiffness)              // A 는 고정 입자
  Bend    : 거리를 [bendMinLength, stretchMaxLength] 로 클램프(각 stiffness)
  LocalRange: |x - 스킨 위치| > shapeRadius 이면 ×0.8 만큼 경계로 되돌림
충돌: 입자 구(r 0.05) vs 캡슐 2개(Head_Root_1, Spine_3) 밀어내기, friction 0.5
MeshBone: 입자 → 머리카락 뼈 회전(체인 방향 맞추기)
```

## 5. 미확정

| 항목 | 필요한 근거 |
|---|---|
| 스텝 dt·호출 주기·CullFrame 4 적용 | 게임 쪽 `spl::PlayerCustomHair` 천 갱신 함수(vt 0x71056416f8 슬롯 48~51 = 0x71026e2bdc/0x71026e3118/0x71026e3728/0x71026e382c, 디컴파일 `analysis/decomp/gfx4/p_batch1.c` 받아 둠, 미독) |
| Havok 감쇠·Bend·LocalRange 정확한 식 | SDK 내부(판독 불가 시 근사 유지) |
| TBDY flags 0x80 추가값 의미 | 다른 TAG0 파일 비교 |
| 다른 Har 의 상수 | 46개 팩 일괄 덤프 |
