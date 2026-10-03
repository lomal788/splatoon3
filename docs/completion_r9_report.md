# r9 종료 보고 — FillUp 집중 분석 및 현재 결과 MD 반영

2026-10-03. 사용자의 최신 지시 “여기서 작업 마무리하고 지금까지 분석한 거 MD 업데이트”에 따라 신규 원본 분석을 종료했다. 모든 에이전트가 현재 결과·실패·경계를 저장하고 마무리했다. 이번 종료는 과거 물리/카메라100% 목표의 달성 보고가 아니다.

## 1. 핵심 체감과 이번 결과

원본 Lby_Lobby00 1인 연습의 카메라·접촉/형상·캐릭터 ASB/cloth·이펙트 생성·효과음 제한을 분석했다. 마지막에는 FillUp의 데이터 입력→원본 프리셋 등록→실제 형상 콜백→플레이어 접촉 분류/보조 탐색을 우선했다. **전체 고정 목록556/986=56.39%, r9 신규 전체확정27개**다. 큰 복합 질문 일부를 검증했다고 전체확정으로 바꾸지 않았다.

## 2. 원본·범위·기준

작업/임시 파일은 `C:\dev\splatoon3` 안에만 저장했다. Splatoon3 v0 Lby_Lobby00, 분석 전용. r7 질문·분모·범위·분류를 고정한1119행(범위내986/범위밖130/집계제외3)을 유지하고 r8 종료529확정을 r9 시작 상태로 썼다. 안정ID의 문서:L번호는 최초inventory 위치이며 이후 MD 줄이 늘어도 ID를 변경하지 않는다. 여러 영역에 대응하는 질문은 전체986에서 한 번만 센다.

## 3. 병렬 작업 정리와 자료 소유

물리 담당은 회전pose/침투보정/FillUp fallback, 카메라 담당은 카메라 및 FillUp 동적 리소스·형상 콜백, 그래픽 담당은 ASB/cloth/FX 및 FillUp 저작 형상 데이터를 마쳤다. root는 효과음/구–사각형TOI/FillUp 프리셋 등록과 공용 집계·정정·목차를 반영했다. 각 영역의 실제 명령/실패는 `analysis/completion/r9/*_commands.md`, 결과는 같은 폴더 JSON, 새 디컴파일은 `analysis/decomp/r9_*`에 보존했다.

## 4. 고정 목록의 최종 확정률

| 영역 | r8 확정 | 최종 확정/분모 | 최종 확정률 | r9 신규 | 기존 목표 | 이번 상태 |
|---|---:|---:|---:|---:|---:|---|
| 물리 | 51 | 52/56 | 92.86% | 1 | 100% | 미달·현재 기록 마감 |
| 카메라 | 67 | 78/106 | 73.58% | 11 | 100% | 미달·현재 기록 마감 |
| 그래픽 | 97 | 102/204 | 50.00% | 5 | 50% | 충족 |
| 피격 | 59 | 59/118 | 50.00% | 0 | 50% | 충족 |
| 이동 | 66 | 66/133 | 49.62% | 0 | 50% | 미달·현재 기록 마감 |
| 탄 | 32 | 32/50 | 64.00% | 0 | 50% | 충족 |
| 표적 | 33 | 33/39 | 84.62% | 0 | 50% | 충족 |
| 이펙트 | 33 | 35/85 | 41.18% | 2 | 50% | 미달·현재 기록 마감 |
| 도색 | 52 | 52/100 | 52.00% | 0 | 50% | 충족 |
| 효과음 | 30 | 38/86 | 44.19% | 8 | 50% | 미달·현재 기록 마감 |

물리 잔여4개, 카메라 목표까지28개, 이동1개, 이펙트8개, 효과음5개가 남았다. 이 숫자는 이전 목표까지 필요한 whole확정 수다. 그래픽·피격·탄·표적·도색은50% 이상이지만 전체100%는 아니다. HUD 및 복합 대응을 포함한 전체986의 세부 상태는 [analysis_completion.md](analysis_completion.md), 이번42개 상태/근거 갱신은 [completion_r9.md](completion_r9.md)에서 확인한다.

## 5. FillUp 입력·상태 수명·소비

**[데이터]** [fillup_authored_data.md](gimmick/fillup_authored_data.md): 원본Actor/Scene3679팩·bphsh1485개·재질3017행, FillUp39행/28Actor팩/19고유shape, Banc105개/FillUp배치40개/Scene13개. BYML40020개는byte검색 수이고 전부 구조파싱한 수가 아니다. 오류/누락0. “모든FillUp이수직”은 원본위/아래/경사면 반례로 정정했다.

**[데이터]+[판독]** [fillup_dynamic_sources.md](physics/fillup_dynamic_sources.md): Lby정적48root+플레이어/슈터/탄5root, 원본부모/Bootup/예약참조338방문·310고유리소스, preset21종에서FillUp입력0/누락0. 실제 `10036a8→3a49c44→콜백→3a513d0`의 태그복사 명령을 확인했다. 모든임의runtime태그쓰기부재나 resolver전체실행으로 확대하지 않는다.

**[실행: 정수 등록]+[판독]+[데이터]** [fillup_preset_runtime.md](physics/fillup_preset_runtime.md): 원본로더3b0f3d8에실제PhiveConfig를 주어49tag+50Entitymask+108preset×10=1179정수필드0bad. FillUpPlayer[61]은tag10000000/valid1, Entitymask62/valid1, 나머지layer0/미지정. allocator/statefixture와무관powf812handler경계는§10에명시했다.

## 6. FillUp 원본 계산·상수·예외

**[판독]+[실행: query결과 공급]** [fillup_contact_runtime.md](physics/fillup_contact_runtime.md), [fillup_fallback.md](physics/fillup_fallback.md): parent원본2048+helper4096=6144사례/**189734 scalar필드bit불일치0**. 원본iterator/math/control을 실행하고 nativequery 결과만 합성입력으로 공급했다.

최고 유효접촉이 FillUp/Water/Slide이면 대체 탐색, Fence/KeepOut이면 높이−.35후재query다. outputY는최종태그분류전에기록한다. offset0은false, 보조탐색은±80°초기query와성공후3회이분, 각도절대값동률은음수측을선택한다. **helper는태그·법선Y를재검사하지않고, querytrue이면서모든후보가제외되면true와기존출력좌표를그대로유지한다.** linkediterator는contact+68bit8필수이며array는그조건이없다. 실제이상한동작도원본그대로기록했다.

## 7. 다른 영역에서 확정한 것

| 영역 | 신규 원본 근거·검증 | 확정 수준·문서 |
|---|---|---|
| 물리 | 특수13캐릭터의 실제 native등록·선cap20000/각10000/감쇠0/중력0/time1, 신규whole1 | [판독]+[실행]+[데이터], [character_controller.md](physics/character_controller.md) §4.2 |
| 물리 부분 | rotation4097/98328필드·실제연결352필드, EPAplane/bary각4097 및실제624필드0bad, sphere–quad5120/25150필드0bad | [실행: 명시입력군]+[판독], [rotation_pose.md](physics/rotation_pose.md), [penetration_recovery.md](physics/penetration_recovery.md), [sphere_quad_toi.md](physics/sphere_quad_toi.md); TOI전체승격0 |
| 카메라 | 상태/snapshot/부품커브/붐후속혼합·원본7/8필터입력과nativeSphereCapsule연결·충돌감쇠, 신규whole11 | [판독]+[실행]+[데이터], [r9_lifecycle.md](camera/r9_lifecycle.md), [r9_boom_query.md](camera/r9_boom_query.md), [r9_collision_spring.md](camera/r9_collision_spring.md), [r9_state_sources.md](camera/r9_state_sources.md) |
| 그래픽 | ASB헤더 실제2파일+mask1024, typed태그1536, cloth감쇠4096+적분1024, Standard1054/Bend2060 모두0bad, 신규whole5 | [판독]+[실행]+[데이터], [asb_header_runtime.md](graphics/asb_header_runtime.md), [asb_typed_tags.md](graphics/asb_typed_tags.md), [cloth_damping_runtime.md](graphics/cloth_damping_runtime.md), [cloth_link_runtime.md](graphics/cloth_link_runtime.md) |
| 이펙트 | game→SDK원본OneEmitter2048사례/293레코드byte0bad, 신규whole2 | [판독]+[실행], [one_emitter_runtime.md](effect_sound/one_emitter_runtime.md) |
| 효과음 | 4종limiter정렬→적용4096/168710필드, 정지envelope768생성/10284진행, prioritychain2048/94208필드0bad, 신규whole8 | [판독]+[실행]+[데이터], [sound_limiter_runtime.md](effect_sound/sound_limiter_runtime.md), [sound_runtime_filters.md](effect_sound/sound_runtime_filters.md) |

이동·피격·탄·표적·도색의 r9 신규whole확정은0이며 이전근거를유지했다. 충돌closest/support32768/724904필드0bad도 부분보조근거이며 전체TOI를완료하지않았다(`analysis/completion/r9/physics_gjk_support.md`). 리셋의원본pitch상한+45 삭제오판 등은 [r9_reset_contexts.md](camera/r9_reset_contexts.md)에 날짜정정했다. GPU전체/전체pose/DSP출력은 이 CPU함수검증으로확정하지않는다.

## 8. 표현·상호작용과 해석 정정

FillUp tag bit28과 body.filter bit28은 기준객체가다르다. bitmask값과collection배열순번을구분한다. towerFillUpType는별도상태이지만실제Gachiyagura의FillUp→Vlift_FillUpP형상은같은tag28을쓴다. 전부무관/전부수직으로단정하지않는다. [collision_mesh.md](gimmick/collision_mesh.md) §3.4.5~7·§4·§11에이전결론을남기고2026-10-03정정이유를추가했다.

## 9. 웹 반영 필요 목록

이번 코드는 변경하지 않았다. 적용 요구는 공용inventory의웹반영열과각본문에만저장했다.

| impl 대응 | 향후 원본값/순서 반영 |
|---|---|
| physics.md | 특수13nativecap, tag/filter분리, FillUp예외·출력선기록·±80°3이분·음수동률·linkedbit8, Bootup공용shape참조. 원본Lby에없는FillUp면추가금지 |
| camera.md | 원본boom반경.3·layer7/mask8·상대허용, native법선부호/포즈혼합, 충돌offset감쇠누적, scene/Jump분모/모듈리셋pitchclamp |
| render.md·assets.md | ASBheader18을AS슬롯수에서이름maskgroup수로정정, typedreader/override비트, nativef32cloth감쇠·invMass가중·제자리갱신 |
| fx.md | OneEmitter두admission/capacity/generation·행렬전치, 4종limiter각정렬/보호비트, group0.016초단위정지시간, 원본priority/serial/필터선택 |
| physics.md·weapon.md의잔여 | 미완전체TOI/solver를부분실행식으로채우지않음. 마지막필드바인딩과nativegeometry전체증거필요 |

## 10. 실제 명령·실패·보호 검증

작업폴더는 `C:\dev\splatoon3`. 새디컴파일은항상SHARED/FUNCS/decomp_index/func_lookup로기존여부를확인하고기존원문은재사용했다. 대표적으로실제로실행한명령:

```powershell
.venv/Scripts/python.exe web/tools/r9_physics_fillup_fallback_emu.py
.venv/Scripts/python.exe web/tools/r9_physics_fillup_parent_emu.py
.venv/Scripts/python.exe web/tools/r9_physics_fillup_preset_emu.py
.venv/Scripts/python.exe web/tools/r9_fillup_actor_source_audit.py
.venv/Scripts/python.exe web/tools/r9_fillup_actor_resource_closure.py
.venv/Scripts/python.exe web/tools/r9_physics_sphere_quad_emu.py
.venv/Scripts/python.exe web/tools/r9_physics_sphere_quad_oblique_emu.py
.venv/Scripts/python.exe analysis/completion/r9/merge_progress.py
```

최종결과는각문서§10/JSON에보존했다. 실패도보존: FillUp초기G0오인으로분류2196bad→원본staticwriter값정정, 프리셋시험heap/CF버퍼경계3회실패→명시allocator/state와충분버퍼로정정, sourceclosure플랫폼접미사누락14→올바른원본참조로정정, sphere–quad독립참조199bad→signed−0·선상한reject순서정정, barycentric898bad→원본f32합순서정정, clothinverse-sqrt첫case14실패→독립estimate구간정정, soundlimiter297bad→pause참조정정. PowerShell PATH/sh·rg와일드카드·func_lookup오귀속·미존재파일조회·문법실패도각commands로그에그대로기록했다.

보호기준592개(게임580/스크립트3/impl8/package1)는해시변경0·추가0이다. SHARED/FUNCS의기존byteprefix를해시로확인해추가만했다. original에는쓰기작업을하지않았으며키값을복사하지않았다. commit/push/대형파일삭제·이동없음. 집계는기존분모1119/986·분류/ID/우선순위를고정검증했고지원manifest를whole승격0으로명시처리했다. 최종검증: 새/갱신 요약 문서23개 모두11절, 확인한local링크77개 누락0, 최종proofJSON5개0bad, 보호592개변경/추가0, SHARED/FUNCS기존prefix보존. `analysis/completion/r9/final_finish_audit.json`에저장했다.

## 11. 미확정·확정 불가·다음 근거

**FillUp의 기능적인경로를확인했어도역사적이름의“구멍메우기”목적은[미확정]이다.** 원본릴리스전체형상/이름/배치, 프리셋로더·형상소비자·접촉fallback까지시도했으나제작자의목적설명이없다. 다음은원본DCC저작소스·exporter주석·제작자의태그설명이다. 따라서L148은조사중유지하고확정률에더하지않았다.

물리L359/L495/L508은모든primitive/mesh/TOI/침투topology/solver/live입력경로가닫히지않았다. 카메라는실제terrain/FieldRigidBody/TAG0전체붐query·최종화면/리셋context등의경계를유지한다. 그래픽은GPU/최종pose/조명전체, 이펙트는birth/GPU전체, 효과음은customspatial/SLinkUserlimit/최종DSP가남았다. 상세다음주소·시도·실패는각11절과analysis_completion.md의next열에기록했다. 다음분석을요청받으면이현재고정ID와저장근거에서이어가며기존분석을재집계하지않는다.
