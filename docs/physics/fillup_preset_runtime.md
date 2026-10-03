# FillUpPlayer 프리셋의 원본 등록과 비트 생성 (r9, 2026-10-03)

## 1. 기능 개요와 체감 동작

**[데이터]+[판독]+[실행: 정수 등록 필드]** FillUp은 원본 `UserShapeTag` bit28=`0x10000000`이다. `FillUpPlayer` 프리셋은 이 태그와 `SplKeepOutPlayer`의 Entity 충돌 마스크 `0x62`를 함께 제공한다. 이름을 보고 추가한 해석이 아니라 원본 PhiveConfig와 실제 로더의 기록으로 확인했다. 프리셋의 존재 자체가 Lby_Lobby00에서 사용됨을 뜻하지 않는다.

## 2. 원본·범위·자료

Splatoon3 v0 Lby_Lobby00 1인 연습. 원본 입력 `extracted/romfs/Phive/Config/PhiveConfig.byml.zs`의 압축 해제 BYML SHA256=`d313feeb573d1b8109630d9e533867260eefb8aa6b9ef079960cf359d88ee3f9`.

`3b0f3d8`(26,120B)의 기존 `analysis/decomp/r9_physics/motion_config.c`를 재사용했다. 기존 MotionProperties 분석을 다시 확정 수로 세지 않는다. 새 도구 `web/tools/r9_physics_fillup_preset_probe.py`, `r9_physics_fillup_preset_emu.py`; 결과 `analysis/completion/r9/physics_fillup_preset_{probe,emu}.json` 및 세 실패 JSON.

## 3. 진입점·호출 흐름

**[판독]** `3b0f3d8(Config, rawBYML, heap)`가 전체 설정을 읽는다. `UserShapeTagMaskCollection`의 이름/MaskValue 표를 먼저 만들고, 이후 `MaterialPresetCollection`의 각 `UserShapeTagMask` 이름을 찾아 대응하는 u64 값을 OR한다. 내부 `3b13b48..3b13cb0`가 이 프리셋 마스크를 만든다. 내부 주소 `3b13a9c`는 독립 함수가 아니며 실제 시작은 `3b0f3d8`이다.

등록된 descriptor는 이후 형상 factory의 프리셋 소비 경로로 전달된다. 실제 Actor→factory→형상 재질 소비는 [fillup_dynamic_sources.md](fillup_dynamic_sources.md)에서 별도 판독하며, 본 실행은 씬 형상을 생성하지 않는다.

## 4. 필드·자료형·초기값

Config 포인터를 CF, 프리셋의64B descriptor를 D라고 한다. 원본 로더의 CF는 최종 후반 표 기록까지 포함하므로 시험용 버퍼는 `0x8000`으로 잡았다. 원본 구조체 전체 크기를 이 숫자로 확정한 것이 아니다.

| 위치 | 형식·기록 의미 |
|---|---|
| CF+80 / +88 | u32 태그 수49 / u64 MaskValue 배열 포인터 |
| CF+3c8 / +3d0 | 태그 이름 수·이름 배열 |
| CF+40 / +48 | Entity layer mask 수50 / u32 MaskValue 배열 |
| CF+2b8 | MaterialPreset 검색 노드 배열, 노드128B |
| D+0 / +4 | Material 값 / 지정 여부 |
| D+8 / +c | SubMaterial 값 / 지정 여부 |
| D+10 / +18 | u64 UserShapeTagMask OR 결과 / 유효 byte |
| D+20 / +24 | Entity mask u32 / 유효 byte |
| D+28 / +2c | Entity sublayer mask u32 / 유효 byte |
| D+30 / +34 | Sensor mask u32 / 유효 byte |
| D+38 / +3c | Sensor sublayer mask u32 / 유효 byte |

오프셋은16진수다. tag collection index26과 프리셋 index61은 원본 데이터의 배열 순서이며, 태그 비트 번호28과 혼동하지 않는다.

## 5. 상태 전이와 수명

**[판독]** 새 설정 로드 시 이름과 수치 표를 만들고 각 프리셋의 빈 선택 값은 미지정 상태로 둔다. UserShapeTagMask 목록은 원본 이름 탐색 결과를 OR한 값과 유효 byte1을 기록한다. 빈 layer 이름이면 값0/유효0, 지정된 이름이면 해당 원본 mask/유효1이다. 이번 실행은 정상 원본 설정의 초기 등록이며 재로드·해제·잘못된 BYML 예외 전체는 신규 검증하지 않았다.

## 6. 계산식과 원본 FillUpPlayer 값

**[데이터]+[실행: 정수 필드]**

```text
UserShapeTagMask = OR(PhiveConfig.UserShapeTagMaskCollection[name].MaskValue)
Layer value,valid = name is empty ? (0,0) : (maskTable[name],1)
```

원본 `MaterialPresetCollection[61]`은 `ComponentName=FillUpPlayer`, `UserShapeTagMask=[FillUp]`, `LayerHitMaskEntity=SplKeepOutPlayer`이며 다른 Material/SubMaterial/layer 선택은 빈 값이다. 등록된 descriptor의 태그 및 네 layer 값/유효byte는 다음과 같다.

```text
[D+10,D+18,D+20,D+24,D+28,D+2c,D+30,D+34,D+38,D+3c]
= [0x10000000,1,0x62,1,0,0,0,0,0,0]
```

`0x62`의 set bit는1(CustomReceiver),5(SplPlayer),6(SplPlayerChariotShield)다. 태그와 충돌 mask는 서로 다른 필드다. 실제 충돌 결합식은 [collision_mesh.md](../gimmick/collision_mesh.md) §3.4의 기존 원본 근거를 재사용한다.

## 7. 표현·리소스 연결

프리셋은 충돌 재질/필터 데이터다. 이 이름만으로 렌더링 재질·도색 가능 여부·화면의 벽 표시를 지정할 수 없다. 실제 bphsh 형상/원본 배치와 태그 적용은 [fillup_authored_data.md](../gimmick/fillup_authored_data.md) §4~6, 플레이어 접촉 소비는 [fillup_contact_runtime.md](fillup_contact_runtime.md) 및 [fillup_fallback.md](fillup_fallback.md)로 연결한다.

## 8. 다른 기능과 상호작용

프리셋 OR 결과는 실제 형상 재질행+8 UserShapeTag로 소비된다. 플레이어 바닥 후보의 최고 접촉이 FillUp이면 `24f8f58`은 일반 바닥 성공 대신 보조 탐색을 택한다. 이 runtime 규칙은 위 두 접촉 문서의 별도 원본 검증이다. 로더가 FillUp 비트를 만드는 일과 native geometry query가 접촉을 생성하는 일은 별도 검증 경계다.

## 9. 웹 반영 필요·구현 순서

웹 코드/impl 수정 없음. 다음 구현 시 tag 이름의 enum 순서 대신 원본 MaskValue를 쓰고, 프리셋의 tag와 Entity mask를 별도 필드로 유지해야 한다. 빈 필드의 유효 byte0을 명시 값0으로 덮어쓰기와 구분한다. 사격장에 원본 데이터상 없는 FillUp 면을 프리셋 이름만으로 새로 만들지 않는다. 관련 impl: `impl/physics.md`의 대응 항목은 공용 inventory의 웹 반영 열에서 확인한다.

## 10. 검증 명령·결과·실패

실제 명령(저장 폴더 `C:\dev\splatoon3`):

```powershell
.venv/Scripts/python.exe web/tools/r9_physics_fillup_preset_probe.py
.venv/Scripts/python.exe web/tools/r9_physics_fillup_preset_emu.py
```

최종 probe exit0, 원본 로더 정상 반환. 독립 원본 BYML 기대값과 **49 tag+50 Entity layer+108 preset×10=1,179 정수 필드** 대조, **0bad**, emu exit0. FillUpPlayer index61도 위10값이 일치한다. null/nullwrite/auto-page/fault/PLT 대체 호출 모두0.

실행 경계: 원본 `3513f3c` heap 생성 및 heap virtual+30 Allocate는 시험용 bump allocator, virtual+b0 heap-state는false fixture로 공급했다. BYML 탐색·이름 대응·OR·표/descriptor 저장은 원본 명령으로 실행했다. 함수 후반의 **FillUp과 무관한 powf812호출**은 공용 하네스의 Python f64 계산→f32 handler를 사용했다. 그 부동소수점 표의 비트 일치를 주장하지 않으며 비교 대상은 위 정수 등록 필드뿐이다.

실패를 보존했다. 첫 CF600/heap string pool 누락은 null394·명령 상한 도달(exit1, `physics_fillup_preset_first_failure.json`). 두 번째 heap 공급 후 CF600은 후반 표가 시험용 heap을 덮어 null1/auto-page1(exit1, `second_failure.json`). 세 번째 CF5000도 후반 기록이 CF+6f08까지 진행해 heap vtable을 덮었으며 null1로 reject(exit1, `third_failure.json`). CF8000과 명시 heap-state 경계 후 최종0bad다. 첫 probe에서 capture register를 X21로 잘못 읽은 부분은 원본 `STR X23,[X28,#10]`에 따라 정정했다.

## 11. 미확정·시도·다음 근거

**[미확정]** Map author의 역사적 “구멍 메우기” 의도는 이름·형상·runtime 처리로 복원할 수 없다. 원본 공개 릴리스에는 제작자의 목적 설명 주석이 발견되지 않았다. 전체 Actor/Scene 원본 데이터, 실제 프리셋 로더·형상 소비자·플레이어 접촉 소비까지 조사한 기능적 결과를 이 의도로 승격하지 않는다. 다음 근거는 원본 DCC 저작 소스·exporter 주석·제작자의 해당 태그 설명이다.

Lby 배치48팩과 플레이어/슈터 포함53root의 원본 리소스 closure에서 FillUp0은 데이터 경계 내 부재이며, 임의 runtime 쓰기 전체의 부재 증명은 아니다. 다른 함수의 원본 heap lifecycle, 설정 재로드/해제/오류 입력, 실제 씬 모든 native geometry query/solver 검증 역시 본 등록 실행의 완료 대상으로 세지 않았다. 고정 질문 `gimmick/collision_mesh.md:L148` 전체 확정 승격 없음.
