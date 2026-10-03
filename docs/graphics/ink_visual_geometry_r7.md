# 시각 지형 도색 좌표 웹 반영 r7

## 1. 기능 개요와 사용자에게 보이는 동작

바닥·벽 잉크를 별도 충돌 삼각형 오버레이 대신 실제 시각 지형의 draw에 연결하기 위한 좌표·기하 모듈을 추가했다. 원본의 두 UV·선택값·접선 CPU writer는 기존 [실행] 근거를 재사용했고, 현재 웹 차트와 시각 모델의 대응은 명시적인 **웹 adapter**다. 완전한 Lby_Lobby00 원본 패널/아틀라스를 생성한 것으로 표기하지 않는다.

이번 모듈은 충돌 면 위로 0.02 띄운 별도 overlay와 그에 따른 지형 틈/계단/벽 형상 차이를 줄이기 위한 연결이다. 잉크 조명·색·법선/neighbor 소비는 별도 surface shader 및 부모 통합에서 검증한다. 이 문서의 단독 테스트 통과를 브라우저 화면 전체 원본 일치로 확대하지 않는다.

## 2. 원본·현재 자료와 중복 확인

- 원본: Splatoon 3 v0 `extracted/exefs/main.reloc.img`.
- 기존 근거: [colpaint_atlas.md §7.2](../paint/colpaint_atlas.md), [model_panel_mapping.md §4~8](../paint/model_panel_mapping.md), [panel_groups.md](../paint/panel_groups.md).
- SHARED 300/597~599/642, FUNCS의 2be2de4/bed910/bedb98/2be59f0/2be5ae8/2be5ba4를 먼저 확인했다. `decomp_index.py`는 모두 기존 C를 반환했다. 신규 디컴파일·전체 패널 배정 재분석은 하지 않았다.
- 웹 GLB audit: `analysis/port_ink_r7/uv/asset_audit.json`. visual.glb는 119개 mesh/primitive, 346개 node, 86개 material이다. paint type1은 11개 material이고 나머지75개는 해당 옵션이 없다 [데이터: 현재 웹 에셋].
- GLB 실제 속성은 POSITION/NORMAL/UV0 각각119, TANGENT118, UV1 85, UV2 3이다. 도색 `_pu0/_pu1/_pu2` actual buffer는 없다. type1 material 메타에는 `_pu` attribute assignment가 남아 있지만 정점 자료를 대신하지 않는다.
- collision.json은 world 좌표 positions/indices/재질/source를 제공한다. 원본 최종 panel ID/UV2×3/3200² 배치 표는 현재 map bundle에 없다. UV1은 베이크용이며 paint UV로 덮어쓰지 않는다.

## 3. 모듈 진입점과 흐름

`bindVisualPaint(root, surfaces, materialForPage)`는 이미 로드/병합된 시각 모델을 읽는다. `nativeForward=true`, 원본 메타 `blitz_paint_type=1`, 단일 MeshStandardMaterial인 visible mesh만 대상으로 한다. skinned/morph mesh는 건너뛰고 기록한다.

```
visual triangle -> current world transform -> current custom chart candidates
 -> plane-distance order -> chart rectangle clipping + remainder partition
 -> barycentric original attributes -> page-specific material callback
 -> paintUv/paintUvSwitch/paintUvTangent -> same visual triangle shader
```

원본 경로인 BFRES→42방향 패널 선택→패턴/연결/그룹→UV mapper와 이 순서를 혼동하지 않는다. 당시 시각 원본 경로는 기존 model_panel_mapping §3~8에 기록돼 있다.

## 4. 계약·상수·필드

| 입력/출력 | 의미·수준 |
|---|---|
| `nativeVisualUv` | 위치·native basis·mapping bbox·UV2×3 → f32 UV. 원본 0x7102bed910의 기존 식 [판독]+[실행 재검증] |
| `nativeVisualTangent` | inverseUV 첫 열 → basis 접선. 0x7102bedb98. finite/non-singular 범위; det0/비정상값은 undefined로 명시 [실행 재검증, 한정] |
| `nativeVisualWorld` | decoded NaN guard→선택적 shape→root3×4. 0x7102bd1298의 원본 명령 블록과 대조 [실행-블록] |
| `nativePackPaintUv/Switch/Tangent` | UV×32767 절삭16비트, switch×127 절삭8비트, tangent×511 ±0.5절삭10비트. writer주소 2be59f0/2be5ae8/2be5ba4 [실행] |
| `paintUv` | Int16×4 normalized=true. 현재 custom chart UV를 두 후보로 복제. GPU 소비는 WebGL SNORM adapter |
| `paintUvSwitch` | Int8 normalized=true, 현재 adapter는0. native의 서로 다른 두 패널/음수 switch 전체를 재현한 것이 아님 |
| `paintUvTangent` | native CPU packed10 writer 뒤 WebGL SNORM float3 adapter. 입력은 chart.e1의 object-space inverse-model 변환 |
| `stats` | candidate/bound mesh, visual/assigned triangle, pieces/remainder, pages/skipped. 실행 브라우저 수치는 부모 통합 보고에서 기록 |

candidate normal dot>.99, 모든 vertex plane-depth≤.2, sphere radius+.2, polygon degeneracy tolerance 1e−10은 이 모듈의 **웹 adapter 정책**이다. 원본 후보우선순위0..11의 동일식이라고 표기하지 않는다. 현재 chart의 8texel/unit은 기존 native density와 같지만 chart 분할/배치는 custom이다.

## 5. 수명과 소유권

binding은 원본 mesh/geometry/material을 수정하거나 해제하지 않고, 원본 visible만 임시 false로 바꾼다. 같은 parent·local matrix·receive/cast shadow·layer·renderOrder의 generated pieces를 추가한다. unassigned remainder에는 원래 material을 사용한다.

`dispose()`는 generated geometry를 해제하고 pieces를 제거한 뒤 원본 visible을 복원한다. 중복 호출은 무해하다. callback이 만든 material clone은 부모 paint view의 소유다. texture/color/shader 소유권을 geometry helper에서 가져오지 않는다.

## 6. 계산·분할과 정밀도

원본 UV leaf는 `u=dot(B0,p)-(minU+maxU)*.5`, `v=dot(B1,p)-(minV+maxV)*.5`, `UV=(translation+(u*m0+v*m1), translation+(u*m3+v*m4))`이며 연산마다 f32다. tangent 및 writer도 기존 원본 순서대로 계산한다.

실제웹 시각 triangle partition은 다음처럼 독립 adapter로 계산한다.

1. world 세 정점에서 법선·중심·최대 정점 거리를 구한다.
2. `chartsInSphere` 후보를 얻고 위 plane 정책으로 걸러 평균 절대 plane 거리, 동률 chart ID로 정렬한다.
3. 각 현재 custom chart의 0≤u≤w, 0≤v≤h 사각형으로 남은 polygon을 자른다.
4. 안쪽은 해당 chart에 배정하고, 바깥쪽은 네 clip 단계의 disjoint remainder로 보존한다. 다음 chart는 remainder만 받으므로 겹친 chart가 같은 면을 중복 생성하지 않는다.
5. polygon을 fan triangle로 만들고 원래 정점 모든 속성을 동일 barycentric weight로 보간한다. 정규화된 Int8/Uint8 속성은 실제 normalized 값을 읽어 float로 보존한다.

현재 chart UV는 `(x0+8*dot(e1,p-o))/pageW`, `1-(y0+8*dot(e2,p-o))/pageH`다. 원본 셰이더 offset 후1−V 분기를 소비하면 DataTexture의 현재 row방향으로 돌아온다. upload orientation은 부모 texture의 계약이다. page를 넘는 triangle은 geometry를 나누며, 원본 두패널 switch와 동일하지 않다.

UV/switch writer는 FCVTZS의 NaN→0, signed32 saturation, 하위16/8비트 저장을 보존한다. 음수/범위밖 값을 clamp01로 정리하지 않는다. 예를 들어 UV1.2의 CPU16비트 결과는 부호 있는 값으로 해석할 때 음수로 감긴다. WebGL SNORM의 signed 최소값 clamp는 CPU writer 뒤 adapter에만 적용된다.

## 7. 애셋·셰이더와 연결

실제 시각 삼각형의 uv/uv1/normal/tangent/color를 유지한다. UV1 베이크는 별도 draw에서도 동일한 barycentric 값이다. 원본 `_pu`에 대응하는 새 속성을 원래 텍스처UV와 별도로 생성한다. chart pad 안 빈 RGB는 surface shader의 branch-off 입력이며 geometry에서 임의 색을 채우지 않는다.

재질 callback은 기존 Hoian/Forward `onBeforeCompile`과 cache key를 보존한 clone에 잉크 branch를 연결해야 한다. 그래픽 helper 자체는 roughness/color/lighting 값이나 polygon lift를 새로 만들지 않는다.

## 8. 다른 기능과 상호작용

physics collision, paint CPU texel ownership, score/swim sampling, collision chart building은 변경하지 않는다. 현재 바닥 잉크 시각 좌표와 custom atlas 사이만 연결한다. geometry는 이미 빌드된 atlas를 읽고 paint events의 상태를 수정하지 않는다.

표적/캐릭터/오징어는 이 map-static binding 대상이 아니다. 환경광 capture와 shadow traversal은 원래 visible 대신 같은 위치 generated pieces를 보게 된다. native full frame/caster 정책은 이 작업으로 확정하지 않는다.

## 9. 웹 파일·통합 순서

| 파일 | 책임 |
|---|---|
| `core/paint/native_visual_uv.ts` | 기존 native leaf의 f32 계산·CPU packing; 명시적 web SNORM decoder |
| `core/paint/visual_chart_adapter.ts` | current custom chart ranking/disjoint clipping/barycentric 계약 |
| `client/paint/visual_geometry.ts` | actual THREE visual geometry와 page material binding/복구 |
| `tests/native_visual_uv.test.mjs` | 기존 native 명령에서 내보낸 fixture와 비트·바이트 대조 |
| `tests/visual_paint_geometry.test.mjs` | floor/wall/page/overlap/attribute/ownership 검증 |

부모 통합은 map load/merge 후 atlas 준비→page DataTexture 준비→same-draw surface branch clone→bind 순서로 수행한다. dispose에서 binding을 먼저 복구한 뒤 clone/texture를 해제한다. 원본3200² atlas 공급이 생기면 current adapter를 그 표로 교체하며 native leaf는 그대로 재사용할 수 있다.

## 10. 실제 검증과 실패

`analysis/port_ink_r7/uv/export_fixture.py`는 이전에 의미가 확정된 원본 leaf를 그대로 실행해 regression fixture를 저장했다. 기존 r7/r8 성과를 신규 native 완료 행으로 재계상하지 않는다.

| 검증 | 결과·범위 |
|---|---|
| native UV/switch/tangent whole writer | 277 입력, 음수/NaN/±inf/overflow 포함. 현재 웹 byte/u32 모두 일치 |
| native panel UV/tangent whole leaf | 256 finite 정상행렬, 42방향. 출력 UV2/접선3 f32 bits 모두 일치. native basis/SDK sinf/cosf 실행 |
| native world instruction excerpt | 128 입력, optional shape/root/NaN. 0x7102bd13f4~1414, 141c~148c, 1360~13dc 블록 출력3 f32 bits 일치. BFRES accessor/shape lookup/whole함수는 제외 |
| leaf Node tests | 6/6 PASS |
| geometry Node tests | 5/5 PASS. 2page 면적보존, 겹침중복제거, dry remainder, wall, translated transform, bakeUV/color/tangent 보간, dispose 원복 |
| custom chart polygon 분할 추가 검증 | 4,096 무작위 triangle/5개 overlap chart 입력에서 barycentric 총면적0.5 보존, 실패0. 웹 adapter 계산이며 원본 실행 건수에 넣지 않음 |
| typecheck | PASS |

명령/실패 기록은 `analysis/port_ink_r7/uv/commands.md`, fixture는 `tests/fixtures/native_visual_uv.json`이다. 첫 `Get-Content analysis/decomp/r7_paint/uv.asm`는 파일이 없어 실패했고 actual panel_uv.asm으로 수정했다. 존재하지 않는 analysis/r7_paint·r8_graphics 조회는 기존 analysis/decomp와analysis/completion으로 바로잡았다. 테스트 기대값을 결과에 맞춰 고치지 않았다.

브라우저 전체 GPU/실제 Lby 샷은 부모 통합의 결과를 따른다. 여기의 CPU writer 실행을 원본 GPU 실행으로 표기하지 않는다.

## 11. 남은 차이·미확정

- current atlas는 coplanar custom chart·PAD1·최대chart1024·2048 shelf다. 원본42방향/3200²/여백3/기요틴/실제 패널연결·그룹·배정 표와 다르다. 이번으로 전체 atlas 완료율을 올리지 않는다.
- 실제 원본 두패널 seam switch/triangle postpass를 current page geometry partition으로 바꾼 이식 차이가 남는다. 원본 규칙은 기존 model_panel_mapping §7에 확정됐지만 해당 로비 final자료는 없음.
- 원본 GPU format0x1502/0x202의 정확한 enum/live binding과 packed10입력 소비는 미확정. WebGL SNORM는 명시적인 adapter이며 CPU bytes만 native 일치다.
- native UV det0의 이전 s8/s9, 비정상 tangent SDK fallback, runtime `col_paint_uv_offset` writer, original geometry→native panel actual atlas는 별도다.
- 잉크 normal/neighbor·roughness/빛/환경맵/최종 색과 전체 캐릭터·잠영 차이는 이 모듈의 단독 검증으로 해소하지 않는다.

2026-10-03 정정: 기존 client/paint의 overlay 주석에는 시각셰이더 미판독이라고 남아 있지만 현재 기존 분석은 CPU writer/시각패널선택/후처리를 확정한 상태다. 원본분석 상태와 currentcustomadapter 웹반영 상태를 별도로 기록했다. 원본/impl/scripts/package/assets 변경은 하지 않았다.
