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

- **해소(2026-10-03) [데이터]:** `PY web/tools/r5_gfx_char_bphcl_batch.py` → `analysis/completion/r5/gfx_char_bphcl_all.json`. Har 팩 54개를 모두 읽었다. 천이 있는 팩은 46개이고 서로 다른 bphcl 은 23개다.
  - 천이 없는 팩: `Har_OCT003`, `Har_OCT_RVL000`, `Har_OCT_RVL001`, `Har_SQD008`(각 _F/_M).
  - `_F`/`_M` 은 같은 파일을 쓴다. 예외는 두 가지다. `Har_SQD005` 는 한 팩 안에 bphcl 이 2개다. `Har_SQD_MSN310` 은 _F 가 SQD000 것을, _M 이 SQD006 것을 그대로 쓴다.
  - 모든 천에서 마찰은 0.5, 감쇠(`globalDampingPerSecond`)는 0.001 로 같다. 중력은 (0, −9.81, 0) 또는 0 이다. 입자 수·고정 입자 수·질량·반경은 머리 모양마다 다르다(아래 표).
  - solver 값(`subSteps`, `numberOfSolveIterations`, `constraintExecution`)은 이 요약 경로에 들어 있지 않아 표에 없다. SQD000 값은 §3.1 에 있다.

| 팩 | 파일 | 천: 입자(고정), 움직이는 입자 질량, 반경, 중력 y |
|---|---|---|
| Har_OCT000 (_F/_M) | `Har_OCT000_F.bphcl` | Sim_Left: 입자 8(고정 2), 질량 1.666667, r 0.006/0.018/0.024/0.036, 중력 y -9.81; Sim_Nape: 입자 3(고정 2), 질량 1.0, r 0.0, 중력 y -9.81; Sim_Right: 입자 8(고정 2), 질량 1.666667, r 0.006/0.018/0.024/0.036, 중력 y -9.81 |
| Har_OCT001 (_F/_M) | `Har_OCT001_F.bphcl` | FrontR: 입자 3(고정 2), 질량 1.0, r 0.0, 중력 y -9.81; FrontL: 입자 3(고정 2), 질량 1.0, r 0.0, 중력 y -9.81; pPlane1: 입자 7(고정 2), 질량 0.2, r 0.0, 중력 y -9.81 |
| Har_OCT002 (_F/_M) | `Har_OCT002_M.bphcl` | Sim_Center: 입자 11(고정 2), 질량 0.111111, r 0.05, 중력 y -9.81 |
| Har_OCT004 (_F/_M) | `Har_OCT004_F.bphcl` | Cloth_HairR: 입자 7(고정 2), 질량 2.0, r 0.0, 중력 y -9.81; Cloth_HairL: 입자 7(고정 2), 질량 2.0, r 0.0, 중력 y -9.81; Cloth_Nape: 입자 3(고정 2), 질량 5.0, r 0.0, 중력 y 0.0 |
| Har_OCT005 (_F/_M) | `Har_OCT005_M.bphcl` | pPlane4: 입자 12(고정 4), 질량 0.625, r 0.0, 중력 y 0.0 |
| Har_OCT006 (_F/_M) | `Har_OCT006_M.bphcl` | Cloth_Nape: 입자 9(고정 6), 질량 1.666667, r 0.0, 중력 y -9.81; Cloth_R: 입자 7(고정 2), 질량 1.0, r 0.0, 중력 y -9.81; Cloth_L: 입자 7(고정 2), 질량 1.0, r 0.0, 중력 y -9.81 |
| Har_OCT007 (_F/_M) | `Har_OCT007_M.bphcl` | Cloth_Hair1: 입자 8(고정 2), 질량 0.833333, r 0.0, 중력 y 0.0; Cloth_Hair2: 입자 6(고정 2), 질량 1.25, r 0.0, 중력 y 0.0 |
| Har_SQD000_F, Har_SQD000_M, Har_SQD_MSN310_F | `Har_SQD000_F.bphcl` | Cloth_Hair_R: 입자 9(고정 2), 질량 0.714286, r 0.05, 중력 y -9.81; Cloth_Hair_L: 입자 9(고정 2), 질량 0.714286, r 0.05, 중력 y -9.81; Cloth_Rear: 입자 3(고정 2), 질량 1.0, r 0.0, 중력 y 0.0 |
| Har_SQD001 (_F/_M) | `Har_SQD001_F.bphcl` | Front_L: 입자 6(고정 2), 질량 2.5, r 0.0, 중력 y -9.81; Front_R: 입자 6(고정 2), 질량 2.5, r 0.0, 중력 y -9.81; Rear_L: 입자 3(고정 2), 질량 5.0, r 0.0, 중력 y -9.81; Rear_R: 입자 3(고정 2), 질량 5.0, r 0.0, 중력 y -9.81 |
| Har_SQD002 (_F/_M) | `Har_SQD002_F.bphcl` | Front_R: 입자 5(고정 2), 질량 1.666667, r 0.0, 중력 y -9.81; Front_L: 입자 5(고정 2), 질량 1.666667, r 0.0, 중력 y -9.81; Tail: 입자 3(고정 2), 질량 5.0, r 0.0, 중력 y 0.0; Rear: 입자 3(고정 2), 질량 1.0, r 0.0, 중력 y 0.0 |
| Har_SQD003 (_F/_M) | `Har_SQD003_F.bphcl` | Sim_Rear: 입자 6(고정 2), 질량 1.25, r 0.0, 중력 y -9.81; Sim_Front: 입자 10(고정 2), 질량 1.0, r 0.0, 중력 y -9.81 |
| Har_SQD004 (_F/_M) | `Har_SQD004_F.bphcl` | Front_L: 입자 3(고정 2), 질량 5.0, r 0.03, 중력 y -9.81; Front_R: 입자 3(고정 2), 질량 5.0, r 0.03, 중력 y -9.81; Side_L: 입자 3(고정 2), 질량 10.0, r 0.03, 중력 y -9.81; Side_R: 입자 3(고정 2), 질량 10.0, r 0.03, 중력 y -9.81; Tail: 입자 3(고정 2), 질량 10.0, r 0.03, 중력 y -9.81 |
| Har_SQD005 (_F/_M) | `Har_SQD005_F.bphcl` | Front_L: 입자 10(고정 2), 질량 0.125, r 0.0, 중력 y -9.81; Front_R: 입자 10(고정 2), 질량 0.125, r 0.0, 중력 y -9.81; Rear: 입자 6(고정 2), 질량 0.25, r 0.0, 중력 y -9.81 |
| Har_SQD005 (_F/_M) | `Har_SQD005_F.bphcl` | Front_L: 입자 9(고정 2), 질량 1.428571, r 0.03, 중력 y -9.81; Front_R: 입자 9(고정 2), 질량 1.428571, r 0.03, 중력 y -9.81; Rear: 입자 5(고정 2), 질량 1.0, r 0.03, 중력 y -9.81 |
| Har_SQD006_F, Har_SQD006_M, Har_SQD_MSN310_M | `Har_SQD006_M.bphcl` | Tail01: 입자 8(고정 2), 질량 0.833333, r 0.0, 중력 y 0.0; Tail02: 입자 8(고정 2), 질량 0.833333, r 0.0, 중력 y 0.0 |
| Har_SQD007 (_F/_M) | `Har_SQD007_M.bphcl` | Front: 입자 6(고정 2), 질량 1.25, r 0.0, 중력 y 0.0; Back: 입자 6(고정 2), 질량 1.25, r 0.0, 중력 y 0.0 |
| Har_SQD009 (_F/_M) | `Har_SQD009_M.bphcl` | Side: 입자 6(고정 2), 질량 1.25, r 0.0, 중력 y -9.81; Back1: 입자 6(고정 2), 질량 0.25, r 0.0, 중력 y 0.0; Back2: 입자 6(고정 2), 질량 0.25, r 0.0, 중력 y 0.0 |
| Har_SQD010 (_F/_M) | `Har_SQD010_M.bphcl` | Main: 입자 12(고정 6), 질량 0.833333, r 0.0, 중력 y 0.0 |
| Har_SQD011 (_F/_M) | `Har_SQD011_M.bphcl` | Sim_Front: 입자 9(고정 3), 질량 0.166667, r 0.0, 중력 y 0.0 |
| Har_SQD012 (_F/_M) | `Har_SQD012_F.bphcl` | Center: 입자 3(고정 2), 질량 5.0, r 0.01, 중력 y 0.0; Left: 입자 7(고정 2), 질량 0.4, r 0.01, 중력 y -9.81; Right: 입자 11(고정 2), 질량 0.333333, r 0.01, 중력 y -9.81 |
| Har_SQD013 (_F/_M) | `Har_SQD013_F.bphcl` | Front_R: 입자 5(고정 2), 질량 3.333333, r 0.03, 중력 y -9.81; Front_L: 입자 5(고정 2), 질량 3.333333, r 0.03, 중력 y -9.81; Side_L: 입자 5(고정 2), 질량 3.333333, r 0.03, 중력 y -9.81; Rear: 입자 3(고정 2), 질량 5.0, r 0.0, 중력 y 0.0 |
| Har_SQD014 (_F/_M) | `Har_SQD014_F.bphcl` | Back: 입자 15(고정 5), 질량 0.5, r 0.0, 중력 y 0.0 |
| Har_SQD015 (_F/_M) | `Har_SQD015_F.bphcl` | pPlane1: 입자 7(고정 3), 질량 0.75, r 0.05, 중력 y -9.81 |

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
| ↳ 갱신(2026-10-03) | 슬롯 49 0x71026e3118 을 읽었다. 몸 `Head`·머리카락 `Head_Root` 뼈 행렬(+0x33e/+0x34a 번호)을 맞추고 모델을 갱신하는 부분이다. 천 스텝 dt·CullFrame 은 이 함수에서 보이지 않는다 [판독]. 다음: 슬롯 48 0x71026e2bdc, 50 0x71026e3728, 51 0x71026e382c 와 머리카락 +0x388(재질/애니 객체)·+0x390(0x14 B 항목 배열) |
| ↳ 갱신(2026-10-03 r6) | 슬롯 48 0x71026e2bdc = 공통 갱신 0x71026ed214 + `Har_SQD004`(전역 0x71058e8784 조건) `Back_1` 위치 +0.1·`Back_1~4` 스케일 0.01 보정, 슬롯 50 0x71026e3728 = +0x39d 에 따라 행렬을 +0x358 에 저장하거나 모델(+0x10) 루트로 넣음, 슬롯 51 0x71026e382c = 공통 0x71026ee2f8 + 애니 플래그. 세 함수 모두 천 스텝 dt 를 다루지 않는다 [판독]. **CullFrame 적용은 찾았다:** 0x71012e8ec8 이 액터의 `game__ClothCullingParam` 을 컴포넌트 +0x80 에 두고, 0x71012e9b28 이 `레코드(+0x70)+0x28 = CullFrame(파라미터 +0x30)`, `+0x2c = 0x71012571f8(전역 *0x7105827e20 +0x90, CullFrame)` 순번, `+0x34 |= 1` 로 등록한다. 플레이어 갱신 0x710243a75c 는 `전역 +0xf0 % +0x28 == +0x2c` 인 프레임에만 HairArrange 확인을 부른다 [판독]. 천 솔버(Havok hcl) 스텝이 같은 레코드로 걸러지는지, 스텝 dt 가 얼마인지는 [미확정]. 다음: 레코드 +0x28/+0x2c 를 읽는 다른 함수(`ldr [x,#0x28]`+`sdiv`+`msub` 패턴), Phive 천 월드 스텝 |
| Havok 감쇠·Bend·LocalRange 정확한 식 | SDK 내부(판독 불가 시 근사 유지) |
| TBDY flags 0x80 추가값 의미 | 다른 TAG0 파일 비교 |
| ~~다른 Har 의 상수~~ | 해소(2026-10-03): §3.3 표 [데이터]. 남은 것: 팩별 solver 설정·제약 강성 표(요약 경로 확장 필요) |


### 5.1 r9 신규 소비자 판독·호출 경계 (2026-10-03)

[cloth_frame_runtime.md §3~§11](cloth_frame_runtime.md)에서 실제 hclWorld 및 모델 프레임 경로를 추적했다. 정상 스텝 `3C0C0BC→CD3EAC`는 전달 dt×instance row48 배율, 초기화4000플래그는f32bits3D088889로30회(pre29회)다 [판독]+[실행:768/0]. 원본frameInfo writer와CullFrame4 최종solver gate,캡슐순서가남아§5의복합질문은 **부분해소/미확정유지**다. World+24의1/60을모델frameInfo+0으로동일시하지않는다.

- r9 추가(2026-10-03) [판독]+[실행:2048/0]: 실제 solver gate `0F73368`은 등록 period/phase로 frame을 걸러 `dt=f32(period*incomingDt)`를 `3DB1704`로 전달한다. bit2 또는 period<2는 unscaled 매호출, manager null은 scaled 매호출이다. `12CF69C` 뼈 후처리는 원래 incomingDt를 받는다. §5.1의 “CullFrame 최종 gate 미확정”은 이 신규 근거로 정정한다. **frameInfo writer·instance 배율 writer·capsule 순서가 남아 복합 질문 전체는 미확정 유지**. 상세 §7/§10은 [cloth_frame_runtime.md](cloth_frame_runtime.md).

### 5.2 r9 감쇠 식 해소 (2026-10-03)

고정 질문 L63의 `(1-damping)^dt` 해석을 신규 native8A63E0/DC42A0/EE41F0로 해소했다 [판독]+[실행: helper4096 + 계수/적분1024, mismatch0]. 상세 [cloth_damping_runtime.md §6~§10](cloth_damping_runtime.md). c는 damping≥1에서0, damping0에서1, 그 외 자체 f32 log/exp 다항식이다. damping=.001, effectiveDt=f32(1/60)는 bits3F7FFEE8. 적분은 `current+c*(current-previous)+dt²*((force+gravity*mass)*invMass)`의 별도 f32 연산 순서다. 기존 §4의 “globalDampingPerSecond 해석 [추정]”은 이 신규 근거로 정정한다. L79 복합 질문의 Bend/LocalRange·충돌은 여전히 미확정이다.

### 5.3 r9 저장 강성 해석 정정 (2026-10-03)

L45의 수치 해석은 새 native Standard D47BD0/Bend D1C354로 확정했다 [판독]+[실행]+[데이터]. 실제 Standard1054/Bend2060 f32bits0bad, raw SQD000 Standard30와 Bend12의 양쪽 coefficient 모두 stored×(invMassA+invMassB)=f32(1). 원본 소비자는 normal×거리오차×stored×입력scalar를 만든 후 각 endpoint invMass를 곱하며 다시 invMass 합으로 나누지 않는다. 상세 [cloth_link_runtime.md §4~§10](cloth_link_runtime.md). 기존 §3.1의 “Havok이 저장 시 미리 나누었다”는 오프라인 작성 경위의 추정을 원본 runtime의 미리 가중된 coefficient 의미로 정정한다. offline exporter 자체는 원본 배포물에 없어 작성 방법까지 단정하지 않는다. §4 Bend의 정확한 양쪽 경계·강성 식도 새 consumer로 확보했지만 L79의 LocalRange는 미확정 유지다.
