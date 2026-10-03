# 바닥 잉크 UBO 입력·이웃 UV — 추가 분석 r2

## 1. 기능 개요와 사용자에게 보이는 동작

2026-10-03 · Lby_Lobby00의 바닥 잉크 윤곽·법선에 사용하는 texel offset 공급을 추가 추적했다. **새 원본 연결 실행 28/28**로 초기화→ColPaint texel 기록→vec4 CPU UBO staging 복사의 값을 확정했다. 이 한 경로에서는 `[22].w`가 0이며, `[22].z`를 복제하지 않는다. 씬 전체 수명에서 W가 항상0이라고 확정한 것은 아니다.

이번 문서는 분석만 수행했다. 웹 소스·에셋·impl·original을 변경하지 않았다. 범위 전체 atlas/raster 질문은 조사중 유지한다.

## 2. 원본·버전·자료 위치

Splatoon 3 v0 main NSO의 `extracted/exefs/main.reloc.img`. 기존 `analysis/decomp/render/scene_common_ubo.c`와 `analysis/decomp/paint4/colpaint_r1.c`, `analysis/decomp/gfx4/g1.c`, `analysis/render/blitzubo0_layout.tsv`를 재사용했다. 신규 디컴파일은 `analysis/visual_gap_r2/floor/member_pack.c`; 하네스/결과는 같은 폴더의 `floor_ubo_emu.py`/`ubo_execution.json`이다.

실제 모델 셰이더는 `analysis/gfx4/programs/Fld_VSLobby__LobbyFloorConcrete.frag/.vert`. `_pu*` 공급과 atlas 기하 질문은 [colpaint_atlas](../paint/colpaint_atlas.md), [model_panel_mapping](../paint/model_panel_mapping.md)의 기존 근거를 우선한다.

SHARED/FUNCS와 `decomp_index.py --no-build`에서 2be8aec·1183ab8·2c1b5a4는 기존 분석, 1030f44는 새 디컴파일 대상으로 확인했다. 기존 Z 수치·S 선택·셰이더 전체 식을 신규 확정으로 중복 계상하지 않는다.

## 3. 진입점과 호출 흐름

```text
SceneCommonUBOHolder 생성자 1183ab8
  [22] 초기화 블록 11846c4..1184828 → X/Y/Z/W = 0
ColPaint 초기화 2be8aec
  S 선택 → texel 블록 2be9068..2be9148 → Z만 두 번 대입
BlitzUBO0 member[22] vt+18 → 1030f44 (whole 함수)
  member+38..44 → table[index22].offset160 → staging[160..16F]
모델 user0 binding 110f8cc → shader BlitzUBO0[22].zw 소비
```

[판독] 마지막 모델 binding은 기존 근거다. 새 실행은 위 두 블록과 whole 1030f44이며 실제 GPU submit/upload 또는 Scene 렌더 루프 실행은 아니다.

## 4. 구조체·필드·상수·writer/reader

| 기준 객체/필드 | 타입·계약 | writer → reader | 수준 |
|---|---|---|---|
| holder+CB8/+CBC | [22].x/y f32 | 2c1b5a4 → shader | 기존 [판독] |
| holder+CC0 | [22].z f32 | 2be90a4·2be90f0 → 1030f44 → shader | 기존 [판독], 새 [실행-블록 연결] |
| holder+CC4 | [22].w 32bit | 11847dc가0 초기화; texel 블록은 보존 → 1030f44 | 새 [실행-블록 연결], 전체 후속 writer [미확정] |
| holder+C80 | member[22], 값+38~44 | layout 선언 kind6/comps4/index22 | 기존 [실행-레이아웃] |
| member+30 | owner 포인터(holder+CB0) | scalar set의 dirty-list 관리 | [판독] |
| owner+2DC/+2C8/+2D8 | node 상대오프셋/dirty head/count | 원본 setter 블록 | 새 [실행-부분] |
| UBO+10/+18 | layout table header/staging pointer | 1030f44 | 새 [판독]+[실행-whole] |
| row22+4/+8 | u16 offset160 / u8 kind6 | 기존 선언 → 1030f44 | 기존 레이아웃 재사용 |

**기존 결론 연결 정정:** [stage_rendering](stage_rendering.md) §7의 비교 문자열 미확정은 [panel_groups §9](../paint/panel_groups.md#9-200400-장면-문자열-판독데이터)에서 이미 해소했다. 기본 BigWorld basename과 비교하므로 Lby_Lobby00는 S=400, Z의 f32 비트는 `0x39a3d70a`(1/3200)이다. 이는 새 발견으로 세지 않는다.

## 5. 상태 전이와 전체 수명

[실행-부분] 네 scalar 초기화는 각 값0을 쓴 뒤 같은 member dirty node를 등록한다. 빈 node에서는 최초 등록만 count를1 늘리고, 이미 등록된 node는 다시 추가하지 않는다. ColPaint texel 블록도 Z setter를 두 번 실행하지만 빈 입력에서 dirty 등록은1회다.

[실행-whole] 1030f44는 값을 read-only로 읽어 staging에 복사한다. W를 default1로 바꾸거나 Z를 복사하는 후처리는 없다. sentinel W의 음수0·NaN payload도 비트 그대로 복사된다.

[미확정] 다른 frame callback/alias setter/메모리 복사를 통한 W 후속 갱신, 실제 NVN 제출/버퍼 교대까지는 미실행이다. 이번 실행을 whole 사격장 수명 확정으로 승격하지 않는다.

## 6. 계산식·조건·상세 의사코드

### 6.1 원본 texel 블록 [실행-부분]+[판독]

```text
n = fcvtzs(S)
n += (S != scvtf(n)) ? 1 : 0
n = (n > 1) ? n : 1
z = f32(1 / scvtf(n << 3))
holder.CC0 = z; markDirty(member22)
holder.CC0 = z; markDirty(member22)  // 원본 두 번째도 CC0
// holder.CC4를 쓰는 명령은 이 블록에 없다.
```

두 번째 CC0를 CC4로 고치는 것은 원본 재현이 아니다. S200과400을 각각 확인했으며 선택 상위 함수는 실행하지 않고 확정된 S를 입력으로 주었다.

### 6.2 staging 복사 [실행-whole]+[판독]

```text
src = member + 0x38
index = signed32(member+8)
dst = UBO.staging + layout[index].offset
n = rodata[4abfdc8 + 4*kind] // kind6 →4 words
copy raw n*4 bytes from src to dst
```

1030f44에서 source W의 raw u32를 저장하는 명령은 1030ff4(load)/1031004(store)다. 합성 table kind6/offset160은 기존 원본 선언 결과를 사용했다. UBO vt+18의 두 callback은 원본 no-op 함수1031040을 붙였다. 실제 플랫폼 buffer accessor를 실행한 것으로 표기하지 않는다.

### 6.3 이웃 샘플의 좌표 계약 [판독, 기존 셰이더 상세 보완]

LobbyFloorConcrete.frag 330~381의 실제 순서:

```text
uvCandidate = switch<0 ? paintUV.zw : paintUV.xy
v = 1 - uvCandidate.y
C  = sample(u, v)
Cv = sample(u, fma(Mottari, W, v))
Cu = sample(fma(Mottari, Z, u), v)
M = max(C.b, max(C.r,C.g))
wr/wg/wb = clamp((C.channel - M + 9.99999975e-5) * 1e8,0,1)
gv = dot(weights, C-Cv) * InkNormalIntensity
gu = dot(weights, C-Cu) * InkNormalIntensity
```

양의 v 오프셋은 **V 반전 후** 더한다. `weights`는 정확히 이 clamp 식이며 임계 근처 좁은 ramp가 있다. `>= M−1e−4` boolean으로 단순화하지 않는다. filtered channel에서 동률이 여러 개면 색/차분을 복수 채널 가중합한다.

위 init→texel→pack 입력에서는 W=0이므로 Cv 좌표가 C와 같다. 이때 gv=0이라는 것은 같은 샘플 결과를 전제로 한 식의 귀결이며 [재구현-추론]이다. 원본 GPU 샘플러/미분/픽셀 실행 결과로 세지 않는다. 자연스럽게 보인다는 이유로 W를 Z/atlasHeight 역수로 채우지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

바닥 윤곽의 normal은 stamp alpha와 별개다. `_pu2` paint tangent와 vertex normal의 기저에서 gu/gv를 합성하고 thickness를 적용한다. Mottari는 기존 매 프레임 공급 2c2036c의 `[20].z`; 애니 시간 f/60와 texel interval을 합쳐 임의 단일 파형으로 바꾸지 않는다. 팀 Ink/InkBright·native cube layer12는 [stage_rendering §7](stage_rendering.md#7-맵-위-잉크-판독-셰이더-1714)을 따른다.

이 분석에서 발사/VAT·오징어 emitter·음원은 추가 확정하지 않았다.

## 8. 다른 기능과의 상호작용

S는 원본 ColPaint 패널 분할 한도와 Z에 모두 연결되지만 web 독자 atlas의 texture width가 S와 같다는 근거는 없다. native UV mapping 없이 `1/webTextureWidth`를 같은 uniform이라고 붙이면 좌표 계약이 달라진다.

모델 paint UV 전환/offset→V 반전→neighbor와 팀 mask를 한 경로로 유지해야 한다. gameplay 소유 스텐실 판정과 visual near-max weights를 같은 boolean으로 합치지 않는다.

## 9. 웹 포팅 구조와 구현 순서

현재 [impl/paint](../impl/paint.md) §1.5의 충돌 overlay/roughness.35 표시를 원본 모델 ink branch에 연결해야 한다. 우선 native model `_pu*` 공급을 연결하고 [20]/[22] provider를 따로 둔다. 고정 default W는 확정된 **초기값0**으로 보존하고, 아직 발견하지 못한 runtime writer는 [미확정] 표시를 유지한다. W를Z로 대칭화하는 변경은 하지 않는다.

shader weights의 narrow clamp와 V 반전 뒤 positive neighbor, InkBright/rim/roughness/normal/thickness/native reflection을 전체 branch로 반영한다. 이 문서는 반영 지시용 근거이며 코드 반영 완료를 주장하지 않는다.

## 10. 검증 코드·명령·실행 결과

| 실제 명령/시도 | 결과 |
|---|---|
| decomp_index --no-build 2be8aec/1183ab8/2c1b5a4 | cached 원본 확인 |
| decomp_index --no-build1030f44·func_lookup1030f44 | 미디컴파일, 시작1030f44/252B |
| `sh web/tools/full_decomp.sh ...member_pack.c 0x7101030f44` | PowerShell PATH에 sh 없음, 실패 |
| `C:/Program Files/Git/bin/sh.exe web/tools/full_decomp.sh ...member_pack.c 0x7101030f44` | exit0·1함수 디컴파일, INDEX6165 |
| `PY analysis/visual_gap_r2/floor/floor_ubo_emu.py` 첫 실행 | INIT466c에서 앞 member+C68 fixture 없음→unmapped 실패, 성공 계상하지 않음 |
| 같은 명령, 실제 [22] 시작46c4로 수정 | exit0, 28/28, mismatch0, fault0 |
| xref GOT5791ec8/direct5818e38·storescan cc4 | broad 후보 검색. GOT xref에는312d260처럼 실제page591의 false-positive가 있어 전역 연관을 일괄 확정하지 않음 |
| `rg --files analysis ...` | unrelated port_graphics/python ACL 오류·큰 검색 truncation, 이후 관련 디렉터리로 축소 |
| player_vt.py numeric address | 클래스명 도구라 vtable lookup 실패, reloc 이미지 raw8Q로 대체 |

28건은 sentinel 보존24건(S2×list2×W6)와 초기화 연결4건(S2×list2)이다. [실행]은 ARM64 원본 명령이며 **mutex ABI 두 함수를 즉시 반환**으로 대체했다. holder/list/table/staging은 합성; whole 생성자·ColPaint 초기화는 두 선택 블록만 실행했다. PACK은 whole 반환까지 실행했다. S분기 상위/콜백 플랫폼 buffer 객체/NVN/GPU는 제외한다. 재현 출력에 원본 이미지 해시·stores PC·값·호출 경계가 있다.

## 11. 미확정 사항과 다음 근거

| 잔여 | 시도·경계 | 다음에 볼 곳 |
|---|---|---|
| whole Lby 수명 W 최종값·후속 writer | ctor initializer/texel writer/whole stagingpack 해소; static cc4 및 GOT 검색은 alias/indirect memcpy 전체 부재 증거가 아님 | whole SceneCommon callback/dirty upload lifecycle, holder+C80 파생 포인터·memcpy source를 런타임 watch |
| 실제 GPU sampling/filter/wrap/derivative | 기존 GLSL 판독만, Maxwell/NVN 실행환경 없음 | gsys_user3 texture/sampler binder·NVN descriptor·원본 GPU capture |
| whole native atlas/UV/raster | 기존 panel/mapper 부분 근거 재사용 | 실제 ColPaint scene 생성·모델 binder·GPU stamp submit |

이번 새 실행은 좁은 입력 계약을 닫았다. 혼합 inventory의 `[22].w/whole atlas/GPU` 행 전체를 확정으로 올리지 않는다. 기존 문서의 S 비교 미확정은 기존 panel_groups 근거로 정정할 수 있지만 확정률 증가로 재계상하지 않는다.
