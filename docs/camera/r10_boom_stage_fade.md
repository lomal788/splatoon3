# r10 실제 사격장 붐 질의와 물체 투명화

작성일: 2026-10-03. Splatoon 3 v0, `Lby_Lobby00` 1인 연습. 원본 분석만 수행했다. 웹 코드·에셋·`docs/impl`은 수정하지 않았다.

## 1. 기능 개요와 사용자에게 보이는 동작

- 붐은 피벗과 카메라 사이의 지형 충돌을 검사해 카메라 거리를 줄인다. 기존 반경 `0.3`, 레이어 `7`, 서브레이어 마스크 `8`, 거리 비율·스프링 근거는 [r9 붐](r9_boom_query.md), [r9 충돌 스프링](r9_collision_spring.md), [player_camera §6.8](player_camera.md)을 재사용한다.
- **[실행] 신규:** 출하 `Fld_VSLobby` TAG0를 원본 로더로 읽고, 원본 Entity 구체 body·userdata·필터 getter를 거쳐 원본 broad query/mesh leaf/TOI/listener를 실행했다. 초기 수평면 8건·40f32 비트 일치 이후, 실제 허용 태그의 서로 다른 2~5개 면이 경쟁하는 16개 수직 질의에서 최근접 비율·거리·법선·접촉점 **128개 f32 비트 일치**를 확인했다. 원본 Default helper와 실제 Banc/태그/비마스크 입력을 연결한 최종 실행도 16건·128f32 불일치0이다.
- **[실행] 신규:** 실제 PhiveConfig의 named collections를 원본 reader로 읽고 FieldParent raw Entity의 Ground/Ground와 원본 Default 문자열을 `3a403f4`로 descriptor D에 공급했다. 실제 마스크는 `1fffffff`/`07ffffff`이며, 이를 원본 Entity/지형 질의에 연결해 같은 8건·40f32 비트 일치를 재확인했다. §8.1의 잘못된 Ragdoll Q 연결은 철회한다.
- **[판독]+[실행]+[데이터] 신규:** 비마스크 descriptor·출하 actor RSDB 태그·Banc 생략 SRT 기본값·Default helper factory·Actor→engine 물리→게임 래퍼를 연결했다. **2026-10-03 후속 [판독]:** 실제 Actor/engine VT→component slot68 dispatcher와 manager 호출 조건도 연결했다(§3.1.5). **[미확정] 유지:** Banc/create-info→Actor current pose 최초 writer→Entity/native 초기 pose 적용의 마지막 동일성이 남는다. 고정4/23/32/38은 모두 조사중 유지하며, 전체 Scene Unicorn 미실행 자체를 보류 이유로 추가하지 않는다.
- **[판독] 신규:** `game::FadeOutCameraXluHelper`는 모델 목록과 `game__gfx__FadeOutCameraXluParam`을 받아 fade manager에 물체 처리를 등록한다. 최종 명명 파라미터는 **`fade_dither_alpha`**다. 카메라 위치를 직접 수정하는 helper가 아니다.
- **[실행] 신규:** 시간 상태·type1 기하·type2 최소값·epsilon/cache 총 **22,288 사례**, 불일치 0. 모델-null cache 검사에는 실제 material upload가 포함되지 않는다.

고정 질문 14의 helper/기존 파라미터 관계는 §3·7의 실제 공급자와 소비자 연결로 정정한다. 전체 NVN 화면, 모든 fade variant 수식, 실제 Lby actor별 활성 시점은 별도 미확정으로 남긴다.

## 2. 분석 대상 원본·버전·자료 위치

| 자료 | 위치/근거 | 수준 |
|---|---|---|
| v0 Main 명령/VT | `extracted/exefs/main.img` 및 `main.reloc.img`, 기존 원본 UC 로더의 BASE `0x7100000000` | [판독]/[실행] |
| 실제 Lobby 지형 | `extracted/romfs/Pack/Actor/Fld_VSLobby.pack.zs` 내 `Phive/Shape/Dcc/Fld_VSLobby.Nin_NX_NVN.bphsh` | [데이터] |
| 실제 지형 해시 | SHA256 `96914a9d26ccf7fbb8d44d98a40972af6152f1c93988d0efcb94506a45ef5856`, 86,768B | [데이터] |
| 표 parser 결과 | `analysis/completion/r7/physics_table_emu.json`의 원본 allow/block Default 3표 | 기존 [실행]/[데이터] 재사용 |
| 스테이지 배치/부모 param | `analysis/completion/r9/physics_fillup_range_data.json`, FieldParent_Main·Fld_VSLobby Shape/ControllerSet | 기존 [데이터] 재사용 |
| 실제 Entity 부모 param | `analysis/r5_ui/bootup/Phive/RigidBodyEntityParam/FieldParent_Main.phive__RigidBodyEntityParam.bgyml`, SHA256 `396418aec8e2b60ea7a72ac62ba0a0eb98c6a72d8fd08b8a2df9c217efee4042` | [데이터] |
| 실제 named mask collections | `extracted/romfs/Phive/Config/PhiveConfig.byml.zs`의 Entity/SubLayer·HitMask 4 collections | [데이터]/[실행] |
| 고정 질문 | `analysis/camera_100_r10/baseline_inventory.json`, 분모106 | 변경 없음 |
| 새 C/JSON/명령 | `analysis/camera_100_r10/boom/` | 이 문서의 재현 자료 |

새 판독 전 SHARED/FUNCS/`decomp_index.py --no-build`를 확인했다. `3bb5d98` 등 캐시 존재 함수는 `analysis/decomp/r9_physics/motion_config.c`를 재사용했다. 내부 주소 `2063e1c`는 `2062f54` visitor 내부였으며, 별도 runtime alpha consumer로 재분석하지 않았다.

## 3. 진입점과 전체 호출 흐름

### 3.1 실제 TAG0 → Entity body → mesh 질의

**[판독]+[실행]**, `r10_camera_boom_mesh_query.py`의 원본 경로:

```text
3a715b4(actual bphsh → owner O/native mesh H)
 → 3a70974(O, 0): Phive mesh wrapper G
 → 3af30fc(descriptor D, 0) → 3af344c: Entity 구체 body
 → G.vt48(inertia) / 3af6088(LayerPair)
 → 3c4e8c4(kind0 native body) → 3af593c(base Entity)
 → body VT5749368 / nativeBody+98=body
 → body.vt90=3af6f88 → body+180 LayerPair
 → native09c6a70(AddBodies)
 → camera24d5c6c / reset24d6d94..24d6dc8(query7/mask8)
 → 3a5f36c → 0a492e8 → 0adb134 → 09af088
 → 0936ee8/09372cc(actual mesh)
 → 3c570c4 → 3c57d04 → 3ad6a70(filter)
 → 0997078(mesh leaf) → 12ac5e0/12acb38(material)
 → 12d8dcc(listener iterator)
```

초기 8건 fixture의 trace 319회 중 `3af6f88` 59, `3c570c4` 50, `0997078` 50, `3c57d04`/`3ad6a70` 각42, material reader 각8회. 모든 query 8회에 실제 native mesh 경로를 탔다. FieldRigidBody 문자열 이름을 찾지 못했다고 임의 class 이름을 붙이지 않았다. 입증한 것은 출하 지형을 소비하는 **Entity VT5749368**이다.

**[판독] 필수 구별:** provider factory `3b1ab5c`의 pair backend VT57564d8과 Entity-world query wrapper `3c4579c`의 VT5756560은 다르다. 후자는 +20에 provider를 보관한다. 초기 pair backend를 query 슬롯에 넣은 시도는 8건 모두 no-hit이었다. 원본 query wrapper 구조로 고친 뒤 8건 모두 hit가 됐다. 첫 실패 JSON을 보존했다.

### 3.1.1 원본 named collections → 실제 raw Entity 마스크 → 같은 질의

**[판독]+[실행]+[데이터]**, `raw_entity_descriptor.c`, `raw_entity_callers.c`, `r10_camera_boom_entity_mask.py`, `mesh_query_authored.json`:

```text
actual PhiveConfig BYML
 → 3b17e1c: LayerHitMaskEntity/SubLayerHitMaskEntity names+u32 values
 → 3b16014: LayerEntity/SubLayerEntity names
 → 351ffe0: 원본 string buffer writer
actual FieldParent_Main BYML
 → 3bb5c5c: Entity raw param VT57502e0/원본 Default strings
 → authored string adapter (typedvisitor3bb5d98 offsets/flags)
 → 3a403f4: 이름 비교/상속/type 확인 → D88/8c/bc/c0/c4/c8
 → 3af344c → 3af6088 → LP → actualTAG0 mesh query
```

원본 reader의 이름 136개·mask 80개가 독립 BYML 값과 모두 일치했다. `3a403f4` 반환1, D의 6필드가 독립 기대값과 일치했다. 실제 FieldParent가 지정한 ShapeName=Main/LayerEntity=Ground/SubLayerEntity=Ground/MotionProperty=Default만 raw string adapter로 공급하고, 4개 mask는 원본 creator의 Default 문자열을 유지했다. 이는 전체 원본 actor-resource parser 실행이 아니다.

원본 이름 검색 순서는 layer→sublayer→enableLayer→enableSubLayer→blockableLayer→blockableSubLayer다. `3a3f29c`는 실제 base descriptor builder `3a3f2dc` 성공 뒤 `3a403f4`를 tail-call하며, `12d71f8`도 같은 reader 뒤 D60을 0으로 쓴다. `3af30fc`는 원본 body dispatch에서 `3af344c`로 연결한다. 원본 class/이름/정수 mask 계산 callback은 스텁으로 바꾸지 않았다. 명시 allocator callback과 cfg150 bootstrap 공급은 메모리 할당 경계이며 이름 비교·mask lookup을 수행하지 않는다.

### 3.1.2 실제 비마스크 입력·Default factory·Actor 물리 공급

**[데이터]+[판독]+[실행]**, `actor_resource_graph.json`, `source_contract.json`, `mesh_query_actor_source.json`:

```text
Actor/Fld_VSLobby → $parent FieldParent, PhysicsRef Fld_VSLobby
 → PhysicsParam Fld_VSLobby → $parent FieldParent, ControllerSetPath Fld_VSLobby
 → ControllerSetParam Fld_VSLobby → $parent FieldParent
    ShapeNamePathAry(Main) = Fld_VSLobby ShapeParam → actual bphsh
    inherited ControllerEntityNamePathAry(Main) = FieldParent controller
    inherited RigidBodyEntityNamePathAry(Main) = FieldParent_Main Entity
 → 3daf7dc/3de7970/38a2518: typed Physics resource → enginePhysics+38
 → engine VT5763968.slot30 = 3dafc2c
    raw ControllerSetPath(+38, flag44) → 3b38b34/3b38c3c resource reader
    context has Actor, model, scale and pose → 3a02888 → enginePhysics+18 bodyset
 → ClassName Default (raw creator3b8bcdc, child/parent omit ClassName)
 → initializer3a027c0..7fc → delegateVT5743fb8.slot0=3a17200
 → 3a02800 helper factory → actual helper VT55762a8
    slot10=12d74b0 Actor binding; slot20=12d71f8 descriptor; slotA0=3a52554
 → existing3a02bf0/3ae9db4/3ae9f2c: Main controller/Entity/Shape resolution
 → helper.slot20: actual3a3f2dc base +3a403f4 masks +D60=0
 → full3af30fc/3af344c/3af357c → Entity body/native userdata
 → 0f75e5c after3cc8010: Actor component array index10 enginePhysics+18
 → gamePhysics wrapper VT5576b40, wrapper+18=same bodyset → actor+510
 → existing0f7400c/12e9914/12ec970 → wholeGround functor12ea8c4
```

자원 그래프는 원본 자료9개의 해시와 참조를 정리한 **[데이터]**이며, Python의 부모·자식 참조 요약을 원본 상속 reader 전체 실행으로 세지 않는다. 실제 producer/consumer는 위 C에서 별도로 **[판독]**했다.

원본 ControllerSet typedvisitor `3b8c0ac`의 실제 배열은 `ControllerEntityNamePathAry value160/flag4c3`, `RigidBodyEntityNamePathAry value3f8/flag4c4`, `ShapeNamePathAry value470/flag4cc`다. `param_reflect` 배열 결과에서 value/flag가 서로 바뀐 출력은 원본 typed visitor로 교정했다. generic ClassName 추출이 다른 타입을 잡은 결과 대신 실제 creator 실행으로 Default를 확인했다.

최종 probe의 actual helper+8 Actor binding은 null이며, descriptor+18의 실제 identity Mtx34는 §3.1.3 결과를 명시 adapter로 공급했다. `12d74b0`의 실제 Actor bind는 판독으로 분리했다. Mass10000·Inertia(1,1,1)·MotionType Static(원본 enum index0)·MotionProperty Default(index0)와 buoyancy 기본1은 원본 전체 config reader/13 motion rows/base descriptor consumer로 공급했고, 원본 Provider `3b1ae90`의 Default allow/block 3표 복사 **174u32**가 기존 원본 표 기대값과 일치했다. 임의 all-mask fixture가 최종 입력을 대신하지 않는다.

### 3.1.3 실제 Banc SRT·RSDB 태그·대기 packet 적용

**[실행]+[데이터] Banc:** `Lby_Lobby00.bcett.byml` Actors35의 Fld_VSLobby(Hash4825244811554112121)는 Translate/Rotate/Scale를 모두 생략한다. 실제 caller `3cfdca4..cd4`가 GOT5790808→4a98180로 scale1·translation0·rotation0을 초기화하고, 전체 `3d03768` parser가 생략값을 유지한다. 기존 `3d03f4c` matrix producer와 실제 SDK sinf/cosf(각3회)를 사용해 identity Mtx34+scale3 **15f32** 비트 일치. 기본 section parent `4a98200`과 Lby 공급3cfa6bc/3cfc140은 r6 기존 근거를 재사용했다. 전체 Actor loader 실행은 아니다.

**[실행]+[데이터] RSDB:** actual Tag.Product.100의 actor row833=Fld_VSLobby, 전체4373 actor×177 tag bit table를 소비한다. 실제 name lookup의 `Actor_MapParts_KeepOut=69`, `Actor_Lift_KeepOut=65`; Fld_VSLobby는 둘 다 false다. 원본 membership `38c4ed0`을 5actor×177+highbit4=**889사례**, 독립 원본 BYML bit 기대값과 대조해 불일치0. 전체 functor `12ea8c4`는 실제 actor holder+348→module+80→ActorParam+128 row833을 읽고 `3af43a4(B,1)`을 호출한다. 대기 packet+c4=1/d4 bit24 → 전체 `3b07b8c` → LP8 **43→10000043(bit28)**를 실제 실행했다. runtime holder/packet 사전 할당은 adapter이며, 태그의 답이나 setter를 상수 stub으로 바꾸지 않았다.

### 3.1.4 등록 수명·같은 native world·프레임 소비의 마지막 경계

**[판독]** engine VT5763968 slot68 실제 `3db22f8`은 engine+18 bodyset에 `3a10c58(P,0,1)`을 호출한다(flag bit2의 다른 경로도 원본에서 구별). 실제 FieldParent controller의 `IsAddToWorldOnReset=true`는 기존 `3ae9f2c`의 18B record.bit0로 간다. `3a10c58`은 해당 bit0/body 등록 상태를 확인하여 `3ae0f08(B)`을 호출하고 bit0를 지운다. `3ae0f08`은 body+80 packet 또는 module+c8 queue의 기존 `3adb644` 결과에 d4 bit0=1/bit1=0을 쓴다. 기존 `3b07b8c`가 bit0를 소비해 새 `3ae5eb0`으로 연결한다.

**[판독]** `3ae5eb0→3c50734`는 `(global599dfa8+e8 module + (B88.bit5)*8 +b8)->c0`의 **같은 native world**를 선택한다. nativeWorld.vt100으로 등록을 검사하고 미등록이면 nativeWorld.vtd0(handlePointer,1,1,activationFlag)에 등록을 요청한다. 원본 world creator09bff14는 VT545e460을 쓰며 실제 relocated data의 slot100=09d1aa0, slotd0=**09c6a70 AddBodies**를 확인했다(`native_world_vt.json`). 이후 B88 bit10/bit32/bit25를 설정하고 backend.vt20을 호출한다. Body userdata writer·query factory `3a60250`가 선택하는 Entity world의 identity는 같은 owner 필드로 판독 연결했다. `3a1476c`는 world-add라고 파일명만 보고 해석하면 안 된다: 실제로는 packet d0 bit1을 끄고 dirty bit25를 요청하는 별도 활성 조건 경로다.

**[미확정] 정확한 잔여:** 실제 Fld_VSLobby engine component의 **slot68 dispatcher 호출 시점/조건**과 Banc/create-info pose가 RBC 초기 body matrix로 들어가는 **마지막 writer 동일성**은 아직 직접 연결하지 못했다. `0f7400c`는 특정 typed component의 slotd0 loop이며 engine Physics VT의 그 slot은 null이므로 slot68 호출 근거로 바꾸지 않았다. 다음은 Actor generic lifecycle/reset에서 VT5763968 slot68을 부르는 dispatcher, `3dafc2c` context pose→`3ae9f2c` descriptor matrix writer와 `12d74b0` Actor bind를 실제 FieldParent branch에 이어 보는 것이다.

기존 [phive_controller §6.7](../physics/phive_controller.md)의 Actor 단계0 그룹2/3/4→Entity 단계0 그룹6→접촉 단계1 그룹0→Player slot19/camera 계산 순서를 재사용했다. 새 fixture는 이 전체 scene schedule을 실행하지 않았다. 실제 camera `24d9ae8`에서 reset/query→`12d8dcc`→Q54 distance→`24dde2c` ratio/피벗 보정을 판독했고, 일반 쿼리·거리 소비는 해소되었다. 위 두 마지막 source 동일성이 남으므로 frozen next의 **프레임**을 삭제하지 않고 4/23/32/38을 모두 조사중으로 유지한다.

### 3.1.5 2026-10-03 후속: 실제 Actor→component slot68 dispatcher 확인

위 §3.1.4의 “slot68 dispatcher 호출 시점/조건 미연결”은 **후속 판독으로 정정**한다. 이전 문장은 당시 경계 기록으로 보존한다. 초기 pose writer의 마지막 동일성은 아직 미확정이다. 사용자 요청에 따라 여기서 새 추적을 중단했으며, 아래는 중단 전에 확보한 원문만 반영한다.

**[판독]+[데이터] 실제 dispatcher:** relocated 원본의 Actor 공통 VT5540368과 engine Actor VT575acd0은 `+d0=3cc7628`을 갖는다. `3cc7628`은 Actor+200의 count, +208의 component array, +210/+218의 index map을 읽는다. null component는 건너뛰고, `i==indexMap[i]`인 실제 소유 슬롯에만 `component.vt68(component)`를 호출한다. map 범위를 벗어나면 map[0]을 사용한다. 이후 Actor.vt228을 tail-call한다. 따라서 engine Physics index10의 실제 VT5763968/slot68=3db22f8→3a10c58→기존 등록 queue 연결을 같은 Actor의 일반 수명 경로에 이어 놓을 수 있다. `next_lifecycle_dispatch.c`, `next_dispatch_pointers.json`에 원문과 실제 pointer 5곳을 보존했다.

**[판독] 호출 시점·조건:** 기존 `r5_physics/mgr4.c`의 `3c7f810`을 재사용했다. Actor+24 상태가 5이고 +28의 bit11/13은 꺼져 있으며 bit14가 켜진 분기에서, 삭제 상태7~11/bit9를 검사한 뒤 **PC3c7fda0/3c7fda8에서 Actor.vtd0을 호출**한다. 호출 후에도 bit9가 꺼져 있으면 상태를4로 쓰고 `3c88fc4`로 활성 목록에 연결한다. 반대 경로는 상태5와 Actor.vtc8→component.vt60이다. 이 관리자가 기존 프레임 시작 대기 목록 처리 `3c85b40`에서 호출된다는 근거는 SHARED521/phive_controller의 기존 판독을 재사용했으며 신규 실행 사례로 세지 않는다. 단위 scene/frame을 Unicorn으로 실행한 결과는 아니다.

**[판독] 초기 pose에 가까운 실제 reset 소비자:** Actor 공통 VT5540368의 `+80=0f73930`은 새 원문 `3cc3c1c`을 호출한다. 기존 관리자의 Actor.vt80 호출 분기는 low-byte 활성 플래그 `0x10`에서 진입한다. `3cc3c1c`은 실제 component index10/engine Physics+18 bodyset과 +30 Actor를 읽고, Actor+298..2b8의 회전과 +28c/+290/+294의 translation을 **48B Mtx34**로 재배열하여 `3a11d40`에 전달한다. 현재 reset flags에 따라 body→Actor 되쓰기를 선행하는 분기도 별도로 존재한다.

새 `3a11d40`은 기존 `3a102f0(P,0)`으로 Main body를 선택한 뒤 원본 zero vector로 linear/angular velocity를 초기화하고 **`3ae14b0(B, suppliedMtx34, ...)`**를 호출한다. 다른 controller/body 배열의 뒤따르는 초기화도 존재하므로 Main 호출 하나만으로 모든 초기 pose를 확정하지 않는다. `3a12ae8`은 배열 조회·순회이며 직접 행렬 writer로 세지 않았다. `next_actor_reset_pose.c`, `next_controller_pose.c`에 원문을 저장했다.

**[미확정] 중단 시점의 정확한 잔여:** §3.1.3의 실제 Banc/create-info SRT가 **Actor+298..2b8/current pose로 최초 기록되는 writer**와, `3ae14b0`의 실제 Entity/native pose write·적용 시점까지 동일한 초기 branch로 이어지는 마지막 연결은 확인하지 못했다. RBC factory `3ae9f2c`의 descriptor는 identity로 시작하므로 “context에 pose가 있다”는 사실만으로 factory가 그 값을 소비했다고 주장할 수 없다. 실제 Fld의 생략 SRT도 identity라는 이유로 두 producer를 동일시하지 않는다. 다음 주소는 `0x7103ae14b0`, Actor의 최초 current-pose writer와 `0x7103cc3c1c`/`0x7100f73930` 진입 flags다. **frozen4/23/32/38은 모두 조사중 유지**한다. 전체 Scene Unicorn 미실행 자체를 추가 완료 조건으로 삼지 않는다.

`next_physics_reset_pose.c`의 `3db2508`은 destructor, `3db2320`은 scale/mass/COM 갱신, `3db1efc`는 metadata 초기 속도 공급이다. `next_actor_pose_dispatch.c`의 `3cc7390`은 body 제거 요청, `3cc6e08`은 resource 교체이며 초기 행렬 writer로 승격하지 않았다. `3a0b044`도 readiness/reset metadata 경로로 분리했다. raw Physics slot90/98 후보는 상태 보관용 할당/복구로 판독되어 pose writer의 근거로 사용하지 않았다.

### 3.2 실제 Fade helper 공급자 → 등록 → material consumer

**[판독]**, `helper_binding.c`, `fade_suppliers.c`, `fade_helper.c`, `fade_math.c`, `consumer_param_factory.c`:

```text
1243ba4: helper40B, VT5571220, +30/+38=0
 → VT slot25=1233928
     component holder+200 count/+208 array
     index1 component.vt+c8 → helper+30 model list
     index23 component → 0f5e51c("game__gfx__FadeOutCameraXluParam")
     native type555cdc0 확인 → helper+38 param
 → 1243c4c: inherited FadeType enum index resolution
 → 10aad20: enum index → {-1,1,2,3,4,5,7,8,9,105}
 → manager5812710, value!=-1이면10b2ba4
 → each actual model (type5556960), manager(type555cf90)
 → 10ae004: native variant creation/init, manager list registration
 → variant geometry + 10aff88 temporal
 → 10afabc cache check
     mode0: 1102f68 → 1103028 exact named parameter lookup
            → FRES offset → material buffer write/dirty bits
     mode!=0: 36aaa24 → model.vt+198 per-model/submesh alpha
 → 1243e98: manager8/10.vt60 remove each model
 → 12442c4: allocator free
```

`0f5e51c`는 이름 해시 `38a0d98`로 actual component resource의 상속 param map과 fallback map을 검색한다. helper에 실제 param 이름을 쓰는 공급자는 `1233928`이다. 이 연결은 `GrindRailParam`의 CameraAlpha 필드로부터 오는 것이 아니다.

## 4. 구조체·필드·상수·열거형 표

기준 객체를 혼동하지 않도록 raw Entity param R, 별도 Ragdoll param Q, Entity descriptor D, Entity body B, LayerPair LP, Fade node F를 구별한다.

| 기준/필드 | 타입·값 | writer → reader | 수준 |
|---|---|---|---|
| mesh owner O+70 | native H 포인터 | 3a715b4 →3a70974 | [실행] |
| O+48 / H+28 | 같은 info 포인터 | TAG0 원본 attach | [실행] |
| wrapper G VT | 5745be8, getType3a71210=8 | 3a70974 →body factory | [판독]/[실행] |
| G+b8 | native shape H | 3a70974 →vt70/98 getters | [판독] |
| B VT/+180 | 5749368 / LP 포인터 | 3af344c→3af6f88(vt90) | [실행] |
| nativeBody+98 | B userdata | 원본 body creation→native query filter | [실행] |
| LP+18 | 이전 all-mask fixture `ff8cffe0`; 실제 Default `1f8cffe0` | body default-table intersection | [실행], 두 입력의 차이 보존 |
| raw R VT57502e0+50/58/60/68 | 기본 `Default` 문자열 |3bb5c5c→3bb5d98 visitor | [판독], numeric mask 아님 |
| D88/8c | Ground/Ground →3/1 |3a403f4→3af6088 | [실행], 실제 FieldParent 입력 |
| Dbc/c4 | Enable/Blockable layer Default →`1fffffff` |3a403f4, cfg48/name390 | [실행]/[데이터] |
| Dc0/c8 | Enable/Blockable sublayer Default →`07ffffff` |3a403f4, cfg58/name3b0 | [실행]/[데이터] |
| 실제 LP8/10/18/1c | `43`/`07ffffff`/`1f8cffe0`/`07ffffff` |Entity3af344c→3af6088 | [실행], 원본 Default+Ground/Ground |
| 별도 Q74/Q48 | Ragdoll RestitutionScale/BuoyancyScale f32 |3ba38e0→3b2ad14 | [판독], Entity masks 연결 아님; §8.1 정정 |
| helper+30/+38 | modellist/param ptr |1233928→1243c4c/e98 | [판독] |
| param P+30/+34 | enum index u32 / inherited flag |10aa494/10aa5dc→1243c4c | [판독] |
| F+08/+10/+1c | primary/secondary model, submesh index |10ae004/init→10afabc | [판독] |
| F+20 | temporal count i32/u32 | constructor9999, reset99999→10aff88 | [판독]/[실행] |
| F+24 / F+34..3c | radius / object world XYZ |bbox/bone init→geometry | [판독], 실제 프레임 공급자 미확정 |
| F+70/+74 | out/in radius offset |default0/−.55; metadata10afe00→geometry | [판독] |
| F+78/+7c | out/in angle |default80/90; metadata10afe00→variant | [판독] |
| F+80..88/+8c | position offsets / FadeCount |default0/10; metadata10afe00→variant | [판독] |
| F+90 | flags byte |geometry→10aff88 | [실행], bit1이 bit0보다 우선 |
| F+94 | cached alpha f32 |init−1→10afabc | [실행] |
| F+98/+99 | output/renderer flags |init→10afabc/10afa20 | [판독] |
| F+9c | temporal N |variant constructor→10aff88 | [판독]/[실행] |

`10ae004`의 enum 값별 VT/N: 1→555d070/30, 2→555d0f8/10, 3·4→555d180/25, 5→555d208/20, 7→555d290/10, 8→555d318/10, 9→555d3a0/10, 105→555d428/20. enum **index**와 실제 값은 다르다. 초기 None index0→−1이며 등록하지 않는다.

## 5. 상태 전이와 전체 수명

**[판독] Fade:** 생성→모델/param bind→상속 index 확인→manager 존재와 None 조건→variant 등록→기하/시간 변화→alpha cache/consumer→모델별 remove→해제. 모델 없음/param 없음/manager 없음/None은 조기 우회한다.

**[판독]+[실행] temporal:** F90 bit1이 동시에 bit0보다 우선한다. bit1은 count를 내리고, bit0은 unsigned 증가/상한 처리를 한다. 두 bit가 없으면 count를 유지한다. 초기 `9999`와 reset `99999`를 동일값으로 정리하지 않는다.

**[판독] 모델 메타데이터:** `10afcb8`는 bbox/bone 초기 radius와 local offset, `10afe00`는 `FadeOutRadiusOffset`, `FadeInRadiusOffset`, `FadeOutAngle`, `FadeInAngle`, `FadeUnitPosOffsetX/Y/Z`, `FadeCount`를 읽어 base defaults를 덮는다. 실제 프레임의 bone/world/input-camera 공급은 §11에서 별도 남긴다.

**[판독] 붐:** 실제 mesh query 연결은 body 생성/AddBodies와 query reset 이후 실행했다. 원본 stage lifecycle 전체를 fixture world 초기화로 대체한 것은 §3.1.4의 실행 경계다. 최초 판독은 engine→game bodyset·등록 packet→같은 native world·camera 소비까지 좁혔다. **후속 §3.1.5에서 실제 slot68 dispatcher와 manager 조건을 해소**했지만 초기 pose writer의 마지막 동일성은 [미확정]이다. r9/r7의 distance→ratio·frame schedule을 신규 사례 수에 다시 더하지 않는다.

## 6. 계산식·조건·상세 의사코드

### 6.1 실제 지형 수평면 TOI 표본

**[실행]** 면 중심에서 Y+3→Y−3, 반경 f32(.3):

```text
distance = f32(f32(abs(startY-planeY)) - f32(.3))
fraction = f32(distance / f32(abs(endY-startY)))
native normal = (0, +1, 0)
```

8면 모두 distance bits=`402ccccd` (2.700000047683716), fraction=`3ee66667` (0.45000001788139343), normal `(0,+1,0)`였다. triangle370/371 tag10 y21, 612/788/716/792/715 tag29 y0, 1889 tag22 y4.099609375. listener entry bit0=1이었다. **초기 문장(2026-10-03):** “실제 camera 소비 법선 부호는 r9의 entry-bit 규칙을 적용한다. native+Y를 camera+Y로 그대로 바꾸지 않는다.” 이 경고만으로 항상 반전한다고 해석하면 안 된다. **정정 [실행]+[판독]:** 두 번째 query 소비 원본24dddd0..24dde08에서 entry.bit0=1은 point normal+c/10/14를 그대로 쓰고 bit0=0만 FNEG한다. 실제 표본 entry.bit0=1이므로 camera normal도 +Y이다. signed zero를 포함한128사례/384f32 비트 일치. 첫 query24dd8c0..dd8f8의 bit0=0은 접촉점에 separation×normal을 더하는 별도 처리이며 법선 전체 반전식이 아니다.

### 6.1.1 실제 가장 가까운 면 경쟁과 접촉점 연산 순서

**[실행]** actual5480 triangles에서 camera-enabled 수평면이 2~5개 겹치는16개 XZ를 선정했다. 내부 edge margin은 .35(반경.3+.05)보다 크며 가까운 비수평 면을 독립 geometry 선택에서 제외했다. 시작=maxY+3, 끝=minY−3, 독립 가장 가까운 면=maxY. 원본 broadphase가 실제 다른 높이의 면들과 경쟁한 뒤 비율·거리·법선·접촉점8필드씩128개를 비트 대조했다. 최종 actual Banc+helper+mask+태그 입력에서도 전부 일치했다. 이 선정 조건의 검증을 모든 임의 기울기/모서리 형상의 독립 기하 검증으로 확대하지 않는다.

접촉점은 면 Y로 강제 맞추는 방식이 아니다. 원본094ae10의 연산 순서:

```text
center = f32(start + f32(delta * fraction))
contact = f32(center - f32(radius * normal))
```

처음 기대값을 planeY에 맞춘 검사는 Y3.80078125와 원본3.800781488418579의 **1ULP 불일치**로 실패했다(`mesh_query_competition_verify_attempt1.json` 보존). 원본 f32 재구성 순서를 independent verifier에 반영한 뒤128개 모두 일치했다. 원본 출력을 허용오차로 가린 것이 아니다.

### 6.2 temporal 원본 `10aff88`

**[실행]**, 각 연산은 원본 i32/u32와 f32 순서를 유지한다.

```text
if flags & 2:
    n = min(i32(n), N)-1 if i32(n)>0 else 0
elif flags & 1:
    n = min(u32(n+1), u32(N-1))
a = clamp(f32(f32(i32(n))/f32(N-1)), 0, 1)
```

**2026-10-03 디컴파일 정정:** Ghidra C가 upper clamp를 도달 불가로 제거했지만 raw `10affe0: fmin s1,s0,1`은 실제 실행된다. C만 보고 상한을 없애면 count9999 유지 같은 입력에서 틀린다. 10,000 사례로 upper clamp 포함 비트 일치를 확인했다.

### 6.3 type1 `10afff4`

**[실행]** camera C, at A, object O, radius r:

```text
D = normalize(C-A), norm sum order z²+x²+y²
V = O-A
cross = (Vz*Dy-Vy*Dz, Vx*Dz-Vz*Dx, Vy*Dx-Vx*Dy)
dist = sqrt(cross.z²+cross.x²+cross.y²)
x = f32(f32(dist-r)/f32(-.55))
near = 1 if x<0 else f32(1-min(x,1))
dot = clamp(dot(normalizeXZ(A-C), normalizeXZ(O-C)), -1, 1)
F90.low2 = 2 if dot>0 else 1
alpha = clamp(f32(near+temporal()),0,1)
```

4,096 finite random 입력을 independent f32 계산과 대조했다. normalize 0-vector/NaN/general metadata override 분기의 전체 native 화면을 검증한 것은 아니다.

### 6.4 type2 `10b0300`, material cache `10afabc`

**[실행]** type2는 input+21 byte가 참이면 low2=1, 거짓이면2, `max(input+1c minimum, temporal())`다. 4,096 사례 비트 일치.

**[실행]/[판독]** cache는 `abs(f32(alpha-F94)) <= 2^-23`이면 consumer/cache를 갱신하지 않는다. 범위 밖이면 named alpha 또는 모델 alpha를 쓰고 F94를 갱신한다. 4,096 cache 검사는 primary/secondary model-null이라 named-parameter actual write는 §7의 판독 근거로만 분리한다.

Type3/4 `10b0350`, type5 `10b0908`, type7/8/9/105는 존재·factory 경로를 확인했으나 본 문서에서 독립 전체 수식 실행으로 확정하지 않았다. 알려진 일부 임계값을 공통식으로 확장하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

### 7.1 실제 alpha 최종 소비

**[데이터]+[판독]** DAT555d050의 원본 string descriptor는 hash=`47c1294a`, string ptr=`495e8eb`, 내용 **`fade_dither_alpha`**다. `camera_alpha`라는 임의 이름으로 문서나 웹을 구현하지 않는다.

`10afabc` mode0는 각 primary/secondary 모델 binding(model+148, stride80)에 `1102f68`을 호출한다. `1103028`은 실제 BFRES 명명 dictionary를 조회하고 없는 이름은 `ffffffff`를 반환한다. 존재하면 FRES parameter table의 row18B/+10 u16 offset으로 materialbuffer(binding+48)에 alpha를 기록한다. remap index≥0의 dirty bit, binding+2c bit0, model+14 state를 갱신한다. mode≠0는 `36aaa24`를 거쳐 model.vt+198에 모델/서브메시 alpha를 전달한다. GPU shader의 dither pattern 자체와 NVN blend/depth 화면 결과는 이 CPU write의 근거로 확정하지 않는다.

### 7.2 2026-10-03 기존 “잉크레일” 문장 정정

이전 [player_camera §6.8](player_camera.md) 문장: “가까운 물체를 반투명하게 하는 game::FadeOutCameraXluHelper … 와 잉크레일 파라미터의 CameraAlphaStartDist 1.0 / CameraAlphaEndDist 0.1 / CameraAlphaMin 0.5 / AlphaFrame 30 … 이 페이드는 물체 쪽 처리로 보이며 … [추정].”

**정정 [판독]+[데이터]:** visitor2061c5c의 VT5604110/getName2065754가 반환하는 실제 타입은 **`spl__GrindRailParam`**이다. creator20619a4는 +78 StartDist1.0(flag e9), +70 EndDist.1(flag ea), +74 Min.5(flag eb), +68 AlphaFrame30(flag ec)을 쓴다. `2063e1c`는 visitor2062f54 내부이다. 이 데이터는 InkRailOnline이나 helper의 직접 param이 아니다. helper의 실제 입력은 별도 `game__gfx__FadeOutCameraXluParam`의 FadeType이며 supplier1233928로 연결했다. GrindRail 전용 alpha runtime 관계는 이 정정만으로 common near fade 식에 합치지 않는다.

## 8. 다른 기능과의 상호작용

- **[판독]** Entity query wrapper/provider/body-pair backend의 위치가 다르면 원본 mesh가 있어도 no-hit가 된다. VT와 owner userdata가 query filter 동작에 참여한다.
- **[판독]/[실행]** Native body userdata는 실제 Entity B로 연결되며 vt90이 반환한 실제 LP를 filter가 소비한다. 초기 fixture D/8면의 근거는 보존한다. **2026-10-03 보강:** 최종 LP는 actual raw Ground/Ground+native Default masks+실제 RSDB ShapeTag bit28을 전체 reader/functor로 공급했으며, 비마스크·Banc SRT·최근접 경쟁까지 §3.1.2~4/6.1.1에서 연결했다. **후속 §3.1.5:** dispatcher source는 연결했으며 남는 경계는 world/query holder adapter와 실제 최초 pose writer/native 적용의 동일성이다.
- **[판독]** sensor3b08cdc는 Entity-world actor body가 아니다: native factory3c4f0b8→sensor world+c0, VT5749830/vt90=3b09a58→B188, B88 bit5. 기존 초기 후보에서 sensor를 지형 Entity로 잘못 부른 설명을 정정한다. 실제 Entity는3af344c→VT5749368/B180이다.
- **[판독]** Fade manager가 물체/모델/material을 갱신하는 것과 camera rig가 pos/at를 결정하는 것은 다른 소비 경로다. alpha를 붐 길이 비율로 대신 쓰지 않는다.

### 8.1 2026-10-03 Ragdoll compact Q와 Entity descriptor 오연결 정정

이 문서의 이전 §4 문장: “Q+74/+48/+64 resolved numeric mask, 3b2ad14→D+c4/c8/c0; raw→Q 미확정.” 이전 §11 다음 후보: “raw3bb5c5c/3bb5d98→runtimeQ resolver→3b2ad14→D”. **이 연결 해석을 철회한다.** 원본 reader 실행이나 D→LayerPair 연산을 철회하는 것이 아니다.

**정정 [판독]+[데이터]:** `3ba35d8`의 raw creator는 88B와 VT574f208을 만들고 `3ba7548`의 getName은 **`phive__RagdollBodyParam`**이다. 실제 typed visitor `3ba38e0`은 Q74를 **RestitutionScale f32(flag85)**, Q48을 **BuoyancyScale f32(flag86)**로 방문한다. 이 Q를 받는 `3b2ad14`는 별도 Ragdoll descriptor의 같은 수치 offset을 쓴다. Entity D의 c4/c8 mask와 외형상 offset이 같다고 같은 구조체로 연결하면 안 된다. `3b1f070`도 Ragdoll VT574a020 경로다. 원문 `ragdoll_param_correction.c`, focused `ragdoll_correction.json`을 보존한다.

실제 Entity raw R의 flags103..106을 읽는 새 원본 함수는 `3a403f4`이다. 원본 actual collections와 연결한 `entity_mask_probe_attempt3.json`에서 Default를 직접 정수 mask로 변환했다. compact Q를 거치지 않는다. 기존 `3af6088` D→LP512입력 원본 실행 자체는 유효하며 구조체 연결 해석만 정정한다.

## 9. 웹 포팅 구조와 구현 순서

웹 반영은 이번 분석의 범위 밖이며 아래는 반영 필요사항이다.

1. `impl/camera.md`: 원본 cameraquery7/mask8·반경.3·필터표/태그·entrybit polarity를 소비하는 질의와 실제 stage geometry/material userdata 공급을 맞춘다. 현 웹을 수정하거나 전체 필터가 동일하다고 선언하지 않았다.
2. `impl/camera.md`와 모델 renderer: 별도 `FadeOutCameraXluParam.FadeType`/enum값을 모델 metadata와 결합한다. 상태 count와 geometry→alpha→cache→materialdirty를 보존한다.
3. `fade_dither_alpha` 명명 slot이 있는 actual material에는 그 slot을 쓴다. generic opacity/blend로 대체하면 동등하지 않으므로 실제 shader dither consumer 추가 판독이 필요하다.
4. GrindRail CameraAlpha 필드는 owner가 다른 별도 동작으로 유지한다. 실제 source 타입·필드 이름을 보존하고 generic 가까운 물체 거리 1.0/.1 공식에 합치지 않는다.
5. 웹 권장 객체는 `NativeCameraQuery`, `NativeBodyLayerPair`, `ModelCameraFadeState` 등으로 둘 수 있으나 원본 클래스명으로 주장하지 않는다. f32 연산, enum index/value, temporal unsigned 증가, upper clamp를 구별한다.

## 10. 검증 코드·실행 결과·기대값

작업 위치 `C:/dev/splatoon3`; 명령과 실패는 `analysis/camera_100_r10/boom/commands.md`에 보존했다. 아래 각 결과는 마지막 JSON의 고유 사례이며, 같은 입력 재실행을 신규 사례에 중복 누적하지 않는다.

| 실제 명령(모두 `.venv/Scripts/python.exe -X utf8`) | 결과 | 원본 확인·경계 |
|---|---|---|
| `web/tools/r10_camera_boom_tag0_probe.py` | 실제 TAG0 attach, null/auto/fault0 | 원본 loader/native info |
| `web/tools/r10_camera_boom_mesh_query.py`, `r10_camera_boom_mesh_verify.py` | 초기8no-hit 보존; wrapper 정정8hit/40f32 불일치0 | 구체 Entity/VT/vt90/userdata→실제 broad/mesh/filter/TOI/listener, fixture D |
| `web/tools/r10_camera_boom_entity_mask.py`, `r10_camera_boom_entity_mask_verify.py` | attempt1/2 실패 보존;136이름+80mask;353사례/2118u32 불일치0 | actual named collections·상속/type·순차 실패; BYML→raw/allocator adapter |
| `web/tools/r10_camera_boom_mesh_query.py --authored`, verify 같은 flag | 8/40f32 불일치0 | actual Default masks; 비마스크/transform fixture |
| `web/tools/r10_camera_boom_mesh_query.py --descriptor`, verify 같은 flag | 8/40f32 불일치0;13 motion rows/Provider174u32 일치 | 전체 config/provider·실제 비마스크·전체 factory, transform fixture |
| `web/tools/r10_camera_boom_mesh_query.py --competition`, verify 같은 flag | 16/128f32 불일치0 | 실제2~5면 최근접 경쟁; 최초 plane snap1ULP 실패 보존 |
| `web/tools/r10_camera_boom_actor_source.py` | RSDB889사례 불일치0, null/auto/fault/PLT/libm0 | 실제 tag membership·원본 name indices69/65 |
| `web/tools/r10_camera_boom_mesh_query.py --stage-filter`, verify 같은 flag | 16/128f32 불일치0 | wholeGround functor/setter/packetflush로 LPbit28 공급 |
| `web/tools/r10_camera_boom_banc_source.py` | 실제 parser/defaults/matrix15f32 불일치0 | 실제 SDK sinf/cosf6회, 최초 double-hook 실패 JSON 보존 |
| `web/tools/r10_camera_boom_source_contract.py` | actualDefault/helper VT·slot 연결;128사례/384f32 불일치0 | 원본 init fragment/whole creator/factory/두 번째 camera normal 소비; 전체Actor 아님 |
| `web/tools/r10_camera_boom_mesh_query.py --actor-source`, verify 같은 flag | **최종16건/128f32 불일치0**, 실제 userdata/getter 일치, null/auto/fault0 | 실제 config/masks/nonmask/Banc/태그/helper→실제TAG0; create-info-to-body/holder adapters·slot68/pose writer 잔여 |
| `web/tools/r10_camera_boom_fade_emu.py` | temporal10000/type1 4096/type2 4096/cache4096=22288사례 불일치0 | 모델-null cache; 실제 material upload 실행 아님 |

**2026-10-03 후속 원문/기록 검증:** `next_*.c` 6파일에 새12함수 원문을 저장했다. 기존 manager `3c7f810`은 캐시를 재사용했다. `analysis/camera_100_r10/boom/next_record.py`는 고정분모106·4행 원문 SHA/next·실제 TAB5열12행·11절·원문 header·original Actor VT+d0를 검사하여 **28/28 PASS**를 기록했다. 이것은 저장 근거의 검증이며, 새 Unicorn 실행이나 새로운 수치 사례가 아니다. 실제 명령·실패는 `next_commands.md`, 결과는 `next_validation.json`에 보존했다.

Geometry/TOI/filter/type/name 검색에 계산 stub을 넣지 않았다. mesh native OS mutex/time/clock·allocatorFree 경계는 JSON과 기존 UC harness에 기록했다. 명시 world/query holder/BYML raw adapter는 실제 boot/frame 실행이 아니다. 두 번째 camera normal/Fade 검사는 PLT/libm/null/auto/fault0. Banc의 sinf/cosf는 원본 SDK를 실행했으며 호스트 수학식으로 대체하지 않았다.

결과 파일은 `analysis/camera_100_r10/boom/`의 `mesh_query_*`, `entity_mask_*`, `actor_tag_membership.json`, `banc_source.json`, `source_contract.json`, `fade_emu.json`이다. 초기 실패 JSON과 `mesh_query_actor_source_before_helper.json`도 보존했다. 독립 검증은 최종128mesh bits/384normal bits/15Banc bits/889tag cases/2118mask fields를 각각 구별하며 임의 합계로 전체 stage 확정률을 만들지 않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 고정 질문 | 원문 해소된 계약 | 고정 next까지의 최종 판단 | 정확한 남은 근거·다음 위치 |
|---|---|---|---|
| 4 벽/지형 회피 | 반경.3/query7/mask8/rate·원본 concreteVT/vt90/userdata·실제 mesh 최근접 경쟁; 후속 실제 Actor→component slot68 dispatcher | **조사중 유지** | §3.1.5: Banc/create-info→Actor current pose 최초 writer→3ae14b0 Entity/native 초기 pose 적용의 마지막 동일성 |
| 23 형상/반경/필터·rate/복귀 | literal 형상·반경·필터와 r7 rate/복귀, 새실제 raw→LP/태그/broadquery; 후속 dispatcher 해소 | **조사중 유지** | literal만 닫아 frozen next의 `Lby mesh broad-query·프레임`을 지우지 않는다. §3.1.5 동일 초기 pose 잔여 |
| 32 첫 붐·전진오징어+14ec | 기존 r7 480/480 +14ec·원본 첫 질의 접촉점 소비, 실제 body/filter 공급; 후속 등록 dispatcher 연결 | **조사중 유지** | 실제 frame 초기 pose writer 동일성; 첫 query entrybit은 법선 전체반전이 아님 |
| 38 웹.2/Ground/항상normal반전과 원본 차이 | 원본.3/query7/mask8·actual 필터·entrybit1 유지/0FNEG 확정; 후속 dispatcher 연결 | **조사중 유지** | 웹 차이 계약은 해소했지만 frozen frame의 동일 초기 pose writer 잔여를 유지 |
| 14 helper/기존 파라미터 관계 | supplier1233928→실제 FadeParam/type/helper→variant→named buffer/model alpha; GrindRail owner 정정 | **확정 추천 [판독]+[데이터]+[실행 보강]** | 전체NVN/allvariants/actual frame bone-camera 공급은 이 관계 질문 밖의 별도 미확정이며 이번실행으로 닫지 않음 |

시도한 generic `0f7400c` slotd0 loop는 engine Physics의 실제 slot68 dispatcher가 아니다. `3cc4a90→3a1476c`도 등록이 아닌 활성 조건 갱신이었다. `3a0be38`은 controller attachment 초기화, `3aec618`은 destructor이므로 body reset/source 해소로 세지 않았다. 직접 확인하지 못한 호출자를 유사 이름이나 fixture 성공으로 대신하지 않았다.

추가 미확정: Fade type3/4/5/7/8/9/105 전체 수식·원본 camera/bone supplier·각 Lby actor의 활성 조건은 manager10af620/variant VT에서 추적한다. `fade_dither_alpha` 실제GPU dither/혼합·UBO upload는 실제 BFRES shader/NVN 경로에서 추적한다. 모델-null cache22288의 일부 성공으로 GPU까지 승격하지 않는다.

담당 frozen5행 중 확정 추천 **1/5(20%)**, 나머지4행 조사중이다. 분모106 및 각 질문의 next를 그대로 유지한다. 전체 카메라 완료율은 parent가 중앙 inventory 고유행으로 계산한다. 위 마지막 writer/dispatcher 둘 다 미연결이라는 문장은 최초 마무리 시점의 판단이었다. **2026-10-03 후속 정정:** dispatcher는 §3.1.5에서 실제 Actor VT와 manager 조건에 연결했다. 현재 보류 이유는 마지막 초기 pose producer/native writer 동일성이다. 이번 후속 frozen4행의 새 전체 확정은 **0/4**이며 부분 결과로 확정률을 올리지 않았다.

후속 기록은 `analysis/camera_100_r10/boom/next_commands.md`, `next_notes.md`, 실제 TAB 5열 `next_functions.tsv`, 기존 frozen row SHA와 next를 보존한 `next_recommendations.json`이다. 기존 `recommendations.json`과 성공/실패 JSON은 덮어쓰지 않았다. 사용자 종료 요청 뒤 새 함수 추적은 수행하지 않고 이미 요청한 decompile 결과만 수집·문서화했다. 새 Unicorn 수치 검증은 없으며 기존 native 사례를 재실행/재누적하지 않았다.
