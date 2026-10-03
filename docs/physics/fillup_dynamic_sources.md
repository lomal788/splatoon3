# FillUp의 사격장 동적 액터·형상 입력 (r9, 2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

**[데이터]** Lby_Lobby00의 배치48종과 1인 스플래시슈터 연습에 명시된 동적5종(`SplPlayer`, `WeaponShooterNormal`, `BulletShooterBase`, `BulletSplashShooter`, `BulletWallDrop`)의 형상 입력에는 `FillUp` 태그를 부여하는 프리셋이 없다. **[판독]** 실제 탄 유닛 초기화→형상 팩토리→프리셋 콜백에서는 `UserShapeTag`를 프리셋 결과에서 복사한다. 이 확인은 아래에 한정한 원본 리소스·함수의 계약이며 모든 런타임 변경의 부재 증명은 아니다.

FillUp의 바닥 후보 소비와 대체 탐색은 [fillup_contact_runtime.md](fillup_contact_runtime.md), 이름·마스크·프리셋 파서는 [fillup_preset_runtime.md](fillup_preset_runtime.md)의 담당 근거와 연결한다. 본문 결과만으로 “구멍 메우기”라는 작성 목적이나 고정 감사 `gimmick/collision_mesh.md:L148`의 전체를 확정하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon3(v0)의 원본 추출물 `extracted/romfs/Pack/Actor/*.pack.zs`, `Pack/Bootup.Nin_NX_NVN.pack.zs`, `Phive/Config/PhiveConfig.byml.zs`, `extracted/exefs/main.reloc.img`를 읽었다. Banc 출처는 `analysis/range/pack_LobbyVersus/Banc/Lby_Lobby00.bcett.byml.json`이다. original·키·웹 코드·impl·package는 변경하지 않았다.

새 데이터 산출물은 `analysis/completion/r9/fillup_actor_source_audit.json`, `fillup_actor_resource_closure.json`; 새 원문은 `analysis/decomp/r9_fillup_actor/shape_factory.c`, `primitive_preset_callbacks.c`다. `10036a8`은 기존 `analysis/decomp/bulletbody/bb_batch2.c`를 재사용한다. 주소는 모두 main 기준 `0x7100000000`을 더한다.

## 3. 진입점과 전체 호출 흐름

### 3.1 원본 리소스 사슬 [데이터]

`ActorParam.Components.PhysicsRef → PhysicsParam.ControllerSetPath → ControllerSet.ShapeNamePathAry.FilePath → ShapeParam`을 따라간다. 탄은 추가로 `ActorParam.Components.BulletBodyRef → BulletBodyControllerEntity.UnitArray → BulletBodyParam/ShapeParam`을 따른다. `$parent`와 공용 Bootup 자료도 포함한다. 예약 요청은 `WeaponShooterNormal.RequestList`의 슈터탄32·스플래시32·벽낙하16으로 연결된다.

`BulletShooterBase`의 `ShapeParam`은 자기 Actor팩에 없고 **공용 Bootup팩**에 있다. 따라서 Actor팩의 이름 검색만으로 형상 태그를 모두 확인했다고 하면 안 된다. `MainWeaponParent_ShotGuide`와 `PlayerCustomPartStandAlone`의 물리 형상 참조도 이번 데이터 사슬에 포함했다. 사격장 정적팩은 기존48종의 새 부모 참조 감사를 수행했으며, 그 기존257배치/59재질행 자체를 새 확정 수로 재계상하지 않는다.

### 3.2 실제 코드 소비 [판독]

기존 `10036a8`의 실제 BL PC `1004350`이 유닛의 shape resource `unit+88 → resource+158`을 새 판독 팩토리 `3a49c44`에 준다. 방문 객체 VT는 `55762a8`; 성공한 shape를 `unit+40`에 기록한 뒤 기존 `3b0ada8`로 탄 몸체를 만든다. 그 원문을 이번에 재실행하지 않았다.

`3a49c44`는 설정됨 플래그와 부모 파라미터를 따라 형상 배열을 순회하고, 형상마다 VT 콜백을 호출한다. 아래 새 판독 콜백의 `MaterialPresets` 리스트는 primitive param+30이며 설정 플래그는 primitive param+7d bit0이다. 리스트가 있으면 `3a513d0`를 호출하고, 성공한 u64 태그 결과를 descriptor+8에 **그대로** 복사한다.

| 콜백/VT 슬롯 | 프리셋 resolver BL PC | u64 태그 복사 PC |
|---|---|---|
| `3a440d8` / `55762a8+50` | `3a44ac4 → 3a513d0` | `3a44afc STR X8,[X19,#8]` |
| `12d7380 → 3a46068` / `+68` | `3a46a54 → 3a513d0` | `3a46a8c STR X8,[X19,#8]` |
| `3a47768` / `+78` | `3a47d7c → 3a513d0` | `3a47db4 STR X8,[X19,#8]` |
| `3a4801c` / `+80` | `3a487c4 → 3a513d0` | `3a487fc STR X8,[X19,#8]` |

기하 생성·scale·반경 보정이 위 u64 복사에 임의의 FillUp 비트를 OR하는 식은 이 콜백에 없다. resolver 내부 전체와 이후 live shape 변경의 전체를 이 문서에서 판독했다고 하지 않는다.

## 4. 구조체·필드·상수·열거형

| 기준 객체 | 필드 | 확인 내용 |
|---|---|---|
| primitive param | +30 리스트 / +7d bit0 | MaterialPresets 배열·설정 여부, 새 콜백 reader |
| primitive descriptor | +0/+4 u32 | resolver가 반환한 Material/SubMaterial; sentinel35 또는1일 때 두 값을0으로 보정 |
| primitive descriptor | +8 u64 | resolver의 UserShapeTag 결과를 복사; geometry vector가 아님 |
| bphsh 재질16B행 | +8 u64 bit28 | FillUp `0x10000000`; Body filter+8 bit28과 구분 |
| PhiveConfig preset | ComponentName `FillUpPlayer` | LayerHitMaskEntity=`SplKeepOutPlayer`, UserShapeTagMask=[`FillUp`] **[데이터]** |

TagCollection의 이름 순번48을 bit48로 해석하지 않는다. 실제 mask는 `UserShapeTagMaskCollection.MaskValue`의 bit28이다.

## 5. 상태 전이와 전체 수명

데이터 감사는 ActorParam·부모·컴포넌트·shape의 로드 입력을 확인한다. 코드 사슬은 탄 유닛 초기화 시 shape와 body가 만들어지는 구간이다. 예약 풀의 활성·해제·lifecycle는 기존 [shooter_bullet.md](../weapon/shooter_bullet.md) §3.3의 근거를 재사용한다.

빈 프리셋 목록이면 콜백은 descriptor+0/+4를0으로 쓰며, 팩토리가 처음0으로 만든 태그를 새 FillUp로 바꾸지 않는다. 리스트가 있으면 resolver 실패시 shape 생성을 실패로 반환한다. reset·파괴·재생성의 모든 actor별 태그 writer는 이번 새 판독 경계에 포함하지 않는다.

## 6. 계산식·조건·상세 의사코드

**[판독]** 태그 생산에서 geometry 보정과 프리셋 결과 복사를 구분한다.

```text
shapeParam = unit.ShapeResource(+88).parameter(+158)
shape = factory3a49c44(visitorVT55762a8, shapeParam, scale, heap)

callback(desc, primitiveParam):
    p = inherited field(MaterialPresets, flag+7d, valueList+30)
    if count(p) < 1:
        desc.material = desc.subMaterial = 0
    else:
        tag = 0
        if !resolver3a513d0(&material, &subMaterial, &tag,
                           &layerMasks..., p): return false
        if material == 35 or subMaterial == 1:
            material = subMaterial = 0
        desc.userShapeTag = tag  // u64 그대로, bit28 추가 없음
    return true
```

Config 데이터에서 프리셋21종의 `UserShapeTagMask` 이름을 실제 `MaskValue`로 OR한 값은 모두 `value & 0x10000000 == 0`이다. 이 OR 계산은 **[데이터: 값 대응]**이며 새 Unicorn 실행이라고 쓰지 않는다. 예: `SplInk=0x10000`, `SplPlayerColOthers=0x50000`, `SplKeepOutPlayer/AndCamera=0x8000000`, `PlayerChariot=0x1210`, `Slide=0x100000`, `PlayerUnsafe=0x400000`. KeepOut bit27과 FillUp bit28은 다르다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

이번 결과는 형상의 필터·재질 태그 입력이다. 카메라 구질의·총구·조준점·도색 표시를 새로 변경하거나, FillUp 이름에서 특정 화면 표현을 추정하지 않는다. 슈터 실제 두 구의 이름은 `GroundOnly/ExceptGround`, 프리셋은 각각 `GroundOnly+SplInk`, `ExceptGround+SplInk`다. ShotGuide의 공용 형상은 `SplInk`를 쓴다 **[데이터]**.

## 8. 다른 기능과의 상호작용

원본 바닥 후보 함수 `24f8f58`의 FillUp 소비와 이번 입력감사는 다른 단계다. 물리 필터가 허용한 접촉이어도 게임 바닥 선택에서 FillUp가 대체 탐색을 선택할 수 있다. body의 레이어 설정이 `SplKeepOutPlayer`라고 해서 그 shape에 FillUp가 있다는 뜻은 아니다.

3572 Actor팩/36758 BYML의 FillUp 문자열 검색에서 일치한12파일은 Gachiyagura_2M/3M/4M의 ControllerSet·RigidBodyEntity·RigidBodyController·ShapeParam이다. 몸체 이름 `FillUp`와 `Vlift_FillUpP.phsh` 참조이며, 해당 이름만으로 재질 bit28과 동일시하지 않는다. 그 actor의 실제 동작은 이번 범위 밖이며 분석하지 않았다.

## 9. 웹 포팅 구조와 구현 순서

웹의 shape metadata에서 material tag u64와 body layer/mask를 별도 필드로 보존한다. 원본 ShapeParam→MaterialPresets→Config mask를 반영한 뒤, 실제 바닥 후보에서 그 태그를 소비한다. Lby에서 새 FillUp 충돌면을 임의로 추가하지 않는다. `impl/physics.md`에 향후 이 계약과 Bootup 공용 shape 참조를 반영할 필요가 있다. 이번 웹 코드·impl 변경은0이다.

## 10. 검증 코드·실행 결과·기대값

새 데이터 감사:

| 검사 | 결과 |
|---|---|
| Actor팩 전체 이름 색인 |3572팩·36758BYML, FillUp 문자열12파일/3actor, 오류0 |
| 명시한 원본 resource closure | static48 + dynamic5 =53roots, 338방문·310고유 리소스 |
| 부모/shape/file 참조 누락 |0 |
| closure FillUp 문자열 / mesh bit28 |0 / 0 (원본mesh59행 포함) |
| Config의 실제 preset21종 |미등록0·FillUp 입력0 |
| dynamic5의 방문 리소스 |55 (예약 요청에서 중복방문 포함) |

도구: `web/tools/r9_fillup_actor_source_audit.py`, `r9_fillup_actor_resource_closure.py`; 결과 JSON과 최초 누락14 결과는 `analysis/completion/r9/`에 저장했다. 최초 phsh 경로 변환은 `.Nin_NX_NVN.bphsh` 플랫폼 접미사를 생략해14참조를 못 찾았다. `fillup_actor_resource_closure_first_missing14.json`을 보존하고 올바른 경로로 정정해 누락0을 얻었다.

새 원본 실행은 없다. 새 디컴파일은 factory1 + callback7함수 성공이며 위 STR의 실제 명령을 별도로 대조했다. `sh`는 PowerShell PATH에 없어 실패했으므로 `C:/Program Files/Git/bin/sh.exe`로 지정해 실행했다. `func_lookup 3a4801c`가 앞 함수3a47768로 안내했으나 실제3a4801c prologue와 직접 진입을 확인했다. 정확한 명령·성공/실패는 `analysis/completion/r9/fillup_actor_commands.md`에 기록했다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

- **[미확정]** 모든 runtime actor 생성·모든 shape 태그 변경의 부재: 이번 source closure는 명시53roots 및 원본 부모·물리 참조에 한정한다. 임의 생성 정보, Scene의 모든 비동기 actor 요청, 모든 modifier·tag setter를 닫지 않았으므로 전체 부재를 주장하지 않는다. 다음은 `3a513d0` resolver 실제 caller/shape tag setter와 Actor/Scene 생성 인자 사슬이다.
- **[미확정]** 제작 목적 “구멍 메우기”: 코드의 소비와 리소스 이름만으로 작성 목적을 확정하지 않는다. 원본 편집기 metadata·주석·작성 툴 자료가 필요하다.
- **[미확정]** factory whole 실행·모든 primitive geometry·모든 오류경로: 새로 원문을 판독했으나 해당 범위를 실행하지 않았다. raw callback offset을 최종 고수준 primitive 이름으로 모두 매핑하지 않았다. 물리 전체로 확대하지 않는다.

사용자의 FillUp 집중 후 종료 지시에 따라 새 분석은 여기서 마무리한다. 고정 질문의 복합 전체를 이 부분 결과로 승격하지 않으며 `fillup_actor_updates.json`은 새 확정0의 빈 배열이다. 기존 카메라 manifest는 변경하지 않았다.
