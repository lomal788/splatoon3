# FillUp 원본 등록·형상·배치 자료 (r9, 2026-10-03)

## 1. 기능 개요와 체감 동작

**[데이터]** 원본 PhiveConfig의 `MaterialPresetCollection[61] FillUpPlayer`는 `LayerHitMaskEntity=SplKeepOutPlayer`와 `UserShapeTagMask=[FillUp]`를 함께 등록한 **플레이어용 충돌 재질 프리셋**이다. 이것은 FillUp 철자에 대한 번역이나 이름 추정이 아니다. 원본 재질행의 bit28과 플레이어용 필터의 실제 조합을 확인했다. 접촉 이후 바닥 후보 대체 소비자는 [fillup_contact_runtime.md](../physics/fillup_contact_runtime.md)로 연결하며 이번 문서는 데이터 작성·배치 근거만 다룬다.

“모든 FillUp은 수직벽이다”는 전수 형상과 맞지 않는다. 위향·아래향·경사·수직면 모두 존재한다. “제작자가 시각적 틈을 메우려고 만든 면”이라는 심리적/역사적 작성 목적은 원본 주석이 없어 **[미확정]**으로 남긴다.

## 2. 원본·버전·자료

Splatoon 3 v0에서 추출한 읽기 전용 `extracted/romfs`를 읽었다. `original/`과 키 파일은 열거나 변경하지 않았다. 도구 `web/tools/r9_physics_fillup_authoring_data.py`, 결과 `analysis/completion/r9/physics_fillup_authoring_data.json`. 기존 SHARED/FUNCS의 Lby48팩·Yagara 샘플 검사를 선행 확인했다. 새 검사는 그 샘플을 다시 신규 성과로 세는 대신 원본 Actor/Scene 팩 전체의 FillUp 사용과 등록값을 조사한다. 다른 맵은 같은 태그의 자료 대조에만 사용했으며 다른 모드 실제 동작은 분석하지 않았다.

## 3. 진입점과 전체 연결 흐름

**[데이터]** config material preset61은 다음 전체 원본 행이다.

```json
{"ComponentName":"FillUpPlayer","LayerHitMaskEntity":"SplKeepOutPlayer","LayerHitMaskSensor":"","Material":"","SubLayerHitMaskEntity":"","SubLayerHitMaskSensor":"","SubMaterial":"","UserShapeTagMask":["FillUp"]}
```

`UserShapeTagMaskCollection[26]`의 `{ComponentName:FillUp,MaskValue:268435456}`은 bit28이다. 빈 Material·SubLayer 필드를 임의 기본값으로 채우지 않는다. 이 프리셋의 빈 Material은 실제 shape마다 다른 Material 값이 기록될 수 있다는 것과 구분한다. descriptor 원본 reader와 runtime tag writer는 별도 협업 근거다.

## 4. 구조체·필드·상수

원본 bphsh 재질행은 `(materialIndex:u32, unknown:u32, UserShapeTag:u64)` 16B이고 filter는 별도 u64 배열이다. FillUp39행 모두 filter low32=`0x62=SplKeepOutPlayer`였다. high32는 37행 `FFFFFFFF`, 한 행 `03FFF5FF`(SplSuperHookCheckThrough), 한 행 `03FF75CF`이며 원본 필터표 이름은 JSON geometry.filter에 보존했다. tag28과 physics body flag28은 다른 필드다.

형상 좌표·tag-run은 기존 원본 판독으로 검증된 `collision_mesh.py`를 쓴다. 면적·법선 y는 복원된 원본 삼각형에서 계산한 **데이터 기술 통계**이고 Havok 질의를 실행한 값이 아니다. `upFacingArea`는 ny>.7, down은 ny<−.7, vertical은 abs(ny)<1e-6 기준이다.

## 5. 상태 전이와 수명

105개 원본 Banc의 선언된 Actors에서 FillUp가 든 Actor 팩을 참조한 배치40개/Scene13개를 확인했다. Hash/Gyaml와 명시된 Translate/Rotate/Scale은 JSON에 그대로 남겼다. 키가 없는 transform을 임의 단위·원점으로 확정하지 않았다. 동적으로 생성되는 형상·태그 변경 여부는 이 파일 목록만으로 확정하지 않는다.

| Scene 팩 | 태그 형상을 가진 Actor 배치 수 |
|---|---:|
| LastBoss.pack.zs | 1 |
| LaunchPadWorld.pack.zs | 1 |
| Msn_A06_02C.pack.zs | 5 |
| Msn_R_05.pack.zs | 1 |
| Plaza.pack.zs | 1 |
| Vss_Carousel.pack.zs | 2 |
| Vss_District00.pack.zs | 5 |
| Vss_Kaisou03.pack.zs | 5 |
| Vss_Scrap00.pack.zs | 1 |
| Vss_Temple00.pack.zs | 1 |
| Vss_Upland03.pack.zs | 9 |
| Vss_Yagara.pack.zs | 6 |
| Vss_Yunohana.pack.zs | 2 |

## 6. 계산식·조건·데이터 값

### 6.1 전수검사 집계 [데이터]

Actor3572+Scene107=**3679팩 /48959entries**, bphsh1485/재질행3017, BYML40020(그중 Phive10771), loose BYML136의 파일 이름·압축 해제 bytes를 조사했다. 구조적 BYML 파싱은 FillUp/fillup 문자열을 포함한 파일과 모든 Scene Banc105개에 적용했다. BYML40020을 모두 구조적 파싱한 것처럼 쓰지 않는다. 팩/형상/대상 BYML 읽기·파싱 및 FillUp geometry decode 오류0. 이 수치는 실제 추출물 목록 범위이며 원본에 포함되지 않은 DCC 제작 파일의 존재/부재를 증명하지 않는다.

FillUp **39재질행 /28Actor 팩 /원본 byte SHA256 기준19개 고유 shape**. Actor 팩별 동일 원본 shape가 중복되어 있으므로39행 면적을 단순 합하여 맵 전체 고유면적이라고 말하지 않는다. 재질은 Undefined23,Stone10,Metal2,Rubber/Vinyl/Plastic/Fence 각1행. tagged root는 모두 hknpMeshShape다.

| Actor 팩 | 행 | 재질 | 함께 기록된 태그 | 삼각형 | 면적 | 위향 면적 | normal y 범위 | filter |
|---|---:|---|---|---:|---:|---:|---|---|
| DObj_BunkerCliff01 | 2 | Rubber | FillUp | 3 | 2.053 | 0.0 | 0.0000~0.3468 | 0xffffffff00000062 |
| DObj_BunkerCliff02 | 2 | Undefined | FillUp | 40 | 29.78 | 0.0 | -1.0000~0.2499 | 0xffffffff00000062 |
| Fld_AlternaR05 | 4 | Undefined | KeepOut/FillUp | 48 | 402.084 | 0.0 | 0.0000~0.0000 | 0xffffffff00000062 |
| Fld_BankaraCity | 4 | Metal | FillUp | 6 | 8.075 | 1.054 | 0.0000~1.0000 | 0xffffffff00000062 |
| Fld_BankaraCity | 10 | Undefined | FillUp | 28 | 36.062 | 1.308 | -1.0000~1.0000 | 0xffffffff00000062 |
| Fld_Carousel03 | 4 | Stone | Slide/FillUp | 54 | 19.769 | 0.369 | 0.3173~0.7608 | 0xffffffff00000062 |
| Fld_Carousel03 | 30 | Undefined | FillUp | 12 | 66.234 | 0.0 | 0.0000~0.0000 | 0xffffffff00000062 |
| Fld_District00 | 22 | Stone | Slide/FillUp | 12 | 42.05 | 0.0 | -1.0000~0.0499 | 0xffffffff00000062 |
| Fld_Kaisou03 | 7 | Undefined | FillUp | 88 | 6.716 | 2.237 | 0.0000~1.0000 | 0xffffffff00000062 |
| Fld_Kaisou03 | 15 | Undefined | PlayerDead/KeepOut/FillUp | 32 | 249.562 | 0.0 | 0.0000~0.0000 | 0x3fff5ff00000062 |
| Fld_Upland03 | 2 | Stone | FillUp | 30 | 23.713 | 0.0 | 0.0000~0.3192 | 0xffffffff00000062 |
| Fld_Upland03 | 4 | Undefined | FillUp | 224 | 3069.373 | 28.918 | -0.0053~1.0000 | 0xffffffff00000062 |
| Fld_Upland03 | 27 | Undefined | Slide/FillUp | 16 | 66.443 | 66.443 | 0.7980~0.8406 | 0xffffffff00000062 |
| Fld_Upland03 | 29 | Undefined | FillUp/IgnoredByMiniMap | 108 | 1890.698 | 35.352 | -1.0000~1.0000 | 0xffffffff00000062 |
| Fld_Yagara | 2 | Undefined | FillUp | 114 | 164.013 | 0.0 | -0.0745~0.4406 | 0xffffffff00000062 |
| Fld_Yagara | 9 | Vinyl | FillUp | 20 | 13.22 | 0.345 | 0.0764~0.9932 | 0xffffffff00000062 |
| Fld_Yagara | 10 | Plastic | FillUp | 29 | 8.512 | 0.31 | -0.1254~1.0000 | 0xffffffff00000062 |
| Fld_Yunohana | 4 | Fence | Fence/FillUp | 40 | 54.971 | 6.296 | 0.0000~1.0000 | 0x3ff75cf00000062 |
| Fld_Yunohana | 8 | Undefined | Slide/FillUp | 24 | 3.409 | 3.143 | 0.0000~0.8553 | 0xffffffff00000062 |
| Fld_Yunohana | 9 | Undefined | FillUp | 116 | 328.782 | 19.431 | -0.0235~1.0000 | 0xffffffff00000062 |
| Fld_Yunohana | 11 | Stone | FillUp | 111 | 28.725 | 0.0 | -0.9942~0.5421 | 0xffffffff00000062 |
| Gachiyagura_2M | 0 | Undefined | FillUp | 14 | 26.574 | 3.715 | -1.0000~1.0000 | 0xffffffff00000062 |
| Gachiyagura_3M | 0 | Undefined | FillUp | 14 | 26.574 | 3.715 | -1.0000~1.0000 | 0xffffffff00000062 |
| Gachiyagura_4M | 0 | Undefined | FillUp | 14 | 26.574 | 3.715 | -1.0000~1.0000 | 0xffffffff00000062 |
| Lft_Fld_BigWorldLaunchPad01 | 6 | Stone | Slide/FillUp | 28 | 2429.712 | 494.215 | -1.0000~1.0000 | 0xffffffff00000062 |
| Lft_FldObj_DistrictBridgeNoHandrail | 1 | Stone | Slide/FillUp | 12 | 42.05 | 0.0 | -1.0000~0.0499 | 0xffffffff00000062 |
| Lft_FldObj_DistrictFence | 1 | Stone | Slide/FillUp | 12 | 42.05 | 0.0 | -1.0000~0.0499 | 0xffffffff00000062 |
| Lft_FldObj_RubberPole00 | 1 | Undefined | Slide/FillUp | 4 | 0.451 | 0.0 | 0.5547~0.5547 | 0xffffffff00000062 |
| Lft_FldObj_UplandAsariSet | 3 | Undefined | FillUp | 18 | 19.959 | 0.0 | -0.0882~0.0567 | 0xffffffff00000062 |
| Lft_FldObj_UplandNoBR | 5 | Undefined | FillUp | 20 | 8.02 | 0.0 | -0.0069~0.6469 | 0xffffffff00000062 |
| Lft_FldObj_UplandWallBlockSet | 4 | Undefined | FillUp | 18 | 19.959 | 0.0 | -0.0882~0.0567 | 0xffffffff00000062 |
| Lft_KumaRocket | 2 | Metal | FillUp | 64 | 401.039 | 0.0 | -0.5681~0.5715 | 0xffffffff00000062 |
| Mpt_Fld_BigWorldLaunchPad01 | 6 | Stone | Slide/FillUp | 28 | 2429.712 | 494.215 | -1.0000~1.0000 | 0xffffffff00000062 |
| Mpt_FldObj_DistrictBridgeNoHandrail | 1 | Stone | Slide/FillUp | 12 | 42.05 | 0.0 | -1.0000~0.0499 | 0xffffffff00000062 |
| Mpt_FldObj_DistrictFence | 1 | Stone | Slide/FillUp | 12 | 42.05 | 0.0 | -1.0000~0.0499 | 0xffffffff00000062 |
| Mpt_FldObj_RubberPole00 | 1 | Undefined | Slide/FillUp | 4 | 0.451 | 0.0 | 0.5547~0.5547 | 0xffffffff00000062 |
| Mpt_FldObj_UplandAsariSet | 3 | Undefined | FillUp | 18 | 19.959 | 0.0 | -0.0882~0.0567 | 0xffffffff00000062 |
| Mpt_FldObj_UplandNoBR | 5 | Undefined | FillUp | 20 | 8.02 | 0.0 | -0.0069~0.6469 | 0xffffffff00000062 |
| Mpt_FldObj_UplandWallBlockSet | 4 | Undefined | FillUp | 18 | 19.959 | 0.0 | -0.0882~0.0567 | 0xffffffff00000062 |

### 6.2 기존 수직벽 결론 정정 (2026-10-03)

기존 collision_mesh§4 표 자체는 Yagara tag9/10의 위향면적을0.3으로 기록했으나 아래 설명은 FillUp2/9/10이 모두 위향면적0·수직벽이라고 표현했다. 새 원본 정점/삼각형 전체 판독은 tag9=0.345,tag10=0.310,tag2 normalY=−.0745..+.4406이다. **플레이어용 필터 조합 결론은 유지하되 모든 면이 수직이라는 표현은 정정**한다. 다른 맵에서도 Upland 태그27 Slide|FillUp는 normalY=.7980.. .8406이고 위향면적66.443으로 원본 경사면이 존재한다. 예외를 임의로 지우지 않는다.

### 6.3 동일 문자열과 실제 shape 연결 [데이터]

검색 결과27기록은 tower Actor3종의 이름/파라미터21기록, Scene5개 Rail FillUpType 기록, PhiveConfig1개이다. 동일 파일이 filename occurrence와 payload occurrence로 각각 기록될 수 있으며27을 고유 파일 수로 쓰지 않는다. tower 상태/enum의 실제 동작은 범위 밖이지만 다음 **동일 UserShapeTag 연결**은 원본 데이터로 확인한다.

`Gachiyagura_2M/3M/4M` ControllerSetParam은 이름 FillUp에 `Gachiyagura_FillUp` rigid body와 `Vlift_FillUpP` shape를 매핑한다. 해당 body는 `EnableLayerHitMask=SplKeepOutPlayer, LayerEntity=SplObject, MotionType=Kinematic, ShapeName=FillUp`; shape param은 `Work/Phive/Shape/Dcc/Vlift_FillUpP.phsh`를 참조한다. 그 실제 bphsh row0는 **UserShapeTag bit28 FillUp**, 필터`FFFFFFFF00000062`, Undefined,14삼각형이다. 따라서 tower 쪽 FillUp 이름을 UserShapeTag와 완전히 무관한 문자열로 단정하지 않는다. 이것이 일반 FillUp의 제작자 의도를 설명한다는 주장은 하지 않는다.

## 7. 화면·애니메이션·이펙트·소리 연결

원본 tagged collision mesh·preset은 보이는 render material과 같은 개념이 아니다. Rubber/Metal 등 물리 재질 이름만으로 어떤 표면이 화면에서 보이거나 소리를 낸다고 확정하지 않는다. FillUp 이름만으로 잉크 표시·도색 가능 여부를 배제하지 않는다.

## 8. 다른 기능과의 상호작용

FillUp에는 Slide/KeepOut/PlayerDead/Fence/IgnoredByMiniMap이 함께 기록될 수 있다. FillUp 하나의 값으로 그 다른 비트의 consumer를 대신하지 않는다. Lby_Lobby00의 정적48배치팩 검사에서는 FillUp0이라는 기존 사실을 유지한다. 전체 원본 전수조사에서 발견한 다른 맵 FillUp를 사격장에 새로 배치하지 않는다.

## 9. 웹 포팅 구조와 순서

향후 `impl/physics.md` 및 `impl/assets.md`: FillUpPlayer 프리셋 구성과 실제 low/high filter를 보존하고 수직벽 전용·구멍 메우기 목적을 근거 없이 하드코딩하지 않는다. `impl/paint.md`의 FillUp 태그 이름만으로 칠을 제외한 근사는 실제 도색 consumer와 따로 검증해야 한다. 이번에는 웹 코드와 impl을 변경하지 않았다.

## 10. 검증 코드·실행 결과

`.venv/Scripts/python.exe web/tools/r9_physics_fillup_authoring_data.py`: exit0,3679팩·1485bphsh·3017재질행,40020BYML byte검색+136loose,FillUp39행/28Actor/19고유shape,105Banc/40배치/13Scene,errors/geometry_errors0. 원본 함수 Unicorn 실행이 아닌 **[데이터] 전수검사**다. 큰 원본/분석 파일을 삭제·이동하지 않았다. geometry의 태그별 전체 상세값·상자·면적·법선·필터, 이름 occurrence 경로와 명시된 배치값은 JSON으로 보존한다.

## 11. 미확정·한계·다음 조사

- **[미확정] 역사적 작성 목적:** 원본 release의 linked preset·BPHSH·Banc·태그 파라미터에 “틈/구멍을 메우기 위해 이 면을 작성했다”는 설명 필드·주석을 찾지 못했다. 이름·면 위치만으로 저자의 의도를 확정하지 않는다. 다음 근거는 release에 없는 DCC authoring source·exporter 설정/주석 또는 원제작자의 명시적 설명이다.
- **[데이터] 기능적 등록 정의:** FillUpPlayer는 원본 config가 지정한 플레이어용 필터+UserShapeTag bit28 재질 프리셋이라는 것은 확정한다. runtime 동작 전체는 원본 소비자/생성자 검증과 결합한다.
- BYML 검색은 명시 문자열을 대상으로 했고 의미가 다른 표현으로 적힌 임의 주석을 증명한 시험이 아니다. 원본 코드 writer와 Lby 실행 후 동적 shape는 다른 에이전트 근거를 기다린다.
- 이 문서만으로 고정 inventory L148 전체를 승격하지 않는다. 부분 근거를 whole 확정으로 세지 않는다.
