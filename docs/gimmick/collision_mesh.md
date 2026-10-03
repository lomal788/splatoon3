# 지형·파츠 충돌 메시 (Phive `.bphsh` = Havok hknpMeshShape)

목차는 [stage_gimmicks.md](stage_gimmicks.md). 표기: **[실행]** 원본 실행, **[판독]** 원본 코드/명령 판독, **[데이터]** 데이터 확인, **[재구현]** 파이썬 재구현, **[추정]**, **[미확정]**.

2026-10-02 정정: 이전 문서(stage_misc §4.3)는 본문을 "hknpCompressedMeshShape"로 추정했습니다. 태그파일의 타입 표를 읽어 보니 **`hknpMeshShape`**(Havok 2021.1의 새 메시 형식, 상대 배열 `hkRelArrayView` 사용)입니다. RomFS의 bphsh 1485개가 전부 이 타입입니다 **[데이터]**. 압축 메시(hknpCompressedMeshShape)의 섹션·공유정점 구조는 여기에 해당하지 않습니다.

## 1. 결론 요약

| 항목 | 결과 | 확정 수준 |
|---|---|---|
| 루트 형상 | `hknpMeshShape`(shape type 8) | [데이터] 타입 표 + [판독] 캐스트 디스패치 `0x71009443c4`가 type 8 = "hknpMeshShape::castShapeImpl" |
| 정점 | `(sectionOffset(s32) + u16) * bitScale16Inv` (1/512) | [판독] `0x71009372cc` + [데이터] 650개 형상의 ShapeParam `AutoCalc` bbox와 최대 오차 9.5e-7 |
| 프리미티브 | u8 a,b,c,d. c==d → 삼각형(a,b,c). c≠d·b≤d → 삼각형 (a,b,c),(a,c,d). c≠d·b>d → 평면 사각형 1개 | [판독] `0x71009372cc` |
| 삼각형 → 재질 | 프리미티브 키 `section<<9 \| prim<<1`로 shapeTagTable 이진 탐색 → shapeTag = bphsh 재질표 인덱스 | [판독] `0x710093e82c`(탐색) + [데이터] (섹션 기준 키 0/512/1024…, 태그 < 재질 수 전수 성립, 물 태그가 수면 높이 평면) |
| shapeTag → 재질·필터 | bphsh 재질표 16B 항목(MaterialCollection 인덱스, UserShapeTag 마스크), 필터표 u64(하위 32 = LayerHitMaskEntity 이름 값, 상위 32 = SubLayerHitMaskEntity 이름 값) | [데이터] (Water→`SplWater`, KeepOut→`SplKeepOutPlayer`, Fence→`SplInkThrough`/`SquidThrough`로 이름이 맞음). 엔진이 태그로 8 B 필터 행을 고르는 한 단계 `0x7103ad6a70`은 [실행] (2026-10-03, 1024/1024). 행 배열 부착은 §3.4.1 [실행] (24필드), 공통 결합은 r6 [실행], 실제 사격장 행을 탄 막음에 연결한 검증은 §3.4.2 [실행] (476건). 16 B 재질 행 reader·실제 leaf·Havok 코덱 클래스는 8차 §3.4.3 [실행]+[판독]으로 해소 |
| Yagara 변환 | 섹션 50, 프리미티브 2787, 삼각형 5103, 정점 4088, 재질 27종, bbox (-81.5,-2,-137)~(81.5,28.875,137) | [데이터]+[재구현] |

## 2. 자료와 도구

| 항목 | 위치 |
|---|---|
| 원본 | 액터 팩 `Phive/Shape/Dcc/<이름>.Nin_NX_NVN.bphsh` (지형 `Fld_<스테이지>`, 파츠 `Obj_*`, `FldObj_*`) |
| bphsh 헤더·재질표·필터표 | `web/tools/gimmick_phive.py` (헤더 구조는 [stage_misc.md §3.2](stage_misc.md)) |
| TAG0 범용 파서 | `web/tools/collision_tag0.py <x.bphsh> types` (또는 `items`) — TYPE 섹션 리플렉션(타입·멤버·오프셋)으로 DATA 해석 |
| 메시 변환 | `web/tools/collision_mesh.py <x.pack.zs 또는 x.bphsh> [--glb out.glb] [--json out.json]` |
| 전수 검사 | `web/tools/collision_scan.py --out analysis/collision/scan_all.json` |
| 산출물 | `analysis/collision/Fld_Yagara_col.glb`(134KB), `Fld_Yagara_col.json`(통계), `scan_all.json`(1485개 요약) |
| 엔진 디컴파일 | `analysis/decomp/gimmick/hknp_mesh.c`(`0x71009443c4` 캐스트 디스패치), `hknp_mesh_cast.c`(`0x7100936ee8` hknpMeshShape::castShapeImpl), `hknp_mesh_sub.c`(`0x71009372cc` 프리미티브 디코드, `0x710093e750`), `hknp_mesh_tag.c`/`hknp_mesh_tag2.c`(`0x710093e3d8`, `0x710093e82c` shapeTag 조회) |

Havok 공개 소스는 쓰지 않았습니다. 형식은 파일 안의 리플렉션 표와 main 디컴파일만으로 정했습니다(외부 출처 없음).

## 3. 형식

### 3.1 TAG0 태그파일 [데이터]

bphsh 헤더의 tagfile 오프셋(0x30)부터 Havok 태그파일입니다. 섹션 헤더 = u32 빅엔디언(상위 2비트 플래그: 0이면 하위 섹션을 가짐, 하위 30비트 크기) + 4문자 태그.

```
TAG0
  SDKV "20210100"
  DATA  객체 메모리 그대로(리틀엔디언, 포인터 8B)
  TYPE  TPTR, TST1(타입 이름 문자열), TNA1(타입 이름·템플릿 인자), FST1(필드 이름 문자열),
        TBDY(타입 본문: parent, flags, [sub][ptr][version][size,align][abstract][members (name,flags,offset,type)] [interfaces] [attr]),
        THSH, TPAD
  INDX  ITEM(12B: u32 type|flags<<24, u32 DATA 내 오프셋, u32 개수)
```

- 가변 정수(packed int): 첫 바이트 `0xxxxxxx` 1B, `10xxxxxx` 2B, `110xxxxx` 3B, `11100xxx` 4B(빅엔디언) — Yagara 타입 표 전체를 이 규칙으로 끝까지 읽음.
- `sub`(형식 플래그) 하위 5비트 = 종류(2 bool, 4 int, 5 float, 6 pointer, 7 record, 8 array), int는 0x200 부호·0x2000/0x4000/0x8000/0x10000 = 8/16/32/64비트, array에 0x20이면 고정 길이(`sub>>8`개).
- `hkRelArrayView<T,int>` = {s32 offset, s32 size}, `hkRelArray<T>` = {s64 offset, s32 size, s32 cap}. **offset은 이 필드 자신의 주소 기준**입니다(예: 루트 +0x70 shapeTagTable offset 0x30 → DATA 0xA0 = ITEM 2와 일치).

### 3.2 hknpMeshShape (Yagara 타입 표, DATA 기준 = 루트 객체) [데이터]

| 오프셋 | 필드 | 타입 | Yagara 값 |
|---|---|---|---|
| +0x18 | type | u8 | 8 |
| +0x19 | dispatchType | u8 | 3 |
| +0x1a | flags | u16 | 4 |
| +0x1c | numShapeKeyBits | u8 | 15 |
| +0x20 | convexRadius | f32 | 0 |
| +0x40 | shapeTagCodecInfo | u32 | 0xFFFFFFFF |
| +0x50 | vertexConversionUtil.bitScale16 | vec4 | 512 |
| +0x60 | vertexConversionUtil.bitScale16Inv | vec4 | 1/512 |
| +0x70 | shapeTagTable | RelArrayView<{u32 meshPrimitiveKey, u16 shapeTag}> (8B) | 255개 |
| +0x78 | topLevelTree | hkcdSimdTree {RelArray<Node 128B> nodes, bool isCompact} | 25 노드 |
| +0x90 | geometrySections | RelArrayView<GeometrySection 64B> | 50개 |

GeometrySection(64B):

| 오프셋 | 필드 | 타입 |
|---|---|---|
| +0x00 | sectionBvh | RelArrayView<hknpAabb8TreeNode 28B> (lx,hx,ly,hy,lz,hz 각 u32 = 자식 4개의 u8, data u8[4]) |
| +0x08 | primitives | RelArrayView<{u8 aId,bId,cId,dId}> |
| +0x10 | quantizedVertices | RelArrayView<{u16 x,y,z}> |
| +0x18 | interiorPrimitiveBitField | RelArrayView<u8> |
| +0x20 | sectionOffset | u32[3] (부호 있는 값으로 씀) |
| +0x2c | bitScale8Inv | f32[3] (BVH 8비트 박스용) |
| +0x38 | bitOffset | s16[3] (BVH 8비트 박스용) |

### 3.3 디코드 규칙 (엔진 판독 `0x71009372cc`)

```
// 섹션 s, 프리미티브 p = (a,b,c,d)
vert(i) = float(sectionOffset_s32 + q16[i]) * bitScale16Inv          // int 덧셈 후 scvtf, 곱
if c == d:            triangle(a,b,c)                 // 형상 정점 수 3
elif b <= d:          triangle(a,b,c), triangle(a,c,d) // 루프 2회, 키 하위 비트 0/1
else:                 quad(a,b,c,d) 평면 1개          // 형상 정점 수 4, 형상 플래그 0x400
shapeTagKey = sectionKeyBase | p<<1                    // 0x710093e3d8 → 0x710093e82c(key)
shapeTag = table[i].shapeTag  where table[i].key <= key < table[i+1].key  (이진 탐색, 표 크기 2면 항목 0)
```

- 섹션 키 기준 `sectionKeyBase`(질의 컨텍스트 +0x60) = `section<<9` **[판독 — 2026-10-02 3차]**: `0x71009372cc`가 topLevelTree 순회에서 잎(스택 값 bit0=1)을 만나면 `section = 값>>1`로 `ctx+0x60 = section << 9`, `ctx+0x68` = geometrySections[section] (루트 +0x90 상대 배열, 64 B 항목), `ctx+0x70` = 그 섹션 BVH를 기록합니다(`analysis/decomp/gimmick/hknp_mesh_sub.c` 341행). 표 키가 512 배수에서 새로 시작하는 데이터 관찰(0, 512, 1024 …)과 일치합니다. 결과로 내는 Havok 셰이프 키는 `((ctx+0x60 | prim<<1 | 삼각형) + 1) << (32 − numShapeKeyBits − 상위 비트) − 1 | 상위 키`입니다(717행) [판독].
- 마지막 항목은 키 `50<<9 | 255<<1`(섹션 수 다음), shapeTag 0xFFFF인 센티널입니다. 실제 프리미티브는 이 키에 닿지 않습니다 [데이터].
- BVH 박스: `min = (bitOffset + u8) * bitScale8Inv`. 정점이 섹션 루트 박스 안에 들어감을 확인했습니다(섹션 0: 정점 x [-28.5,-4.34], 박스 [-28.59,-4.21]) [데이터]. 웹 충돌에는 BVH를 쓰지 않고 다시 만들면 됩니다.
- interiorPrimitiveBitField (2026-10-02 3차, `web/tools/collision_interior.py`, 결과 `analysis/stage/interior_bitfield_yagara.txt`):
  - **프리미티브당 1비트**: 길이 = ceil(프리미티브 수/8)이 Fld_*·Mpt_* 166개 파일 3667개 섹션 전부 성립, 비트 i = `bits[i>>3] >> (i&7) & 1` [데이터].
  - Yagara 2787개 프리미티브 상관: 비트 1인 275개는 **전부 열린 모서리가 없음**(모든 모서리를 다른 프리미티브와 공유). 그중 254개(92%)가 "볼록 모서리 없음(이웃이 오목 쪽이거나 같은 평면)". 반대로 열린 모서리가 없고 볼록 모서리도 없는 275개 중 254개가 비트 1 [데이터].
  - 해석: **내부 프리미티브(모서리 접촉이 생길 수 없는 면) 표시 — 용접(welding) 생략용** **[추정 — 상관 92%]**. 캐스트 경로 `0x71009372cc`/`0x7100936ee8`는 이 비트를 읽지 않습니다(섹션 +0x18 접근 없음) [판독]. 접촉 생성(Phive 물리) 쪽 사용은 [bulletbody]/[physics] 소관입니다.
  - 웹: 충돌 질의 결과에는 영향이 없습니다. 모서리 걸림(ghost edge) 처리를 원본처럼 하려면 이 비트를 삼각형 속성으로 보존하세요(`collision_mesh.py`는 아직 출력하지 않음).
- topLevelTree(섹션 BVH 위 트리) 노드 형식은 순회 코드 판독(잎 = bit0, 섹션 번호 = 값>>1)까지만 했고 노드 박스 해석은 하지 않았습니다. 웹은 BVH를 새로 만들므로 필요 없습니다.

### 3.3.1 interior의 실제 이름·좁은 충돌 사용 — 8차 [데이터]+[판독]+[실행]

2026-10-03 정정: §3.3의 “내부 프리미티브 — welding 생략용 [추정]”을 **원본의 `IS_INTERIOR_TRIANGLE` 속성과 전용 interior 접촉 처리 분기**로 정정한다. 기존 상관 92% 분석은 과거 추정의 근거로 보존한다. 이것을 원본이 직접 명명한 용접 비트라고 부르거나, bit1인 모든 면에서 용접을 끈다는 규칙으로 구현하면 안 된다.

원본 hknpShape::FlagsEnum 설명자 `0x7105468380`은 이름15개(+0x10=0x7105468288)와 별도 값 포인터 배열(+0x18=0x7105468300)을 연결한다. 실제 값은 `IS_INTERIOR_TRIANGLE=0x20`, `SUPPORTS_COLLISIONS_WITH_INTERIOR_TRIANGLES=0x40`, `USE_NORMAL_TO_FIND_SUPPORT_PLANE=0x80`, `IS_TRIANGLE_OR_QUAD_SHAPE=0x200`, `IS_QUAD_SHAPE=0x400`이다. **이름의 배열 인덱스로 비트값을 추정하면 안 된다**(bit8 등의 빈칸이 있다). §3.4.3의 실제 leaf writer `0x7100997078`는 파일의 primitive bit를 형상+0x1a의0x20으로 옮긴다.

원본 hknpBodyQuality::FlagsEnum도 별도 값 배열을 가진다: `ALLOW_INTERIOR_TRIANGLE_COLLISIONS=0x8`, `ENABLE_NEIGHBOR_WELDING=0x80`, `ENABLE_MOTION_WELDING=0x100`, `ENABLE_TRIANGLE_WELDING=0x200`, `ENABLE_LIVE_WELDING=0x10`. interior 형상 속성과 welding 품질 옵션은 다른 필드다 [데이터].

실제 접촉 쌍 처리 `0x7100a5b798`의 `0x7100a5c678..68c`는 pair cache+0xa의0x8이 켜진 경우 **A형상.flags0x40 && B형상.flags0x20**가 아니면 그0x8을 지운다. 둘 다 충족하면 유지한다. 그 후 활성 다른 처리기가 없고 `(pair.flags&0x18)==0x8 && A형상.flags0x40`이면 `0x7100b230e4` interior 전용 접촉 처리를 호출한다(`0x7100a5c6e8..78c`); 음수 반환은 일반 형상 쌍 generator 테이블(world+0x13c8)에 폴백한다. 같은 gate는 `0x7100a5d6f4`에도 있다 [판독]. `0x7100b230e4`는 triangle vertex로 면 법선·평면을 만들고 A형상의 ±면 방향 support point, 분리거리·feature를 사용해 manifold/cache를 만든다. 단순히 삼각형 또는 접촉 전체를 버리는 분기가 아니다.

새 원본 gate 명령 실행 `web/tools/r8_physics_interior_gate_emu.py`: A/B 형상 flags·pairflags 랜덤 **20,000건 불일치0**. enum15+quality20 값은 원본 이미지에서 직접 읽었다. 실제 leaf 기하/bit/tag5,530건은 같은8차 §3.4.3 실행이다. 이번 gate 테스트는 원본 좁은 충돌 함수의 명령 구간만 실행했고, manifold 전체·welding modifier·솔버 전체를 실행한 것은 아니다. **원본 bit의 이름·값·producer·실제 interior 소비 경로는 확정**이며, 전체 모서리 용접/접촉 해소 알고리즘은 별도 미확정이다.

근거: `analysis/decomp/r8_physics/interior_collision_full.c`, `narrow_kernels.c`, `physics_interior_gate_emu.json`. 초기 중간주소 a5c100/a5f32c 디컴파일은 함수 경계가 틀려 폐기했고, func_lookup의 실제 시작 a5b798/a5d6f4로 다시 디컴파일했다.

### 3.3.2 topLevelTree 노드 박스·선택 — 8차 [데이터]+[판독]+[실행]

2026-10-03 정정: §3.3의 “노드 박스 해석은 하지 않았다”는 당시 상태이며, 이번에 원본 순회 `0x71009372cc`의 미판독 구간으로 해소했다. `hkcdSimdTree::Node` 128B에는 자식4개의 `lx[4]@0x00,hx@0x10,ly@0x20,hy@0x30,lz@0x40,hz@0x50`(f32), `data[4]@0x60`(u32), 공유 `isLeaf@0x70`(u8)가 있다. 루트 호출 `0x7100936ee8`은 `H+0x78` 상대 배열과 시작 노드번호1을 넘긴다(`0x7100937154`, `0x71009371e4`). 노드0은 실제 시작이 아니다.

질의 O=원점, I=역방향, E=형상 반폭, L=listener+0x10 최대 진행비율일 때 각 축에 대해 원본은 `a=f32(I*f32(f32(min−E)−O))`, `b=f32(I*f32(f32(E+max)−O))`를 만든다. **원본 `SMIN/SMAX`는 f32 비트열을 signed32 정수로 비교하는 명령이다**. 따라서 다음 `imin/imax`를 일반 float min/max로 바꾸면 안 된다. `u_axis=imin(a,b)`, `v_axis=FMAX(a,b)`, `near=imax(imax(ux,uy),imax(uz,+0))`, `far=imin(imin(vx,vy),imin(vz,L))`. 실제 판정은 `hx>=lx && far>=near`다(`0x7100937538..75dc`). 좌표·반폭·역방향 계산은 f32 단계별 반올림이며 FMA가 아니다 [판독].

4lane 유효마스크는 원본 `0x7104a841a0` TBL permutation과 `0x7104a84060` 개수표로 압축된다. 선택 lane의 `data<<1 | (isLeaf!=0)`를 스택에 넣는다. bit0=0이면 노드번호, bit0=1이면 섹션번호(`value>>1`)다. flags bit0=0은 마지막 스택 항목부터 진행하고, bit0=1은 최근 최대4개 중 near가 작은 항목을 골라 L보다 멀면 잘라낸다. §3.3의 섹션키 `section<<9`는 이 다음 분기에서 작성된다.

`web/tools/r8_physics_top_tree_emu.py`는 수정하지 않은 원본4개 메시에서 원본 함수의 **실제 노드 순회**를 실행했다. 섹션 분기 `0x710093767c` 직전에 선택번호를 수집하고 다음 top-tree 반복으로 복귀시켰다. mode0/LIFO 원본 선택 순서 **4,800건 불일치0**, 원본 near/far SIMD **41,504 f32 필드 비트 불일치0**, PLT 스텁없음. Fld_VSLobby21노드/46섹션, YagaraArea2/4, VSLobbyExterior4/7, 교차 Yagara25/50. **섹션 BVH·삼각형 TOI·충돌 솔버까지 실행한 것은 아니다**. mode1 방문 선택은 판독 수준이다.

첫 실행은 검증용 Python의 f32 overflow 변환에서68건 후 중단(원본 오류 아님). 검증용 변환을 원본의 infinity 결과에 맞춰 재실행했다. 결과 `analysis/completion/r8/physics_top_tree_emu.json`. 이로써 interior와 topLevelTree의 의미를 함께 묻던 기존 질문도 모두 해소한다. 웹 반영: 원본 노드 좌표/키/leaf를 보존하고 원본 순서 재현 시 정수 min/max 명령 차이를 보존할 것. 웹 구현파일은 변경하지 않았다.

### 3.4 shapeTag → 재질·태그·필터 [데이터]

shapeTag = bphsh 재질표 인덱스입니다. Yagara 27종 전부 태그 < 27이고, 1485개 전체에서도 재질표 범위를 벗어난 태그가 없습니다. 필터표는 재질표보다 1개 많고(28) 마지막은 0입니다.

| 필터 하위 32비트 | LayerHitMaskEntity 이름 | 상위 32비트 | SubLayerHitMaskEntity | Yagara tag 예 |
|---|---|---|---|---|
| 0x1ffffffe | SplSolidGround | 0xffffffff | HitAll | 1, 5, 6 … |
| 0x1ffffffe | SplSolidGround | 0x03fff5ff | SplSuperHookCheckThrough | 16 |
| 0x00000062 | SplKeepOutPlayer (= 플레이어만) | 0xffffffff | HitAll | 2, 3, 4, 9, 10 |
| 0x000000e2 | SplKeepOutPlayerAndCamera | 0xffffffff | HitAll | 22 |
| 0x1fffff9e | SplPlayerThrough | 0xffffffff | HitAll | 7 |
| 0x1f0cbc7e | SplInkThrough | 0x03ff75cf | SquidThrough | 0, 8 |
| 0x1bffffc6 | SplWater | 0x03bffa07 | SplWater | 14 |

이름은 `PhiveConfig`의 MaskValue와 정확히 같은 값으로 붙였습니다.

엔진 쪽 사용(2026-10-03 보완·5차) — 상세는 [../physics/character_controller.md](../physics/character_controller.md) §3.5:
- **[실행]** 형상 필터 행 선택 `0x7103ad6a70`: 형상 type 7..10 이고 정보 = 형상+0x28, 내부 메시 = 정보+0x28 이면, 잎 결과 태그 `tag & 0x1fff`가 정보+8(행 수)보다 작을 때 정보+0x10 의 8 B 행 low/high u32 를 내보낸다. 행의 low/high 가 이 표의 하위 32(Layer)/상위 32(SubLayer)에 대응한다는 것은 오프셋 배치로 본 것이다.
- **[실행]+[판독]** 정보 writer `0x7103a715b4`와 실제 bphsh 행 배열의 userData 부착은 §3.4.1. 이전 5차의 writer 미확정은 7차에서 해소(2026-10-03).
- **[실행]** 공통 쌍+형상 행 결합은 r6 `0x7103c5e244` 4096건. 탄 막음은 기존 r6 combat 경로에 원본 배열 writer를 연결한 §3.4.2 476건.

마스크 비트 대응 **[데이터]**(PhiveConfig `LayerEntityCollection` 순번: 0 NoHit, 1 CustomReceiver, 2 GameCustomReceiver, 3 Ground, 4 Water, 5 SplPlayer, 6 SplPlayerChariotShield, 7 SplCamera, 8 SplInkBullet, 9 SplInkBullet_FriendThrough, …): `SplKeepOutPlayer` 0x62 = 비트 1·5·6(CustomReceiver·SplPlayer·SplPlayerChariotShield), `SplKeepOutPlayerAndCamera` 0xe2 = 여기에 비트 7(SplCamera), `SplPlayerThrough` 0x1fffff9e = 비트 0·5·6 만 빠짐(플레이어·전차 방패만 통과). 비트가 접촉 유지/제거 및 슈터 막음 비트에 쓰이는 것은 §3.4.2 **[실행]**. 전체 기하 충돌·TOI는 §11 [미확정].

### 3.4.1 bphsh 로더 → hknpShape.userData (7차, 2026-10-03) [실행]+[판독]+[데이터]

기준 객체를 구분한다. `P` = 읽기 전용 bphsh 바이트, `O` = Phive 형상 파일 래퍼(이름은 설명용), `H` = TAG0에서 얻은 hknp 형상, `I = O+0x48` = 행 정보. writer `0x7103a715b4(O, P, 파일크기, allocator)`는 다음과 같이 쓴다. 이 함수는 형상 파일 가상함수 표 `0x7105745cf8`의 +0x18 슬롯이다. 자원 파서 `0x7103de04d0`의 객체와 `O`는 서로 다른 기준 객체다.

```text
N = min(u32(P+0x20) >> 4, u32(P+0x24) >> 3)
if N != 0:
    O+0x28 = N; O+0x30 = P + u32(P+0x10)     // 16 B 재질 행
    O+0x38 = N; O+0x40 = P + u32(P+0x14)     // 8 B 필터 행
    I+0x08 = N; I+0x10 = P + u32(P+0x14)     // 필터 reader 0x7103ad6a70
    I+0x18 = N; I+0x20 = P + u32(P+0x10)     // 재질 행 배열
    O+0x78 = 1
H = TAG0_loader(P + u32(P+0x0c), type 0x7105466738)
if H != null && i32(H+0x94) >= 1:             // hknpMeshShape 섹션 수
    H+0x28(userData) = I
    I+0x28 = H                               // O+0x70
    O+0x20 = {vtable 0x7105754e80, H}         // 16 B 래퍼, 참조 증가
```

처음 TAG0 타입 로드 실패 시 `0x7105465bb8`(hknpCompressedMeshShape)로 재시도하고 +0x68 >= 1을 확인하는 대체 경로도 있다 **[판독]**. v0 bphsh 전수 데이터는 hknpMeshShape이므로 이번 실행은 첫 경로만 검증했다. `N=0`이면 행 필드 기록을 건너뛴다는 분기는 **[판독]**, 런타임 행 정보의 영행 초기 상태는 실행하지 않았다.

| 원본 데이터 | 재질 바이트/행 | 필터 바이트/행 | 원본 writer N | 실행 |
|---|---|---|---|---|
| Fld_VSLobby | 608 / 38 | 304 / 38 | 38 | 6필드 일치 |
| Mpt_Fld_VSLobbyExterior 안 FldObj_YagaraArea | 32 / 2 | 16 / 2 | 2 | 6필드 일치 |
| Mpt_Fld_VSLobbyExterior 안 Fld_VSLobbyExterior | 16 / 1 | 16 / 2 | 1 | 6필드 일치 |
| Fld_Yagara(교차 검증) | 432 / 27 | 224 / 28 | 27 | 6필드 일치 |

따라서 Yagara 필터 마지막 0행은 `I+8`의 유효 행 수에 포함되지 않는다. 정정(2026-10-03, 7차): 6차 자원 parser의 +0x38 = 재질바이트>>3 = 54를 필터 reader 행 수로 이어 붙일 수 없었다. 실제 형상 파일 writer는 **두 배열의 행 수 중 작은 값**을 userData 정보에 저장한다. 이전의 "정보 writer 미확정"은 이 판독과 원본 실행 24/24 필드로 해소한다. 다만 7차 당시 **16 B 재질 행 reader와 Havok 코덱 클래스는 [미확정]**이었다. **8차 정정(2026-10-03): §3.4.3 새 원본 근거로 해소**했다.

### 3.4.2 사격장 행의 슈터 막음 판정 (7차) [실행]+[판독]+[데이터]

공통 탄 막음 경로 자체는 이미 r6 combat에서 4,606건으로 확정했다([../combat/hitbox.md](../combat/hitbox.md) §3, SHARED.md). 이번 신규 실행은 §3.4.1의 **원본 bphsh 로더 결과를 그대로 연결**하여 실제 사격장 행이 쓰이는지 검증한다. 기존 경로의 재실행을 신규 분석 항목으로 세지 않는다.

```text
탄 수집기 0x7103c55ed8(contact, bullet, keyA, rigid, keyB)
 → 0x7103c34e14(Fbullet=bullet+0x138, Frigid=rigid+0x180, …)
 → 그룹별 막음 표(Default +0x190 / Same +0x210 / Other +0x290)
 → 양쪽 F+0x18(상대 레이어)·F+0x1c(상대 하위 레이어) 검사
 → 0x7103c34ce8: 각 F bit28이 1이면 해당 형상의 행 검사
 → 0x7103ad658c → 0x7103ad6a70: H.userData I의 tag&0x1fff 행
모두 통과할 때 contact+0x68 |= 2
```

공통 표의 셀 값 `2`만 막음 배열에 들어가는 변환은 [../physics/character_controller.md](../physics/character_controller.md) §3.5.1의 원본 BYML 실행으로 확정했다. bit28=0이면 형상 행을 검사하지 않으며, bit28=1인데 행 찾기가 실패하면 low/high를 0xffffffff로 두는 분기는 **[판독]**이다. 복합 형상(IsA `0x7105553a08`)은 직접 +0xb8/+0xbc를 검사한다; 원본 bphsh 표본은 일반 메시 행 경로로 검증했다.

검증 입력: 위 4개 bphsh의 유효 68행 × `(레이어,하위레이어)={(8,0),(9,0),(5,3),(5,4),(5,5),(5,6),(7,0)}` = **476건, 불일치 0**. 비교 그룹은 양쪽 1, 몸체의 F+0x18/+0x1c는 0xffffffff, 지형 F bit28=1이다. 기대값은 실제 bphsh low/high와 원본 BYML에서 만든 막음 표로 별도 계산했다.

| 사격장 Fld_VSLobby 행 | 실제 u64 행 | 레이어8 슈터의 contact bit1 | 결론 |
|---|---|---|---|
| 태그 1·2·25·33, SplKeepOutPlayer | 0xffffffff00000062 | 0 | 이 행은 슈터 탄을 막는 접촉을 만들지 않음 |
| 태그 23, SplPlayerThrough | 0xffffffff1fffff9e | 1 | 이 행은 슈터 탄을 막는 접촉을 만듦 |

Yagara의 KeepOut/FillUp 태그 2·3·4·9·10도 bit1=0, PlayerThrough 태그7은 bit1=1로 대조했다. 플레이어(레이어5) 결과는 기존 r6 매니폴드 행 결합식과 같은 비트 규칙이다: KeepOut 행은 접촉 유지, PlayerThrough 행은 접촉 제거. 이 문장의 "막음"은 **기하 접촉이 주어진 뒤의 필터·접촉 플래그 결정**을 뜻하며 실제 스윕 TOI·Havok 솔버의 침투 해소 전체를 실행했다는 뜻이 아니다.

정정(2026-10-03, 7차): 6차에서 탄 막음 출처 후보로 적은 `0x7103c39158`은 `0x7103c38b08`의 일반 질의 접촉 생성 분기다. 실제 탄 바디의 막음 경로는 위 `0x7103c55ed8 → 0x7103c34e14`이며, r6 combat의 기존 확정 결과와도 일치한다.


### 3.4.3 실제 메시 잎·16 B 재질 reader·월드 코덱 (8차, 2026-10-03) [실행]+[판독]

**정정 이유:** 7차는 Havok 잎 태그를 스텁으로 공급했다. 8차에서 원본 메시 잎 함수와 게임의 16 B 재질 reader, 실제 월드 코덱 생성자를 찾았으므로 “16 B reader·코덱 구현 클래스 미확정”을 해소한다. 기하 쓸어 넘기기·TOI·솔버 전체를 확정한 것으로 확대하지 않는다.

기준 객체 `H`·`I`·`P`는 §3.4.1과 같다. 새 reader `0x71012ac5e0(PhiveShape, &key)`는 일반 형상에서 shape vt+0x70 → hknp 래퍼 vt+0x10 → `H`를 얻는다. `H.type==12`인 복합 형상은 key 상위 비트로 64 B 자식 항목(+0x48 상대 배열, 자식+0x30 상대 포인터)을 고르고 자식 key를 `(key+1)<<numBits − 1`로 바꾼다. 일반 메시에서는 `0x71012acb38(H, &key)`를 부른다.

```text
12acb38: H.type in [7,10], key != 0xffffffff, H.userData I != null, I+28 != null
  leaf = 원본 getLeafShapes(I+28, &key, 1)
  index = u16(leaf+0xbf8) & 0x1fff
  return index < i32(I+0x18) ? ptr(I+0x20) + index*16 : null
12ac5e0: 위 reader가 null이면 PhiveShape.vt+0x18 기본 재질을 반환
3c5606c: 12ac5e0(shapeA,keyA)의 16 B → contact+0x38/+0x3c/+0x40
          12ac5e0(shapeB,keyB)의 16 B → contact+0x48/+0x4c/+0x50
```

마지막 접촉 복사는 새 `0x7103c5606c` 원본 명령 **[판독]**이다. raw 배열을 반환하는 pointer/16 B 바이트는 아래 원본 실행으로 확인했다. type15 복합 Phive 형상의 `0x71012ac76c`도 디컴파일했고, 20 B child tag 정보의 base material 인덱스를 자식 mesh tag&0x1fff에 더한 뒤 16 B 행을 고른다 **[판독]**. 사격장 raw mesh 실행은 일반 type8 경로다.

**실제 Havok 잎:** `0x710093149c`가 디스패치 배열을 초기화한다. 소유 객체 `D`에 대해 이 함수의 인자는 `D+0x18`(`0x7100932f64`, `0x7100933024/3088/3298` 명령). 따라서 `D+8*0x200+0xc0` = mesh leaf `0x7100997078`. 앞서 slot+0xc0 후보로 본 `0x7100b1c720`은 초기화 배열의 기준 +0x18을 놓친 잘못된 후보였으며 실제 reader에 연결하지 않았다.

`0x7100997078(H,&key,n,result)`는 `localKey = key >> (32-H.numShapeKeyBits)`, section=`localKey>>9`, primitive=`(localKey>>1)&255`, triangle=`localKey&1`을 사용한다. 섹션의 상대 배열에서 원본 4개 정점 번호와 u16 정점을 읽고 `(s32 sectionOffset + u16)*bitScale16Inv`로 세 정점을 만든다. `0x710093e82c(H,localKey)`의 원본 tag 이진탐색 결과를 result+0xbf8에 쓴다. 16 B 재질 reader와 기존 8 B 필터 reader는 동일 leaf tag의 하위13비트 행을 각각 stride16/8로 선택한다.

**월드 코덱·필터 클래스 [판독]:** 하위 월드 생성 `0x7103ac6a20 → 0x7103c4579c`가 label `WorldShapeTagCodec`, 크기0x20, vt `0x7105755ee8` 객체를 하위 월드+0xd0에 설치하고 Havok 월드 vt+0x60으로 전달한다. 코덱 vt+0x40 = `0x7103c49f00`은 **RET 한 명령**이며 query decode 호출에서 출력 구조를 바꾸지 않는다. 재질 행을 해독하는 함수로 이 슬롯을 해석했던 기존 가정은 철회한다. Entity의 `CollisionFilterBackEnd`(0x28 B, vt `0x7105756560`)는 하위 월드+0x110, provider는 +0x20에 있다. vt+0x40 = `0x7103c570c4`는 query kind·양쪽 순서에 따라 `3c57608/3c5780c/3c57b00/3c5746c`로 분기한다. 이들 함수는 `3c57d04 → 3ad6a70`로 형상 행을 얻고 query layer/sub 비트와 AND한다; kind별 제외 목록·type15 child 규칙도 해당 함수에 분리되어 있다. 몸체 쌍 매니폴드의 공통 표+양쪽 마스크+shape override AND는 기존 r6 확정식을 그대로 따른다.

**새 원본 실행:** `web/tools/r8_physics_material_leaf_emu.py`, 결과 `analysis/completion/r8/physics_material_leaf_emu.json`. 원본 bphsh DATA의 상대 배열·geometry·tag table를 그대로 메모리에 놓고, 정보 I만 §3.4.1 writer 명세대로 연결했다. 디스패치 초기화·leaf·tag 이진탐색·16 B reader를 원본 명령으로 실행했다.

| 실제 파일 | 전수 triangle key | 재질 유효 행 | key bits |
|---|---:|---:|---:|
| Fld_VSLobby | 5480 | 38 | 15 |
| FldObj_YagaraArea | 42 | 2 | 11 |
| Fld_VSLobbyExterior | 872 | 1 | 12 |
| Fld_Yagara (교차 검증) | 5103 | 27 | 15 |

재질 pointer/바이트·invalid key 기본재질 **11505건 불일치0**; 잎 tag·interior flag·삼각형 정점 **5530건**, 정점 f32 **49770필드 불일치0**. 원본 데이터와 독립 TAG0 파서·메시 decoder의 결과를 비교했다. 스텁은 Phive 래퍼의 type/get-H/default-material 가상함수뿐이며 leaf/tag 공급 스텁은 없다. PLT 미구현 스텁0. TAG0 loader, broadphase/cast, TOI, solver, 실제 프레임의 geometry 접촉 생성은 이 실행에 포함하지 않았다.

interiorPrimitiveBitField의 실제 consumer 첫 단계도 여기서 새 확인했다: 원본 leaf가 section+0x18 상대 비트 배열에서 primitive의 bit를 읽어 leaf flags(+0xb90) **0x20**으로 전파한다. “캐스트 경로에 없어 consumer 미발견”은 이 단계까지 정정한다. 해당 flag가 최종 용접을 생략하는 규칙은 아직 [미확정]; 별도 §11에 다음 소비자를 기록한다.

### 3.4.4 사격장 배치 액터의 FillUp 사용 여부 (9차, 2026-10-03) **[데이터]**

기존 §4의 FillUp 태그2/9/10은 **교차 검증용 Fld_Yagara의 데이터**이다. 이를 Lby_Lobby00 사격장 데이터로 읽으면 안 된다. 새 `web/tools/r9_physics_fillup_range_data.py`는 원본 `LobbyVersus.pack`에서 이미 추출한 `Banc/Lby_Lobby00.bcett.byml`의 **배치 액터257개/고유Gyaml48개**와 연결된 원본 Actor pack48개를 읽었다. `Work/Actor/Mpt_Fld_LockerEditBG.engine__actor__ActorParam.gyml`처럼 경로로 기록된 Gyaml도 같은 원본 ActorParam basename의 팩으로 해석했다.

그48팩의 **bphsh14개/재질행59개**, Phive BYML118개를 전수 읽은 결과, UserShapeTagMaskCollection의 **FillUp=0x10000000(bit28)**을 포함한 재질행과 FillUp 문자열을 사용하는 Phive 파라미터는 **모두0개**였다. 누락팩/파서오류0. 결과 `analysis/completion/r9/physics_fillup_range_data.json`에 팩·파일·행수·오류 목록을 보존했다. 물리body의 flags bit28(형상 필터 검사)과 UserShapeTag FillUp bit28은 서로 다른 기준 객체의 비트이다.

이 결과는 **그 배치 액터/팩의 데이터 범위에서 FillUp이 사용되지 않음**을 확정한다. 씬 실행 후 동적으로 추가되는 모든 형상까지 부재를 증명한 것은 아니며, 정적인 bphsh/Phive 파라미터에서 Map author가 어떤 목적으로 이름을 붙였는지도 복원하지 않는다. 기존 Yagara의 수직면·필터 규칙은 기존 근거로 유지하지만, “구멍 메우기”라는 authoring 목적은 여전히 **[미확정]**이다. exact FillUp 문자열 xref에서는 독립 소비자가 없었고 UserShapeTag enum 목록에만 있었다. 별도의 타워 `Top,Ride,FillUp` enum/FillUpType 문자열은 다른 원본기능이므로 이 UserShapeTag의 이름 설명으로 사용하지 않았다. 다음 근거는 원본 맵 작성 주석/metadata 또는 UserShapeTag bit28을 의도적으로 소비하는 별도 액터/씬 생성 경로이며, 현재 자료에 author의 목적 설명은 없다.

### 3.4.5 FillUp의 실제 접촉 후보 처리 (9차, 2026-10-03) **[판독]+[실행: 분류 블록]**

새 [fillup_contact_runtime.md](../physics/fillup_contact_runtime.md) §3~11은 원본 `24f8f58`의 최고 높이 접촉→재질행+8 UserShapeTag→`24f91a8` bit28 소비를 확정한다. FillUp 또는 `0x100004=Water|Slide` 태그는 일반 성공을 그대로 반환하지 않고 수평각도 ±1.3962634의 fallback에 들어가며, 같은 위치(delta0)는 false다. `0x8200000=Fence|KeepOut`은 높이−.35 후 재질의를 수행한다. 이것은 기능적으로 확인된 소비 규칙이며 author가 “구멍 메우기”를 의도했다는 근거는 아니다.

원본 분류 block **4096사례/28672필드 비트 불일치0**. 원본 정적 writer `24f0c84..94`부터 normal guard G58bc7a0=`0x3f24360c`를 공급한다. 첫2196 참조 불일치는 BSS 초기0을 실행 후 static 값으로 오해한 실패였으며 firstfailure JSON을 보존했다. null/auto/PLT/fault0. 상위 전 수명·실제 사격장 동적생성 및 작성 목적은 미확정이고, 정적 사격장48팩 부재 결과는 §3.4.4 범위대로 유지한다.

### 3.4.6 FillUp 대체 위치·실제 caller (r9, 2026-10-03) **[판독]+[실행: query입력 공급]**

[fillup_fallback.md](../physics/fillup_fallback.md) §3~11:원본24f8f58 전체→24f9384±80°초기+3이분→원본12d8dcc array/linked iterator의 제어·식·출력은새6144사례/189734필드독립bit0bad다. Nativequery결과는명시된합성입력공급이며geometryhit증거로확대하지않는다. helper에는normal/tag검사가없고초기querytrue일때후보모두제외돼도true/좌표보존,양쪽각도동률음수선택. linked는contact68bit8필수,array는불필요. 앞방향70query caller24f99b4도Water|Slide|PlayerDead|KeepOut|FillUp를제외하는실제mask18300004가있다[판독]. 작성목적과Lby정적48팩FillUp0범위는기존미확정/데이터구분유지.

### 3.4.7 FillUp 프리셋·원본 저작 데이터·형상 공급 연결 (r9, 2026-10-03)

**[데이터]+[판독]+[실행: 정수 등록]** [fillup_preset_runtime.md](../physics/fillup_preset_runtime.md) §3~11은 원본 `3b0f3d8` 로더의 태그49/Entity마스크50/프리셋108×10=1,179정수필드0bad를 확인했다. `FillUpPlayer[61]`은 tag`0x10000000`/유효1, Entity`0x62`/유효1이며 나머지 layer선택은0/미지정이다. allocator/state fixture와 무관powf handler 경계는 해당 문서§10에 명시했다.

**[데이터]** [fillup_authored_data.md](fillup_authored_data.md) §4~6은 원본 Actor/Scene3,679팩, bphsh1,485개/재질3,017행에서 FillUp39행/28액터팩/19고유형상을 기록했다. BYML40,020개는 문자열 byte검사 수이며 전부 구조 파싱했다고 확대하지 않는다. 태그가 있는 원본 면에는 수직뿐 아니라 경사·위향·아래향이 있으며 §4의 이전 수직 단정은 아래 날짜 정정으로 철회한다. [fillup_dynamic_sources.md](../physics/fillup_dynamic_sources.md)는 Lby48root+플레이어/슈터5root의 상속·예약·Bootup 포함 원본 리소스 closure와 실제 `10036a8→3a49c44→3a513d0` 프리셋 소비 경로를 기록한다.

정정(2026-10-03, §3.4.4의 이전 설명 보존): “타워 enum/FillUpType이 다른 원본기능”이라는 사실을 모든 타워 형상과 UserShapeTag가 무관하다는 뜻으로 사용하면 틀린다. 원본 `Gachiyagura2M/3M/4M`의 ControllerSet FillUp→`Gachiyagura_FillUp` body→`Vlift_FillUpP.phsh`는 실제 bit28 재질행을 쓴다. Rail의 FillUpType 상태와 tag의 의미를 임의로 합치지 않되, 이 실제 형상 연결은 확정한다. “수직면 규칙 유지”라는 §3.4.4의 이전 문구도 §4의 아래 정정을 우선한다. 제작자가 왜 그 이름을 붙였는지는 확인되지 않았으며 L148 전체확정 승격은 없다.

## 4. Yagara 결과 (`analysis/collision/Fld_Yagara_col.json`) [데이터+재구현]

삼각형 5103(삼각형 프리미티브 471 + 삼각형 쌍 2316×2, 평면 사각형 0), 퇴화 삼각형 0. bbox는 ShapeParam `AutoCalc` Min/Max와 정확히 같습니다.

| tag | 재질 | UserShapeTag | 필터(Layer/Sub) | 삼각형 | 면적 | 위향 면적 | y 범위 |
|---|---|---|---|---|---|---|---|
| 0 | Fence | Fence | SplInkThrough/SquidThrough | 464 | 662.7 | 95.5 | 1.5~17.8 |
| 1 | Vinyl | | SplSolidGround | 770 | 2249.4 | 1439.3 | 1.5~22.1 |
| 2 | Undefined | FillUp | SplKeepOutPlayer | 114 | 164.0 | 0 | 2.1~18.5 |
| 3 | Vinyl | KeepOut | SplKeepOutPlayer | 36 | 117.2 | 0 | 18.0~18.5 |
| 4 | Undefined | KeepOut | SplKeepOutPlayer | 140 | 165.0 | 0 | 6.9~18.5 |
| 5 | Stone | | SplSolidGround | 2060 | 11798.2 | 7101.7 | -1.5~26.1 |
| 6 | Plastic | | SplSolidGround | 393 | 157.4 | 81.1 | 4.5~16.1 |
| 7 | Stone | | SplPlayerThrough | 20 | 28.6 | 28.6 | 6.0~15.0 |
| 8 | RopeNet | Fence | SplInkThrough/SquidThrough | 12 | 32.6 | 4.8 | 13.5~15.3 |
| 9 | Vinyl | FillUp | SplKeepOutPlayer | 20 | 13.2 | 0.3 | 13.5~16.1 |
| 10 | Plastic | FillUp | SplKeepOutPlayer | 29 | 8.5 | 0.3 | 6.0~9.0 |
| 11 | Wood | | SplSolidGround | 66 | 317.5 | 317.1 | 4.5~16.0 |
| 12 | Metal | IgnoredByMiniMap | SplSolidGround | 100 | 53.1 | 53.1 | 1.5~13.5 |
| 13 | Wood | IgnoredByMiniMap | SplSolidGround | 250 | 225.7 | 225.7 | 1.5~15.1 |
| 14 | Water | Water, BombDead, TripleTornadoDeviceDead | SplWater/SplWater | 24 | 44662.0 | 44662.0 | **-0.05 평면** |
| 15 | Metal | | SplSolidGround | 82 | 61.6 | 33.8 | 1.5~13.8 |
| 16 | Undefined | BombDead, TTDDead, PlayerDead, KeepOut | SplSolidGround/SplSuperHookCheckThrough | 359 | 11437.4 | 2515.9 | -2.0~28.9 |
| 17~20 | Vinyl/Plastic/Stone/Wood | ForceColPaintNotPaintable | SplSolidGround | 8/8/8/4 | | | 7.5~13.5 |
| 21, 25, 26 | Stone/Wood/Metal | ForceColPaintPaintable | SplSolidGround | 2/8/8 | | | 13.5~13.8 |
| 22 | Undefined | BombDead, TTDDead, KeepOut | SplKeepOutPlayerAndCamera | 102 | 4077.8 | 0 | -1.5~14.0 (벽) |
| 23, 24 | Wood/Metal | ForceColPaintYPlus | SplSolidGround | 8/8 | | 0 | 10.5~10.6 |

관찰(데이터 해석):
- 물(14)은 맵 전체(163×274)를 덮는 y=-0.05 평면 24개 삼각형입니다. 그래픽 수면 `OceanHeight 0.0`과 0.05 차이 [데이터].
- 이전 설명(2026-10-03 정정 대상): “`FillUp`(2, 9, 10)과 `KeepOut`(3, 4)은 필터가 `SplKeepOutPlayer`이고 위향 면적이 0인 수직 벽입니다.” 필터 하위 32비트 0x62 의 레이어 비트는 CustomReceiver·SplPlayer·SplPlayerChariotShield 뿐입니다 **[데이터]**(§3.4). 레이어5 플레이어 접촉 유지, 레이어8·9 잉크탄의 막음 비트0은 §3.4.2의 **[실행]+[판독]+[데이터]**로 확정합니다. "구멍 메우기"라는 용도 해석은 이름 외 근거가 없으므로 **[미확정]**으로 남깁니다(기존 [추정]을 2026-10-03에 명시적 미확정으로 정정; 필터 동작과 이름의 목적은 별개).
- 정정(2026-10-03, 원본 형상 재계산): 위 “위향 면적0·전부 수직”은 잘못된 일반화다. 기존 표도9/10에위향0.3을 기록하고 있었으며 새 원본 geometry결과는 Yagara tag9위향0.345, tag10위향0.310, tag2 법선Y범위−0.0745~+0.4406이다. 다른 맵의 Slide|FillUp 경사 위향과 타워 위/아래향도 확인했다([fillup_authored_data.md](fillup_authored_data.md) §6). **필터0x62·플레이어/탄의 접촉 유지 규칙은 별도 근거로 유효**하며, 형상 방향/작성 목적을 필터에서 추정하지 않는다.
- 7번(Stone, `SplPlayerThrough`)은 수평 면이고, 필터 하위 32비트 0x1fffff9e 는 SplPlayer·SplPlayerChariotShield(와 NoHit) 비트만 뺀 값입니다 **[데이터]**. 플레이어 접촉은 제거하고 잉크탄(레이어8·9)의 막음 비트는 켭니다 **[실행]+[데이터]**(§3.4.2). 정정(2026-10-03): 이전 "엔진 결합 방식 미확정"은 r6 결합식과 r7 원본 배열 부착 실행으로 해소했습니다.
- 좌우 x, z 범위가 전부 원점 대칭이라 점대칭 맵 구조와 맞습니다.

## 5. 검증

| 검사 | 종류 | 결과 |
|---|---|---|
| 정점 디코드 ↔ ShapeParam `AutoCalc` Min/Max | [데이터] `collision_scan.py` | 단일 메시 팩 650개 비교, 최대 차 9.5e-7 |
| 1485개 bphsh 전부 hknpMeshShape로 풀림, 태그 < 재질 수 | [데이터] | 오류 0 |
| 섹션 BVH 루트 박스 ⊇ 정점 | [데이터] | 표본 섹션 0, 1, 2, 47, 49 |
| 표시 모델(`Fld_Yagara.bfres` 안 모델 `Fld_Yagara`, 85 셰이프)과 거리 | [데이터] 임시 C#(BfresLibrary)로 정점 추출 | 충돌 정점 300개 → 표시 표면 거리 중앙값 7mm, 90% 0.19, 99% 2.6 |
| 사각형 분할 대각선 | [판독] `0x71009372cc` + [데이터] | 피라미드 지붕(섹션 2 프리미티브 105·108)이 (a,b,c),(a,c,d)로 네 면이 닫힘. 경계 모서리 a-c 분할 1227 vs b-d 1235 |
| 평면 사각형(b>d) | [데이터] | Yagara 0개, RomFS 1485개 전체(삼각형 998,793)에서도 0개 — v0 데이터에는 이 경로가 쓰이지 않음 |

원본 전체 기하 충돌 쿼리·TOI는 실행하지 않았습니다. 필터/접촉 비트 및 원본 배열 writer만 §3.4.1~2·§10에서 실행 대조했습니다.

## 6. 웹 포팅

```
사전 변환(빌드 단계):  collision_mesh.py <Fld_X.pack.zs> --glb Fld_X_col.glb
  glb: 노드 1개 "collision", 메시 primitive = shapeTag별 1개
       primitive.extras / material.extras = { shapeTag, material, userShapeTagMask, userShapeTags[], filter{layerHitMask, subLayerHitMask} }
       좌표는 원본 그대로(Y 위, 단위 = 게임 단위). 정점은 섹션 간 공유 안 함(원본처럼 섹션별)
런타임:
  StageCollision.load(glb) → 삼각형 배열 + 삼각형별 shapeTag
  query(ray|sphere|capsule, layerMask) → 맞은 삼각형의 shapeTag → {material, tags, filter}
     필터: 쿼리 레이어 비트가 삼각형 layerHitMask 에 없으면 통과(예: 플레이어는 SplInkThrough 면을 통과 못 하고 잉크는 통과)
  도색: tags 의 ForceColPaint* 와 [paint] 규칙
  사망/장외: PlayerDead, KeepOut, Water 태그 → [player]/[combat] 규칙
```

- 웹 권장 이름(`StageCollision`, `query`)은 원본 이름이 아닙니다.
- 원본과 같게 유지할 것: 정점 양자화 결과(1/512 격자), 삼각형 분할 (a,b,c),(a,c,d), 삼각형별 태그. 평면 사각형(b>d)은 원본이 볼록 사각형 1개로 처리하므로 웹에서 두 삼각형으로 나눠도 같은 면입니다.
- 레이어 필터 비트의 의미(어느 쿼리가 어느 비트를 쓰는지)는 [physics]/[combat] 문서를 따릅니다.
- 파츠(`Mpt_*`, `Lft_*`, `Obj_*`)도 같은 도구로 변환됩니다(전부 hknpMeshShape). 대형 출력은 Yagara 지형 1개만 저장했습니다.

## 7. 미확정

| 항목 | 필요한 것 |
|---|---|
| 섹션 키 기준(`+0x60`) 계산 코드 | **해소 [판독]** §3.3: 잎 순회에서 `section << 9` |
| shapeTag → bphsh 재질표 조회 코드(Phive 쪽) | **해소 [실행]+[판독]**(8차 §3.4.3): `12ac5e0→12acb38→0997078`, tag&0x1fff stride16. 코덱 `WorldShapeTagCodec` vt5755ee8+40=RET |
| interiorPrimitiveBitField·topLevelTree 의미 | 비트필드 = 프리미티브당 1비트 [데이터], 내부 프리미티브 표시 [추정 — 상관 92%]. 사용 코드(접촉·용접)는 캐스트 경로에 없음. 5차에서도 읽는 코드를 찾지 못함 → 좁은 단계 처리기 표 `0x7105756468` 4종과 메시 접촉 생성에서 섹션 +0x18 읽기 확인 필요 |
| 필터표 → 충돌 필터 적용 | **해소 [실행]**: r6 공통+형상 결합, r7 원본 bphsh 배열 writer와 사격장 행 탄 막음 연결. [../physics/character_controller.md](../physics/character_controller.md) §3.5.1~2, 이 문서 §3.4.1~2. Havok 태그 코덱은 별도 미확정 |

### 6차 갱신 (2026-10-03, r6 physics)

| 항목 | 결과 | 수준 |
|---|---|---|
| 필터표 → 충돌 필터 적용 | 결합식 `0x7103c5e244`: bit28 몸체는 삼각형 행 low/high 에 상대 레이어·하위 레이어 비트가 있어야 접촉 유지, 그 뒤 공통 쌍 필터 AND. 4096/4096 원본 실행([../physics/character_controller.md](../physics/character_controller.md) §3.5) | [실행] |
| 지형 bit28 | 물리 구성요소 초기화 `0x71012e9914` → functor slot0 `0x71012ea8c4`가 레이어 3(Ground) 몸체에 bit28 = 1(태그 `Actor_MapParts_KeepOut`/`Actor_Lift_KeepOut` 액터 제외) | [판독] |
| bphsh 자원 파서 | 자원 vtable `0x7105765ad8` 슬롯5 `0x7103de04d0`: 헤더 "Phive\0\1\0", BOM 0xfeff, tagfile = base+[0xc]; 자원+0x30 = base+[0x10] (재질표), +0x38 = [0x20]>>3, +0x40 = base+[0x14] (필터표). Yagara: [0x20] = 0x1b0 → 54(필터 행 28개보다 큼, 태그 ≤ 26 이라 영향 없음). `gimmick_phive.py`의 0x18~0x24 필드 이름(end/tag/mat/flt)은 [0x18] = 파일 크기, [0x1c] = tagfile 크기, [0x20] = 재질표 크기, [0x24] = 필터표 크기로 읽는 것이 실제 값과 맞음 | [판독]+[데이터] |
| 정보 객체(hknpShape.userData, +0x28) writer | 자원 필드와 정보 객체(+8 행 수, +0x10 행, +0x28 메시)를 잇는 코드 [미확정]. 자원 크기 0x48 이라 정보 = 자원+0x30 은 아님 | 다음: 자원 +0x38/+0x40 reader |
| FillUp/KeepOut(플레이어만 막음), Stone PlayerThrough | 플레이어 쪽: 결합식 [실행]+bit28 [판독]로 KeepOut 행은 플레이어 접촉 유지, PlayerThrough 행은 끔. 탄 쪽: 막는 접촉 비트 `0x7103c39158` [판독], 호출 사슬 [미확정] | [미확정, 부분] |
| 용접 비트 | 6차 미착수 | [미확정] |

## 8. 다른 기능과의 상호작용 (7차 보강)

플레이어 지지 판정은 접촉의 레이어3·막음 bit1·16 B 재질 정보를 읽는다([../physics/character_controller.md](../physics/character_controller.md) §6). 슈터 탄은 막음 bit1 접촉의 가장 작은 f에서 멈추고, 게임 쪽 지형 명중 콜백에서 도색·이펙트로 이어진다([../physics/phive_controller.md](../physics/phive_controller.md) §6.4~6.5). 이 순서를 필터 통과 여부와 구분해야 한다.

## 9. 웹 포팅 구조와 구현 순서 (7차 보강)

웹 반영 필요: `impl/physics.md`의 플레이어-표적 근사 충돌과 지형 쿼리 필터를 구분하고, 지형 행 low/high와 양쪽 몸체 마스크·그룹별 막음 표를 함께 검사한다. `impl/physics.md`는 이번에 수정하지 않았다. 헤더의 재질/필터 크기는 각각 16/8로 나누고 둘 중 작은 값을 유효 행 수로 쓴다. PlayerThrough를 이름 때문에 탄까지 통과시키거나 KeepOut을 모든 레이어 벽으로 취급하면 원본 필터와 다르다. 재질·코덱·TOI의 미확정은 구현 가정으로 분리한다.

## 10. 검증 코드·실행 결과·기대값 (7차)

- `web/tools/r7_physics_mesh_emu.py`: 원본 `0x7103a715b4` + 실제 bphsh 4개, 행 수·재질 포인터·필터 포인터·userData·내부 형상 부착 **24/24필드 일치**. 이어 기존 확정 탄 필터 함수를 원본 연결해 **476/476 bit1 일치**. 결과 `analysis/completion/r7/physics_mesh_emu.json`.
- 스텁: 메모리 할당, TAG0 객체 로드/타입 검사/문맥 정리, 형상 가상함수에서 원본 부착 결과 포인터 반환, Havok 잎 결과에 선택 shapeTag 공급, 타입 검사, 뮤텍스 PLT. 실제 원본 bphsh 바이트와 행은 변경하지 않았다. 원본 할당 참조 증가·필터 계산·행 reader 명령은 실행했다. 실제 프리미티브 스윕과 TOI는 검증하지 않았다.
- 명령과 실패 기록: `analysis/completion/r7/physics_commands.md`. 디컴파일: `analysis/decomp/r7_physics/mesh_attach.c`, `bullet_mesh_filter.c`(탄 공통 경로는 r6 combat 확정 근거 재사용).

## 11. 미확정 사항과 추가 분석에 필요한 근거 (7차)

| 미확정 | 이번 시도와 막힌 이유 | 다음에 볼 곳 |
|---|---|---|
| shapeTag → 16 B 재질 행 reader | userData의 I+0x18/0x20에 원본 행 부착은 확정. 필터 reader만 원본 연결 실행했으므로 접촉 +0x38/+0x48 재질 복사를 확정하지 않음 | 코덱/접촉 생성의 I+0x18 개수·I+0x20 포인터 reader, `0x7103c51de0`, `0x7103b02470` |
| Havok shapeTag 코덱 구현 클래스 | `0x7103b1b33c`는 0x38 관리자와 큰 하위 버퍼 생성(명령 판독), `0x7103a72c28`도 형상 생성 경로라 코덱으로 단정할 근거 없음. 이번 실행에서 잎 태그를 공급했기 때문에 실제 코덱 해독은 미검증 | 쿼리 +0x130 [0] vt+0x40, 월드+0xd0 writer를 역추적 |
| interiorPrimitiveBitField·용접·TOI | 필터 행 연결로는 기하 결과를 증명할 수 없음. 이번에 좁은 단계 내부를 실행하지 않음 | `0x7105756468` 처리기, `0x71009af088`, 섹션 +0x18 reader |
| FillUp 이름의 "구멍 메우기" 목적 | 문자열과 수직 면·필터 데이터는 있으나 원본에서 그 목적을 나타낸 호출/주석 없음. 임의 해석으로 채우지 않음 | 액터·맵 작성 데이터의 FillUp 태그 소비자 |

8차 §10 보강(2026-10-03): 신규 실행·스텁·기대값은 §3.4.3 표와 `r8/physics_material_leaf_emu.json`; 명령·실패는 `r8/physics_commands.md`.

8차 §11 정정: 16 B 재질 reader·WorldShapeTagCodec 클래스 두 행은 §3.4.3으로 해소. 남은 실제 용접은 `0997078`가 생산하는 leaf flags0x20의 소비(접촉 manifold/triangle-welding), TOI는 `09af088`, 침투 솔버는 `09cec84`. 넓은 단계·쓸어 넘기기를 실행하지 않았으므로 그 질문은 그대로 미확정이다.

2026-10-03 8차 추가 정정: interiorPrimitiveBitField를 원본 형상IS_INTERIOR_TRIANGLE=0x20·ALLOW_INTERIOR_TRIANGLE_COLLISIONS=0x8 경로로 확정했다(§3.3.1). 이전welding생략추정은 원본 이름이 아니며 그 추정을 적용해서는 안 된다. topLevelTree 노드 박스 해석과 전체용접은 별도미확정으로 유지한다.

9차 §10 추가: `r9_physics_fillup_range_data.py` exit0, 팩48/충돌형상14/재질행59/Phive BYML118 전수 읽기, FillUp행·파라미터0,누락·오류0. 첫 검사에서 Gyaml 경로1개를 팩명 그대로 찾아 누락했으나 원본 ActorParam basename 규칙으로 정정하여48팩을 모두 읽었다. 원본 함수/solver 실행이 아닌 데이터 전수검사다.

9차 §11 정정: FillUp 목적 질문(L148)은 현재 범위의 배치 팩에서 태그를 사용하지 않는다는 새 데이터로 좁혔지만 authoring 목적은 확정하지 않는다. 따라서 미확정 상태를 유지한다. 추측으로 미확정 값을 채워 완료 수를 늘리지 않는다.

2026-10-03 r9 최종 정정(§11): 위의 과거 FillUp 질문 표에서 “수직 면”은 작성 의도의 근거가 될 수 없고 원본 geometry의 반례도 있다. 실제 tag 생성/형상 소비·접촉/fallback 처리와 릴리스의 전수 데이터 검사까지 시도했다(§3.4.5~7). 역사적 이름의 목적을 설명한 원본 주석/metadata가 없으므로 **[미확정]**으로 남긴다. 다음 근거는 원본 DCC 저작 소스·exporter 주석·제작자의 해당 태그 설명이다. 임의 runtime 모든 쓰기 부재나 모든nativequery/solver를 이번 결과에서 승격하지 않는다.
