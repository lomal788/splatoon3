# 스테이지 구성과 기믹 (목차)

Splatoon 3 v0 대전 스테이지 8개의 배치 데이터 → 액터 → 파라미터 → 코드 동작을 정리합니다. 기준 스테이지는 **Vss_Yagara(ヤガラ市場)**이고, 잉크레일·스펀지·이동 발판은 코드 판독까지, 지형 충돌 메시는 형식 판독과 변환(glb)까지, 나머지는 데이터와 클래스 수준까지 추적했습니다.

| 문서 | 내용 | 상태 |
|---|---|---|
| 이 문서 | 스테이지 로딩 흐름, Banc 포맷, 모드 레이어, 8개 스테이지 기믹 표, 웹 구조 | 분석 진행 |
| [inkrail.md](inkrail.md) | 잉크레일(InkRailOnline): 상태·수명·연장·접촉·탑승·이탈 | 핵심 판독 완료(3차: 탑승 금지 조건표·최근접점·끝/이탈 분기 전체, 끝 자동 이탈 없음으로 정정), 일부 플래그 의미 미확정 |
| [sponge.md](sponge.md) | 스펀지: 피해→크기, 크기 동역학, 충돌 박스, SafePos/Linked | 핵심 판독 완료(3차: 박스 중심 = 뼈 root_sub, SafePosLinks = 적 팀 착지 대체), 애니 궤적 미확정 |
| [stage_misc.md](stage_misc.md) | 이동 발판(일정·이동 법칙·좌표계·회전 판독+재구현), 고정 맵 파츠, 장외·사망 박스, 사망 이유 열거형, 칠 가능 영역, 스폰, 히어로 모드 기믹 | 이동 발판 판독 완료(3차: 레일 행렬·부모 변환·Bravo 회전), 히어로 모드 리플렉션 정정·간헐천 판독, 그 외 데이터 수준 |
| [collision_mesh.md](collision_mesh.md) | 지형·파츠 충돌 메시(Havok hknpMeshShape) 형식·디코드·삼각형별 재질, Yagara glb | 형식 판독·전수 데이터 검증 완료(3차: 섹션 키 기준 판독, 내부 비트필드 데이터 분석), glb 1개 출력 |

표기: **[실행]** 원본 실행 확인(이 영역에는 없음), **[판독]** 원본 명령/디컴파일 판독, **[데이터]** 데이터 확인, **[재구현]** 파이썬 재구현 계산, **[추정]**, **[미확정]**. 웹 구현은 없습니다("분석 진행" ≠ "구현 완료" ≠ "검증 완료").

## 1. 자료 위치

| 항목 | 경로 |
|---|---|
| 스테이지 목록 | RSDB `VersusSceneInfo`(8행: Id·DisplayOrder·Season 0), `SceneInfo`(Label, PreloadResource `Model/Fld_<이름>.bfres`, SequenceName "Versus") [데이터] |
| 씬 팩 | `romfs/Pack/Scene/Vss_<이름>.pack.zs` (해제본 `analysis/gimmick/pack/Scene_Vss_Yagara/`) |
| 배치 | 씬 팩 안 `Banc/Vss_<이름>.bcett.byml` = `extracted/params/Banc/Vss_<이름>.bcett.byml.json` |
| 액터 팩 | `romfs/Pack/Actor/<Gyaml>.pack.zs` |
| 지형 | `Pack/Actor/Fld_<이름>.pack.zs`(모델 `Fld_<이름>.fmdb` + 서브모델, 충돌 `Phive/Shape/Dcc/Fld_<이름>.Nin_NX_NVN.bphsh`) |
| 베이크 | `romfs/Bake/Scene/Vss_<이름>_<모드>_Day.bkres.zs` (SceneBake의 모드별 소스) |
| 도구 | `web/tools/gimmick_stage.py`(요약·재구현), `gimmick_phive.py`(충돌 재질표), `collision_tag0.py`·`collision_mesh.py`·`collision_scan.py`(충돌 메시, [collision_mesh.md](collision_mesh.md)), `collision_interior.py`(내부 프리미티브 비트필드 상관), `gimmick_lift.py`(이동 발판 일정·자세 재구현), `gimmick_reflect_fix.py`(리플렉션 방문 함수 역할 기준 재판독 — 커브 필드 뒤 오프셋 정정), `gimmick_funcs.py`(함수 시작 후보·호출자), `gimmick_annot.py`(디컴파일 문자열·f32 주석, 파라미터 체인 접기) |
| 산출물 | `analysis/gimmick/`(스테이지 요약 JSON, 시뮬레이션 결과 `sim_results.json`·`lift_sim_carousel.json`, 재질표, 팩 해제본, 파라미터 리플렉션), `analysis/collision/`(Yagara 충돌 glb·통계, 전수 스캔), `analysis/stage/`(3차: `lift_sim_carousel_rot.json`, `hero_param_reflect_fix.txt`, `interior_bitfield_yagara.txt`), 디컴파일 `analysis/decomp/gimmick/`(`lift_rail.c`, `lift_rail_adapter.c`, `hknp_mesh*.c`), `analysis/decomp/stage/`(3차: `lift_rail_matrix.c`, `lift_rail_class.c`, `rail_mgr_sponge.c`, `inkrail_ride_full.c`) |

## 2. 스테이지 로딩 흐름 [데이터]

```
VersusSceneInfo 행 "Vss_Yagara"
 → Pack/Scene/Vss_Yagara.pack.zs
    Scene/Vss_Yagara.engine__scene__SceneParam  ($parent VersusRcParent: Sequence Versus, SceneBgm Versus)
      Components:
        StartupMap        Work/Banc/Scene/Vss_Yagara.bcett.json → Banc/Vss_Yagara.bcett.byml
        VersusMapInfo     {Id 3, DisplayOrder 3, Season 0}
        VersusCamera      미니맵·결과 카메라(CameraPoserFixedParam), 관전 CameraInfo
        SceneBake         모드별 베이크 소스(Pnt_Day, Var_Day, Vcl_Day, Vgl_Day, Vlf_Day)
        SceneGfxFieldEnv  Day/Night/Sunset 렌더 설정, Ocean(Vss_YagaraWater)
        SceneSoundEnv, SceneGraffitiPlacementData
 → Banc: Actors[] / Rails[]
    각 액터: Gyaml 이름 → Pack/Actor/<이름>.pack.zs → ActorParam($parent 체인)
       Behavior.ClassName → 코드 클래스(vtable, web/docs/02 §3)
       GameParameterTable → 파라미터 구조체($type) → 코드 리플렉션
```

로더 코드(StartupMap 해석, 레이어 필터)는 판독하지 않았습니다. 레이어 의미는 이름·분포로 정한 **[데이터+추정]**입니다.

## 3. Banc 포맷 [데이터]

최상위 `{Actors[], Rails[], FilePath}`.

| 키 | 내용 |
|---|---|
| `Gyaml` | 액터 이름(`InkRailOnline`) 또는 전체 경로(`Work/Actor/Mpt_KeepOutPlayer.engine__actor__ActorParam.gyml`) |
| `Hash` | u64 인스턴스 ID. `Links[].Dst`, Banc 파라미터의 참조(`LinkToPoint`, `SafePosLinks`, `ToTarget_Cube` 등)가 이 값을 가리킴. 레일 점도 Hash를 가짐 |
| `Layer` | 모드 레이어(아래) |
| `Translate`/`Rotate`/`Scale` | 월드 위치, 라디안 오일러(적용 순서 [추정]), 스케일. 없으면 0/0/1 |
| `TeamCmp.Team` | Alpha / Bravo / Charlie(트리컬러) / Neutral |
| `Links[]` | `{Dst: Hash, Name: 링크 이름}` |
| `<타입>BancParam` | 인스턴스별 파라미터(`spl__InkRailBancParam`, `spl__SpongeBancParam`, `game__RailMovableSequentialParam` 등). 코드에서 GameParameter와 같은 리플렉션 구조체로 읽음 [판독 — InkRailBancParam 방문 `0x71020703f0`] |
| `Bakeable`, `SRTHash`, `InstanceID`, `Phive.Placement.ID` | 에디터·베이크용 |

`Rails[]`: `{Gyaml(LiftRail/GeneralRail/GachiyaguraRail), Hash, IsClosed, Layer, Points[{Hash, Translate, <노드 파라미터>}], Rotation}`. 잉크레일 레일은 점 사이 직선입니다([inkrail.md](inkrail.md) §6.1).

### 3.1 레이어 = 모드

| 레이어 | 의미 | 근거 |
|---|---|---|
| Cmn | 모든 모드 공통 | 지형 `Fld_*`가 항상 Cmn |
| Pnt | 나와바리(Turf War) | 베이크 `_Pnt_Day`, 다른 모드 오브젝트 없음 |
| Var | 가치에리어 | `PaintTargetArea_Cube`가 Var에만 |
| Vlf | 가치야구라 | `Gachiyagura_3M`, `GachiyaguraRail`, KeepOut 박스 |
| Vgl | 가치호코 | `Gachihoko`, `LocatorGachihoko*`, `GachihokoGoal` |
| Vcl | 가치아사리 | `GachiasariGoal`, `LocatorGachiasariClam*` |
| Tcl | 트리컬러(페스) | Charlie 팀 스폰 |
| Day/Night/Sound | 조명·사운드 | |

웹 로더 규칙(권장): `Layer ∈ {Cmn, 선택 모드}`인 액터·레일만 생성. Day/Night/Sound는 그래픽·사운드 담당 판단.

## 4. 8개 스테이지 기믹 분포 [데이터 — `gimmick_stage.py all`]

R 잉크레일, S 스펀지, L 이동 발판, K KeepOutPlayer, D PlayerDead 박스, P ChangePaintableArea, M 고정 맵 파츠.

| 스테이지(라벨) | Cmn | Pnt | Var | Vlf | Vgl | Vcl | Tcl |
|---|---|---|---|---|---|---|---|
| Vss_Yunohana(ユノハナ渓谷) | P8 | P29 M13 | P29 M13 | K20 P19 M6 | P21 M13 | P27 M9 | — |
| Vss_District00(ゴンズイ地区) | P16 M6 | S2 P11 M16 | S2 P16 M14 | K8 P15 M13 | P21 M26 | S2 P7 M11 | — |
| **Vss_Yagara(ヤガラ市場)** | S2 P6 M1 | **R2 S4** P15 M21 | R2 S4 P15 M19 | S4 K12 P4 M10 | R2 S2 P21 M23 | R2 S4 P17 M17 | 스폰만 |
| Vss_Temple00(マテガイ放水路) | **D10** P4 M4 | S4 P18 M17 | S2 P20 M19 | S4 K16 P12 M11 | R2 S2 P12 M18 | S4 P20 M20 | — |
| Vss_Scrap00(ナメロウ金属) | — | S2 P4 M10 | S2 P4 M10 | S2 K16 M3 | P2 M14 | P2 M10 | — |
| Vss_Kaisou03(マサバ海峡大橋) | P26 M4 | S2 P17 M14 | S2 P18 M12 | S2 K10 P24 M19 | P25 M19 | S2 P23 M14 | S4 |
| Vss_Upland03(海女美術大学) | P10 M1 | P17 M17 | P19 M19 | R2 P20 M28 | R2 P24 M22 | R2 S2 P20 M21 | S2 M4 |
| Vss_Carousel(スメーシーワールド) | R2 P4 M3 | L4 P54 M10 | P58 M11 | L4 K2 P50 M12 | L4 P42 M16 | L4 P34 M8 | — |

- v0 대전에는 점프대·간헐천·파이프라인·그라인드 레일 배치가 없습니다(히어로 모드 전용, [stage_misc.md](stage_misc.md) §7).
- 철망(그레이팅)은 별도 액터가 아니라 충돌 재질 `Fence`/`RopeNet`(UserShapeTag Fence, 프리셋 SplFence = 잉크·오징어 통과) 면입니다. Upland03 `Mpt_UplandNet`, Scrap00 `Mpt_FldObj_Scrap00_Net`도 맵 파츠입니다 [데이터].

## 5. 공통 규칙

| 규칙 | 내용 | 근거 |
|---|---|---|
| 시간 | 60fps 프레임. 초 단위 파라미터는 `sec*60` 후 int 절삭 | InkRail `0x710217b514` 등 [판독] |
| 파라미터 상속 | 필드별 "설정됨 플래그"가 켜진 가장 가까운 `$parent` 값, 없으면 생성자 기본값 | [bullet] 공유 사실 [판독] |
| 팀 | 액터 +0x668: 0, 1, 3(중립), -1(없음) | InkRail·Sponge 판독, Alpha=0 [추정] |
| 피해 단위 | 0.1 HP | [combat] 공유 사실 |
| 바이어스 곡선 | `|x|^(-log2 b)`, b=0.5면 항등 | [inkrail.md](inkrail.md) §7.4 [판독] |
| 프레임 카운터 | `[[0x7105790610]+0x148]` u32 | 마감 비교 [판독] |
| f32 | 원본 f32 연산 → 웹 `Math.fround` | [bullet] 권장 |

## 6. 웹 포팅 구조

```
StageLoader
  loadScene(name)            Scene pack → SceneParam → Banc JSON (사전 변환: spl_data.py → JSON)
  filterLayer(mode)          Cmn + 모드 레이어
  railGraph                  Rails → {hash → point}, 구간 길이(f32)
  actorFactory(gyaml)        ActorParam $parent 병합(필드 단위) → ClassName 별 생성
     "spl::InkRail"  → InkRail      (inkrail.md)
     "spl::Sponge"   → Sponge       (sponge.md)
     Lft_* + AILift(BlitzCompatibles) → RailMover (stage_misc.md §1.3, 일정·이동 법칙 판독)
     Mpt_KeepOutPlayer / Mpt_PlayerDead → TriggerBox(tags)
     LocatorSpawner / LocatorVersusStart → SpawnTable
     ChangePaintableArea → paint 모듈로 전달
  collision                  Fld/파츠 bphsh → 사전 변환 glb(삼각형별 shapeTag·재질·필터) (collision_mesh.md)
GimmickWorld.update(frame)   (서버 권위, 클라 동일 코드로 예측)
  1. 피격 이벤트 분배(InkRail.onDamage, Sponge.onDamage)
  2. 각 기믹 update(now)
  3. 접촉/탑승 처리, 탑승자 갱신
  4. 넷 상태 스냅샷(InkRail: life, deadline, team, connected / Sponge: SpongeNetState)
```

에셋 변환: 액터 팩·씬 팩은 `spl_data.py unpack --json`, 모델은 [graphics]의 bfres→glTF 도구, 충돌은 `web/tools/collision_mesh.py`(bphsh → glb, [collision_mesh.md](collision_mesh.md)).

## 7. 검증 요약

| 항목 | 종류 | 결과 |
|---|---|---|
| 8개 스테이지 레이어·기믹 분포 | [데이터] 도구 집계 | §4 표, `analysis/gimmick/*_summary.json` |
| Yagara 잉크레일 길이·연장·수명 | [재구현] | 15.1593 / 16프레임 / 900프레임 연결 / 30프레임 해제 |
| 탑승 가속·최대 속도·이탈 속도 | [재구현] | 5프레임째 0.192 도달, 이탈 (v.x−dz·s·0.01, 0.3v.y+0.19, v.z+dx·s·0.01) |
| 스펀지 1발 응답 | [재구현] | Small_3p0 sLin 1.288, 8프레임에 1.259 |
| 지형 충돌 재질표 | [데이터] | `analysis/gimmick/fld_phive_materials.txt` |
| 충돌 메시 디코드 | [데이터] 전수 + [판독] 엔진 디코드 | bphsh 1485개 전부 hknpMeshShape, 650개 bbox가 ShapeParam AutoCalc와 오차 ≤ 9.5e-7, Yagara 삼각형 5103·재질 27종 → `analysis/collision/Fld_Yagara_col.glb` |
| 이동 발판 일정 | [재구현] `gimmick_lift.py` | Carousel MoveA/MoveB 모두 60초 주기, MoveA 첫 이동 4초 시작 |
| 이동 발판 자세(회전) | [재구현] `gimmick_lift.py`(3차) | Alpha 회전 단위, Bravo 회전 Y축 180°(레일 Rotation 출처), 위치 Bravo = −Alpha → `analysis/stage/lift_sim_carousel_rot.json` |
| 리플렉션 커브 정정 | [판독] `gimmick_reflect_fix.py` | GrindRail 2필드·Pipeline 6필드 정정, Geyser/JumpGimmick/GeyserParam 무결 |
| 내부 비트필드 | [데이터] `collision_interior.py` | 166파일 3667섹션 길이 = ceil(n/8), Yagara 비트1 275개 전부 닫힌 모서리, 92% 볼록 모서리 없음 |

원본 실행 대조는 없습니다. 재구현은 판독식 옮김 + 합성 입력이며 "동작 검증 완료"가 아닙니다.

## 8. 미확정 (영역 전체)

| 항목 | 이유 / 필요한 것 |
|---|---|
| Banc 레이어 필터·로더 코드 | StartupMap 로더 미판독(데이터 분포로만 결정) |
| Rotate 오일러 적용 순서 | 레일 Rotation(라디안)·노드 Rotation(도)은 R = Rz·Ry·Rx **[판독]**. 액터 Rotate는 같은 규약 [추정] |
| 이동 발판 좌표계·회전 | **해소 [판독]** stage_misc §1.5(레일 위치 = R1·R0ᵀ(p−T0)+T1, LiftRail 부모 단위, 회전 = 점 회전 slerp, Bravo 회전 = 레일 Rotation). 남은 것: 시간 원점 보관 객체의 초기값, 출력이 액터 배치 행렬을 대체하는지(데이터상 동일) |
| 충돌 메시 남은 부분 | 섹션 키 기준은 **해소 [판독]**, 용접 비트필드는 [데이터+추정]으로 축소. 남은 것: shapeTag→재질표 조회(Phive 콜백), 비트필드 사용 코드 — [bulletbody]/[physics] 소관 |
| 장외·사망·물 판정의 플레이어 쪽 처리 | [player]/[combat] 소관 |
| 히어로 모드 기믹 동작 | 리플렉션 정정 + 간헐천 상태·높이 법칙 + 점프대 발사 조건 판독(stage_misc §7.1~7.3). 남은 것: 간헐천 Wait→Extend 진입, 점프대 속도 출처, 파이프라인·그라인드 레일 동작 |

## 9. 공용 문서 반영 제안 (직접 수정하지 않음)

- `01_package_and_assets.md`: Banc 포맷(§3)과 레이어=모드 표(§3.1), `.bphsh` 헤더·재질표 구조(stage_misc §3.2), 본문 = Havok TAG0 hknpMeshShape([collision_mesh.md](collision_mesh.md)) 행 추가.
- `tools.md` 영역 도구 표 기믹 행: `collision_tag0.py`, `collision_mesh.py`, `collision_scan.py`, `gimmick_lift.py` 추가.
- `02_code_and_params.md`: 열거형 값 목록은 `spl::<이름>` 다음 줄이 아니라 "이름 문자열 기록 직후 bl 하는 정보 함수" 안의 값 문자열에 있다(stage_misc §1.2, §3.3). 리플렉션 도구의 열거형 필드 타입 표기는 믿지 말 것(`RailMovableSequentialParam.SpeedCalcType`을 f32로 표시).
- `tools.md`: `gimmick_funcs.py`(BL·포인터·ADRP 대상으로 함수 시작 후보), `gimmick_annot.py --collapse`(파라미터 체인 접기) 소개. 같은 주소의 상태머신 콜백(ADRP+ADD로만 참조)은 BL 목록에 안 잡히므로 ADRP 대상을 함께 봐야 한다는 주의.
- `02_code_and_params.md` §2.3: 리플렉션 도구가 커브 필드 뒤 오프셋·플래그를 뒤바꾸는 경우(원인: 커브는 '값 → 이름 → 플래그' 순서, 정정 도구 `web/tools/gimmick_reflect_fix.py`, 정정표 stage_misc §7.1), 열거형을 bool로 표시하는 경우(Sponge `ModelType`), 다른 구조체의 같은 플래그 번호를 혼동하기 쉬운 점(InkRailParam 0xfc~ vs PlayerPipelineParam 0xf8~) 주의 문구.
- `tools.md`: capstone `disasm`으로 넓은 범위를 훑을 때 `md.skipdata = True`가 없으면 첫 데이터 워드에서 조용히 멈춥니다(3차 작업 중 확인).
