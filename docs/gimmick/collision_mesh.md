# 지형·파츠 충돌 메시 (Phive `.bphsh` = Havok hknpMeshShape)

목차는 [stage_gimmicks.md](stage_gimmicks.md). 표기: **[실행]** 원본 실행, **[판독]** 원본 코드/명령 판독, **[데이터]** 데이터 확인, **[재구현]** 파이썬 재구현, **[추정]**, **[미확정]**.

2026-10-02 정정: 이전 문서(stage_misc §4.3)는 본문을 "hknpCompressedMeshShape"로 추정했습니다. 태그파일의 타입 표를 읽어 보니 **`hknpMeshShape`**(Havok 2021.1의 새 메시 형식, 상대 배열 `hkRelArrayView` 사용)입니다. RomFS의 bphsh 1485개가 전부 이 타입입니다 **[데이터]**. 압축 메시(hknpCompressedMeshShape)의 섹션·공유정점 구조는 여기에 해당하지 않습니다.

## 1. 결론 요약

| 항목 | 결과 | 확정 수준 |
|---|---|---|
| 루트 형상 | `hknpMeshShape`(shape type 8) | [데이터] 타입 표 + [판독] 캐스트 디스패치 `0x71009443c4`가 type 8 = "hknpMeshShape::castShapeImpl" |
| 정점 | `(sectionOffset(s32) + u16) * bitScale16Inv` (1/512) | [판독] `0x71009372cc` + [데이터] 650개 형상의 ShapeParam `AutoCalc` bbox와 최대 오차 9.5e-7 |
| 프리미티브 | u8 a,b,c,d. c==d → 삼각형(a,b,c). c≠d·b≤d → 삼각형 (a,b,c),(a,c,d). c≠d·b>d → 평면 사각형 1개 | [판독] `0x71009372cc` |
| 삼각형 → 재질 | 프리미티브 키 `section<<9 \| prim<<1`로 shapeTagTable 이진 탐색 → shapeTag = bphsh 재질표 인덱스 | [판독] `0x710093e82c`(탐색) + [데이터](섹션 기준 키 0/512/1024…, 태그 < 재질 수 전수 성립, 물 태그가 수면 높이 평면) |
| shapeTag → 재질·필터 | bphsh 재질표 16B 항목(MaterialCollection 인덱스, UserShapeTag 마스크), 필터표 u64(하위 32 = LayerHitMaskEntity 이름 값, 상위 32 = SubLayerHitMaskEntity 이름 값) | [데이터] (Water→`SplWater`, KeepOut→`SplKeepOutPlayer`, Fence→`SplInkThrough`/`SquidThrough`로 이름이 맞음). 엔진이 태그로 8 B 필터 행을 고르는 한 단계 `0x7103ad6a70`은 [실행](2026-10-03, 1024/1024). 그 행 배열을 형상에 붙이는 writer·형상별 결과와 공통 필터의 결합은 [미확정] |
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

- 섹션 키 기준 `sectionKeyBase`(질의 컨텍스트 +0x60) = `section<<9` **[판독 — 2026-10-02 3차]**: `0x71009372cc`가 topLevelTree 순회에서 잎(스택 값 bit0=1)을 만나면 `section = 값>>1`로 `ctx+0x60 = section << 9`, `ctx+0x68` = geometrySections[section](루트 +0x90 상대 배열, 64 B 항목), `ctx+0x70` = 그 섹션 BVH를 기록합니다(`analysis/decomp/gimmick/hknp_mesh_sub.c` 341행). 표 키가 512 배수에서 새로 시작하는 데이터 관찰(0, 512, 1024 …)과 일치합니다. 결과로 내는 Havok 셰이프 키는 `((ctx+0x60 | prim<<1 | 삼각형) + 1) << (32 − numShapeKeyBits − 상위 비트) − 1 | 상위 키`입니다(717행) [판독].
- 마지막 항목은 키 `50<<9 | 255<<1`(섹션 수 다음), shapeTag 0xFFFF인 센티널입니다. 실제 프리미티브는 이 키에 닿지 않습니다 [데이터].
- BVH 박스: `min = (bitOffset + u8) * bitScale8Inv`. 정점이 섹션 루트 박스 안에 들어감을 확인했습니다(섹션 0: 정점 x [-28.5,-4.34], 박스 [-28.59,-4.21]) [데이터]. 웹 충돌에는 BVH를 쓰지 않고 다시 만들면 됩니다.
- interiorPrimitiveBitField (2026-10-02 3차, `web/tools/collision_interior.py`, 결과 `analysis/stage/interior_bitfield_yagara.txt`):
  - **프리미티브당 1비트**: 길이 = ceil(프리미티브 수/8)이 Fld_*·Mpt_* 166개 파일 3667개 섹션 전부 성립, 비트 i = `bits[i>>3] >> (i&7) & 1` [데이터].
  - Yagara 2787개 프리미티브 상관: 비트 1인 275개는 **전부 열린 모서리가 없음**(모든 모서리를 다른 프리미티브와 공유). 그중 254개(92%)가 "볼록 모서리 없음(이웃이 오목 쪽이거나 같은 평면)". 반대로 열린 모서리가 없고 볼록 모서리도 없는 275개 중 254개가 비트 1 [데이터].
  - 해석: **내부 프리미티브(모서리 접촉이 생길 수 없는 면) 표시 — 용접(welding) 생략용** **[추정 — 상관 92%]**. 캐스트 경로 `0x71009372cc`/`0x7100936ee8`는 이 비트를 읽지 않습니다(섹션 +0x18 접근 없음) [판독]. 접촉 생성(Phive 물리) 쪽 사용은 [bulletbody]/[physics] 소관입니다.
  - 웹: 충돌 질의 결과에는 영향이 없습니다. 모서리 걸림(ghost edge) 처리를 원본처럼 하려면 이 비트를 삼각형 속성으로 보존하세요(`collision_mesh.py`는 아직 출력하지 않음).
- topLevelTree(섹션 BVH 위 트리) 노드 형식은 순회 코드 판독(잎 = bit0, 섹션 번호 = 값>>1)까지만 했고 노드 박스 해석은 하지 않았습니다. 웹은 BVH를 새로 만들므로 필요 없습니다.

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
- **[미확정]** 정보 객체(형상+0x28 → +8 행 수, +0x10 행 배열, +0x28 내부 메시)를 만드는 writer(bphsh 로더). 5차 시도: 경로 생성 `0x7103a221cc`(".%s.bphsh")까지 찾음. 헤더 오프셋으로 포인터를 만드는 저장 패턴은 phive 범위에서 찾지 못함.
- **[미확정]** 형상별 행이 공통 쌍 필터(양방향 6개 AND, [실행])와 어떻게 결합되는지(`0x7103c34b7c` → `0x7103b02470`).

마스크 비트 대응 **[데이터]**(PhiveConfig `LayerEntityCollection` 순번: 0 NoHit, 1 CustomReceiver, 2 GameCustomReceiver, 3 Ground, 4 Water, 5 SplPlayer, 6 SplPlayerChariotShield, 7 SplCamera, 8 SplInkBullet, 9 SplInkBullet_FriendThrough, …): `SplKeepOutPlayer` 0x62 = 비트 1·5·6(CustomReceiver·SplPlayer·SplPlayerChariotShield), `SplKeepOutPlayerAndCamera` 0xe2 = 여기에 비트 7(SplCamera), `SplPlayerThrough` 0x1fffff9e = 비트 0·5·6 만 빠짐(플레이어·전차 방패만 통과). 이 비트가 실제 접촉 판정에 그대로 쓰이는지는 위 결합 방식이 남아 **[미확정]**.

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
- `FillUp`(2, 9, 10)과 `KeepOut`(3, 4)은 필터가 `SplKeepOutPlayer`이고 위향 면적이 0인 수직 벽입니다. 필터 하위 32비트 0x62 의 레이어 비트는 CustomReceiver·SplPlayer·SplPlayerChariotShield 뿐입니다 **[데이터]**(§3.4). 그래서 "플레이어만 막는 면"은 마스크 데이터로는 맞고, 엔진이 형상 행을 공통 필터와 결합하는 방식이 남아 동작으로는 **[미확정]**입니다. "구멍 메우기"라는 용도 해석은 이름에서 온 **[추정]**입니다.
- 7번(Stone, `SplPlayerThrough`)은 수평 면이고, 필터 하위 32비트 0x1fffff9e 는 SplPlayer·SplPlayerChariotShield(와 NoHit) 비트만 뺀 값입니다 **[데이터]**. 플레이어는 통과하고 잉크탄(비트 8·9)은 맞는다는 해석은 이 비트 대응에서 나오며, 엔진 결합 방식이 남아 동작은 **[미확정]**입니다.
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

원본 충돌 쿼리를 실행해 비교하지는 않았습니다(Phive 런타임 미실행).

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
| shapeTag → bphsh 재질표 조회 코드(Phive 쪽) | 행 선택 한 단계 `0x7103ad6a70` [실행] (§3.4). 남은 것: `0x710093e3d8`가 넘기는 콜백(`[+0x130]` vt+0x40) 구현 클래스, 정보 객체 writer(bphsh 로더, 경로 생성 `0x7103a221cc` 이후) |
| interiorPrimitiveBitField·topLevelTree 의미 | 비트필드 = 프리미티브당 1비트 [데이터], 내부 프리미티브 표시 [추정 — 상관 92%]. 사용 코드(접촉·용접)는 캐스트 경로에 없음. 5차에서도 읽는 코드를 찾지 못함 → 좁은 단계 처리기 표 `0x7105756468` 4종과 메시 접촉 생성에서 섹션 +0x18 읽기 확인 필요 |
| 필터표 → 충돌 필터 적용 | 공통 쌍 필터 결합식 [실행]·형상 행 선택 [실행]은 해소. 형상 행과 공통 결과의 결합(`0x7103c34b7c` → `0x7103b02470`)과 행 배열 부착 writer 는 [미확정] — [../physics/character_controller.md](../physics/character_controller.md) §3.5, §9 |

### 6차 갱신 (2026-10-03, r6 physics)

| 항목 | 결과 | 수준 |
|---|---|---|
| 필터표 → 충돌 필터 적용 | 결합식 `0x7103c5e244`: bit28 몸체는 삼각형 행 low/high 에 상대 레이어·하위 레이어 비트가 있어야 접촉 유지, 그 뒤 공통 쌍 필터 AND. 4096/4096 원본 실행([../physics/character_controller.md](../physics/character_controller.md) §3.5) | [실행] |
| 지형 bit28 | 물리 구성요소 초기화 `0x71012e9914` → functor slot0 `0x71012ea8c4`가 레이어 3(Ground) 몸체에 bit28 = 1(태그 `Actor_MapParts_KeepOut`/`Actor_Lift_KeepOut` 액터 제외) | [판독] |
| bphsh 자원 파서 | 자원 vtable `0x7105765ad8` 슬롯5 `0x7103de04d0`: 헤더 "Phive\0\1\0", BOM 0xfeff, tagfile = base+[0xc]; 자원+0x30 = base+[0x10](재질표), +0x38 = [0x20]>>3, +0x40 = base+[0x14](필터표). Yagara: [0x20] = 0x1b0 → 54(필터 행 28개보다 큼, 태그 ≤ 26 이라 영향 없음). `gimmick_phive.py`의 0x18~0x24 필드 이름(end/tag/mat/flt)은 [0x18] = 파일 크기, [0x1c] = tagfile 크기, [0x20] = 재질표 크기, [0x24] = 필터표 크기로 읽는 것이 실제 값과 맞음 | [판독]+[데이터] |
| 정보 객체(hknpShape.userData, +0x28) writer | 자원 필드와 정보 객체(+8 행 수, +0x10 행, +0x28 메시)를 잇는 코드 [미확정]. 자원 크기 0x48 이라 정보 = 자원+0x30 은 아님 | 다음: 자원 +0x38/+0x40 reader |
| FillUp/KeepOut(플레이어만 막음), Stone PlayerThrough | 플레이어 쪽: 결합식 [실행]+bit28 [판독]로 KeepOut 행은 플레이어 접촉 유지, PlayerThrough 행은 끔. 탄 쪽: 막는 접촉 비트 `0x7103c39158` [판독], 호출 사슬 [미확정] | [미확정, 부분] |
| 용접 비트 | 6차 미착수 | [미확정] |
